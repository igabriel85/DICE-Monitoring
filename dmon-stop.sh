#!/bin/bash
ARCH=`uname -s`
DIR=

if [ $ARCH == "Linux" ]; then
   DIR=`readlink -f "$( dirname "$0" )"`
elif [ $ARCH == "Darwin" ]; then
   CMD="import os, sys; print os.path.realpath(\"$( dirname $0 )\")"
   DIR=`python -c "$CMD"`
fi

echo "Stopping Kibana ..."
kill -9  `cat $DIR/src/pid/kibana.pid`
echo "Stopping Logstash Server ..."
kill -9  `cat $DIR/src/pid/logstash.pid`
echo "Stopping ElasticSearch ..."
kill -9  `cat $DIR/src/pid/elasticsearch.pid`

echo "Stopping D-Mon"
killall -9 python #TODO need more elegant solution

echo "D-Mon Stopped"