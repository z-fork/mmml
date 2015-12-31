# coding: utf-8

from __future__ import absolute_import

import numpy as np
import pandas as pd
from patsy import dmatrices
from sklearn.linear_model import LogisticRegression

LR_FORMULA = ('correct ~ C(qtype) + seconds + C(gender) + C(location_id) '
              '+ u_avg_time + u_avg_correct + n_question + diff '
              '+ C(exam_type) + q_avg_time + q_avg_correct')


def get_train_data(data_path):
    df = pd.read_csv(data_path, sep='\t', header=None)
    df.columns = ['uid', 'qtype', 'qid', 'sub_id', 'correct',
                  'seconds', 'gender', 'location_id', 'u_avg_time',
                  'u_avg_correct', 'n_question', 'diff', 'exam_type',
                  'q_avg_time', 'q_avg_correct']
    return df


def get_design_info(data_path):
    '''返回 LR_FORMULA 对应的 design_info, 重构数据集时需要用'''
    data = get_train_data(data_path)
    y, X = dmatrices(LR_FORMULA, data)
    return X.design_info


def logistic_regression(data):
    y, X = dmatrices(LR_FORMULA, data)
    y = np.ravel(y)
    model = LogisticRegression(penalty='l1', C=0.1, fit_intercept=True)
    model = model.fit(X, y)
    print model.score(X, y)
    return model

