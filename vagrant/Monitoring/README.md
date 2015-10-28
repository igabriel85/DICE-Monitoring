
Simple Vagrant box with the DICE Monitoring Solution (D-Mon) and ELK stack for testing purposes:

* Installs the following libraries
  * python-dev
  * python-lxml
  * python-pip
  * git
* Installs python dependancies for D-Mon
  * see [requirements.txt](https://github.com/igabriel85/IeAT-DICE-Repository/blob/master/src/requirements.txt) 	 
* Installs D-Mon
  * default location is in /opt directory 	
* Elasticsearch
* Logstash collecting stats from:
  * collectd on CPU, memory, load and network stats on eth1
* Kibana
* Marvel ES monitoring
