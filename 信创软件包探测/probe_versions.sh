#!/usr/bin/env bash
# 信创节点第三方软件版本探测 v4
# v2: Tomcat 走 catalina.jar MANIFEST / Nacos 走 jar 文件名 / 错误静默 / 补全 ES/nmap/sysbench/OnlyOffice
# v3: Tomcat 递归找 catalina.jar 覆盖嵌套 /apache-tomcat-X.Y.Z-<biz>/ 多实例 / Nacos 进 jar MANIFEST 取版本 + runtime API fallback
# v4: + OpenIM (config.yaml serverversion + 老/新分支判定 open_im_* vs openim-*) + MongoDB/etcd docker image
set +e
P(){ printf '%s=%s\n' "$1" "$2"; }
sh(){ # safe-run: 超时+静默 stderr
  timeout 8 bash -c "$1" 2>/dev/null
}

. /etc/os-release 2>/dev/null
P OS_NAME "$PRETTY_NAME"; P OS_ID "$ID"; P OS_VER "$VERSION_ID"; P ARCH "$(uname -m)"; P HOST "$(hostname)"; P KERNEL "$(uname -r)"

# JDK
J=$(java -version 2>&1 | head -1); [ -z "$J" ] && J=$(ls -d /usr/java/* 2>/dev/null | tr '\n' ';')
P JDK "$J"
# Docker
P DOCKER "$(sh 'docker --version')"
P DOCKER_COMPOSE "$(sh 'docker compose version' | head -1 || sh 'docker-compose --version')"
# MySQL Server / Client
P MYSQL_CLIENT "$(sh 'mysql --version')"
P MYSQL_SERVER "$(sh 'mysqld --version')"
# Redis
P REDIS "$(sh 'redis-server --version' || sh 'redis-cli --version')"
# PostgreSQL
PG=$(sh 'psql --version')
[ -z "$PG" ] && PG=$(sh '/egova/pgsql/bin/postgres --version')
P POSTGRESQL "$PG"
P POSTGIS_IMAGE "$(sh 'docker images --format "{{.Repository}}:{{.Tag}}"' | grep -i postgis | head -1)"
# TDengine 2
P TDENGINE2 "$(sh 'taos -V' | head -2 | tr '\n' ' ')"
# TDengine 3 docker
P TDENGINE3_DOCKER "$(sh 'docker ps -a --format {{.Image}}' | grep -i tdengine | head -1)"
# OpenResty / Nginx
NG=$(/usr/local/openresty/nginx/sbin/nginx -v 2>&1)
[ -z "$NG" ] && NG=$(sh 'nginx -v' 2>&1)
P OPENRESTY_NGINX "$NG"

# === Tomcat (v3: 递归找 catalina.jar 覆盖嵌套结构 /egova/tomcat/apache-tomcat-X.Y.Z-<biz>) ===
TC_JARS=$(find /egova/tomcat* /opt/tomcat* -maxdepth 5 -name catalina.jar 2>/dev/null)
if [ -n "$TC_JARS" ]; then
  i=0
  for J in $TC_JARS; do
    i=$((i+1))
    TC_IMPL=$(unzip -p "$J" META-INF/MANIFEST.MF 2>/dev/null | grep -i '^Implementation-Version' | head -1 | tr -d '\r' | awk -F': ' '{print $2}')
    TC_BIZ=$(echo "$J" | grep -oE 'tomcat-[A-Za-z0-9]+' | head -1)
    TC_FOLDER=$(echo "$J" | grep -oE 'apache-tomcat-[0-9.]+(-[A-Za-z0-9]+)?')
    P "TOMCAT_${i}" "${TC_IMPL} [${TC_FOLDER}] ${TC_BIZ}"
  done
else
  P TOMCAT "未安装"
fi

# === Nacos (v3: 进 jar 取 MANIFEST.MF Implementation-Version 不依赖文件名) ===
NA_JAR=$(find /egova /opt /usr/local -maxdepth 6 -name 'nacos-server*.jar' 2>/dev/null | head -1)
if [ -n "$NA_JAR" ]; then
  NA_VER=$(unzip -p "$NA_JAR" META-INF/MANIFEST.MF 2>/dev/null | grep -i '^Implementation-Version' | head -1 | tr -d '\r' | awk -F': ' '{print $2}')
  NA_SB=$(unzip -p "$NA_JAR" META-INF/MANIFEST.MF 2>/dev/null | grep -i '^Spring-Boot-Version' | head -1 | tr -d '\r' | awk -F': ' '{print $2}')
  # backup: runtime API
  [ -z "$NA_VER" ] && NA_VER=$(sh 'curl -s --max-time 3 localhost:8848/nacos/v1/console/server/state' | grep -oE '"version":"[^"]+"' | head -1 | cut -d'"' -f4)
  P NACOS_JAR "$NA_JAR"
  P NACOS_VERSION "$NA_VER"
  [ -n "$NA_SB" ] && P NACOS_SPRING_BOOT "$NA_SB"
else
  P NACOS "未安装"
fi

# Kafka (改: 取 libs 下 kafka_X.Y-Z.Z.Z.jar)
KFJ=$(ls /egova/kafka*/libs/kafka_*.jar 2>/dev/null | head -1)
[ -n "$KFJ" ] && P KAFKA "$(basename "$KFJ" | grep -oE 'kafka_[0-9.]+-[0-9.]+[A-Za-z0-9.-]*' | head -1)" || P KAFKA "未安装"

