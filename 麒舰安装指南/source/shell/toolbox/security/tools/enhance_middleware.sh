#!/bin/bash

# 配置文件路径
APUSIC_CONFIG_FILE="apusic.conf"
LOG_CONFIG_FILE="logging.xml"
# 新的MaxSpareThreads和MaxThreads值
MUX_MAX_SPARE_THREADS=200
HTTP_MAX_SPARE_THREADS=500
NEW_BACKLOG=100
NEW_MAX_SESSIONS_IN_CACHE=102400
NEW_SESSION_INVALIDATE_CHECK_INTERVAL=6000
NEW_SERVLET_RELOAD_CHECK_INTERVAL=-1

DOMAIN_XML="/egova/AAS-V9.0/domains/mydomain/config/domain.xml"
STARTAPUSIC="/egova/AAS-V9.0/domains/mydomain/bin/startapusic"
DONGWEB_JVM_FILE="/egova/TongWeb7.0.4.9"

function get_domain_home() {
    DOMAIN_HOME=$(ps -ef | grep apusic | grep -m 1 -oP '(?<=-Dcom.apusic.domain.home=)[^ ]+')

    if [ -z "$DOMAIN_HOME" ]; then
        echo "未找到-Dcom.apusic.domain.home的目录路径。"
    else
        echo "提取的目录路径为: $DOMAIN_HOME"
        STARTAPUSIC="$DOMAIN_HOME/bin/startapusic"
        DOMAIN_XML="$DOMAIN_HOME/config/domain.xml"
        APUSIC_CONFIG_FILE="$DOMAIN_HOME/config/apusic.conf"
        LOG_CONFIG_FILE="$DOMAIN_HOME/config/logging.xml"
    fi
    echo "apusic.conf 路径为: $APUSIC_CONFIG_FILE"
}

function get_dongweb_home() {
    DONGWEB_HOME=$(ps -ef | grep ton | grep -m 1 -oP '(?<=-Dtongweb.home=)[^ ]+')

    if [ -z "$DONGWEB_HOME" ]; then
        echo "未找到-Dtongweb.home的目录路径。"
    else
        echo "提取的目录路径为: $DONGWEB_HOME"
        DONGWEB_JVM_FILE="$DONGWEB_HOME/bin/external.vmoptions"
    fi
    echo "external.vmoptions 路径为: $DONGWEB_JVM_FILE"
}

# 选择加固的中间件
function select_middleware() {
    echo "请选择要加固的中间件："
    echo "1. 东方通"
    echo "2. 金蝶(适合AAS V9版本)"
    read -p "输入选择的数字: " middleware_choice

    case $middleware_choice in
        1)
            echo "-------------------开始东方通配置文件调整-------------------"
            get_dongweb_home
            update_dongweb_config
            ;;
        2)
            echo "------------------开始金蝶配置文件调整-------------------"
            get_domain_home
            bakup_config
            update_apusic_config
            ;;
        *)
            echo "无效的选择，退出脚本。"
            exit 1
            ;;
    esac
}

