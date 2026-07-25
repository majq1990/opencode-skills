#!/bin/bash

# 数据库配置
DB_HOST=$1
DB_USER=$2
DB_NAME=$3
DB_PASS=$4

# 预期的更新值
EXPECTED_VALUES=(
  "egova.wukong.force.change.P|true"
  "encode|sm4"
  "encodeWhiteList|/wfs"
  "egova.security.password.enable|true"
  "login|true"
  "egova.security.password.passwordExpireDays|180"
  "egova.security.password.strong|EASY"
  "egova.security.passwordEncryptType|sm2"
  "egova.security.failure.enable|true"
  "egova.security.failure.account-lock-minutes|10"
  "egova.security.failure.max-retry-times|5"
  "egova.wukong.interceptor.freeInterfaceVerifyUrl|/free/page,/free/project/,/free/card-data/,/free/layer-menu,/free/interaction,/free/image/upload"
  "egova.wukong.interceptor.imageAllowType|png,svg,jpg,otf,ttf,gif,jpeg,webm,woff"
  "egova.wukong.interceptor.imageDisabledType|html,htm,shtml,shtm,shtml"
  "egova.xss.enabled|true"
  "egova.xss.excludes|"
  "egova.xss.urlPatterns|/*"
)

# 检查更新操作是否有效执行的函数
check_update() {
    local name=$1
    local expected_value=$2
    local actual_value=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "SELECT value FROM com_option WHERE name = '$name';" | tr -d '\n')
    
    if [ "$actual_value" == "$expected_value" ]; then
        echo "配置项 $name 已经是期望的值 $expected_value"
    else
        echo "配置项 $name 未更新为期望的值 $expected_value, 当前值为 $actual_value"
    fi
}

# 检查 com_option 表中的记录
for i in "${!EXPECTED_VALUES[@]}"; do
    name_value_pair=($(echo "${EXPECTED_VALUES[$i]}" | tr "|" " "))
    check_update "${name_value_pair[0]}" "${name_value_pair[1]}"
done
