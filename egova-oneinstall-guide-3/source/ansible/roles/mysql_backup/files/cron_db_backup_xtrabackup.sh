#!/bin/bash --login

shopt -s expand_aliases
set -e
DB_USER=root
DB_PWD=Wk2uBTeyp6
DB_PORT=3306

# 本机部署时，请将MEDIA_SERVER改为localhost或者置为空
MEDIA_SERVER=localhost
SSH_PORT=22
SSH_USER_HOME=/root
SSH_USER=root

BACKUP_BIZ=1
BACKUP_STAT=1

#xtrabackup 全量备份数据库,该配置没用到
#DATABASE_BIZ="cgdb,public,mms"
#DATABASE_STAT="cgdbstat"

cur_date=$(date +%Y-%m-%d_%H-%M-%S-%N | cut -b 1-23)
back_path=/egova/backup/db
log_file=${back_path}/mysql-backup.log
lock_file=${back_path}/back.lock
temp_file=${back_path}/temp_${cur_date}.log

#binlog最少保留天数
bin_log_min_stay_days=30
full_backup_max_stay_days=30
incr_backup_max_stay_days=7

# 动态计算并行度
cpu_count=$(nproc --all)
parallel=$(($cpu_count / 4))
if [ $parallel -lt 1 ]; then
    parallel=1
fi

