#!/bin/bash

. tools/utils/tool_echo.sh

set -e
# 检查是否安装了 yq
if ! command -v yq &> /dev/null; then
    Echo_Red "未安装 yq。请安装它以解析 YAML 文件。"
    exit 1
fi

# 从 YAML 文件加载配置
CONFIG_FILE="tools/conf/check_config.yml"
CHECK_SCRIPT="/egova/check_start.sh"

# 本地文件路径
LOCAL_PASSWORD_FILE="law_default_passwd.txt"
DEX_CONFIG_FILE="dex_firewall_values.txt"
# 文件用于存储用户输入的配置值
BS_CONFIG_FILE="bisheng_firewall_values.txt"

IP_FIREWALL_BLACKLIST=""
IP_FIREWALL_WHITELIST=""

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
# 提示用户输入IP_FIREWALL_BLACKLIST的值并保存
input_and_save_ip_firewall_blacklist() {
  read -p "请输入IP_FIREWALL_BLACKLIST的值（多个IP用逗号隔开）: " IP_FIREWALL_BLACKLIST
#   IP_FIREWALL_BLACKLIST=${input//,/}  # 替换逗号，避免解析错误
  echo "IP_FIREWALL_BLACKLIST|$IP_FIREWALL_BLACKLIST" >> "$BS_CONFIG_FILE"
}

# 提示用户输入IP_FIREWALL_WHITELIST的值并保存
input_and_save_ip_firewall_whitelist() {
  read -p "请输入IP_FIREWALL_WHITELIST的值（多个IP用逗号隔开）: " IP_FIREWALL_WHITELIST
#   IP_FIREWALL_WHITELIST=${input//,/}
  echo "IP_FIREWALL_WHITELIST|$IP_FIREWALL_WHITELIST" >> "$BS_CONFIG_FILE"
}
function check_bisheng_config(){
    if [ ! -f "$BS_CONFIG_FILE" ]; then
      input_and_save_ip_firewall_blacklist
      input_and_save_ip_firewall_whitelist
      # 将IP_FIREWALL_OTHERWISE_TYPE的值添加到配置文件
      echo "IP_FIREWALL_OTHERWISE_TYPE|1" >> "$BS_CONFIG_FILE"
    else
      # 如果文件存在，从文件中读取IP值
      IP_FIREWALL_BLACKLIST=$(grep "IP_FIREWALL_BLACKLIST" "$BS_CONFIG_FILE" | cut -d'|' -f2)
      IP_FIREWALL_WHITELIST=$(grep "IP_FIREWALL_WHITELIST" "$BS_CONFIG_FILE" | cut -d'|' -f2)
    fi
        echo "IP防火墙黑名单: $IP_FIREWALL_BLACKLIST"
        echo "IP防火墙白名单: $IP_FIREWALL_WHITELIST"
}
function check_dex_config(){
    # 检查配置文件是否存在
    if [ ! -f "$DEX_CONFIG_FILE" ]; then
      # 如果文件不存在，提示用户输入并保存
      read -p "请输入IP防火墙黑名单（多个IP用逗号隔开）: " IP_FIREWALL_BLACKLIST
      echo "egova.security.ip-firewall.blacklist|$IP_FIREWALL_BLACKLIST" > "$DEX_CONFIG_FILE"

      read -p "请输入IP防火墙白名单（多个IP用逗号隔开）: " IP_FIREWALL_WHITELIST
      echo "egova.security.ip-firewall.whitelist|$IP_FIREWALL_WHITELIST" >> "$DEX_CONFIG_FILE"
    else
      # 如果文件存在，从文件中读取IP地址
      IP_FIREWALL_BLACKLIST=$(grep "egova.security.ip-firewall.blacklist" "$DEX_CONFIG_FILE" | cut -d'|' -f2)
      IP_FIREWALL_WHITELIST=$(grep "egova.security.ip-firewall.whitelist" "$DEX_CONFIG_FILE" | cut -d'|' -f2)
    fi
    echo "IP防火墙黑名单: $IP_FIREWALL_BLACKLIST"
    echo "IP防火墙白名单: $IP_FIREWALL_WHITELIST"
}

