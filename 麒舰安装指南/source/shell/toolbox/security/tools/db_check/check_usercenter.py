from database_utils import Database
from dbutils.logger_utils import logger
import sys

db_type = sys.argv[1]

# 预期的更新值
updates = {
      "PASSWORD_COMPLEXITY": "1",
      "HUMAN_DEFAULT_PASSWORD": "eGova@2024",
      "LOGIN_FAILURE_MAX_RETRY_TIMES": "5",
      "LOGIN_FAILURE_ACCOUNT_LOCK_MINUTES": "5",
      "APP_FIRST_LOGIN_PW": "true",
      "CHECK_CRYPTOGRAM_STRENGTH": "true",
      "SECURITY_ENABLED": "true",
      "LOGIN_MULTI_IP": "true"
}

def fetch_and_compare(db, sql, expected_value, name=None):
    try:
        results = db.execute_query(sql)
        if results is not None:
            current_value = str(results[0][0])
            if current_value is None:
                logger.info(f"配置项 {name} 不存在。")
            if current_value != expected_value and name is not None:
                update_sql = "UPDATE com_option SET value='{}' WHERE name='{}'".format(expected_value, name)
                db.execute_sql_by_type(update_sql, operation_type="update")
                logger.info(f"更新 {name}: {current_value} -> {expected_value}")
        else:
            if name:
                logger.info(f"未能获取配置项 {name} 的值")
            else:
                logger.info("未能获取值")
    except Exception as e:
        if name:
            logger.info(f"处理配置项 {name} 时发生错误: {e}")
        else:
            logger.info(f"查询时发生错误: {e}")


def check_update(name, expected_value):
    db = Database(db_type)
    sql = "SELECT item_value FROM com_option WHERE name = '{}'".format(name)
    fetch_and_compare(db, sql, expected_value, name)



# 检查 com_option 表中的记录
for name, expected_value in updates.items():
    check_update(name, expected_value)
