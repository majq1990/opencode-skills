#!/bin/bash

# 数据库配置
DB_HOST=$1
DB_USER=$2
DB_NAME=$3
DB_PASS=$4

# 预期的更新值，与上面的UPDATE语句中的值对应
EXPECTED_VALUES=(
     "PASSWORD_COMPLEXITY|1",
     "HUMAN_DEFAULT_PASSWORD|eGova@2024",
     "LOGIN_FAILURE_MAX_RETRY_TIMES|5",
     "LOGIN_FAILURE_ACCOUNT_LOCK_MINUTES|5",
     "APP_FIRST_LOGIN_PW|true",
     "CHECK_CRYPTOGRAM_STRENGTH|true",
     "SECURITY_ENABLED|true",
     "LOGIN_MULTI_IP|true"
)

# 检查更新操作是否有效执行的函数
check_update() {
    local name=$1
    local value=$2
    local actual_value=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "SELECT value FROM com_option WHERE name = '$name';" | tr -d '\n')
    
    if [ "$actual_value" == "$value" ]; then
        echo "配置项 com_option.$name 已经是期望的值 $value"
    else
        echo "配置项 com_option.$name 未更新为期望的值 $value, 当前值为 $actual_value"
    fi
}

# 检查 com_option 表中的记录
for i in "${!EXPECTED_VALUES[@]}"; do
    name_value_pair=($(echo "${EXPECTED_VALUES[$i]}" | tr "|" " "))
    check_update "${name_value_pair[0]}" "${name_value_pair[1]}"
done
