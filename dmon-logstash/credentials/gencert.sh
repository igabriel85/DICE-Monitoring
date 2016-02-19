#!/usr/bin/env bash
# Create Certificate for dmon-logstash
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
echo "Generating certificates for Logstash ..."
#HostIP=$(ifconfig eth0 2>/dev/null|awk '/inet addr:/ {print $2}'|sed 's/addr://') #need to change to eth0 for non vagrant
#backup open ssl
cp /etc/ssl/openssl.cnf /etc/ssl/openssl.backup
sed -i "/# Extensions for a typical CA/ a\subjectAltName = IP:$HostIP" /etc/ssl/openssl.cnf

#generate certificates

openssl req -config /etc/ssl/openssl.cnf -x509 -days 3650 -batch -nodes -newkey rsa:2048 -keyout /opt/IeAT-DICE-Repository/dmon-logstash/credentials/logstash.key -out /opt/IeAT-DICE-Repository/dmon-logstash/credentials/logstash.crt
