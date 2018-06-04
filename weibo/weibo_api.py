# -*- coding: utf-8 -*-
__author__ = 'lihe <imanux@sina.com>'
__date__ = '21/12/2017 3:00 PM'
__description__ = '''
    ☰
  ☱   ☴
☲   ☯   ☵
  ☳   ☶
    ☷
'''

import os
import sys
import json
from urllib.parse import urljoin, urlencode, quote, unquote_plus, parse_qsl
import re
import base64
import binascii
from pprint import pprint
import math

app_root = '/'.join(os.path.abspath(__file__).split('/')[:-2])
sys.path.append(app_root)

import requests
import click
from logzero import logger as log

from izen import helper, dec
import base
from base import cfg
from base import pprt

from weibo import actions
from weibo.wb_base import WeiboBase, M, Login, HEADERS
from base import Colorful

clr = Colorful()
# TODO 使用 bs4 替换
zh_cn_colon = '：'
enable_pprt = True

API_URL = {
    'config': 'https://m.weibo.cn/api/config',
    'index': 'https://m.weibo.cn/api/container/getIndex',
    'unread': 'https://m.weibo.cn/unread',
    'fan_fo': 'https://m.weibo.cn/api/container/getSecond',
    'follow': 'https://m.weibo.cn/api/friendships/create',
    'groups_info': 'https://m.weibo.cn/friendships/groups',
    'add_groups': 'https://m.weibo.cn/friendships/groupsMemberAdd',
    'un_follow': 'https://m.weibo.cn/api/friendships/destory',
    'statuses': 'https://m.weibo.cn/api/statuses/',
    'blog_deal': 'https://m.weibo.cn/mblogDeal/',
    'comments': 'https://m.weibo.cn/api/comments/',
    'like': 'https://m.weibo.cn/api/attitudes/',
    'feed_friends': 'https://m.weibo.cn/feed/friends?version=v4',
    # 'repost': 'https://m.weibo.cn/api/statuses/repostTimeline',
}

mblogDeal = {
    'delete': 'delMyMblog'
}


def confirm_do(hints):
    c = helper.yn_choice(
        '是否[{}]'.format(hints)
    )
    if not c:
        log.warn('放弃 ({}) 操作.'.format(hints))
        return False
    return True


