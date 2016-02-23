#!/bin/bash

ARCH=`uname -s`
DIR=
RE='^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$'
RENR='^[0-9]+$'

if [ $ARCH == "Linux" ]; then
   DIR=`readlink -f "$( dirname "$0" )"`
elif [ $ARCH == "Darwin" ]; then
   CMD="import os, sys; print os.path.realpath(\"$( dirname $0 )\")"
   DIR=`python -c "$CMD"`
fi

if [ $# -eq 0 ]; then
    echo "Starting dmon-agent"
	#. $DIR/dmonEnv/bin/activate
        python dmon-agent.py > dmon-agent.log 2>&1 &
        echo $! > pid/dmon-agent.pid
elif [[ $1 == "stop" ]]; then
    echo "Stopping dmon-agent"
    if [ ! -f $DIR/pid/dmon-agent.pid ]; then
        echo "No dmon-agent PID file found."
    fi
    kill -9 `cat $DIR/pid/dmon-agent.pid`
    killall -9 python #TODO: fix this, kill only dmon-logstash by pid
    echo "Stopped dmon-agent"
else
   echo "dmon-agent does not support this command line argument!"
fi
