#!/bin/bash
# 对应主菜单：安装软件的工具箱

. ../include/tool_echo.sh
# 优化内核参数
function patch_centos_kernel() {
    Echo_Red "选择需要打安全补丁的服务器， 注意: 打补丁后的服务器将禁用root用户密码登录!!!root用户仅能使用密钥+密码方式登录!!!"
    Echo_Red "注意: 新增用户egova，密码为Z@Tpwd@2024，首次登录需改密码!!!"
    cd ../include
    . tool_hosts.sh
    display_all_hosts
    cd ../tools
    echo "q: 退出"
    read -p "请输入: " input
    case $input in
    [0-9]*)
        Echo_Red "执行此步骤后，root 账户已经不允许账户密码登录，只能使用私钥+密码方式登录,请确认是否已下载/root/.ssh/id_ed25519文件"
        echo "y: 已下载，继续"
        echo "q: 退出"
        read -p "请输入: " choice
        case $choice in

        y)
            host=$(yq ".all.hosts|keys|.[$(($input - 1))]" ../../ansible/inventory/hosts.yml)
            ansible-playbook -i ../../ansible/inventory/hosts.yml -e "host=$host mode=patch" ../../ansible/install_common.yml
            Echo_Yellow "ansible执行日志见/var/log/ansible.log"
            ;;
        q)
            Echo_Yellow "退出"
            return 0
            ;;
        *)
            Echo_Red "输入错误"
            ;;
        esac
        ;;
    q)
        Echo_Yellow "退出"
        return 0
        ;;
    *)
        Echo_Red "输入错误"
        ;;
    esac
}

patch_centos_kernel