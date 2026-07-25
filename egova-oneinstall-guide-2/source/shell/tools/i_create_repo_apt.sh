#!/bin/bash
#
#  使用createrepo在Ansible主控节点创建本地apt源，并通过nginx将本地apt源代理出去，受控节点可以通过配置代理，使用主控节点的apt源。
#  本脚本可以执行多次，但每次需要更换端口号。
#
. ../include/tool_echo.sh
. ./check_repo.sh
EGOVA_REPO_HOME=$1

Echo_Green "获取ubuntu版本"
release_ver=$(lsb_release -rs | cut -d. -f1)
echo "获取到的版本为: ${release_ver}"

#复制离线repo包
if test -d $EGOVA_REPO_HOME; then
    rm -rf "${EGOVA_REPO_HOME:?}"/*
fi

mkdir -p $EGOVA_REPO_HOME/$release_ver
\cp -rf ../../src/repo/* $EGOVA_REPO_HOME/$release_ver

if ! test -d $EGOVA_REPO_HOME/${release_ver}/; then
    Echo_Red "请下载ubuntu${release_ver}版本的deb包,并上传到$EGOVA_REPO_HOME/${release_ver}/"
    exit 1
fi
#先备份本地源
if test ! -e /etc/apt/sources.listbak ; then
    \cp -f /etc/apt/sources.list /etc/apt/sources.listbak
fi
# 生成本地repo文件
\cp -f ../template/egova-oneinstall-local.list /etc/apt/sources.list
sed -i 's#http://127.0.0.1:EGOVA_LOCAL_PORT/repo/RELEASE_VER/#file:///'${EGOVA_REPO_HOME}'/'${release_ver}'/#' /etc/apt/sources.list
# 安装基础软件工具
sudo dpkg  -i $EGOVA_REPO_HOME/${release_ver}/unzip*
sudo dpkg  -i $EGOVA_REPO_HOME/${release_ver}/net-tools*
##安装dpkg
sudo dpkg  -i $EGOVA_REPO_HOME/${release_ver}/libdpkg-perl_*
sudo dpkg  -i $EGOVA_REPO_HOME/${release_ver}/man-db_*
sudo dpkg  -i $EGOVA_REPO_HOME/${release_ver}/binutils-common_*
sudo dpkg  -i $EGOVA_REPO_HOME/${release_ver}/libbinutils_*
sudo dpkg  -i $EGOVA_REPO_HOME/${release_ver}/libctf-nobfd0_*
sudo dpkg  -i $EGOVA_REPO_HOME/${release_ver}/libctf0_*
sudo dpkg  -i $EGOVA_REPO_HOME/${release_ver}/binutils-x86-64-linux-gnu_*
sudo dpkg  -i $EGOVA_REPO_HOME/${release_ver}/binutils_*
sudo dpkg  -i $EGOVA_REPO_HOME/${release_ver}/dpkg-dev_*

cd "$EGOVA_REPO_HOME"/$release_ver
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz
cd -
apt update
Echo_Yellow "----开始依赖检查----------"
check_dependencies
Echo_Green "----所有依赖均通过检查，开始构建本地源------------"
# 安装基础软件工具


which nginx &>/dev/null
if test $? -ne 0; then
    Echo_Yellow "安装nginx..."
    #先安装依赖,通过源安装存在问题，先暂时通过deb包安装
    tar -xvf ../../src/bin/openresty/openresty.tar.gz -C /usr/local/

    # 使用相对路径
    sudo -u#0 \cp -f ../template/openresty_nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
    sudo -u#0 \cp -f ../template/openresty.service /usr/lib/systemd/system/openresty.service
    sudo -u#0 mkdir -p /etc/nginx/conf.d
    sudo -u#0 mkdir -p /egova/log/nginx
    grep nginx /etc/passwd &>/dev/null
    if test $? -ne 0; then
        sudo -u#0 chattr -i /etc/gshadow
        sudo -u#0 chattr -i /etc/group
        sudo -u#0 chattr -i /etc/shadow
        sudo -u#0 chattr -i /etc/passwd
        groupadd nginx
        useradd -M -s /sbin/nologin -g nginx nginx
    fi
    chown -R nginx:nginx /egova/log/nginx
    ln -s /usr/local/openresty/nginx/conf/nginx.conf /etc/nginx/nginx.conf
    ln -s /usr/lib/systemd/system/openresty.service /usr/lib/systemd/system/nginx.service
    ln -s /usr/local/openresty/nginx/sbin/nginx /usr/sbin/nginx
    /usr/local/openresty/nginx/sbin/nginx -t
    systemctl daemon-reload
    systemctl start openresty
    systemctl enable openresty
fi


if test -e /etc/nginx/conf.d/egova-oneinstall-local-repo-nginx.conf; then
    rm -rf /etc/nginx/conf.d/egova-oneinstall-local-repo-nginx.conf
    systemctl restart nginx
fi
while [ "$EGOVA_APT_PORT" == "" ] || [ "$PORT_USED" != "0" ]; do
    Echo_Yellow "请配置apt源端口（建议配置7777）"
    read -p "输入: " EGOVA_APT_PORT
    PORT_USED=$(netstat -anop | grep ":$EGOVA_APT_PORT" | grep -i listen | wc -l)
    if [ $PORT_USED -gt 0 ]; then
        echo "$EGOVA_APT_PORT 已在使用，请更换其他端口"
    fi
done

if ! test -e /etc/nginx/conf.d/default.conf;then
    \cp -f ../template/default.conf /etc/nginx/conf.d/
fi
\cp -f ../template/egova-oneinstall-local.list /etc/apt/sources.list
\cp -f ../template/egova-oneinstall-local-repo-nginx.conf /etc/nginx/conf.d/egova-oneinstall-local-repo-nginx.conf
sed -i "s#EGOVA_REPO_HOME#$EGOVA_REPO_HOME#g" /etc/nginx/conf.d/egova-oneinstall-local-repo-nginx.conf
sed -i "s/EGOVA_LOCAL_PORT/$EGOVA_APT_PORT/g" /etc/nginx/conf.d/egova-oneinstall-local-repo-nginx.conf
sed -i "s/EGOVA_LOCAL_PORT/$EGOVA_APT_PORT/g" /etc/apt/sources.list
sed -i "s/RELEASE_VER/${release_ver}/g" /etc/apt/sources.list
# 保存端口到全局配置
sed -i "s/^egova_local_port:.*$/egova_local_port: $EGOVA_APT_PORT/" ../../ansible/group_vars/all.yml
if  command -v hostname &> /dev/null ; then
    local_ip=$(hostname -I | awk '{print $1}')
    sed -i "s|127.0.0.1|${local_ip}|g" /etc/apt/sources.list
fi
#防火墙开放apt源端口  需在nginx restart前开放端口
which ufw
if [ "$?" == "0" ]; then
    ufw allow ${EGOVA_APT_PORT}/tcp
    ufw reload
else
    iptables -I INPUT -p tcp --dport ${EGOVA_APT_PORT} -j ACCEPT
fi
systemctl stop apparmor
systemctl restart nginx
# cd "$EGOVA_REPO_HOME"/$release_ver
file_attr=$(lsattr -d "/etc/group" 2>/dev/null)
if [[ $file_attr == *i* ]]; then
      sudo -u#0 chattr -i /etc/gshadow
      sudo -u#0 chattr -i /etc/group
      sudo -u#0 chattr -i /etc/shadow
      sudo -u#0 chattr -i /etc/passwd
fi
# dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz
# 删除已下载的包并清理缓存
apt clean all
apt update
# 修复软件包依赖关系
apt --fix-broken -y install
###升级低版本包
apt upgrade -y
apt autoremove
Echo_Green "----构建本地源构建结束，查看本机repo是否生效，请执行apt update 无报错则本地源构建成功------------"