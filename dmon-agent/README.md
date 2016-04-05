# DICE Monitoring Agent (dmon-agent)

The DICE Monitoring Agent (dmon-agent) is a microservice designed to provide controll over different metrics collection components. In the current version these include:

* Collectd
* Logstash-forwarder
* jmxtrans

These components are completely controlled and even installed by the dmon-agent providing an easy and efficient way to configure these components. It is important to note that it is basically stateless. It does not use any database or files to store past interactions with users or other services/components. It is meant only to handle incoming request as efficiently as possible.

**NOTE:** Future releases may include different metrics collecting components. ELK stack components such as the [Beats](https://www.elastic.co/products/beats) will be investigated.


##Change Log
* v0.0.4 - First alpha release
	 	
	  		 	
##Installation and Use

###Manual
Intallation is done by downloading the dmon-agent [archive](https://github.com/igabriel85/IeAT-DICE-Repository/releases/download/v0.0.4-dmon-agent/dmon-agent.tar.gz) and untaring it.

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

* python-dev
* python-pip
* contents of [requirements.txt](https://github.com/igabriel85/IeAT-DICE-Repository/blob/master/dmon-agent/requirements.txt)

Required python modules are automaticaly installed using the _requrement.txt_ file.

Inorder to stop the python agent the user has to execute:

```
sudo ./dmon-agent.sh stop
```

###Using DICE Monitoring Controller (dmon-controller)
Monitoring agents can be installed using the dmon-controller by first registering the nodes into the monitoring platform. 

First we can  check if monitoring agents are alrady installed on the registered nodes using:

`GET` `/dmon/v2/overlord/aux/agent`

Then we can install _dmon-agents_ on all registered nodes which don't yet have the agent installed.

`POST` `/dmon/v2/overlord/aux/agent`

We can also check the current status of the agent. By this we mean if the agent is installed but not started and the current status of collectd and logstash-forwarder.

`GET` `/dmon/v2/overlord/aux/deploy`

Which returns:

```json
{
  "Aux Status": [
    {
      "Collectd": "<cd_status>",
      "LSF": "<lsf_status>",
      "Monitored": "<true|false>",
      "NodeFQDN": "<node_fqdn>",
      "NodeIP": "<node_ip>"
    }
  ]
}
```

**Note:** Monitored is set to _true_ of dmon-agent is detected on that node otherwise it is set to _false_.

Whe then can deploy configurations to allnodes (config based on their roles) or on specific nodes identified by their _FQDN_.

For all nodes use:

`POST` `/dmon/v2/overlord/aux/deploy`

For specific nodes use:

`POST` `/dmon/v2/overlord/aux/deploy/<auxComp>/<nodeFQDN>`



###Using DICE Deployment Service

**NOTE:** Not schedueled for M12.

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

Sets the roles available on this node. These roles represent big data services that are installed and started on this node.

__Inptu:__

```json
{
  "roles": [
    "hdfs", 
    "spark"
  ]
}
```

These defined roles are used to decide what data collectors are installed and configured. For example for _hdfs_ and _yarn_ it is required to install both collectd and logstash-forwarder. In the case of Storm only collectd is required.

`POST` `/agent/v1/jmx`
This resource is used to generate jmxtrans configuration.

**Note:** Future versions may ommit the use of jmxtrans and use GenericJMX or FastJMX plugin from Collectd.

`GET` `/agent/v1/log`

Return the log of _dmon-agent_.  

`GET` `/agent/v1/log/component/<auxComp>`

Returns logs of collectd or logstash-forwarder components.

`POST` `/agent/v1/lsf`
Generates the configuration for logstash-forwarder component. 

__Input:__
```json
{
  "LogstashIP": "<logstash_port>",
  "LumberjackPort": "<port>"
}
```

**Note:** Current version requires the logstash server certificate to be present in a specific location. If it is not found it will return a warning and normal functionin of the component is imposible.


`GET` `/agent/v1/node`

Returns hardware and OS information about the current node. 

__Output:__

```json
{
  "Machine": "<node_arch>",
  "Node": "<node_name>",
  "Processor": "<processor_id>",
  "Release": "<release>",
  "System": "<os_name>",
  "Version": "<kernel_version_information>"
}
```


`POST` `/agent/v1/start`

Start all components. It uses the last generated configuration file for each components. If none exists it returns a warning.

`POST` `/agent/v1/start/<auxComp>`

Starts a specific component defined by _auxComp_. It uses the last configuration file generated. If non exists it returns a warning.

`POST` `/agent/v1/stop`

Stops all components. 

`POST` `/agent/v1/stop/<auxComp>`

Stops a specific component defined by _auxComp_.



