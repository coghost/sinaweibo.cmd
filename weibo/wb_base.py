# -*- coding: utf-8 -*-
__author__ = 'lihe <imanux@sina.com>'
__date__ = '04/01/2018 4:56 PM'
__description__ = '''
    ☰
  ☱   ☴
☲   ☯   ☵
  ☳   ☶
    ☷
'''

import os
import sys
import functools
import binascii
import base64
import json
import click
import re
from pprint import pprint

app_root = '/'.join(os.path.abspath(__file__).split('/')[:-2])
sys.path.append(app_root)

import requests
from clint import textui
from logzero import logger as log

from base.crawl import Crawl
from izen import helper, dec
import rsa

import base
from weibo import wb_mg_doc
from base import pprt
from base import cfg

M = {
    'refer': 'https://weibo.com/',
    'pre_login': 'https://login.sina.com.cn/sso/prelogin.php',
    'login': 'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)',
    'search_user': 'http://s.weibo.com/user/{}&page={}',
    'profile': 'https://weibo.com/{}/profile?topnav=1&wvr=6&is_all=1',
    'my_info': 'https://weibo.com/{}/info',
    'info': 'https://weibo.com/p/{}/info',
    'my_base_info': 'https://account.weibo.com/set/iframe',
    'album': 'http://photo.weibo.com/albums/get_all',
    'photo': 'http://photo.weibo.com/photos/get_all',
    'big_img': 'http://wx1.sinaimg.cn/large/{}.jpg',
    'get_my_follow': 'https://weibo.com/p/{}/myfollow',
    'get_follow': 'https://weibo.com/p/{}/follow',
    'get_my_fans': '',
    'get_fans': '',
    'do_follow': 'https://weibo.com/aj/f/followed?ajwvr=6',
    'do_add_group': 'http://s.weibo.com/ajax/user/addUserToGroup',
    'undo_follow': 'https://weibo.com/aj/f/unfollow',
    'pub_one': 'https://weibo.com/p/aj/v6/mblog/add',
    'weibo': 'https://weibo.com/p/{}'
}

HEADERS = {
    'mobile_json_headers': {
        'X-Requested-With': 'XMLHttpRequest',
        'Host': 'm.weibo.cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0',
        'Accept': 'application/json, */*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://m.weibo.cn',
    },
    'mobile_login_headers': {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
        'Host': 'passport.weibo.cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://m.weibo.cn',
    },
    'mobile_post_headers': {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
        'Host': 'm.weibo.cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://m.weibo.cn',
    },
    'web_json_headers': {
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0',
        'Host': 'weibo.com',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://weibo.com',
        'Content-Type': 'application/x-www-form-urlencoded',
    },
    'pic_headers': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Host': 'picupload.weibo.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://weibo.com',
        'Upgrade-Insecure-Requests': '1',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
}


class APIError(Exception):
    code = None
    """HTTP status code"""

    url = None
    """request URL"""

    body = None
    """server response body; or detailed error information"""

    def __init__(self, code, url, body):
        self.code = code
        self.url = url
        self.body = body

    def __str__(self):
        return 'code={s.code}\nurl={s.url}\n{s.body}'.format(s=self)

    __repr__ = __str__


