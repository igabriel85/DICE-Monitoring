# pyDMON - DICE Monitoring Platform

It is designed as a web service that serves as the main interface (REST API) and controlling agent for the other monitoring components.
These components include:

* ElasticsSearch
* Logstash Server
* kibana
* collectd
* logstash-forwarder
* jmxtrans


It is designed for:

* **first design choice** - something

**TODO**

##Changelog

**NOTE:** Changelog moved to separate file. Plese follow this [link](). 	
	  		 	

##Installation

The installation is largely based on bash scripts. Future versions will most likely be based on chef recepies and/or deb or rpm packages. There are 2 types of installation procedures currently supported.

### Cloud
This type of installation is for client/cloud deployment. It will install all python modules as well as the ELK (ElasticSearch, logstash and kibana 4) stack. Only local  deployment  is currently supported.

* Download the installation script to the desired host and make it executable

```
wget https://github.com/igabriel85/IeAT-DICE-Repository/releases/download/v0.1-install/install-dmon.sh && sudo chmod +x install-dmon.sh

```

    

* After which execute the installation script

```
sudo ./install-dmon.sh
``` 

**Note**: This script will clone the D-Mon repository into */opt* and change the owner of this directory to _ubuntu.ubuntu_!

* Next co inside the cloned repository and run

```
sudo ./dmon-start.sh -i -p 5001
```
The '-i' flag will install all Core components of the monitoring platform (i.e. ELK) as well as setting the appropriate permissions for all folders and files. The '-p' flag designates the port on which D-Mon will be deployed.

* In order deploy D-Mon localy execute:

```
./dmon-start.sh -l -p 5001
``` 
The '-l' flag signas the service that this is a local deployment of both ElasticSearch and Logstash server. The service will start logging into stdout.

**Note**: Do not execute this command as root! It will corrupt the previously set permissions and the service will be inoperable.

If you do not wish to create a local deployment run the command.

```
./dmon-start.sh -p 5001
```

This will only start the service and not load the local deployment module.

**Note**: By default all the IP is set to _0.0.0.0_. This can be change using the '-e' flag.

**Observation**: Kibana 4 service is started during the bootstrapping process. You can check the service by running:

```
sudo service kibana4 status
```

For starting toping the service replace the _status_ command with _start_, _stop_ or _restart_.


### Vagrant

