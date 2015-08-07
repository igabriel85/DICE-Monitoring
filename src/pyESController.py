from datetime import datetime
from elasticsearch import Elasticsearch

es = Elasticsearch('<ES-Endpoint>')


#body got from request tab in kibana
body = {
  "size": 500,
  "sort": {
    "@timestamp": "desc"
  },
  "query": {
    "filtered": {
      "query": {
        "query_string": {
          "query": "host:*",
          "analyze_wildcard": True
        }
      },
      "filter": {
        "bool": {
          "must": [
            {
              "range": {
                "@timestamp": {
                  "gte": 1438900439450,
                  "lte": 1438901339450
                }
              }
            }
          ],
          "must_not": []
        }
      }
    }
  },
  "highlight": {
    "pre_tags": [
      "@kibana-highlighted-field@"
    ],
    "post_tags": [
      "@/kibana-highlighted-field@"
    ],
    "fields": {
      "*": {}
    }
  },
  "aggs": {
    "2": {
      "date_histogram": {
        "field": "@timestamp",
        "interval": "30s",
        "pre_zone": "+03:00",
        "pre_zone_adjust_large_interval":True,
        "min_doc_count": 0,
        "extended_bounds": {
          "min": 1438900439450,
          "max": 1438901339450
        }
      }
    }
  },
  "fields": [
    "*",
    "_source"
  ],
  "script_fields": {},
  "fielddata_fields": [
    "@timestamp",
    "received_at"
  ]
}


testServiceType = {
  "size": 500,
  "sort": {
    "@timestamp": "desc"
  },
  "query": {
    "filtered": {
      "query": {
        "query_string": {
          "query": "hostname:\"dice.cdh5.s2.internal\" AND serviceType:\"yarn\" ",
          "analyze_wildcard": True
        }
      },
      "filter": {
        "bool": {
          "must": [
            {
              "range": {
                "@timestamp": {
                  "gte": 1438939155342,
                  "lte": 1438940055342
                }
              }
            }
          ],
          "must_not": []
        }
      }
    }
  },
  "fields": [
    "*",
    "_source"
  ],
  "script_fields": {},
  "fielddata_fields": [
    "@timestamp"
  ]
}


#these are the metrics listed in the response JSON under "_source"
metrics = ['message','type','@timestamp','host','job_id','hostname','AvailableVCores']

res = es.search(index="logstash-*",body=testServiceType)
print("%d documents found" % res['hits']['total'])
for doc in res['hits']['hits']:
  for met in metrics:
    #prints the values of the metrics defined in the metrics list
    print("%s) %s" % (doc['_id'], doc['_source'][met]))


# def queryESCore(es,body,index="logstash-*"):
#   res = es.search(index,body)
#   print("%d documents found" % res['hits']['total'])
#   for doc in res['hits']['hits']:
#     print("%s) %s" % (doc['_id'], doc['_source']['AvailableVCores']))

