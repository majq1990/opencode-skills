from database_utils import Database
from dbutils.logger_utils import logger
import sys

db_type = sys.argv[1]

# 预期的更新值
updates = {
    "egova.wukong.force.change.P": "true",
    "encode": "sm4",
    "encodeWhiteList": "/wfs",
    "egova.security.password.enable": "true",
    "login": "true",
    "egova.security.password.passwordExpireDays": "180",
    "egova.security.password.strong": "EASY",
    "egova.security.passwordEncryptType": "sm2",
    "egova.security.failure.enable": "true",
    "egova.security.failure.account-lock-minutes": "10",
    "egova.security.failure.max-retry-times": "5",
    "egova.wukong.interceptor.freeInterfaceVerifyUrl": "/free/page,/free/project/,/free/card-data/,/free/layer-menu,/free/interaction,/free/image/upload",
    "egova.wukong.interceptor.imageAllowType": "png,svg,jpg,otf,ttf,gif,jpeg,webm,woff",
    "egova.wukong.interceptor.imageDisabledType": "html,htm,shtml,shtm,shtml",
    "egova.xss.enabled": "true",
    "egova.xss.excludes": "",
    "egova.xss.urlPatterns": "/*"
}


def fetch_and_compare(db, sql, expected_value, config_item_name=None):
    try:
        results = db.execute_query(sql)
        if results is not None:
            current_value = str(results[0][0])
            if current_value is None:
                logger.info(f"配置项 {config_item_name} 不存在。")
            if current_value != expected_value and config_item_name is not None:
                update_sql = "UPDATE tc_sys_config_item SET item_value='{}' WHERE config_item_name='{}'".format(expected_value, config_item_name)
                db.execute_sql_by_type(update_sql, operation_type="update")
                logger.info(f"更新 {config_item_name}: {current_value} -> {expected_value}")
        else:
            if config_item_name:
                logger.info(f"未能获取配置项 {config_item_name} 的值")
            else:
                logger.info("未能获取值")
    except Exception as e:
        if config_item_name:
            logger.info(f"处理配置项 {config_item_name} 时发生错误: {e}")
        else:
            logger.info(f"查询时发生错误: {e}")


def check_update(config_item_name, expected_value):
    db = Database(db_type)
    sql = "SELECT item_value FROM tc_sys_config_item WHERE config_item_name = '{}'".format(config_item_name)
    fetch_and_compare(db, sql, expected_value, config_item_name)


# 检查 tc_sys_config_item 表中的记录
for config_item_name, expected_value in updates.items():
    check_update(config_item_name, expected_value)
