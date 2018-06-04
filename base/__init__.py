# -*- coding: utf-8 -*-
__author__ = 'lihe <imanux@sina.com>'
__date__ = '26/10/2017 9:56 AM'
__description__ = '''
    ☰
  ☱   ☴
☲   ☯   ☵
  ☳   ☶
    ☷
'''

import os
import sys
from functools import wraps
import random
import base64
from pprint import pprint
from urllib.parse import urljoin, urlencode, quote, unquote_plus, parse_qsl

app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(app_root)
if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

import logzero
from logzero import logger as log

from bs4 import BeautifulSoup
from izen import helper, dec
from clint import textui
from config import Conf, LFormatter

base_pth = os.path.join(os.path.expanduser('~'), '.weibocli')
app_pth = {
    'cfg': os.path.join(base_pth, 'config/weibo.cfg'),
    'log': os.path.join(base_pth, 'logs/weibo.log'),
    'personal': os.path.join(base_pth, 'dat/personal.txt'),
    'cookie': os.path.join(base_pth, 'dat/cookie.txt'),
    'mobile_cookie': os.path.join(base_pth, 'dat/mobile_cookie.txt'),
}

cfg = Conf(app_pth.get('cfg')).cfg

# 检查日志配置, 是否写入文件
if cfg.get('log.enabled', False):
    logzero.logfile(
        cfg.get('log.file_pth', app_pth.get('log')),
        maxBytes=cfg.get('log.file_size', 5) * 1000000,
        backupCount=cfg.get('log.file_backups', 3),
        loglevel=cfg.get('log.level', 10),
    )

# bagua = '☼✔❄✖✄'
# bagua = '☰☷☳☴☵☲☶☱'  # 乾(天), 坤(地), 震(雷), 巽(xun, 风), 坎(水), 离(火), 艮(山), 兑(泽)
bagua = '🍺🍻♨️️😈☠'
formatter = LFormatter(bagua)
logzero.formatter(formatter)
click_hint = '{}\ne.g. <cmd> {}'

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


class Colorful(object):
    def __init__(self, indent=2, quote=' '):
        self.indent = indent
        self.quote = quote

    def p(self, color, msg):
        with textui.indent(indent=self.indent, quote=self.quote):
            textui.puts(getattr(textui.colored, color)(msg))

    def debug(self, msg):
        self.p('green', msg)

    def info(self, msg):
        self.p('cyan', msg)

    def error(self, msg):
        self.p('red', msg)


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


