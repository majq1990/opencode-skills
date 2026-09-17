# -*- coding: utf-8  -*-

"""

@Time : 2024/8/17 10:50
@Auth : tanchengbing
@File : getConfig.py
"""

import configparser
import os
from dbutils.logger_utils import logger

# 获取当前文件的绝对路径
current_file_path = os.path.abspath(__file__)
# 获取当前文件所在目录
current_dir = os.path.dirname(current_file_path)
# 构建配置文件的绝对路径
configPath = os.path.join(current_dir, 'db_config.ini')
config = configparser.ConfigParser()
config.read(configPath, 'utf-8')


def getConfig(section='DEFAULT', option=None):
    '''
    获取db_config.ini中的参数值
    :param section: 默认config，为配置文件中[]内名称
    :param option: 参数名
    :return: 指定参数名的参数值，无数据返回None
    '''
    try:
        if not config.has_section(section):
            logger.warning(f"Section '{section}' does not exist in the config file.")
            return None
        if not option:
            return config.options(section)
        else:
            if not config.has_option(section, option):
                logger.warning(f"Option '{option}' does not exist in section '{section}'.")
                return None
            return config.get(section, option)
    except Exception as e:
        logger.exception(f"Error retrieving config: {e}")
        return None


def modifyConfig(section, args):
    '''
    修改数据源
    :param section: 字符串形式，数据源名称
    :param args: 字典格式，形如：{'PORT':'3306', 'USER':'root', 'dbType':'mysql'}
    :return: 修改成功返回0，失败返回1
    '''
    if config.has_section(section):
        logger.info(f"修改数据源{section}: {args}")
        for key in args:
            value = args.get(key)
            if config.has_option('DEFAULT', key):
                config.set(section, key, value)
                config.write(open(configPath, "w", encoding="utf-8"))
        logger.info("修改成功！")
        return 0
    else:
        logger.warning("数据源不存在，请检查输入！")
        return 1


def setConfig(section, args):
    '''
    设置数据源
    :param section:字符串形式，数据源名称
    :param args:字典格式，形如：{'PORT':'3306', 'USER':'root', 'dbType':'mysql'}
    :return:新增成功返回0，失败返回1
    '''

    if config.has_section(section):
        logger.warning("当前数据源名称已存在，请重新命名！")
        return 1
    else:
        logger.info(f"新增数据源{section}: {args}")
        config.add_section(section)
        for key in args:
            value = args.get(key)
            config.set(section, key, value)
            config.write(open(configPath, "w", encoding="utf-8"))
        logger.info("新增成功！")
        return 0


def getAllConfig():
    '''
    获取所有数据源名称+对应ip+数据库名称
    :return:
    '''
    sections = config.sections()
    dbdatas = []

    for sec in sections:
        dbdatas.append("{}, {}, {}".format(config[sec]['host'], config[sec]['dbname'], config[sec]['dbType']))

    return dict(zip(sections, dbdatas))


DMDRIVER = getConfig(section='dm', option='dmdriver')
DMDRIVERPATH = getConfig(section='dm', option='dmdriverpath')
if DMDRIVER is None:
    logger.error("DMDRIVER 配置不正确. 请检查db_config.ini配置文件.")
if DMDRIVERPATH is None:
    logger.error("DMDRIVERPATH 配置不正确. 请检查db_config.ini配置文件.")
DMDRIVERPATH = os.path.join(os.path.dirname(configPath), DMDRIVERPATH)

if __name__ == '__main__':
    modifyConfig("dm", {'PORT': '5501', 'USER': 'DLMIS', 'HOST': '10.255.18.12', 'dbType': 'dm', 'pwd': 'sHzZht@2023!',
                        'dbname': 'cgdb'})
    # getAllConfig()
