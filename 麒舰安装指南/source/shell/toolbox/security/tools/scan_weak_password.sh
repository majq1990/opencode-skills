#!/bin/bash
## 弱密码检查工具脚本

OPTION_FILE=./selection_config.yml
path_script="/egova/weakPwd_Check"
DB_TABLE="com_user"
CUSTOME_FIELD="encryptionType"
function display_selection() {
  echo "请选择加密的产品类型："
  yq '.[] | select(.display=="1") | key ' ${OPTION_FILE} | while read key; do
    local name=$(yq ".${key}.name" ${OPTION_FILE})
    local choice_index=$(yq ".${key}.choice_index" ${OPTION_FILE})
    echo "${choice_index}: ${name}"
  done
  echo "q: 退出"
  read -p "请选择: " Select
  case "${Select}" in
  1)
    display_service_select "v14_service"
    ;;
  2)
    display_service_select "app_service"
    ;;
  q)
    echo "退出"
    exit 0
    ;;
  *)
    echo "选择错误！"
    ;;
  esac
  display_selection
}
function display_service_select() {
  local key=$1
  local count=$(yq ".${key}.sub_options | length " ${OPTION_FILE})
  local index=0
  echo "请选择弱密码扫描产品："
  while [ $index -lt $count ]; do
    local server_name=$(yq ".${key}.sub_options[${index}].name" ${OPTION_FILE})
    ((index = index + 1))
    echo "${index}: ${server_name}"
  done
  echo "q: 退出"
  read -p "请选择: " Select
  case "$Select" in
  1)
    if [ "${key}" = "v14_service" ]; then
      check_weak_password "bootstrap.sh" "mysql" ${key}
    else
      display_database_type_select ${key} $(($Select - 1)) "linglong"
    fi
    ;;
  2)
    if [ "${key}" = "v14_service" ]; then
      DB_TYPE="dm"
      DB_DRIVER="dm.jdbc.driver.DmDriver"
      check_weak_password "bootstrap.sh" ${DB_TYPE} ${key}
    else
      display_database_type_select ${key} $(($Select - 1)) "dex"
    fi
    ;;
  3)
    if [ "${key}" = "v14_service" ]; then
      DB_TYPE="postgresql"
      DB_DRIVER="org.postgresql.Driver"
      check_weak_password "bootstrap.sh" ${DB_TYPE} ${key}
    else
      display_database_type_select ${key} $(($Select - 1)) "wukong"
    fi
    ;;
  4)
    if [ "${key}" = "v14_service" ]; then
      DB_TYPE="postgresql"
      DB_DRIVER="org.postgresql.Driver"
      check_weak_password "bootstrap.sh" ${DB_TYPE} ${key}
    else
      display_database_type_select ${key} $(($Select - 1)) "usercenter"
    fi
    ;;
  q)
    echo "退出安装"
    exit 0
    ;;
  *)
    echo "选择错误！"
    display_service_select
    ;;
  esac
}
function display_database_type_select() {
  local key=$1
  local index=$2
  local app_type=$3
  local count=$(yq ".${key}.sub_options[${index}].sub_options | length " ${OPTION_FILE})
  local sub_index=0
  echo "请选择检查的数据库类型："
  while [ $sub_index -lt $count ]; do
    local name=$(yq ".${key}.sub_options[${index}].sub_options[${sub_index}].name" ${OPTION_FILE})
    ((sub_index = sub_index + 1))
    echo "${sub_index}: ${name}"
  done
  echo "q: 退出"
  read -p "请选择: " Select
  case "$Select" in
  1)
    check_weak_password "bootstrap-lowcode.sh" "mysql" ${app_type}
    ;;
  2)
    DB_TYPE="dm"
    DB_DRIVER="dm.jdbc.driver.DmDriver"

    check_weak_password "bootstrap-lowcode.sh" ${DB_TYPE} ${app_type}
    ;;
  3)
    DB_TYPE="postgresql"
    DB_DRIVER="org.postgresql.Driver"
    check_weak_password "bootstrap-lowcode.sh" ${DB_TYPE} ${app_type}
    ;;
  4)
    DB_TYPE="postgresql"
    DB_DRIVER="org.postgresql.Driver"
    check_weak_password "bootstrap-lowcode.sh" ${DB_TYPE} ${app_type}
    ;;
  q)
    echo "退出安装"
    exit 0
    ;;
  *)
    echo "选择错误！"
    display_database_type_select
    ;;
  esac
}
function input_database_connection_info() {
  local db_type=$1
  local product_type=$2
  echo "Database type ${db_type}"
  read -ep '请输入数据库IP:' DB_HOST
  read -ep '请输入数据库端口:' DB_PORT
  read -ep '请输入数据库用户名:' DB_USER
  read -sp '请输入数据库用户密码:' DB_PASSWORD && printf "\n"
  if  [ "${db_type}" != "dm" ]; then
     read -ep '请输入数据库实例名称:' DB_NAME
  fi
  if { [[ "${product_type}" == "dex" ]] && [ "${db_type}" == "dm" ]; }; then
    return
  fi
  if { [[ "${db_type}" == "postgresql" ]] || [ "${db_type}" == "dm" ]; }; then
    read -ep '请输入数据库Schema:' DB_SCHEMA
  fi
}
function modify_database_connection_info() {
  local key=$1
  local db_type=$2
  local product_type=$3
  if [ "${db_type}" == "postgresql" ] && [ "${product_type}" == "v14_service" ] && [ "${DB_SCHEMA}" != "" ]; then
    sed -i "s|DATASOURCE_URL=jdbc:DB_TYPE://DB_HOST:DB_PORT/DB_NAME|DATASOURCE_URL=jdbc:${db_type}://${DB_HOST}:${DB_PORT}/${DB_NAME}?currentSchema=${DB_SCHEMA}|g" ${path_script}/$1
  elif [ "${product_type}" == "usercenter" ]; then
    DB_TABLE="sys_human"
    if [ "${db_type}" == "dm" ]; then
      sed -i "s|DATASOURCE_URL=jdbc:DB_TYPE://DB_HOST:DB_PORT/DB_NAME|DATASOURCE_URL=jdbc:${db_type}://${DB_HOST}:${DB_PORT}|g" ${path_script}/$1
    elif [ "${db_type}" == "postgresql" ]; then
      sed -i "s|DATASOURCE_URL=jdbc:DB_TYPE://DB_HOST:DB_PORT/DB_NAME|DATASOURCE_URL=jdbc:${db_type}://${DB_HOST}:${DB_PORT}/${DB_NAME}?currentSchema=${DB_SCHEMA}|g" ${path_script}/$1
    fi
    sed -i "s|DB_HOST:DB_PORT/DB_NAME|${DB_HOST}:${DB_PORT}/${DB_NAME}|g" ${path_script}/$1
    sed -i '/QUERY_SCRIPT/d' ${path_script}/$1
    sed -i '31s/.*/--QUERY_SCRIPT='"'"'select id as id, uid as humanId, username as username, cryptogram_salt as salt, cryptogram_type as encType, cryptogram as dbValue from usercenter.sys_human where uid>? and valid_flag=1 and delete_flag=0 order by uid asc limit <maxFetchSize>'"'"' \\\n&/' ${path_script}/$1
    sed -i '/COUNT_SCRIPT/d' ${path_script}/$1
    sed -i '32s/.*/--COUNT_SCRIPT='"'"'select count(*) from sys_human where valid_flag=1 and delete_flag=0'"'"' \\\n&/' ${path_script}/$1
  elif [ "${product_type}" == "dex" ] &&  [ "${db_type}" == "postgresql" ] ; then
    CUSTOME_FIELD="'BCrypt'"
    sed -i "s|DATASOURCE_URL=jdbc:DB_TYPE://DB_HOST:DB_PORT/DB_NAME|DATASOURCE_URL=jdbc:${db_type}://${DB_HOST}:${DB_PORT}/${DB_NAME}?currentSchema=${DB_SCHEMA}|g" ${path_script}/$1
  elif [ "${product_type}" == "dex" ] &&  [ "${db_type}" == "dm" ] ; then
    CUSTOME_FIELD="'BCrypt'"
    sed -i "s|DATASOURCE_URL=jdbc:DB_TYPE://DB_HOST:DB_PORT/DB_NAME|DATASOURCE_URL=jdbc:${db_type}://${DB_HOST}:${DB_PORT}|g" ${path_script}/$1
  elif [ "${product_type}" == "dex" ]; then
    CUSTOME_FIELD="'BCrypt'"
    sed -i "s|DB_HOST:DB_PORT/DB_NAME|${DB_HOST}:${DB_PORT}/${DB_NAME}|g" ${path_script}/$1
  elif [ "${db_type}" == "postgresql" ] && { [ "${product_type}" == "linglong" ] || [ "${product_type}" == "wukong" ]; }; then
    sed -i "s|DATASOURCE_URL=jdbc:DB_TYPE://DB_HOST:DB_PORT/DB_NAME|DATASOURCE_URL=jdbc:${db_type}://${DB_HOST}:${DB_PORT}/${DB_NAME}?currentSchema=${DB_SCHEMA}|g" ${path_script}/$1
  elif [ "${db_type}" == "dm" ] && [ "${product_type}" == "wukong" ]; then
    sed -i "s|DATASOURCE_URL=jdbc:DB_TYPE://DB_HOST:DB_PORT/DB_NAME|DATASOURCE_URL=jdbc:${db_type}://${DB_HOST}:${DB_PORT}?SCHEMA=${DB_SCHEMA}|g" ${path_script}/$1
  elif [ "${db_type}" == "dm" ]; then
    sed -i "s|DATASOURCE_URL=jdbc:DB_TYPE://DB_HOST:DB_PORT/DB_NAME|DATASOURCE_URL=jdbc:${db_type}://${DB_HOST}:${DB_PORT}?clobAsString=true|g" ${path_script}/$1
  else
    sed -i "s|DB_HOST:DB_PORT/DB_NAME|${DB_HOST}:${DB_PORT}/${DB_NAME}|g" ${path_script}/$1
  fi
  if [ "${product_type}" != "usercenter" ]; then
    sed -i "s|DB_TABLE|${DB_TABLE}|g" ${path_script}/$1
    sed -i "s|CUSTOME_FIELD|${CUSTOME_FIELD}|g" ${path_script}/$1
  fi
  if [ "${db_type}" == "mysql" ]; then
    sed -i '/DATASOURCE/d' ${path_script}/$1
  else
    sed -i '/MYSQL/d' ${path_script}/$1
  fi
  sed -i "s|DB_USER|${DB_USER}|g" ${path_script}/$1
  sed -i "s|DB_PASSWORD|${DB_PASSWORD}|g" ${path_script}/$1
  sed -i "s|DB_TYPE|${DB_TYPE}|g" ${path_script}/$1
  sed -i "s|DB_DRIVER|${DB_DRIVER}|g" ${path_script}/$1
}
function check_weak_password() {
  local key=$1
  local db_type=$2
  local product_type=$3
  input_database_connection_info ${db_type} ${product_type}
  \cp -f template/$1 ${path_script}/$1
#  if [ "${product_type}" == "v14_service" ] && [ "${db_type}" == "mysql" ]; then
#    query="SELECT count(*) as count FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='tc_human' AND COLUMN_NAME='enc_rdm';"
#    result=$(mysql -h ${DB_HOST} -u ${DB_USER} -p${DB_PASSWORD} -e "${query}")
#    value=$(echo "$result" | awk 'NR==2{print $1}')
#    echo "返回值：${value}"
#    if [[ ${value} -eq 0 ]]; then
#      echo "字段 $FIELD_NAME 不存在于表 $TABLE_NAME 中"
#      sed -i '30s/.*/--QUERY_SCRIPT='"'"'select human_id as humanId,user_name as username,human_password as dbValue from tc_human where human_id>? and valid_flag=1 and delete_flag=0 order by human_id asc limit <maxFetchSize>'"'"' \\\n&/' ${path_script}/$1
#    fi
#  fi
  modify_database_connection_info $1 ${db_type} ${product_type}
  cd ${path_script}
  bash $1
  cd -
}

function check_architecture() {
  uname_info=$(arch)

  if echo "$uname_info" | grep -q -i "arm"; then
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
    if test -f src/yq_x86 &&  check_architecture ; then
        \cp src/yq_x86 $yqpath
        chmod +x $yqpath
    else
       \cp src/yq_arm64 $yqpath
        chmod +x $yqpath
    fi
}
function unarchive() {
  add_yq
  if ! test -d /egova/weakPwd_Check; then
     tar xvf src/weakPwd_Check.tar.gz -C /egova/
  fi
}
function check_env(){
    which java 1>/dev/null 2>/dev/null
    if [ $? -gt 0 ] ;then
        echo "请在有jdk环境的服务器上运行弱密码检测工具!"
        exit 1
    fi
}
function run() {
    check_env
    unarchive
    display_selection
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

if ! _is_sourced; then
    run "$@"
fi
