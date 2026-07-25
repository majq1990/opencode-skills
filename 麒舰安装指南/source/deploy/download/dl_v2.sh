#!/bin/bash
VER=1.0.1

WEB_VERS=(
"20240301"
)

INSTALL_TYPE_ARRAY=(
"V14智信云标准(标准城管)"
"麒舰平台微服务"
"基础平台微服务"
"一网统管业务线微服务"
"社会治理业务线微服务"
"城市生命线微服务"
"执法业务线微服务"
"GIS微服务"
"城市管理业务线微服务"
"AI业务线微服务"
"明镜场景微服务"
)

INSTALL_FILE_ARRAY=(
"oneinstall_v2-files-v14-standard.ini"
"oneinstall_v2-files-ms-eurbanpro.ini"
"oneinstall_v2-files-ms-basic.ini"
"oneinstall_v2-files-ms-mis.ini"
"oneinstall_v2-files-ms-sg.ini"
"oneinstall_v2-files-ms-fac.ini"
"oneinstall_v2-files-ms-elaw.ini"
"oneinstall_v2-files-ms-gis.ini"
"oneinstall_v2-files-ms-csgl.ini"
"oneinstall_v2-files-ms-ai.ini"
"oneinstall_v2-files-ms-mjing.ini"
)

tar_file=""
# 默认使用武汉服务器
domain=http://oneops.egova.com.cn:8093

# 处理启动参数
if [ "$1" = "--internal" ]; then
    domain=http://172.16.4.100:82
    echo "使用内部服务器: ${domain}"
fi

