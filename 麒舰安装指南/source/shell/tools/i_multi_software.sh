#!/bin/bash
# 对应主菜单：分布式部署
server_config_file=$1



. ../include/tool_metadata.sh
. ../include/tool_multi.sh ${server_config_file}
metadata_file=../../ansible/inventory/metadata.yml
# 定义关联数组
declare -A HOST_CHOICE_MAP
deploy_status_flag=0
function input_server_ip() {
    Select=999
    while [ "${Select}" != "y" ]; do
        modify_server_ip "$@"
    done
}
function is_biz_flag(){
  local selected_index=$1
  local biz_flag
  local length=$(echo -n "$selected_index" | wc -c)
  if [[ "$length" -eq 1 ]]; then
     biz_flag=0
  elif [[ ! "$selected_index" =~ ^[0-9]+$ && "$length" -eq 2 ]]; then
     biz_flag=0
  else
     biz_flag=1
  fi
  echo "$biz_flag"
}
# 获取multi_server.yml中的key：ip_db_biz
function get_web_by_index() {
    local selected_index=$1
    local biz_flag=$(is_biz_flag $selected_index )
    if [[ "$biz_flag" -eq 1 ]]; then
      selected_index="${selected_index:0:-1}"
    fi
    local web_server_name=$(echo "$index_key_json" | jq -r ".\"$selected_index\"")
    if [ "$web_server_name" != "null" ] && [ -n "$web_server_name" ]; then
        echo "$web_server_name"
    else
        echo "无效的索引号"
    fi
}
# 获取ip
function get_ip_by_index() {
    local key_index=$1
    local server_ip=$(echo "$index_server_json" | jq -r ".\"$key_index\"")
    if [ "$server_ip" != "null" ] && [ -n "$server_ip" ]; then
            echo "$server_ip"
    else
        echo "无效的索引号"
    fi
}
# 删除 server_config_file和metadata_file的相关配置
function delete_server_config() {
    local web_server_name=$1
    local server_ip=$2
    local selected_index=$3

    # 检查参数是否为空
    if [[ -z "$web_server_name" || -z "$server_ip" || -z "$selected_index" ]]; then
        Echo_Red "Missing required parameters"
        return 1
    fi

    # 检查文件是否存在
    if [[ ! -f ${server_config_file} ]]; then
        Echo_Red "File ${server_config_file} does not exist"
        return 1
    fi

    # 检查是否是业务服务器
    local is_biz_server=$(is_biz_flag $selected_index)

    # 检查键是否存在
    local key_exists=$(yq "has(\"${web_server_name}\")" ${server_config_file})
    if [[ "$key_exists" == "false" ]]; then
        Echo_Red "Key '${web_server_name}' does not exist in ${server_config_file}"
        return 1
    fi
    local last_digit=${selected_index: -1}
    local i=$((last_digit-1))
    local master_host_node=$(get_master_host $web_server_name)
    local slave_host_node=$(get_slave_host $web_server_name $i)
    local types=($(yq ".${web_server_name}.modules[].type" ${server_config_file}))
    local sub_types=($(yq ".${web_server_name}.modules[].sub_type" ${server_config_file}))

    # 删除 ${server_config_file} host
    if [[ "${is_biz_server}" -gt 0 ]]; then
        echo "删除 ${web_server_name} 的 ${slave_host_node} 服务器"
        yq -i 'del(.'"${web_server_name}"'.hosts.slave[] | select(. == "'${slave_host_node}'"))' ${server_config_file}
    else
        echo "删除 ${web_server_name} 的 ${master_host_node} 服务器"
        yq -i '.'"${web_server_name}"'.hosts.master = ""' ${server_config_file}
    fi

    # 部署状态初始化
    yq -i '.'"${web_server_name}"'.deploy_status_flag = 0' ${server_config_file}

    # 删除 metadata_file 服务信息
    for type in "${types[@]}"; do
        key_exists=$(yq "has(\"${type}\")" ${metadata_file})
        if [[ "$key_exists" == "false" ]]; then
            continue
        fi
        yq -i 'del(.'"${type}"'."'${sub_types[$i]}'"[] | select(.ip == "'${server_ip}'"))' ${metadata_file}
    done

    Echo_Green "$server_ip 已删除"
    return 0
}

