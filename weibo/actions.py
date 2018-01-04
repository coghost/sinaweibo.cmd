# -*- coding: utf-8 -*-
__author__ = 'lihe <imanux@sina.com>'
__date__ = '27/12/2017 11:01 AM'
__description__ = '''
    ☰
  ☱   ☴
☲   ☯   ☵
  ☳   ☶
    ☷
'''

import os
import sys

app_root = '/'.join(os.path.abspath(__file__).split('/')[:-2])
sys.path.append(app_root)

menus = {
    'root': [
        {
            '_do': 'get_personal_info',
            '_txt': '个人信息',
            'showed': '__'
        },
        {
            '_do': 'get_followed',
            '_txt': '关注用户列表',
            'showed': 'name,sex,uid'
        },
        {
            '_do': 'publish',
            '_access': 3,
            '_txt': '发布微博',
        },
        {
            '_do': 'get_feed',
            '_txt': '用户微博',
        },
    ],
    'feed': [
        {
            '_do': 'more',
            '_txt': '更多信息',
        },
        {
            '_do': 'large',
            '_txt': '显示大图',
        },
        {
            '_do': 'video',
            '_txt': '显示视频',
        },
        {
            '_do': 'forward',
            '_txt': '转发',
        },
        {
            '_do': 'comment',
            '_txt': '评论',
        },
        {
            '_do': 'like',
            '_txt': '赞/取消',
        },
        {
            '_do': 'delete',
            '_access': 3,
            '_txt': '删除微博',
        },
        {
            '_do': 'topit',
            '_access': 3,
            '_txt': '置顶',
        },
        {
            '_do': 'add_tag',
            '_access': 3,
            '_txt': '加标签',
        },
        {
            '_do': 'view_by_friends',
            '_access': 3,
            '_txt': '好友圈可见',
        },
        {
            '_do': 'only_me',
            '_access': 3,
            '_txt': '自己可见',
        },
        {
            '_do': 'favor',
            '_access': 2,
            '_txt': '收藏/取消',
        },
        {
            '_do': 'raw_data',
            '_txt': '原始信息',
        },
    ],
    'publish': [
        {
            '_do': 'publish_text',
            '_txt': '文字信息',
        },
        {
            '_do': 'publish_pic',
            '_txt': '图文信息',
        },
        {
            '_do': 'publish_video',
            '_txt': '视频信息',
        },
    ],
}


def get_user_action(is_me=False):
    n = 3 if is_me else 2
    dat = {}
    for k, menu in menus.items():
        dat[k] = [
            x
            for x in menu
            if not x.get('_access') or x['_access'] == n
        ]
    return dat


def get_actions(use_uid='', key='root'):
    if not use_uid:
        return menus[key]

    return [x for x in menus[key] if x.get('_access')]


if __name__ == '__main__':
    from pprint import pprint

    _a = get_user_action()
    pprint(_a)