class WeiboBase(Crawl):
    __metaclass__ = dec.Singleton

    def __init__(self, refer=M.get('refer', '')):
        Crawl.__init__(self, refer=refer)
        self.get_headers = {
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0',
        }
        self.post_headers = {
            'Host': 'login.sina.com.cn',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://weibo.com/',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        self.json_headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0',
            'Host': 'weibo.com',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://weibo.com',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        self.mobile_json_headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Host': 'm.weibo.cn',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0',
            'Accept': 'application/json, */*',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://m.weibo.cn',
        }
        self.pic_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Host': 'picupload.weibo.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://weibo.com',
            # 'X-Requested-With': 'XMLHttpRequest',
            'Upgrade-Insecure-Requests': '1',
            # 'Cookie': 'SINAGLOBAL=2387021546050.9604.1459612470000; ULV=1513134639264:2:2:2:1334820737119.291.1513134639112:1512880066460; SCF=AoNKXIor2ckWKv5uNCqwGIFlEt8jOwxy5sbK-uJ6WbFaeVAfNTbEuPQ5Yo4F1uVa7ShKvmfEo4jIInVD8JYoSe4.; SUHB=0btMiDZ5GGqzsu; UOR=,,login.sina.com.cn; wvr=6; _T_WM=7d84e18b9f0d552d4aa911691e107a17; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5rvaLovm-ojOzIZ5a3kPSA5JpX5KMhUgL.Foq7So.NS0nfSK.2dJLoIEXLxK-LB.eLBo2LxK-LB.eLBo2LxK-LB.eLBo2LxKBLBonL1h5LxKML1KBL1-qt; ALF=1546231873; _s_tentry=-; Apache=1334820737119.291.1513134639112; cross_origin_proto=SSL; SUB=_2A253TBySDeRhGeBO7VsW9ybJzjWIHXVUOAlarDV8PUNbmtAKLUXEkW9NRcESI51fUtkkCic1lzuPz0Y80V_mATUU; SSOLoginState=1514695874',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        self.mobile_login_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'Host': 'passport.weibo.cn',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://m.weibo.cn',
        }

        self.sess = requests.session()
        self.mobile_sess = requests.session()
        self.my_info = {}

        # weibo stk 返回的 domid, 在解析个人关注时, url拼接时需要使用
        # self.stk_dom_id = ''
        self.img_cache_dir = cfg.get('weibo.img_cache_dir', '/tmp/weibo')
        self.use_cache = cfg.get('weibo.use_cache', True)
        self.big_head = cfg.get('weibo.big_head', False)
        self.img_height = cfg.get('weibo.img_height', 12)

        self.cached_users_followed = []
        self.cached_users_followed_index = 0

    @staticmethod
    def load_albums_photos(dat):
        albums = wb_mg_doc.WeiboAlbums.objects(
            __raw__={'uid': dat['uid']}
        )
        dat = []
        for alb in albums:
            dat.append(alb._data)
        return dat

    def cat_net_img(self, pic_url, indent=4, large=False, height=0):
        """
            封装了 ``helper.cat_net_img`` 的偏函数, 方便使用本地配置参数

        :param height:
        :type height:
        :param large:
        :type large:
        :param pic_url:
        :type pic_url:
        :param indent:
        :type indent:
        :return:
        :rtype:
        """
        pic_url = self.use_big_head(pic_url, use_big=large)
        height = height or self.img_height
        # print('cat_net_img 223: ', pic_url)

        if 'large' in pic_url:
            cache_dir = os.path.join(self.img_cache_dir, 'large')
        else:
            cache_dir = os.path.join(self.img_cache_dir, 'default')

        functools.partial(helper.cat_net_img,
                          img_height=height,
                          img_cache_dir=cache_dir,
                          use_cache=self.use_cache)(url=pic_url, indent=indent)

    @staticmethod
    def add_http(img_url, pre='https'):
        if img_url.startswith('//'):
            img_url = '{}:{}'.format(pre, img_url)
        return img_url

    def use_big_head(self, img_url, use_big=False):
        """
            是否使用大图
            - 如果启用, 则替换 url 为 ``large``

        :param img_url:
        :type img_url:
        :param use_big:
        :type use_big:
        :return:
        :rtype:
        """
        img_url = self.add_http(img_url)

        if use_big or self.big_head:
            img = img_url.split('/')
            if not img[-2] == 'images':
                img[-2] = 'large'
            img_url = '/'.join(img)

        return img_url

    @staticmethod
    def get_markup_by_el_id(dat, el_id, which_key='html'):
        for k, v in dat.items():
            if k.find(el_id) != -1:
                return v.get(which_key)

    @staticmethod
    def trim_rtb(txt):
        """
            注意: 有中文空格

        :param txt:
        :type txt:
        :return:
        :rtype:
        """
        txt = helper.multi_replace(txt, ' | |\r|\t|\n|：,:')
        # txt = helper.multi_replace(txt, ' , | ,|：,:')
        return txt

    def wbui(self, orig_dat, cb=None, **kwargs):
        def echo(val=''):
            with textui.indent(indent=2, quote=' '):
                pprint(val)

        cb = cb if cb else echo
        choice = [x.get('_txt') for x in orig_dat]
        while True:
            c = helper.num_choice(
                choice,
                **kwargs
            )
            if str(c) in 'bB':
                return c
            cb(orig_dat[c])


