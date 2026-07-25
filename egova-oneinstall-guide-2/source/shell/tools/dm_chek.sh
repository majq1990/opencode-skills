#!/bin/bash

# 配置数据库连接信息
DB_HOST="localhost"  # 数据库主机地址
DB_PORT="5236"       # 达梦数据库默认端口
DB_USER="SYSDBA"   # 数据库用户名
DB_PASSWORD="SYSDBA" # 数据库密码

PROCESS_INFO=$(ps -ef | grep 'dmserver' | grep -v grep)
DMSERVER_PATH=$(echo "$PROCESS_INFO" | awk '{print $(NF-2)}' | head -1)
DISQL_CMD="./disql SYSDBA/SYSDBA -E"


if [ -z "$DMSERVER_PATH" ]; then
    echo "未找到 dmserver 进程，请到安装达梦服务器上执行脚本"
    exit 1
else
    DMSERVER_DIR=$(dirname "$DMSERVER_PATH")
    echo "dmserver 路径: $DMSERVER_DIR"
fi

function check_dm_awr() {
    cd "$DMSERVER_DIR"
    # 要执行的SQL语句
    INIT_AWR_SQL="sp_init_awr_sys(1);"
    CLEAN_AWR_SQL="CALL DBMS_WORKLOAD_REPOSITORY.MODIFY_SNAPSHOT_SETTINGS(10080,60);"
    DISQL_CMD="./disql SYSDBA/SYSDBA -E 'SELECT SF_CHECK_AWR_SYS;'"

    val=$(eval "$DISQL_CMD" 2>&1 | awk '
        BEGIN { found = 0 }
        /^SF_CHECK_AWR_SYS/ { found = 1 }
        found && /^[0-9]+$/ { print $1; exit }
    ')
    if [ $val -gt 0  ]; then
        echo "awr配置已开启"
        exit 0
    fi

    # 开启awr配置
    echo "$INIT_AWR_SQL" | ./disql $DB_USER/$DB_PASSWORD@$DB_HOST:$DB_PORT 2>&1
    echo "$CLEAN_AWR_SQL" | ./disql $DB_USER/$DB_PASSWORD@$DB_HOST:$DB_PORT 2>&1
}
# 清理一周前的awr 数据
function clean_awr_data() {

    SQL_COMMANDS=(
        "call SP_CREATE_JOB('定期清理AWR',1,0,'',0,0,'',0,'定期清理一周前的awr');"
        "call SP_JOB_CONFIG_START('定期清理AWR');"
        "call SP_ADD_JOB_STEP('定期清理AWR', '删除7天前的快照', 0, 'BEGIN DBMS_WORKLOAD_REPOSITORY.DROP_SNAPSHOT_BY_TIME(SYSDATE-7, TRUE); END;', 0, 0, 0, 0, NULL, 0);"
        "call SP_ADD_JOB_SCHEDULE('定期清理AWR', '清理一周前的awr', 1, 1, 1, 0, 0, '23:40:50', NULL, SYSDATE, NULL, '');"
        "call SP_JOB_CONFIG_COMMIT('定期清理AWR');"
    )

# 循环执行 SQL 命令
for SQL_COMMAND in "${SQL_COMMANDS[@]}"
    do
        echo "执行SQL 命令: $SQL_COMMAND"
        echo "$DISQL_CMD '$SQL_COMMAND'" | ./disql $DB_USER/$DB_PASSWORD@$DB_HOST:$DB_PORT 2>&1
        echo "SQL 命令执行完成"
        echo "---------------------------------"
    done
    echo "所有 SQL 命令执行完成"
}
check_dm_awr
clean_awr_data