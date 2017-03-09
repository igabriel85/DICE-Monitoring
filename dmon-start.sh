#!/bin/bash
ARCH=`uname -s`
DIR=
RE='^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$'
RENR='^[0-9]+$'
export ES_HEAP_SIZE=4g
export LS_HEAP_SIZE=1024m
export ES_USE_GC_LOGGING=yes
export LS_VERSION="2.2.0"
export KB_VERSION="4.3.1"
export DMON_TIMEOUT=5
#DMON Agent archive location
export DMON_AGENT="https://github.com/igabriel85/IeAT-DICE-Repository/releases/download/v0.0.4-dmon-agent/dmon-agent.tar.gz"
#Logging can be set to INFO, WARN or ERROR
export DMON_LOGGING="INFO"

if [ $ARCH == "Linux" ]; then
   DIR=`readlink -f "$( dirname "$0" )"`
elif [ $ARCH == "Darwin" ]; then
   CMD="import os, sys; print os.path.realpath(\"$( dirname $0 )\")"
   DIR=`python -c "$CMD"`
fi



if [ $# -eq 0 ]; then
    echo "Starting default."
	. $DIR/dmonEnv/bin/activate
        python $DIR/src/start.py
else
   #. $DIR/dmonEnv/bin/activate
	python $DIR/src/start.py $1 $2 $3 > src/logs/dmon.log 2>&1 &
fi
