#!/bin/bash

ARCH=`uname -s`
DIR=
RE='^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$'
RENR='^[0-9]+$'
currentDate=$(date "+%Y.%m.%d-%H.%M.%S")


if [ $ARCH == "Linux" ]; then
   DIR=`readlink -f "$( dirname "$0" )"`
elif [ $ARCH == "Darwin" ]; then
   CMD="import os, sys; print os.path.realpath(\"$( dirname $0 )\")"
   DIR=`python -c "$CMD"`
fi
if [[ $EUID != 0 ]]; then
    echo "Agent requires root privilages! Exiting"
    exit 1
fi

if [ ! -d "$DIR/pid" ]; then
  mkdir -p $DIR/pid/
fi

if [ ! -d "$DIR/log" ]; then
  mkdir $DIR/log
fi

if [ ! -d "$DIR/cert" ]; then
  mkdir $DIR/cert
fi

if [ ! -d "$DIR/lock" ]; then
  mkdir $DIR/lock
fi

if [ ! -f "$DIR/lock/agent.lock" ]; then
  apt-get install -y python-dev python-pip && pip install -r $DIR/requirements.txt
  echo "Installed on: $currentDate" >> $DIR/lock/agent.lock
fi

if [ $# -eq 0 ]; then
    echo "Starting dmon-agent"
	#. $DIR/dmonEnv/bin/activate
        python dmon-agent.py > $DIR/log/dmon-agent.out 2>&1 &
        echo $! > $DIR/pid/dmon-agent.pid
elif [[ $1 == "stop" ]]; then
    echo "Stopping dmon-agent"
    if [ ! -f $DIR/pid/dmon-agent.pid ]; then
        echo "No dmon-agent PID file found."
    fi
    kill -9 `cat $DIR/pid/dmon-agent.pid`
    killall -9 python #TODO: fix this, kill only dmon-logstash by pid
    rm -rf $DIR/pid/dmon-agent.pid
    echo "Stopped dmon-agent"
else
   echo "dmon-agent does not support this command line argument!"
fi