function modify_server_ip() {
    Echo_Yellow "请配置服务器IP(为*代表必填,黄色表示已部署的应用)："
    local input_index=$1
    local index=1
    local choices=""
    local choice_names=""
    local keys=($(yq 'keys | .[]' $server_config_file)) # 获取所有主键
    local index_key_json="{"
    local index_server_json="{"

    # 显示主节点信息（主节点不依赖 sub_flag）
    for key in "${keys[@]}"; do
       local name=$(yq ".${key}.name" ${server_config_file})
       local sub_flag=$(yq ".${key}.sub_flag" ${server_config_file})
       local need_flag=$(yq ".${key}.need_flag" ${server_config_file})
       local choice_index=$(yq ".${key}.choice_index" ${server_config_file})
       local deploy_status_flag=$(yq ".${key}.deploy_status_flag" ${server_config_file})

       # 主节点信息展示（不考虑 sub_flag 的值）
       display_server_ip_one ${choice_index} ${name} ${key} ${sub_flag} ${need_flag} ${deploy_status_flag}
       choices="$choices ${choice_index}"
       choice_names="$choice_names ${key}"
       index_key_json+="\"${choice_index}\":\"${key}\","
       let "index=index+1"
    done

    index_key_json="${index_key_json%,}}"
    index_server_json="${index_server_json%,}}"
    # 提供主选项
    echo "a: 增加从节点"
    echo "y: 确认配置，继续安装"
    Echo_Red "N: 删除对应服务器"
    echo "q: 返回上级菜单"

    read -p "请选择: " Select

    # 如果选择增加从节点
    if [[ "${Select}" == "a" ]]; then
        display_sub_menu
    fi

    case "${Select}" in
    y|Y)
        check_server_notnull
        check_server_norepeat
        check_web_master_slave
        check_tdengine_separate
        if [ "$NotNullResult" == "0" ] || [ "$NoRepeatResult" == "0" ] || [ "$web_master_slave_result" == "0" ];then
            Select="999"
        else
            Select="y"
        fi
        ;;
    n|N)
        read -p "请选择待删除的服务器: " selected_index
        get_ip_by_index $selected_index
        local web_server_key=$(get_web_by_index $selected_index )
        local host_id=$(get_ip_by_index $selected_index)
        delete_server_config $web_server_key $host_id $selected_index
        modify_server_ip
        ;;
    q|Q)
        echo "退出安装"
        exit 0
        ;;
    [1-9] | x[1-5] | x10 | x11 | x12)
        # 验证选择是否有效
        local is_valid=$(is_valid_choice_index "${Select}")
        if [ "$is_valid" == "true" ]; then
            choose_and_set_master_host "${Select}"
        else
            Echo_Red "无效的选择: ${Select}，请重新输入"
            Select="999"
        fi
        ;;
    m | m[1-9] | s | s[1-9] | s10 | s11 | s12)
        # 验证选择是否有效
        local is_valid=$(is_valid_choice_index "${Select}")
        if [ "$is_valid" == "true" ]; then
            choose_and_set_master_host "${Select}"
        else
            Echo_Red "无效的选择: ${Select}，请重新输入"
            Select="999"
        fi
        ;;
    x | x6 | x8 | x9)
        local target_key=$(get_key_by_choice_index $Select)
        if [ -n "$target_key" ]; then
            set_mis_associated_host "$target_key" 1
        else
            Echo_Red "无效的选择: ${Select}，请重新输入"
            Select="999"
        fi
        ;;
    x7)
        set_gis_associated_host "ip_web_gisserver" 1
        ;;
    *)
        Select="999"
    esac
}

display_sub_menu() {
    echo "显示从节点信息："
    local sub_keys=($(yq '.[] | select(.sub_flag == 1) | key' ${server_config_file}))
    for key in "${sub_keys[@]}"; do
        local name=$(yq ".${key}.name" ${server_config_file})
        local choice_index=$(yq ".${key}.choice_index" ${server_config_file})
        echo "a${choice_index}: 增加${name}（从节点）"
        index_key_json+="\"${choice_index}\":\"${key}\","
    done
    echo "q: 退出安装"
    read -p "请选择从节点: " Select
    # 在此处继续处理选择的从节点配置
    case "${Select}" in
    a[1-9] | ax[1-5] | as | as[2-4])
        # 这里进行后续的从节点配置，比如选择服务器等
        choose_and_set_slave_host ${Select:1} 0
        display_sub_menu
        ;;
    [1-5][1-9])
        choose_and_set_slave_host ${Select:0:1} ${Select:1:1}
        display_sub_menu
        ;;
    x[2-4][1-9])
        choose_and_set_slave_host ${Select:0:2} ${Select:2:1}
        display_sub_menu
        ;;
    q|Q)
        Echo_Green "所有从节点增加完成，返回上级菜单"
        modify_server_ip
        ;;
    *)
        Echo_Red "无效选择，请重新选择。"
        return 0
        ;;
    esac
}

