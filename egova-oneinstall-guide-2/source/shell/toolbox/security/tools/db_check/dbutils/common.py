# -*- coding: utf-8  -*-

"""

@Time : 2023/9/11 15:46
@Auth : luoyiting
@File : common.py
@From : xxx
"""
import decimal
import json
from datetime import datetime, date


class DateEncoder(json.JSONEncoder):
    '''
    json模块中的dumps方法无法对字典中datetime时间格式的数据进行转化，需进行处理
    https://www.jianshu.com/p/6450be37662b
    '''
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, bytes):
            return str(obj, encoding='utf-8')
        elif isinstance(obj, int):
            return int(obj)
        elif isinstance(obj, float):
            return float(obj)
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def authCookie(uid):
    '''
    权限验证
    :param uid: 请求头的密钥
    :return:
    '''
    cookie = 'guHIhFE9R2KLjaE096lC1pkrWKGpP5J5rxYsPJNqsn0N8vIvItVWL153KknyDns0'
    if uid != cookie:
        return {'msg': '权限不够！请联系管理员！', 'success': 'false'}
    else:
        return 1

def checkNotNone(field, value):
    '''
    检查字段是否为None，None则返回错误信息
    :param field: 字段名
    :param value: 字段值
    :return: 字段值为空则返回错误信息，不为空则返回1
    '''
    if value==None:
        return {'msg': '字段{}为必填项，请填写！'.format(field), 'success': 'false'}
    else:
        return 1

def checkRequired(args):
    '''
    检查必填项是否必填
    :param args: 字典形式 {字段名：字段值}
    :return: 某一字段值为空则返回错误信息，均不为空则返回1
    '''
    for key, value in args.items():
        if value == None:
            return {'msg': '字段{}为必填项，请填写！'.format(key), 'success': 'false'}
    return 1

def trans2jsonstr(ren):
    return json.dumps(ren, ensure_ascii=False, cls=DateEncoder)

def sqlChange(sql):
    '''
    对于传入的sql实际为多条，有;间隔的情况
    :param sql:
    :return: list或原始sql语句
    '''
    # 去除字符串两端的空格和结尾的分号
    sql = sql.strip()
    sql = sql.rstrip(';')

    if ';' in sql:
        return sql.split(';')

    return sql