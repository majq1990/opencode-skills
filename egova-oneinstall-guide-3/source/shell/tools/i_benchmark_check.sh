#!/bin/bash

# 对应主菜单：安装软件的工具箱

INSPECT_PERFORMANCE_FILE=../../ansible/benchmark_check.yml
hosts_file=../../ansible/inventory/hosts.yml

. ../include/tool_echo.sh
function input_redis_connection(){
    echo "请输入redis连接信息"
    read -p "请输入redis ip: " redis_ip
    read -p "请输入redis port: " redis_port
    read -p "请输入redis password: " redis_password

}
function run() {
   Echo_Yellow "-----开始基准检查-----"
   input_redis_connection
   ansible-playbook -i $hosts_file  -e "host=all redis_ip=${redis_ip} redis_port=${redis_port} redis_password=${redis_password}" ${INSPECT_PERFORMANCE_FILE}
   Echo_Yellow "-----基准检查结束-----"
}

run