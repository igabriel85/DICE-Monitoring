# DICE Monitoring ElasticSearch Service (dmon-elasticsearch)

The DICE MOnitoring logstash service is designed to provide a REST API in order to controll elasticsearch instances. It is designed to facilitate the configuration of elasticsearch instances that are part of a cluster. It doesn't provide any querying capabilities. This is done using the dmon-controller.

**NOTE:** Because this is still a prototype some changes to the respurces it exposes can change in later version. To see all changes please consult the Change Log.

##Change Log
* v0.0.1 - First alpha release
	 	
	  		 	
##Installation and Use
###Manual
In contrast to the dmon-agent the dmon-elasticsearch installs an elasticsearch instance on the target host at deployment.

**TODO**

##REST API Structure 
**NOTE:** This is a preliminary structure of the REST API. It mau be sibject to changes!

`GET` `/agent/v1/cert`

Lists the current content of the certificate directory.

`POST` `/agent/v1/cert`

Ads new certificate for elasticsearch instance. 

**NOTE:** These certificates are not mandatory. They are used only for production systems. During testing and development they are usually omited.

`GET` `/agent/v1/elasticsearch`

Returns the current state and PID (if process is found to be still running) of the managed elasticsearch instance.

`POST` `/agent/v1/elasticsearch/cmd`

Is used to issue runtime commands to the managed elasticsearch instance.

**NOTE:** Not yet implemented. Schedueled for future release.

`GET` `/agent/v1/elasticsearch/config`

Returns the current elasticsearch configuration file.

`POST` `/agent/v1/elasticsearch/config`

The request payload is used to generate the elasticsearch configuration file.

__INPUT:__

```json
{
  "cacheSettings": {
    "cacheFilterExpires": "6h",
    "cacheFilterSize": "20%",
    "fieldDataCacheExpires": "6h",
    "fieldDataCacheSize": "20%"
  },
  "clusterName": "diceMonit",
  "indexSettings": {
    "bufferSize": "30%",
    "minIndexBufferSize": "96mb",
    "minShardBufferSize": "12mb"
  },
  "networkHost": "0.0.0.0",
  "nodeData": "True",
  "nodeID": "esMaster",
  "nodeMaster": "True",
  "replicas": 1,
  "shards": 5
}

```

`GET` `/agent/v1/elastisearch/config/<parameter>`

Is used to get the current runtime parameters of the managed elasticsearch instance.

`PUT` `/agent/v1/elasticsearch/config/<parameter>`

Is used to change the configuration of specific runtime parameters of the managed elastisearch instance.

**NOTE:** Not yet implemented. Is schedueled for later releases.

`POST` `/agent/v1/elasticsearcg/start`

Starts the managed elasticsearch instance with the last known good configuration.

`POST` `/agent/v1/elasticsearch/stop`

Stops the managed elasticsearch instance.

`GET` `/agent/v1/elasticsearch/state`

Returns the last known good payload from _/agent/v1/elasticsearch/config_.

`GET` `/agent/v1/host`

Returns host specific information.

__OUTPUT:__

```json
{
  "Machine": "x86_64",
  "Node": "<esnode>",
  "Processor": "i386",
  "Release": "15.4.0",
  "System": "Darwin",
  "Version": "Darwin Kernel Version ...." 
}

```

`GET` `/agent/v1/logs`

Returns a list of available logs.

__OUTPUT:__

```json

{
  "Logs": [
    "dmon-elasticsearch.log"
  ]
}

```

`GET` `/agent/v1/logs/<log>`

Return a specific log from the log directory.