function downfile_with_auth(){
    local file=$1
    local target=$2
    [ "$target" == "" ] && target=${file##*/} && target=${target%%\?*}
    local retries=3
    until (( retries == 0 )); do
        wget -c "${file}" -O "${target}" --http-user="${user}" --http-passwd="${password}"
        if [ $? -eq 0 ];then
            echo "$file 下载成功！"
            return 0
        fi
        (( retries-- ))
        sleep 1
    done
    echo "!!!!!!!!!!!!!!! $file 下载失败！"
}

function download_fileslist(){
    # 下载前清除旧的ini文件，确保每次下载的ini是当前所需的
    rm -rf oneinstall_v2-files*.ini
    if [ "${web_version_select}" == "" ];then
      web_version_select=${WEB_VERS[0]}
    fi

    if [ "${base_select}" == "1" ];then
        downfile_with_auth ${domain}/one/v2/iniconfig/oneinstall_v2-files-base.ini
    elif [ "${base_select}" == "2" ];then
        downfile_with_auth ${domain}/one/v2/iniconfig/oneinstall_v2-files-base.ini
        downfile_with_auth ${domain}/one/v2/iniconfig/oneinstall_v2-files-env-base.ini
    fi
    if [ "$script_select" != "0" ] ; then
        downfile_with_auth ${domain}/one/v2/iniconfig/${INSTALL_FILE_ARRAY[$(($script_select - 1))]}
        sed -i "s/\${WEB_VER}/${web_version_select}/g" oneinstall_v2-files*.ini
    fi

    # 调试信息：显示替换前的ini文件内容
    echo "=== 替换前ini文件内容 ==="
    for ini in oneinstall_v2-files*.ini; do
        if [ -f "$ini" ]; then
            echo "文件: $ini"
            head -5 "$ini"
        fi
    done

    # 执行替换操作 - 应用路径映射
    local mapped_path="${os_select}"
    if [ -n "${OS_PATH_MAP[${os_select}]}" ]; then
        mapped_path="${OS_PATH_MAP[${os_select}]}"
    fi
    sed -i "s/\${OS_VER}/${mapped_path}/g" oneinstall_v2-files*.ini
    sed -i "s/\${VER}/${VER}/g" oneinstall_v2-files*.ini
    sed -i "s/\${architecture}/${architecture}/g" oneinstall_v2-files*.ini

    # 调试信息：显示替换后的ini文件内容
    echo "=== 替换后ini文件内容 ==="
    echo "os_select 变量值: $os_select"
    for ini in oneinstall_v2-files*.ini; do
        if [ -f "$ini" ]; then
            echo "文件: $ini"
            head -5 "$ini"
        fi
    done
}
#根据files文件下载
function download_by_fileslist(){
    for ini in oneinstall_v2-files*.ini; do
        if [ -f "$ini" ]; then  # 检查文件是否存在
            local keys_array=()
            while IFS= read -r line; do
                # 判断key是否包含"-"字符
                if [[ $line =~ ^\[(.*-[^]]+)\]$ ]]; then
                  keys_array+=("${BASH_REMATCH[1]}")
                fi
            done < "$ini"
            # 判断数组是否为空
            if [ ${#keys_array[@]} -eq 0 ]; then
              # 下载全部
              web_select="all"
            else
              # 数组不为空，按需下载
              display_web_app_select "${keys_array[@]}"
            fi
#            echo "选择下载的web应用：$web_select"
            download_by_select "$ini" "$web_select"
        fi
    done
}
function construct_download_url() {
    local file=$1
    if [[ "${file}" =~ "oneinstall_v2.sh" ]]; then
        echo "${domain}/one/v2/${file}?user=${user}&project=${project}&os_select_info=${os_select_info}&date=$( date +%Y%m%d_%H%M)"
    else
        echo "${domain}/one/v2/${file}"
    fi
}
#根据选择项下载对应安装包
function download_by_select(){
    local ini=$1
    local type=$2
    while IFS= read -r file; do
        # 排除以 [ 开头的行以及空行
         if [[ $file =~ ^\[ ]] || [[ -z "$file" ]]; then
                    continue
         fi
         if [ "$type" != "all" ] && [[ "$file" != *"$type"* ]]; then
                     continue
         fi
         local download_url
         download_url=$(construct_download_url "$file")
         downfile_with_auth "$download_url"
    done < "$ini"
}
# 操作系统类型定义
OS_TYPES=(
"CentOS"
"Ubuntu"
"银河麒麟"
"欧拉"
"UOS"
"龙蜥"
)

# CPU架构
CPU_ARCHS=("x86" "arm")

# 操作系统路径映射表
# 格式："内部版本名_架构"="实际路径名"
declare -A OS_PATH_MAP=(
    ["kylin_V10_SP3_x86"]="kylinV10_x86"
    ["kylin_V10_SP3_arm"]="kylinV10_arm"
    ["kylin_V11_x86"]="kylinV11_x86"
    ["centos_7.9_x86"]="centos7_x86"
    ["ubuntu_20.04_x86"]="ubuntu20_x86"
    ["openEuler_22.03_x86"]="openEuler22_x86"
    ["openEuler_22.03_arm"]="openEuler22_arm"
    ["uos_20_1060a_x86"]="uos20a_x86"
    ["uos_20_1060a_arm"]="uos20a_arm"
    ["uos_20_1060e_x86"]="uos20e_x86"
    ["uos_20_1060e_arm"]="uos20e_arm"
    ["uos20_1070a_x86"]="uos20-1070a_x86"
    ["anolis_8.9_x86"]="anolis8_x86"
    ["anolis_8.9_arm"]="anolis8_arm"
    ["anolis_7.9_x86"]="anolis7_x86"
)

# 仅支持x86架构的操作系统版本
X86_ONLY_VERSIONS=(
    "kylin_V11"
    "uos20_1070a"
    "centos_7.9"
    "ubuntu_20.04"
    "anolis_7.9"
)

function display_os_type(){
    echo "请选择操作系统类型"
    for ((i=0; i<${#OS_TYPES[@]}; i++)); do
        echo "$(($i+1)) : ${OS_TYPES[$i]}"
    done
    read -p "请选择: " Select
    case "$Select" in
    [1-6])
        os_type_idx=$(($Select-1))
        os_type=${OS_TYPES[$os_type_idx]}
        display_os_version
        ;;
    *)
        echo "选择错误！"
        display_os_type
        ;;
    esac
}

function display_os_version(){
    echo "请选择 ${os_type} 的版本"
    case "$os_type" in
    "CentOS")
        echo "1 : CentOS 7.9"
        read -p "请选择: " Select
        case "$Select" in
        1) os_version="centos_7.9" ;;
        *) echo "选择错误！"; display_os_version; return ;;
        esac
        ;;
    "Ubuntu")
        echo "1 : Ubuntu 20.04"
        read -p "请选择: " Select
        case "$Select" in
        1) os_version="ubuntu_20.04" ;;
        *) echo "选择错误！"; display_os_version; return ;;
        esac
        ;;
    "银河麒麟")
        echo "1 : 银河麒麟 V10 SP3"
        echo "2 : 银河麒麟 V11"
        read -p "请选择: " Select
        case "$Select" in
        1) os_version="kylin_V10_SP3" ;;
        2) os_version="kylin_V11" ;;
        *) echo "选择错误！"; display_os_version; return ;;
        esac
        ;;
    "欧拉")
        echo "1 : 欧拉 22.03"
        read -p "请选择: " Select
        case "$Select" in
        1) os_version="openEuler_22.03" ;;
        *) echo "选择错误！"; display_os_version; return ;;
        esac
        ;;
    "UOS")
        echo "1 : UOS 20 1060a"
        echo "2 : UOS 20 1060e"
        echo "3 : UOS 20 1070a"
        read -p "请选择: " Select
        case "$Select" in
        1) os_version="uos_20_1060a" ;;
        2) os_version="uos_20_1060e" ;;
        3) os_version="uos20_1070a" ;;
        *) echo "选择错误！"; display_os_version; return ;;
        esac
        ;;
    "龙蜥")
        echo "1 : 龙蜥 8.9"
        echo "2 : 龙蜥 7.9"
        read -p "请选择: " Select
        case "$Select" in
        1) os_version="anolis_8.9" ;;
        2) os_version="anolis_7.9" ;;
        *) echo "选择错误！"; display_os_version; return ;;
        esac
        ;;
    esac
    display_cpu_arch
}

