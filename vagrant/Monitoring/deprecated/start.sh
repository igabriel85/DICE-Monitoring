#!/usr/bin/env bash

#Preliminary sartup changed to service in later versions
ES_HEAP_SIZE=4g /opt/elasticsearch/bin/elasticsearch -d > /dev/null 2>&1
/opt/logstash/bin/logstash agent -f /vagrant/logstash.conf > /dev/null 2>&1 &

echo "Marvel is running at http://localhost:9200/_plugin/marvel/"

sudo service kibana4 start
echo "Kibana is running on http://localhost:5601"
#echo "Kibana is running at http://localhost:8080/index.html#/dashboard/file/logstash.json"

echo "Restarting collectd ...."
sudo service collectd restart
echo "Done" 
