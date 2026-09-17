#!/bin/bash
#
#  使用createrepo在Ansible主控节点创建本地yum源，并通过nginx将本地yum源代理出去，受控节点可以通过配置代理，使用主控节点的yum源。
#  本脚本可以执行多次，但每次需要更换端口号。
#
. ../include/tool_echo.sh
. ./check_repo.sh
EGOVA_REPO_HOME=$1

#复制离线repo包
if test -d $EGOVA_REPO_HOME; then
    rm -rf $EGOVA_REPO_HOME/*
fi
mkdir -p $EGOVA_REPO_HOME
\cp -rf ../../src/repo/* $EGOVA_REPO_HOME/
Echo_Green "获取redhat版本"
. tool_utils.sh
release_info=$(get_distribution_info)
release_name=$(echo "${release_info}"|awk -F"_" '{print $1}')
release_ver=$(echo "${release_info}"|awk -F"_" '{print $2}')
echo "获取到的版本为: ${release_ver}"
if ! get_distribution_info; then
    Echo_Red "获取发行版本失败,请检查操作系统版本 /etc/os-release"
    exit 1
fi
Echo_Green "安装createrepo"

# 本地yum源需要的rpm打成tar包，解压到/egova/devops/oneops/src/repo/7目录下
if  ! test -d $EGOVA_REPO_HOME/${release_name}/${release_ver}/ && ! is_centos ; then
    Echo_Red "请下载${release_info}版本的rpm包,并上传到$EGOVA_REPO_HOME/${release_name}/${release_ver}/"
    exit 1
elif  ! test -d $EGOVA_REPO_HOME/${release_ver}/ && is_centos ; then
      Echo_Red "请下载centos${release_ver}版本的rpm包,并上传到$EGOVA_REPO_HOME/${release_ver}/"
      exit 1
fi

echo "备份原有yum源至/etc/yum.repos.d/bak (如可联网，可按需还原)"
mkdir -p /etc/yum.repos.d/bak
find /etc/yum.repos.d/ -maxdepth 1 -name "*.repo" |xargs -I {} mv {} /etc/yum.repos.d/bak/

# 生成本地repo文件
\cp -f ../template/egova-oneinstall-local.repo /etc/yum.repos.d/egova-oneinstall-local.repo
if ! is_centos ; then
  sed -i "s|baseurl=.*|baseurl=file://${EGOVA_REPO_HOME}/${release_name}/${release_ver}|g" /etc/yum.repos.d/egova-oneinstall-local.repo
elif is_centos; then
  sed -i "s|baseurl=.*|baseurl=file://${EGOVA_REPO_HOME}/${release_ver}|g" /etc/yum.repos.d/egova-oneinstall-local.repo
fi


Echo_Yellow "安装createrepo..."
if ! is_centos ; then
    rpm -ivh $EGOVA_REPO_HOME/${release_name}/${release_ver}/openssl-devel-*.rpm --nodeps
    rpm -ivh $EGOVA_REPO_HOME/${release_name}/${release_ver}/createrepo_c-*.rpm --nodeps
    rpm -ivh $EGOVA_REPO_HOME/${release_name}/${release_ver}/drpm-*.rpm --nodeps
else
   rpm -ivh $EGOVA_REPO_HOME/${release_ver}/python-deltarpm-*.rpm --nodeps
   rpm -ivh $EGOVA_REPO_HOME/${release_ver}/createrepo-*.rpm --nodeps
fi

if test -d $EGOVA_REPO_HOME/6/; then
    createrepo $EGOVA_REPO_HOME/6
fi

if test -d $EGOVA_REPO_HOME/7/; then
    createrepo $EGOVA_REPO_HOME/7
fi

if test -d $EGOVA_REPO_HOME/8/; then
    createrepo $EGOVA_REPO_HOME/8
fi

if [[ -d "$EGOVA_REPO_HOME/${release_name}/${release_ver}" ]] && [[ "${release_info}" =~ (uos_20_arm|uos_20_x86|anolis_8_arm) ]]; then
    rpm -ivh $EGOVA_REPO_HOME/${release_name}/${release_ver}/python3-createrepo_c-*.rpm --nodeps
    rpm -ivh $EGOVA_REPO_HOME/${release_name}/${release_ver}/python3-libmodulemd-*.rpm --nodeps
    rpm -ivh $EGOVA_REPO_HOME/${release_name}/${release_ver}/modulemd-tools-*.rpm --nodeps
    cd $EGOVA_REPO_HOME/${release_name}/${release_ver}
    createrepo .
    repo2module .
    createrepo_mod .
    cd -
elif [[ -d "$EGOVA_REPO_HOME/${release_name}/${release_ver}" ]] && [[ "${release_info}" =~ (anolis_8_arm) ]]; then
    rpm -ivh $EGOVA_REPO_HOME/${release_name}/${release_ver}/python3-createrepo_c-*.rpm --nodeps
    rpm -ivh $EGOVA_REPO_HOME/${release_name}/${release_ver}/python3-libmodulemd-*.rpm --nodeps
    rpm -ivh $EGOVA_REPO_HOME/${release_name}/${release_ver}/modulemd-tools-*.rpm --nodeps
    cd $EGOVA_REPO_HOME/${release_name}/${release_ver}
    createrepo_c .
    repo2module -s stable ./
    modifyrepo_c --mdtype=modules modules.yaml repodata/
elif [[ -d "$EGOVA_REPO_HOME/${release_name}/${release_ver}" ]] ; then
   createrepo $EGOVA_REPO_HOME/${release_name}/${release_ver}
fi
yum clean all
yum makecache
if ! is_centos; then
chmod 755 -R $EGOVA_REPO_HOME/${release_name}/$release_ver
else
  chmod 755 -R $EGOVA_REPO_HOME/$release_ver
fi
chmod o+x /egova/opt/
Echo_Yellow "----开始依赖检查----------"
check_dependencies
Echo_Green "----所有依赖均通过检查，开始构建本地源------------"
if  is_anolis ; then
   yum install -y glibc-locale-source glibc-langpack-zh
fi
# 安装基础软件工具
which netstat &>/dev/null
if test $? -ne 0; then
  yum install -y net-tools
fi
if  ! command -v hostname &> /dev/null ; then
    echo "hostname 命令不存在,开始自动安装..."
    yum install -y hostname
fi
if  ! command -v iptables &> /dev/null ; then
    echo "iptables 命令不存在,开始自动安装..."
    yum install -y iptables
fi
which openresty &>/dev/null
if test $? -ne 0; then
    Echo_Yellow "安装openresty..."
    yum install -y openresty
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
    ln -sf /usr/local/openresty/nginx/conf/nginx.conf /etc/nginx/nginx.conf
    ln -sf  /usr/lib/systemd/system/openresty.service /usr/lib/systemd/system/nginx.service
    ln -sf  /usr/local/openresty/nginx/sbin/nginx /usr/sbin/nginx
    /usr/local/openresty/nginx/sbin/nginx -t
    systemctl daemon-reload
    systemctl start openresty
    systemctl enable openresty
fi

if test -e /etc/nginx/conf.d/egova-oneinstall-local-repo-nginx.conf; then
     rm -rf /etc/nginx/conf.d/egova-oneinstall-local-repo-nginx.conf
     systemctl restart nginx
fi
while [ "$EGOVA_YUM_PORT" == "" ] || [ "$PORT_USED" != "0" ]; do
    Echo_Yellow "请配置yum源端口（建议配置7777）"
    read -p "输入: " EGOVA_YUM_PORT
    PORT_USED=$(netstat -anop | grep ":$EGOVA_YUM_PORT" | grep -i listen | wc -l)
    if [ $PORT_USED -gt 0 ]; then
        echo "$EGOVA_YUM_PORT 已在使用，请更换其他端口"
    fi
done

if ! test -e /etc/nginx/conf.d/default.conf;then
    \cp -f ../template/default.conf /etc/nginx/conf.d/
fi
echo "端口是：$EGOVA_YUM_PORT"
\cp -f ../template/egova-oneinstall-local-repo-nginx.conf /etc/nginx/conf.d/egova-oneinstall-local-repo-nginx.conf
\cp -f ../template/egova-oneinstall-local.repo /etc/yum.repos.d/egova-oneinstall-local.repo
sed -i "s#EGOVA_REPO_HOME#$EGOVA_REPO_HOME#g" /etc/nginx/conf.d/egova-oneinstall-local-repo-nginx.conf
sed -i "s/EGOVA_LOCAL_PORT/$EGOVA_YUM_PORT/g" /etc/nginx/conf.d/egova-oneinstall-local-repo-nginx.conf
sed -i "s/EGOVA_LOCAL_PORT/$EGOVA_YUM_PORT/g" /etc/yum.repos.d/egova-oneinstall-local.repo

if ! is_centos; then
sed -i "s|RELEASE_VER|${release_name}/${release_ver}|g" /etc/yum.repos.d/egova-oneinstall-local.repo
else
  sed -i "s/RELEASE_VER/${release_ver}/g" /etc/yum.repos.d/egova-oneinstall-local.repo
fi
# 保存端口到全局配置
sed -i "s/^egova_local_port:.*$/egova_local_port: $EGOVA_YUM_PORT/" ../../ansible/group_vars/all.yml

if   command -v hostname &> /dev/null ; then
     local_ip=$(hostname -I | awk '{print $1}')
     sed -i "s|127.0.0.1|${local_ip}|g" /etc/yum.repos.d/egova-oneinstall-local.repo
fi

if ! command -v iptables &> /dev/null; then
        echo "iptables 安装失败，退出脚本。"
        exit 1
fi
#防火墙开放yum源端口  需在nginx restart前开放端口
which firewall-cmd
if [ "$?" == "0" ]; then
    firewall-cmd --permanent --add-port=${EGOVA_YUM_PORT}/tcp
    firewall-cmd --reload
else
    iptables -I INPUT -p tcp --dport ${EGOVA_YUM_PORT} -j ACCEPT
fi
setenforce 0

systemctl restart nginx

Echo_Green "构建本地源构建结束，查看本机repo是否生效，请执行yum update 无报错则本地源构建成功"

yum repolist --disablerepo="*" --enablerepo="egova-local"
