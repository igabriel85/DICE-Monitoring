'''

Copyright 2015, Institute e-Austria, Timisoara, Romania
    http://www.ieat.ro/
Developers:
 * Gabriel Iuhasz, iuhasz.gabriel@info.uvt.ro

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:
    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

from datetime import datetime
from elasticsearch import Elasticsearch
import csv
import unicodedata
import os
import sys, getopt
#from addict import Dict


#ouptu dir location
outDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

#Global es
es = Elasticsearch('109.231.121.210')

# class ESCoreInit:
#   def __init__(self, IP):
#     self.IP = IP
#   def initialize(self,IP):
#     self.


def queryConstructor(tstart, queryString,tstop = 'None',  size=500,ordering="desc"):
  '''
      Function generates a query string reprezented by a dictionary/json.
      It has the following arguments:

      tstart      -> unix time representation of required period start
                  -> can use type "now-10s" definition 
      tstop       -> unix time representation of required period stop
                  -> be default it is set to None and will be ommited
      queryString -> represents the query from the user
      size        -> repreents how many records should be in the output
                  -> default is 500
      ordering    -> can be "asc" or "desc"
                  -> default is "desc"

      Function returns a dictionary of the query body required for elasticsearch.
  '''
  if tstop == 'None':
    nestedBody = {'gte':tstart}
  else:
    nestedBody = {'gte':tstart,'lte':tstop}

  queryBody= {
  "size": size,
  "sort": {
    "@timestamp": ordering
  },
  "query": {
    "filtered": {
      "query": {
        "query_string": {
          "query": queryString,
          "analyze_wildcard": True
        }
      },
      "filter": {
        "bool": {
          "must": [
            {
              "range": {
                "@timestamp": nestedBody
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
  return queryBody


def queryESCore(queryBody, allm=True, dMetrics=[ ], debug=False, myIndex="logstash-*"):
  '''
      Function to query the Elasticsearch monitoring (ESM) core.
      It has the following arguments:
      queryBody -> is a dictionary that reprezents the query for ESM Core
                -> it is returned by the function queryConstructor()
      all       -> boolean arguments; if True returns all available metrics from the query
                -> if False must specify list of user defined metrics
                -> default value is True
      dMetrics  -> List of user defined metrics
                -> default is the empty list
                -> if all argument is set to False dMetrics is mandatory
      debug     -> if set to true prints debug information
      myIndex   -> user defined index for ESM Core
                -> default is "logstash-*"

      TODO: 
      - filter by removing terms/metrics from all not only specifying desired metrics

  '''
  #these are the metrics listed in the response JSON under "_source"
  res = es.search(index=myIndex,body=queryBody)
  if debug == True:
    print "%---------------------------------------------------------%"
    print "Raw JSON Ouput"
    print res
    print("%d documents found" % res['hits']['total'])
    print "%---------------------------------------------------------%"
  termsList = []
  termValues = []
  ListMetrics = []
  for doc in res['hits']['hits']:
    if allm == False:
      if not dMetrics:
        sys.exit("dMetrics argument not set. Please supply valid list of metrics!")
      for met in dMetrics:
      #prints the values of the metrics defined in the metrics list
        if debug == True:
          print "%---------------------------------------------------------%"
          print "Parsed Output -> ES doc id, metrics, metrics values."
          print("doc id %s) metric %s -> value %s" % (doc['_id'], met, doc['_source'][met]))
          print "%---------------------------------------------------------%"
        termsList.append(met)
        termValues.append(doc['_source'][met]) 
      dictValues=dict(zip(termsList,termValues))
    else:
      for terms in doc['_source']:
      #prints the values of the metrics defined in the metrics list
        if debug == True:
          print "%---------------------------------------------------------%"
          print "Parsed Output -> ES doc id, metrics, metrics values."
          print("doc id %s) metric %s -> value %s" % (doc['_id'],terms,  doc['_source'][terms]))
          print "%---------------------------------------------------------%"
        termsList.append(terms)
        termValues.append(doc['_source'][terms])
        dictValues=dict(zip(termsList,termValues))
    ListMetrics.append(dictValues)
  return ListMetrics, res
  

def dict2CSV(ListValues,fileName="output"):
  '''
      Function that creates a csv file from a list of dictionaries.
      It has the arguments:
      ListValues  -> is a list containing dictionaries with individual timestamped metrics.
      fileName    -> name of the ouput csv file
                  -> default is "ouput"

  '''
  if not ListValues:
        sys.exit("listValues argument is empty. Please supply valid input!")
  fileType = fileName+".csv"
  csvOut = os.path.join(outDir,fileType)
  try:
    with open(csvOut,'wb') as csvfile:
      w=csv.DictWriter(csvfile, ListValues[0].keys())
      w.writeheader()
      for dictMetrics in ListValues:
        w.writerow(dictMetrics)
    csvfile.close()
  except EnvironmentError:
    print "ops"



def main(argv):
  try:
    opts, args=getopt.getopt(argv,"hd")
  except getopt.GetoptError:
    print "%-------------------------------------------------------------------------------------------%"
    print "Invalid argument! Arguments must take the form:"
    print ""
    print "pyESController.py {-h| -d}"
    print ""
    print "%-------------------------------------------------------------------------------------------%"
    sys.exit(2)
  for opt, arg in opts:
      if opt == '-h':
        print "%-------------------------------------------------------------------------------------------%"
        print ""
        print "pyESController is desigend to facilitate the querying of ElasticSearch Monitoring Core."
        print "Only two arguments are currently supported: -h for help or -d for debug mode"
        print "Usage Example:"
        print "pyESController.py {-h|-d}"
        print "                                                                                              "
        print "%-------------------------------------------------------------------------------------------%"
        sys.exit()
      elif opt in ("-d"):
        testQuery = queryConstructor(1438939155342,1438940055342,"hostname:\"dice.cdh5.s4.internal\" AND serviceType:\"dfs\"")
        metrics = ['type','@timestamp','host','job_id','hostname','AvailableVCores']
        test, test2 = queryESCore(testQuery, debug=True)
        dict2CSV(test)
def defineESCore(IP):
  es = Elasticsearch(IP)
  return es
if __name__=='__main__':
  #ElasticSearch object that defines the endpoint
  es = Elasticsearch('85.120.206.43')
  if len(sys.argv) == 1: # only for development
    testQuery = queryConstructor(1438939155342, 1438940055342, "hostname:\"dice.chd5.mng.internal\" AND serviceType:\"dfs\"")
    print testQuery
    #metrics = ['type','@timestamp','host','job_id','hostname','RamDiskBlocksDeletedBeforeLazyPersisted']
    test, test2 = queryESCore(testQuery, allm=True, debug=True)
    dict2CSV(test)
    print test2
    #queryESCoreCSV(test, True)
  else:
    main(sys.argv[1:])