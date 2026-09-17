#!/bin/bash

# 1、选择切换的数据库类型
# 2、选择输入数据库信息
# 3、修改jdbc.properties 、hibernate.properties、env文件
# 4、ansible 执行脚本
# 5、restart service或mc

ms_template_file=/egova/tools/script/microservice_template.yml
service_template_file=/egova/tools/script/tomcat_app_template.yml
db_template_file=/egova/tools/script/db_template.yml

# 读取参数
while [ -n "$1" ]; do
    case "$1" in
    --DB_USER=*)
        DB_USER="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --DB_PASSWORD=*)
        DB_PASSWORD="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --DB_PORT=*)
        DB_PORT="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --DB_HOST=*)
        DB_HOST="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --DB_NAME=*)
        DB_NAME="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --DB_SCHEMA=*)
        DB_SCHEMA="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --DB_TYPE=*)
        DB_TYPE="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --DB_DRIVER=*)
        DB_DRIVER="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --SELECTED_PRODUCT_NAME=*)
        SELECTED_PRODUCT_NAME="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --DB_STAT_HOST=*)
        DB_STAT_HOST="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --DB_STAT_NAME=*)
        DB_STAT_NAME="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --DB_STAT_PORT=*)
        DB_STAT_PORT="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    --DB_STAT_SCHEMA=*)
        DB_STAT_SCHEMA="$(echo $1|awk -F= '{print $2}')"
        shift 1
        ;;
    *)
        shift 1
        break
        ;;
    esac
done

[ -z "$DB_USER" ] && DB_USER=root
[ -z "$DB_PASSWORD" ] && DB_PASSWORD=egova
[ -z "$DB_PORT" ] && DB_PORT=3306
[ -z "$DB_HOST" ] && DB_HOST=127.0.0.1
[ -z "$DB_NAME" ] && DB_NAME=test
[ -z "${DB_SCHEMA}" ] && DB_SCHEMA=""
[ -z "${DB_TYPE}" ] && DB_TYPE="dm"
[ -z "${DB_DRIVER}" ] && DB_DRIVER="dm.jdbc.driver.DmDriver"
[ -z "$DB_STAT_HOST" ] && DB_STAT_HOST=""
[ -z "$DB_STAT_PORT" ] && DB_STAT_PORT=3306
[ -z "$DB_STAT_NAME" ] && DB_STAT_NAME=test
[ -z "${DB_STAT_SCHEMA}" ] && DB_STAT_SCHEMA=""
[ -z "${SELECTED_PRODUCT_NAME}" ] && SELECTED_PRODUCT_NAME=""

