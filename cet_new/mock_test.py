# coding: utf-8

from __future__ import absolute_import
import json
from operator import itemgetter

import numpy as np
import pandas as pd
from patsy import dmatrix
from multiprocessing import Pool

from utils.data_store import redis_cet_debug, redis_cet_online
from utils.tools import random_sample
from cet_new.dump_feature import CET_USER_FEATURE_KEY, CET_QUESTION_FEATURE_KEY
from cet_new.model_training import get_design_info
from cet_new.consts import (
    EXAM_CET4, EXAM_CET6,
    K_COMPOSITION,
    K_SHORT_DIALOG,
    K_LONG_DIALOG,
    K_ESSAY,
    K_LISTEN_DICTATION,
    K_SELECT_WORD,
    K_PARAGRAPH_INFO_MATCH,
    K_READING_IN_DEPTH,
    K_TRANSLATION
)

Q_WEIGHT = {
    K_COMPOSITION: 15,
    K_SHORT_DIALOG: 8,
    K_LONG_DIALOG: 7,
    K_ESSAY: 10,
    K_LISTEN_DICTATION: 10,
    K_SELECT_WORD: 5,
    K_PARAGRAPH_INFO_MATCH: 10,
    K_READING_IN_DEPTH: 20,
    K_TRANSLATION: 15
}

column_names = ['uid', 'qtype', 'qid', 'sub_id', 'correct',
                'seconds', 'gender', 'location_id', 'u_avg_time',
                'u_avg_correct', 'n_question', 'diff', 'exam_type',
                'q_avg_time', 'q_avg_correct']

# exam_type, uid
CET_MOCK_TEST_USER_ESTIMATE_KEY = '/alg/cet/mock_test/user_estimate/%s/%s'
# 为了出题方便，这里的 field 为大题 qtype:qid 的形式
CET_MOCK_TEST_QUESTION_ESTIMATE_KEY = '/alg/cet/mock_test/question_estimate'
CET_MOCK_TEST_SCORE_MEAN = '/alg/cet/mock_test/score_mean/%s' # exam_type
CET_MOCK_TEST_SCORE_SD = '/alg/cet/mock_test/score_sd/%s' # exam_type


def get_valid_user_set(practice_log_path):
    df = pd.read_csv(practice_log_path, sep='\t', header=None)
    df.columns = column_names
    return set(df.uid)


def load_question_feature(redis_db, qtype, qid, sub_id):
    field = '%s:%s:%s' % (qtype, qid, sub_id)
    question_feature = redis_db.hget(CET_QUESTION_FEATURE_KEY, field)
    question_feature = json.loads(question_feature)
    n_question, diff, exam_type, q_avg_time, q_avg_correct = question_feature
    n_question, exam_type = int(n_question), int(exam_type)
    diff, q_avg_time, q_avg_correct = map(float, [diff, q_avg_time, q_avg_correct])
    return (n_question, diff, exam_type, q_avg_time, q_avg_correct)


def lr_predict(param):
    '''
    对一组数据应用 LR 模型得到对于小题的对错预测

    Args:
        param: 模型参数, 包括
               debug, q_key, valid_user_set, exist_keys, model, data_path

    Returns:
        ans: 包含预测结果的 pd.DataFrame
             各列依次为 uid, qtype, qid, sub_id, yhat
             其中 yhat 就是预测的结果列
    '''
    debug, q_key, valid_user_set, exist_keys, model, data_path = param
    # redis_db 无法被 pickle 序列化, 所以只能在函数内部得到 redis_db
    redis_db = redis_cet_debug if debug else redis_cet_online
    # 同理, 因为 patsy 的 DesignInfo 无法序列化, 所以只能在并行函数内部来拿
    design_info = get_design_info(data_path)
    # 如果取全部用户计算时间太长, 这里对一道题目只抽样部分用户
    user_list = random_sample(list(valid_user_set), 100)
    qtype, qid, sub_id = map(int, q_key.split(':'))
    question_feature = load_question_feature(redis_db, qtype, qid, sub_id)
    n_question, diff, exam_type, q_avg_time, q_avg_correct = question_feature

    data = []
    for uid in user_list:
        k = '%s:%s:%s:%s' % (uid, qtype, qid, sub_id)
        if k in exist_keys:
            continue
        user_feature = redis_db.get(CET_USER_FEATURE_KEY % uid)
        gender, location_id, u_score = json.loads(user_feature)
        gender = int(gender)
        location_id = int(location_id)
        u_avg_time, u_avg_correct = map(float, u_score[str(qtype)])
        seconds = (u_avg_time + q_avg_time) / 2.0
        data.append([uid, qtype, qid, sub_id, 0.5, seconds, gender, location_id,
                     u_avg_time, u_avg_correct, n_question, diff, exam_type,
                     q_avg_time, q_avg_correct])
    data = pd.DataFrame(data, columns=column_names)
    X = dmatrix(design_info, data)

    yhat = map(itemgetter(1), model.predict_proba(X))
    ans = data.iloc[:, range(4)].copy()  # 取 uid, qtype, qid, sub_id
    ans.loc[:, 'yhat'] = pd.Series(yhat, index=ans.index)
    return ans


