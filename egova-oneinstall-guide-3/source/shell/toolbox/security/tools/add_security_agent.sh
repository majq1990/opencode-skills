#!/bin/bash
_cur_shell_path=$0
_cur_shell_name=${_cur_shell_path##*/}
_cur_shell_dir=${_cur_shell_path%/*}
if [ "${_cur_shell_name}" == "${_cur_shell_dir}" ]; then
    _cur_shell_dir=$(pwd)
fi
#微服务只对一体化增加，tomcat则全部增加
micro_services_reg="service-pub-core\.jar|egova-service-gis-map-.*\.jar"
find_services_cmd="-o -name service-pub-core.jar -o -name egova-service-gis-map-*.jar"
#tomcat搜索路径,多个用逗号分隔
tomcat_search_dirs="/egova"
deploy_dir="/egova/web/egova-security-agent"
rst_enhance_tomcat=/tmp/enhance_tomcat.log
rst_enhance_ms=/tmp/enhance_ms.log


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
#从pid中提取-jar后面的参数
get_jar_file_by_pid() {
    local pid=$1
    ps -ef | grep java | awk '{if($2=='$pid'){after_jar=0;for(i=3;i<=NF;i++){if($i=="-jar"){after_jar=1}else if(after_jar==1 && $i ~ /\.jar$/ ){print $i}}}}'
}
#从pid中提取-javaagent参数
check_has_security_agent_by_pid() {
    local pid=$1
    local agent_info="$(ps -ef | grep java | awk '{if($2=='$pid'){before_jar=1;for(i=3;i<=NF;i++){if(before_jar==1){if($i=="-jar"){before_jar=0}; if($i ~ /-javaagent:\S*egova-security-agent\.jar$/ ){print $i}}}}}' | awk -F: '{print $2}')"
    if [ "${agent_info}" != "" ] && test -f ${agent_info}; then
        echo 1
    else
        echo 0
    fi
}
#获取程序所在路径
get_cwd_by_pid() {
    local pid=$1
    local pid_cwd="$(ls -l /proc/${pid}/cwd | awk '{print $NF}')"
    test -d ${pid_cwd} && echo "${pid_cwd}" || echo ""
}
#从java进程中获取tomcat目录
get_catalina_path() {
    local pid=$1
    local catalina_home="$(ps -ef | grep java | awk '{if($2=='$pid'){for(i=3;i<=NF;i++){if($i ~ /-Dcatalina.home=/){print $i}}}}' | awk -F= '{print $2}')"
    if [ "${catalina_home}" != "" ] && test -f ${catalina_home}/bin/catalina.sh; then
        echo "${catalina_home}/bin/catalina.sh"
    else
        echo ""
    fi
}
#判断是否为指定微服务
is_matched_microservice() {
    local pid=$1
    local jar_name="$(get_jar_file_by_pid $pid)"
    [ $(echo ${jar_name} | grep -E "${micro_services_reg}" | wc -l) -gt 0 ] && echo 1 || echo 0
}
#检查主机进程
check_host_java_proc() {
    echo_num "检查主机java进程"
    for pid in $(ps -ef | grep "java " | grep -v grep | awk '{print $2}'); do
        local exe=$(ls -l /proc/$pid/exe | sed "s/ (deleted)//g" | awk -F/ '{print $NF}')
        local pid_cwd="$(get_cwd_by_pid $pid)"
        if [ "${exe}" == "java" ] && [ "${pid_cwd}" != "" ]; then
            local cataline_path="$(get_catalina_path $pid)"
            if [ "${cataline_path}" != "" ]; then
                log_info "主机进程[$pid]为待增强的tomcat服务,路径${cataline_path}"
            elif [ $(is_matched_microservice $pid) -eq 1 ]; then
                log_info "主机进程[$pid]为待增强的微服务,路径${pid_cwd}"
                local jar_name="$(get_jar_file_by_pid $pid)"
                if [ "${jar_name:0:1}" == "/" ]; then
                    echo "${jar_name}" >>${rst_enhance_ms}
                else
                    echo "${pid_cwd}/${jar_name}" >>${rst_enhance_ms}
                fi
            fi
        fi
    done
}
#向tomcat注入agent
function add_agent_for_tomcat() {
    local catalina_path=$1
    local path="${catalina_path%/*}"
    log_info "处理${catalina_path}..."

    local last_agent_info="$(cat ${catalina_path} | grep -E "\s*(-javaagent:\S*/egova-security-agent.jar)" -o | awk -F: '{print $2}')"
    if [ "${last_agent_info}" != "" ] && test -f ${last_agent_info}; then
        log_info "${catalina_path}已经配置过安全增强参数,无需处理！"
        return
    fi
    local line="$(grep -n '^JAVA_OPTS=\"\s*-server' ${catalina_path} | head -1 | awk -F: '{print $1}')"
    [ "$line" == "" ] && line="$(grep -n '^JAVA_OPTS="\$' ${catalina_path} | head -1 | awk -F: '{print $1}')"
    if [ "${line}" == "" ]; then
        # 增加到-server前方
        log_info "路径[${catalina_path}]搜索JAVA_OPTS失败,请手工添加启动-javaagent:${deploy_dir}/egova-security-agent.jar \
        -Degova.security.agent.config=${deploy_dir}/security.conf参数"
    else
        cp -f ${catalina_path} ${catalina_path}_$(date +%s)_$RANDOM
        sed -i "${line}s|JAVA_OPTS=\"|JAVA_OPTS=\"-javaagent:${deploy_dir}/egova-security-agent.jar -Degova.security.agent.config=${deploy_dir}/security.conf |g" ${catalina_path}
    fi
}
#向微服务注入agent
function add_agent_for_microservice() {
    local ms_path=$1
    local gis=$2
    local path="${ms_path%/*}"
    log_info "处理${ms_path}..."
    for line_info in $(grep -Hn -E "nohup\s*java\s*" ${path}/*.sh 2>/dev/null| awk -F: '{print $1":"$2}' 2>/dev/null); do
        local file="$(echo $line_info | awk -F: '{print $1}')"
        if [ $(grep -E "${micro_services_reg}" $file |wc -l) -eq 0 ];then
#            echo "ignore $file"
            continue
        fi
        log_info "检测到微服务重启脚本${line_info},增加参数..."

        local line="$(echo $line_info | awk -F: '{print $2}')"
        local last_agent_info="$(cat ${file} | grep -E "\s*(-javaagent:\S*/egova-security-agent.jar)" -o | awk -F: \
        '{print $2}' |head -1)"
#        echo last_agent_info="${last_agent_info}"
        if [ "${last_agent_info}" != "" ] && test -f ${last_agent_info}; then
            log_info "${file}已经配置过安全增强参数,无需处理！"
            continue
        fi
        cp -f ${file} ${file}_$(date +%s)_$RANDOM
        sed -i "${line}s|nohup\s*java\s*|nohup java -javaagent:${deploy_dir}/egova-security-agent.jar -Degova.security.agent.config=${deploy_dir}/security.conf |g" ${file}
    done
    for line_info in $(grep -Hn -E "^JAVA_OPTIONS\s*=\s*\"" ${path}/*.env 2>/dev/null | awk -F: '{print $1":"$2}' \
    2>/dev/null); do
        local file="$(echo $line_info | awk -F: '{print $1}')"
        if [ $(grep -E "${micro_services_reg}" $file |wc -l) -eq 0 ];then
#            echo "ignore $file"
            continue
        fi
        log_info "检测到微服务环境变量${line_info},增加参数..."
        local line="$(echo $line_info | awk -F: '{print $2}')"
        local last_agent_info="$(cat ${file} | grep -E "\s*(-javaagent:\S*/egova-security-agent.jar)" -o | awk -F: '{print $2}')"
        if [ "${last_agent_info}" != "" ] && test -f ${last_agent_info}; then
            log_info "${file}已经配置过安全增强参数,无需处理！"
            continue
        fi
        cp -f ${file} ${file}_$(date +%s)_$RANDOM
        sed -i "${line}s|JAVA_OPTIONS\s*=\s*\"|JAVA_OPTIONS=\"-javaagent:${deploy_dir}/egova-security-agent.jar -Degova.security.agent.config=${deploy_dir}/security.conf |g" ${file}
    done
}
#目录扫描
function scan_dir() {
    local dirs="$1"
    if [ "$dirs" == "" ]; then
        dirs="${tomcat_search_dirs}"
    fi
    OLD_IFS="$IFS"
    IFS=","
    arr_dir=($dirs)
    IFS="$OLD_IFS"
    result=""
    echo_num "检查主机目录"
    for dir in ${arr_dir[@]}; do
        if [ -d "$dir" ]; then
            log_info "扫描主机目录: $dir"
            local cmd="find $dir -type f -name catalina.sh ${find_services_cmd}"
            for file in $(eval "$cmd"); do
                if [[ " $file " =~ "/catalina.sh " ]]; then
                    log_info "检测到tomcat: $file"
                    echo $file >>${rst_enhance_tomcat}
                else
                    log_info "检测到微服务: $file"
                    echo $file >>${rst_enhance_ms}
                fi
            done
        fi
    done
}

