#!/bin/bash
# 对应主菜单：安装软件的工具箱

SOFTWARE_CONFIG_FILE=../../ansible/inventory/software_tools.yml
metadata_file=../../ansible/inventory/metadata.yml
. ../include/tool_echo.sh
function display_all_software() {
    Echo_Yellow "选择需要部署的软件:"
    local count=$(yq '.software_tools|length' ${SOFTWARE_CONFIG_FILE})
    if [ $count -eq 0 ]; then
        Echo_Red "未配置任何软件"
        return 0
    fi
    let i=1
    while [ $i -le $count ]; do
        local name=$(yq ".software_tools[$((i - 1))].name" ${SOFTWARE_CONFIG_FILE})
        local desc="$(yq ".software_tools[$((i - 1))].desc" ${SOFTWARE_CONFIG_FILE})"
        echo "$i: ${name} (${desc})"
        let i=i+1
    done
    echo "q: 退出"
    local input="ERROR"
    read -p "请输入: " input

    case $input in
    [0-9]*)
        if [ $input -gt $count ]; then
            Echo_Red "选择错误！"
            display_all_software
            return 0
        fi
        show_params "$input"
        ;;
    q)
        return 0
        ;;
    *)
        Echo_Red "选择错误！"
        display_all_software
        return 0
        ;;
    esac
}

