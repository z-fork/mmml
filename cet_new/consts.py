# coding: utf-8

from collections import OrderedDict

QUESTION_TYPE_PRACTICE = 1  # 练题模式
QUESTION_TYPE_CHALLENGE = 2  # 挑战模式
QUESTION_TYPE_REVIEW = 3  # 查看模式
QUESTION_TYPE_MOCK_EXAM = 4  # 模拟考试

QUESTION_TYPES = [
    (QUESTION_TYPE_PRACTICE, '练题模式'),
    (QUESTION_TYPE_CHALLENGE, '挑战模式'),
    (QUESTION_TYPE_REVIEW, '查看模式'),
    (QUESTION_TYPE_MOCK_EXAM, '模拟考试')
]

'''
四六级用到的题型常量, 四大类题型分组的常量以 K_XX_GROUP 表示

K_COMPOSITION_GROUP = 1
K_LISTEN_GROUP = 2
K_READING_GROUP = 3
K_TRANSLATION_GROUP = 4

K_COMPOSITION = 1019

K_SHORT_DIALOG = 1012  # 听力-短对话
K_LONG_DIALOG = 1014  # 听力-长对话
K_LONG_DIALOG_QUESTION = 1028  # 听力-长对话-问题
K_LISTEN_PASSAGE = 1025
K_LISTEN_PASSAGE_QUESTION = 1026
K_DICTATION = 1009 # 重写四六级题型中的短文听写
K_DICTATION_QUESTION = 1010

K_WORD_SELECT = 1011 # 重写四六级题型中的选词填空
K_WORD_SELECT_QUESTION = 1031
K_PARAGRAPH_INFO_MATCH = 1039  # 段落信息匹配
K_PARAGRAPH_INFO_MATCH_QUESTION = 1040  # 段落信息匹配-问题
K_READING_IN_DEPTH = 1020  # 仔细阅读
K_READING_QUESTION = 1021  # 仔细阅读-问题

K_TRANSLATION = 1016  # 翻译

'''

K_COMPOSITION_GROUP = 1
K_LISTEN_GROUP = 2
K_READING_GROUP = 3
K_TRANSLATION_GROUP = 4

# 题目类型
K_CHOICE_STEM = 1000

K_LISTENING = 1008  # 听力大类
K_LISTEN_DICTATION = 1009
K_LISTEN_DICTATION_ANSWER = 1010

K_DICTATION = 1009  # 重写四六级题型中的短文听写
K_DICTATION_QUESTION = 1010


K_WORD_SELECT = 1011  # 重写四六级题型中的选词填空
K_WORD_SELECT_QUESTION = 1031

K_SELECT_WORD = 1011  # 选词填空(共享答案的选择题)
K_SHORT_DIALOG = 1012  # 听力-短对话
K_SHORT_DIALOG_QUESTION = 1013  # 听力-短对话-问题
K_LONG_DIALOG = 1014  # 听力-长对话
K_TRANSLATION = 1016  # 翻译
K_SINGLE_CHOICE = 1017  # 单项选择题
K_COMPOSITION = 1019

K_READING = 1077  # 阅读大类
K_READING_IN_DEPTH = 1020  # 仔细阅读
K_READING_QUESTION = 1021  # 仔细阅读-问题
K_ESSAY = 1025
K_LISTEN_PASSAGE = 1025
K_ESSAY_QUESTION = 1026
K_LISTEN_PASSAGE_QUESTION = 1026
K_LONG_DIALOG_QUESTION = 1028  # 听力-长对话-问题
K_SELECT_WORD_QUESTION = 1031  # 选词填空-问题
K_CONTEXT_COMPLETE = 1034  # 补全对话/短文
K_COMPLETE_QUESTION = 1035  # 补全对话/短文-问题
K_INFORMATION = 1037  # 主观听取信息
K_INFORMATION_ANSWER = 1038  # 主观听取信息-答案

K_PARAGRAPH_INFO_MATCH = 1039  # 段落信息匹配
K_PARAGRAPH_INFO_MATCH_QUESTION = 1040  # 段落信息匹配-问题