#单个服务器ip配置展示
function display_server_ip_one() {
    local _index=$1
    local _name=$2
    local _var_name=$3
    local _sub_flag=$4
    local _need_flag=$5
    local _deploy_status_flag=$6

    local _need="  "
    if [ "$_need_flag" == "1" ];then
        _need="* "
    fi

    local server_ip=$(get_master_ip ${_var_name})
    if [ "${_deploy_status_flag}" -eq 0 ]; then
       echo "${_index}: ${_need}${_name}：        " ${server_ip}
    else
       Echo_Yellow "${_index}: ${_need}${_name}：        ${server_ip}"
    fi
    index_server_json+="\"${_index}\":\"${server_ip}\","
    local sub_count=$(get_slave_node_count ${_var_name})
    if [ "$_sub_flag" == "1" ] && [ $sub_count -gt 0 ];then
        local idx=1
        local slave_keys=($(yq '.'${_var_name}'.hosts.slave[]' ${server_config_file}))
        local slave_key
        for slave_key in "${slave_keys[@]}"; do
            server_ip=$(get_ip_by_host $slave_key)
            if [ "$server_ip" != "null" ]; then
                if [ "${_deploy_status_flag}" -eq 0 ]; then
                    echo "  ${_index}$idx:  ${_name}（从节点$idx）：         " ${server_ip}
                else
                    Echo_Yellow "  ${_index}$idx:  ${_name}（从节点$idx）：         ${server_ip}"
                fi

                # 拼接 JSON 字符串
                index=$(echo "${_index}$idx")
                index_server_json+="\"${index}\":\"${server_ip}\","
            fi
            let "idx=idx+1"
        done
    fi

}

# 非空服务器检查
function check_server_notnull() {
    NotNullResult=1
    local name
    local server_ip

    readarray -t keys < <(yq '.[] | select(.need_flag == 1) | key ' ${server_config_file})
    for key in "${keys[@]}"; do
        name=$(yq ".${key}.name" ${server_config_file})
        server_ip=$(get_master_ip ${key})
        if [ -z "$server_ip" ]; then
            Echo_Red "[$name]IP不能为空!"
            NotNullResult=0
        fi
    done

    check_biz_not_all_empty
    check_es_not_empty
}
# ES服务器非空检查
function check_es_not_empty() {
   local ip_web_name=$(yq '.[] | select(.choice_index == "s3") | key ' ${server_config_file})
   if [ -z "$ip_web_name" ]; then
       return
   fi
   local server_ip=$(get_master_ip ${ip_web_name})
   if [ ! -z "$server_ip" ]; then
     ip_web_name=$(yq '.[] | select(.choice_index == "m4") | key ' ${server_config_file})
     server_ip=$(get_master_ip ${ip_web_name})
     if [ -z "$server_ip" ]; then
         Echo_Red "ES服务器IP不能为空!"
         NotNullResult=0
     fi
   fi
}

# 业务线服务器不能全为空检查
function check_biz_not_all_empty() {
    local cnt=0;
    local index=0;
    local -a biz_names=()
    local name
    local server_ip

    readarray -t keys < <(yq '.[] | select(.biz_flag == 1) | key ' ${server_config_file})
    for key in "${keys[@]}"; do
        name=$(yq ".${key}.name" ${server_config_file})
        biz_names+=("${name}")
        server_ip=$(get_master_ip ${key})
        if [ -z "$server_ip" ]; then
            ((cnt=cnt+1))
        fi
        ((index=index+1))
    done

    if [ ${index} -gt 0 ] && [ $cnt -eq ${index} ] ;then
        Echo_Red "【${biz_names[*]}】不能全部为空！"
        NotNullResult=0
    fi
}

