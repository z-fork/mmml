# coding: utf-8

from __future__ import absolute_import

from utils.meta import construct_meta
from art.consts import ART_CONSTS, subject_name2id

meta_info = {
    0: {
        'subject_name': '%s',
        'knowledge_table': '%s_knowledge',
        'knowledge_tag_table': '%s_knowledge_tag',
        'related_knowledge_tag_table': '%s_related_knowledge_tag',
        'origin_table': '%s_origin',
        'choice_table': '%s_choice',
        'material_table': '%s_material',
        'material_question_table': '%s_material_question',
        'reading_table': '%s_reading',
        'reading_question_table': '%s_reading_question',

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

    'K_MATERIAL': 'K_%s_MATERIAL',
    'K_MATERIAL_QUESTION': 'K_%s_MATERIAL_QUESTION',

    'K_READING': 'K_%s_READING',
    'K_READING_QUESTION': 'K_%s_READING_QUESTION',
}

kind_map_info = {
    'QUESTION_KIND_MAP': {
        'K_%s_CHOICE': 'K_%s_CHOICE',
        'K_%s_MATERIAL_QUESTION': 'K_%s_MATERIAL',
        'K_%s_READING_QUESTION': 'K_%s_READING'
    }
}


ChineseMeta = construct_meta('ChineseMeta', 'chinese', ART_CONSTS,
        meta_info, consts_info, kind_map_info, subject_name2id)
HistoryMeta = construct_meta('HistoryMeta', 'history', ART_CONSTS,
        meta_info, consts_info, kind_map_info, subject_name2id)
GeographyMeta = construct_meta('GeographyMeta', 'geography', ART_CONSTS,
        meta_info, consts_info, kind_map_info, subject_name2id)
PoliticsMeta = construct_meta('PoliticsMeta', 'politics', ART_CONSTS,
        meta_info, consts_info, kind_map_info, subject_name2id)

