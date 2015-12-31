# coding: utf-8

from __future__ import absolute_import
import argparse

import numpy as np
import pandas as pd

from utils.data_store import (
        get_banker_conn, get_banker_dev_conn,
        redis_online, redis_debug
)
from utils.consts import QUESTION_SUBTYPE_MAP, CONF_MAP
from english.consts import ENGLISH_USER_FACTOR_KEY

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


# oh, why the data structure are designed like this?
def get_record_factor(conn_func, parent_kind):
    conn = conn_func()
    qtype = QUESTION_SUBTYPE_MAP[parent_kind]
    sql = ('select question_type,question_id,user_id,status,date '
           'from question_record_detail where status!=0 and question_type=%s')
    record = pd.read_sql_query(sql, conn, params=(qtype,))
    record.rename(columns = {'question_type':'qtype',
                             'question_id':'qid',
                             'user_id':'uid'}, inplace=True)

    sql = ('select target_kind, target_id, tag_id from knowledge_tag '
           'where target_kind = %s')
    ktags = pd.read_sql_query(sql, conn, params=(qtype,))
    ktags.columns = ['qtype', 'qid', 'tag_id']

    conf = CONF_MAP[parent_kind]['question_conf']
    table_name = conf['table']
    qid_name = conf['qid']
    sql = ('select question_type,%s,difficulty from %s '
           'where question_type=%s' % (qid_name, table_name, qtype))
    diff = pd.read_sql_query(sql, conn)
    if len(diff) == 0:
        return None
    diff.columns = ['qtype', 'qid', 'difficulty']

    def _convert_fac(x):
        res = zip(map(str, x.tag_id), map(str, x.difficulty))
        return "|".join(['%s:%s' % (t, d) for t, d in res])

    fac = pd.merge(ktags, diff).groupby(['qtype', 'qid']
            ).apply(_convert_fac).reset_index()
    fac.columns = ['qtype', 'qid', 'score']

    return pd.merge(record, fac)[['uid', 'status', 'score']]


def calc_user_factor(conn_func):
    records = []
    for parent_kind in CONF_MAP.keys():
        record = get_record_factor(conn_func, parent_kind)
        if record is None or record.empty:
            continue
        records.append(record)
    records = pd.concat(records)

    def _calc_bayes(df):
        ufac = {}
        for idx, row in df.iterrows():
            uid, status, score = row
            correct = status - 1  # 1/2 -> 0/1, 做错/做对
            tags = [x.split(':') for x in score.split('|')]
            tags = [(int(tag), int(d)) for tag, d in tags]
            for tag, d in tags:
                if tag not in ufac:
                    ufac[tag] = population_pri.copy()
                px = np.array(priori[:, d-1]).T
                ufac[tag] = ufac[tag] * (correct * px + (1 - correct) * (1 - px))
        u_score = []
        for tag, fac in ufac.iteritems():
            u_score.append(str(tag) + ':' + str(fac.argmax() + 1))
        return "|".join(u_score)

    user_factor = records.groupby(['uid']).apply(_calc_bayes).reset_index()
    if len(user_factor) == 0:
        user_factor = pd.DataFrame()
    user_factor.columns = ['uid', 'score']
    return user_factor


def dump_user_factor(redis_db, user_factor):
    if len(user_factor) == 0:
        return
    for idx, row in user_factor.iterrows():
        uid, score = row
        key = ENGLISH_USER_FACTOR_KEY % uid
        redis_db.set(key, score)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action = 'store_true')
    args = parser.parse_args()

    conn_func = get_banker_dev_conn if args.debug else get_banker_conn
    redis_db = redis_debug if args.debug else redis_online

    user_factor = calc_user_factor(conn_func)
    dump_user_factor(redis_db, user_factor)
    print 'english user factor done'