function display_cpu_arch(){
    # 检查是否为仅支持x86的版本
    for x86_only in "${X86_ONLY_VERSIONS[@]}"; do
        if [ "$os_version" = "$x86_only" ]; then
            echo "注意：${os_type} ${os_version} 仅支持 x86 架构"
            architecture="x86"
            os_select="${os_version}_x86"
            os_select_info="${os_type} ${os_version} x86"
            return
        fi
    done

    echo "请选择 CPU 架构"
    echo "1 : x86 (Intel/AMD)"
    echo "2 : ARM (飞腾/鲲鹏)"
    read -p "请选择: " Select
    case "$Select" in
    1)
        architecture="x86"
        os_select="${os_version}_x86"
        ;;
    2)
        architecture="arm"
        os_select="${os_version}_arm"
        ;;
    *)
        echo "选择错误！"
        display_cpu_arch
        return
        ;;
    esac

    # 使用映射表处理路径映射
    local mapped_path="${OS_PATH_MAP[$os_select]}"
    if [ -n "$mapped_path" ]; then
        os_select="$mapped_path"
    fi

    os_select_info="${os_type} ${os_version} ${architecture}"

    # 特殊处理：欧拉系统需要设置tar文件路径
    if [ "$os_type" = "欧拉" ] && [ "$architecture" = "x86" ]; then
        tar_file="one/v2/${os_select}/tar-1.34-5.oe2203.x86_64.rpm"
    fi
}

function display_base_type(){
    echo "请选择待下载的基础环境安装包类型"
    echo "1 : 仅包含一键部署脚本及配置"
    echo "2 : 包含一键部署脚本及配置，以及依赖的env和repo安装包"
    echo "3 : 已下载，不再重复下载"
    read -p "请选择: " Select
    case "$Select" in
    1|2|3)
        base_select=${Select}
        ;;
    *)
      echo "选择错误！"
      display_base_type
      ;;
    esac
}

