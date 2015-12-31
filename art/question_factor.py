# coding: utf-8

from __future__ import absolute_import
import argparse

import pandas as pd

from utils.data_store import (get_banker_conn, get_banker_dev_conn,
        redis_online, redis_debug, flush_redis)
from utils.consts import (
        ART_EXAM_KIND_MAP, ART_EXAM_KIND_DEFAULT,
        K_CHECKED, K_APPROVED
)
from art.meta import ChineseMeta, HistoryMeta, GeographyMeta, PoliticsMeta
from art.knowledge_model import ArtQuestionFactor
from art.question_index import ArtQuestionIndexBase

VALID_QUESTION_STATE = [K_CHECKED, K_APPROVED]
VALID_QUESTION_STATE = ",".join(map(str, VALID_QUESTION_STATE))


class ArtQuestionFactorBase(ArtQuestionIndexBase):

    def get_origin_info(self):
        conn = self.conn_func()
        sql = 'select target_kind, target_id, grade_id from %s'
        origin = pd.read_sql_query(sql % self.origin_table, conn)
        def _get_exam_kind(row):
            return ART_EXAM_KIND_MAP.get(row.grade_id, ART_EXAM_KIND_DEFAULT)
        origin['exam_kind'] = origin.apply(_get_exam_kind, axis=1)
        origin = origin[['target_kind', 'target_id', 'exam_kind']].drop_duplicates()
        origin = origin[origin.exam_kind != ART_EXAM_KIND_DEFAULT]
        origin.rename(columns={'target_kind':'qtype', 'target_id':'qid'},
                      inplace=True)
        return origin

    def get_choice_info(self):
        conn = self.conn_func()
        sql = ('select question_type, id, difficulty from %s where state '
               'in (%s)' % (self.choice_table, VALID_QUESTION_STATE))
        df = pd.read_sql_query(sql, conn)
        df.columns = ['qtype', 'qid', 'difficulty']
        df['sub_qid'] = df['qid']
        df['sub_type'] = df['qtype']
        return df

    def get_material_info(self):
        conn = self.conn_func()
        sql = ('select question_type, id, difficulty from %s where state '
               'in (%s)' % (self.material_table, VALID_QUESTION_STATE))
        df = pd.read_sql_query(sql, conn)
        df.columns = ['qtype', 'qid', 'difficulty']
        sql = 'select id, stem_id from %s' % self.material_question_table
        X = pd.read_sql_query(sql, conn)
        X.columns = ['sub_qid', 'qid']
        X['sub_type'] = self.K_MATERIAL_QUESTION
        return pd.merge(df, X)

    def get_reading_info(self):
        conn = self.conn_func()
        sql = ('select question_type, id, difficulty from %s where state '
               'in (%s)' % (self.reading_table, VALID_QUESTION_STATE))
        df = pd.read_sql_query(sql, conn)
        df.columns = ['qtype', 'qid', 'difficulty']
        sql = 'select id, stem_id from %s' % self.reading_question_table
        X = pd.read_sql_query(sql, conn)
        X.columns = ['sub_qid', 'qid']
        X['sub_type'] = self.K_READING_QUESTION
        return pd.merge(df, X)

    def get_knowledge_info(self):
        conn = self.conn_func()
        _convert = lambda df: df.groupby(['target_kind', 'target_id']
                ).apply(lambda x: "|".join(map(str, x.tag_id))).reset_index()
        VALID_TARGETS = [self.K_CHOICE, self.K_MATERIAL_QUESTION,
                         self.K_READING_QUESTION]
        VALID_TARGETS = ",".join(map(str, VALID_TARGETS))
        sql = ('select target_kind, target_id, tag_id from %s '
               'where target_kind in (%s)')
        k_info = _convert(pd.read_sql_query(sql % (self.knowledge_tag_table,
            VALID_TARGETS), conn))
        rk_info = _convert(pd.read_sql_query(sql %
            (self.related_knowledge_tag_table , VALID_TARGETS), conn))
        k_info.columns = ['sub_type', 'sub_qid', 'ktag']
        rk_info.columns = ['sub_type', 'sub_qid', 'rktag']
        info = pd.merge(k_info, rk_info, how='outer')
        info[['sub_type']] = info[['sub_type']].astype('int64')
        info[['sub_qid']] = info[['sub_qid']].astype('int64')
        return info

    def dump_question_factor(self, SUB_QTYPE, qinfo,
                             knowledge_info, knowledge_tree):
        res = []
        df = pd.merge(qinfo,
                      knowledge_info[knowledge_info.sub_type == SUB_QTYPE])
        df_group = df.groupby(['qtype', 'qid'])
        for name, group in df_group:
            qtype, qid = name
            difficulty = group.difficulty.iloc[0]
            S = group[['ktag', 'rktag']]
            ktag, rktag = set(), set()
            _f = lambda x: None if pd.isnull(x) else set(map(int, x.split('|')))
            for _, row in S.iterrows():
                ktag_set, rktag_set = map(_f, row)
                if ktag_set: ktag.update(ktag_set)
                if rktag_set: rktag.update(rktag_set)
            question_info = (ktag, rktag, difficulty)
            qfactor = ArtQuestionFactor()
            qfactor.add_factor(question_info)
            factor_value = qfactor.dump_factor()
            factor_key = self.QUESTION_FACTOR_KEY % (qtype, qid)
            flush_redis(self.redis_db, factor_key, factor_value)

            indices = self.get_question_knowledge_index(qfactor, knowledge_tree)
            res.append((qtype, qid, indices))
        return res

    def dump_question_index(self, question_list, origin):
        '''[(qtype, qid, set_of_module_ids), ...]'''
        df = pd.DataFrame(question_list)
        df.columns = ['qtype', 'qid', 'module_ids']
        df = pd.merge(df, origin)
        inv_idx = {}
        for _, row in df.iterrows():
            qtype, qid, module_ids, exam_kind = row
            for module_id in module_ids:
                inv_idx.setdefault((exam_kind, qtype, module_id), []).append(qid)

        modified_fields = set()
        for (exam_kind, qtype, module_id), qids in inv_idx.iteritems():
            field = '%s:%s:%s' % (exam_kind, qtype, module_id)
            value = "|".join(map(str, qids))
            self.redis_db.hset(self.QUESTION_INV_INDEX, field, value)
            modified_fields.add(field)

        self.flush_inv_index(self.QUESTION_INV_INDEX, modified_fields)

    def remove_unapproved_questions(self, question_type, table_name):
        conn = self.conn_func()
        cursor = conn.cursor()
        sql = 'select id from %s where state in (%s)'
        cursor.execute(sql % (table_name, VALID_QUESTION_STATE))
        pool = set([qid for qid, in cursor.fetchall()])

        count = 0
        qfactor_keys = self.get_all_question_factor_keys()
        keys = qfactor_keys.get(question_type, [])
        for key in keys:
            qid = int(key.split('/')[-1])
            if qid not in pool:
                self.redis_db.delete(key)
                count += 1
        print 'remove unapproved %s questions: %d' % (question_type, count)

    def calc_question_factor(self):
        self.remove_unapproved_questions(self.K_CHOICE, self.choice_table)
        self.remove_unapproved_questions(self.K_MATERIAL, self.material_table)
        self.remove_unapproved_questions(self.K_READING, self.reading_table)

        knowledge_tree = self.get_knowledge_tree()
        self.set_knowledge_tree_index(knowledge_tree)
        knowledge_info = self.get_knowledge_info()

        qinfo = self.get_choice_info()
        choice_idx = self.dump_question_factor(self.K_CHOICE, qinfo,
                                               knowledge_info, knowledge_tree)
        print '%s choice ok' % self.subject_name

        qinfo = self.get_material_info()
        material_idx = self.dump_question_factor(self.K_MATERIAL_QUESTION, qinfo,
                                                 knowledge_info, knowledge_tree)
        print '%s material ok' % self.subject_name

        qinfo = self.get_reading_info()
        reading_idx = self.dump_question_factor(self.K_READING_QUESTION, qinfo,
                                                knowledge_info, knowledge_tree)
        print '%s response ok' % self.subject_name

        question_list = choice_idx + material_idx + reading_idx
        origin = self.get_origin_info()
        self.dump_question_index(question_list, origin)
        print '%s question index ok' % self.subject_name
        self.set_knowledge_inv_index()
        print '%s knowledeg inverse index ok' % self.subject_name


class ChineseQuestionFactor(ChineseMeta, ArtQuestionFactorBase):
    pass


class HistoryQuestionFactor(HistoryMeta, ArtQuestionFactorBase):
    pass


class GeographyQuestionFactor(GeographyMeta, ArtQuestionFactorBase):
    pass


class PoliticsQuestionFactor(PoliticsMeta, ArtQuestionFactorBase):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    redis_db = redis_debug if args.debug else redis_online
    conn_func = get_banker_dev_conn if args.debug else get_banker_conn

    chinese_qfactor = ChineseQuestionFactor(conn_func, redis_db)
    chinese_qfactor.calc_question_factor()
    print 'chinese done.'

    history_qfactor = HistoryQuestionFactor(conn_func, redis_db)
    history_qfactor.calc_question_factor()
    print 'history done.'

    geography_qfactor = GeographyQuestionFactor(conn_func, redis_db)
    geography_qfactor.calc_question_factor()
    print 'geography done.'

    politics_qfactor = PoliticsQuestionFactor(conn_func, redis_db)
    politics_qfactor.calc_question_factor()
    print 'politics done.'

