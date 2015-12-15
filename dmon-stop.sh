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
if [ ! -f $DIR/src/pid/kibana.pid ]; then
	echo "No Kibana instance to stop."
else
	kill -15  `cat $DIR/src/pid/kibana.pid`
	echo "Kibana Stopped!"
fi

echo "Stopping Logstash Server ..."
if [ ! -f $DIR/src/pid/logstash.pid ]; then
	echo "No Logstash instance to stop."
else
	kill -15  `cat $DIR/src/pid/logstash.pid`
	echo "Logstash Stopped!"
fi

echo "Stopping ElasticSearch ..."
if [ ! -f $DIR/src/pid/elasticsearch.pid ]; then
	echo "No ElasticSearch instance to stop."
else
	kill -15  `cat $DIR/src/pid/elasticsearch.pid`
	echo "ElasticSearch Stopped!"
fi

echo "Stopping D-Mon"
killall -15 python #TODO need more elegant solution

echo "D-Mon Stopped!"