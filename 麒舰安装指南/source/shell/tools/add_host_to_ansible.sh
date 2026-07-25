#!/bin/bash

. ../include/tool_ssh.sh

function get_host_param() {
    params=""
    if [ "${devops_ssh_user}" != "$USER" ]; then
        params="$params ansible_ssh_user=${devops_ssh_user}"
    fi
    if [ "${devops_ssh_port}" != "22" ]; then
        params="$params ansible_ssh_port=${devops_ssh_port}"
    fi

    if [ "${devops_ssh_key}" != "" ] && [ "${devops_ssh_key}" != "/root/.ssh/id_rsa" ]; then
        params="$params ansible_ssh_private_key_file=${devops_ssh_key}"
    fi
}
function add_host_to_ansible() {
    Echo_Yellow "添加服务器："
    read -p "请输入服务器IP: " server_ip
    get_host_param
    add_flag=0
    for i in ${idx_arr[@]}; do
        expr $i + 1 &>/dev/null
        if [ $? -eq 0 ] && [ $i -ge 1 ] && [ $i -lt $idx ]; then
            group_key=${group_array[$i - 1]}
            group_name=${group_name_array[$i - 1]}
            if [ "${group_key}" != "" ]; then
                begin_row=$(cat -n /etc/ansible/hosts | grep "# BEGIN ${group_key}" | awk '{print $1}')
                end_row=$(cat -n /etc/ansible/hosts | grep "# END ${group_key}" | awk '{print $1}')
                if [ "${begin_row}" == "" ] || [ "${end_row}" == "" ]; then
                    continue
                fi
                exist_flag=$(sed -n "${begin_row},${end_row}p" /etc/ansible/hosts | awk '{if($1=="'${server_ip}'")print $1}' | wc -l)
                if [ ${exist_flag} -eq 0 ]; then
                    add_flag=1
                    echo "增加${server_ip}到组【${group_name}】..."
                    sed -i "/END ${group_key}/i\ ${server_ip}$params" /etc/ansible/hosts
                else
                    echo "组【${group_name}】中已存在${server_ip}"
                fi
            fi
        fi
    done
    if [ ${add_flag} -eq 1 ]; then
        Check_SSH_Status ${server_ip} "${devops_ssh_port}" "${devops_ssh_user}" "${devops_ssh_key}"
    fi
}
