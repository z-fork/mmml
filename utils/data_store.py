# coding: utf-8

import MySQLdb
import redis

redis_online = redis.Redis(host='shakuras', port=6301, db=0)
redis_debug = redis.Redis(host='char', port=5301, db=0)
redis_cet_online = redis.Redis(host='shakuras', port=6303, db=0)
redis_cet_debug = redis.Redis(host='char', port=5303, db=0)

banker_production_conf = {
        'host':'sqlproxy',
        'user':'banker',
        'passwd':'YouShallNotPass',
        'db':'banker_production',
        'port':4406
}

banker_read_conf = {
        'host':'sqlproxy',
        'user':'banker',
        'passwd':'YouShallNotPass',
        'db':'banker_production',
        'port':3406
}

banker_dev_conf = {
        'host':'char',
        'user':'banker_dev',
        'passwd':'nosecret',
        'db':'banker_dev',
        'port':3306
}

cet_production_conf = {
        'host':'sqlproxy',
        'user':'cet',
        'passwd':'TOEFLeasier',
        'db':'cet_production',
        'port':4406
}

cet_read_conf = {
        'host':'sqlproxy',
        'user':'cet',
        'passwd':'TOEFLeasier',
        'db':'cet_production',
        'port':3406
}

cet_dev_conf = {
        'host':'char',
        'user':'cet_dev',
        'passwd':'nopasswd',
        'db':'cet_dev',
        'port':3306
}


def get_mysql_conn(conf):
    return MySQLdb.connect(host = conf['host'],
                        user = conf['user'],
                        passwd = conf['passwd'],
                        db = conf['db'],
                        port = conf['port'],
                        charset='utf8')


def get_banker_conn():
    return get_mysql_conn(conf=banker_production_conf)


def get_banker_read_conn():
    return get_mysql_conn(conf=banker_read_conf)


def get_banker_dev_conn():
    return get_mysql_conn(conf=banker_dev_conf)


def get_cet_conn():
    return get_mysql_conn(conf=cet_production_conf)


def get_cet_read_conn():
    return get_mysql_conn(conf=cet_read_conf)


def get_cet_dev_conn():
    return get_mysql_conn(conf=cet_dev_conf)


def flush_redis(redis_db, key, value):
    pipe = redis_db.pipeline()
    pipe.delete(key)
    for v in value:
        pipe.rpush(key, v)
    pipe.execute()

