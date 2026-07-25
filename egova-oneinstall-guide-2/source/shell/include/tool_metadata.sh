#!/bin/bash

metadata_file=../../ansible/inventory/metadata.yml
template_dir=../../ansible/inventory/template
hosts_file=../../ansible/inventory/hosts.yml
SOFTWARE_CONFIG_FILE=../../ansible/inventory/software_tools.yml
ms_template_file=../../shell/template/microservice_template.yml
tomcat_app_template_file=../../shell/template/tomcat_app_template.yml

. ../include/tool_echo.sh
tmp_name_arr=()
tmp_desc_arr=()
tmp_value_arr=()

tmp_hide_name_arr=()
tmp_default_value_arr=()

TYPE_ARRAY=("software" "microservice" "service")

# 根据传入的参数数组，显示名称和描述
# 输入样例: param_array=("ip" "port"), param_desc_array=("IP地址" "端口")
function add_custom_config() {

    local software_name=$1

    yq '.software_tools.[] | select(.name == "'$software_name'") | .params' $SOFTWARE_CONFIG_FILE   > .${software_name}.conf

    param_count=$(yq '.software_tools.[] | select(.name == "'$software_name'") | .params | keys' $SOFTWARE_CONFIG_FILE | wc -l)
    local idx=0
    local hide_idx=0
    local param_idx=0
    while [ $idx -lt $param_count ]
    do
        access_conf=$(yq '.['$idx'].access_conf' .${software_name}.conf)
        if [ $access_conf == "1" ];then
            tmp_name_arr[$param_idx]=$(yq '.['$idx'].name' .${software_name}.conf)
            tmp_desc_arr[$param_idx]=$(yq '.['$idx'].desc' .${software_name}.conf)
            let param_idx=param_idx+1
        fi
        if [ $access_conf == "0" ];then
            tmp_hide_name_arr[$hide_idx]=$(yq '.['$idx'].name' .${software_name}.conf)
            tmp_default_value_arr[$hide_idx]=$(yq '.['$idx'].default' .${software_name}.conf)
            let hide_idx=hide_idx+1
        fi
        let idx=idx+1
    done

    local idx=1
    while [ $idx -le $param_idx ]
    do
        current_value=${tmp_value_arr[$idx-1]}
        echo "${idx}: ${tmp_desc_arr[$idx-1]} 当前值: ${current_value}"
        let idx=idx+1
    done

    echo "y: 确认配置，下一步"
    echo "q: 退出"
    local param_input="ERROR"
    read -p "输入序号更改相应配置: " param_input

    case ${param_input} in
    [0-9]*)
        if echo "$param_input"|[ ! -n "`sed -n '/^[0-9][0-9]*$/p'`" ] ;then
            Echo_Red "输入错误，只能输入数字！"
            add_custom_config "$software_name"
            return 0
        fi

        if [ ${param_input} -gt ${param_count} ]; then
                Echo_Red "选择错误！"
                add_custom_config "$software_name"
                return 0
        fi
        Echo_Yellow "${tmp_desc_arr[$param_input-1]}"
        read -p "请输入[${tmp_desc_arr[$param_input-1]}]: " param_value
        tmp_value_arr[$param_input-1]=$param_value
        add_custom_config $software_name
        ;;
    q)
        exit 0
        ;;
    y | Y)
        # save to metadata
        local current_size=$(yq '.'$software_name' | length' $metadata_file)
        let current_size=current_size+1
        local idx=0
        while [ $idx -lt $param_idx ]
        do
            yq -i '.'${software_name}'.'${software_name}'_'${current_size}'.'${tmp_name_arr[$idx]}'="'${tmp_value_arr[$idx]}'"' $metadata_file
            let idx=idx+1
        done
        # 不展示的参数自动写入默认值
        local idxx=0
        while [ $idxx -lt $hide_idx ]
        do
            yq -i '.'${software_name}'.'${software_name}'_'${current_size}'.'${tmp_hide_name_arr[$idxx]}'="'${tmp_default_value_arr[$idxx]}'"' $metadata_file
            let idxx=idxx+1
        done
        tmp_name_arr=()
        tmp_desc_arr=()
        tmp_value_arr=()
        tmp_hide_name_arr=()
        tmp_default_value_arr=()
        return 0
        ;;
    *)
        Echo_Red "选择错误！"
        add_custom_config $software_name
        return 0
        ;;
    esac

}

