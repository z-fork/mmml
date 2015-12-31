# coding: utf-8

from collections import OrderedDict

K_CAPABILITY_TYPE = 1
K_EXPERIENCE_TYPE = 2

# %s/%s: EXAM_KIND/APP_QUESTION_KIND
# APP_QUESTION_KIND 中 0 表示总榜
CAPABILITY_CHART_KEY = '/alg/chart/capability/%s/%s'
EXPERIENCE_CHART_KEY = '/alg/chart/experience/%s/%s'

# %s: exam_kind
MATH_CAPABILITY_CHART_KEY = '/alg/math/chart/capability/%s'
MATH_EXPERIENCE_CHART_KEY = '/alg/math/chart/experience/%s'

#---------------------------------------------

K_LISTENING = 1008 # 听力大类
K_LISTEN_DICTATION = 1009
K_LISTEN_DICTATION_ANSWER = 1010

K_SHORT_DIALOG = 1012  # 听力-短对话
K_SHORT_DIALOG_QUESTION = 1013  # 听力-短对话-问题
K_LONG_DIALOG = 1014  # 听力-长对话
K_TRANSLATION = 1016  # 翻译
K_SINGLE_CHOICE = 1017 # 单项选择题
K_COMPOSITION = 1019
#----------------------------------------------------

K_SINGLE_CHOICE = 1017 # 单项选择题

K_CLOZE = 1047 # 完形
K_CLOZE_QUESTION = 1048

#-------------------------

K_READING = 1077 # 阅读大类
K_READING_IN_DEPTH = 1020 # 仔细阅读
K_READING_QUESTION = 1021 # 仔细阅读-问题
K_OBJECT_CHOICE = 1022 # 听力-客观单选题
K_OBJECT_CHOICE_QUESTION = 1023 # 听力-客观单选题-问题
K_ESSAY = 1025
K_ESSAY_QUESTION = 1026
K_LONG_DIALOG_QUESTION = 1028  # 听力-长对话-问题

K_SELECT_WORD = 1011  # 选词填空(共享答案的选择题)
K_SELECT_WORD_QUESTION = 1031 # 选词填空-问题

K_CONTEXT_COMPLETE = 1034 # 补全对话/短文
K_COMPLETE_QUESTION = 1035 # 补全对话/短文-问题
K_INFORMATION = 1037 # 主观听取信息
K_INFORMATION_ANSWER = 1038 # 主观听取信息-答案

K_PARAGRAPH_INFO_MATCH = 1039 # 段落信息匹配
K_PARAGRAPH_INFO_MATCH_QUESTION = 1040 # 段落信息匹配-问题

K_TASK = 1041 # 任务型写作/阅读
K_TASK_QUESTION = 1042 # 任务型写作/阅读-问题

K_READ_EXPRESSION = 1043 # 阅读表达
K_READ_EXPRESSION_QUESTION = 1044 # 阅读表达-问题

K_PASSAGE_BLANK = 1045 # 短文填词&语法填空&补全对话
K_PASSAGE_BLANK_QUESTION = 1046 # 短文填词&语法填空&补全对话

K_JUDGE = 1058 # 判断型阅读
K_JUDGE_QUESTION = 1059 # 判断型阅读-问题

#-----------------------------------------------------

READING_IN_DEPTH_CONF = {
        'context_conf':{
            'qtype':K_READING_IN_DEPTH,
            'table':'context_choice_stem',
            'cid':'id'
        },
        'question_conf':{
            'qtype':K_READING_QUESTION,
            'table':'context_choice_question',
            'cid':'context_id',
            'qid':'id'
        }
}

JUDGE_CONF= {
        'context_conf':{
            'qtype':K_JUDGE,
            'table':'context_choice_stem',
            'cid':'id'
        },
        'question_conf':{
            'qtype':K_JUDGE_QUESTION,
            'table':'context_choice_question',
            'cid':'context_id',
            'qid':'id'
        }
}

SELECT_WORD_CONF = {
        'context_conf':{
            'qtype':K_SELECT_WORD,
            'table':'context_dictation',
            'cid':'id'
        },
        'question_conf':{
            'qtype':K_SELECT_WORD_QUESTION,
            'table':'context_dictation_question',
            'cid':'stem_id',
            'qid':'id'
        }
}

