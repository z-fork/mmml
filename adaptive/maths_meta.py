# coding: utf-8

from __future__ import absolute_import

from utils.meta import construct_meta
from science.meta import consts_info, kind_map_info
from science.consts import SCIENCE_CONSTS, subject_name2id

math_meta_info = {
    0: {
        'subject_name': '%s',
        'origin_table': '%s_origin',
        'knowledge_table': '%s_knowledge',
        'knowledge_tag_table': '%s_knowledge_tag',
        'solution_method_table': '%s_solution_method',
        'solution_method_tag_table': '%s_solution_method_tag',
        'analysis_table': '%s_analysis',
        'solution_table': '%s_solution',
        'choice_table': '%s_choice_stem',
        'blank_table': '%s_fill_blank_stem',
        'blank_question_table': '%s_fill_blank_question',
        'response_table': '%s_response_stem',
        'response_question_table': '%s_response_question',

        # 一级知识点包含的子知识点，出题过滤时用
        # subject_name, field: "module_id", 结果为子知识点 list
        'KNOWLEDGE_TREE_INDEX': '/alg/%s/knowledge_tree',
        # KNOWLEDGE_INV_INDEX 所有知识点，出题时使用
        # subject_name, field: "knowledge_id:qtype"
        'KNOWLEDGE_INV_INDEX': '/alg/%s/knowledge_index',

        # QUESTION_INV_INDEX 只有一级知识点，作为索引取题时使用
        # subject_name, field: "exam_kind:qtype:knowledge_id"
        'QUESTION_INV_INDEX': '/alg/%s/question_index',
        # CARD_INV_INDEX 根据 book_id, week, card_type 取 card; 用于自适应出题
        # hset, field: "book_id:week:card_type"
        'CARD_INV_INDEX': '/alg/%s/card_index',

        # 整体知识图谱
        'CONCEPT_GRAPH': '/alg/%s/concept_graph',
        'CONCEPT_GRAPH_TRANSPOSE': '/alg/%s/concept_graph_transpose',

        # WEEK_CONCEPT_INV_INDEX 根据 book_id, week 取该周卡片中涉及的知识点
        # hset, field: "book_id:week", value: "knowledge_id|...|knowledge_id"
        'WEEK_CONCEPT_INV_INDEX': '/alg/%s/week_concept_index'
    },

    1: {
        'USER_FACTOR_KEY': '/alg/%s/user_factor/%s', # user_id
        'ADAPTIVE_USER_FACTOR_KEY': '/alg/%s/adaptive_user_factor/%s'  # user_id
    },

    2: {
        'QUESTION_FACTOR_KEY': '/alg/%s/question_factor/%s/%s', # qtype, qid
        'CARD_FACTOR_KEY': '/alg/%s/card_factor/%s/%s', # card_type, card_id

        # 自适应出题从 concept_graph 到 item 索引
        # 参数为系数矩阵坐标 x:id, x = k 知识点, x = m 解题方法
        # 值为 kind:id 列表, 比如 qtype:qid 或者 card_type:card_id
        'CONCEPT_QUESTION_INDEX': '/alg/%s/concept_inv_index/question/%s/%s',
        'CONCEPT_CARD_INDEX': '/alg/%s/concept_inv_index/card/%s/%s'
    }
}


_MathMeta = construct_meta('_MathMeta', 'math', SCIENCE_CONSTS, math_meta_info,
                           consts_info, kind_map_info, subject_name2id)


class MathMeta(_MathMeta):

    def get_all_question_factor_keys(self):
        keys = set()
        fields = self.redis_db.hkeys(self.QUESTION_INV_INDEX)
        for field in fields:
            _, qtype, _ = field.split(':')
            qids = self.redis_db.hget(self.QUESTION_INV_INDEX, field)
            if not qids:
                continue
            for qid in qids.split('|'):
                keys.add(self.QUESTION_FACTOR_KEY % (qtype, qid))
        return list(keys)

    def get_all_card_factor_keys(self):
        keys = set()
        fields = self.redis_db.hkeys(self.CARD_INV_INDEX)
        for field in fields:
            _, _, card_type = field.split(':')
            card_ids = self.redis_db.hget(self.CARD_INV_INDEX, field)
            if not card_ids:
                continue
            for card_id in card_ids.split('|'):
                keys.add(self.CARD_FACTOR_KEY % (card_type, card_id))
        return list(keys)

