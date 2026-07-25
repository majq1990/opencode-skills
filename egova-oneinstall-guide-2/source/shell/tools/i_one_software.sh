#!/bin/bash
# 对应主菜单：一站式部署

server_config_file=$1
. ../include/tool_echo.sh
. ../include/tool_hosts.sh
. ../include/tool_multi.sh ${server_config_file}

SERVICE_SELECT_TYPE=""
SERVICE_SELECT_HOST=""

function run_one_install() {
    # 选择一站式部署的节点node
    choose_one_host "${SERVICE_SELECT_TYPE}" "SERVICE_SELECT_HOST" "single"
    echo "待安装主机：${SERVICE_SELECT_HOST}"
    local index=1
    yq '.[] | key ' ${server_config_file} | while read key; do
        # 视频中台不参与一站式部署
        if [[  "${key}" =~ "video" ]]; then
            continue
        fi
        # 配置服务器
        set_master_host $key $SERVICE_SELECT_HOST
        set_slave_host_empty $key
        let "index=index+1"
    done
    # 安装服务
    ./i_common_software.sh ${server_config_file}
}
echo "------------------------------------------------------------------------------------------------------"
echo "开始进行一站式部署"
run_one_install
Echo_Green "一站式部署完成"


