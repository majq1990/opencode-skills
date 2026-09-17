hostgroup=$1

hosts_file="/etc/ansible/hosts"
deploy_update_path="/egova/update"
deploy_web_path="/egova/web"
mis_app_types=("eUrbanUMA" "eUrbanMF" "eUrbanMIS" "eUrbanSG")
ms_template_file=../template/microservice_template.yml

if [ "$hostgroup" == "" ];then
    echo "请输入分组"
    exit 1
elif ! grep -q "^\[$hostgroup\]" "$hosts_file"; then
    echo "分组不存在，请检查$hosts_file文件"
    exit 1
fi

if ! test -d $deploy_update_path/; then
    mkdir -p $deploy_update_path
fi

timestamp=$(date +%Y%m%d%H%M%S)
zip_files=($(find $deploy_update_path -name "*.zip" 2>/dev/null))
for zip_file in ${zip_files[@]} ; do
  echo "解压: $zip_file..."
  unzip -o "$zip_file" -d $deploy_update_path
done

function update_mis(){
    local app_name=$1
    local lib_path=$app_name/WEB-INF/lib
    local jar_files=$(ls $deploy_update_path/$lib_path 2>/dev/null | xargs)
    echo "更新后端jar: $jar_files..."
    ansible-playbook -i ../../ansible/inventory/hosts.yml -e "hostgroup=${hostgroup} timestamp=${timestamp} jar_files='${jar_files[*]}' app_name=${app_name} " ../../ansible/onekey_update_web.yml
    local dir_paths=$(find $deploy_update_path/$app_name/view -mindepth 1 -maxdepth 1 -type d | xargs)
    local file_paths=$(find $deploy_update_path/$app_name/view -mindepth 1 -maxdepth 1 -type f | xargs)
    if [ -n "$file_paths" ]; then
       echo "更新前端文件: $file_paths..."
       ansible-playbook -i ../../ansible/inventory/hosts.yml -e "hostgroup=${hostgroup} file_paths='${file_paths}' timestamp=${timestamp} app_name=${app_name} " ../../ansible/onekey_update_web.yml
    fi
    if [ -n "$dir_paths" ]; then
      echo "更新前端目录:$dir_paths ..."
      dir_paths=$(echo $dir_paths | sed "s|$deploy_update_path/||g")
      ansible-playbook -i ../../ansible/inventory/hosts.yml -e "hostgroup=${hostgroup} dir_paths='${dir_paths}' timestamp=${timestamp} app_name=${app_name} " ../../ansible/onekey_update_web.yml
    fi
}
function update_microservice(){
    local deploy_path=$(yq ".${SELECTED_PRODUCT_NAME}.base_path" ${ms_template_file})
    local jar_name=$(yq ".${SELECTED_PRODUCT_NAME}.jar_name" ${ms_template_file})
    local src_web_paths=$(find $deploy_update_path/${SELECTED_PRODUCT_NAME} -mindepth 1 -maxdepth 1 -type d | xargs)
    local src_jar_path=$(find $deploy_update_path/${SELECTED_PRODUCT_NAME} -mindepth 1 -maxdepth 1 -type f | xargs)
    ansible-playbook -i ../../ansible/inventory/hosts.yml -e "hostgroup=${hostgroup} timestamp=${timestamp} app_name=${SELECTED_PRODUCT_NAME} jar_name=${jar_name} src_web_paths=${src_web_paths} src_jar_path=${src_jar_path} deploy_path=${deploy_path} "  .../../ansible/onekey_update_web.yml
}
function display_mc_select() {
    local index=0
    local keys=($(yq '.[] | key ' ${ms_template_file}))
    echo "请选择更新的产品："
    for key in "${keys[@]}"; do
      local server_name=$(yq ".${key}.name" ${ms_template_file})
      echo "${index}: ${server_name}"
      ((index++))
    done
    echo "q: 退出"
    read -p "请选择: " Select
    if [[ "$Select" == "q" ]]; then
        echo "退出"
        return
    fi
  # 根据用户选择的索引找到对应的 key
    if [[ "$Select" =~ ^[0-9]+$ ]] && [[ "$Select" -ge 0 ]] && [[ "$Select" -lt "${#keys[@]}" ]]; then
        SELECTED_PRODUCT_NAME=${keys[$Select]}
    else
        Echo_Red "无效选择，请重试。"
        display_mc_select
    fi

}
function display_select(){
	echo "请选择待更新的产品"
    echo "1 : 智信云"
    echo "2 : 微服务"
    read -p "请选择: " Select
    case "$Select" in
    1)
        run_mis
        ;;
    2)
       display_mc_select
       update_microservice
        ;;
    *)
        echo "选择错误！"
        display_select
        ;;
    esac
}
function run_mis(){
     for app_type in "${mis_app_types[@]}" ; do
        if ! test -d $deploy_update_path/$app_type/; then
            echo "$app_type 未找到，跳过"
            continue
        fi
        echo "-------开始更新 ----------"
        update_mis $app_type
        echo "-------$app_type 更新完成----------"
     done
     echo "请手动执行，批量重启系统命令：ansible $hostgroup -m shell -a "systemctl restart tomcat-$hostgroup" "
}
function run(){
  display_select
}
run


