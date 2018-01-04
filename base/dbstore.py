# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = 'lihe <imanux@sina.com>'
__date__ = '06/12/2017 2:33 PM'
__description__ = '''
    ☰
  ☱   ☴
☲   ☯   ☵
  ☳   ☶
    ☷
'''

import os
import sys

app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(app_root)
if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

from mongoengine import connect
import pymongo
from pymongo import MongoClient
from pymongo import errors as pyerrors
import redis

from izen import rds

from base import cfg

# 映射出 rds

mg_cfg = {
    'host': cfg.get('mg.host', 'localhost'),
    'port': cfg.get('mg.port', 27027),
    'db': cfg.get('mg.db', 'luoo'),
    'alias': cfg.get('mg.alias', 'luoo_rw'),
    'username': cfg.get('mg.username', ''),
    'password': cfg.get('mg.password', ''),
}
connect(**mg_cfg)

MG_CONN = MongoClient('mongodb://{}:{}/{}'.format(
    cfg.get('mg.host', 'localhost'),
    cfg.get('mg.port', 27027),
    cfg.get('mg.db', 'luoo'),
))
LUOO_DB = MG_CONN[cfg.get('mg.db', 'luoo')]

# redis 配置参数
redis_conf = {
    'host': cfg.get('rds.host', 'localhost'),
    'port': cfg.get('rds.port', 6379),
    'password': cfg.get('rds.password', '123456'),
    'socket_timeout': cfg.get('rds.socket_timeout'),
    'socket_connect_timeout': cfg.get('rds.socket_connect_timeout'),
    'db': cfg.get('rds.db'),
}

rds = rds
rds.config(redis_conf)


def batch_write(dat, tb):
    try:
        res = LUOO_DB[tb].insert_many(dat)
        return len(res.inserted_ids)
    except pyerrors.BulkWriteError as _:
        print(_)
        return None


def rdc(db=0):
    """
        通过指定连接的 ``db`` 建立一个到 ``redis`` 连接的client

    - 连接参数, 使用 ``配置文件`` 指定

    :param db: ``待操作的redis db``
    :type db:
    """
    if not isinstance(db, int):
        db = 0
    redis_conf['db'] = db

    return rds.client(redis_conf)


def clear_rds_key(key):
    rd = redis.StrictRedis(**redis_conf)
    rd.delete(key)
