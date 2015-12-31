# coding: utf-8

from __future__ import absolute_import
import argparse

from utils.data_store import (
    redis_cet_debug, redis_cet_online,
    get_cet_dev_conn, get_cet_read_conn
)
from cet_new.dump_feature import (
    dump_user_feature, dump_question_feature,
    dump_practice_log, dump_question_inv_index,
    CET_PRACTICE_LOG_PATH
)
from cet_new.data_prepare import (
    get_user_profile,
    get_question_info,
    get_valid_practice_log
)
from cet_new.model_training import get_train_data, logistic_regression
from cet_new.mock_test import MockTestEstimation, dump_estimation


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    conn_func = get_cet_dev_conn if args.debug else get_cet_read_conn
    redis_db = redis_cet_debug if args.debug else redis_cet_online
    suffix = 'dev' if args.debug else 'online'
    practice_log_path = CET_PRACTICE_LOG_PATH % suffix

    # 计算有效练题 log
    user_profile = get_user_profile(conn_func)
    qinfo = get_question_info(conn_func)
    practice_log, user_avg, item_avg = get_valid_practice_log(conn_func, qinfo)

    # 计算 user_feature/question_feature, 连同练题记录一起存入 redis 和硬盘
    user_feature = dump_user_feature(redis_db, user_profile, user_avg)
    question_feature = dump_question_feature(redis_db, qinfo, item_avg)
    dump_practice_log(practice_log, user_feature, question_feature, practice_log_path)
    dump_question_inv_index(conn_func, redis_db, qinfo)
    print 'feature dump ok'

    # 训练 LR 模型
    data = get_train_data(practice_log_path)
    model = logistic_regression(data)
    print 'model training ok'

    # 计算离线估分
    estimator = MockTestEstimation(args.debug, model)
    estimation = estimator.calc_estimation(redis_db, practice_log_path)
    dump_estimation(redis_db, estimation)
    print 'estimation calc ok'

