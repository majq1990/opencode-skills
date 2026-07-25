#!/bin/bash

# hosts.yml
hosts_file=../../ansible/inventory/hosts.yml
global_conf=../../ansible/group_vars/all.yml

. ../include/tool_echo.sh
. ../tools/tool_utils.sh

declare -A index_map
# 显示已添加的所有节点
function display_all_hosts() {
    # 从hosts.yml文件中遍历
    local count=$(yq '.all.hosts | length ' ${hosts_file})
    if [ $count -eq 0 ]; then
#          Echo_Yellow "当前无可删除服务器，请新增服务器："
         return 0
    else
        local index=1
        local hosts=($(yq '.all.hosts | keys | .[]' ${hosts_file}))
        local host
        for host in "${hosts[@]}"; do
            ip=$(yq '.all.hosts.'${host}'.ansible_ssh_host' ${hosts_file})
            echo "$index: $host   $ip"
            index_map[$index]=$host
            let "index=index+1"
        done
        return 1
    fi
}

# 通过host从hosts.yml中获取ip
function get_ip_by_host() {
    local host=$1

    local ip=$(yq '.all.hosts.'${host}'.ansible_ssh_host' ${hosts_file})
    echo $ip
}

# 通过ip从hosts.yml中获取host
function get_host_by_ip() {
    local server_ip=$1

    local host=$(yq '.all.hosts | to_entries | .[] | select(.value.ansible_ssh_host == "'${server_ip}'") | .key' ${hosts_file})
    echo $host
}

function check_hosts_exists() {
    local ip=$1
    local count=$(cat ${hosts_file} 2>/dev/null | yq '.all.hosts.[].ansible_ssh_host' | grep -w "${ip}" | wc -l)
    if [ $count -gt 0 ]; then
        Echo_Red "ip=$ip的主机已存在,无需添加"
        return 1
    else
        return 0
    fi
}
# add a host to hosts.yml
function add_host() {
    local ip=$1
    # 考虑为空的情况
    local ssh_port=$2

    local count=$(yq '.all.hosts | length ' ${hosts_file})
    let "size=count+1"

    # 检查节点是否存在，如果存在则size++
    while yq -e '.all.hosts.node'${size}'' ${hosts_file} >/dev/null 2>&1; do
        ((size++))
    done

    #local ssh_port=$(yq '.devops_ssh_port' ${global_conf})
    yq -i '.all.hosts.node'${size}'.ansible_ssh_host = "'$ip'"' ${hosts_file}
    yq -i '.all.hosts.node'${size}'.ansible_ssh_port = "'$ssh_port'"' ${hosts_file}

    # 新增节点后，需要重新生成ini文件
    # yml_to_ini
    # 备份一份到/etc/
    \cp -f ${hosts_file} /etc/
}

# convert to yml to ini
function yml_to_ini() {

    # 除了all分组，其他mysql/redis分组也需要处理
    echo "# host list" >${hosts_file}.ini
    yq '. | keys | .[]' ${hosts_file} | while read key; do
        # node1 ansible_ssh_host=192.168.0.10
        # 校验是否为空
        check=$(yq '.'$key' | length ' ${hosts_file})
        if [ $check -gt 0 ]; then
            echo "[$key]" >>${hosts_file}.ini
            yq '.'$key' | keys | .[] ' ${hosts_file} | while read sub_key; do
                if [ $key == "all" ]; then
                    ip=$(yq '.all.'${sub_key}'.ansible_ssh_host' ${hosts_file})
                    ssh_port=$(yq '.devops_ssh_port' ${global_conf})
                    echo "$sub_key ansible_ssh_host=${ip} ansible_ssh_port=${ssh_port}" >>${hosts_file}.ini
                else
                    # mysql、linglong等
                    echo "${sub_key}" >>${hosts_file}.ini
                fi
            done
        fi
    done

}

# update a group
function update_host_group() {
    local host_type=$1
    local host_idxes=$2
    local array=($(echo ${host_idxes} | sed 's/,/ /g'))
    for idx in ${array[@]}; do
        host=$(yq '.all.hosts | keys | .['$(($idx - 1))']' ${hosts_file})
        yq -i '.all.children.'$host_type'.'$host'=""' ${hosts_file}
    done
    #yml_to_ini
}

function save_app_to_hostfile() {
    type=$1
    host=$2
    yq -i '.all.children.'$type'.hosts.'$host'=""' ${hosts_file}
}

# 保存hosts
function save_app_hosts() {
    local type=$1
    local host=$2

    save_app_to_hostfile $type $host
}

# 选择新增或修改服务器
function choose_add_or_delete_hosts() {
    display_all_hosts
    Echo_Yellow "【请选择操作】：0：添加服务器(执行免密),a：增加IP地址（rds场景，不执行免密），1：刪除服务器"
      local input=""
      read -p "请选择：" input
      case ${input} in
      0)
          add_a_server
          ;;
      1)
         display_all_hosts
         if [ $? -eq 0 ]; then
            Echo_Yellow "当前无可删除服务器，请新增服务器："
            add_a_server
            return 1
         fi
         read -p "请选择对应服务器: " selected_index
         local server_host=$(get_ip_by_index $selected_index)
         delete_server_host ${server_host}
          ;;
     a)
        add_server_IP
        ;;
      *)
          Echo_Red "输入错误,请重新选择"
          choose_add_or_delete_hosts
          ;;
      esac

}

