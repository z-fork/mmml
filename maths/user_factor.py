# coding: utf-8

from __future__ import absolute_import
import argparse

import numpy as np
import pandas as pd

from utils.data_store import (
    redis_online, redis_debug,
    get_banker_conn, get_banker_dev_conn
)
from utils.tools import redis_scan
from utils.consts import SUBJECT_MATH
from maths.consts import (
    QUESTION_TYPE_REVIEW, K_MATH_CHOICE, MATH_USER_FACTOR_KEY,
    MATH_QUESTION_FACTOR_KEY, MATH_QUESTION_INV_INDEX
)
from maths.knowledge_model import load_matrix

# copy from english user_factor (TODO) 数学单独处理
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


def extract_tags(redis_db, key):
    k_str, m_str, k_m_str, diff = redis_db.lrange(key, 0, -1)
    def _extractor(x):
        mat = load_matrix(x)
        res = [":".join([str(tag), diff]) for tag in mat.keys()]
        return "|".join(res)
    return map(_extractor, [k_str, m_str])


def load_adaptive_record(conn_func):
    conn = conn_func()
    sql = ('select target_kind, target_id, user_id, n_correct, '
           'n_wrong, record_time from adaptive_question_record '
           'where subject_id = %s' % SUBJECT_MATH)
    record = pd.read_sql_query(sql, conn)
    record.columns = ['qtype', 'qid', 'uid', 'n_correct', 'n_wrong', 'record_time']
    return record


def load_question_record(conn_func):
    conn = conn_func()
    sql = ('select target_kind, target_id, user_id, n_correct, '
           'n_wrong, record_time from math_question_record '
           'where record_type != %s' % QUESTION_TYPE_REVIEW)
    record = pd.read_sql_query(sql, conn)
    record.columns = ['qtype', 'qid', 'uid', 'n_correct', 'n_wrong', 'record_time']
    return record


def get_practice_record(redis_db, record):

    def _pick_latest(df):
        res = df.sort('record_time').tail(1)
        return res[['n_correct', 'n_wrong']]
    record = record.groupby(['qtype', 'qid', 'uid']).apply(_pick_latest).reset_index()
    record = record[(record.n_correct != 0) | (record.n_wrong != 0)]
    record = record[['qtype', 'qid', 'uid', 'n_correct', 'n_wrong']]

    keys = set()
    fields = redis_db.hkeys(MATH_QUESTION_INV_INDEX)
    for field in fields:
        qtype = int(field.split(':')[1])  # exam_type, qtype, module_id
        if qtype == K_MATH_CHOICE:
            qids = redis_db.hget(MATH_QUESTION_INV_INDEX, field)
            qids = qids.split('|')
            for qid in qids:
                keys.add(MATH_QUESTION_FACTOR_KEY % (qtype, qid))

    qfactor_dict = {}
    for key in keys:
        kscore, mscore = extract_tags(redis_db, key)
        qid = int(key.split('/')[-1])
        qfactor_dict[qid] = (kscore, mscore)

    res = []
    for _, row in record.iterrows():
        qtype, qid, uid, n_correct, n_wrong = map(int, row)
        if qid not in qfactor_dict:
            continue
        kscore, mscore = qfactor_dict[qid]
        res.append((uid, n_correct, kscore, mscore))
    res = pd.DataFrame(res, columns=['uid', 'correct', 'kscore', 'mscore'])
    return res


def calc_user_factor(redis_db, records):

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
                ufac[tag] = ufac[tag] * (correct * px + (1 - correct) * (1 - px))
        u_score = []
        for tag, fac in ufac.iteritems():
            u_score.append('%s:%s' % (tag, fac.argmax() + 1))
        return "|".join(u_score)

    k_factor = records[['uid', 'correct', 'kscore']].groupby(
            ['uid']).apply(_calc_bayes).reset_index()
    k_factor.columns = ['uid', 'kscore']
    m_factor = records[['uid', 'correct', 'mscore']].groupby(
            ['uid']).apply(_calc_bayes).reset_index()
    m_factor.columns = ['uid', 'mscore']
    user_factor = pd.merge(k_factor, m_factor)
    if len(user_factor) == 0:
        user_factor = pd.DataFrame()
    return user_factor


def dump_user_factor(redis_db, user_factor):
    if len(user_factor) == 0:
        return
    for idx, row in user_factor.iterrows():
        uid, kscore, mscore = row
        key = MATH_USER_FACTOR_KEY % uid
        redis_db.delete(key)
        redis_db.rpush(key, kscore, mscore)


def flush_user_factor(redis_db):
    key_pattern = '/alg/math/user_factor/*'
    keys = redis_scan(redis_db, key_pattern)
    pipe = redis_db.pipeline()
    for key in keys:
        pipe.delete(key)
    pipe.execute()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--flush_old_factor', action='store_true')
    args = parser.parse_args()
    redis_db = redis_debug if args.debug else redis_online
    conn_func = get_banker_dev_conn if args.debug else get_banker_conn

    adaptive_record = load_adaptive_record(conn_func)
    question_record = load_question_record(conn_func)
    record = pd.concat([adaptive_record, question_record])

    practice_record = get_practice_record(redis_db, record)
    if args.flush_old_factor:
        flush_user_factor(redis_db)
        print 'flush all old math user factor'
    user_factor = calc_user_factor(redis_db, practice_record)
    dump_user_factor(redis_db, user_factor)
    print 'math user factor done'

