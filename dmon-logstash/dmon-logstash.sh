#!/bin/bash

ARCH=`uname -s`
DIR=
PID=
RE='^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$'
RENR='^[0-9]+$'


if [ $ARCH == "Linux" ]; then
   DIR=`readlink -f "$( dirname "$0" )"`
elif [ $ARCH == "Darwin" ]; then
   CMD="import os, sys; print os.path.realpath(\"$( dirname $0 )\")"
   DIR=`python -c "$CMD"`
fi

if [ ! -d "$DIR/pid" ]; then
    mkdir -p $DIR/pid/
fi

if [ ! -d "$DIR/log" ]; then
    mkdir $DIR/log
fi

if [ ! -d "$DIR/credentials" ]; then
    mkdir $DIR/credentials
fi

if [ ! -d "$DIR/lock" ]; then
    mkdir $DIR/lock
fi

if [ ! -d "$DIR/config" ]; then
    mkdir $DIR/config
fi

if [ ! -f "$DIR/lock/dmon-logstash.lock" ]; then
  echo "Basic pre-requisets seem to be missing, begining installation"
  if [[ $EUID != 0 ]]; then
    echo "Installation requires root privilages!"
    exit 1
  fi
  apt-get install -y python-dev python-pip && pip install -r $DIR/requirements.txt
  echo "Installed on: $currentDate" >> $DIR/lock/dmon-logstash.lock
  echo "Done installing prerequisets please restart without root privilages!"
  exit 0
fi

if [[ $EUID -ne 0 ]]; then
    echo "Warning root not recommended after installation"
    exit 1  #TODO: delete not to enforce warning
fi

if [ $# -eq 0 ]; then
    echo "Starting dmon-logstash"
	#. $DIR/dmonEnv/bin/activate
        python dmon-logstash.py > log/dmon-logstash.out 2>&1 &
        echo $! > $DIR/pid/dmon-logstash.pid
    echo "Finished"
elif [[ $1 == "stop" ]]; then
    if [ ! -f $DIR/pid/dmon-logstash.pid ]; then
        echo "No dmon-logstash PID file found."
    fi
    echo "Stopping dmon-logstash"
    kill -9 `cat $DIR/pid/dmon-logstash.pid`
    killall -9 python #TODO: fix this, kill only dmon-logstash by pid
    rm -rf $DIR/pid/dmon-logstash.pid
    echo "Stopped dmon-logstash"

    echo "Stopping logstash"
    if [ ! -f $DIR/pid/logstash.pid ]; then
        echo "No Logstash PID file found."
    fi

    PID=`cat $DIR/pid/logstash.pid`
    kill -15  `cat $DIR/pid/logstash.pid`
    sleep 5
    kill -9 $(($PID+1)) #TODO: fix this, kill by child process
    rm -rf $DIR/pid/logstash.pid
    echo "Stopped logstash server"
else
   echo "dmon-logstash does not support this command line argument!"
fi