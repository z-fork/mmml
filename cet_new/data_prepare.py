# coding: utf-8

from __future__ import absolute_import

import numpy as np
import pandas as pd

from cet_new.consts import QUESTION_CONF, K_APPROVED, EXAM_TYPE_DEFAULT
from utils.consts import (
    QUESTION_RECORD_STATUS_EMPTY as EMPTY,
    QUESTION_RECORD_STATUS_RIGHT as RIGHT
)


def get_location_info(conn_func):
    conn = conn_func()
    sql = ('select id location_id, type, parent_id from location '
           'where type != 0 order by type')
    A = pd.read_sql_query(sql, conn)
    location_info = dict()
    for _, row in A.iterrows():
        location_id, type, parent_id = map(int, row)
        if type <= 2:
            location_info[location_id] = location_id
        else:
            location_info[location_id] = location_info[parent_id]
    return location_info


def get_user_profile(conn_func):
    '''返回 {uid: [gender, location_id], ...}'''
    conn = conn_func()
    sql = 'select id uid, gender, location_id from user_profile'
    A = pd.read_sql_query(sql, conn)

    location_info = get_location_info(conn_func)
    user_profile = dict()
    for _, row in A.iterrows():
        uid, gender, location_id = row
        uid = int(uid)
        gender = 0 if np.isnan(gender) else int(gender)
        location_id = 0 if np.isnan(location_id) else int(location_id)
        location_id = location_info.get(location_id, location_id)
        user_profile[uid] = [gender, location_id]
    return user_profile


def get_origin_info(conn_func):
    conn = conn_func()
    sql = ('select target_kind, target_id, exam_type '
           'from origin where exam_type != %s') % EXAM_TYPE_DEFAULT
    df = pd.read_sql_query(sql, conn)
    origin = dict()
    for _, row in df.iterrows():
        qtype, qid, exam_type = map(int, row)
        origin.setdefault(qtype, {})[qid] = exam_type
    return origin


def get_qinfo_by_type(conn_func, configs, qtype):
    '''
    获取某题型下题目基本信息

    Args:
        conn_func: 数据库连接函数
        configs: 题库基本信息配置
        qtype: 题型

    Returns:
        [(qtype, qid, sub_id, n_question, diff), ...]
        sub_id: 小题 ID, 如没有小题则跟大题 ID 相同
        n_question: 该大题一共有几道小题
        diff: 难度, 如无小题难度则使用大题难度
    '''
    conn = conn_func()
    conf = configs[qtype]
    if conf['has_stem_difficulty']:
        sql = 'select id, difficulty from %s where status = %s'
    else:
        sql = 'select id, 0 from %s where status = %s'
    A = pd.read_sql_query(sql % (conf['table'], K_APPROVED), conn)
    A.columns = ['qid', 'q_diff']

    qinfo = dict()
    for _, row in A.iterrows():
        qid, q_diff = map(int, row)
        # q_diff, sub_info
        # 大题难度, 小题信息 {sub_id:sub_diff}
        qinfo[qid] = [q_diff, dict()]

    if conf['question_table']:
        sql = 'select stem_id, id, difficulty from %s'
        B = pd.read_sql_query(sql % conf['question_table'], conn)
        B.columns = ['qid', 'sub_id', 'sub_diff']
        for _, row in B.iterrows():
            qid, sub_id, sub_diff = map(int, row)
            # 如果 qid 不在 qinfo 说明不是入库的题, 需要跳过
            if qid not in qinfo:
                continue
            qinfo[qid][1][sub_id] = sub_diff

    ans = []
    for qid, (q_diff, sub_info) in qinfo.iteritems():
        if not sub_info:
            ans.append((qtype, qid, qid, 1, q_diff))
            continue
        n_question = len(sub_info)
        for sub_id, sub_diff in sub_info.iteritems():
            diff = q_diff if not sub_diff else sub_diff
            ans.append((qtype, qid, sub_id, n_question, diff))

    return ans


