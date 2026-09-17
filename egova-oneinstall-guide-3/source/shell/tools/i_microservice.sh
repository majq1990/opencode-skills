#!/bin/bash

ms_template_file=../template/microservice_template.yml
metadata_file=../../ansible/inventory/metadata.yml
hosts_yml=../../ansible/inventory/hosts.yml
# 已支持的微服务列表
microservice_name_array=
microservice_desc_array=
APP_TYPE_ARRAY=("eurbanpro" "basic")
policy_template=../template/mino-policy-template.json
global_conf=../../ansible/group_vars/all.yml

. ../include/tool_echo.sh
. ../include/tool_metadata.sh

# 创建桶、用户及赋权
function create_bucket_user() {
    local select_key=$1
    local key=$2
    local minio_ip=$(yq ".minio.${select_key}.ip" ${metadata_file})
    local minio_port=$(yq ".minio.${select_key}.port" ${metadata_file})
    local minio_access_key=$(yq ".minio.${select_key}.access_key" ${metadata_file})
    local minio_secret_key=$(yq ".minio.${select_key}.secret_key" ${metadata_file})
    local bucket_names=$(yq '.'${key}'.depends[] | select(.type == "minio") | .bucket_name' ${ms_template_file})
    host_exist=$(mc config host list|grep $select_key)
    if [ "$host_exist" == "" ]; then
      mc config host add $select_key http://${minio_ip}:${minio_port} $minio_access_key $minio_secret_key
    fi
    local minio_bucket_name=''
    IFS=',' read -ra buckets <<< "$(echo $bucket_names | cut -d',' -f1-)"
    for bucket in "${buckets[@]}"
    do
      minio_bucket_name=$bucket
      bucket_exist=$(mc ls $select_key |grep $minio_bucket_name)
      if [ "$bucket_exist" == "" ]; then
        mc mb ${select_key}/${minio_bucket_name} -p
        common_pwd=$(yq '.common_password' $global_conf)
        mc admin user add $select_key ${minio_bucket_name} ${common_pwd}
        mc admin policy attach $select_key readonly --user ${minio_bucket_name}
        mc admin policy attach $select_key writeonly -user ${minio_bucket_name}
      fi
    done

}
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
    for type in "${microservice_name_array[@]}"; do
        echo "已部署的${type}列表如下:"
        local index=0
        # 需校验是否为空
        local cur_ms_len=$(yq ".microservice.${type} | length" ${metadata_file})
        if [ ${cur_ms_len} -gt 0 ]; then
            yq ".microservice.${type}.[] | key" ${metadata_file} | while read name; do
                # 过滤状态为success的
                status=$(yq ".microservice.${type}.${name}.status" ${metadata_file})
                if [ "$status" == "success" ]; then
                    ip=$(yq ".microservice.${type}.${name}.ip" ${metadata_file})
                    port=$(yq ".microservice.${type}.${name}.server_port" ${metadata_file})
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
    for key in "${microservice_name_array[@]}"; do
        local name=$(yq ".${key}.name" ${ms_template_file})
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
    local depend_size=$(yq ".microservice.${key}.${key}_${size}.depends | length" ${metadata_file})
    local index=0
    while [ $index -lt $depend_size ]; do
        depend_name=$(yq '.microservice.'${key}'.'${key}'_'${size}'.depends['$index'].name' ${metadata_file})
        depend_type=$(yq '.microservice.'${key}'.'${key}'_'${size}'.depends['$index'].type' ${metadata_file})
        depend_key=$(yq '.microservice.'${key}'.'${key}'_'${size}'.depends['$index'].depend_key' ${metadata_file})
        # check if depend_key is null
        if [ "$depend_key" != "null" ]; then
            if [ "$depend_type" == "microservice" ]; then
                array=(${depend_key//_/ })
                depend_ip=$(yq '.'${depend_type}'.'${array[0]}'.'${depend_key}'.ip' ${metadata_file})
                depend_port=$(yq '.'${depend_type}'.'${array[0]}'.'${depend_key}'.server_port' ${metadata_file})
           elif [ "$depend_type" == "usercenter_redis" ]; then
             depend_type="redis"
             depend_ip=$(yq '.'${depend_type}'.'${depend_key}'.ip' ${metadata_file})
             depend_port=$(yq '.'${depend_type}'.'${depend_key}'.port' ${metadata_file})
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
    local count=$(yq '.microservice.'$key' | length ' ${metadata_file})
    if [ $count -gt 0 ]; then
        size=$(yq '.microservice.'${key}' | length' ${metadata_file})
    fi
    # 如果为空,直接新增，如果不为空，则核查上次的部署状态，如果为success，也新增
    # TODO: 需考虑脚本同时运行多个，且都是部署同一类型的微服务，故不能只判断最后一条的部署状态来判断，应该直接加1
    # TODO: 通过metadata.yml获取当前部署情况时，过滤掉状态为undeploy的。
    let "size=size+1"
    # 获取当前metadata现有所有配置

    # 保存元数据配置并初始化status、host
    save_metadata "microservice" "none" ${key} ${size} "undeployed"
    #当同一个服务非第一次按照成功时，每一次在前一个端口的基础上+1，避免端口号重复
    if [ $size -gt 1 ]; then
        let "sizeService=size-1"
        port=$(yq '.microservice.'${key}'.'${key}'_'${sizeService}'.server_port' ${metadata_file})
        let "port=port+1"
        yq -i '.microservice.'${key}'.'${key}'_'${size}'.server_port= '${port}'' ${metadata_file}
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
        local depend_type=$(yq '.'${key}'.depends['$(($input - 1))'].type' ${ms_template_file})
        local depend_name=$(yq '.'${key}'.depends['$(($input - 1))'].name' ${ms_template_file})
        local depend_sub_type=$(yq '.'${key}'.depends['$(($input - 1))'].sub_type' ${ms_template_file})
        if [ "$depend_type" == "null" ]; then
            Echo_Yellow "输入错误，请重试"
            display_depends $key $size
        fi

        local depend_type_key=".${depend_type}"
        local depend_is_ms=0
        if [ "${depend_type}" == "microservice" ]; then
            depend_type=${depend_sub_type}
            depend_is_ms=1
            depend_type_key=".microservice.${depend_type}"
        fi

       if [ "${depend_type}" == "usercenter_redis" ]; then
           depend_type="redis"
            depend_type_key=".${depend_type}"
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
                    select_key_tmp=$(cat ${metadata_file} | yq '.microservice.'${depend_type}'.[] | select(.status != "undeployed" and .status != "delete") | key')
                else
                    select_key_tmp=$(cat ${metadata_file} | yq '.'${depend_type}'.[] | select(.status != "undeployed" and .status != "delete") | key')
                fi
                key_array=(${select_key_tmp// / })
                select_key=${key_array[$select_depend-1]}
                # TODO fzl 迁移到统一模版处
                # 如果是minio,需要创建桶、用户并赋权
                if [ "${depend_type}" == "minio" ]; then
               #     create_bucket_user $select_key $key
               #  修改为可在远程机部署
                  local minio_host=$(yq '.'${depend_type}'.'${select_key}'.host ' ${metadata_file})
                  if [ "${minio_host}" != "null" ]; then
                   ansible-playbook -i ${hosts_yml} -e "host=${minio_host} app_type=${key} depend_key=${select_key}" ../../ansible/config_minio_bucket.yml
                  fi
                fi

                # nacos 命名空间配置
                if [ "${depend_type}" == "nacos" ]; then
                    local nacos_host=$(yq '.'${depend_type}'.'${select_key}'.host' ${metadata_file})
                    if [ "${nacos_host}" != "null" ]; then
                        ansible-playbook -i ${hosts_yml} -e "host=${nacos_host} app_type=${key} depend_key=${select_key}" ../../ansible/config_nacos_namespace.yml
                    fi
                fi

                # 更新依赖到metadata.yml，可直接根据index更新
                local idx=$((input - 1))
                yq -i '.microservice.'${key}'.'${key}'_'${size}'.depends['$idx'].depend_key = "'${select_key}'"' ${metadata_file}
                ;;
            a)
                if [ "${depend_type}" == "usercenter_redis" ]; then
                   depend_type="redis"
                fi
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
                ./i_microservice.sh
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
        local ms_name=$(yq '.microservice.'${key}'.'${key}'_'${size}'.name' ${metadata_file})
        local port=$(yq '.microservice.'${key}'.'${key}'_'${size}'.server_port' ${metadata_file})
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
        if [ "$key" == "video" ]; then
            local usercenter_ip=$(yq '.microservice.usercenter.[] | select(.status == "success") | .ip' ${metadata_file} | head -n 1)
            if [ "$usercenter_ip" == "" ] || [ "$usercenter_ip" == "null" ]; then
                Echo_Red "请先安装用户中心"
                exit 0
            fi
        fi
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
    local depend_size=$(yq ".microservice.${key}.${key}_${size}.depends | length" ${metadata_file})
    local index=0
    local vf=0
    while [ $index -lt $depend_size ]; do
        depend_name=$(yq '.microservice.'${key}'.'${key}'_'${size}'.depends['$index'].name' ${metadata_file})
        depend_type=$(yq '.microservice.'${key}'.'${key}'_'${size}'.depends['$index'].type' ${metadata_file})
        depend_key=$(yq '.microservice.'${key}'.'${key}'_'${size}'.depends['$index'].depend_key' ${metadata_file})
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
    yq '.'${key}'' ${ms_template_file}
}

# init params array
function init_param_array() {
      if [ -z "$1" ]; then
          microservice_names=$(yq '.[] | select(.display=="1") | key ' ${ms_template_file})
      else
           if [[ $1 == "basic" ]];then
            for key in "${APP_TYPE_ARRAY[@]}"; do
              result=$(yq '.[] | select(.display=="1" and .category=="'${key}'") | key ' ${ms_template_file})
              microservice_names+=$'\n'"${result}"
            done
          else
            microservice_names=$(yq '.[] | select(.display=="1" and .category=="'${1}'") | key ' ${ms_template_file})
          fi
      fi
#       if [[ $(echo "$microservice_names" | wc -l) -gt 1 ]]; then
#            microservice_names=$(echo "$microservice_names" | sed '1d')
#       fi
    microservice_name_array=(${microservice_names})
    microservice_desc_array=()
    for key in "${microservice_name_array[@]}"; do
        name=$(yq ".${key}.name" ${ms_template_file})
        microservice_desc_array+=("${name}")
    done
}

# 检查上一次的部署状态，如上一次undeployed，则直接加载上次的配置
function check_last_config() {
    type=$1
    Echo_Yellow "检查上一次的部署状态"
    local count=$(yq '.microservice.'$type'.[] | select(.status=="undeployed") | key' $metadata_file | wc -l)
    if [ $count -gt 0 ]; then
        local key=$(yq '.microservice.'$type'.[] | select(.status=="undeployed") | key' $metadata_file | head -n 1)
        local index=$(echo $key | awk -F "_" '{print $NF}')
        LAST_UNDEPLOYED_KEY=$index
    fi
}
# 输出部署后的信息
function deploy_info() {
    local keys=($(yq '.[] | key ' ${metadata_file}))
    for key in "${keys[@]}"; do
    if [[ "${key}" != "service" && "${key}" != "microservice" ]]; then
        continue
    fi
    local app_type=($(yq ".${key}[] | key" ${metadata_file}))
       for app_type in "${app_type[@]}"; do
         local sub_type=($(yq ".${key}.${app_type}[] | key" ${metadata_file}))
         for sub_type in "${sub_type[@]}"; do
              service_name=$(yq ".${key}.${app_type}.${sub_type}.name" ${metadata_file})
              ip=$(yq ".${key}.${app_type}.${sub_type}.ip" ${metadata_file})
              status=$(yq ".${key}.${app_type}.${sub_type}.status" ${metadata_file})
              login_url=$(yq ".${key}.${app_type}.${sub_type}.login_url" ${metadata_file})
              wiki=$(yq ".${key}.${app_type}.${sub_type}.wiki" ${metadata_file})
              user=$(yq ".${key}.${app_type}.${sub_type}.user" ${metadata_file})
              password=$(yq ".${key}.${app_type}.${sub_type}.password" ${metadata_file})
             if [ "$wiki" == "null" ] || [ -z "$wiki" ]; then
                wiki="http://faq.egova.com.cn:7777/projects/redmine/wiki/%E4%BF%A1%E5%88%9B%E4%B8%80%E9%94%AE%E9%83%A8%E7%BD%B2"
             fi
             if [ "$login_url" == "null" ] || [ -z "$login_url" ]; then
                    login_url="无登录地址，请查询对应的wiki，按要求配置"
             fi
             if [ "$user" == "null" ] || [ -z "$user" ]; then
                 user="无内置用户和密码，可能是用户中心或智信云登录密码，请查看wiki说明"
             fi
             # 输出服务信息
               echo "------------------------------------------"
               echo "服务名称  : $service_name"
               echo "服务器IP            : $ip"
               echo "部署状态        : $status"
               echo "系统登录地址     : $login_url"
               echo "系统登录用户          : $user"
               echo "系统登录用户密码      : $password"
               echo "$service_name部署Wiki          : $wiki"
               echo "------------------------------------------"

         done
       done
    done
}
# 部署微服务
function run_ms_install() {
    #当前方法执行时，pwd=shell/include
    LAST_UNDEPLOYED_KEY="default"
    #yml转换为json格式
    ms_yml_to_json
    init_param_array "$@"
    display_keys
    local index=""
    read -p "请输入: " index
    case $index in
    [0-9]*)
        # 根据微服务模板，初始化一份微服务配置到metadata.yml
        local ms_type=${microservice_name_array[(($index - 1))]}
        check_last_config $ms_type
        if [ $LAST_UNDEPLOYED_KEY == "default" ]; then
            init_ms_config ${microservice_name_array[(($index - 1))]}
            # 配置依赖
            local current_size=$?
            display_depends ${microservice_name_array[(($index - 1))]} $current_size
        else
            current_size=$LAST_UNDEPLOYED_KEY
            display_depends ${microservice_name_array[(($index - 1))]} $LAST_UNDEPLOYED_KEY
        fi
        ;;
    v)
        display_deployed
        run_ms_install "$@"
        ;;
    q)
        exit 0
        ;;
    *)
        Echo_Red "输入错误"
        run_ms_install "$@"
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
       local ms_install_file=../../ansible/install_microservice.yml
       if [ -e ../../ansible/install_${ms_type}.yml ];then
             ms_install_file=../../ansible/install_${ms_type}.yml
       fi
        jvm_opts=$(yq ".${ms_type}.environment.jvm_opts" "${ms_template_file}")
        max_xmx=$(echo "$jvm_opts" | sed -n 's/.*-Xmx\([0-9]\+\)m.*/\1/p')
        ansible-playbook -i ../../ansible/inventory/hosts.yml -e "max_xmx=${max_xmx} host=${MS_SELECT_HOST} app_type=${ms_type} app_name=${ms_type}_${current_size}" -e "@../../ansible/inventory/metadata.yml" ${ms_install_file}
        local rst=$?
        Echo_Yellow "ansible执行日志见/var/log/ansible.log"
        if [ $rst -gt 0 ]; then
            Echo_Red "${ms_type}安装失败！"
        else
            Echo_Green "${ms_type}安装成功！"
            # 调用灵珑组件初始化
            linglong_init ${ms_type} ${ms_type}_${current_size}
        fi
    fi
    deploy_info
}