function list_displayed_checks {
    local checks=($(yq -r '.checks[] | select(.display == true) | .desc' "$CONFIG_FILE"))
    Echo_Yellow "请输入要检查的产品: "
    for i in "${!checks[@]}"; do
        echo "$((i + 1)): ${checks[i]}"
    done
    read -ep "请选择: " product_index

    # 获取指定产品的脚本
    product_name=$(get_check_product_name "$product_index")
    if [ "$product_name" == "law" ]; then
          DEFAULT_PASSWORD=$(read_default_password)
    elif [ "$product_name" == "dex" ]; then
        check_dex_config
    elif [ "$product_name" == "bisheng" ]; then
         check_bisheng_config
    fi
}
function list_displayed_db_types {
    local  db_types=($(yq -r '.db_types[] | select(.display == true) | .desc' "$CONFIG_FILE"))
    Echo_Yellow "请输入数据库类型: "
     for i in "${!db_types[@]}"; do
            echo "$((i + 1)): ${db_types[i]}"
    done
    read -ep "请选择: " db_type_index
    case "${db_type_index}" in
        1)
          DB_TYPE="mysql"
          DB_DRIVER="com.mysql.cj.jdbc.Driver"
          modify_db_config ${DB_TYPE}
          ;;
        2)
          DB_TYPE="dm"
          DB_DRIVER="dm.jdbc.driver.DmDriver"
          modify_db_config ${DB_TYPE}
          ;;
        3)
          DB_TYPE="postgresql"
          DB_DRIVER="org.postgresql.Driver"
          modify_db_config ${DB_TYPE}
          ;;
        4)
          DB_TYPE="highgo"
          DB_DRIVER="com.highgo.jdbc.Driver"
          modify_db_config ${DB_TYPE}
          ;;
        q)
            echo "退出"
            exit 0
            ;;
        *)
            echo "选择错误！"
            list_displayed_db_types
            ;;
            esac
}
# 函数：获取指定产品的检查脚本名称
function get_check_product_name {
    local index="$1"
    yq -r '.checks[] | select(.display == true) | .name' "$CONFIG_FILE" | sed -n "${index}p"
}

function get_check_db {
    local index="$1"
    yq -r '.db_types[] | select(.display == true) | .name' "$CONFIG_FILE" | sed -n "${index}p"
}

function run_check {
    local script_name="$1"
    if [[ -n "$script_name" ]]; then
    current_dir=$(pwd)
    echo "Current directory: $current_dir"
        Echo_Yellow "------正在运行检查------:"
        bash "$script_name"
    else
        Echo_Red "错误: 找不到或无法执行脚本
        $script_name。"
    fi
}

