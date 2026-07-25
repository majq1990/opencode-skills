#!/bin/bash
function color_text(){
    echo -e " \e[0;$2m$1\e[0m"
}
function echo_green()
{
    echo $(color_text "$1" "32")
}
function echo_red()
{
    echo $(color_text "$1" "31")
}
function echo_yellow()
{
    echo $(color_text "$1" "33")
}

function exec_tool_by_mode(){
    local tool_name=$1
    echo_yellow "模式选择: "
    echo "1: 单机模式"
    echo "2: ansible模式(请先手工配置免密，并将服务器配置添加到/etc/ansible/hosts中)"
    read -p "请选择: " select_mode
    case ${select_mode} in
    1)
        echo_green "执行命令: bash ${tool_name}.sh local"
        cd tools/
        bash ${tool_name}.sh local
        cd ../
        ;;
    2)
        set +e
        which ansible 2>/dev/null 1>/dev/null
        if [ $? -gt 0 ];then
            echo_red "未找到ansible命令！"
            exit 1
        fi
        let host_count=$(ansible all --list-hosts 2>/dev/null |wc -l)-1
        if [ ${host_count} -eq 0 ];then
            echo_red "从/etc/ansible/hosts中未检测到任何服务器！"
            exit 1
        fi
        echo_yellow "检查服务器免密连通性..."
        ansible all -m ping
        if [ $? -gt 0 ];then
            echo_red "存在无法免密的服务器,请先手工配置免密"
            exit 1
        fi
        echo_green "执行命令: bash ${tool_name}.sh ansible"
        set -e
        cd tools
        bash ${tool_name}.sh ansible
        cd ../
      ;;
    *)
        echo "选择错误！"
        exec_tool_by_mode ${tool_name}
    esac
}
function exec_tool(){
    local tool_name=$1
    source tools/${tool_name}.sh
    if [ $(support_multi_mode) -eq 1 ];then
        exec_tool_by_mode ${tool_name}
    else
        cd tools
        bash ${tool_name}.sh local
        cd ../
    fi
}
function display_tools()
{
    local tool_file=$1
    if [ "$tool_file" == "" ];then
        tool_file="tools/list.yaml"
    fi
    echo "安全加固工具箱(攻防演练版)："
    local sh_tools=()
    local tool_index=0
    while read line
    do
#        local script=$(echo $line |awk -F: '{print $1}')
        temp_line=$(echo $line | grep -v "^#" |grep ":"|awk -F: '{print $1" "$2}')
        if [ "$temp_line" == "" ];then
            continue
        fi
        local info=($temp_line)
        if ! test -f tools/${info[0]}.sh; then
            continue
        fi
        sh_tools[$tool_index]=${info[0]}
        let tool_index=tool_index+1
        local pre_str=""
        if [ $tool_index -lt 10 ];then
            pre_str=" "
        fi
        echo "$pre_str$tool_index : ${info[*]:1}"
    done < $tool_file
    echo "q: 退出工具箱"

    read -p "请选择：" tool_select
    case "${tool_select}" in
    [0-9]*)
		if [ $tool_select -gt 0 ] && [ $tool_select -le $tool_index ];then
			local sh_tool=${sh_tools[(($tool_select-1))]}
			if [ "$sh_tool" == "" ] || [ ! -e tools/${sh_tool}.sh ];then
				echo "不存在的工具 tools/${sh_tool}.sh"
			else
				exec_tool ${sh_tool}
				echo "执行完成！"
				display_tools ${tool_file}
			fi
		else
			echo "选择错误！"
			display_tools ${tool_file}
		fi
		;;
    q)
        return 0
        ;;
    *)
        echo "选择错误！"
        display_tools ${tool_file}
        ;;
    esac
}

display_tools $@