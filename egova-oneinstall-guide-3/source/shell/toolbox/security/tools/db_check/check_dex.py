from database_utils import Database
from dbutils.logger_utils import logger
import sys

db_type = sys.argv[1]

# 预期的更新值
updates = {
    "egova.security.referer.enabled":"true",
    "egova.security.referer.referer":"允许访问的来源，逗号隔开多个，一般设置一个内网地址、一个外网地址",
    "egova.security.front-end-encrypted":"true",
    "egova.security.failure.enable":"true",
    "egova.security.failure.maxRetryTimes":"5",
    "egova.security.failure.accountLockMinutes":"10",
    "egova.security.fileupload.whitelist.enabled":"true",
    "egova.security.xss.enabled":"true",
    "egova.security.ip-firewall.enabled":"true",
    "egova.security.ip-firewall.blacklist":"$blacklist_ips",
    "egova.security.ip-firewall.whitelist":"$whitelist_ips",
    "web.commonsetting.isConversionMethod":"true",
    "web.commonsetting.isShowSignature":"true",
    "web.commonsetting.encryptType":"aes",
    "egova.request.body.decode":"aes"
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
    sql = "SELECT value FROM com_option WHERE name = '{}'".format(name)
    fetch_and_compare(db, sql, expected_value, name)


# 检查 com_option 表中的记录
for name, expected_value in updates.items():
    check_update(name, expected_value)
