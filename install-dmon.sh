#!/usr/bin/env bash
# Install script for DICE Monitoring (D-Mon)
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

apt-get update
apt-get install python-dev -y
apt-get install python-lxml -y
apt-get install python-pip -y
apt-get install git -y
apt-get isntall htop -y

cd /opt

git clone https://github.com/igabriel85/IeAT-DICE-Repository.git

chown -R ubuntu.ubuntu /opt

pip install -r /opt/IeAT-DICE-Repository/src/requirements.txt