class MockTestEstimation(object):
    '''
    LR 的 model 不能每次都在并行函数内部生成
    为了避免奇怪的序列化错误智能用 class 的方式来包装
    '''

    def __init__(self, debug, model):
        self.debug = debug
        self.model = model

    def calc_estimation(self, redis_db, practice_log_path):
        estimation = dict()
        # 将所有做题对错结果存储到 estimation
        # 已做过的存真实结果, 没做过的存预测结果
        fin = open(practice_log_path)
        for line in fin:
            uid, qtype, qid, sub_id, correct = line.strip().split('\t')[:5]
            k = '%s:%s:%s:%s' % (uid, qtype, qid, sub_id)
            estimation[k] = int(float(correct))
        fin.close()
        exist_keys = set(estimation.keys())

        valid_users = get_valid_user_set(practice_log_path)
        q_keys = redis_db.hkeys(CET_QUESTION_FEATURE_KEY)
        params = []
        for q_key in q_keys:
            param = (self.debug, q_key, valid_users, exist_keys, self.model, practice_log_path)
            params.append(param)

        parallel_pool = Pool(16)
        res = pd.concat(parallel_pool.map(lr_predict, params))
        for _, row in res.iterrows():
            uid, qtype, qid, sub_id = map(int, row[:4])
            yhat = float(row[-1])
            k = '%s:%s:%s:%s' % (uid, qtype, qid, sub_id)
            estimation[k] = yhat
        return estimation


def dump_estimation(redis_db, estimation):
    q_stat, u_stat_cet4, u_stat_cet6 = dict(), dict(), dict()
    q_origin = dict()  # "qtype:qid": exam_type

    for k, y in estimation.iteritems():
        uid, qtype, qid, sub_id = map(int, k.split(':'))
        item_id = '%s:%s' % (qtype, qid)
        q_stat.setdefault(item_id, {}).setdefault(sub_id, []).append(y)
        if item_id not in q_origin:
            exam_type = load_question_feature(redis_db, qtype, qid, sub_id)[2]
            q_origin[item_id] = exam_type
        exam_type = q_origin[item_id]
        # 只对于真题计算用户估分
        if exam_type == EXAM_CET4:
            u_stat_cet4.setdefault(uid, {}).setdefault(qtype, []).append(y)
        elif exam_type == EXAM_CET6:
            u_stat_cet6.setdefault(uid, {}).setdefault(qtype, []).append(y)

    for item_id, v in q_stat.iteritems():
        sub_correct = [np.mean(ys) for _, ys in v.iteritems()]
        score = np.mean(sub_correct)
        redis_db.hset(CET_MOCK_TEST_QUESTION_ESTIMATE_KEY, item_id, score)

    def _process_u_stat(u_stat, exam_type):
        all_yhat = []
        for uid, v in u_stat.iteritems():
            for qtype, ys in v.iteritems():
                v[qtype] = np.mean(ys)
            yhat, total_weight = 0.0, 0
            for qtype, y in v.iteritems():
                yhat += y * Q_WEIGHT[qtype]
                total_weight += Q_WEIGHT[qtype]
            yhat = int(yhat / total_weight * 100)
            key = CET_MOCK_TEST_USER_ESTIMATE_KEY % (exam_type, uid)
            redis_db.set(key, yhat)
            all_yhat.append(yhat)

        global_mean = np.mean(all_yhat)
        global_sd = np.std(all_yhat)
        redis_db.set(CET_MOCK_TEST_SCORE_MEAN % exam_type, global_mean)
        redis_db.set(CET_MOCK_TEST_SCORE_SD % exam_type, global_sd)

    _process_u_stat(u_stat_cet4, EXAM_CET4)
    _process_u_stat(u_stat_cet6, EXAM_CET6)

