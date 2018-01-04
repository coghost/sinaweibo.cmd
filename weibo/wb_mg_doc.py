# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = 'lihe <imanux@sina.com>'
__date__ = '11/12/2017 9:28 PM'
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

from mongoengine import *
from base import dbstore


class WeiboAlbums(Document):
    """ weibo 相册信息

    """
    count = DictField()
    source = StringField()
    album_id = StringField()
    album_order = StringField()
    answer = StringField()
    caption = StringField()
    cover_pic = StringField()
    cover_photo_id = StringField()
    created_at = StringField()
    description = StringField()
    is_favorited = StringField()
    is_private = StringField()
    property = StringField()
    question = StringField()
    sq612_pic = StringField()
    status = StringField()
    thumb120_pic = StringField()
    thumb300_pic = StringField()
    timestamp = StringField()
    album_type = StringField()  # 爬取的数据为 type, 但是在更新时出错, 因此重命名
    uid = StringField()
    updated_at = StringField()
    updated_at_int = StringField()
    usort = StringField()

    meta = {
        'strict': False,
        'db_alias': dbstore.mg_cfg.get('alias'),
        'collection': 'weibo.albums',
        'ordering': [
            '-album_id'
        ],
        'indexes': [
            {
                'fields': ['album_id'],
                'unique': True,
            },
            'uid'
        ]
    }


class WeiboUsers(Document):
    """
        微博用户信息

    """
    name = StringField()
    uid = StringField()
    sex = StringField()
    addr = StringField()
    home_page = StringField()
    person_pic = StringField()
    person_num = StringField()
    person_card = StringField()
    person_info = StringField()
    person_label = StringField()
    approve = StringField()
    crawlers = DictField()  # 图片爬取进度信息

    meta = {
        'strict': False,
        'db_alias': dbstore.mg_cfg.get('alias'),
        'collection': 'weibo.users',
        'ordering': [
            '-name',
            'uid',
        ],
        'indexes': [
            {
                'fields': ['name'],
                'unique': True,
            },
            {
                'fields': ['uid'],
                'unique': True,
            },
        ]
    }


class WeiboPhotos(Document):
    """
        照片信息

    """

    album_id = StringField()
    caption = StringField()
    caption_render = StringField()
    created_at = StringField()
    feed_id = StringField()
    count = DictField()
    is_favorited = BooleanField()
    is_liked = BooleanField()
    is_paid = BooleanField()
    is_private = BooleanField()
    latitude = StringField()
    longitude = StringField()
    mblog_vip_type = IntField()
    mid = StringField()
    oid = StringField()
    photo_id = StringField()
    pic_host = StringField()
    pic_name = StringField()
    pic_pid = StringField()
    pic_type = IntField()
    property = IntField()
    source = StringField()
    tags = StringField()
    timestamp = IntField()
    type = IntField()
    uid = IntField()
    updated_at = StringField()
    visible_type = IntField()

    meta = {
        'strict': False,
        'db_alias': dbstore.mg_cfg.get('alias'),
        'collection': 'weibo.photo.details',
        'ordering': [
            'uid',
            '-timestamp',
        ],
        'indexes': [
            'timestamp',
        ]
    }


class WeiboUserFollowed(Document):
    pass


def album_update(dat):
    doc = WeiboAlbums.objects(
        album_id=dat.get('album_id'),
    )
    p = {}

    for k, v in dat.items():
        if k in ['type']:
            p['album_type'] = str(v)
            continue

        if k in ['count']:
            p[k] = v
            continue

        try:
            if not v:
                p[k] = '0'
                continue
            p[k] = str(v)
        except TypeError as _:
            # print(_)
            p[k] = '0'

    try:
        doc.update(
            upsert=True,
            **p
        )
    except NotUniqueError as _:
        print(_)


def album_query():
    pass


def user_update(dat):
    doc = WeiboUsers.objects(
        uid=dat.get('uid')
    )
    doc.update(
        upsert=True,
        **dat
    )