#输出本次备份日志
function log()
{
	echo "back_time=$1 success=$2 back_type=$3 lsn_path=$4 bak_file=$5  error=$6"
	echo "back_time=$1 success=$2 back_type=$3 lsn_path=$4 bak_file=$5  error=$6" >>${log_file}
}
function get_databases()
{
    DATABASES="1"
#    if [ "$BACKUP_BIZ" == "1" ];then
#        DATABASES=$DATABASE_BIZ
#    fi
#    if [ "$BACKUP_STAT" == "1" ];then
#        DATABASES="$DATABASES,$DATABASE_STAT"
#    fi
#    DATABASES=${DATABASES##,}
#    if [ "$DATABASES" == "" ];then
#        ERROR_INFO="配置了不导出BIZ及STAT"
#    fi


}
# 根据时间删除指定路径下的log文件
function del_log_by_time(){
  dir=$1
  days=$2
  filePattern=$3
  dirFlag=$4
  if [ -d ${dir} ] && [ ${#dir} -gt 2 ]; then
     if [ "${dirFlag}" == "1" ];then
        find ${dir} -mtime +$((days-1)) -type d -name "${filePattern}" -exec rm -rf {} \;
     else
        find ${dir} -mtime +$((days-1)) -name "${filePattern}" -exec rm -f {} \;
     fi
  fi
}
#判断是否成功
function check_success()
{
	if [ $(tail -1 ${temp_file} 2>/dev/null |grep "completed OK!"|wc -l) -eq 1 ];then
		rm -rf ${temp_file}
		SUCCESS_FLAG=1
	else
		ERROR_INFO=$(tail -1 ${temp_file} 2>/dev/null)
		rm -rf ${temp_file}
		SUCCESS_FLAG=0
	fi
}

#获取上一次成功路径
function get_last_success_path()
{
    search_type=$1
    grep_str=""
    if [ "$search_type" == "" ];then
        grep_str="back_type=full"
    else
        grep_str="back_type=$search_type"
    fi
	LAST_SUCCESS_PATH=$(cat ${log_file} 2>/dev/null |grep "success=1"|grep -E "$grep_str" |awk '{print $4}' |awk -F= '{if($2!="-")print $2}'|tail -1)
	if [ "$LAST_SUCCESS_PATH" != "" ] && [ ! -d "${back_path}/$LAST_SUCCESS_PATH" ];then
        LAST_SUCCESS_PATH=""
	fi
}
#复制到多媒体路径
function move_to_media_server()
{
    to_move_file=$1

    if [ "$MEDIA_SERVER" == "localhost" ] || [ `ifconfig |grep "$MEDIA_SERVER "|wc -l` -gt 0 ];then
        ERROR_INFO="多媒体服务即本机,无需上传"
        return 0
    fi
    if [ "$MEDIA_SERVER" == "" ];then
        ERROR_INFO="未能获取多媒体服务器"
        return 0
    fi

    # 判断免密状态，无则不复制
    if [ `cat $SSH_USER_HOME/.ssh/known_hosts |grep -E "$MEDIA_SERVER |$MEDIA_SERVER," |wc -l` -lt 1 ];then
        ERROR_INFO="未设置免密登录到$MEDIA_SERVER"
        return 0
    fi



    hostname=$(hostname)
    ssh -p $SSH_PORT -o "StrictHostKeyChecking no" $SSH_USER@$MEDIA_SERVER "mkdir -p $back_path/${hostname}"
    scp -r -P $SSH_PORT $to_move_file $SSH_USER@[$MEDIA_SERVER]:$back_path/${hostname}/
	return 0
}

#加锁
function get_lock()
{
	back_type=$1
	if [ -e $lock_file ] ; then
		lock_time=$(stat -c %Y $lock_file)
		cur_time=$(date +%s)
		let second_diff=cur_time-lock_time
		if [ $second_diff -gt 7200 ];then
			rm -rf ${lock_file}
			touch ${lock_file}
			return 0
		fi
        log ${cur_date} 0 ${back_type} "-" "-" "其他备份任务正在运行"
        exit
    fi
    touch ${lock_file}
	return 0
}
function release_lock()
{
	rm -rf ${lock_file}
}
# 全量备份
function backup_full()
{
	get_lock full
	bak_file=full_${cur_date}.tar.gz
	echo "开始全量备份...."
	get_databases
    if [ "$DATABASES" == "" ];then
        SUCCESS_FLAG=0
	else
	    #超过9600s（3小时）自动停止备份进程
	    set +e
        timeout 9600 xtrabackup --backup --user=${DB_USER} --password=${DB_PWD} --host=127.0.0.1 --port=${DB_PORT} --extra-lsndir=${back_path}/full_${cur_date} --target-dir=${back_path}/full_db_${cur_date} --parallel=${parallel}  --compress --compress-threads=4 2>${temp_file}
        OVER_TIME_FLAG=$?
        if [ "$OVER_TIME_FLAG" = "124" ];then
            ERROR_INFO=备份超时
            SUCCESS_FLAG=0
        else
            check_success
        fi
        set -e
        if [ $SUCCESS_FLAG -eq 1 ];then
            tar -czf ${back_path}/full_${cur_date}.tar.gz -C ${back_path}/full_db_${cur_date} .
            rm -rf ${back_path}/full_db_${cur_date}
    #        xtrabackup --backup --user=${DB_USER} --password=${DB_PWD} --databases=${DATABASES} --host=127.0.0.1 --port=${DB_PORT} --extra-lsndir=${back_path}/full_${cur_date} --parallel=${parallel} --stream=tar --target-dir=${back_path} 2>${temp_file} |gzip -> ${back_path}/${bak_file}
        fi

	fi
	release_lock
    if [ $SUCCESS_FLAG -eq 1 ];then
        # 删除bin-log日志
        del_log_by_time "/egova/db/mysql" $bin_log_min_stay_days "mysql-bin.[0-9]*"
        # 清除30天前的full备份
        del_log_by_time "${back_path}" $full_backup_max_stay_days "full_*.tar.gz"
        del_log_by_time "${back_path}" $full_backup_max_stay_days "full_" 1
        move_to_media_server ${back_path}/${bak_file}
        move_to_media_server ${log_file}
        move_to_media_server ${temp_file}
        log ${cur_date} 1 full "full_${cur_date}" "${bak_file}" "${ERROR_INFO}"
    else
        log ${cur_date} 0 full "-" "-" "${ERROR_INFO}"
    fi
	echo "结束备份！"
}
# 增量备份
function backup_incr()
{
	get_lock incr
	get_last_success_path
	if [ "$LAST_SUCCESS_PATH" == "" ] || [ ! -d "${back_path}/$LAST_SUCCESS_PATH" ];then
                log ${cur_date} 0 incr "-" "-"  "不存在成功的备份,将执行全量备份"
		release_lock
		backup_full
		return
	fi
	echo "开始增量备份...."
	bak_file=incr_${cur_date}.xbstream
	get_databases
	if [ "$DATABASES" == "" ];then
     	SUCCESS_FLAG=0
	else
		#超过9600s（3小时）自动停止备份进程
		set +e
        timeout 9600 xtrabackup --backup --user=${DB_USER} --password=${DB_PWD} --port=${DB_PORT} --host=127.0.0.1 --extra-lsndir=${back_path}/incr_${cur_date}  --incremental-basedir=${back_path}/${LAST_SUCCESS_PATH} --stream=xbstream --compress --compress-threads=4 --target-dir=${back_path} > ${back_path}/${bak_file} 2>${temp_file}
        OVER_TIME_FLAG=$?
#	    xtrabackup --backup --user=${DB_USER} --password=${DB_PWD} --port=${DB_PORT} --databases=${DATABASES} --host=127.0.0.1 --extra-lsndir=${back_path}/incr_${cur_date} --incremental --incremental-basedir=${back_path}/${LAST_SUCCESS_PATH} --stream=xbstream --compress --target-dir=${back_path} > ${back_path}/${bak_file} 2>${temp_file}
        if [ "$OVER_TIME_FLAG" = "124" ];then
            ERROR_INFO=备份超时
            SUCCESS_FLAG=0
        else
            check_success
        fi
        set -e
	fi
	release_lock
    if [ $SUCCESS_FLAG -eq 1 ];then
        # 清除30天前的incr备份
          del_log_by_time "${back_path}" $incr_backup_max_stay_days "incr_*.xbstream"
          del_log_by_time "${back_path}" $incr_backup_max_stay_days "incr_" 1
          move_to_media_server ${back_path}/${bak_file}
          move_to_media_server ${log_file}
          log ${cur_date} 1 incr "incr_${cur_date}" "${bak_file}" "${ERROR_INFO}"
    else
            log ${cur_date} 0 incr "-" "-" "${ERROR_INFO}"
    fi
	echo "结束备份！"
}

function Usage()
{
	cat << EOF

Usage: 备份当前数据库

mysql-backup.sh [OPTIONS]
OPTIONS 可用参数如下:
-full,--full		全库备份
-incr,--incr		增量备份
--get-last-success=<full|incr|all> 获取上次成功路径
EOF

	exit
}
# 初始化参数
function Init_Options()
{
	OPT_FULL="0"
	OPT_INCR="1"
	OPT_GET_LAST_SUCCESS=""
	#获取参数
	while [ -n "$1" ]
	do
		case "$1" in
			-full|--full)OPT_FULL="1";shift 1;;
			-incr|--incr)OPT_INCR="1";shift 1;;
			--get-last-success=*)OPT_INCR="0";OPT_FULL=0;OPT_GET_LAST_SUCCESS=$(echo $1|awk -F= '{print $2}');shift 1;;
			--) break ;;
			*)	Usage; break;;
		esac
	done
}
function run()
{
    if [ "$SSH_PORT" == "" ];then
        SSH_PORT=22
    fi
    if [ "$DB_PORT" == "" ];then
        DB_PORT=3306
    fi

	Init_Options $@
	if [ "$OPT_GET_LAST_SUCCESS" == "full" ];then
	    get_last_success_path full
	    echo $LAST_SUCCESS_PATH
	    exit
	fi
	if [ "$OPT_GET_LAST_SUCCESS" == "incr" ];then
	    get_last_success_path incr
	    echo $LAST_SUCCESS_PATH
	    exit
	fi
	if [ "$OPT_GET_LAST_SUCCESS" == "all" ];then
	    get_last_success_path
	    echo $LAST_SUCCESS_PATH
	    exit
	fi
	if [ "$OPT_FULL" == "1" ];then
		backup_full
	elif [ "$OPT_INCR" == "1" ];then
		backup_incr
	fi
}
run $@
