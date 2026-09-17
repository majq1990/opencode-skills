#!/bin/bash
shopt -s expand_aliases

VER_NUM=1.0.1
ONEINSTALL_VER=${VER_NUM}_04
VER=$ONEINSTALL_VER
SSH_PORT=22
SSH_USER=$USER
SSH_USER_HOME=$HOME
SSH_KEY=$HOME/.ssh/id_rsa

EGOVA_REPO_HOME=/egova/opt/repo
OPTION_FILE=./option_config.yml
. shell/tools/tool_utils.sh
release_ver=$(get_distribution_info)
release_name=$(echo "${release_ver}"|awk -F'_' '{print $1"_"$NF}')
if is_kylin || is_uos || is_anolis; then
  sed -i 's/NAME=.*/NAME="'"${release_name}"'"/' /etc/os-release
fi


_cur_shell_path=$0
_cur_shell_name=${_cur_shell_path##*/}
_cur_shell_dir=${_cur_shell_path%/*}
if [ "${_cur_shell_name}" == "${_cur_shell_dir}" ]; then
    _cur_shell_dir=$(pwd)
fi

alias ansible="ansible -i $_cur_shell_dir/ansible/inventory/hosts.yml"

# 显示运行选项
function display_selection() {
    Echo_Yellow "请选择运行参数，首次执行脚本步骤：1)先创建本地源，选择0——> 2)安装ansible，选择1——> 3)选择待安装服务器，选择2："
    yq '.[] | select(.display=="1") | key ' ${OPTION_FILE} | while read key; do
        local name=$(yq ".${key}.name" ${OPTION_FILE})
        local choice_index=$(yq ".${key}.choice_index" ${OPTION_FILE})
        echo "${choice_index}: ${name}"
    done
    echo "q: 退出"
    read -p "请选择: " Select
    case "${Select}" in
    0)
        cd shell/tools/
        if is_ubuntu; then
             ./i_create_repo_apt.sh $EGOVA_REPO_HOME
        else
           ./i_create_repo_yum.sh $EGOVA_REPO_HOME
        fi
        if [ $? -ne 0 ]; then
            Echo_Red "安装本地源失败, 请提案件给技术支持部，补充缺失依赖包！！！"
            Echo_Red "上传补充缺失依赖包至/egova/onekey_install/oneinstall_v2/src/repo/xx/xxx 然后执行安装脚本，重新构建本地源！！！"
            exit 1
        fi
        ./i_tools.sh
        # 主控节点工具软件安装，预留3
        cd ../../
        # 处理本机挂载问题
        ./shell/include/automount.sh
        ;;
    1)
        .  shell/tools/tool_utils.sh
        if is_ubuntu ; then
          apt install -y ansible
        elif is_anolis && [ "${release_ver}" != "anolis_7_x86" ] ; then
          yum install -y ansible-core --disablerepo="*" --enablerepo="egova-local" 1>/dev/null 2>/dev/null
          ansible-galaxy collection install src/bin/postgresql/collections/community-general-9.4.0.tar.gz
          ansible-galaxy collection install src/bin/postgresql/collections/community-postgresql-3.6.1.tar.gz
        else
          yum install -y ansible --disablerepo="*" --enablerepo="egova-local" 1>/dev/null 2>/dev/null
        fi

        local cfg_file=/etc/ansible/ansible.cfg
        sed -i "s/#gathering.*/gathering = explicit/g" ${cfg_file}
        # 开启日志
        sed -i s@"^#log_path = /var/log/ansible.log"@"log_path = /var/log/ansible.log"@g ${cfg_file}
        sed -i s@"^#display_skipped_hosts = True"@"display_skipped_hosts = False"@g ${cfg_file}
        Echo_Green "安装完成"
        echo "设置当前机器为主控机..."
        get_local_ip
        yq -i '.ansible_master_ip="'$LOCAL_IP'"' ansible/group_vars/all.yml
        # 主控机安装ntp-server
        cd shell/tools
        ./i_ntp.sh
        cd ../../
        Echo_Yellow "ntp-server已安装, 请确保服务器时间和互联网的时间一致！！！如果有互联网环境可直接用ntpdate ntp.aliyun.com"
        # 主控机安装JDK（新增）
        cd shell/tools
        ./i_jdk.sh
        cd ../../
        Echo_Green "JDK已安装到主控节点"
        ;;
    2)
        cd shell/include
        . tool_hosts.sh
        choose_add_or_delete_hosts
        cd ../../
        ;;
    3)
        display_server_select "app_service"
        ;;
    4)
        cd shell/tools
        ./i_software.sh
        cd ../../
        ;;
    101)
        # 配置出口nginx
        cd shell/tools
        ./i_config_outlet_nginx.sh
        cd ../../
        ;;
    m)
        cd shell/tools
        ./i_modify_db_connection.sh
        cd ../../
        ;;
    b)
        cd shell/tools
        ./i_benchmark_check.sh
        cd ../../
        ;;
    p)
        cd shell/tools
        ./i_patch_os.sh
        cd ../../
        ;;
    s)
        cd shell/toolbox/security
        ./main.sh
        cd ../../../
        ;;
    q)
        echo "退出安装"
        return 0
        ;;
    i)
        ./update.sh
        ;;
    *)
        Echo_Red "选择错误！"
        ;;
    esac
    display_selection
}