TASK_CONF = {
        'context_conf':{
            'qtype':K_TASK,
            'table':'context_dictation',
            'cid':'id'
        },
        'question_conf':{
            'qtype':K_TASK_QUESTION,
            'table':'context_dictation_question',
            'cid':'stem_id',
            'qid':'id'
        }
}

PASSAGE_BLANK_CONF = {
        'context_conf':{
            'qtype':K_PASSAGE_BLANK,
            'table':'context_dictation',
            'cid':'id'
        },
        'question_conf':{
            'qtype':K_PASSAGE_BLANK_QUESTION,
            'table':'context_dictation_question',
            'cid':'stem_id',
            'qid':'id'
        }
}

READ_EXPRESSION_CONF = {
        'context_conf':{
            'qtype':K_READ_EXPRESSION,
            'table':'context_dictation',
            'cid':'id'
        },
        'question_conf':{
            'qtype':K_READ_EXPRESSION_QUESTION,
            'table':'context_dictation_question',
            'cid':'stem_id',
            'qid':'id'
        }
}

PARAGRAPH_INFO_MATCH_CONF = {
        'context_conf':{
            'qtype':K_PARAGRAPH_INFO_MATCH,
            'table':'disjoint_choice_context',
            'cid':'id',
        },
        'question_conf':{
            'qtype':K_PARAGRAPH_INFO_MATCH_QUESTION,
            'table':'disjoint_choice_question',
            'cid':'context_id',
            'qid':'id',
        }
}

CONTEXT_COMPLETE_CONF = {
        'context_conf':{
            'qtype':K_CONTEXT_COMPLETE,
            'table':'disjoint_choice_context',
            'cid':'id',
        },
        'question_conf':{
            'qtype':K_COMPLETE_QUESTION,
            'table':'disjoint_choice_question',
            'cid':'context_id',
            'qid':'id',
        }
}

READING_CONFS = [
        [READING_IN_DEPTH_CONF, JUDGE_CONF, SELECT_WORD_CONF,
            TASK_CONF, PASSAGE_BLANK_CONF, READ_EXPRESSION_CONF],
        [PARAGRAPH_INFO_MATCH_CONF, CONTEXT_COMPLETE_CONF]
]

#---------------------


CLOZE_CONF = {
        'context_conf':{
            'qtype':K_CLOZE,
            'table':'context_choice_stem',
            'cid':'id'
        },
        'question_conf':{
            'qtype':K_CLOZE_QUESTION,
            'table':'context_choice_question',
            'cid':'context_id',
            'qid':'id'
        }
}

#----------------------------------

SHORT_DIALOG_CONF = {
        'context_conf':{
            'qtype':K_SHORT_DIALOG,
            'table':'listen_choice_stem',
            'cid':'id'
        },
        'question_conf':{
            'qtype':K_SHORT_DIALOG_QUESTION,
            'table':'listen_choice_question',
            'cid':'stem_id',
            'qid':'id'
        }
}


LONG_DIALOG_CONF = {
        'context_conf':{
            'qtype':K_LONG_DIALOG,
            'table':'listen_choice_stem',
            'cid':'id'
        },
        'question_conf':{
            'qtype':K_LONG_DIALOG_QUESTION,
            'table':'listen_choice_question',
            'cid':'stem_id',
            'qid':'id'
        }
}

ESSAY_CONF = {
        'context_conf':{
            'qtype':K_ESSAY,
            'table':'listen_choice_stem',
            'cid':'id'
        },
        'question_conf':{
            'qtype':K_ESSAY_QUESTION,
            'table':'listen_choice_question',
            'cid':'stem_id',
            'qid':'id'
        }
}

OBJECT_CHOICE_CONF = {
        'context_conf':{
            'qtype':K_OBJECT_CHOICE,
            'table':'listen_choice_stem',
            'cid':'id'
        },
        'question_conf':{
            'qtype':K_OBJECT_CHOICE_QUESTION,
            'table':'listen_choice_question',
            'cid':'stem_id',
            'qid':'id'
        }
}


LISTEN_CONFS = [
        SHORT_DIALOG_CONF,
        LONG_DIALOG_CONF,
        ESSAY_CONF,
        #LISTEN_DICTATION_CONF,
        OBJECT_CHOICE_CONF,
        #INFORMATION_CONF
]

