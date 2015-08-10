from datetime import datetime
from elasticsearch import Elasticsearch
import csv
import unicodedata




#body got from request tab in kibana



def queryConstructor(ordering, tstart, tstop, queryString):
  defaultBody= {
  "size": 500,
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
                "@timestamp": {
                  "gte": tstart,
                  "lte": tstop
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
  return defaultBody







def queryESCore(queryString, all=False):
  #these are the metrics listed in the response JSON under "_source"
  metrics = ['message','type','@timestamp','host','job_id','hostname','AvailableVCores']
  res = es.search(index="logstash-*",body=queryString)
  #print res
  print("%d documents found" % res['hits']['total'])
  for doc in res['hits']['hits']:
    if all == False:
      for met in metrics:
      #prints the values of the metrics defined in the metrics list
        print("%s) %s" % (doc['_id'], doc['_source'][met]))
    else:
      #get all terms from query
      for terms in doc['_source']:
      #prints the values of the metrics defined in the metrics list
        print("%s) %s %s" % (doc['_id'],terms,  doc['_source'][terms]))

def queryESCoreCSV(queryString, all=False):
  #these are the metrics listed in the response JSON under "_source"
  metrics = ['message','type','@timestamp','host','job_id','hostname','AvailableVCores']
  res = es.search(index="logstash-*",body=queryString)
  #print res
  #print("%d documents found" % res['hits']['total'])
  #get results
  results = res['hits']['hits']
  termsList = []
  #print results
  for doc in results:
    for terms in doc['_source']:
      termsList.append(terms)
  termsUniqueList = list(set(termsList)) #retain only the unique value from the list of terms
  print termsUniqueList  #####

  with open('output.csv','wb') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',' #can be changed to ',' for standard csv
      ,quotechar='|', quoting=csv.QUOTE_MINIMAL)

    #Create headers
    filewriter.writerow(termsUniqueList)    #change the column labels here
    for hit in results:
      #print hit
      for terms in termsList:
        #print terms
        #print hit['_source'][terms].decode('utf-8')
        colList = []
        try: 
          col =  hit['_source'][terms]
        except Exception, e:
          #print "What?"
          col = "a "
        colList.append(col)
        #print colList
        
    filewriter.writerow(colList)


      

if __name__=='__main__':
  #Elastic search endpoint
  es = Elasticsearch('109.231.126.38')
  test = queryConstructor("desc",1438939155342,1438940055342,"hostname:\"dice.cdh5.s3.internal\" AND serviceType:\"yarn\"")
  print test

  queryESCore(test, True)
  #queryESCoreCSV(test, True)