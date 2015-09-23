# pyDMON - DICE Monitoring Platform

It is designed as a web service that serves as the main interface (REST API) and controlling agent for the other monitoring components.
These components include:

* ElasticsSearch
* Logstash Server
* kibana
* collectd
* logstash-forwarder
* etc

It is designed for:

* **first design choice** - something

**TODO**

##Change Log
* v0.1.1 - First alpha release

##Installation

The instalation is largely based on bash scripts. Future versions will most likely be based on chef recepies and/or deb/rpm packages. There are 2 types of instalation procedures currently supported.

### Cloud
This type of instalation is for client/cloud deployment. It will install all python modules as well as the ELK (ElasticSearch, logstash and kibana 4) stack. Only local  installation is currently supported.

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
The '-i' flag will install all Core components of the monitoring platform (i.e. ELK) as well as setting the appropriate permisions for all folders and files. The '-p' flag designates the port on which D-Mon will be deployed.

* In order deploy D-Mon localy execute:

```
./dmon-start.sh -l -p 5001
``` 
The '-l' flag signas the service that this is a local deployment of both ElasticSearch and Logstash server. The service will start logging into stdout.

**Note**: Do not execute this command as root! It will corrupt the previously set permissions and the service will be inoperable.

If you do not wish to create a local deployment run the comand.

```
./dmon-start.sh -p 5001
```

This will only start theservice and not load the local deployment module.

**Note**: By default all the IP is set to _0.0.0.0_. This can be change using the '-e' flag.


### Vagrant

* TODO

### Chef
* TODO not schedueled for M12


##REST API Structure
**NOTE:** This is a preliminary structure of the REST API. It may be subject to changes!

There are two main componets from this API: 

* First we have the management and deployment/provisioning component called **Overlord**.
 * It is responsible for the deployment and management of the Monitoring Core components: ElasticSearch, Logstash Server and Kibana.
 * It is also responsible for the auxiliary component management and deployment. These include: Collectd, Logstash-forwarder
* Second, we have the interface used by other applications to query the DataWarehouse represented by ElasticSearch. This component is called **Observer**.
 * It is responsible for the returning of monitoring metrics in the form of: CSV, JSON, simple ouput. 

### Overlord

The Overlord is structured into two components:

* **Monitoring Core** represented by: ElasticSearch, LogstashServer and Kibana
* **Monitoring Auxiliary** represented by: Collectd, logstash-forwarder

-
#### Monitoring Core

`GET` `/v1/overlord`

Returns information regarding the current version of the Monitoring Platform.


`PUT` `/v1/overlord/application`

Registers an application with DMON and creates a unique tag for the monitored data.

**NOTE**: Schedueled for future versions!


`POST` `/v1/overlord/core`

Deploys all monitoring core components provided they have values preset hosts. If not it deploys all componenets locally with default settings.

**NOTE**: Currently the '-l' flag of the start script _dmon-start.sh_ does the same as the later option.


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

`GET` `/v1/overlord/chef`

Returns the status of the chef-client of the monitoring core services.

**TODO:** json structure.

**NOTE:** This feature will be developed for future versions.


`GET` `/v1/overlord/nodes/chef`

Returns the status of the chef-clients from all monitored nodes.

**TODO:** json structure.

**NOTE:** This feature will be developed for future versions.


`GET` `/v1/overlord/nodes`
 
 Returns the current monitored nodes list.
 
```json
{
    "Nodes":[
      {"<NodeFQDN1>":"NodeIP1"},
      {"<NodeFQDN2>":"NodeIP2"},
      {"<NodeFQDNn>":"NodeIPn"}
      ]
  }
```


`PUT` `/v1/overlord/nodes`

Inludes the given nodes into the monitored node pools.

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


`POST` `/v1/overlord/nodes`

Bootstrap of all non monitored nodes. Installs collectd and logstash-forwarder on them.


`GET` `/v1/overlord/nodes/{NodeFQDN}`

Returns information of a particular monitored node identified by its NodeFQDN.

```json
{
      "NodeName":"nodeFQDN",
      "Status":"<online|offline|unstable>",
      "IP":"<NodeIP>",
      "OS":"<Operating_Systen>",
      "key":"<keyName|null>",
      "username":"<uname|null>",
      "password":"<pass|null>",
      "chefclient":"<True|False>",
      "CDH":"<active|inactive|unknown>",
      "CDHVersion":"<version>"
}
```

`PUT` `/v1/overlord/nodes/{NodeFQDN}`

Changes the current information of a given node. Node FQDN and IP may not change from one version to another.

Input:

```json
{
  "NodeName":"<nodeFQDN>",
  "IP":"<NodeIP>",
  "OS":"<Operating_Systen>",
  "key":"<keyName|null>",
  "username":"<uname|null>",
  "password":"<pass|null>"
}
```

`DELETE` `/v1/overlord/nodes/purge/{nodeFQDN}`

Stops all auxiliary monitoring components associated with a particular node.

