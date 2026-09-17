#!/bin/bash

SCRIPT_DIR="/egova/onekey_install/oneinstall_v2/src/bin/jdk"
JDK_TARBALL="jdk-8u421-linux.tar.gz"
JDK_VERSION="1.8.0_421"
# 检查是否已安装,防止只存在软链接
if command -v java >/dev/null 2>&1; then
  if java -version >/dev/null 2>&1; then
    echo "Java 已安装，跳过安装"
    exit 0
  fi
fi

JDK_SRC="${SCRIPT_DIR}/${JDK_TARBALL}"
JAVA_HOME_DIR="/usr/java/jdk${JDK_VERSION}"

if [ ! -f "${JDK_SRC}" ]; then
  echo "错误：JDK 安装包不存在: ${JDK_SRC}"
  exit 1
fi

mkdir -p "${JAVA_HOME_DIR}"

echo "正在解压 JDK..."
tar -xzf "${JDK_SRC}" -C "${JAVA_HOME_DIR}" --strip-components=1

echo "配置 root 环境变量..."
if ! grep -q '^export JAVA_HOME=' /root/.bashrc 2>/dev/null; then
  cat >> /root/.bashrc <<EOF
# BEGIN ANSIBLE MANAGED BLOCK JAVA_HOME
export JAVA_HOME=${JAVA_HOME_DIR}
export PATH=\$PATH:\$JAVA_HOME/bin
# END ANSIBLE MANAGED BLOCK JAVA_HOME
EOF
fi

ln -sf "${JAVA_HOME_DIR}/bin/java" /usr/bin/java

source /root/.bashrc
echo "JDK ${JDK_VERSION} 安装完成"
