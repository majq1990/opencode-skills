from database_utils import Database
from dbutils.logger_utils import logger
import sys

# db_type = sys.argv[1]
db_type = "highgo"
# 预期的更新值
updates = {
    "MIS_REC_ENABLE_HUMAN_CODE": '0',
    "COMMON_SHOW_SERVER_ERROR_DETAIL": '1',
    "MIS_LOGIN_REFRESH_SESSION": '1',
    "MIS_LOGIN_FUZZY_SEARCH": '0',
    "MIS_LOGIN_AUTO_FILL_USERNAME": '0',
    "MIS_LOGIN_VALID_WAY": '3',
    "MEDIA_INFO_SHOW_PASSWORD_FLAG": '0',
    "MIS_LOGIN_VALID_ERROR_NUM": '5',
    "MIS_LOGIN_LOCK_TIME": '5',
    "MIS_LOGIN_VALID_TIME_SEGMENT": '5',
    "MIS_LOGIN_PASS_MINCHAR": '6',
    "MIS_LOGIN_PASS_MAXCHAR": '9',
    "SYS_PASS_ENC_TYPE": '1',
    "MIS_PASSWORD_CHECK_REGEXP": '[a-z],[A-Z],[0-9],[$@$!%*#?&]',
    "MIS_BUILDER_HUMAN_DEFAULT_PASSWORD": 'Egova@2023',
    "MIS_LOGIN_ENABLE_CHANGE_PASSWORD_NOTICE_DIALOG": '1',
    "MIS_CHANGE_PASSWORD_VIEW_URL": 'view/bizbase/sysconfig/sysconfig?_$_title=系统配置',
    "MIS_CHANGE_PASSWORD_NOTICE_CONTENT": '温馨提示：为了您的账号安全，请及时修改密码。',
    "MIS_FORCE_CHANGE_PASSWORD_NOTICE_CONTENT": '请按照密码规则修改密码!',
    "MIS_ENABLE_FORCE_CHANGE_PASSWORD": '1',
    "MIS_LOGIN_REGULAR_CHANGE_PASSWORD_REMIND_CONFIG": '30',
    "GIS_SYSCONFIGITEMURL_ENCRY": '1',
    "GIS_OPEN_TOKEN": '1'
}


def fetch_and_compare(db, sql, expected_value, config_item_name=None):
    try:
        results = db.execute_query(sql)
        if results is not None:
            current_value = str(results[0][0]) if results else None
            if current_value is None:
                logger.info(f"配置项 {config_item_name} 不存在。")
            elif current_value != expected_value:
                update_sql = get_update_sql(config_item_name, expected_value)
                db.execute_sql_by_type(update_sql, operation_type="update")
                logger.info(f"更新 {config_item_name}: {current_value} -> {expected_value}")
            else:
                logger.info(f"配置项 {config_item_name } 的值已是期待值：{expected_value}")
    except Exception as e:
        logger.info(f"处理配置项 {config_item_name or '未知配置'} 时发生错误: {e}")


def get_update_sql(config_item_name, expected_value):
    if config_item_name is not None:
        return "UPDATE tc_sys_config_item SET item_value='{}' WHERE config_item_name='{}'".format(expected_value, config_item_name)
    else:
        return "UPDATE tc_gis_base_layer SET use_proxy={} WHERE layer_id={}".format(expected_value, expected_value)


def check_update(config_item_name, expected_value):
    db = Database(db_type)
    sql = "SELECT item_value FROM tc_sys_config_item WHERE config_item_name = '{}'".format(config_item_name)
    fetch_and_compare(db, sql, expected_value, config_item_name)


# 检查 tc_gis_base_layer 表中的记录
db = Database(db_type)
query_sql = "SELECT use_proxy FROM tc_gis_base_layer WHERE layer_id = {}".format(2)
fetch_and_compare(db, query_sql, 2)

# 检查 tc_sys_config_item 表中的记录
for config_item_name, expected_value in updates.items():
    check_update(config_item_name, expected_value)