function display_server_select(){
    local key=$1
    local count=$(yq ".${key}.sub_options | length " ${OPTION_FILE})
    local index=0
	  Echo_Yellow "请选择安装服务类型："
	  while [ $index -lt $count ]; do
        local server_name=$(yq ".${key}.sub_options[${index}].name" ${OPTION_FILE})
        ((index=index+1))
        echo "${index}: ${server_name}"
    done
    echo "q: 退出"
    read -p "请选择: " Select
    case "$Select" in
    1)
        display_install_type_select ${key} $(($Select - 1))
        ;;
    2)
        display_install_type_select ${key} $(($Select - 1))
        ;;
    [3-9])
        local idx=$(($Select - 1))
        local type=$(yq ".${key}.sub_options[${idx}].category" ${OPTION_FILE})
        cd shell/tools
        ./i_microservice.sh "${type}"
        cd ../../
        ;;
    10)
        display_install_type_select ${key} $(($Select - 1))
        ;;
    q)
        echo "退出安装"
        return 0
        ;;
    *)
        Echo_Red "选择错误！"
        display_server_select
        ;;
    esac
}

function display_install_type_select(){
    local key=$1
    local index=$2
    local count=$(yq ".${key}.sub_options[${index}].sub_options | length " ${OPTION_FILE})
    local sub_index=0
	  Echo_Yellow "请选择安装方式："
	  while [ $sub_index -lt $count ]; do
        local name=$(yq ".${key}.sub_options[${index}].sub_options[${sub_index}].name" ${OPTION_FILE})
        local type=$(yq ".${key}.sub_options[${index}].sub_options[${sub_index}].type" ${OPTION_FILE})
        local config_file=$(yq ".${key}.sub_options[${index}].sub_options[${sub_index}].config_file" ${OPTION_FILE})
        ((sub_index=sub_index+1))
        echo "${sub_index}: ${name}"
    done
    echo "q: 退出"
    read -p "请选择: " Select
    local selected_type=$(yq ".${key}.sub_options[${index}].sub_options[$(($Select-1))].type" ${OPTION_FILE})
    local selected_config_file=$(yq ".${key}.sub_options[${index}].sub_options[$(($Select-1))].config_file" ${OPTION_FILE})
    local deploy_config_file="../../ansible/inventory/${selected_config_file}"
    case "$Select" in
    1)
        cd shell/tools
        if [ "${selected_type}" = "one" ]; then
            ./i_one_software.sh ${deploy_config_file}
        elif [ "${selected_type}" = "multi" ]; then
           ./i_multi_software.sh ${deploy_config_file}
        elif [ "${selected_type}" = "tiny" ]; then
            ./i_tiny_software.sh ${deploy_config_file}
        fi
        cd ../../
        ;;
    2)
        cd shell/tools
        ./i_multi_software.sh ${deploy_config_file}
        cd ../../
        ;;
    3)
        cd shell/tools
        ./i_tiny_software.sh ${deploy_config_file}
        cd ../../
        ;;
    q)
        echo "退出安装"
        exit 0
        ;;
    *)
        Echo_Red "选择错误！"
        display_install_type_select
        ;;
    esac
}

