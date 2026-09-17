#!/bin/bash
#SSH_PORT=22
devops_ssh_user=root
devops_ssh_port=22

Safe_Easy_SSH() {
    #$1 待连接客户端IP

    if test ! -e "/root/.ssh/id_ed25519"; then
        ssh-keygen -t ed25519 -P "" -f /root/.ssh/id_ed25519
    fi

    if test ! -e "/egova/conf/ssh_$1.status"; then
        #ssh-copy-id -i /root/.ssh/id_ed25519 $1
        if [ $(command -V ssh-copy-id | wc -L) -le 0 ]; then
            rsa=$(cat /root/.ssh/id_ed25519.pub)
            ssh -p $SSH_PORT root@$1 "echo $rsa >> /root/.ssh/authorized_keys ; chmod 600 /root/.ssh/authorized_keys;"
            ssh -p $SSH_PORT root@$1 "sed -i 's/^#*UseDNS.*/UseDNS no/' /etc/ssh/sshd_config ; systemctl restart sshd;"
            SSH_SUCCESS_FLAG=$?
        else
            ssh-copy-id -h 2>temp.txt
            if [ $(cat temp.txt | grep "\[-p port\]" | wc -l) -eq 1 ]; then
                ssh-copy-id -i /root/.ssh/id_ed25519 -p $SSH_PORT $1
            else
                ssh-copy-id -i /root/.ssh/id_ed25519 "-p $SSH_PORT $1"
            fi
            SSH_SUCCESS_FLAG=$?
            rm -rf temp.txt
        fi
        if [ "$SSH_SUCCESS_FLAG" == "0" ]; then
            ssh -p $SSH_PORT -o "StrictHostKeyChecking no" root@$1 " echo \$(hostname) 免密成功"
            mkdir -p /egova/conf
            echo ok >>"/egova/conf/ssh_$1.status"
            echo "设置免密码登录$1成功。"
        else
            rm -rf temp.txt
            echo "设置免密码登录$1失败。"
            return 1
        fi
    fi
    return 0
}
# 本机免密ssh ,一键监控脚本需要
Safe_Easy_SSH_Local() {
    if test ! -e "/root/.ssh/id_ed25519"; then
        ssh-keygen -t ed25519 -P "" -f /root/.ssh/id_ed25519
    fi

    if test ! -e "/egova/conf/ssh_localhost.status"; then
        cat /root/.ssh/id_ed25519.pub >>/root/.ssh/authorized_keys
        chmod 600 /root/.ssh/authorized_keys
        ssh -p $SSH_PORT -o "StrictHostKeyChecking no" root@127.0.0.1 " echo \$(hostname) 免密成功"
    fi
}
# 在当前服务器上，生成SERVER1到SERVER2的免密登录
# 前置条件，当前服务器可免密登录到SERVER1和SERVER2
Safe_Easy_SSH_Remote() {
    from_server=$1
    to_server=$2
    # 检查是否能免密登录
    if [ $(cat /root/.ssh/known_hosts | grep -E "$from_server |$from_server," | wc -l) -lt 1 ]; then
        echo "需要先设置免密登录${from_server}"
        Safe_Easy_SSH $from_server
        if [ "$?" == "1" ]; then
            return 1
        fi
    fi
    if [ $(cat /root/.ssh/known_hosts | grep -E "$to_server |$to_server," | wc -l) -lt 1 ]; then
        echo "需要先设置免密登录${to_server}"
        Safe_Easy_SSH $to_server
        if [ "$?" == "1" ]; then
            return 1
        fi
    fi

    ssh -p $SSH_PORT root@${from_server} "if [ $(cat /root/.ssh/known_hosts | grep -E \"$to_server \|$to_server,\" | wc -l) -eq 0 ];then exit 1; else exit 0; fi"
    if [ "$?" == "1" ]; then
        # 未免密登录
        # 首先SERVER1生成rsa,拉到本地，写入到SERVER2
        ssh -p $SSH_PORT root@${from_server} "if [ ! -e /root/.ssh/id_ed25519.pub ] || [ ! -e /root/.ssh/id_ed25519 ];then ssh-keygen -t ed25519 -P \"\" -f /root/.ssh/id_ed25519 ;fi " >/dev/null
        scp -P $SSH_PORT root@${from_server}:/root/.ssh/id_ed25519.pub /egova/conf/id_ed25519_${from_server} >/dev/null
        rsa=$(cat /egova/conf/id_ed25519_${from_server})
        if [ "$rsa" == "" ]; then
            return 1
        fi
        ssh -p $SSH_PORT root@${to_server} "echo $rsa >> /root/.ssh/authorized_keys ; chmod 600 /root/.ssh/authorized_keys;"
        # 尝试执行
        ssh -p $SSH_PORT root@$from_server " ssh -p $SSH_PORT -o \"StrictHostKeyChecking no\" root@$to_server  \"echo 从 $from_server 到$to_server \\\$(hostname) 免密成功\" "
        if [ "$?" == "1" ]; then
            return 1
        fi
        mkdir -p /egova/conf
        ssh -p $SSH_PORT root@${from_server} " echo ok >> /egova/conf/ssh_${to_server}.status"
        return 0
    else
        echo 服务器${from_server}已经设置免密登录到${to_server}！
        return 0
    fi

}

