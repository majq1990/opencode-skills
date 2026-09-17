#!/bin/bash

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