# ZooKeeper
P ZOOKEEPER "$(ls /egova/*zookeeper*/lib/zookeeper-*.jar /egova/zookeeper*/lib/zookeeper-*.jar 2>/dev/null | grep -oE 'zookeeper-[0-9.]+' | head -1)"

# MinIO
MN=$(sh '/egova/minio/minio --version' | head -1)
[ -z "$MN" ] && MN=$(sh 'minio --version' | head -1)
P MINIO "$MN"

# Cetus (改: 静默缺失)
if [ -x /usr/local/cetus/bin/cetus ]; then
  P CETUS "$(/usr/local/cetus/bin/cetus --version 2>&1 | head -1)"
else
  P CETUS "未安装"
fi

# Elasticsearch (改: 加 max-time)
ES=$(sh 'curl -s --max-time 3 localhost:9201 || curl -s --max-time 3 localhost:9200' | grep -oE '"number"\s*:\s*"[^"]+"' | head -1)
[ -z "$ES" ] && ES=$(ls -d /egova/elasticsearch* 2>/dev/null | head -1)
[ -z "$ES" ] && ES="未安装"
P ELASTICSEARCH "$ES"

# OnlyOffice (改)
P ONLYOFFICE "$(sh 'docker ps -a --format {{.Image}}' | grep -iE 'onlyoffice|documentserver' | head -1)"

# nmap / sysbench (改)
P NMAP "$(sh 'nmap --version' | head -1)"
P SYSBENCH "$(sh 'sysbench --version' | head -1)"

# Python
P PYTHON3 "$(python3 --version 2>&1)"
P PYTHON2 "$(python2 --version 2>&1)"

# 关键 rpm/deb 包版本
for pkg in mysql-community-server mysql-community-client percona-xtrabackup-80 mydumper openresty apr apr-util tomcat-native postgresql13 postgis logrotate ntp chrony lvm2 nmap sysbench; do
  V=$(rpm -q "$pkg" 2>/dev/null)
  case "$V" in
    package*|"") V=$(dpkg-query -W -f='${Package} ${Version}' "$pkg" 2>/dev/null) ;;
  esac
  [ -n "$V" ] && P "PKG_$pkg" "$V"
done

# === OpenIM (v4: 老 2.x 命名 open_im_* / 新 3.x openim-*) ===
OIM_DIR=$(find /egova /opt /usr/local -maxdepth 6 -type d \( -iname "Open-IM-Server" -o -iname "openim*" \) 2>/dev/null | head -1)
if [ -n "$OIM_DIR" ]; then
  OIM_CFG="$OIM_DIR/config/config.yaml"
  OIM_VER=$(grep -iE "^[[:space:]]*serverversion" "$OIM_CFG" 2>/dev/null | head -1 | awk -F: '{print $2}' | tr -d ' "')
  [ -z "$OIM_VER" ] && OIM_VER=$(find "$OIM_DIR" -maxdepth 3 -name "VERSION" -exec cat {} \; 2>/dev/null | head -1)
  P OPENIM_DIR "$OIM_DIR"
  P OPENIM_VERSION "$OIM_VER"
  if ls "$OIM_DIR/bin/" 2>/dev/null | grep -q "^open_im_"; then
    P OPENIM_BRANCH "2.x (open_im_* legacy)"
  elif ls "$OIM_DIR/bin/" 2>/dev/null | grep -q "^openim-"; then
    P OPENIM_BRANCH "3.x (openim-* new)"
  fi
else
  P OPENIM "未安装"
fi

# === MongoDB / etcd (v4: 从 docker images 取 OpenIM 依赖) ===
MONGO_IMG=$(sh 'docker images --format "{{.Repository}}:{{.Tag}} {{.CreatedAt}}"' | grep -iE "^mongo:" | head -1)
[ -n "$MONGO_IMG" ] && P MONGO_IMAGE "$MONGO_IMG"
ETCD_IMG=$(sh 'docker images --format "{{.Repository}}:{{.Tag}} {{.CreatedAt}}"' | grep -iE "etcd" | head -1)
[ -n "$ETCD_IMG" ] && P ETCD_IMAGE "$ETCD_IMG"

# Docker 镜像
P DOCKER_IMAGES "$(sh 'docker images --format {{.Repository}}:{{.Tag}}' | tr '\n' ',' | sed 's/,$//')"
echo "PROBE_DONE=4"
