#!/usr/bin/env bash
# Bootstrap script for DICE Experimental Cluster Deployment
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


# echo "Installing Oracle Java 1.8 ...."
# apt-get install python-software-properties -y
# echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | sudo /usr/bin/debconf-set-selections
# add-apt-repository ppa:webupd8team/java -y
# apt-get update -y
# apt-get install oracle-java8-installer -y
# apt-get install ant -y
# apt-get install wget -y
# apt-get install unzip -y


# echo "Changing swappiness ...."
# #Set Swappiness value to 10 instead of 60
# sysctl -w vm.swappiness=10
# cat /proc/sys/vm/swappiness



# echo "Installing oryx2...... "
# mkdir /opt/oryx
# cd /opt/oryx
# wget https://github.com/OryxProject/oryx/releases/download/oryx-2.0.0-beta-2/compute-classpath.sh
# wget https://github.com/OryxProject/oryx/releases/download/oryx-2.0.0-beta-2/oryx-run.sh
# chmod +x compute-classpath.sh 
# chmod +x oryx-run.sh
# #Currently set to beta 2

# wget https://github.com/OryxProject/oryx/releases/download/oryx-2.0.0-beta-2/oryx-batch-2.0.0-beta-2.jar
# wget https://github.com/OryxProject/oryx/releases/download/oryx-2.0.0-beta-2/oryx-serving-2.0.0-beta-2.jar
# wget https://github.com/OryxProject/oryx/releases/download/oryx-2.0.0-beta-2/oryx-speed-2.0.0-beta-2.jar


# #Copy example conf
# wget https://github.com/OryxProject/oryx/blob/master/app/conf/als-example.conf
# mv als-example.conf oryx.conf

# #download example dataset
# wget http://files.grouplens.org/datasets/movielens/ml-100k.zip
# unzip ml-100k.zip
# cd ml-100k
# #change u.data to csv format
# tr '\t' ',' < u.data > data.csv
# echo "Fixing owner ..."
# chown -R ubuntu.ubuntu /opt

echo "Modifying hosts file ...."
#edit hosts file
echo "#Auto generated DICE Cluster FQDN
109.231.126.25 dice.hdp.mng.internal 109-231-126-25
109.231.121.200 dice.hdp.w1.internal 109-231-121-200
109.231.126.27 dice.hdp.w2.internal 109-231-126-27
109.231.126.18 dice.hdp.w3.internal 109-231-126-18" >> /etc/hosts
