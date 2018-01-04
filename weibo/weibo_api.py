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
import time
import functools
from pprint import pprint
import binascii

app_root = '/'.join(os.path.abspath(__file__).split('/')[:-2])
sys.path.append(app_root)

import requests

from izen.crawl import Crawl
from izen import helper
import click

import rsa
from clint import textui

from logzero import logger as log
from tqdm import tqdm
from izen import helper, dec

from base import dbstore
import base
from base import cfg

from weibo import wb_mg_doc

from weibo import actions

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

_personal_info_pth = os.path.join(base.base_pth, 'dat/personal.txt')
_cookie_pth = os.path.join(base.base_pth, 'dat/cookie.txt')
_mobile_cookie_pth = os.path.join(base.base_pth, 'dat/mobile_cookie.txt')

# TODO 使用 bs4 替换
zh_cn_colon = '：'
enable_catch = False


class Player(object):
    def __init__(self, url):
        self.url = url
        self.init()

    @dec.threads(True)
    def init(self, use_cache=True, show_log=False):
        cmd = '/usr/local/bin/mplayer -vo corevideo -slave'
        if use_cache:
            cmd += ' -cache 8192'
        if not show_log:
            cmd += ' -really-quiet'
        cmd += ' "{}" &'.format(self.url)
        os.popen(cmd).read()


class WeiboBase(Crawl):
    __metaclass__ = dec.Singleton

    def __init__(self, refer=M.get('refer', ''),
                 big_head=False, img_cache_dir='/tmp/weibo', img_height=6, use_cache=True,
                 ):
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
            'Accept': '*/*',
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
        self.img_cache_dir = img_cache_dir
        self.use_cache = use_cache
        self.big_head = big_head
        self.img_height = img_height

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
        _use_big = large
        if large:
            cache_dir = os.path.join(self.img_cache_dir, 'large')
        else:
            cache_dir = os.path.join(self.img_cache_dir, 'default')

        pic_url = self.use_big_head(pic_url, use_big=_use_big)
        height = height or self.img_height
        # print(pic_url, height)

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
        self.dump_cookies(self.sess.cookies, _cookie_pth)
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
            # 'r': 'https://m.weibo.cn',
            'ec': '0',
            # 'pagerefer': 'https://passport.weibo.cn/signin/',
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
        dat = res.json().get('data')
        self.dump_cookies(self.mobile_sess.cookies, _mobile_cookie_pth)
        return dat


class WeiboPage(WeiboBase):
    def __init__(self):
        WeiboBase.__init__(self)

    def stk_view_js_to_html(self, dat):
        """
            转换 ``weibo stk js`` 为可识别的 html Markup

            输出:
            <div class="list_person clearfix">
                <div class="person_pic">
                    <a target="_blank" href="//weibo.com/u/1915268965?refer_flag=1001030201_" title="霹雳无敌李三娘" suda-data="key=tblog_search_user&value=user_feed_1_icon"><img class="W_face_radius" src="//tvax1.sinaimg.cn/crop.0.0.1242.1242.180/7228af65ly8fmc4jx2rwij20yi0yi419.jpg" uid="1915268965" height="80" width="80"/></a>
                </div>
                <div class="person_detail">
                    <p class="person_name">
                        <a class="W_texta W_fb" target="_blank" href="//weibo.com/u/1915268965?refer_flag=1001030201_" title="霹雳无敌李三娘" uid="1915268965" suda-data="key=tblog_search_user&value=user_feed_1_name">
                            霹雳无敌<em class="red">李三娘</em>
                        </a>
                        <a target="_blank" href="//verified.weibo.com/verify" title= "微博个人认证 " alt="微博个人认证 " class="W_icon icon_approve"></a><a href="//vip.weibo.com/personal?from=search" target="_blank" title="微博会员"><i class="W_icon ico_member4"></i></a>
                    </p>
                    <p class="person_addr">
                        <span class="female m_icon" title="女"></span>
                        <span>其他</span>
                        <a class="W_linkb" target="_blank" href="//weibo.com/u/1915268965?refer_flag=1001030201_" class="wb_url" suda-data="key=tblog_search_user&value=user_feed_1_url">//weibo.com/u/1915268965</a>
                    </p>
                    <p class="person_card">
                        知名萌宠博主 萌宠视频自媒体
                    </p>
                    <p class="person_num">
                        <span>关注<a class="W_linkb" href="//weibo.com/1915268965/follow?refer_flag=1001030201_" target="_blank" suda-data="key=tblog_search_user&value=user_feed_1_num">333</a></span>
                        <span>粉丝<a class="W_linkb" href="//weibo.com/1915268965/fans?refer_flag=1001030201_" target="_blank" suda-data="key=tblog_search_user&value=user_feed_1_num">10万</a></span>
                        <span>微博<a class="W_linkb" href="//weibo.com/1915268965/profile?refer_flag=1001030201_" target="_blank" suda-data="key=tblog_search_user&value=user_feed_1_num">3319</a></span>
                    </p>
                        <div class="person_info">
                            <p>简介：
                                天天被儿砸殴打的老母亲
                            </p>
                        </div>
                        <p class="person_label">标签：
                            <a class="W_linkb" href="&tag=%25E5%25A4%25A9%25E7%25A7%25A4%25E5%25BA%25A7&Refer=SUer_tag" suda-data="key=tblog_search_user&value=user_feed_1_label">
                                天秤座
                            </a>
                            <a class="W_linkb" href="&tag=%25E5%25A6%2596%25E5%25AD%25BD&Refer=SUer_tag" suda-data="key=tblog_search_user&value=user_feed_1_label">
                                妖孽
                            </a>
                            <a class="W_linkb" href="&tag=%25E9%2585%2592%25E9%25AC%25BC%25E4%25B8%2580%25E6%259E%259A&Refer=SUer_tag" suda-data="key=tblog_search_user&value=user_feed_1_label">
                                酒鬼一枚
                            </a>
                        </p>
                </div>
            </div>

        :param dat:
        :type dat:
        :return:
        :rtype:
        """
        raw = self.bs4markup(dat)
        dat = raw.find('script').text.split('{')[1].split('}')[0]
        dat = '{' + dat + '}'
        try:
            dat = json.loads(dat)
            if dat.get('html'):
                user_raw = dat.get('html')
                # user_raw = user_raw.replace('\n', '').replace('\t', '').replace('\/', '/')
                # user_raw = user_raw.replace('\n', '').replace('\t', '').replace('\/', '/')
                user_raw = helper.multi_replace(user_raw, '\n|\t|\/')
                dat['html'] = user_raw
        except json.JSONDecodeError as _:
            return {}

        return dat

    def page_to_dict(self, raw):
        """
            转换页面 js script 内容为 dict
        :return:
        :rtype:
        """
        elems = {}
        for line in raw.split('\n'):
            if line.find('<script>FM.view({') == -1:
                continue

            el = self.stk_view_js_to_html(line)
            if el:
                elems[el['domid']] = el

        return elems