function modify_db_config {
    local DB_TYPE="$1"
     # 从用户获取数据库信息
    Echo_Yellow "请输入数据库信息:"
    read -ep "数据库IP地址: " DB_HOST
    read -ep "数据库端口: " DB_PORT
    read -ep "数据库用户名: " DB_USER
    read -ep "数据库名称: " DB_NAME
    read -ep "数据库密码: " DB_PASSWORD
    read -ep '请输入数据库Schema:' DB_SCHEMA
    echo # 为密码输入后换行
    cp -f tools/template/check_start.sh ${CHECK_SCRIPT}
    echo "------DB_TYPE=$DB_TYPE"
    if [ "${DB_TYPE}" == "mysql" ]; then
      sed -i "s|-Ddatasource_url=.*|-Ddatasource_url=jdbc:${DB_TYPE}://${DB_HOST}:${DB_PORT}/${DB_NAME}?serverTimezone=Asia/Shanghai \\\\|g" ${CHECK_SCRIPT}
    elif [ "${DB_TYPE}" == "dm" ]; then
      sed -i "s|-Ddatasource_url=.*|-Ddatasource_url=jdbc:${DB_TYPE}://${DB_HOST}:${DB_PORT}?clobAsString=true \\\\|g" ${CHECK_SCRIPT}
    elif [ "${DB_TYPE}" == "postgresql" ]; then
      sed -i "s|-Ddatasource_url=.*|-Ddatasource_url=jdbc:${DB_TYPE}://${DB_HOST}:${DB_PORT}/${DB_NAME} \\\\|g" ${CHECK_SCRIPT}
    elif [ "${DB_TYPE}" == "highgo" ]; then
      sed -i "s|-Ddatasource_url=.*|-Ddatasource_url=jdbc:${DB_TYPE}://${DB_HOST}:${DB_PORT}/${DB_NAME}?currentSchema=${DB_SCHEMA},public&serverTimezone=GMT%2B8 \\\\|g" ${CHECK_SCRIPT}
    else
      Echo_Red "不支持数据库类型:${DB_TYPE}"
      exit 1
    fi
    sed -i "s|DB_HOST:DB_PORT|${DB_HOST}:${DB_PORT}|g" ${CHECK_SCRIPT}
    sed -i "s|DB_TYPE|${DB_TYPE}|g" ${CHECK_SCRIPT}
    sed -i "s|DB_USER|${DB_USER}|g" ${CHECK_SCRIPT}
    sed -i "s|DB_PASSWORD|${DB_PASSWORD}|g" ${CHECK_SCRIPT}
    sed -i "s|DB_DRIVER|${DB_DRIVER}|g" ${CHECK_SCRIPT}
    sed -i "s|DB_SCHEMA|${DB_SCHEMA}|g" ${CHECK_SCRIPT}
    sed -i "s|PRODUCT_TYPE|${product_name}|g" ${CHECK_SCRIPT}
    sed -i "s|IP_FIREWALL_BLACKLIST|${IP_FIREWALL_BLACKLIST}|g" ${CHECK_SCRIPT}
    sed -i "s|IP_FIREWALL_WHITELIST|${IP_FIREWALL_WHITELIST}|g" ${CHECK_SCRIPT}
    sed -i "s|DEFAULT_PASSWORD|${DEFAULT_PASSWORD}|g" ${CHECK_SCRIPT}
    sed -i "s|CONFIG_PATH|$(pwd)/tools/conf/product-configs.json|g" ${CHECK_SCRIPT}
}
function check_architecture() {
  uname_info=$(uname -a)

  if echo "$uname_info" | grep  -q -i "arm"; then
    echo "ARM 架构"
    return 1
  elif echo "$uname_info" | grep -q -i "x86_64"; then
    echo "x86_64 架构"
    return 0
  elif echo "$uname_info" | grep -q -i "i386\|i686"; then
    echo "x86 架构"
    return 0
  else
    echo "无法确定系统架构"
    return 2
  fi
}
function add_yq() {
    type yq > /dev/null 2>&1
    local isExist=$?
    if [[ $isExist = 0 ]]; then
       local yqpath=`which yq`
    else
       local yqpath="/usr/bin/yq"
    fi
    if test -f tools/src/yq_x86 ; then
        \cp tools/src/yq_x86 $yqpath
        chmod +x $yqpath
    else
       \cp tools/src/yq_arm64 $yqpath
        chmod +x $yqpath
    fi
}

function check_jar() {
    local jar_path="/egova/security"
    local jar_file="tools/src/egova-check-save-tools.jar"

    # 检查目标目录是否存在，如果不存在则创建
    if ! test -d "$jar_path"; then
        echo "目录 $jar_path 不存在，正在创建..."
        mkdir -p "$jar_path"
    fi

    # 检查源文件是否存在
    if ! test -f "$jar_file"; then
        echo "文件 $jar_file 不存在，无法复制。"
        return 1
    fi

    # 复制文件到目标目录
    echo "正在将 $jar_file 复制到 $jar_path..."
    \cp "$jar_file" "$jar_path"

    # 检查复制是否成功
    if test -f "$jar_path/egova-check-save-tools.jar"; then
        echo "文件复制成功。"
    else
        echo "文件复制失败。"
        return 1
    fi
}




function check_env(){
    which java 1>/dev/null 2>/dev/null
    if [ $? -gt 0 ] ;then
        echo "请在有jdk环境的服务器上运行安全配置项检测工具!"
        exit 1
    fi
}
# 运行指定产品的检查
function run() {
    check_env
    check_jar
    list_displayed_checks
    list_displayed_db_types
    run_check "$CHECK_SCRIPT"
    if [ $? = 0 ]; then
       Echo_Green "-----检查完成------:"
       exit 1
    fi
}
#不需要支持ansible模式
function support_multi_mode(){
    echo 0
}

# check to see if this file is being run or sourced from another script
_is_sourced() {
    # https://unix.stackexchange.com/a/215279
    [ "${#FUNCNAME[@]}" -ge 2 ] \
        && [ "${FUNCNAME[0]}" = '_is_sourced' ] \
        && [ "${FUNCNAME[1]}" = 'source' ]
}

run "$@"