# 主从服务器IP重复性检查
function check_server_norepeat() {
    NoRepeatResult=1
    #如果业务库和统计库均存在主从，则需要检测一个从库是否拥有了多个主库
    local biz_server="ip_db_biz"
    local stat_server="ip_db_stat"
    local biz_db_count=$(get_slave_node_count $biz_server)
    local stat_db_count=$(get_slave_node_count $stat_server)

    local master_biz_node=$(get_master_host $biz_server)
    local master_stat_node=$(get_master_host $stat_server)
    if [ $master_biz_node == $master_stat_node ] && [ $biz_db_count -gt 0 ] && [ $stat_db_count -gt 0 ]; then
         Echo_Red "统计主库和业务主库不能同一个服务器上"
    fi
    if [ $biz_db_count -gt 0 ] && [ $stat_db_count -gt 0 ] && [ "$master_biz_node" != "$master_stat_node" ];then
         # 检查一个从库是否有多个主库
         # 检查主库是否为从库
         for ((stat_idx=0; stat_idx<stat_db_count; stat_idx++)); do
             local stat_host=$(get_slave_host $stat_server $stat_idx)
             if [ "$stat_host" != "null" ];then
                 if [ "$stat_host" == "$master_biz_node" ];then
                     Echo_Red "统计从库[$stat_host]不可同时为业务主库!"
                     NoRepeatResult=0
                 fi
                 # 是否存在业务库从节点中
                 local contain_res=$(has_contain_host $biz_server $stat_host)
                 if [ "$contain_res" == "true" ];then
                     Echo_Red "从库[$stat_host]存在多个主库!"
                     NoRepeatResult=0
                 fi
             fi
         done
         for ((biz_idx=0; biz_idx<biz_db_count; biz_idx++)); do
            local biz_host=$(get_slave_host $biz_server $biz_idx)
            if [ "$biz_host" != "null" ];then
                if [ "$biz_host" == "$master_stat_node" ];then
                    Echo_Red "业务从库[$biz_host]不可同时为统计主库!"
                    NoRepeatResult=0
                fi
                # 是否存在统计库从节点中
                local contain_res=$(has_contain_host $stat_server $biz_host)
                if [ "$contain_res" == "true" ];then
                    Echo_Red "从库[$biz_host]存在多个主库!"
                    NoRepeatResult=0
                fi
            fi
        done
    fi
}

# 主从web检查，防止nginx转发故障
function check_web_master_slave() {
    web_master_slave_result=1
    #mis有从节点时,人脸服务只能装在从节点
    local mis_server="ip_web_mis"
    local face_server="ip_web_face_server"
    local mis_count=$(get_slave_node_count $mis_server)
    local web_mis_host=$(get_master_host $mis_server)
    local web_face_host=$(get_master_host $face_server)
    if [ $mis_count -gt 0 ] && [ "$web_face_host" == "$web_mis_host" ]; then
        Echo_Red "MIS服务有从节点时，人脸服务只能装在从节点"
        web_master_slave_result=0
    fi
}

# TDengine和TDengine3服务器分离检查
function check_tdengine_separate() {
    web_master_slave_result=1
    local tdengine_server="ip_db_tdengine"
    local tdengine3_server="ip_db_tdengine_3"
    local tdengine_host=$(get_master_host $tdengine_server)
    local tdengine3_host=$(get_master_host $tdengine3_server)
    
    # 只有当两个服务器都配置了IP时才进行检查
    if [ -n "$tdengine_host" ] && [ "$tdengine_host" != "null" ] && [ -n "$tdengine3_host" ] && [ "$tdengine3_host" != "null" ]; then
        if [ "$tdengine_host" == "$tdengine3_host" ]; then
            Echo_Red "TDengine 和 TDengine3 不应该在同一个服务器上"
            web_master_slave_result=0
        fi
    fi
}

# 设置mis关联服务器
function set_mis_associated_host() {
    NotNullResult=1
    check_biz_not_all_empty
    if [ "$NotNullResult" == "0" ] ;then
        return 0
    fi

    local target_key=$1
    local only_slave=$2
    choose_add_or_deployed_host

    local index=0
    readarray -t keys < <(yq '.[] | select(.biz_flag == 1) | key ' ${server_config_file})
    for key in "${keys[@]}"; do
        local host=$(get_master_host $key)
        if ( [ "$key" == "ip_web_mis" ] || [ "$key" == "ip_web_uma" ] || [ "$key" == "ip_web_sg" ] || [ "$key" == "ip_web_mf" ] ) && [ "$host" != "null" ]; then
                  display_optional_server $target_key $key $only_slave
        fi
        let "index=index+1"
    done
    local input=""
    read -p "请选择: " input
    case ${input} in
    4 | 4[0-9]* | x[2-4]*)
        local host=${HOST_CHOICE_MAP["$input"]}
        if [ "$host" != "null" ] && [ "$host" != "" ]; then
            set_master_host $target_key $host
            set_deployed_status $target_key ${deploy_status_flag}
            return 0
        else
          Echo_Red "输入错误,请重新选择"
        fi
        ;;
    *)
        Echo_Red "输入错误,请重新选择"
        ;;
    esac

    set_mis_associated_host "$@"
}

