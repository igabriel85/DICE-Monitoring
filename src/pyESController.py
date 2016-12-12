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

from elasticsearch import Elasticsearch
import csv
import unicodedata
import requests
import os
import sys, getopt
from app import *
from datetime import *
import time
from addict import Dict
import pandas as pd
from pyUtil import csvheaders2colNames


# ouptu dir location
outDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

# Global es
es = Elasticsearch()


def queryConstructor(tstart, queryString, tstop='None', size=500, ordering="desc"):
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
        nestedBody = {'gte': tstart}
    else:
        nestedBody = {'gte': tstart, 'lte': tstop}

    queryBody = {
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


def queryESCore(queryBody, allm=True, dMetrics=[], debug=False, myIndex="logstash-*"):
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
    # these are the metrics listed in the response JSON under "_source"
    res = es.search(index=myIndex, body=queryBody)
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
                # prints the values of the metrics defined in the metrics list
                if debug == True:
                    print "%---------------------------------------------------------%"
                    print "Parsed Output -> ES doc id, metrics, metrics values."
                    print("doc id %s) metric %s -> value %s" % (doc['_id'], met, doc['_source'][met]))
                    print "%---------------------------------------------------------%"
                termsList.append(met)
                termValues.append(doc['_source'][met])
            dictValues = dict(zip(termsList, termValues))
        else:
            for terms in doc['_source']:
                # prints the values of the metrics defined in the metrics list
                if debug == True:
                    print "%---------------------------------------------------------%"
                    print "Parsed Output -> ES doc id, metrics, metrics values."
                    print("doc id %s) metric %s -> value %s" % (doc['_id'], terms, doc['_source'][terms]))
                    print "%---------------------------------------------------------%"
                termsList.append(terms)
                termValues.append(doc['_source'][terms])
                dictValues = dict(zip(termsList, termValues))
        ListMetrics.append(dictValues)
    return ListMetrics, res


def dict2CSV(ListValues, fileName="output"):
    '''
      Function that creates a csv file from a list of dictionaries.
      It has the arguments:
      ListValues  -> is a list containing dictionaries with individual timestamped metrics.
      fileName    -> name of the ouput csv file
                  -> default is "ouput"

  '''
    if not ListValues:
        sys.exit("listValues argument is empty. Please supply valid input!")
    fileType = fileName + ".csv"
    csvOut = os.path.join(outDir, fileType)
    try:
        with open(csvOut, 'wb') as csvfile:
            uniqueColumns = set()
            for d in ListValues:
                # print >>sys.stderr, d.keys()
                for e in d.keys():
                    if e not in uniqueColumns:
                        uniqueColumns.add(e)
            csvHeaders = list(uniqueColumns)
            w = csv.DictWriter(csvfile, csvHeaders)
            w.writeheader()
            for dictMetrics in ListValues:
                w.writerow(dictMetrics)
        csvfile.close()
    except EnvironmentError:
        print "ops"


def getYarnJobs(yhIP, yhPort):
    '''
  :param yhIP: History Server IP
  :param yhPort: History Server Port
  :return: Jobs descriptor
  '''
    jURL = 'http://%s:%s/ws/v1/history/mapreduce/jobs' % (yhIP, str(yhPort))
    try:
        rJobs = requests.get(jURL)
    except Exception as inst:
        print "Exception %s with %s while getting jobs" % (type(inst), inst.args)
        raise
    return rJobs.status_code, rJobs.json()


def getYarnJobsStatistic(yhIP, yhPort, jDescriptor):
    '''
    :param yhIP: History server IP
    :param yhPort: History Server Port
    :param jDescriptor: Jobs descriptor
    :return: Jobs statistics
    '''

    #print >> sys.stderr, jDescriptor
    if jDescriptor['jobs'] is None:
        raise Exception('No jobs found')
    jList = []
    # print >> sys.stderr, len(jDescriptor['jobs']['job'])
    for j in jDescriptor['jobs']['job']:
        # print >> sys.stderr, j
        jList.append(j['id'])
        # print >> sys.stderr, jList
        responseList = []
    for id in jList:
        jURL = 'http://%s:%s/ws/v1/history/mapreduce/jobs/%s' % (yhIP, str(yhPort), id)
        try:
            rJobId = requests.get(jURL)
        except Exception as inst:
            raise "Exception %s with %s while getting job details" % (type(inst), inst.args)
        data = rJobId.json()
        # data['timestamp'] = datetime.now()
        responseList.append(data)
    retDict = {}
    retDict['jobs'] = responseList

    return retDict


def getYarnJobTasks(yhIP, yhPort, jDescriptor):
    '''
    :param yhIP: History Server IP
    :param yhPort: History Server Port
    :param jDescriptor: Jobs descriptor
    :return: Tasks statistics
    '''
    if jDescriptor['jobs'] is None:
        raise Exception('No jobs found')
    jList = []
    for j in jDescriptor['jobs']['job']:
        jList.append(j['id'])

    responseList = []
    for id in jList:
        jURL = 'http://%s:%s/ws/v1/history/mapreduce/jobs/%s/tasks' % (yhIP, str(yhPort), id)
        try:
            rJobId = requests.get(jURL)
        except Exception as inst:
            raise Exception("Exception %s with %s while getting job details") % (type(inst), inst.args)
        data = rJobId.json()
        data['jobId'] = id
        # data['timestamp'] = datetime.now()
        responseList.append(data)
    retDict = {}
    retDict['jobs'] = responseList

    return retDict

def dmonESIndexer(esCoreEndpoint, dmonindex, dmondoc_type, docId, body):
    '''
    :param esCoreEndpoint: ES Endpoint
    :param index: Index elasticsearch index
    :param doc_type: Type of document
    :param docId: Document id
    :param body: Data to be indexed
    :return:
    '''

    es = Elasticsearch(esCoreEndpoint)
    res = es.index(index=dmonindex, doc_type=dmondoc_type, id=docId, body=body, request_timeout=30)
    return res


class ESCoreConnector:
    def __init__(self, esEndpoint, esInstanceEndpoint=9200, index="logstash-*"):
        self.esInstance = Elasticsearch(esEndpoint)
        self.esEndpoint = esEndpoint
        self.esInstanceEndpoint = esInstanceEndpoint
        self.myIndex = index

    def info(self):
        try:
            res = self.esInstance.info()
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Exception has occured while connecting to ES core with type %s at arguments %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            res = 0
        return res

    def createIndex(self, indexName):
        try:
            res = self.esInstance.create(index=indexName, ignore=400)
            app.logger.info('[%s] : [INFO] Created index %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), indexName)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Failed to created index %s with %s and %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), indexName, type(inst), inst.args)
            res = 0
        return res

    def closeIndex(self, indexName):
        try:
            res = self.esInstance.close(index=indexName)
            app.logger.info('[%s] : [INFO] Closed index %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), indexName)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Failed to close index %s with %s and %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), indexName, type(inst),
                         inst.args)
            res = 0
        return res

    def deleteIndex(self, indexName):
        try:
            res = self.esInstance.indices.delete(index=indexName, ignore=[400, 404])
            app.logger.info('[%s] : [INFO] Deleted index %s',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), indexName)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Failed to delete index %s with %s and %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), indexName, type(inst),
                         inst.args)
            res = 0
        return res

    def openIndex(self, indexName):
        try:
            res = self.esInstance.indices.open(index=indexName)
            app.logger.info('[%s] : [INFO] Open index %s',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), indexName)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Failed to open index %s with %s and %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), indexName, type(inst), inst.args)
            res = 0
        return res

    def getIndex(self, indexName):
        try:
            res = self.esInstance.indices.get(index=indexName, human=True)
            app.logger.info('[%s] : [INFO] Got index %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), indexName)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Failed to get index %s with %s and %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), indexName, type(inst), inst.args)
            res = 0
        return res

    def getIndexSettings(self, indexName):
        try:
            res = self.esInstance.indices.get_settings(index=indexName, human=True)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Failed to fetch index %s settings with %s and %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), indexName, type(inst), inst.args)
            res = 0
        return res

    def clusterHealth(self):
        try:
            res = self.esInstance.cluster.health(request_timeout=15)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Failed to fetch cluster health with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            res = 0
        return res

    def clusterSettings(self):
        try:
            res = self.esInstance.cluster.get_settings(request_timeout=15)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Failed to fetch cluster settings with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            res = 0
        return res

    def clusterState(self):
        try:
            res = self.esInstance.cluster.stats(human=True, request_timeout=15)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Failed to fetch cluster state with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            res = 0
        return res

    def nodeInfo(self):
        try:
            res = self.esInstance.nodes.info(request_timeout=15)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Failed to fetch node indo with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            res = 0
        return res

    def nodeState(self):
        try:
            res = self.esInstance.nodes.stats(request_timeout=15)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Failed to fetch node state with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            res = 0
        return res

    def aggQuery(self, index, queryBody):
        try:
            res = self.esInstance.search(index=index, body=queryBody)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Exception while executing ES query with %s and %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            res = 0
        return res

    def pushToIndex(self, index, typeD, body, id=None):
        try:
            if id is None:
                res = self.esInstance.index(index=index, doc_type=typeD, body=body)
            else:
                res = self.esInstance.index(index=index, doc_type=typeD, body=body, id=id)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Exception has occured while pushing anomaly with type %s at arguments %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            return 0
        return res