# 灵珑组件初始化
# 参数: ms_type, ms_name
function linglong_init() {
    local ms_type=$1
    local ms_name=$2

    # 检查 linglong_init.yml 文件是否存在
    local linglong_init_file=../../ansible/inventory/linglong_init.yml
    if [ ! -e ${linglong_init_file} ]; then
        return 0
    fi

    # 检查该微服务是否在 linglong_init.yml 中配置且值为0（需要初始化）
    local need_init=$(yq ".${ms_type}" ${linglong_init_file})
    if [ "${need_init}" != "0" ]; then
        Echo_Yellow "${ms_type} 不需要灵珑初始化或已初始化"
        return 0
    fi

    # 检查是否有已安装成功的灵珑微服务
    local metadata_file=../../ansible/inventory/metadata.yml
    local linglong_keys=($(yq '.microservice.linglong[] | select(.status == "success") | key' ${metadata_file}))

    if [ ${#linglong_keys[@]} -eq 0 ]; then
        Echo_Yellow "未找到已安装的灵珑服务，跳过灵珑组件初始化"
        return 0
    fi

    # 获取第一个灵珑节点信息（暂不支持多节点）
    local success_linglong_key=${linglong_keys[0]}
    Echo_Yellow "开始初始化 ${ms_type} 灵珑组件"

    local host=$(yq ".microservice.linglong.${success_linglong_key}.host" ${metadata_file})
    local dest_path=$(yq ".microservice.linglong.${success_linglong_key}.base_path" ${metadata_file})
    local linglong_db_key=$(yq ".microservice.linglong.${success_linglong_key}.depends[] | select(.sub_type==\"biz\") | .depend_key" ${metadata_file})

    # 获取当前微服务的数据库信息
    local app_db_key=$(yq ".microservice.${ms_type}.${ms_name}.depends[] | select(.sub_type==\"biz\") | .depend_key" ${metadata_file})
    local app_database=$(yq ".microservice.${ms_type}.${ms_name}.depends[] | select(.sub_type==\"biz\") | .database" ${metadata_file})

    # 检查组件包是否存在
    local component_package="../../src/web/${ms_type}/${ms_type}-linglong.tar"

    if [ ! -f "${component_package}" ]; then
        Echo_Yellow "未找到灵珑组件包: ${component_package}，跳过灵珑初始化"
        return 0
    fi

    # 执行灵珑初始化
    local hosts_yml=../../ansible/inventory/hosts.yml
    ansible-playbook -i ${hosts_yml} \
        -e "host=${host}" \
        -e "app_type=${ms_type}" \
        -e "app_name=${ms_name}" \
        -e "app_database=${app_database}" \
        -e "dest_path=${dest_path}" \
        -e "linglong_db_key=${linglong_db_key}" \
        -e "db_key=${app_db_key}" \
        -e "@${metadata_file}" \
        ../../ansible/linglong_init.yml

    local rst=$?
    if [ $rst -gt 0 ]; then
        Echo_Red "${ms_type} 灵珑组件初始化失败！"
        return 1
    else
        Echo_Green "${ms_type} 灵珑组件初始化成功！"
        # 更新 linglong_init.yml
        yq eval ".${ms_type} = 1" -i ${linglong_init_file}

        # 提示重启灵珑服务
        local linglong_ip=$(yq ".microservice.linglong.${success_linglong_key}.ip" ${metadata_file})
        Echo_Yellow "灵珑组件初始化完成，需要重启灵珑服务才能生效"
        Echo_Yellow "灵珑服务所在IP: ${linglong_ip}"
        read -p "请输入灵珑服务ip确认重启对应灵珑服务？(${linglong_ip}): " restart_confirm

        if [[ "${restart_confirm}" =~ ^${linglong_ip}$ ]]; then
            Echo_Green "开始重启灵珑服务..."
            ansible-playbook -i ${hosts_yml} \
                -e "host=${host}" \
                -e "service_name=linglong" \
                -e "@${metadata_file}" \
                ../../ansible/restart_service.yml

            if [ $? -eq 0 ]; then
                Echo_Green "灵珑服务重启成功！"
            else
                Echo_Yellow "灵珑服务重启失败，请手动重启"
            fi
        else
            Echo_Yellow "已跳过灵珑服务重启，请稍后手动重启"
        fi
    fi
}

run_ms_install "$@"
