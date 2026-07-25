#!/bin/bash

# 读取参数
while [ -n "$1" ]; do
    case "$1" in
    --user=*)
        user="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --password=*)
        password="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --port=*)
        port="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --host=*)
        host="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --database=*)
        database="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --dir=*)
        dir="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    *)
        shift 1
        break
        ;;
    esac
done

[ -z "$user" ] && user=root
[ -z "$password" ] && password=egova
[ -z "$port" ] && port=3306
[ -z "$host" ] && host=127.0.0.1
[ -z "$database" ] && database=test
[ -z "${dir}" ] && dir="/egova"

# 建库
connect_db_cmd="-h ${host} -P ${port} -u ${user} -p${password}"
mysql ${connect_db_cmd} -e "CREATE DATABASE IF NOT EXISTS ${database} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;" 2>/dev/null
# 建表
mysql ${connect_db_cmd} -D ${database} -e "CREATE TABLE IF NOT EXISTS db_init_log_oneinstall(id bigint NOT NULL AUTO_INCREMENT, sql_file varchar(255) NOT NULL, execute_time timestamp NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (id)) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;"  2>/dev/null
ls ${dir}/*.sql | while read sql_file
do
    # 为防止删除库表，直接注释掉相关的drop语句
    sed -i "s/^DROP /-- DROP /g;s/^drop /-- drop/g" ${sql_file}
    sed -i "s/^CREATE TABLE \`/CREATE TABLE IF NOT EXISTS \`/g" ${sql_file}
    echo "执行sql: ${sql_file}"
    query_rst=$(mysql ${connect_db_cmd} -D ${database} -e "select count(*) from db_init_log_oneinstall where sql_file = \"$sql_file\"")
    count_rst=$(echo $query_rst | awk '{print $2}')
    if [ $count_rst -eq 0 ];then
        mysql ${connect_db_cmd} -e "SET GLOBAL log_bin_trust_function_creators=TRUE;"
        mysql ${connect_db_cmd} -D ${database} -e "source $sql_file;insert into db_init_log_oneinstall(sql_file) values(\"$sql_file\");"
    fi
done
