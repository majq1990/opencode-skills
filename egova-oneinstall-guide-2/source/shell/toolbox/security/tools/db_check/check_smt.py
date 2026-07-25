from database_utils import Database
from dbutils.logger_utils import logger
import sys

db_type = sys.argv[1]

# 预期的更新值
updates = {
    "PUB_MIS_LOGIN_FUZZY_SEARCH": "0",
    "PUB_LOGIN_VALID_WAY": "1",
    "PUB_LOGIN_VALID_TIME_SEGMENT": "5",
    "PUB_LOGIN_VALID_ERROR_NUM": "5",
    "PUB_LOGIN_LOCK_TIME": "5",
    "PUB_USER_VALIDATE_PASSWORD": "1",
    "PUB_PASSWORD_CHECK_REGEXP": "[a-z],[A-Z],[0-9],[$@$!%*#?&]",
    "PUB_LOGIN_PASS_MINCHAR": "6",
    "PUB_LOGIN_PASS_MAXCHAR": "9",
    "PUB_LOGIN_ENABLE_CHANGE_PASSWORD_NOTICE_DIALOG": "1",
    "PUB_CHANGE_PASSWORD_NOTICE_CONTENT": "温馨提示：为了您的账号安全，请及时修改密码。",
    "PUB_ENABLE_FORCE_CHANGE_PASSWORD": "1",
    "PUB_FORCE_CHANGE_PASSWORD_NOTICE_CONTENT": "请按照密码规则修改密码!",
    "PUB_LOGIN_PASSWORD_ALLOW_EMPTY": "0",
    "PUB_SYS_CONFIG_USER_INFO_MASK": "1",
    "PUB_REPORT_USER_NAME_MASK": "1",
    "PUB_SYS_CONFIG_IDCARDNUM_MASK": "1",
    "UPLOAD_FILE_TYPE_WHITELIST": "jpg,jpeg,png,gif,tif,bmp,dwg,html,rtf,xml,zip,xls,xlsx,doc,docx,csv,zip,rar,txt,pdf,mp3,mp4,wav,avi,amr,rm,mpg,mov,sql,proxy,json,wma,3gp,asf,wmv,thumb",
    "DOWNLOAD_FILE_TYPE_WHITELIST": "jpg,jpeg,png,gif,tif,bmp,dwg,html,rtf,xml,zip,xls,xlsx,doc,docx,csv,zip,rar,txt,pdf,mp3,mp4,wav,avi,amr,rm,mpg,mov,sql,proxy,json,wma,3gp,asf,wmv,thumb"
}


def fetch_and_compare(db, sql, expected_value, config_name=None):
    try:
        results = db.execute_query(sql)
        if results is not None:
            current_value = str(results[0][0])
            if current_value is None:
                logger.info(f"配置项 {config_name} 不存在。")
            if current_value != expected_value and config_name is not None:
                update_sql = "UPDATE tc_pub_city_sys_config SET config_value='{}' WHERE Config_Name='{}'".format(expected_value, config_name)
                db.execute_sql_by_type(update_sql, operation_type="update")
                logger.info(f"更新 {config_name}: {current_value} -> {expected_value}")
        else:
            if config_name:
                logger.info(f"未能获取配置项 {config_name} 的值")
            else:
                logger.info("未能获取值")
    except Exception as e:
        if config_name:
            logger.info(f"处理配置项 {config_name} 时发生错误: {e}")
        else:
            logger.info(f"查询时发生错误: {e}")


def check_update(config_name, expected_value):
    db = Database(db_type)
    sql = "SELECT config_value FROM tc_pub_city_sys_config WHERE Config_Name = '{}'".format(config_name)
    fetch_and_compare(db, sql, expected_value, config_name)


# 检查 tc_sys_config_item 表中的记录
for config_name, expected_value in updates.items():
    check_update(config_name, expected_value)