function report() {
    echo_num "本次扫描报告如下: $(date "+%Y-%m-%d %H:%M:%S")"
    log_info "-----tomcat路径如下---------"
    cat ${rst_enhance_tomcat} | grep -v "^$" | sort | uniq
    log_info "-----命中的微服务路径如下---------"
    cat ${rst_enhance_ms} | grep -v "^$" | sort | uniq

}

function gen_default_conf(){
    local gis="$1"
    mkdir -p ${deploy_dir}
    cat > ${deploy_dir}/security.conf <<EOF
egova.security.agent.gis.enable=$gis
egova.security.agent.gis.users=egova2018,egova2022,egovagis,egova2015
egova.security.agent.mis.users=egova2015,egovaadmin,egovagis
EOF
    if [ -f ${_cur_shell_dir}/egova-security-agent.jar ];then
        \cp -f ${_cur_shell_dir}/egova-security-agent.jar ${deploy_dir}/ 2>/dev/null
    else
        \cp -f ${_cur_shell_dir}/src/egova-security-agent.jar ${deploy_dir}/ 2>/dev/null
    fi
    chmod a+rx -R ${deploy_dir}
}
function auto_enhance() {
    local quiet="$1"
    local gis="$2"
    gen_default_conf ${gis}
    local cnt=$(cat ${rst_enhance_tomcat} ${rst_enhance_ms} | grep -v "^$" | sort | uniq | wc -l)
    if [ $cnt -gt 0 ]; then
        if [ "$quiet" != "quiet" ]; then
            echo_num "开始增强"
            read -p "检查到有${cnt}个文件需要处理，输入yes自动处理，输入其他跳过: " user_select
            if [ "${user_select}" != "yes" ]; then
                log_info "退出，请手工处理如下文件"
                log_info "done!"
                cat ${rst_enhance_tomcat}  ${rst_enhance_ms}| grep -v "^$" | sort | uniq | awk '{print $1}'
                exit 0
            fi
        fi
        set -u
        cat ${rst_enhance_tomcat} | grep -v "^$" | sort | uniq | while read file; do
            log_info "增强tomcat..."
            if [ ! -f "$file" ]; then
                continue
            fi
            add_agent_for_tomcat $file $gis
        done
        cat ${rst_enhance_ms} | grep -v "^$" | sort | uniq | while read file; do
            log_info "增强微服务..."
            if [ ! -f "$file" ]; then
                continue
            fi
            add_agent_for_microservice $file $gis
        done
        log_info "修改完成,请手工重启所有tomcat以及微服务！！"
        set +u

    fi

}
function check_env() {
    if [ "$USER" != "root" ]; then
        log_error "请使用root用户执行此脚本"
        exit 1
    fi
    if [ ! -f ${_cur_shell_dir}/egova-security-agent.jar ] && [ ! -f ${_cur_shell_dir}/src/egova-security-agent.jar ];
    then
        log_error "未找到egova-security-agent.jar,请上传到目录: ${_cur_shell_dir}"
        exit 1
    fi
}
#
function scan() {
    local dirs="$1"
    echo -n "" >${rst_enhance_tomcat}
    echo -n "" >${rst_enhance_ms}
    echo_num "开始扫描..."
    check_env
    check_host_java_proc
    scan_dir "${dirs}"
    report
}
function enhance() {
    check_env
    if [ "$2" == "--disable-gis" ];then
        auto_enhance "$1" "false"
    else
        auto_enhance "$1" "true"
    fi

}
function verify() {
    log_info "检查正在运行的服务是否已经增强..."
    for pid in $(ps -ef | grep "java " | grep -v grep | awk '{print $2}'); do
        local exe=$(ls -l /proc/$pid/exe | sed "s/ (deleted)//g" | awk -F/ '{print $NF}')
        local pid_cwd="$(get_cwd_by_pid $pid)"
        if [ "${exe}" == "java" ] && [ "${pid_cwd}" != "" ]; then
            local cataline_path="$(get_catalina_path $pid)"
            if [ "${cataline_path}" != "" ]; then
                if [ $(check_has_security_agent_by_pid $pid) -eq 0 ]; then
                    log_error "tomcat进程${pid}无安全增强参数,请确认${cataline_path}已经追加-javaagent参数并且已重启"
                else
                    log_info "tomcat进程${pid}安全增强成功"
                fi
            elif [ $(is_matched_microservice $pid) -eq 1 ]; then
                if [ $(check_has_security_agent_by_pid $pid) -eq 0 ]; then
                    local jar_name="$(get_jar_file_by_pid $pid)"
                    if [ "${jar_name:0:1}" != "/" ]; then
                        jar_name="${pid_cwd}/${jar_name}"
                    fi
                    log_error "微服务进程${pid}无安全增强参数,请确认${jar_name}所在目录中的.sh和.env已经追加-javaagent参数并且已重启"
                else
                    log_info "微服务进程${pid}安全增强成功"
                fi
            fi
        fi
    done
}

