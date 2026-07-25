#!/bin/bash

# 检查是否安装了 yq
if ! command -v yq &> /dev/null; then
    echo "未安装 yq。请安装它以解析 YAML 文件。"
    exit 1
fi

# 从 YAML 文件加载配置
CONFIG_FILE="./check_config.yml"
DB_CONFIG_FILE="./db_config.ini"

function list_displayed_checks {
    local checks=($(yq -r '.checks[] | select(.display == true) | .name' "$CONFIG_FILE"))
    echo "请输入要检查的产品: "
    for i in "${!checks[@]}"; do
        echo "$((i + 1)): ${checks[i]}"
    done
    read -p "请选择: " product_index

    # 获取指定产品的脚本
    script_name=$(get_check_script "$product_index")
}
function list_displayed_db_types {
    local  db_types=($(yq -r '.db_types[] | select(.display == true) | .desc' "$CONFIG_FILE"))
    echo "请输入数据库类型: "
     for i in "${!db_types[@]}"; do
            echo "$((i + 1)): ${db_types[i]}"
    done
    read -p "请选择: " db_type_index
    DB_TYPE=$(get_check_script "$product_index")
    # 从用户获取数据库信息
    echo "请输入数据库信息:"
    read -p "数据库IP地址: " DB_HOST
    read -p "数据库端口: " DB_PORT
    read -p "数据库用户名: " DB_USER
    read -p "数据库名称: " DB_NAME
    read -sp "数据库密码: " DB_PASS
    echo # 为密码输入后换行
}
# 函数：获取指定产品的检查脚本名称
function get_check_script {
    local index="$1"
    yq -r '.checks[] | select(.display == true) | .script' "$CONFIG_FILE" | sed -n "${index}p"
}

function get_check_db {
    local index="$1"
    yq -r '.db_types[] | select(.display == true) | .name' "$CONFIG_FILE" | sed -n "${index}p"
}

function run_check {
    local script_name="$1"
    local db_type="$2"

    if [[ -x "$script_name" ]]; then
    current_dir=$(pwd)
    echo "Current directory: $current_dir"
        echo "------正在运行检查------:"
        python3 "$script_name" "$db_type"
    else
        echo "错误: 找不到或无法执行脚本 $script_name。"
    fi
}

function mkdify_db_config {
 sed -i '/^\['$DB_TYPE'\]/,/^$/ {
     s/^port = .*/port = '$DB_PORT'/
     s/^user = .*/user = '$DB_USER'/
     s/^pwd = .*/pwd = '$DB_PASS'/
     s/^host = .*/host = '$DB_HOST'/
     s/^dbtype = .*/dbtype = '$DB_TYPE'/
     s/^dbname = .*/dbname = '$DB_NAME'/
 }' $DB_CONFIG_FILE

}


# 运行指定产品的检查
function run() {

list_displayed_checks
list_displayed_db_types
modify_db_config
if [[ -n "$script_name" ]]; then
    run_check "$script_name" "$DB_TYPE"
    if [ $? = 0 ]; then
       echo "-----检查完成------:"
       exit 1
    fi
else
    echo "错误: 找不到产品 '$product_name' 的检查。"
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