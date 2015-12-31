# coding: utf-8

from __future__ import absolute_import
import argparse

import pandas as pd

from maths.consts import (
    MATH_QUESTION_KIND_MAP, MATH_ANALYSIS_KIND_MAP,
    K_MATH_CHOICE, K_MATH_BLANK, K_MATH_RESPONSE,
    MATH_QUESTION_INV_INDEX, MATH_QUESTION_FACTOR_KEY
)
from utils.consts import (
    MATH_EXAM_KIND_MAP, MATH_EXAM_KIND_DEFAULT,
    MATH_CATEGORY_W,  MATH_EXAM_KIND_GK_ARTS,
    K_CHECKED, K_APPROVED
)
from utils.data_store import (
    get_banker_conn, get_banker_dev_conn,
    redis_online, redis_debug, flush_redis
)
from maths.knowledge_model import MathQuestionFactor
from maths.question_index import (
    get_knowledge_tree, set_knowledge_tree_index,
    set_math_knowledge_inv_index, get_question_knowledge_index,
    flush_inv_index, get_all_question_factor_keys
)

VALID_QUESTION_STATE = [K_CHECKED, K_APPROVED]
VALID_QUESTION_STATE = ",".join(map(str, VALID_QUESTION_STATE))


def get_origin_info(conn_func):
    conn = conn_func()
    sql = 'select target_kind, target_id, grade_id, category from math_origin'
    origin = pd.read_sql_query(sql, conn)
    def _get_exam_kind(row):
        if row.category == MATH_CATEGORY_W:
            return MATH_EXAM_KIND_GK_ARTS
        return MATH_EXAM_KIND_MAP.get(row.grade_id, MATH_EXAM_KIND_DEFAULT)
    origin['exam_kind'] = origin.apply(_get_exam_kind, axis=1)
    origin = origin[['target_kind', 'target_id', 'exam_kind']].drop_duplicates()
    origin = origin[origin.exam_kind != MATH_EXAM_KIND_DEFAULT]
    origin.rename(columns={'target_kind':'qtype', 'target_id':'qid'},
                  inplace=True)
    return origin


def get_analysis_info(conn_func):
    _convert = lambda df: df.groupby(['target_kind', 'target_id']
            ).apply(lambda x: "|".join(map(str, x.tag_id))).reset_index()
    conn = conn_func()
    MATH_ANALYSIS_KEYS = ",".join(map(str, MATH_ANALYSIS_KIND_MAP.keys()))
    sql = ('select target_kind, target_id, tag_id from %s '
           'where target_kind in (%s)')
    Ktags = _convert(pd.read_sql_query(sql % ('math_knowledge_tag',
        MATH_ANALYSIS_KEYS), conn))
    Mtags = _convert(pd.read_sql_query(sql % ('math_solution_method_tag',
        MATH_ANALYSIS_KEYS), conn))
    Ktags.columns = ['analysis_kind', 'analysis_id', 'ktag']
    Mtags.columns = ['analysis_kind', 'analysis_id', 'mtag']
    Atags = pd.merge(Ktags, Mtags, how='outer')
    Atags.rename(columns={'analysis_kind':'qtype'}, inplace=True)
    Atags[['qtype']] = Atags[['qtype']].astype('int64')
    Atags[['analysis_id']] = Atags[['analysis_id']].astype('int64')
    Atags['qtype'] = Atags['qtype'].map(lambda x: MATH_ANALYSIS_KIND_MAP[x])

    X = pd.read_sql_query('select id, solution_id from math_analysis', conn)
    X.rename(columns={'id':'analysis_id'}, inplace=True)
    return pd.merge(Atags, X)


def get_solution_info(conn_func):
    conn = conn_func()
    sql = 'select id, target_kind, target_id, order_id from math_solution'
    df = pd.read_sql_query(sql, conn)
    df.columns = ['solution_id', 'qtype', 'sub_qid', 'order_id']
    # qtype 统一到题型
    df['qtype'] = df['qtype'].map(lambda x: MATH_QUESTION_KIND_MAP[x])
    return df


def get_choice_info(conn_func):
    conn = conn_func()
    sql = ('select question_type, id, difficulty from math_choice_stem '
           'where state in (%s)' % VALID_QUESTION_STATE)
    df = pd.read_sql_query(sql, conn)
    df.columns = ['qtype', 'qid', 'difficulty']
    df['sub_qid'] = df['qid']
    return df


def get_blank_info(conn_func):
    conn = conn_func()
    sql = ('select question_type, id, difficulty from math_fill_blank_stem '
           'where state in (%s)' % VALID_QUESTION_STATE)
    df = pd.read_sql_query(sql, conn)
    df.columns = ['qtype', 'qid', 'difficulty']
    sql = 'select id, stem_id from math_fill_blank_question'
    X = pd.read_sql_query(sql, conn)
    X.columns = ['sub_qid', 'qid']
    return pd.merge(df, X)


