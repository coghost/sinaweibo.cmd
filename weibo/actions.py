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
from pprint import pprint

app_root = '/'.join(os.path.abspath(__file__).split('/')[:-2])
sys.path.append(app_root)

from bs4 import BeautifulSoup as BS
from clint import textui

from logzero import logger as log
from izen import dec
from izen import helper

import base
from base import cfg
from base import Player
from weibo.wb_base import WeiboBase
from base import Colorful

clr = Colorful()

icos = '🚦✔️✖️✔︎✘✰❤︎✉︎'
ico = {
    'rgb': '🚦',
    'gender': {
        'm': 'M ',
        'f': 'F '
    },
    'yorn': {
        'y': '️✔︎',
        'n': '️✘',
    }
}

menus = {
    'root': [
        # {
        #     '_do': 'go_home',
        #     '_access': 2,
        #     '_txt': '返回个人主页',
        # },
        {
            '_do': 'get_personal_info',
            '_txt': '个人信息',
            'showed': '__',
        },
        {
            '_do': 'get_searched',
            '_txt': '查找账号',
            'showed': 'screen_name,gender,id'
        },
        {
            '_do': 'get_fans',
            '_txt': '粉丝列表',
            'showed': 'screen_name,gender,id'
        },
        {
            '_do': 'get_followed',
            '_txt': '关注用户列表',
            'showed': 'screen_name,gender,id'
        },
        {
            '_do': 'get_unread',
            '_access': 3,
            '_txt': '我的消息',
        },
        {
            '_do': 'publish',
            '_access': 3,
            '_txt': '发布微博',
        },
        {
            '_do': 'do_follow',
            '_access': 2,
            '_txt': '关注/取关',
        },
        {
            '_do': 'get_feeds',
            '_txt': '用户微博',
        },
    ],
    'user': [
        {
            '_do': 'more',
            '_txt': '查看账号详情',
        },
        {
            '_do': 'go_home',
            '_txt': '返回个人主页',
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

DEPTH = 0


def gender(g):
    if not g:
        g = 'm'
    return ico['gender'][g]


def yorn(t):
    return ico['yorn']['y' if t else 'n']


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


class Action(WeiboBase):
    __metaclass__ = dec.Singleton

    def __init__(self, user):
        WeiboBase.__init__(self)
        self.wb_user = user
        self.choice_list = []
        self.act = {}

        self.selected_feed = None
        self.selected_user = None

        self.menus = get_user_action(user.is_me)

        if not self.choice_list:
            self.add_menu_to_choices()

    def filter_menu(self, menu_in):
        """
            过滤符合个人身份的菜单

        :param menu_in:
        :type menu_in:
        :return:
        :rtype:
        """
        if self.selected_user:
            for menu in menu_in:
                menu['_txt'] = menu['_txt'].format(self.selected_user.get('screen_name'))

        if self.selected_feed:
            dat = self.selected_feed
            has_video = False
            if dat.get('page_info', {}) and dat['page_info'].get('type') == 'video':
                has_video = True

            retweeted = dat.get('retweeted_status')
            if retweeted:
                if retweeted.get('page_info', {}) and retweeted['page_info'].get('type') == 'video':
                    has_video = True

            if not has_video:
                menu_in = [
                    x for x in menu_in
                    if x['_do'] != 'video'
                ]

        return menu_in

    def add_menu_to_choices(self, menu_key='root', default=0):
        """
            添加到选项列表

        :param menu_key:
        :type menu_key:
        :param default:
        :type default:
        :return:
        :rtype:
        """
        menu = self.menus.get(menu_key)
        menu = self.filter_menu(menu)
        _handler = self.root_action

        if hasattr(self, '{}_action'.format(menu_key)):
            _handler = getattr(self, '{}_action'.format(menu_key))

        operation = {
            'orig_dat': menu,
            'cb': _handler,
            'default': default or len(menu),
        }

        self.choice_list.append(operation)
        _menu = self.choice_list[-1]
        self.run_menu(_menu)

    def add_to_choices(self, choice):
        pass

    def run_menu(self, menu):
        log.debug('is me ? {}'.format(self.wb_user.is_me))
        c = self.wb_user.wbui(
            **menu
        )
        if str(c) in 'bB':
            # 从账号详情菜单返回 第二级菜单, 则重设账号为登陆账号!!!
            if len(self.choice_list) == 2:
                self.wb_user.reset_uid('')
                self.menus = get_user_action(self.wb_user.is_me)

            self.choice_list.pop()
            return c

    @dec.catch(cfg.get('sys.catch_error', False), AttributeError)
    def root_action(self, act):
        self.act = act
        log.debug('{} {} {}({})'.format(ico['rgb'] * 3, act.get('_txt'), act.get('_do'), self.wb_user.user_uid))

        if act.get('_do') == 'go_home':
            self.wb_user.reset_uid('')
            self.menus = get_user_action(self.wb_user.is_me)
            self.add_menu_to_choices('root')

        resp = getattr(self.wb_user, act.get('_do'))()

        if hasattr(self, '{}_handler'.format(act.get('_do'))):
            getattr(self, '{}_handler'.format(act.get('_do')))(resp)
        else:
            self.echo_handler(act)

    def user_action(self, act):
        log.debug('{} {} {}({})'.format(ico['rgb'] * 3, act.get('_txt'), act.get('_do'), self.wb_user.user_uid))

        user_ = self.selected_user.get('user')
        if not user_:
            user_ = self.selected_user

        if act.get('_do') == 'more':
            self.wb_user.reset_uid(user_.get('id'))
        elif act.get('_do') == 'go_home':
            self.wb_user.reset_uid('')

        self.menus = get_user_action(self.wb_user.is_me)
        self.add_menu_to_choices('root')

    def feed_action(self, act):
        log.debug('{} {} {}({})'.format(ico['rgb'] * 3, act.get('_txt'), act.get('_do'), self.wb_user.user_uid))
        resp = getattr(self.wb_user, act.get('_do'))(self.selected_feed)

        if hasattr(self, 'feed_{}_handler'.format(act.get('_do'))):
            getattr(self, 'feed_{}_handler'.format(act.get('_do')))(resp)
        else:
            self.echo_handler(act)

    def echo_handler(self, act):
        __showed = act.get('showed')
        if __showed:
            _info = act.get('_do').replace('get_', '')
            dat = getattr(self.wb_user, _info)
            if __showed == '__':
                print(dat)
                return

            keys = act.get('showed').split(',')
            _ = [
                ', '.join(['{}'.format(x.get(_x)) for _x in keys if _x])
                for x in dat
            ]
            print('\n'.join(_))

    def get_fans_handler(self, dat):
        self.page_handler('fans', self.do_user_handler)

        # idx = self.wb_user.ctrl['fans']['page']
        # ch = self.do_user_handler(self.wb_user.fans[idx])
        # while ch and ch in 'nNpP':
        #     step = 1 if ch in 'nN' else -1
        #     self.wb_user.get_fans(step)
        #     idx = self.wb_user.ctrl['fans']['page']
        #     ch = self.do_user_handler(self.wb_user.fans[idx])
        # else:
        #     if ch and ch in 'bB':
        #         return

    @dec.catch(cfg.get('sys.catch_error', False), (ValueError, IndexError, KeyError))
    def page_handler(self, key_in, handler):
        page_dat = getattr(self.wb_user, key_in)
        page_req = getattr(self.wb_user, 'get_' + key_in)
        # print(page_dat)
        print(self.wb_user.ctrl)

        idx = self.wb_user.ctrl[key_in]['page']
        ch = handler(page_dat[idx])

        while ch and ch in 'nNpP' or ch and ch.startswith('go'):
            if ch.startswith('go'):
                _abs_idx = int(helper.multi_replace(ch, 'go| ,'))
            else:
                _abs_idx = 0
            step = 1 if ch in 'nN' else -1
            page_req(step=step, abs_page=_abs_idx)
            idx = self.wb_user.ctrl[key_in]['page']
            print('curr-page', idx, page_dat.keys(), idx in page_dat)

            if idx in page_dat:
                # print(page_dat[idx])
                ch = handler(page_dat[idx])
            else:
                page_req(step=step, abs_page=1)
                ch = handler(page_dat.get(1))
        else:
            if ch and ch in 'bB':
                return

    def get_followed_handler(self, dat):
        self.page_handler('followed', self.do_user_handler)
        # _abs_idx = 0
        # idx = self.wb_user.ctrl['followed']['page']
        #
        # ch = self.do_user_handler(self.wb_user.followed[idx])
        # while ch and ch in 'nNpP' or ch.startswith('go'):
        #     if ch.startswith('go'):
        #         _abs_idx = int(helper.multi_replace(ch, 'go|, |'))
        #     step = 1 if ch in 'nN' else -1
        #     self.wb_user.get_followed(step=step, abs_page=_abs_idx)
        #     idx = self.wb_user.ctrl['followed']['page']
        #     ch = self.do_user_handler(self.wb_user.followed[idx])
        # else:
        #     if ch and ch in 'bB':
        #         return

    def get_searched_handler(self, dat):
        self.page_handler('searched', self.do_user_handler)
        # idx = self.wb_user.ctrl['searched']['page']
        #
        # ch = self.do_user_handler(self.wb_user.searched[idx])
        # while ch and ch in 'nNpP':
        #     step = 1 if ch in 'nN' else -1
        #     self.wb_user.get_searched(step)
        #     idx = self.wb_user.ctrl['searched']['page']
        #     ch = self.do_user_handler(self.wb_user.searched[idx])
        # else:
        #     if ch and ch in 'bB':
        #         return

    @dec.catch(cfg.get('sys.catch_error', False), (ValueError, IndexError))
    def do_user_handler(self, dat_in):
        def gen_str(dat):
            name_ = dat.get('screen_name')
            name_ = '{0:{w}}'.format(
                name_,
                w=16 - base.cn_len(name_),
            )
            st_info = '微博: %-10s 关注: %-10s 粉丝: %-10s' % (
                str(dat.get('statuses_count')),
                str(dat.get('follow_count')),
                str(dat.get('followers_count')),
            )
            txt = '{}[{}]\t{:{}}\t'.format(
                name_,
                gender(dat.get('gender', '')),
                st_info,
                48 - base.cn_len(st_info)
            )
            txt += '级别: %-4s\t 关注我: %s\t已关注: %s' % (
                dat.get('urank') if dat.get('urank') else '',
                yorn(dat.get('follow_me')),
                yorn(dat.get('following')),
                # yorn(dat.get('like_me')), \t喜欢我:{}\t已喜欢:{}
                # yorn(dat.get('like')),
            )
            txt += ''
            return txt

        if not dat_in:
            log.warn('1. 账号无相关信息!')
            return

        users_ = [
            gen_str(x)
            for x in dat_in
        ]
        if not users_:
            log.warn('2. 账号无相关信息!')
            return

        while True:
            c = helper.num_choice(
                users_,
                default=1,
                # valid_keys='p,P,n,N,go',
                valid_keys='all',
            )
            if not c:
                return c

            if str(c) in 'bB':
                return str(c)

            if str(c) in 'nNpP':
                return str(c)

            if str(c).startswith('go'):
                print(str(c))
                return c

            c = int(c) - 1
            self.selected_user = dat_in[c]
            self.add_menu_to_choices('user', 1)

    def get_personal_info_handler(self, dat):
        dat = self.wb_user.personal_info
        pic = dat.get('avatar_hd')
        self.cat_net_img(pic, height=12)

        txt = '{}[{}]({})\t(微博:{} 关注:{} 粉丝:{})\n'.format(
            dat.get('screen_name'),
            '男' if dat.get('gender') is 'm' else '女',
            dat.get('id'),
            dat.get('statuses_count'),
            dat.get('follow_count'),
            dat.get('followers_count'),
        )
        txt += '级别:{}\t 关注我:{}\t已关注:{}\t喜欢我:{}, 已喜欢:{}'.format(
            dat.get('urank'),
            dat.get('follow_me'),
            dat.get('following'),
            dat.get('like_me'),
            dat.get('like'),
        )
        if dat.get('description'):
            txt += '\n' + dat.get('description')
        txt += '\n' + '✁ ' * 32
        clr.debug(txt)

    @dec.catch(cfg.get('sys.catch_error', False), (ValueError, IndexError))
    def do_feed_handler(self, dat_in):
        def gen_str(dat):
            txt = ['{}{} (转发:{}, 评论:{}, 点赞:{}) 来自<{}>'.format(
                '👍 ' if dat.get('liked') else '',
                dat.get('created_at'),
                dat.get('reposts_count'),
                dat.get('comments_count'),
                dat.get('attitudes_count'),
                dat.get('source'),
            )]
            if len(dat.get('pics', [])):
                txt.append('[{}图]'.format(len(dat.get('pics'))))

            if dat.get('page_info', {}) and dat['page_info'].get('type') == 'video':
                txt.append('[1个视频]')
            txt = ', '.join(txt)
            __txt = base.bs4txt(dat.get('text'))
            txt += '\n{} ...\n'.format(__txt[:40])
            if dat.get('retweeted_status'):
                # txt += '{} 转发自 {}\n'.format('-' * 32, '-' * 32)
                t = '{} 转发自 {}\n'.format('⇢ ' * 16, '⇠ ' * 16)
                t += gen_str(dat.get('retweeted_status'))
                t = textui.colored.blue(t)
                txt += t
            return txt

        if not dat_in:
            log.warn('账号无微博!!!')
            return

        feeds = dat_in
        feeds = [
            gen_str(x)
            for x in feeds
        ]

        if not feeds:
            log.warn('账号无微博!!!')
            return

        while True:
            c = helper.num_choice(
                feeds,
                default=1,
                valid_keys='all',
            )
            if not c:
                return c

            if str(c) in 'bB':
                return str(c)

            if str(c) in 'nNpP':
                return str(c)

            if c and str(c).startswith('go'):
                print(str(c))
                return c

            c = int(c) - 1
            self.selected_feed = dat_in[c]
            self.add_menu_to_choices('feed', 1)

    def get_feeds_handler(self, dat):
        self.page_handler('feeds', self.do_feed_handler)
        # idx = self.wb_user.ctrl['feeds']['page']
        # ch = self.do_feed_handler(self.wb_user.feeds[idx])
        # while ch and ch in 'nNpP':
        #     step = 1 if ch in 'nN' else -1
        #     self.wb_user.get_feeds(step)
        #     idx = self.wb_user.ctrl['feeds']['page']
        #     ch = self.do_feed_handler(self.wb_user.feeds[idx])
        # else:
        #     if ch and ch in 'bB':
        #         return

    def publish_handler(self, dat):
        self.add_menu_to_choices('publish', 1)

    def feed_more_handler(self, act):
        """
            详细信息
            图片缩略图
        :param act:
        :type act:
        :return:
        :rtype:
        """
        dat = self.selected_feed

        def show_retweeted(dat):
            txt = '{}\n转发:{}, 评论:{}, 点赞:{}\n'.format(
                '✁ ' * 16,
                dat.get('reposts_count'),
                dat.get('comments_count'),
                dat.get('attitudes_count'),
                dat.get('text'),
            )
            print(txt)
            pics = [
                x['url']
                for x in dat.get('pics', [])
            ]
            if not pics and dat.get('page_info'):
                pics = dat['page_info'].get('page_pic', {}).get('url')

            if pics and not isinstance(pics, list):
                pics = [pics]

            for pic in pics:
                self.cat_net_img(pic)

            retweeted = dat.get('retweeted_status')
            if retweeted:
                show_retweeted(retweeted)

        show_retweeted(dat)

    @dec.catch(cfg.get('sys.catch_error', False), (ValueError, IndexError))
    def feed_large_handler(self, act):
        dat = self.selected_feed

        def show_retweeted(dat):
            pics = [
                x['url']
                for x in dat.get('pics', [])
            ]
            if not pics and dat.get('page_info'):
                pics = dat['page_info'].get('page_pic', {}).get('url')

            if pics and not isinstance(pics, list):
                pics = [pics]

            if pics:
                return pics

            retweeted = dat.get('retweeted_status')
            if retweeted:
                return show_retweeted(retweeted)

        pics_all = show_retweeted(dat)
        if not pics_all:
            return

        if len(pics_all) == 1:
            self.cat_net_img(pics_all[0], large=True, height=base.get_height())
            return

        pics_sn = [
            '图片({})'.format(x + 1) for x in range(len(pics_all))
        ]
        while True:
            c = helper.num_choice(
                pics_sn,
                default=1,
            )
            if str(c) in 'bB':
                return str(c)
            c = int(c) - 1
            self.cat_net_img(pics_all[c], large=True, height=base.get_height())

    def feed_video_handler(self, act):
        dat = self.selected_feed
        retweeted = dat.get('retweeted_status')
        if retweeted:
            dat = retweeted

        def show_retweeted(dat):
            url = dat.get('HDVideo')
            if not url:
                url = dat.get('page_info', {}).get('media_info', {}).get('stream_url', '')

            if url:
                url = url.replace('https', 'http')
                Player(url)
            else:
                log.error('No Video info found!!!')

        show_retweeted(dat)


if __name__ == '__main__':
    from pprint import pprint

    # _a = get_user_action()
    # pprint(_a)
    cn = '这个可以001'
    print(base.cn_len(cn))
