# coding: utf-8

from __future__ import absolute_import
import argparse

import numpy as np
import pandas as pd

from utils.data_store import (redis_online, redis_debug,
        get_banker_conn, get_banker_dev_conn)
from utils.meta import AlgMeta
from utils.tools import redis_scan
from art.meta import ChineseMeta, HistoryMeta, GeographyMeta, PoliticsMeta
from art.knowledge_model import load_vector
from science.consts import QUESTION_TYPE_PRACTICE

# 做题先验，难度数值是 1～5
# e.g.水平为y的做难度为x对的概率 priori[y-1, x-1]
# TODO: 改成利用数据估计
priori = np.mat([
    [0.6, 0.4, 0.25, 0.1, 0.02],
    [0.7, 0.6, 0.4, 0.25, 0.15],
    [0.85, 0.75, 0.6, 0.45, 0.3],
    [0.95, 0.9, 0.75, 0.6, 0.4],
    [0.99, 0.95, 0.8, 0.75, 0.65]
])

# 人群先验
#population_pri = {1:0.15, 2:0.2, 3:0.3, 4:0.2, 5:0.15}
population_pri = np.array([0.15, 0.2, 0.3, 0.2, 0.15])

VALID_RECORD_TYPE = [QUESTION_TYPE_PRACTICE]
VALID_RECORD_TYPE = ",".join(map(str, VALID_RECORD_TYPE))


class ArtUserFactorBase(AlgMeta):

    def extract_tags(self, key):
        ktag_str, rktag_str, diff = self.redis_db.lrange(key, 0, -1)
        def _extractor(x):
            vec = load_vector(x)
            res = [":".join([str(tag), diff]) for tag in vec]
            return "|".join(res)
        return map(_extractor, [ktag_str, rktag_str])

    def get_question_record(self):
        sql = ('select target_kind, target_id, user_id, n_correct, n_wrong '
               'from generic_question_record where subject_id = %s and '
               'record_type in (%s)' % (self.subject_id, VALID_RECORD_TYPE))
        conn = self.conn_func()
        record = pd.read_sql_query(sql, conn)
        record.columns = ['qtype', 'qid', 'uid', 'n_correct', 'n_wrong']

        qtypes = [self.K_CHOICE]
        if self.subject_name == 'chinese':
            qtypes.append(self.K_READING)
        keys = set()
        fields = self.redis_db.hkeys(self.QUESTION_INV_INDEX)
        for field in fields:
            qtype = int(field.split(':')[1])  # exam_type, qtype, module_id
            if qtype in qtypes:
                qids = self.redis_db.hget(self.QUESTION_INV_INDEX, field)
                qids = qids.split('|')
                for qid in qids:
                    keys.add(self.QUESTION_FACTOR_KEY % (qtype, qid))

        qfactor_dict = {}
        for key in keys:
            kscore, rkscore = self.extract_tags(key)
            qid = int(key.split('/')[-1])
            qfactor_dict[qid] = kscore

        res = []
        for _, row in record.iterrows():
            qtype, qid, uid, n_correct, n_wrong = map(int, row)
            if n_correct + n_wrong == 0: continue # 过滤没有实际做的题
            if qid not in qfactor_dict: continue
            kscore = qfactor_dict[qid]
            correct = float(n_correct) / (n_correct + n_wrong)
            res.append((uid, correct, kscore))
        if len(res) == 0:
            res = pd.DataFrame()
        else:
            res = pd.DataFrame(res)
            res.columns = ['uid', 'correct', 'kscore']
        return res

    def calc_user_factor(self, records):
        if len(records) == 0:
            return pd.DataFrame()

        def _calc_bayes(df):
            ufac = {}
            for _, row in df.iterrows():
                uid, correct, score = row
                if not score: continue
                tags = [x.split(':') for x in score.split('|')]
                tags = [(int(tag), int(d)) for tag, d in tags]
                for tag, d in tags:
                    if tag not in ufac:
                        ufac[tag] = population_pri.copy()
                    px = np.array(priori[:, d-1]).T
                    ratio = (correct * px + (1 - correct) * (1 - px))
                    ufac[tag] = ufac[tag] * ratio
            u_score = []
            for tag, fac in ufac.iteritems():
                u_score.append(str(tag) + ':' + str(fac.argmax() + 1))
            return "|".join(u_score)

        k_factor = records[['uid', 'correct', 'kscore']].groupby(
                ['uid']).apply(_calc_bayes).reset_index()
        k_factor.columns = ['uid', 'kscore']
        user_factor = k_factor
        if len(user_factor) == 0:
            user_factor = pd.DataFrame()
        return user_factor

    def dump_user_factor(self, user_factor):
        if len(user_factor) == 0:
            return
        for idx, row in user_factor.iterrows():
            uid, kscore = row
            key = self.USER_FACTOR_KEY % uid
            self.redis_db.delete(key)
            # 考虑后续扩展性, 此处依然用 redis list
            self.redis_db.rpush(key, kscore)

    def flush_user_factor(self):
        key_pattern = '/alg/%s/user_factor/*' % self.subject_name
        keys = redis_scan(redis_db, key_pattern)
        pipe = self.redis_db.pipeline()
        for key in keys:
            pipe.delete(key)
        pipe.execute()

    def compute_user_factor(self, flush_old_factor):
        records = self.get_question_record()
        if flush_old_factor:
            self.flush_user_factor()
            print 'flush all old %s user factor' % self.subject_name
        user_factor = self.calc_user_factor(records)
        self.dump_user_factor(user_factor)

class ChineseUserFactor(ChineseMeta, ArtUserFactorBase):
    pass


class HistoryUserFactor(HistoryMeta, ArtUserFactorBase):
    pass


class GeographyUserFactor(GeographyMeta, ArtUserFactorBase):
    pass


class PoliticsUserFactor(PoliticsMeta, ArtUserFactorBase):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action = 'store_true')
    parser.add_argument('--flush_old_factor', action='store_true')
    args = parser.parse_args()
    redis_db = redis_debug if args.debug else redis_online
    conn_func = get_banker_dev_conn if args.debug else get_banker_conn

    chinese_user_factor = ChineseUserFactor(conn_func, redis_db)
    chinese_user_factor.compute_user_factor(args.flush_old_factor)
    print 'chinese done.'

    history_user_factor = HistoryUserFactor(conn_func, redis_db)
    history_user_factor.compute_user_factor(args.flush_old_factor)
    print 'history done.'

    geography_user_factor = GeographyUserFactor(conn_func, redis_db)
    geography_user_factor.compute_user_factor(args.flush_old_factor)
    print 'geography done.'

    politics_user_factor = PoliticsUserFactor(conn_func, redis_db)
    politics_user_factor.compute_user_factor(args.flush_old_factor)
    print 'politics done.'

