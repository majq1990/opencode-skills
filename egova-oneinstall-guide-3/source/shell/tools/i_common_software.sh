#!/bin/bash
# 分布式部署、一站式部署、轻量化部署通用安装部分
# 设计思路概要：
# 1.根据已配置好的multi_server.yml生成待安装列表至metadata.yml
# 2.根据metadata.yml逐个部署各服务应用
# 3.配置主入口nginx

metadata_file=../../ansible/inventory/metadata.yml
hosts_yml=../../ansible/inventory/hosts.yml
global_conf=../../ansible/group_vars/all.yml
linglong_init_file=../../ansible/inventory/linglong_init.yml

server_config_file=$1
software_config_file=../../ansible/inventory/software_tools.yml
service_template_file=../template/tomcat_app_template.yml
ms_template_file=../template/microservice_template.yml

. ../include/tool_metadata.sh
. ../include/tool_multi.sh ${server_config_file}

TYPE_ARRAY=("software" "microservice" "service")
STATUS_ARRAY=("undeployed" "success" "delete")
DB_TYPE_ARRAY=("biz" "stat")
APP_TYPES=("eUrbanSG" "eGovaPublic" "faceserver" "statgather")
MS_APP_TYPES=("eUrbanUMA" "eUrbanMF" "eUrbanMIS" "eurbanpro" "workflow" "eurbanpro_media" "sms" "IM" "usercenter" "linglong" "xuanzang" "evaluation" "wukong" "dex" "bigdata" "dataflow")
MJ_APP_TYPES=("IM" "usercenter" "linglong" "xuanzang" "evaluation" "wukong" "dex" "mjing")

PROXY_BIZ_FLAG=0
PROXY_STAT_FLAG=0
PROXY_BIZ_HOST=""
PROXY_STAT_HOST=""

# 自动根据数据库IP生成代理IP
function  modify_mysql_proxy_ip()
{
    #自动判断mysql代理
    local biz_server="ip_db_biz"
    local stat_server="ip_db_stat"
    local biz_db_count=$(get_slave_node_count $biz_server)
    local stat_db_count=$(get_slave_node_count $stat_server)

    if [ $biz_db_count -gt 0 ];then
         PROXY_BIZ_FLAG=1
         PROXY_BIZ_HOST=$(get_master_host $biz_server)
         Echo_Green "业务库代理：$PROXY_BIZ_HOST"
    else
        PROXY_BIZ_FLAG=0
        PROXY_BIZ_HOST=""
        Echo_Green "业务库代理：无"
    fi

    if [ $stat_db_count -gt 0 ];then
         PROXY_STAT_FLAG=1
         PROXY_STAT_HOST=$(get_master_host $stat_server)
         Echo_Green "统计库代理：$PROXY_STAT_HOST"
    else
        PROXY_STAT_FLAG=0
        PROXY_STAT_HOST=""
        Echo_Green "统计库代理：无"
    fi
    yq -i '.proxy_biz_flag="'$PROXY_BIZ_FLAG'"' ${global_conf}
    yq -i '.proxy_stat_flag="'$PROXY_STAT_FLAG'"' ${global_conf}
}

# 根据服务器配置生成待安装元数据
function save_modules_to_metadata() {
    # 获取已配置的服务器
    local host
    local sub_flag
    local sub_count=0
    local hosts=($(yq '.[] | select(.hosts.master != null) | key ' ${server_config_file}))
    for key in "${hosts[@]}"; do
        host=$(get_master_host $key)
        init_metadata_config $key $host "master"

        # 初始化从节点配置
        sub_flag=$(yq ".${key}.sub_flag" ${server_config_file})
        sub_count=$(get_slave_node_count $key)
        if [ "$sub_flag" == "1" ] && [ $sub_count -gt 0 ];then
           local sub_nodes=($(yq '.'${key}'.hosts.slave[]' ${server_config_file}))
           for sub_node in "${sub_nodes[@]}"; do
              init_metadata_config $key $sub_node "slave"
            done
        fi
    done
}

