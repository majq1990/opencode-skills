#!/bin/bash

service_template_file=../template/tomcat_app_template.yml
metadata_file=../../ansible/inventory/metadata.yml

# 已支持的微服务列表
service_name_array=
service_desc_array=

policy_template=../template/mino-policy-template.json
global_conf=../../ansible/group_vars/all.yml

. ../include/tool_echo.sh
. ../include/tool_metadata.sh

# convert yaml to json
function ms_yml_to_json() {
    local yml_file=$1
    if [ "${yml_file}" == "" ]; then
        yml_file=${ms_template_file}
    fi
    yq ${yml_file} -o=json >${yml_file}.json
}

# 显示已部署的微服务,只需要显示ip和端口
function display_deployed() {
    yq '.[] | key ' ${ms_template_file} | while read type; do
        echo "已部署的${type}列表如下:"
        local index=0
        # 需校验是否为空
        local cur_ms_len=$(yq ".service.${type} | length" ${metadata_file})
        if [ ${cur_ms_len} -gt 0 ]; then
            yq ".service.${type}.[] | key" ${metadata_file} | while read name; do
                # 过滤状态为success的
                status=$(yq ".service.${type}.${name}.status" ${metadata_file})
                if [ "$status" == "success" ]; then
                    ip=$(yq ".service.${type}.${name}.ip" ${metadata_file})
                    port=$(yq ".service.${type}.${name}.server_port" ${metadata_file})
                    echo "$(($index + 1)): IP为${ip}, 端口为${port}"
                    let "index=index+1"
                fi
            done
        fi
    done
}

# display keys
function display_keys() {
    Echo_Yellow "选择需要部署的微服务:"
    local index=1
    yq '.[] | key ' ${service_template_file} | while read key; do
        local name=$(yq ".${key}.name" ${service_template_file})
        echo "${index}: $name"
        let "index=index+1"
    done
    echo "v: 显示已部署的微服务"
    echo "q: 退出"
}