function help() {

    cat <<EOF
    脚本用途: 扫描本机的java进程、/egova目录中的tomcat和微服务,增加-javaagent参数
      $0 auto                       : 交互式扫描+增强修改(用于单机执行)
    如下分步骤执行(可用于ansible批量执行):
      $0 scan                       : 仅扫描,不做增强修改,结果记录到${rst_enhance_tomcat}和${rst_enhance_ms}
      $0 scan 路径参数                  : 扫描指定路径,多个路径用逗号分隔如 $0 scan "/egova,/root"
      $0 enhance                    : 根据扫描结果(/tmp中的两个文件)执行增强修改操作,增强后需要手工重启对应的服务
      $0 enhance --disable-gis      : 增强对gis失效
      $0 verify                      : 检查是否有未增强的进程（用于重启后验证）
      $0 ansible_help                : 获取ansible参考命令
EOF
}

function ansible_help() {
    cat <<EOF
    ansible示例脚本:（假设脚本$0 和 egova-security-agent.jar下载到了/root路径）
    \ansible all -m copy -a "src=/root/add_security_agent.sh dest=/tmp/ mode=0755"
    \ansible all -m copy -a "src=/root/egova-security-agent.jar dest=/tmp/"
    \ansible all -m shell -a "/tmp/add_security_agent.sh scan /egova"
    #gis不增强
    \ansible all -m shell -a "/tmp/add_security_agent.sh enhance --disable-gis"
    #gis也增强
    \ansible all -m shell -a "/tmp/add_security_agent.sh enhance"
    \ansible all -m shell -a "/tmp/add_security_agent.sh verify"
EOF
}

