#!/bin/bash

#tip为是否仅提示/egova将挂载在哪个分区的标识，若为onlytip,则为仅提示
tip=$1
EGOVA_ROOT=/egova
CONF_MOUNT_DIR=/etc/egova/mount
TEST_MOUNT_DIR=/etc/egova/mnt
#最大分区已经被挂载时，是否允许替换已有mount为/egova
CHANGE_MOUNT_IF_MAX_PARTITION_USED=1
#本脚本只做检查，不做实际操作
ONLY_CHECK_PARTITION=0
#可以用来挂载/egova的目录
AVAILABLE_DIR=("/data" "/home" "/")

mkdir -p $CONF_MOUNT_DIR
mkdir -p $TEST_MOUNT_DIR

cached_distribution_info=""
##获取系统版本信息
function get_distribution_info() {
    ##缓存版本信息
    if [ -n "$cached_distribution_info" ]; then
          echo "$cached_distribution_info"
          return 0
    fi
    if [ -f /etc/os-release ]; then
        source /etc/os-release

        if [ -n "$ID" ]; then
            # 检查centos版本
            if [ -n "$VERSION_ID" ]; then
                version=$(echo $VERSION_ID | cut -d'.' -f1)
            else
                # 检查Ubuntu版本
                if [ -n "$UBUNTU_CODENAME" ]; then
                    version=$(lsb_release -rs | cut -d. -f1)
                fi
            fi
            if [ "$(uname -m)" == "x86_64" ]; then
              arch=$(echo "x86")
            else
              arch=$(echo "arm")
            fi
            cached_distribution_info="$ID"_"$version"_"$arch"
            echo "$cached_distribution_info"
            return 0
        fi
    fi
    return 1
}
##检查版本
function check_distribution() {
    local distribution=$1

    if [[ "$(get_distribution_info)" =~ ($distribution) ]]; then
        echo "操作系统：$(get_distribution_info)"
        return 0
    fi
    return 1
}
function is_kylin() {
   check_distribution "kylin"
}
function is_openEuler() {
     check_distribution "openEuler"
}
function is_ubuntu() {
   check_distribution "ubuntu"
}
function is_centos() {
   check_distribution "centos"
}
max_2_egova() {
    max_dir=$1
    p=$(df -hP | grep "$max_dir" | cut -d " " -f 1)
    if [ "${p}" != "" ]; then
        umount $max_dir
        mkdir -p $EGOVA_ROOT
        mount $p $EGOVA_ROOT
        sed -i "s#${max_dir}#${EGOVA_ROOT}#g" /etc/fstab
        return 0
    fi
    return 1
}

is_empty_dir() {
    return $(ls -A $1 | wc -w)
}

is_str_contain() {
    if [[ $1 == *$2* ]]; then
        return 1
    else
        return 0
    fi
}

get_partition_size() {
    #$1 partition
    #echo size
    list=$(fdisk -l $1 | grep -E "Disk|磁盘" | grep "/dev" | awk -F"[： ]" '{print $3 " " $4}' | awk -F"[,，]" '{print $1}')
    array=($list)
    size=${array[0]}
    unit=${array[1]}
    if [ "${unit}" = "" ]; then
        echo 0
    elif [ $unit = "GB" ]; then
        echo $size | awk '{printf "%d",$1*1024}'
    elif [ $unit = "GiB" ]; then
        echo $size | awk '{printf "%d",$1*1024}'
    elif [ $unit = "TB" ]; then
        echo $size | awk '{printf "%d",$1*1024*1024}'
    else
        echo $size
    fi
}
# 获取分区状态
check_partition_status() {
    partition=$1
    # 尝试挂载，判断是否可用
    ret=$(mount $partition $TEST_MOUNT_DIR 2>&1)
    if [ $? = 0 ]; then
        umount $TEST_MOUNT_DIR
        partition_status="mount"
    else
        unknow_flag=$(echo "$ret" | grep -E "unknown filesystem|未知的文件系统类型|上有坏超级块" | wc -l)
        if [ ${unknow_flag} -gt 0 ]; then
            partition_status="format"
        else
            partition_status="error"
        fi
    fi
}
# 检查最大分区是否存在lvm，
check_partition_has_lvm() {
    # $1 : partition
    partition_lvm=""
    vgname=$(pvs | awk '{if($1=="'$1'")print $2}' | head -1)
    if [ "$vgname" != "" ]; then
        #        lvname=$(lvs |awk '{if($2=="'${vgname}'")print $1}' |head -1)
        list=($(lvs | awk '{if($2=="'${vgname}'")print $1"="$4}' ORS=' '))
        maxSize=0
        maxPartName=""
        for lvname in ${list[@]}; do
            name=$(echo $lvname | cut -d "=" -f 1)
            size=$(echo $(echo $lvname | cut -d "=" -f 2) | tr 'A-Z' 'a-z')
            unit=$(echo $size | tr -d '[<0-9.]')
            sizeNum=$(echo $size | tr -d '[<a-z]')
            case $unit in
            m)
                multi=1024
                ;;
            g)
                multi=1048576
                ;;
            t)
                multi=1099511627776
                ;;
            *)
                multi=1
                ;;
            esac
            sizeNum=$(echo $(awk -v x=$multi -v y=$sizeNum 'BEGIN{printf "%d\n",x*y}'))
            if test $sizeNum -ge $maxSize; then
                maxPartName=$name
                maxSize=$sizeNum
            fi

        done

        partition_lvm=/dev/mapper/${vgname}-${maxPartName}
    fi
}

