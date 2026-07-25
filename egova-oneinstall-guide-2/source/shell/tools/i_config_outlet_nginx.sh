#!/bin/bash
# 对应主菜单：101 出口nginx配置

metadata_file=../../ansible/inventory/metadata.yml
ms_template_file=../template/microservice_template.yml
hosts_file=../../ansible/inventory/hosts.yml

. ../include/tool_echo.sh

# 选择微服务
function choose_ms_type() {
    Echo_Yellow "选择需要配置出口nginx的微服务:"
    local microservice_types=$(yq '.[] | key ' ${ms_template_file})
    local ms_type_arr=(${microservice_types})
    local index=1
    yq '.[] | key ' ${ms_template_file} | while read key; do
        local name=$(yq ".${key}.name" ${ms_template_file})
        echo "${index}: $name"
        let "index=index+1"
    done
    echo "q: 退出"
    read -p "请输入:" select
    case $select in
    [0-9]*)
        MS_SELECT_TYPE=${ms_type_arr[$select-1]}
        ;;
    q)
        echo "退出安装"
        exit 0
        ;;
    *)
        Echo_Red "输入错误"
        choose_ms_type

    esac
}

# 选择出口nginx节点
function choose_outlet_nginx_host() {
    cd ../include
    . tool_hosts.sh
    # . tool_metadata.sh
    choose_one_host "出口nginx" "OUTLET_NGINX_HOST" "single"
    cd ../tools
}


function run(){
    MS_SELECT_TYPE=""
    OUTLET_NGINX_HOST=""

    choose_ms_type
    choose_outlet_nginx_host

    #Echo_Yellow "要配置出口nginx的微服务为: ${MS_SELECT_TYPE}, 出口nginx的节点: ${OUTLET_NGINX_HOST}"
    # deploy
    Echo_Yellow "开始配置出口nginx"
    local keys=($(yq '.microservice.'${MS_SELECT_TYPE}'.[] | select(.status=="success" and .host != "none") | key ' ${metadata_file}))
    if [ ${#keys[@]} -ne 0 ]; then
        app_name=${keys[0]}
    fi
    ansible-playbook -i $hosts_file -e "app_type=${MS_SELECT_TYPE} app_name=${app_name} host=${OUTLET_NGINX_HOST}" ../../ansible/config_outlet_nginx.yml
    Echo_Yellow "ansible执行日志见/var/log/ansible.log"
}
run
