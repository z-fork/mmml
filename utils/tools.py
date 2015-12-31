# coding: utf-8

from __future__ import absolute_import

import numpy as np


def random_sample(x, size, replace=False, p=None):
    if not x:
        return []
    a = range(len(x))
    n = min(len(a), size)
    idx = list(np.random.choice(a, n, replace=replace, p=p))
    return [x[i] for i in idx]


def redis_scan(redis_db, key_pattern):
    key_list = []
    for key in redis_db.scan_iter(match=key_pattern):
        key_list.append(key)
    return key_list
