#!/bin/bash --login

shopt -s expand_aliases

# 加锁重要文件
function lock_important_files() {
    #    sudo -u#0 chattr +i /etc/gshadow
    #    sudo -u#0 chattr +i /etc/group
    #    sudo -u#0 chattr +i /etc/shadow
    #    sudo -u#0 chattr +i /etc/passwd
    echo 0 >>/dev/null
}

# 解锁重要文件
function unlock_important_files() {
    sudo -u#0 chattr -i /etc/gshadow
    sudo -u#0 chattr -i /etc/group
    sudo -u#0 chattr -i /etc/shadow
    sudo -u#0 chattr -i /etc/passwd
}
