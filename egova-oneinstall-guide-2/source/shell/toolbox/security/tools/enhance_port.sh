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

#交互式输入的ip列表
ipset_name_prompt_expose_nets="prompt-vpc-nets"
ipset_name_prompt_expose_ports="prompt-expose-ports"

log_num=0
proto="tcp"

# check to see if this file is being run or sourced from another script
_is_sourced() {
    # https://unix.stackexchange.com/a/215279
    [ "${#FUNCNAME[@]}" -ge 2 ] \
        && [ "${FUNCNAME[0]}" = '_is_sourced' ] \
        && [ "${FUNCNAME[1]}" = 'source' ]
}

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
# 检查服务是否存在
function check_service_exists(){
    local name=$1
    set +e
    [ $(systemctl list-unit-files |grep $name|wc -l) -eq 0 ] && echo 0 || echo 1
    set -e
}
function check_env(){
    set +e
    which ipset 1>/dev/null
    if [ $? -gt 0 ] ;then
        log_error "请先安装iptables以及ipset!"
        exit 1
    fi
    which iptables 1>/dev/null
    if [ $? -gt 0 ] ;then
        log_error "请先安装iptables以及ipset!"
        exit 1
    fi
    set -e
}

function install_iptables_systemctl(){
    #关闭防火墙
    if [ $(check_service_exists "firewalld.service") -eq 1 ];then
        echo_num "关闭firewalld服务..."
        systemctl stop firewalld.service
        systemctl disable firewalld.service
        log_info "firewalld服务关闭完成,并禁止开机启动。"
    fi
    #增加iptables服务
    if [ $(check_service_exists "iptables.service") -eq 0 ] ; then
        echo_num "配置iptables服务..."
        cp ${_cur_shell_dir}/conf/iptables/iptables.init /usr/libexec/iptables/
        chmod a+x /usr/libexec/iptables/iptables.init
        touch /etc/sysconfig/iptables
        cp ${_cur_shell_dir}/conf/iptables/iptables.service /lib/systemd/system/iptables.service
        test -f /etc/init.d/functions || \
        (cp ${_cur_shell_dir}/conf/iptables/functions /etc/init.d/functions && \
        chmod a+x /etc/init.d/functions)
        systemctl daemon-reload
        systemctl enable iptables
        systemctl start iptables
        log_info "iptables服务配置完成。"
        # 仅对centos支持service iptables save,其他请直接使用exec /usr/libexec/iptables/iptables.init save
        sudo mkdir -p /usr/libexec/initscripts/legacy-actions/iptables/
        sudo cat > /usr/libexec/initscripts/legacy-actions/iptables/save <<EOF
#!/bin/bash
exec /usr/libexec/iptables/iptables.init save
EOF
        sudo chmod a+x /usr/libexec/initscripts/legacy-actions/iptables/save
    fi
    #增加ipset服务
    if [ $(check_service_exists "ipset.service") -eq 0 ];then
        echo_num "配置ipset服务..."
        cp ${_cur_shell_dir}/conf/iptables/ipset.service /lib/systemd/system/ipset.service
        touch /etc/sysconfig/ipset
        systemctl daemon-reload
        systemctl start ipset
        systemctl enable ipset

        if ! test -f /usr/sbin/ipset ;then
            #防止ipset不存在
            set +e
            local ipset_path="$(which ipset 2>/dev/null)"
            if [ "${ipset_path}" != "" ];then
                ln -s ${ipset_path} /usr/sbin/ipset
            else
                echo "清先安装ipset！"
                exit 1
            fi
            set -e
        fi
        log_info "ipset服务配置完成。"
    fi
}

