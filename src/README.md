# pyDMON - DICE Monitoring Platform

It is designed as a web service that serves as the main interface (REST API) and controlling agent for the other monitoring components.
These components include:
* ElasticsSearch
* Logstash Server
* kibana
* collectd
* logstash-forwarder
*etc

It is designed for:
* **first design choice** - something

**TODO**

##Change Log
* TODO


##REST API Structure
**NOTE:** This is a preliminary structure of the REST API. It may be subject to changes!

There are two main componets from this API: 
* First we have the management and deployment/provisioning component called **Overlord**.
 * It is responsible for the deployment and management of the Monitoring Core components: ElasticSearch, Logstash Server and Kibana.
 * It is also responsible for the auxiliary component management and deployment. These include: Collectd, Logstash-forwarder
* Second, we have the interface used by other applications to query the DataWarehouse represented by ElasticSearch. This component is called **Observer**.
 * It is responsible for the returning of monitoring metrics in the form of: CSV, JSON, simple ouput. 



something

```
something
```
### Overlord
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

`GET` `/v1/overlord/core/es/config`

Returns the current configuration of ElasticSearch.

**TODO** json structure.

`GET` `/v1/overlord/ls/config`

Returns the current configuration of LogstashServer

**TODO** json structure.

`GET` `/v1/overlord/core/kb/config`

Returns the current configuration for Kibana

**TODO** json structure.




### Observer
`GET` `/v1/observer/nodes`
 
 Returns the current monitored nodes list.
 
```json
{
  "DMON":{
    "Nodes":[
      {"<NodeFQDN1>":"NodeIP1"},
      {"<NodeFQDN2>":"NodeIP2"},
       .......................,
      {"<NodeFQDNn>":"NodeIPn"}
      ]
  }
}
```

`GET` `/v1/observer/nodes/{NodeFQDN}`

Returns information of a particular monitored node.

```json
{
  "DMON":{
    "<NodeFQDN>":{
      "Status":"<online|offline|unstable>",
      "IP":"<NodeIP>",
      "OS":"Operating_Systen",
      "CDH":"<active|inactive|unknown>",
      "CDHVersion":"<version>"
    }
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

