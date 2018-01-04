#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'lihe <imanux@sina.com>'
__date__ = '21/12/2017 3:08 PM'
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

import logzero
from logzero import logger as log

import click
from izen import helper

from base import click_hint, cfg
import base
from weibo import weibo_api


@click.command()
@click.option('--big_head', '-big',
              is_flag=True,
              help=click_hint.format('显示原始大图', ' -big'))
@click.option('--img_cache_dir', '-cache',
              help=click_hint.format('终端显示照片缓存目录', '-cache <dir>'))
@click.option('--img_height', '-h',
              type=int,
              help=click_hint.format('iterm2 终端显示照片占用的行数', '-h <num>'))
@click.option('--init_photos', '-i',
              is_flag=True,
              help=click_hint.format('初始化账号专辑照片信息, 否则只更新', ' -i'))
@click.option('--login', '-lg',
              is_flag=True,
              help=click_hint.format('手动登陆', ' -lg'))
@click.option('--mlogin', '-mlg',
              is_flag=True,
              help=click_hint.format('手机端登陆', ' -mlg'))
@click.option('--log_level', '-log',
              type=int,
              help=click_hint.format(
                  '终端显示log级别 1-debug/2-info/3-warn/4-error', '-log <num>'))
@click.option('--skip_cache', '-sc',
              is_flag=True,
              help=click_hint.format('不使用照片缓存', ' -sc'))
@click.option('--name', '-n',
              help=click_hint.format('从本地mongo查询', '-n <name>'))
@click.option('--search', '-s',
              help=click_hint.format('从新浪直接查询', '-s <name>'))
@click.option('--test', '-t',
              is_flag=True,
              help=click_hint.format('测试cookie是否可用', ' -t'))
@click.option('--uid', '-id',
              help=click_hint.format('依据uid获取账号信息', '-id <uid>'))
@click.option('--update_personal_info', '-update',
              is_flag=True,
              help=click_hint.format('更新个人信息', ' -update'))
def run(big_head,
        img_cache_dir, img_height, init_photos, login, log_level, mlogin, name,
        search, skip_cache, test,
        uid, update_personal_info, ):
    img_height = img_height or cfg.get('weibo.img_height', 3)
    log_level = log_level or cfg.get('weibo.log_level', 1)
    img_cache_dir = img_cache_dir or cfg.get('weibo.img_cache_dir', '/tmp/weibo')

    big_head = big_head or cfg.get('weibo.big_head', False)
    skip_cache = skip_cache or cfg.get('weibo.skip_cache', False)

    logzero.loglevel(log_level * 10)

    weibo_api.WeiboBase(big_head=big_head,
                        img_cache_dir=img_cache_dir,
                        img_height=img_height,
                        use_cache=not skip_cache)

    myself = weibo_api.Myself(
        login_ok=not login and not mlogin,
        uid_in=uid,
    )

    if mlogin:
        myself.mobile_login()
        base.force_quit()

    if login:
        try:
            myself.login()
        except IndexError as _:
            lg = weibo_api.Login()
            lg.do_login()
            print(_)
        base.force_quit()

    if test:
        myself.is_mobile_login_ok()
        myself.is_cookie_ok()
        base.force_quit()

    if not myself.sess.cookies:
        log.warn('no cookie found!, login `-lg` first!!!')
        base.force_quit()

    if not myself.mobile_sess.cookies:
        log.warn('no mobile cookie found!, login `-mlg` first!!!')
        base.force_quit()

    myself.run()


if __name__ == '__main__':
    run()