There are two vagrant files in this repository. The [first](https://github.com/igabriel85/IeAT-DICE-Repository/tree/master/Vagrant%20CDH%20Cluster) one creates a deployment of 4 VM on which it automatically installs the Cloudera Manager  suite. 

The [second](https://github.com/igabriel85/IeAT-DICE-Repository/tree/master/Monitoring) script installs D-Mon as well as the ELK stack, essentially taking the place of the '-i' flag in the above mentioned instructions. The procedure for creating a local deployment of D-Mon is the same as before.

### Chef
* TODO not scheduled for M18


##REST API Structure
**NOTE:** This is a preliminary structure of the REST API. It may be subject to changes!

There are two main components from this API: 

* First we have the management and deployment/provisioning component called **Overlord** (Monitoring Management API).
 * It is responsible for the deployment and management of the Monitoring Core components: ElasticSearch, Logstash Server and Kibana.
 * It is also responsible for the auxiliary component management and deployment. These include: Collectd, Logstash-forwarder
* Second, we have the interface used by other applications to query the DataWarehouse represented by ElasticSearch. This component is called **Observer**.
 * It is responsible for the returning of monitoring metrics in the form of: CSV, JSON, simple output. 


**NOTE**: Future versions will include authentication for the _Overlord_ resources. 

### Overlord (Monitoring Management API)

The Overlord is structured into two components:

* **Monitoring Core** represented by: ElasticSearch, LogstashServer and Kibana
* **Monitoring Auxiliary** represented by: Collectd, Logstash-Forwarder

-
#### Monitoring Core

`GET` `/v1/log`

Return the log of dmon. It contains information about the last requests and the IPs from which they originated as well as status information of variouse sub components.

The dmon internal logging system lists 3 types of messages. __INFO__ messages represent debug level information, __WARNING__ is for handeled exceptions and finaly __ERROR__ for caught errors.

`GET` `/v1/overlord`

Returns information regarding the current version of the Monitoring Platform.

`GET` `/v1/overlord/framework`

Returns the currently supported frameworks.

```json
{
	Supported Frameworks:[<list_of_frameoworks>]
}
```

`GET` `/v1/overlord/framework/{fwork}`

Returns the metrics configuration file for big data technologies. The response will have the file mime-type encoded. For HDFS,Yarn and Spark it is set to __'text/x-java-properties'__ while for Storm it is __'text/yaml'__.

`PUT` `/v1/overlord/application/{appID}`

Registers an application with DMON and creates a unique tag for the monitored data. The tag is defined by _appID_.

**NOTE**: Scheduled for future versions!


`POST` `/v1/overlord/core`

Deploys all monitoring core components provided they have values preset hosts. If not it deploys all components locally with default settings.

**NOTE**: Currently the '-l' flag of the start script _dmon-start.sh_ does the same as the later option. Schedueled for M18.


`GET` `/v1/overlord/core/database`

Return the current internal state of Dmon in the form of an sqlite2 database. The response has _application/x-sqlite3_ mimetype.

`PUT` `/v1/overlord/core/database`

Can submit a new version of the internal database to dmon. It will replace the current states with new states. The old states are backed up before applying the new ones. Database should take the form of sqlite3 database file and sent unsing the _application/x-sqlite3_ mimetype.


`GET` `/v1/overlord/core/status`

Returns the current status of the Monitoring platform status.

```json
{
    "ElasticSearch":{
      "Status":"<HTTP_CODE>",
      "Name":"<NAME>",
      "ClusterName":"<CLUSTER_NAME>",
      "version":{
        "number":"<ES_VERSION>",
        "BuildHash":"<HASH>",
        "BuildTimestamp":"<TIMESTAMP>",
        "BuildSnapshot":"<BOOL>",
        "LuceneVersion":"<LC_VERSION>"
      		}
      },
    "Logstash":{
      "Status":"<HTTP_CODE>",
      "Version":"<VNUMBER>"
      },
    "Kibana":{
      "Status":"<HTTP_CODE>",
      "Version":"<VNUMBER>"
    }
}
```

**NOTE**: Only works for local deployments. It returns the current state of local ElasticSearch, Logstash server and Kibana status information.
***

`POST` `/v1/overlord/detect/storm`

Tries do detect if the current registered nodes have a valid storm deployment. It will first test if there are any nodes that have a Storm endpoint and port. If this fails it starts to scan all registered nodes. If it finds the endpoint it sets the first topology as the one to be monitored. Then, it sets all configurations necesary for storm monitoring automatically.

***

`GET` `/v1/overlord/nodes`
 
 Returns the current monitored nodes list. It is the same as `/v1/observer/chef`.
 
```json
{
    "Nodes":[
      {"<NodeFQDN1>":"NodeIP1"},
      {"<NodeFQDN2>":"NodeIP2"},
      {"<NodeFQDNn>":"NodeIPn"}
      ]
  }
```
***

`PUT` `/v1/overlord/nodes`

Includes the given nodes into the monitored node pools. In essence nodes are represented as a list of dictionaries. Thus, it is possible to register one to many nodes at the same time. It is possible to assign different user names and passwords to each node.

Input:

```json
{
    "Nodes":[
      
        {
          "NodeName":"<NodeFQDN1>",
          "NodeIP":"<IP>",
          "key":"<keyName|null>",
          "username":"<uname|null>",
          "password":"<pass|null>"
      },
        {
          "NodeName":"<NodeFQDNn>",
          "NodeIP":"<IP>",
          "key":"<keyName|null>",
          "username":"<uname|null>",
          "password":"<pass|null>"
        }
    ]
}
```
**NOTE**: Only username and key authentication is currently supported. There is a facility to use public/private key authentication which is currently undergoing testing.

***

`POST` `/v1/overlord/nodes`

Bootstrap of all non monitored nodes. Installs, configures and start collectd and logstash-forwarder on them. This feature is not recommended for testing, the usage of separate commands is preffered in order to detect network failures.

**NOTE**: Meant for M24. Define one json to completely populate and set up dmon-controller. It can be then used to save and share internal state by sending the json between controller instances.
***

`GET` `/v1/overlord/nodes/roles`

Returns the roles currently held by each computational node.

```json
{
  "Nodes": [
    {
      "dice.cdh5.mng.internal": [
        "storm",
        "spark"
      ]
    },
    {
      "dice.cdh5.w1.internal": [
        "unknown"
      ]
    },
    {
      "dice.cdh5.w2.internal": [
        "yarn",
        "spark",
        "storm"
      ]
    },
    {
      "dice.cdh5.w3.internal": [
        "unknown"
      ]
    }
  ]
}
```

If the node has an unknown service installed, or the roles are not specified the type is set to __unknown__.


`PUT` `/v1/overlord/nodes/roles`

Modifies the roles of each nodes.

__Input:__

```json
{
  "Nodes": [
    {
      "NodeName": "<nodeFQDN>",
      "Roles": [
        "yarn"
      ]
    }
```


`POST` `/v1/overlord/nodes/roles`

Generates metrics configuration files for each role assigned to a node and uploads it to the required directory. It returns a list of all nodes to which a configuration of a certain type (i.e. yarn, spark, storm etc) has been uploaded.

```json
{
	'Status':{
		'yarn':[list_of_yarn_nodes],
		'spark':[list_of_spark_nodes],
		'storm':[list_of_storm_nodes],
		'unknown':[list_of_unknown_nodes]
		}
}
```



**NOTE:** The directory structure is based on the Vanilla and Cloudera distribution of HDFS, Yarn and Spark. Custom installtions are not yet supported.
As __yarn__ and __HDFS__ have the same metrics system their tags (i.e. hdfs and yarn) are interchangable in the context of D-Mon.



`GET` `/v1/overlord/nodes/{nodeFQDN}`

Returns information of a particular monitored node identified by _nodeFQDN_.

Response:

```json
{
      "NodeName":"nodeFQDN",
      "Status":"<online|offline>",
      "IP":"<NodeIP>",
      "OS":"<Operating_Systen>",
      "key":"<keyName|null>",
      "username":"<uname|null>",
      "password":"<pass|null>",
      "chefclient":"<True|False>",
      "Roles":"[listofroles]"
}
```

**FUTURE Version**: A more fine grained node status will be implemented. Currently it is boolean - online/offline. The last three elements  are not implemented. These are scheduled for future versions.


***

`PUT` `/v1/overlord/nodes/{NodeFQDN}`

Changes the current information of a given node. Node FQDN  may not change from one version to another. 

Input:

```json
{
  "NodeName":"<nodeFQDN>",
  "IP":"<NodeIP>",
  "OS":"<Operating_Systen>",
  "Key":"<keyName|null>",
  "Username":"<uname|null>",
  "Password":"<pass|null>",
  "LogstashInstance": "<ip_logstash>"
}
```

***

`POST` `/v1/overlord/nodes/{NodeFQDN}`

Bootstraps specified node. 

**NOTE**: Possible duplication with `../aux/..` branch. DEPRECATED.
***

`DELETE` `/v1/overlord/nodes/{nodeFQDN}`

Stops all auxiliary monitoring components associated with a particular node.

**NOTE**: This does not delete the nodes nor the configurations it simply stops collectd and logstash-forwarder on the selected nodes. DEPRECATED.


`PUT` `/v1/overlord/nodes/{nodeFQDN}/roles`

Defines the roles each node has inside the cluster.

Input:

```json
{
	"Roles":"[list_of_roles]"
}
```


`POST` `/v1/overlord/nodes/{nodeFQDN}/roles`

Redeploys metrics configuration for a specific node based on the roles assigned to it.

**FUTURE WORK:** This feature will be developed for future versions.

***
`DELETE` `/v1/overlord/nodes/{nodeFQDN}/purge`

This resource deletes auxiliary tools from the given node. It also removes all setting from D-Mon. This process is **irreversible**.
***
`GET` `/v1/overlord/core/es`

Return a list of current hosts  comprising the ES cluster core components. The first registered host is set as the default master node. All subsequent nodes are set as workers.

```json
{
  "ES Instances": [
    {
      "DataNode": true,
      "ESClusterName": "diceMonit",
      "ESCoreDebug": "0",
      "ESCoreHeap": "3g",
      "FieldDataCacheExpire": "6h",
      "FieldDataCacheFilterExpires": "6h",
      "FieldDataCacheFilterSize": "20%",
      "FieldDataCacheSize": "20%",
      "HostFQDN": "dice.cdh5.dmon.internal",
      "IP": "127.0.0.1",
      "IndexBufferSize": "30%",
      "MasterNode": true,
      "MinIndexBufferSize": "96mb",
      "MinShardIndexBufferSize": "12mb",
      "NodeName": "esCoreMaster",
      "NodePort": 9200,
      "NumOfReplicas": 1,
      "NumOfShards": 5,
      "OS": "ubuntu",
      "PID": 2531,
      "Status": "Running"
    }
  ]
}

```

**NOTE:** 

`POST` `/v1/overlord/core/es` 

Generates and applies the new configuration options of the ES Core components. During this request the new configuration will be generated.

**NOTE**: If configuration is unchanged ES Core will not be restarted!
It is possible to deploy the monitoring platform on different hosts than elasticsearch provided that the FQDN or IP is provided.



**FUTURE Work**: This process needs more streamlining. It is recommended to use only local deployments for this version.

***

`GET` `/v1/overlord/core/es/config`

Returns the current configuration file of ElasticSearch in the form of a YAML file.



**NOTE**: The first registered ElasticSearch information will be set by default to be the master node.

***

`PUT` `/v1/overlord/core/es/config`

Changes the current configuration options for the Elasticsearch instance defined by it's FQDN and IP.

Input:

```json
{
  {
  "DataNode": true,
  "ESClusterName": "string",
  "ESCoreDebug": 1,
  "ESCoreHeap": "4g",
  "FieldDataCacheExpires": "6h",
  "FieldDataCacheFilterExpires": "6h",
  "FieldDataCacheFilterSize": "20%",
  "FieldDataCacheSize": "20%",
  "HostFQDN": "string",
  "IP": "string",
  "IndexBufferSize": "30%",
  "MasterNode": true,
  "MinIndexBufferSize": "96mb",
  "MinShardIndexBufferSize": "12mb",
  "NodeName": "string",
  "NodePort": 9200,
  "NumOfReplicas": 0,
  "NumOfShards": 1,
  "OS": "unknown"
 }
}

```

**NOTE**: The new configuration will **not** be generated at this step. Currently only ESClusterName, HostFQDN, IP, NodeName, NodePort are required. This will be probably changed in future versions.
***

`GET` `/v1/overlord/core/es/status/<intComp>/property/<intProp>`

Returns diagnostic data about the master elasticsearch instance.

`DELETE` `/v1/overlord/core/es/<hostFQDN>`

Stops the ElasticSearch instance on a given host and removes all configuration data from DMON.


***

`POST` `/v1/overlord/core/es/<hostFQDN>/start`

Start the es instance on the host identified by _hostFQDN_. It uses the last good generated es configuration.

`POST` `/v1/overlord/core/es/<hostFQDN>/stop`

Stops the es instance on the host identified by _hostFQDN_. 


`POST` `/v1/overlord/core/halt`

Stops all core components on every node.

**NOTE:** Future release.


`GET` `/v1/overlord/core/es/<hostFQDN>/status`

Returns the current status (Running, Stopped, Unknown) and PID of the es instance on the host identified by _hostFQDN_.

***
 
`GET` `/v1/overlord/core/ls`

Returns the current status of all logstash server instances registered with D-Mon.

Response:

```json
{
	"LS Instances":[
	  {
	  	"ESClusterName": "diceMonit",
      "HostFQDN": "dice.cdh5.dmon.internal",
      "IP": "109.231.121.210",
      "LPort": 5000,
      "LSCoreHeap": "512m",
      "LSCoreSparkEndpoint": "None",
      "LSCoreSparkPort": "None",
      "LSCoreStormEndpoint": "None",
      "LSCoreStormPort": "None",
      "LSCoreStormTopology": "None",
      "OS": "ubuntu",
      "Status": "Running",
      "udpPort": 25680
	  	  
	  }
	]
}
```
***

`POST` `/v1/overlord/core/ls`

Starts the logstash server based on the configuration information. During this step the configuration file is first generated.

**FUTURE Work**: Better support for distributed deployment of logstash core service instances.

***

`DELETE` `/v1/overlord/core/ls/<hostFQDN>`

Stops the logstash server instance on a given host and removes all configuration data from DMON.


`GET` `/v1/overlord/core/ls/config`

Returns the current configuration file of Logstash Server.

***

`PUT` `/v1/overlord/ls/config`

Changes the current configuration of Logstash Server.

Input:

```json
{
  "ESClusterName": "diceMonit",
  "HostFQDN": "string",
  "IP": "string",
  "Index": "logstash",
  "LPort": 5000,
  "LSCoreHeap": "512m",
  "LSCoreSparkEndpoint": "None",
  "LSCoreSparkPort": "None",
  "LSCoreStormEndpoint": "None",
  "LSCoreStormPort": "None",
  "LSCoreStormTopology": "None",
  "LSCoreWorkers": "4",
  "OS": "string",
  "udpPort": 25826
}

```

**NOTE:** LS instances are bound by their FQDN this meanst that it can't change.
**Future Work**: Only for local deployment of logstash server core service. Future versions will include distributed deployment.
 
`GET` `/v1/overlord/core/ls/<hostFQDN>/status`

Return the status of the logstash server running on the host identified by _hostFQDN_.

`POST` `/v1/overlord/core/ls/<hostFQDN>/start` 

Start the logstash server instance on the host identified by _hostFQDN_. It will use the last good configuration.
 
`POST` `/v1/overlord/core/ls/<hostFQDN>/stop` 

Stops the logstash server instance on the host identified by _hostFQDN_. 

***

`GET` `/v1/overlord/core/ls/credentials`

Returns the current credentials for logstash server core service.

Response:

```json
{
  "Credentials": [
  	{
  		"Certificate":"<certificate name>",
  		"Key":"<key name>",
  		"LS Host":"<host fqdn>"
  	}
  ]
}

```

**NOTE**: Logstash server and the logstash forwarder need a private/public key in order to establish secure communications. During local deployment ('-l' flag) a default public private key-pair is created.

***

`GET` `/v1/overlord/core/ls/cert/{certName}`

Returns the hosts using a specified certificate. The certificate is identified by its _certName_.

Response:

```json
{
	"Host":"[listofhosts]",
}

```

**Note**: By default all Nodes use the default certificate created during D-Mon initialization. This request returns a list of hosts using the specified certificate. 

***

`PUT` `/v1/overlord/core/ls/cert/{certName}/{hostFQDN}`

Uploads a certificate with the name given by _certName_ and associates it with the given host identified by _hostFQDN_.

**NOTE**: The submitted certificate must use the **application/x-pem-file** Content-Type.

***

`GET` `/v1/overlord/core/ls/key/{keyName}`

Retruns the host associated with the given key identified by _keyName_ parameter.

Response:

```json
{
	"Host":"<LS host name>",
	"Key":"<key name>"
}

```
***

`PUT` `/v1/overlord/core/ls/key/{keyName}/{hostFQDN}`

Uploads a private key with the name given by _keyName_ and associates it with the given host identified by _hostFQDN_.

**NOTE**: The submitted private key must use the **application/x-pem-file** Content-Type.

***

`GET` `/v1/overlord/core/kb`

Returns information for all kibana instances.

```json
{
	KB Instances:[{
		"HostFQDN":<FQDN>,
		"IP":<host_ip>,
		"OS":<os_type>,
		"KBPort":<kibana_port>
		"PID":<kibana_pid>,
		"KBStatus":<Running|Stopped|Unknown>
	},
	......................
	]
}
```

`POST` `/v1/overlord/core/kb`

Generates the configuration file and  Starts or restarts a kibana session.

**NOTE:** Currently supports only one instance. No dostributed deployment.


`GET` `/v1/overlord/core/kb/config`

Returns the current configuration file for Kibana. Uses the mime-type __'text/yaml'__.



`PUT` `/v1/overlord/core/kb/config`
Changes the current configuration for Kibana

Input:

```json
{
	"HostFQDN":<FQDN>,
	"IP":<host_ip>,
	"OS":<os_type>,
	"KBPort":<kibana_port>
}
```



***



-
#### Monitoring auxiliary


`GET` `/v1/overlord/aux`

Returns basic information about auxiliary components.

**FUTURE Work**: Information will basically be a kind of Readme. 

***

`GET` `/v1/overlord/aux/agent`

Returns the current deployment status of dmon-agents.

```json
{
  "Agents": [
    {
      "Agent": false,
      "NodeFQDN": "dice.cdh5.mng.internal"
    },
    {
      "Agent": false,
      "NodeFQDN": "dice.cdh5.w1.internal"
    },
    {
      "Agent": false,
      "NodeFQDN": "dice.cdh5.w2.internal"
    },
    {
      "Agent": false,
      "NodeFQDN": "dice.cdh5.w3.internal"
    }
  ]
}
```

`POST` `/v1/overlord/aux/agent`

Bootstraps the installation of dmon-agent services on nodes who are note marked as
already active. It only works if all nodes have the same authentication.

`GET` `/v1/overlord/aux/deploy`

Returns monitoring component status of all nodes. Similar to __v2__ of this resource.

```json
{
	{
		"NodeFQDN":"<nodeFQDN>",
		"NodeIP":"<nodeIP>",
		"Monitored":"<boolean>",
		"Collectd":"<status>",
		"LSF":"<status>",
		"LSInstance": "<ip_logstash>"
	},
	............................
}

```

**NOTE:** Marked as __DEPRECATED__. Will be deleted in future versions.
***

`POST` `/v1/overlord/aux/deploy`

Deploys all auxiliary monitoring components on registered nodes and configures them.

**NOTE**: There are three statuses associated with each auxiliary component. 

* __None__ -> There is no aux component on the registered node
* __Running__ -> There is the aux component on the registered node an it is currently running
* __Stopped__ -> There is the aux component on the registered node and it is currently stopped

If the status is _None_ than this resource will install and configure the monitoring components. However if the status is _Running_ nothing will be done. The services with status _Stopped_ will be restarted.

All nodes can be restarted independent from their current state using the **--redeploy-all** parameter.

**NOTE:** Marked as __DEPRECATED__. Will be deleted in future versions. Use __v2__ version of the same resource for parallel implementation of this resource.

***

`POST` `/v1/overlord/aux/deploy/{collectd|logstashfw}/{NodeName}`

Deploys either collectd or logstash-forwarder to the specified node. In order to reload the configuration file the **--redeploy** parameter has to be set. If the  current node status is _None_ than the defined component (collectd or lsf) will be installed.

**FUTURE Work**: Currently configurations of both collectd and logstash-forwarder are global and can't be changed on a node by node basis.

***

`GET` `/v1/overlord/aux/interval`

Returns the current polling time interval for all tools. This is a global setting. Future versions may be implemented for a node by node interval setting.

__Output:__

```json
{
	"Spark": "5",
	"Storm": "60",
	"System": "15",
	"YARN": "15"
}
```
`PUT` `/v1/overlord/aux/interval`

Changes the settings for all monitored systems.


__Input:__

```json
{
	"Spark": "5",
	"Storm": "60",
	"System": "15",
	"YARN": "15"
}
```


***


`GET` `/v1/overlord/aux/{collectd|logstashfw}/config`

Returns the current collectd or logstashfw configuration file.



`PUT` `/v1/overlord/aux/{collectd|logstashfw}/config`

Changes the configuration/status of collectd or logstashforwarder and restarts all aux components.

***

`POST` `/v1/overlord/aux/{auxComp}/start` 

Starts the specified auxiliary component on all nodes.

**NOTE:** This resource is DEPRECATED. Use _v2_ instead.


`POST` `/v1/overlord/aux/{auxComp}/stop`

Stops the specified auxiliary components on all nodes.

**NOTE:** This resource is DEPRECATED. Use _v2_ instead.

***

`POST` `/v1/overlord/aux/{auxComp}/{nodeFQDN}/start`

Starts the specified auxiliary component on a specific node.

**NOTE:** This resource is DEPRECATED. Use _v2_ instead.


`POST` `/v1/overlord/aux/{auxComp}/{nodeFQDN}/stop`

Stops the specified auxiliary component on a specific node.

**NOTE:** This resource is DEPRECATED. Use _v2_ instead.



__Note:__ Some resources have been redesigned with parallel processing in mind. These use greenlets (gevent) to parallelize as much as possible the first version of the resources. These paralel resources are marked with _../v2/.._. All other functionality and return functions are the same.

For the sake of brevity these resources will not be detailed. Only additional functionality will be documented.


***

`POST` `/v2/overlord/aux/deploy`

Sets up the dmon-agent based on what roles are registerd for each nodes.


`POST` `/v2/overlord/aux/{auxComp}/{nodeFQDN}/configure`

Configures  dmon-agent _auxComp_  on node _nodeFQDN_.


`POST` `/v2/overlord/aux/{auxComp}/configure`

Configures  dmon-agent _auxComp_  on all nodes.


`GET` `/v2/overlord/aux/deploy/check`


Polls dmon-agents from the current monitored cluster.


```json
{
  "Failed": [],
  "Message": "Nodes updated!",
  "Status": "Update"
}
```

If nodes don't respon they are added to the _Failed_ list togheter with the appropiate HTTP error code.


`GET` `/v2/overlord/aux/status`

Returns the current status of all nodes and auxiliary components:

__Outputs:__

```json
{
  "Aux Status": [
    {
      "Collectd": "Running",
      "LSF": "Running",
      "Monitored": true,
      "NodeFQDN": "dice.cdh5.mng.internal",
      "NodeIP": "109.231.121.135",
      "Status": true
    },
    {
      "Collectd": "Running",
      "LSF": "Running",
      "Monitored": true,
      "NodeFQDN": "dice.cdh5.w1.internal",
      "NodeIP": "109.231.121.194",
      "Status": true
    },
    {
      "Collectd": "Running",
      "LSF": "Running",
      "Monitored": true,
      "NodeFQDN": "dice.cdh5.w2.internal",
      "NodeIP": "109.231.121.134",
      "Status": true
    },
    {
      "Collectd": "Running",
      "LSF": "Running",
      "Monitored": true,
      "NodeFQDN": "dice.cdh5.w3.internal",
      "NodeIP": "109.231.121.156",
      "Status": true
    }
  ]
}
```

***

`POST` `/v2/overlord/aux/{auxComp}/start`

Start _auxComp_ on all nodes using parallel calls to the dmon-agent.

`POST` `/v2/overlord/aux/{auxComp}/stop`

Stops _auxComp_ on all nodes using parallel calls to the dmon-agent.


`POST` `/v2/overlord/aux/{auxComp}/{nodeFQDN}/start`

Start _auxComp_ on node _nodeFQDN_ using parallel calls to the dmon-agent.

`POST` `/v2/overlord/aux/{auxComp}/{nodeFQDN{/stop`

Stops _auxComp_ on node _nodeFQDN_ using parallel calls to the dmon-agent.

-
### Observer


`GET` `/v1/observer/applications`

Returns a list of all YARN applications/jobs on the current monitored big data cluster.

**NOTE**: Scheduled for future release. After M18.

***

`GET` `/v1/observer/applications/{appID}`

Returns information on a particular YARN application identified by _{appID}_.
The information will not contain monitoring data only a general overview. Similar to YARN History Server.

**NOTE**: Scheduled for future release. After M18

***

`GET` `/v1/observer/nodes`
 
 Returns the current monitored nodes list. Listing is only limited to node FQDN and current node IP.
 
 **NOTE**: Some cloud providers assign the IP dynamically at VM startup. Because of this D-Mon treats the FQDN as a form of UUID. In future versions this might change, the FQDN being replaced/augmented with a hash.
 
 Response:
 
```json
{
    "Nodes":[
      {"<NodeFQDN1>":"NodeIP1"},
      {"<NodeFQDN2>":"NodeIP2"},
      {"<NodeFQDNn>":"NodeIPn"}
      ]
  }
```
***
`GET` `/v1/observer/nodes/{nodeFQDN}`

Returns information of a particular monitored node. No information is limited to non confidential information, no authentication credentials are returned. The _Status_ field is true if dmon-agent has been already deployed while _Monitored_ is true if it is also started. _LSInstance_ represents the to witch logstash instance the node is assigned to.

Response:

```json
{
    "<nodeFQDN>":{
      "Status":"<boolean>",
      "IP":"<NodeIP>",
      "Monitored":"<boolean>",
      "OS":"<Operating_System>",
      "LSInstance": "<ip_of_logstash>"
    }
}
```
***
`GET` `/v1/observer/nodes/{nodeFQDN}/roles`

Returns roles of the node identified by _'nodeFQDN'_.

Response:

```json
{
	'Roles':['yarn','spark']
}
```


**NOTE:** Roles are returned as a list. Some elements represent in fact more than one service, for example _'yarn'_ represents both _'HDFS'_ and _'Yarn'_.

***
`POST` `/v1/observer/query/{csv/json/plain}`

Returns the required metrics in csv, json or plain format.

Input:

```json
{
  "DMON":{
    "query":{
      "size":"<SIZEinINT>",
      "ordering":"<asc|desc>",
      "queryString":"<query>",
      "tstart":"<startDate>",
      "tstop":"<stopDate>"
    }
  }
}
```
Output depends on the option selected by the user: csv, json or plain. 

**NOTE**: The filter metrics must be in the form of a list. Also, filtering currently works only for CSV and plain output. Future versions will include the ability to export metrics in the form of RDF+XML in concordance with the OSLC Performance Monitoring 2.0 standard. It is important to note that we will export in this format only system metrics. No Big Data framework specific metrics.

From version __0.1.3__ it is possible to ommit the _tstop_ parameter, instead it is possible to define a time window based on the current  system time:

```json
{
  "DMON":{
    "query":{
      "size":"<SIZEinINT>",
      "ordering":"<asc|desc>",
      "queryString":"<query>",
      "tstart":"now-30s"
    }
  }
}

```

where __s__ stands for second or __m__ for minites and __h__ for hours. 

From version __0.2.0__ it is possible to specify custom index to be used in the query. The index definiton supports the __*__ wildcard character.

```json
{
  "DMON":{
    "query":{
      "size":"<SIZEinINT>",
      "index":"logstash-*",
      "ordering":"<asc|desc>",
      "queryString":"<query>",
      "tstart":"now-30s"
    }
  }
}

```


#License

__DICE Monitoring Platform__

Copyright (C) 2015 Gabriel Iuhasz, Institute e-Austria Romania


Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
