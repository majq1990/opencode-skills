#!/bin/bash

. tool_utils.sh
. ../include/tool_echo.sh

# 要安装的软件包列表,检查依赖关系
apt_special_packages=(dpkg language-pack-zh-hans language-pack-zh-hant mysql-server nmap ncat mysql-client-8.0 libapr1 libaprutil1 libtcnative-1)
yum_special_packages=(openresty java-1.8.0-openjdk apr apr-util iptables)
common_packages=(hostname tar unzip net-tools ntpdate cronolog tcpdump dos2unix telnet ipset curl mydumper percona-xtrabackup-80 redis ansible vim lvm2 python3-jmespath tcpdump parted python3-wheel python3-pip sysbench)
os_special_packages=(mysql-community-server mysql-community-client nmap-ncat mysql-community-client mysql-community-client-plugins tomcat-native)
openeuler_special_packages=(mysql mysql-server mysql-common)
kylin_special_packages=(libtcnative-1-0)
missing_packages=()

is_yum_system() {
    command -v yum >/dev/null 2>&1
}
is_apt_system() {
    command -v apt >/dev/null 2>&1
}

if is_anolis ; then
  common_packages=("${common_packages[@]/ansible/ansible-core}")
fi

# 检查依赖关系(yum)
check_dependencies_yum() {
    for package in "${common_packages[@]}" "${yum_special_packages[@]}" "${os_special_packages[@]}"; do
        echo "检查 $package 的依赖关系..."

        # 尝试检查依赖关系
        check_output=$(yum install --assumeno --allowerasing $package 2>&1)
        if echo "$check_output" | grep -qE "No match for argument|conflicting|Error: Unable to find a match|未找到匹配的参数"; then
            missing_packages+=($package)
        fi
    done
}
# 检查依赖关系 (apt)
check_dependencies_apt() {
    for package in "${common_packages[@]}" "${apt_special_packages[@]}"; do
        echo "检查 $package 的依赖关系"

        # 尝试检查依赖关系
        check_output=$(apt-get install --assume-no $package 2>&1)
        if echo "$check_output" | grep -q "Unable to locate package"; then
            missing_packages+=($package)
        fi
    done
}

# 检查依赖关系 (openeuler)
check_dependencies_openeuler() {
    for package in "${common_packages[@]}" "${yum_special_packages[@]}" "${openeuler_special_packages[@]}"; do
        echo "检查 $package 的依赖关系"

        # 尝试检查依赖关系
        check_output=$(yum install --assumeno --allowerasing $package 2>&1)
        if echo "$check_output" | grep -qE "No match for argument|conflicting|Error: Unable to find a match|未找到匹配的参数"; then
            missing_packages+=($package)
        fi
    done
}
# 检查依赖关系 (kylin)
check_dependencies_kylin() {
    for package in "${common_packages[@]}" "${yum_special_packages[@]}" "${kylin_special_packages[@]}"; do
        echo "检查 $package 的依赖关系"

        # 尝试检查依赖关系
        check_output=$(yum install --assumeno --allowerasing $package 2>&1)
        if echo "$check_output" | grep -qE "No match for argument|conflicting|Error: Unable to find a match|未找到匹配的参数"; then
            missing_packages+=($package)
        fi
    done
}
# 检查依赖关系
check_dependencies(){
    if is_openEuler; then
        check_dependencies_openeuler
    elif is_kylin; then
        check_dependencies_kylin
    elif is_yum_system; then
        check_dependencies_yum
    elif is_apt_system; then
        check_dependencies_apt
    else
        echo "不支持的包管理工具。"
        exit 1
    fi

   if [ ${#missing_packages[@]} -ne 0 ]; then
       Echo_Red "以下软件包无法安装，可能缺少依赖或包不存在。脚本将强制退出！！！"
       for package in "${missing_packages[@]}"; do
           echo "$package"
       done
       exit 1
   fi
}

# check_dependencies $@