function add_server_IP() {
    read -p "请输入服务器IP: " server_ip
    # 检查ip是否合法
    [[ ${server_ip} =~ ^(2(5[0-5]{1}|[0-4][0-9]{1})|[0-1]?[0-9]{1,2})(\.(2(5[0-5]{1}|[0-4][0-9]{1})|[0-1]?[0-9]{1,2})){3}$ ]] || {
        Echo_Red "[ERROR] IP地址不合法!"
        return 1
    }

    # 检查ip是否已经存在
    check_hosts_exists ${server_ip}
    if [ $? -gt 0 ]; then
        return 1
    fi
    local common_port=$(yq '.devops_ssh_port' ${global_conf})
    #不输入端口号就使用all.yaml中的端口，输入则就使用输入的
    read -p "请输入服务器ssh端口（若为${common_port}可直接回车）: " port
    if [ "$port" = "" ];then
        local server_port=$common_port
    elif grep '^[[:digit:]]*$' <<< "$port";then
        local server_port=${port}
    else
        Echo_Red "[ERROR] SSH端口号不合法!"
        return 1
    fi
    cd ../tools
    # 增加主机
    add_host $server_ip $server_port
    Echo_Yellow "当前已添加的服务器如下: "
    display_all_hosts
    cd ../include
}

# 新增服务器
function add_a_server() {
    read -p "请输入服务器IP: " server_ip
    # 检查ip是否合法
    [[ ${server_ip} =~ ^(2(5[0-5]{1}|[0-4][0-9]{1})|[0-1]?[0-9]{1,2})(\.(2(5[0-5]{1}|[0-4][0-9]{1})|[0-1]?[0-9]{1,2})){3}$ ]] || {
        Echo_Red "[ERROR] IP地址不合法!"
        return 1
    }

    # 检查ip是否已经存在
    check_hosts_exists ${server_ip}
    if [ $? -gt 0 ]; then
        return 1
    fi
    local common_port=$(yq '.devops_ssh_port' ${global_conf})
    #不输入端口号就使用all.yaml中的端口，输入则就使用输入的
    read -p "请输入服务器ssh端口（若为${common_port}可直接回车）: " port
    if [ "$port" = "" ];then
        local server_port=$common_port
    elif grep '^[[:digit:]]*$' <<< "$port";then
        local server_port=${port}
    else
        Echo_Red "[ERROR] SSH端口号不合法!"
        return 1
    fi
    cd ../tools
    # TODO: 添加服务器后，是否自动配置免密
    Echo_Yellow "开始配置SSH免密"
    . set_ssh_login_nopass.sh
    set_ssh_nopass $server_ip $server_port
    # 增加主机
    add_host $server_ip $server_port
    scp -P $server_port /etc/os-release root@$server_ip:/etc/os-release
    local_ip=$(yq '.ansible_master_ip' ${global_conf})
    if is_ubuntu; then
         scp -P $server_port /etc/apt/sources.list root@$server_ip:/etc/apt/sources.list
    else
       if [ "$local_ip" != "$server_ip" ]; then
          ssh -p$server_port root@$server_ip 'mkdir -p /etc/yum.repos.d/backup && mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/backup'
       fi
       scp -P $server_port /etc/yum.repos.d/egova-oneinstall-local.repo root@$server_ip:/etc/yum.repos.d/
    fi
    scp -P $server_port ../include/automount.sh root@$server_ip:/root
    ssh -p$server_port root@$server_ip 'bash /root/automount.sh'
    Echo_Yellow "当前已添加的服务器如下: "
    display_all_hosts
    cd ../include
}
function get_ip_by_index() {
    local host_index=$1
    if [ -n "${index_map[$host_index]}" ]; then
        selected_host=${index_map[$host_index]}
        echo "$selected_host"
    else
        echo "无效的索引号"
    fi
}
function delete_server_host() {
    local server_host=$1
    yq -i "del(.all.hosts.\"${server_host}\")" $hosts_file
    Echo_Green "$server_host 已刪除"
}

# 选择一个或者多个节点
function choose_one_host() {
    # 要部署的应用类型
    local type=$1
    # 要部署的应用名称，解决多个终端同时部署会导致配置冲突的场景，目前只有微服务用到。
    local rst=$2
    # mode为选择模式，不传就默认多选
    if [ $# -eq 2 ];then
        mode=multi
    else
        mode=$3
    fi
    if [ $mode == "multi" ];then
        Echo_Yellow "选择需要部署${type}的服务器(多个以逗号分隔):"
    else
        Echo_Yellow "选择需要部署${type}的服务器:"
    fi
    display_all_hosts
    echo "a: 新增服务器"
    echo "q: 退出"
    local input=""
    read -p "请输入: " input
    case $input in
    [0-9]*)

        local array=($(echo ${input} | sed 's/,/ /g;s/，/ /g'))
        local host=""
        for a_idx in ${array[@]}; do
            local cur_host="$(yq '.all.hosts | keys | .['$((${a_idx} - 1))']' ${hosts_file})"
            if [ "${cur_host}" != "null" ]; then
                host="${host},${cur_host}"
            fi
        done
        host=$(echo ${host} | sed "s/^,//g")
        #校验输入
        if [ "${host}" == "" ]; then
            Echo_Red "选择错误，未匹配到服务器"
            choose_one_host $type $rst $mode
        else
            #设置返回值
            eval "${rst}=${host}"
        fi
        ;;
    q | Q)
        Echo_Yellow "退出安装${type}"
        exit 0
        ;;
    a)
        add_a_server
        choose_one_host $type $rst $mode
        ;;
    *)
        Echo_Red "输入错误"
        choose_one_host $type $rst $mode
        ;;
    esac
}