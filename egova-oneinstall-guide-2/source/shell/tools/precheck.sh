#!/bin/bash

# 1、服务器间网络达到500M;
# 2、td、数据库的服务器，磁盘IO最低不低于100M/s（区县），一般比低于300M/s（一般地市），最好不低于500M/s（中心城市或市区一体化项目）
# 3、服务器的基础CPU和内存检查（数据库不低于8U32G的底线）

set -e

check_iperf3_installed() {
    if ! command -v iperf3 &> /dev/null; then
        echo "iperf3 未安装，请先安装 iperf3。"
        return 1
    fi
    return 0
}

# 网络带宽检查
check_network_speed() {
    local server_ip=$1
    local total_speed=0
    local count=5

    check_iperf3_installed || return 1
    if ! ssh "$server_ip" "command -v iperf3 &> /dev/null"; then
        echo "目标服务器 $server_ip 未安装 iperf3，请先安装 iperf3。"
        return 1
    fi
    ssh "$server_ip" 'pgrep iperf3 > /dev/null'
    if [ $? -ne 0 ]; then
       ssh "$server_ip" "iperf3 -s -D"
    fi
    for i in $(seq 1 $count); do
        echo "第 $i 次测试..."
        # 本机作为客户端进行带宽测试，提取发送方带宽值
        local speed=$(iperf3 -c "$server_ip" -f M | grep -oP '\d+(\.\d+)?(?= MBytes/sec)' | tail -n1)
        if [[ -z "$speed" ]]; then
            echo "无法检测到网络带宽，请检查网络配置。"
        fi
        # 将带宽值转换为 Mbits/sec（1 MBytes = 8 Mbits）
        local bandwidth=$(echo "$speed * 8" | bc)
        total_speed=$(echo "$total_speed + $bandwidth" | bc)
        echo "第 $i 次带宽: $bandwidth Mbits/sec"
    done
     local average_speed=$(echo "$total_speed / $count" | bc)
     echo "平均带宽: $average_speed Mbits/sec"

    if (( $(echo "$average_speed < 500" | bc -l) )); then
        echo "网络带宽不足: $average_speed Mbits/sec (要求 >= 500 Mbits/sec)"
    else
        echo "网络带宽合格: $average_speed Mbits/sec"
    fi
}

# 磁盘 IO 检查
check_disk_io() {
    local project_type=$1
    local io_speed=$(dd if=/dev/zero of=testfile bs=1M count=1024 conv=fdatasync 2>&1 | grep -oP '\d+(\.\d+)?(?= (MB/秒|MBytes/秒|MB/s|MBytes/sec))')

    local min_io=0
    case "$project_type" in
        1)
            min_io=100
            ;;
        2)
            min_io=300
            ;;
        3)
            min_io=500
            ;;
        *)
            echo "未知项目类型，请检查输入。"
            return 1
            ;;
    esac

    if (( $(echo "$io_speed < $min_io" | bc -l) )); then
        echo "磁盘 IO 不足: $io_speed MB/s (要求 >= $min_io MB/s)"
    else
        echo "磁盘 IO 合格: $io_speed MB/s"
    fi

    rm -f testfile
}

# CPU 和内存检查
check_cpu_memory() {
    local cpu_cores=$(nproc)
    local total_memory=$(free -g | awk '/^Mem:/{print $2}')

    if (( cpu_cores < 8 )) || (( total_memory < 32 )); then
        echo "CPU 或内存不足: $cpu_cores 核心, $total_memory GB 内存 (要求 >= 8 核心, >= 32GB 内存)"
    else
        echo "CPU 和内存合格: $cpu_cores 核心, $total_memory GB 内存"
    fi
}

main() {
    local server_ip=$1
    local project_type=$2

    echo "开始安装服务的预检查..."
    check_network_speed "$server_ip"
    select_project_type
    check_disk_io "$project_type"
    check_cpu_memory

    echo "所有预检查通过，开始安装服务..."
}

# 选择项目类型
select_project_type() {
    echo "请选择项目类型："
    echo "1) 区县"
    echo "2) 一般地市"
    echo "3) 中心城市"
    read -rp "输入序号 (1/2/3): " project_type

     if ! [[ "$project_type" =~ ^[1-3]$ ]]; then
        echo "无效输入，请输入 1, 2, 或 3."
        exit 1
    fi
}

server_ip=$1
main "$server_ip" "$project_type"
