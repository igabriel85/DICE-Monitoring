#!/usr/bin/env bash
# Bootstrap script for DICE Monitoring Elk stack
#TODO Legal stuff




# update package repo
apt-get update

# install collectd
apt-get install -y collectd
service collectd stop
rm -f /etc/collectd/collectd.conf
ln -sf /vagrant/collectd.conf /etc/collectd/collectd.conf
service collectd start

# install Apache for kibana3
#apt-get install -y apache2
#rm -rf /var/www
#mkdir /var/www
#chown www-data.www-data /var/www

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

cd /tmp
wget -q --no-check-certificate https://github.com/aglover/ubuntu-equip/raw/master/equip_java8.sh && bash equip_java8.sh

# install Elasticsearch 1.4.4
cd /opt
tar zxf /vagrant/elasticsearch-1.4.4.tar.gz
ln -sf elasticsearch-1.4.4 elasticsearch

#replace configuration files
rm -f /opt/elasticsearch/config/elastcisearch.yml
ln -sf /vagrant/elasticsearch.yml /opt/elasticsearch/config/elasticsearch.yml

# install Marvel (posibly obsolete afther further testing)
/opt/elasticsearch/bin/plugin -i elasticsearch/marvel/latest


# install Logstash
cd /opt
tar zxf /vagrant/logstash-1.5.2.tar.gz
ln -sf logstash-1.5.2 logstash

# fix permissions
cd /opt
chown -R vagrant.vagrant logstash* elasticsearch*

# call startup  script
su - vagrant -c /vagrant/start.sh
