# coding: utf-8

from __future__ import absolute_import

import pandas as pd
import json

from utils.meta import AlgMeta
from adaptive.maths_meta import MathMeta
from maths.knowledge_model import load_question_factor
from adaptive.card_factor import load_card_factor
from utils.data_store import flush_redis


def merge_graph_matrix(X, Y):
    for k, v in Y.iteritems():
        X.setdefault(k, {})
        for m, w in v.iteritems():
            X[k][m] = 1


def transpose_matrix(mat_str):
    mat = json.loads(mat_str)
    mat_t = {}
    for k, v in mat.iteritems():
        for m, d in v.iteritems():
            mat_t.setdefault(m, {})[k] = d
    return json.dumps(mat_t)


class ConceptGraphBase(AlgMeta):

    def __init__(self, *args, **kwargs):
        super(ConceptGraphBase, self).__init__(*args, **kwargs)
        self.knowledge_mat = {}
        self.method_mat = {}
        self.knowledge_method_mat = {}

    def emerge_item_hierarchy(self, table, item_type='knowledge'):
        conn = self.conn_func()
        sql = 'select id item_id, parent_id from %s where level > 1'
        K = pd.read_sql_query(sql % table, conn)
        mat = self.method_mat if item_type == 'method' else self.knowledge_mat
        for _, row in K.iterrows():
            item_id, parent_id = map(int, row)
            mat.setdefault(item_id, {})[parent_id] = 1
            mat.setdefault(parent_id, {})[item_id] = 1

    def emerge_question_factor(self, factor_list):
        for item_factor in factor_list:
            k_mat, m_mat, k_m_mat, diff = item_factor
            merge_graph_matrix(self.knowledge_mat, k_mat)
            merge_graph_matrix(self.method_mat, m_mat)
            merge_graph_matrix(self.knowledge_method_mat, k_m_mat)

    def emerge_card_factor(self, factor_list):
        for card_factor in factor_list:
            merge_graph_matrix(self.knowledge_mat, card_factor)

    def build_concept_graph(self):
        self.emerge_item_hierarchy(self.knowledge_table)
        self.emerge_item_hierarchy(self.solution_method_table, 'method')

        keys = self.get_all_question_factor_keys()
        fac_list = [load_question_factor(self.redis_db, key) for key in keys]
        self.emerge_question_factor(fac_list)

        keys = self.get_all_card_factor_keys()
        fac_list = [load_card_factor(self.redis_db, key) for key in keys]
        self.emerge_card_factor(fac_list)

    def dump_concept_graph(self):
        k_str = json.dumps(self.knowledge_mat)
        m_str = json.dumps(self.method_mat)
        k_m_str = json.dumps(self.knowledge_method_mat)
        key = self.CONCEPT_GRAPH
        value = [k_str, m_str, k_m_str]
        flush_redis(self.redis_db, key, value)
        key = self.CONCEPT_GRAPH_TRANSPOSE
        value = map(transpose_matrix, value)
        flush_redis(self.redis_db, key, value)


class MathConceptGraph(MathMeta, ConceptGraphBase):
    pass