function install_iptables_service(){
    #增加iptables服务
    echo_num "配置iptables服务..."
    if [ $(chkconfig --list iptables |wc -l) -eq 0 ];then
        log_error "未找到iptables服务，请手动处理！"
        exit 1
    fi
    if [ $(chkconfig --list ipset |wc -l) -eq 0 ];then
        log_error "未找到ipset服务，请手动处理！"
        exit 1
    fi

    test -f /etc/sysconfig/iptables || touch /etc/sysconfig/iptables
    test -f /etc/init.d/functions || \
    (cp ${_cur_shell_dir}/conf/iptables/functions /etc/init.d/functions && \
    chmod a+x /etc/init.d/functions)
    chkconfig iptables on || { log_error "iptables 开机自启失败，请手动处理"; exit 1; }
    service iptables restart || { log_error "iptables 重启失败，请手动处理"; exit 1; }
    log_info "iptables服务配置完成。"
    # 仅对centos支持service iptables save,其他请直接使用exec /usr/libexec/iptables/iptables.init save
    sudo mkdir -p /usr/libexec/initscripts/legacy-actions/iptables/
    test -f /usr/libexec/initscripts/legacy-actions/iptables/save || sudo cat > /usr/libexec/initscripts/legacy-actions/iptables/save <<EOF
#!/bin/bash
exec /usr/libexec/iptables/iptables.init save
EOF
    sudo chmod a+x /usr/libexec/initscripts/legacy-actions/iptables/save

    #增加ipset服务
    echo_num "配置ipset服务..."
    test -f /etc/sysconfig/ipset || touch /etc/sysconfig/ipset
    chkconfig ipset on || { log_error "ipset 开机自启失败，请手动处理"; exit 1; }
    service ipset restart || { log_error "ipset 重启失败，请手动处理"; exit 1; }
}
# 安装iptables服务
function install_iptables(){
    mkdir -p /usr/libexec/iptables/ /etc/sysconfig

    set +e
    which systemctl 1>/dev/null 2>/dev/null
    local systemctl_error=$?
    set -e
    # 判断是否存在 systemctl 服务
    if [ ${systemctl_error} -eq 0 ]; then
        install_iptables_systemctl
    else
        log_warn "centos6模式..."
        install_iptables_service
    fi
}

# 保存
function save_iptables(){
    echo_num "iptables策略持久化..."
    iptables-save > /etc/sysconfig/iptables
    log_info "save iptables rules to /etc/sysconfig/iptables done!"
    echo_num "ipset策略持久化..."
    ipset save > /etc/sysconfig/ipset
    log_info "save ipset conf to /etc/sysconfig/ipset done!"
}

function open_port_for_ipset(){
    local type=$1
    local src_set=$2
    local dst_set=$3
    set +e
    iptables -C INPUT -p ${type} -m set --match-set ${src_set} src -m set --match-set ${dst_set} dst -j ACCEPT \
    2>/dev/null 1>/dev/null
    [ $? -gt 0 ] && iptables -I INPUT -p ${type} -m set --match-set ${src_set} src -m set --match-set ${dst_set} \
    dst -j ACCEPT
    set -e
}
#指定本机网卡暴露端口
function open_port_for_iface(){
    local type=$1
    local ether=$2
    local dst_set=$3
    set +e
    iptables -C INPUT -p ${type} -i ${ether} -m set --match-set ${dst_set} dst -j ACCEPT 2>/dev/null 1>/dev/null
    [ $? -gt 0 ] &&  iptables -I INPUT -p ${type} -i ${ether} -m set --match-set ${dst_set} dst -j ACCEPT
    set -e
}


#查询ssh开放的端口
function add_sshd_port(){
    local hit=0
    set +e
    local ssh_port="$(netstat -tulnp |grep sshd |grep LISTEN |grep -w tcp |awk '{print $4}'\
        |awk -F: '{print $NF}'|sort|uniq|head -1)"
    set -e
    if [ "${ssh_port}" != "" ] ;then
        echo_num "开放sshd端口${ssh_port}"
        ipset add -! ${ipset_name_of_egova_expose_ports} ${ssh_port}
#        open_tcp_port ${ssh_port}
        hit=1
    fi
    set +e
    ssh_port=$(cat /etc/ssh/sshd_config |grep "^Port "|awk '{print $2}'|sort|uniq|head -1)
    set -e

    if [ "${ssh_port}" != "" ] ;then
        echo_num "开放sshd端口${ssh_port}"
        ipset add -! ${ipset_name_of_egova_expose_ports} ${ssh_port}
#        open_tcp_port ${ssh_port}
        hit=1
    fi
    if [ ${hit} -eq 0 ] ;then
        log_error "未检测到sshd端口,为避免无法连接，不再进行端口加固"
        exit 22
    fi
    log_info "sshd端口开放成功"
}