# 修改智信云产品数据库连接信息
function modify_service_db_connection() {
  local keys=($(yq '.[] | key ' ${service_template_file}))
  for key in "${keys[@]}"; do
    local base_path=$(yq ".${key}.base_path" ${service_template_file})
    local JDBC_PROPERTIES_PATH="${base_path}/${key}/WEB-INF/classes/jdbc.properties"
    local HIBERNATE_PROPERTIES_PATH="${base_path}/${key}/WEB-INF/classes/hibernate.properties"
    if ! [ -f "$JDBC_PROPERTIES_PATH" ]; then
            continue
    fi
    local db_url=$(yq ".${DB_TYPE}.sub_options[].sub_options[] | select(.type == \"${key}\") | .db_url // \"\"" ${db_template_file})
    # Replace JDBC properties
    if [ "${db_url}" != "" ]; then
          sed -i "s|^biz.jdbc.url=.*|${db_url}|g" "$ENV_PATH"
          sed -i "s|DB_HOST:DB_PORT|${DB_HOST}:${DB_PORT}|g" ${ENV_PATH}
          sed -i "s|DB_TYPE|${DB_TYPE}|g" ${ENV_PATH}
          sed -i "s|DB_NAME|${DB_NAME}|g" ${ENV_PATH}
          sed -i "s|DB_SCHEMA|${DB_SCHEMA}|g" ${ENV_PATH}
    elif [ "${DB_TYPE}" == "dm" ]; then
          sed -i "s|^biz.jdbc.url=.*|biz.jdbc.url=jdbc:${DB_TYPE}://${DB_HOST}:${DB_PORT}?clobAsString=true|g" "$JDBC_PROPERTIES_PATH"
          sed -i "s|^stat.jdbc.url=.*|stat.jdbc.url=jdbc:${DB_TYPE}://${DB_STAT_HOST}:${DB_STAT_PORT}?clobAsString=true|g" "$JDBC_PROPERTIES_PATH"
          sed -i "s|^biz.jdbc.validation.query=.*|biz.jdbc.validation.query=select sysdate from dual|g" "$HIBERNATE_PROPERTIES_PATH"
          sed -i "s|^stat.jdbc.validation.query=.*|biz.jdbc.validation.query=select sysdate from dual|g" "$HIBERNATE_PROPERTIES_PATH"
          grep -q "^hibernate.dialect=org.hibernate.dialect.DmDialect" "$HIBERNATE_PROPERTIES_PATH" || sed -i "/^hibernate.format_sql=.*/a hibernate.dialect=org.hibernate.dialect.DmDialect " "$HIBERNATE_PROPERTIES_PATH"
          sed -i "s|^#hibernate.dialect=org.hibernate.dialect.DmDialect|hibernate.dialect=org.hibernate.dialect.DmDialect|g" "$HIBERNATE_PROPERTIES_PATH"
    elif [ "${DB_TYPE}" == "postgresql" ]; then
          sed -i "s|^biz.jdbc.url=.*|biz.jdbc.url=jdbc:${DB_TYPE}://${DB_HOST}:${DB_PORT}?currentSchema=${DB_NAME},public|g" "$JDBC_PROPERTIES_PATH"
          sed -i "s|^stat.jdbc.url=.*|stat.jdbc.url=jdbc:${DB_TYPE}://${DB_STAT_HOST}:${DB_STAT_PORT}?currentSchema=${DB_STAT_NAME},public|g" "$JDBC_PROPERTIES_PATH"
          grep -q "^hibernate.dialect=cn.com.egova.base.dialect.EgovaKingbase8Dialect" "$HIBERNATE_PROPERTIES_PATH" || sed -i "/^hibernate.format_sql=.*/a hibernate.dialect=cn.com.egova.base.dialect.EgovaKingbase8Dialect " "$HIBERNATE_PROPERTIES_PATH"
          sed -i "s|^#hibernate.dialect=org.hibernate.dialect.DmDialect|hibernate.dialect=cn.com.egova.base.dialect.EgovaKingbase8Dialect|g" "$HIBERNATE_PROPERTIES_PATH"
    elif [ "${DB_TYPE}" == "highgo" ]; then
          sed -i "s|^biz.jdbc.url=.*|biz.jdbc.url=jdbc:${DB_TYPE}://${DB_HOST}:${DB_PORT}?currentSchema=${DB_NAME},public|g" "$JDBC_PROPERTIES_PATH"
          sed -i "s|^stat.jdbc.url=.*|stat.jdbc.url=jdbc:${DB_TYPE}://${DB_STAT_HOST}:${DB_STAT_PORT}?currentSchema=${DB_STAT_NAME},public|g" "$JDBC_PROPERTIES_PATH"
          grep -q "^hibernate.dialect=cn.com.egova.base.dialect.EgovaHgdbDialect" "$HIBERNATE_PROPERTIES_PATH" || sed -i "/^hibernate.format_sql=.*/a hibernate.dialect=cn.com.egova.base.dialect.EgovaHgdbDialect " "$HIBERNATE_PROPERTIES_PATH"
          sed -i "s|^#hibernate.dialect=org.hibernate.dialect.DmDialect|hibernate.dialect=cn.com.egova.base.dialect.EgovaHgdbDialect|g" "$HIBERNATE_PROPERTIES_PATH"
    else
          SELECTED_PRODUCT_NAME "不支持数据库类型"
    fi
    sed -i "s|^biz.jdbc.driverClassName=.*|biz.jdbc.driverClassName=${DB_DRIVER}|g" "$JDBC_PROPERTIES_PATH"
    sed -i "s|^biz.jdbc.username=.*|biz.jdbc.username=${DB_USER}|g" "$JDBC_PROPERTIES_PATH"
    sed -i "s|^biz.jdbc.cryptogram=.*|biz.jdbc.cryptogram=${DB_PASSWORD}|g" "$JDBC_PROPERTIES_PATH"

    sed -i "s|^stat.jdbc.driverClassName=.*|stat.jdbc.driverClassName=${DB_DRIVER}|g" "$JDBC_PROPERTIES_PATH"
    sed -i "s|^stat.jdbc.username=.*|stat.jdbc.username=${DB_USER}|g" "$JDBC_PROPERTIES_PATH"
    sed -i "s|^stat.jdbc.cryptogram=.*|stat.jdbc.cryptogram=${DB_USER}|g" "$JDBC_PROPERTIES_PATH"
    sed -i "s|^hibernate.dialect=org.hibernate.dialect.MySQLDialect|#hibernate.dialect=org.hibernate.dialect.MySQLDialect|g" "$HIBERNATE_PROPERTIES_PATH"
    sed -i "s|^hibernate.special_sql_type=.*|hibernate.special_sql_type=1|g" "$HIBERNATE_PROPERTIES_PATH"
  done
}

