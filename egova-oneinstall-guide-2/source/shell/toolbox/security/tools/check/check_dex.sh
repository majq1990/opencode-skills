#!/bin/bash

# 数据库配置
DB_HOST=$1
DB_USER=$2
DB_NAME=$3
DB_PASS=$4

# 配置文件路径
CONFIG_FILE="dex_firewall_values.txt"

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
  # 如果文件不存在，提示用户输入并保存
  read -p "请输入IP防火墙黑名单（多个IP用逗号隔开）: " blacklist_ips
  echo "egova.security.ip-firewall.blacklist|$blacklist_ips" > "$CONFIG_FILE"

  read -p "请输入IP防火墙白名单（多个IP用逗号隔开）: " whitelist_ips
  echo "egova.security.ip-firewall.whitelist|$whitelist_ips" >> "$CONFIG_FILE"
else
  # 如果文件存在，从文件中读取IP地址
  IFS=$'\n' read -rd '' -a blacklist_line < <(grep "egova.security.ip-firewall.blacklist" "$CONFIG_FILE")
  blacklist_ips=$(echo "${blacklist_line[1]}" | cut -d'|' -f2)

  IFS=$'\n' read -rd '' -a whitelist_line < <(grep "egova.security.ip-firewall.whitelist" "$CONFIG_FILE")
  whitelist_ips=$(echo "${whitelist_line[1]}" | cut -d'|' -f2)
fi

# 预期的更新值
EXPECTED_VALUES=(
  "egova.security.referer.enabled|true"
  "egova.security.referer.referer|允许访问的来源，逗号隔开多个，一般设置一个内网地址、一个外网地址"
  "egova.security.front-end-encrypted|true"
  "egova.security.failure.enable|true"
  "egova.security.failure.maxRetryTimes|5"
  "egova.security.failure.accountLockMinutes|10"
  "egova.security.fileupload.whitelist.enabled|true"
  "egova.security.xss.enabled|true"
  "egova.security.ip-firewall.enabled|true"
  "egova.security.ip-firewall.blacklist|$blacklist_ips"
  "egova.security.ip-firewall.whitelist|$whitelist_ips"
  "web.commonsetting.isConversionMethod|true"
  "web.commonsetting.isShowSignature|true"
  "web.commonsetting.encryptType|aes"
  "egova.request.body.decode|aes"
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