# 初始化待安装服务配置
function init_metadata_config() {
    local key=$1
    local host=$2
    local host_type=$3
    local size=0

    local desc=$(get_server_name $key)
    local modules_size=$(get_modules_count ${key})
    local index=0
    local server_type
    local sub_type
    local server_name
    while [ $index -lt $modules_size ]; do
        server_type=$(get_module_value_by_key ${key} ${index} "type")
        sub_type=$(get_module_value_by_key ${key} ${index} "sub_type")
        server_name=$(get_module_value_by_key ${key} ${index} "name")

        # 判断是否需要安装cetus代理
        local skip_flag=0
        if [ "$server_type" == "cetus" ]; then
            if [ "$host_type" == "slave" ]; then
                # 从节点不安装cetus
                skip_flag=1;
            fi
            if [ "$sub_type" == "${DB_TYPE_ARRAY[0]}" ] && [ "$PROXY_BIZ_FLAG" == "0" ]; then
                skip_flag=1;
            elif [ "$sub_type" == "${DB_TYPE_ARRAY[1]}" ] && [ "$PROXY_STAT_FLAG" == "0" ]; then
                skip_flag=1;
            fi
        fi
        if [ "$skip_flag" == "1" ]; then
            ((index=index+1))
            continue
        fi

        local prefix_key="${server_type}.${sub_type}"
        if [ "${server_type}" != "${TYPE_ARRAY[1]}" ] && [ "${server_type}" != "${TYPE_ARRAY[2]}" ]; then
            server_type="${TYPE_ARRAY[0]}"
            sub_type=$(get_module_value_by_key ${key} ${index} "type")
            prefix_key="${sub_type}"
        fi
        echo "在${desc}：${host}生成${sub_type}待部署记录"
        local success_count=$(count_by_status $prefix_key "${STATUS_ARRAY[1]}" $host)
        if [ ${success_count} -gt 0 ]; then
            Echo_Yellow "${sub_type}在${host}服务器已部署，将跳过安装"
            ((index=index+1))
            continue
        fi

        local undeployed_count=$(count_by_status $prefix_key "${STATUS_ARRAY[0]}" $host)
        if [ ${undeployed_count} -gt 0 ]; then
            # 已生成待部署记录，不再重复增加
            Echo_Yellow "已生成${sub_type}待部署记录，不再重复增加"
            ((index=index+1))
            continue
        fi

        # 生成sofyware配置文件
        if [ "${server_type}" == "${TYPE_ARRAY[0]}" ];then
            local file=../../ansible/inventory/template/${sub_type}.yml
            touch $file
            local params_len=$(yq '.software_tools[] | select(.name == "'${sub_type}'").params | length' ${software_config_file})
            # 设置默认值为 0，如果params_len为空字符串
            params_len=${params_len:-0}
            if [ ${params_len} -gt 0 ]; then
                local param_index=0
                local idx=1
                while [ ${param_index} -lt ${params_len} ]; do
                    local name=$(yq '.software_tools[] | select(.name == "'${sub_type}'").params['${param_index}'].name' ${software_config_file})
                    local last=$(yq ".${name}" ${file})
                    if [ "$name" == "db_type" ]; then
                        last=$(get_module_value_by_key ${key} ${index} "sub_type")
                    fi
                    if [ "$last" == "null" ] || [ "$last" == "" ]; then
                        last=$(yq '.software_tools[] | select(.name == "'${sub_type}'").params['${param_index}'].default' ${software_config_file})
                    fi
                    yq -i '.'${name}' = "'${last}'"' $file
                    ((param_index=param_index+1))
                done
            fi
            # 设置额外参数到metadata.yml
            local ext_params=$(get_module_value_by_key ${key} ${index} "ext_params")
            if [ "$ext_params" != "null" ] && [ "$ext_params" != "" ]; then
                # 解析ext_params，格式为key:value,key:value
                local ext_params_array=(${ext_params//,/ })
                for ext_param in "${ext_params_array[@]}"; do
                    local ext_params_key=$(echo $ext_param | awk -F ":" '{print $1}')
                    local ext_params_value=$(echo $ext_param | awk -F ":" '{print $2}')
                    yq -i ".${ext_params_key} = \"${ext_params_value}\"" $file
                done
            fi
        fi

        size=$(yq '.'$prefix_key' | length ' ${metadata_file})
        (( size++ )) || true
        # 保存元数据配置并初始化status、host
        local deploy_status_flag=($(yq '.'${key}'.deploy_status_flag' ${server_config_file}))
        if [ "${deploy_status_flag}" -eq 0 ];then
           save_metadata ${server_type} ${host} ${sub_type} ${size} "${STATUS_ARRAY[0]}"
        else
           save_metadata ${server_type} ${host} ${sub_type} ${size} "${STATUS_ARRAY[1]}"
        fi
        ((index=index+1))
    done
}

# 更新依赖的key
function update_depend_key() {
    local prefix_key=$1
    local host=$2
    local depend_size=$(yq ".${prefix_key}.depends | length" ${metadata_file})
    local index=0
    while [ $index -lt $depend_size ]; do
        local depend_name=$(yq '.'${prefix_key}'.depends['$index'].name' ${metadata_file})
        local depend_type=$(yq '.'${prefix_key}'.depends['$index'].type' ${metadata_file})
        local depend_sub_type=$(yq '.'${prefix_key}'.depends['$index'].sub_type' ${metadata_file})
        # 判断是否使用数据库代理
        local use_proxy=0
        if [ "$depend_type" == "mysql" ]; then
            if [ "$depend_sub_type" == "${DB_TYPE_ARRAY[0]}" ] && [ "$PROXY_BIZ_FLAG" == "1" ]; then
                use_proxy=1
            elif [ "$depend_sub_type" == "${DB_TYPE_ARRAY[1]}" ] && [ "$PROXY_STAT_FLAG" == "1" ]; then
                use_proxy=1
            fi
        fi
        if [ "$use_proxy" == "1" ]; then
            depend_name="cetus数据库代理"
            depend_type="cetus"
        fi
        local depend_prefix_key="${depend_type}"
        if [ "$depend_type" == "${TYPE_ARRAY[1]}" ] || [ "$depend_type" == "${TYPE_ARRAY[2]}" ]; then
            depend_prefix_key="${depend_type}.${depend_sub_type}"
        fi
#        # 根据depend_type获取对应主机
        if [ "$depend_type" == "usercenter_redis" ]; then
              depend_type="redis"
              depend_prefix_key="redis"
        fi
        local config_key=$(get_key_by_module_type $depend_type $depend_sub_type)
        if [ "$config_key" == "null" ] || [ "$config_key" == "" ]; then
            Echo_Red "未找到${depend_name}对应主机！$config_key"
            exit 0
        fi
        local depend_host=$(get_master_host $config_key)
        local depend_key=$(get_depend_key_by_status $depend_prefix_key "${STATUS_ARRAY[1]}" $depend_host)
        if [ -n "$depend_key" ]; then
            # 已安装成功，直接更新依赖的key
            yq -i '.'${prefix_key}'.depends['$index'].depend_key="'${depend_key}'"' ${metadata_file}
        else
            # 获取是否有待部署的key
            depend_key=$(get_depend_key_by_status $depend_prefix_key "${STATUS_ARRAY[0]}" $depend_host)
            if [ -n "$depend_key" ]; then
                # 先安装依赖的服务
                if [ "${depend_type}" == "${TYPE_ARRAY[1]}" ];then
                    # microservice
                    install_microservice $depend_sub_type
                elif [ "${depend_type}" == "${TYPE_ARRAY[2]}" ];then
                    # service
                    install_tomcat_service $depend_sub_type
                else
                    install_software $depend_type
                fi
                # 检查安装是否成功
                if [ $? -eq 0 ]; then
                    # 更新依赖的key
                    depend_key=$(get_depend_key_by_status $depend_prefix_key "${STATUS_ARRAY[1]}" $depend_host)
                    yq -i '.'${prefix_key}'.depends['$index'].depend_key="'${depend_key}'"' ${metadata_file}
                else
                    echo "退出安装"
                    exit 0
                fi
            else
                Echo_Red "未找到${depend_name}安装信息，请先配置！"
                exit 0
            fi
        fi
        let "index=index+1"
    done
}

# 安装软件
function install_software() {
    local type=$1

    # 设置状态码，默认为0（表示成功）
    local status=0
    local master_biz=0
    local master_stat=0
    local keys=($( yq '.'${type}'.[] | select(.status=="'${STATUS_ARRAY[0]}'" and .host != "none") | key ' ${metadata_file}))
    local sub_key
    for sub_key in "${keys[@]}"; do
        Echo_Green "==============开始安装${type}=============="
        local host=$(yq '.'${type}'.'${sub_key}'.host' ${metadata_file})
        local size=$(echo $sub_key | awk -F "_" '{print $NF}')
        local db_type="${DB_TYPE_ARRAY[0]}"
        local install_file=../../ansible/install_${type}.yml

        if [[ "$type" == "cetus" && "${server_config_file}" =~ "eurbanpro" ]]; then
            db_type=$(yq '.'${type}'.'${sub_key}'.db_type' ${metadata_file})
            install_file=../../ansible/install_eurbanpro_cetus.yml
        fi
        ansible-playbook -i ${hosts_yml} -e "host=${host} db_type=${db_type} software_type=${type} software_key=${sub_key}" -e "@../../ansible/inventory/template/${type}.yml"  ${install_file}
        local rst=$?
        if [ $rst -eq 0 ]; then
            # 更新状态
            save_metadata "${TYPE_ARRAY[0]}" ${host} ${type} ${size} "${STATUS_ARRAY[1]}"
            save_app_hosts ${type} ${host}
            Echo_Green "${type}安装成功！"
        else
            Echo_Red "${type}安装失败！"
            status=1
            exit 0
        fi
        if [ "$type" == "mysql" ] ; then
          mysql_db_type=$(yq '.'${type}'.'${sub_key}'.db_type' ${metadata_file})
          if [ ${mysql_db_type} == "biz" ] && [ ${master_biz} == 0 ] ;then
            Echo_Green "==============开始安装xtrabackup=============="
             ansible-playbook -i ${hosts_yml} -e "host=${host} db_type=${db_type}"  ../../ansible/install_xtrabackup.yml
             master_biz=1
          fi
          if [ ${mysql_db_type} == "stat" ] && [ ${master_stat} == 0 ] ;then
              Echo_Green "==============开始安装xtrabackup=============="
              ansible-playbook -i ${hosts_yml} -e "host=${host} db_type=${db_type}"  ../../ansible/install_xtrabackup.yml
              master_stat=1
          fi
        fi
    done
    # 返回状态码
    return $status
}

# 安装微服务
function install_microservice() {
    local ms_type=$1

    # 设置状态码，默认为0（表示成功）
    local status=0
    local prefix_key="${TYPE_ARRAY[1]}.${ms_type}"
    local keys=($(yq '.'${prefix_key}'.[] | select(.status=="'${STATUS_ARRAY[0]}'" and .host != "none") | key ' ${metadata_file}))
    local sub_key
    for sub_key in "${keys[@]}"; do
        Echo_Blue "=========================="
        Echo_Green "==============开始安装${ms_type}=============="
        local host=$(yq '.'${prefix_key}'.'${sub_key}'.host' ${metadata_file})
        local server_port=$(yq '.'${prefix_key}'.'${sub_key}'.server_port' ${metadata_file})
        # 更新依赖的key
        update_depend_key "${prefix_key}.${sub_key}" ${host}

        local depend_size=$(yq ".${prefix_key}.${sub_key}.depends | length" ${metadata_file})
        local index=0
        while [ $index -lt $depend_size ]; do
            local depend_name=$(yq '.'${prefix_key}'.'${sub_key}'.depends['$index'].name' ${metadata_file})
            local depend_type=$(yq '.'${prefix_key}'.'${sub_key}'.depends['$index'].type' ${metadata_file})
            local depend_key=$(yq '.'${prefix_key}'.'${sub_key}'.depends['$index'].depend_key' ${metadata_file})
            # 如果是minio,需要创建桶、用户并赋权
            if [ "${depend_type}" == "minio" ]; then
             local minio_host=$(yq '.'${depend_type}'.'${depend_key}'.host ' ${metadata_file})
             ansible-playbook -i ${hosts_yml} -e "host=${minio_host} app_type=${ms_type} depend_key=${depend_key}" ../../ansible/config_minio_bucket.yml
            fi
            # nacos 命名空间配置
            if [ "${depend_type}" == "nacos" ]; then
                local nacos_host=$(yq '.'${depend_type}'.'${depend_key}'.host' ${metadata_file})
                if [ "${nacos_host}" != "null" ]; then
                    ansible-playbook -i ${hosts_yml} -e "host=${nacos_host} app_type=${ms_type} depend_key=${depend_key}" ../../ansible/config_nacos_namespace.yml
                fi
            fi
            let index++
        done
        local ms_install_file=../../ansible/install_microservice.yml
         if [ -e ../../ansible/install_${ms_type}.yml ];then
               ms_install_file=../../ansible/install_${ms_type}.yml
         fi
        jvm_opts=$(yq ".${ms_type}.environment.jvm_opts" "${ms_template_file}")
        max_xmx=$(echo "$jvm_opts" | sed -n 's/.*-Xmx\([0-9]\+\)m.*/\1/p')
        ansible-playbook -i ${hosts_yml} -e "max_xmx=${max_xmx} host=${host} app_type=${ms_type} app_name=${sub_key} app_port=${server_port}" -e "@${metadata_file}" ${ms_install_file}
        local rst=$?
        if [ $rst -gt 0 ]; then
            Echo_Red "${ms_type}安装失败！"
            status=1
            exit 0
        else
            Echo_Green "${ms_type}安装成功！"
        fi
    done
    # 返回状态码
    return $status
}

# 安装tomcat类应用
function install_tomcat_service() {
    local app_type=$1

    # 设置状态码，默认为0（表示成功）
    local status=0
    local prefix_key="${TYPE_ARRAY[2]}.${app_type}"
    local keys=($(yq '.'${prefix_key}'.[] | select(.status=="'${STATUS_ARRAY[0]}'" and .host != "none") | key ' ${metadata_file}))
    local sub_key
    for sub_key in "${keys[@]}"; do
        Echo_Yellow "=========================="
        Echo_Green "==============开始安装${app_type}=================="
        local host=$(yq '.'${prefix_key}'.'${sub_key}'.host' ${metadata_file})
        local biz_type=$(yq '.'${prefix_key}'.'${sub_key}'.biz_type' ${metadata_file})
        local server_port=$(yq '.'${prefix_key}'.'${sub_key}'.server_port' ${metadata_file})
        # 更新依赖的key
        update_depend_key "${prefix_key}.${sub_key}" ${host}

        local install_file=../../ansible/install_tomcat_app.yml
        if [[  "${server_config_file}" =~ "eurbanpro" ]]; then
              install_file=../../ansible/install_eurbanpro_tomcat_app.yml
        fi
        if [ -e ../../ansible/install_${app_type}.yml ];then
            install_file=../../ansible/install_${app_type}.yml
        fi
        ansible-playbook -i ${hosts_yml} -e "host=${host} app_type=${app_type} app_name=${sub_key} app_port=${server_port} biz_type=${biz_type}" -e "@${metadata_file}" ${install_file}
        local rst=$?
        if [ $rst -gt 0 ]; then
            Echo_Red "${app_type}安装失败！"
            status=1
            exit 0
        else
            Echo_Green "${app_type}安装成功！"
        fi
    done
    # 返回状态码
    return $status
}
function do_install() {
   local status_flag=0
    # 安装服务
    local types=($(yq '.[] | key ' ${metadata_file}))
    for type in "${types[@]}"; do
        if [ "${type}" == "${TYPE_ARRAY[1]}" ];then
            # microservice
            local ms_types=($(yq '.'${TYPE_ARRAY[1]}'.[] | key ' ${metadata_file}))
            for ms_type in "${ms_types[@]}"; do
                install_microservice $ms_type
            done
        elif [ "${type}" == "${TYPE_ARRAY[2]}" ];then
            # service
            local app_types=($(yq '.'${TYPE_ARRAY[2]}'.[] | key ' ${metadata_file}))
            for app_type in "${app_types[@]}"; do
                install_tomcat_service $app_type
            done
        else
            install_software $type
        fi
    done
    # --- 灵珑组件初始化 ---
    # 判断是否有已安装成功的灵珑微服务
    # 存在linglong_init文件才处理
    if [ -e ${linglong_init_file} ]; then
        Echo_Yellow "开始初始化灵珑组件"
        local linglong_keys=($(yq '.'${TYPE_ARRAY[1]}'.linglong[] | select(.status == "success") | key' ${metadata_file}))
        if [ ${#linglong_keys[@]} -ne 0 ]; then
            # 暂时不考虑多节点，只处理第一个
            local success_linglong_key=${linglong_keys[0]}
            Echo_Yellow "开始初始化${success_linglong_key}组件"
            local host=$(yq '.'${TYPE_ARRAY[1]}'.linglong.'${success_linglong_key}'.host' ${metadata_file})
            local dest_path=$(yq '.'${TYPE_ARRAY[1]}'.linglong.'${success_linglong_key}'.base_path' ${metadata_file})
            local linglong_db_key=$(yq '.'${TYPE_ARRAY[1]}'.linglong.'${success_linglong_key}'.depends[] | select(.sub_type=="biz")|.depend_key' ${metadata_file})
            local need_init_ms=$(yq eval 'to_entries | .[] | select(.value == 0) | .key' ${linglong_init_file})
            # 记录是否需要重启
            local restart_flag=0
            # 判断需要初始化的微服务是否已安装成功
            for ms_type in ${need_init_ms}; do
                local ms_key=($(yq '.'${TYPE_ARRAY[1]}'.'${ms_type}'.[] | select(.status == "success") | key' ${metadata_file}))
                if [ ${#ms_key[@]} -ne 0 ]; then
                    Echo_Yellow "开始初始化${ms_type}组件"
                    local ms_sub_key=${ms_key[0]}
                    local app_db_key=$(yq '.'${TYPE_ARRAY[1]}'.'${ms_type}'.'${ms_sub_key}'.depends[] | select(.sub_type=="biz")|.depend_key' ${metadata_file})
                    local app_database=$(yq '.'${TYPE_ARRAY[1]}'.'${ms_type}'.'${ms_sub_key}'.depends[] | select(.sub_type=="biz")|.database' ${metadata_file})
                    ansible-playbook -i ${hosts_yml} -e "host=${host} app_type=${ms_type}  app_name=${ms_sub_key} app_database=${app_database} dest_path=${dest_path} linglong_db_key=${linglong_db_key} db_key=${app_db_key}" -e "@${metadata_file}" ../../ansible/linglong_init.yml
                    local rst=$?
                    if [ $rst -gt 0 ]; then
                        Echo_Red "${ms_type}灵珑组件初始化失败！"
                        status=1
                        exit 0
                    else
                        Echo_Green "${ms_type}灵珑组件初始化成功！"
                        # 更新linglong_init_file
                        yq eval '.'${ms_type}' = 1' -i ${linglong_init_file}
                        restart_flag=1
                    fi
                fi
            done
            # 若有组件初始化成功，进行重启交互
            if [ ${restart_flag} -eq 1 ]; then
                # 重启交互，输灵珑ip确认重启
                # 获取灵珑服务IP
                local linglong_ip=$(yq '.'${TYPE_ARRAY[1]}'.linglong.'${success_linglong_key}'.ip' ${metadata_file})
                Echo_Yellow "灵珑组件初始化完成，需要重启灵珑服务才能生效"
                Echo_Yellow "灵珑服务所在IP: ${linglong_ip}"
                Echo_Yellow "请输入灵珑服务ip确认重启对应灵珑服务？(${linglong_ip})"
                read -r restart_confirm
                if [[ "$restart_confirm" =~ ^${linglong_ip}$ ]]; then
                    Echo_Green "开始重启灵珑服务..."
                    # 重启灵珑服务
                    ansible-playbook -i ${hosts_yml} -e "host=${host} service_name=linglong" -e "@${metadata_file}" ../../ansible/restart_service.yml
                    local rst=$?
                    if [ $rst -eq 0 ]; then
                        Echo_Green "灵珑服务重启成功！"
                    else
                        Echo_Red "灵珑服务重启失败！"
                        status=1
                    fi
                else
                    Echo_Yellow "已跳过灵珑服务重启，请稍后手动重启"
                fi
            fi
        fi
    fi
    # 配置主入口nginx
    Echo_Yellow "开始配置出口nginx"
    local nginx_host=$(get_master_host "ip_nginx_main")
    Echo_Yellow "开始配置${app_type}路由"
    yq '.[] | select(.biz_type != null) | key ' ${service_template_file} | while read app_type; do
        if [[ "${server_config_file}" == *eurbanpro* && " ${APP_TYPES[@]} " =~ " ${app_type} " ]]; then
            continue
        fi
        Echo_Yellow "开始配置${app_type}路由"
        ansible-playbook -i ${hosts_yml} -e "app_type=${app_type} app_name=${app_name} host=${nginx_host} server_type=${TYPE_ARRAY[2]}" ../../ansible/config_outlet_nginx.yml
    done

    if [[  "${server_config_file}" =~ "eurbanpro" ]]; then
        for app_type in "${MS_APP_TYPES[@]}"
        do
           Echo_Yellow "=======开始配置${app_type}路由======="
           local keys=($(yq '.microservice.'${app_type}'.[] | select(.status=="success" and .host != "none") | key ' ${metadata_file}))
           if [ ${#keys[@]} -ne 0 ]; then
               app_name=${keys[0]}
           fi
           ansible-playbook -i ${hosts_yml} -e "app_type=${app_type} app_name=${app_name} host=${nginx_host}" ../../ansible/config_outlet_nginx.yml
        done
    elif [[  "${server_config_file}" =~ "mjing" ]]; then
        for app_type in "${MJ_APP_TYPES[@]}"
        do
           Echo_Yellow "=======开始配置${app_type}路由======="
           local keys=($(yq '.microservice.'${app_type}'.[] | select(.status=="success" and.host!= "none") | key' ${metadata_file}))
           if [ ${#keys[@]} -ne 0 ]; then
               app_name=${keys[0]}
           fi
           ansible-playbook -i ${hosts_yml} -e "app_type=${app_type} app_name=${app_name} host=${nginx_host}" ../../ansible/config_outlet_nginx.yml
        done
    fi
    Echo_Yellow "ansible执行日志见/var/log/ansible.log"
    #未部署eUrbanMIS情况下，配置主入口nginx
    ansible-playbook -i ${hosts_yml} -e " host=${nginx_host} " ../../ansible/check_main_nginx.yml
}
# 输出部署后的信息
function display_deploy_info() {
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
function main(){
    modify_mysql_proxy_ip
    save_modules_to_metadata
    do_install
    display_deploy_info
}

main