# display depends details
function display_depend_detail() {
    local key=$1
    local size=$2
    local depend_size=$(yq ".service.${key}.${key}_${size}.depends | length" ${metadata_file})
    local index=0
    while [ $index -lt $depend_size ]; do
        depend_name=$(yq '.service.'${key}'.'${key}'_'${size}'.depends['$index'].name' ${metadata_file})
        depend_type=$(yq '.service.'${key}'.'${key}'_'${size}'.depends['$index'].type' ${metadata_file})
        depend_key=$(yq '.service.'${key}'.'${key}'_'${size}'.depends['$index'].depend_key' ${metadata_file})
        # check if depend_key is null
        if [ "$depend_key" != "null" ]; then
            if [ "$depend_type" == "service" ]; then
                array=(${depend_key//_/ })
                depend_ip=$(yq '.'${depend_type}'.'${array[0]}'.'${depend_key}'.ip' ${metadata_file})
                depend_port=$(yq '.'${depend_type}'.'${array[0]}'.'${depend_key}'.server_port' ${metadata_file})
            else
                depend_ip=$(yq '.'${depend_type}'.'${depend_key}'.ip' ${metadata_file})
                depend_port=$(yq '.'${depend_type}'.'${depend_key}'.port' ${metadata_file})
            fi
            echo "$(($index + 1)): ${depend_name} ip为${depend_ip}, 端口为${depend_port}"
        else
            echo "$(($index + 1)): ${depend_name}"
        fi
        let "index=index+1"
    done
}

# 初始化微服务配置
function init_ms_config() {
    local key=$1
    local size=0

    # 考虑为空的情况，metadata.yml中配置从1开始依次递增
    local count=$(yq '.service.'$key' | length ' ${metadata_file})
    if [ $count -gt 0 ]; then
        size=$(yq '.service.'${key}' | length' ${metadata_file})
    fi
    # 如果为空,直接新增，如果不为空，则核查上次的部署状态，如果为success，也新增
    # TODO: 需考虑脚本同时运行多个，且都是部署同一类型的微服务，故不能只判断最后一条的部署状态来判断，应该直接加1
    # TODO: 通过metadata.yml获取当前部署情况时，过滤掉状态为undeploy的。
    let "size=size+1"
    # 获取当前metadata现有所有配置

    if [ $count -gt 0 ]; then
        yq '.service.'$key'' ${metadata_file} >.${key}_update.yml
    else
        echo "" >.${key}_update.yml
    fi

    # 按照模板内容，新增配置追加到update，加上前缀
    cat ${service_template_file} | yq '.TEMP.service.'${key}'.'${key}'_'${size}' = .'${key}' | .TEMP' >.${key}_update.yml
    # 利用update.yml更新metadata.yml
    yq eval-all --inplace 'select(fileIndex == 0) * select(fileIndex == 1)' ${metadata_file} .${key}_update.yml

    # 初始化status、host
    yq -i '.service.'${key}'.'${key}'_'${size}'.status= "undeployed"' ${metadata_file}
    yq -i '.service1.'${key}'.'${key}'_'${size}'.host= "none"' ${metadata_file}
    #当同一个服务非第一次按照成功时，每一次在前一个端口的基础上+1，避免端口号重复
    if [ $size -gt 1 ]; then
        let "sizeService=size-1"
        port=$(yq '.service.'${key}'.'${key}'_'${sizeService}'.server_port' ${metadata_file})
        let "port=port+1"
        yq -i '.service.'${key}'.'${key}'_'${size}'.server_port= '${port}'' ${metadata_file}
    fi
    return $size
}

# display depends
function display_depends() {
    local key=$1
    local size=$2
    Echo_Yellow "选择要配置的依赖组件:"
    local index=1

    # 改成遍历的方式
    display_depend_detail $key $size
    echo "v: 显示当前所有配置"
    echo "y: 确认当前所有配置，进入下一步部署"
    echo "q: 退出"

    read -p "请输入: " input
    case $input in
    [0-9]*)
        # config and save depends
        local depend_type=$(yq '.'${key}'.depends['$(($input - 1))'].type' ${service_template_file})
        local depend_name=$(yq '.'${key}'.depends['$(($input - 1))'].name' ${service_template_file})
        local depend_sub_type=$(yq '.'${key}'.depends['$(($input - 1))'].sub_type' ${service_template_file})
        if [ "$depend_type" == "null" ]; then
            Echo_Yellow "输入错误，请重试"
            display_depends $key $size
        fi

        local depend_type_key=".${depend_type}"
        local depend_is_ms=0
        if [ "${depend_type}" == "service" ]; then
            depend_type=${depend_sub_type}
            depend_is_ms=1
            depend_type_key=".service.${depend_type}"
        fi
        # check metadata if exists
        local count=$(yq ''${depend_type_key}'.[] | select(.status != "undeployed" and .status != "delete") | key' $metadata_file | wc -l)

#        local count=$(yq ''${depend_type_key}' | length ' ${metadata_file})
        if [ $count -gt 0 ]; then
            Echo_Yellow "配置${depend_name}，当前已部署的${depend_type}如下，请选择 "
            index=1
            yq ''${depend_type_key}'.[] | select(.status != "undeployed" and .status != "delete") | key ' ${metadata_file} | while read key; do
                ip=$(yq ''${depend_type_key}'.'$key'.ip' ${metadata_file})
                if [ ${depend_is_ms} -eq 1 ]; then
                  port=$(yq ''${depend_type_key}'.'$key'.server_port' ${metadata_file})
                else
                  port=$(yq ''${depend_type_key}'.'$key'.port' ${metadata_file})
                fi
                echo "$index: $ip $port"
                let "index=index+1"
            done
#            if [ ${depend_is_ms} -eq 0 ];then
#                # TODO 微服务暂不支持录入，后续需要支持
#                echo "a: 录入${depend_type}配置"
#            fi
            echo "a: 录入${depend_type}配置"
            echo "q: 退出"
            read -p "请输入: " select_depend
            case $select_depend in
            [0-9]*)
                # TODO: 此处需要校验输入项
                Echo_Yellow "选择了${select_depend}"
                if [ $count -lt $select_depend ]; then
                    Echo_Yellow "输入错误，请重试"
                    display_depends $key $size
                fi
                if [ ${depend_is_ms} -eq 1 ];then
                    select_key_tmp=$(cat ${metadata_file} | yq '.service.'${depend_type}'.[] | select(.status != "undeployed" and .status != "delete") | key')
                else
                    select_key_tmp=$(cat ${metadata_file} | yq '.'${depend_type}'.[] | select(.status != "undeployed" and .status != "delete") | key')
                fi
                key_array=(${select_key_tmp// / })
                select_key=${key_array[$select_depend-1]}
                # TODO fzl 迁移到统一模版处
                # 如果是minio,需要创建桶、用户并赋权
                if [ "${depend_type}" == "minio" ]; then
                    create_bucket_user $select_key $key
                fi

                # 更新依赖到metadata.yml，可直接根据index更新
                local idx=$((input - 1))
                yq -i '.service.'${key}'.'${key}'_'${size}'.depends['$idx'].depend_key = "'${select_key}'"' ${metadata_file}
                ;;
            a)
                if [ ${depend_is_ms} -eq 0 ];then
                    add_custom_config ${depend_type}
                else
                    add_custom_microsevice ${depend_type}
                fi
                ;;
            q)
                Echo_Yellow "退出"
                ;;
            *)
                Echo_Red "输入错误"
                ;;
            esac
            display_depends $key $size
        else
            Echo_Yellow "没有找到已部署的${depend_type}, 请选择"
