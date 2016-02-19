#!/usr/bin/env bash
# Install logstash and http_poller plugin
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

echo "Installing Logstash 2.2.1"
cd /opt/IeAT-DICE-Repository/dmon-logstash
wget https://download.elastic.co/logstash/logstash/logstash-2.2.1.tar.gz
tar xvf logstash-2.2.1.tar.gz

mv logstash-2.2.1/* logstash
rm -rf logstash-2.2.1


echo "Installing http_poller"
cd /opt/IeAT-DICE-Repository/dmon-logstash/logstash/bin

./plugin install http_poller

echo "Installation Complete!"