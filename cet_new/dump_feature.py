# coding: utf-8

from __future__ import absolute_import
import json
from operator import itemgetter

import numpy as np

from utils.data_store import flush_redis
from cet_new.data_prepare import get_origin_info
from cet_new.consts import EXAM_TYPE_DEFAULT, CET_QUESTION_KINDS

CET_PRACTICE_LOG_PATH = '/home/shenfei/data/dagobah/cet_practice_log_%s.csv'

CET_USER_FEATURE_KEY = '/alg/cet/user_feature/%s'  # uid
# 题目特征, 详见 `dump_question_feature` 函数
CET_QUESTION_FEATURE_KEY = '/alg/cet/question_feature'

# 用户默认各题型 score, hset {qtype: (avg_time, avg_corret), ...}
CET_USER_DEFAULT_FEATURE_KEY = '/alg/cet/user_default_feature'
# 题目默认各题型 score, hset {qtype: (avg_time, avg_correct)}
CET_QUESTION_DEFAULT_FEATURE_KEY = '/alg/cet_question_default_feature'

CET_QUESTION_INV_INDEX_KEY = '/alg/cet/question_index/%s/%s'  # exam_type qtype


def dump_user_feature(redis_db, user_profile, user_avg):
    '''
    将用户特征存入 redis, json 格式, 每个 uid key 解析后为:
    [
        gender,
        location,
        {
            qtype: (avg_time, avg_correct)
        }
    ]
    同时返回结果 dict 方便输出 practice_log 训练数据
    {qtype: (avg_time, avg_correct)} 的默认值也会存储到 redis 中
    '''
    res = dict()
    # 对于没有练题记录的用户, 用某种题型的全体均值作为默认值
    default_score = dict()
    # 对于没有练题记录的题型, 则用全部记录的均值作为默认值
    global_score_list = []

    for _, row in user_avg.iterrows():
        uid, qtype, avg_time, avg_correct = row
        uid, qtype = int(uid), int(qtype)
        res.setdefault(uid, {})[qtype] = (avg_time, avg_correct)
        default_score.setdefault(qtype, []).append((avg_time, avg_correct))
        global_score_list.append((avg_time, avg_correct))

    for qtype, score_list in default_score.iteritems():
        avg_time = np.mean(map(itemgetter(0), score_list))
        avg_correct = np.mean(map(itemgetter(1), score_list))
        default_score[qtype] = (avg_time, avg_correct)
    global_avg_time = np.mean(map(itemgetter(0), global_score_list))
    global_avg_correct = np.mean(map(itemgetter(1), global_score_list))
    global_default_score = (global_avg_time, global_avg_correct)

    # 处理第一次上线新题型没有练题数据的尴尬
    for qtype in CET_QUESTION_KINDS:
        if qtype not in default_score:
            default_score[qtype] = global_default_score

    user_feature = dict()
    for uid, (gender, location_id) in user_profile.iteritems():
        score = res.get(uid, default_score)
        for qtype in CET_QUESTION_KINDS:
            if qtype not in score:
                score[qtype] = default_score[qtype]
        feature = [gender, location_id, score]
        user_feature[uid] = feature

        key = CET_USER_FEATURE_KEY % uid
        value = json.dumps(feature)
        redis_db.set(key, value)

    # 将默认值也存入 redis, 供没有特征的用户使用
    for qtype, score in default_score.iteritems():
        value = json.dumps(score)
        redis_db.hset(CET_USER_DEFAULT_FEATURE_KEY, qtype, value)

    return user_feature


