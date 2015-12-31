# coding: utf-8

from __future__ import absolute_import
from string import upper


class AlgMeta(object):

    def __init__(self, conn_func=None, redis_db=None):
        self.conn_func = conn_func
        self.redis_db = redis_db


def construct_meta(cls_name, subject_name, SBJ_CONSTS,
        meta_info, consts_info, kind_map_info, subject_name2id):
    attrs = {}
    for var_num, fields in meta_info.iteritems():
        for k, v in fields.iteritems():
            attrs[k] = v % tuple([subject_name] + ['%s'] * var_num)
    for k, v in consts_info.iteritems():
        attrs[k] = SBJ_CONSTS[v % upper(subject_name)]
    for kind_map_key, info in kind_map_info.iteritems():
        res_map = {}
        for k, v in info.iteritems():
            k = SBJ_CONSTS[k % upper(subject_name)]
            v = SBJ_CONSTS[v % upper(subject_name)]
            res_map[k] = v
        attrs[kind_map_key] = res_map
    attrs['subject_id'] = subject_name2id[subject_name]
    return type(cls_name, (object,), attrs)

