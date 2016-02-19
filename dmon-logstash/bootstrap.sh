#!/usr/bin/env bash
# Bootstrapping for dmon-logstash
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
# Install Java 8
echo "Starting deployment bootstrap for dmon-logstash"
echo "Installing Oracle Java 1.8 ...."
apt-get install python-software-properties -y
echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | sudo /usr/bin/debconf-set-selections
add-apt-repository ppa:webupd8team/java -y
apt-get update -y
apt-get install oracle-java8-installer -y
apt-get install ant -y

#set FQDN for HOST
HostIP=$(ifconfig eth0 2>/dev/null|awk '/inet addr:/ {print $2}'|sed 's/addr://')  #need to change to eth0 for non vagrant
echo "#Auto generated DICE Monitoring FQDN
$HostIP dice.dmon.logstash.internal dmon-logstash" >> /etc/hosts

#Setup Logrotate
echo "Setting up logrotate ..."

echo "/opt/IeAT-DICE-Repository/dmon-logstash/log/logstash.log{
size 20M
create 777 ubuntu ubuntu
rotate 4
}" >> /etc/logrotate.conf

cd /etc
logrotate -s /var/log/logstatus logrotate.conf

echo "Generating certificates for Logstash ..."
#HostIP=$(ifconfig eth0 2>/dev/null|awk '/inet addr:/ {print $2}'|sed 's/addr://') #need to change to eth0 for non vagrant
#backup open ssl
cp /etc/ssl/openssl.cnf /etc/ssl/openssl.backup
sed -i "/# Extensions for a typical CA/ a\subjectAltName = IP:$HostIP" /etc/ssl/openssl.cnf

#generate certificates

openssl req -config /etc/ssl/openssl.cnf -x509 -days 3650 -batch -nodes -newkey rsa:2048 -keyout /opt/IeAT-DICE-Repository/dmon-logstash/credentials/logstash.key -out /opt/IeAT-DICE-Repository/dmon-logstash/credentials/logstash.crt


echo "Installing Logstash 2.2.1"
cd /opt/IeAT-DICE-Repository/dmon-logstash
wget https://download.elastic.co/logstash/logstash/logstash-2.2.1.tar.gz
tar xvf logstash-2.2.1.tar.gz

mv logstash-2.2.1/* logstash
rm -rf logstash-2.2.1.tar.gz
rm -rf logstash-2.2.1


echo "Installing http_poller"
cd /opt/IeAT-DICE-Repository/dmon-logstash/logstash/bin

./plugin install http_poller

echo "Fixing permisions"
cd /opt/IeAT-DICE-Repository/dmon-logstash
chown -R ubuntu.ubuntu logstash
chown -R ubuntu.ubuntu /opt
mkdir -p /etc/logstash/conf.d

echo "dmon-logstash bootstrapping Complete!"