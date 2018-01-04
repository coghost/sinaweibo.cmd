# -*- coding: utf-8 -*-
from __future__ import print_function

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

app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(app_root)
if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

import logzero
from logzero import logger as log

from bs4 import BeautifulSoup
from izen import helper
from clint import textui
from config import Conf, LFormatter

base_pth = os.path.join(os.path.expanduser('~'), '.weibocli')
app_pth = {
    'cfg': os.path.join(base_pth, 'config/weibo.cfg'),
    'log': os.path.join(base_pth, 'logs/weibo.log'),
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
click_hint = '{}\ne.g.: <cmd> {}'

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


def force_quit():
    """
        call os._exit(-1) to force quit program.

    :return:
    :rtype:
    """
    os._exit(-1)


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