# --------------------------------------

# 为了代码兼容方便，对于非组合题型的单选也构建一个conf
SINGLE_CHOICE_CONFS = {
        'context_conf':{
            'qtype':K_SINGLE_CHOICE,
            'table':'choice_stem',
            'cid':'id'
        },
        'question_conf':{
            'qtype':K_SINGLE_CHOICE,
            'table':'choice_stem',
            'cid':'id',
            'qid':'id'
        }
}

# --------------------------------------

QUESTION_TYPE_PRACTICE = 1 # 练题模式
QUESTION_TYPE_CHALLENGE = 2 # 挑战模式

# 大题类型到小题题型映射
QUESTION_SUBTYPE_MAP = {
        K_READING_IN_DEPTH: K_READING_QUESTION,
        K_CLOZE: K_CLOZE_QUESTION,
        K_SHORT_DIALOG: K_SHORT_DIALOG_QUESTION,
        K_LONG_DIALOG: K_LONG_DIALOG_QUESTION,
        K_ESSAY: K_ESSAY_QUESTION,
        K_OBJECT_CHOICE: K_OBJECT_CHOICE_QUESTION,
        K_SINGLE_CHOICE: K_SINGLE_CHOICE
}


#---------------------------------------

CONF_MAP = {
        K_SINGLE_CHOICE: SINGLE_CHOICE_CONFS,
        K_READING_IN_DEPTH: READING_IN_DEPTH_CONF,
        K_CLOZE: CLOZE_CONF,
        K_SHORT_DIALOG: SHORT_DIALOG_CONF,
        K_LONG_DIALOG: LONG_DIALOG_CONF,
        K_ESSAY: ESSAY_CONF,
        K_OBJECT_CHOICE: OBJECT_CHOICE_CONF
}


APP_QUESTION_KIND_ALL = 0
# App定义的四种大题型
APP_QUESTION_KIND_READ = 100 # 阅读理解
APP_QUESTION_KIND_CLOZE = 101 # 完形填空
APP_QUESTION_KIND_SINGLE = 102 # 单选
APP_QUESTION_KIND_LISTEN = 103 # 听力理解

APP_QUESTION_KIND_MAP = {
        APP_QUESTION_KIND_READ: [K_READING_IN_DEPTH],
        APP_QUESTION_KIND_CLOZE: [K_CLOZE],
        APP_QUESTION_KIND_SINGLE: [K_SINGLE_CHOICE],
        APP_QUESTION_KIND_LISTEN: [K_SHORT_DIALOG, K_LONG_DIALOG,
                                   K_ESSAY, K_OBJECT_CHOICE]
}

# 年级常量
GRADE_COLLEGE = 1 # 大学
GRADE_HIGH = 2 # 高中
GRADE_HIGH_III = 3 # 高三
GRADE_HIGH_III_ARTS = 11
GRADE_HIGH_III_SCIENCE = 12
GRADE_HIGH_III_GENERAL = 13
GRADE_HIGH_II = 4 # 高二
GRADE_HIGH_I = 5 # 高一
GRADE_JUNIOR = 6 # 初中
GRADE_JUNIOR_IV = 20  # 初四
GRADE_JUNIOR_III = 7 # 初三
GRADE_JUNIOR_II = 8 # 初二
GRADE_JUNIOR_I = 9 # 初一
GRADE_PRIMARY = 10 # 小学
GRADE_PRIMARY_VI = 14  # 小六
GRADE_PRIMARY_V = 15  # 小五
GRADE_PRIMARY_IV = 16  # 小四
GRADE_PRIMARY_III = 17  # 小三
GRADE_PRIMARY_II = 18  # 小二
GRADE_PRIMARY_I = 19  # 小一

PRIMARY_SCHOOL_GRADES = set([
    GRADE_PRIMARY, GRADE_PRIMARY_I, GRADE_PRIMARY_II, GRADE_PRIMARY_III,
    GRADE_PRIMARY_IV, GRADE_PRIMARY_V, GRADE_PRIMARY_VI])

JUNIOR_SCHOOL_GRADES = set([
    GRADE_JUNIOR, GRADE_JUNIOR_I, GRADE_JUNIOR_II, GRADE_JUNIOR_III,
    GRADE_JUNIOR_IV])