#初始化ipset
function init_ipset(){
    echo_num "初始化ipset..."
    ipset create -! ${ipset_name_of_egova_vpc_nets} hash:net 2>/dev/null
    ipset create -! ${ipset_name_of_egova_local_ports} bitmap:port range 0-65535 2>/dev/null
    ipset create -! ${ipset_name_of_egova_expose_ports} bitmap:port range 0-65535 2>/dev/null
    #首先进行清空
    ipset flush ${ipset_name_of_egova_vpc_nets}
    ipset flush ${ipset_name_of_egova_local_ports}
    ipset flush ${ipset_name_of_egova_expose_ports}
    log_info "ipset规则创建完成,并进行了初始化。"
}
#用于记录输入的ip和出口端口等信息
function init_prompt_ipset(){
    ipset create -! ${ipset_name_prompt_expose_nets} hash:net 2>/dev/null
    ipset create -! ${ipset_name_prompt_expose_ports} hash:ip,port 2>/dev/null
}
function flush_prompt_ipset(){
    read -p "确认清除ip和端口列表？(y / n): " flush_select
    if [ "$flush_select" == "y" ];then
        ipset flush ${ipset_name_prompt_expose_nets}
        ipset flush ${ipset_name_prompt_expose_ports}
	ipset flush ${ipset_name_of_egova_vpc_nets}
        ipset flush ${ipset_name_of_egova_local_ports}
        ipset flush ${ipset_name_of_egova_expose_ports}
    fi
}
#扫描本机非ssh端口
function scan_local_listen_ports(){
    echo_num "扫描本机开放的端口..."
    set +e
    for port in $(ss -tunlp  | grep -Ev 'Local|sshd' | awk '{split($5,a,":");print a[length(a)]}' | grep -v ^$ |sort |uniq)
    do
        local is_expose=$(ipset list ${ipset_name_of_egova_expose_ports} |grep -v : | \
            awk '{if($1=='${port}'){print $0}}'|wc -l)
        if [ ${is_expose} -eq 0 ];then
            ipset add -! ${ipset_name_of_egova_local_ports} ${port}
        else
            log_info "忽略对外暴露的端口:${port}"
        fi
    done
    set -e
    log_info "共扫描到$(ipset list ${ipset_name_of_egova_local_ports}|grep "Number of entries:"|awk '{print $NF}')个本地${proto}端口。"
    log_info "端口列表为$(ipset list ${ipset_name_of_egova_local_ports}|grep "Members:" -A 100| \
        awk '{if(NR>1){printf $NF","}}')"
}
#为指定ip开放端口
function add_vpc_nets_by_file(){
#    local ip_file=$1
#    echo_num "将文件${ip_file}中的ip添加到白名单..."
#    cat ${ip_file} | grep -v "^$" | sort | uniq | while read addr; do
#        #网段格式记录(支持cidr)
#        log_info "添加${addr}..."
#        ipset add -! ${ipset_name_of_egova_vpc_nets} "$addr"
#    done

    local ip_file=$1
    echo_num "将文件${ip_file}中的ip添加到白名单..."
    cat ${ip_file} |  grep -E "add\s*${ipset_name_prompt_expose_nets}\s+" |awk '{print $NF}'| sort | uniq | while read addr; do
        #网段格式记录(支持cidr)
        log_info "添加${addr}..."
        ipset add -! ${ipset_name_of_egova_vpc_nets} "$addr"
    done
}
#增加对外部暴露的端口
function add_expose_port_by_file(){
    local ip_file=$1
    echo_num "将文件${ip_file}中的暴露端口添加到白名单..."
    cat ${ip_file} |  grep -E "add\s*${ipset_name_prompt_expose_ports}\s+" | \
        awk '{print $NF}'| sort | uniq | while  read ip_port;
    do
        local ip=$(echo ${ip_port}|awk -F, '{print $1}')
        local port=$(echo ${ip_port}|awk -F: '{print $2}')
        if [ $(ifconfig |grep " ${ip} "|wc -l) -gt 0 ];then
            log_info "添加${port}..."
            ipset add -! ${ipset_name_of_egova_expose_ports} "${port}"
        fi
    done
}

