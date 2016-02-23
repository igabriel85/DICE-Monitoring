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

if [ $# -eq 0 ]; then
    echo "Starting dmon-logstash"
	#. $DIR/dmonEnv/bin/activate
        python dmon-logstash.py > log/dmon-logstash.out 2>&1 &
        echo $! > pid/dmon-logstash.pid
    echo "Finished"
elif [[ $1 == "stop" ]]; then
    if [ ! -f $DIR/pid/dmon-logstash.pid ]; then
        echo "No dmon-logstash PID file found."
    fi
    echo "Stopping dmon-logstash"
    kill -9 `cat $DIR/pid/dmon-logstash.pid`
    killall -9 python #TODO: fix this, kill only dmon-logstash by pid
    echo "Stopped dmon-logstash"

    echo "Stopping logstash"
    if [ ! -f $DIR/pid/logstash.pid ]; then
        echo "No Logstash PID file found."
    fi

    PID=`cat $DIR/pid/logstash.pid`
    kill -15  `cat $DIR/pid/logstash.pid`
    sleep 5
    kill -9 $(($PID+1)) #TODO: fix this, kill by child process
    echo "Stopped logstash server"
else
   echo "dmon-logstash does not support this command line argument!"
fi