# yq/jq使用二进制文件方式安装
function add_yq() {
    type yq > /dev/null 2>&1
    local isExist=$?
    if [[ $isExist = 0 ]]; then
       local yqpath=`which yq`
    else
       local yqpath="/usr/bin/yq"
    fi
    if test -f src/bin/yq; then
        \cp src/bin/yq $yqpath
        chmod +x $yqpath
    fi
    type jq > /dev/null 2>&1
    local isjqExist=$?
    if [[ $isjqExist = 0 ]]; then
       local jqpath=`which jq`
    else
       local jqpath="/usr/bin/jq"
    fi
    if test -f src/bin/jq; then
        \cp src/bin/jq $jqpath
        chmod +x $jqpath
    fi
}

# 拷贝minio客户端
function add_mc() {
    if test -f src/bin/mc && ! test -f /usr/bin/mc; then
        \cp src/bin/mc /usr/bin/
        chmod +x /usr/bin/mc
    fi
}
function check_os_release() {
   if [[ ! "${release_ver}" =~ (centos|ubuntu|uos|kylin|openEuler|anolis) ]]; then
     echo "发现${release_ver}不支持的操作系统，请检查系统版本"
     exit 1
  elif [[ ${release_ver} == "uos_20_x86" ]] && [[ $(cat /etc/product-info |egrep "1060e|1060a|1070a" |wc -l)  -eq 0 ]] ; then
       echo "统信x86架构目前只适配uos 20 1060e、1060a、1070a版本，查看版本信息 cat /etc/product-info "
       exit 1
  elif [[ ${release_ver} == "uos_20_arm" ]] && [[ $(cat /etc/product-info |egrep "1060a|1060e|1070a" |wc -l)  -eq 0 ]] ; then
       echo "统信ARM架构目前只适配uos 20 1060a、1070a版本，查看版本信息 cat /etc/product-info "
       exit 1
  elif [[ ${release_ver} == "ubuntu_20_x86" ]] ; then
       ubuntu_version=$(lsb_release -r | awk '{print $2}')
       if [[ "$ubuntu_version" != "20.04" ]]; then
         echo "ubuntu x86架构目前只适配Ubuntu 20.04 LTS版本，查看版本信息 cat /etc/os-release "
         exit 1
      fi
  elif [[ ${release_ver} == "kylin_V10_x86" ]] && [[ -f /etc/.productinfo ]]  ; then
     productinfo=$(cat /etc/.productinfo)
     if ! [[ $productinfo == *"SP3"* ]]; then
       echo "银河麒麟V10 x86架构目前只适配kylin_V10 SP3 版本，查看版本信息 /etc/.productinfo"
       exit 1
     fi
  elif [[ -f /etc/os-release ]] && is_openEuler ; then
       productinfo=$(cat /etc/os-release)
        if ! [[ $productinfo == *"LTS"* ]]  ; then
            echo "未发现欧拉操作系统 LTS 版本，请检查系统版本"
            exit 1
        fi
  fi

}
#运行入口
function run() {
    check_os_release
    add_yq
    add_mc
    display_selection
}
mkdir -p $SSH_USER_HOME/.ssh
sudo -u#0 mkdir -p /egova/conf
sudo -u#0 mkdir -p /egova/log
sudo -u#0 mkdir -p /egova/temp
sudo -u#0 mkdir -p temp
sudo -u#0 mkdir -p temp/gen
#首次执行脚本先创建egova用户
cd shell/include
. ./i_security_os_patch.sh
create_user_egova >/dev/null 2>&1
cd ../../
. shell/include/tool_echo.sh
# 菜单选项配置
if [ $# = 0 ]; then
    clear
    echo "+------------------------------------------------------------------------+"
    echo "|           信创一键部署 v$VER for ${release_ver}, Written by Egova         |"
    echo "+------------------------------------------------------------------------+"
else
    echo 自动安装模式
fi
run $@
