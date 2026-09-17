#!/bin/bash
set -eu
_cur_shell_path=$0
_cur_shell_name=${_cur_shell_path##*/}
_cur_shell_dir=${_cur_shell_path%/*}
if [ "${_cur_shell_name}" == "${_cur_shell_dir}" ]; then
    _cur_shell_dir=$(pwd)
fi
#服务器表文件
host_file="./enhance_hosts.conf"
#ipset名称: 用于记录egova服务器ip列表
ipset_name_of_egova_vpc_nets="egova-vpc-nets"
#ipset名称: 用于记录本机对vpc开放的端口列表
ipset_name_of_egova_local_ports="egova-local-ports"
#ipset名称: 用于记录本机对公网开放的端口列表
ipset_name_of_egova_expose_ports="egova-expose-ports"


log_num=0

function color_text(){
    echo -e " \e[0;$2m$1\e[0m"
}
function echo_green()
{
    echo $(color_text "$1" "32")
}
function echo_num(){
    local msg=$1
    let log_num=log_num+1
    echo "${log_num}: ${msg}"
}

function log_info(){
    local msg="  INFO: $1"
    echo "$(color_text "$1" "32")"
}
function log_error(){
    local msg="  ERROR: $1"
    echo "$(color_text "$1" "31")"
}
function check_env(){
    set +e
    which ipset 1>/dev/null
    if [ $? -gt 0 ] ;then
        echo "请先安装iptables以及ipset!"
        exit 1
    fi
    which iptables 1>/dev/null
    if [ $? -gt 0 ] ;then
        echo "请先安装iptables以及ipset!"
        exit 1
    fi
    set -e
}
#检查ipset
function check_ipset(){
    log_info "检查当前服务器是否进行端口加固..."
    set +e
    ipset list ${ipset_name_of_egova_vpc_nets} 2>/dev/null 1>/dev/null || \
        (log_error "ipset=${ipset_name_of_egova_vpc_nets}不存在,请直接使用[端口加固]对当前服务器进行加固" && exit 1)
    ipset list ${ipset_name_of_egova_local_ports} 2>/dev/null 1>/dev/null || \
      (log_error "ipset=${ipset_name_of_egova_local_ports}不存在,请直接使用[端口加固]对当前服务器进行加固" && exit 1)
    ipset list ${ipset_name_of_egova_expose_ports} 2>/dev/null  1>/dev/null|| \
      (log_error "ipset=${ipset_name_of_egova_expose_ports}不存在,请直接使用[端口加固]对当前服务器进行加固" && exit 1)
    set -e
    log_info "检查通过。"
}
# 保存
function save_ipset(){
    log_info "ipset策略持久化..."
    ipset save -f /etc/sysconfig/ipset
    log_info "save ipset conf to /etc/sysconfig/ipset done!"
}


#显示已添加的ip列表
function show_hosts(){
    log_info "内部服务器IP列表(白名单): "
    ipset list ${ipset_name_of_egova_vpc_nets} |grep -v : |sort |awk '{print NR": "$0}'
}
#当前已对外的端口列表
function show_expose_ports(){
    log_info "已对外的端口列表为: "
    ipset list ${ipset_name_of_egova_expose_ports} |grep Members: -A 10000 |grep -v Members|sed "s|,tcp||g" |sort |awk '{print NR": "$0}'
}
#仅对内部端口列表为
function show_vpc_ports(){
    log_info "仅对内部端口列表为: "
    ipset list ${ipset_name_of_egova_local_ports} |grep Members: -A 10000 |grep -v Members|sed "s|,tcp||g" |sort |awk '{print NR": "$0}'
}
#添加ip
function pre_add_vpc_ip() {
    set +e
    read -p "请输入服务器IP(支持cidr和网段,请勿添加非公司服务器ip): " server_ip
    ipset add -! ${ipset_name_of_egova_vpc_nets} "${server_ip}" 2>/dev/null
    if [ $? -gt 0 ];then
        log_error "格式输入有误，请检查！支持的格式为: 单个ip 192.168.1.1 、cidr 192.168.1.0/24 、ip段 192.168.1.1-192.168.1.10)"
        pre_add_vpc_ip
    fi
    set -e
}
function get_sshd_port(){
    netstat -anop|grep -w LISTEN |grep /sshd |awk '{print $4}' |awk -F: '{print $NF}'|head -1
}
function pre_read_port(){
    set +e
    read -p "请输入端口号: " read_port
    if [[ $read_port =~ ^[0-9]+$ ]] && [ $read_port -gt 0 ] && [ $read_port -le 65535 ]; then
        return 0
    else
        log_error "端口输入有误，请检查！端口范围: 1-65535"
        pre_read_port
    fi

}
function add_vpc_ip() {
    pre_add_vpc_ip
    set +e
    ipset add -! ${ipset_name_of_egova_vpc_nets} ${server_ip}
    if [ $? -gt 0 ];then
        log_error "格式输入有误，请检查！支持的格式为: 单个ip 192.168.1.1 、cidr 192.168.1.0/24 、ip段 192.168.1.1-192.168.1.10)"
    else
        log_info "${server_ip}添加成功。"
    fi
    set -e
}
function ansible_add_host() {
    local server_ip=$1
    \ansible all -m shell -a "ipset add -! ${ipset_name_of_egova_vpc_nets} ${server_ip} && ipset save -f /etc/sysconfig/ipset"
}
#删除ip
function del_host() {
    show_hosts
    echo "q: 返回并保存"
    read -p "请选择需要删除ip的序号: " ip_index
    if [ "${ip_index}" == "q" ];then
        return 0
    fi
    local select_ip="$(ipset list ${ipset_name_of_egova_vpc_nets} |grep -v : |sort |awk '{if(NR=='${ip_index}'){print $0}}')"
    if [ "${select_ip}" == "" ];then
        log_error "选择有误！"
        del_host
        return 0
    fi
    read -p "确认删除ip ${select_ip} ? (y / n) : " ip_del_yes
    if [ "${ip_del_yes}" == "y" ];then
        ipset del -! ${ipset_name_of_egova_vpc_nets} ${select_ip}
        log_info "${select_ip}删除成功。"
        del_host
    fi
}
#删除port
function del_expose_port() {
    show_expose_ports
    echo "q: 返回并保存"
    read -p "请选择需要删除端口的序号: " port_index
    if [ "${port_index}" == "q" ];then
        return 0
    fi
    local select_port="$(ipset list ${ipset_name_of_egova_expose_ports} | \
       grep Members: -A 10000 |grep -v Members |sort |awk '{if(NR=='${port_index}'){print $0}}')"
    if [ "${select_port}" == "" ];then
        log_error "选择有误！"
        del_port
        return 0
    fi
    if [ "${select_port}" == "$(get_sshd_port)" ];then
        log_error "为避免ssh无法访问,禁止对ssh端口进行加固！请配置/etc/ssh/sshd_config禁用密码登录ssh即可！"
        del_expose_port
        return 0
    fi
    read -p "确认删除端口 ${select_port} ? (y / n) : " port_del_yes
    if [ "${port_del_yes}" == "y" ];then
        ipset del -! ${ipset_name_of_egova_expose_ports} ${select_port}
        log_info "${select_port}删除成功。"
        del_expose_port
    fi
}
function add_expose_port(){
    echo "q: 返回并保存"
    read -p "请输入对外暴露的服务端口(格式为ip:port,只允许暴露nginx8080端口、即时通讯5222端口、808对接端口,不可直接暴露tomcat): " ip_port
    if [ "${ip_port}" == "q" ];then
        return 0
    fi
    set +e
    ipset add -! ${ipset_name_of_egova_expose_ports} $(echo ${ip_port}|sed "s|:|,|g")
    if [ $? -gt 0 ];then
        log_error "格式输入有误，请检查！支持的格式为: 8080"
        add_expose_port
    else
        ipset del -! ${ipset_name_of_egova_local_ports} $(echo ${ip_port}|sed "s|:|,|g")
        log_info "${ip_port}添加成功。"
        add_expose_port
    fi
    set -e
}
function ansible_add_expose_port(){
    set +e
    read -p "请输入ip端口(格式如 192.168.1.100:8080 ) : " ip_port
    local addr="$(echo "${ip_port}"|awk -F: '{print $1}')"
    local port=$(echo "${ip_port}"|awk -F: '{print $2}')
    if [[ $port =~ ^[0-9]+$ ]] && [ $port -gt 0 ] && [ $port -le 65535 ] ;then
        if [ "$addr" == "" ] ;then
            log_error "请输入正确的ip和端口！"
            ansible_add_expose_port
        else
            log_info "检查${addr}是否可通过ansible连接..."
            local hit=$(ansible ${addr} -m ping 2>/dev/null |grep pong |wc -l)
            if [ $hit -eq 1 ];then
                ansible ${addr} -m  shell -a "ipset add -! ${ipset_name_of_egova_expose_ports} ${port} \
                   && ipset del -! ${ipset_name_of_egova_local_ports} ${port} \
                   && ipset save -f /etc/sysconfig/ipset \
                   && echo 端口${port}暴露成功。
                "
            else
                log_error "${addr}无法连通！"
                ansible_add_expose_port
            fi
        fi
    else
        log_error "请输入正确的ip和端口！"
        ansible_add_expose_port
    fi
    set -e
}
function add_vpc_port(){
    echo "q: 返回并保存"
    read -p "请输入内部加固的服务端口: " ip_port
    if [ "${ip_port}" == "q" ];then
        return 0
    fi
    if [ "${ip_port}" == "$(get_sshd_port)" ];then
        log_error "为避免ssh无法访问,禁止对ssh端口进行加固！请配置/etc/ssh/sshd_config禁用密码登录ssh即可！"
        add_vpc_port
        return 0
    fi
    set +e
    ipset test ${ipset_name_of_egova_expose_ports} ${ip_port} 2>/dev/null
    if [ $? -eq 0 ];then
        log_error "端口${ip_port}在对外暴露端口列表中,无法加固！如需加固请先执行[删除暴露的端口]"
        return 0
    fi
    ipset add -! ${ipset_name_of_egova_local_ports} ${ip_port}
    if [ $? -gt 0 ];then
        log_error "格式输入有误，请检查！支持的格式为: 8080"
        add_vpc_port
    else
        log_info "${ip_port}添加成功。"
        add_vpc_port
    fi
    set -e
}
#交互式配置
function prompt(){
    echo_green "开放端口管理(本机): "
    echo "1: 显示内部服务器IP列表(白名单)"
    echo "2: 显示内部端口列表"
    echo "3: 显示对外暴露端口列表"
    echo "4: 增加内部服务器IP(白名单)"
    echo "5: 加固内部端口"
    echo "6: 增加对外暴露的端口"
    echo "7: 删除内部服务器IP"
    echo "8: 删除对外暴露的端口"
    echo "q: 退出"
    read -p "请选择: " Select

    case "${Select}" in
    q)
        return 0
        ;;
    1)
        show_hosts
        ;;
    2)
        show_vpc_ports
        ;;
    3)
        show_expose_ports
        ;;
    4)
        show_hosts
        add_vpc_ip
        save_ipset
        ;;
    5)
        show_vpc_ports
        add_vpc_port
        save_ipset
        ;;
    6)
        show_expose_ports
        add_expose_port
        save_ipset
        ;;
    7)
        log_error "注意: 如果添加过CIDR网段，需要先删除CIDR网段才能生效！本工具仅能保证所输入的IP不存在与列表中！"
        del_host
        save_ipset
        ;;
    8)
        del_expose_port
        save_ipset
        ;;
    esac
    prompt
}

#交互式配置
function prompt_ansible(){
    echo_green "开放端口管理(ansible): "
    echo "1: 显示内部服务器IP列表(白名单)"
    echo "2: 显示内部端口列表"
    echo "3: 显示对外暴露端口列表"
    echo "4: 增加内部服务器IP(白名单)"
    echo "5: 加固内部端口"
    echo "6: 增加对外暴露的端口"
    echo "7: 删除内部服务器IP"
    echo "8: 删除对外暴露的端口"
    echo "q: 退出"
    read -p "请选择: " Select

    case "${Select}" in
    q)
        return 0
        ;;
    1)
        \ansible all -m shell -a "ipset list ${ipset_name_of_egova_vpc_nets} |grep -v : |sort |awk '{print NR\": \"\$0}'"
        ;;
    2)
        \ansible all -m shell -a "ipset list ${ipset_name_of_egova_local_ports} |\
        grep Members: -A 10000 |grep -v Members|sed \"s|,tcp||g\" |sort |awk '{print NR\": \"\$0}'"
        ;;
    3)
        \ansible all -m shell -a "ipset list ${ipset_name_of_egova_expose_ports} |grep Members: -A 10000 \
                |grep -v Members|sed \"s|,tcp||g\" |sort |awk '{print NR\": \"\$0}'
        "
        ;;
    4)
        pre_add_vpc_ip
        \ansible all -m shell -a "ipset add -! ${ipset_name_of_egova_vpc_nets} ${server_ip} \
            && ipset save -f  /etc/sysconfig/ipset \
            && echo 白名单${server_ip}增加成功。
        "
        ;;
    5)
        pre_read_port
        if [ "${read_port}" == "$(get_sshd_port)" ];then
            log_error "为避免ssh无法访问,禁止对ssh端口进行加固！请配置/etc/ssh/sshd_config禁用密码登录ssh即可！"
        else
            \ansible all -m shell -a "[ \$(netstat -anop|grep -w LISTEN |grep /sshd | \
                awk '{print \$4}' |awk -F: '{print \$NF}' |grep -w ${read_port}|wc -l) -gt 0 ] \
                && echo ${read_port}为sshd端口,禁止加固！ \
                || (    \
                    ipset test ${ipset_name_of_egova_expose_ports} ${read_port} 2>/dev/null \
                    && echo 端口${read_port}在对外暴露端口列表中,请先删除对外暴露端口 \
                    || (ipset add -! ${ipset_name_of_egova_local_ports} ${read_port} && \
                        ipset save -f /etc/sysconfig/ipset \
                        && echo 端口${read_port}加固增加成功。) \
                )"
        fi
        ;;
    6)
        ansible_add_expose_port
        ;;
    7)
        log_error "注意: 如果添加过CIDR网段，需要先删除CIDR网段才能生效！本工具仅能保证所输入的IP不存在与列表中！"
        pre_add_vpc_ip

        \ansible all -m shell -a "ipset del -! ${ipset_name_of_egova_vpc_nets} ${server_ip} && \
            \ ipset save -f /etc/sysconfig/ipset \
            && echo 白名单${server_ip}删除成功。
        "
        ;;
    8)
        pre_read_port
        if [ "${read_port}" == "$(get_sshd_port)" ];then
            log_error "为避免ssh无法访问,禁止对ssh端口进行加固！请配置/etc/ssh/sshd_config禁用密码登录ssh即可！"
        else
            \ansible all -m shell -a "[ \$(netstat -anop|grep -w LISTEN |grep /sshd | \
                awk '{print \$4}' |awk -F: '{print \$NF}' |grep -w ${read_port}|wc -l) -gt 0 ] \
                && echo ${read_port}为sshd端口,禁止删除！ \
                || (    \
                     ipset del -! ${ipset_name_of_egova_expose_ports} ${read_port} && \
                     ipset save -f /etc/sysconfig/ipset \
                     && echo ${read_port}删除成功。 \
                )"
        fi

        ;;
    esac
    prompt_ansible
}
function help() {

    cat <<EOF
    脚本用途: 修改已加固的端口或者ip列表
    依赖项： ipset、iptables
    参数说明:
      $0 local                               : 单机交互式配置(用于单机执行)
      $0 ansible                             : 使用ansile批量配置(提前配置好/etc/ansible/hosts以及免密)
EOF
}
function main(){

    if [ $# -eq 0 ];then
        echo "参数有误！"
        help
        exit 1
    fi
    case $1 in
    "local")
        #环境检查
        check_env
        check_ipset
        #交互式配置
        prompt "local"
        ;;
    "ansible")
        #批量处理
        set +e
        which ansible 2>/dev/null 1>/dev/null
        if [ $? -gt 0 ];then
            log_error "未找到ansible命令！"
            exit 1
        fi
        set -e
        prompt_ansible
        ;;
    *)
        log_error "参数有误！"
        help
    esac
}

# check to see if this file is being run or sourced from another script
_is_sourced() {
    # https://unix.stackexchange.com/a/215279
    [ "${#FUNCNAME[@]}" -ge 2 ] \
        && [ "${FUNCNAME[0]}" = '_is_sourced' ] \
        && [ "${FUNCNAME[1]}" = 'source' ]
}
#支持多种模式
function support_multi_mode(){
    echo 1
}
if ! _is_sourced; then
    main "$@"
fi