#增加本机ip
function add_vpc_nets_by_local(){
    #查询docker网段并增加到本机网段列表中
    set +e
    which docker 2>/dev/null 1>/dev/null
    if [ $? -eq 0 ] ;then
        echo_num "将docker网桥添加到白名单..."
        for addr in $(docker network list|awk '{if(NR>1){print $1}}' | \
            xargs -I {} docker network inspect {} |grep Subnet | \
            awk  '{print $2}'|sed "s|\"||g;s|,||g" )
        do
            log_info "添加${addr}..."
            ipset add -! ${ipset_name_of_egova_vpc_nets} "${addr}"
        done
    fi
    set -e
    #查询本机所有已存在的ip加入白名单
    echo_num "将本机ip添加到白名单..."
    for addr in $(ifconfig |grep inet|grep -v inet6|awk '{print $2}'|grep -oP '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    do
        log_info "添加${addr}..."
        ipset add -! ${ipset_name_of_egova_vpc_nets} ${addr}
    done
}
# 对外暴露端口完全放行
function open_ports_for_expose(){
    echo_num "对外部ip开放${proto}协议的ipset=${ipset_name_of_egova_expose_ports}端口访问权限..."
    set +e
    # 检查并添加 TCP 端口放行规则
    iptables -C INPUT -p ${proto}  -m set --match-set ${ipset_name_of_egova_expose_ports} dst -j ACCEPT 2>/dev/null 1>/dev/null
    [ $? -gt 0 ] &&  iptables -I INPUT -p  ${proto} -m set --match-set ${ipset_name_of_egova_expose_ports} dst -j ACCEPT
    log_info "iptables INPUT链添加完成。"
    set -e
}
# vpc网段放行
function open_ports_for_vpc_nets(){
    echo_num "为ipset=${ipset_name_of_egova_vpc_nets}开放端口权限..."
    open_port_for_ipset "${proto}" "${ipset_name_of_egova_vpc_nets}" "${ipset_name_of_egova_local_ports}"
    log_info "iptables INPUT链添加完成。"
}
# 本机网卡放行
function open_ports_for_local_iface(){
    echo "这里有BUG，不能开，所有的外部流量的都是从这里进来的"
#    echo_num "为本机物理网卡开放端口权限..."
#    #查询本机非虚拟网卡（注意diff在中文系统下的区别）
#    for iface in $(diff /sys/class/net/ /sys/devices/virtual/net/ |grep /sys/class/net/ | \
#        awk -F"[:：]" '{print $2}'|sed "s/ //g")
#    do
#        log_info "添加网卡${iface}..."
#        open_port_for_iface "tcp" "${iface}" "${ipset_name_of_egova_local_ports}"
#    done
}

#最后增加端口拒绝策略
function append_drop_ports(){
    echo_num "追加端口默认拒绝策略..."
    set +e
    #先清除
    iptables -D INPUT -p ${proto}  -m set --match-set ${ipset_name_of_egova_local_ports} dst -j DROP 2>/dev/null
    local rst=$?
    until [ $rst -gt 0 ]; do #直道清除失败
#        echo 清除旧值确保追加到最后
        iptables -D INPUT -p ${proto} -m set --match-set ${ipset_name_of_egova_local_ports} dst -j DROP 2>/dev/null
        rst=$?
    done
    iptables -A INPUT -p ${proto} -m set --match-set ${ipset_name_of_egova_local_ports} dst -j DROP
    log_info "iptables INPUT链添加完成。"
    set -e
}
function check(){
    #检查ssh是否禁止密码登录
    check_ssh_pwd_auth
    #检测nginx是否开启waf

}
function help_cmd_output(){
    echo_num "端口加固完成，可使用如下命令检查效果:"
cat <<EOF
    # 检查对egova内网服务器开放的端口列表
    ipset list ${ipset_name_of_egova_local_ports}

    # 检查对全部ip开放的端口列表
    ipset list ${ipset_name_of_egova_expose_ports}

    # 检查内网ip列表(放行白名单)
    ipset list ${ipset_name_of_egova_vpc_nets}

    # 检查iptables规则(Chain INPUT中对于端口${ipset_name_of_egova_vpc_nets}先对内网${ipset_name_of_egova_local_ports}放行最后全部拒绝)
    iptables -nv -L

    #追加端口tcp:50000仅对内网放行(当机器上部署了新的服务，避免外部可以访问到)
    ipset add ${ipset_name_of_egova_local_ports} 50000
    ipset save > /etc/sysconfig/ipset

    #增加内网服务器192.168.1.199,使能访问内部服务(当申请到了新的服务器加入到集群时使用)
    ipset add ${ipset_name_of_egova_vpc_nets} 192.168.1.199
    ipset save > /etc/sysconfig/ipset

    #将本机8080端口暴露给非内部服务器(慎重使用: 一般仅暴露nginx8080、5222即时通讯、808对接等端口)
    ipset add ${ipset_name_of_egova_expose_ports} 8080
    ipset save > /etc/sysconfig/ipset
EOF
}
# 端口加固执行入口
function enhance(){
    #检查必要的工具是否已经安装
    check_env
    #检查入参
    local ip_file=$(echo $1|awk -F= '{print $2}')
    if [ "${ip_file}" == "" ] || ! test -f ${ip_file} || [ $(cat ${ip_file}|wc -l) -eq 0 ] ;then
        log_error "请传入内部服务器ip配置列表"
        exit 1
    fi
    #安装iptables服务禁用firewalld
    install_iptables
    #初始化ipset
    init_ipset
    #开放ssh端口,全部
    add_sshd_port
    #开放指定的端口
    add_expose_port_by_file ${ip_file}
    #扫描本机非ssh端口&非暴露端口，并加入到ipset中
    scan_local_listen_ports
    #将文件中的ip增加到vpc白名单
    add_vpc_nets_by_file "${ip_file}"
    #将本机ip增加到ip白名单
    add_vpc_nets_by_local
    #对外暴露端口放行
    open_ports_for_expose
    #对ipset中的这个vpc放行
    open_ports_for_vpc_nets
    #最后增加端口拒绝策略
    append_drop_ports
    #保存iptables
    save_iptables
    #输出辅助日志
    help_cmd_output
}
#显示已添加的ip列表
function show_hosts(){
    log_info "当前已添加的ip列表为: "
    ipset list ${ipset_name_prompt_expose_nets} |grep -v : |sort |awk '{print NR": "$0}'
}
#显示已添加的port列表
function show_ports(){
    if [ "${proto}" == "" ];then
        proto="tcp"
    fi
    log_info "当前已添加的端口列表为: "
    ipset list ${ipset_name_prompt_expose_ports} |grep Members: -A 10000 |grep -v Members|sed "s|,${proto}||g" |sort \
        |awk '{print NR": "$0}'
}
#导出配置
function export_prompt(){
    log_info "开始导出..."
    local export_file=./ip_port.conf
    ipset save ${ipset_name_prompt_expose_nets} > ${export_file}
    ipset save ${ipset_name_prompt_expose_ports} >> ${export_file}
    log_info "已导出到./ip_port.conf文件。"
}
#导入配置
function import_prompt(){
    local export_file="$1"
    local quiet="$2"
    if [ "${quiet}" == "true" ];then
        if ! test -f ${export_file} ;then
            return 1
        fi
    else
        if test -f "${export_file}" ;then
            log_info "检测到${export_file}文件"
            read -p "导入时将清空之前的配置，确认导入? (y / n) : " import_select
            if [ "${import_select}" != "y" ];then
                return 0
            fi
        else
            read -p "请输入待导入的配置文件路径: " export_file
            import_prompt "${export_file}" "false"
            return 0
        fi
    fi

    log_info "开始清除之前的配置..."
    ipset flush ${ipset_name_prompt_expose_nets}
    ipset flush ${ipset_name_prompt_expose_ports}
    ipset restore -! -f ${export_file}
    log_info "导入完成。"
}
#添加ip
function add_host() {
    show_hosts
    echo "q: 返回上一层"
    read -p "请输入服务器IP(支持cidr和网段,请勿添加非公司服务器ip): " server_ip
    if [ "$server_ip" == "q" ];then
        return 0
    fi
    set +e
    ipset add -! ${ipset_name_prompt_expose_nets} ${server_ip}
    if [ $? -gt 0 ];then
        log_error "格式输入有误，请检查！支持的格式为: 单个ip 192.168.1.1 、cidr 192.168.1.0/24 、ip段 192.168.1.1-192.168.1.10)"
        add_host
    else
        add_host
    fi
    set -e
}
#删除ip
function del_host() {
    show_hosts
    echo "q: 返回上一层"
    read -p "请选择需要删除ip的序号: " ip_index
    if [ "${ip_index}" == "q" ];then
        return 0
    fi
    local select_ip="$(ipset list ${ipset_name_prompt_expose_nets} |grep -v : |sort \
        |awk '{if(NR=='${ip_index}'){print $0}}')"
    if [ "${select_ip}" == "" ];then
        log_error "选择有误！"
        del_host
        return 0
    fi
    read -p "确认删除ip ${select_ip} ? (y / n) : " ip_del_yes
    if [ "${ip_del_yes}" == "y" ];then
        ipset del -! ${ipset_name_prompt_expose_nets} ${select_ip}
    fi
}
#删除port
function del_port() {
    show_ports
    echo "q: 返回上一层"
    read -p "请选择需要删除端口的序号: " port_index
    if [ "${port_index}" == "q" ];then
        return 0
    fi
    local select_port="$(ipset list ${ipset_name_prompt_expose_ports} | \
       grep Members: -A 10000 |grep -v Members |sort |awk '{if(NR=='${port_index}'){print $0}}')"
    if [ "${select_port}" == "" ];then
        log_error "选择有误！"
        del_port
        return 0
    fi
    read -p "确认删除端口 ${select_port} ? (y / n) : " port_del_yes
    if [ "${port_del_yes}" == "y" ];then
        ipset del -! ${ipset_name_prompt_expose_ports} ${select_port}
    fi
}
function add_expose_port(){
    show_ports
    echo "q: 返回上一层"
    read -p "请输入对外暴露的服务端口(格式为ip:port,只允许暴露nginx8080端口、即时通讯5222端口、808对接端口,不可直接暴露tomcat): " ip_port
    if [ "${ip_port}" == "q" ];then
        return 0
    fi
    set +e
    ipset add -! ${ipset_name_prompt_expose_ports} $(echo ${ip_port}|sed "s|:|,|g")
    if [ $? -gt 0 ];then
        log_error "格式输入有误，请检查！支持的格式为: 192.168.1.1:8080"
        add_expose_port
    else
        add_expose_port
    fi
    set -e
}
# 选择加固端口的协议
function select_port_proto(){
    echo "请选择加固端口的协议类型: "
    echo "1: tcp"
    echo "2: udp)"
    read -p "请选择: " select_proto
    case ${select_proto} in
    1)
       proto="tcp"
        ;;
    2)
       proto="udp"
      ;;
    *)
        echo "选择错误！"
        select_port_proto
    esac
}
#交互式配置
function prompt_config(){
    local mode=$1
    echo_green "开始设置egova内部服务器列表..."
    echo "i: 导入配置(之前配置过,可直接导入)"
    echo "1: 增加内部服务器"
    echo "2: 增加对外暴露的端口"
    echo "3: 删除内部服务器ip"
    echo "4: 删除对外暴露的端口"
    echo "5: 清空所有配置"
    echo "v: 查看已配置的内部服务器和端口"
    echo "e: 导出配置用于给其他服务器使用(ip和端口)"
    echo "p: 执行端口增强(默认tcp)"
    echo "q: 退出"
    read -p "请选择: " Select

    case "${Select}" in
    q)
        return 0
        ;;
    i)
        import_prompt "" "false"
        ;;
    v)
        show_hosts
        show_ports
        ;;
    1)
        add_host
        ;;
    2)
        add_expose_port
        ;;
    3)
        del_host
        ;;
    4)
        del_port
        ;;
    5)
        flush_prompt_ipset
        ;;
    e)
        export_prompt
        ;;
    p)
        select_port_proto
        export_prompt
        if [ "$mode" == "local" ];then
            enhance --conf=./ip_port.conf
        elif [ "$mode" == "ansible" ];then
            #拷贝配置
            echo_num "拷贝脚本和配置..."
            set -e
            \ansible all -m file -a "name=/tmp/toolbox/enhance_port/conf state=directory"
            \ansible all -m copy -a "src=${_cur_shell_path} dest=/tmp/toolbox/enhance_port/${_cur_shell_name} mode=0755"
            \ansible all -m copy -a "src=${_cur_shell_dir}/conf/iptables dest=/tmp/toolbox/enhance_port/conf/ mode=0755"
            \ansible all -m copy -a "src=${_cur_shell_dir}/ip_port.conf dest=/tmp/toolbox/enhance_port/ip_port.conf"

            #执行增强
            echo_num "检查环境..."
            \ansible all -m shell -a "/tmp/toolbox/enhance_port/${_cur_shell_name} check"
            log_info "环境检查通过！"
            echo_num "执行端口加固..."
            \ansible all -m shell -a "/tmp/toolbox/enhance_port/${_cur_shell_name} enhance --conf=/tmp/toolbox/enhance_port/ip_port.conf"
            log_info "端口加固完成！"
        fi
        ;;
    esac
    prompt_config $mode
}
function help() {

    cat <<EOF
    脚本用途: 对本机暴露的端口进行加固，对于非nginx或者即时通信、808协议对接等端口
            如mysql、tomcat、redis、zookeeper、es等端口（端口无需配置，自动扫描本机所有监听）
            仅允许我方服务器访问，其他机器(用户PC或者第三方服务器)无法访问内部端口。
            需要配置内部服务器列表以及对外暴露的端口
    依赖项： ipset、iptables
    参数说明:
      $0 local                               : 单机交互式配置和加固(用于单机执行)
      $0 ansible                             : 使用ansile批量加固(提前配置好/etc/ansible/hosts以及免密)
      $0 enhance --conf=/tmp/ip_port.conf    : 根据ip_port.conf中的配置进行加固(配置可用交互式模式下配置并导出)
EOF
}
function main(){
    #环境检查
    check_env
    if [ $# -eq 0 ];then
        echo "参数有误！"
        help
        exit 1
    fi
    case $1 in
    "local")
        #初始化ipset配置
        init_prompt_ipset
        #交互式配置
        prompt_config "local"
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
        #初始化ipset配置
        init_prompt_ipset
        prompt_config "ansible"
        ;;
    "check")
        #环境检查
        check_env
        ;;
    "enhance")
        #执行加固
        if [ $# -ge 2 ];then
            enhance "$2"
        else
            log_error "加固参数有误！请传入加固配置文件"
        fi
        ;;
    *)
        log_error "参数有误！"
        help
    esac
}

#支持多种模式
function support_multi_mode(){
    echo 1
}
if ! _is_sourced; then
    main "$@"
fi
