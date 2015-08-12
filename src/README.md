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


`GET` `/resource/someting`
 
```json
{
  "Gateways": [
    "gatewayHTTP", 
    "gatewayTCP", 
    "gatewayHTTPS" 
  ]
}
```