is_available_path() {
    path=$1
    for item in ${AVAILABLE_DIR[@]}; do
        if [ "$item" = "$path" ]; then
            echo 0
            return
        fi
    done
    echo 1
}

check_partition() {
    # 查询设备下所有的part
    #    list=`fdisk -l $1 | grep "/dev" | grep -v -E "Disk|磁盘" | awk '{print $1}'`
    list=$(lsblk -bl $1 | grep -v "NAME" | awk '{if($6=="part"||($7!=""&&$7!="MOUNTPOINT"))print $1","$4}')
    flag=0
    for partition_info in $list; do
        flag=1
        partition=$(echo ${partition_info} | awk -F, '{print $1}')
        size=$(echo ${partition_info} | awk -F, '{print $2}')
        size=$(expr $size / 1024 / 1024)
        name=${partition}
        partition=/dev/${partition}

        if [ $size -gt ${max_partition_size} ]; then
            #echo "====find max_size $size"
            # 是否已被挂载
            if test -e $CONF_MOUNT_DIR/$name; then
                old_path=$(cat $CONF_MOUNT_DIR/$name)
                if [ ${CHANGE_MOUNT_IF_MAX_PARTITION_USED} -eq 1 ]; then
                    if ! test $(is_available_path $old_path) -eq 0; then
                        continue
                    fi
                    max_partition_size=$size
                    max_partition=$partition
                    max_partition_status="chmount"
                    max_partition_path=$old_path
                    if [ "$old_path" == "/" ]; then
                        max_partition_status="useroot"
                    fi
                else
                    echo "分区${partition}已被 使用，忽略..."
                fi
            else
                # 尝试挂载，判断是否可用
                check_partition_status $partition
                #echo partition_status=${partition_status}
                if [ "${partition_status}" != "error" ]; then
                    max_partition_size=$size
                    max_partition=$partition
                    max_partition_status="${partition_status}"
                fi
            fi
        fi

        if test ! -e $CONF_MOUNT_DIR/$name; then
            #echo size=$size max_partition_size=${max_partition_size}
            if [ $size -gt ${max_partition_size} ]; then
                #echo "====find max_size $size"
                # 尝试挂载，判断是否可用
                check_partition_status $partition
                #echo partition_status=${partition_status}
                if [ "${partition_status}" != "error" ]; then
                    max_partition_size=$size
                    max_partition=$partition
                    max_partition_status="${partition_status}"
                fi
            fi
        fi
    done
    if [ $flag = 0 ]; then
        # 不存在分区，且不是lvm块设备时，需要进行分区创建（即，不允许对磁盘进行无分区直接格式化后挂载使用）
        disk_size=$(lsblk -bl $1 | awk '{if($6=="disk")print $4}')

        if [ "${disk_size}" != "" ]; then
            partition=$1
            size=$(expr ${disk_size} / 1024 / 1024)
            if [ $size -gt ${max_partition_size} ]; then
                max_partition_size=$size
                max_partition=$partition
                max_partition_status="create"
            fi
        fi
    fi
}