function display_script_select(){
    echo "请选择待下载的服务类型"
    echo "0 : 安装基础软件,跳过web服务下载"
    for ((i=0; i<${#INSTALL_TYPE_ARRAY[@]}; i++)); do
        echo "$(($i+1)): ${INSTALL_TYPE_ARRAY[$i]}"
    done
    read -p "请选择: " Select
    case "$Select" in
    [0-9]|10|11)
        script_select=$Select
        if [ "$Select" == "1" ]; then
            display_web_version_select
        fi
        ;;
    *)
        echo "选择错误！"
        display_script_select
        ;;
    esac
}

function display_web_version_select(){
    echo "请选择待下载的web应用版本"
    idx=0
    for web_ver in "${WEB_VERS[@]}"; do
        let idx=idx+1
        echo "$idx : ${web_ver}"
    done
    read -p "请选择: " Select
    case "$Select" in
    [0-9]*)
        if [ $Select -gt 0 ] && [ $Select -le $idx ];then
            let s_idx=Select-1
            web_version_select=${WEB_VERS[$s_idx]}
        else
            echo "选择错误！"
            display_web_version_select
        fi
        ;;
    *)
        echo "选择错误！"
        display_web_version_select
        ;;
    esac
}

function display_web_app_select(){
    # 将参数转存到本地数组
    local arr=("$@")
    # 支持一键下载所有
    echo "请选择待下载web应用"
    echo "0 : 全部"
    idx=0
    for web_name in "${arr[@]}"
    do
      let idx=idx+1
      echo "$idx : ${web_name}"
    done
    read -p "请选择: " Select
    case "$Select" in
    0)
        web_select="all"
        ;;
    [1-9]*)
        if [ $Select -gt 0 ] && [ $Select -le $idx ];then
            let s_idx=Select-1
            # 根据最后一个-分割
            local select_array=(${arr[$s_idx]%-*})
            web_select=${select_array[0]}
        else
            echo "选择错误！"
            display_web_app_select "${arr[@]}"
        fi
        ;;
    *)
        echo "选择错误！"
        display_web_app_select "${arr[@]}"
        ;;
    esac
}

function auth(){
    echo "一键部署下载需要根据【项目管理平台】账号和密码来验证身份，验证不通过时，下载将提示【401 Unauthorized】"
    read -p "请输入账号: " user
    read -s -p "请输入密码: " password  && printf "\n"
    while true; do
       read -p "请输入项目名称: " project
       if [ -n "$project" ]; then
           # 检查项目名称是否至少有三个字符
           if [[ "$project" == "egovatest" || ${#project} -ge 3 ]]; then
               break
           else
               echo "项目名称必须至少包含三个字符，请重新输入。"
           fi
       else
           echo "项目名称不能为空，请重新输入。"
       fi
    done


}
function download(){
    if ! command -v wget &> /dev/null; then
        echo "wget命令未找到，请手动安装。"
        exit 1
    fi

    # 第一步：选择操作系统类型
    display_os_type

    # 第二步：选择基础环境类型
    display_base_type

    # 第三步：选择服务类型
    display_script_select


    echo "========================================"
    echo "下载配置汇总："
    echo "操作系统: ${os_select_info}"
    echo "基础环境: 选项${base_select}"
    if [ "$script_select" != "0" ]; then
        echo "服务类型: ${INSTALL_TYPE_ARRAY[$(($script_select - 1))]}"
        echo "版本: ${web_version_select}"
    else
        echo "服务类型: 仅安装基础软件"
    fi
    echo "下载服务器: ${domain}/one/v2"
    echo "========================================"

    read -p "确认配置无误，输入回车开始下载: " input_temp
    auth
    download_fileslist
    download_by_fileslist
    if [[ -n "${tar_file}" ]]; then
        downfile_with_auth ${domain}/${tar_file}
    fi
}
download $@