K_TASK = 1041  # 任务型写作/阅读
K_TASK_QUESTION = 1042  # 任务型写作/阅读-问题

K_READ_EXPRESSION = 1043  # 阅读表达
K_READ_EXPRESSION_QUESTION = 1044  # 阅读表达-问题

K_PASSAGE_BLANK = 1045  # 短文填词&语法填空&补全对话
K_PASSAGE_BLANK_QUESTION = 1046  # 短文填词&语法填空&补全对话

K_CLOZE = 1047  # 完形填空
K_CLOZE_QUESTION = 1048

K_SENTENCE = 1083  # 大类 & 小类
K_SENTENCE_TRANSFORMATION = 1081  # 句型转换
K_SENTENCE_ANALYSIS = 1082  # 句子成分分析
K_SENTENCE_ANSWER = 1051  # 完成句子-答案
K_TRANSLATION_SENTENCE = 1052  # 单句翻译
K_TRANSLATION_SENTENCE_QUESTION = 1053  # 单句翻译-答案

K_SENTENCE_QUESTION = 1090

K_SELECT_WORD_DICTATION = 1054  # 选词填空-上下文填空题 (Note: 区分选词填空选择题)
K_SELECT_WORD_DICTATION_QUESTION = 1055  # 选词填空-上下文填空题-问题

K_DISJOINT_SELECT_WORD = 1073  # 选词填空，有公共选项，答案是文本形式
K_DISJOINT_SELECT_WORD_QUESTION = 1074  # 选词填空问题

K_COMPOSE_SENTENCE = 1056  # 连词成句
K_COMPOSE_SENTENCE_QUESTION = 1057  # 连词成句-答案

K_JUDGE = 1058  # 判断型阅读
K_JUDGE_QUESTION = 1059  # 判断型阅读-问题

K_IMAGE_DICTATION = 1061  # 根据图片写句子
K_IMAGE_DICTATION_QUESTION = 1062  # 根据图片写句子-问题

K_SPELL_WORD = 1064  # 单词拼写
K_SPELL_WORD_ANSWER = 1065  # 单词拼写-答案

K_DISJOINT_MULTI_CHOICE_CONTEXT = 1066  # 共享答案一问多空选择题
K_DISJOINT_MULTI_CHOICE_QUESTION = 1067  # 共享答案一问多空选择题-问题

K_CORRECTION = 1070  # 改错题
K_CORRECTION_ANSWER = 1071  # 改错题-答案

K_INFO_MATCH = 1084  # 信息匹配（主旨与段落匹配）
K_INFO_MATCH_QUESTION = 1085

K_IMPORTING_ENGLISH_STEM = 1111  # 从第三方数据库导入的英语题目

# -------华丽的分割线-------NOTE: 所有题型的KIND常量请写在该分割线上面------华丽的分割线----------

# 四六级题目类型
CET_QUESTION_KINDS = {
    K_COMPOSITION,
    K_SHORT_DIALOG,
    K_LONG_DIALOG,
    K_ESSAY,
    K_LISTEN_DICTATION,
    K_SELECT_WORD,
    K_PARAGRAPH_INFO_MATCH,
    K_READING_IN_DEPTH,
    K_TRANSLATION,
}

# 题目审核状态
K_EDITING = 3000
K_SUBMITTED = 3001
K_CHECKED = 3002
K_APPROVED = 3003
K_DISCARDED = 3004
K_REJECTED = 3005
K_REEDITING = 3012

K_STATE_DICT = {
    K_EDITING: "录入中",
    K_SUBMITTED: "待初审",
    K_CHECKED: "待复审",
    K_APPROVED: "已入库",
    K_DISCARDED: "已废除",
    K_REJECTED: "被驳回",
    K_REEDITING: "初审驳回",
}

# 来源类型
SOURCE_DEFAULT = 0
SOURCE_ZH_MATH = 1
SOURCE_ZH_ENGLISH = 2