class WeiboApi(object):
    """
    API 接口负责数据获取. 所有与 ``weibo.cn`` 的交互操作

    """

    def __init__(self, user, enable_show_url=False):
        self.user = user
        self.uid = user.user_uid
        self.client = user.mobile_sess
        self.web_sess = user.sess
        self.enable_show_url = enable_show_url
        self.domain_id = ''

        self.base_info = {}
        self.tabs_info = {}
        self.channels = {}
        self.st_token = ''
        self.spawn()

    def fake_it(self):
        self.base_info = {
            'userInfo': {
                'id': 6069778559,
                'screen_name': '弱弱弱一生',
                'profile_image_url': 'https://tvax3.sinaimg.cn/crop.0.0.534.534.180/006CMaGbly8fn03eat8x2j30ew0eutfc.jpg',
                'profile_url': 'https://m.weibo.cn/u/6069778559?uid=6069778559&luicode=10000011&lfid=1005056069778559',
                'statuses_count': 9,
                'verified': False,
                'verified_type': -1,
                'close_blue_v': False,
                'description': '人生真有意思',
                'gender': 'm',
                'mbtype': 0,
                'urank': 7,
                'mbrank': 0,
                'follow_me': False,
                'following': False,
                'followers_count': 63,
                'follow_count': 58,
                'cover_image_phone': 'https://tva1.sinaimg.cn/crop.0.0.640.640.640/549d0121tw1egm1kjly3jj20hs0hsq4f.jpg',
                'avatar_hd': 'https://wx3.sinaimg.cn/orj480/006CMaGbly8fn03eat8x2j30ew0eutfc.jpg',
                'like': False,
                'like_me': False
            },
            'fans_scheme': 'https://m.weibo.cn/p/index?containerid=231016&luicode=10000011&lfid=1005056069778559',
            'follow_scheme': 'https://m.weibo.cn/feature/download/index?luicode=10000011&lfid=1005056069778559',
            'tabsInfo': {
                'selectedTab': 1,
                'tabs': [{
                    'title': '主页',
                    'tab_type': 'profile',
                    'containerid': '2302836069778559'
                }, {
                    'title': '微博',
                    'tab_type': 'weibo',
                    'containerid': '1076036069778559',
                    'url': '/index/my'
                }]
            },
            'showAppTips': 1,
            'scheme': 'sinaweibo://userinfo?uid=6069778559&luicode=10000011&lfid=&featurecode='
        }
        self.channels = [{'containerid': '2308696069778559_-_mix',
                          'default_add': 1,
                          'id': '2308696069778559_-_mix',
                          'must_show': 1,
                          'name': '赞'},
                         {'containerid': '2308696069778559_-_collect',
                          'default_add': 1,
                          'id': '2302596069778559',
                          'must_show': 1,
                          'name': '收藏'},
                         {'containerid': '2308696069778559_-_like_video',
                          'default_add': 1,
                          'id': '2308696069778559_-_like_video',
                          'must_show': 1,
                          'name': '视频'},
                         {'containerid': '2308696069778559_-_like_article',
                          'default_add': 1,
                          'id': '2308696069778559_-_like_article',
                          'must_show': 1,
                          'name': '文章'},
                         {'containerid': '2308696069778559_-_like_pic',
                          'default_add': 1,
                          'id': '2308696069778559_-_like_pic',
                          'must_show': 1,
                          'name': '图片'}]

    def get_config(self):
        """
            获取 ``st`` 字段, 作为CRUD的 token

        :return:
        :rtype:
        """
        dat = self.get_it(API_URL['config']).get('data', {})
        if not dat.get('login'):
            log.error('Failed of Login {}'.format(dat))

        self.st_token = dat.get('st')
        return dat

    def spawn(self):
        self.get_config()
        self.base_info = self.get_enter_point()
        # self.fake_it()

    @staticmethod
    def is_res_success(dat):
        try:
            if not dat.get('ok'):
                return dat

            if not dat.get('ok') == 1:
                log.error('GOT FAILED: {}'.format(dat))
                return {}
            return dat
        except AttributeError as _:
            log.error('RES: {}'.format(_))
            return dat

    def get_it(self, url='', params=None):
        url = url or API_URL['index']

        try:
            res = self.client.get(url, params=params, headers=HEADERS['mobile_json_headers'])
        except requests.ConnectionError as _:
            log.error('Cannot connect to {}'.format(url))
            base.force_quit()

        if self.enable_show_url:
            print(res.url)

        if res.status_code == 200:
            return self.is_res_success(res.json())

    def get_unread(self):
        # dat = self.get_it(API_URL['unread'], '').get('data', {})
        dat = self.get_it(API_URL['unread'], '')  # .get('data', {})
        if self.enable_show_url:
            log.debug('unread {}'.format(dat))
        if dat.get('data'):
            return dat.get('data')
        return dat

    def analy_base(self):
        scheme_url = self.base_info.get('follow_scheme')
        url, params = base.split_url_param(scheme_url)
        lfid = params.get('lfid')
        if lfid and len(lfid) > 6:
            self.domain_id = lfid[:6]

        tabs = self.base_info.get('tabsInfo', {})
        if not tabs:
            log.error('无法获取账号页面信息')
            return {}

        _tabs = tabs['tabs']
        if isinstance(_tabs, list):
            self.tabs_info = {
                x['tab_type']: x
                for x in _tabs
            }
        elif isinstance(_tabs, dict):
            self.tabs_info = {
                x['tab_type']: x
                for k, x in _tabs.items()
            }

    def get_enter_point(self):
        params = {
            'type': 'uid',
            'value': self.uid,
        }
        dat = self.get_it(API_URL['index'], params=params)
        return dat.get('data')

    def search(self, name, page=1):
        params = {
            'type': 'user',
            'queryVal': name,
            'containerid': '100103type={}&q={}'.format(3, name),
            'page': page if page > 0 else 1,
        }
        dat = self.get_it(API_URL['index'], params)
        return dat.get('data', {})

    def get_fans(self, page=1):
        """
            粉丝和关注账号的url, 可以直接拼接,
            唯一需求是 domain_id, 需要从enter_point中获取

        :return:
        :rtype:
        """
        if not self.domain_id:
            self.analy_base()
        p = {
            'containerid': '{}{}_-_FANS'.format(self.domain_id, self.uid),
            'page': page if page > 0 else 1,
        }
        dat = self.get_it(API_URL['fan_fo'], p)
        return dat.get('data', {})

    def get_followed(self, page=1):
        if not self.domain_id:
            self.analy_base()
        p = {
            'containerid': '{}{}_-_FOLLOWERS'.format(self.domain_id, self.uid),
            'page': page if page > 0 else 1,
        }
        dat = self.get_it(API_URL['fan_fo'], p)
        return dat.get('data', {})

    def get_feed(self, page=1):
        if not self.tabs_info:
            self.analy_base()

        params = {
            'type': 'uid',
            'page': page if page > 0 else 1,
            'value': self.uid,
            'containerid': self.tabs_info['weibo']['containerid'],
        }

        dat = self.get_it(API_URL['index'], params)
        return dat

    def post_it(self, prompt, url, form):
        """
            post form to url

        :param prompt: 提示信息
        :type prompt:
        :param url:
        :type url:
        :param form:
        :type form:
        :return:
        :rtype:
        """
        c = helper.yn_choice(
            '是否[{}]'.format(prompt)
        )
        if not c:
            log.warn('放弃 ({}) 操作.'.format(prompt))
            return

        res = self.client.post(url, data=form, headers=HEADERS['mobile_post_headers'])
        if self.enable_show_url:
            log.debug('POST {} with {}'.format(url, form))
        dat = res.json()

        if dat.get('ok') == 1:
            log.info('[{}]成功!!!'.format(prompt))
        else:
            log.error('错误: {}'.format(dat))
        return dat.get('ok')

    def do_follow(self, uid):
        user_info = self.base_info.get('userInfo')
        act = user_info.get('following')
        oper, url = ('取消关注', API_URL['un_follow']) if act else ('关注', API_URL['follow'])
        data = {
            'uid': uid,
            'st': self.st_token,
        }
        ok = self.post_it(oper, url, form=data)
        if ok:
            self.base_info = self.get_enter_point()

    def get_groups(self, uid):
        pass

    def do_add_groups(self):
        pass

    def pub_blog(self, dat):
        if not isinstance(dat, dict):
            dat = {'content': dat}
        data = {
            'st': self.st_token,
        }
        data = dict(data, **dat)
        self.post_it('发布微博', urljoin(API_URL['statuses'], 'update'), data)

    def upload_pic(self):
        pic_url = 'https://picupload.weibo.com/interface/pic_upload.php'
        params = {
            'cb': 'https://weibo.com/aj/static/upimgback.html?_wv=5&callback=STK_ijax_{}'.format(
                helper.unixtime(True) * 100),
            'mime': 'image/jpeg',
            'data': 'base64',
            'url': 'weibo.com/u/6069778559',
            'markpos': '1',
            'logo': '1',
            'marks': '1',
            'app': 'miniblog',
            's': 'rdxt',
            'file_source': '1',
        }
        pic_pth = ''
        if not pic_pth:
            pic_pth = click.prompt('输入图片路径,或者拖拽图片到此')
            pic_pth = pic_pth.lstrip().rstrip()
            if not pic_pth:
                log.error('a picture path should be given!!!')
                return

        if not confirm_do('上传图片'):
            return

        data = {
            'b64_data': base64.b64encode(helper.read_file(pic_pth))
        }

        raw = self.web_sess.post(pic_url, params=params, data=data, allow_redirects=False,
                                 headers=HEADERS['pic_headers'])

        if raw.status_code == 302:
            loc = raw.headers['Location']
            p = dict(parse_qsl(unquote_plus(loc)))
            return p
        else:
            log.error(raw.text)

    def publish_pic(self):
        pic = self.upload_pic()
        if not pic:
            log.error('upload picture failed!!!')
            return
        else:
            helper.cat_net_img('https://wx3.sinaimg.cn/orj360/{}.jpg'.format(pic['pid']))
        log.debug('pid: {}'.format(pic['pid']))
        data = {
            'content': '',
            'picId': pic['pid'],
        }
        cnt = base.multi_line_input('说点什么')
        data['content'] = cnt
        self.pub_blog(data)

    def publish_text(self):
        data = {
            'content': '',
        }
        cnt = base.multi_line_input('说点什么')
        data['content'] = cnt
        self.pub_blog(data)

    def publish_video(self):
        """
           暂时支持
        :return:
        :rtype:
        """
        cnt = ''
        cnt += base.multi_line_input('共两步:1. 描述视频一下')
        cnt += base.multi_line_input('2. 粘贴链接')
        self.pub_blog(cnt)

    def delete(self, feed):
        form = {
            'id': feed.get('mid'),
            'st': self.st_token
        }
        self.post_it('删除微博', urljoin(API_URL['blog_deal'], mblogDeal['delete']), form)

    def do_favor(self, feed=None):
        form = {
            'st': self.st_token,
            'id': feed.get('mid'),
        }
        if feed.get('favorited'):
            hint_ = '取消收藏'
            url = 'delFavMblog'
        else:
            hint_ = '收藏'
            url = 'addFavMblog'

        self.post_it(hint_, urljoin(API_URL['blog_deal'], url), form)

    def do_like(self, feed=None):
        """
            点赞

            - 执行与当前状态相反的操作

                + 已点赞 -> 则取消
                + 未点赞 -> 则点赞

        :param feed:
        :type feed:
        :return:
        :rtype:
        """
        # url = 'https://m.weibo.cn/api/attitudes/'
        form = {
            'id': feed.get('mid'),
            'st': self.st_token,
            'attitude': 'heart',
        }

        if feed.get('liked'):
            oper = '取消点赞'
            url = 'destroy'
        else:
            oper = '点赞'
            url = 'create'

        return self.post_it(oper, urljoin(API_URL['like'], url), form)

    def do_comment(self, feed=None):
        form = {
            'id': feed.get('mid'),
            'mid': feed.get('mid'),
            'st': self.st_token,
            'content': ''
        }
        comments = base.multi_line_input('输入评论')
        if not comments:
            log.error('comment is must')
            return

        form['content'] = comments
        return self.post_it('提交评论', urljoin(API_URL['comments'], 'create'), form)

    def do_forward(self, feed=None):
        form = {
            'id': feed.get('mid'),
            'mid': feed.get('mid'),
            'st': self.st_token,
            'content': ''
        }

        comments = base.multi_line_input('输入评论')
        form['content'] = comments
        return self.post_it('转发', urljoin(API_URL['statuses'], 'repost'), form)

    def web_forward(self, feed=None):
        url = 'https://weibo.com/aj/v6/mblog/forward'
        # todo: 自动获取或者登陆时更新 ``cfg -> weibo.domain``
        params = {
            'domain': cfg.get('weibo.domain'),
        }
        data = {
            'mid': feed.get('mid'),
            'style_type': 2,
            'rank': 0,
            'reason': '',
        }
        comments = base.multi_line_input('输入评论')
        if comments:
            data['reason'] = comments

        res = self.web_sess.post(url, params=params, data=data, headers=HEADERS['web_json_headers'])
        dat = res.json()
        if dat.get('code') == '100000':
            log.info('[{}]成功!!!'.format('转发'))
        else:
            log.error('错误: {}'.format(dat))

    def get_video(self, feed):
        """
            从 feed 数据中获取 标清 video 的路径, 并依据此从 web 页面解析获取 720p 视频源
        :param feed:
        :type feed:
        :return:
        :rtype:
        """

        def get_video_id_url(url_in='', bid=''):
            """
            https://m.weibo.cn/api/container/getIndex
            :param url_in:
            :type url_in:
            :return:
            :rtype:
            """
            _para = url_in.split('?')[1]
            url_in = 'https://m.weibo.cn/api/container/getIndex?' + _para
            res = self.client.get(url_in, headers=HEADERS['mobile_json_headers'])
            dat = res.json()['data']

            if not dat:
                return ''
            obj_id = dat.get('pageInfo', {}).get('object_id', '')
            url_in = 'https://weibo.com/tv/v/{}?fid={}'.format(bid, obj_id)
            return url_in

        def html_to_video(mark):
            if not mark:
                return
            for room in mark.find_all('div'):
                if room.get('action-type', '') == 'feed_list_third_rend':
                    video_src = dict(parse_qsl(unquote_plus(room.get('video-sources'))))
                    return video_src

        def gen_720p(dat):
            if not dat:
                return
            url = dat.get(dat.get('qType'))
            if not url:
                return

            ok = dat.get('template') and dat.get('Expires') and dat.get('ssig')
            if not ok:
                log.debug('no 720p video!!!, show orig')
                return

            params = {
                'template': dat['template'],
                'Expires': dat['Expires'],
                'ssig': dat['ssig'],
            }
            url = '{}&{}&KID={}'.format(url, urlencode(params), dat.get('KID', ''))
            feed['HDVideo'] = url

        retweeted = feed.get('retweeted_status')
        if retweeted:
            log.debug('ReTweeted Video')
            feed = retweeted
        url = feed.get('page_info', {}).get('page_url', '')
        url = get_video_id_url(url, feed.get('bid', ''))
        if not url:
            log.error('no video')
            return

        raw = self.web_sess.get(url)
        raw = self.user.bs4markup(raw.text)
        if not raw:
            log.error('no video')
            return

        player_room = raw.find('div', id='playerRoom')
        video_info = html_to_video(player_room)
        # log.debug('video_info: {}'.format(video_info))
        gen_720p(video_info)