HIGH_SCHOOL_GRADES = set([
    GRADE_HIGH, GRADE_HIGH_I, GRADE_HIGH_II, GRADE_HIGH_III,
    GRADE_HIGH_III_ARTS, GRADE_HIGH_III_SCIENCE, GRADE_HIGH_III_GENERAL])

GRADES = OrderedDict([
    (GRADE_COLLEGE, "大学"),
    (GRADE_HIGH, "高中"),
    (GRADE_HIGH_III, "高三"),
    (GRADE_HIGH_II, "高二"),
    (GRADE_HIGH_I, "高一"),
    (GRADE_JUNIOR, "初中"),
    (GRADE_JUNIOR_IV, "初四"),
    (GRADE_JUNIOR_III, "初三"),
    (GRADE_JUNIOR_II, "初二"),
    (GRADE_JUNIOR_I, "初一"),
    (GRADE_PRIMARY, "小学"),
    (GRADE_HIGH_III_ARTS, "高三文科"),
    (GRADE_HIGH_III_SCIENCE, "高三理科"),
    (GRADE_HIGH_III_GENERAL, "高三综合"),
])

# 考试类型：针对 app 练题的考试类型
# 区别于 banker 中的考试类型(试卷类型)
EXAM_KIND_DEFAULT = 0

EXAM_KIND_GK = 3
EXAM_KIND_ZK = 4
EXAM_KIND_JUNIOR_I = 5
EXAM_KIND_JUNIOR_II = 6
EXAM_KIND_HIGH_I = 7
EXAM_KIND_HIGH_II = 8

EXAM_KIND_INV_MAP = {
    EXAM_KIND_GK: [GRADE_HIGH, GRADE_HIGH_III, GRADE_HIGH_III_GENERAL,
                    GRADE_HIGH_III_SCIENCE, GRADE_HIGH_III_ARTS],
    EXAM_KIND_ZK: [GRADE_JUNIOR, GRADE_JUNIOR_III, GRADE_JUNIOR_IV],
    EXAM_KIND_JUNIOR_I: [GRADE_JUNIOR_I],
    EXAM_KIND_JUNIOR_II: [GRADE_JUNIOR_II],
    EXAM_KIND_HIGH_I: [GRADE_HIGH_I],
    EXAM_KIND_HIGH_II: [GRADE_HIGH_II]
}

EXAM_KIND_MAP = {grade: exam_kind for exam_kind, grades
                 in EXAM_KIND_INV_MAP.iteritems() for grade in grades}

# 数学考试类型：针对 app 端练题/能力值/排行榜
MATH_EXAM_KIND_DEFAULT = 0
MATH_EXAM_KIND_ZK = 1
MATH_EXAM_KIND_GK = 2
MATH_EXAM_KIND_GK_ARTS = 3
MATH_EXAM_KIND_JUNIOR_I = 4
MATH_EXAM_KIND_JUNIOR_II = 5
MATH_EXAM_KIND_HIGH_I = 6
MATH_EXAM_KIND_HIGH_II = 7

MATH_EXAM_KINDS = [
        MATH_EXAM_KIND_ZK, MATH_EXAM_KIND_GK, MATH_EXAM_KIND_GK_ARTS,
        MATH_EXAM_KIND_JUNIOR_I, MATH_EXAM_KIND_JUNIOR_II,
        MATH_EXAM_KIND_HIGH_I, MATH_EXAM_KIND_HIGH_II]

MATH_EXAM_KIND_INV_MAP = {
        MATH_EXAM_KIND_ZK: [GRADE_JUNIOR, GRADE_JUNIOR_III, GRADE_JUNIOR_IV],
        MATH_EXAM_KIND_GK: [GRADE_HIGH, GRADE_HIGH_III,
                            GRADE_HIGH_III_SCIENCE, GRADE_HIGH_III_GENERAL],
        MATH_EXAM_KIND_GK_ARTS: [GRADE_HIGH_III_ARTS],
        MATH_EXAM_KIND_JUNIOR_I: [GRADE_JUNIOR_I],
        MATH_EXAM_KIND_JUNIOR_II: [GRADE_JUNIOR_II],
        MATH_EXAM_KIND_HIGH_I: [GRADE_HIGH_I],
        MATH_EXAM_KIND_HIGH_II: [GRADE_HIGH_II]
}

