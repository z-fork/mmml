# coding: utf-8

import argparse

import numpy as np

from utils.data_store import (redis_online, redis_debug,
        get_banker_conn, get_banker_dev_conn)
from utils.consts import (
        APP_QUESTION_KIND_ALL,
        APP_QUESTION_KIND_READ,
        APP_QUESTION_KIND_CLOZE,
        APP_QUESTION_KIND_SINGLE,
        APP_QUESTION_KIND_LISTEN
)


CAPABILITY_RANK_QUANTILE = '/alg/capability_rank_quantile/%s'


def set_capability_rank_quantile(app_question_kind, redis_db, conn_func):
    quantile_nodes = range(100)
    conn = conn_func()
    cursor = conn.cursor()
    if app_question_kind == APP_QUESTION_KIND_ALL:
        cursor.execute('select sum(value) from capability group by user_id')
        caps = np.array([int(v) for v, in cursor.fetchall()])
    else:
        cursor.execute('select value from capability where '
                       'question_type=%s', [app_question_kind])
        caps = np.array([v for v, in cursor.fetchall()])
    if len(caps) == 0:
        caps = np.array([0])
    quantiles = []
    for q in quantile_nodes:
        quantiles.append((q, np.percentile(caps, q)))
    key = CAPABILITY_RANK_QUANTILE % str(app_question_kind)
    redis_db.hmset(key, dict(quantiles))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action = 'store_true')
    args = parser.parse_args()
    redis_db = redis_debug if args.debug else redis_online
    conn_func = get_banker_dev_conn if args.debug else get_banker_conn

    set_capability_rank_quantile(APP_QUESTION_KIND_ALL, redis_db, conn_func)
    set_capability_rank_quantile(APP_QUESTION_KIND_READ, redis_db, conn_func)
    set_capability_rank_quantile(APP_QUESTION_KIND_CLOZE, redis_db, conn_func)
    set_capability_rank_quantile(APP_QUESTION_KIND_SINGLE, redis_db, conn_func)
    set_capability_rank_quantile(APP_QUESTION_KIND_LISTEN, redis_db, conn_func)