def get_response_info(conn_func):
    conn = conn_func()
    sql = ('select question_type, id, difficulty from math_response_stem '
           'where state in (%s)' % VALID_QUESTION_STATE)
    df = pd.read_sql_query(sql, conn)
    df.columns = ['qtype', 'qid', 'difficulty']
    sql = 'select id, stem_id from math_response_question'
    X = pd.read_sql_query(sql, conn)
    X.columns = ['sub_qid', 'qid']
    return pd.merge(df, X)


# TODO 待重构，不要每次传这么多参数
def dump_question_factor(conn_func, redis_db, info_func,
        QTYPE, solution, analysis_info, knowledge_tree):
    res = []
    qinfo = info_func(conn_func)
    df = pd.merge(qinfo, solution[solution.qtype == QTYPE])
    df = pd.merge(df, analysis_info[analysis_info.qtype == QTYPE])
    df_group = df.groupby(['qtype', 'qid'])
    for name1, group1 in df_group:
        qtype, qid = name1
        difficulty = group1.difficulty.iloc[0]
        question_analysis = []
        for name2, group2 in group1.groupby(['sub_qid', 'solution_id']):
            sub_qid, solution_id = name2
            S = group2.sort(columns='analysis_id')[['ktag', 'mtag']]
            analysis_step = []
            f = lambda x: None if pd.isnull(x) else set(map(int, x.split('|')))
            for _, row in S.iterrows():
                ktag, mtag = row
                analysis_step.append((f(ktag), f(mtag)))
            question_analysis.append(analysis_step)

        qfactor = MathQuestionFactor(difficulty)
        qfactor.add_factor(question_analysis)
        factor_value = qfactor.dump_factor()
        factor_key = MATH_QUESTION_FACTOR_KEY % (qtype, qid)
        flush_redis(redis_db, factor_key, factor_value)

        indices = get_question_knowledge_index(qfactor, knowledge_tree)
        res.append((qtype, qid, indices))
    return res


def dump_question_index(redis_db, question_list, origin):
    '''[(qtype, qid, set_of_module_ids), ...]'''
    df = pd.DataFrame(question_list)
    df.columns = ['qtype', 'qid', 'module_ids']
    df = pd.merge(df, origin)
    inv_idx = {}
    for _, row in df.iterrows():
        qtype, qid, module_ids, exam_kind = row
        for module_id in module_ids:
            inv_idx.setdefault((exam_kind, qtype, module_id), []).append(qid)

    modified_fields = set()
    for (exam_kind, qtype, module_id), qids in inv_idx.iteritems():
        field = '%s:%s:%s' % (exam_kind, qtype, module_id)
        value = "|".join(map(str, qids))
        redis_db.hset(MATH_QUESTION_INV_INDEX, field, value)
        modified_fields.add(field)

    flush_inv_index(redis_db, MATH_QUESTION_INV_INDEX, modified_fields)


def remove_unapproved_questions(conn_func, redis_db, question_type, table_name):
    conn = conn_func()
    cursor = conn.cursor()
    sql = 'select id from %s where state in (%s)'
    cursor.execute(sql % (table_name, VALID_QUESTION_STATE))
    pool = set([qid for qid, in cursor.fetchall()])

    count = 0
    qfactor_keys = get_all_question_factor_keys(redis_db)
    keys = qfactor_keys.get(question_type, [])
    for key in keys:
        qtype, qid = map(int, key.split('/')[-2:])
        if qid not in pool:
            redis_db.delete(key)
            count += 1
    print 'remove unapproved %s questions: %d' % (question_type, count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    redis_db = redis_debug if args.debug else redis_online
    conn_func = get_banker_dev_conn if args.debug else get_banker_conn

    remove_unapproved_questions(conn_func, redis_db,
                                K_MATH_CHOICE, 'math_choice_stem')
    remove_unapproved_questions(conn_func, redis_db,
                                K_MATH_BLANK, 'math_fill_blank_stem')
    remove_unapproved_questions(conn_func, redis_db,
                                K_MATH_RESPONSE, 'math_response_stem')

    solution = get_solution_info(conn_func)
    analysis_info = get_analysis_info(conn_func)
    knowledge_tree = get_knowledge_tree(conn_func)
    set_knowledge_tree_index(redis_db, knowledge_tree)

    choice_idx = dump_question_factor(conn_func, redis_db, get_choice_info,
            K_MATH_CHOICE, solution, analysis_info, knowledge_tree)
    print 'math choice ok'
    blank_idx = dump_question_factor(conn_func, redis_db, get_blank_info,
            K_MATH_BLANK, solution, analysis_info, knowledge_tree)
    print 'math fill blank ok'
    response_idx = dump_question_factor(conn_func, redis_db, get_response_info,
            K_MATH_RESPONSE, solution, analysis_info, knowledge_tree)
    print 'math response ok'

    question_list = choice_idx + blank_idx + response_idx
    origin = get_origin_info(conn_func)
    dump_question_index(redis_db, question_list, origin)
    print 'question index ok'
    set_math_knowledge_inv_index(redis_db)
    print 'knowledeg inverse index ok'