class WeiboCli(WeiboBase):
    __metaclass__ = dec.Singleton

    def __init__(self):
        WeiboBase.__init__(self)


class WeiboUser(WeiboBase):
    """
        微博个人账号信息
    """

    def __init__(self, uid_in=''):
        WeiboBase.__init__(self)
        self.user_uid = uid_in
        self.is_me = False
        # self.container_id = '{}{}'.format(self.my_info['domain'], self.user_uid)
        self.container_id = ''
        self.mobile_container = {}

        self.info_page_dict = {}
        self.follow_page_dict = {}
        # self.follow_page = {
        #     'index': 1,
        # }
        # self.uid = ''
        self.k2v = {
            'nick': '昵称',
            'city': '所在地',
            'sex': '性别',
            'domain': '个性域名',
            'brief': '简介',
            'level': '当前等级',
            'got': '经验值',
            'needed': '距离升级需经验值',
            'upgrade_speed': '成长速度',
            'total': '成长值',
            'upgrade_in': '下次升级',
            'username': '登录名',
            'realname': '真实姓名',
            'sex_trend': '性取向',
            'love_view': '感情状况',
            'birth': '生日',
            'blood': '血型',
            'blog': '博客地址',
            'desc': '简介',
            'reg_date': '注册时间',
            'email': '邮箱',
            'qq': 'QQ',
            'msn': 'MSN',
            'tags': '标签',
        }
        self.personal_info = {
            'info': {},
            'tags': [],
            'honors': [],
            'counter': {
                'follow': 1,
                'fans': 1,
                'weibo': 1,
            },
            'level_info': {
                'level': '',
                'got': 0,
                'needed': 0,
            },
            'credit': {
                'desc': '',
            },
            'vip': {
                'info': '',
                'upgrade_speed': 0,
                'total': 0,
                'upgrade_in': 0,
            },
        }
        self.followed = []
        self.fans = []
        self.page_index = {
            'feed': 1,
            'follow': 1,
        }
        self.feeds = []
        self.menus = actions.get_user_action(self.is_me)

    def bs_it(self, dat, el_id):
        """ 转换成 BS """
        raw = self.get_markup_by_el_id(dat, el_id)
        markup = self.bs4markup(raw)
        return markup

    @staticmethod
    def degree2val(deg):
        """
            阳光信息角度转换成实际分数

        :param deg:
        :type deg:
        :return:
        :rtype:
        """
        if deg < 0:
            deg = abs(deg)
        else:
            deg += 90

        a = 300
        b = 900
        d = (b - a) * deg / 180 + 300
        return int(d)

    def get_en_key(self, val):
        for k, v in self.k2v.items():
            if v == self.trim_rtb(val):
                return k

    def load_markup(self, url, params=None):
        if params:
            raw = self.sess.get(url, params=params)
            # print(raw.url, params)
        else:
            raw = self.sess.get(url)
        return WeiboPage().page_to_dict(raw.text)

    @staticmethod
    def action_to_dict(plain):
        dat = {}
        if not plain:
            return dat

        acts = plain.split('&')

        for act in acts:
            k, v = act.split('=')
            if k and v:
                dat[k] = v
        return dat

    def get_counter(self):
        raw = self.get_markup_by_el_id(self.info_page_dict, 'Pl_Core_T8CustomTriColumn__')
        markup = self.bs4markup(raw)
        person_num = ''
        for lk in markup.find_all('a'):
            person_num += lk.text
        person_num = helper.multi_replace(person_num, '\n|关注,/|粉丝,/|微博')
        c_ = person_num.split('/')
        counter = {
            'follow': c_[0],
            'fans': c_[1],
            'weibo': c_[2],
        }
        self.personal_info['counter'] = counter

    def get_info(self):
        """
            用来非自己的账号的基本信息

        :return:
        :rtype:
        """
        raw = self.get_markup_by_el_id(self.info_page_dict, 'Pl_Official_PersonalInfo__')
        markup = self.bs4markup(raw)
        lis = markup.find_all('li', 'li_1 clearfix')

        def txt_detail(li_m):
            alinks = li_m.find('span', 'pt_detail').find_all('a')
            if not alinks:
                txt = li_m.text.split(zh_cn_colon)
                k = self.get_en_key(txt[0])
                self.personal_info['info'][k] = self.trim_rtb(txt[1])
                return
            for a in alinks:
                self.personal_info['tags'].append(self.trim_rtb(a.text))

        for li in lis:
            txt_detail(li)

    def get_credit(self):
        raw = self.bs_it(self.info_page_dict, 'Pl_Third_Inline__')
        cre = raw.find('div', 'text_box available avable_color')
        if cre:
            self.personal_info['credit']['desc'] = self.trim_rtb(cre.text)

    def get_grow_info(self):
        """
            bagde: 勋章
            level: 级别
            vip:   会员

        :return:
        :rtype:
        """
        raw = self.bs_it(self.info_page_dict, 'Pl_Official_RightGrowNew__')

        def get_badge():
            lis = raw.find_all('li', 'bagde_item')
            for li in lis:
                self.personal_info['honors'].append(li.a.get('title'))

        def get_level():
            level_box = raw.find('div', 'level_box S_txt2')
            for span in level_box.find('p', 'level_info').find_all('span', 'info'):
                txt = span.text.split(zh_cn_colon)
                k = self.get_en_key(txt[0])
                self.personal_info['level_info'][k] = self.trim_rtb(txt[1])

        def get_vip():
            vip_box = raw.find('div', 'vip_box S_txt2')
            if not vip_box:
                return
            _years_raw = vip_box.find('p', 'info_icon_box')
            _year = ''
            for pi in _years_raw.find_all('i'):
                _suffix = pi.text
                if not _suffix:
                    _c = pi.get('class')
                    if _c:
                        _c = helper.multi_replace(_c[1], 'icon_member')
                        _year += _c
                        continue
                _year += _suffix
            self.personal_info['vip']['info'] = _year
            vip_info_raw = raw.find('div', 'vip_info line S_line1')
            for p in vip_info_raw.find_all('p'):
                txt = p.text.split(zh_cn_colon)
                k = self.get_en_key(txt[0])
                self.personal_info['vip'][k] = self.trim_rtb(txt[1])

        get_badge()
        get_level()
        get_vip()

    def get_personal_info(self):
        """获取用户的信息
            - 关注/粉丝/微博数
            - 昵称/位置等信息
            - 增长信息: 会员/等级/勋章等
            - 阳光信用

        :return:
        :rtype:
        """
        url = M['info'].format(self.my_info.get('pid', '') + self.user_uid)
        self.info_page_dict = self.load_markup(url)
        self.get_counter()
        self.get_info()

        self.get_grow_info()
        self.get_credit()

    def get_personal_followed(self):
        params = {
            't': 1,
            'cfs': ''
        }
        # 默认使用自己的信息
        _from_id = self.my_info.get('domain') + self.user_uid
        follow_url = M['get_follow']
        url = follow_url.format(_from_id)

        follow_id = 'Pl_Official_HisRelation__'
        # params['page'] = self.follow_page['index']
        params['page'] = self.page_index['follow']

        self.follow_page_dict = self.load_markup(url, params=params)
        user_raw = self.get_markup_by_el_id(self.follow_page_dict, follow_id)
        user_raw = self.bs4markup(user_raw)

        def get_markup_txt(mark):
            if not mark:
                return ''
            return mark.text

        def user_followed():
            """
                action-data="uid=5943836571&fnick=叫什么不一定&sex=f"
                //tvax1.sinaimg.cn/crop.0.0.512.512.50/006ufJpNly8fme6z2nhfmj30e80e8mxi.jpg

            :return:
            :rtype:
            """
            follow_list = user_raw.find('ul', 'follow_list')
            members_ = []
            for li in follow_list.find_all('li', 'follow_item S_line2'):
                img_src = self.use_big_head(li.find('img').get('src'))
                info = li.get('action-data')
                followed = self.action_to_dict(info)

                mod_info = li.find('dd', 'mod_info S_line1')
                d = {
                    'name': followed.get('fnick', ''),
                    'uid': followed.get('uid', ''),
                    'sex': followed.get('sex'),
                    'person_pic': img_src,
                }

                if mod_info:
                    info_connect = get_markup_txt(mod_info.find('div', 'info_connect'))
                    address = get_markup_txt(mod_info.find('div', 'info_add').span)
                    brief = get_markup_txt(mod_info.find('div', 'info_intro'))
                    info_from = get_markup_txt(mod_info.find('div', 'info_from').a)
                    d['info_connect'] = helper.multi_replace(info_connect, '关注,|粉丝,/|微博,/')
                    d['brief'] = brief
                    d['address'] = address
                    d['info_from'] = info_from

                d = {
                    k: self.trim_rtb(v)
                    for k, v in d.items()
                }
                members_.append(d)

            return members_

        self.followed = user_followed()

    def get_followed(self):
        """
            用户的关注列表

        :return:
        :rtype:
        """
        self.get_personal_followed()

    def get_fans(self, user_info=None):
        pass

    @staticmethod
    def feed_detail(doc):
        return WeiboFeed(doc)

    def get_mobile_container_id(self):
        url = 'https://m.weibo.cn/api/container/getIndex?containerid={}'.format(self.container_id)
        res = self.mobile_sess.get(url, headers=self.mobile_json_headers)
        dat = res.json()
        tabs = dat['data']['tabsInfo']['tabs']
        for t in tabs:
            self.mobile_container[t['tab_type']] = t['containerid']
        # print(self.mobile_container)

    def get_feed(self):
        if not self.mobile_container:
            self.get_mobile_container_id()

        url = 'https://m.weibo.cn/api/container/getIndex'
        params = {
            'containerid': self.mobile_container['weibo'],
            'page': self.page_index['feed']
        }
        res = self.mobile_sess.get(url, params=params, headers=self.mobile_json_headers)
        dat = res.json()['data']
        cards = [
            x.get('mblog') for x in dat['cards']
            if x['card_type'] == 9
        ]
        # print(cards)
        self.feeds.append(cards)

    def get_feed_by_page(self):
        """
            domid = Pl_Official_MyProfileFeed

        :return:
        :rtype:
        """
        params = {
            'is_all': 1,
        }
        url = M['weibo'].format(self.my_info.get('pid', '') + self.user_uid)
        msgs = self.load_markup(url, params=params)
        user_raw = self.get_markup_by_el_id(msgs, 'Pl_Official_MyProfileFeed')
        user_raw = self.bs4markup(user_raw)
        feeds_raw = user_raw.find_all('div', tbinfo='ouid={}'.format(self.user_uid))
        feeds_ = []
        for feed in feeds_raw:
            feeds_.append(self.feed_detail(feed))

        self.feeds.append(feeds_)

    def more(self, feed):
        pass

    def raw_data(self, feed):
        pass

    def large(self, feed):
        pass

    def video(self, feed):
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
            res = self.mobile_sess.get(url_in, headers=self.mobile_json_headers)
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

            params = {
                'template': dat['template'],
                'Expires': dat['Expires'],
                'ssig': dat['ssig'],
            }
            url = '{}&{}&KID={}'.format(url, urlencode(params), dat.get('KID', ''))
            feed['HDVideo'] = url

        url = feed.get('page_info', {}).get('page_url', '')
        url = get_video_id_url(url, feed.get('bid', ''))
        if not url:
            log.error('no video')
            return

        raw = self.sess.get(url)
        raw = self.bs4markup(raw.text)
        if not raw:
            log.error('no video')
            return

        player_room = raw.find('div', id='playerRoom')
        video_info = html_to_video(player_room)
        # log.debug('video_info: {}'.format(video_info))
        gen_720p(video_info)

    def forward(self, feed=None):
        print('forward {}'.format(feed))

    def comment(self, feed=None):
        print('comment {}'.format(feed))

    def like(self, feed=None):
        print('like {}'.format(feed))

    def favor(self, feed=None):
        print('favor {}'.format(feed))


