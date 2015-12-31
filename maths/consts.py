# coding: utf-8

K_MATH_CHOICE = 2000
K_MATH_CHOICE_ANALYSIS = 2001

K_MATH_BLANK = 2002
K_MATH_BLANK_QUESTION = 2003
K_MATH_BLANK_ANALYSIS = 2004

K_MATH_RESPONSE = 2006
K_MATH_RESPONSE_QUESTION = 2007
K_MATH_RESPONSE_ANALYSIS = 2008

MATH_QUESTION_KIND_MAP = {
        K_MATH_CHOICE: K_MATH_CHOICE,
        K_MATH_BLANK_QUESTION: K_MATH_BLANK,
        K_MATH_RESPONSE_QUESTION: K_MATH_RESPONSE
}

MATH_ANALYSIS_KIND_MAP = {
        K_MATH_CHOICE_ANALYSIS: K_MATH_CHOICE,
        K_MATH_BLANK_ANALYSIS: K_MATH_BLANK,
        K_MATH_RESPONSE_ANALYSIS: K_MATH_RESPONSE
}

MATH_QUESTION_FACTOR_KEY = '/alg/math/question_factor/%s/%s' # qtype, qid

# MATH_QUESTION_INV_INDEX 只有一级知识点，作为索引取题时使用
# hset: field: "exam_kind:qtype:knowledge_id", value: "qid:qid..."
MATH_QUESTION_INV_INDEX = '/alg/math/question_index'
# MATH_QUESTION_INV_INDEX = '/alg/math/question_index/%s/%s/%s'

# MATH_KNOWLEDGE_INV_INDEX 所有知识点，出题时使用
# hset, field: "knowledge_id:qtype", value: "qid:qid..."
MATH_KNOWLEDGE_INV_INDEX = '/alg/math/knowledge_index'
# knowledge_id, qtype
# MATH_KNOWLEDGE_INV_INDEX = '/alg/math/knowledge/%s/qtype/%s'

# 数学一级知识点包含的子知识点，出题过滤时用
# field: module_id, value: 子知识点 list
MATH_KNOWLEDGE_TREE_INDEX = '/alg/math/knowledge_tree'
# MATH_KNOWLEDGE_TREE_INDEX = '/alg/math/knowledge_tree/%s'

QUESTION_TYPE_PRACTICE = 1 # 练题
QUESTION_TYPE_CHALLENGE = 2 # 挑战
QUESTION_TYPE_REVIEW = 3 # 查看

MATH_USER_FACTOR_KEY = '/alg/math/user_factor/%s' # user_id