function add_custom_microsevice(){
    local microsevice_name=$1

    display_name=$(yq '.'${microsevice_name}'.name' $ms_template_file)
    tmp_name_arr[0]='name'
    tmp_name_arr[1]='ip'
    tmp_name_arr[2]='server_port'
    tmp_name_arr[3]='backend'
    tmp_desc_arr[0]='请输入IP地址'
    tmp_desc_arr[1]='请输入端口'
    tmp_desc_arr[2]='请输入路径（如/eureka）'
    local param_count=3
    local idx=1
    while [ $idx -le $param_count ]
    do
        current_value=${tmp_value_arr[$idx-1]}
        echo "${idx}: ${tmp_desc_arr[$idx-1]} 当前值: ${current_value}"
        let idx=idx+1
    done

    echo "y: 确认配置，下一步"
    echo "q: 退出"
    local param_input="ERROR"
    read -p "输入序号更改相应配置: " param_input

    case ${param_input} in
    [0-9]*)
        if echo "$param_input"|[ ! -n "`sed -n '/^[0-9][0-9]*$/p'`" ] ;then
            Echo_Red "输入错误，只能输入数字！"
            add_custom_microsevice "$microsevice_name"
            return 0
        fi

        if [ ${param_input} -gt ${param_count} ]; then
                Echo_Red "选择错误！"
                add_custom_microsevice "$microsevice_name"
                return 0
        fi
        Echo_Yellow "${tmp_desc_arr[$param_input-1]}"
        read -p "请输入[${tmp_desc_arr[$param_input-1]}]: " param_value
        tmp_value_arr[$param_input-1]=$param_value
        add_custom_microsevice $microsevice_name
        ;;
    q)
        exit 0
        ;;
    y | Y)
        # save to metadata
        local current_size=$(yq '.microservice.'$microsevice_name' | length' $metadata_file)
        let current_size=current_size+1
        local idx=0
        let param_count=$param_count+1
        while [ $idx -lt $param_count ]
        do
            if [ ${idx} -eq 0 ];then
                yq -i '.microservice.'${microsevice_name}'.'${microsevice_name}'_'${current_size}'.'${tmp_name_arr[$idx]}'="'${display_name}'"' $metadata_file
            else
                yq -i '.microservice.'${microsevice_name}'.'${microsevice_name}'_'${current_size}'.'${tmp_name_arr[$idx]}'="'${tmp_value_arr[$idx-1]}'"' $metadata_file
            fi
            let idx=idx+1
        done
        tmp_name_arr=()
        tmp_desc_arr=()
        tmp_value_arr=()

        return 0
        ;;
    *)
        Echo_Red "选择错误！"
        add_custom_config $software_name
        return 0
        ;;
    esac

}


# 保存数据库和中间件元数据配置
function save_config_to_metadata() {
    # 对于微服务，有sub_type。 type=service, sub_type=eUrbanMIS
    local type=$1
    local host=$2
    local sub_type=$3
    local size=$4
    local status=$5

    local type_key="${type}.${sub_type}"
    if [ "${type}" == "${TYPE_ARRAY[0]}" ];then
        type_key="${sub_type}"
    fi

    if [ $size -gt 1 ]; then
        yq '.'$type_key'' ${metadata_file} >.${sub_type}_update.yml
    else
        echo "" >.${sub_type}_update.yml
    fi
    # 按照模板内容，新增配置追加到update，加上前缀
    # yq r ${template_dir}/${type}.yml ${type} > .{type}_template.yml
    local prefix_key="${type_key}.${sub_type}_${size}"
    if [ "${type}" == "${TYPE_ARRAY[1]}" ];then
        # microservice
        cat ${ms_template_file} | yq '.TEMP.'${prefix_key}' = .'${sub_type}' | .TEMP' >.${sub_type}_update.yml
    elif [ "${type}" == "${TYPE_ARRAY[2]}" ];then
        # service
        cat ${tomcat_app_template_file} | yq '.TEMP.'${prefix_key}' = .'${sub_type}' | .TEMP' >.${sub_type}_update.yml
    else
        cat ${template_dir}/${sub_type}.yml | yq '.TEMP.'${prefix_key}' = . | .TEMP |del(.'${prefix_key}'.TEMP) ' >.${sub_type}_update.yml
    fi
    # 利用update.yml更新metadata.yml
    yq eval-all --inplace 'select(fileIndex == 0) * select(fileIndex == 1)' ${metadata_file} .${sub_type}_update.yml
    # 初始化status、host、ip
    yq -i '.'${prefix_key}'.status="'$status'"' ${metadata_file}
    yq -i '.'${prefix_key}'.host="'$host'"' ${metadata_file}
    if [ "${host}" != "none" ] && [ "${host}" != "" ] ;then
        local ip=$(yq '.all.hosts.'${host}'.ansible_ssh_host' ${hosts_file})
        yq -i '.'${prefix_key}'.ip="'$ip'"' ${metadata_file}
    fi

    # 备份一份
    \cp -f ${metadata_file} /etc/
}

