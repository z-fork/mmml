# coding: utf-8

import json


def fill_matrix(X, tags1, tags2, weight):
    if tags1 == None or tags2 == None:
        return
    for k in tags1:
        X.setdefault(k, {})
        for m in tags2:
            X[k].setdefault(m, 0)
            # 不填充对角线
            if k != m: X[k][m] += weight


# inplace version
def merge_matrix(X, Y):
    for k, v in Y.iteritems():
        X.setdefault(k, {})
        for m, w in v.iteritems():
            X[k].setdefault(m, 0)
            X[k][m] += w


def matrix_normalize(X):
    if not X: return
    total = sum([w for k, v in X.iteritems() for m, w in v.iteritems()])
    for k, v in X.iteritems():
        for m in v:
            X[k][m] /= float(total)


def build_knowledge_method_matrix(analysis_steps):
    '''
    analysis_steps: [(knowledge_set, method_set), ...]
    '''
    knowledge_mat = {}
    method_mat = {}
    knowledge_method_mat = {}
    knowledge_set = set()
    method_set = set()

    for step in analysis_steps:
        kset, mset = step
        if kset != None: knowledge_set.update(kset)
        if mset != None: method_set.update(mset)
        fill_matrix(knowledge_mat, kset, kset, 1)
        fill_matrix(method_mat, mset, mset, 1)
        fill_matrix(knowledge_method_mat, kset, mset, 1)
    for ktag in knowledge_set:
        knowledge_mat[ktag][ktag] = 1
    for mtag in method_set:
        method_mat[mtag][mtag] = 1

    if len(analysis_steps) > 1:
        for i in range(len(analysis_steps) - 1):
            kset1, mset1 = analysis_steps[i]
            kset2, mset2 = analysis_steps[i + 1]
            fill_matrix(knowledge_mat, kset1, kset2, 1)
            fill_matrix(method_mat, mset1, mset2, 1)
    map(matrix_normalize, [knowledge_mat, method_mat, knowledge_method_mat])
    return knowledge_mat, method_mat, knowledge_method_mat


def load_matrix(x):
    res = {}
    y = json.loads(x)
    for k, v in y.iteritems():
        res[int(k)] = {}
        for m, w in v.iteritems():
            res[int(k)][int(m)] = w
    return res


class SciQuestionFactor(object):

    def __init__(self, difficulty=0):
        self.difficulty = difficulty
        self.knowledge_mat = {}
        self.method_mat = {}
        self.knowledge_method_mat = {}

    def add_factor(self, question_analysis):
        for analysis_steps in question_analysis:
            k_mat, m_mat, km_mat = build_knowledge_method_matrix(analysis_steps)
            merge_matrix(self.knowledge_mat, k_mat)
            merge_matrix(self.method_mat, m_mat)
            merge_matrix(self.knowledge_method_mat, km_mat)
        matrix_normalize(self.knowledge_mat)
        matrix_normalize(self.method_mat)
        matrix_normalize(self.knowledge_method_mat)

    def dump_factor(self):
        knowledge_str = json.dumps(self.knowledge_mat)
        method_str = json.dumps(self.method_mat)
        knowledge_method_str = json.dumps(self.knowledge_method_mat)
        return [knowledge_str, method_str, knowledge_method_str, str(self.difficulty)]

    def load_factor(self, values):
        knowledge_str, method_str, knowledge_method_str, diff = values
        self.knowledge_mat = load_matrix(knowledge_str)
        self.method_mat = load_matrix(method_str)
        self.knowledge_method_mat = load_matrix(knowledge_method_str)
        self.difficulty = int(diff)