**NOTE**: This does not delete the nodes nor the configurations it simply stops collectd and logstash-forwarder on the selected nodes.


`GET` `/v1/overlord/core/es`

Return a list of current hosts in comprising the ES cluster core components.

```json
{
  "ES Instances": [
    {
      "ClusterName": "<clustername>",
      "HostFQDN": "<HostFQDN>",
      "IP": "<Host IP>",
      "NodeName": "<NodeName>",
      "NodePort": "<IP:int>",
      "OS": "<host OS>",
      "PID": "<ES component PID>",
      "Status": "<ES Status>"
    },
    ..................
  ]
}

```

`POST` `/v1/overlord/core/es` 

Generates and applies the new configuration options of the ES Core components.

**NOTE**: If configuration is unchanged ES Core will not be restarted!
It is possible to deploy the monitoring platform on different hosts than elasticsearch. 



`GET` `/v1/overlord/core/es/config`

Returns the current configuration file of ElasticSearch in the form of a YAML file.



**NOTE**: The first registered ElasticSearch information will be set by default to be the master node.


`DELETE` `/v1/overlord/core/es/<hostFQDN>`

Stops the ElasticSearch instance on a given host and removes all condiguration data from DMON.

 

`GET` `/v1/overlord/core/ls/config`

Returns the current configuration file of Logstash Server.



`GET` `/v1/overlord/core/kb/config`

Returns the current configuration file for Kibana.

**NOTE:** Marked as obsolete!



`PUT` `/v1/overlord/core/es/config`

Changes the current configuration options of ElasticSearch.

Input:

```json
{
  "HostFQDN":"<nodeFQDN>",
  "IP":"<NodeIP>",
  "OS":"<Operating_Systen>",
  "NodeName":"<ES host name>",
  "NodePort":"<ES host port>",
  "ClusterName":"<ES cluster name>"
}

```

`PUT` `/v1/overlord/ls/config`

Changes the current configuration of LogstashServer.

Input:

```json
{
  "HostFQDN":"<nodeFQDN>",
  "IP":"<NodeIP>",
  "OS":"<Operating_Systen>",
  "LPort":"<Lumberjack Port>",
  "udpPort":"<UDP Collectd port>",
  "ESClusterName":"<ES cluster Name>"
}

```

`PUT` `/v1/overlord/core/kb/config`

Input:
Changes the current configuration for Kibana

**NOTE:** Marked as obsolete!

-
#### Monitoring auxiliary

`GET` `/v1/overlord/aux/deploy`

Returns monitoring status of all nodes.

```json
{
	{
		"NodeFQDN":"<nodeFQDN>",
		"NodeIP":"<nodeIP>",
		"Monit":"<True|False>",
		"Collectd":"<status>",
		"LSF":"<status>"
	},
	............................
}

```


`POST` `/v1/overlord/aux/deploy`

Deploys all auxiliary monitoring components on registered nodes and configures them.



`POST` `/v1/overlord/aux/deploy/{collectd|logstashfw}/{NodeName}`

Deploys either collectd or logstash-forwarder to the specified node. It is


`GET` `/v1/overlord/aux/{collectd|logstashfw}/config`

Returns the current collectd or logstashfw configuration

**TODO** json structure.

`PUT` `/v1/overlord/aux/{collectd|logstashfw}/config`

Changes the configuration/status of collectd or logstashfw and restarts all aux components.
 
 Input:
**TODO** json structure.

**NOTE**: Currently configurations of both collectd and logstash-forwarder are global and can't be changed on a node by node basis. 

-
### Observer

`GET` `/v1/observer/applications`

Returns a list of all YARN applications/jobs.

**NOTE**: Schedueled for future release.



`GET` `/v1/observer/applications/<appID>`

Returns information on a particular YARN application identified by <appID>





`GET` `/v1/observer/nodes`
 
 Returns the current monitored nodes list.
 
```json
{
    "Nodes":[
      {"<NodeFQDN1>":"NodeIP1"},
      {"<NodeFQDN2>":"NodeIP2"},
      {"<NodeFQDNn>":"NodeIPn"}
      ]
  }
```

`GET` `/v1/observer/nodes/{NodeFQDN}`

Returns information of a particular monitored node.

```json
{
    "<NodeFQDN>":{
      "Status":"<online|offline>",
      "IP":"<NodeIP>",
      "Monitored":"<true|false>"
      "OS":"Operating_Systen"
    }
}
```

`GET` `/v1/observer/nodes/{NodeFQDN}/services`

Returns information on the services running on a given node.

```json
{
    "<NodeFQDN>":[
      {
        "ServiceName":"<ServiceName>",
        "ServiceStatus":"<ServiceStatus>"
      },
      ............................,
      {
        "ServiceName":"<ServiceName>",
        "ServiceStatus":"<ServiceStatus>"
      }
      ]
}
```

`POST` `/v1/observer/query/{CSV/JSON/Plain}`

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
Output depends on the option selected by the user: csv, json or Plain. 

NOTE: The metrics must be in the form of a list.