class QueryConstructor():
    def __init__(self):
        self.author = 'Constructor for dmon ES connector querys'

    def loadString(self, host):
        qstring = "collectd_type:\"load\" AND host:\"%s\"" % host
        file = "Load_%s.csv" % host
        return qstring, file

    def memoryString(self, host):
        qstring = "collectd_type:\"memory\" AND host:\"%s\"" % host
        file = "Memory_%s.csv" % host
        return qstring, file

    def interfaceString(self, host):
        qstring = "plugin:\"interface\" AND collectd_type:\"if_octets\" AND host:\"%s\"" % host
        file = "Interface_%s.csv" % host
        return qstring, file

    def packetString(self, host):
        qstring = "plugin:\"interface\" AND collectd_type:\"if_packets\" AND host:\"%s\"" % host
        file = "Packets_%s.csv" % host
        return qstring, file

    def dfsString(self):
        qstring = "serviceType:\"dfs\""
        file = "DFS.csv"
        return qstring, file

    def dfsFString(self):
        qstring = "serviceType:\"dfs\" AND serviceMetrics:\"FSNamesystem\""
        file = "DFSFS.csv"
        return qstring, file

    def jvmnodeManagerString(self, host):
        qstring = "serviceType:\"jvm\" AND ProcessName:\"NodeManager\" AND hostname:\"%s\"" % host
        file = "JVM_NM_%s.csv" % host
        return qstring, file

    def jvmNameNodeString(self):
        qstring = "serviceType:\"jvm\" AND ProcessName:\"NameNode\""
        file = "JVM_NN.csv"
        return qstring, file

    def nodeManagerString(self, host):
        qstring = "serviceType:\"yarn\" AND serviceMetrics:\"NodeManagerMetrics\" AND hostname:\"%s\"" % host
        file = "NM_%s.csv" % host
        return qstring, file

    def queueResourceString(self):
        qstring = "type:\"resourcemanager-metrics\" AND serviceMetrics:\"QueueMetrics\""
        file = "ResourceManagerQueue.csv"
        return qstring, file

    def clusterMetricsSring(self):
        qstring = "type:\"resourcemanager-metrics\" AND ClusterMetrics:\"ResourceManager\""
        file = "ClusterMetrics.csv"
        return qstring, file

    def jvmMapTask(self, host):
        qstring = "hostname:\"%s\" AND type:\"maptask-metrics\"" % host  # TODO add per process name
        file = "JVM_MapTask_%s.csv" % host
        return qstring, file

    def jvmResourceManagerString(self):
        qstring = "type:\"resourcemanager-metrics\" AND serviceType:\"jvm\""
        file = "JVM_RM.csv"
        return qstring, file

    def datanodeString(self, host):
        qstring = "type:\"datanode-metrics\" AND serviceType:\"dfs\" AND hostname:\"%s\"" % host
        file = 'DN_%s.csv' % host
        return qstring, file

    def mrappmasterString(self):
        qstring = "type:\"mrappmaster-metrics\" AND serviceMetrics:\"MRAppMetrics\""
        file = 'MRAPP.csv'
        return qstring, file

    def jvmMrappmasterString(self):
        qstring = "type:\"mrappmaster-metrics\" AND serviceMetrics:\"JvmMetrics\""
        file = "JVM_MRAPP.csv"
        return qstring, file

    def fsopDurationsString(self):
        qstring = "type:\"resourcemanager-metrics\" AND serviceMetrics:\"FSOpDurations\""
        file = 'FSOP.csv'
        return qstring, file

    def shuffleString(self, host):
        qstring = "serviceMetrics:\"ShuffleMetrics\" AND serviceType:\"mapred\" AND hostname:\"%s\"" % host
        file = 'Shuffle_%s.csv' % host
        return qstring, file

    def jvmRedProcessString(self, host):
        qstring = "type:\"reducetask-metrics\" AND serviceType:\"jvm\" AND hostname:\"%s\"" % host
        return qstring

    def jvmMapProcessingString(self, host):
        qstring = "type:\"maptask-metrics\" AND serviceType:\"jvm\" AND hostname:\"%s\"" % host
        return qstring #TODO

    def jvmRedProcessbyNameString(self, host, process):
        qstring = "type:\"reducetask-metrics\" AND serviceType:\"jvm\" AND hostname:\"%s\" AND ProcessName:\"%s\"" %(host, process)
        file = 'JVM_ReduceTask_%s_%s.csv' %(host, process)
        return qstring, file

    def jvmMapProcessbyNameString(self, host, process):
        qstring = "type:\"maptask-metrics\" AND serviceType:\"jvm\" AND hostname:\"%s\" AND ProcessName:\"%s\"" % (
        host, process)
        file = 'JVM_MapTasksTask_%s_%s.csv' % (host, process)
        return qstring, file

    def loadAverage(self):  # TODO
        return "Average load across all nodes!"

    def memoryAverage(self):
        return "Average memory across all nodes!"

    def interfaceAverage(self):  # TODO
        return "Average interface across all nodes!"

    def packetAverage(self):  # TODO
        return "Average packets across all nodes!"

    def yarnNodeManager(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):

        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["3"].date_histogram.field = "@timestamp"
        cquery.aggs["3"].date_histogram.interval = qinterval
        cquery.aggs["3"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["3"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["3"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["3"].date_histogram.extended_bounds.max = qlte

        # Specify precise metrics, and the average value expressed by 'avg' key
        cquery.aggs["3"].aggs["40"].avg.field = "ContainersLaunched"
        cquery.aggs["3"].aggs["41"].avg.field = "ContainersCompleted"
        cquery.aggs["3"].aggs["42"].avg.field = "ContainersFailed"
        cquery.aggs["3"].aggs["43"].avg.field = "ContainersKilled"
        cquery.aggs["3"].aggs["44"].avg.field = "ContainersIniting"
        cquery.aggs["3"].aggs["45"].avg.field = "ContainersRunning"
        cquery.aggs["3"].aggs["47"].avg.field = "AllocatedGB"
        cquery.aggs["3"].aggs["48"].avg.field = "AllocatedContainers"
        cquery.aggs["3"].aggs["49"].avg.field = "AvailableGB"
        cquery.aggs["3"].aggs["50"].avg.field = "AllocatedVCores"
        cquery.aggs["3"].aggs["51"].avg.field = "AvailableVCores"
        cquery.aggs["3"].aggs["52"].avg.field = "ContainerLaunchDurationNumOps"
        cquery.aggs["3"].aggs["53"].avg.field = "ContainerLaunchDurationAvgTime"
        cqueryd = cquery.to_dict()
        return cqueryd

    def systemLoadQuery(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):
        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["2"].date_histogram.field = "@timestamp"
        cquery.aggs["2"].date_histogram.interval = qinterval
        cquery.aggs["2"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["2"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["2"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["2"].date_histogram.extended_bounds.max = qlte

        # Specifc system metrics for cpu load
        cquery.aggs["2"].aggs["1"].avg.field = "shortterm"
        cquery.aggs["2"].aggs["3"].avg.field = "midterm"
        cquery.aggs["2"].aggs["4"].avg.field = "longterm"
        cqueryd = cquery.to_dict()
        return cqueryd

    def systemMemoryQuery(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):
        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["2"].date_histogram.field = "@timestamp"
        cquery.aggs["2"].date_histogram.interval = qinterval
        cquery.aggs["2"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["2"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["2"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["2"].date_histogram.extended_bounds.max = qlte

        cquery.aggs["2"].aggs["3"].terms.field = "type_instance.raw"
        cquery.aggs["2"].aggs["3"].terms.size = 0
        cquery.aggs["2"].aggs["3"].terms.order["1"] = "desc"
        cquery.aggs["2"].aggs["3"].aggs["1"].avg.field = "value"
        cqueryd = cquery.to_dict()
        return cqueryd

    def systemInterfaceQuery(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):

        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["3"].date_histogram.field = "@timestamp"
        cquery.aggs["3"].date_histogram.interval = qinterval
        cquery.aggs["3"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["3"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["3"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["3"].date_histogram.extended_bounds.max = qlte
        cquery.aggs["3"].aggs["1"].avg.field = "tx"
        cquery.aggs["3"].aggs["2"].avg.field = "rx"
        cqueryd = cquery.to_dict()
        return cqueryd

    def dfsQuery(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):

        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["3"].date_histogram.field = "@timestamp"
        cquery.aggs["3"].date_histogram.interval = qinterval
        cquery.aggs["3"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["3"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["3"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["3"].date_histogram.extended_bounds.max = qlte

        #DFS metrics
        cquery.aggs["3"].aggs["2"].avg.field = "CreateFileOps"
        cquery.aggs["3"].aggs["4"].avg.field = "FilesCreated"
        cquery.aggs["3"].aggs["5"].avg.field = "FilesAppended"
        cquery.aggs["3"].aggs["6"].avg.field = "GetBlockLocations"
        cquery.aggs["3"].aggs["7"].avg.field = "FilesRenamed"
        cquery.aggs["3"].aggs["8"].avg.field = "GetListingOps"
        cquery.aggs["3"].aggs["9"].avg.field = "DeleteFileOps"
        cquery.aggs["3"].aggs["10"].avg.field = "FilesDeleted"
        cquery.aggs["3"].aggs["11"].avg.field = "FileInfoOps"
        cquery.aggs["3"].aggs["12"].avg.field = "AddBlockOps"
        cquery.aggs["3"].aggs["13"].avg.field = "GetAdditionalDatanodeOps"
        cquery.aggs["3"].aggs["14"].avg.field = "CreateSymlinkOps"
        cquery.aggs["3"].aggs["15"].avg.field = "GetLinkTargetOps"
        cquery.aggs["3"].aggs["16"].avg.field = "FilesInGetListingOps"
        cquery.aggs["3"].aggs["17"].avg.field = "AllowSnapshotOps"
        cquery.aggs["3"].aggs["18"].avg.field = "DisallowSnapshotOps"
        cquery.aggs["3"].aggs["19"].avg.field = "CreateSnapshotOps"
        cquery.aggs["3"].aggs["20"].avg.field = "DeleteSnapshotOps"
        cquery.aggs["3"].aggs["21"].avg.field = "RenameSnapshotOps"
        cquery.aggs["3"].aggs["22"].avg.field = "ListSnapshottableDirOps"
        cquery.aggs["3"].aggs["23"].avg.field = "SnapshotDiffReportOps"
        cquery.aggs["3"].aggs["24"].avg.field = "BlockReceivedAndDeletedOps"
        cquery.aggs["3"].aggs["25"].avg.field = "StorageBlockReportOps"
        cquery.aggs["3"].aggs["26"].avg.field = "TransactionsNumOps"
        cquery.aggs["3"].aggs["27"].avg.field = "TransactionsAvgTime"
        cquery.aggs["3"].aggs["28"].avg.field = "SnapshotNumOps"
        cquery.aggs["3"].aggs["29"].avg.field = "SyncsAvgTime"
        cquery.aggs["3"].aggs["30"].avg.field = "TransactionsBatchedInSync"
        cquery.aggs["3"].aggs["31"].avg.field = "BlockReportNumOps"
        cquery.aggs["3"].aggs["32"].avg.field = "BlockReportAvgTime"
        cquery.aggs["3"].aggs["33"].avg.field = "SafeModeTime"
        cquery.aggs["3"].aggs["34"].avg.field = "FsImageLoadTime"
        cquery.aggs["3"].aggs["35"].avg.field = "GetEditNumOps"
        cquery.aggs["3"].aggs["36"].avg.field = "GetGroupsAvgTime"
        cquery.aggs["3"].aggs["37"].avg.field = "GetImageNumOps"
        cquery.aggs["3"].aggs["38"].avg.field = "GetImageAvgTime"
        cquery.aggs["3"].aggs["39"].avg.field = "PutImageNumOps"
        cquery.aggs["3"].aggs["40"].avg.field = "PutImageAvgTime"
        cqueryd = cquery.to_dict()
        return cqueryd

    def dfsFSQuery(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):
        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["34"].date_histogram.field = "@timestamp"
        cquery.aggs["34"].date_histogram.interval = qinterval
        cquery.aggs["34"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["34"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["34"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["34"].date_histogram.extended_bounds.max = qlte

        #DFS FS metrics
        cquery.aggs["34"].aggs["1"].avg.field = "BlocksTotal"
        cquery.aggs["34"].aggs["2"].avg.field = "MissingBlocks"
        cquery.aggs["34"].aggs["3"].avg.field = "MissingReplOneBlocks"
        cquery.aggs["34"].aggs["4"].avg.field = "ExpiredHeartbeats"
        cquery.aggs["34"].aggs["5"].avg.field = "TransactionsSinceLastCheckpoint"
        cquery.aggs["34"].aggs["6"].avg.field = "TransactionsSinceLastLogRoll"
        cquery.aggs["34"].aggs["7"].avg.field = "LastWrittenTransactionId"
        cquery.aggs["34"].aggs["8"].avg.field = "LastCheckpointTime"
        cquery.aggs["34"].aggs["9"].avg.field = "UnderReplicatedBlocks"
        cquery.aggs["34"].aggs["10"].avg.field = "CorruptBlocks"
        cquery.aggs["34"].aggs["11"].avg.field = "CapacityTotal"
        cquery.aggs["34"].aggs["12"].avg.field = "CapacityTotalGB"
        cquery.aggs["34"].aggs["13"].avg.field = "CapacityUsed"
        #cquery.aggs["34"].aggs["14"].avg.field = "CapacityTotalGB" ####
        #cquery.aggs["34"].aggs["15"].avg.field = "CapacityUsed"
        cquery.aggs["34"].aggs["16"].avg.field = "CapacityUsedGB"
        cquery.aggs["34"].aggs["17"].avg.field = "CapacityRemaining"
        cquery.aggs["34"].aggs["18"].avg.field = "CapacityRemainingGB"
        cquery.aggs["34"].aggs["19"].avg.field = "CapacityUsedNonDFS"
        cquery.aggs["34"].aggs["20"].avg.field = "TotalLoad"
        cquery.aggs["34"].aggs["21"].avg.field = "SnapshottableDirectories"
        cquery.aggs["34"].aggs["22"].avg.field = "Snapshots"
        cquery.aggs["34"].aggs["23"].avg.field = "FilesTotal"
        cquery.aggs["34"].aggs["24"].avg.field = "PendingReplicationBlocks"
        cquery.aggs["34"].aggs["25"].avg.field = "ScheduledReplicationBlocks"
        cquery.aggs["34"].aggs["26"].avg.field = "PendingDeletionBlocks"
        cquery.aggs["34"].aggs["27"].avg.field = "ExcessBlocks"
        cquery.aggs["34"].aggs["28"].avg.field = "PostponedMisreplicatedBlocks"
        cquery.aggs["34"].aggs["29"].avg.field = "PendingDataNodeMessageCount"
        cquery.aggs["34"].aggs["30"].avg.field = "MillisSinceLastLoadedEdits"
        cquery.aggs["34"].aggs["31"].avg.field = "BlockCapacity"
        cquery.aggs["34"].aggs["32"].avg.field = "StaleDataNodes"
        cquery.aggs["34"].aggs["33"].avg.field = "TotalFiles"
        cqueryd = cquery.to_dict()
        return cqueryd

    def jvmNNquery(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):
        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["13"].date_histogram.field = "@timestamp"
        cquery.aggs["13"].date_histogram.interval = qinterval
        cquery.aggs["13"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["13"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["13"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["13"].date_histogram.extended_bounds.max = qlte

        #NN JVM Metrics
        cquery.aggs["13"].aggs["1"].avg.field = "MemNonHeapUsedM"
        cquery.aggs["13"].aggs["2"].avg.field = "MemNonHeapCommittedM"
        cquery.aggs["13"].aggs["3"].avg.field = "MemHeapUsedM"
        cquery.aggs["13"].aggs["4"].avg.field = "MemHeapCommittedM"
        cquery.aggs["13"].aggs["5"].avg.field = "MemHeapMaxM"
        cquery.aggs["13"].aggs["6"].avg.field = "MemMaxM"
        cquery.aggs["13"].aggs["7"].avg.field = "GcCountParNew"
        cquery.aggs["13"].aggs["8"].avg.field = "GcTimeMillisParNew"
        cquery.aggs["13"].aggs["9"].avg.field = "GcCountConcurrentMarkSweep"
        cquery.aggs["13"].aggs["10"].avg.field = "GcTimeMillisConcurrentMarkSweep"
        cquery.aggs["13"].aggs["11"].avg.field = "GcCount"
        cquery.aggs["13"].aggs["12"].avg.field = "GcTimeMillis"
        cquery.aggs["13"].aggs["14"].avg.field = "GcNumWarnThresholdExceeded"
        cquery.aggs["13"].aggs["15"].avg.field = "GcNumInfoThresholdExceeded"
        cquery.aggs["13"].aggs["16"].avg.field = "GcTotalExtraSleepTime"
        cquery.aggs["13"].aggs["17"].avg.field = "ThreadsNew"
        cquery.aggs["13"].aggs["18"].avg.field = "ThreadsRunnable"
        cquery.aggs["13"].aggs["19"].avg.field = "ThreadsBlocked"
        cquery.aggs["13"].aggs["20"].avg.field = "ThreadsWaiting"
        cquery.aggs["13"].aggs["21"].avg.field = "ThreadsTimedWaiting"
        cquery.aggs["13"].aggs["22"].avg.field = "ThreadsTerminated"
        cquery.aggs["13"].aggs["23"].avg.field = "LogError"
        cquery.aggs["13"].aggs["24"].avg.field = "LogFatal"
        cquery.aggs["13"].aggs["25"].avg.field = "LogWarn"
        cquery.aggs["13"].aggs["26"].avg.field = "LogInfo"
        cqueryd = cquery.to_dict()
        return cqueryd

    def jvmMRQuery(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):
        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["13"].date_histogram.field = "@timestamp"
        cquery.aggs["13"].date_histogram.interval = qinterval
        cquery.aggs["13"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["13"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["13"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["13"].date_histogram.extended_bounds.max = qlte

        # NN JVM Metrics
        cquery.aggs["13"].aggs["1"].avg.field = "MemNonHeapUsedM"
        cquery.aggs["13"].aggs["2"].avg.field = "MemNonHeapCommittedM"
        cquery.aggs["13"].aggs["3"].avg.field = "MemHeapUsedM"
        cquery.aggs["13"].aggs["4"].avg.field = "MemHeapCommittedM"
        cquery.aggs["13"].aggs["5"].avg.field = "MemHeapMaxM"
        cquery.aggs["13"].aggs["6"].avg.field = "MemMaxM"
        cquery.aggs["13"].aggs["7"].avg.field = "GcCountParNew"
        cquery.aggs["13"].aggs["8"].avg.field = "GcTimeMillisParNew"
        cquery.aggs["13"].aggs["9"].avg.field = "GcCountConcurrentMarkSweep"
        cquery.aggs["13"].aggs["10"].avg.field = "GcTimeMillisConcurrentMarkSweep"
        cquery.aggs["13"].aggs["11"].avg.field = "GcCount"
        cquery.aggs["13"].aggs["12"].avg.field = "GcTimeMillis"
        cquery.aggs["13"].aggs["17"].avg.field = "ThreadsNew"
        cquery.aggs["13"].aggs["18"].avg.field = "ThreadsRunnable"
        cquery.aggs["13"].aggs["19"].avg.field = "ThreadsBlocked"
        cquery.aggs["13"].aggs["20"].avg.field = "ThreadsWaiting"
        cquery.aggs["13"].aggs["21"].avg.field = "ThreadsTimedWaiting"
        cquery.aggs["13"].aggs["22"].avg.field = "ThreadsTerminated"
        cquery.aggs["13"].aggs["23"].avg.field = "LogError"
        cquery.aggs["13"].aggs["24"].avg.field = "LogFatal"
        cquery.aggs["13"].aggs["25"].avg.field = "LogWarn"
        cquery.aggs["13"].aggs["26"].avg.field = "LogInfo"
        cqueryd = cquery.to_dict()
        return cqueryd

    def resourceQueueQuery(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):

        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["23"].date_histogram.field = "@timestamp"
        cquery.aggs["23"].date_histogram.interval = qinterval
        cquery.aggs["23"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["23"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["23"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["23"].date_histogram.extended_bounds.max = qlte

        # Resource Manager Queue Metrics
        cquery.aggs["23"].aggs["1"].avg.field = "running_0"
        cquery.aggs["23"].aggs["2"].avg.field = "running_60"
        cquery.aggs["23"].aggs["3"].avg.field = "running_300"
        cquery.aggs["23"].aggs["4"].avg.field = "running_1440"
        cquery.aggs["23"].aggs["5"].avg.field = "AppsSubmitted"
        cquery.aggs["23"].aggs["6"].avg.field = "AppsPending"
        cquery.aggs["23"].aggs["7"].avg.field = "AppsCompleted"
        cquery.aggs["23"].aggs["8"].avg.field = "AllocatedMB"
        cquery.aggs["23"].aggs["9"].avg.field = "AllocatedVCores"
        cquery.aggs["23"].aggs["10"].avg.field = "AllocatedContainers"
        cquery.aggs["23"].aggs["11"].avg.field = "AggregateContainersAllocated"
        cquery.aggs["23"].aggs["12"].avg.field = "AggregateContainersReleased"
        cquery.aggs["23"].aggs["13"].avg.field = "AvailableMB"
        cquery.aggs["23"].aggs["14"].avg.field = "AvailableVCores"
        cquery.aggs["23"].aggs["15"].avg.field = "PendingVCores"
        cquery.aggs["23"].aggs["16"].avg.field = "PendingContainers"
        cquery.aggs["23"].aggs["17"].avg.field = "ReservedMB"
        cquery.aggs["23"].aggs["18"].avg.field = "ReservedContainers"
        cquery.aggs["23"].aggs["19"].avg.field = "ActiveUsers"
        cquery.aggs["23"].aggs["20"].avg.field = "ActiveApplications"
        cquery.aggs["23"].aggs["21"].avg.field = "AppAttemptFirstContainerAllocationDelayNumOps"
        cquery.aggs["23"].aggs["22"].avg.field = "AppAttemptFirstContainerAllocationDelayAvgTime"
        cqueryd = cquery.to_dict()
        return cqueryd

    def clusterMetricsQuery(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):

        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["2"].date_histogram.field = "@timestamp"
        cquery.aggs["2"].date_histogram.interval = qinterval
        cquery.aggs["2"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["2"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["2"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["2"].date_histogram.extended_bounds.max = qlte

        # Cluster Metrics
        cquery.aggs["2"].aggs["1"].avg.field = "NumActiveNMs"
        cquery.aggs["2"].aggs["3"].avg.field = "NumDecommissionedNMs"
        cquery.aggs["2"].aggs["4"].avg.field = "NumLostNMs"
        cquery.aggs["2"].aggs["5"].avg.field = "NumUnhealthyNMs"
        cquery.aggs["2"].aggs["6"].avg.field = "AMLaunchDelayNumOps"
        cquery.aggs["2"].aggs["7"].avg.field = "AMLaunchDelayAvgTime"
        cquery.aggs["2"].aggs["8"].avg.field = "AMRegisterDelayNumOps"
        cquery.aggs["2"].aggs["9"].avg.field = "AMRegisterDelayAvgTime"
        cquery.aggs["2"].aggs["10"].avg.field = "NumRebootedNMs"
        cqueryd = cquery.to_dict()
        return cqueryd

    def datanodeMetricsQuery(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):

        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["12"].date_histogram.field = "@timestamp"
        cquery.aggs["12"].date_histogram.interval = qinterval
        cquery.aggs["12"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["12"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["12"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["12"].date_histogram.extended_bounds.max = qlte

        # DataNode Metrics
        cquery.aggs["12"].aggs["1"].avg.field = "BytesWritten"
        cquery.aggs["12"].aggs["2"].avg.field = "TotalWriteTime"
        cquery.aggs["12"].aggs["3"].avg.field = "BytesRead"
        cquery.aggs["12"].aggs["4"].avg.field = "TotalReadTime"
        cquery.aggs["12"].aggs["5"].avg.field = "BlocksWritten"
        cquery.aggs["12"].aggs["6"].avg.field = "BlocksRead"
        cquery.aggs["12"].aggs["7"].avg.field = "BlocksReplicated"
        cquery.aggs["12"].aggs["8"].avg.field = "BlocksRemoved"
        cquery.aggs["12"].aggs["9"].avg.field = "BlocksVerified"
        cquery.aggs["12"].aggs["10"].avg.field = "BlockVerificationFailures"
        cquery.aggs["12"].aggs["11"].avg.field = "BlocksCached"
        cquery.aggs["12"].aggs["13"].avg.field = "BlocksUncached"
        cquery.aggs["12"].aggs["14"].avg.field = "ReadsFromLocalClient"
        cquery.aggs["12"].aggs["15"].avg.field = "ReadsFromRemoteClient"
        cquery.aggs["12"].aggs["16"].avg.field = "WritesFromLocalClient"
        cquery.aggs["12"].aggs["17"].avg.field = "WritesFromRemoteClient"
        cquery.aggs["12"].aggs["18"].avg.field = "BlocksGetLocalPathInfo"
        cquery.aggs["12"].aggs["19"].avg.field = "RemoteBytesRead"
        cquery.aggs["12"].aggs["20"].avg.field = "RemoteBytesWritten"
        cquery.aggs["12"].aggs["21"].avg.field = "RamDiskBlocksWrite"
        cquery.aggs["12"].aggs["22"].avg.field = "RamDiskBlocksWriteFallback"
        cquery.aggs["12"].aggs["23"].avg.field = "RamDiskBytesWrite"
        cquery.aggs["12"].aggs["24"].avg.field = "RamDiskBlocksReadHits"
        cquery.aggs["12"].aggs["25"].avg.field = "RamDiskBlocksEvicted"
        cquery.aggs["12"].aggs["27"].avg.field = "RamDiskBlocksEvictedWithoutRead"
        cquery.aggs["12"].aggs["28"].avg.field = "RamDiskBlocksEvictionWindowMsNumOps"
        cquery.aggs["12"].aggs["29"].avg.field = "RamDiskBlocksEvictionWindowMsAvgTime"
        cquery.aggs["12"].aggs["30"].avg.field = "RamDiskBlocksLazyPersisted"
        cquery.aggs["12"].aggs["31"].avg.field = "RamDiskBlocksDeletedBeforeLazyPersisted"
        cquery.aggs["12"].aggs["32"].avg.field = "RamDiskBytesLazyPersisted"
        cquery.aggs["12"].aggs["33"].avg.field = "RamDiskBlocksLazyPersistWindowMsNumOps"
        cquery.aggs["12"].aggs["34"].avg.field = "RamDiskBlocksLazyPersistWindowMsAvgTime"
        cquery.aggs["12"].aggs["35"].avg.field = "FsyncCount"
        cquery.aggs["12"].aggs["36"].avg.field = "VolumeFailures"
        cquery.aggs["12"].aggs["37"].avg.field = "DatanodeNetworkErrors"
        cquery.aggs["12"].aggs["38"].avg.field = "ReadBlockOpNumOps"
        cquery.aggs["12"].aggs["39"].avg.field = "ReadBlockOpAvgTime"
        cquery.aggs["12"].aggs["40"].avg.field = "CopyBlockOpNumOps"
        cquery.aggs["12"].aggs["41"].avg.field = "CopyBlockOpAvgTime"
        cquery.aggs["12"].aggs["42"].avg.field = "ReplaceBlockOpNumOps"
        cquery.aggs["12"].aggs["43"].avg.field = "ReplaceBlockOpAvgTime"
        cquery.aggs["12"].aggs["44"].avg.field = "HeartbeatsNumOps"
        cquery.aggs["12"].aggs["45"].avg.field = "HeartbeatsAvgTime"
        cquery.aggs["12"].aggs["46"].avg.field = "BlockReportsNumOps"
        cquery.aggs["12"].aggs["47"].avg.field = "BlockReportsAvgTime"
        cquery.aggs["12"].aggs["48"].avg.field = "IncrementalBlockReportsNumOps"
        cquery.aggs["12"].aggs["49"].avg.field = "IncrementalBlockReportsAvgTime"
        cquery.aggs["12"].aggs["50"].avg.field = "CacheReportsNumOps"
        cquery.aggs["12"].aggs["51"].avg.field = "CacheReportsAvgTime"
        cquery.aggs["12"].aggs["52"].avg.field = "PacketAckRoundTripTimeNanosNumOps"
        cquery.aggs["12"].aggs["53"].avg.field = "FlushNanosNumOps"
        cquery.aggs["12"].aggs["54"].avg.field = "FlushNanosAvgTime"
        cquery.aggs["12"].aggs["55"].avg.field = "FsyncNanosNumOps"
        cquery.aggs["12"].aggs["56"].avg.field = "FsyncNanosAvgTime"
        cquery.aggs["12"].aggs["57"].avg.field = "SendDataPacketBlockedOnNetworkNanosNumOps"
        cquery.aggs["12"].aggs["58"].avg.field = "SendDataPacketBlockedOnNetworkNanosAvgTime"
        cquery.aggs["12"].aggs["59"].avg.field = "SendDataPacketTransferNanosNumOps"
        cquery.aggs["12"].aggs["60"].avg.field = "SendDataPacketTransferNanosAvgTime"
        cquery.aggs["12"].aggs["61"].avg.field = "WriteBlockOpNumOps"
        cquery.aggs["12"].aggs["62"].avg.field = "WriteBlockOpAvgTime"
        cquery.aggs["12"].aggs["63"].avg.field = "BlockChecksumOpNumOps"
        cquery.aggs["12"].aggs["64"].avg.field = "BlockChecksumOpAvgTime"
        cqueryd = cquery.to_dict()
        return cqueryd

    def fsopDurationsQuery(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):
        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["2"].date_histogram.field = "@timestamp"
        cquery.aggs["2"].date_histogram.interval = qinterval
        cquery.aggs["2"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["2"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["2"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["2"].date_histogram.extended_bounds.max = qlte

        # FSOpDuration metrics
        cquery.aggs["2"].aggs["1"].avg.field = "ContinuousSchedulingRunNumOps"
        cquery.aggs["2"].aggs["3"].avg.field = "ContinuousSchedulingRunAvgTime"
        cquery.aggs["2"].aggs["4"].avg.field = "ContinuousSchedulingRunStdevTime"
        cquery.aggs["2"].aggs["5"].avg.field = "ContinuousSchedulingRunIMinTime"
        cquery.aggs["2"].aggs["6"].avg.field = "ContinuousSchedulingRunIMaxTime"
        cquery.aggs["2"].aggs["7"].avg.field = "ContinuousSchedulingRunMinTime"
        cquery.aggs["2"].aggs["8"].avg.field = "ContinuousSchedulingRunMaxTime"
        cquery.aggs["2"].aggs["9"].avg.field = "ContinuousSchedulingRunINumOps"
        cquery.aggs["2"].aggs["10"].avg.field = "NodeUpdateCallNumOps"
        cquery.aggs["2"].aggs["11"].avg.field = "NodeUpdateCallAvgTime"
        cquery.aggs["2"].aggs["12"].avg.field = "NodeUpdateCallStdevTime"
        cquery.aggs["2"].aggs["13"].avg.field = "NodeUpdateCallMinTime"
        cquery.aggs["2"].aggs["14"].avg.field = "NodeUpdateCallIMinTime"
        cquery.aggs["2"].aggs["15"].avg.field = "NodeUpdateCallMaxTime"
        cquery.aggs["2"].aggs["16"].avg.field = "NodeUpdateCallINumOps"
        cquery.aggs["2"].aggs["17"].avg.field = "UpdateThreadRunNumOps"
        cquery.aggs["2"].aggs["18"].avg.field = "UpdateThreadRunAvgTime"
        cquery.aggs["2"].aggs["19"].avg.field = "UpdateThreadRunStdevTime"
        cquery.aggs["2"].aggs["20"].avg.field = "UpdateThreadRunIMinTime"
        cquery.aggs["2"].aggs["21"].avg.field = "UpdateThreadRunMinTime"
        cquery.aggs["2"].aggs["22"].avg.field = "UpdateThreadRunMaxTime"
        cquery.aggs["2"].aggs["23"].avg.field = "UpdateThreadRunINumOps"
        cquery.aggs["2"].aggs["24"].avg.field = "UpdateCallNumOps"
        cquery.aggs["2"].aggs["25"].avg.field = "UpdateCallAvgTime"
        cquery.aggs["2"].aggs["26"].avg.field = "UpdateCallStdevTime"
        cquery.aggs["2"].aggs["27"].avg.field = "UpdateCallIMinTime"
        cquery.aggs["2"].aggs["28"].avg.field = "UpdateCallMinTime"
        cquery.aggs["2"].aggs["29"].avg.field = "UpdateCallMaxTime"
        cquery.aggs["2"].aggs["30"].avg.field = "UpdateCallINumOps"
        cquery.aggs["2"].aggs["31"].avg.field = "PreemptCallNumOps"
        cquery.aggs["2"].aggs["32"].avg.field = "PreemptCallAvgTime"
        cquery.aggs["2"].aggs["33"].avg.field = "PreemptCallStdevTime"
        cquery.aggs["2"].aggs["34"].avg.field = "PreemptCallINumOps"
        cqueryd = cquery.to_dict()
        return cqueryd

    def shuffleQuery(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):
        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["2"].date_histogram.field = "@timestamp"
        cquery.aggs["2"].date_histogram.interval = qinterval
        cquery.aggs["2"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["2"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["2"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["2"].date_histogram.extended_bounds.max = qlte

        #Shuffle metrics
        cquery.aggs["2"].aggs["1"].avg.field = "ShuffleConnections"
        cquery.aggs["2"].aggs["3"].avg.field = "ShuffleOutputBytes"
        cquery.aggs["2"].aggs["4"].avg.field = "ShuffleOutputsFailed"
        cquery.aggs["2"].aggs["5"].avg.field = "ShuffleOutputsOK"
        cqueryd = cquery.to_dict()
        return cqueryd

    def queryByProcess(self, qstring, qgte, qlte, qsize, qinterval, wildCard=True, qtformat="epoch_millis",
                            qmin_doc_count=1):
        cquery = Dict()
        cquery.query.filtered.query.query_string.query = qstring
        cquery.query.filtered.query.query_string.analyze_wildcard = wildCard
        cquery.query.filtered.filter.bool.must = [
            {"range": {"@timestamp": {"gte": qgte, "lte": qlte, "format": qtformat}}}]
        cquery.query.filtered.filter.bool.must_not = []
        cquery.size = qsize

        cquery.aggs["2"].date_histogram.field = "@timestamp"
        cquery.aggs["2"].date_histogram.interval = qinterval
        cquery.aggs["2"].date_histogram.time_zone = "Europe/Helsinki"
        cquery.aggs["2"].date_histogram.min_doc_count = qmin_doc_count
        cquery.aggs["2"].date_histogram.extended_bounds.min = qgte
        cquery.aggs["2"].date_histogram.extended_bounds.max = qlte

        cquery.fields = ["*", "_source"]
        cquery.script_fields = {}
        cquery.fielddata_fields = ["@timestamp"]

        cquery.sort = [{"@timestamp": {"order": "desc", "unmapped_type": "boolean"}}]
        cqueryd = cquery.to_dict()
        return cqueryd


class DataFormatter:

    def __init__(self):
        self.fmHead = 0

    def filterColumns(self, df, lColumns):
        '''
        :param df: -> dataframe
        :param lColumns: -> column names
        :return: -> filtered df
        '''
        if not isinstance(lColumns, list):
            app.logger.error('[%s] : [ERROR] Dataformatter filter method expects list of column names not %s',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(lColumns))
        if not lColumns in df.columns.values:
            app.logger.error('[%s] : [ERROR] Dataformatter filter method unknown columns %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), lColumns)
        return df[lColumns]

    def filterRows(self, df, ld, gd=0):
        '''
        :param df: -> dataframe
        :param ld: -> less then key based timeframe in utc
        :param gd: -> greter then key based timeframe in utc
        :return: -> new filtered dataframe
        '''
        if gd:
            try:
                df = df[df.key > gd]
                return df[df.key < ld]
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Dataformatter filter method row exited with %s and %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
        else:
            try:
                return df[df.key < ld]
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Dataformatter filter method row exited with %s and %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)

    def dropColumns(self, df, lColumns, cp=True):
        '''
        Inplace true means the selected df will be modified
        :param df: dataframe
        :param lColumns: filtere clolumns
        :param cp: create new df
        '''
        if cp:
            try:
                return df.drop(lColumns, axis=1)
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Dataformatter filter method drop columns exited with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
        else:
            try:
                df.drop(lColumns, axis=1, inplace=True)
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Dataformatter filter method drop columns exited with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            return 0

    def fillMissing(self, df):
        df.fillna(0, inplace=True)

    def dropMissing(self, df):
        df.dropna(axis=1, how='all', inplace=True)

    def chainMerge(self, lFiles, colNames, iterStart=1):
        '''
        :param lFiles: -> list of files to be opened
        :param colNames: -> dict with master column names
        :param iterStart: -> start of iteration default is 1
        :return: -> merged dataframe
        '''
        #Parsing colNames
        slaveCol = {}
        for k, v in colNames.iteritems():
            slaveCol[k] = '_'.join([v.split('_')[0], 'slave'])

        dfList = []
        if all(isinstance(x, str) for x in lFiles):
            for f in lFiles:
                df = pd.read_csv(f)
                dfList.append(df)
        elif all(isinstance(x, pd.DataFrame) for x in lFiles):
            dfList = lFiles
        else:
            app.logger.error('[%s] : [ERROR] Cannot merge type %s ',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(type(dfList[0])))
        # Get first df and set as master
        current = dfList[0].rename(columns=colNames)
        for i, frame in enumerate(dfList[1:], iterStart):
            iterSlave = {}
            for k, v in slaveCol.iteritems():
                iterSlave[k] = v+str(i)
            current = current.merge(frame).rename(columns=iterSlave)
        #current.to_csv(mergedFile)
        # current.set_index('key', inplace=True)
        return current

    def chainMergeNR(self, interface, memory, load, packets):
        '''
        :return: -> merged dataframe System metrics
        '''
        lFiles = [interface, memory, load, packets]
        return self.listMerge(lFiles)

    def chainMergeDFS(self, dfs, dfsfs, fsop):
        '''
        :return: -> merged dfs metrics
        '''
        lFiles = [dfs, dfsfs, fsop]
        return self.listMerge(lFiles)

    def chainMergeCluster(self, clusterMetrics, queue, jvmRM):
        '''
        :return: -> merged cluster metrics
        '''
        lFiles = [clusterMetrics, queue, jvmRM]

        return self.listMerge(lFiles)

    def chainMergeNM(self, lNM, lNMJvm, lShuffle):
        '''
        :return: -> merged namemanager metrics
        '''

        # Read files
        # Get column headers and gen dict with new col headers
        colNamesNM = csvheaders2colNames(lNM[0], 'slave1')
        df_NM = self.chainMerge(lNM, colNamesNM, iterStart=2)

        colNamesJVMNM = csvheaders2colNames(lNMJvm[0], 'slave1')
        df_NM_JVM = self.chainMerge(lNMJvm, colNamesJVMNM, iterStart=2)

        colNamesShuffle = csvheaders2colNames(lShuffle[0], 'slave1')
        df_Shuffle = self.chainMerge(lShuffle, colNamesShuffle, iterStart=2)

        return df_NM, df_NM_JVM, df_Shuffle

    def chainMergeDN(self, lDN):
        '''
        :return: -> merged datanode metrics
        '''
        # Read files
        # Get column headers and gen dict with new col headers
        colNamesDN = csvheaders2colNames(lDN[0], 'slave1')
        df_DN = self.chainMerge(lDN, colNamesDN, iterStart=2)
        return df_DN

    def listMerge(self, lFiles):
        '''
        :param lFiles: -> list of files
        :return: merged dataframe
        :note: Only use if dataframes have divergent headers
        '''
        dfList = []
        if all(isinstance(x, str) for x in lFiles):
            for f in lFiles:
                if not f:
                    app.logger.warning('[%s] : [WARN] Found empty string instead of abs path ...',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                try:
                    df = pd.read_csv(f)
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Cannot load file at %s exiting',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), f)
                dfList.append(df)
        elif all(isinstance(x, pd.DataFrame) for x in lFiles):
            dfList = lFiles
        else:
            app.logger.error('[%s] : [INFO] Cannot merge type %s',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(type(dfList[0])))
        try:
            current = reduce(lambda x, y: pd.merge(x, y, on='key'), dfList)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Merge dataframes exception %s with args %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            app.logger.error('[%s] : [ERROR] Merge dataframes exception df list %s',
                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), dfList)
            current = 0
        # current.set_index('key', inplace=True)
        return current

    def df2csv(self, dataFrame, mergedFile):
        '''
        :param dataFrame: dataframe to save as csv
        :param mergedFile: merged csv file name
        :return:
        '''
        # dataFrame.set_index('key', inplace=True) -> if inplace it modifies all copies of df including
        # in memory resident ones
        try:
            kDF = dataFrame.set_index('key')
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Cannot write dataframe exception %s with arguments %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)

        kDF.to_csv(mergedFile)

    def chainMergeSystem(self, linterface, lload, lmemory, lpack):
        app.logger.info('[%s] : [INFO] Startig system metrics merge .......',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

        colNamesInterface = {'rx': 'rx_master', 'tx': 'tx_master'}
        df_interface = self.chainMerge(linterface, colNamesInterface)

        app.logger.info('[%s] : [INFO] Interface metrics merge complete',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

        colNamesPacket = {'rx': 'rx_master', 'tx': 'tx_master'}
        df_packet = self.chainMerge(lpack, colNamesPacket)

        app.logger.info('[%s] : [INFO] Packet metrics merge complete',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

        colNamesLoad = {'shortterm': 'shortterm_master', 'midterm': 'midterm_master', 'longterm': 'longterm_master'}
        df_load = self.chainMerge(lload, colNamesLoad)

        app.logger.info('[%s] : [INFO] Load metrics merge complete',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

        colNamesMemory = {'cached': 'cached_master', 'buffered': 'buffered_master',
                          'used': 'used_master', 'free': 'free_master'}
        df_memory = self.chainMerge(lmemory, colNamesMemory)
        app.logger.info('[%s] : [INFO] Memory metrics merge complete',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

        app.logger.info('[%s] : [INFO] Sistem metrics merge complete',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

        return df_interface, df_load, df_memory, df_packet

    def mergeFinal(self, dfs, cluster, nodeMng, jvmnodeMng, dataNode, jvmNameNode, shuffle, system):
        lFile = [dfs, cluster, nodeMng, jvmnodeMng, dataNode, jvmNameNode, shuffle, system]
        merged_df = self.listMerge(lFile)
        merged_df.sort_index(axis=1, inplace=True)
        self.fillMissing(merged_df)
        self.fmHead = list(merged_df.columns.values)
        return merged_df

    def dict2csv(self, response, query, filename, df=False):
        '''
        :param response: elasticsearch response
        :param query: elasticserch query
        :param filename: name of file
        :param df: if set to true method returns dataframe and doesn't save to file.
        :return: 0 if saved to file and dataframe if not
        '''
        requiredMetrics = []
        app.logger.info('[%s] : [INFO] Started response to csv conversion',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        # print "This is the query _------------_-> %s" %query
        # print "This is the response _------------_-> %s" %response
        for key, value in response['aggregations'].iteritems():
            for k, v in value.iteritems():
                for r in v:
                    dictMetrics = {}
                    # print "This is the dictionary ---------> %s " % str(r)
                    for rKey, rValue in r.iteritems():
                        if rKey == 'doc_count' or rKey == 'key_as_string':
                            pass
                        elif rKey == 'key':
                            app.logger.debug('[%s] : [DEBUG] Request has keys %s and  values %s',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), rKey, rValue)
                            # print "%s -> %s"% (rKey, rValue)
                            dictMetrics['key'] = rValue
                        elif query['aggs'].values()[0].values()[1].values()[0].values()[0].values()[0] =='type_instance.raw':
                            app.logger.debug('[%s] : [DEBUG] Detected Memory type aggregation', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                            # print "This is  rValue ________________> %s" % str(rValue)
                            # print "Keys of rValue ________________> %s" % str(rValue.keys())
                            for val in rValue['buckets']:
                                dictMetrics[val['key']] = val['1']['value']
                        else:
                            # print "Values -> %s" % rValue
                            # print "rKey -> %s" % rKey
                            # print "This is the rValue ___________> %s " % str(rValue)
                            app.logger.debug('[%s] : [DEBUG] Request has keys %s and flattened values %s',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), rKey, rValue['value'])
                            dictMetrics[rKey] = rValue['value']
                    requiredMetrics.append(dictMetrics)
        # print "Required Metrics -> %s" % requiredMetrics
        csvOut = os.path.join(outDir, filename)
        cheaders = []
        if query['aggs'].values()[0].values()[1].values()[0].values()[0].values()[0] == "type_instance.raw":
            app.logger.debug('[%s] : [DEBUG] Detected Memory type query', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            cheaders = requiredMetrics[0].keys()
        else:
            kvImp = {}

            for qKey, qValue in query['aggs'].iteritems():
                app.logger.info('[%s] : [INFO] Value aggs from query %s',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qValue['aggs'])
                for v, t in qValue['aggs'].iteritems():
                    kvImp[v] = t['avg']['field']
                    cheaders.append(v)

            cheaders.append('key')
            for key, value in kvImp.iteritems():
                cheaders[cheaders.index(key)] = value
            for e in requiredMetrics:
                for krep, vrep in kvImp.iteritems():
                    e[vrep] = e.pop(krep)
            app.logger.info('[%s] : [INFO] Dict translator %s',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(kvImp))
        app.logger.info('[%s] : [INFO] Headers detected %s',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(cheaders))
        if not df:
            try:
                with open(csvOut, 'wb') as csvfile:
                    w = csv.DictWriter(csvfile, cheaders)
                    w.writeheader()
                    for metrics in requiredMetrics:
                        w.writerow(metrics)
                csvfile.close()
            except EnvironmentError:
                app.logger.error('[%s] : [ERROR] File %s could not be created', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), csvOut)
                sys.exit(1)
            app.logger.info('[%s] : [INFO] Finished csv %s',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), filename)
            return 0
        else:
            df = pd.DataFrame(requiredMetrics)
            # df.set_index('key', inplace=True)
            app.logger.info('[%s] : [INFO] Created dataframe',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return df


class QueryEngine:
    def __init__(self, fqdn):
        self.esConnector = ESCoreConnector(fqdn)
        self.qConstructor = QueryConstructor()
        self.dformater = DataFormatter()

    def getCluster(self, tfrom, to, qsize, qinterval, index):
        app.logger.info('[%s] : [INFO] Querying Cluster metrics ...',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        queue, queue_file = self.qConstructor.queueResourceString()
        cluster, cluster_file = self.qConstructor.clusterMetricsSring()
        jvmResMng, jvmResMng_file = self.qConstructor.jvmResourceManagerString()
        qqueue = self.qConstructor.resourceQueueQuery(queue, tfrom, to, qsize, qinterval)
        qcluster = self.qConstructor.clusterMetricsQuery(cluster, tfrom, to, qsize, qinterval)
        qjvmResMng = self.qConstructor.jvmNNquery(jvmResMng, tfrom, to, qsize, qinterval)
        gqueue = self.esConnector.aggQuery(index, qqueue)
        print gqueue
        if not gqueue:
            return 0
        gcluster = self.esConnector.aggQuery(index, qcluster)
        gjvmResourceManager = self.esConnector.aggQuery(index, qjvmResMng)
        df_cluster = self.dformater.dict2csv(gcluster, qcluster, cluster_file, df=True)
        df_queue = self.dformater.dict2csv(gqueue, qqueue, queue_file, df=True)
        df_jvmResourceManager = self.dformater.dict2csv(gjvmResourceManager, qjvmResMng, jvmResMng_file, df=True)
        app.logger.info('[%s] : [INFO] Starting cluster merge ...',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        merged_cluster = self.dformater.chainMergeCluster(clusterMetrics=df_cluster, queue=df_queue,
                                                          jvmRM=df_jvmResourceManager)
        clusterReturn = merged_cluster
        app.logger.info('[%s] : [INFO] Finished cluster metrics query and aggregation',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        return clusterReturn

    def getDataNode(self, nodes, tfrom, to, qsize, qinterval, index):
        app.logger.info('[%s] : [INFO] Querying  Data Node metrics ...',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        lDN = []
        for node in nodes:
            datanode, datanode_file = self.qConstructor.datanodeString(node)
            qdatanode = self.qConstructor.datanodeMetricsQuery(datanode, tfrom, to, qsize,
                                                               qinterval)
            gdatanode = self.esConnector.aggQuery(index, qdatanode)
            if gdatanode['aggregations'].values()[0].values()[0]:
                lDN.append(self.dformater.dict2csv(gdatanode, qdatanode, datanode_file, df=True))
            else:
                app.logger.info('[%s] : [INFO] Empty response from  %s no datanode metrics!',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), node)

        app.logger.info('[%s] : [INFO] Querying  Data Node metrics complete',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))


        dn_merged = self.dformater.chainMergeDN(lDN=lDN)
        app.logger.info('[%s] : [INFO] Data Node metrics merge complete',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        return dn_merged

    def getDFS(self, tfrom, to, qsize, qinterval, index):
        # Query Strings
        app.logger.info('[%s] : [INFO] Querying DFS metrics...',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        dfs, dfs_file = self.qConstructor.dfsString()
        dfsFs, dfsFs_file = self.qConstructor.dfsFString()
        fsop, fsop_file = self.qConstructor.fsopDurationsString()

        # Query constructor
        qdfs = self.qConstructor.dfsQuery(dfs, tfrom, to, qsize, qinterval)
        qdfsFs = self.qConstructor.dfsFSQuery(dfsFs, tfrom, to, qsize, qinterval)
        qfsop = self.qConstructor.fsopDurationsQuery(fsop, tfrom, to, qsize, qinterval)

        # Execute query
        gdfs = self.esConnector.aggQuery(index, qdfs)
        gdfsFs = self.esConnector.aggQuery(index, qdfsFs)
        gfsop = self.esConnector.aggQuery(index, qfsop)

        df_dfs = self.dformater.dict2csv(gdfs, qdfs, dfs_file, df=True)
        df_dfsFs = self.dformater.dict2csv(gdfsFs, qdfsFs, dfsFs_file, df=True)
        df_fsop = self.dformater.dict2csv(gfsop, qfsop, fsop_file, df=True)

        app.logger.info('[%s] : [INFO] Querying DFS metrics complete.',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

        merged_DFS = self.dformater.chainMergeDFS(dfs=df_dfs, dfsfs=df_dfsFs, fsop=df_fsop)
        app.logger.info('[%s] : [INFO] DFS merge complete',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

        return merged_DFS

    def getNodeManager(self, nodes, tfrom, to, qsize, qinterval, index):

        app.logger.info('[%s] : [INFO] Querying  Node Manager and Shuffle metrics...',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        lNM = []
        ljvmNM = []
        lShuffle = []
        for node in nodes:
            nodeManager, nodeManager_file = self.qConstructor.nodeManagerString(node)
            jvmNodeManager, jvmNodeManager_file = self.qConstructor.jvmnodeManagerString(node)
            shuffle, shuffle_file = self.qConstructor.shuffleString(node)

            qnodeManager = self.qConstructor.yarnNodeManager(nodeManager, tfrom, to, qsize,
                                                             qinterval)
            qjvmNodeManager = self.qConstructor.jvmNNquery(jvmNodeManager, tfrom, to, qsize,
                                                           qinterval)
            qshuffle = self.qConstructor.shuffleQuery(shuffle, tfrom, to, qsize, qinterval)

            gnodeManagerResponse = self.esConnector.aggQuery(index, qnodeManager)
            if gnodeManagerResponse['aggregations'].values()[0].values()[0]:
                lNM.append(self.dformater.dict2csv(gnodeManagerResponse, qnodeManager, nodeManager_file, df=True))
            else:
                app.logger.info('[%s] : [INFO] Empty response from  %s no Node Manager detected!',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), node)

            gjvmNodeManagerResponse = self.esConnector.aggQuery(index, qjvmNodeManager)
            if gjvmNodeManagerResponse['aggregations'].values()[0].values()[0]:
                ljvmNM.append(
                    self.dformater.dict2csv(gjvmNodeManagerResponse, qjvmNodeManager, jvmNodeManager_file, df=True))
            else:
                app.logger.info('[%s] : [INFO] Empty response from  %s no Node Manager detected!',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), node)

            gshuffleResponse = self.esConnector.aggQuery(index, qshuffle)
            if gshuffleResponse['aggregations'].values()[0].values()[0]:
                lShuffle.append(self.dformater.dict2csv(gshuffleResponse, qshuffle, shuffle_file, df=True))
            else:
                app.logger.info('[%s] : [INFO] Empty response from  %s no shuffle metrics!',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), node)

        app.logger.info('[%s] : [INFO] Querying  Node Manager and Shuffle metrics complete...',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

        nm_merged, jvmnn_merged, shuffle_merged = self.dformater.chainMergeNM(lNM=lNM, lNMJvm=ljvmNM,
                                                                              lShuffle=lShuffle)
        app.logger.info('[%s] : [INFO] Node Manager Merge complete',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        return nm_merged, jvmnn_merged, shuffle_merged

    def getNameNode(self, tfrom, to, qsize, qinterval, index):
        app.logger.info('[%s] : [INFO] Querying  Name Node metrics ...',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

        jvmNameNodeString, jvmNameNode_file = self.qConstructor.jvmNameNodeString()
        qjvmNameNode = self.qConstructor.jvmNNquery(jvmNameNodeString, tfrom, to, qsize, qinterval)
        gjvmNameNode = self.esConnector.aggQuery(index, qjvmNameNode)
        df_NN = self.dformater.dict2csv(gjvmNameNode, qjvmNameNode, jvmNameNode_file, df=True)
        # df_NN.set_index('key', inplace=True)
        returnNN = df_NN

        app.logger.info('[%s] : [INFO] Querying  Name Node metrics complete',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        return returnNN

    def getSystemMetrics(self, nodes, tfrom, to, qsize, qinterval, index):
        lload = []
        lmemory = []
        linterface = []
        lpack = []
        app.logger.info('[%s] : [INFO] Querying System metrics ...',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        for node in nodes:
            load, load_file = self.qConstructor.loadString(node)
            memory, memory_file = self.qConstructor.memoryString(node)
            interface, interface_file = self.qConstructor.interfaceString(node)
            packet, packet_file = self.qConstructor.packetString(node)

            # Queries
            qload = self.qConstructor.systemLoadQuery(load, tfrom, to, qsize, qinterval)
            qmemory = self.qConstructor.systemMemoryQuery(memory, tfrom, to, qsize, qinterval)
            qinterface = self.qConstructor.systemInterfaceQuery(interface, tfrom, to, qsize, qinterval)
            qpacket = self.qConstructor.systemInterfaceQuery(packet, tfrom, to, qsize, qinterval)

            # Execute query and convert response to csv
            qloadResponse = self.esConnector.aggQuery(index, qload)
            gmemoryResponse = self.esConnector.aggQuery(index, qmemory)
            ginterfaceResponse = self.esConnector.aggQuery(index, qinterface)
            gpacketResponse = self.esConnector.aggQuery(index, qpacket)

            linterface.append(self.dformater.dict2csv(ginterfaceResponse, qinterface, interface_file, df=True))
            lmemory.append(self.dformater.dict2csv(gmemoryResponse, qmemory, memory_file, df=True))
            lload.append(self.dformater.dict2csv(qloadResponse, qload, load_file, df=True))
            lpack.append(self.dformater.dict2csv(gpacketResponse, qpacket, packet_file, df=True))

        # Merge and rename by node system Files
        df_interface, df_load, df_memory, df_packet = self.dformater.chainMergeSystem(linterface=linterface,
                                                                                      lload=lload, lmemory=lmemory,
                                                                                      lpack=lpack)
        merged_df = self.dformater.chainMergeNR(interface=df_interface, memory=df_memory, load=df_load,
                                                packets=df_packet)
        app.logger.info('[%s] : [INFO] Querying System metrics complete',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        return merged_df

    def merge(self, listDataframes):
        merged = self.dformater.listMerge(listDataframes)
        return merged

    def toDict(self, dataframe):
        res = dataframe.to_dict()
        return res

    def toCSV(self, dataframe, location):
        dataframe.to_csv(location)


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hd")
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
            testQuery = queryConstructor(1438939155342, 1438940055342,
                                         "hostname:\"dice.cdh5.s4.internal\" AND serviceType:\"dfs\"")
            metrics = ['type', '@timestamp', 'host', 'job_id', 'hostname', 'AvailableVCores']
            test, test2 = queryESCore(testQuery, debug=True)
            dict2CSV(test)


if __name__ == '__main__':
    # ElasticSearch object that defines the endpoint
    es = Elasticsearch('85.120.206.43')
    if len(sys.argv) == 1:  # only for development
        testQuery = queryConstructor(1438939155342, 1438940055342,
                                     "hostname:\"dice.chd5.mng.internal\" AND serviceType:\"dfs\"")
        print testQuery
        # metrics = ['type','@timestamp','host','job_id','hostname','RamDiskBlocksDeletedBeforeLazyPersisted']
        test, test2 = queryESCore(testQuery, allm=True, debug=True)
        dict2CSV(test)
        print test2
        # queryESCoreCSV(test, True)
    else:
        main(sys.argv[1:])
