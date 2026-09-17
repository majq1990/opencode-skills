#!/bin/bash

# v14应用服务打包脚本，用于将整理的服务文件，打包成框架支持的tar.gz安装文件

# check param
if [ $# -ne 1 ];then
  echo "Usage: package_app.sh APP_NAME. Supported app_name is eUrbanMIS|statgather|faceserver"
  exit -1
fi

app_name=$1

app_name_arr=(
eUrbanMIS
eUrbanUMA
statgather
faceserver
)


# check source dir
if test ! -d ${app_name};then
  echo "Dir ${app_name} not found!"
  exit -1
fi

# prepare dirs
rm -rf ./temp/${app_name}
rm -rf ./temp/oneinstall_v2
mkdir -p temp/${app_name}/db/
mkdir -p temp/${app_name}/service/${app_name}


# copy files
if test -e ${app_name}/db;then
    cp -r ${app_name}/db temp/${app_name}/
fi
cp -r ${app_name}/* temp/${app_name}/service/${app_name}/
rm -rf ./temp/${app_name}/service/${app_name}/custom
rm -rf ./temp/${app_name}/service/${app_name}/db

# package tar files
cd temp/${app_name}
if [ -n "$(ls -A ./db)" ];then
    tar -cf ${app_name}-db.tar db
fi
cd ./service
tar -cf ${app_name}.tar ${app_name}
cd ../../../

# process custom dir
if test -d ${app_name}/custom;then
    cp -r ${app_name}/custom temp/${app_name}/
    cd temp/${app_name}/
    tar -cf ${app_name}-custom.tar custom
    cd ../..
fi


# mv tar files
mkdir -p temp/oneinstall_v2/src/web/${app_name}
cd temp
if test -e ${app_name}/${app_name}-db.tar;then
    mv ${app_name}/${app_name}-db.tar oneinstall_v2/src/web/${app_name}/
fi
mv ${app_name}/service/${app_name}.tar oneinstall_v2/src/web/${app_name}/
# process custom tar
if test -e ${app_name}/${app_name}-custom.tar;then
  mv ${app_name}/${app_name}-custom.tar oneinstall_v2/src/web/${app_name}/
fi


# package tar.gz
tar -zcf oneinstall_v2-web-${app_name}-latest.tar.gz oneinstall_v2