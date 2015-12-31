# coding: utf-8

import argparse

import numpy as np

from utils.data_store import (redis_online, redis_debug,
        get_banker_conn, get_banker_dev_conn)
from utils.consts import MODULE_ALL


MATH_CAPABILITY_RANK_QUANTILE = '/alg/math/capability_rank_quantile/%s'


def set_capability_rank_quantile(module_id, redis_db, conn_func):
    quantile_nodes = range(100)
    conn = conn_func()
    cursor = conn.cursor()
    if module_id == MODULE_ALL:
        cursor.execute('select sum(value) from math_capability group by user_id')
        caps = np.array([int(v) for v, in cursor.fetchall()])
    else:
        cursor.execute('select value from math_capability where module_id=%s', [module_id])
        caps = np.array([v for v, in cursor.fetchall()])
    if len(caps) == 0:
        caps = np.array([0])
    quantiles = []
    for q in quantile_nodes:
        quantiles.append((q, np.percentile(caps, q)))
    key = MATH_CAPABILITY_RANK_QUANTILE % str(module_id)
    redis_db.hmset(key, dict(quantiles))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action = 'store_true')
    args = parser.parse_args()
    redis_db = redis_debug if args.debug else redis_online
    conn_func = get_banker_dev_conn if args.debug else get_banker_conn

    set_capability_rank_quantile(MODULE_ALL, redis_db, conn_func)
    conn = conn_func()
    cursor = conn.cursor()
    cursor.execute('select id from math_knowledge where level = 1')
    module_ids = [kid for kid, in cursor.fetchall()]
    for module_id in module_ids:
        set_capability_rank_quantile(module_id, redis_db, conn_func)

