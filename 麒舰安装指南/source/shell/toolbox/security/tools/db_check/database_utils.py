# -*- coding: utf-8  -*-

"""

@Time : 2024/8/26 18:41
@Auth : tanchengbing
@File : database_utils.py
@From :
"""

import pymysql
import dmPython
import psycopg2
from DBUtils.PooledDB import PooledDB
import config_utils
from config_utils import getConfig
from dbutils.logger_utils import logger


class Database:
    def __init__(self, section='DEFAULT'):
        '''
        :param section: 数据源名称
        '''
        self.dbType = getConfig(section=section, option='dbType')
        self.connection_params = self._get_connection_params(section)
        self.cgPool = self._create_pool()
        self.conn = self._get_connection()
        self.cursor = self.conn.cursor()
        self._set_schema(getConfig(section=section, option='schema'))

    def _get_connection_params(self, section):
        return {
            'host': getConfig(section=section, option='host'),
            'port': int(getConfig(section=section, option='port')),
            'user': getConfig(section=section, option='user'),
            'pwd': getConfig(section=section, option='pwd'),
            'dbname': getConfig(section=section, option='dbname'),
            'character': getConfig(option='character')
        }

    def _create_pool(self):
        params = self.connection_params
        if self.dbType == 'mysql':
            return PooledDB(
                creator=pymysql,
                maxconnections=100,
                mincached=2,
                maxcached=4,
                host=params['host'],
                port=params['port'],
                user=params['user'],
                passwd=params['pwd'],
                database=params['dbname'],
                charset=params['character']
            )
        elif self.dbType == 'dm':
            return PooledDB(
                creator=dmPython,
                maxconnections=5,
                mincached=2,
                maxcached=4,
                server=params['host'],
                port=params['port'],
                user=params['user'],
                password=params['pwd']
            )
        elif self.dbType in ('kb', 'highgo'):
            return PooledDB(
                creator=psycopg2,
                maxconnections=5,
                mincached=2,
                maxcached=4,
                host=params['host'],
                port=params['port'],
                user=params['user'],
                password=params['pwd'],
                database=params['dbname'],
            )
        else:
            logger.warning(f"未适配的数据库类型: {self.dbType}")
            return None

    def _get_connection(self):
        if self.cgPool:
            return self.cgPool.connection(shareable=False)
        logger.warning("数据库连接池未创建，无法获取连接。")
        return None

    def _set_schema(self, schema):
        if schema:
            self.cursor.execute(f"SET search_path TO '{schema}';")

    def execute_query(self, sql, params=None):
        try:
            if params:
                self.cursor.execute(sql, params or ())
            else:
                self.cursor.execute(sql)
            logger.info(f"执行查询sql语句为：{sql}")
            res = self.cursor.fetchall()
            return res
        except Exception:
            logger.exception(sql)
            return None

    def commit(self):
        self.conn.commit()

    def create_table(self, table_name, sql):
        try:
            self.cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
            self.cursor.execute(sql)
            logger.info(f"创建表SQL: {sql}")
        except Exception as e:
            logger.exception(f"创建表失败: {sql}, 错误: {e}")

    def insert(self, sql, params=None):
        return self._execute_with_commit(sql, "插入", params)

    def delete(self, sql, params=None):
        return self._execute_with_commit(sql, "删除", params)

    def update(self, sql, params=None):
        return self._execute_with_commit(sql, "更新", params)

    def _execute_with_commit(self, sql, operation_type, params=None):
        try:
            if params:
                self.cursor.execute(sql, params or ())
            else:
               self.cursor.execute(sql)
            logger.info(f"{operation_type}操作SQL: {sql}")
            self.conn.commit()
            return 0
        except Exception as e:
            self.conn.rollback()
            logger.exception(f"{operation_type}操作失败: {sql}, 错误: {e}")
            return 1

    def exit(self):
        self.cursor.close()
        self.conn.close()

    def execute_sql_by_type(self, sql, operation_type="insert", params=None):
        operations = {
            "insert": self.insert,
            "update": self.update,
            "delete": self.delete
        }

        operation = operations.get(operation_type)
        if not operation:
            return 1
        if isinstance(sql, list):
            return sum(operation(item.strip(), params) for item in sql)
        return operation(sql, params)


if __name__ == '__main__':
    db = Database("dm")
    update_sql = "UPDATE tc_sys_config_item SET item_value=? WHERE config_item_name=?"
    db.execute_sql_by_type(update_sql, operation_type="update", params=(0, "MIS_REC_ENABLE_HUMAN_CODE"))