def dump_question_feature(redis_db, qinfo, item_avg):
    '''
    将题目特征存入 redis, json 格式, 解析后为:
    {
        'qtype:qid:sub_id': [n_question, diff, exam_type, avg_time, avg_correct]
    }
    '''
    res = dict()
    # 对于没有练题记录的题目, 用该题型的全体均值作为默认值
    default_score = dict()
    # 对于没有练题记录的题型, 则用全部记录的均值作为默认值
    global_score_list = []

    for _, row in item_avg.iterrows():
        qtype, qid, sub_id  = map(int, row[:3])
        item_id = '%s:%s' % (qid, sub_id)
        avg_time, avg_correct = row[3:5]
        res.setdefault(qtype, {})[item_id] = (avg_time, avg_correct)
        default_score.setdefault(qtype, []).append((avg_time, avg_correct))
        global_score_list.append((avg_time, avg_correct))

    for qtype, score_list in default_score.iteritems():
        avg_time = np.mean(map(itemgetter(0), score_list))
        avg_correct = np.mean(map(itemgetter(1), score_list))
        default_score[qtype] = (avg_time, avg_correct)
    global_avg_time = np.mean(map(itemgetter(0), global_score_list))
    global_avg_correct = np.mean(map(itemgetter(1), global_score_list))
    global_default_score = (global_avg_time, global_avg_correct)

    for qtype in CET_QUESTION_KINDS:
        if qtype not in default_score:
            default_score[qtype] = global_default_score

    question_feature = dict()
    for k, v in qinfo.iteritems():
        qtype, qid, sub_id = k
        item_id = '%s:%s' % (qid, sub_id)
        n_question, diff, exam_type = v
        avg_time, avg_correct = res[qtype].get(item_id, default_score[qtype])
        feature = [n_question, diff, exam_type, avg_time, avg_correct]

        field = '%s:%s:%s' % (qtype, qid, sub_id)
        question_feature[field] = feature
        value = json.dumps(feature)
        redis_db.hset(CET_QUESTION_FEATURE_KEY, field, value)

    # 将默认值也存入 redis, 供没有特征的题目使用
    for qtype, score in default_score.iteritems():
        value = json.dumps(score)
        redis_db.hset(CET_QUESTION_DEFAULT_FEATURE_KEY, qtype, value)

    return question_feature


def dump_practice_log(practice_log, user_feature, question_feature, outpath):
    '''
    将需要用到的特征连同练题记录输出到文件, 供模型训练使用
    '''
    out = open(outpath, 'w')
    for _, row in practice_log.iterrows():
        uid, qtype, qid, sub_id = map(int, row[:4])
        seconds, correct = row[4:6]
        gender, location_id, u_score = user_feature[uid]
        u_avg_time, u_avg_correct = u_score[qtype]
        field = '%s:%s:%s' % (qtype, qid, sub_id)
        if field not in question_feature:
            continue  # 会有部分已废弃题目的练题脏数据
        feature = question_feature[field]
        n_question, diff, exam_type, q_avg_time, q_avg_correct = feature

        line = [uid, qtype, qid, sub_id, correct, seconds,
                gender, location_id, u_avg_time, u_avg_correct,
                n_question, diff, exam_type, q_avg_time, q_avg_correct]
        line = "\t".join(map(str, line))
        print >> out, line
    out.close()


def dump_question_inv_index(conn_func, redis_db, qinfo):
    valid_question_set = set()
    for k, _ in qinfo.iteritems():
        qtype, qid, _ = k
        valid_question_set.add((qtype, qid))

    origin = get_origin_info(conn_func)
    keys = redis_db.hkeys(CET_QUESTION_FEATURE_KEY)
    res = dict()
    removed_questions = set()
    for key in keys:
        qtype, qid, _ = map(int, key.split(':'))
        # 可能会因为各种莫名原因导致 redis 中残存有脏数据
        # 用本次计算的 qinfo 过滤一遍保证都是已入库题目
        if (qtype, qid) not in valid_question_set:
            removed_questions.add((qtype, qid))
            continue
        exam_type = origin.get(qtype, {}).get(qid, EXAM_TYPE_DEFAULT)
        if exam_type == EXAM_TYPE_DEFAULT:
            continue
        res.setdefault(exam_type, {}).setdefault(qtype, []).append(qid)

    for exam_type, v in res.iteritems():
        for qtype, qids in v.iteritems():
            key = CET_QUESTION_INV_INDEX_KEY % (exam_type, qtype)
            flush_redis(redis_db, key, qids)

    print 'remove %s questions' % len(removed_questions)

