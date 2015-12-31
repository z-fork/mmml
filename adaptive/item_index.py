# coding: utf-8

from __future__ import absolute_import

from utils.meta import AlgMeta
from adaptive.maths_meta import MathMeta
from adaptive.card_factor import load_card_factor
from maths.knowledge_model import load_question_factor
from utils.data_store import flush_redis


def append_item_id(item_id, mat, inv_idx, cat1, cat2):
    '''
    将 item_id 插入 mat 中元素所表示的索引
    结果修改到 inv_idx
    '''
    for k, v in mat.iteritems():
        k1 = '%s%s' % (cat1, k)
        inv_idx.setdefault(k1, {})
        for m in v.keys():
            k2 = '%s%s' % (cat2, m)
            inv_idx[k1].setdefault(k2, []).append(item_id)


class ItemIndexBase(AlgMeta):

    def dump_question_inv_index(self):
        '''计算 concept_graph 中元素(顶点/边)到 question 的索引'''
        keys = self.get_all_question_factor_keys()
        res = {}
        for key in keys:
            qtype, qid = key.split('/')[-2:]
            item_id = '%s:%s' % (qtype, qid)
            qfactor = load_question_factor(self.redis_db, key)
            k_mat, m_mat, k_m_mat, diff = qfactor
            append_item_id(item_id, k_mat, res, 'k', 'k')
            append_item_id(item_id, m_mat, res, 'm', 'm')
            append_item_id(item_id, k_m_mat, res, 'k', 'm')

        for k1, v in res.iteritems():
            for k2, item_ids in v.iteritems():
                key = self.CONCEPT_QUESTION_INDEX % (k1, k2)
                flush_redis(self.redis_db, key, item_ids)

    def dump_card_inv_index(self):
        '''计算 concept_graph 中元素(顶点/边)到 card 的索引'''
        keys = self.get_all_card_factor_keys()
        res = {}
        for key in keys:
            card_type, card_id = key.split('/')[-2:]
            item_id = '%s:%s' % (card_type, card_id)
            k_mat = load_card_factor(self.redis_db, key)
            append_item_id(item_id, k_mat, res, 'k', 'k')

        for k1, v in res.iteritems():
            for k2, item_ids in v.iteritems():
                key = self.CONCEPT_CARD_INDEX % (k1, k2)
                flush_redis(self.redis_db, key, item_ids)


class MathItemIndex(MathMeta, ItemIndexBase):
    pass

