#!/bin/bash
# 对应主菜单：安装软件的工具箱

SOFTWARE_CONFIG_FILE=../../ansible/inventory/software_tools.yml
metadata_file=../../ansible/inventory/metadata.yml
. ../include/tool_echo.sh
function display_all_software() {
    Echo_Yellow "请选择服务器ip:"
    local count=$(yq '.softwares|length' ${SOFTWARE_CONFIG_FILE})
    let i=1
    while [ $i -le $count ]; do
        local name=$(yq ".softwares[$((i - 1))].name" ${SOFTWARE_CONFIG_FILE})
        local desc="$(yq ".softwares[$((i - 1))].desc" ${SOFTWARE_CONFIG_FILE})"
        #先判断是否存在name.yml
        local ids=0
        if [ -f ../../ansible/inventory/template/$name.yml ]; then
            local ids=$(wc -l ../../ansible/inventory/template/$name.yml | awk '{print $1}')
        fi
        #判断ids是否等于0
        if [ $ids -eq 0 ]; then
            local ip=""
            echo "$i: ${name} (${desc}) ${ip}"
        else
            for id in $(seq 1 $ids)
            do
                if [ $id == 1 ]; then
                    if [ -f ../../ansible/inventory/template/$name.yml ]; then
                        local ip=$(yq ".host" ../../ansible/inventory/template/${name}.yml)
                    fi
                    echo "$i: ${name} (${desc}) ${ip}"
                else
                    local ip=$(yq ".host_$ids" ../../ansible/inventory/template/${name}.yml)
                    echo "  ${name}从节点$id (${desc}) ${ip}"
                fi
            done
        fi
        let i=i+1
    done
    echo "y: 确认配置，下一步"
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
    y)
        ./i_multi_software.sh
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

function show_params() {
    local index=$1
    let index=index-1
    local type=$(yq ".softwares[${index}].name" ${SOFTWARE_CONFIG_FILE})
    local file=../../ansible/inventory/template/${type}.yml
    touch $file
    local params_len=$(yq ".softwares[${index}].params|length" ${SOFTWARE_CONFIG_FILE})
    if [ ${params_len} -gt 0 ]; then
        Echo_Yellow "输入序号更改相应配置:"
        local param_index=0
        local idx=1
        while [ ${param_index} -lt ${params_len} ]; do
            local name=$(yq ".softwares[${index}].params[${param_index}].name" ${SOFTWARE_CONFIG_FILE})
            local display=$(yq ".softwares[${index}].params[${param_index}].display" ${SOFTWARE_CONFIG_FILE})
            local last=$(yq ".${name}" ${file})
            local desc=$(yq ".softwares[${index}].params[${param_index}].desc" ${SOFTWARE_CONFIG_FILE})
            if [ "$last" == "null" ] || [ "$last" == "" ]; then
                last=$(yq ".softwares[${index}].params[${param_index}].default" ${SOFTWARE_CONFIG_FILE})
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
        local name=$(cat ${SOFTWARE_CONFIG_FILE} | yq ".softwares[${index}].params[]|select(.display==1)" -o json | jq '.' -cr | sed -n "${param_input}p" | jq -cr '.name')
        local desc=$(cat ${SOFTWARE_CONFIG_FILE} | yq ".softwares[${index}].params[]|select(.display==1)" -o json | jq '.' -cr | sed -n "${param_input}p" | jq -cr '.desc')
        Echo_Yellow "${desc}"
        read -p "请输入[${desc}]: " param_value
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
function run() {
    SOFTWARE_SELECT_INDEX=-1
    SOFTWARE_SELECT_TYPE=""
    SOFTWARE_SELECT_HOST=""
    SOFTWARE_SELECT_PARAMS_LENGTH=1
    display_all_software
    if [ ${SOFTWARE_SELECT_INDEX} -ge 0 ]; then
        cd ../include
        . tool_hosts.sh
        . tool_metadata.sh
        choose_one_host "${SOFTWARE_SELECT_TYPE}" "SOFTWARE_SELECT_HOST" "single"
        #将上个命令的状态码保存到rst中,0表示成功，非0表示失败
        local rst=$?
        local ip=$(yq e '.all.hosts.'${SOFTWARE_SELECT_HOST}'.ansible_ssh_host' ../../ansible/inventory/hosts.yml)
        yq -i '.host = "'${ip}'"' ../../ansible/inventory/template/${SOFTWARE_SELECT_TYPE}.yml
        #将选择的IP地址保存到文件中
        if [ $rst -eq 0 ]; then
            # 保存元数据
            if [ ${SOFTWARE_SELECT_PARAMS_LENGTH} -gt 0 ]; then
                local hosts="$(echo ${SOFTWARE_SELECT_HOST} | sed "s/,/ /g")"
                for h in ${hosts}; do
                    save_metadata ${SOFTWARE_SELECT_TYPE} ${h}
                    save_app_hosts ${SOFTWARE_SELECT_TYPE} ${h}
                done
            fi
        fi
        run
    fi
}

run