Safe_Easy_SSH_V2() {
    #$1 待连接客户端IP
    if [ "$SSH_USER" == "" ]; then
        SSH_USER=root
    fi
    if [ "$SSH_KEY" == "" ]; then
        SSH_KEY="/root/.ssh/id_ed25519"
    fi
    if test ! -e "$SSH_KEY"; then
        ssh-keygen -t ed25519 -P "" -f $SSH_KEY
    fi
    #ssh-copy-id -i /root/.ssh/id_ed25519 $1
    if [ $(command -V ssh-copy-id | wc -L) -le 0 ]; then
        if test ! -e ${SSH_KEY}.pub; then
            echo "找不到命令ssh-copy-id,而且不存在${SSH_KEY}.pub"
            SSH_SUCCESS_FLAG=1
        else
            rsa=$(cat ${SSH_KEY}.pub)
            ssh -i $SSH_KEY -p $SSH_PORT ${SSH_USER}@$1 "echo $rsa >> /${SSH_USER}/.ssh/authorized_keys ; chmod 600 /${SSH_USER}/.ssh/authorized_keys;" 2>/dev/null
            SSH_SUCCESS_FLAG=$?
        fi
    else
        ssh-copy-id -h 2>temp.txt
        if [ $(cat temp.txt | grep "\[-p port\]" | wc -l) -eq 1 ]; then
            ssh-copy-id -i ${SSH_KEY} -p $SSH_PORT $1
        else
            ssh-copy-id -i ${SSH_KEY} "-p $SSH_PORT $1"
        fi
        SSH_SUCCESS_FLAG=$?
        rm -rf temp.txt
    fi
    if [ "$SSH_SUCCESS_FLAG" == "0" ]; then
        ssh -i $SSH_KEY -p $SSH_PORT -o "StrictHostKeyChecking no" ${SSH_USER}@$1 " echo \$(hostname) 免密成功" 2>/dev/null
        mkdir -p /egova/conf
        echo ok >>"/egova/conf/ssh_$1.status"
        echo "设置免密码登录$1成功。"
    else
        rm -rf temp.txt
        echo "设置免密码登录$1失败。"
        return 1
    fi
}

function Check_SSH_Status() {
    s=$1
    SSH_PORT=$2
    SSH_USER=$3
    SSH_KEY="$4"
    if [ "$SSH_USER" == "" ]; then
        SSH_USER=root
    fi
    if [ "$SSH_KEY" == "" ]; then
        SSH_KEY="/root/.ssh/id_ed25519"
    fi
    if [ -e "$SSH_KEY" ] && [ "$SSH_KEY" != "/root/.ssh/id_ed25519" ]; then
        Echo_Yellow "尝试使用配置的SSH_KEY登录远程服务器,如果提示输入密码,请直接敲击Ctrl+C终止执行(如果有远程服务器密码，请不要配置SSH_KEY。如果没有密码，请向管理员索取可用的唯一密钥)"
        ssh -i $SSH_KEY -p $SSH_PORT ${SSH_USER}@$s "echo 1>/dev/null" 2>/dev/null
        if [ $? != 0 ]; then
            Echo_Red "$s 使用配置的$SSH_KEY无法成功登录"
            exit 1
        else
            Echo_Green "$s 设置免密登录成功 "
        fi
    else
        SSH_KEY=/root/.ssh/id_ed25519
        Safe_Easy_SSH_V2 $s
        if [ $? != 0 ]; then
            Echo_Red "$s 无法SSH成功"
            exit 1
        fi
        ssh -i $SSH_KEY -p $SSH_PORT ${SSH_USER}@$s "echo 1>/dev/null" 2>/dev/null
        if [ $? != 0 ]; then
            Echo_Red "$s 无法SSH成功"
            exit 1
        fi
    fi
}