#            if [ ${depend_is_ms} -eq 0 ];then
#            fi
            echo "a: 录入${depend_type}配置"
            if [ ${depend_is_ms} -eq 1 ];then
                echo "m: 安装依赖的微服务${depend_type}"
            else
                echo "i: 进入软件工具箱部署${depend_type}"
            fi
            echo "q: 退出"
            read -p "请输入: " select
            case $select in
            a)
                if [ ${depend_is_ms} -eq 0 ];then
                    add_custom_config ${depend_type}
                else
                    add_custom_microsevice ${depend_type}
                fi
                display_depends $key $size
                ;;
            i)
                ./i_software.sh
                display_depends $key $size
                ;;
            m)
                ./i_service.sh
                display_depends $key $size
                ;;
            q)
                Echo_Yellow "退出"
                display_depends $key $size
                ;;
            *)
                Echo_Red "输入错误"
                display_depends $key $size
                ;;
            esac
        fi
        ;;
    v)
        Echo_Yellow "当前微服务所有配置如下:"
        # 从metadata.yml中读取当前微服务的所有配置
        # TODO: 显示信息需优化
        local ms_name=$(yq '.service.'${key}'.'${key}'_'${size}'.name' ${metadata_file})
        local port=$(yq '.service.'${key}'.'${key}'_'${size}'.server_port' ${metadata_file})
        echo "名称: $ms_name"
        echo "端口: $port"
        # 显示依赖
        echo "依赖配置如下："
        display_depend_detail "$key" "$size"
        # 显示上级选项
        display_depends "$key" "$size"
        ;;
    y)
        check_depend_selected "$key" "$size"
        Echo_Yellow "依赖配置已确认"
        ;;
    q)
        Echo_Yellow "退出"
        exit
        ;;
    *)
        Echo_Red "选择错误"
        display_depends $key $size
        ;;
    esac

    # 打印服务名称，对应app_type和app_name
    # echo "$key $key$size"
}
#检查微服务所有的依赖是否都已选择了对应依赖配置
function check_depend_selected(){
    local key=$1
    local size=$2
    local depend_size=$(yq ".service.${key}.${key}_${size}.depends | length" ${metadata_file})
    local index=0
    local vf=0
    while [ $index -lt $depend_size ]; do
        depend_name=$(yq '.service.'${key}'.'${key}'_'${size}'.depends['$index'].name' ${metadata_file})
        depend_type=$(yq '.service.'${key}'.'${key}'_'${size}'.depends['$index'].type' ${metadata_file})
        depend_key=$(yq '.service.'${key}'.'${key}'_'${size}'.depends['$index'].depend_key' ${metadata_file})
        # check if depend_key is null
        if [ "$depend_key" == "null" ]; then
            vf=1
            let ix=index+1
            Echo_Red "${depend_name}还未选择依赖配置，请输入${ix}，选择依赖配置后再输入y安装"
        fi
        let "index=index+1"
    done
    if [ "$vf" == 1 ]; then
        display_depends "$key" "$size"
    fi
}




