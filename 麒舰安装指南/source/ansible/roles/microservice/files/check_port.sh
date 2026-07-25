#!/bin/bash

if [ $# -ne 1 ];then
  echo "Invalid input! Usage: check_port.sh port"
  exit -1
fi

port=$1

function check_port() {
  port=$1
  flag=0
  while [ $flag -eq 0 ]
  do
    check=`netstat -anp | grep "$port " | grep LISTEN | wc -l`
    if [ $check -eq 0 ];then
        flag=1
    else
        let "port=port+1"
    fi
    sleep 1
  done
}

check_port $port

echo $port
