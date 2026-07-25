#!/bin/bash

. ../include/tool_ssh.sh
. fix_hostname.sh
. ../include/tool_echo.sh

function set_ssh_nopass() {
    Echo_Yellow "set ssh nopass"
    host=$1
    port=$2
    Check_SSH_Status $host "${port}" "${devops_ssh_user}" "${devops_ssh_key}"
    host_name="cg"$( echo $host | awk -F '.' '{print $NF}')
    if [[ $(cat /etc/ansible/hosts |grep ${host} |wc -l) -eq 0  ]]; then
      echo "$host ansible_ssh_port=${port}" >>/etc/ansible/hosts
    fi
    run_fix_hostname "remote" $host "${port}" "${devops_ssh_user}" "${devops_ssh_key}" ${host_name}
}
