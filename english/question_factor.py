# coding: utf-8

from __future__ import absolute_import
import argparse

from utils.data_store import (
        redis_online, redis_debug, flush_redis,
        get_banker_conn, get_banker_dev_conn)
from utils.consts import (
        K_SINGLE_CHOICE, READING_CONFS, CLOZE_CONF, LISTEN_CONFS,
        EXAM_KIND_MAP, EXAM_KIND_DEFAULT, K_APPROVED, CONF_MAP
)
from english.knowledge_factor import KnowledgeFactor
from english.consts import (
        ENGLISH_QUESTION_FACTOR_KEY, ENGLISH_QUESTION_INV_INDEX
)

KNOWLEDGE_INV_INDEX = '/alg/knowledge/%s/qtype/%s'
RELATED_KNOWLEDGE_INV_INDEX = '/alg/related_knowledge/%s/qtype/%s'


def remove_unapproved_questions(conn_func, redis_db):
    fields = redis_db.hkeys(ENGLISH_QUESTION_FACTOR_KEY)
    keys_map = dict()
    for field in fields:
        qtype, qid = field.split(':')
        keys_map.setdefault(int(qtype), []).append(field)

    conn = conn_func()
    cursor = conn.cursor()
    count = 0
    for qtype, conf in CONF_MAP.iteritems():
        context_conf = conf['context_conf']
        table = context_conf['table']
        cid = context_conf['cid']
        sql = 'select %s from %s where question_type=%s and state=%s'
        cursor.execute(sql % (cid, table, qtype, K_APPROVED))
        pool = set([qid for qid, in cursor.fetchall()])
        keys = keys_map.get(qtype, [])
        for key in keys:
            qid = int(key.split(':')[1])
            if qid not in pool:
                redis_db.hdel(ENGLISH_QUESTION_FACTOR_KEY, key)
                count += 1
    conn.close()
    print 'remove unapproved english questions: %d' % count


def get_origin(conn_func):
    conn = conn_func()
    cursor = conn.cursor()
    cursor.execute('select target_kind, target_id, '
                   'grade_id, exam_type from origin')
    origin = {}
    for qtype, qid, grade_id, etype in cursor.fetchall():
        ekind = EXAM_KIND_MAP.get(grade_id, EXAM_KIND_DEFAULT)
        if qtype not in origin:
            origin[qtype] = {}
        # 每道题目可能有多个 origin 来源
        origin[qtype].setdefault(qid, []).append((grade_id, etype, ekind))
    cursor.close()
    conn.close()
    return origin


def get_knowledge(conn_func, table):
    conn = conn_func()
    cursor = conn.cursor()
    cursor.execute('select target_id, target_kind, tag_id from %s' % table)
    knowledge = dict()
    for qid, qtype, ktag in cursor.fetchall():
        if qtype not in knowledge:
            knowledge[qtype] = {}
        knowledge[qtype].setdefault(qid, []).append(ktag)
    cursor.close()
    conn.close()
    return knowledge


def dump_factor(redis_db, qtype, info, origin):
    res = []
    for qid, factor in info.iteritems():
        score = factor.text()
        if not score:
            continue
        origin_info = origin.get(qtype, {}).get(qid, [])
        if not origin_info:
            continue
        field = '%s:%s' % (qtype, qid)
        redis_db.hset(ENGLISH_QUESTION_FACTOR_KEY, field, score)
        for grade_id, etype, ekind in origin_info:
            res.append((ekind, qtype, qid))
    return res


def dump_question_index(redis_db, question_index):
    idx = {}
    for exam_kind, qtype, qid in question_index:
        idx.setdefault((exam_kind, qtype), []).append(qid)
    for (exam_kind, qtype), qids in idx.iteritems():
        key = ENGLISH_QUESTION_INV_INDEX % (exam_kind, qtype)
        flush_redis(redis_db, key, qids)


