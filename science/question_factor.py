# coding: utf-8

from __future__ import absolute_import
import argparse

import pandas as pd

from utils.data_store import (
    get_banker_conn, get_banker_dev_conn,
    redis_online, redis_debug, flush_redis
)
from utils.consts import (
    SCI_EXAM_KIND_MAP, SCI_EXAM_KIND_DEFAULT,
    K_CHECKED, K_APPROVED
)
from science.meta import PhysicsMeta, ChemistryMeta, BiologyMeta
from science.knowledge_model import SciQuestionFactor
from science.question_index import ScienceQuestionIndexBase

VALID_QUESTION_STATE = [K_CHECKED, K_APPROVED]
VALID_QUESTION_STATE = ",".join(map(str, VALID_QUESTION_STATE))


class ScienceQuestionFactorBase(ScienceQuestionIndexBase):

    def get_origin_info(self):
        conn = self.conn_func()
        sql = 'select target_kind, target_id, grade_id from %s'
        origin = pd.read_sql_query(sql % self.origin_table, conn)
        def _get_exam_kind(row):
            return SCI_EXAM_KIND_MAP.get(row.grade_id, SCI_EXAM_KIND_DEFAULT)
        origin['exam_kind'] = origin.apply(_get_exam_kind, axis=1)
        origin = origin[['target_kind', 'target_id', 'exam_kind']].drop_duplicates()
        origin = origin[origin.exam_kind != SCI_EXAM_KIND_DEFAULT]
        origin.rename(columns={'target_kind':'qtype', 'target_id':'qid'},
                      inplace=True)
        return origin

    def get_analysis_info(self):
        _convert = lambda df: df.groupby(['target_kind', 'target_id']
                ).apply(lambda x: "|".join(map(str, x.tag_id))).reset_index()
        conn = self.conn_func()
        ANALYSIS_KEYS = ",".join(map(str, self.ANALYSIS_KIND_MAP.keys()))
        sql = ('select target_kind, target_id, tag_id from %s '
               'where target_kind in (%s)')
        Ktags = _convert(pd.read_sql_query(sql % (self.knowledge_tag_table,
            ANALYSIS_KEYS), conn))
        Mtags = _convert(pd.read_sql_query(sql % (self.solution_method_tag_table,
            ANALYSIS_KEYS), conn))
        Ktags.columns = ['analysis_kind', 'analysis_id', 'ktag']
        Mtags.columns = ['analysis_kind', 'analysis_id', 'mtag']
        Atags = pd.merge(Ktags, Mtags, how='outer')
        Atags.rename(columns={'analysis_kind':'qtype'}, inplace=True)
        Atags[['qtype']] = Atags[['qtype']].astype('int64')
        Atags[['analysis_id']] = Atags[['analysis_id']].astype('int64')
        Atags['qtype'] = Atags['qtype'].map(lambda x: self.ANALYSIS_KIND_MAP[x])

        sql = 'select id analysis_id, solution_id from %s' % self.analysis_table
        X = pd.read_sql_query(sql, conn)
        return pd.merge(Atags, X)

    def get_solution_info(self):
        conn = self.conn_func()
        sql = ('select id, target_kind, target_id '
               'from %s' % self.solution_table)
        df = pd.read_sql_query(sql, conn)
        df.columns = ['solution_id', 'qtype', 'sub_qid']
        # qtype 统一到题型
        df['qtype'] = df['qtype'].map(lambda x: self.QUESTION_KIND_MAP[x])
        return df

    def get_choice_info(self):
        conn = self.conn_func()
        sql = ('select question_type, id, difficulty from %s where state '
               'in (%s)' % (self.choice_table, VALID_QUESTION_STATE))
        df = pd.read_sql_query(sql, conn)
        df.columns = ['qtype', 'qid', 'difficulty']
        df['sub_qid'] = df['qid']
        return df

    def get_blank_info(self):
        conn = self.conn_func()
        sql = ('select question_type, id, difficulty from %s where state '
               'in (%s)' % (self.blank_table, VALID_QUESTION_STATE))
        df = pd.read_sql_query(sql, conn)
        df.columns = ['qtype', 'qid', 'difficulty']
        sql = 'select id, stem_id from %s' % self.blank_question_table
        X = pd.read_sql_query(sql, conn)
        X.columns = ['sub_qid', 'qid']
        return pd.merge(df, X)

    def get_response_info(self):
        conn = self.conn_func()
        sql = ('select question_type, id, difficulty from %s where state '
               'in (%s)' % (self.response_table, VALID_QUESTION_STATE))
        df = pd.read_sql_query(sql, conn)
        df.columns = ['qtype', 'qid', 'difficulty']
        sql = 'select id, stem_id from %s' % self.response_question_table
        X = pd.read_sql_query(sql, conn)
        X.columns = ['sub_qid', 'qid']
        return pd.merge(df, X)

    def dump_question_factor(self, QTYPE, qinfo, solution,
                             analysis_info, knowledge_tree):
        res = []
        df = pd.merge(qinfo, solution[solution.qtype == QTYPE])
        df = pd.merge(df, analysis_info[analysis_info.qtype == QTYPE])
        df_group = df.groupby(['qtype', 'qid'])
        for name1, group1 in df_group:
            qtype, qid = name1
            difficulty = group1.difficulty.iloc[0]
            question_analysis = []
            for name2, group2 in group1.groupby(['sub_qid', 'solution_id']):
                sub_qid, solution_id = name2
                S = group2.sort(columns='analysis_id')[['ktag', 'mtag']]
                analysis_step = []
                f = lambda x: None if pd.isnull(x) else set(map(int, x.split('|')))
                for _, row in S.iterrows():
                    ktag, mtag = row
                    analysis_step.append((f(ktag), f(mtag)))
                question_analysis.append(analysis_step)

            qfactor = SciQuestionFactor(difficulty)
            qfactor.add_factor(question_analysis)
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
        self.remove_unapproved_questions(self.K_BLANK, self.blank_table)
        self.remove_unapproved_questions(self.K_RESPONSE, self.response_table)

        solution = self.get_solution_info()
        analysis_info = self.get_analysis_info()
        knowledge_tree = self.get_knowledge_tree()
        self.set_knowledge_tree_index(knowledge_tree)

        qinfo = self.get_choice_info()
        choice_idx = self.dump_question_factor(self.K_CHOICE, qinfo, solution,
                                               analysis_info, knowledge_tree)
        print '%s choice ok' % self.subject_name

        qinfo = self.get_blank_info()
        blank_idx = self.dump_question_factor(self.K_BLANK, qinfo, solution,
                                              analysis_info, knowledge_tree)
        print '%s blank ok' % self.subject_name

        qinfo = self.get_response_info()
        response_idx = self.dump_question_factor(self.K_RESPONSE, qinfo,
                                                 solution, analysis_info,
                                                 knowledge_tree)
        print '%s response ok' % self.subject_name

        question_list = choice_idx + blank_idx + response_idx
        origin = self.get_origin_info()
        self.dump_question_index(question_list, origin)
        print '%s question index ok' % self.subject_name
        self.set_knowledge_inv_index()
        print '%s knowledeg inverse index ok' % self.subject_name


class PhysicsQuestionFactor(PhysicsMeta, ScienceQuestionFactorBase):
    pass


class ChemistryQuestionFactor(ChemistryMeta, ScienceQuestionFactorBase):
    pass


class BiologyQuestionFactor(BiologyMeta, ScienceQuestionFactorBase):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    redis_db = redis_debug if args.debug else redis_online
    conn_func = get_banker_dev_conn if args.debug else get_banker_conn

    physics_qfactor = PhysicsQuestionFactor(conn_func, redis_db)
    physics_qfactor.calc_question_factor()
    print 'physics done.'

    chemistry_qfactor = ChemistryQuestionFactor(conn_func, redis_db)
    chemistry_qfactor.calc_question_factor()
    print 'chemistry done.'

    biology_qfactor = BiologyQuestionFactor(conn_func, redis_db)
    biology_qfactor.calc_question_factor()
    print 'biology done.'

