# coding: utf-8

from __future__ import absolute_import

import pandas as pd

from maths.consts import (
    MATH_KNOWLEDGE_INV_INDEX, MATH_KNOWLEDGE_TREE_INDEX,
    MATH_QUESTION_INV_INDEX, MATH_QUESTION_FACTOR_KEY
)
from maths.knowledge_model import load_matrix


def get_knowledge_tree(conn_func):
    conn = conn_func()
    sql = 'select id, parent_id, level from math_knowledge where level>0'
    K = pd.read_sql_query(sql, conn)
    K.rename(columns={'id':'kid'}, inplace=True)
    K.sort(columns='level', inplace=True)
    res = {}
    for _, row in K.iterrows():
        kid, parent_id, level = row
        if level == 1:
            res[kid] = kid
        else:  # 已按 level 排序，所以父节点存在
            res[kid] = res[parent_id]
    return res


def set_knowledge_tree_index(redis_db, ktree_map):
    ktree_idx = {}
    for kid, module_id in ktree_map.iteritems():
        ktree_idx.setdefault(module_id, []).append(kid)
    for module_id, kids in ktree_idx.iteritems():
        value = "|".join(map(str, kids))
        redis_db.hset(MATH_KNOWLEDGE_TREE_INDEX, module_id, value)


def get_question_knowledge_index(qfactor, ktree):
    res = set()
    for ktag in qfactor.knowledge_mat.keys():
        if ktag in ktree:
            res.add(ktree[ktag])
    return res


def get_all_question_factor_keys(redis_db):
    '''
    {qtype: [qfactor_key_str, ...], ...}
    '''
    fields = redis_db.hkeys(MATH_QUESTION_INV_INDEX)
    qfactor_keys = dict()
    for field in fields:
        _, qtype, _ = map(int, field.split(':'))
        qids = redis_db.hget(MATH_QUESTION_INV_INDEX, field)
        keys = []
        for qid in qids.split('|'):
            keys.append(MATH_QUESTION_FACTOR_KEY % (qtype, qid))
        qfactor_keys.setdefault(qtype, []).extend(keys)
    return qfactor_keys


def set_math_knowledge_inv_index(redis_db):
    qfactor_keys = get_all_question_factor_keys(redis_db)
    keys = reduce(list.__add__, qfactor_keys.values())

    k_idx = {}
    for key in keys:
        qtype, qid = key.split('/')[-2:]
        k_str, m_str, k_m_str, diff = redis_db.lrange(key, 0, -1)
        k_mat = load_matrix(k_str)
        for ktag in k_mat.keys():
            k_idx.setdefault(ktag, {})
            value = ":".join([qid, diff])
            k_idx[ktag].setdefault(qtype, []).append(value)

    modified_fields = set()
    for ktag, item in k_idx.iteritems():
        for qtype, qids in item.iteritems():
            field = '%s:%s' % (ktag, qtype)
            value = "|".join(qids)  # qids 中每项是 'qid:k_mat_value'
            redis_db.hset(MATH_KNOWLEDGE_INV_INDEX, field, value)
            modified_fields.add(field)

    flush_inv_index(redis_db, MATH_KNOWLEDGE_INV_INDEX, modified_fields)


def flush_inv_index(redis_db, hset_key, modified_fields):
    '''
    根据此次更新的索引 fields 删除 redis hset 中冗余的 fields

    因为题目编辑状态改动或知识点改动可能造成某个大类索引下题目为空。
    此时更新脚本不会刷新该索引对应的 redis hset field，
    但具体题目的 key 已经被删，从而造成读取时出错。
    '''
    current_fields = set(redis_db.hkeys(hset_key))
    to_del = current_fields - modified_fields
    for field in to_del:
        redis_db.hdel(hset_key, field)
        print 'delete hset field %s of key %s' % (field, hset_key)