SOURCE_TYPES = OrderedDict([
    (SOURCE_DEFAULT, '默认'),
    (SOURCE_ZH_MATH, '志鸿数学'),
    (SOURCE_ZH_ENGLISH, '志鸿英语'),
])

# 考试类型
EXAM_TYPE_DEFAULT = 0

EXAM_CET4 = 1
EXAM_CET4_MOCK = 2
EXAM_CET6 = 3
EXAM_CET6_MOCK = 4
EXAM_GK = 5
EXAM_GK_MOCK = 6
EXAM_ZK = 7
EXAM_ZK_MOCK = 8
EXAM_MID_TERM = 9
EXAM_MID_TERM_MOCK = 10
EXAM_MONTHLY = 11
EXAM_SYNC_TEST = 12
EXAM_HK = 13
EXAM_COMPETITION = 14
EXAM_MKZH = 15

EXAM_TYPES = OrderedDict([
    (EXAM_TYPE_DEFAULT, '无'),
    (EXAM_CET4, "四级真题"),
    (EXAM_CET4_MOCK, "四级模拟题"),
    (EXAM_CET6, "六级真题"),
    (EXAM_CET6_MOCK, "六级模拟题"),
    (EXAM_GK, "高考真题"),
    (EXAM_GK_MOCK, "高考模拟题"),
    (EXAM_ZK, "中考真题"),
    (EXAM_ZK_MOCK, "中考模拟题"),
    (EXAM_MID_TERM, "期中"),
    (EXAM_MID_TERM_MOCK, "期末"),
    (EXAM_MONTHLY, "月考"),
    (EXAM_SYNC_TEST, "同步测试"),
    (EXAM_HK, "会考"),
    (EXAM_COMPETITION, "竞赛题"),
    (EXAM_MKZH, "模块综合"),
])

OFFICIAL_EXAM_TYPES = OrderedDict([
    (EXAM_CET4, "四级真题"),
    (EXAM_CET6, "六级真题"),
])

CET_EXAM_TYPES = OrderedDict([
    (EXAM_TYPE_DEFAULT, '无'),
    (EXAM_CET4, "四级真题"),
    (EXAM_CET4_MOCK, "四级模拟题"),
    (EXAM_CET6, "六级真题"),
    (EXAM_CET6_MOCK, "六级模拟题"),
])

#----------------------------------------

QUESTION_CONF = {
    K_COMPOSITION:{
        'table':'composition',
        'question_table':None,
        'sub_type':None,
        'has_stem_difficulty':True
    },

    K_SHORT_DIALOG:{
        'table':'short_dialog',
        'question_table':None,
        'sub_type':None,
        'has_stem_difficulty':True
    },

    K_LONG_DIALOG:{
        'table':'long_dialog',
        'question_table':'long_dialog_question',
        'sub_type':K_LONG_DIALOG_QUESTION,
        'has_stem_difficulty':False
    },

    K_LISTEN_PASSAGE:{
        'table':'listen_passage',
        'question_table':'listen_passage_question',
        'sub_type':K_LISTEN_PASSAGE_QUESTION,
        'has_stem_difficulty':False
    },

    K_DICTATION:{
        'table':'dictation',
        'question_table':'dictation_question',
        'sub_type':K_DICTATION_QUESTION,
        'has_stem_difficulty':True
    },

    K_WORD_SELECT:{
        'table':'word_select',
        'question_table':'word_select_question',
        'sub_type':K_WORD_SELECT_QUESTION,
        'has_stem_difficulty':True
    },

    K_PARAGRAPH_INFO_MATCH:{
        'table':'info_match',
        'question_table':'info_match_question',
        'sub_type':K_PARAGRAPH_INFO_MATCH_QUESTION,
        'has_stem_difficulty':True
    },

    K_READING_IN_DEPTH:{
        'table':'intensive_reading',
        'question_table':'intensive_reading_question',
        'sub_type':K_READING_QUESTION,
        'has_stem_difficulty':True
    },

    K_TRANSLATION:{
        'table':'translation',
        'question_table':None,
        'sub_type':None,
        'has_stem_difficulty':True
    }
}

