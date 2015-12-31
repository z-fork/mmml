# coding: utf-8


def dump_vector(vec):
    return '' if not vec else "|".join(map(str, vec))


def load_vector(vec_str):
    return [] if not vec_str else map(int, vec_str.split('|'))


class ArtQuestionFactor(object):

    def __init__(self, difficulty=0):
        self.difficulty = difficulty
        self.knowledge_vec = []
        self.related_knowledge_vec = []

    def add_factor(self, question_info):
        k_vec, rk_vec, diff = question_info
        self.difficulty = int(diff)
        if k_vec:
            if isinstance(k_vec, set):
                k_vec = list(k_vec)
            self.knowledge_vec = k_vec[:]
        if rk_vec:
            if isinstance(rk_vec, set):
                rk_vec = list(rk_vec)
            self.related_knowledge_vec = rk_vec[:]

    def dump_factor(self):
        k_str = dump_vector(self.knowledge_vec)
        rk_str = dump_vector(self.related_knowledge_vec)
        return [k_str, rk_str, str(self.difficulty)]

    def load_factor(self, values):
        k_str, rk_str, diff = values
        self.knowledge_vec = load_vector(k_str)
        self.related_knowledge_vec = load_vector(rk_str)
        self.difficulty = int(diff)

