#!/bin/bash
set -e

# 工具中包含 MySQL，达梦，人大金仓，PG驱动
# 若使用其他数据库，则使用 DATASOURCE_URL，DATASOURCE_DRIVER，DATASOURCE_USERNAME，DATASOURCE_PASSWORD
# 例如达梦:
# --DATASOURCE_URL=jdbc:dm://192.168.101.18:5235?clobAsString=true 
# --DATASOURCE_USERNAME=SYSDBA 
# --DATASOURCE_PASSWORD=SYSDBA 
# --DATASOURCE_DRIVER=dm.jdbc.driver.DmDriver 
# 
# 其他参数说明：
# BUFFER_SIZE：任务执行队列（从主线程分发到各个执行现场的队列）长度，默认是100，一般无需调整
# CORE_TASK_NUM：执行线程数，建议调整为CPU核心数-2，默认5
# MAX_FETCH_SIZE：每次从数据库中查询的人员数据行数，默认100
# CHECK_FILE：弱密码字典位置，使用绝对路径，文件中每行一个弱密码
CUR_DIR=$(dirname "$0")

nohup java -jar /egova/weakPwd_Check/egova-weak-pass-check-tool.jar \
--DATASOURCE_URL=jdbc:DB_TYPE://DB_HOST:DB_PORT/DB_NAME \
--DATASOURCE_USERNAME=DB_USER \
--DATASOURCE_PASSWORD=DB_PASSWORD \
--DATASOURCE_DRIVER=DB_DRIVER \
--MYSQL_URL=DB_HOST:DB_PORT/DB_NAME \
--MYSQL_USERNAME=DB_USER \
--MYSQL_PASSWORD=DB_PASSWORD \
--BUFFER_SIZE=100 \
--CORE_TASK_NUM=5 \
--MAX_FETCH_SIZE=100 \
--CHECK_FILE=/egova/weakPwd_Check/checkfile.txt \
--QUERY_SCRIPT="select id as humanId, username, CUSTOME_FIELD as encType, password as dbValue from DB_TABLE where id>? and (disabled=0 or disabled is null) order by id asc limit <maxFetchSize>" \
--COUNT_SCRIPT="select count(*) from DB_TABLE where disabled=0 or disabled is null" \
--ID_TYPE=STRING \
> /dev/null 2>&1 &

echo "logs in /egova/weakPwd_Check/logs/info.log"