# 检查已挂载的分区信息
check_mount() {
    index=0
    rm -f $CONF_MOUNT_DIR/*

    list=$(mount | grep "/dev" | grep -v "/dev/pts" | grep -v -E "/dev/shm|/boot|devtmpfs" | awk '{print $1 ":" $3}')
    for str in $list; do
        OLD_IFS="$IFS"
        IFS=":"
        array=($str)
        IFS="$OLD_IFS"
        partition=${array[0]}
        mount_dir=${array[1]}
        #echo "item $partition $mount_dir"
        echo "$mount_dir" >$CONF_MOUNT_DIR/${partition##*/}
        if [ $mount_dir = "$EGOVA_ROOT" ]; then
            EGOVA_PARTITION=$partition
            EGOVA_SIZE=$(get_partition_size $partition)
            #echo "EGOVA_SIZE=$EGOVA_SIZE"
        elif [ $mount_dir = "/" ]; then
            ROOT_PARTITION=$partition
            ROOT_SIZE=$(get_partition_size $partition)
            #echo "ROOT_SIZE=$ROOT_SIZE"
        fi
    done
}

auto_create_egova_dir() {
    #判断是否已经创建或挂载EGOVA_ROOT目录

    egova_root_size=$(df -hP | awk '{if($6=="'${EGOVA_ROOT}'")print $2}')
    root_size=$(df -hP | awk '{if($6=="/")print $2}')

    if [ "${egova_root_size}" != "" ]; then
        echo "$EGOVA_ROOT 已经挂载，独立分区，容量$egova_root_size"
         #仅提示时不退出整个脚本
        if [ "$tip" = "onlytip" ];then
            return
        fi
        cat /etc/fstab | grep -w "/egova" >/dev/null
        if [ $? != 0 ]; then
            p=$(df -hP | grep -w "${EGOVA_ROOT}" | cut -d " " -f 1)
            echo "$p $EGOVA_ROOT ext4 defaults 0 0" >>/etc/fstab
            echo "修正/etc/fstab"
        fi
        echo "ok"
        exit 0
    else
        if test -d $EGOVA_ROOT; then
            if ! is_empty_dir $EGOVA_ROOT; then
                echo "$EGOVA_ROOT 已经创建，在/所在分区，容量$root_size"
                #仅提示时不退出整个脚本
                if [ "$tip" = "onlytip" ];then
                    return
                else
                    echo "ok"
                    exit 0
                fi
            fi
            #仅提示时不退出整个脚本
            if [ "$tip" = "onlytip" ];then
                return
            fi
            #        else
            #            mkdir -p $EGOVA_ROOT
        fi
    fi

    # home_2_egova

    check_mount

    max_partition_size=0
    # 获取所有磁盘，遍历分区获取最大分区
    list=$(fdisk -l | grep -E "Disk|磁盘" | grep "/dev" | awk '{print $2}' | awk -F"[:：]" '{print $1}')
    for disk in $list; do
        #echo disk=$disk
        check_partition $disk
    done
    #判断是否存在lvm
    check_partition_has_lvm $max_partition
    use_lvm=0
    if [ "${partition_lvm}" != "" ]; then
        check_partition_status ${partition_lvm}
        if [ "${partition_status}" != "error" ]; then
            max_partition=${partition_lvm}
            max_partition_size=$(get_partition_size ${partition_lvm})
            max_partition_status="${partition_status}"
            use_lvm=1
            if [ "${partition_status}" == "mount" ]; then
                #检查是否已被挂载
                name=${max_partition##*/}
                if test -e $CONF_MOUNT_DIR/$name; then
                    old_path=$(cat $CONF_MOUNT_DIR/$name)
                    if [ "$old_path" == "/" ]; then
                        max_partition_status="useroot"
                    else
                        max_partition_status="chmount"
                        max_partition_path=$old_path
                    fi
                fi
            fi
        else
            echo "最大分区[$max_partition]的LVM分区[${partition_lvm}]不可用,只能使用root目录"
            max_partition_status="useroot"
        fi
    fi
    if [ "$tip" == "onlytip" ]; then
        max_partition_status="onlytip"
    fi
    if [ "${max_partition_status}" == "create" ]; then
        echo "create_and_mount $max_partition"
        create_and_mount
        exit 0
    elif [ "${max_partition_status}" == "format" ]; then
        echo "format_and_mount $max_partition"
        format_and_mount
        exit 0
    elif [ "${max_partition_status}" == "mount" ]; then
        echo "only_mount $max_partition"
        only_mount
        exit 0
    elif [ "${max_partition_status}" == "chmount" ]; then
        echo "chmount $max_partition ${max_partition_path}"
        chmount ${max_partition_path}
        exit 0
    elif [ "${max_partition_status}" == "useroot" ]; then
        echo "useroot"
        useroot
        exit 0
    elif [ "${max_partition_status}" == "onlytip" ]; then
        only_mount_tip
        return
    fi
    echo "error 非预期结果：max_partition_status=${max_partition_status} max_partition=$max_partition"
    exit 1
}

# 将已有挂载改为egova
chmount() {
    if [ ${ONLY_CHECK_PARTITION} -eq 0 ] && [ "${max_partition_path}" != "/" ]; then
        max_2_egova ${max_partition_path}
        echo "/egova挂载到分区${max_partition},容量${max_partition_size},原有挂载点${max_partition_path}被移除！"
    fi
}
#直接使用root目录
useroot() {
    if [ ${ONLY_CHECK_PARTITION} -eq 1 ]; then
        return
    fi
    echo "最大分区$max_partition为根目录,直接创建$EGOVA_ROOT"
    mkdir -p $EGOVA_ROOT
}
#空盘,创建分区并且挂载
create_and_mount() {
    if [ ${ONLY_CHECK_PARTITION} -eq 1 ]; then
        return
    fi
    echo "创建分区${max_partition}1并格式化..."
    parted -s $max_partition mklabel gpt mkpart primary 0% 100%
    pvcreate -f ${max_partition}1
    vgcreate vgegova ${max_partition}1
    lvcreate -l 100%FREE -n egova vgegova
    mkfs.ext4 /dev/mapper/vgegova-egova
    mkdir -p $EGOVA_ROOT
    mount /dev/mapper/vgegova-egova $EGOVA_ROOT
    echo "/dev/mapper/vgegova-egova $EGOVA_ROOT ext4 defaults 0 0" >>/etc/fstab
    echo "/egova挂载到分区/dev/mapper/vgegova-egova,容量${max_partition_size}"
}
format_and_mount() {
    if [ ${ONLY_CHECK_PARTITION} -eq 1 ]; then
        return
    fi
    echo "分区${max_partition}格式化..."
    mkfs.ext4 $max_partition
    mkdir -p $EGOVA_ROOT
    mount ${max_partition} $EGOVA_ROOT
    echo "${max_partition} $EGOVA_ROOT ext4 defaults 0 0" >>/etc/fstab
    echo "/egova挂载到分区${max_partition},容量${max_partition_size}"
}
only_mount() {
    if [ ${ONLY_CHECK_PARTITION} -eq 1 ]; then
        return
    fi
    mkdir -p $EGOVA_ROOT
    mount ${max_partition} $EGOVA_ROOT
    echo "${max_partition} $EGOVA_ROOT ext4 defaults 0 0" >>/etc/fstab
    echo "/egova挂载到分区${max_partition},容量${max_partition_size}"
}

#用于提醒要挂载的磁盘，避免磁盘选择出现错误时工程无法及时发现的问题
only_mount_tip() {
    if [ ${ONLY_CHECK_PARTITION} -eq 1 ]; then
        return
    fi

    max_partition_size=$(expr $max_partition_size / 1024)
    echo "${EGOVA_ROOT}将挂载到分区${max_partition},容量${max_partition_size}G，若挂载分区不正确请输入N退出，自行手动挂载后再执行"
    read -r -p "请确认将挂载的分区是否正确[Y/N]" isSure
    case $isSure in
        [Yy])
          return
          ;;
        *)
          exit 1
          ;;
    esac
}

release_info=$(get_distribution_info)
release_name=$(echo "${release_info}"|awk -F"_" '{print $1}')
release_ver=$(echo "${release_info}"|awk -F"_" '{print $2}')

#该脚本安装一键部署脚本所必须的工具
#安装lvs pvs命令
install_lvm2() {
    which pvs &>/dev/null
    if test $? -ne 0; then
        # 在脚本开始前执行的，不展示安装信息
         if is_ubuntu; then
           apt install -y lvm2
         else
           yum install -y lvm2
         fi
    fi

}

install_lvm2

auto_create_egova_dir

which pvs &>/dev/null
if [ $? -gt 0 ]; then
    echo "检查到当前机器未能成功安装lvm,请手工确认/egova挂载到最大磁盘"
fi
