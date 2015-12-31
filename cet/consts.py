# coding: utf-8

CET_RECORD_PATH = '/home/shenfei/data/dagobah/cet_question_record.csv'
BANKER_CET_RECORD_PATH = '/home/shenfei/data/dagobah/banker_cet_question_record.csv'

# 这里的 question_id 都是小题的 subtype:subid 形式
CET_MOCK_TEST_USER_FACTOR_KEY = '/alg/cet_mock/user_factor/%s'
CET_MOCK_TEST_QUESTION_FACTOR_KEY = '/alg/cet_mock/question_factor/%s'
CET_MOCK_TEST_MODEL_WEIGHT_KEY = '/alg/cet_mock/model_weight'
CET_MOCK_TEST_MODEL_BIAS_WEIGHT_KEY = '/alg/cet_mock/model_bias_weight'

CET_MOCK_TEST_USER_ESTIMATE_KEY = '/alg/cet_mock/user_estimate/%s'
# 为了出题方便，这里的 question_id 是大题 qtype:qid 的形式
CET_MOCK_TEST_QUESTION_ESTIMATE_KEY = '/alg/cet_mock/question_estimate/%s'

CET_MOCK_TEST_SCORE_MEAN = '/alg/cet_mock/score_mean/%s' # exam_kind
CET_MOCK_TEST_SCORE_SD = '/alg/cet_mock/score_sd/%s' # exam_kind
