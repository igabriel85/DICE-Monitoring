# DICE Monitoring Logstash Service (dmon-logstash)

The DICE MOnitoring logstash service is designed to provide a REST API in order to controll a Logstash server instance. Currently this is not provided by logstash itself but it is under [investigation](https://github.com/elastic/logstash/issues/2612) by the development team. Because of the need to create a distributed deployment of logstash servers in the [DICE Project](http://www.dice-h2020.eu/) there is a clear need for controlling them in a consitent and efficient way.

This is the main reason this service has been created. It allows the generation of logstash configuration files as well as the starting/restarting and stopping.

**NOTE:** Because this is still a prototype some changes to the respurces it exposes can change in later version. To see all changes please consult the Change Log.

##Change Log
* v0.0.2 - First alpha release
	 	
	  		 	
##Installation and Use

**TODO**

###Manual
**TODO**

##REST API Structure 
**NOTE:** This is a preliminary structure of the REST API. It mau be sibject to changes!

`GET` `/agent/v1/cert`

Return two list. One for the public key and one for the private key.

__Output:__

```json
{
  "certificates": [
    "logstash.crt"
  ],
  "keys": [
    "logstash.key"
  ]
}
```

`POST` `/agent/v1/cert`

Enables the sending of new certificates to replace the default (dev) ones.

`GET` `/agent/v1/cert/type/<ctype/name/<cname>`

Return a specific certificate defined by its name (__cname__) and its type (__ctype__). This enables the dmon-controller to receive certificates for several logstash servers and use them for bootstrapping monitoring on registered nodes. It returns these using the __application/x=x509-ca-cert__ content type.

`GET` `/agent/v1/host`

Return information about the current host. Both hardware and OS information

__Output:__

```json
{
  "Machine": "<machine_arch>",
  "Node": "<fqdn>",
  "Processor": "<proc_name>",
  "Release": "<os release>",
  "System": "<os_name>",
  "Version": "<Kernel_version>"
}
```

`GET` `/agent/v1/logstash`

Return the current status of the logstash server.

`GET` `/agent/v1/logstash/config`

Returns the current collectd configuration file content.

`POST` `/agent/v1/logstash/config`

Enables the setting for the logstash server instance

__Input:__

```json
{
  "ESCluster": "<es_cluster_name>",
  "EShostIP": "<host_IP>",
  "EShostPort": "<es_master_port>",
  "LSHeap": "<heap_size>",
  "LSWorkers": "<num_of_workers>",
  "StormRestIP": "<storm_rest_ip>",
  "StormRestPort": "<storm_rest_port>",
  "StormTopologyID": "<storm_rest_topology>",
  "UDPPort": "<udp_port>"
}
```

`POST` `/agent/v1/logstash/deploy`

This is used to install logstash server version 2.2.1. It is also resposible for installing all required libraries and runtimes as well as creating security certificates used for development and testing.

`GET` `/agent/v1/logstash/log`

Return the log of dmon-logstash.

`POST` `/agent/v1/logstash/start`

Starts the logstash server instance using the last known good configuration.

`POST` `/agent/v1/logstash/stop`

Stops the last started logstash server instance.