def get_single_choice_info(conn_func, redis_db,
                           knowledge, related_knowledge, origin):
    conn = conn_func()
    qtype = K_SINGLE_CHOICE
    cursor = conn.cursor()
    cursor.execute('select id, difficulty from choice_stem where '
                   'question_type=%s and state=%s', (qtype, K_APPROVED))
    info = {}
    for qid, diff in cursor.fetchall():
        ktags = knowledge.get(qtype, {}).get(qid, [])
        rktags = related_knowledge.get(qtype, {}).get(qid, [])
        ktags = [(tag, diff) for tag in ktags]
        rktags = [(tag, diff) for tag in rktags]
        info[qid] = KnowledgeFactor(ktags, rktags)
    cursor.close()
    conn.close()
    return dump_factor(redis_db, qtype, info, origin)


# FIXME: 临时起的函数名字应付各种奇怪的题型
def get_combine_info1(conn_func, redis_db, conf,
                      knowledge, related_knowledge, origin):
    '''
    针对大题没有难度，而小题有难度，得到大题对应知识点表示
    '''
    conn = conn_func()
    cursor = conn.cursor()
    context_conf = conf['context_conf']
    question_conf = conf['question_conf']

    context_type = context_conf['qtype']
    table = context_conf['table']
    context_id = context_conf['cid']
    context_sql = 'select %s from %s where question_type=%s and state=%s'
    cursor.execute(context_sql % (context_id, table, context_type, K_APPROVED))
    valid_cids = set([cid for cid, in cursor.fetchall()])

    question_type = question_conf['qtype']
    table = question_conf['table']
    context_id = question_conf['cid']
    question_id = question_conf['qid']
    question_sql = 'select %s,%s,difficulty from %s where question_type=%s'
    param = (context_id, question_id, table, question_type)
    cursor.execute(question_sql % param)

    info = {}
    for cid, qid, diff in cursor.fetchall():
        if cid not in valid_cids: continue # 只考虑审核过的大题
        ktags = knowledge.get(question_type, {}).get(qid, [])
        rktags = related_knowledge.get(question_type, {}).get(qid, [])
        ktags = [(tag, diff) for tag in ktags]
        rktags = [(tag, diff) for tag in rktags]
        qfac = KnowledgeFactor(ktags, rktags)
        info.setdefault(cid, []).append(qfac)

    combine_info = {}
    for cid, factors in info.iteritems():
        question_fac = KnowledgeFactor.merge(factors)
        # 使用小题知识点的平均难度作为大题的难度
        diff = question_fac.difficulty()
        ktags = knowledge.get(context_type, {}).get(cid, [])
        rktags = related_knowledge.get(context_type, {}).get(cid, [])
        ktags = [(tag, diff) for tag in ktags]
        rktags = [(tag, diff) for tag in rktags]
        context_fac = KnowledgeFactor(ktags, rktags)
        combine_info[cid] = KnowledgeFactor.merge([context_fac, question_fac])
    cursor.close()
    return dump_factor(redis_db, context_type, combine_info, origin)


def get_combine_info2(conn_func, redis_db, conf,
                      knowledge, related_knowledge, origin):
    '''
    针对大题有难度，而小题没有难度，得到大题对应知识点表示
    '''
    conn = conn_func()
    cursor = conn.cursor()
    context_conf = conf['context_conf']
    question_conf = conf['question_conf']

    context_type = context_conf['qtype']
    table = context_conf['table']
    context_id = context_conf['cid']
    context_sql = ('select %s, difficulty from %s where question_type=%s '
                   'and state=%s')
    cursor.execute(context_sql % (context_id, table, context_type, K_APPROVED))
    diff_dict = dict([(cid, diff) for cid, diff in cursor.fetchall()])

    question_type = question_conf['qtype']
    table = question_conf['table']
    context_id = question_conf['cid']
    question_id = question_conf['qid']
    question_sql = 'select %s,%s from %s where question_type=%s'
    param = (context_id, question_id, table, question_type)
    cursor.execute(question_sql % param)

    info = {}
    for cid, qid in cursor.fetchall():
        ktags = knowledge.get(question_type, {}).get(qid, [])
        rktags = related_knowledge.get(question_type, {}).get(qid, [])
        if cid not in diff_dict: continue  # 只考虑审核过的大题
        diff = diff_dict[cid]
        # 将大题的难度当作小题各知识点难度
        ktags = [(tag, diff) for tag in ktags]
        rktags = [(tag, diff) for tag in rktags]
        qfac = KnowledgeFactor(ktags, rktags)
        info.setdefault(cid, []).append(qfac)

    combine_info = {}
    for cid, factors in info.iteritems():
        diff = diff_dict[cid]
        ktags = knowledge.get(context_type, {}).get(cid, [])
        rktags = related_knowledge.get(context_type, {}).get(cid, [])
        ktags = [(tag, diff) for tag in ktags]
        rktags = [(tag, diff) for tag in rktags]
        context_fac = KnowledgeFactor(ktags, rktags)
        question_fac = KnowledgeFactor.merge(factors)
        combine_info[cid] = KnowledgeFactor.merge([context_fac, question_fac])
    cursor.close()
    return dump_factor(redis_db, context_type, combine_info, origin)


