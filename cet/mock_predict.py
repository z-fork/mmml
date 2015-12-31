# coding: utf-8

from __future__ import absolute_import
import argparse
from multiprocessing import Pool

import pandas as pd
import numpy as np

from cet.data_split import load_data
from cet.sgd import predict
from utils.data_store import (
        redis_cet_debug, redis_cet_online,
        redis_debug, redis_online,
        get_cet_conn, get_cet_dev_conn,
        get_banker_conn, get_banker_dev_conn
)
from cet.consts import (
        CET_RECORD_PATH, BANKER_CET_RECORD_PATH,
        CET_MOCK_TEST_USER_FACTOR_KEY,
        CET_MOCK_TEST_QUESTION_FACTOR_KEY,
        CET_MOCK_TEST_MODEL_WEIGHT_KEY,
        CET_MOCK_TEST_MODEL_BIAS_WEIGHT_KEY,
        CET_MOCK_TEST_USER_ESTIMATE_KEY,
        CET_MOCK_TEST_QUESTION_ESTIMATE_KEY,
        CET_MOCK_TEST_SCORE_MEAN,
        CET_MOCK_TEST_SCORE_SD
)
# TODO 把代码中各种常量用已有变量替换
from utils.consts import (
        EXAM_KIND_MAP, EXAM_KIND_DEFAULT,
        EXAM_KIND_CET4, EXAM_KIND_CET6,
        K_SHORT_DIALOG_QUESTION, K_LONG_DIALOG_QUESTION,
        K_ESSAY_QUESTION, K_READING_QUESTION
)
from english.consts import ENGLISH_QUESTION_INV_INDEX

Q_WEIGHT = {
        K_SHORT_DIALOG_QUESTION:8,
        K_LONG_DIALOG_QUESTION:7,
        K_ESSAY_QUESTION:10,
        K_READING_QUESTION:20
}


def get_question_factor(conn_func, redis_db):
    res = []
    for exam_kind in (EXAM_KIND_CET4, EXAM_KIND_CET6):
        key_pattern = ENGLISH_QUESTION_INV_INDEX % (exam_kind, '*')
        keys = redis_db.keys(key_pattern)
        for key in keys:
            qtype = int(key.split('/')[-1])
            qids = map(int, redis_db.lrange(key, 0, -1))
            res.extend([(qtype, qid, exam_kind) for qid in qids])
    qfactor = pd.DataFrame(res)
    qfactor.columns = ['qtype', 'qid', 'exam_kind']

    conn = conn_func()
    sql = 'select target_kind, target_id, exam_type from origin'
    A = pd.read_sql_query(sql, conn)
    A.columns = ['qtype', 'qid', 'exam_type']
    return pd.merge(A, qfactor)


def get_questions(conn_func, qfactor, context_id, stem_table, question_table):
    conn = conn_func()
    sql = 'select question_type, id from %s' % stem_table
    stem_df = pd.read_sql_query(sql, conn)
    stem_df.columns = ['qtype', 'qid']
    sql = 'select %s, question_type, id, difficulty from %s'
    question_df = pd.read_sql_query(sql % (context_id, question_table), conn)
    question_df.columns = ['qid', 'subtype', 'subid', 'difficulty']
    df = pd.merge(stem_df, question_df)
    return pd.merge(df, qfactor)


def get_question_info(conn_func, banker_conn_func, redis_db):
    qfactor = get_question_factor(conn_func, redis_db)
    listen = get_questions(banker_conn_func, qfactor, 'stem_id',
                           'listen_choice_stem', 'listen_choice_question')
    reading = get_questions(banker_conn_func, qfactor, 'context_id',
                            'context_choice_stem', 'context_choice_question')
    df = pd.concat([listen, reading])
    df_cet4 = df[(df.exam_kind == 1) & (df.exam_type == 1)].drop('exam_kind', axis=1)
    df_cet6 = df[(df.exam_kind == 2) & (df.exam_type == 3)].drop('exam_kind', axis=1)
    return df_cet4, df_cet6, df


def get_record(fpath):
    record = load_data(fpath)
    user_record = {}
    for _, row in record.iterrows():
        uid, qid, status, difficulty = row
        user_record.setdefault(uid, {})[qid] = status
    return user_record


def get_user_profile(conn_func):
    conn = conn_func()
    sql = 'select id, grade_id, exam from user_profile'
    A = pd.read_sql_query(sql, conn)
    A.columns = ['uid', 'grade_id', 'exam_type']
    res = {}
    for _, row in A.iterrows():
        uid, grade_id, exam_type = row
        exam_kind = EXAM_KIND_MAP.get(grade_id, {}).get(exam_type, EXAM_KIND_DEFAULT)
        res[uid] = exam_kind
    return res