MATH_EXAM_KIND_MAP = {grade: math_exam_kind for math_exam_kind, grades
                      in MATH_EXAM_KIND_INV_MAP.iteritems() for grade in grades}

# 与数学一级知识点 module_id 对应，在计算总体能力/经验值时用到
MODULE_ALL = 0

# 数学分科
MATH_CATEGORY_W = 50
MATH_CATEGORY_L = 51
MATH_CATEGORY_Z = 52

#--------------------------

# 理科考试类型
SCI_EXAM_KIND_DEFAULT = 0
SCI_EXAM_KIND_GK = 1
SCI_EXAM_KIND_HIGH_II = 2
SCI_EXAM_KIND_HIGH_I = 3
SCI_EXAM_KIND_ZK = 4
SCI_EXAM_KIND_JUNIOR_II = 5
SCI_EXAM_KIND_JUNIOR_I = 6

SCI_EXAM_KIND_INV_MAP = {
    SCI_EXAM_KIND_GK: [GRADE_HIGH, GRADE_HIGH_III,
                       GRADE_HIGH_III_SCIENCE, GRADE_HIGH_III_GENERAL],
    SCI_EXAM_KIND_HIGH_II: [GRADE_HIGH_II],
    SCI_EXAM_KIND_HIGH_I: [GRADE_HIGH_I],
    SCI_EXAM_KIND_ZK: [GRADE_JUNIOR,
                       GRADE_JUNIOR_IV, GRADE_JUNIOR_III],
    SCI_EXAM_KIND_JUNIOR_II: [GRADE_JUNIOR_II],
    SCI_EXAM_KIND_JUNIOR_I: [GRADE_JUNIOR_I]
}

SCI_EXAM_KIND_MAP = {grade: sci_exam_kind for sci_exam_kind, grades
                     in SCI_EXAM_KIND_INV_MAP.iteritems() for grade in grades}

# TODO 统一各学科的 EXAM_KIND 表示
# 文科考试类型
ART_EXAM_KIND_DEFAULT = 0
ART_EXAM_KIND_GK = 1
ART_EXAM_KIND_HIGH_II = 2
ART_EXAM_KIND_HIGH_I = 3
ART_EXAM_KIND_ZK = 4
ART_EXAM_KIND_JUNIOR_II = 5
ART_EXAM_KIND_JUNIOR_I = 6

ART_EXAM_KIND_INV_MAP = {
    ART_EXAM_KIND_GK: [GRADE_HIGH, GRADE_HIGH_III, GRADE_HIGH_III_SCIENCE,
                       GRADE_HIGH_III_ARTS, GRADE_HIGH_III_GENERAL],
    ART_EXAM_KIND_HIGH_II: [GRADE_HIGH_II],
    ART_EXAM_KIND_HIGH_I: [GRADE_HIGH_I],
    ART_EXAM_KIND_ZK: [GRADE_JUNIOR,
                       GRADE_JUNIOR_IV, GRADE_JUNIOR_III],
    ART_EXAM_KIND_JUNIOR_II: [GRADE_JUNIOR_II],
    ART_EXAM_KIND_JUNIOR_I: [GRADE_JUNIOR_I]
}

ART_EXAM_KIND_MAP = {grade: art_exam_kind for art_exam_kind, grades
                     in ART_EXAM_KIND_INV_MAP.iteritems() for grade in grades}

#-----------------------

# 题目审核状态
K_EDITING = 3000
K_SUBMITTED = 3001
K_CHECKED = 3002
K_APPROVED = 3003
K_DISCARDED = 3004
K_REJECTED = 3005

# 学科
SUBJECT_ALL = 0
SUBJECT_ENGLISH = 1
SUBJECT_MATH = 2
SUBJECT_CHINESE = 3
SUBJECT_PHYSICS = 4
SUBJECT_CHEMISTRY = 5
SUBJECT_GEOGRAPHY = 6
SUBJECT_HISTORY = 7
SUBJECT_POLITICS = 8
SUBJECT_BIOLOGY = 9

QUESTION_RECORD_STATUS_EMPTY = 0  # 未作答
QUESTION_RECORD_STATUS_WRONG = 1  # 做错
QUESTION_RECORD_STATUS_RIGHT = 2  # 做对了

