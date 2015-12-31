# coding: utf-8

from __future__ import absolute_import
import argparse

from utils.data_store import (
    get_banker_conn, get_banker_dev_conn,
    redis_online, redis_debug
)
from adaptive.card_factor import MathCardFactor
from adaptive.concept_graph import MathConceptGraph
from adaptive.item_index import MathItemIndex
from adaptive.user_factor.user_factor import MathUserFactor


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    redis_db = redis_debug if args.debug else redis_online
    conn_func = get_banker_dev_conn if args.debug else get_banker_conn

    card_factor = MathCardFactor(conn_func, redis_db)
    card_factor.dump_card_factor()
    print 'card factor ok'
    card_factor.dump_card_index()
    print 'card index ok'
    card_factor.dump_week_concept_index()
    print 'week concept index ok'

    concept_graph = MathConceptGraph(conn_func, redis_db)
    concept_graph.build_concept_graph()
    concept_graph.dump_concept_graph()
    print 'concept graph build ok'

    item_index = MathItemIndex(conn_func, redis_db)
    item_index.dump_card_inv_index()
    print 'dump card_inv_index ok'
    item_index.dump_question_inv_index()
    print 'dump question_inv index ok'

    user_factor = MathUserFactor(conn_func, redis_db)
    user_factor.dump_user_factor()
    print 'dump user_factor ok'