class Login(WeiboBase):
    def __init__(self):
        WeiboBase.__init__(self)

    @staticmethod
    def gen_rsa(dat, password=''):
        rp = int(dat.get('pubkey'), 16)
        key = rsa.PublicKey(rp, 65537)
        msg = '{}\t{}\n{}'.format(dat.get('servertime'), dat.get('nonce'), password)
        msg = helper.to_bytes(msg)
        sp = rsa.encrypt(msg, key)
        sp = binascii.b2a_hex(sp)
        return sp

    def pre_login(self, username='', password=''):
        params = {
            'entry': 'weibo',
            'su': base64.b64encode(helper.to_bytes(username))[:-1],
            'rsakt': 'mod',
            'checkpin': 1,
            'client': 'ssologin.js(v1.4.19)',
            '_': helper.unixtime(mm=True)
        }
        raw = self.sess.get(M['pre_login'], params=params, headers=self.get_headers)
        dat = json.loads(raw.content)

        _sp = self.gen_rsa(dat, password=password)
        rt = {
            'servertime': dat['servertime'],
            'nonce': dat['nonce'],
            'rsakv': dat['rsakv'],
            'su': params['su'],
            'sp': _sp,
        }
        return rt

    def do_login(self, username='', password=''):
        if not username or not password:
            username = click.prompt('username', type=str)
            password = click.prompt('password', type=str, hide_input=True)

        form = {
            'entry': 'weibo',
            'gateway': '1',
            'from': '',
            'savestate': '7',
            'qrcode_flag': False,
            'useticket': '1',
            'pagerefer': 'https://login.sina.com.cn/crossdomain2.php?action=logout&r=https%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl%3D%252F',
            'vsnf': 1,
            'service': 'miniblog',
            'pwencode': 'rsa2',
            'sr': '1280*800',
            'encoding': 'UTF-8',
            'prelt': '41',
            'url': 'https://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
            'returntype': 'META',
            'sp': '',
            'servertime': '',
            'nonce': '',
            'rsakv': '',
        }
        dat = self.pre_login(username=username, password=password)
        form = dict(form, **dat)

        log.debug('STEP1: get {}'.format(M['login']))
        res = self.sess.post(M['login'], data=form, headers=self.post_headers)

        # 分析 login.php 返回信息的重定向 url
        pa = r'location\.replace\([\'"](.*?)[\'"]\)'
        loop_url = re.findall(pa, res.content.decode('GBK'))[0]
        log.debug('STEP2: get {}'.format(loop_url))
        # 获取返回第一次重定向 url 的返回信息
        res = self.sess.get(loop_url)
        # 返回信息分两部分, 第一部分 setCrossDomainUrlList 出现 302 Moved Temporarily 错误, 故跳过
        # 只取返回信息的第二部分 解析方式同 login.php 返回结果
        final_url = re.findall(pa, res.content.decode('GBK'))[0]
        log.debug('STEP3: get {}'.format(final_url))

        res = self.sess.get(final_url)
        uuid_pa = r'"uniqueid":"(.*?)"'
        uuid_res = re.findall(uuid_pa, res.text, re.S)[0]
        log.debug('STEP4: user_id: {}'.format(uuid_res))

        url = M['profile'].format(uuid_res)
        self.sess.get(url)
        # 存储 cookie 到本地, 为下次登陆时使用.
        self.dump_cookies(self.sess.cookies, base.app_pth['cookie'])
        return uuid_res

    def do_mobile_login(self, username='', password=''):
        url = 'https://passport.weibo.cn/sso/login'
        if not username or not password:
            username = click.prompt('username', type=str)
            password = click.prompt('password', type=str, hide_input=True)
        form = {
            'username': username,
            'password': password,
            'savestate': '1',
            'ec': '0',
            'entry': 'mweibo',
            'wentry': '',
            'loginfrom': '',
            'client_id': '',
            'code': '',
            'qq': '',
            'mainpageflag': '1',
            'hff': '',
            'hfp': '',
        }
        res = self.mobile_sess.post(url, data=form, headers=self.mobile_login_headers)
        dat = res.json().get('data', {})
        # print(dat)
        if dat.get('uid'):
            # self.uid = dat.get('uid')
            log.info('[MOBILE-LOGIN:SUCCESS] ({})'.format(dat.get('uid')))
            self.dump_cookies(self.mobile_sess.cookies, base.app_pth['mobile_cookie'])
            return username, password
        else:
            log.error('[FAILED] ({})'.format(res.json()))

    def login(self, auto_login=True):
        username, password = '', ''
        if auto_login:
            username = cfg.get('weibo.username', '')
            password = cfg.get('weibo.password', '')
        else:
            dml = self.do_mobile_login(username, password)
            if dml:
                username, password = dml
        uuid_ = self.do_login(username, password)

        url = M['profile'].format(uuid_)
        raw = self.sess.get(url)
        me = self.dump_my_page_config(raw.text)
        log.info('[LOGIN:SUCCESS] {}({})'.format(me.get('nick'), me.get('uid')))

    @staticmethod
    def dump_my_page_config(txt):
        """
            保存个人登陆信息到本地缓存

        :param txt:
        :type txt:
        :return:
        :rtype:
        """

        def get_config(raw_mark):
            """
                从 config 字段中解析出账号的信息

            :param raw_mark:
            :type raw_mark:
            :return:
            :rtype:
            """
            _START = '<!-- $CONFIG -->'
            _END = '<!-- / $CONFIG -->'
            return raw_mark.split(_START)[1].split(_END)[0]

        txt = get_config(txt)
        txt = [t[1:].rstrip() for t in txt.split('\n') if t and t.find('CONFIG') != -1 and t.find('var ') == -1]
        dat = {}
        keys = ['oid', 'page_id', 'uid', 'nick', 'sex',
                'watermark', 'domain', 'lang', 'skin',
                'avatar_large', 'pid', ]

        for t in txt:
            k, v = t[:-1].split('=')
            k = k.split('\'')[1]
            if k not in keys:
                continue
            dat[k] = v.replace('\'', '') if k != 'avatar_large' else 'http:' + v.replace('\'', '')

        helper.write_file(json.dumps(dat), base.app_pth['personal'])
        return dat

    def load_my_page_config(self):
        my_info = json.loads(helper.read_file(base.app_pth['personal']))
        self.my_info = my_info
        if not my_info:
            log.error('Login to get your person info first!!!')
            base.force_quit()

    @dec.catch(True, requests.TooManyRedirects, hints='登陆失败: 请求超时, 异常退出. ')
    def is_cookie_ok(self):
        url = 'http://photo.weibo.com/albums/get_all?uid={}&page=1&count=20'.format(
            self.my_info.get('uid'))
        # log.info('TEST of access to {}'.format(url))

        rs = self.sess.get(url, headers=self.get_headers)
        if rs.history and rs.history[0].status_code == 302:
            log.warn('✘ [session Expired], re-login.')
            base.force_quit()
        else:
            log.info('✔ [Web session] is ok!!!')

    def mobile_login(self, auto_login=True):
        username, password = '', ''
        if auto_login:
            username = cfg.get('weibo.username', '')
            password = cfg.get('weibo.password', '')
        # username = cfg.get('weibo.username', '')
        # password = cfg.get('weibo.password', '')
        self.do_mobile_login(username, password)
        # log.info('[MOBILE-LOGIN:SUCCESS] ({})'.format(dat.get('uid')))

    def is_mobile_login_ok(self):
        url = 'https://m.weibo.cn/api/config'
        res = self.mobile_sess.get(url, headers=self.mobile_json_headers)
        if res and res.json():
            dat = res.json()
            if dat['data']['login']:
                log.debug('✔ [Mobile Session] is Valid!!!')
                return True
        else:
            log.error('✘ [Mobile Session] is in-Valid!!!')
        return False