class Myself(Login, WeiboBase):
    __metaclass__ = dec.Singleton

    """
        登陆账号的个人信息

        1. 从缓存文件中加载个人信息
        2. 更新个人信息到数据库中

    """

    def __init__(self, login_ok=True, uid_in='', log_level=1):
        Login.__init__(self)
        WeiboBase.__init__(self)
        self.log_debug_url = log_level == 1
        self.feeds = {}
        self.followed = {}
        self.fans = {}
        self.searched = {}
        self.ctrl = {}

        if login_ok:
            self.sess.cookies = self.load_cookies(base.app_pth['cookie'])
            self.mobile_sess.cookies = self.load_cookies(base.app_pth['mobile_cookie'])

            self.spawn(uid_in)

    def spawn(self, uid_in=''):
        self.ctrl = {
            'searched': {
                'name': '',
                'page': 1,
                'page_nums': 1,
                'size': 10,
                'total': 0,
            },
            'fans': {
                'name': '',
                'page': 1,
                'page_nums': 1,
                'size': 10,
                'total': 0,
            },
            'followed': {
                'name': '',
                'page': 1,
                'page_nums': 1,
                'size': 10,
                'total': 0,
            },
            'feeds': {
                'name': '',
                'page': 1,
                'page_nums': 1,
                'size': 10,
                'total': 0,
            },
        }
        self.personal_info = {}
        self.followed = {}
        self.fans = {}
        self.feeds = {}
        self.searched = {}

        self.user_uid = uid_in if uid_in else cfg.get('weibo.uid')
        self.is_me = self.user_uid == cfg.get('weibo.uid')
        #
        self.container_id = '{}{}'.format(cfg.get('weibo.domain'), self.user_uid)
        # 个人菜单选项
        # print('is Me: ', self.is_me)
        # self.menus = actions.get_user_action(self.is_me)
        self.api = WeiboApi(self, self.log_debug_url)

    def run(self):
        actions.Action(self)

    def reset_uid(self, uid=''):
        uid = uid or cfg.get('weibo.uid')
        self.spawn(uid)

    def ctrl_info(self, name):
        ctrl_ = self.ctrl.get(name)
        if not ctrl_:
            return ''
        inf_ = '{}/{}页,共:{}记录'.format(
            ctrl_['page'],
            int(ctrl_.get('total') // ctrl_['size']) + 1,
            ctrl_['total'],
        )
        if ctrl_.get('name'):
            inf_ = '{}{}'.format(ctrl_['name'], inf_)
        clr.info(inf_)

    def get_unread(self):
        msgs = self.api.get_unread()

        print('未读: {0[new]}, 私信: {0[sx]}'.format(msgs.get('qp')))

    def get_personal_info(self):
        """获取用户的信息
            - 关注/粉丝/微博数
            - 昵称/位置等信息
            - 增长信息: 会员/等级/勋章等
            - 阳光信用

        :return:
        :rtype:
        """
        dat = self.api.get_enter_point()
        self.personal_info = dat.get('userInfo')

    def ff(self, dat):
        d = [
            x.get('user') for x in dat.get('cards', [])
        ]
        return d

    def do_follow(self):
        self.api.do_follow(self.user_uid)

    def get_searched(self, step=0, abs_page=0):
        ctrl_ = self.ctrl['searched']
        # ctrl_['page'] += step
        # if ctrl_['page'] < 1:
        #     ctrl_['page'] = 1

        if self.cached_res('searched', step, abs_page):
            return

        if not step:
            # 每次进行查询时, 重置查询名字.
            ctrl_['name'] = ''
        ctrl_['name'] = ctrl_['name'] or click.prompt('name', type=str)

        dat = self.api.search(ctrl_['name'], ctrl_['page'])

        if dat.get('ok') == 0:
            ctrl_['page'] -= step
            self.ctrl_info('searched')
            return

        clinfo = dat.get('cardlistInfo')
        ctrl_['total'] = clinfo.get('total', 0)
        ctrl_['page_nums'] = ctrl_['total'] // ctrl_['size']

        d = [
            x for x in dat.get('cards') if x.get('card_type') == 11
        ][0]

        dat_ = []
        for card in d.get('card_group'):
            user__ = card.get('user')
            btn = card.get('buttons')[0]
            user__['following'] = btn.get('sub_type') == 1
            dat_.append(user__)

        self.searched[ctrl_['page']] = dat_
        self.ctrl_info('searched')

    def get_followed(self, step=0, abs_page=0):
        ctrl_ = self.ctrl['followed']

        if self.cached_res('followed', step, abs_page):
            return

        dat = self.api.get_followed(ctrl_['page'])

        if dat.get('ok') == 1:
            ctrl_['total'] = dat.get('count')
            ctrl_['page_nums'] = ctrl_['total'] // ctrl_['size']
            # print('followed: ', ctrl_)
            self.followed[ctrl_['page']] = self.ff(dat)
        elif dat.get('ok') == 0:
            ctrl_['page'] -= step

        self.ctrl_info('followed')

    def cached_res(self, key_in, step=0, abs_page=0):
        dat = getattr(self, key_in)
        ctrl_ = self.ctrl.get(key_in)
        ok = True
        ctrl_['page'] += step

        if abs_page:
            ctrl_['page'] = min(abs_page if abs_page > 0 else 1, ctrl_['page_nums'] + 1)

        while ok:
            if ctrl_['page'] in dat:
                break

            if step and ctrl_['page'] < 1:
                ctrl_['page'] = 1
                break
            ok = False

        if ctrl_['total'] and ok:
            self.ctrl_info(key_in)
        return ok

    def get_fans(self, step=0, abs_page=0):
        ctrl_ = self.ctrl['fans']

        if self.cached_res('fans', step, abs_page):
            return

        dat = self.api.get_fans(ctrl_['page'])

        if dat.get('ok') == 1:
            ctrl_['total'] = dat.get('count')
            ctrl_['page_nums'] = ctrl_['total'] // ctrl_['size']
            self.fans[ctrl_['page']] = self.ff(dat)
        elif dat.get('ok') == 0:
            ctrl_['page'] -= step

        self.ctrl_info('fans')

    def get_feeds(self, step=0, abs_page=0):
        ctrl_ = self.ctrl['feeds']

        if self.cached_res('feeds', step, abs_page):
            return

        dat = self.api.get_feed(ctrl_['page'])
        if dat.get('ok') == 1:
            dat = dat.get('data', {})
            cards = [
                x.get('mblog') for x in dat['cards']
                if x['card_type'] == 9
            ]
            ctrl_['total'] = dat.get('cardlistInfo').get('total')
            ctrl_['page_nums'] = ctrl_['total'] // ctrl_['size']
            self.feeds[ctrl_['page']] = cards
        elif dat.get('ok') == 0:
            ctrl_['page'] -= step

        self.ctrl_info('feeds')

    def video(self, feed=None):
        self.api.get_video(feed)

    def publish(self, feed=None):
        pass

    def publish_pic(self, feed=None):
        self.api.publish_pic()

    def publish_text(self, feed=None):
        self.api.publish_text()

    def publish_video(self, feed=None):
        self.api.publish_video()

    def delete(self, feed=None):
        self.api.delete(feed)

    def favor(self, feed=None):
        self.api.do_favor(feed)

    def like(self, feed=None):
        self.api.do_like(feed)

    def comment(self, feed=None):
        self.api.do_comment(feed)

    def forward(self, feed=None):
        self.api.do_forward(feed)

    def topit(self, feed=None):
        print('topit {}'.format(feed))

    def add_tag(self, feed=None):
        print('add_tag {}'.format(feed))

    def view_by_friends(self, feed=None):
        print('view_by_friends {}'.format(feed))

    def only_me(self, feed):
        print('only_me {}'.format(feed))

    def more(self, feed):
        _txt = base.bs4txt(feed.get('text'))
        print(_txt)

    def raw_data(self, feed):
        print(feed)

    def large(self, feed):
        pass


if __name__ == '__main__':
    from bs4 import BeautifulSoup as BS

    # fee = '分享图片 <a data-url="http://t.cn/R2WxlPJ" href="https://m.weibo.cn/p/tabbar?containerid=23044100658008635010000000000&needlocation=1&luicode=10000011&lfid=1076032757573151&page_type=tabbar&ep=FEbZx4TDI%2C2757573151%2CFEbZx4TDI%2C2757573151" data-hide=""><span class="url-icon"><img src="https://h5.sinaimg.cn/upload/2015/09/25/3/timeline_card_small_location_default.png"></span></i><span class="surl-text">福州</a>'
    # print(BS(fee).text)
    print(urljoin(API_URL['blog_deal'], 'delete'))
    # rs = base.multi_line_input()
    # print(rs)
