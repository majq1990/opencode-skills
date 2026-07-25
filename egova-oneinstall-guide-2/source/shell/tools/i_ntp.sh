#!/bin/bash

.  tool_utils.sh

Install_Ntp_Server()
{
    local lock_file="/egova/conf/install/time-sync"
    local ntp_installed=false
    local chrony_installed=false

    # 检查是否已经安装过
    if test -e $lock_file ; then
        echo "Time synchronization is already installed."
        return
    fi

    # 尝试安装NTP
    echo "Attempting to install NTP..."
    if yum install -y ntp > /dev/null 2>&1; then
        echo "NTP installed successfully."
        ntp_installed=true
    else
        echo "NTP installation failed. Attempting to install Chrony..."
        # 如果NTP安装失败，则尝试安装Chrony
        if yum install -y chrony > /dev/null 2>&1; then
            echo "Chrony installed successfully."
            chrony_installed=true
        else
            echo "Chrony installation failed. Please check your network and repository configurations."
            return 1
        fi
    fi

    # 配置NTP或Chrony
    if $ntp_installed; then
        echo "Configuring NTP..."
        if ! test -d /egova/conf/install; then
            mkdir -p /egova/conf/install
        fi
        # 假设你的ntp.conf模板路径
        if [ -f "../template/ntp.conf" ]; then
            sudo -u#0 cp -f ../template/ntp.conf /etc/
        else
            echo "Warning: ../template/ntp.conf not found. Using default NTP configuration."
        fi

        # 移除系统对 /etc/gshadow, /etc/group, /etc/shadow, /etc/passwd 的immutable属性
        # 这部分操作需要谨慎，确保你理解其风险
        sudo -u#0 chattr -i /etc/gshadow > /dev/null 2>&1
        sudo -u#0 chattr -i /etc/group > /dev/null 2>&1
        sudo -u#0 chattr -i /etc/shadow > /dev/null 2>&1
        sudo -u#0 chattr -i /etc/passwd > /dev/null 2>&1

        # 创建ntp用户和组（如果不存在）
        if ! getent group ntp > /dev/null 2>&1; then
            groupadd ntp
        fi
        if ! getent passwd ntp > /dev/null 2>&1; then
            useradd -M -s /sbin/nologin -g ntp ntp
        fi

        # 确保/var/log/ntpstats目录存在并设置权限
        if ! test -d /var/log/ntpstats; then
            mkdir -p /var/log/ntpstats
        fi
        chown -R ntp:ntp /var/log/ntpstats

        # 启动并启用NTP服务
        sudo -u#0 systemctl start ntpd
        sudo -u#0 systemctl enable ntpd
        echo "NTP configuration complete."

    elif $chrony_installed; then
        echo "Configuring Chrony..."
        if ! test -d /egova/conf/install; then
            mkdir -p /egova/conf/install
        fi
        # 假设你的chrony.conf模板路径
        if [ -f "../template/chrony.conf" ]; then
            sudo -u#0 cp -f ../template/chrony.conf /etc/
        else
            echo "Warning: ../template/chrony.conf not found. Using default Chrony configuration."
        fi

        # 启动并启用Chrony服务
        sudo -u#0 systemctl start chronyd
        sudo -u#0 systemctl enable chronyd
        echo "Chrony configuration complete."
    fi

    # 创建锁文件
    sudo -u#0 touch $lock_file
    echo "Time synchronization setup finished."
}

# 新建存储ntp认证密钥和密码的文件，确保NTP服务器和客户端之间的通信的完整性和身份验证
if is_ubuntu ; then
    apt install -y ntp
    mkdir -p /etc/ntp/crypto
    touch /etc/ntp/crypto/pw
    chmod 644 /etc/ntp/crypto/pw
    sudo -u#0 chattr -i /etc/gshadow
    sudo -u#0 chattr -i /etc/group
    sudo -u#0 chattr -i /etc/shadow
    sudo -u#0 chattr -i /etc/passwd
    groupadd ntp
    useradd -M -s /sbin/nologin -g ntp ntp
    chown ntp:ntp /etc/ntp/crypto/pw
    # 修改配置文件
    \cp -f ../template/ntp.conf /etc/.
    systemctl start ntp
    systemctl enable ntp
else
  Install_Ntp_Server
fi
