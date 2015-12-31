# coding: utf-8

from __future__ import absolute_import
import json

import pandas as pd

from utils.meta import AlgMeta
from adaptive.maths_meta import MathMeta
from utils.consts import K_APPROVED
from adaptive.consts import K_MATH_CARD
from maths.knowledge_model import load_matrix


def ktag2mat(ktag):
    ktag = set(ktag.split('|'))
    k_mat = {}
    for k in ktag:
        k_mat[k] = {v:1 for v in ktag}
    return k_mat


def load_card_factor(redis_db, key):
    try:
        k_str = redis_db.get(key)
    except ValueError:
        k_str = '{}'
    return load_matrix(k_str)


class CardFactorBase(AlgMeta):

    def __init__(self, *args, **kwargs):
        super(CardFactorBase, self).__init__(*args, **kwargs)
        self.knowledge_mat = {}

    def get_book_info(self):
        '''
        book_info: book_id, root_id
        '''
        conn = self.conn_func()
        sql = ('select id book_id, root_id from book '
               'where subject_id = %s' % self.subject_id)
        book_info = pd.read_sql_query(sql, conn)
        return book_info

    def get_lesson_info(self):
        '''
        lesson_info: lesson_id, week, root_id, lesson_plan_id
        '''
        conn = self.conn_func()
        sql = ('select id s_id, parent_id, level '
               'from book_hierarchy where level > 0')
        A = pd.read_sql_query(sql, conn)
        A.sort(columns='level', inplace=True)
        root_id_map = {}
        for _, row in A.iterrows():
            s_id, parent_id, level = row
            s_id = int(s_id)
            level = int(level)
            if not pd.isnull(parent_id):
                parent_id = int(parent_id)
            if level == 1:
                root_id_map[s_id] = s_id
            else:
                root_id_map[s_id] = root_id_map[parent_id]
        _f = lambda x: root_id_map[x.s_id]
        sql = 'select id s_id, week from book_hierarchy where level = 4'
        lesson_info = pd.read_sql_query(sql, conn)
        lesson_info['root_id'] = lesson_info.apply(_f, axis=1)
        lesson_info.rename(columns={'s_id':'lesson_id'}, inplace=True)

        sql = ('select id lesson_plan_id, lesson_id '
               'from lesson_plan where subject_id = %s '
               'and status = %s' % (self.subject_id, K_APPROVED))
        lesson_plan = pd.read_sql_query(sql , conn)
        lesson_info = pd.merge(lesson_info, lesson_plan)
        return lesson_info

    def get_lesson_piece(self):
        '''
        lesson_piece: lesson_plan_id, card_id
        '''
        conn = self.conn_func()
        sql = ('select lesson_plan_id, content_id card_id '
               'from lesson_piece where content_kind = %s' % K_MATH_CARD)
        lesson_piece = pd.read_sql_query(sql, conn)
        return lesson_piece

    def get_card_info(self):
        '''
        card_info: card_id, card_type
        '''
        conn = self.conn_func()
        sql = ('select id card_id, card_type '
               'from card where subject_id = %s '
               'and status = %s' % (self.subject_id, K_APPROVED))
        card_info = pd.read_sql_query(sql, conn)
        return card_info

    def get_card_knowledge_tag(self):
        '''
        card_ktag: card_id, ktag
        '''
        conn = self.conn_func()
        sql = ('select target_id card_id, tag_id from %s where '
               'target_kind = %s' % (self.knowledge_tag_table, K_MATH_CARD))
        card_ktag = pd.read_sql_query(sql, conn)
        card_ktag = card_ktag.groupby('card_id').apply(
            lambda x: "|".join(map(str, x.tag_id))).reset_index()
        card_ktag.columns = ['card_id', 'ktag']
        return card_ktag

    def dump_card_factor(self):
        card_info = self.get_card_info()
        card_ktag = self.get_card_knowledge_tag()
        # TODO 避免重复计算 card_info 和 card_ktag
        A = pd.merge(card_info, card_ktag)
        for _, row in A.iterrows():
            card_id, card_type, ktag = row
            card_id = int(card_id)
            card_type = int(card_type)
            k_mat = ktag2mat(ktag)
            k_str = json.dumps(k_mat)
            key = self.CARD_FACTOR_KEY % (card_type, card_id)
            self.redis_db.set(key, k_str)

    def dump_card_index(self):
        '''根据 book_id 和 week 取 card'''
        book_info = self.get_book_info()
        lesson_info = self.get_lesson_info()
        lesson_piece = self.get_lesson_piece()
        card_info = self.get_card_info()

        df = pd.merge(book_info, lesson_info)
        df = df[['book_id', 'week', 'lesson_plan_id']]
        df = pd.merge(df, lesson_piece)
        df = pd.merge(df, card_info)
        df = df[['book_id', 'week', 'card_type', 'card_id']]

        res = {}
        for _, row in df.iterrows():
            book_id, week, card_type, card_id = map(int, row)
            res.setdefault((book_id, week, card_type), []).append(card_id)
        for (book_id, week, card_type), card_ids in res.iteritems():
            field = '%s:%s:%s' % (book_id, week, card_type)
            value = '|'.join(map(str, card_ids))
            self.redis_db.hset(self.CARD_INV_INDEX, field, value)

    def dump_week_concept_index(self):
        '''
        根据 book_id 和 week 取该周卡片中涉及的知识点
        依赖 dump_card_index 结果
        '''
        fields = self.redis_db.hkeys(self.CARD_INV_INDEX)
        res = {}
        for field in fields:
            book_id, week, card_type = field.split(':')
            card_ids = self.redis_db.hget(self.CARD_INV_INDEX, field)
            if not card_ids:
                continue
            card_ids = card_ids.split('|')
            ktag_set = set()
            for card_id in card_ids:
                card_key = self.CARD_FACTOR_KEY % (card_type, card_id)
                k_mat = load_card_factor(self.redis_db, card_key)
                ktag_set.update(k_mat.keys())
            res.setdefault((book_id, week), set()).update(ktag_set)
        for (book_id, week), ktag_set in res.iteritems():
            field = "%s:%s" % (book_id, week)
            value = '|'.join(map(str, ktag_set))
            self.redis_db.hset(self.WEEK_CONCEPT_INV_INDEX, field, value)


class MathCardFactor(MathMeta, CardFactorBase):
    pass

