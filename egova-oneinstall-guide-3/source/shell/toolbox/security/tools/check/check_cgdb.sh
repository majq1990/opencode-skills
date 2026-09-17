#!/bin/bash

# 数据库配置
DB_HOST=$1
DB_USER=$2
DB_NAME=$3
DB_PASS=$4

TABLE_PREFIX="tc_"

# 预期的更新值，与上面的UPDATE语句中的值对应
EXPECTED_VALUES=("0" "1" "1" "0" "0" "3" "0" "5" "5" "5" "6" "9" "1" "[a-z],[A-Z],[0-9],[\$@\$!%*#?&]" "Egova@2023" "1" "view/bizbase/sysconfig?_\$_title=系统配置" "温馨提示：为了您的账号安全，请及时修改密码。" "请按照密码规则修改密码!" "1" "30" "2" "1")

# 检查更新操作是否有效执行的函数
check_update() {
    local config_item_name=$1
    local expected_value=$2
    local actual_value=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "SELECT item_value FROM ${TABLE_PREFIX}sys_config_item WHERE config_item_name = '$config_item_name';" | grep -v "NULL" | tr -d '\n')
    
    if [ "$actual_value" == "$expected_value" ]; then
        echo "配置项 ${TABLE_PREFIX}sys_config_item.$config_item_name 已经是期望的值 $expected_value"
    else
        echo "配置项 ${TABLE_PREFIX}sys_config_item.$config_item_name 未更新为期望的值 $expected_value, 当前值为 $actual_value"
    fi
}

# 检查 tc_gis_base_layer 表中的记录
actual_use_proxy=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "SELECT use_proxy FROM ${TABLE_PREFIX}gis_base_layer WHERE layer_id = 2;" | grep -v "NULL" | tr -d '\n')
if [ "$actual_use_proxy" == "2" ]; then
    echo "GIS 代理配置已经是加密状态"
else
    echo "GIS 代理配置未更新为加密状态, 当前值为 $actual_use_proxy"
fi

# 检查 tc_sys_config_item 表中的记录
for i in "${!EXPECTED_VALUES[@]}"; do
    check_update "${!i}" "${EXPECTED_VALUES[$i]}"
done
