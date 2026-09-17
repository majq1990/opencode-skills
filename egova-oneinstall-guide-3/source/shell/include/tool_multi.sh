#!/bin/bash

# hosts.yml
hosts_file=../../ansible/inventory/hosts.yml
global_conf=../../ansible/group_vars/all.yml
server_file=$1

. ../include/tool_echo.sh
. ../include/tool_hosts.sh
deploy_status_flag=0
# 获取指定类型服务器下配置的从节点数量
function get_slave_node_count() {
  if [[ "$1" != "" && "$1" != *yml* ]]; then
      local name=$1

      local count=$(yq ".${name}.hosts.slave | length " ${server_file})
      echo $count
  fi
}

# 获取主节点配置值长度，用于判断是否配置主节点
function get_master_node_count() {
    local name=$1

    local count=$(yq ".${name}.hosts.master | length " ${server_file})
    echo $count
}

# 获取指定类型服务器下配置的主节点主机
function get_master_host() {
    local name=$1

    local host=$(yq ".${name}.hosts.master" ${server_file})
    echo $host
}

# 获取指定类型服务器下从节点指定位置主机
function get_slave_host() {
    local name=$1
    local index=$2

    local host=$(yq '.'${name}'.hosts.slave['${index}']' ${server_file})
    echo $host
}

# 获取指定类型服务器下配置的主节点ip
function get_master_ip() {
    local host
    host=$(get_master_host "$1")
    local server_ip=""
    if [ "$host" != "null" ] && [ "$host" != "" ];then
        server_ip=$(get_ip_by_host $host)
    fi
    echo $server_ip
}

# 获取指定类型服务器下配置的从节点ip
function get_slave_ip() {
    local host
    host=$(get_slave_host "$1" "$2")
    local server_ip=""
    if [ "$host" != "null" ] && [ "$host" != "" ];then
        server_ip=$(get_ip_by_host $host)
    fi
    echo $server_ip
}

# 判断从节点是否包含指定主机
function has_contain_host() {
    local name=$1
    local host=$2

    local result=$(yq eval '.'${name}'.hosts.slave[] | select(. =="'${host}'") | length >0' ${server_file})
    echo $result
}

# 选择并设置主节点服务器
function choose_and_set_master_host() {
    local choice_index=$1
    local deploy_status_flag=$2
    
    # 验证 choice_index 是否有效
    local is_valid=$(is_valid_choice_index $choice_index)
    if [ "$is_valid" == "false" ]; then
        Echo_Red "错误: 无效的选择索引 '${choice_index}'，请重新选择"
        return 1
    fi
    
    local server_type=$(get_key_by_choice_index $choice_index)
    
    # 再次检查 server_type 是否有效
    if [ -z "$server_type" ]; then
        Echo_Red "错误: 无法获取服务器类型，选择索引 '${choice_index}' 可能无效"
        return 1
    fi
    
    local server_name=$(get_server_name $server_type)
    choose_add_or_deployed_host
    choose_one_host "${server_name//器/}" "SELECT_MASTER_HOST" "single"
    set_master_host ${server_type} ${SELECT_MASTER_HOST}
    set_deployed_status ${server_type} ${deploy_status_flag}
}

# 选择并设置从节点服务器
function choose_and_set_slave_host() {
    local choice_index=$1
    local host_index=$(($2 - 1))

    local server_type=$(get_key_by_choice_index $choice_index)
    local server_name=$(get_server_name $server_type)

    local master_host=$(get_master_host $server_type)
    if [ "$master_host" == "null" ] || [ "$master_host" == "" ];then
        Echo_Red "请先设置${server_name}主节点"
        return 0
    fi

    choose_one_host "${server_name//器/}" "SELECT_SLAVE_HOST" "single"
    while [ "$master_host" == "$SELECT_SLAVE_HOST" ]; do
        Echo_Red "从节点与主节点服务器重复！"
        choose_one_host "${server_name//器/}" "SELECT_SLAVE_HOST" "single"
    done
    if [ $host_index -lt 0 ]; then
        host_index=$(get_slave_node_count $server_type)
    fi
    set_slave_host ${server_type} ${host_index} ${SELECT_SLAVE_HOST}
}

# 验证 choice_index 是否存在于配置文件中
function is_valid_choice_index() {
    local choice_index=$1
    local key=$(yq eval '.[] | select(.choice_index=="'${choice_index}'") | key' ${server_file})
    
    if [ -z "$key" ] || [ "$key" == "null" ]; then
        echo "false"
    else
        echo "true"
    fi
}

# 根据choice_index获取对应key
function get_key_by_choice_index() {
    local choice_index=$1
    local key=$(yq eval '.[] | select(.choice_index=="'${choice_index}'") | key' ${server_file})
    
    if [ -z "$key" ] || [ "$key" == "null" ]; then
        Echo_Red "错误: 无效的选择索引 '${choice_index}'"
        echo ""
    else
        echo $key
    fi
}

# 选择新增或已存在应用的服务器
function choose_add_or_deployed_host() {
    Echo_Yellow "【选择部署的应用，新增或已存在】：0：新增应用，1：应用已存在"
    local input=""
    read -p "请选择: " input
    case ${input} in
    0)
        deploy_status_flag=0
        ;;

    1)
       deploy_status_flag=1
        ;;
    *)
        Echo_Red "输入错误,请重新选择"
        choose_add_or_deployed_host
        ;;
    esac
    echo ${deploy_status_flag}
}

# 获取服务器描述
function get_server_name() {
    local server_type=$1
    local name=$(yq ".${server_type}.name" ${server_file})
    echo $name
}

# 设置主节点服务器
function set_master_host() {
    local key=$1
    local host=$2
    yq -i '.'${key}'.hosts.master="'${host}'"' ${server_file}
}
# 设置部署状态
function set_deployed_status() {
    local key=$1
    local deploy_status_flag=$2
    yq -i '.'${key}'.deploy_status_flag='${deploy_status_flag}'' ${server_file}
}
# 设置从节点服务器
function set_slave_host() {
    local key=$1
    local index=$2
    local host=$3
    yq -i '.'${key}'.hosts.slave['$index']="'${host}'"' ${server_file}
}

# 主节点服务器配置置空
function set_master_host_null() {
    local key=$1
    yq -i '.'${key}'.hosts.master=null' ${server_file}
}

# 从节点服务器配置置空
function set_slave_host_empty() {
    local key=$1
    yq -i '.'${key}'.hosts.slave=[]' ${server_file}
}

# 获取指定类型服务器下要安装的服务数量
function get_modules_count() {
    local name=$1

    local count=$(yq ".${name}.modules | length " ${server_file})
    echo $count
}

# 获取指定类型服务器下要安装的服务
function get_module_value_by_key() {
    local key=$1
    local index=$2
    local name=$3

    local value=$(yq ".${key}.modules[${index}].${name} " ${server_file})
    echo $value
}

# 根据安装的服务类型获取对应key
function get_key_by_module_type() {
    local type=$1
    local sub_type=$2

    local key=""
    if [ "$sub_type" == "null" ] || [ "$sub_type" == "" ]; then
        key=$(yq 'to_entries | map(select(.value.modules[]?.type == "'${type}'")) | .[0].key' ${server_file})
    else
        key=$(yq 'to_entries | map(select(.value.modules[]?.type == "'${type}'" and .value.modules[]?.sub_type == "'${sub_type}'")) | .[0].key' ${server_file})
    fi
    echo $key
}