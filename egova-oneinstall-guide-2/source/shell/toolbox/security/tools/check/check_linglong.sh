#!/bin/bash

# 数据库配置
DB_HOST=$1
DB_USER=$2
DB_NAME=$3
DB_PASS=$4

# 预期的更新值，与上面的UPDATE语句中的值对应
EXPECTED_VALUES=(
         "egova.security.request.encrypt-type|sm4",
         "commonSetting.strict|true",
         "egova.security.injection.xss-enable|true",
         "egova.file-type.check.enabled|true",
         "egova.lowcode.backup.application.enable|true",
         "com.egova.security.sql.sensitive.columns|com_user.password|com_user.phone|ddcat_source.password",
         "com.egova.security.sql.sensitive.schemas|mysql|information_schema|performance_schema",
         "com.egova.security.sql.sensitive.tables|com_user|ddcat_source",
         "com.egova.security.sql.sensitive.enable|true",
         "com.egova.security.sql.select-all.enable|false",
         "egova.file-type.check.white-list|jpeg, jpg, png, gif, bmp, tiff, tif, webp, svg, ico, hdr, doc, docx, xls, xlsx, ppt, pptx, pdf, odt, ods, odp, zip, rar, 7z, tar, gz, bz2, xz, mp4, avi, mov, mkv, wmv, flv, mpeg, mpg, 3gp, txt, xml, json",
         "egova.file-type.check.strong-verify|true",
         "com.egova.lowcode.global-exception.responseCode|403",
         "egova.security.referer.enabled|true"
         "egova.security.limit.design-permission.enabled|true"
)

# 检查更新操作是否有效执行的函数
check_update() {
    local name=$1
    local value=$2
    local actual_value=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "SELECT value FROM com_option WHERE name = '$name';" | tr -d '\n')
    
    if [ "$actual_value" == "$value" ]; then
        echo "配置项 com_option.$name 已经是期望的值 $value"
    else
        echo "配置项 com_option.$name 未更新为期望的值 $value, 当前值为 $actual_value"
    fi
}

# 检查 com_option 表中的记录
for i in "${!EXPECTED_VALUES[@]}"; do
    name_value_pair=($(echo "${EXPECTED_VALUES[$i]}" | tr "|" " "))
    check_update "${name_value_pair[0]}" "${name_value_pair[1]}"
done