function bakup_config(){
    if [ -f "$DOMAIN_XML" ]; then
        echo "domain.xml 文件存在，替换 -Xmx1024m 为 -Xmx6G"
        sed -i 's/-Xmx1024m/-Xmx6G/g' "$DOMAIN_XML"
    else
        echo "domain.xml 文件不存在，备份 startapusic 文件并替换 MEMORY_JVMOPTS"
        # 备份文件
        cp "$STARTAPUSIC" /root
        echo "已备份 startapusic 文件为 /root/startapusic"

        # 替换 MEMORY_JVMOPTS
        sed -i 's/MEMORY_JVMOPTS="-Xms512m -Xmx8092m"/MEMORY_JVMOPTS="-Xms3G -Xmx6G -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=\/egova\/log"/g' "$STARTAPUSIC"
        echo "已替换 MEMORY_JVMOPTS 为 -Xms3G -Xmx6G -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/egova/log"
    fi
}
# 更新金蝶配置文件
function update_apusic_config() {
    sed -i "
    /NAME=\"apusic:service=ThreadPool,name=MuxHandler\"/,/<\/SERVICE>/ {
        s/MaxSpareThreads\" VALUE=\"[0-9]*\"/MaxSpareThreads\" VALUE=\"$MUX_MAX_SPARE_THREADS\"/g
        s/MaxThreads\" VALUE=\"[0-9]*\"/MaxThreads\" VALUE=\"$MUX_MAX_SPARE_THREADS\"/g
    }
    /NAME=\"apusic:service=ThreadPool,name=HTTPHandler\"/,/<\/SERVICE>/ {
        s/MaxSpareThreads\" VALUE=\"[0-9]*\"/MaxSpareThreads\" VALUE=\"$HTTP_MAX_SPARE_THREADS\"/g
        s/MaxThreads\" VALUE=\"[0-9]*\"/MaxThreads\" VALUE=\"$HTTP_MAX_SPARE_THREADS\"/g
    }
    "  $APUSIC_CONFIG_FILE

    sed -i "s/Backlog\" VALUE=\"[0-9]*\"/Backlog\" VALUE=\"$NEW_BACKLOG\"/g" $APUSIC_CONFIG_FILE
    sed -i "s/MaxSessionsInCache\" VALUE=\"[0-9]*\"/MaxSessionsInCache\" VALUE=\"$NEW_MAX_SESSIONS_IN_CACHE\"/g" $APUSIC_CONFIG_FILE
    sed -i "s/SessionInvalidateCheckInterval\" VALUE=\"[0-9]*\"/SessionInvalidateCheckInterval\" VALUE=\"$NEW_SESSION_INVALIDATE_CHECK_INTERVAL\"/g" $APUSIC_CONFIG_FILE
    sed -i "s/ServletReloadCheckInterval\" VALUE=\"[0-9]*\"/ServletReloadCheckInterval\" VALUE=\"$NEW_SERVLET_RELOAD_CHECK_INTERVAL\"/g" $APUSIC_CONFIG_FILE
    sed -i 's/<ATTRIBUTE NAME="EnableLog" VALUE="False"\/>/<ATTRIBUTE NAME="EnableLog" VALUE="True"\/>/g' $APUSIC_CONFIG_FILE

    if ! grep -q 'DateFileHandler' "$APUSIC_CONFIG_FILE"; then
         echo "======增加日志切割配置======"
         sed -i  '/<ATTRIBUTE NAME="LogFileCount" VALUE="10"\/>/a\ \ \ \ \<ATTRIBUTE NAME="LogHandler" VALUE="com.apusic.logging.DateFileHandler"/>' "$APUSIC_CONFIG_FILE"
    fi


    ##替换日志文件
    echo "======INFO日志改成ERROR======I"
    sed -i "s/INFO/EERROR/g"  $LOG_CONFIG_FILE
    echo "-------------------配置文件已更新。请手动重启服务！--------------------"
}
function update_dongweb_config(){
    if [ ! -f "$DONGWEB_JVM_FILE" ]; then
        echo "配置文件 $DONGWEB_JVM_FILE 不存在"
        exit 1
    fi
     echo "======修改JVM参数======"
     if grep -q '^-Xms3G$' "$DONGWEB_JVM_FILE" && grep -q '^-Xmx6G$' "$DONGWEB_JVM_FILE"; then
         echo "配置文件已包含新的参数值，无需替换"
     fi
     sed -i '/^-Xms/c\-Xms3G' "$DONGWEB_JVM_FILE"
     sed -i '/^-Xmx/c\-Xmx6G' "$DONGWEB_JVM_FILE"
     if grep -q 'HeapDumpOnOutOfMemoryError' "$DONGWEB_JVM_FILE" ; then
         echo "配置文件已包含新的参数值，无需替换"
         exit 0
     fi
    echo "-XX:+HeapDumpOnOutOfMemoryError" >> "$DONGWEB_JVM_FILE"
    echo "-XX:HeapDumpPath=${DONGWEB_HOME}/logs" >> "$DONGWEB_JVM_FILE"
    echo "-------------------配置文件已更新。请手动重启服务！--------------------"
}
function run() {
   select_middleware
}

run