# -*- coding: utf-8  -*-

"""

@Time : 2023/9/28 17:01
@Auth : luoyiting
@File : logger_utils.py
@From : https://github.com/Delgan/loguru#readme
"""

import time
from loguru import logger as ulog

# 定义日志路径，每天0点自动生成，仅保留7天的日志
LOG_DIR = "logs/"
ROTATION = "00:00"
RETENTION = "7 days"

log_time = time.strftime("%Y_%m_%d", time.localtime())


class MyLog():
    def __init__(self):
        self.log = ulog
        self.log.add(LOG_DIR+"info_"+log_time+".log",
                     rotation=ROTATION,
                     retention=RETENTION,
                     level="INFO")
        self.log.add(LOG_DIR+"error_"+log_time+".log",
                     rotation=ROTATION,
                     retention=RETENTION,
                     level="ERROR")


logger = MyLog().log


if __name__ == '__main__':
    logger.info("正确测试！")
    logger.error("错误测试！")
    logger.warning("异常测试！")
