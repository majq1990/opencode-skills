#!/bin/bash

# oneinstall-v2增量更新

. shell/include/tool_echo.sh

EARLIEST_VERSION=20221001
PACKAGE_NAME=oneinstall_v2-latest.tar.gz
EGOVA_REPO_HOME=/opt/egova/

function update_script() {
    Echo_Yellow "更新脚本..."
    upgrade_dir=temp/
    rm -rf $upgrade_dir
    mkdir $upgrade_dir
    tar xzf $PACKAGE_NAME -C $upgrade_dir
    cd $upgrade_dir/oneinstall_v2

    # 需要覆盖的目录列表(目录以/结束，文件以filename结束)
    dir_overwrite=(
        shell/
        ansible/roles/
    )
    for dir in ${dir_overwrite[@]}; do
        target_dir=../../${dir%/*}
        if ! test -d ${target_dir}; then
            echo "新增目录$d..."
            mkdir -p ${target_dir}
        fi

        if test -d $dir; then
            echo "更新目录$dir..."
            \cp -rf ${dir}* ${target_dir}
        fi
    done

    file_overwrite=(
        install.sh
        ansible/*.yml
    )
    for file in ${file_overwrite[@]}; do
        target_dir=../../
        echo "更新文件$file"
        \cp -f $file $target_dir/$file
    done

    # 更新配置文件
    echo "更新配置文件..."
    new_config="ansible/group_vars/all.yml"
    target_config="../../ansible/group_vars/all.yml"
    
    if [ -f "$new_config" ] && [ -f "$target_config" ]; then
        # 读取现有配置文件中的所有键
        existing_keys=$(grep '^[a-zA-Z_][a-zA-Z0-9_]*:' "$target_config" | cut -d':' -f1)
        
        # 处理新配置文件
        while IFS= read -r line; do
            if [[ $line =~ ^[a-zA-Z_][a-zA-Z0-9_]*: ]]; then
                key=$(echo "$line" | cut -d':' -f1)
                if ! echo "$existing_keys" | grep -q "^$key\$"; then
                    echo "添加新配置项: $key"
                    echo "$line" >> "$target_config"
                fi
            fi
        done < "$new_config"
    fi

    cd ../../
    rm -rf temp/
    Echo_Yellow "更新脚本完成"
}

function update_bin() {
    Echo_Yellow "更新二进制离线安装包..."
    tar_files=(
        oneinstall_v2-env-bin.tar.gz
    )
    for tar_file in ${tar_files[@]}; do
        if test ! -e $tar_file;then
            Echo_Red "当前目录找不到$tar_file，请确认"
            continue
        fi
        update_flag=1
        md5_file=".${tar_file%%.*}.md5"
        if test -e ${md5_file}; then
            md5sum -c $md5_file
            if [ $? == 0 ]; then
                update_flag=0
            fi
        fi
        if [ $update_flag == 1 ]; then
            echo "解压$tar_file .."
            tar xzf $tar_file -C ../
            echo "$(md5sum $tar_file)" >$md5_file
        fi
    done
}

function update_repo() {
    Echo_Yellow "更新本地yum源..."
    tar_files=(
        oneinstall_v2-env-repo.tar.gz
    )
    update_cnt=0
    for tar_file in ${tar_files[@]}; do
        if test ! -e $tar_file;then
            Echo_Red "当前目录找不到$tar_file，请确认"
            continue
        fi
        update_flag=1
        md5_file=".${tar_file%%.*}.md5"
        if test -e ${md5_file}; then
            md5sum -c $md5_file
            if [ $? == 0 ]; then
                update_flag=0
            fi
        fi
        if [ $update_flag == 1 ]; then
            echo "解压$tar_file .."
            tar xzf $tar_file -C ../
            # copy to egova_repo_home
            \cp -rf ../oneinstall_v2/src/repo $EGOVA_REPO_HOME
            echo "$(md5sum $tar_file)" >$md5_file
            let update_cnt=update_cnt+1
        fi
    done
    if [ ${update_cnt} -gt 0 ]; then
        Echo_Green "刷新yum源..."
        createrepo --update $EGOVA_REPO_HOME/repo/7
        yum clean all
    else
        Echo_Green "yum源文件无变更，无需刷新"
    fi
    Echo_Yellow "更新本地yum源完成"
}


function exec_shell() {
    Echo_Yellow "执行升级脚本..."
    # 获取当前版本号
    last_ver=$(cat .VERSION 2>/dev/null | awk -F_ '{print $1}')
    if [ "$last_ver" == "" ]; then
        last_ver=$EARLIEST_VERSION
    fi
    cd shell/upgrade/
    check=$(ls upgrade_*.sh 2>/dev/null | wc -l)
    if [ $check -gt 0 ];then
        for shell in $(ls upgrade_*.sh | awk -F[_.] '{if($2>"'${last_ver}'")print $0}' | sort); do
            Echo_Yellow "执行$shell"
            ./${shell}
            current_ver=$(echo ${shell} | awk -F[_.] '{print $2}')
            echo ${current_ver} >../../.VERSION
        done
    else
        Echo_Green "没有找到升级脚本, 无需执行升级"
    fi
    cd ../../
    Echo_Yellow "执行完成"
}


#运行入口
function run() {
    Echo_Yellow "开始更新..."
    if [ ! -e $PACKAGE_NAME ]; then
        Echo_Red "当前目录不存在$PACKAGE_NAME，请下载最新该文件"
        exit
    fi
    update_script
    update_repo
    update_bin
    exec_shell
}

run $@
