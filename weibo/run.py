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
@click.option('--uid', '-id',
              help=click_hint.format('依据uid获取账号信息/无则为登陆账号信息', '-id <uid>'))
@click.option('--login', '-lg',
              is_flag=True,
              help=click_hint.format('手动输入账号密码登陆', ' -lg'))
@click.option('--auto_login', '-alg',
              is_flag=True,
              help=click_hint.format('使用配置自动登陆', ' -alg'))
@click.option('--log_level', '-log',
              type=int,
              help=click_hint.format(
                  '终端显示log级别 1-debug/2-info/3-warn/4-error', '-log <num>'))
@click.option('--test', '-t',
              is_flag=True,
              help=click_hint.format('测试cookie是否可用', ' -t'))
def run(auto_login,
        login, log_level,
        test, uid, ):
    log_level = log_level or cfg.get('weibo.log_level', 2)
    logzero.loglevel(log_level * 10)

    weibo_api.WeiboBase()

    myself = weibo_api.Myself(
        login_ok=not login and not auto_login,
        uid_in=uid,
        log_level=log_level,
    )

    if login or auto_login:
        try:
            myself.login(auto_login)
        except IndexError as _:
            lg = weibo_api.Login()
            lg.do_login()
            print(_)
        # myself.mobile_login(auto_login)
        base.force_quit(0)

    if test:
        myself.is_mobile_login_ok()
        myself.is_cookie_ok()
        base.force_quit(0)

    if not myself.sess.cookies:
        log.warn('no cookie found!, login `-lg` first!!!')
        base.force_quit()

    if not myself.mobile_sess.cookies:
        log.warn('no mobile cookie found!, login `-mlg` first!!!')
        base.force_quit()

    myself.run()


if __name__ == '__main__':
    run()
