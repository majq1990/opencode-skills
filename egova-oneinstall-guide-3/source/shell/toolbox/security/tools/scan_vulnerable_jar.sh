#!/bin/bash
set -u
USER="`whoami`"
_cur_shell_path=$0
_cur_shell_name=${_cur_shell_path##*/}
_cur_shell_dir=${_cur_shell_path%/*}
if [ "${_cur_shell_name}" == "${_cur_shell_dir}" ];then
    _cur_shell_dir=$(pwd)
fi

_scan_jar_version="v1.0.0-20231211"

#除了基于进程扫描外，额外增加的扫描目录
ex_scan_dir="/egova/web,/egova/apps/,/egova/egova_apps/,/egova/ZTnew,/egova_apps,/egova_docker,/egova/egova_docker,/egova/datatransfer,/egova/auth-center"

#jar最低版本列表，自动升级时准备的jar可以比这个版本高
scan_jar_name=(
    fastjson-1.2.83.jar
    commons-fileupload-1.5.jar
    commons-text-1.10.0.jar
    axis-1.4.jar
    axis-saaj-1.4.jar
    commons-collections-3.2.2.jar
    commons-collections4-4.1.jar
    log4j-web-2.17.1.jar
    log4j-api-2.17.1.jar
    log4j-jcl-2.17.1.jar
    log4j-core-2.17.1.jar
    log4j-slf4j-impl-2.17.1.jar
    jackson-databind-2.12.1.jar #升级为2.12.4
    postgresql-42.4.1.jar
    h2-2.2.220.jar
    xstream-1.4.20.jar
    rocketmq-client-4.3.0.jar
    rocketmq-common-4.3.0.jar
    rocketmq-logging-4.3.0.jar
    rocketmq-remoting-4.3.0.jar
    poi-ooxml-4.1.2.jar
    poi-ooxml-schemas-4.1.2.jar
    poi-scratchpad-4.1.2.jar
    #仅扫描
    mysql-connector-java-8.0.30.jar
    # spring暂不扫描
    # spring-web-5.3.26.RELEASE.jar
    # spring-webmvc-5.3.26.RELEASE.jar
)
#仅扫描不做自动替换的jar（已注释，因为升级功能已禁用）
: <<'ONLY_SCAN_JARS_COMMENT'
only_scan_jars=(
    "mysql-connector-java|cetus字符集可能存在不兼容问题,需先升级cetus"
    "jackson-databind|[335925]疑似2.9版本的jackson无法直接升级2.12,联系研发更新相关代码"
    "poi-ooxml|poi升级需研发确认是否同步升级代码"
    "poi-ooxml-schemas|poi升级需研发确认是否同步升级代码"
    "poi-scratchpad|poi升级需研发确认是否同步升级代码"
    "xstream|xstream升级需研发确认是否同步升级代码"
#    "spring-web|spring升级需发确认是否同步升级代码"
#    "spring-webmvc|spring升级需研发确认是否同步升级代码"

)
ONLY_SCAN_JARS_COMMENT
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
function log_warn(){
    local msg="  WARN: $1"
    echo "$(color_text "$msg" "33")"
}
function log_error(){
    local msg="  ERROR: $1"
    echo "$(color_text "$1" "31")"
}

#-v接收min_jars="${scan_jar_name[@]}"
cat > /tmp/${USER}_check_jar_version.awk <<EOF
function get_jar_name(full_name){
    size1=split(full_name,arr,"-");
    _jar_name=""
    for(i=1;i<size1;i++){
        if(i<size1-1){
            _jar_name=_jar_name""arr[i]"-"
        }else{
            _jar_name=_jar_name""arr[i];
        }
    }
    return _jar_name;
}
function get_jar_version_arr(full_name,jar_version_arr){
    size1=split(full_name,arr,"-");
    jar_info=arr[size1];
    size2=split(jar_info,jar_version_arr,".");
    delete jar_version_arr[size2];
}
function check_jar_version_less_than(jar_version_arr,min_version_jar_full_name){
    min_jar_name=get_jar_name(min_version_jar_full_name);
    get_jar_version_arr(min_version_jar_full_name,min_arr);
    for(j=1;j<=length(jar_version_arr);j++){
        if(jar_version_arr[j] < min_arr[j]){
            return 1;
        }else if(jar_version_arr[j] > min_arr[j]){
            return 0;
        }
    }
    return 0;
}
BEGIN{}
{
    size=split(min_jars,min_jar_arr," ");
    jar_version=\$NF;
    jar_name=get_jar_name(jar_version);
    get_jar_version_arr(jar_version,jar_version_arr);
    hit=0;
    for(k=1;k<=size;k++){
        min_jar_name=get_jar_name(min_jar_arr[k]);
        if( min_jar_name == jar_name){
            if(check_jar_version_less_than(jar_version_arr,min_jar_arr[k]) == 1){
                print \$0","jar_name","jar_version;
            }
            break;
        }
    }
}
END{}
EOF


#find /home/egova/code/wizdom-urban-v14-framework -name "*.jar"  \
#    |awk -F/ -v \
#    min_jars="${scan_jar_name[*]}" -f /tmp/root_check_jar_version.awk

#exit 0

rst_file_error=/tmp/${USER}_scan_jars_error.log
rst_file_detail=/tmp/${USER}_scan_jars_detail.log
rst_file_warn=/tmp/${USER}_scan_jars_warn.log
rst_file_safe=/tmp/${USER}_scan_jars_safe.log
tmp_container_pid=/tmp/${USER}_scan_jars_java_container_pid.txt


#从pid中提取-jar后面的参数
function get_jar_file_by_pid(){
   local pid=$1
   ps -ef|grep java |awk '{if($2=='$pid'){after_jar=0;for(i=3;i<=NF;i++){if($i=="-jar"){after_jar=1}else if(after_jar==1 && $i ~ /\.jar$/ ){print $i}}}}'
}

#从pid中提取-cp以及-classpath后面的参数
function get_cp_file_by_pid(){
   local pid=$1
   ps -ef|grep java |awk '{if($2=='$pid'){for(i=3;i<NF;i++){if($i=="-cp"){printf $(i+1)":"} else if($i=="-classpath"){printf $(i+1)":"}}}}'
}
#扫描jar中是否含有漏洞jar
function check_fatjar(){
    local file=$1
    which jar 2>/dev/null 1>/dev/null
    if [ $? -gt 0 ];then
        log_error "由于当前服务器未安装java环境,扫描微服务中的jar,请手工确认${file}"
        return
    fi

    jar -tf $file 2>/dev/null |awk -F/ -v \
     min_jars="${scan_jar_name[*]}" -f /tmp/${USER}_check_jar_version.awk > /tmp/${USER}_scan_jars_fatjar_tmp_hit.txt
    if [ $(cat /tmp/${USER}_scan_jars_fatjar_tmp_hit.txt|wc -l) -gt 0 ];then
        log_error "[ ${file} ]中含有高危漏洞的第三方jar!"
        cat /tmp/${USER}_scan_jars_fatjar_tmp_hit.txt|awk '{printf $0"|"}'| \
         xargs -I {} echo "FATJAR ${file} {}" >> ${rst_file_detail}
    fi
}
#扫描目录中是否含有漏洞jar
function check_dir(){
    local dir=$1
    find ${dir} -name "*.jar" 2>/dev/null \
        |awk -F/ -v \
        min_jars="${scan_jar_name[*]}" -f /tmp/${USER}_check_jar_version.awk > /tmp/${USER}_scan_jars_dir_tmp_hit.txt
    if [ $(cat /tmp/${USER}_scan_jars_dir_tmp_hit.txt|wc -l) -gt 0 ];then
      log_error "[ ${dir} ]中含有高危漏洞的第三方jar!"
#      cat /tmp/dir_tmp_hit.txt
      cat /tmp/${USER}_scan_jars_dir_tmp_hit.txt|xargs -I {} echo "DIR - {}" >> ${rst_file_detail}
    fi
}
#从进程的jar文件中提取目标jar
function scan_by_proc_jar(){
   local pid=$1
   local container_dir=$2
   local file_name=$(get_jar_file_by_pid $pid)
   if [[ "$file_name" != /* ]];then
       local cwd=$(ls -l /proc/$pid/cwd 2>/dev/null|awk  '{print $NF}')
       file_name="$cwd/${file_name}"
   fi
#   echo ${container_dir}/${file_name}
   if [ -f "${container_dir}/${file_name}" ];then
        check_fatjar "${container_dir}/${file_name}"
   fi
}

#从进程的classPath中提取$grep_reg文件名
function scan_by_proc_classpath(){
   local pid=$1
   local cfiles=$(get_cp_file_by_pid $pid)
   local files=""
   for f in $(echo $cfiles|sed "s/:/ /g")
   do
       check_dir $f
   done
}

#检查tomcat下发布的所有服务目录
function scan_tomcat_apps(){
    local pid=$1
    local c_home=$(ps -ef|grep java|awk '{if($2=='$pid'){print $0}}'|awk -F"[= ]" '{for(i=3;i<NF;i++){if($i=="-Dcatalina.home"){print $(i+1)}}}')
    if [ ! -z "${c_home}" ];then
        local tfiles=""
        for dir in $(cat ${c_home}/conf/Catalina/localhost/*.xml 2>/dev/null|grep docBase|awk -F"[= ]" '{for(i=0;i<NF;i++){if($i=="docBase"){print $(i+1)}}}' |sed "s/\"//g")
        do
            check_dir ${dir}
        done

        for dir in $(cat  ${c_home}/conf/server.xml |grep "<Context"  |grep -v  "<\!--" | grep docBase|awk -F"[= ]" '{for(i=0;i<NF;i++){if($i=="docBase"){print $(i+1)}}}' |sed "s/\"//g")
        do
            check_dir ${dir}
        done
    fi
}
#检查非容器进程
function scan_host_java_proc(){
   echo_num "检查主机java进程（微服务类会自动解压判断，请确保微服务已启动）"
   for pid in $(ps -ef|grep "java "|grep -v grep|awk '{print $2}')
   do
        local exe=$(ls -l /proc/$pid/exe |sed "s/ (deleted)//g"|awk -F/ '{print $NF}')
        if [ $(grep -w $pid ${tmp_container_pid}|wc -l) -eq 0 ] && [ "${exe}" == "java" ];then
            scan_by_proc_jar $pid ""
            scan_tomcat_apps $pid
            scan_by_proc_classpath $pid
        fi
   done
}
#检查容器
function scan_containers(){
   echo_num "检查容器"
   # 判断
   which docker 2>/dev/null 1>/dev/null
   if [ $? -gt 0 ];then
      log_info "未找到docker命令,跳过容器检查"
      return;
   fi

   for c in $( docker ps |awk '{print $1}'|grep -v CONTAINER )
   do
      local pid=$(docker top $c |grep "java "|awk '{print $2}'|head -1)
      if [ ! -z "$pid" ];then
            echo ${pid} >> ${tmp_container_pid}
            local dir=$(docker inspect $c |grep MergedDir |awk '{print $NF}'|sed "s/\"//g;s/,//g")
            log_info "容器[$c]中包含java进程"
            check_dir $dir
            scan_by_proc_jar $pid $dir
      fi
   done
}

#检查是否为仅扫描的jar
function check_is_only_scan_jar(){
    local jar_name=$1
    for o_jar in ${only_scan_jars[@]}
    do
        local o_jar_name=$(echo ${o_jar}|awk -F"|" '{print $1}')
        if [ "${o_jar_name}" == "${jar_name}" ];then
            echo ${o_jar}|awk -F"|" '{print $2}'
            return
        fi
    done
    echo ""
}
# 注释掉检查是否可替换函数
: <<'CHECK_CAN_REPLACE_COMMENT'
function check_can_replace(){
    local jar_name=$1
    local only_scan_info="$(check_is_only_scan_jar ${jar_name})"
    if [ "${only_scan_info}" != "" ]; then
        log_warn "  ${jar_name}暂不进行自动替换: ${only_scan_info}"
        return 1
    fi
    if [  $(ls ${_cur_shell_dir}/src/update_jars/${jar_name}-*.jar 2>/dev/null |wc -l) -eq 0 ]; then
        log_error "  ${jar_name}未下载无漏洞版本，无法自动替换！"
        return 2
    fi
    return 0
}
CHECK_CAN_REPLACE_COMMENT


#扫描某个目录
function scan_dir(){
    local dirs="$1"
    if [ "$dirs" == "" ]; then
        dirs="${ex_scan_dir}"
    fi
    OLD_IFS="$IFS"
    IFS=","
    arr_dir=($dirs)
    IFS="$OLD_IFS"
    result=""
    echo_num "检查主机目录(只基于文件名扫描，不解压微服务的jar包)"
    local options="$(cat ${rst_file_detail} |grep -v ^$|awk '{printf " -o -name "$4}')"
    local cmd=" -name 'fastjson-*.jar' $options"
    for dir in ${arr_dir[@]}
    do
        if [ -d "$dir" ];then
            log_info "扫描主机目录: $dir"
            check_dir $dir
        fi
    done
}

#打印报告
function report(){
    echo_num "本次扫描报告如下: $(date "+%Y-%m-%d %H:%M:%S")"
    local jar_cnt=$(cat ${rst_file_detail} |grep "^DIR"|awk '{print $3}'|awk -F, '{print $2,$1}'|sort|uniq|wc -l)
    local fatjar_cnt=$(cat ${rst_file_detail} |grep "^FATJAR"|sort|uniq|wc -l)
    let cnt=jar_cnt+fatjar_cnt
    echo "检测脚本版本号: ${_scan_jar_version}"
    log_error "漏洞总数量: ${cnt}"

    log_error "-----漏洞jar包数量: ${jar_cnt}---------"
    cat  ${rst_file_detail}  |grep "^DIR"|awk '{print $3}'|awk -F, '{print "  "$2,$1}'|sort|uniq

    log_error "-----含有漏洞的微服务数量: ${fatjar_cnt}---------"
    cat  ${rst_file_detail}  |grep "^FATJAR"|sort|uniq| \
      awk '{print $2" :";size=split($3,arr,"|");for(i=1;i<=size;i++){split(arr[i],arr2,",");print "    "arr2[3]}}'

    log_warn "可根据文件${rst_file_detail}再次查看扫描结果。"
}
#扫描入口
function scan(){
    echo -n "" > ${rst_file_error}
    echo -n "" > ${rst_file_detail}
    echo -n "" > ${rst_file_warn}
    echo -n "" > ${rst_file_safe}
    echo -n "" > ${tmp_container_pid}
    local _scan_dir="$1"
    scan_containers
    scan_host_java_proc
    scan_dir "${_scan_dir}"
    report
    log_info "done!"
}
#获取修正后的jar文件名
: <<'GET_FIX_JAR_NAME_COMMENT'
function get_fix_jar_name(){
    local jar_name=$1
    if [ $(ls ${_cur_shell_dir}/src/update_jars/${jar_name}-*.jar| wc -l) -eq 1 ];then
        #前缀匹配只有一个时直接返回
        ls ${_cur_shell_dir}/src/update_jars/${jar_name}-*.jar|awk -F/ '{print $NF}'
    else
        #当有多个时，只能返回后面带有版本号的匹配文件，如log4j-web-1.1.2.jar，不再支持如rc、snapshot等
        ls ${_cur_shell_dir}/src/update_jars/${jar_name}-*.jar|grep -E "${jar_name}-[0-9\.]*\.jar" \
          | awk -F/ '{print $NF}' |head -1
    fi
}
GET_FIX_JAR_NAME_COMMENT
#自动修复
: <<'AUTO_REPLACE_COMMENT'
function auto_replace(){
    echo_num "开始自动修复"
    if [ -f ${_cur_shell_dir}/src/update_jars.tar.gz ] && [ ! -d ${_cur_shell_dir}/src/update_jars ];then
        tar -xzf ${_cur_shell_dir}/src/update_jars.tar.gz -C ${_cur_shell_dir}/src/
        rm -rf ${_cur_shell_dir}/src/update_jars.tar.gz
    fi
    local cnt=$(cat ${rst_file_detail} |grep -v "^$" |sort|uniq|wc -l)
    if [  $cnt -gt 0 ];then

        #备份目录
        backup_dir=/egova/scan_jars_backup/$(date +%Y%m%d_%H%M)
        mkdir -p ${backup_dir}
        #逐个遍历
        cat ${rst_file_detail} |grep -v ^$|sort|uniq |while read line
        do
            local type=$(echo $line|awk '{print $1}')
            local src_file=""
            local match_file=$(echo $line|awk '{print $3}')

            if [ "${type}" == "DIR" ];then
                src_file=$(echo $line|awk '{print $3}'|awk -F, '{print $1}')
            else
                src_file=$(echo $line|awk '{print $2}')
            fi
            if [ ! -f "$src_file" ];then
                continue
            fi

            if [ "${type}" == "FATJAR" ];then
                which jar 2>/dev/null 1>/dev/null
                if [ $? -gt 0 ];then
                    log_error "由于当前服务器未安装java环境,无法自动替换微服务中的jar,请手工处理${src_file}"
                    continue
                fi

                log_info "处理微服务：${src_file} ..."
                #备份
                backname=${src_file##*/}_$(date +%s)_$RANDOM
                cp -f ${src_file} ${backup_dir}/${backname}

                cd ${backup_dir}
                newname=${src_file##*/}_new
                rm -rf temp/ && mkdir temp/
                unzip -q ./${backname} -d temp/
                cd temp/

                for match_info in $(echo ${match_file}|awk -F"|" '{for(i=1;i<=NF;i++){print $i}}')
                do
                    local jar_name=$(echo ${match_info}|awk -F, '{print $2}')
                    local old_jar_version=$(echo ${match_info}|awk -F, '{print $3}')
                    #检查是否不能直接修复
                    check_can_replace ${jar_name}
                    if [ $? -gt 0 ];then
                        continue
                    fi

                    local fix_name="$(get_fix_jar_name ${jar_name})"
                    sed -i "s/${old_jar_version}/${fix_name}/g" BOOT-INF/*.idx 2>/dev/null
                    rm -rf BOOT-INF/lib/${old_jar_version}
                    log_info "  ${old_jar_version}升级至${fix_name}。"
                    \cp -f ${_cur_shell_dir}/src/update_jars/${fix_name} BOOT-INF/lib/
                done
                jar -cfM0 ${newname} ./
                echo "src=${src_file} back=${backname}" >> ${backup_dir}/backup.info
                cd ../
                cp temp/${newname} ${backup_dir}/

#                echo TODO cp -f ${newname} ${src_file}
                cp -f ${newname} ${src_file}
                chmod a+rw ${src_file}
                rm -rf temp/
                log_info "  处理完成。"
            else
                log_info "升级文件 ${src_file}  ..."
                local jar_name=$(echo ${match_file}|awk -F, '{print $2}')
                #检查是否不能直接修复
                check_can_replace ${jar_name}
                if [ $? -gt 0 ];then
                    continue
                fi
                #备份
                backname=${src_file##*/}_$(date +%s)_$RANDOM
                cp -f ${src_file} ${backup_dir}/${backname}
                local fix_name="$(get_fix_jar_name ${jar_name})"
                echo "src=${src_file} back=${backname} new=${fix_name}" >> ${backup_dir}/backup.info
#                echo TODO \cp -f ${_cur_shell_dir}/src/update_jars/${fix_name} ${src_file%/*}
#                echo TODO rm -rf ${src_file}
                \cp -f ${_cur_shell_dir}/src/update_jars/${fix_name} ${src_file%/*}
                chmod a+rw ${src_file%/*}/${fix_name}
                rm -rf ${src_file}
                log_info "  已升级至${fix_name}。"
            fi
        done
        log_warn "修改完成,请手工重启所有java服务以及docker容器！！"
        log_warn "如需恢复某一个文件，可以在目录${backup_dir}找到原始文件，backup.info文件记录了原始文件信息和备份文件信息。"
    else
        log_warn "${rst_file_detail}未记录任何漏洞。"
    fi
    log_info "自动替换完成，请重启对应的服务！"

}
AUTO_REPLACE_COMMENT


function help() {
    cat <<EOF
    脚本用途: 扫描本机的java进程、/egova目录中的tomcat和微服务,是否存在漏洞的jar
      $0 local                       : 交互式扫描(用于单机执行)
    如下分步骤执行(可用于ansible批量执行):
      $0 scan                       : 仅扫描,不做修改,结果记录到${rst_file_detail}
      $0 scan 路径参数                  : 扫描指定路径,多个路径用逗号分隔如 $0 scan "/egova,/root"
      # $0 update                    : 根据扫描结果(${rst_file_detail}执行jar升级操作,升级后需要手工重启对应的服务(已禁用))
EOF
}

function main(){
    if [ $# -eq 0 ];then
        help
        exit 1
    fi
    case $1 in
        local)
            scan "${ex_scan_dir}"
            # 注释掉升级提示和功能
: <<'LOCAL_UPGRADE_COMMENT'
            read -p "是否自动对执行结果进行升级,输入yes进行升级: " user_select
            if [ "${user_select}" == "yes" ]; then
                auto_replace
            fi
LOCAL_UPGRADE_COMMENT
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
            # 注释掉升级提示和功能
            : <<'ANSIBLE_UPGRADE_COMMENT'
            read -p "是否自动对执行结果进行升级,输入yes进行升级: " user_select
ANSIBLE_UPGRADE_COMMENT
            log_info "拷贝脚本和配置..."
            \ansible all -m file -a "name=/tmp/toolbox/scan_jars/src state=directory"
            \ansible all -m copy -a "src=${_cur_shell_path} dest=/tmp/toolbox/scan_jars/${_cur_shell_name} mode=0755"
            # 注释掉升级包拷贝
            : <<'UPGRADE_JARS_COPY_COMMENT'
            \ansible all -m copy -a \
                "src=${_cur_shell_dir}/src/update_jars.tar.gz dest=/tmp/toolbox/scan_jars/src/ mode=0755"
UPGRADE_JARS_COPY_COMMENT
            \ansible all -m shell -a "/tmp/toolbox/scan_jars/${_cur_shell_name} scan ${ex_scan_dir}"
            # 注释掉升级执行
            : <<'ANSIBLE_UPDATE_COMMENT'
            if [ "${user_select}" == "yes" ];then
                \ansible all -m shell -a "/tmp/toolbox/scan_jars/${_cur_shell_name} update"
                log_info "升级完成，请重启tomcat后，二次执行扫描！ "
            fi
ANSIBLE_UPDATE_COMMENT
            ;;
        "scan")
            #执行扫描
            if [ $# -ge 2 ];then
                scan "$2"
            else
                log_error "参数有误！请传入待扫描的目录"
            fi
            ;;
        "update")
            # 注释掉升级功能
            : <<'UPDATE_COMMAND_COMMENT'
            #执行升级
            auto_replace
UPDATE_COMMAND_COMMENT
            log_info "升级功能已禁用，请仅使用扫描功能"
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
