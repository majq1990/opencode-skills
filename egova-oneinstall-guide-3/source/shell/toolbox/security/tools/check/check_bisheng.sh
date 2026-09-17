#!/bin/bash

# 数据库配置
DB_HOST="bisheng_db_ip"
DB_USER="bisheng_db_user"
DB_PASS="bisheng_db_password"
DB_NAME="bisheng_db_name"

# 预期的更新值，除了IP_FIREWALL_BLACKLIST和IP_FIREWALL_WHITELIST以外
EXPECTED_VALUES=(
  "REQUEST_BODY_DECODE_TYPE|1"
  "UPLOAD_WHITELIST_ENABLED|1"
  "UPLOAD_WHITELIST_VALUE|zip,json"
  "XSS_ENABLED|1"
  "IP_FIREWALL_ENABLED|1"
)

# 文件用于存储用户输入的配置值
CONFIG_FILE="bisheng_firewall_values.txt"

# 提示用户输入IP_FIREWALL_BLACKLIST的值并保存
input_and_save_ip_firewall_blacklist() {
  read -p "请输入IP_FIREWALL_BLACKLIST的值（多个IP用逗号隔开）: " input
  IP_FIREWALL_BLACKLIST=${input//,/}  # 替换逗号，避免解析错误
  echo "IP_FIREWALL_BLACKLIST|$IP_FIREWALL_BLACKLIST" >> "$CONFIG_FILE"
}

# 提示用户输入IP_FIREWALL_WHITELIST的值并保存
input_and_save_ip_firewall_whitelist() {
  read -p "请输入IP_FIREWALL_WHITELIST的值（多个IP用逗号隔开）: " input
  IP_FIREWALL_WHITELIST=${input//,/}
  echo "IP_FIREWALL_WHITELIST|$IP_FIREWALL_WHITELIST" >> "$CONFIG_FILE"
}

# 检查更新操作是否有效执行的函数
check_update() {
    local name=$1
    local expected_value=$2
    local actual_value=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "SELECT item_value FROM stat_config_item WHERE config_item_name = '$name';" | tr -d '\n')
    
    if [ "$actual_value" == "$expected_value" ]; then
        echo "配置项 $name 已经是期望的值 $expected_value"
    else
        echo "配置项 $name 未更新为期望的值 $expected_value, 当前值为 $actual_value"
    fi
}

# 检查CONFIG_FILE文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
  # 如果文件不存在，提示用户输入并保存
  input_and_save_ip_firewall_blacklist
  input_and_save_ip_firewall_whitelist
  # 将IP_FIREWALL_OTHERWISE_TYPE的值添加到配置文件
  echo "IP_FIREWALL_OTHERWISE_TYPE|1" >> "$CONFIG_FILE"
else
  # 如果文件存在，从文件中读取IP值
  IP_FIREWALL_BLACKLIST=$(grep "IP_FIREWALL_BLACKLIST" "$CONFIG_FILE" | cut -d'|' -f2)
  IP_FIREWALL_WHITELIST=$(grep "IP_FIREWALL_WHITELIST" "$CONFIG_FILE" | cut -d'|' -f2)
fi

# 将用户输入的值添加到EXPECTED_VALUES数组中
EXPECTED_VALUES+=(
  "IP_FIREWALL_BLACKLIST|$IP_FIREWALL_BLACKLIST"
  "IP_FIREWALL_WHITELIST|$IP_FIREWALL_WHITELIST"
  "IP_FIREWALL_OTHERWISE_TYPE|1"
)

# 检查 stat_config_item 表中的记录
for i in "${!EXPECTED_VALUES[@]}"; do
  name_value_pair=($(echo "${EXPECTED_VALUES[$i]}" | tr "|" " "))
  check_update "${name_value_pair[0]}" "${name_value_pair[1]}"
done
