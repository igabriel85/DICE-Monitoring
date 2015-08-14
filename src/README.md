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
* TODO

##Installation
* TODO

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




`GET` `/v1/overlord/core/status`

Returns the current status of the Monitoring platform status.

```json
{
  "DMON":{
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
  }
}

```

`GET` `/v1/overlord/chef`

Returns the status of the chef-client of the monitoring core services.

**TODO** json structure.


`GET` `/v1/overlord/nodes/chef`

Returns the status of the chef-clients from all monitored nodes.

**TODO** json structure.


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


`POST` `/v1/overlord/nodes`

Inludes the given nodes into the monitored node pools.

Input:

```json
{
  "DMON":{
    "Nodes":[
      {"<NodeFQDN1>":
        {
          "NodeIP":"<IP>",
          "Credentials":{
            "key":"<keyName|null>",
            "username":"<uname|null>",
            "password":"<pass|null>"
          }
        }
      },
      ..........................,
      {"<NodeFQDNn>":
        {
          "NodeIP":"<IP>",
          "Credentials":{
            "key":"<keyName|null>",
            "username":"<uname|null>",
            "password":"<pass|null>"
          }
        }
      }
    ]
  }
}
```

`GET` `/v1/overlord/nodes/{NodeFQDN}`

Returns information of a particular monitored node.

```json
{
  "DMON":{
    "<NodeFQDN>":{
      "Status":"<online|offline|unstable>",
      "IP":"<NodeIP>",
      "OS":"<Operating_Systen>",
      "Credentials":{
        "key":"<keyName|null>",
        "username":"<uname|null>",
        "password":"<pass|null>"
      },
      "chefclient":"<True|False>",
      "CDH":"<active|inactive|unknown>",
      "CDHVersion":"<version>"
    }
  }
}
```

`PUT` `/v1/overlord/nodes/{NodeFQDN}`

Changes the current information of a given node.

Input:

```json
{
  "DMON":{
    "<NodeFQDN>":{
      "IP":"<NodeIP>",
      "OS":"<Operating_Systen>",
      "Credentials":{
        "key":"<keyName|null>",
        "username":"<uname|null>",
        "password":"<pass|null>"
      }
    }
  }  
}
```

`POST`  `/v1/overlord/core/check`

Returns complete health check report on all core components

Response 

**TODO** json structure


`POST` `/v1/overlord/nodes/check`
Returns complete health check report on all subscribed nodes


`GET` `/v1/overlord/core/es/config`

Returns the current configuration of ElasticSearch.

**TODO** json structure.

`GET` `/v1/overlord/ls/config`

Returns the current configuration of LogstashServer

**TODO** json structure.

`GET` `/v1/overlord/core/kb/config`

Returns the current configuration for Kibana

**TODO** json structure.


`PUT` `/v1/overlord/core/es/config`

Changes the current configuration of ElasticSearch.

Input:
**TODO** json structure.

`PUT` `/v1/overlord/ls/config`

Input:
Changes the current configuration of LogstashServer

**TODO** json structure.

`PUT` `/v1/overlord/core/kb/config`

Input:
Changes the current configuration for Kibana

**TODO** json structure.

-
#### Monitoring auxiliary

`GET` `/v1/overlord/aux/deploy/{NodeName}`

Retruns the current deployment of auxiliary monitoring components to all nodes or to a specified Node defined by {NodeName}


`POST` `/v1/overlord/aux/deploy`

Deploys all auxiliary monitoring applications and configures them.

`POST` `/v1/overlord/aux/deploy/{collectd|logstashfw}/{NodeName}`

Deploys either collectd or logstash-forwarder to all nodes if {NodeName} is specified it deploys the selected auxiliary component to the node specified.


`GET` `/v1/overlord/aux/{collectd|logstashfw}/config`

Returns the current collectd or logstashfw configuration

**TODO** json structure.

`PUT` `/v1/overlord/aux/{collectd|logstashfw}/config`

Changes the configuration of collectd or logstashfw and restarts all aux components.
 
 Input:
**TODO** json structure.

**NOTE**: Currently configurations of both collectd and logstash-forwarder are global and can't be changed on a node by node basis. 

-
### Observer
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
  "DMON":{
    "<NodeFQDN>":[
      {
        "ServiceName":"<ServiceName>",
        "ServiceStatus":"<ServiceStatus>"
      },
          ..........................,
      {
        "ServiceName":"<ServiceName>",
        "ServiceStatus":"<ServiceStatus>"
      }
      ]
  }
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