def load_fac(redis_db, key):
    fac = redis_db.lrange(key, 0, -1)
    return np.array(map(float, fac))


def mock_predict(uid, record, qinfo, w, w0, redis_db):
    res = {}
    user_key = CET_MOCK_TEST_USER_FACTOR_KEY % uid
    ufac = load_fac(redis_db, user_key)

    for _, row in qinfo.iterrows():
        qtype, qid, subtype, subid, difficulty, exam_type = row
        _qid = str(subtype) + ':' + str(subid)
        if _qid in record:
            y = record[_qid]
        else:
            item_key = CET_MOCK_TEST_QUESTION_FACTOR_KEY % _qid
            # FIXME 不知道为什么会有不存在的 item_key
            if not redis_db.exists(item_key):
                continue
            ifac = load_fac(redis_db, item_key)
            y = predict(ufac, ifac, w, w0, difficulty)
            y = 1 if y >= 0.5 else 0
        res[_qid] = y
    return res


def dump_user_prediction(user_record, user_profile, redis_db):
    stat = {}
    for uid, record in user_record.iteritems():
        user_key = CET_MOCK_TEST_USER_ESTIMATE_KEY % uid
        res = {}
        for qid, y in record.iteritems():
            subtype, subid = qid.split(':')
            res.setdefault(subtype, []).append(y)
        for subtype, ys in res.iteritems():
            res[subtype] = np.mean(ys)
        estimate = sum([Q_WEIGHT[int(k)] * v for k, v in res.iteritems()])
        estimate = int(estimate / sum(Q_WEIGHT.values()) * 100)
        redis_db.set(user_key, estimate)
        exam_kind = user_profile[uid]
        stat.setdefault(exam_kind, []).append(estimate)

    for exam_kind, scores in stat.iteritems():
        mean = np.mean(scores)
        sd = np.std(scores)
        redis_db.set(CET_MOCK_TEST_SCORE_MEAN % exam_kind, mean)
        redis_db.set(CET_MOCK_TEST_SCORE_SD % exam_kind, sd)


def dump_item_prediction(item_record, qinfo, redis_db):
    qid_map = {}
    combine_id = lambda x, y: str(x) + ':' + str(y)
    for _, row in qinfo.iterrows():
        qtype, qid, subtype, subid, diff, exam_type, exam_kind = row
        qid_map[combine_id(subtype, subid)] = combine_id(qtype, qid)

    res = {}
    for qid, record in item_record.iteritems():
        parent_id = qid_map[qid]
        res.setdefault(parent_id, []).append(np.mean(record.values()))
    for parent_id, estimates in res.iteritems():
        item_key = CET_MOCK_TEST_QUESTION_ESTIMATE_KEY % parent_id
        redis_db.set(item_key, np.mean(estimates))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--banker', action='store_true')
    args = parser.parse_args()
    conn_func = get_cet_dev_conn if args.debug else get_cet_conn
    banker_conn_func = get_banker_dev_conn if args.debug else get_banker_conn
    if args.banker:
        conn_func = banker_conn_func
        redis_db = redis_debug if args.debug else redis_online
    else:
        redis_db = redis_cet_debug if args.debug else redis_cet_online

    fpath = BANKER_CET_RECORD_PATH if args.banker else CET_RECORD_PATH
    user_record = get_record(fpath)
    df_cet4, df_cet6, qinfo = get_question_info(conn_func, banker_conn_func,
                                                redis_db)
    user_profile = get_user_profile(conn_func)

    w = load_fac(redis_db, CET_MOCK_TEST_MODEL_WEIGHT_KEY)
    w0 = float(redis_db.get(CET_MOCK_TEST_MODEL_BIAS_WEIGHT_KEY))

    def _predict(x):
        uid, record = x
        exam_kind = user_profile.get(uid, EXAM_KIND_DEFAULT)
        if exam_kind == EXAM_KIND_CET4:
            qinfo = df_cet4
        elif exam_kind == EXAM_KIND_CET6:
            qinfo = df_cet6
        else:
            return None
        y = mock_predict(uid, record, qinfo, w, w0, redis_db)
        return (uid, y)
    parallel_pool = Pool(12)
    res = parallel_pool.map(_predict, user_record.items())
    user_record = dict([t for t in res if t != None])

    item_record = {}
    for uid, record in user_record.iteritems():
        for qid, y in record.iteritems():
            item_record.setdefault(qid, {})[uid] = y

    dump_user_prediction(user_record, user_profile, redis_db)
    dump_item_prediction(item_record, qinfo, redis_db)