function main(){
    case $1 in
        local)
            main "auto"
            ;;
        auto)
            scan
            read -p "是否对GIS服务进行增强(不升级GIS将无法登录),输入yes进行增强: " gis_enable
            if [ "${gis_enable}" == "yes" ]; then
                enhance "prompt" "--enable-gis"
            else
                enhance "prompt" "--disable-gis"
            fi
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
            read -p "是否对GIS服务进行增强(不升级GIS将无法登录),输入yes进行增强: " gis_enable
            log_info "拷贝脚本和配置..."
            \ansible all -m file -a "name=/tmp/toolbox/add_security_agent/src state=directory"
            \ansible all -m copy -a "src=${_cur_shell_path} dest=/tmp/toolbox/add_security_agent/${_cur_shell_name} mode=0755"
            \ansible all -m copy -a "src=${_cur_shell_dir}/src/egova-security-agent.jar dest=/tmp/toolbox/add_security_agent/src/egova-security-agent.jar"
            \ansible all -m shell -a "/tmp/toolbox/add_security_agent/${_cur_shell_name} scan ${tomcat_search_dirs}"
            if [ "${gis_enable}" == "yes" ];then
                #gis不增强
                \ansible all -m shell -a "/tmp/toolbox/add_security_agent/${_cur_shell_name} enhance"
            else
                 #gis也增强
                \ansible all -m shell -a "/tmp/toolbox/add_security_agent/${_cur_shell_name} enhance --disable-gis"
            fi
            log_info "增强完成，请重启tomcat后，使用如下命令验证: "
            log_info "\ansible all -m shell -a \"/tmp/toolbox/add_security_agent/${_cur_shell_name} verify\""
            ;;
        "check")
            #环境检查
            check_env
            ;;
        "scan")
            #执行扫描
            if [ $# -ge 2 ];then
                scan "$2"
            else
                log_error "参数有误！请传入待扫描的目录"
            fi
            ;;
        "enhance")
            #执行加固
            if [ $# -ge 2 ];then
                enhance "quiet" "$2"
            else
                enhance "quiet" ""
            fi
            ;;
        ansible_help)
            ansible_help
            ;;
        verify)
            verify
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

# check to see if this file is being run or sourced from another script
_is_sourced() {
    # https://unix.stackexchange.com/a/215279
    [ "${#FUNCNAME[@]}" -ge 2 ] \
        && [ "${FUNCNAME[0]}" = '_is_sourced' ] \
        && [ "${FUNCNAME[1]}" = 'source' ]
}

if ! _is_sourced; then
    main "$@"
fi