# 保存元数据配置
function save_metadata() {
    local type=$1
    local host=$2
    local sub_type=$3
    local size=$4
    local status=$5
    save_config_to_metadata $type $host $sub_type $size $status
}

# 更新元数据配置状态
function update_metadata_status() {
    local type=$1
    local name=$2
    local host=$3
    local status=$4

    local prefix_key="${type}.${name}"
    yq -i '.'${prefix_key}'.status="'$status'"' ${metadata_file}
    yq -i '.'${prefix_key}'.host="'$host'"' ${metadata_file}
    if [ "${host}" != "none" ] && [ "${host}" != "" ] ;then
        local ip=$(yq '.all.hosts.'${host}'.ansible_ssh_host' ${hosts_file})
        yq -i '.'${prefix_key}'.ip="'$ip'"' ${metadata_file}
    fi
}

# 克隆微服务的配置
function clone_ms_metadata() {
    local type=$1
    local src_index=$2
    local host=$3
    local count=$(yq ".service.${type}|keys|length")
    local old_key=".service.${type}.${type}_${src_index}"
    local new_key=".service.${type}.${type}_$((count + 1))"
    yq -i "${new_key}=${old_key}" ${metadata_file}
    yq -i ''${new_key}'.'${host}'="'${host}'"' ${metadata_file}
}

# 统计对应状态元素数量
function count_by_status() {
  local type=$1
  local status=$2
  local host=$3
  local count=0
  if [ -z "$host" ]; then
      count=$(yq '.'$type'.[] | select(.status=="'$status'") | key' $metadata_file | wc -l)
  else
      count=$(yq '.'$type'.[] | select(.status=="'$status'" and .host=="'$host'") | key' $metadata_file | wc -l)
  fi
  echo $count
}

# 获取上一次的某部署状态的key
function get_depend_key_by_status() {
    local type=$1
    local status=$2
    local host=$3
    local count=$(count_by_status $type $status $host)
    local depend_key=""
    if [ $count -gt 0 ]; then
        if [ -z "$host" ]; then
            depend_key=$(yq '.'$type'.[] | select(.status=="'$status'") | key' $metadata_file | head -n 1)
        else
            depend_key=$(yq '.'$type'.[] | select(.status=="'$status'" and .host=="'$host'") | key' $metadata_file | head -n 1)
        fi
    fi
    echo $depend_key
}

# 获取上一次的某部署状态的index
function get_last_index_by_status() {
    local type=$1
    local status=$2
    local host=$3
    local key=$(get_depend_key_by_status $type $status $host)
    local last_index=1
    if [ "$key" != "" ] && [ "$key" != "null" ]; then
        last_index=$(echo $key | awk -F "_" '{print $NF}')
    fi
    echo $last_index
}

# 更新depend_key
function update_metadata_depend_key() {
    local prefix_key=$1
    local host=$2
    local depend_type=$3
    local index=$4
    local success_key=$(yq '.'$depend_type'.[] | select(.status=="success" and .node=="'$host'") | key' $metadata_file | head -n 1)
    yq -i '.'${prefix_key}'.depends['$index'].depend_key= '${success_key}'' ${metadata_file}
}
