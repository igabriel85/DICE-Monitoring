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
    echo "Starting dmon."
	#. $DIR/dmonEnv/bin/activate
        python dmon-agent.py > dmon-agent.log 2>&1 &
        echo $! > dmon-agent.pid
else
   echo "DMON-agent does not support commandline arguments!"
fi
