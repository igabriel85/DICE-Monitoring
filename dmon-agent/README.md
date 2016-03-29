# DICE Monitoring Agent (dmon-agent)

The DICE Monitoring Agent (dmon-agent) is a microservice designed to provide controll over different metrics collection components. In the current version these include:

* Collectd
* Logstash-forwarder
* jmxtrans

These components are completely controlled and even installed by the dmon-agent providing an easy and efficient way to configure these components. It is important to note that it is basicaly stateless. It does not use any database or files to store past interactions with users or other components. It is meant only to handle incomming request as efficiently as possible.

**NOTE:** Future releases may inlclude different metrics collecting components. ELK stack components such as the [Beats](https://www.elastic.co/products/beats) will be investigated.


##Change Log
* v0.0.4 - First alpha release
	 	
	  		 	
##Installation and Use

###Manual
Intalation is done by downloading the dmon-agent [archive](https://github.com/igabriel85/IeAT-DICE-Repository/releases/download/v0.0.4-dmon-agent/dmon-agent.tar.gz) and untaring it.

```
wget https://github.com/igabriel85/IeAT-DICE-Repository/releases/download/v0.0.4-dmon-agent/dmon-agent.tar.gz
```

```
tar -xvf dmon-agent.tar.gz
```

The agent can then be started using the _dmon-agent.sh_ bash script:

```
sudo ./dmon-agent.sh
```

This will check the current folder structure of the agent and create missing folders. If it is started for the first time it will check if the prerequiset are met. If they are not, it installs them.

Prerequisets include:

* __python-dev__
* __python-pip__

Required python modules are automaticaly installed using the _requrement.txt_ file.

Inorder to stop the python agent the user has to execute:

```
sudo ./dmon-agent.sh stop
```

###Using DICE Monitoring Controller (dmon-controller)
Monitoring agents can be installed using the dmon-controller by first registering the nodes into the monitoring platform. 

###Using DICE Deployment Service
__TODO__

##REST API Structure
**NOTE:** This is a preliminary structure of the REST API. It may be subject to changes!

`POST` `/agent/v1/bdp/<platform>`

This resource is used to generate the settings files necesary for monitoring both YARN and Spark platforms.

__Input__:

```json
{
  "GraphitePort": "5002",
  "LogstashIP": "<LS_IP>",
  "Period": "5"
}
```

_GraphitePort_ and _LogstashIP_ are used to define the endpoint used by Spark metrics system for metrics sent to a logstash server. The polling period can also be defined here.

`GET` `/agent/v1/check`

Returns the current status of both collectd and logstash forwarder.

__Output:__

```json
{
  "Collectd": 0,
  "LSF": 0
}
```

`POST` `/agent/v1/collectd`

This resource is used to set basic collectd parameters.

__Input:__

```json
{
	"LogstashIP": "<LS_IP>",
	"UDPPort": "<port>"
}
```

Sets logstash service IP and UDP listening port.

`GET` `agent/v1/conf/<auxComp>`

Returns the current configuration for collectd ot logstash-forwarder (lsf)

`POST` `/agent/v1/deploy`

`POST` `/agent/v1/jmx`

`GET` `/agent/v1/log`

`GET` `/agent/v1/log/component/<auxComp>`

`POST` `/agent/v1/lsf`

`GET` `/agent/v1/node`

`POST` `/agent/v1/start`

`POST` `/agent/v1/start/<auxComp>`

`POST` `/agent/v1/stop`

`POST` `/agent/v1/stop/<auxComp>`



