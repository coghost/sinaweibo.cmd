import os
import sys
import logging

app_root = '/'.join(os.path.abspath(__file__).split('/')[:-2])
sys.path.append(app_root)

import logzero
import profig


class Conf(object):
    """运行所需要的配置文件
    """

    def __init__(self, pth=None):
        self.pth = pth if pth else os.path.join(app_root, 'config/.weibo.cnf')
        self.cfg = profig.Config(self.pth, encoding='utf-8')
        self.cfg.read()
        self.init_type()
        if not os.path.exists(os.path.expanduser(self.pth)):
            self.cfg.sync()
            raise SystemExit('config file path not exists: {}'.format(os.path.expanduser(self.pth)))

    def init_type(self):
        """通过手动方式, 指定类型, 如果配置文件有变动, 需要手动在这里添加"""
        _cfg = self.cfg
        _cfg.init('sys.catch_error', False, bool)  # 是否捕获错误
        _cfg.init('sys.abc', [], list)

        _cfg.init('log.enabled', False, bool)  # 是否记录到文件
        _cfg.init('log.file_pth', '/tmp/crawl.log', str)
        _cfg.init('log.file_backups', 3, int)
        _cfg.init('log.file_size', 5, int)  # M
        _cfg.init('log.level', 10, int)  # d/i/w/e/c 10/20/30/40/50
        _cfg.init('log.symbol', '☰☷☳☴☵☲☶☱', str)  # 使用前5个字符

        _cfg.init('mg.host', '127.0.0.1', str)
        _cfg.init('mg.port', 27027, int)
        _cfg.init('mg.db', 'luoo', str)
        _cfg.init('mg.username', '', str)
        _cfg.init('mg.password', '', str)

        _cfg.init('rds.host', '127.0.0.1', str)
        _cfg.init('rds.port', 6380, int)
        _cfg.init('rds.socket_timeout', 2, int)
        _cfg.init('rds.socket_connect_timeout', 2, int)
        _cfg.init('rds.password', '123456', str)
        _cfg.init('rds.db', 0, int)

        _cfg.init('weibo.username', '', str)
        _cfg.init('weibo.password', '', str)
        _cfg.init('weibo.nickname', '', str)
        _cfg.init('weibo.uid', '6069778559', str)
        _cfg.init('weibo.domain', '100505', str)
        _cfg.init('weibo.big_head', False, bool)
        _cfg.init('weibo.img_height', 6, int)
        _cfg.init('weibo.log_level', 2, int)
        _cfg.init('weibo.img_cache_dir', '/tmp/weibo', str)
        _cfg.init('weibo.album_page_count', 20, int)
        _cfg.init('weibo.photo_page_count', 32, int)
        _cfg.init('weibo.app_key', '', str)
        _cfg.init('weibo.app_secret', '', str)

        _cfg.sync()


class LFormatter(logzero.LogFormatter):
    """ 改写 logzero 的 LogFormatter
    - 移除 ``[]``, 支持自定义前导字符(任意长度, 但只取前5个字符),
    - 增加 ``critical`` 的颜色实现
    """
    DEFAULT_FORMAT = '%(color)s {}%(levelname)1.1s %(asctime)s ' \
                     '%(module)s:%(lineno)d {}%(end_color)s %(' \
                     'message)s'
    DEFAULT_DATE_FORMAT = '%y%m%d %H:%M:%S'
    DEFAULT_COLORS = {
        logging.DEBUG: logzero.ForegroundColors.CYAN,
        logging.INFO: logzero.ForegroundColors.GREEN,
        logging.WARNING: logzero.ForegroundColors.YELLOW,
        logging.ERROR: logzero.ForegroundColors.RED,
        logging.CRITICAL: logzero.ForegroundColors.MAGENTA,
    }

    def __init__(self, log_pre='♨✔⊙✘◈'):
        logzero.LogFormatter.__init__(self,
                                      datefmt=self.DEFAULT_DATE_FORMAT,
                                      colors=self.DEFAULT_COLORS
                                      )
        blank__ = '➵' * 5
        log_pre += blank__[len(log_pre):]  # 如果无, 或者长度小于5, 则使用 blank_ 自动补全5个字符
        self.CHAR_PRE = dict(zip(range(5), log_pre))

    def format(self, record):
        _char_pre = self.CHAR_PRE[record.levelno / 10 - 1] + ' '
        __fmt = self.DEFAULT_FORMAT
        __fmt = __fmt.format(_char_pre, '|')
        self._fmt = __fmt
        return logzero.LogFormatter.format(self, record)
