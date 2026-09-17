#!/bin/bash

VER_NUM=1.0.1
VER=${VER_NUM}_ubuntu20
cd $(dirname $0)
ONEINSTALL_V2=oneinstall_v2
ONEKEY_INSTALL_HOME=/egova/onekey_install
# 不能覆盖的文件列表
no_overwrite_files=(
      ${ONEKEY_INSTALL_HOME}/${ONEINSTALL_V2}/ansible/group_vars/all.yml
      ${ONEKEY_INSTALL_HOME}/${ONEINSTALL_V2}/ansible/inventory/metadata.yml
      ${ONEKEY_INSTALL_HOME}/${ONEINSTALL_V2}/ansible/inventory/metadata.json
      ${ONEKEY_INSTALL_HOME}/${ONEINSTALL_V2}/ansible/inventory/hosts.yml
      ${ONEKEY_INSTALL_HOME}/${ONEINSTALL_V2}/ansible/inventory/hosts.ini
      ${ONEKEY_INSTALL_HOME}/${ONEINSTALL_V2}/ansible/inventory/multi_server.yml
      ${ONEKEY_INSTALL_HOME}/${ONEINSTALL_V2}/ansible/inventory/eurbanpro_multi_server.yml
)

# 如果非首次执行，需先备份不能覆盖的文件，如ansible的metadata.yml文件
ts=`date +%s`
for file in ${no_overwrite_files[@]}
do
  if test -e $file; then
    \cp $file ${file}.${ts}
  fi
done

PWD=$(pwd)

# 校验md5
function unarchive() {
  # 检查是否指定包，如果指定则只解压指定的包
  if [[ $# -ge 1 ]]; then
    fixed_package=$1
    if [ -e "$fixed_package" ]; then
        echo "解压$fixed_package .."
        tar xzf "$fixed_package" || { echo "解压 $fixed_package 失败"; return 1; }
        return 0
    else
        echo "指定 $fixed_package 不存在，请确认后重新运行脚本。"
        return 1
    fi
  fi

  ls oneinstall_v2*.tar.gz &>/dev/null
  if test $? -eq 0; then
    ls oneinstall_v2*.tar.gz | while read tar_file
    do
        if [ "$tar_file" == "$fixed_package" ]; then
          continue
        fi
        update_flag=1
        md5_file=".${tar_file}.md5"
        if  test -e ${md5_file} ;then
            md5sum -c  $md5_file
            if [ $? == 0 ];then
                update_flag=0
            fi
        fi
        if [ $update_flag == 1 ]; then
            echo "解压$tar_file .."
            tar xzf $tar_file
            echo "$(md5sum $tar_file)" > $md5_file
        fi
    done
  fi
}
if ! command -v tar &> /dev/null; then
    echo "tar命令未找到，请手动安装。"
    exit 1
fi
ls oneinstall_v2*.tar.gz &>/dev/null
if test $? -eq 0; then
  if ! test -d /egova; then
    unarchive oneinstall_v2-env-repo.tar.gz || exit 1
    unarchive oneinstall_v2-code_latest.tar.gz || exit 1
    echo 执行磁盘挂载
    cd ${ONEINSTALL_V2}
    bash shell/include/automount.sh || exit 1
    mkdir -p ${ONEKEY_INSTALL_HOME}
    mv ../*.tar.gz  ${ONEKEY_INSTALL_HOME}/
    if ! test -d ${ONEKEY_INSTALL_HOME}/oneinstall_v2; then
      mv  ../oneinstall_v2  ${ONEKEY_INSTALL_HOME}/
    fi
    current_dir=$(pwd)
    echo "当前目录是：${current_dir}"
  else
    mkdir -p ${ONEKEY_INSTALL_HOME}
    mv *.tar.gz  ${ONEKEY_INSTALL_HOME}
  fi
  cd ${ONEKEY_INSTALL_HOME}
  unarchive
fi
echo 解压一键安装包结束
cd ${ONEKEY_INSTALL_HOME}
# 还原已备份的不能覆盖的配置文件
for file in ${no_overwrite_files[@]}
do
  if test -e ${file}.${ts};then
    \cp ${file}.${ts} ${file}
  fi
done
cd ${ONEINSTALL_V2}
chmod +x *sh
chmod +x shell/include/*sh
chmod +x shell/tools/*sh
chmod +x shell/toolbox/security/*sh
chmod +x shell/toolbox/security/tools/*sh
chmod +x shell/toolbox/security/tools/utils/*sh

./install.sh "$@"
