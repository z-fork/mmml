# coding: utf-8

from __future__ import absolute_import
import argparse
from operator import itemgetter

import pandas as pd
import numpy as np

from utils.data_store import (flush_redis,
        redis_cet_debug, redis_cet_online,
        redis_debug, redis_online
)
from cet.sgd import irt_process
from cet.consts import (
        CET_RECORD_PATH, BANKER_CET_RECORD_PATH,
        CET_MOCK_TEST_USER_FACTOR_KEY,
        CET_MOCK_TEST_QUESTION_FACTOR_KEY,
        CET_MOCK_TEST_MODEL_WEIGHT_KEY,
        CET_MOCK_TEST_MODEL_BIAS_WEIGHT_KEY
)
from cet.data_split import make_data_set


# user_fac, item_fac, w, w0, accuracy
def merge_result(result_list):

    def _merge_fac_map(fac_map_list):
        ans = {}
        for fac_map in fac_map_list:
            for _id, fac in fac_map.iteritems():
                ans.setdefault(_id, []).append(fac)
        for _id, fac_list in ans.iteritems():
            ans[_id] = np.mean(fac_list, axis=0)
        return ans

    user_fac = _merge_fac_map(map(itemgetter(0), result_list))
    item_fac = _merge_fac_map(map(itemgetter(1), result_list))
    w = np.mean(map(itemgetter(2), result_list), axis=0)
    w0 = np.mean(map(itemgetter(3), result_list))
    accuracy = np.mean(map(itemgetter(4), result_list))
    return user_fac, item_fac, w, w0, accuracy


def dump_result(result, redis_db):
    user_fac, item_fac, w, w0, accuracy = result
    print 'accuracy: %.4f' % accuracy
    for uid, fac in user_fac.iteritems():
        key = CET_MOCK_TEST_USER_FACTOR_KEY % uid
        flush_redis(redis_db, key, list(fac))
    for qid, fac in item_fac.iteritems():
        key = CET_MOCK_TEST_QUESTION_FACTOR_KEY % qid
        flush_redis(redis_db, key, list(fac))
    flush_redis(redis_db, CET_MOCK_TEST_MODEL_WEIGHT_KEY, list(w))
    redis_db.set(CET_MOCK_TEST_MODEL_BIAS_WEIGHT_KEY, w0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--banker', action='store_true')
    parser.add_argument('--cross_validation', action='store_true')
    args = parser.parse_args()
    if args.banker:
        redis_db = redis_debug if args.debug else redis_online
    else:
        redis_db = redis_cet_debug if args.debug else redis_cet_online

    # TODO 改成用 rpy2 交互，或者抽空整个改成 python
    fpath = BANKER_CET_RECORD_PATH if args.banker else CET_RECORD_PATH
    data = make_data_set(fpath, kfold=5)
    result = []
    if args.cross_validation:
        for i in xrange(len(data)):
            print 'Round %d' % (i + 1)
            train = pd.concat(data[:i] + data[i+1:])
            test = data[i]
            result.append(irt_process(train, test))
        result = merge_result(result)
    else:
        train = pd.concat(data[:-1])
        test = data[-1]
        result = irt_process(train, test)
    dump_result(result, redis_db)

