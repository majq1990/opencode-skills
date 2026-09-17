#!/bin/bash --login

shopt -s expand_aliases

#设置时区为上海时区
timedatectl set-timezone Asia/Shanghai

#禁用apparmor，使得mysql可以自启动成功
systemctl stop apparmor
systemctl disable apparmor

#禁用firewalld，使用ubuntu默认的ufw
which firewall-cmd
FIREWALL_SUCCESS_FLAG=$?
if [ "$FIREWALL_SUCCESS_FLAG" == "0" ]; then
    systemctl stop firewalld
    systemctl disable firewalld
fi


#设置open files
sed -i '/^ulimit -n/d' /etc/profile
echo ulimit -n 1048576 >>/etc/profile
source /etc/profile
sed -i '/^nofile[ ]*[0-9]*$/d' /etc/security/limits.conf
echo "* soft nofile 1048576" >> /etc/security/limits.conf
echo "* hard nofile 1048576" >> /etc/security/limits.conf

sed -i "s/.DefaultLimitNOFILE=.*/DefaultLimitNOFILE=1048576/g" /etc/systemd/system.conf
systemctl daemon-reexec

#设置history
sed -i '/^HISTFILESIZE=[0-9]*/d' /etc/bashrc
sed -i '/^HISTSIZE=[0-9]*/d' /etc/bashrc
echo "HISTFILESIZE=2000" >> /etc/bashrc
echo "HISTSIZE=2000" >> /etc/bashrc

sed -i '/^USER_IP=.*/d' /etc/bashrc
echo "USER_IP=\`who -u am i 2>/dev/null| awk '{print \$NF}'|sed -e 's/[()]//g'\`" >> /etc/bashrc
sed -i '/^export HISTTIMEFORMAT=.*/d' /etc/bashrc
echo "export HISTTIMEFORMAT=\"[%F %T][\`whoami\`][\${USER_IP}]\" " >> /etc/bashrc
sed -i '/^export PROMPT_COMMAND=.*/d' /etc/bashrc
echo "export PROMPT_COMMAND='{ msg=\$(history 1 | { read x y ; echo \$y ;});logger [\`pwd\`]\"\$msg\";}'" >> /etc/bashrc

source /etc/bashrc

cd {{ dest_path }}

## umask
sed -i '/^umask [0-9]*/d' /etc/profile
echo "umask 022" >> /etc/profile
sed -i '/^umask [0-9]*/d' /etc/bashrc
echo "umask 022" >> /etc/bashrc
sed -i '/^umask [0-9]*/d' ~/.bashrc
echo "umask 022" >> ~/.bashrc
source /etc/profile
source /etc/bashrc

echo "GMT+8" > /etc/timezone


#设置tcp_max_tw_buckets
temp_file=/etc/sysctl.conf
grep "net.ipv4.tcp_max_tw_buckets" $temp_file &>/dev/null
if test $? -eq 0;then
    sed -i 's/^net.ipv4.tcp_max_tw_buckets.*/net.ipv4.tcp_max_tw_buckets=5000/'  $temp_file
else
    echo "net.ipv4.tcp_max_tw_buckets=5000" >> $temp_file
fi

grep "net.ipv4.tcp_fin_timeout" $temp_file &>/dev/null
if test $? -eq 0;then
    sed -i 's/^net.ipv4.tcp_fin_timeout.*/net.ipv4.tcp_fin_timeout=5/'  $temp_file
else
    echo "net.ipv4.tcp_fin_timeout=5" >> $temp_file
fi

sysctl -p &> /dev/null

#解决egova用户重启权限问题
file=/usr/share/polkit-1/actions/org.freedesktop.systemd1.policy
cat /etc/org.freedesktop.systemd1.policy > $file