# 设置gis关联服务器
function set_gis_associated_host() {
    local target_key=$1
    local only_slave=$2
    local source_key="ip_web_gis"
    choose_add_or_deployed_host

    local master_count=$(get_master_node_count $source_key)
    if [ $master_count -eq 0 ] ;then
        Echo_Red "请先设置GIS服务器主节点"
        return 0
    fi

    display_optional_server $target_key $source_key $only_slave
    local input=""
    read -p "请选择: " input
    case ${input} in
    5 | 5[0-9]*)
        local host=${HOST_CHOICE_MAP["$input"]}
        if [ "$host" != "null" ] && [ "$host" != "" ]; then
            set_master_host $target_key $host
            set_deployed_status ${target_key} ${deploy_status_flag}
            return 0
        else
          Echo_Red "输入错误,请重新选择"
        fi
        ;;
    *)
        Echo_Red "输入错误,请重新选择"
        ;;
    esac

    set_gis_associated_host "$@"
}
# 显示可供选择的服务器
function display_optional_server() {
#选择服务器IP
#$1 服务器名称
#$2 待选IP名称
#$3 是否默认安装从服务器上

#foo 输入IP值
    local target_key=$1
    local source_key=$2
    local only_slave=$3

    local target_name=$(get_server_name $target_key)
    local source_name=$(get_server_name $source_key)

    Echo_Yellow "$source_name可选择作为$target_name："
    local source_count=$(get_slave_node_count $source_key)
    if [ $source_count -eq 0 ];then
        only_slave=0
    fi
    local host=""
    local ip=""
    local choice_index=$(yq ".${source_key}.choice_index" ${server_config_file})
    if [ "$only_slave" == "0" ];then
        host=$(get_master_host ${source_key})
        ip=$(get_master_ip ${source_key})
        if [ "$ip" != "" ]; then
            HOST_CHOICE_MAP["$choice_index"]=$host
            echo "$choice_index: $host   $ip"
        fi
    else
        local index=0
        while [ $index -lt $source_count ]; do
            host=$(get_slave_host ${source_key} ${index})
            ip=$(get_slave_ip ${source_key} ${index})
            let "index=index+1"
            if [ "$ip" != "" ]; then
                local idx_key="$choice_index$index"
                HOST_CHOICE_MAP[$idx_key]=$host
                echo "$idx_key: $host   $ip"
            fi
        done
    fi
}

# 安装前特殊处理：针对特定部署场景进行配置调整
function pre_install_special_handle() {
    # 检查场景配置文件中是否包含毕升（evaluation）服务
    has_evaluation_in_config=$(yq '... | select(.sub_type == "evaluation")' ${server_config_file} 2>/dev/null)

    if [ -n "$has_evaluation_in_config" ]; then
        # 检查metadata.yml中是否存在export服务
        if yq '.microservice.export' ${metadata_file} &>/dev/null; then
            # 检查是否已存在毕升统计服务依赖
            has_eval_dep=$(yq '.microservice.export.export_1.depends[] | select(.sub_type == "evaluation")' ${metadata_file})
            if [ -z "$has_eval_dep" ]; then
                # 添加毕升统计服务依赖
                yq -i '.microservice.export.export_1.depends += {"type": "microservice", "sub_type": "evaluation", "name": "毕升统计服务"}' ${metadata_file} 2>/dev/null || true
                echo "检测到场景配置包含毕升服务：已为export服务添加毕升统计服务依赖"
            fi
        fi
    fi
}

function run_multi_install() {
    input_server_ip "$@"
    # 执行安装前特殊处理
    pre_install_special_handle
    # 安装服务
    ./i_common_software.sh ${server_config_file}
}
echo "开始进行部署"
run_multi_install "$@"
echo "分布式部署完成"
