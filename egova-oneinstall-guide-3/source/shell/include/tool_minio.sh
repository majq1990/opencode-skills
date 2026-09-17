#!/bin/bash

policy_template=../template/mino-policy-template.json
metadata_file=../../ansible/inventory/metadata.yml
global_conf=../../ansible/group_vars/all.yml
ms_template_file=../template/microservice_template.yml

# 创建桶、用户及赋权
function create_bucket_user() {
    local select_key=$1
    local key=$2
    local minio_ip=$(yq ".minio.${select_key}.ip" ${metadata_file})
    local minio_port=$(yq ".minio.${select_key}.port" ${metadata_file})
    local minio_access_key=$(yq ".minio.${select_key}.access_key" ${metadata_file})
    local minio_secret_key=$(yq ".minio.${select_key}.secret_key" ${metadata_file})
   # local minio_catalog_user=$(yq ".minio.${select_key}.catalog_user" ${metadata_file})
   # local minio_catalog_password=$(yq ".minio.${select_key}.catalog_password" ${metadata_file})
    local minio_bucket_name=$(yq '.'${key}'.depends[] | select(.type == "minio") | .bucket_name' ${ms_template_file})
    host_exist=$(mc config host list|grep $select_key)
    bucket_exist=$(mc ls $select_key |grep $minio_bucket_name)
    # 创建host
    if [ "$host_exist" == "" ]; then
      mc config host add $select_key http://${minio_ip}:${minio_port} $minio_access_key $minio_secret_key
    fi
    # 创建桶
    if [ "$bucket_exist" == "" ]; then
     mc mb ${select_key}/${minio_bucket_name} -p
     common_pwd=$(yq '.common_password' $global_conf)
     mc admin user add $select_key ${minio_bucket_name} ${common_pwd}
     mc admin policy attach $select_key readonly --user ${minio_bucket_name}
     mc admin policy attach $select_key writeonly -user ${minio_bucket_name}
    fi
    # gis配置文件需要egovacatalog用户
   # result=$(mc admin user list $select_key | grep ${minio_catalog_user})
   # if [ "$result" == "" ]; then
   #     mc admin user add $select_key ${minio_catalog_user} ${minio_catalog_password}
   #    mc admin policy attach  $select_key readonly --user ${minio_catalog_user}
   #     mc admin policy attach  $select_key writeonly --user ${minio_catalog_user}
   # fi

}
