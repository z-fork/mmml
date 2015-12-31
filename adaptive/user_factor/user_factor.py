# coding: utf-8

from __future__ import absolute_import
import json

import pandas as pd

from utils.meta import AlgMeta
from adaptive.maths_meta import MathMeta
from utils.data_store import flush_redis


def score2mat(score):
    if not score:
        return {}
    x = [item.split(':') for item in score.split('|')]
    mat = {}
    for item in x:
        tag, d = map(int, item)
        mat[tag] = {tag:d}
    return mat


def convert_user_factor(redis_db, key):
    res = redis_db.lrange(key, 0, -1)
    if not res:
        return None
    k_mat, m_mat = map(score2mat, res)
    k_str = json.dumps(k_mat)
    m_str = json.dumps(m_mat)
    return (k_str, m_str)


class UserFactorBase(AlgMeta):

    def get_user_set(self):
        conn = self.conn_func()
        # TODO 改成各学科通用
        sql = 'select distinct user_id from math_question_record'
        A = pd.read_sql_query(sql, conn)
        sql = 'select distinct user_id from adaptive_question_record'
        B = pd.read_sql_query(sql, conn)
        df = pd.concat([A, B])
        return set(df.user_id)

    def dump_user_factor(self):
        user_set = self.get_user_set()
        for uid in user_set:
            key = self.USER_FACTOR_KEY % uid
            ufac = convert_user_factor(self.redis_db, key)
            if ufac is None:
                continue
            adaptive_key = self.ADAPTIVE_USER_FACTOR_KEY % uid
            flush_redis(self.redis_db, adaptive_key, ufac)


class MathUserFactor(MathMeta, UserFactorBase):
    pass

