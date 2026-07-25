#!/bin/bash

# 数据库配置
DB_HOST=$1
DB_USER=$2
DB_NAME=$3
DB_PASS=$4

# 预期的更新值
EXPECTED_VALUES=(
  "PUB_MIS_LOGIN_FUZZY_SEARCH|0"
  "PUB_LOGIN_VALID_WAY|1"
  "PUB_LOGIN_VALID_TIME_SEGMENT|5"
  "PUB_LOGIN_VALID_ERROR_NUM|5"
  "PUB_LOGIN_LOCK_TIME|5"
  "PUB_USER_VALIDATE_PASSWORD|1"
  "PUB_PASSWORD_CHECK_REGEXP|[a-z],[A-Z],[0-9],[$@$!%*#?&]"
  "PUB_LOGIN_PASS_MINCHAR|6"
  "PUB_LOGIN_PASS_MAXCHAR|9"
  "PUB_LOGIN_ENABLE_CHANGE_PASSWORD_NOTICE_DIALOG|1"
  "PUB_CHANGE_PASSWORD_NOTICE_CONTENT|温馨提示：为了您的账号安全，请及时修改密码。"
  "PUB_ENABLE_FORCE_CHANGE_PASSWORD|1"
  "PUB_FORCE_CHANGE_PASSWORD_NOTICE_CONTENT|请按照密码规则修改密码!"
  "PUB_LOGIN_PASSWORD_ALLOW_EMPTY|0"
  "PUB_SYS_CONFIG_USER_INFO_MASK|1"
  "PUB_REPORT_USER_NAME_MASK|1"
  "PUB_SYS_CONFIG_IDCARDNUM_MASK|1"
  "UPLOAD_FILE_TYPE_WHITELIST|jpg,jpeg,png,gif,tif,bmp,dwg,html,rtf,xml,zip,xls,xlsx,doc,docx,csv,zip,rar,txt,pdf,mp3,mp4,wav,avi,amr,rm,mpg,mov,sql,proxy,json,wma,3gp,asf,wmv,thumb"
  "DOWNLOAD_FILE_TYPE_WHITELIST|jpg,jpeg,png,gif,tif,bmp,dwg,html,rtf,xml,zip,xls,xlsx,doc,docx,csv,zip,rar,txt,pdf,mp3,mp4,wav,avi,amr,rm,mpg,mov,sql,proxy,json,wma,3gp,asf,wmv,thumb"
)

# 检查更新操作是否有效执行的函数
check_update() {
    local name=$1
    local expected_value=$2
    local actual_value=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "SELECT config_value FROM tc_pub_city_sys_config WHERE Config_Name = '$name';" | tr -d '\n')
    
    if [ "$actual_value" == "$expected_value" ]; then
        echo "配置项 $name 已经是期望的值 $expected_value"
    else
        echo "配置项 $name 未更新为期望的值 $expected_value, 当前值为 $actual_value"
    fi
}

# 检查 tc_pub_city_sys_config 表中的记录
for i in "${!EXPECTED_VALUES[@]}"; do
  name_value_pair=($(echo "${EXPECTED_VALUES[$i]}" | tr "|" " "))
  check_update "${name_value_pair[0]}" "${name_value_pair[1]}"
done
