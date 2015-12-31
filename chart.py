# coding: utf-8

import argparse

from utils.data_store import redis_online, redis_debug
from utils.consts import (
        CAPABILITY_CHART_KEY,
        EXPERIENCE_CHART_KEY,
        MATH_CAPABILITY_CHART_KEY,
        MATH_EXPERIENCE_CHART_KEY,
        APP_QUESTION_KIND_ALL,
        APP_QUESTION_KIND_READ,
        APP_QUESTION_KIND_CLOZE,
        APP_QUESTION_KIND_SINGLE,
        APP_QUESTION_KIND_LISTEN,
        EXAM_KIND_CET4,
        EXAM_KIND_CET6,
        EXAM_KIND_GK,
        EXAM_KIND_ZK,
        MATH_EXAM_KINDS
)


EXAM_KINDS = [EXAM_KIND_CET4, EXAM_KIND_CET6, EXAM_KIND_GK, EXAM_KIND_ZK]

CHART_KINDS = [APP_QUESTION_KIND_ALL,
               APP_QUESTION_KIND_READ,
               APP_QUESTION_KIND_CLOZE,
               APP_QUESTION_KIND_SINGLE,
               APP_QUESTION_KIND_LISTEN]


def reset_chart(redis_db, key):
    '''
    定时调用，清理能力值/经验值排行榜 redis key 中冗余的数据
    '''
    print 'reset %s' % key
    chart = redis_db.hgetall(key)
    if not chart:
        return
    tops = [(uid, int(value)) for uid, value in chart.iteritems()]
    tops.sort(key = lambda x: x[1])
    for uid, value in tops[:-120]:
        redis_db.hdel(key, uid)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    redis_db = redis_debug if args.debug else redis_online
    for exam_kind in EXAM_KINDS:
        for kind in CHART_KINDS:
            reset_chart(redis_db, CAPABILITY_CHART_KEY % (str(exam_kind), str(kind)))
            reset_chart(redis_db, EXPERIENCE_CHART_KEY % (str(exam_kind), str(kind)))

    for exam_kind in MATH_EXAM_KINDS:
        reset_chart(redis_db, MATH_CAPABILITY_CHART_KEY % str(exam_kind))
        reset_chart(redis_db, MATH_EXPERIENCE_CHART_KEY % str(exam_kind))

