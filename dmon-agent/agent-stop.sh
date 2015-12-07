#!/bin/bash
ARCH=`uname -s`
DIR=

if [ $ARCH == "Linux" ]; then
   DIR=`readlink -f "$( dirname "$0" )"`
elif [ $ARCH == "Darwin" ]; then
   CMD="import os, sys; print os.path.realpath(\"$( dirname $0 )\")"
   DIR=`python -c "$CMD"`
fi

echo "Stopping DMON-agent ..."
kill -9  `cat dmon-agent.pid`

echo "DMON-agent Stopped"
echo "Exiting"