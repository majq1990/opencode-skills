#!/bin/bash

# 数据库配置
DB_HOST=$1
DB_USER=$2
DB_NAME=$3
DB_PASS=$4

# 本地文件路径
LOCAL_PASSWORD_FILE="law_default_passwd.txt"

# 检查本地文件是否存在，并读取默认密码值
read_default_password() {
  if [ -f "$LOCAL_PASSWORD_FILE" ]; then
    # 从文件中读取默认密码
    DEFAULT_PASSWORD=$(cat "$LOCAL_PASSWORD_FILE")
  else
    # 如果文件不存在，提示用户输入并保存
    read -p "请输入一个唯一的默认密码值: " input_password
    # 写入文件
    echo "$input_password" > "$LOCAL_PASSWORD_FILE"
    # 再次读取确认
    read -p "请再次输入以确认密码: " confirm_password
    if [ "$input_password" != "$confirm_password" ]; then
      echo "两次输入的密码不匹配，请重新运行脚本。"
      exit 1
    fi
    DEFAULT_PASSWORD="$input_password"
  fi
  echo "$DEFAULT_PASSWORD"
}

# 获取默认密码值
DEFAULT_PASSWORD=$(read_default_password)

# 预期的更新值
EXPECTED_VALUES=(
  "MIS_PASSWORD_CHECK_REGEXP|[a-z],[A-Z],[0-9],[\$@\$!%*#?&]"
  "MIS_BUILDER_HUMAN_PASSWORD_CHECK_REGEXP|[a-z],[A-Z],[0-9],[\$@\$!%*#?&]"
  "MIS_BUILDER_HUMAN_DEFAULT_PASSWORD|$DEFAULT_PASSWORD"
  "MIS_DEFAULT_PASSWORD_FORCE_CHANGE|1"
  "MIS_ENABLE_FORCE_CHANGE_PASSWORD|1"
  "MIS_FORCE_CHANGE_PASSWORD_PERIOD|3"
  "MOBILE_FORM_DATA_ENCRYPT_PARAM|1"
  "MIS_LOGIN_VALID_WAY|3"
  "MIS_LOGIN_VALID_ERROR_NUM|5"
  "MIS_LOGIN_LOCK_TIME|5"
  "MIS_LOGIN_VALID_TIME_SEGMENT|5"
  "AUTO_COMPLETE_TIP|5"
)

# 检查更新操作是否有效执行的函数
check_update() {
    local table_name=$1
    local name=$2
    local expected_value=$3
    local actual_value=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "SELECT item_value FROM $table_name WHERE config_item_name = '$name';" | tr -d '\n')
    
    if [ "$actual_value" == "$expected_value" ]; then
        echo "配置项 $table_name.$name 已经是期望的值 $expected_value"
    else
        echo "配置项 $table_name.$name 未更新为期望的值 $expected_value, 当前值为 $actual_value"
    fi
}

# 检查 tc_sys_config_item 表中的记录
for i in "${!EXPECTED_VALUES[@]}"; do
  name_value_pair=($(echo "${EXPECTED_VALUES[$i]}" | tr "|" " "))
  check_update "tc_sys_config_item" "${name_value_pair[0]}" "${name_value_pair[1]}"
done