class WeiboJson(WeiboBase):
    """
        all in this class is communication with weibo.cn
    """

    def __init__(self, url):
        WeiboBase.__init__(self)
        self.showed = []
        self.info = {}
        self.media = {
            'images': [],
            'video': {},
        }
        self.init(url)

    def init(self, url):
        res = self.sess.get(url)


class WeiboFeed(WeiboBase):
    def __init__(self, doc):
        WeiboBase.__init__(self)
        self.showed = []
        self.info = {}
        self.media = {
            'images': [],
            'video': {},
        }
        self.init(doc)

    def feed_html_to_text(self, _cnt_txt, is_long=False):
        cnt = []
        for i, c in enumerate(_cnt_txt):
            if not cnt:
                if not self.trim_rtb(c):
                    continue
                cnt.append(c.lstrip())
            elif cnt[0].find('置顶') != -1 and len(cnt) == 1:
                cnt.append(c.lstrip())
            elif len(cnt) > 2 and cnt[-1].find('视频') != -1:
                cnt[-2] = cnt.pop()
            elif c == '展开全文':
                self.showed.append('more')
                break
            else:
                cnt.append(c)

        # TODO: add this to config file.
        content_display_line = 3
        if is_long:
            return '\n'.join(cnt)
        return '\n'.join(cnt[:content_display_line])

    def html_to_video(self, mark):
        if not mark:
            return
        video_data = mark.get('action-data')
        video_data = unquote_plus(video_data)
        video_data = dict(parse_qsl(video_data))
        # 可播放视频的源文件, 不能使用 action-data, 出现 404错误.
        video_src = dict(parse_qsl(unquote_plus(mark.get('video-sources'))))

        self.media['video']['data'] = video_data
        self.media['video']['source'] = video_src
        self.showed.append('video')

    def feed_html_to_media(self, media_raw):
        if not media_raw:
            return

        media_raw_ul = media_raw.find('div', 'media_box')
        images = []

        for li in media_raw_ul.find_all('li'):
            if 'WB_pic' in li.get('class'):
                images.append(li.img.get('src'))
            elif 'WB_video' in li.get('class'):
                self.html_to_video(li)
        self.media['images'] = images
        if images:
            self.showed.append('more')
            self.showed.append('large')

    def init(self, doc):
        """
            时间, 来自,
            内容, 展开全文,

            可用操作
        :param doc:
        :type doc:
        :return:
        :rtype:
        """
        self.info['mid'] = doc.get('mid')
        detail = doc.find('div', 'WB_detail')
        from_raw = detail.find('div', 'WB_from S_txt2').find_all('a')
        self.info['time'] = from_raw[0].get('title')
        self.info['app_source'] = from_raw[1].text
        _cnt_txt = detail.find('div', 'WB_text W_f14').strings
        self.info['content'] = self.feed_html_to_text(_cnt_txt)

        media_raw = detail.find('div', 'WB_media_wrap clearfix')
        self.feed_html_to_media(media_raw)

    def load_more(self, raw):
        if raw:
            dat = raw.json()
            longtext = dat.get('data', {}).get('html', '')
            longtext = self.bs4markup(longtext)
            self.info['longtext'] = self.feed_html_to_text(longtext.strings, is_long=True)


