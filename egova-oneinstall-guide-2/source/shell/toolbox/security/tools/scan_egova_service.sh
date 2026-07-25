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
LOGIN_SHELLS="/bin/bash|/bin/sh|/bin/zsh"

#[免密扫描]扫描nginx的access日志中免密登录的请求
check_logon_username_password_log="/tmp/check_logon_username_password_log.txt"
readonly USER="`whoami`"

log_num=0

#获取nginx日志的status位置
cat > /tmp/${USER}_log_col_index.awk <<EOF
BEGIN{}
{
  cur=0;
  for(i=1;i<=NF;i++)
  {
    cur++;
    if(\$i=="time_local"){
      cur++
    }
    else if(\$i=="request"){
      cur=cur+2
    }
    if(\$i==key){
      if(key=="time_local"||key=="request"){
        print cur-1
      }else{
       print cur
      }
    }
  }
}
END{}
EOF

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
function check_env(){
    which ipset 1>/dev/null
    if [ $? -gt 0 ] ;then
        log_error "端口加固不安全: 未进行端口加固(未找到ipset命令)!"
        return 1
    fi
    which iptables 1>/dev/null
    if [ $? -gt 0 ] ;then
        log_error "端口加固不安全: 未进行端口加固(未找到iptables命令)!"
        return 1
    fi
    return 0
}
#检查ipset
function check_ipset(){
    echo_num "检查当前服务器是否进行端口加固"

    #兼容低版本里没有Number of entries属性
    local cnt=$(ipset list ${ipset_name_of_egova_vpc_nets} 2>/dev/null|grep "Members:" -A 10000 |wc -l)
    let cnt=cnt-1
    if [ $? -gt 0 ] ;then
        log_error "端口加固不安全: ipset=${ipset_name_of_egova_vpc_nets}不存在"
        return 1
    elif [ "$cnt" == "0" ]; then
        log_error "端口加固不安全: ipset=${ipset_name_of_egova_vpc_nets}中不存在任何白名单IP"
        return 1
    else
        log_info "pass: 当前服务器存在ipset list ${ipset_name_of_egova_vpc_nets}中白名单数量为${cnt}个。"
    fi
    local cnt=$(ipset list ${ipset_name_of_egova_local_ports} 2>/dev/null|grep "Members:" -A 10000|awk '{print $NF}' |wc -l)
    let cnt=cnt-1
    if [ $? -gt 0 ];then
        log_error "端口加固不安全: ipset=${ipset_name_of_egova_local_ports}不存在"
        return 1
     elif [ "$cnt" == "0" ]; then
        log_error "端口加固不安全: ipset=${ipset_name_of_egova_local_ports}中不存在任何内部端口。"
        return 1
    else
        log_info "pass: 当前服务器存在ipset list ${ipset_name_of_egova_local_ports}中内部端口数量为${cnt}个。"
    fi
    local cnt=$(ipset list ${ipset_name_of_egova_expose_ports} 2>/dev/null|grep "Members:" -A 10000|awk '{print $NF}' |wc -l)
    let cnt=cnt-1
    if [ $? -gt 0 ];then
        log_error "端口加固不安全: ipset=${ipset_name_of_egova_expose_ports}不存在"
        return 1
    else
        log_warn "警告: 当前服务器存在ipset list ${ipset_name_of_egova_expose_ports}中外部端口数量为${cnt}个。"
    fi

}
#检查ssh是否禁止密码登录
function check_ssh_pwd_auth(){
    local sshd_config="/etc/ssh/sshd_config"
    local missing_configs=()
    echo_num "扫描ssh配置..."
    # 检查配置项
    if ! grep -q "^PasswordAuthentication yes" "$sshd_config"; then
        missing_configs+=("PasswordAuthentication yes")
    fi
    if ! grep -q "^PubkeyAuthentication yes" "$sshd_config"; then
        missing_configs+=("PubkeyAuthentication yes")
    fi
    if ! grep -q "^AuthenticationMethods publickey,password" "$sshd_config"; then
        missing_configs+=("AuthenticationMethods publickey,password")
    fi
     # 根据结果给出提示
    if [ ${#missing_configs[@]} -eq 0 ]; then
        log_info "双因素认证已启用,sshd_config中已禁止密码登录。"
        log_warn "注意:本结果只对配置文件/etc/ssh/sshd_config 正确性负责,如果是手工修改过PasswordAuthentication参数,请切记重启一次sshd服务！"
    else
        log_error "以下配置项缺失，未启用双因素认证登录（密钥+密码方式登录）："
        for config in "${missing_configs[@]}"; do
            log_error " $config"
        done
    fi
}

# 服务器login权限账户检测
function scan_logon_username(){
    temp_file=$(mktemp)
    # 检测所有可以登录的用户
    echo "以下是所有可以登录的用户："
    awk -F: -v shells="$LOGIN_SHELLS" '$7 ~ shells {print $1 " " $7}' /etc/passwd > "$temp_file"

    # 按顺序列出可登录用户
    count=1
    while read -r user shell; do
        echo "$count. $user ($shell)"
        echo "$count $user" >> "$temp_file.index"
        count=$((count + 1))
    done < "$temp_file"

    # 判断是否运行在 ansible 模式下
    if [ "$1" == "ansible" ]; then
        echo "跳过用户禁止登录的交互式部分（ansible 模式）"
    else
        # 询问用户选择需要禁止登录的用户
        echo
        echo "请输入要禁止登录的用户的序号（用空格分隔多个序号，回车跳过）："
        read -r selected_numbers

        if [ -z "$selected_numbers" ]; then
            echo "未选择任何用户进行禁止登录。"
        fi

        # 遍历用户并设置为 nologin
        for number in $selected_numbers; do
            user=$(awk -v num="$number" '$1 == num {print $2}' "$temp_file.index")
            if [ -n "$user" ]; then
                echo "设置用户 $user 为 nologin"
                usermod -s /sbin/nologin "$user"
            else
                echo "序号 $number 无效，跳过..."
            fi
        done
    fi

    # 删除临时文件
    rm -f "$temp_file" "$temp_file.index"
}

#url探测
function get_curl_resp_code(){
    local url=$1
    curl ${url} -w %{http_code} --connect-timeout 3 -s -o /dev/null 2>/dev/null
}
#检查http服务是否存在
function check_http_addr_exists(){
    local ip=$1
    local port=$2
    local url=$3
    local code=$(get_curl_resp_code http://${ip}:${port}/${url})
#    echo "$url $code"
    if [ "$code" == "000" ] || [ "$code" == "404" ];then
        return 0
    else
        return $code
    fi
}

#检查nginx下是否暴露了file_server
function check_nginx_file_server(){

    check_http_addr_exists 127.0.0.1 ${port} HttpFileServer
    local code=$?
    if [ $code -gt 0 ];then
        # 老版本会返回302,netty版本会返回401
        log_error "nginx监听端口不安全: 端口号${port}疑似暴露了HttpFileServer服务[code=$code]！！！" |tee -a rst_error_log
    else
        log_info "pass: 端口号${port}下无HttpFileServer服务。"
    fi
}

#检查tomcat下是否暴露了MediaRoot
function check_java_media_root(){
    check_http_addr_exists 127.0.0.1 ${port} MediaRoot/mediaroot.proxy
    local code=$?
    if [ $code -gt 0 ];then
        log_error "tomcat监听端口不安全: 端口号${port}疑似暴露了MediaRoot服务[code=$code]！！！" |tee -a rst_error_log
    else
        log_info "pass: 端口号${port}下无MediaRoot服务。"
    fi
}
#检查tomcat下是否暴露了MediaRoot
function check_tomcat_conf_media_root(){
    local catalina_home=$1

    local hit_media_root=$(grep MediaRoot ${catalina_home}/conf/Catalina/localhost/*.xml \
            ${catalina_home}/conf/server.xml 2>/dev/null 1>/dev/null |wc -l)
    if [ ${hit_media_root} -gt 0 ];then
        log_error "tomcat目录不安全: ${catalina_home}疑似暴露了MediaRoot服务！！！" |tee -a rst_error_log
    else
        log_info "pass: 目录${catalina_home}下无MediaRoot服务"
    fi
}

#检测geoserver服务是否默认账号密码为admin geoserver
function check_geoserver_passwd(){
    log_info "检测geoserver服务是否为默认账号密码"
    check_http_addr_exists 127.0.0.1 ${port} geoserver/web
    local code=$?
    if [ $code -gt 0 ];then
        # geoserver 返回302
        local geo_url="http://127.0.0.1:${port}"
        # 登录
        local httpcode=$(curl -X POST -d "username=admin&password=geoserver"  "$geo_url/geoserver/j_spring_security_check" -s -w %{http_code})
        if [ "$httpcode" == "302" ];then
              log_error "geoserver默认账号可登录geoserver服务"
          if [ $( curl -X POST -d "username=admin&password=geoserver"  "$geo_url/geoserver/j_spring_security_check" --connect-timeout 3  -i -s |grep Location |grep 'GeoServerLoginPage?error=true' | wc -l ) -lt 1 ];then
              log_error "geoserver默认账号不安全" |tee -a $rst_error_log
          fi
        fi
    else
        log_info "pass: 端口号${port}下无geoserver服务。"
    fi

}


#检查tomcat下是否暴露了manager如无
function check_tomcat_manager(){
    local catalina_home=$1

    local hit_media_root=$(grep MediaRoot ${catalina_home}/conf/Catalina/localhost/*.xml \
            ${catalina_home}/conf/server.xml 2>/dev/null  1>/dev/null |wc -l)
    if [ -d ${catalina_home}/webapps/manager ];then
        log_error "tomcat目录不安全: ${catalina_home}疑似暴露了manager服务！！！" |tee -a rst_error_log
    else
        log_info "pass: 目录${catalina_home}下无webapps/manager目录。"
    fi
}
#检查端口下是否开启了waf
function check_nginx_with_waf(){
    local ip=127.0.0.1
    local port=$1
    local code=$(get_curl_resp_code http://${ip}:${port}/?a=javascript%3A)
    if [ "$code" != "000" ] && [ "$code" != "403" ];then
        log_error "nginx监听端口不安全: 端口号${port}未开启waf！！！" |tee -a rst_error_log
    else
        log_info "pass: 端口${port}下已开启waf。"
    fi
}
#扫描nginx的access日志中免密登录的请求
function check_logon_username_password(){
  #先删除日志文件
  if [ -f "${check_logon_username_password_log}" ];then
      rm -rf  ${check_logon_username_password_log}
      log_info "删除日志文件：日志文件存在已删除完成${check_logon_username_password_log}"
  fi
  #多个nginx时：查找nginx.conf
  for path_nginx_conf in $(nginx -t 2>&1 | grep -o '/.*\.conf' |uniq)
    do
      echo "$(color_text "当前扫描的nginx是：${path_nginx_conf}" "33")"
      #获取nginx log_format status
      log_format=$(cat ${path_nginx_conf} |grep "log_format" |grep main |head -1|awk -F"'" '{print $2}'|sed 's/\$//g'|sed "s/\[//g" |sed "s/\]//g"|sed 's/"//g')
      code=$(echo $log_format|awk -f /tmp/${USER}_log_col_index.awk key="status")
      #获取nginx日志路径
      path_nginx_accesslogfile=$(cat ${path_nginx_conf} | grep access_log |awk '{print $2}' |head -n 1)
      path_nginx_access=${path_nginx_accesslogfile%/*}
      #如果日志路径存在则继续
      if [ -e "${path_nginx_access}" ];then
        #查找今天起的最近两个access日志
        for accessfile in $(ls -t ${path_nginx_access}/access* |head -n 2|awk -F "/" '{print $5}' )
            do
                log_info "当前扫描的access日志文件是：${path_nginx_access}/${accessfile}"
                ##查询请求含username和password的access日志，不区分大小写
                grep -i -E "username=|password=" ${path_nginx_access}/${accessfile} | \
                awk '{if($'${code}'>=200 && $'${code}'< 400) print $7,$'${code}'}' |sort|uniq | tee -a ${check_logon_username_password_log}
            done
      fi
    done
    log_info "查询最近两个access log file结束,请查看日志文件：${check_logon_username_password_log}"
}
#检查是否有未加固的端口
function check_without_enhanced_port(){
    ipset list ${ipset_name_of_egova_local_ports} |grep Members: -A 10000 > /tmp/${ipset_name_of_egova_local_ports}.txt
    ipset list ${ipset_name_of_egova_expose_ports} |grep Members: -A 10000  >> /tmp/${ipset_name_of_egova_local_ports}.txt
    for port in $(netstat -anop|grep -w LISTEN |grep -v sshd |awk '{print $4}' |grep -v -E "127.0.0.1:|::1:"| \
        awk -F: '{print $NF}'|sort|uniq )
    do
        cat /tmp/${ipset_name_of_egova_local_ports}.txt |grep -w $port 2>/dev/null 1>/dev/null
        if [ $? -gt 0 ];then
            log_error "端口加固不安全: 端口${port}未进行加固！"
        else
            log_info "pass: 端口${port}已加固(仅内部白名单可访问)。"
        fi
    done
}
#检查暴露的端口是否是nginx或者sshd
function check_exposed_port_is_safe(){
    set +e
    netstat -anopp|grep -E "sshd|nginx" |grep -w LISTEN |grep -E "/sshd|/nginx"\
       |awk '{print $4}' |grep -v -E "127.0.0.1:|::1:"| \
       awk -F: '{print $NF}'|sort|uniq > /tmp/nginx_sshd_ports.txt
    for port in $(ipset list ${ipset_name_of_egova_expose_ports} |grep Members: -A 10000|grep -v Members)
    do
        set +e
        grep -w ${port} /tmp/nginx_sshd_ports.txt 2>/dev/null 1>/dev/null
        if [ $? -gt 0 ];then
            log_error "端口加固不安全: 端口${port}非nginx或者sshd端口,请确认端口对外开放的必要性！！"
        else
            log_info "pass: 端口${port}对外暴露，为sshd或者nginx端口。"
        fi
    done
}
#检查是否重复暴露了多台服务器的多个端口
function ansible_check_multi_expose(){
    echo "对比所有服务器暴露的端口: 扫描是否存在对外重复暴露的端口..."
    #读取全部机器上暴露的非sshd端口
    \ansible all -m shell -a "sshd_port=\$(netstat -anop|grep /sshd | \
        grep -w LISTEN |awk '{print \$4}'|awk -F:  '{print \$NF}'|head -1) \
        && echo -n {{inventory_hostname}}: && ipset list ${ipset_name_of_egova_expose_ports} \
        |grep Members: -A 1000|grep -v -w \"\${sshd_port}\" |awk \
        '{printf \$0\" \"}'
    " |grep ":Members:" > /tmp/all_hosts_expose_port.txt

    for port_cnt in $(cat /tmp/all_hosts_expose_port.txt |awk -F: '{print $NF}'|\
        awk '{for(i=1;i<=NF;i++){print $i}}'|sort|uniq -c|awk '{print $2","$1}')
    do
        local port=$(echo ${port_cnt}|awk -F, '{print $1}')
        local cnt=$(echo ${port_cnt}|awk -F, '{print $2}')
        local exposed_hosts=$(cat /tmp/all_hosts_expose_port.txt \
                | awk -F"[: ]" '{for(i=1;i<=NF;i++)if($i=='${port}'){printf $1" "}}'
            )
        if [ $cnt -gt 1 ];then
            log_error "端口加固不安全: 端口${port}同时在${cnt}个服务器对外暴露[${exposed_hosts}]"
        else
            log_info "pass: 端口${port}仅暴露一次ip=${exposed_hosts}"
        fi
    done

}
#nginx扫描
function scan_nginx(){
    echo_num "检查nginx端口(仅针对已启动的nginx): "
    for port in $(netstat -anop |grep nginx |grep -w LISTEN|awk '{print $4}'|awk -F: '{print $2}')
    do
        log_info "检查nginx端口: ${port} ..."
        check_nginx_file_server ${port}
        check_nginx_with_waf ${port}
    done
    echo_num "开始查询最近两个access log file"
    check_logon_username_password
}
#tomcat扫描
function scan_tomcat(){
    echo_num "检查tomcat端口(仅针对已启动的tomcat): "
    for port in $(netstat -anop |grep java |grep -w LISTEN|awk '{print $4}'|awk -F: '{print $2}')
    do
        check_java_media_root
        check_geoserver_passwd
    done

    echo_num "检查tomcat目录(仅针对已启动的tomcat): "
    for catalina_home in $(ps -ef|grep tomcat |grep java |grep -v grep \
         |awk '{for(i=3;i<=NF;i++){if($i ~ /-Dcatalina.home=/){print $i}}}' | \
         awk -F= '{print $2}')
    do
        check_tomcat_conf_media_root ${catalina_home}
        check_tomcat_manager ${catalina_home}
    done
}
function scan_iptables_rule(){
    echo_num "检查iptables中INPUT链规则..."
    #检查是否有内部端口DROP规则
    iptables -C INPUT -p tcp -m set --match-set ${ipset_name_of_egova_local_ports} dst -j DROP 2>/dev/null
    if [ $? -gt 0 ];then
        log_error "端口加固不安全: iptables中未找到内部端口对外的DROP规则"
        log_error "请使用如下命令核对: iptables -C INPUT -p tcp -m set --match-set \
            ${ipset_name_of_egova_local_ports} dst -j DROP"
    else
        log_info "pass: iptables中存在内部端口对外拒绝的规则。"
    fi
    #查询INPUT下所有的rule
    iptables --list-rules INPUT > /tmp/iptables_chain_input.rules

    #检查DROP规则是否处于INPUT链表中最后一行
    cat /tmp/iptables_chain_input.rules |grep -E "${ipset_name_of_egova_local_ports}|${ipset_name_of_egova_vpc_nets}"| \
        tail -1 |grep "\-A INPUT -p tcp -m set --match-set ${ipset_name_of_egova_local_ports} dst -j DROP" 1>/dev/null
    if [ $? -gt 0 ];then
        log_warn "端口加固存在隐患: iptables中内部端口对外拒绝的规则的位于内部放行之前(可能将导致内部服务之间无法互通)"
        log_error "请使用如下命令核对: iptables --list-rules INPUT (核对DROP规则是否位于最后)"
    else
        log_info "pass: iptables中存在内部端口对外拒绝的规则位于最后。"
    fi
    #检查默认策略是否为ACCET
    cat /tmp/iptables_chain_input.rules |head -1 |grep "\-P INPUT ACCEPT" 1>/dev/null
    if [ $? -gt 0 ];then
        log_error "端口加固存在隐患: iptables中INPUT链默认策略不是ACCEPT(可能将导致内部服务之间无法互通)"
        log_error "请使用如下命令核对: iptables --list-rules INPUT (核对第一行是否为-P INPUT ACCEPT)"
    else
        log_info "pass: iptables中INPUT链默认策略为ACCEPT。"
    fi

    #检查是否有对vpc暴露的放行规则
    iptables -C INPUT -p tcp -m set --match-set ${ipset_name_of_egova_vpc_nets} \
        src -m set --match-set   ${ipset_name_of_egova_local_ports} dst -j ACCEPT 2>/dev/null
    if [ $? -gt 0 ];then
        log_warn "端口加固存在隐患: iptables中未找到内部端口对内部服务器的放行规则(可能将导致内部服务之间无法互通)。"
        log_warn "请使用如下命令核对: iptables -C INPUT -p tcp -m set --match-set ${ipset_name_of_egova_vpc_nets} \
                    src -m set --match-set   ${ipset_name_of_egova_local_ports} dst -j ACCEPT"
    else
        log_info "pass: iptables中存在内部端口对内部服务器的放行规则。"
    fi
    #检查是否有对外暴露端口的放行规则
    iptables -C INPUT -p tcp -m set --match-set ${ipset_name_of_egova_expose_ports} dst -j ACCEPT 2>/dev/null
    if [ $? -gt 0 ];then
        log_warn "端口加固存在隐患: iptables中未找到对外部暴露的端口规则(可能导致nginx/ssh服务无法从外部访问)。"
        log_warn "请使用如下命令核对: iptables -C INPUT -p tcp -m set --match-set ${ipset_name_of_egova_expose_ports} dst -j ACCEPT"
    else
        log_info "pass: iptables中存在对外部暴露的端口放行规则。"
    fi
}
#端口加固扫描
function scan_port_enhance(){
    check_env
    if [ $? -gt 0 ];then
        #未加固无需进行后续判断
        return 0
    fi

    check_ipset
    if [ $? -gt 0 ];then
        #未加固无需进行后续判断
        return 0
    fi
    echo_num "检查iptables和ipset服务状态"
    systemctl status iptables 2>/dev/null 1>/dev/null
    if [ $? -gt 0 ];then
        log_error "端口加固不安全: iptables服务不存在或者未启动！"
    else
        systemctl enable iptables
        log_info "pass: 服务iptables运行正常。"
    fi


    systemctl status ipset 2>/dev/null 1>/dev/null
    if [ $? -gt 0 ];then
        log_error "端口加固不安全: ipset服务不存在或者未启动！"
    else
        systemctl enable ipset
        log_info "pass: 服务ipset运行正常。"
    fi

    #检查iptables规则
    scan_iptables_rule

    #检查未加固的端口
    echo_num "检查未增强的端口"
    check_without_enhanced_port
    #检查暴露的端口是否是nginx或者sshd
    echo_num "检查对外暴露的端口"
    check_exposed_port_is_safe


}

#扫描sshd服务
function scan_sshd(){
    check_ssh_pwd_auth
}

#交互式配置
function local_scan(){
    scan_nginx
    scan_tomcat
    scan_sshd
    scan_port_enhance
    log_info "----------扫描完成。开始服务器login权限账户检测---------"
    scan_logon_username  # 本地模式不传递参数
}

function ansible_scan(){
    echo "分发脚本..."
    \ansible all -m copy -a "src=${_cur_shell_path} dest=/tmp/${_cur_shell_name} mode=0755"
    \ansible all -m shell -a "/tmp/${_cur_shell_name} local"
    ansible_check_multi_expose
    log_info "扫描完成。"
}

function main(){
    if [ $# -eq 0 ];then
        echo "参数有误！"
        help
        exit 1
    fi
    case $1 in
    "local")
        set +e
        local_scan
        set -e
        ;;
    "ansible")
        # 批量处理
        set +e
        which ansible 2>/dev/null 1>/dev/null
        if [ $? -gt 0 ];then
            log_error "未找到ansible命令！"
            exit 1
        fi
        ansible_scan
        set -e
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
