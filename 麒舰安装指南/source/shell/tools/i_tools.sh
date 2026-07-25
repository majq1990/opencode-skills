#!/bin/bash --login
. ./tool_utils.sh

if is_ubuntu; then
  apt install -y unzip
else
  yum install -y unzip
fi
if  ! command -v unzip &> /dev/null ; then
    echo "unzip 命令不存在"
    exit 1
fi
#arthas
if ! test -d /egova/tools/arthas; then
  mkdir -p /egova/tools/arthas
  unzip ../../src/bin/tools/arthas-3.2.0-bin.zip -d /egova/tools/arthas
fi
##弱密码检测工具
if ! test -d /egova/tools/weakPwd_Check; then
  mkdir -p /egova/tools/weakPwd_Check/
  tar -xvf  ../../src/bin/tools/weakPwd_Check.tar.gz -C /egova/tools/weakPwd_Check
fi

## 安全检测工具
if ! test -d /egova/tools/security; then
  mkdir -p /egova/tools/security/
  tar -xvf  ../../src/bin/tools/egova-security-toolbox.tar.gz -C /egova/tools/security --strip-components=1
fi

##性能分析脚本
if ! test -d /egova/tools/script; then
  mkdir -p /egova/tools/script/
  cp -r ../../src/bin/tools/script  /egova/tools/
fi
echo "install tools ok"