function select_install_cetus() {
    Echo_Yellow "安装选项："
    echo "1: 安装业务库代理"
    echo "2: 安装统计库代理"
    echo "0: 返回上层"
    Install_Select=999
    while [ "${Install_Select}" != "y" ]; do
       read -p "请选择: " Install_Select
       if [ "$Install_Select" == "1" ];then
           Install_Select="y"
           db_type="biz"
       elif [ "$Install_Select" == "2" ];then
           Install_Select="y"
           db_type="stat"
       elif [ "$Install_Select" == "0" ];then
           Install_Select="y"
           display_all_software
       else
           Echo_Red "输入错误！"
       fi
    done
    return 0;
}
function show_params() {
    local index=$1
    let index=index-1
    local type=$(yq ".software_tools[${index}].name" ${SOFTWARE_CONFIG_FILE})
    local file=../../ansible/inventory/template/${type}.yml
    touch "$file"
    local params_len=$(yq ".software_tools[${index}].params|length" ${SOFTWARE_CONFIG_FILE})
    if [ ${type} == "cetus" ]; then
       select_install_cetus
    elif [ ${params_len} -gt 0 ]; then
        Echo_Yellow "输入序号更改相应配置:"
        local param_index=0
        local idx=1
        while [ ${param_index} -lt ${params_len} ]; do
            local name=$(yq ".software_tools[${index}].params[${param_index}].name" ${SOFTWARE_CONFIG_FILE})
            local display=$(yq ".software_tools[${index}].params[${param_index}].display" ${SOFTWARE_CONFIG_FILE})
            local last=$(yq ".${name}" ${file})
            local desc=$(yq ".software_tools[${index}].params[${param_index}].desc" ${SOFTWARE_CONFIG_FILE})
            if [ "$last" == "null" ] || [ "$last" == "" ]; then
                last=$(yq ".software_tools[${index}].params[${param_index}].default" ${SOFTWARE_CONFIG_FILE})
            fi
            yq -i '.'${name}' = "'${last}'"' $file
            if [ "$display" == "1" ]; then
                echo "${idx}: ${desc} 当前值: ${last}"

                let idx=idx+1
            fi
            let param_index=param_index+1
        done
    else
        SOFTWARE_SELECT_INDEX=${index}
        SOFTWARE_SELECT_TYPE=${type}
        return 0
    fi
    echo "y: 确认配置，下一步"
    echo "q: 退出"
    local param_input="ERROR"
    read -p "输入序号更改相应配置: " param_input

    case ${param_input} in
    [0-9]*)
        if echo "$param_input"|[ ! -n "`sed -n '/^[0-9][0-9]*$/p'`" ] ;then
            Echo_Red "输入错误，只能输入数字！"
            show_params "$((index + 1))"
            return 0
        fi
        if [ ${param_input} -gt ${params_len} ]; then
            Echo_Red "选择错误！"
            show_params "$((index + 1))"
            return 0
        fi
        local name=$(cat ${SOFTWARE_CONFIG_FILE} | yq ".software_tools[${index}].params[]|select(.display==1)" -o json | jq '.' -cr | sed -n "${param_input}p" | jq -cr '.name')
        local desc=$(cat ${SOFTWARE_CONFIG_FILE} | yq ".software_tools[${index}].params[]|select(.display==1)" -o json | jq '.' -cr | sed -n "${param_input}p" | jq -cr '.desc')
        Echo_Yellow "${desc}"
        local options=$(cat ${SOFTWARE_CONFIG_FILE} | yq ".software_tools[${index}].params[]|select(.display==1)" -o json | jq '.' -cr | sed -n "${param_input}p" | jq -cr '.options')
        if [ "$options" != "null" ]; then
            # 读取用户输入的下标
            temp_index=0
            while read -r option; do
                echo "  $temp_index. $option"
                temp_index=$((temp_index + 1))
            done < <(echo "$options" | jq -r '.[]')
            while true; do
                read -p "请选择: ${desc}: " selected_temp_index
                # 检查输入是否为数字
                if ! [[ "$selected_temp_index" =~ ^[0-9]+$ ]]; then
                    Echo_Red "输入错误，只能输入数字！"
                    continue
                fi
                # 检查输入的数字是否在有效范围内
                if [ "$selected_temp_index" -lt 0 ] || [ "$selected_temp_index" -ge "$temp_index" ]; then
                    Echo_Red "选择错误，输入的序号不在有效范围内！"
                    continue
                fi
                break
            done
            # 根据下标获取选中的选项值
            param_value=$(echo "$options" | jq -r ".[$selected_temp_index]")
        else
            read -p "请输入[${desc}]: " param_value
        fi
        yq -i '.'${name}' = "'${param_value}'"' $file
        show_params "$((index + 1))"
        ;;
    q)
        exit 0
        ;;
    y | Y)
        SOFTWARE_SELECT_INDEX=${index}
        SOFTWARE_SELECT_TYPE=${type}
        SOFTWARE_SELECT_PARAMS_LENGTH=${params_len}
        return 0
        ;;
    *)
        Echo_Red "选择错误！"
        show_params "$((index + 1))"
        return 0
        ;;
    esac
}
# 检查服务器上是否已部署对应端口的服务
function check_software_installed() {
    local type=$1
    local hosts="$2"
    local file=../../ansible/inventory/template/${type}.yml
    if ! test -e $file; then
        return 0
    fi
    local port=$(yq '.port' $file)
    if [ "$port" == "null" ]; then
        return 0
    fi
    local hosts="$(echo ${SOFTWARE_SELECT_HOST} | sed "s/,/ /g")"
    local rst=0
    for h in ${hosts}; do
        local count=$(cat ${metadata_file} | yq '(.'${type}'.[]| select(.host=="'${h}'" and .port=="'${port}'" and .status == "success")) |length' | wc -l)
        let rst=$count+$rst
        if [ $count -gt 0 ]; then
            Echo_Red "主控机上的配置文件检查到${h}上已安装过port=${port}的$type服务！"
        fi
    done
    if [ $rst -gt 0 ];then
        Echo_Yellow "是否强制安装,将覆盖已有配置？"
        local forceInput=""
        read -p "输入y强制安装: " forceInput
        if [ "$forceInput" == "y" ];then
            for h in ${hosts}; do
                Echo_Green "清除[host=$h,port=$port]"
                yq -i '(.'${type}'.[]| select(.host=="'${h}'" and .port=="'${port}'" and .status == "success")) |= .status="delete"' ${metadata_file}
            done
            return 0
        else
            return $rst
        fi
    fi
}
function run() {
    SOFTWARE_SELECT_INDEX=-1
    SOFTWARE_SELECT_TYPE=""
    SOFTWARE_SELECT_HOST=""
    SOFTWARE_SELECT_PARAMS_LENGTH=0
    display_all_software
    if [ ${SOFTWARE_SELECT_INDEX} -ge 0 ]; then
        cd ../include
        . tool_hosts.sh
        . tool_metadata.sh
        choose_one_host "${SOFTWARE_SELECT_TYPE}" "SOFTWARE_SELECT_HOST" "single"
        # TODO 同一服务器，同一端口，重复覆盖提醒
        if [ "${SOFTWARE_SELECT_HOST}" != "" ]; then
            if [ $SOFTWARE_SELECT_PARAMS_LENGTH -eq 0 ]; then
                ansible-playbook -i ../../ansible/inventory/hosts.yml -e "host=${SOFTWARE_SELECT_HOST} db_type=${db_type}"   ../../ansible/install_${SOFTWARE_SELECT_TYPE}.yml
                Echo_Yellow "ansible执行日志见/var/log/ansible.log"
            else
                #检查host和端口
                check_software_installed "${SOFTWARE_SELECT_TYPE}" "${SOFTWARE_SELECT_HOST}"
                if [ $? -gt 0 ];then
                    cd ../tools
                    display_all_software
                    return 0
                fi
                ansible-playbook -i ../../ansible/inventory/hosts.yml -e "host=${SOFTWARE_SELECT_HOST} db_type=${db_type}"  -e "@../../ansible/inventory/template/${SOFTWARE_SELECT_TYPE}.yml" ../../ansible/install_${SOFTWARE_SELECT_TYPE}.yml
                Echo_Yellow "ansible执行日志见/var/log/ansible.log"
            fi
            local rst=$?
            if [ $rst -eq 0 ]; then
                # 保存元数据
                if [ ${SOFTWARE_SELECT_PARAMS_LENGTH} -gt 0 ]; then
                    local hosts="$(echo ${SOFTWARE_SELECT_HOST} | sed "s/,/ /g")"
                    for h in ${hosts}; do
                        local size=$(yq '.'$SOFTWARE_SELECT_TYPE' | length ' ${metadata_file})
                        (( size++ )) || true
                        save_metadata "software" ${h} ${SOFTWARE_SELECT_TYPE} ${size} "success"
                        save_app_hosts ${SOFTWARE_SELECT_TYPE} ${h}
                    done
                fi
            else
                Echo_Red "${SOFTWARE_SELECT_TYPE}安装失败！"
            fi
        fi
        cd ../tools
    fi
}
run
