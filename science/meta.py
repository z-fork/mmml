# coding: utf-8

from __future__ import absolute_import

from utils.meta import construct_meta
from science.consts import SCIENCE_CONSTS, subject_name2id

meta_info = {
    0: {
        'subject_name': '%s',
        'knowledge_table': '%s_knowledge',
        'origin_table': '%s_origin',
        'knowledge_tag_table': '%s_knowledge_tag',
        'solution_method_tag_table': '%s_solution_method_tag',
        'analysis_table': '%s_analysis',
        'solution_table': '%s_solution',
        'choice_table': '%s_choice',
        'blank_table': '%s_blank',
        'blank_question_table': '%s_blank_question',
        'response_table': '%s_response',
        'response_question_table': '%s_response_question',

        # 一级知识点包含的子知识点，出题过滤时用
        # subject_name, field: "module_id", 结果为子知识点 list
        'KNOWLEDGE_TREE_INDEX': '/alg/%s/knowledge_tree',
        # KNOWLEDGE_INV_INDEX 所有知识点，出题时使用
        # subject_name, field: "knowledge_id:qtype"
        'KNOWLEDGE_INV_INDEX': '/alg/%s/knowledge_index',

        # QUESTION_INV_INDEX 只有一级知识点，作为索引取题时使用
        # subject_name, field: "exam_kind:qtype:knowledge_id"
        'QUESTION_INV_INDEX': '/alg/%s/question_index'
    },

    1: {
        'USER_FACTOR_KEY': '/alg/%s/user_factor/%s'  # user_id
    },

    2: {
        # qtype, qid
        'QUESTION_FACTOR_KEY': '/alg/%s/question_factor/%s/%s'
    }
}

consts_info = {
    'K_CHOICE': 'K_%s_CHOICE',
    'K_CHOICE_ANALYSIS': 'K_%s_CHOICE_ANALYSIS',

    'K_BLANK': 'K_%s_BLANK',
    'K_BLANK_QUESTION': 'K_%s_BLANK_QUESTION',
    'K_BLANK_ANALYSIS': 'K_%s_BLANK_ANALYSIS',

    'K_RESPONSE': 'K_%s_RESPONSE',
    'K_RESPONSE_QUESTION': 'K_%s_RESPONSE_QUESTION',
    'K_RESPONSE_ANALYSIS': 'K_%s_RESPONSE_ANALYSIS',
}

kind_map_info = {
    'QUESTION_KIND_MAP': {
        'K_%s_CHOICE': 'K_%s_CHOICE',
        'K_%s_BLANK_QUESTION': 'K_%s_BLANK',
        'K_%s_RESPONSE_QUESTION': 'K_%s_RESPONSE'
    },
    'ANALYSIS_KIND_MAP': {
        'K_%s_CHOICE_ANALYSIS': 'K_%s_CHOICE',
        'K_%s_BLANK_ANALYSIS': 'K_%s_BLANK',
        'K_%s_RESPONSE_ANALYSIS': 'K_%s_RESPONSE'
    }
}


PhysicsMeta = construct_meta('PhysicsMeta', 'physics', SCIENCE_CONSTS,
        meta_info, consts_info, kind_map_info, subject_name2id)
ChemistryMeta = construct_meta('ChemistryMeta', 'chemistry', SCIENCE_CONSTS,
        meta_info, consts_info, kind_map_info, subject_name2id)
BiologyMeta = construct_meta('BiologyMeta', 'biology', SCIENCE_CONSTS,
        meta_info, consts_info, kind_map_info, subject_name2id)