def get_cloze_info(conn_func, redis_db, knowledge, related_knowledge, origin):
    return get_combine_info1(conn_func, redis_db, CLOZE_CONF,
                             knowledge, related_knowledge, origin)


def get_reading_info(conn_func, redis_db, knowledge, related_knowledge, origin):
    res = []
    for conf in READING_CONFS[0]:
        res.extend(get_combine_info1(conn_func, redis_db, conf,
                                     knowledge, related_knowledge, origin))
    for conf in READING_CONFS[1]:
        res.extend(get_combine_info2(conn_func, redis_db, conf,
                                     knowledge, related_knowledge, origin))
    return res


def get_listen_info(conn_func, redis_db, knowledge, related_knowledge, origin):
    res = []
    for conf in LISTEN_CONFS:
        res.extend(get_combine_info1(conn_func, redis_db, conf,
                                     knowledge, related_knowledge, origin))
    return res


def get_knowledge_index(redis_db):
    fields = redis_db.hkeys(ENGLISH_QUESTION_FACTOR_KEY)
    k_idx = {}
    rk_idx = {}
    for field in fields:
        qtype, qid = map(int, field.split(':'))
        score = redis_db.hget(ENGLISH_QUESTION_FACTOR_KEY, field)
        if not score:
            continue
        score = [item.split(':') for item in score.split('|')]
        score = [(cat, int(tag), float(d)) for cat, tag, d in score]
        for cat, tag, d in score:
            if cat == '1':
                if tag not in k_idx:
                    k_idx[tag] = {}
                k_idx[tag].setdefault(qtype, set()).add((qid, d))
            elif cat == '2':
                if tag not in rk_idx:
                    rk_idx[tag] = {}
                rk_idx[tag].setdefault(qtype, set()).add((qid, d))
    return (k_idx, rk_idx)


def set_knowledge_index(kidx, redis_db, redis_key):
    for tag, items in kidx.iteritems():
        for qtype, qset in items.iteritems():
            key = redis_key % (tag, qtype)
            value = "|".join([(str(qid) + ':' + str(d)) for qid, d in qset])
            redis_db.set(key, value)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    conn_func = get_banker_dev_conn if args.debug else get_banker_conn
    redis_db = redis_debug if args.debug else redis_online
    remove_unapproved_questions(conn_func, redis_db)

    origin = get_origin(conn_func)
    knowledge = get_knowledge(conn_func, 'knowledge_tag')
    related_knowledge = get_knowledge(conn_func, 'related_knowledge_tag')

    choice_idx = get_single_choice_info(conn_func, redis_db,
                                        knowledge, related_knowledge, origin)
    print 'single choice ok'
    cloze_idx = get_cloze_info(conn_func, redis_db,
                               knowledge, related_knowledge, origin)
    print 'cloze ok'
    reading_idx = get_reading_info(conn_func, redis_db,
                                   knowledge, related_knowledge, origin)
    print 'reading ok'
    listen_idx = get_listen_info(conn_func, redis_db,
                                 knowledge, related_knowledge, origin)
    print 'listen ok'

    question_index = choice_idx + cloze_idx + reading_idx + listen_idx
    dump_question_index(redis_db, question_index)

    k_idx, rk_idx = get_knowledge_index(redis_db)
    set_knowledge_index(k_idx, redis_db, KNOWLEDGE_INV_INDEX)
    set_knowledge_index(rk_idx, redis_db, RELATED_KNOWLEDGE_INV_INDEX)

