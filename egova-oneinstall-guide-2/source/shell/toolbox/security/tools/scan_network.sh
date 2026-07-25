#!/bin/bash
set -u
set -o pipefail
_cur_shell_path=$0
_cur_shell_name=${_cur_shell_path##*/}
_cur_shell_dir=${_cur_shell_path%/*}
if [ "${_cur_shell_name}" == "${_cur_shell_dir}" ]; then
    _cur_shell_dir=$(pwd)
fi

#ipset名称: 用于记录egova服务器ip列表
ipset_name_of_egova_vpc_nets="egova-vpc-nets"
#ipset名称: 用于记录本机对vpc开放的端口列表
ipset_name_of_egova_local_ports="egova-local-ports"
#ipset名称: 用于记录本机对公网开放的端口列表
ipset_name_of_egova_expose_ports="egova-expose-ports"

rst_error_log="/tmp/scan_error.txt"

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
    echo "$(color_text "$msg" "32")"
}
function log_warn(){
    local msg="  WARN: $1"
    echo "$(color_text "$msg" "33")"
}
function log_error(){
    local msg="  ERROR: $1"
    echo "$(color_text "$msg" "31")"
}
function install_fscan(){
    echo_num "检查fscan是否已安装"
    which fscan 1>/dev/null 2>/dev/null
    if [ $? -gt 0 ] ;then
        log_info "fscan未安装。"
        if ! test -f ${_cur_shell_dir}/src/fscan ;then
            log_error "请先下载fscan到${_cur_shell_dir}/src/fscan"
            exit 1
        fi
        local arch=$(uname -m)
        if [ "${arch}" == "aarch64" ] || [ "${arch}" == "arm64" ];then
            \cp ${_cur_shell_dir}/src/fscan-arm64 /usr/bin/fscan
            chmod a+rx /usr/bin/fscan
            log_info "${arch}版本fscan安装成功。"
        elif [ "${arch}" == "x86_64" ];then
            \cp ${_cur_shell_dir}/src/fscan /usr/bin/fscan
            chmod a+rx /usr/bin/fscan
            log_info "${arch}版本fscan安装成功。"
        else
            log_error "cpu架构${arch}暂不支持自动安装,请通过https://github.com/shadow1ng/fscan确认是否支持。"
            exit 1
        fi
    else
        log_info "fscan已安装。"
    fi

}
function get_cidrs(){
    ip a |grep inet |grep -v inet6 |awk '{print $2}'|grep -v "127.0.0.1"|awk '{printf $1","}'
}
function do_scan(){

    echo_num "获取网段"
    local cidrs=$(get_cidrs)
    log_warn "获取到的网段为:${cidrs}"
    log_warn "是否开始扫描？执行过程可能耗时较多,请关注红色信息并进行修正。"
    read -p "输入任意字符开始扫描,ctrl+c 退出..."
    echo_num "开始扫描..."
    mkdir -p /egova
    local f=/egova/fscan_result_$( date +%Y%m%d_%H%M).txt
    fscan -h $cidrs -o $f
    log_info "扫描完成,结果存放于${f},可随时查看。"
}
function scan_network(){
    install_fscan
    do_scan
}

function help() {

    cat <<EOF
    脚本用途: 使用fscan扫描网段(如果有不同网段的服务器,请在每个网段选择一个服务器执行fscan)
    依赖项： fscan
    参数说明:
      $0 cidr                              : 获取当前服务器所处的网段
      $0 local                             : 单机交互
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
        scan_network
        ;;
    "cidr")
        get_cidrs
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
    echo 0
}
if ! _is_sourced; then
    main "$@"
fi