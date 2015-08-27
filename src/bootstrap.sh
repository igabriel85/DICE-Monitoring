#!/usr/bin/env bash
# Bootstrap script for DICE Monitoring Core Componets
#
#Copyright 2015, Institute e-Austria, Timisoara, Romania
#    http://www.ieat.ro/
#Developers:
# * Gabriel Iuhasz, iuhasz.gabriel@info.uvt.ro
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at:
#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


#get kibana4 and  install
#TODO Replace wget

cd ~/ 
wget https://download.elasticsearch.org/kibana/kibana/kibana-4.0.1-linux-x64.tar.gz
tar xvf kibana-4.0.1-linux-x64.tar.gz
mkdir -p /opt/kibana
cp -R ~/kibana-4.0.1-linux-x64/* /opt/kibana/
cd /etc/init.d && sudo wget https://gist.githubusercontent.com/thisismitch/8b15ac909aed214ad04a/raw/bce61d85643c2dcdfbc2728c55a41dab444dca20/kibana4
chmod +x /etc/init.d/kibana4
update-rc.d kibana4 defaults 96 9

# install Java 8
#sudo apt-get install python-software-properties -y
#sudo echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | sudo /usr/bin/debconf-set-selections
#sudo add-apt-repository ppa:webupd8team/java -y
#sudo apt-get update -y
#sudo apt-get install oracle-java8-installer -y
#sudo apt-get install ant -y
# TODO Replace wget command

#cd /tmp
#wget -q --no-check-certificate https://github.com/aglover/ubuntu-equip/raw/master/equip_java8.sh && bash equip_java8.sh

# install Elasticsearch 1.4.4
cd /opt
wget https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch-1.4.4.tar.gz
tar zxf elasticsearch-1.4.4.tar.gz
ln -sf elasticsearch-1.4.4 elasticsearch

#delete config file
rm -f /opt/elasticsearch/config/elastcisearch.yml
#ln -sf /vagrant/elasticsearch.yml /opt/elasticsearch/config/elasticsearch.yml

# install Marvel (posibly obsolete afther further testing)
/opt/elasticsearch/bin/plugin -i elasticsearch/marvel/latest


# install Logstash
cd /opt
wget https://download.elastic.co/logstash/logstash/logstash-1.5.4.tar.gz
tar zxf logstash-1.5.4.tar.gz
ln -sf logstash-1.5.4 logstash

# fix permissions
cd /opt
chown -R ubuntu.ubuntu logstash* elasticsearch*