def pprt(show=False):
    def dec_(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            result = None
            if show:
                try:
                    result = fn(*args, **kwargs)
                except Exception as e:
                    pprint(e)
                finally:
                    _m = 64
                    _fn = fn.__code__.co_name
                    _h = (_m - len(_fn)) // 2 - 2
                    t = '-'
                    b = '-'
                    Colorful(0, ' ').debug('{} [{}({}){}] {}'.format(t * _h,
                                                                     fn.__code__.co_filename.split('/')[-1],
                                                                     fn.__code__.co_firstlineno,
                                                                     fn.__code__.co_name, t * _h))
                    pprint(result)
                    # print(b * _m)
                    return result
            else:
                return fn(*args, **kwargs)

        return wrapper

    return dec_


def update_cfg(key, val):
    cfg[key] = val
    cfg.sync()


def bs4markup(params=None):
    """
        **format the markup str to BeautifulSoup doc.**

    .. code:: python

        @bs4markup
        def fn():
            pass

    :rtype: BeautifulSoup
    :param params: ``{'parser': 'html5lib'}``
    :return:
    """
    params = params or {}

    def dec(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                rs = fn(*args, **kwargs)
                markup = BeautifulSoup(
                    rs,
                    params.get('parser', 'html5lib'),
                )
                # 如果 rs 的值与 markup.text 相同, 则判定为非 html markup 标记, 直接返回原值
                if rs == markup.text:
                    return rs
                else:
                    return markup
            except TypeError as _:
                pass

        return wrapper

    return dec


def bs4txt(markup_in, parser='lxml', enc='utf-8'):
    markup = BeautifulSoup(
        markup_in, parser
    ).text
    return markup


def save_img(dat, pth):
    if not dat:
        return
    helper.write_file(dat, pth)


def add_jpg(pathin):
    if not os.path.exists(pathin):
        log.debug('{} not exist'.format(pathin))
        return

    for root, dirs, files in os.walk(pathin):
        for f in files:
            ext = f.split('.')
            _fpth = os.path.join(root, f)
            if len(ext) != 1:
                if ext[-1] == 'jpg':
                    print('skip', _fpth)
                    continue

            os.rename(_fpth, '{}.jpg'.format(_fpth))


def randint(start=0, end=100):
    return random.randint(start, end)


def force_quit(exit_code=-1):
    """
        call os._exit(-1) to force quit program.

    :return:
    :rtype:
    """
    os._exit(exit_code)


def base62_encode(orig_num, alphabet=ALPHABET):
    """Encode a number in Base X

    `num`: The number to encode
    `alphabet`: The alphabet to use for encoding
    """
    if orig_num == 0:
        return alphabet[0]

    arr = []
    base = len(alphabet)
    while orig_num:
        rem = orig_num % base
        orig_num = orig_num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)


def base62_decode(string, alphabet=ALPHABET):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(alphabet)
    str_len = len(string)
    num_ = 0

    idx = 0
    for char in string:
        power = (str_len - (idx + 1))
        num_ += alphabet.index(char) * (base ** power)
        idx += 1

    return num_


def get_height():
    lines = os.get_terminal_size().lines
    if lines < 45:
        lines -= 4
    else:
        lines -= 8
    return lines


def multi_line_input(hint='', no_prefix=False):
    prefix = '【GEN By Python{} at {}】'.format(sys.version.split(' ')[0], helper.now())
    hint += '(use CTRL+D to end input.)'
    Colorful(2, '➜').debug(hint)
    lines = [prefix]

    if no_prefix:
        lines.pop()

    for line in sys.stdin:
        lines += line.split('\n')
    lines = '\n'.join(lines)
    return lines


def split_url_param(url=''):
    if url.find('?') == -1:
        return url, {}
    url, p_ = url.split('?')
    params = dict(parse_qsl(unquote_plus(p_)))
    return url, params


def cn_len(dat):
    d = [
        x for x in dat
        if ord(x) > 127
    ]
    return len(d)


import traceback


def catch(do, my_exception=TypeError, hints=''):
    """
    防止程序出现 exception后异常退出,
    但是这里的异常捕获机制仅仅是为了防止程序退出, 无法做相应处理
    可以支持有参数或者无参数模式

    -  ``do == True`` , 则启用捕获异常
    -  无参数也启用 try-catch

    .. code:: python

            @catch
            def fnc():
                pass

    -  在有可能出错的函数前添加, 不要在最外层添加,
    -  这个catch 会捕获从该函数开始的所有异常, 会隐藏下一级函数调用的错误.
    -  但是如果在内层的函数也有捕获方法, 则都会catch到异常.

    :param do:
    :type do:
    :param my_exception:
    :type my_exception:
    :param hints:
    :type hints:
    :return:
    :rtype:
    """
    if not hasattr(do, '__call__'):
        def dec(fn):
            @wraps(fn)
            def wrapper_(*args, **kwargs):
                if not do:
                    return fn(*args, **kwargs)

                try:
                    return fn(*args, **kwargs)
                except my_exception as e:
                    # log.error("{}({})>{}: has err({})".format(
                    #     fn.__code__.co_filename.split('/')[-1],
                    #     fn.__code__.co_firstlineno,
                    #     fn.__name__, e))
                    traceback.print_exc()
                    ty, tv, tb = sys.exc_info()
                    print(ty, tv)
                    print(''.join(traceback.format_tb(tb)))
                    # print(traceback.format_tb(tb))
                    if hints:
                        print(hints)

            return wrapper_

        return dec

    @wraps(do)
    def wrapper(*args, **kwargs):
        try:
            return do(*args, **kwargs)
        except Exception as e:
            log.error("{}({})>{}: has err({})".format(
                do.__code__.co_filename.split('/')[-1],
                do.__code__.co_firstlineno,
                do.__name__, e
            ))
            traceback.print_exc()
            if hints:
                print(hints)

    return wrapper


@catch(True, Exception)
def upc():
    update_cfg('sys.abc', [1, 2, 3])


if __name__ == '__main__':
    upc()