class Myself(Login, WeiboUser):
    __metaclass__ = dec.Singleton

    """
        登陆账号的个人信息

        1. 从缓存文件中加载个人信息
        2. 更新个人信息到数据库中

    """

    def __init__(self, login_ok=True, uid_in=''):
        Login.__init__(self)
        WeiboUser.__init__(self)
        self.followed_dom_id = ''
        self.mobile_config = {}

        if login_ok:
            self.sess.cookies = self.load_cookies(_cookie_pth)
            self.mobile_sess.cookies = self.load_cookies(_mobile_cookie_pth)
            self.load_my_page_config()
            self.user_uid = uid_in if uid_in else self.my_info.get('uid')
            self.is_me = self.user_uid == self.my_info.get('uid')
            self.container_id = '{}{}'.format(self.my_info['domain'], self.user_uid)
            self.menus = actions.get_user_action(self.is_me)
            self.refresh_mobile_config()

    def run(self):
        Action(self)

    def refresh_mobile_config(self):
        url = 'https://m.weibo.cn/api/config'
        res = self.mobile_sess.get(url)
        if res and res.json():
            self.mobile_config = res.json().get('data')
        if not self.mobile_container:
            self.get_mobile_container_id()

    def login(self):
        username = cfg.get('weibo.username', '')
        password = cfg.get('weibo.password', '')
        uuid_ = self.do_login(username, password)

        url = M['profile'].format(uuid_)
        raw = self.sess.get(url)
        me = self.dump_my_page_config(raw.text)
        log.info('[LOGIN:SUCCESS] {}({})'.format(me.get('nick'), me.get('uid')))

    def mobile_login(self):
        username = cfg.get('weibo.username', '')
        password = cfg.get('weibo.password', '')
        dat = self.do_mobile_login(username, password)
        log.info('[MOBILE-LOGIN:SUCCESS] ({})'.format(dat.get('uid')))

    def is_mobile_login_ok(self):
        url = 'https://m.weibo.cn/api/config'
        res = self.mobile_sess.get(url, headers=self.mobile_json_headers)
        if res and res.json():
            dat = res.json()
            if dat['data']['login']:
                log.debug('Mobile Session is Valid!!!')
        else:
            log.error('Mobile Session is in-Valid!!!')

    @dec.catch(True, requests.TooManyRedirects, hints='登陆失败: 请求超时, 异常退出. ')
    def is_cookie_ok(self):
        url = 'http://photo.weibo.com/albums/get_all?uid={}&page=1&count=20'.format(
            self.my_info.get('uid'))
        log.info('TEST of access to {}'.format(url))

        rs = self.sess.get(url, headers=self.get_headers)
        if rs.history and rs.history[0].status_code == 302:
            log.warn('session Expired, re-login.')
            base.force_quit()
        else:
            log.info('Web session is ok!!!')

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

        helper.write_file(json.dumps(dat), _personal_info_pth)
        return dat

    def load_my_page_config(self):
        my_info = json.loads(helper.read_file(_personal_info_pth))
        self.my_info = my_info
        if not my_info:
            log.error('Login to get your person info first!!!')
            base.force_quit()

    def get_personal_info(self):
        """获取用户的信息
            - 关注/粉丝/微博数
            - 昵称/位置等信息
            - 增长信息: 会员/等级/勋章等
            - 阳光信用

        :return:
        :rtype:
        """
        url = M['info'].format(self.my_info.get('pid', '') + self.user_uid)
        self.info_page_dict = self.load_markup(url)
        self.get_counter()

        if self.is_me:
            self.get_iframe_info()
        else:
            self.get_info()

        self.get_grow_info()
        self.get_credit()

    def get_iframe_info(self):
        raw = self.sess.get(url='https://account.weibo.com/set/iframe')
        raw = self.bs4markup(raw.text)
        account_items = raw.find('div', id='pl_content_account').find_all('div', 'infoblock')

        def get_base_view():
            if not account_items:
                return
            for pf_item in account_items[0].find_all('div', 'pf_item clearfix'):
                parent = pf_item.parent.parent
                if parent.get('style') and parent.get('style').find('display:none') != -1:
                    continue

                key_ = pf_item.find('div', 'label S_txt2').text
                key_ = self.trim_rtb(key_)

                if not key_:
                    return
                con = pf_item.find('div', 'con')

                if not len(list(con.stripped_strings)):
                    txt = ''
                else:
                    txt = list(con.stripped_strings)[0]
                if con.find('a'):
                    txt = txt.replace(con.a.text, '')
                txt = self.trim_rtb(txt)
                key_ = self.get_en_key(key_)
                # print('BASE: {} ==> {}'.format(key_, txt))
                self.personal_info['info'][key_] = txt

        def get_connection():
            d = {}
            if len(account_items) < 2:
                return
            for pf_item in account_items[1].find_all('div', 'pf_item clearfix'):
                key_ = pf_item.find('div', 'label S_txt2').text
                key_ = self.trim_rtb(key_)
                if not key_:
                    return
                con = pf_item.find('div', 'con')

                if not len(list(con.stripped_strings)):
                    continue

                txt = list(con.stripped_strings)[0]
                if con.find('a'):
                    txt = txt.replace(con.a.text, '')
                txt = self.trim_rtb(txt)
                key_ = self.get_en_key(key_)
                # print('CONN: {} ==> {}'.format(key_, txt))
                self.personal_info['info'][key_] = txt

        def get_job():
            if len(account_items) < 3:
                return
            for pf_item in account_items[2].find_all('div', 'pf_item clearfix'):
                key_ = pf_item.find('div', 'label S_txt2').text
                key_ = self.trim_rtb(key_)
                if not key_:
                    return
                con = pf_item.find('div', 'con')

                if not len(list(con.stripped_strings)):
                    continue

                txt = list(con.stripped_strings)[0]
                if con.find('a'):
                    txt = txt.replace(con.a.text, '')
                txt = self.trim_rtb(txt)
                print('JOB: {} ==> {}'.format(key_, txt))

        def get_edu():
            if len(account_items) < 4:
                return
            for pf_item in account_items[3].find_all('div', 'pf_item clearfix'):
                key_ = pf_item.find('div', 'label S_txt2').text
                key_ = self.trim_rtb(key_)
                if not key_:
                    return
                con = pf_item.find('div', 'con')

                if not len(list(con.stripped_strings)):
                    continue

                txt = list(con.stripped_strings)[0]
                if con.find('a'):
                    txt = txt.replace(con.a.text, '')
                txt = self.trim_rtb(txt)
                print('EDU: {} ==> {}'.format(key_, txt))

        def get_tags():
            if len(account_items) < 5:
                return
            for pf_item in account_items[4].find_all('div', 'pf_item clearfix'):
                parent = pf_item.parent
                if parent.get('style') and parent.get('style').find('display:none') != -1:
                    continue

                key_ = pf_item.find('div', 'label S_txt2').text
                key_ = self.trim_rtb(key_)
                if not key_:
                    return

                con = pf_item.find('div', 'con')

                if not len(list(con.stripped_strings)):
                    continue

                tags_ = []
                for a in con.find_all('a'):
                    tags_.append(a.text)
                txt = self.trim_rtb(','.join(tags_))
                txt = helper.multi_replace(txt, '马上填写')
                key_ = self.get_en_key(key_)
                # print('CONN: {} ==> {}'.format(key_, txt))
                self.personal_info['info'][key_] = txt
                # print('TAGS: {} ==> {}'.format(key_, txt))
                # self.user_info['info'][self.get_en_key(key_)] = txt

        get_base_view()
        get_connection()
        # get_job()
        # get_edu()
        get_tags()

    def get_followed(self):
        """
            用户的关注列表

        :return:
        :rtype:
        """
        if self.is_me:
            self.get_my_followed()
        else:
            self.get_personal_followed()

    def get_my_followed(self):
        params = {
            't': 1,
            'cfs': ''
        }
        _from_id = self.my_info['domain'] + self.my_info['uid']
        follow_url = M['get_my_follow']
        url = follow_url.format(_from_id)
        follow_id = 'Pl_Official_RelationMyfollow__'

        if self.followed_dom_id:
            params['{}_page'.format(self.followed_dom_id)] = self.page_index['follow']

        self.follow_page_dict = self.load_markup(url, params=params)
        user_raw = self.get_markup_by_el_id(self.follow_page_dict, follow_id)
        self.followed_dom_id = self.get_markup_by_el_id(self.follow_page_dict, follow_id, which_key='domid')
        user_raw = self.bs4markup(user_raw)

        def my_followed():
            """
            <img alt="主播佳期" class="W_face_radius" height="50"
            src="//tva4.sinaimg.cn/crop.3.0.506.506.50/9549f643jw8f9dvpn6kn3j20e80e2gm7.jpg"
            title="主播佳期" usercard="id=2504652355" width="50"/>

            action-data="uid=1915268965
            &profile_image_url=http://tvax1.sinaimg.cn/crop.0.0.1242.1242.50/7228af65ly8fmc4jx2rwij20yi0yi419.jpg
            &gid=0&gname=未分组&screen_name=霹雳无敌李三娘&sex=f"
            """
            member_box = user_raw.find('div', 'member_box')
            members_raw = member_box.find_all('li', 'member_li S_bg1')
            members_ = []

            for li in members_raw:
                followed = self.action_to_dict(li.get('action-data'))
                img_src = self.use_big_head(followed.get('profile_image_url'))
                followed_from = li.find('div', 'info_from S_txt2').a.text
                approve = li.find('i', 'W_icon')
                grouped = li.find('div', 'opt').find('span', 'txt W_autocut').text
                brief = li.find('div', 'text W_autocut S_txt2').text
                if approve:
                    approve = approve.get('title')
                else:
                    approve = ''

                d = {
                    'person_pic': img_src,
                    'name': followed.get('screen_name', ''),
                    'uid': followed.get('uid', ''),
                    'sex': followed.get('sex'),
                    'followed_from': self.trim_rtb(followed_from),
                    'approve': helper.multi_replace(approve, '微博|认证'),
                    'grouped': grouped,
                    'brief': brief,
                }
                d = {
                    k: self.trim_rtb(v)
                    for k, v in d.items()
                }
                members_.append(d)
            return members_

        self.followed = my_followed()

    def web_publish(self, content=''):
        """
            step1: get https://weibo.com/p/aj/v6/publish?ajwvr=6&forpub2000=1&_t=0&__rnd=1514191263435
            step2:
        :param content:
        :type content:
        :return:
        :rtype:
        """
        url = M['pub_one']
        params = {
            'domain': self.my_info.get('domain'),
            'ajwvr': 6,
        }
        # print(content)
        dat_form = {
            'location': 'page_{}_home'.format(self.my_info.get('domain')),
            'text': content,
            'style_type': 3,
            'pdetail': '{}{}'.format(self.my_info.get('domain'), self.my_info.get('uid')),
            '_t': 7,
        }
        res = self.sess.post(url, params=params, data=dat_form, headers=self.json_headers)
        print(res.url)
        print(res.json())

    def publish(self, feed=''):
        print(feed)

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
            'nick': '@弱弱弱一生',
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

        if not self.confirm_do('上传图片'):
            return

        data = {
            'b64_data': base64.b64encode(helper.read_file(pic_pth))
        }

        raw = self.sess.post(pic_url, params=params, data=data, allow_redirects=False, headers=self.pic_headers)

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
        self.mobile_pub(data)

    def publish_text(self):
        data = {
            'content': '',
        }
        cnt = base.multi_line_input('说点什么')
        data['content'] = cnt
        self.mobile_pub(data)

    def mobile_pub(self, dat):
        if not isinstance(dat, dict):
            dat = {'content': dat}
        url = 'https://m.weibo.cn/api/statuses/update'
        data = {
            'st': self.mobile_config.get('st'),
        }
        data = dict(data, **dat)
        self.mobile_crud('发布微博', url, data)

    def publish_video(self):
        """
           暂时支持
        :return:
        :rtype:
        """
        cnt = ''
        cnt += base.multi_line_input('说点什么')
        cnt += base.multi_line_input('粘贴链接')
        self.mobile_pub(cnt)

    def web_delete(self, feed):
        dat = feed.info
        _ = '{}({})\n{}'.format(dat['mid'], dat['time'], dat['content'])
        # print('delete {}'.format(feed.info['mid']))
        url = 'https://weibo.com/aj/mblog/del'
        data = {
            'mid': feed.info['mid']
        }
        res = self.sess.post(url, params={'ajwvr': 6}, data=data, headers=self.json_headers)
        res = res.json()
        if res.get('code') == '10000':
            log.info('[SUCCESS]delete {}'.format(_))
        else:
            log.error('[FAILED] {}:{}'.format(res.get('code'), res.get('msg')))

    def confirm_do(self, oper):
        c = helper.yn_choice(
            '是否[{}]'.format(oper)
        )
        if not c:
            log.warn('放弃 ({}) 操作.'.format(oper))
            return False
        return True

    def mobile_crud(self, oper, url, form):
        c = helper.yn_choice(
            '是否[{}]'.format(oper)
        )
        if not c:
            log.warn('放弃 ({}) 操作.'.format(oper))
            return

        res = self.mobile_sess.post(url, data=form, headers=self.mobile_json_headers)
        dat = res.json()
        if dat['ok'] == 1:
            log.debug('[{}]成功!!!'.format(oper))
        else:
            log.error('错误: {}'.format(dat))

    def delete(self, feed):
        url = 'https://m.weibo.cn/mblogDeal/delMyMblog'
        form = {
            'id': feed.get('mid'),
            'st': self.mobile_config.get('st')
        }
        self.mobile_crud('删除微博', url, form)

    def topit(self, mid=''):
        print('topit {}'.format(mid))

    def add_tag(self, mid=''):
        print('add_tag {}'.format(mid))

    def view_by_friends(self, mid=''):
        print('view_by_friends {}'.format(mid))

    def only_me(self, mid=''):
        print('only_me {}'.format(mid))

    def more(self, feed):
        # pprint(feed['text'])
        print(helper.multi_replace(feed['text'], '<br/>,\n'))

    def favor(self, feed=None):
        url = 'https://m.weibo.cn/mblogDeal/'
        form = {
            'st': self.mobile_config.get('st'),
            'id': feed.get('mid'),
        }
        if feed.get('favorited'):
            oper = '取消收藏'
            url += 'delFavMblog'
        else:
            oper = '收藏'
            url += 'addFavMblog'
        self.mobile_crud(oper, url, form)

    def like(self, feed=None):
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
        url = 'https://m.weibo.cn/api/attitudes/'
        form = {
            'id': feed.get('mid'),
            'st': self.mobile_config.get('st'),
            'attitude': 'heart',
        }

        if feed.get('liked'):
            oper = '取消点赞'
            url += 'destroy'
        else:
            oper = '点赞'
            url += 'create'

        self.mobile_crud(oper, url, form)

    def comment(self, feed=None):
        url = 'https://m.weibo.cn/api/comments/create'
        form = {
            'id': feed.get('mid'),
            'mid': feed.get('mid'),
            'st': self.mobile_config.get('st'),
            'content': ''
        }
        comments = base.multi_line_input('输入评论')
        if not comments:
            log.error('comment is must')
            return

        form['content'] = comments
        res = self.mobile_sess.post(url, form, headers=self.mobile_json_headers)
        dat = res.json()
        if dat['ok'] == 1:
            log.debug('[{}]成功!!!'.format('评论'))
        else:
            log.error('错误: {}'.format(dat))

    def forward(self, feed=None):
        url = 'https://weibo.com/aj/v6/mblog/forward'
        params = {
            'domain': self.my_info.get('domain'),
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

        res = self.sess.post(url, params=params, data=data, headers=self.json_headers)
        dat = res.json()
        if dat.get('code') == '100000':
            log.debug('[{}]成功!!!'.format('转发成功'))
        else:
            log.error('错误: {}'.format(dat))


class Action(WeiboBase):
    __metaclass__ = dec.Singleton

    def __init__(self, user):
        WeiboBase.__init__(self)
        self.wb_user = user
        self.choice_list = []
        self.act = {}
        self.selected_feed = None
        self.menus = user.menus
        if not self.choice_list:
            self.add_to_choices()

        self.wb_user.page_index['follow'] = 1

    def filter_menu(self, menu_in):
        if not self.selected_feed:
            return menu_in

        dat = self.selected_feed

        has_video = False
        if dat.get('page_info', {}) and dat['page_info'].get('type') == 'video':
            has_video = True

        if not has_video:
            menu_in = [
                x for x in menu_in
                if x['_do'] != 'video'
            ]
        return menu_in

    def add_to_choices(self, menu_key='root', default=0):
        menu = self.menus.get(menu_key)
        menu = self.filter_menu(menu)
        _handler = self.root_action

        if hasattr(self, '{}_action'.format(menu_key)):
            _handler = getattr(self, '{}_action'.format(menu_key))

        operation = {
            'orig_dat': menu,
            'cb': _handler,
            'default': default or len(menu)
        }
        self.choice_list.append(operation)
        self.run()

    def run(self):
        log.debug('is me: {}'.format(self.wb_user.is_me))
        while len(self.choice_list):
            _menu = self.choice_list[-1]
            c = self.wb_user.wbui(
                **_menu
            )
            if str(c) in 'bB':
                return c

    @dec.catch(enable_catch, AttributeError)
    def root_action(self, act):
        self.act = act
        print('{} {} {}({})'.format('►' * 3, act.get('_txt'), act.get('_do'), self.wb_user.user_uid))
        resp = getattr(self.wb_user, act.get('_do'))()

        if hasattr(self, '{}_handler'.format(act.get('_do'))):
            getattr(self, '{}_handler'.format(act.get('_do')))(resp)
        else:
            self.echo_handler(act)

    def feed_action(self, act):
        print('{} {} {}({})'.format('►' * 3, act.get('_txt'), act.get('_do'), self.wb_user.user_uid))
        resp = getattr(self.wb_user, act.get('_do'))(self.selected_feed)

        if hasattr(self, 'feed_{}_handler'.format(act.get('_do'))):
            getattr(self, 'feed_{}_handler'.format(act.get('_do')))(resp)
        else:
            self.echo_handler(act)

    def echo_handler(self, act):
        # print('echo_handler of >>> ', act)
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

    def get_followed_handler(self, dat):
        self.wb_user.page_index['follow'] += 1
        self.echo_handler(self.act)

    def get_feed_handler(self, dat):
        def gen_str(dat):
            txt = ['{} (转发:{}, 评论:{}, 点赞:{})'.format(
                dat.get('created_at'),
                dat.get('reposts_count'),
                dat.get('comments_count'),
                dat.get('attitudes_count'),
            )]
            if len(dat.get('pics', [])):
                txt.append('[{}图]'.format(len(dat.get('pics'))))

            if dat.get('page_info', {}) and dat['page_info'].get('type') == 'video':
                txt.append('[1个视频]')
            txt = ', '.join(txt)
            txt += '\n{} ...\n'.format(dat.get('text')[:80])
            return txt

        feeds = self.wb_user.feeds[-1]
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
                default=1
            )
            if str(c) in 'bB':
                return

            self.selected_feed = self.wb_user.feeds[-1][c]
            self.add_to_choices('feed', 1)

    def publish_handler(self, dat):
        self.add_to_choices('publish', 1)

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
        txt = '转发:{}, 评论:{}, 点赞:{}\n{}\n'.format(
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

        if not isinstance(pics, list):
            pics = [pics]

        for pic in pics:
            self.cat_net_img(pic)

    def feed_large_handler(self, act):
        dat = self.selected_feed

        pics = [
            x['url']
            for x in dat.get('pics', [])
        ]
        if not pics and dat.get('page_info'):
            pics = dat['page_info'].get('page_pic', {}).get('url')

        if not isinstance(pics, list):
            pics = [pics]

        for pic in pics:
            self.cat_net_img(pic, large=True, height=base.get_height())

    def feed_video_handler(self, act):
        dat = self.selected_feed
        url = dat.get('HDVideo')
        if not url:
            url = dat.get('page_info', {}).get('media_info', {}).get('stream_url', '')

        if url:
            url = url.replace('https', 'http')
            Player(url)
        else:
            log.error('No Video info found!!!')


if __name__ == '__main__':
    a = '现\t\t\r\n在'
    rs = base.multi_line_input()
    print(rs)
