# coding: utf-8

from __future__ import absolute_import
import argparse

import numpy as np

from utils.data_store import (redis_cet_debug, redis_cet_online,
        get_cet_conn, get_cet_dev_conn)
from utils.consts import (
        APP_QUESTION_KIND_ALL,
        APP_QUESTION_KIND_READ,
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
    redis_db = redis_cet_debug if args.debug else redis_cet_online
    conn_func = get_cet_dev_conn if args.debug else get_cet_conn

    set_capability_rank_quantile(APP_QUESTION_KIND_ALL, redis_db, conn_func)
    set_capability_rank_quantile(APP_QUESTION_KIND_READ, redis_db, conn_func)
    set_capability_rank_quantile(APP_QUESTION_KIND_LISTEN, redis_db, conn_func)

