#!/bin/bash

cached_distribution_info=""

function get_local_ip() {
    list=$(ip link | grep ^[0-9] | awk -F: '{print $2}')
    i=0
    for e in $list; do
        ip=$(ifconfig $e | grep inet | grep -v inet6 | grep -v 127.0.0.1 | awk '{for(i=1;i<NF;i++){if($i=="inet"){print $(i+1)}}}' | awk -F: '{print $NF}')
        if [ "$ip" != "" ]; then
            ((i++))
            eth_array[i]=$e
            ip_array[i]=$ip
            LOCAL_IP=$ip
        fi
    done

    if [ "$i" == "1" ]; then
        Echo_Green "本地网卡IP为$LOCAL_IP"
    else
        while true; do
            echo "本机eth*网卡IP列表："
            i=0
            for e in ${eth_array[@]}; do
                ((i++))
                echo "$i: $e ${ip_array[$i]}"
            done
            read -p "请选择: " Select

            if [ $Select -ge 1 ] && [ $Select -le $i ]; then
                ip=$(eval echo \${ip_array[$Select]})
                Echo_Green "你选择的网卡IP是$ip"
                LOCAL_IP=$ip
                break
            else
                Echo_Red "你的选择无效"
            fi
        done
    fi
}

##获取系统版本信息
function get_distribution_info() {
    ##缓存版本信息
    if [ -n "$cached_distribution_info" ]; then
          echo "$cached_distribution_info"
          return 0
    fi
    if [ -f /etc/os-release ]; then
        source /etc/os-release

        if [ -n "$ID" ]; then
            # 检查centos版本
            if [ -n "$VERSION_ID" ]; then
                version=$(echo $VERSION_ID | cut -d'.' -f1)
            else
                # 检查Ubuntu版本
                if [ -n "$UBUNTU_CODENAME" ]; then
                    version=$(lsb_release -rs | cut -d. -f1)
                fi
            fi
            if [ "$(uname -m)" == "x86_64" ]; then
              arch=$(echo "x86")
            else
              arch=$(echo "arm")
            fi
            cached_distribution_info="$ID"_"$version"_"$arch"
            echo "$cached_distribution_info"
            return 0
        fi
    fi
    return 1
}
##检查版本
function check_distribution() {
    local distribution=$1

    if [[ "$(get_distribution_info)" =~ ($distribution) ]]; then
        echo "操作系统：$(get_distribution_info)"
        return 0
    fi
    return 1
}
function is_kylin() {
   check_distribution "kylin"
}
function is_openEuler() {
     check_distribution "openEuler"
}
function is_ubuntu() {
   check_distribution "ubuntu"
}
function is_centos() {
   check_distribution "centos"
}
function is_uos() {
   check_distribution "uos"
}
function is_anolis() {
   check_distribution "anolis"
}
