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

'''

'''
from setuptools import setup, find_packages

setup(
    name='SinaWeiboCMDLine',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'bs4',
        'click',
        'clint',
        'colorama',
        'html5lib',
        'izen',
        'logzero',
        'lxml',
        'mongoengine',
        'profig',
        'requests',
        'rsa',
        'tqdm',
        'urwid',
    ],

    entry_points={
        'console_scripts': [
            'weibocli = weibo:start'
        ],
    },

    license='MIT',
    author='lihe',
    author_email='imanux@sina.com',
    url='https://github.com/coghost/sinaweibo.cmd',
    description='A Navy command line interface of weibo.com',
    keywords=['cli', 'weibocli', 'weibocmd', '微博', 'sina', 'weibo.com', 'item2'],
)