# 修改微服务产品数据库连接信息
function modify_microservice_db_connection() {
    local base_path=$(yq ".${SELECTED_PRODUCT_NAME}.base_path" ${ms_template_file})
    local ENV_PATH="${base_path}/${SELECTED_PRODUCT_NAME}.env"
    if ! [ -f "$ENV_PATH" ]; then
        echo "未找到$ENV_PATH文件，跳过切换"
        return
    fi
    local db_url=$(yq ".${DB_TYPE}.sub_options[].sub_options[] | select(.type == \"${SELECTED_PRODUCT_NAME}\") | .db_url // \"\"" ${db_template_file})
    local db_custom_config=$(yq ".${DB_TYPE}.sub_options[].sub_options[] | select(.type == \"${SELECTED_PRODUCT_NAME}\") | .db_custom_config[] " ${db_template_file})
    # Replace JDBC properties
    if [ "${db_url}" != "" ]; then
      sed -i "s|^--DATASOURCE_URL=.*|${db_url} \\\\|g" "$ENV_PATH"
      sed -i "s|DB_HOST:DB_PORT|${DB_HOST}:${DB_PORT}|g" ${ENV_PATH}
      sed -i "s|DB_TYPE|${DB_TYPE}|g" ${ENV_PATH}
      sed -i "s|DB_NAME|${DB_NAME}|g" ${ENV_PATH}
      sed -i "s|DB_SCHEMA|${DB_SCHEMA}|g" ${ENV_PATH}
    elif [ "${DB_TYPE}" == "dm" ]; then
         if { [[ "${SELECTED_PRODUCT_NAME}" == "export" ]] || [ "${SELECTED_PRODUCT_NAME}" == "evaluation" ]; }; then
             sed -i "s|^--STAT_DATASOURCE_URL=.*|--STAT_DATASOURCE_URL=jdbc:${DB_TYPE}://${DB_STAT_HOST}:${DB_STAT_PORT}?clobAsString=true \\\\|g" "$ENV_PATH"
         fi
      sed -i "s|^--DATASOURCE_URL=.*|--DATASOURCE_URL=jdbc:${DB_TYPE}://${DB_HOST}:${DB_PORT}?clobAsString=true \\\\|g" "$ENV_PATH"
    elif [ "${DB_TYPE}" == "postgresql" ]; then
        if { [[ "${SELECTED_PRODUCT_NAME}" == "export" ]] || [ "${SELECTED_PRODUCT_NAME}" == "evaluation" ]; }; then
           sed -i "s|^--STAT_DATASOURCE_URL=.*|--STAT_DATASOURCE_URL=jdbc:${DB_TYPE}://${DB_STAT_HOST}:${DB_STAT_PORT}/${DB_STAT_NAME_NAME} \\\\|g" "$ENV_PATH"
        fi
      sed -i "s|^--DATASOURCE_URL=.*|--DATASOURCE_URL=jdbc:${DB_TYPE}://${DB_HOST}:${DB_PORT}/${DB_NAME} \\\\|g" "$ENV_PATH"
    elif [ "${DB_TYPE}" == "highgo" ]; then
       if { [[ "${SELECTED_PRODUCT_NAME}" == "export" ]] || [ "${SELECTED_PRODUCT_NAME}" == "evaluation" ]; }; then
         sed -i "s|^--STAT_DATASOURCE_URL=.*|--STAT_DATASOURCE_URL=jdbc:${DB_TYPE}://${DB_STAT_HOST}:${DB_STAT_PORT}/${DB_STAT_NAME_NAME}?currentSchema=${DB_STAT_SCHEMA} \\\\|g" "$ENV_PATH"
       fi
       sed -i "s|^--DATASOURCE_URL=.*|--DATASOURCE_URL=jdbc:${DB_TYPE}://${DB_HOST}:${DB_PORT}/${DB_NAME}?currentSchema=${DB_SCHEMA} \\\\|g" "$ENV_PATH"
    else
      echo "不支持数据库类型"
    fi
    if { [[ "${SELECTED_PRODUCT_NAME}" == "export" ]] || [ "${SELECTED_PRODUCT_NAME}" == "evaluation" ]; }; then
        sed -i "s|^--STAT_DATASOURCE_DRIVER=.*|--STAT_DATASOURCE_DRIVER=${DB_DRIVER} \\\\|g" "$ENV_PATH"
        sed -i "s|^--STAT_DATASOURCE_USERNAME=.*|--STAT_DATASOURCE_USERNAME=${DB_USER} \\\\|g" "$ENV_PATH"
        sed -i "s|^--STAT_DATASOURCE_PASSWORD=.*|--STAT_DATASOURCE_PASSWORD=${DB_PASSWORD} \\\\|g" "$ENV_PATH"
    fi
    sed -i "s|^--DATASOURCE_DRIVER=.*|--DATASOURCE_DRIVER=${DB_DRIVER} \\\\|g" "$ENV_PATH"
    sed -i "s|^--DATASOURCE_USERNAME=.*|--DATASOURCE_USERNAME=${DB_USER} \\\\|g" "$ENV_PATH"
    sed -i "s|^--DATASOURCE_PASSWORD=.*|--DATASOURCE_PASSWORD=${DB_PASSWORD} \\\\|g" "$ENV_PATH"
    # Update Hibernate properties
    for item in ${db_custom_config[@]}; do
        grep -q "^$item" "$ENV_PATH" || sed -i "/^--DATASOURCE_PASSWORD=.*/a $item \\\\" "$ENV_PATH"
    done
}

function run(){
   if [ "${SELECTED_PRODUCT_NAME}" != "" ]; then
         modify_microservice_db_connection
   else
        modify_service_db_connection
   fi
}

run