#!/bin/bash
# 对应主菜单：轻量化部署

server_config_file=$1
. ../include/tool_echo.sh
. ../include/tool_hosts.sh ${server_config_file}
. ../include/tool_multi.sh ${server_config_file}

TINY_SELECT_HOST=""
function run_tiny_install() {
    # 选择一站式部署的节点node
        choose_one_host "" "TINY_SELECT_HOST" "single"
        echo "待安装主机：${TINY_SELECT_HOST}"
        local index=1
        # 配置服务器
        yq '.[] | select(.tiny_flag == 1) | key ' ${server_config_file} | while read key; do
            set_master_host $key $TINY_SELECT_HOST
            set_slave_host_empty $key
            let "index=index+1"
        done
        yq '.[] | select(.tiny_flag == 0) | key ' ${server_config_file} | while read key; do
            set_master_host_null $key
            set_slave_host_empty $key
        done
        # 安装服务
        ./i_common_software.sh ${server_config_file}
}
echo "------------------------------------------------------------------------------------------------------"
echo "开始进行轻量化部署"
run_tiny_install
Echo_Green "轻量化部署完成"