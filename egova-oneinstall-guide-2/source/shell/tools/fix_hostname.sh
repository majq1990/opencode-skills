#!/bin/bash

SSH_PORT=22
SSH_USER=root

hosts_file=../../ansible/inventory/hosts.yml

function fix_ubuntu20() {
    local name
    name=$(hostname)
    Echo_Green "当前hostname为:$name"
    echo "127.0.0.1 $1" >>/etc/hosts
    echo "::1 $1" >>/etc/hosts
    hostnamectl set-hostname $1
    Echo_Green "修复后：$(hostnamectl | grep hostname)"
}

function fix_one_server() {
     hostnamectl -h >/dev/null 2>&1
     local cmd_check=$?
     if [ $cmd_check -eq 0 ]; then
         fix_ubuntu20 $1
     else
         Echo_Red "ERROR:缺少hostnamectl 请手动检查"
     fi
}
function run_fix_hostname() {
    Echo_Yellow "run fix hostname"
    if [ "$1" == "one" ]; then
        fix_one_server $6
    else
        if [ "$1" == "remote" ]; then
            s_ip=$2
            _SSH_PORT=$3
            _SSH_USER=$4
            SSH_KEY="$5"
            if [ "$_SSH_USER" == "" ]; then
                _SSH_USER=root
            fi
            key_param=""
            if [ "$SSH_KEY" != "" ]; then
                key_param="-i $SSH_KEY"
            fi
            ssh ${key_param} -p ${_SSH_PORT} ${_SSH_USER}@${s_ip} "echo '::1 $6' >> /etc/hosts && echo '127.0.0.1 $6' >> /etc/hosts && echo '${s_ip} $6' >> /etc/hosts && hostnamectl set-hostname $6"
            return 0
        fi
        if test -e ${hosts_file}; then
            Echo_Yellow "检测到hosts文件，将根据此配置依次修复所有服务器"
            yq ".all.hosts.[].ansible_ssh_host" ${hosts_file} | while read host; do
                echo "----------------------------------"
                ip=$(echo $host | sed s/\"//g)
                Echo_Green "修复$ip"
                # TODO: 此处SSH用户和端口获取方式需要优化。
                ssh -p $SSH_PORT $SSH_USER@$ip "echo '::1 $6' >> /etc/hosts && echo '127.0.0.1 $6' >> /etc/hosts && echo '${ip} $6' >> /etc/hosts && hostnamectl set-hostname $6"
            done
        else
            fix_one_server $6
        fi
    fi
}