def get_question_info(conn_func):
    '''
    获取题目基本信息

    Args:
        conn_func: 数据库连接函数

    Returns:
        {(qtype, qid, sub_id): (n_question, diff, exam_type), ...}
        exam_type: 考试类型, 四/六级, 真题/模拟题
        其他数据同 `get_qinfo_by_type` 函数的返回值
    '''
    origin = get_origin_info(conn_func)

    qinfo = dict()
    for qtype in QUESTION_CONF.keys():
        res = get_qinfo_by_type(conn_func, QUESTION_CONF, qtype)
        for qtype, qid, sub_id, n_question, diff in res:
            exam_type = origin.get(qtype, {}).get(qid, EXAM_TYPE_DEFAULT)
            if exam_type == EXAM_TYPE_DEFAULT:
                continue
            qinfo[(qtype, qid, sub_id)] = (n_question, diff, exam_type)

    return qinfo


def get_valid_practice_log(conn_func, qinfo):
    '''
    获取清洗后的练题记录

    Args:
        conn_func: 数据库连接函数
        qinfo: 题目信息, 即 `get_question_info` 函数返回值

    Returns:
        practice_log: [uid, qtype, qid, sub_id, seconds, correct]
        user_avg: [uid, qtype, avg_time, avg_correct]
        item_avg: [qtype, qid, sub_id, avg_time, avg_correct]

        返回值均为 pandas.DataFrame 格式
        其中 seconds 和 avg_time 参数均针对小题,
        即原始时间除以该大题的小题数
    '''
    conn = conn_func()
    sql = ('select id parent_log_id, user_id uid, target_kind qtype, '
           'target_id qid, seconds, record_time, '
           'n_right, n_wrong from practice_log')
    A = pd.read_sql_query(sql, conn)
    # 去掉做题时间过于极端的
    A = A[(A.seconds > 2) & (A.seconds < 1800)]

    B = A.groupby('uid').size().reset_index()
    B.columns = ['uid', 'q_count']
    B = B[B.q_count >= 3]
    # 去掉做题数量过少的用户
    M = pd.merge(A, B)

    def _pick_latest_log(df):
        res = df.sort('record_time').tail(1)
        return res[['parent_log_id', 'seconds', 'n_right', 'n_wrong']]

    # 同一题目多次练习只取最后一次记录
    M = M.groupby(['uid', 'qtype', 'qid']).apply(_pick_latest_log).reset_index()
    M = M[(M.n_right != 0) | (M.n_wrong != 0)]
    M = M[['parent_log_id', 'uid', 'seconds']]

    conn = conn_func()
    sql = ('select parent_log_id, user_id, parent_kind, parent_id, '
           'target_id, status from practice_log_detail')
    X = pd.read_sql_query(sql, conn)
    X.columns = ['parent_log_id', 'uid', 'qtype', 'qid', 'sub_id', 'status']
    M = pd.merge(X, M)

    practice_log = []
    for _, row in M.iterrows():
        parent_log_id, uid, qtype, qid, sub_id, status, seconds = map(int, row)
        if status == EMPTY:
            continue
        correct = 1 if status == RIGHT else 0
        res = qinfo.get((qtype, qid, sub_id), None)
        if res is None:
            continue
        n_question, diff, exam_type = res
        seconds = float(seconds) / n_question
        line = (uid, qtype, qid, sub_id, seconds, correct)
        practice_log.append(line)

    practice_log = pd.DataFrame(practice_log)
    practice_log.columns = ['uid', 'qtype', 'qid', 'sub_id', 'seconds', 'correct']

    user_avg = practice_log.drop(['qid', 'sub_id'], axis=1).groupby(
        ['uid', 'qtype']).mean().reset_index()
    user_avg.columns = ['uid', 'qtype', 'avg_time', 'avg_correct']
    item_avg = practice_log.drop('uid', axis=1).groupby(
        ['qtype', 'qid', 'sub_id']).mean().reset_index()
    item_avg.columns = ['qtype', 'qid', 'sub_id', 'avg_time', 'avg_correct']

    return practice_log, user_avg, item_avg