function display_value_by_key() {
    local key=$1
    yq '.'${key}'' ${service_template_file}
}

# init params array
function init_param_array() {
    service_names=$(yq '.[] | key ' ${service_template_file})
    service_name_array=(${service_names})
    service_descs=$(yq '.[].name' ${service_template_file})
    service_desc_array=(${service_descs})
}

# 检查上一次的部署状态，如上一次undeployed，则直接加载上次的配置
function check_last_config() {
    type=$1
    Echo_Yellow "检查上一次的部署状态"
    local count=$(yq '.service.'$type'.[] | select(.status=="undeployed") | key' $metadata_file | wc -l)
    if [ $count -gt 0 ]; then
        local key=$(yq '.service.'$type'.[] | select(.status=="undeployed") | key' $metadata_file | head -n 1)
        local index=$(echo $key | awk -F "_" '{print $NF}')
        LAST_UNDEPLOYED_KEY=$index
    fi
}

# 部署微服务
function run_ms_install() {
    #当前方法执行时，pwd=shell/include
    LAST_UNDEPLOYED_KEY="default"
    #yml转换为json格式
    ms_yml_to_json
    init_param_array
    display_keys
    local index=""
    read -p "请输入: " index
    case $index in
    [0-9]*)
        # 根据微服务模板，初始化一份微服务配置到metadata.yml
        local ms_type=${service_name_array[(($index - 1))]}
        check_last_config $ms_type
        if [ $LAST_UNDEPLOYED_KEY == "default" ]; then
            init_ms_config ${service_name_array[(($index - 1))]}
            # 配置依赖
            local current_size=$?
            display_depends ${service_name_array[(($index - 1))]} $current_size
        else
            current_size=$LAST_UNDEPLOYED_KEY
            display_depends ${service_name_array[(($index - 1))]} $LAST_UNDEPLOYED_KEY
        fi
        ;;
    v)
        display_deployed
        run_ms_install
        ;;
    q)
        exit 0
        ;;
    *)
        Echo_Red "输入错误"
        run_ms_install
        ;;
    esac

    # deploy by ansible
    #init_ms_db $ms_type ${ms_type}_${current_size}
    local MS_SELECT_HOST=""
    cd ../include
    . tool_hosts.sh
    choose_one_host "$ms_type" "MS_SELECT_HOST"
    cd ../tools
    echo "${MS_SELECT_HOST}"
    # TODO 同一服务器，同一端口，重复覆盖提醒
    if [ "${MS_SELECT_HOST}" != "" ]; then
        ansible-playbook -i ../../ansible/inventory/hosts.yml -e "host=${MS_SELECT_HOST} app_type=${ms_type} app_name=${ms_type}_${current_size}" -e "@../../ansible/inventory/metadata.yml" ../../ansible/install_tomcat_app.yml
        local rst=$?
        Echo_Yellow "ansible执行日志见/var/log/ansible.log"
        if [ $rst -gt 0 ]; then
            Echo_Red "${ms_type}安装失败！"
            #yq -i 'del(.service.'$ms_type'.'${ms_type}'_'${current_size}')' $metadata_file
        else
            Echo_Green "${ms_type}安装成功！"
        fi
    fi
}

run_ms_install
