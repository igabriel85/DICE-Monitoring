"""

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
"""
#!flask/bin/python


from flask.ext.restplus import Api, Resource, fields
from flask import Flask, jsonify
from flask import request
from flask import redirect
from flask import make_response
from flask import abort
from flask import url_for
from flask import render_template
from flask import Response
from flask import send_file
from flask import send_from_directory
from flask import copy_current_request_context
import os
import sys
import signal
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
import jinja2
import requests
import shutil
# from werkzeug import secure_filename #unused
from urlparse import urlparse
# DICE Imports
from pyESController import *
from pysshCore import *
from dmonPerfMon import *
from app import *
from pyUtil import *
# from threadRequest import *
from greenletThreads import *
# import Queue
# from threading import Thread
import requests
import psutil
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime
import glob
import multiprocessing
#from threadRequest import getStormLogs
from artifactRepository import *

# directory Location
outDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
tmpDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
cfgDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')
baseDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db')
pidDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pid')
logDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
credDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys')


esDir = '/opt/elasticsearch'
lsCDir = '/etc/logstash/conf.d/'

# D-Mon Supported frameworks
lFrameworks = ['hdfs', 'yarn', 'spark', 'storm', 'cassandra', 'mongodb']
# app = Flask("D-MON")
# api = Api(app, version='0.2.0', title='DICE MONitoring API',
#     description='RESTful API for the DICE Monitoring Platform  (D-MON)',
# )

# changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
# dmon = api.namespace('dmon', description='D-MON operations')

#Initialize detect service
servDet = DetectBDService()

# argument parser
dmonAux = api.parser()
dmonAux.add_argument('redeploy', type=str, required=False,
                     help='Redeploys configuration of Auxiliary components on the specified node.')
dmonAuxAll = api.parser()
dmonAuxAll.add_argument('redeploy-all', type=str, required=False,
                        help='Redeploys configuration of Auxiliary components on all nodes.')
# pQueryES.add_argument('task',type=str, required=True, help='The task details', location='form')


# descripes universal json @api.marshal_with for return or @api.expect for payload model
queryES = api.model('query details Model', {
    'fname': fields.String(required=False, default="output", description='Name of output file.'),
    'size': fields.Integer(required=True, default=500, description='Number of record'),
    'ordering': fields.String(required=True, default='desc', description='Ordering of records'),
    'queryString': fields.String(required=True, default="host:\"dice.cdh5.s4.internal\" AND serviceType:\"dfs\""
                                 , description='ElasticSearc Query'),
    'tstart': fields.Integer(required=True, default="now-1d", description='Start Date'),
    'tstop': fields.Integer(required=False, default="None", description='Stop Date'),
    'metrics': fields.List(fields.String(required=False, default=' ', description='Desired Metrics')),
    'index': fields.String(required=False, default='logstash-*', description='Name of ES Core index')
})

queryESEnhanced = api.model('aggregated query details Model', {
    'fname': fields.String(required=False, default="output", description='Name of output file.'),
    'interval': fields.String(required=False, default="10s", description='Aggregation interval.'),
    'size': fields.Integer(required=True, default=0, description='Number of record'),
    'tstart': fields.Integer(required=True, default="now-1d", description='Start Date'),
    'tstop': fields.Integer(required=False, default="now", description='Stop Date'),
    'aggregation': fields.String(required=False, default="system", description='Aggregation'),
    'index': fields.String(required=False, default='logstash-*', description='Name of ES Core index')
})

#Nested ENhanced JSON input
dDMONQueryEnh = api.model('queryESEnh Model', {
    'DMON':fields.Nested(queryESEnhanced, description="Query details")
})

# Nested JSON input
dMONQuery = api.model('queryES Model', {
    'DMON': fields.Nested(queryES, description="Query details")
})

nodeSubmitCont = api.model('Submit Node Model Info', {
    'NodeName': fields.String(required=True, description="Node FQDN"),
    'NodeIP': fields.String(required=True, description="Node IP"),
    'NodeOS': fields.String(required=False, description="Node OS"),
    'key': fields.String(required=False, description="Node Pubilc key"),
    'username': fields.String(required=False, description="Node User Name"),
    'password': fields.String(required=False, description="Node Password"),
    'LogstashInstance': fields.String(required=False, description='Logstash Server Endpoint')
})

nodeDelList = api.model('Delete node list', {
    'Nodes': fields.List(fields.String(required=True, default='node_name', description='Node FQDN'))
})

nodeSubmit = api.model('Submit Node Model', {
    'Nodes': fields.List(fields.Nested(nodeSubmitCont, required=True, description="Submit Node details"))
})

esCore = api.model('Submit ES conf', {
    'HostFQDN': fields.String(required=True, description='Host FQDN'),
    'IP': fields.String(required=True, description='Host IP'),
    'OS': fields.String(required=False, default='unknown', description='Host OS'),
    'NodeName': fields.String(required=True, description='ES Host Name'),
    'NodePort': fields.Integer(required=False, default=9200, description='ES Port'),
    'ESClusterName': fields.String(required=True, description='ES Host Name'),
    'ESCoreHeap': fields.String(required=False, default='4g', description='ES Heap size'),
    'MasterNode': fields.Boolean(required=False, description='ES Master'),
    'DataNode': fields.Boolean(required=False, description='ES Data'),
    'NumOfShards': fields.Integer(required=False, default=1, description='Number of shards'),
    'NumOfReplicas': fields.Integer(required=False, default=0, description='Number of replicas'),
    'FieldDataCacheSize': fields.String(required=False, default='20%', description='Field cache  size'),
    'FieldDataCacheExpires': fields.String(required=False, default='6h', description='Field cache expiration'),
    'FieldDataCacheFilterSize': fields.String(required=False, default='20%', description='Field cache filter size'),
    'FieldDataCacheFilterExpires': fields.String(required=False, default='6h',
                                                 description='Field cache filter expiration'),
    'IndexBufferSize': fields.String(required=False, default='30%', description='Index buffer size'),
    'MinShardIndexBufferSize': fields.String(required=False, default='12mb', description='Min Shard index buffer size'),
    'MinIndexBufferSize': fields.String(required=False, default='96mb', description='Min index buffer size'),
    'ESCoreDebug': fields.Boolean(required=False, default=1, description='Debug logs')
})

kbCore = api.model('Submit KB conf', {
    'HostFQDN': fields.String(required=True, description='Host FQDN'),
    'IP': fields.String(required=True, description='Host IP'),
    'OS': fields.String(required=False, default='unknown', description='Host OS'),
    'KBPort': fields.Integer(required=False, default=5601, description='KB Port'),
})

nodeUpdate = api.model('Update Node Model Info', {
    'IP': fields.String(required=True, description="Node IP"),
    'OS': fields.String(required=False, description="Node OS"),
    'Key': fields.String(required=False, description="Node Public key"),
    'User': fields.String(required=False, description="Node User Name"),
    'Password': fields.String(required=False, description="Node Password"),
    'LogstashInstance': fields.String(required=False, description='Logstash Server Endpoint')
})

nodeRoles = api.model('Update Node Role Model Info', {
    'Roles': fields.List(fields.String(required=True, default='yarn', description='Node Roles'))
})

listNodesRolesInternal = api.model('Update List Node Role Model Info Nested', {
    "NodeName": fields.String(required=True, description="Node FQDN"),
    "Roles": fields.List(fields.String(required=True, default='yarn', description='Node Roles'))
})

listNodeRoles = api.model('Update List Node Role Model Info', {
    "Nodes": fields.List(
        fields.Nested(listNodesRolesInternal, required=True, description='List of nodes and their roles'))
})

lsCore = api.model('Submit LS conf', {
    'HostFQDN': fields.String(required=True, description='Host FQDN'),
    'IP': fields.String(required=True, description='Host IP'),
    'OS': fields.String(required=False, description='Host OS'),
    'LPort': fields.Integer(required=False, default=5000, description='Lumberjack port'),
    'udpPort': fields.String(required=False, default=25826, description='UDP Collectd Port'),
    'LSCoreHeap': fields.String(required=False, default='512m', description='Heap size for LS server'),
    'LSCoreWorkers': fields.String(required=False, default='4', description='Number of workers for LS server'),
    'ESClusterName': fields.String(required=True, default='diceMonit', description='ES cluster name'),
# TODO: use as foreign key same as ClusterName in esCore
    'LSCoreStormEndpoint': fields.String(required=False, default='None', description='Storm REST Endpoint'),
    'LSCoreStormPort': fields.String(required=False, default='None', description='Storm REST Port'),
    'LSCoreStormTopology': fields.String(required=False, default='None', description='Storm Topology ID'),
    'LSCoreSparkEndpoint': fields.String(required=False, default='None', description='Spark REST Endpoint'),
    'LSCoreSparkPort': fields.String(required=False, default='None', description='Spark REST Port'),
    'Index': fields.String(required=False, default='logstash', description='ES index name to be used')
})
# monNodes = api.model('Monitored Nodes',{
# 	'Node':fields.List(fields.Nested(nodeDet, description="FQDN and IP of nodes"))
# 	})
# nodeDet = api.model('Node Info',{
# 	'FQDN' : field
# 	})#[{'FQDN':'IP'}]

certModel = api.model('Update Cert', {
    'Certificate': fields.String(required=False, description='Certificate')
})

resInterval = api.model('Polling interval', {
    'Spark': fields.String(required=False, default='15', description='Polling period for Spark metrics'),
    'Storm': fields.String(required=False, default='60', description='Polling period for Storm metrics'),
    'System': fields.String(required=False, default='15', description='Polling period for System metrics'),
    'YARN': fields.String(required=False, default='15', description='Polling period for YARN metrics')
})

yarnHistorySettings = api.model('Settings for Yarn history server', {
    'NodeIP': fields.String(required=False, default='127.0.0.1', description='History Server IP'),
    'NodePort': fields.Integer(required=False, default=19888, description='History Server Port'),
    'Polling': fields.String(required=False, default=30, description='History Server Polling Period')
})

mongoDBConf = api.model('Settings for MongoDB', {
    'MongoHost': fields.String(required=True, default='127.0.0.1', description='MongoDB Host'),
    'MongoPort': fields.String(required=True, default='27017', description='MongoDB Port'),
    'MongoUser': fields.String(required=False, default='', description='MongoDB User'),
    'MongoPassword': fields.String(required=False, default='27017', description='MongoDB Password'),
    'MongoDBs': fields.String(required=False, default='admin', description='MongoDBs')
})

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(baseDir, 'dmon.db')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db.create_all()


@dmon.route('/v1/log')
class DmonLog(Resource):
    def get(self):
        try:
            logfile = open(os.path.join(logDir, 'dmon-controller.log'), 'r')
        except EnvironmentError:
            response = jsonify({'EnvError': 'file not found'})
            response.status_code = 500
            return response
        return Response(logfile, status=200, mimetype='text/plain')


@dmon.route('/v1/observer/applications')
class ObsApplications(Resource):
    def get(self):
        qApps = db.session.query(dbApp.appName, dbApp.appVersion, dbApp.startTime, dbApp.stopTime, dbApp.jobID).all()
        appDict = {}
        for a in qApps:
            appDict[a[0]] = {'ver': a[1], 'start': a[2], 'stop': a[3], 'status': a[4]}
        response = jsonify(appDict)
        response.status_code = 200
        return response


@dmon.route('/v1/observer/applications/<appID>')
@api.doc(params={'appID': 'Application identification'})
class ObsAppbyID(Resource):
    def get(self, appID):
        qApp = dbApp.query.filter_by(appName=appID).first()
        if qApp is None:
            response = jsonify({'Status': 'Warning', 'Message': appID + ' not registered'})
            response.status_code = 404
            app.logger.warning('[%s] : [INFO] Application %s is not registered',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), )
            return response
        # todo sync with dev brach to add missing code
        response = jsonify({qApp.appName: {'ver': qApp.appVersion, 'start': qApp.startTime, 'stop': qApp.stopTime, 'status': qApp.jobID}})
        response.status_code = 200
        return response


@dmon.route('/v1/observer/nodes')
class NodesMonitored(Resource):
    # @api.marshal_with(monNodes) # this is for response
    def get(self):
        nodeList = []
        nodesAll = db.session.query(dbNodes.nodeFQDN, dbNodes.nodeIP).all()
        if nodesAll is None:
            response = jsonify({'Status': 'No monitored nodes found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No nodes registered',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        for nl in nodesAll:
            nodeDict = {}
            app.logger.info('[%s] : [INFO] Nodes - > %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nl[0]))
            # print >> sys.stderr, nl[0]
            nodeDict.update({nl[0]: nl[1]})
            nodeList.append(nodeDict)
        response = jsonify({'Nodes': nodeList})
        response.status_code = 200
        app.logger.info('[%s] : [INFO] Node list is: %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nodeList))
        return response


@dmon.route('/v1/observer/nodes/<nodeFQDN>')
@api.doc(params={'nodeFQDN': 'Nodes FQDN'})
class NodeStatus(Resource):
    def get(self, nodeFQDN):
        qNode = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
        if qNode is None:
            response = jsonify({'Status': 'Node ' + nodeFQDN + ' not found!'})
            response.status_code = 404
            app.logger.warn('[%s] : [WARN] Node  %s not found',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nodeFQDN))
            return response
        else:
            response = jsonify({nodeFQDN: {
                'Status': qNode.nStatus,
                'IP': qNode.nodeIP,
                'Monitored': qNode.nMonitored,
                'OS': qNode.nodeOS,
                'LSInstance': qNode.nLogstashInstance
            }})
            response.status_code = 200
            app.logger.info('[%s] : [INFO] Node info -> Status:%s, IP:%s, Monitored:%s, OS:%s, LSInstance: %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qNode.nStatus,
                            qNode.nodeIP, qNode.nMonitored, qNode.nodeOS, qNode.nLogstashInstance)
            return response


@dmon.route('/v1/observer/nodes/<nodeFQDN>/roles')
@api.doc(params={'nodeFQDN': 'Nodes FQDN'})
class NodeStatusServices(Resource):
    def get(self, nodeFQDN):
        qNode = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
        if qNode.nRoles == 'unknown':
            response = jsonify({'Status': 'No known service on ' + nodeFQDN})
            response.status_code = 200
            app.logger.warning('[%s] : [WARN] No known service on %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nodeFQDN))
            return response
        else:
            roleList = qNode.nRoles
            response = jsonify({'Roles': roleList.split()})
            response.status_code = 200
            app.logger.info('[%s] : [INFO] Node roles %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(roleList.split()))
            return response


@dmon.route('/v1/observer/query/<ftype>')
@api.doc(params={'ftype': 'Output type'})
class QueryEsCore(Resource):
    # @api.doc(parser=pQueryES) #inst parser
    # @api.marshal_with(dMONQuery) # this is for response
    @api.expect(dMONQuery)  # this is for payload
    def post(self, ftype):
        # args = pQueryES.parse_args()#parsing query arguments in URI
        supportType = ["csv", "json", "plain", "oslc"]
        if ftype not in supportType:
            response = jsonify({'Supported types': supportType, "Submitted Type": ftype})
            response.status_code = 415
            app.logger.warn('[%s] : [WARN] Unsuported output type %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), ftype)
            return response
        if ftype == 'oslc' and 'collectd' not in request.json['DMON']['queryString']:
            response = jsonify({'Status': 'Unsuported query',
                                'Message': 'Only system metrics supported for oslc'})
            response.status_code = 409
            return response
        if request.json is None:
            response = jsonify({'Status': 'Empty payload',
                                'Message': 'Request has empty payload'})
            response.status_code = 417
            app.logger.error('[%s] : [ERROR] Empty payload received for query, returned error 417',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        if 'queryString' not in request.json['DMON']:
            response = jsonify({'Status': 'No queryString',
                                'Message': 'Query string not found in payload'})
            response.status_code = 404
            app.logger.error('[%s] : [ERROR] Empty queryString received for query, returned error 404',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        if 'tstop' not in request.json['DMON']:
            query = queryConstructor(tstart=request.json['DMON']['tstart'],
                                     queryString=request.json['DMON']['queryString'],
                                     size=request.json['DMON']['size'], ordering=request.json['DMON']['ordering'])
        else:
            query = queryConstructor(tstart=request.json['DMON']['tstart'], tstop=request.json['DMON']['tstop'],
                                     queryString=request.json['DMON']['queryString'], size=request.json['DMON']['size'],
                                     ordering=request.json['DMON']['ordering'])

        if 'index' not in request.json['DMON']:
            myIndex = 'logstash-*'
        else:
            myIndex = request.json['DMON']['index']

        app.logger.info('[%s] : [INFO] Index set to %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), myIndex)
        if not 'metrics' in request.json['DMON'] or request.json['DMON']['metrics'] == " ":
            try:
                ListMetrics, resJson = queryESCore(query, debug=False, myIndex=myIndex)
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Cannot connect to ES instance with %s and %s',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                response = jsonify({'Status': 'Connection error',
                                    'Message': 'ES unreachable'})
                response.status_code = 404
                return response
            if not ListMetrics:
                response = jsonify({'Status': 'No results found',
                                    'Message': 'Please check time interval and index'})
                response.status_code = 404
                app.logger.info('[%s] : [INFO] No results found',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response

            if ftype == 'csv':
                if not 'fname' in request.json['DMON']:
                    fileName = 'output' + '.csv'
                    dict2CSV(ListMetrics)
                else:
                    fileName = request.json['DMON']['fname'] + '.csv'
                    dict2CSV(ListMetrics, request.json['DMON']['fname'])

                csvOut = os.path.join(outDir, fileName)
                try:
                    csvfile = open(csvOut, 'r')
                except EnvironmentError:
                    response = jsonify({'EnvError': 'file not found'})
                    response.status_code = 500
                    app.logger.error('[%s] : [ERROR] CSV file not found',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    return response
                return send_file(csvfile, mimetype='text/csv', as_attachment=True)
            if ftype == 'json':
                response = jsonify({'DMON': resJson})
                response.status_code = 200
                return response
            if ftype == 'plain':
                return Response(str(ListMetrics), status=200, mimetype='text/plain')

            if ftype == 'oslc':
                # queryStr = request.json['DMON']['queryString']
                resOSLC = jsonToPerfMon(resJson)
                return Response(resOSLC, mimetype='application/rdf+xml')

        else:
            metrics = request.json['DMON']['metrics']
            app.logger.info('[%s] : [INFO] Metrics filter set to %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(metrics))
            try:
                ListMetrics, resJson = queryESCore(query, allm=False, dMetrics=metrics, debug=False, myIndex=myIndex)
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Cannot connect to ES instance with %s and %s',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                response = jsonify({'Status': 'Connection error',
                                    'Message': 'ES unreachable'})
                response.status_code = 404
                return response
            if not ListMetrics:
                response = jsonify({'Status': 'No results found!'})
                response.status_code = 404
                app.logger.info('[%s] : [INFO] No results found',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response
            # repeated from before create function
            if ftype == 'csv':
                if not 'fname' in request.json['DMON']:
                    fileName = 'output' + '.csv'
                    dict2CSV(ListMetrics)
                else:
                    fileName = request.json['DMON']['fname'] + '.csv'
                    dict2CSV(ListMetrics, request.json['DMON']['fname'])
                csvOut = os.path.join(outDir, fileName)
                try:
                    csvfile = open(csvOut, 'r')
                except EnvironmentError:
                    response = jsonify({'EnvError': 'file not found'})
                    response.status_code = 500
                    app.logger.error('[%s] : [ERROR] CSV file not found',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    return response
                return send_file(csvfile, mimetype='text/csv', as_attachment=True)
            if ftype == 'json':
                response = jsonify({'DMON': resJson})
                response.status_code = 200
                return response
            if ftype == 'plain':
                return Response(str(ListMetrics), status=200, mimetype='text/plain')
            if ftype == 'oslc':
                # queryStr = request.json['DMON']['queryString']
                resOSLC = jsonToPerfMon(resJson)
                return Response(resOSLC, mimetype='application/rdf+xml')


@dmon.route('/v2/observer/query/<ftype>')
@api.doc(params={'ftype': 'Output type'})
class QueryEsEnhancedCore(Resource):
    @api.expect(dDMONQueryEnh)
    def post(self, ftype):
        supportType = ["csv", "json"]
        if ftype not in supportType:
            response = jsonify({'Supported types': supportType, "Submitted Type": ftype})
            response.status_code = 415
            app.logger.warn('[%s] : [WARN] Unsuported output type %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), ftype)
            return response
        if request.json is None:
            response = jsonify({'Status': 'Empty payload',
                                'Message': 'Request has empty payload'})
            response.status_code = 417
            app.logger.error('[%s] : [ERROR] Empty payload received for query, returned error 417',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        if 'aggregation' not in request.json['DMON']:
            response = jsonify({'Status': 'Missing aggregation', 'Message': 'Aggregation must be defined'})
            response.status_code = 400
            app.logger.error('[%s] : [ERROR] Query missing aggregation field',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        supportedAggregation = ['system', 'yarn', 'spark', 'storm', 'cassandra']
        if request.json['DMON']['aggregation'] not in supportedAggregation:
            response = jsonify({'Supported aggregation': supportedAggregation, "Submitted Type": request.json['DMON']['aggregation']})
            response.status_code = 415
            app.logger.warn('[%s] : [WARN] Unsuported aggregation  %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), request.json['DMON']['aggregation'])
            return response
        if 'index' not in request.json['DMON']:
            index = 'logstash-*'
        else:
            index = request.json['DMON']['index']

        app.logger.info('[%s] : [INFO] Using index  %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), index)

        if 'size' not in request.json['DMON']:
            size = 0
        else:
            size = request.json['DMON']['size']
        app.logger.info('[%s] : [INFO] Using size  %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), size)

        if 'tstop' and 'tstart' not in request.json['DMON']:
            response = jsonify({'Status': 'Missing time interval declaration', 'Message': 'Both tstart and tstop must be defined'})
            response.status_code = 400
            app.logger.error('[%s] : [ERROR] Time interval not defined properly in request -> %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(request.json))
            return response

        if 'interval' not in request.json['DMON']:
            interval = '10s'
        else:
            interval = request.json['DMON']['interval']

        app.logger.info('[%s] : [INFO] Interval set to %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), interval)

        qES = dbESCore.query.filter_by(MasterNode=1).first()
        if qES is None:
            response = jsonify({'Status': 'Not found', 'Message': 'No es Core instance registered'})
            response.status_code = 503
            app.logger.info('[%s] : [INFO] ES core instance not registered',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        dqengine = QueryEngine(qES.hostIP)
        qNode = dbNodes.query.all()
        if qNode is None:
            response = jsonify({'Status': 'No registered nodes'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No nodes found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        nodeList = []
        for nodes in qNode:
            nodeList.append(nodes.nodeFQDN)
        if request.json['DMON']['aggregation'] == 'system':
            # nodes, tfrom, to, qsize, qinterval, index)
            df_system = dqengine.getSystemMetrics(nodeList, request.json['DMON']['tstart'], request.json['DMON']['tstop'], int(size), interval, index)
            # df_system = dqengine.getSystemMetrics(nodeList, request.json['DMON']['tstart'],
            #                                       request.json['DMON']['tstop'], 0, '10s', 'logstash-*')
            df_system.set_index('key', inplace=True)
            if isinstance(df_system, int):
                response = jsonify({'Status': 'error', 'Message': 'response is null'})
                response.status_code = 500
                app.logger.error('[%s] : [ERROR] System metrics return 0',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response
            if ftype == 'json':
                response = jsonify(dqengine.toDict(df_system))
                response.status_code = 200
                return response
            if ftype == 'csv':
                if not 'fname' in request.json['DMON']:
                    fileName = 'output.csv'
                else:
                    fileName = '%s.csv' % request.json['DMON']['fname']
                csvOut = os.path.join(outDir, fileName)
                dqengine.toCSV(df_system, csvOut)
                # with open(csvOut, 'r') as f:
                #     read_data = f.read()
                try:
                    csvfile = open(csvOut, 'r')
                except EnvironmentError:
                    response = jsonify({'EnvError': 'file not found'})
                    response.status_code = 500
                    app.logger.error('[%s] : [ERROR] CSV file not found',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    return response
                return send_file(csvfile, mimetype='text/csv', as_attachment=True)
        if request.json['DMON']['aggregation'] == 'yarn':
            df_dfs = dqengine.getDFS(request.json['DMON']['tstart'], request.json['DMON']['tstop'], int(size),
                                     interval, index)
            df_cluster = dqengine.getCluster(request.json['DMON']['tstart'], request.json['DMON']['tstop'],
                                             int(size), interval, index)
            df_name_node = dqengine.getNameNode(request.json['DMON']['tstart'], request.json['DMON']['tstop'],
                                                int(size), interval, index)

            nm_merged, jvmnn_merged, shuffle_merged = dqengine.getNodeManager(nodeList, request.json['DMON']['tstart'],
                                                                              request.json['DMON']['tstop'], int(size),
                                                                              interval, index)
            df_dn_merged = dqengine.getDataNode(nodeList, request.json['DMON']['tstart'], request.json['DMON']['tstop'],
                                                int(size), interval, index)
            listDF = [df_dfs, df_cluster, df_name_node, nm_merged, jvmnn_merged, shuffle_merged, df_dn_merged]
            df_merged = dqengine.merge(listDF)
            df_merged.set_index('key', inplace=True)
            if ftype == 'json':
                response = jsonify(dqengine.toDict(df_merged))
                response.status_code = 200
                return response
            if ftype == 'csv':
                if not 'fname' in request.json['DMON']:
                    fileName = 'output.csv'
                else:
                    fileName = '%s.csv' % request.json['DMON']['fname']
                csvOut = os.path.join(outDir, fileName)
                dqengine.toCSV(df_merged, csvOut)
                # with open(csvOut, 'r') as f:
                #     read_data = f.read()
                try:
                    csvfile = open(csvOut, 'r')
                except EnvironmentError:
                    response = jsonify({'EnvError': 'file not found'})
                    response.status_code = 500
                    app.logger.error('[%s] : [ERROR] CSV file not found',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    return response
                return send_file(csvfile, mimetype='text/csv', as_attachment=True)

        if request.json['DMON']['aggregation'] == 'storm':
            qSCore = dbSCore.query.first()
            if qSCore is None:
                response = jsonify({"Status": "No LS instances registered", "spouts": 0, "bolts": 0})
                response.status_code = 500
                app.logger.warning('[%s] : [WARN] No LS instance registred',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response
            if qSCore.LSCoreStormTopology == 'None':
                response = jsonify({"Status": "No Storm topology registered"})
                response.status_code = 404
                app.logger.info(
                    '[%s] : [INFO] No Storm topology registered, cannot fetch number of spouts and bolts',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response
            else:
                bolts, spouts = checkStormSpoutsBolts(qSCore.LSCoreStormEndpoint, qSCore.LSCoreStormPort,
                                                      qSCore.LSCoreStormTopology)
                app.logger.info('[%s] : [INFO] Storm topology %s with %s spounts and %s bolts found',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                str(qSCore.LSCoreStormTopology), str(spouts), str(bolts))
                df_storm = dqengine.getStormMetrics(request.json['DMON']['tstart'], request.json['DMON']['tstop'],
                                                    int(size), interval, index, bolts=bolts, spouts=spouts)
                if ftype == 'json':
                    response = jsonify(dqengine.toDict(df_storm))
                    response.status_code = 200
                    return response
                if ftype == 'csv':
                    if not 'fname' in request.json['DMON']:
                        fileName = 'output.csv'
                    else:
                        fileName = '%s.csv' % request.json['DMON']['fname']
                    csvOut = os.path.join(outDir, fileName)
                    dqengine.toCSV(df_storm, csvOut)
                    try:
                        csvfile = open(csvOut, 'r')
                    except EnvironmentError:
                        response = jsonify({'EnvError': 'file not found'})
                        response.status_code = 500
                        app.logger.error('[%s] : [ERROR] CSV file not found',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                        return response
                    return send_file(csvfile, mimetype='text/csv', as_attachment=True)

        if request.json['DMON']['aggregation'] == 'spark':
            return "Not for this version"

        if request.json['DMON']['aggregation'] == 'cassandra':
            df_CA_Count, df_CA_Gauge = dqengine.getCassandraMetrics(nodeList, request.json['DMON']['tstart'],
                                                  request.json['DMON']['tstop'], int(size), interval, index)
            if isinstance(df_CA_Gauge, int) or isinstance(df_CA_Gauge, int):
                response = jsonify({'Status': 'Empty response for cassandra metrics'})
                response.status_code = 400
                app.logger.warning('[%s] : [WARN] Empty response detected for Cassandra',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response
            listDF = [df_CA_Count, df_CA_Gauge]
            df_merged = dqengine.merge(listDF)
            df_merged.set_index('key', inplace=True)
            if ftype == 'json':
                response = jsonify(dqengine.toDict(df_merged))
                response.status_code = 200
                return response
            if ftype == 'csv':
                if not 'fname' in request.json['DMON']:
                    fileName = 'output.csv'
                else:
                    fileName = '%s.csv' % request.json['DMON']['fname']
                csvOut = os.path.join(outDir, fileName)
                dqengine.toCSV(df_merged, csvOut)
                # with open(csvOut, 'r') as f:
                #     read_data = f.read()
                try:
                    csvfile = open(csvOut, 'r')
                except EnvironmentError:
                    response = jsonify({'EnvError': 'file not found'})
                    response.status_code = 500
                    app.logger.error('[%s] : [ERROR] CSV file not found',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    return response
                return send_file(csvfile, mimetype='text/csv', as_attachment=True)

        if request.json['DMON']['aggregation'] == 'mongodb':
            df_MD_Count, df_MD_Gauge = dqengine.getMongoMetrics(nodeList, request.json['DMON']['tstart'],
                                                                request.json['DMON']['stop'], int(size), interval, index)
            if isinstance(df_MD_Count, int) or isinstance(df_MD_Gauge, int):
                response = jsonify({'Status': 'Empty response for MongoDB metrics'})
                response.status_code = 400
                app.logger.warning('[%s] : [WARN] Empty response detected for MongoDB',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response
            listDF = [df_MD_Count, df_MD_Gauge]
            df_merged = dqengine.merge(listDF)
            df_merged.set_index('key', inplace=True)
            if ftype == 'json':
                response = jsonify(dqengine.toDict(df_merged))
                response.status_code = 200
                return response
            if ftype == 'csv':
                if not 'fname' in request.json['DMON']:
                    fileName = 'output.csv'
                else:
                    fileName = '%s.csv' % request.json['DMON']['fname']
                csvOut = os.path.join(outDir, fileName)
                dqengine.toCSV(df_merged, csvOut)
                try:
                    csvfile = open(csvOut, 'r')
                except EnvironmentError:
                    response = jsonify({'EnvError': 'file not found'})
                    response.status_code = 500
                    app.logger.error('[%s] : [ERROR] CSV file not found',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    return response
                return send_file(csvfile, mimetype='text/csv', as_attachment=True)


@dmon.route('/v1/overlord')
class OverlordInfo(Resource):
    def get(self):
        response = jsonify({'Status': 'Current version is 0.2.1'})
        response.status_code = 200
        return response


@dmon.route('/v1/overlord/framework')
class OverlordFrameworkInfo(Resource):
    def get(self):
        response = jsonify({'Supported Frameworks': lFrameworks})
        response.status_code = 200
        return response


@dmon.route('/v1/overlord/framework/<fwork>')
@api.doc(params={'fwork': 'Big Data framework name'})
class OverlordFrameworkProperties(Resource):
    def get(self, fwork):
        if fwork not in lFrameworks:
            response = jsonify({'Status': 'Malformed URI', 'Message': 'Unknown framework ' + fwork})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] Malformed URI because framewrok %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fwork)
            return response
        if fwork == 'hdfs' or fwork == 'yarn':
            templateLoader = jinja2.FileSystemLoader(searchpath="/")
            templateEnv = jinja2.Environment(loader=templateLoader)
            propYarnTmp = os.path.join(tmpDir, 'metrics/hadoop-metrics2.tmp')
            propYarnFile = os.path.join(cfgDir, 'hadoop-metrics2.properties')
            try:
                template = templateEnv.get_template(propYarnTmp)
            except:
                response = jsonify({'Status': 'I/O Error', 'Message': 'Template file missing!'})
                response.status_code = 500
                app.logger.error('[%s] : [ERROR] YARN template file missing',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response
            qPeriod = dbMetPer.query.first()
            if qPeriod is None:
                period = '10'
            else:
                period = qPeriod.yarnMet

            infoYarn = {'metrics2_period': period}
            propSparkInfo = template.render(infoYarn)
            propYarnConf = open(propYarnFile, "w+")
            propYarnConf.write(propSparkInfo)
            propYarnConf.close()
            try:
                propCfg = open(propYarnFile, 'r')
            except EnvironmentError:
                response = jsonify({'Status': 'Environment Error!', 'Message': 'File not Found!'})
                response.status_code = 500
                app.logger.error('[%s] : [ERROR] YARN/HDFS properties file not found',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response
            return send_file(propCfg, mimetype='text/x-java-properties', as_attachment=True)

        if fwork == 'spark':
            templateLoader = jinja2.FileSystemLoader(searchpath="/")
            templateEnv = jinja2.Environment(loader=templateLoader)
            propSparkTemp = os.path.join(tmpDir, 'metrics/spark-metrics.tmp')
            propSparkFile = os.path.join(cfgDir, 'metrics.properties')
            try:
                template = templateEnv.get_template(propSparkTemp)
            except:
                response = jsonify({'Status': 'I/O Error', 'Message': 'Template file missing!'})
                response.status_code = 500
                app.logger.error('[%s] : [ERROR] Spark template file missing',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response

            qLSCore = dbSCore.query.first()  # TODO: Only works for single deployment
            if qLSCore is None:
                response = jsonify({'Status': 'Missing Instance', 'Message': 'No Logstash Instance Configured'})
                response.status_code = 404
                app.logger.warning('[%s] : [WARN] No Logstash server instance configured',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response
            qPeriod = dbMetPer.query.first()
            if qPeriod is None:
                period = '10'
            else:
                period = qPeriod.sparkMet
            infoSpark = {'logstashserverip': qLSCore.hostIP, 'logstashportgraphite': '5002', 'period': period}
            propSparkInfo = template.render(infoSpark)
            propSparkConf = open(propSparkFile, "w+")
            propSparkConf.write(propSparkInfo)
            propSparkConf.close()

            rSparkProp = open(propSparkFile, 'r')
            return send_file(rSparkProp, mimetype='text/x-java-properties',
                             as_attachment=True)  # TODO: Swagger returns same content each time, however sent file is correct
        if fwork == 'cassandra':
            return "Cassandra conf" #todo
        if fwork == 'mongodb':
            return "mongodb conf"


@dmon.route('/v1/overlord/application/<appID>')
@api.doc(params={'appID': 'Application identification'})
class OverlordAppSubmit(Resource):
    def put(self, appID):
        startT = datetime.utcnow()
        qApp = dbApp.query.filter_by(appName=appID).first()
        if qApp is None:
            # Sort by id desc
            lastApp = db.session.query(dbApp.id, dbApp.appName).order_by(dbApp.id.desc()).first()
            if lastApp is None:
                app.logger.info('[%s] : [INFO] No previouse application registered', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            else:
                # Get id of last inserted app, ordering is based in where lastApp is decalred; [0]-> dbApp.id
                app.logger.info('[%s] : [INFO] Last registered applications id %s name %s, setting to inactive',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), lastApp[0],
                                lastApp[1])
                qlastApp = dbApp.query.filter_by(appName=lastApp[1]).first()
                qlastApp.stopTime = startT
                qlastApp.jobID = 'STOPPED'
                db.session.add(qlastApp)
            appl = dbApp(appName=appID, appVersion=1, jobID='ACTIVE', startTime=startT, stopTime=None)
            db.session.add(appl)
            app.logger.info('[%s] : [INFO] Added new application %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), appID)
            response = jsonify({'Status': 'Registered Application', 'App': appID, 'Start': startT})
            response.status_code = 201
        else:
            newVer = int(qApp.appVersion) + 1
            qApp.appVersion = newVer
            qApp.startTime = startT
            #check if it is marked as active if not set active and mark others as inactive
            app.logger.info('[%s] : [INFO] Application %s has status %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qApp.appName, qApp.jobID)
            if qApp.jobID == 'ACTIVE':
                pass
            else:
                qApp.jobID = 'ACTIVE'
                qActive = dbApp.query.filter_by(jobID='ACTIVE').first()
                app.logger.info('[%s] : [INFO] Found other active application %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qActive.appName)
                qActive.jobID = 'STOPPED'
            db.session.add(qApp)
            response = jsonify({'Status': 'Modified', 'App': appID, 'Version': qApp.appVersion})
            app.logger.info('[%s] : [INFO] Modified application %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), appID)
            response.status_code = 200
        return response


@dmon.route('/v1/overlord/core')
class OverlordBootstrap(Resource):
    def post(self):
        return "Deploys all monitoring core components with default configuration"


@dmon.route('/v1/overlord/core/halt')
class OverlordCoreHalt(Resource):
    def post(self):
        return "Stop all core components!"


@dmon.route('/v1/overlord/core/database')
class OverlordCoredb(Resource):
    def get(self):
        try:
            dbFile = open(os.path.join(baseDir, 'dmon.db'), 'r')
        except EnvironmentError:
            response = jsonify({'EnvError': 'file not found'})
            response.status_code = 500
            app.logger.error('[%s] [ERROR] Database not found')
            return response
        return send_file(dbFile, mimetype='application/x-sqlite3', as_attachment=True)

    def put(self):
        dbLoc = os.path.join(baseDir, 'dmon.db')
        file = request.files['dmon.db']
        if os.path.isfile(os.path.join(baseDir, 'dmon.db')) is True:
            os.rename(dbLoc, dbLoc + '.backup')
            app.logger.info('[%s] : [INFO] Old database backup created',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        file.save(dbLoc)

        response = jsonify({'Status': 'Done',
                            'Message': 'New DB loaded'})
        response.status_code = 201
        app.logger.info('[%s] : [INFO] New database loaded',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        return response

# @dmon.route('/v1/overlord/core/state')
# class OverlordCoreState(Resource):
#     def get(self):
#         qAll = db.session.query(dbNodes.nodeFQDN, dbSCore.hostFQDN, dbESCore.hostFQDN, dbKBCore.hostFQDN, dbApp.appName, dbCDHMng.cdhMng).all()
#         payload ={}
#         for res in qAll:
#             qNodes = dbNodes.query.filter_by(nodeFQDN=res[0]).first()


@dmon.route('/v1/overlord/core/status')
class OverlordCoreStatus(Resource):
    def get(self):
        rspD = {}
        qESCore = dbESCore.query.filter_by(
            MasterNode=1).first()  # TODO -> curerntly only generates config file for master node
        if qESCore is None:
            response = jsonify({"Status": "No master ES instances found!"})
            response.status_code = 500
            app.logger.warning('[%s] : [WARN] No Master ES Instance registered',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        try:
            esCoreUrl = 'http://' + qESCore.hostIP + ':' + str(qESCore.nodePort)
            r = requests.get(esCoreUrl, timeout=DMON_TIMEOUT)  # timeout in seconds
        except:
            response = jsonify({"Error": "Master ES instances not reachable!"})
            response.status_code = 500
            app.logger.error('[%s] : [ERROR] ES instance not responding at %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), esCoreUrl)
            return response
        qLSCore = dbSCore.query.first()  # TODO: -> only works for single LS deployment
        if qLSCore is None:
            response = jsonify({"Status": "No LS instances found!"})
            response.status_code = 500
            app.logger.warning('[%s] : [WARN] No LS Instance registered',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        qKBCore = dbKBCore.query.first()
        if qKBCore is None:
            response = jsonify({"Status": "No KB instances found!"})
            response.status_code = 500
            app.logger.warning('[%s] : [WARN] No KB Instance registered',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        rsp = r.json()
        rspES = {'ElasticSearch': rsp}
        LSVer = os.getenv('LS_VERSION', '2.2.0')
        KBVer = os.getenv('KB_VERSION', '4.3.1')
        rspLS = {'Logstash': {'Status': qLSCore.LSCoreStatus, 'Version': str(LSVer)}}
        rspKB = {'Kibana': {'Status': qKBCore.KBCoreStatus, 'Version': str(KBVer)}}

        rspD.update(rspES)
        rspD.update(rspLS)
        rspD.update(rspKB)
        response = jsonify(rspD)
        response.status_code = 200
        return response


# @dmon.route('/v1/overlord/core/chef')
# class ChefClientStatus(Resource):
# 	def get(self):
# 		return "Monitoring Core Chef Client status"
#
#
# @dmon.route('/v1/overlord/nodes/chef')
# class ChefClientNodes(Resource):
# 	def get(self):
# 		return "Chef client status of monitored Nodes"


@dmon.route('/v1/overlord/nodes')  # TODO -checkOS and -checkRoles
class MonitoredNodes(Resource):
    def get(self):
        nodeList = []
        nodesAll = db.session.query(dbNodes.nodeFQDN, dbNodes.nodeIP).all()
        if nodesAll is None:
            response = jsonify({'Status': 'No monitored nodes found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No registered  nodes found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        for nl in nodesAll:
            nodeDict = {}
            # print >>sys.stderr, nl[0]
            app.logger.info('[%s] : [INFO] Node %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nl[0])
            nodeDict.update({nl[0]: nl[1]})
            nodeList.append(nodeDict)
        response = jsonify({'Nodes': nodeList})
        app.logger.info('[%s] : [INFO] Registered nodes %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nodeList))
        response.status_code = 200
        return response

    @api.expect(nodeSubmit)
    def put(self):
        if not request.json:
            abort(400)
        listN = []
        if "Nodes" not in request.json:
            response = jsonify({'Status': 'Malformed request',
                                'Message': 'JSON payload malformed'})
            response.status_code = 400
            app.logger.warning('[%s] : [WARN] Malformed json request',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        nLSI = ''
        for nodes in request.json['Nodes']:
            qNodes = dbNodes.query.filter_by(nodeFQDN=nodes['NodeName']).first()
            qNodeLSinstance = dbSCore.query.first()
            if qNodes is None:
                if 'LogstashInstance' not in nodes:
                    if qNodeLSinstance is None:
                        nLSI = 'None'
                        app.logger.warning('[%s] : [WARN] No LS Instance registered',
                                           datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    else:
                        nLSI = qNodeLSinstance.hostIP
                        app.logger.info('[%s] : [INFO] LS Instance %s assigned to %s',
                                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                        nodes['NodeName'], qNodeLSinstance.hostFQDN)
                else:
                    nLSI = nodes['LogstashInstance']
                    app.logger.info('[%s] : [INFO] LS Instance at %s assigned to %s',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                    nLSI, nodes['NodeName'])

                if 'NodeOS' not in nodes:
                    nodeOS = 'unknown'
                else:
                    nodeOS = nodes['NodeOS']

                if 'key' not in nodes:
                    nodeKey = 'unknown'
                else:
                    nodeKey = nodes['key']

                e = dbNodes(nodeFQDN=nodes['NodeName'], nodeIP=nodes['NodeIP'], nodeOS=nodeOS,
                            nkey=nodeKey, nUser=nodes['username'], nPass=nodes['password'], nLogstashInstance=nLSI)
                db.session.add(e)
            else:
                qNodes.nodeIP = nodes['NodeIP']
                if 'NodeOS' in nodes:
                    qNodes.nodeOS = nodes['NodeOS']
                if 'key' in nodes:
                    qNodes.nkey = nodes['key']
                qNodes.nUser = nodes['username']
                qNodes.nPass = nodes['password']
                if 'LogstashInstance' not in nodes:
                    nLSI = qNodeLSinstance.hostIP
                else:
                    nLSI = nodes['LogstashInstance']
                    app.logger.info('[%s] : [INFO] LS Instance changed for node %s from %s to %s',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                    qNodes.nodeFQDN, qNodes.nLogstashInstance, nLSI)
                qNodes.nLogstashInstance = nLSI
                db.session.add(qNodes)
            db.session.commit
        response = jsonify({'Status': "Nodes list Updated!"})
        response.status_code = 201
        app.logger.info('[%s] : [INFO] Nodes updated',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        return response

    def post(self): #todo
        return "Bootstrap monitoring"


@dmon.route('/v1/overlord/nodes/roles')
class ClusterRoles(Resource):
    def get(self):
        nodeList = []
        nodesAll = db.session.query(dbNodes.nodeFQDN, dbNodes.nRoles).all()
        if nodesAll is None:
            response = jsonify({'Status': 'No monitored nodes found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No registered nodes found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        for nl in nodesAll:
            nodeDict = {}
            app.logger.info('[%s] : [INFO] Node name -> %s ',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nl[0]))
            nodeDict.update({nl[0]: nl[1].split(', ')})
            nodeList.append(nodeDict)
        response = jsonify({'Nodes': nodeList})
        app.logger.info('[%s] : [INFO] Nodes and their associted roles %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nodeList))
        response.status_code = 200
        return response

    @api.expect(listNodeRoles)
    def put(self):
        if not request.json:
            response = jsonify({'Status': 'Malformed Request',
                                'Message': 'Only JSON requests are permitted'})
            response.status_code = 400
            app.logger.warning('[%s] : [WARN] Malformed request, not JSON',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        if "Nodes" not in request.json:
            response = jsonify({'Status': 'Malformed Request',
                                'Message': 'Missing key(s)'})
            response.status_code = 400
            app.logger.warning('[%s] : [WARN] Malformed request, missing Node key',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        nrNodes = len(request.json['Nodes'])
        for n in range(nrNodes):
            if "NodeName" not in request.json['Nodes'][n]:
                response = jsonify({'Status': 'Malformed Request',
                                'Message': 'Missing key(s)'})
                response.status_code = 400
                app.logger.warning('[%s] : [WARN] Malformed request, missing NodeName key',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response

        nList = request.json["Nodes"]

        for n in nList:
            # print n["NodeName"]
            # print n["Roles"]
            upRoles = dbNodes.query.filter_by(nodeFQDN=n["NodeName"]).first()
            if upRoles is None:
                response = jsonify({'Status': 'Node Name Error',
                                    'Message': 'Node' + n["NodeName"] + ' not found!'})
                response.status_code = 404
                app.logger.warning('[%s] : [WARN] Node %s not found',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                    str(n["NodeName"]))
                return response
            upRoles.nRoles = ', '.join(map(str, n["Roles"]))

        response = jsonify({'Status': 'Done',
                            'Message': 'All roles updated!'})

        response.status_code = 201
        app.logger.info('[%s] : [INFO] Node roles updated',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        return response

    def post(self):
        nodes = db.session.query(dbNodes.nodeFQDN, dbNodes.nodeIP, dbNodes.nUser, dbNodes.nPass, dbNodes.nRoles).all()
        if nodes is None:
            response = jsonify({'Status': 'No monitored nodes found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No registererd nodes found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        yarnList = []
        sparkList = []
        stormList = []
        unknownList = []
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        propYarnTmp = os.path.join(tmpDir, 'metrics/hadoop-metrics2.tmp')
        propYarnFile = os.path.join(cfgDir, 'hadoop-metrics2.properties')
        try:
            template = templateEnv.get_template(propYarnTmp)
        except:
            response = jsonify({'Status': 'I/O Error', 'Message': 'Template file missing!'})
            response.status_code = 500
            app.logger.error('[%s] : [ERROR] YARN template file missing',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        qPeriod = dbMetPer.query.first()
        if qPeriod is None:
            period = '10'
        else:
            period = qPeriod.yarnMet

        infoYarn = {'metrics2_period': period}
        propSparkInfo = template.render(infoYarn)
        propYarnConf = open(propYarnFile, "w+")
        propYarnConf.write(propSparkInfo)
        propYarnConf.close()

        for node in nodes:
            roleList = node[4].split(',')
            if 'yarn' in roleList or 'hdfs' in roleList:
                nl = []
                nl.append(node[1])
                uploadFile(nl, node[2], node[3], propYarnFile, 'hadoop-metrics2.tmp',
                           '/etc/hadoop/conf.cloudera.yarn/hadoop-metrics2.properties')  # TODO better solution
                uploadFile(nl, node[2], node[3], propYarnFile, 'hadoop-metrics2.tmp',    #TODO instead of tmp add polling interval
                           '/etc/hadoop/conf.cloudera.hdfs/hadoop-metrics2.properties')  # TODO better solution
                uploadFile(nl, node[2], node[3], propYarnFile, 'hadoop-metrics2.tmp',
                           '/etc/hadoop/conf/hadoop-metrics2.properties')  # TODO better solution
                yarnList.append(node[0])
                app.logger.info('[%s] : [INFO] HDFS/YARN conf upload to %s, %s, %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nl),
                                str(node[2]), str(node[3]))
            if 'spark' in roleList:  # TODO Same as /v1/overlord/framework/<fwork>, needs unification
                templateLoader = jinja2.FileSystemLoader(searchpath="/")
                templateEnv = jinja2.Environment(loader=templateLoader)
                propSparkTemp = os.path.join(tmpDir, 'metrics/spark-metrics.tmp')
                propSparkFile = os.path.join(cfgDir, 'metrics.properties')
                try:
                    template = templateEnv.get_template(propSparkTemp)
                except:
                    response = jsonify({'Status': 'I/O Error', 'Message': 'Template file missing!'})
                    response.status_code = 500
                    app.logger.error('[%s] : [ERROR] Spark properties template missing',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    return response

                qLSCore = dbSCore.query.first()  # TODO: Only works for single deployment
                if qLSCore is None:
                    response = jsonify({'Status': 'Missing Instance', 'Message': 'No Logstash Instance Configured'})
                    response.status_code = 404
                    app.logger.warning('[%s] : [WARN] No LS instance registered')
                    return response

                qPeriod = dbMetPer.query.first()
                if qPeriod is None:
                    period = '10'
                else:
                    period = qPeriod.sparkMet
                infoSpark = {'logstashserverip': qLSCore.hostIP, 'logstashportgraphite': '5002', 'period': period}
                app.logger.info(
                    '[%s] : [INFO] Spark Config used based on role def: LSServer -> %s, Graphite -> 5002, Period -> %s',
                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qLSCore.hostIP, period)
                propSparkInfo = template.render(infoSpark)
                propSparkConf = open(propSparkFile, "w+")
                propSparkConf.write(propSparkInfo)
                propSparkConf.close()

                nl = []
                nl.append(node[1])
                uploadFile(nl, node[2], node[3], propSparkFile, 'metrics.properties',
                           '/etc/spark/conf/metrics.properties')  # TODO better solution
                sparkList.append(node[0])
                app.logger.info('[%s] : [INFO] Spark conf upload to %s, %s, %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nl),
                                str(node[2]), str(node[3]))
            if 'storm' in roleList:
                stormList.append(node[0])  # TODO

            if 'unknown' in roleList:
                unknownList.append(node[0])

        response = jsonify(
            {'Status': {'yarn': yarnList, 'spark': sparkList, 'storm': stormList, 'unknown': unknownList}})
        response.status_code = 200
        app.logger.info('[%s] : [INFO] Status YARN List %s, SPARK List %s, STORM list %s, Unknown LIST %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(yarnList),
                        str(sparkList), str(stormList), str(unknownList))
        return response


@dmon.route('/v1/overlord/detect/storm')
class DetectStormRA(Resource):
    def get(self):
        qSCore = dbSCore.query.first()
        if qSCore is None:
            response = jsonify({"Status": "No LS instances registered", "spouts": 0, "bolts": 0})
            response.status_code = 500
            app.logger.warning('[%s] : [WARN] No LS instance registred',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        if qSCore.LSCoreStormTopology == 'None':
            response = jsonify({"Status": "No Storm topology registered"})
            response.status_code = 404
            app.logger.info('[%s] : [INFO] No Storm topology registered, cannot fetch number of spouts and bolts',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        else:
            bolts, spouts = checkStormSpoutsBolts(qSCore.LSCoreStormEndpoint, qSCore.LSCoreStormPort, qSCore.LSCoreStormTopology)
            response = jsonify({'Topology': qSCore.LSCoreStormTopology, "spouts": spouts, "bolts": bolts})
            response.status_code = 200
            app.logger.info('[%s] : [INFO] Storm topology %s with %s spounts and %s bolts found',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                            str(qSCore.LSCoreStormTopology), str(spouts), str(bolts))

            return response

    def post(self):
        qNode = dbNodes.query.all()
        if qNode is None:
            response = jsonify({'Status': 'No registered nodes'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No nodes found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        qLSStorm = dbSCore.query.all()
        if not qLSStorm:
            response = jsonify({'Status': 'No registered logstash server'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No logstash instance found found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        regStorm = {}
        for l in qLSStorm:
            if l.LSCoreStormEndpoint != 'None':
                app.logger.info('[%s] : [INFO] Found Storm Endpoint set to %s ',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), l.LSCoreStormEndpoint)
                if validateIPv4(l.LSCoreStormEndpoint):
                    if l.LSCoreStormPort.isdigit():
                        regStorm[l.LSCoreStormEndpoint] = l.LSCoreStormPort
                        app.logger.info('[%s] : [INFO] Storm REST Port is %s',
                                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), l.LSCoreStormPort)
                    else:
                        regStorm[l.LSCoreStormEndpoint] = '8080'
                        l.LSCoreStormPort = '8080'
                        app.logger.info('[%s] : [INFO] Storm REST Port set to default -> 8080',
                                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    if l.LSCoreStormTopology != 'None':
                        try:
                            getTop = detectStormTopology(l.LSCoreStormEndpoint, l.LSCoreStormPort)
                        except Exception as inst:
                            app.logger.warning('[%s] : [WARNING] Error while trying enpoint -> %s port -> %s;  with %s and %s',
                                       datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), l.LSCoreStormEndpoint, l.LSCoreStormPort,
                                               type(inst), inst.args)
                            getTop = 'None'
                        if l.LSCoreStormTopology == getTop:
                            response = jsonify({'Status': 'Topology Verified',
                                                'Topology': getTop})
                            response.status_code = 200
                            app.logger.info('[%s] : [INFO] Topology %s verified',
                                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), getTop)
                            return response
        foundTopologies = set()
        lsTopology = {}
        if regStorm:
            for k, v in regStorm.iteritems():
                try:
                    topology = detectStormTopology(k, v)
                except Exception as inst:
                    app.logger.warning('[%s] : [WARNING] Error while trying enpoint -> %s port -> %s;  with %s and %s',
                                       datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), k, v,
                                       type(inst), inst.args)
                    break
                foundTopologies.add(topology)
                lsTopology[k] = topology
            if len(foundTopologies) > 1:
                setTopology = next(iter(foundTopologies))
                for k, v in lsTopology.iteritems():
                    qLStorm = dbSCore.query.filter_by(LSCoreStormEndpoint=k).first()
                    if v == setTopology:
                        qLStorm.LSCoreStormTopology = setTopology
                        app.logger.info('[%s] : [INFO] Topology %s set at IP %s',
                                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), setTopology, k)
                    break
                response = jsonify({'Status': 'Topologies found ' + str(len(foundTopologies)),
                                    'Topologies': list(foundTopologies),
                                    'SetTopology': setTopology})
                response.status_code = 201
                return response
            if lsTopology:
                for k, v in lsTopology.iteritems():
                    qLStorm = dbSCore.query.filter_by(LSCoreStormEndpoint=k).all()
                    #TODO: adds Port and Storm Topology for all ls instances with the same set of registered Storm Endpoints, need to change in future versions
                    for e in qLStorm:
                        e.LSCoreStormTopology = v
                        app.logger.info('[%s] : [INFO] Topology %s set at IP %s',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), v, k)
                response = jsonify({'Status': 'Topology found',
                                'Topology': list(foundTopologies)})
                response.status_code = 201
                return response

        stormNodes = []
        for n in qNode:
            if "storm" in n.nRoles:
                stormNodes.append(n.nodeIP)
        if not stormNodes:
            response = jsonify({'Status': 'Storm role not found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARNING] No nodes have storm role',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        resList = []
        for n in stormNodes:
            url = 'http://%s:%s/api/v1/topology/summary' %(n, '8080')
            resList.append(url)
        app.logger.info('[%s] : [INFO] Resource list for topoligy discovery -> %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), resList)
        dmon = GreenletRequests(resList)
        nodeRes = dmon.parallelGet()

        topoIDs = {}
        for i in nodeRes:
            nodeIP = urlparse(i['Node'])
            data = i['Data']
            if data !='n/a':
                try:
                    topoIDs[nodeIP.hostname] = data.get('topologies')[0]['id']
                except Exception as inst:
                    app.logger.warning('[%s] : [WARN] No topology has been loaded,  with %s and %s',
                                       datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                    response = jsonify({'Status': 'No topology has been loaded'})
                    response.status_code = 404
                    return response

        if not topoIDs:
            response = jsonify({'Status': 'No Storm detected on registered nodes'})
            response.status_code = 404
            app.logger.info('[%s] : [INFO] No Storm detected on registered nodes',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        elif len(topoIDs) > 1:
            response = jsonify({'Status': 'More than one Storm deployment detected',
                                'Message': 'Only one deployment per monitoring solution',
                                'Nodes': topoIDs})
            response.status_code = 500
            app.logger.info('[%s] : [INFO] More than one Storm detected: %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(topoIDs))
            return response
        for ls in qLSStorm:
            for k, v in topoIDs.iteritems():
                ls.LSCoreStormEndpoint = k
                ls.LSCoreStormPort = '8080'
                ls.LSCoreStormTopology = v

        response = jsonify({'Status': 'Detected Storm deployment',
                            'StormEndpoint': topoIDs.keys()[0],
                            'StormTopology': topoIDs.get(topoIDs.keys()[0]),
                            'StormPort': '8080'
                            })
        response.status_code = 201
        dmon.reset()
        return response


@dmon.route('/v1/overlord/mongo')
class MongoSettings(Resource):
    def get(self):
        qBDS = dbBDService.query.first()
        if qBDS is None:
            response = jsonify({'Status': 'No registered mongo settings'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No mongo settings found found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        if qBDS.mongoUser is None:
            mUser = False
        elif qBDS.mongoUser.strip():
            mUser = True
        else:
            mUser = False
        if qBDS.mongoPswd is None:
            mPass = False
        elif qBDS.mongoPswd.strip():
            mPass = True
        else:
            mPass = False

        response = jsonify({'MongoHost': qBDS.mongoHost, 'MongoPort': qBDS.mongoPort,
                            'User': mUser, 'Password': mPass, 'MongoDBs': qBDS.mongoDBs})
        response.status_code = 200
        return response

    @api.expect(mongoDBConf)
    def put(self):
        if not request.json:
            abort(400)
        requiredKeys = ['MongoHost', 'MongoPort']
        for key in requiredKeys:
            if key not in request.json:
                response = jsonify({'Error': 'malformed request, missing key(s)'})
                response.status_code = 400
                app.logger.warning('[%s] : [WARN] Malformed Request, missing key(s)',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response
        if 'MongoUser' not in request.json:
            mUser = ''
        else:
            mUser = request.json['MongoUser']
        if 'MongoPassword' not in request.json:
            mPass = 'password'
        else:
            mPass = request.json['MongoPassword']
        if 'MongoDBs' not in request.json:
            dbs = 'admin'
        else:
            dbs = request.json['MongoDBs']
        qBDS = dbBDService.query.first()
        if qBDS is None:
            # {'MongoHost': qBDS.mongoHost, 'MongoPort': qBDS.mongoPort,
            #  'User': mUser, 'Password': mPass, 'MongoDBs': qBDS.mongoDBs})
            e = dbBDService(mongoHost=request.json['MongoHost'], mongoPort=request.json['MongoPort'], mongoUser=mUser,
                            mongoPswd=mPass, mongoDBs=dbs)
            db.session.add(e)
            db.session.commit()
            response = jsonify({'Status': 'Added MongoDB Settings'})
            response.status_code = 201
            app.logger.info('[%s] : [INFO] Added MongoDB settings: Host-> %s, Port ->%s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                            str(request.json['MongoUser']), str(request.json['MongoPassword']))
            return response
        else:
            qBDS.mongoHost = request.json['MongoHost']
            qBDS.mongoPort = request.json['MongoPort']
            qBDS.mongoUser = mUser
            qBDS.mongoPswd = mPass
            qBDS.mongoDBs = dbs
            response = jsonify({'Status': 'Modified MongoDB Settings'})
            response.status_code = 201
            app.logger.info('[%s] : [INFO] Modified MongoDB settings: Host-> %s, Port ->%s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                            str(request.json['MongoUser']), str(request.json['MongoPassword']))
            return response


@dmon.route('/v1/overlord/storm/logs')
class StormLogs(Resource):
    def get(self):
        workerFile = 'workerlogs_*.tar'
        lFile = []
        for name in glob.glob(os.path.join(outDir, workerFile)):
            path, filename = os.path.split(name)
            lFile.append(filename)

        response = jsonify({'StormLogs': lFile})
        response.status_code = 200
        app.logger.info('[%s] : [INFO] Available Storm logs %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(lFile))
        return response

    def post(self):
        nodeList = []
        nodesAll = db.session.query(dbNodes.nodeFQDN, dbNodes.nRoles, dbNodes.nodeIP).all()
        try:
            global backProc
            alive = backProc.is_alive()
            if alive:
                response = jsonify({'Status': 'Only one background process is permited', 'PID': str(backProc.pid),
                                    'BProcess': 'Active'})
                response.status_code = 409
                return response
        except Exception as inst:
            app.logger.warning('[%s] : [WARN] First startup detected, skipping backgroundproces alive check',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

        if nodesAll is None:
            response = jsonify({'Status': 'No monitored nodes found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No registered nodes found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        for nl in nodesAll:
            app.logger.info('[%s] : [INFO] Node name -> %s ',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nl[0]))

            if 'storm' in nl[1].split(', '): #TODO modify to STORM
                nodeList.append(nl[2])

        if not nodeList:
            response = jsonify({'Status': 'No nodes with role storm found'})
            response.status_code = 404
            return response

        stormLogAgent = AgentResourceConstructor(nodeList, '5222')
        resourceList = stormLogAgent.stormLogs()

        backProc = multiprocessing.Process(target=getStormLogsGreen, args=(resourceList, ))
        backProc.daemon = True
        backProc.start()
        response = jsonify({'Status': 'Started background process', 'PID': str(backProc.pid)})
        response.status_code = 201
        return response


@dmon.route('/v1/overlord/storm/logs/active')
class StormLogFetchActive(Resource):
    def get(self):
        try:
            pid = str(backProc.pid)
            alive = str(backProc.is_alive())
        except Exception as inst:
            app.logger.warning('[%s] : [WARN] No Background proc detected with %s and %s ',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            response = jsonify({'Status': 'No background process detected'})
            response.status_code = 404
            return response
        response = jsonify({'PID': pid,
                            'Alive': alive})
        response.status_code = 200
        return response


@dmon.route('/v1/overlord/storm/logs/<log>')
class StormLogsLog(Resource):
    def get(self, log):
        if not os.path.isfile(os.path.join(outDir, log)):
            response = jsonify({'Status': 'Not found',
                                'StormLog': log})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] Strom log %s not found',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), log)
            return response
        app.logger.info('[%s] : [INFO] Served Storm log %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), log)
        return send_from_directory(outDir, log, as_attachment=True, mimetype='application/tar')


@dmon.route('/v1/overlord/detect/yarn')
class DetectYarnHS(Resource):
    def get(self):
        qDBS = dbBDService.query.first()
        if qDBS is None:
            response = jsonify({'Status': 'Not Found',
                                'Message': 'No Yarn history server instance found'})
            response.status_code = 404
            return response

        response = jsonify({'NodePort': qDBS.yarnHPort,
                            'NodeIP': qDBS.yarnHEnd,
                            'Polling': qDBS.yarnHPoll})
        response.status_code = 200
        return response

    @api.expect(yarnHistorySettings)
    def put(self):
        if not request.json:
            abort(400)
        qBDS = dbBDService.query.first()
        if 'NodeIP' not in request.json:
            nodeIP = 0
        else:
            nodeIP = request.json['NodeIP']

        if 'NodePort' not in request.json:
            nodePort = 0
        else:
            nodePort = request.json['NodePort']

        if 'Polling' not in request.json:
            poll = 0
        else:
            poll = request.json['Polling']

        if qBDS is None:
            if not nodeIP:
                response = jsonify({'Status': 'Missing parameter',
                                    'Message': 'Yarn History server IP must be defined at first submit'})
                response.status_code = 406
                return response
            if not nodePort:
                nodePort = 19888
            if not poll:
                poll = 30
            upBDS = dbBDService(yarnHPort=nodePort, yarnHEnd=nodeIP, yarnHPoll=poll)
            db.session.add(upBDS)
            db.session.commit()
            app.logger.info('[%s] : [INFO] Added Yarn History Server Node info',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'Added Yarn History',
                                'Message': 'Added Yarn History server info'})
            response.status_code = 200
            return response
        else:
            if nodeIP:
                qBDS.yarnHEnd = nodeIP
                app.logger.info('[%s] : [INFO] Updated Yarn History Server Endpoint to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeIP)
            if nodePort:
                qBDS.yarnHPort = nodePort
                app.logger.info('[%s] : [INFO] Updated Yarn History Server Port to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nodePort))
            if poll:
                qBDS.yarnHPoll = poll
                app.logger.info('[%s] : [INFO] Updated Yarn History Server Polling period to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nodePort))

            response = jsonify({'Status': 'Updated Yarn History',
                                'Message': 'Update Yarn History server info'})
            response.status_code = 200
            return response

    def post(self):
        #yarnDetect = DetectBDService()
        response = servDet.detectYarnHS()
        return response


@dmon.route('/v1/overlord/detect/spark')
class DetectSparkHS(Resource):
    def get(self):
        return 'Get spark history server settings'

    def put(self):
        return 'Define or modify spark history server endpoint'

    def post(self):
        return 'Define or modify spark history server endpoint'


@dmon.route('/v1/overlord/history/yarn')
class YarnHistoryServer(Resource):
    def get(self):
        qBDService = dbBDService.query.first()
        if qBDService is None:
            app.logger.warning('[%s] : [WARN] No entry for Yarn History server found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'No Yarn History server entry found'})
            response.status_code = 404
            return response
        elif qBDService.yarnHEnd == 'None':
            app.logger.warning('[%s] : [WARN] Yarn History server not registered',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'Yarn History server not registered'})
            response.status_code = 404
            return response
        else:
            try:
                yarnJobsStatus, yarnJobs = getYarnJobs(qBDService.yarnHEnd, qBDService.yarnHPort)
            except Exception as inst:
                app.logger.warning('[%s] : [WARN] Yarn History server not responding at %s with port %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qBDService.yarnHEnd, str(qBDService.yarnHPort))
                response = jsonify({'Status': 'Yarn History server not responding'})
                response.status_code = 408
                return response

            return yarnJobs


@dmon.route('/v1/overlord/history/yarn/jobs')
class YarnHistoryServerJobs(Resource):
    def get(self):
        qBDService = dbBDService.query.first()
        if qBDService is None:
            app.logger.warning('[%s] : [WARN] No entry for Yarn History server found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'No Yarn History server entry found'})
            response.status_code = 404
            return response
        elif qBDService.yarnHEnd == 'None':
            app.logger.warning('[%s] : [WARN] Yarn History server not registered',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'Yarn History server not registered'})
            response.status_code = 404
            return response
        else:
            try:
                yarnJobsStatus, yarnJobs = getYarnJobs(qBDService.yarnHEnd, qBDService.yarnHPort)
            except Exception as inst:
                app.logger.warning('[%s] : [WARN] Yarn History server not responding at %s with port %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qBDService.yarnHEnd, str(qBDService.yarnHPort))
                response = jsonify({'Status': 'Yarn History server not responding'})
                response.status_code = 408
                return response

            try:
                jStatJob = getYarnJobsStatistic(qBDService.yarnHEnd, qBDService.yarnHPort, yarnJobs)
            except Exception as inst:
                app.logger.warning('[%s] : [WARN] Yarn History server not responding at %s with port %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qBDService.yarnHEnd, str(qBDService.yarnHPort))
                response = jsonify({'Status': 'Yarn History server not responding'})
                response.status_code = 408
                return response
            #TODO: Stronger sync index with logstash server needed
            # dindex = 'logstash-%s' %datetime.now().strftime("%Y.%m.%d")
            qES = dbESCore.query.filter_by(MasterNode=1).first()
            if qES is None:
                response = jsonify({'Status': 'ES not registered'})
                response.status_code = 404
                app.logger.error('[%s] : [ERROR] ES core not registered into dmon', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response

            try:
                rIndex = dmonESIndexer(qES.hostIP, dmonindex='ystat', dmondoc_type='yarn_jobstat', docId='yarn-jobstat', body=jStatJob)
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Indexing failed with %s and %s',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                response = jsonify({'Status': 'Error while indexing'})
                response.status_code = 503
                return response
            app.logger.info('[%s] : [INFO] Jobs indexed %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(rIndex))
            # return rIndex
            return jStatJob


@dmon.route('/v1/overlord/history/yarn/jobs/tasks')
class YarnHistoryServerJobTasks(Resource):
    def get(self):
        qBDService = dbBDService.query.first()
        if qBDService is None:
            app.logger.warning('[%s] : [WARN] No entry for Yarn History server found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'No Yarn History server entry found'})
            response.status_code = 404
            return response
        elif qBDService.yarnHEnd == 'None':
            app.logger.warning('[%s] : [WARN] Yarn History server not registered',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'Yarn History server not registered'})
            response.status_code = 404
            return response
        else:
            try:
                yarnJobsStatus, yarnJobs = getYarnJobs(qBDService.yarnHEnd, qBDService.yarnHPort)
            except Exception as inst:
                app.logger.warning('[%s] : [WARN] Yarn History server not responding at %s with port %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qBDService.yarnHEnd, str(qBDService.yarnHPort))
                response = jsonify({'Status': 'Yarn History server not responding'})
                response.status_code = 408
                return response

            try:
                jStatTask = getYarnJobTasks(qBDService.yarnHEnd, qBDService.yarnHPort, yarnJobs)
            except Exception as inst:
                app.logger.warning('[%s] : [WARN] Yarn History server not responding at %s with port %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qBDService.yarnHEnd, str(qBDService.yarnHPort))
                response = jsonify({'Status': 'Yarn History server not responding'})
                response.status_code = 408
                return response
            qES = dbESCore.query.filter_by(MasterNode=1).first()
            if qES is None:
                response = jsonify({'Status': 'ES not registered'})
                response.status_code = 404
                app.logger.error('[%s] : [ERROR] ES core not registered into dmon', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response

            try:
                rIndex = dmonESIndexer(qES.hostIP, dmonindex='ystat', dmondoc_type='yarn_jobstasks', docId='yarn-jobstasks', body=jStatTask)
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Indexing failed with %s and %s',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                response = jsonify({'Status': 'Error while indexing'})
                response.status_code = 503
                return response
            app.logger.info('[%s] : [INFO] Jobs indexed %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(rIndex))
            # return rIndex
            return jStatTask


@dmon.route('/v1/overlord/nodes/<nodeFQDN>')
@api.doc(params={'nodeFQDN': 'Nodes FQDN'})
class MonitoredNodeInfo(Resource):
    def get(self, nodeFQDN):
        qNode = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
        if qNode is None:
            response = jsonify({'Status': 'Node ' + nodeFQDN + ' not found!'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No node %s found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN)
            return response
        else:
            response = jsonify({
                'NodeName': qNode.nodeFQDN,
                'Status': qNode.nStatus,
                'IP': qNode.nodeIP,
                'Monitored': qNode.nMonitored,
                'OS': qNode.nodeOS,
                'Key': qNode.nkey,
                'Roles': qNode.nRoles,
                'LSInstance': qNode.nLogstashInstance
            })
            response.status_code = 200
            app.logger.info(
                '[%s] : [INFO] Node info -> Status:%s, IP:%s, Monitored:%s, OS:%s, LSInstance: %s, Key:%s, Roles:%s, ',
                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qNode.nStatus,
                qNode.nodeIP, qNode.nMonitored, qNode.nodeOS, qNode.nLogstashInstance, qNode.nkey,
                str(qNode.nRoles))
            return response

    @api.expect(nodeUpdate)
    def put(self, nodeFQDN):
        if not request.json:
            abort(400)
            app.logger.warning('[%s] : [WARN] Malformed request, not json',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        qNode = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
        nLSI = ''
        if qNode is None:
            response = jsonify({'Status': 'Node ' + nodeFQDN + ' not found!'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No node %s found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN)
            return response
        else:
            qNode.nodeIP = request.json['IP']
            qNode.nodeOS = request.json['OS']
            if 'Key' not in request.json:
                app.logger.warning('[%s] : [WARN] Key not changed for node  %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN)
            else:
                qNode.nkey = request.json['Key']
            qNode.nPass = request.json['Password']
            qNode.nUser = request.json['User']
            if 'LogstashInstance' not in request.json:
                qLSCore = dbNodes.query.first()
                if qLSCore is None:
                    nLSI = 'None'
                else:
                    nLSI = qLSCore.hostIP
            else:
                nLSI = request.json['LogstashInstance']
                app.logger.info('[%s] : [INFO] LS Instance changed for node %s from %s to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                qNode.nodeFQDN, qNode.nLogstashInstance, nLSI)
            response = jsonify({'Status': 'Node ' + nodeFQDN + ' updated!'})
            qNode.nLogstashInstance = nLSI
            response.status_code = 201
            return response

    def delete(self, nodeFQDN):
        qNode = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
        if qNode is None:
            response = jsonify({'Status': 'Node ' + nodeFQDN + ' not found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No node %s found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN)
            return response
        else:
            nodeID = qNode.nodeFQDN
            status = 0
            node = []
            node.append(qNode.nodeIP)
            agentr = AgentResourceConstructor(node, '5222')
            if qNode.nStatus:
                resourceCheck = agentr.check()
                try:
                    r = requests.get(resourceCheck[0], timeout=DMON_TIMEOUT)
                except requests.exceptions.Timeout:
                    app.logger.warning('[%s] : [WARN] Agent on node  %s timedout',
                                       datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeID)
                except requests.exceptions.ConnectionError:
                    app.logger.error('[%s] : [ERROR] Agent on node %s connection error',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeID)
                if r.status_code == 200:
                    resourceList = agentr.shutdownAgent()
                    try:
                        requests.post(resourceList[0], timeout=DMON_TIMEOUT)
                    except requests.exceptions.Timeout:
                        app.logger.warning('[%s] : [WARN] Agent on node  %s timedout',
                                           datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeID)
                        status = 1
                    except requests.exceptions.ConnectionError:
                        app.logger.error('[%s] : [ERROR] Agent on node %s connection error',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeID)
                        status = 2

            db.session.delete(qNode)
            db.session.commit()
            response = jsonify({'Status': status,
                                'Node': nodeID,
                                'Message': 'Node succesfully removed'})
            response.status_code = 200
            return response


@dmon.route('/v1/overlord/nodes/list')
class ClusterNodeListDelete(Resource):
    @api.expect(nodeDelList)
    def delete(self):
        if not request.json:
            app.logger.warning('[%s] : [WARN] Malformed request, not json',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            abort(400)
        listNodes = request.json['Nodes']
        invalidNodes = []
        validNodes = {}
        validNodesList = []
        for n in listNodes:
            qNode = dbNodes.query.filter_by(nodeFQDN=n).first()
            if qNode is None:
                invalidNodes.append(n)
            else:
                validNodes[n] = qNode.nodeIP
                validNodesList.append(qNode.nodeIP)
        agentr = AgentResourceConstructor(validNodesList, '5222')

        resourceShutDown = agentr.shutdownAgent()
        dmon = GreenletRequests(resourceShutDown)
        nodeRes = dmon.parallelPost(None)

        failedNodes = {}
        successNodes = {}
        for res in nodeRes:
            nodeIP = urlparse(res['Node'])
            if res['StatusCode'] == 200:
                for k, v in validNodes.iteritems():
                    if v == nodeIP.hostname:
                        successNodes[k] = v
            else:
                for k, v in validNodes.iteritems():
                    if v == nodeIP.hostname:
                        failedNodes[k] = v
        for nod in validNodesList:
            qNodeDel = dbNodes.query.filter_by(nodeIP=nod).first()
            db.session.delete(qNodeDel)
            db.session.commit()
        response = jsonify({'Valid': validNodes, 'Invalid': invalidNodes, 'Stopped': successNodes, 'Unavailable': failedNodes})
        response.status_code = 200
        dmon.reset()
        return response


@dmon.route('/v1/overlord/nodes/<nodeFQDN>/roles')
@api.doc(params={'nodeFQDN': 'Nodes FQDN'})
class ClusterNodeRoles(Resource):
    @api.expect(nodeRoles)
    def put(self, nodeFQDN):  # TODO validate role names
        qNode = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
        if qNode is None:
            response = jsonify({'Status': 'Node ' + nodeFQDN + ' not found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No node %s found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN)
            return response
        else:
            listRoles = request.json['Roles']
            qNode.nRoles = ', '.join(map(str, listRoles))
            response = jsonify({'Status': 'Node ' + nodeFQDN + ' roles updated!'})
            response.status_code = 201
            app.logger.info('[%s] : [INFO] Node %s roles %s added.',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN,
                            str(qNode.nRoles))
            return response

    # def post(self, nodeFQDN): #TODO -> is this  required
    #     return 'Redeploy configuration for node ' + nodeFQDN + '!'


@dmon.route('/v1/overlord/nodes/<nodeFQDN>/purge')
@api.doc(params={'nodeFQDN': 'Nodes FQDN'})
class PurgeNode(Resource):
    def delete(self, nodeFQDN):
        qPurge = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
        if qPurge is None:
            abort(404)
            app.logger.warning('[%s] : [WARN] No node %s found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN)
        lPurge = []
        lPurge.append(qPurge.nodeIP)
        try:
            serviceCtrl(lPurge, qPurge.nUser, qPurge.nPass, 'logstash-forwarder', 'stop')
        except Exception as inst:
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            response = jsonify({'Error': 'Stopping LSF!'})
            response.status_code = 500
            app.logger.error('[%s] : [ERROR] While stopping LSF on %s with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN, type(inst),
                             inst.args)
            return response
        try:
            serviceCtrl(lPurge, qPurge.nUser, qPurge.nPass, 'collectd', 'stop')
        except Exception as inst:
            response = jsonify({'Error': 'Stopping collectd!'})
            response.status_code = 500
            app.logger.error('[%s] : [ERROR] While stopping collectd on %s with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN, type(inst),
                             inst.args)
            return response

        try:
            stopAgent(lPurge, qPurge.nUser, qPurge.nPass)
        except Exception as inst:
            response = jsonify({'Status': 'Error Stopping agent on  ' + qPurge.nodeFQDN + '!'})
            response.status_code = 500
            app.logger.error('[%s] : [INFO] Error stopping agent on %s with exception %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                             str(qPurge.nodeFQDN), type(inst), inst.args)
            return response

        try:
            purgeAgent(lPurge, qPurge.nUser, qPurge.nPass)
        except Exception as inst:
            response = jsonify({'Status': 'Error deleting agent on  ' + qPurge.nodeFQDN + '!'})
            response.status_code = 500
            app.logger.error('[%s] : [INFO] Error deleting agent on %s with exception %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                             str(qPurge.nodeFQDN), type(inst), inst.args)
            return response

        db.session.delete(qPurge)
        db.session.commit()
        response = jsonify({'Status': 'Node ' + nodeFQDN + ' deleted!'})
        response.status_code = 200
        app.logger.info('[%s] : [INFO] Node %s deleted',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN)
        return response



@dmon.route('/v1/overlord/core/es/config')  # TODO use args for unsafe cfg file upload
class ESCoreConfiguration(Resource):
    def get(self):  # TODO same for all get config file createfunction
        if not os.path.isdir(cfgDir):
            response = jsonify({'Error': 'Config dir not found !'})
            response.status_code = 404
            app.logger.error('[%s] : [ERROR] Config dir not found',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        if not os.path.isfile(os.path.join(cfgDir, 'elasticsearch.yml')):
            response = jsonify({'Status': 'Config file not found !'})
            response.status_code = 404
            app.logger.error('[%s] : [ERROR] ES config dir not found',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        try:
            esCfgfile = open(os.path.join(cfgDir, 'elasticsearch.yml'), 'r')
        except EnvironmentError:
            response = jsonify({'EnvError': 'file not found'})
            response.status_code = 500
            app.logger.error('[%s] : [ERROR] ES config file failed to open',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        return send_file(esCfgfile, mimetype='text/yaml', as_attachment=True)

    @api.expect(esCore)
    def put(self):
        requiredKeys = ['ESClusterName', 'HostFQDN', 'NodeName']
        if not request.json:
            abort(400)
        for key in requiredKeys:
            if key not in request.json:
                response = jsonify({'Error': 'malformed request, missing key(s)'})
                response.status_code = 400
                app.logger.warning('[%s] : [WARN] Malformed Request, missing key(s)',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response

        qESCore = dbESCore.query.filter_by(hostFQDN=request.json['HostFQDN']).first()
        if 'IP' not in request.json:
            ip = '127.0.0.1'
        else:
            ip = request.json['IP']
        if 'NodePort' not in request.json:
            nodePort = 9200
        else:
            nodePort = request.json['NodePort']
        if 'OS' not in request.json:
            os = "unknown"
        else:
            os = request.json["OS"]
        if 'ESCoreHeap' not in request.json:
            ESHeap = '4g'
        else:
            ESHeap = request.json['ESCoreHeap']

        check, value = sysMemoryCheck(ESHeap)
        if not check:
            app.logger.warning('[%s] : [WARN] ES Core service heapsize modified to %s instead of %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(value), str(ESHeap))
            ESHeap = value
        if 'DataNode' not in request.json:
            data = 1
        else:
            data = request.json['DataNode']
        if 'NumOfShards' not in request.json:
            shards = 1
        else:
            shards = request.json['NumOfShards']
        if 'NumOfReplicas' not in request.json:
            rep = 0
        else:
            rep = request.json['NumOfReplicas']
        if 'FieldDataCacheSize' not in request.json:
            fdcs = '20%'
        else:
            fdcs = request.json['FieldDataCacheSize']
        if 'FieldDataCacheExpires' not in request.json:
            fdce = '6h'
        else:
            fdce = request.json['FieldDataCacheExpires']
        if 'FieldDataCacheFilterSize' not in request.json:
            fdcfs = '20%'
        else:
            fdcfs = request.json['FieldDataCacheFilterSize']
        if 'FieldDataCacheFilterExpires' not in request.json:
            fdcfe = '6h'
        else:
            fdcfe = request.json['FieldDataCacheFilterExpires']
        if 'IndexBufferSize' not in request.json:
            ibs = '30%'
        else:
            ibs = request.json['IndexBufferSize']
        if 'MinShardIndexBufferSize' not in request.json:
            msibs = '12mb'
        else:
            msibs = request.json['MinShardIndexBufferSize']
        if 'MinIndexBufferSize' not in request.json:
            mibs = '96mb'
        else:
            mibs = request.json['MinIndexBufferSize']
        test = db.session.query(
            dbESCore.hostFQDN).all()  # TODO: it always sets the first node to master need to fix future version
        if not test:
            master = 1
            app.logger.info('[%s] : [INFO] First ES host set to Master',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        else:
            master = 0
            app.logger.info('[%s] : [INFO] ES host set to Slave',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

        if qESCore is None:
            upES = dbESCore(hostFQDN=request.json["HostFQDN"], hostIP=ip, hostOS=os,
                            nodeName=request.json["NodeName"], clusterName=request.json["ESClusterName"],
                            conf='None', nodePort=nodePort, MasterNode=master, DataNode=data,
                            ESCoreHeap=ESHeap, NumOfShards=shards, NumOfReplicas=rep, FieldDataCacheSize=fdcs,
                            FieldDataCacheExpires=fdce, FieldDataCacheFilterSize=fdcfs,
                            FieldDataCacheFilterExpires=fdcfe, IndexBufferSize=ibs, MinShardIndexBufferSize=msibs,
                            MinIndexBufferSize=mibs)
            db.session.add(upES)
            db.session.commit()
            response = jsonify({'Added': 'ES Config for ' + request.json["HostFQDN"]})
            response.status_code = 201
            app.logger.info(
                '[%s] : [INFO] ES config for %s set to:  OS %s, NodeName %s, ClusterName %s, Port %s, Heap %s, Shards %s, Replicas %s',
                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), os,
                request.json["NodeName"], request.json["ESClusterName"], str(request.json['NodePort']),
                ESHeap, shards, rep)
            return response
        else:
            # qESCore.hostFQDN =request.json['HostFQDN'] #TODO document hostIP and FQDN may not change in README.md
            qESCore.hostOS = os
            qESCore.nodename = request.json['NodeName']
            qESCore.clusterName = request.json['ESClusterName']
            if 'IP' not in request.json:
                # print >> sys.stderr, 'IP unchanged'
                app.logger.info('[%s] : [INFO] IP unchanged', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            elif request.json['IP'] == ip:
                qESCore.hostIP = ip
            if 'NodePort' not in request.json:
                # print >> sys.stderr, 'NodePort unchanged'
                app.logger.info('[%s] : [INFO] NodePort unchanged', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            elif request.json['NodePort'] == nodePort:
                qESCore.nodePort = nodePort
            if 'DataNode' not in request.json:
                # print >> sys.stderr, 'DataNode unchanged'
                app.logger.info('[%s] : [INFO] DataNode unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            elif request.json['DataNode'] == data:
                qESCore.DataNode = data
                # print >> sys.stderr, 'DataNode set to ' + str(data)
                app.logger.info('[%s] : [INFO] DataNode set to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(data))
            if 'ESCoreHeap' not in request.json:
                # print >> sys.stderr, 'ESCoreHeap unchanged'
                app.logger.info('[%s] : [INFO] ESCoreHeap unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            elif request.json['ESCoreHeap'] == ESHeap:
                qESCore.ESCoreHeap = ESHeap
                # print >> sys.stderr, 'ESCoreHeap set to ' + ESHeap
                app.logger.info('[%s] : [INFO] ESCoreHeap set to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), ESHeap)
            if 'NumOfShards' not in request.json:
                # print >> sys.stderr, 'NumOfShards unchanged'
                app.logger.info('[%s] : [INFO] NumOfShards unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            elif request.json['NumOfShards'] == shards:
                qESCore.NumOfShards = shards
                # print >> sys.stderr, 'NumOfShards set to ' + str(shards)
                app.logger.info('[%s] : [INFO] NumOfShard set to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(shards))
            if 'NumOfReplicas' not in request.json:
                # print >> sys.stderr, 'NumOfReplicas unchanged'
                app.logger.info('[%s] : [INFO] NumOfReplicas unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            elif request.json['NumOfReplicas'] == rep:
                qESCore.NumOfReplicas = rep
                # print >> sys.stderr, 'NumOfReplicas set to ' + str(rep)
                app.logger.info('[%s] : [INFO] NumOfReplicas set to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(rep))
            if 'FieldDataCacheSize' not in request.json:
                # print >> sys.stderr, 'FieldDataCacheSize unchanged'
                app.logger.info('[%s] : [INFO] FieldDataCacheSize unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            elif request.json['FieldDataCacheSize'] == fdcs:
                qESCore.FieldDataCacheSize = fdcs
                # print >> sys.stderr, 'FieldDataCacheSize set to ' + fdcs
                app.logger.info('[%s] : [INFO] FieldDataCacheSize set to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fdcs)
            if 'FieldDataCacheExpires' not in request.json:
                # print >> sys.stderr, 'FieldDataCacheExpires unchanged'
                app.logger.info('[%s] : [INFO] FieldDataCacheExpires unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            elif request.json['FieldDataCacheExpires'] == fdce:
                qESCore.FieldDataCacheExpires = fdce
                app.logger.info('[%s] : [INFO] FieldDataCacheExpires set to',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fdce)
                # print >> sys.stderr, 'FieldDataCacheExpires set to ' + fdce
            if 'FieldDataCacheFilterSize' not in request.json:
                # print >> sys.stderr, 'FieldDataCacheFilterSize unchanged'
                app.logger.info('[%s] : [INFO] FieldDataCacheFilterSize unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            elif request.json['FieldDataCacheFilterSize'] == fdcfs:
                qESCore.FieldDataCacheFilterSize = fdcfs
                # print >> sys.stderr, 'FieldDataCacheFilterSize set to ' + fdcfs
                app.logger.info('[%s] : [INFO] FieldDataCacheFilterSize set to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fdcfs)
            if 'FieldDataCacheFilterExpires' not in request.json:
                # print >> sys.stderr, 'FieldDataCacheFilterExpires unchanged'
                app.logger.info('[%s] : [INFO] FieldDataCacheFilterExpires unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            elif request.json['FieldDataCacheFilterExpires'] == fdcfe:
                qESCore.FieldDataCacheFilterExpires = fdcfe
                # print >> sys.stderr, 'FieldDataCacheFilterExpires set to ' + fdcfe
                app.logger.info('[%s] : [INFO] FieldDataCacheFilterExpires set to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fdcfe)
            if 'IndexBufferSize' not in request.json:
                # print >> sys.stderr, 'IndexBufferSize unchanged'
                app.logger.info('[%s] : [INFO] IndexBufferSize unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            elif request.json['IndexBufferSize'] == ibs:
                qESCore.IndexBufferSize = ibs
                # print >> sys.stderr, 'IndexBufferSize set to ' + ibs
                app.logger.info('[%s] : [INFO] IndexBufferSize set to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), ibs)
            if 'MinShardIndexBufferSize' not in request.json:
                # print >> sys.stderr, 'MinShardIndexBufferSize unchanged'
                app.logger.info('[%s] : [INFO] MinShardIndexBufferSize unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            elif request.json['MinShardIndexBufferSize'] == msibs:
                qESCore.MinShardIndexBufferSize = msibs
                # print >> sys.stderr, 'MinShardIndexBufferSize set to ' + msibs
                app.logger.info('[%s] : [INFO] MinShardIndexBufferSize set to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), msibs)
            if 'MinIndexBufferSize' not in request.json:
                # print >> sys.stderr, 'MinIndexBufferSize unchanged'
                app.logger.info('[%s] : [INFO] MinIndexBufferSize unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            elif request.json['MinIndexBufferSize'] == mibs:
                qESCore.MinIndexBufferSize = mibs
                # print >> sys.stderr, 'MinIndexBufferSize set to ' + mibs
                app.logger.info('[%s] : [INFO] MinIndexBufferSize set to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), mibs)
            db.session.commit()
            response = jsonify({'Updated': 'ES config for ' + request.json["HostFQDN"]})
            response.status_code = 201
            app.logger.info('[%s] : [INFO] Updated ES config with %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(request.json))
            return response


@dmon.route('/v1/overlord/core/es/<hostFQDN>')
@api.doc(params={'hostFQDN': 'Host FQDN'})
class ESCoreRemove(Resource):
    def delete(self, hostFQDN):
        qESCorePurge = dbESCore.query.filter_by(hostFQDN=hostFQDN).first()
        if qESCorePurge is None:
            response = jsonify({'Status': 'Unknown host ' + hostFQDN})
            response.status_code = 404
            return response
        try:
            os.kill(qESCorePurge.ESCorePID, signal.SIGTERM)
        except:
            app.logger.warning('[%s] : [WARN] No ES instance with PID %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qESCorePurge.ESCorePID)

        db.session.delete(qESCorePurge)
        db.session.commit()
        response = jsonify({'Status': 'Deleted ES at host ' + hostFQDN})
        response.status_code = 200
        return response


@dmon.route('/v1/overlord/core/ls/<hostFQDN>')
@api.doc(params={'hostFQDN': 'Host FQDN'})
class LSCoreRemove(Resource):
    def delete(self, hostFQDN):
        qLSCorePurge = dbSCore.query.filter_by(hostFQDN=hostFQDN).first()
        if qLSCorePurge is None:
            response = jsonify({'Status': 'Unknown host ' + hostFQDN})
            response.status_code = 404
            return response
        try:
            os.kill(qLSCorePurge.LSCorePID, signal.SIGTERM)
        except:
            app.logger.warning('[%s] : [WARN] No LS instance with PID %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qLSCorePurge.LSCorePID)
        db.session.delete(qLSCorePurge)
        db.session.commit()
        response = jsonify({'Status': 'Deleted LS at host ' + hostFQDN})
        response.status_code = 200
        return response


@dmon.route('/v1/overlord/core/es')
class ESCoreController(Resource):
    def get(self):
        hostsAll = db.session.query(dbESCore.hostFQDN, dbESCore.hostIP, dbESCore.hostOS, dbESCore.nodeName,
                                    dbESCore.nodePort,
                                    dbESCore.clusterName, dbESCore.ESCoreStatus, dbESCore.ESCorePID,
                                    dbESCore.MasterNode, dbESCore.DataNode,
                                    dbESCore.NumOfShards, dbESCore.NumOfReplicas, dbESCore.FieldDataCacheSize,
                                    dbESCore.FieldDataCacheExpires, dbESCore.FieldDataCacheFilterSize,
                                    dbESCore.FieldDataCacheFilterExpires, dbESCore.IndexBufferSize,
                                    dbESCore.MinShardIndexBufferSize, dbESCore.MinIndexBufferSize,
                                    dbESCore.ESCoreDebug, dbESCore.ESCoreHeap).all()
        resList = []
        for hosts in hostsAll:
            confDict = {}
            confDict['HostFQDN'] = hosts[0]
            confDict['IP'] = hosts[1]
            confDict['OS'] = hosts[2]
            confDict['NodeName'] = hosts[3]
            confDict['NodePort'] = hosts[4]
            confDict['ESClusterName'] = hosts[5]
            if checkPID(hosts[7]):
                confDict['Status'] = hosts[6]
                confDict['PID'] = hosts[7]
            else:
                app.logger.warning('[%s] : ES Core service not found at PID %s, setting to failed',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(hosts[7]))
                pidESLoc = os.path.join(pidDir, 'elasticsearch.pid')
                if os.path.isfile(pidESLoc):
                    esPIDf = check_proc(pidESLoc)
                    if checkPID(esPIDf):
                        confDict['Stats'] = 'detached'
                        confDict['PID'] = esPIDf
                        app.logger.warning('[%s] : Detached ES Core service found at PID %s, setting to detached',
                                           datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                           str(esPIDf))
                else:
                    #hosts.ESCorePID = 0
                    #hosts.ESCoreStatus = 'unknown'
                    # todo status detached if pid only in file not in sqlite, read pid from file
                    confDict['Status'] = 'unknown'  #TODO: Document failed message if PID is not assigned to an ES Instance
                    confDict['PID'] = 0
                    app.logger.warning('[%s] : ES Core service not found, setting to unknown',
                                       datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            confDict['MasterNode'] = hosts[8]
            confDict['DataNode'] = hosts[9]
            confDict['NumOfShards'] = hosts[10]
            confDict['NumOfReplicas'] = hosts[11]
            confDict['FieldDataCacheSize'] = hosts[12]
            confDict['FieldDataCacheExpire'] = hosts[13]
            confDict['FieldDataCacheFilterSize'] = hosts[14]
            confDict['FieldDataCacheFilterExpires'] = hosts[15]
            confDict['IndexBufferSize'] = hosts[16]
            confDict['MinShardIndexBufferSize'] = hosts[17]
            confDict['MinIndexBufferSize'] = hosts[18]
            confDict['ESCoreDebug'] = hosts[19]
            confDict['ESCoreHeap'] = hosts[20]
            resList.append(confDict)
        response = jsonify({'ES Instances': resList})
        response.status_code = 200
        return response

    def post(self):
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        esTemp = os.path.join(tmpDir, 'elasticsearch.tmp')  # tmpDir+"/collectd.tmp"
        esfConf = os.path.join(cfgDir, 'elasticsearch.yml')
        qESCore = dbESCore.query.filter_by(MasterNode=1).first()  # TODO -> curerntly only generates config file for master node
        if qESCore is None:
            response = jsonify({"Status": "No master ES instances found!"})
            response.status_code = 500
            return response

        if checkPID(qESCore.ESCorePID) is True:
            subprocess.call(["kill", "-15", str(qESCore.ESCorePID)])

        try:
            template = templateEnv.get_template(esTemp)
        # print >>sys.stderr, template
        except:
            response = jsonify({'Status': 'Error', 'Message': 'Tempalte file unavailable!'})
            response.status_code = 500
            app.logger.error("[%s] : [ERROR] Cannot load es core template at location %s",
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), esTemp)
            return response

        infoESCore = {"clusterName": qESCore.clusterName, "nodeName": qESCore.nodeName, "esLogDir": logDir,
                      "MasterNode": qESCore.MasterNode, "DataNode": qESCore.DataNode,
                      "NumberOfShards": qESCore.NumOfShards, "NumberOfReplicas": qESCore.NumOfReplicas,
                      "IndexBufferSize": qESCore.IndexBufferSize,
                      "MinShardIndexBufferSize": qESCore.MinShardIndexBufferSize,
                      "MinIndexBufferSize": qESCore.MinIndexBufferSize,
                      "FieldDataCacheSize": qESCore.FieldDataCacheSize,
                      "FieldDataCacheExpires": qESCore.FieldDataCacheExpires,
                      "FieldDataCacheFilterSize": qESCore.FieldDataCacheFilterSize,
                      "FieldDataCacheFilterExpires": qESCore.FieldDataCacheFilterExpires,
                      "ESCoreDebug": qESCore.ESCoreDebug}
        esConf = template.render(infoESCore)
        qESCore.conf = esConf
        # print >>sys.stderr, esConf
        db.session.commit()
        esCoreConf = open(esfConf, "w+")
        esCoreConf.write(esConf)
        esCoreConf.close()

        # TODO find better solution
        os.system('rm -rf /opt/elasticsearch/config/elasticsearch.yml')
        os.system('cp ' + esfConf + ' /opt/elasticsearch/config/elasticsearch.yml ')

        os.environ['ES_HEAP_SIZE'] = qESCore.ESCoreHeap

        esPid = 0
        try:
            esPid = subprocess.Popen('/opt/elasticsearch/bin/elasticsearch',
                                     stdout=subprocess.PIPE, close_fds=True).pid  # TODO: Try -p to set pid file location and -d for daemon
        except Exception as inst:
            # print >> sys.stderr, 'Error while starting elasticsearch'
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            app.logger.error("[%s] : [ERROR] Cannot start ES Core service with %s and %s",
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            response = jsonify({'Status': 'Error', 'Message': 'Cannot start ES Core'})
            response.status_code = 500
            return response
        qESCore.ESCorePID = esPid
        qESCore.ESCoreStatus = 'Running'
        # ES core pid location
        pidESLoc = os.path.join(pidDir, 'elasticsearch.pid')
        try:
            esPIDFile = open(pidESLoc, 'w+')
            esPIDFile.write(str(esPid))
            esPIDFile.close()
        except IOError:
            response = jsonify({'Error': 'File I/O!'})
            response.status_code = 500
            return response
        response = jsonify({'Status': 'ElasticSearch Core  PID ' + str(esPid)})
        response.status_code = 200
        return response


@dmon.route('/v2/overlord/core/es')
class ESCoreControllerInit(Resource):
    def post(self):
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        esTemp = os.path.join(tmpDir, 'elasticsearch.tmp')  # tmpDir+"/collectd.tmp"
        esfConf = os.path.join(cfgDir, 'elasticsearch.yml')
        pidESLoc = os.path.join(pidDir, 'elasticsearch.pid')
        qESCore = dbESCore.query.filter_by(MasterNode=1).first()  # TODO -> curerntly only generates config file for master node
        if qESCore is None:
            response = jsonify({"Status": "No master ES instances found!"})
            response.status_code = 500
            return response

        # if checkPID(qESCore.ESCorePID) is True:
        #     subprocess.call(["kill", "-15", str(qESCore.ESCorePID)])

        try:
            template = templateEnv.get_template(esTemp)
        except:
            response = jsonify({'Status': 'Error', 'Message': 'Tempalte file unavailable!'})
            response.status_code = 500
            app.logger.error("[%s] : [ERROR] Cannot load es core template at location %s",
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), esTemp)
            return response

        infoESCore = {"clusterName": qESCore.clusterName, "nodeName": qESCore.nodeName, "esLogDir": logDir,
                      "MasterNode": qESCore.MasterNode, "DataNode": qESCore.DataNode,
                      "NumberOfShards": qESCore.NumOfShards, "NumberOfReplicas": qESCore.NumOfReplicas,
                      "IndexBufferSize": qESCore.IndexBufferSize,
                      "MinShardIndexBufferSize": qESCore.MinShardIndexBufferSize,
                      "MinIndexBufferSize": qESCore.MinIndexBufferSize,
                      "FieldDataCacheSize": qESCore.FieldDataCacheSize,
                      "FieldDataCacheExpires": qESCore.FieldDataCacheExpires,
                      "FieldDataCacheFilterSize": qESCore.FieldDataCacheFilterSize,
                      "FieldDataCacheFilterExpires": qESCore.FieldDataCacheFilterExpires,
                      "ESCoreDebug": qESCore.ESCoreDebug}
        esConf = template.render(infoESCore)
        qESCore.conf = esConf
        # print >>sys.stderr, esConf
        db.session.commit()
        esCoreConf = open(esfConf, "w+")
        esCoreConf.write(esConf)
        esCoreConf.close()

        # TODO find better solution
        os.system('rm -rf /opt/elasticsearch/config/elasticsearch.yml')
        os.system('cp ' + esfConf + ' /opt/elasticsearch/config/elasticsearch.yml ')

        os.environ['ES_HEAP_SIZE'] = qESCore.ESCoreHeap

        #check for running detached es core
        if os.path.isfile(pidESLoc):
            esPIDf = check_proc(pidESLoc)
        else:
            esPIDf = 0

        if esPIDf != qESCore.ESCorePID:
            app.logger.warning("[%s] : [WARN] Conflicting PID values found, detached pid -> %s, attached -> %s",
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(esPIDf),
                               str(qESCore.ESCorePID))

        if checkPID(qESCore.ESCorePID) is True:
            try:
                subprocess.check_call(["service", "dmon-es", "restart", qESCore.ESCoreHeap])
            except Exception as inst:
                app.logger.error("[%s] : [ERROR] Cannot restart ES Core service with %s and %s",
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Cannot restart ES Core'})
                response.status_code = 500
                return response
            esPID = check_proc(pidESLoc)
            if not esPID:
                app.logger.error("[%s] : [ERROR] Can't read pidfile for es core",
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                response = jsonify({'Status': 'Error', 'Message': 'Cannot read escore pid file'})
                response.status_code = 500
                return response
            qESCore.ESCorePID = esPID
            qESCore.ESCoreStatus = 'Running'
            response = jsonify({'Status': 'ES Core Restarted', 'PID': esPID})
            response.status_code = 201
            return response
        elif checkPID(int(esPIDf)) is True:
            try:
                subprocess.check_call(["service", "dmon-es", "restart", qESCore.ESCoreHeap])
            except Exception as inst:
                app.logger.error("[%s] : [ERROR] Cannot restart detached ES Core service with %s and %s",
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Cannot restart detached ES Core'})
                response.status_code = 500
                return response
            esPID = check_proc(pidESLoc)
            if not esPID:
                app.logger.error("[%s] : [ERROR] Can't read pidfile for es core",
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                response = jsonify({'Status': 'Error', 'Message': 'Cannot read escore pid file'})
                response.status_code = 500
                return response
            qESCore.ESCorePID = esPID
            qESCore.ESCoreStatus = 'Running'
            response = jsonify({'Status': 'ES Core  Restarted and attached', 'PID': esPID})
            response.status_code = 201
            return response
        else:
            try:
                subprocess.check_call(["service", "dmon-es", "start", qESCore.ESCoreHeap])
            except Exception as inst:
                app.logger.error("[%s] : [ERROR] Cannot start ES Core service with %s and %s",
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Cannot start ES Core'})
                response.status_code = 500
                return response
            esPID = check_proc(pidESLoc)
            if not esPID:
                app.logger.error("[%s] : [ERROR] Can't read pidfile for es core",
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                response = jsonify({'Status': 'Error', 'Message': 'Cannot read escore pid file'})
                response.status_code = 500
                return response
            qESCore.ESCorePID = esPID
            qESCore.ESCoreStatus = 'Running'
            response = jsonify({'Status': 'ES Core Started', 'PID': esPID})
            response.status_code = 201
            return response
        # response = jsonify({'Status': 'ElasticSearch Core  PID ' + str(esPid)})
        # response.status_code = 200
        # return response


@dmon.route('/v2/overlord/core/es/<hostFQDN>/start')
@api.doc(params={'hostFQDN': 'Host FQDN'})
class ESControllerStartInit(Resource):
    def post(self, hostFQDN):
        qESCoreStart = dbESCore.query.filter_by(hostFQDN=hostFQDN).first()
        pidESLoc = os.path.join(pidDir, 'elasticsearch.pid')
        if qESCoreStart is None:
            response = jsonify({'Status': 'Unknown host ' + hostFQDN})
            response.status_code = 404
            return response

        if checkPID(qESCoreStart.ESCorePID) is True:
            proc = psutil.Process(qESCoreStart.ESCorePID)
            if proc.status() == psutil.STATUS_ZOMBIE:
                # print >> sys.stderr, 'Process ' + str(qESCoreStart.ESCorePID) + ' is zombie!'
                app.logger.warning("[%s] : [WARN] Process %s is zombie!",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(qESCoreStart.ESCorePID))
            else:
                app.logger.info("[%s] : [INFO] ES Core alredy running with pid %s",
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                str(qESCoreStart.ESCorePID))
                response = jsonify({'Status': 'Detected ES Core instance', 'PID': qESCoreStart.ESCorePID})
                response.status_code = 200
                return response

        os.environ['ES_HEAP_SIZE'] = qESCoreStart.ESCoreHeap

        # check for running detached es core
        if os.path.isfile(pidESLoc):
            esPIDf = check_proc(pidESLoc)
        else:
            esPIDf = 0

        if esPIDf != qESCoreStart.ESCorePID:
            app.logger.warning("[%s] : [WARN] Conflicting PID values found, detached pid -> %s, attached -> %s",
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(esPIDf),
                               str(qESCoreStart.ESCorePID))
        elif checkPID(int(esPIDf)) is True:
            app.logger.info("[%s] : [INFO] ES Core alredy running with detached pid %s",
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                            str(qESCoreStart.ESCorePID))
            response = jsonify({'Status': 'Detected detached ES Core instance', 'PID': esPIDf})
            response.status_code = 200
            return response
        else:
            try:
                subprocess.check_call(["service", "dmon-es", "start", qESCoreStart.ESCoreHeap])
            except Exception as inst:
                app.logger.error("[%s] : [ERROR] Cannot start ES Core service with %s and %s",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                 inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Cannot start ES Core'})
                response.status_code = 500
                return response
            esPID = check_proc(pidESLoc)
            if not esPID:
                app.logger.error("[%s] : [ERROR] Can't read pidfile for es core",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                response = jsonify({'Status': 'Error', 'Message': 'Cannot read escore pid file'})
                response.status_code = 500
                return response
            qESCoreStart.ESCorePID = esPID
            qESCoreStart.ESCoreStatus = 'Running'
            response = jsonify({'Status': 'ES Core Started', 'PID': esPID})
            response.status_code = 201
            return response


@dmon.route('/v2/overlord/core/es/<hostFQDN>/stop')
@api.doc(params={'hostFQDN': 'Host FQDN'})
class ESControllerStopInit(Resource):
    def post(self, hostFQDN):
        qESCoreStop = dbESCore.query.filter_by(hostFQDN=hostFQDN).first()
        pidESLoc = os.path.join(pidDir, 'elasticsearch.pid')
        if qESCoreStop is None:
            response = jsonify({'Status': 'Unknown host ' + hostFQDN})
            response.status_code = 404
            return response
            # check for running detached es core
        if os.path.isfile(pidESLoc):
            esPIDf = check_proc(pidESLoc)
        else:
            esPIDf = 0
        if checkPID(qESCoreStop.ESCorePID) is True:
            # os.kill(qESCoreStop.ESCorePID, signal.SIGTERM)
            try:
                subprocess.check_call(["service", "dmon-es", "stop"])
            except Exception as inst:
                app.logger.error("[%s] : [ERROR] Cannot stop ES Core service with %s and %s",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                 inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Cannot stop ES Core'})
                response.status_code = 500
                return response
            qESCoreStop.ESCoreStatus = 'Stopped'
            response = jsonify({'Status': 'Stopped',
                                'Message': 'Stopped ES instance at ' + str(qESCoreStop.ESCorePID)})
            app.logger.info('[%s] : [INFO] Stopped ES instance with pid %s ',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qESCoreStop.ESCorePID)
            response.status_code = 200
            return response
        elif checkPID(esPIDf) is True:
            try:
                subprocess.check_call(["service", "dmon-es", "stop"])
            except Exception as inst:
                app.logger.error("[%s] : [ERROR] Cannot stop detached ES Core service with %s and %s",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                 inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Cannot stop ES Core'})
                response.status_code = 500
                return response
            qESCoreStop.ESCoreStatus = 'Stopped'
            response = jsonify({'Status': 'Stopped',
                                'Message': 'Stopped detached ES instance at ' + str(qESCoreStop.ESCorePID)})
            app.logger.info('[%s] : [INFO] Stopped ES instance with pid %s ',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), qESCoreStop.ESCorePID)
            response.status_code = 200
            return response
        else:
            qESCoreStop.ESCoreStatus = 'unknown'
            response = jsonify({'Status': 'No ES Instance Found',
                                'Message': 'No ES instance with PID ' + str(qESCoreStop.ESCorePID)})
            response.status_code = 404
            return response


@dmon.route('/v/overlord/core/es/status/<intComp>/property/<intProp>')
@api.doc(params={'intComp': 'ES specific component', 'intProp': 'Component specific property'})
class ESControllerStatus(Resource):
    def get(self, intComp, intProp):

        compList = ['cluster', 'shards']
        propList = ['health', 'stats', 'pending_tasks', 'list']

        if intComp not in compList:
            response = jsonify({'Status': 'Invalid argument',
                                'Message': 'Argument ' + intComp + ' not supported'})
            response.status_code = 400
            return response

        if intProp not in propList:
            response = jsonify({'Status': 'Invalid argument',
                                'Message': 'Argument ' + intProp + ' not supported'})
            response.status_code = 400
            return response

        qESCore = dbESCore.query.filter_by(MasterNode=1).first()
        if qESCore is None:
            response = jsonify({"Status": "No master ES instances found!"})
            response.status_code = 500
            return response
        if intComp == 'cluster':
            try:
                esCoreUrl = 'http://%s:%s/%s/%s' % (qESCore.hostIP, qESCore.nodePort, '_cluster', intProp)
                app.logger.info('[%s] : [INFO] ES Core Url set to %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), esCoreUrl)
                # print >> sys.stderr, esCoreUrl
                r = requests.get(esCoreUrl, timeout=DMON_TIMEOUT)  # timeout in seconds
                data = r.json()
            except:
                app.logger.error('[%s] : [ERROR] Master ES instance unreachable at %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), esCoreUrl)
                response = jsonify({"Error": "Master ES instances not reachable!"})
                response.status_code = 500
                return response
        elif intComp == 'shards' and intProp == 'list':
            try:
                shardUrl = 'http://%s:%s/%s/%s' % (qESCore.hostIP, qESCore.nodePort, '_cat', intComp)
                app.logger.info("[%s] : [INFO] Shard URL set to %s",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), shardUrl)
                # print >> sys.stderr, shardUrl
                r = requests.get(shardUrl, timeout=DMON_TIMEOUT)
                data = r.text
            except:
                response = jsonify({"Error": "Master ES instances not reachable!"})
                response.status_code = 500
                return response
        else:
            response = jsonify({"Status": "Mallformed request"})
            response.status_code = 400
            return response
        return data

@dmon.route('/v1/overlord/core/es/index/<index>')
class ESControllerIndex(Resource):
    def get(self, index):
        qES = dbESCore.query.filter_by(MasterNode=1).first()
        if qES is None:
            app.logger.error('[%s] : [ERROR] Master ES instance not set at %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'Missing es core',
                                'Message': 'ES core instance not set'})
            response.status_code = 503
            return response

        ecc = ESCoreConnector(esEndpoint=qES.hostIP)
        res = ecc.getIndexSettings(index)
        if res:
            response = jsonify(res)
            response.status_code = 200
            return response
        else:
            response = jsonify({'Status': 'Error',
                                'Message': 'Cannot get index settings'})
            response.status_code = 500
            return response


@dmon.route('/v1/overlord/core/es/cluster/health')
class ESControllerClusterHealth(Resource):
    def get(self):
        qES = dbESCore.query.filter_by(MasterNode=1).first()
        if qES is None:
            app.logger.error('[%s] : [ERROR] Master ES instance not set at %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'Missing es core',
                                'Message': 'ES core instance not set'})
            response.status_code = 503
            return response
        ecc = ESCoreConnector(esEndpoint=qES.hostIP)
        res = ecc.clusterHealth()
        if res:
            response = jsonify(res)
            response.status_code = 200
            return response
        else:
            response = jsonify({'Status': 'Error',
                                'Message': 'Cannot get cluster health'})
            response.status_code = 500
            return response


@dmon.route('/v1/overlord/core/es/cluster/settings')
class ESControllerClusterSettings(Resource):
    def get(self):
        qES = dbESCore.query.filter_by(MasterNode=1).first()
        if qES is None:
            app.logger.error('[%s] : [ERROR] Master ES instance not set at %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'Missing es core',
                                'Message': 'ES core instance not set'})
            response.status_code = 503
            return response
        ecc = ESCoreConnector(esEndpoint=qES.hostIP)
        res = ecc.clusterSettings()
        if res:
            response = jsonify(res)
            response.status_code = 200
            return response
        else:
            response = jsonify({'Status': 'Error',
                                'Message': 'Cannot get cluster settings'})
            response.status_code = 500
            return response


@dmon.route('/v1/overlord/core/es/cluster/state')
class ESCOntrollerClusterState(Resource):
    def get(self):
        qES = dbESCore.query.filter_by(MasterNode=1).first()
        if qES is None:
            app.logger.error('[%s] : [ERROR] Master ES instance not set at %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'Missing es core',
                                'Message': 'ES core instance not set'})
            response.status_code = 503
            return response
        ecc = ESCoreConnector(esEndpoint=qES.hostIP)
        res = ecc.clusterState()
        if res:
            response = jsonify(res)
            response.status_code = 200
            return response
        else:
            response = jsonify({'Status': 'Error',
                                'Message': 'Cannot get cluster state'})
            response.status_code = 500
            return response


@dmon.route('/v1/overlord/core/es/node/master/info')
class ESControllerNodeInfo(Resource):
    def get(self):
        qES = dbESCore.query.filter_by(MasterNode=1).first()
        if qES is None:
            app.logger.error('[%s] : [ERROR] Master ES instance not set at %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'Missing es core',
                                'Message': 'ES core instance not set'})
            response.status_code = 503
            return response
        ecc = ESCoreConnector(esEndpoint=qES.hostIP)
        res = ecc.nodeInfo()
        if res:
            response = jsonify(res)
            response.status_code = 200
            return response
        else:
            response = jsonify({'Status': 'Error',
                                'Message': 'Cannot get node info'})
            response.status_code = 500
            return response


@dmon.route('/v1/overlord/core/es/node/master/state')
class ESControllerNodeState(Resource):
    def get(self):
        qES = dbESCore.query.filter_by(MasterNode=1).first()
        if qES is None:
            app.logger.error('[%s] : [ERROR] Master ES instance not set at %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'Missing es core',
                                'Message': 'ES core instance not set'})
            response.status_code = 503
            return response
        ecc = ESCoreConnector(esEndpoint=qES.hostIP)
        res = ecc.nodeState()
        if res:
            response = jsonify(res)
            response.status_code = 200
            return response
        else:
            response = jsonify({'Status': 'Error',
                                'Message': 'Cannot get node state'})
            response.status_code = 500
            return response

# todo add node state and info for each registered node


@dmon.route('/v1/overlord/core/es/<hostFQDN>/status')
@api.doc(params={'hostFQDN': 'Host FQDN'})
class ESControllerStatusSpecific(Resource):
    def get(self, hostFQDN):
        qESCoreStatus = dbESCore.query.filter_by(hostFQDN=hostFQDN).first()
        if qESCoreStatus is None:
            response = jsonify({'Status': 'Unknown host ' + hostFQDN})
            response.status_code = 404
            return response
        pid = qESCoreStatus.ESCorePID
        if not checkPID(pid):
            if pid != 0:
                qESCoreStatus.ESCoreStatus = 'Stopped'
            else:
                qESCoreStatus.ESCoreStatus = 'unknown'
        response = jsonify({'Status': qESCoreStatus.ESCoreStatus,
                            'PID': qESCoreStatus.ESCorePID})
        response.status_code = 200
        return response


@dmon.route('/v1/overlord/core/es/<hostFQDN>/start')
@api.doc(params={'hostFQDN': 'Host FQDN'})
class ESControllerStart(Resource):
    def post(self, hostFQDN):
        qESCoreStart = dbESCore.query.filter_by(hostFQDN=hostFQDN).first()
        if qESCoreStart is None:
            response = jsonify({'Status': 'Unknown host ' + hostFQDN})
            response.status_code = 404
            return response

        if checkPID(qESCoreStart.ESCorePID) is True:
            proc = psutil.Process(qESCoreStart.ESCorePID)
            if proc.status() == psutil.STATUS_ZOMBIE:
                # print >> sys.stderr, 'Process ' + str(qESCoreStart.ESCorePID) + ' is zombie!'
                app.logger.warning("[%s] : [WARN] Process %s is zombie!",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(qESCoreStart.ESCorePID))
            else:
                response = jsonify({'Status': 'ES already Running',
                                    'PID': str(qESCoreStart.ESCorePID)})
                response.status_code = 200
                return response

        esPid = 0
        try:
            esPid = subprocess.Popen('/opt/elasticsearch/bin/elasticsearch',
                                     stdout=subprocess.PIPE).pid  # TODO: Try -p to set pid file location
        except Exception as inst:
            app.logger.error("[%s] : [ERROR] Cannot start ES core service with %s and %s",
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            response = jsonify({'Status': 'error', 'Message': 'Cannot start ES Core instance'})
            response.status_code = 500
            return response
            # print >> sys.stderr, 'Error while starting elasticsearch'
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
        qESCoreStart.ESCorePID = esPid
        qESCoreStart.ESCoreStatus = 'Running'
        # ES core pid location
        pidESLoc = os.path.join(pidDir, 'elasticsearch.pid')
        try:
            esPIDFile = open(pidESLoc, 'w+')
            esPIDFile.write(str(esPid))
            esPIDFile.close()
        except IOError:
            response = jsonify({'Error': 'File I/O!'})
            response.status_code = 500
            return response
        response = jsonify({'Status': 'ElasticSearch Core  PID ' + str(esPid)})
        response.status_code = 201
        return response


@dmon.route('/v1/overlord/core/es/<hostFQDN>/stop')
@api.doc(params={'hostFQDN': 'Host FQDN'})
class ESControllerStop(Resource):
    def post(self, hostFQDN):
        qESCoreStop = dbESCore.query.filter_by(hostFQDN=hostFQDN).first()
        if qESCoreStop is None:
            response = jsonify({'Status': 'Unknown host ' + hostFQDN})
            response.status_code = 404
            return response
        if checkPID(qESCoreStop.ESCorePID) is True:
            os.kill(qESCoreStop.ESCorePID, signal.SIGTERM)
            qESCoreStop.ESCoreStatus = 'Stopped'
            response = jsonify({'Status': 'Stopped',
                                'Message': 'Stopped ES instance at ' + str(qESCoreStop.ESCorePID)})
            response.status_code = 200
            return response
        else:
            qESCoreStop.ESCoreStatus = 'unknown'
            response = jsonify({'Status': 'No ES Instance Found',
                                'Message': 'No ES instance with PID ' + str(qESCoreStop.ESCorePID)})
            response.status_code = 404
            return response


@dmon.route('/v1/overlord/core/kb/config')
class KBCoreConfiguration(Resource):
    def get(self):
        if not os.path.isdir(cfgDir):
            response = jsonify({'Error': 'Config dir not found !'})
            response.status_code = 404
            return response
        if not os.path.isfile(os.path.join(cfgDir, 'kibana.yaml')):
            response = jsonify({'Error': 'Config file not found !'})
            response.status_code = 404
            return response
        try:
            lsCfgfile = open(os.path.join(cfgDir, 'kibana.yaml'), 'r')
        except EnvironmentError:
            response = jsonify({'EnvError': 'file not found'})
            response.status_code = 500
            return response
        return send_file(lsCfgfile, mimetype='text/yaml', as_attachment=True)

    @api.expect(kbCore)  # TODO same for all 3 core services create one class for all
    def put(self):
        requiredKeys = ['HostFQDN', 'IP']
        if not request.json:
            abort(400)
        for key in requiredKeys:
            if key not in request.json:
                response = jsonify({'Error': 'malformed request, missing key(s)'})
                response.status_code = 400
                return response

        qKBCore = dbKBCore.query.filter_by(hostIP=request.json['IP']).first()
        if request.json["OS"] is None:
            os = "unknown"
        else:
            os = request.json["OS"]

        if qKBCore is None:
            upKB = dbKBCore(hostFQDN=request.json["HostFQDN"], hostIP=request.json["IP"],
                            hostOS=os, kbPort=request.json["KBPort"], KBCoreStatus='Stopped')
            db.session.add(upKB)
            db.session.commit()
            response = jsonify({'Added': 'KB Config for ' + request.json["HostFQDN"]})
            response.status_code = 201
            return response
        else:
            qKBCore.hostOS = os
            qKBCore.kbPort = request.json['KBPort']
            db.session.commit()
            response = jsonify({'Updated': 'KB config for ' + request.json["HostFQDN"]})
            response.status_code = 201
            return response


@dmon.route('/v1/overlord/core/kb')
class KKCoreController(Resource):
    def get(self):
        KBhostsAll = db.session.query(dbKBCore.hostFQDN, dbKBCore.hostIP, dbKBCore.hostOS,
                                      dbKBCore.kbPort, dbKBCore.KBCorePID, dbKBCore.KBCoreStatus).all()
        resList = []
        for hosts in KBhostsAll:
            confDict = {}
            confDict['HostFQDN'] = hosts[0]
            confDict['IP'] = hosts[1]
            confDict['OS'] = hosts[2]
            confDict['KBPort'] = hosts[3]
            if checkPID(hosts[4]):
                confDict['Status'] = hosts[5]
                confDict['PID'] = hosts[4]
            else:
                app.logger.warning('[%s] : KB Core service not found at PID %s, setting to failed',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(hosts[7]))
                #hosts.ESCorePID = 0
                #hosts.ESCoreStatus = 'unknown'
                confDict['Status'] = 'failed'  #TODO: Document failed message if PID is not assigned to an KB Instance
                confDict['PID'] = 0
            resList.append(confDict)
        response = jsonify({'KB Instances': resList})
        response.status_code = 200
        return response

    def post(self):
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        kbTemp = os.path.join(tmpDir, 'kibana.tmp')  # tmpDir+"/collectd.tmp"
        kbfConf = os.path.join(cfgDir, 'kibana.yml')
        qKBCore = dbKBCore.query.first()
        if qKBCore is None:
            response = jsonify({"Status": "No KB instance found!"})
            response.status_code = 500
            return response

        if checkPID(qKBCore.KBCorePID) is True:
            subprocess.call(["kill", "-9", str(qKBCore.KBCorePID)])

        try:
            template = templateEnv.get_template(kbTemp)
        # print >>sys.stderr, template
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Template file unavailable with %s and %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            response = jsonify({'Status': 'Error', 'Message': 'Template file unavailable'})
            response.status_code = 500
            return response

        # Log and PID location for kibana

        kbPID = os.path.join(pidDir, 'kibana.pid')
        kbLog = os.path.join(logDir, 'kibana.log')

        infoKBCore = {"kbPort": qKBCore.kbPort, "kibanaPID": kbPID, "kibanaLog": kbLog}
        kbConf = template.render(infoKBCore)
        qKBCore.conf = kbConf
        # print >>sys.stderr, esConf
        db.session.commit()
        kbCoreConf = open(kbfConf, "w+")
        kbCoreConf.write(kbConf)
        kbCoreConf.close()

        # TODO find better solution
        os.system('rm -rf /opt/kibana/config/kibana.yml')
        os.system('cp ' + kbfConf + ' /opt/kibana/config/kibana.yml ')

        kbPid = 0
        FNULL = open(os.devnull, 'w')
        try:
            kbPid = subprocess.Popen('/opt/kibana/bin/kibana', stdout=FNULL, stderr=subprocess.STDOUT).pid
        except Exception as inst:
            app.logger.warning('[%s] : [ERROR] Cannot start KB core service with %s and %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            response = jsonify({'Status': 'Error', 'Message': 'Cannot start Kibana Core'})
            response.status_code = 500
            return response
        qKBCore.KBCorePID = kbPid
        qKBCore.KBCoreStatus = 'Running'
        response = jsonify({'Status': 'Kibana Core  PID ' + str(kbPid)})
        response.status_code = 200
        return response


@dmon.route('/v1/overlord/core/kb/visualisations')
class KBVisualisations(Resource):
    def get(self):
        qESCore = dbESCore.query.filter_by(MasterNode=1).first()
        if qESCore is None:
            response = jsonify({'Status': 'ES Core not registered'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] ES Core not registered',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        ecc = ESCoreConnector(esEndpoint=qESCore.hostIP, index='.kibana')
        query = {"query": {"match_all": {}}, "size": 500}
        rsp = ecc.aggQuery('.kibana', queryBody=query)
        if not rsp:
            app.logger.error('[%s] : [ERROR] ES Core unreachable',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'ES Core unreachable'})
            response.status_code = 503
            return response
        foundv = []
        for hits in rsp['hits']['hits']:
            if hits['_type'] == 'visualisation':
                foundv.append(hits['_source']['title'])
        response = jsonify({'Visualisations': foundv})
        response.status_code = 200
        return response

    def post(self):
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        kbVisTemp = os.path.join(tmpDir, 'visualizations')
        qNode = dbNodes.query.all()
        qESCore = dbESCore.query.filter_by(MasterNode=1).first()
        if qESCore is None:
            response = jsonify({'Status': 'ES Core not registered'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] ES Core not registered',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        if qNode is None:
            response = jsonify({'Status': 'No registered nodes'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No nodes found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        nodeDict = {}
        for nodes in qNode:
            listRoles = nodes.nRoles.split(', ')
            nodeDict[nodes.nodeFQDN] = {'IP': nodes.nodeIP, 'Roles': listRoles}

        ecc = ESCoreConnector(esEndpoint=qESCore.hostIP, index='.kibana')
        rsp = {}
        listLoad = []
        listMemory = []
        listPackets = []
        listOctets = []
        listIfError = []
        for node in nodeDict.keys():
            try:
                template = templateEnv.get_template(os.path.join(kbVisTemp, 'load.tmp'))
            # print >>sys.stderr, template
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Template file unavailable with %s and %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Load template file unavailable'})
                response.status_code = 500
                return response
            nodeIDName = node.split('.')[-1]
            lsindex = 'logstash-*'  # TODO create separate viz for more than one index
            infoKBCore = {"nodeID": node, "nodeIDName": nodeIDName, "index": lsindex}
            kbConf = template.render(infoKBCore)
            idStr = "%s-CPU-Load" % nodeIDName
            res = ecc.pushToIndex('.kibana', 'visualization', kbConf, id=idStr)
            try:
                listLoad.append(res["_id"])
            except Exception as inst:
                app.logger.warning('[%s] : [ERROR] Failed to create visualization with  %s and %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                listLoad.append({'Failed': node})

            try:
                template = templateEnv.get_template(os.path.join(kbVisTemp, 'memory.tmp'))
            # print >>sys.stderr, template
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Template file unavailable with %s and %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Load template file unavailable'})
                response.status_code = 500
                return response
            nodeIDName = node.split('.')[-1]
            lsindex = 'logstash-*'  # TODO create separate viz for more than one index
            infoKBCore = {"nodeID": node, "nodeIDName": nodeIDName, "index": lsindex}
            kbConf = template.render(infoKBCore)
            idStr = "%s-Memory" % nodeIDName
            res = ecc.pushToIndex('.kibana', 'visualization', kbConf, id=idStr)
            try:
                listMemory.append(res["_id"])
            except Exception as inst:
                app.logger.warning('[%s] : [ERROR] Failed to create visualization with  %s and %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                listMemory.append({'Failed': node})

            try:
                template = templateEnv.get_template(os.path.join(kbVisTemp, 'packets.tmp'))
            # print >>sys.stderr, template
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Template file unavailable with %s and %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Load template file unavailable'})
                response.status_code = 500
                return response
            nodeIDName = node.split('.')[-1]
            lsindex = 'logstash-*'  # TODO create separate viz for more than one index
            infoKBCore = {"nodeID": node, "nodeIDName": nodeIDName, "index": lsindex}
            kbConf = template.render(infoKBCore)
            idStr = "%s-Packets" % nodeIDName
            res = ecc.pushToIndex('.kibana', 'visualization', kbConf, id=idStr)
            try:
                listPackets.append(res["_id"])
            except Exception as inst:
                app.logger.warning('[%s] : [ERROR] Failed to create visualization with  %s and %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                listPackets.append({'Failed': node})

            try:
                template = templateEnv.get_template(os.path.join(kbVisTemp, 'octets.tmp'))
            # print >>sys.stderr, template
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Template file unavailable with %s and %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Load template file unavailable'})
                response.status_code = 500
                return response
            if len(node.split('.')) == 1:
                nodeIDName = node
            else:
                nodeIDName = node.split('.')[-1]
            lsindex = 'logstash-*'  # TODO create separate viz for more than one index
            infoKBCore = {"nodeID": node, "nodeIDName": nodeIDName, "index": lsindex}
            kbConf = template.render(infoKBCore)
            idStr = "%s-Octets" % nodeIDName
            res = ecc.pushToIndex('.kibana', 'visualization', kbConf, id=idStr)
            try:
                listOctets.append(res["_id"])
            except Exception as inst:
                app.logger.warning('[%s] : [ERROR] Failed to create visualization with  %s and %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                listOctets.append({'Failed': node})

            try:
                template = templateEnv.get_template(os.path.join(kbVisTemp, 'iferror.tmp'))
            # print >>sys.stderr, template
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Template file unavailable with %s and %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Load template file unavailable'})
                response.status_code = 500
                return response
            nodeIDName = node.split('.')[-1]
            lsindex = 'logstash-*'  # TODO create separate viz for more than one index
            infoKBCore = {"nodeID": node, "nodeIDName": nodeIDName, "index": lsindex}
            kbConf = template.render(infoKBCore)
            idStr = "%s-IfError" % nodeIDName
            res = ecc.pushToIndex('.kibana', 'visualization', kbConf, id=idStr)
            try:
                listIfError.append(res["_id"])
            except Exception as inst:
                app.logger.warning('[%s] : [ERROR] Failed to create visualization with  %s and %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                listIfError.append({'Failed': node})

        rsp['Load'] = listLoad
        rsp['Memory'] = listMemory
        rsp['Packets'] = listPackets
        rsp['Octets'] = listOctets
        rsp['IfError'] = listIfError
        app.logger.info('[%s] : [INFO] Created visualizations %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(rsp))
        response = jsonify(rsp)
        response.status_code = 201
        return response


@dmon.route('/v1/overlord/core/kb/visualizations/storm')
class KBVisualizationsStorm(Resource):
    def post(self):
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        kbVisTemp = os.path.join(tmpDir, 'visualizations')
        qNode = dbNodes.query.all()
        qESCore = dbESCore.query.filter_by(MasterNode=1).first()
        if qESCore is None:
            response = jsonify({'Status': 'ES Core not registered'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] ES Core not registered',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        if qNode is None:
            response = jsonify({'Status': 'No registered nodes'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No nodes found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        qSCore = dbSCore.query.first()
        if qSCore is None:
            response = jsonify({"Status": "No LS instances registered", "spouts": 0, "bolts": 0})
            response.status_code = 500
            app.logger.warning('[%s] : [WARN] No LS instance registred',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        if qSCore.LSCoreStormTopology == 'None':
            response = jsonify({"Status": "No Storm topology registered"})
            response.status_code = 404
            app.logger.info('[%s] : [INFO] No Storm topology registered, cannot fetch number of spouts and bolts',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        else:
            bolts, spouts = checkStormSpoutsBolts(qSCore.LSCoreStormEndpoint, qSCore.LSCoreStormPort,
                                                  qSCore.LSCoreStormTopology)
            response = jsonify({'Topology': qSCore.LSCoreStormTopology, "spouts": spouts, "bolts": bolts})
            response.status_code = 200
            app.logger.info('[%s] : [INFO] Storm topology %s with %s spounts and %s bolts found',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                            str(qSCore.LSCoreStormTopology), str(spouts), str(bolts))

            ecc = ESCoreConnector(esEndpoint=qESCore.hostIP, index='.kibana')
            listStorm = []
            try:
                template = templateEnv.get_template(os.path.join(kbVisTemp, 'storm.tmp'))
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Template file unavailable with %s and %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Load template file unavailable'})
                response.status_code = 500
                return response
            lsindex = 'logstash-*'  # TODO create separate viz for more than one index
            infoKBCoreStorm = {"nBolt": bolts, "nSpout": spouts, "lsindex": lsindex}
            kbStorm = template.render(infoKBCoreStorm)
            kbStormJ = json.loads(kbStorm)

            for visualisation in kbStormJ:
                res = ecc.pushToIndex('.kibana', visualisation['_type'], visualisation['_source'], id=visualisation['_id'])
                try:
                    listStorm.append(res["_id"])
                except Exception as inst:
                    app.logger.warning('[%s] : [ERROR] Failed to create visualization with  %s and %s',
                                       datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                       inst.args)
                    listStorm.append({'Failed': visualisation})

            app.logger.info('[%s] : [INFO] Generated storm visualizations: %s ',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                            str(qSCore.LSCoreStormTopology), str(listStorm))
            response = jsonify({'Visualizations': listStorm})
            response.status_code = 201
            return response

@dmon.route('/v1/overlord/core/ls/config')
class LSCoreConfiguration(Resource):
    def get(self):
        if not os.path.isdir(cfgDir):
            response = jsonify({'Error': 'Config dir not found !'})
            response.status_code = 404
            return response
        if not os.path.isfile(os.path.join(cfgDir, 'logstash.conf')):
            response = jsonify({'Error': 'Config file not found !'})
            response.status_code = 404
            return response
        try:
            lsCfgfile = open(os.path.join(cfgDir, 'logstash.conf'), 'r')
        except EnvironmentError:
            response = jsonify({'EnvError': 'file not found'})
            response.status_code = 500
            return response
        return send_file(lsCfgfile, mimetype='text/plain', as_attachment=True)

    @api.expect(lsCore)
    def put(self):
        requiredKeys = ['HostFQDN', 'ESClusterName']
        if not request.json:
            abort(400)
        for key in requiredKeys:
            if key not in request.json:
                response = jsonify({'Error': 'malformed request, missing key(s)'})
                response.status_code = 400
                return response

        qESCheck = dbESCore.query.filter_by(clusterName=request.json['ESClusterName'])
        if qESCheck is None:
            response = jsonify({'Status': 'Invalid cluster name: ' + request.json['ESClusterName']})
            response.status_code = 404
            return response
        qSCore = dbSCore.query.filter_by(hostFQDN=request.json['HostFQDN']).first() #TODO: rework which kv pair is required
        if 'IP' not in request.json:
            hIP = '127.0.0.1'
        else:
            hIP = request.json['IP']
        if 'OS' not in request.json:
            os = "unknown"
        else:
            os = request.json["OS"]

        if 'LSCoreHeap' not in request.json:
            lsHeap = '1g'
        else:
            lsHeap = request.json["LSCoreHeap"]

        if 'LSCoreWorkers' not in request.json:
            lsWorkers = '4'
        else:
            lsWorkers = request.json["LSCoreWorkers"]

        if 'LSCoreStormEndpoint' not in request.json:
            StormEnd = 'None'
        else:
            StormEnd = request.json['LSCoreStormEndpoint']

        if 'LSCoreStormPort' not in request.json:
            StormPort = 'None'
        else:
            StormPort = request.json['LSCoreStormPort']

        if 'LSCoreStormTopology' not in request.json:
            StormTopo = 'None'
        else:
            StormTopo = request.json['LSCoreStormTopology']

        if 'LSCoreSparkEndpoint' not in request.json:
            SparkEnd = 'None'
        else:
            SparkEnd = request.json['LSCoreSparkEndpoint']

        if 'LSCoreSparkPort' not in request.json:
            SparkPort = 'None'
        else:
            SparkPort = request.json['LSCoreSparkPort']

        if 'ESClusterName' not in request.json:
            ESCname = 'diceMonit'
        else:
            ESCname = request.json['ESClusterName']
        if 'udpPort' not in request.json:
            udpPort = 25826
        else:
            udpPort = request.json['udpPort']
        if 'LPort' not in request.json:
            lumberPort = 5000
        else:
            lumberPort = request.json['LPort']

        if 'Index' not in request.json:
            rIndex = 'logstash'
        else:
            rIndex = request.json['Index']

        if qSCore is None:
            upS = dbSCore(hostFQDN=request.json["HostFQDN"], hostIP=hIP, hostOS=os,
                          outESclusterName=ESCname, udpPort=udpPort,
                          inLumberPort=lumberPort, LSCoreWorkers=lsWorkers, LSCoreHeap=lsHeap,
                          LSCoreStormEndpoint=StormEnd, LSCoreStormPort=StormPort, LSCoreStormTopology=StormTopo,
                          LSCoreSparkEndpoint=SparkEnd, LSCoreSparkPort=SparkPort, diceIndex=rIndex)
            db.session.add(upS)
            db.session.commit()
            response = jsonify({'Added': 'LS Config for ' + request.json["HostFQDN"]})
            response.status_code = 201
            return response
        else:
            # qESCore.hostFQDN =request.json['HostFQDN'] #TODO document hostIP and FQDN may not change in README.md
            if 'IP' in request.json:
                qSCore.hostIP = hIP
            if 'OS' in request.json:
                qSCore.hostOS = os
            if 'LSCoreWorkers' in request.json:
                qSCore.LSCoreWorkers = lsWorkers
            if 'LSCoreHeap' in request.json:
                qSCore.LSCoreHeap = lsHeap
            if 'ESClusterName' in request.json:
                qSCore.outESclusterName = ESCname
            if 'udpPort' in request.json:
                qSCore.udpPort = udpPort
            if 'LPort' in request.json:
                qSCore.inLumberPort = lumberPort
            if StormEnd != 'None':
                qSCore.LSCoreStormEndpoint = StormEnd
            if StormPort != 'None':
                qSCore.LSCoreStormPort = StormPort
            if StormTopo != 'None':
                qSCore.LSCoreStormTopology = StormTopo
            if SparkEnd != 'None':
                qSCore.LSCoreSparkEndpoint = SparkEnd
            if SparkPort != 'None':
                qSCore.LSCoreSparkPort = SparkPort
            if 'Index' in request.json:
                qSCore.diceIndex = rIndex
            db.session.commit()
            response = jsonify({'Updated': 'LS config for ' + request.json["HostFQDN"]})
            response.status_code = 201
            return response
        # return "Changes configuration fo logstash server"


@dmon.route('/v1/overlord/core/ls')
class LSCoreController(Resource):
    def get(self):
        hostsAll = db.session.query(dbSCore.hostFQDN, dbSCore.hostIP, dbSCore.hostOS, dbSCore.inLumberPort,
                                    dbSCore.sslCert, dbSCore.sslKey, dbSCore.udpPort, dbSCore.outESclusterName,
                                    dbSCore.LSCoreStatus,
                                    dbSCore.LSCoreStormEndpoint, dbSCore.LSCoreStormPort, dbSCore.LSCoreStormTopology,
                                    dbSCore.LSCoreSparkEndpoint, dbSCore.LSCoreSparkPort, dbSCore.LSCoreHeap, dbSCore.LSCorePID).all()
        resList = []
        for hosts in hostsAll:
            confDict = {}
            confDict['HostFQDN'] = hosts[0]
            confDict['IP'] = hosts[1]
            confDict['OS'] = hosts[2]
            confDict['LPort'] = hosts[3]
            confDict['udpPort'] = hosts[6]
            confDict['ESClusterName'] = hosts[7]
            confDict['LSCoreStormEndpoint'] = hosts[9]
            confDict['LSCoreStormPort'] = hosts[10]
            confDict['LSCoreStormTopology'] = hosts[11]
            confDict['LSCoreSparkEndpoint'] = hosts[12]
            confDict['LSCoreSparkPort'] = hosts[13]
            if checkPID(hosts[15]):
                confDict['Status'] = hosts[8]
                confDict['PID'] = hosts[15]
                app.logger.info('[%s] : LS Core service  found at PID %s',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                   str(hosts[15]))
            else:
                pidLSLoc = os.path.join(pidDir, 'logstash.pid')
                if os.path.isfile(pidLSLoc):
                    esPIDf = check_proc(pidLSLoc)
                    if checkPID(esPIDf):
                        confDict['Status'] = 'detached'  #TODO: Document failed message if PID is not assigned to an LS Instance
                        confDict['PID'] = esPIDf
                        app.logger.warning('[%s] : Detached LS Core service  found at PID %s, setting to detached',
                                           datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                           esPIDf)
                    else:
                        confDict['Status'] = 'unknown'  # TODO: Document failed message if PID is not assigned to an LS Instance
                        confDict['PID'] = 0
                        app.logger.warning('[%s] : LS Core service , setting to unknonw',
                                           datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

            confDict['LSCoreHeap'] = hosts[14]
            resList.append(confDict)
        response = jsonify({'LS Instances': resList})
        response.status_code = 200
        return response

    def post(self):
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        lsTemp = os.path.join(tmpDir, 'logstash.tmp')  # tmpDir+"/collectd.tmp"
        lsfCore = os.path.join(cfgDir, 'logstash.conf')
        # qSCore = db.session.query(dbSCore.hostFQDN).first()
        qSCore = dbSCore.query.first()  # TODO: currently only one LS instance supported
        # return qSCore
        if qSCore is None:
            response = jsonify({"Status": "No LS instances registered"})
            response.status_code = 500
            app.logger.warning('[%s] : [WARN] No LS instance registred',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        qESCore = dbESCore.query.filter_by(MasterNode=1).first()  # TODO: only works with the master node
        if qESCore is None:
            response = jsonify({"Status": "No ES instances registered"})
            response.status_code = 500
            app.logger.warning('[%s] : [WARN] No ES instance registred',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        if checkPID(qSCore.LSCorePID) is True:
            subprocess.call(['kill', '-9', str(qSCore.LSCorePID)])
            app.logger.info('[%s] : [INFO] Killed LS Instance at %s',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                            str(qSCore.LSCorePID))

        try:
            template = templateEnv.get_template(lsTemp)
        # print >>sys.stderr, template
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] LS tempalte file unavailable with %s and %s',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            response = jsonify({"Status": "LS Tempalte file unavailable!"})
            response.status_code = 404
            return response

        if qSCore.sslCert == 'default':
            certLoc = os.path.join(credDir, 'logstash-forwarder.crt')
        else:
            certLoc = os.path.join(credDir, qSCore.sslCert + '.crt')

        if qSCore.sslKey == 'default':
            keyLoc = os.path.join(credDir, 'logstash-forwarder.key')
        else:
            keyLoc = os.path.join(credDir, qSCore.sslKey + '.key')

        if qSCore.LSCoreStormEndpoint == 'None':
            StormRestIP = 'None'
        else:
            StormRestIP = qSCore.LSCoreStormEndpoint
        qNodeRoles = db.session.query(dbNodes.nRoles).all()
        if qNodeRoles is None:
            uniqueRolesList = ['unknown']
        else:
            uList = []
            for r in qNodeRoles:
                uList.append(r[0].split(', '))
            uniqueRoles = set(x for l in uList for x in l) #TODO find better solution for finding unique roles
            uniqueRolesList = list(uniqueRoles)

        qMetInt =dbMetPer.query.first()
        if qMetInt is None:
            stormInterval = '60'
        else:
            stormInterval = qMetInt.stormMet
        if 'storm' in uniqueRolesList:
            stormStatus = 'Storm registered'
            bolts, spouts = checkStormSpoutsBolts(StormRestIP, qSCore.LSCoreStormPort, qSCore.LSCoreStormTopology)
            if spouts == 0 or bolts == 0:
                uniqueRolesList.remove('storm')
                app.logger.warning('[%s] : [WARN] Storm topology spouts and botls not found, ignoring Storm',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                stormStatus = 'Storm Ignored'
        else:
            stormStatus = 'Not registered'
            spouts = 0
            bolts = 0
        app.logger.info('[%s] : [INFO] Storm Status -> %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), stormStatus)

        qBDService = dbBDService.query.first()
        if qBDService is None:
            yarnHEnd = 'None'
            yarnHPort = '19888'
            yarnHPoll = '30'
            yarnStatus = 'Not Registered'
        else:
            yarnHEnd = qBDService.yarnHEnd
            yarnHPort = qBDService.yarnHPort
            yarnHPoll = qBDService.yarnHPoll
            yarnStatus = 'Registered'

        app.logger.info('[%s] : [INFO] Yarn History Status -> %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), yarnStatus)

        # appname tag is set the same for spark and yarn
        qActiveApp = dbApp.query.filter_by(jobID='ACTIVE').first()
        if qActiveApp is None:
            app.logger.warning('[%s] : [WARN] No active applications registered tag set to default',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            appName = 'default'
        else:
            appName = qActiveApp.jobID
            app.logger.info('[%s] : [INFO] Tag for application %s set',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), appName)

        infoSCore = {"sslcert": certLoc, "sslkey": keyLoc, "udpPort": qSCore.udpPort,
                     "ESCluster": qSCore.outESclusterName, "EShostIP": qESCore.hostIP,
                     "EShostPort": qESCore.nodePort, "StormRestIP": StormRestIP,
                     "StormRestPort": qSCore.LSCoreStormPort, "StormTopologyID": qSCore.LSCoreStormTopology,
                     'storm_interval': stormInterval, 'roles': uniqueRolesList, 'myIndex': qSCore.diceIndex,
                     'nSpout': spouts, 'nBolt': bolts, 'yarnHEnd': yarnHEnd, 'yarnHPort': yarnHPort,
                     'yarnHPoll': yarnHPoll, 'appName': appName}
        sConf = template.render(infoSCore)
        qSCore.conf = sConf
        # print >>sys.stderr, esConf
        db.session.commit()

        lsCoreConf = open(lsfCore, "w+")
        lsCoreConf.write(sConf)
        lsCoreConf.close()

        os.environ['LS_HEAP_SIZE'] = os.getenv('LS_HEAP_SIZE',
                                               qSCore.LSCoreHeap)  # TODO: if heap size set in env then use it if not use db one
        app.logger.info('[%s] : [INFO] LS Heap size set to %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        str(os.environ['LS_HEAP_SIZE']))

        lsLogfile = os.path.join(logDir, 'logstash.log')
        lsPid = 0
        LSServerCmd = '/opt/logstash/bin/logstash agent  -f %s -l %s -w %s' % (lsfCore, lsLogfile, qSCore.LSCoreWorkers)
        try:
            lsPid = subprocess.Popen(LSServerCmd, shell=True).pid
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Cannot start LS instance with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            qSCore.LSCoreStatus = 'unknown'
        qSCore.LSCorePID = lsPid
        lsPIDFileLoc = os.path.join(pidDir, 'logstash.pid')
        try:
            lsPIDFile = open(lsPIDFileLoc, 'w+')
            lsPIDFile.write(str(lsPid))
            lsPIDFile.close()
        except IOError:
            response = jsonify({'Error': 'File I/O!'})
            response.status_code = 500
            app.logger.error('[%s] : [ERROR] Cannot write LS pid file',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        qSCore.LSCoreStatus = 'Running'
        app.logger.info('[%s] : [INFO] LS instance started with PID %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(lsPid))
        response = jsonify({'Status': 'Logstash Core PID ' + str(lsPid),
                            'Storm': stormStatus,
                            'YarnHistory': yarnStatus})
        response.status_code = 200
        return response


@dmon.route('/v2/overlord/core/ls')
class LSCoreControllerInit(Resource):
    def post(self):
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        lsTemp = os.path.join(tmpDir, 'logstash.tmp')  # tmpDir+"/collectd.tmp"
        lsfCore = os.path.join(cfgDir, 'logstash.conf')
        # qSCore = db.session.query(dbSCore.hostFQDN).first()
        qSCore = dbSCore.query.first()  # TODO: currently only one LS instance supported
        # return qSCore
        if qSCore is None:
            response = jsonify({"Status": "No LS instances registered"})
            response.status_code = 500
            app.logger.warning('[%s] : [WARN] No LS instance registred',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        qESCore = dbESCore.query.filter_by(MasterNode=1).first()  # TODO: only works with the master node
        if qESCore is None:
            response = jsonify({"Status": "No ES instances registered"})
            response.status_code = 500
            app.logger.warning('[%s] : [WARN] No ES instance registred',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        if checkPID(qSCore.LSCorePID) is True:
            subprocess.call(['kill', '-9', str(qSCore.LSCorePID)])
            app.logger.info('[%s] : [INFO] Killed LS Instance at %s',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                            str(qSCore.LSCorePID))

        try:
            template = templateEnv.get_template(lsTemp)
        # print >>sys.stderr, template
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] LS tempalte file unavailable with %s and %s',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            response = jsonify({"Status": "LS Tempalte file unavailable!"})
            response.status_code = 404
            return response

        if qSCore.sslCert == 'default':
            certLoc = os.path.join(credDir, 'logstash-forwarder.crt')
        else:
            certLoc = os.path.join(credDir, qSCore.sslCert + '.crt')

        if qSCore.sslKey == 'default':
            keyLoc = os.path.join(credDir, 'logstash-forwarder.key')
        else:
            keyLoc = os.path.join(credDir, qSCore.sslKey + '.key')

        if qSCore.LSCoreStormEndpoint == 'None':
            StormRestIP = 'None'
        else:
            StormRestIP = qSCore.LSCoreStormEndpoint
        qNodeRoles = db.session.query(dbNodes.nRoles).all()
        if qNodeRoles is None:
            uniqueRolesList = ['unknown']
        else:
            uList = []
            for r in qNodeRoles:
                uList.append(r[0].split(', '))
            uniqueRoles = set(x for l in uList for x in l)
            uniqueRolesList = list(uniqueRoles)

        qMetInt =dbMetPer.query.first()
        if qMetInt is None:
            stormInterval = '60'
        else:
            stormInterval = qMetInt.stormMet
        if 'storm' in uniqueRolesList:
            stormStatus = 'Storm registered'
            bolts, spouts = checkStormSpoutsBolts(StormRestIP, qSCore.LSCoreStormPort, qSCore.LSCoreStormTopology)
            if spouts == 0 or bolts == 0:
                uniqueRolesList.remove('storm')
                app.logger.warning('[%s] : [WARN] Storm topology spouts and botls not found, ignoring Storm',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                stormStatus = 'Storm ignored'
        else:
            stormStatus = 'Not registered'
            spouts = 0
            bolts = 0
        app.logger.info('[%s] : [INFO] Storm Status -> %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), stormStatus)

        qBDService = dbBDService.query.first()
        if qBDService is None:
            yarnHEnd = 'None'
            yarnHPort = '19888'
            yarnHPoll = '30'
            yarnStatus = 'Not Registered'
        else:
            yarnHEnd = qBDService.yarnHEnd
            yarnHPort = qBDService.yarnHPort
            yarnHPoll = qBDService.yarnHPoll
            yarnStatus = 'Registered'

        app.logger.info('[%s] : [INFO] Yarn History Status -> %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), yarnStatus)

        # appname tag is set the same for spark and yarn
        qActiveApp = dbApp.query.filter_by(jobID='ACTIVE').first()
        if qActiveApp is None:
            app.logger.warning('[%s] : [WARN] No active applications registered tag set to default',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            appName = 'default'
        else:
            appName = qActiveApp.jobID
            app.logger.info('[%s] : [INFO] Tag for application %s set',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), appName)

        infoSCore = {"sslcert": certLoc, "sslkey": keyLoc, "udpPort": qSCore.udpPort,
                     "ESCluster": qSCore.outESclusterName, "EShostIP": qESCore.hostIP,
                     "EShostPort": qESCore.nodePort, "StormRestIP": StormRestIP,
                     "StormRestPort": qSCore.LSCoreStormPort, "StormTopologyID": qSCore.LSCoreStormTopology,
                     'storm_interval': stormInterval, 'roles': uniqueRolesList, 'myIndex': qSCore.diceIndex,
                     'nSpout': spouts, 'nBolt': bolts, 'yarnHEnd': yarnHEnd, 'yarnHPort': yarnHPort,
                     'yarnHPoll': yarnHPoll, 'appName': appName}
        sConf = template.render(infoSCore)
        qSCore.conf = sConf
        # print >>sys.stderr, esConf
        db.session.commit()

        lsCoreConf = open(lsfCore, "w+")
        lsCoreConf.write(sConf)
        lsCoreConf.close()

        os.environ['LS_HEAP_SIZE'] = os.getenv('LS_HEAP_SIZE',
                                               qSCore.LSCoreHeap)  # TODO: if heap size set in env then use it if not use db one
        app.logger.info('[%s] : [INFO] LS Heap size set to %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        str(os.environ['LS_HEAP_SIZE']))

        lsLogfile = os.path.join(logDir, 'logstash.log')
        lsPIDFileLoc = os.path.join(pidDir, 'logstash.pid')

        if os.path.isfile(lsPIDFileLoc):
            lsPidf = check_proc(lsPIDFileLoc)
        else:
            lsPidf = 0

        if lsPidf != qSCore.LSCorePID:
            app.logger.warning("[%s] : [WARN] Conflicting PID values found, detached pid -> %s, attached -> %s",
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(lsPidf),
                               str(qSCore.LSCorePID))

        if checkPID(qSCore.LSCorePID) is True:
            try:
                subprocess.check_call(["service", "dmon-ls", "restart", qSCore.LSCoreHeap, qSCore.LSCoreWorkers])
            except Exception as inst:
                app.logger.error("[%s] : [ERROR] Cannot restart LS Core service with %s and %s",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                 inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Cannot restart LS Core'})
                response.status_code = 500
                return response
            lsPID = check_proc(lsPIDFileLoc)
            if not lsPID:
                app.logger.error("[%s] : [ERROR] Can't read pidfile for ls core",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                response = jsonify({'Status': 'Error', 'Message': 'Cannot read lscore pid file'})
                response.status_code = 500
                return response
            qSCore.ESCorePID = lsPID
            qSCore.ESCoreStatus = 'Running'
            response = jsonify({'Status': 'LS Core Restarted', 'PID': lsPID})
            response.status_code = 201
            return response
        elif checkPID(int(lsPidf)) is True:
            try:
                subprocess.check_call(["service", "dmon-ls", "restart", qSCore.LSCoreHeap, qSCore.LSCoreWorkers])
            except Exception as inst:
                app.logger.error("[%s] : [ERROR] Cannot restart detached LS Core service with %s and %s",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                 inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Cannot restart detached LS Core'})
                response.status_code = 500
                return response
            lsPID = check_proc(lsPIDFileLoc)
            if not lsPID:
                app.logger.error("[%s] : [ERROR] Can't read pidfile for ls core",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                response = jsonify({'Status': 'Error', 'Message': 'Cannot read ls core pid file'})
                response.status_code = 500
                return response
            qSCore.LSCorePID = lsPID
            qSCore.LSCoreStatus = 'Running'
            response = jsonify({'Status': 'LS Core  Restarted and attached', 'PID': lsPID})
            response.status_code = 201
            return response
        else:
            try:
                subprocess.check_call(["service", "dmon-ls", "start", qSCore.LSCoreHeap, qSCore.LSCoreWorkers])
            except Exception as inst:
                app.logger.error("[%s] : [ERROR] Cannot start LS Core service with %s and %s",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                 inst.args)
                response = jsonify({'Status': 'Error', 'Message': 'Cannot start LS Core'})
                response.status_code = 500
                return response
            lsPID = check_proc(lsPIDFileLoc)
            if not lsPID:
                app.logger.error("[%s] : [ERROR] Can't read pidfile for ls core",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                response = jsonify({'Status': 'Error', 'Message': 'Cannot read lscore pid file'})
                response.status_code = 500
                return response
            qSCore.LSCorePID = lsPID
            qSCore.LSCoreStatus = 'Running'
            response = jsonify({'Status': 'LS Core Started', 'PID': lsPID, 'Storm': stormStatus, 'YarnHistory': yarnStatus})
            response.status_code = 201
            app.logger.info("[%s] : [INFO] LS Core started with PID %s, Storm %s and YanrHistory %s",
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), lsPID, stormStatus, yarnStatus)
            return response


@dmon.route('/v1/overlord/core/ls/<hostFQDN>/status')
@api.doc(params={'hostFQDN': 'Host FQDN'})
class LSCoreControllerStatus(Resource):
    def get(self, hostFQDN):
        qLSCoreStatus = dbSCore.query.filter_by(hostFQDN=hostFQDN).first()
        if qLSCoreStatus is None:
            response = jsonify({'Status': 'Unknown host ' + hostFQDN})
            response.status_code = 404
            return response
        pid = qLSCoreStatus.LSCorePID
        if not checkPID(pid):
            if pid != 0:
                qLSCoreStatus.LSCoreStatus = 'Stopped'
            else:
                qLSCoreStatus.LSCoreStatus = 'unknown'
        response = jsonify({'Status': qLSCoreStatus.LSCoreStatus,
                            'PID': qLSCoreStatus.LSCorePID})
        response.status_code = 200
        return response


@dmon.route('/v1/overlord/core/ls/<hostFQDN>/start')
@api.doc(params={'hostFQDN': 'Host FQDN'})
class LSCoreControllerStart(Resource):
    def post(self, hostFQDN):
        lsfCore = os.path.join(cfgDir, 'logstash.conf')
        lsLogfile = os.path.join(logDir, 'logstash.log')
        qLSCoreStart = dbSCore.query.filter_by(hostFQDN=hostFQDN).first()
        if qLSCoreStart is None:
            response = jsonify({'Status': 'Unknown host ' + hostFQDN})
            response.status_code = 404
            return response

        if checkPID(qLSCoreStart.LSCorePID) is True:
            proc = psutil.Process(qLSCoreStart.LSCorePID)
            if proc.status() == psutil.STATUS_ZOMBIE:
                # print >> sys.stderr, 'Process ' + str(qLSCoreStart.LSCorePID) + ' is zombie!'
                app.logger.warning('[%s] : [WARN] Process %s is a zombie!',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                   str(qLSCoreStart.LSCorePID))
            else:
                response = jsonify({'Status': 'LS already Running',
                                    'PID': qLSCoreStart.LSCorePID})
                response.status_code = 200
                return response

        lsPid = 0
        try:
            lsPid = subprocess.Popen('/opt/logstash/bin/logstash agent  -f ' + lsfCore + ' -l ' + lsLogfile + ' -w 4',
                                     shell=True).pid
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Cannot start ls core instance with %s and %s!',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            response = jsonify({'Status': 'Error', 'Message': 'Cannot start LS Core service'})
            response.status_code = 500
            return response
            # print >> sys.stderr, 'Error while starting logstash'
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
        qLSCoreStart.LSCorePID = lsPid
        qLSCoreStart.LSCoreStatus = 'Running'
        # LS core pid location
        pidLSLoc = os.path.join(pidDir, 'logstash.pid')
        try:
            lsPIDFile = open(pidLSLoc, 'w+')
            lsPIDFile.write(str(lsPid))
            lsPIDFile.close()
        except IOError:
            response = jsonify({'Error': 'File I/O!'})
            response.status_code = 500
            return response
        response = jsonify({'Status': 'Logstash Core  PID ' + str(lsPid)})
        response.status_code = 201
        return response


@dmon.route('/v1/overlord/core/ls/<hostFQDN>/stop')
@api.doc(params={'hostFQDN': 'Host FQDN'})
class LSCoreControllerStop(Resource):
    def post(self, hostFQDN):
        qLSCoreStop = dbSCore.query.filter_by(hostFQDN=hostFQDN).first()
        if qLSCoreStop is None:
            response = jsonify({'Status': 'Unknown host ' + hostFQDN})
            response.status_code = 404
            return response
        if checkPID(qLSCoreStop.LSCorePID) is True:
            parent = psutil.Process(qLSCoreStop.LSCorePID)
            for c in parent.children(recursive=True):
                c.kill()
            parent.kill()
            os.kill(qLSCoreStop.LSCorePID, signal.SIGKILL)
            qLSCoreStop.LSCoreStatus = 'Stopped'
            response = jsonify({'Status': 'Stopped',
                                'Message': 'Stopped LS instance at ' + str(qLSCoreStop.LSCorePID)})
            response.status_code = 200
            return response
        else:
            qLSCoreStop.LSCoreStatus = 'unknown'
            response = jsonify({'Status': 'No LS Instance Found',
                                'Message': 'No LS instance with PID ' + str(qLSCoreStop.LSCorePID)})
            response.status_code = 404
            return response


@dmon.route('/v1/overlord/core/ls/credentials')
class LSCredControl(Resource):
    def get(self):
        credList = []
        credAll = db.session.query(dbSCore.hostFQDN, dbSCore.hostIP, dbSCore.sslCert, dbSCore.sslKey).all()
        if credAll is None:
            response = jsonify({'Status': 'No credentials set!'})
            response.status_code = 404
            return response
        for nl in credAll:
            credDict = {}
            # print >> sys.stderr, nl[0]
            app.logger.info('[%s] : [INFO] Credentials host %s!',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nl[0])
            credDict['LS Host'] = nl[0]
            credDict['Certificate'] = nl[2]
            credDict['Key'] = nl[3]
            credList.append(credDict)
        response = jsonify({'Credentials': credList})
        response.status_code = 200
        return response

        # def post(self):
        # 	qLSCore = dbSCore.query.first()
        # 	if qLSCore is None:
        # 		response = jsonify({'Status':'No LS Core set!'})
        # 		response.status_code = 404
        # 		return response

        # 	templateLoader = jinja2.FileSystemLoader( searchpath="/" )
        # 	templateEnv = jinja2.Environment( loader=templateLoader )
        # 	oSSLTemp= os.path.join(tmpDir,'openssl.tmp')
        # 	oSSLLoc = os.path.join(cfgDir,'openssl.cnf')

        # 	template = templateEnv.get_template( oSSLTemp )
        # 	osslPop = {"LSHostIP":qLSCore.hostIP}
        # 	oSSLConf = template.render(osslPop)

        # 	osslFile = open(lsfCore,"wb")
        # 	osslFile.write(oSSLLoc)
        # 	osslFile.close()


@dmon.route('/v1/overlord/core/ls/cert/<certName>')
@api.doc(params={'certName': 'Name of the certificate'})
class LSCertQuery(Resource):
    def get(self, certName):
        qSCoreCert = dbSCore.query.filter_by(sslCert=certName).all()
        certList = []
        for i in qSCoreCert:
            certList.append(i.hostFQDN)

        if not certList:
            response = jsonify({'Status': certName + ' not found!'})
            response.status_code = 404
            return response
        else:
            response = jsonify({'Hosts': certList})
            response.status_code = 200
            return response


@dmon.route('/v1/overlord/core/ls/cert/<certName>/<hostFQDN>')
@api.doc(params={'certName': 'Name of the certificate',
                 'hostFQDN': 'Host FQDN'})
class LSCertControl(Resource):
    @api.expect(certModel)  # TODO FIX THIS
    def put(self, certName, hostFQDN):
        if request.headers['Content-Type'] == 'application/x-pem-file':
            pemData = request.data
        else:
            abort(400)
        qSCoreCert = dbSCore.query.filter_by(hostFQDN=hostFQDN).first()
        if qSCoreCert is None:
            response = jsonify({'Status': 'unknown host'})
            response.status_code = 404
            return response
        else:
            if certName == 'default':
                crtFile = os.path.join(credDir, 'logstash-forwarder.crt')
            else:
                crtFile = os.path.join(credDir, certName + '.crt')
            try:
                cert = open(crtFile, 'w+')
                cert.write(pemData)
                cert.close()
            except IOError:
                response = jsonify({'Error': 'File I/O!'})
                response.status_code = 500
                return response

        qSCoreCert.sslCert = certName
        response = jsonify({'Status': 'updated certificate!'})
        response.status_code = 201
        return response


@dmon.route('/v1/overlord/core/ls/key/<keyName>')
@api.doc(params={'keyName': 'Name of the private key.'})
class LSKeyQuery(Resource):
    def get(self, keyName):
        if keyName == 'default':
            response = jsonify({'Key': 'default'})
            response.status_code = 200
            return response
        qSCoreKey = dbSCore.query.filter_by(sslKey=keyName).first()
        if qSCoreKey is None:
            response = jsonify({'Status': keyName + ' not found!'})
            response.status_code = 404
            return response

        response = jsonify({'Host': qSCoreKey.hostFQDN, 'Key': qSCoreKey.sslKey})
        response.status_code = 200
        return response


@dmon.route('/v1/overlord/core/ls/key/<keyName>/<hostFQDN>')
@api.doc(params={'keyName': 'Name of the private key.', 'hostFQDN': 'Host FQDN'})
class LSKeyControl(Resource):
    def put(self, keyName, hostFQDN):
        if request.headers['Content-Type'] == 'application/x-pem-file':
            pemData = request.data
        else:
            abort(400)
        qSCoreKey = dbSCore.query.filter_by(hostFQDN=hostFQDN).first()
        if qSCoreKey is None:
            response = jsonify({'Status': 'unknown host'})
            response.status_code = 404
            return response
        else:
            if keyName == 'default':
                keyFile = os.path.join(credDir, 'logstash-forwarder.key')
            else:
                keyFile = os.path.join(credDir, keyName + '.key')
            try:
                key = open(keyFile, 'w+')
                key.write(pemData)
                key.close()
            except IOError:
                response = jsonify({'Error': 'File I/O!'})
                response.status_code = 500
                return response

        qSCoreKey.sslKey = keyName
        response = jsonify({'Status': 'updated key!'})
        response.status_code = 201
        return response


@dmon.route('/v1/overlord/aux')
class AuxInfo(Resource):
    def get(self):
        response = jsonify({'AuxComponents': ['collectd', 'logstash-forwarder', 'jmx']})
        response.status_code = 200
        return response


@dmon.route('/v1/overlord/aux/deploy')
class AuxDeploy(Resource):
    def get(self):
        qNodes = db.session.query(dbNodes.nodeFQDN, dbNodes.nodeIP, dbNodes.nMonitored,
                                  dbNodes.nCollectdState, dbNodes.nLogstashForwState, dbNodes.nLogstashInstance).all()
        mnList = []
        for nm in qNodes:
            mNode = {}
            mNode['NodeFQDN'] = nm[0]
            mNode['NodeIP'] = nm[1]
            mNode['Monitored'] = nm[2]
            mNode['Collectd'] = nm[3]
            mNode['LSF'] = nm[4]
            mNode['LSInstance'] = nm[5]
            mnList.append(mNode)
        # print >> sys.stderr, nm
        response = jsonify({'Aux Status': mnList})
        response.status_code = 200
        return response

    @api.doc(parser=dmonAuxAll)  # TODO Status handling (Running, Stopped, None )Needs Checking
    def post(self):  # TODO currently works only if the same username and password is used for all Nodes
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        lsfTemp = os.path.join(tmpDir, 'logstash-forwarder.tmp')  # tmpDir+"/collectd.tmp"
        collectdTemp = os.path.join(tmpDir, 'collectd.tmp')
        collectdConfLoc = os.path.join(cfgDir, 'collectd.conf')
        lsfConfLoc = os.path.join(cfgDir, 'logstash-forwarder.conf')
        qNodes = db.session.query(dbNodes.nodeFQDN, dbNodes.nMonitored,
                                  dbNodes.nCollectdState, dbNodes.nLogstashForwState, dbNodes.nUser, dbNodes.nPass,
                                  dbNodes.nodeIP, dbNodes.nLogstashInstance).all()
        result = []
        credentials = {}
        for n in qNodes:
            credentials['User'] = n[4]  # TODO need a more elegant solution, currently it is rewriten every iteration
            credentials['Pass'] = n[5]
            # print >> sys.stderr, credentials
            app.logger.info('[%s] : [INFO] Credentials used %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), credentials)
            rp = {}
            if n[1] == False:  # check if node is monitored
                rp['Node'] = n[0]
                rp['Collectd'] = n[2]
                rp['LSF'] = n[3]
                rp['IP'] = n[6]
                rp['LSInstance'] = n[7]
                # rp['User']=n[4]
                # rp['Pass']=n[5]
                result.append(rp)
        collectdList = []
        LSFList = []
        allNodes = []
        for res in result:
            if res['Collectd'] == 'None':
                # print >> sys.stderr, 'No collectd!'
                app.logger.info('[%s] : [INFO] No collectd',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                collectdList.append(res['IP'])
            if res['LSF'] == 'None':
                LSFList.append(res['IP'])
                app.logger.info('[%s] : [INFO] No LSF',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                # print >> sys.stderr, 'No LSF!'
            allNodes.append(res['IP'])

        args = dmonAuxAll.parse_args()

        if args == 'redeploy-all':  # TODO check if conf files exist if not catch error
            uploadFile(allNodes, credentials['User'], credentials['Pass'], collectdConfLoc, 'collectd.conf',
                       '/etc/collectd/collectd.conf')
            uploadFile(allNodes, credentials['User'], credentials['Pass'], lsfConfLoc, 'logstash-forwarder.conf',
                       '/etc/logstash-forwarder.conf')
            serviceCtrl(allNodes, credentials['User'], credentials['Pass'], 'collectd', 'restart')
            serviceCtrl(allNodes, credentials['User'], credentials['Pass'], 'logstash-forwarder', 'restart')
            response = jsonify({'Status': 'All aux components reloaded!'})
            response.status_code = 200
            return response

        if not collectdList and not LSFList:
            response = jsonify({'Status': 'All registred nodes are already monitored!'})
            response.status_code = 200
            return response

        app.logger.info('[%s] : [INFO] Collectd list -> %s, LSFList -> %s, credentials -> %s, Conf dir -> %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), collectdList, LSFList, credentials['User'], confDir)
        # print >> sys.stderr, collectdList
        # print >> sys.stderr, LSFList
        # print >> sys.stderr, credentials['User']
        # print >> sys.stderr, confDir

        qSCore = dbSCore.query.first()  # TODO Change for distributed deployment
        if qSCore is None:
            response = jsonify({'Status': 'DB empty',
                                'Message': 'There is no logstash instance registered!'})
            response.status_code = 400
            return response
        try:
            lsfTemplate = templateEnv.get_template(lsfTemp)
        # print >>sys.stderr, template
        except:
            app.logger.error('[%s] : [ERROR] Template file unavailable',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'Error', 'Message': 'Template file unavailable'})
            response.status_code = 500
            return response

        # {{ESCoreIP}}:{{LSLumberPort}}
        infolsfAux = {"ESCoreIP": qSCore.hostIP, "LSLumberPort": qSCore.inLumberPort}
        lsfConf = lsfTemplate.render(infolsfAux)

        lsfConfFile = open(lsfConfLoc, "wb")  # TODO trycatch
        lsfConfFile.write(lsfConf)
        lsfConfFile.close()

        # {{logstash_server_ip}}" "{{logstash_server_port}}
        try:
            collectdTemplate = templateEnv.get_template(collectdTemp)
        except:
            app.logger.error('[%s] : [ERROR] Template file unavailable',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            response = jsonify({'Status': 'Error', 'Message': 'Template file unavailable'})
            response.status_code = 500
            return response
            # return "Template file unavailable!"

        infocollectdAux = {"logstash_server_ip": qSCore.hostIP, "logstash_server_port": qSCore.udpPort}
        collectdConf = collectdTemplate.render(infocollectdAux)

        collectdConfFile = open(collectdConfLoc, "wb")
        collectdConfFile.write(collectdConf)
        collectdConfFile.close()

        try:
            installCollectd(collectdList, credentials['User'], credentials['Pass'], confDir=cfgDir)
        except Exception as inst:  # TODO if exceptions is detected check to see if collectd started if not return fail if yes return warning
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            app.logger.error('[%s] : [ERROR] Cannot install collectd with %s and  %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            response = jsonify({'Status': 'Error Installing collectd!'})
            response.status_code = 500
            return response
        # TODO Assign logsash server instance to each node
        try:
            installLogstashForwarder(LSFList, userName=credentials['User'], uPassword=credentials['Pass'],
                                     confDir=cfgDir)
        except Exception as inst:
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            app.logger.error('[%s] : [ERROR] Cannot install lsf with %s and  %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            response = jsonify({'Status': 'Error Installing LSF!'})
            response.status_code = 500
            return response

        for c in collectdList:
            updateNodesCollectd = dbNodes.query.filter_by(nodeIP=c).first()
            if updateNodesCollectd is None:
                response = jsonify({'Error': 'DB error, IP ' + c + ' not found!'})
                response.status_code = 500
                return response
            updateNodesCollectd.nCollectdState = 'Running'

        for l in LSFList:
            updateNodesLSF = dbNodes.query.filter_by(nodeIP=l).first()
            if updateNodesLSF is None:
                response = jsonify({'Error': 'DB error, IP ' + l + ' not found!'})
                response.status_code = 500
                return response
            updateNodesLSF.nLogstashForwState = 'Running'

        updateAll = dbNodes.query.filter_by(nMonitored=0).all()
        for ua in updateAll:
            ua.nMonitored = 1

        response = jsonify({'Status': 'Aux Componnets deployed!'})
        response.status_code = 201
        return response


@dmon.route('/v2/overlord/aux/agent')  # TODO: create better variant
class AuxAgentDeploy(Resource):
    def get(self):
        qNodes = db.session.query(dbNodes.nodeFQDN, dbNodes.nStatus).all()
        an = []
        for n in qNodes:
            nAgent = {}
            nAgent['NodeFQDN'] = n[0]
            nAgent['Agent'] = n[1]
            an.append(nAgent)

        response = jsonify({'Agents': an})
        response.status_code = 200
        app.logger.info('[%s] : [INFO] Agents status: %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(an))
        return response

    def post(self):  # todo verify
        qN = db.session.query(dbNodes.nodeIP, dbNodes.nStatus, dbNodes.nUser, dbNodes.nPass).all()
        if not qN:
            response = jsonify({'Status': 'No nodes registered'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No nodes registered',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        noAgent = []
        user = ' '
        password = ' '
        for n in qN:
            if not n[1]:
                noAgent.append(n[0])
                user = n[2]
                password = n[3]

        if not noAgent:
            response = jsonify({'Status': 'All nodes have unpacked agents'})
            response.status_code = 200
            app.logger.info('[%s] : [INFO] All nodes have unpacked agents',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        try:
            deployAgent(noAgent, user, password)
        except Exception as inst:
            response = jsonify({'Status': 'Agent Error',
                                'Message': 'Error while deploying agent!'})
            app.logger.error('[%s] : [ERROR] Failed to deploy agent %s with %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            response.status_code = 500
            return response

        for a in noAgent:
            updateAll = dbNodes.query.filter_by(nodeIP=a).first()
            updateAll.nStatus = 1

        response = jsonify({'Status': 'Done', 'Message': 'Agents Installed!'})
        response.status_code = 201
        app.logger.info('[%s] : [INFO] Agents installed',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        return response


@dmon.route('/v2/overlord/agent/start')
class AuxAgentStart(Resource):
    def post(self):
        qNodeStatus = dbNodes.query.filter_by(nStatus=1).all()
        app.logger.info('[%s] : [INFO] Node Status %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(qNodeStatus))
        if not qNodeStatus:
            response = jsonify({'Status': 'Agent Exception',
                                'Message': 'No agents are registered'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No agents registered',
					datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        dnode = []
        nnodes = []
        for ns in qNodeStatus:
            node = []
            if ns.nMonitored is True:
                break
            else:
                node.append(ns.nodeIP)
            app.logger.info('[%s] : [INFO] Unmonitored nodes %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(node))
            AgentNodes = {}
            try:
                startAgent(node, ns.nUser, ns.nPass)
                ns.nMonitored = 1
                app.logger.info('[%s] : [INFO] Started agent at %s',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(node))
                AgentNodes['Node'] = ns.nodeFQDN
                AgentNodes['IP'] = ns.nodeIP
                dnode.append(AgentNodes)
            except Exception as inst:
                app.logger.error('[%s] : [INFO] Error starting agent on %s with exception %s and %s',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                 str(ns.nodeFQDN), type(inst), inst.args)
                AgentNodes['Node'] = ns.nodeFQDN
                AgentNodes['IP'] = ns.nodeIP
                nnodes.append(AgentNodes)
                break
        response = jsonify({'Status': 'Agents Started',
                            'Sucessfull': dnode,
                            'Failed': nnodes})
        response.status_code = 200
        app.logger.info('[%s] : [INFO] Agents started on nodes %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(dnode))
        return response


@dmon.route('/v2/overlord/agent/stop') #todo verify
class AuxAgentStop(Resource):
    def post(self):
        qNodeStatus = dbNodes.query.filter_by(nMonitored=1).all()
        if not qNodeStatus:
            response = jsonify({'Status': 'Agent Exception',
                                'Message': 'No agents are registered'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No agents registered',
					datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        dnode = []
        for ns in qNodeStatus:
            node = []
            node.append(ns.nodeIP)
            app.logger.info('[%s] : [INFO] Monitored nodes %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(node))

            try:
                stopAgent(node, ns.nUser, ns.nPass)
            except Exception as inst:
                # print >> sys.stderr, type(inst)
                # print >> sys.stderr, inst.args
                response = jsonify({'Status': 'Error Stopping agent on  ' + ns.nodeFQDN + '!'})
                response.status_code = 500
                app.logger.error('[%s] : [INFO] Error stopping agent on %s with exception %s and %s',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                 str(ns.nodeFQDN), type(inst), inst.args)
                return response
            app.logger.info('[%s] : [INFO] Stopped agent at %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(node))
            AgentNodes = {}
            AgentNodes['Node'] = ns.nodeFQDN
            AgentNodes['IP'] = ns.nodeIP
            dnode.append(AgentNodes)
            ns.nMonitored = 0
        response = jsonify({'Status': 'Agents Stopped',
                            'Nodes': dnode})
        response.status_code = 200
        app.logger.info('[%s] : [INFO] Agents stopped on nodes %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(dnode))
        return response


@dmon.route('/v2/overlord/aux/status')
class AuxDeployStatus(Resource):
    def get(self):
        qNodes = db.session.query(dbNodes.nodeFQDN, dbNodes.nodeIP, dbNodes.nMonitored, dbNodes.nStatus,
                                  dbNodes.nCollectdState, dbNodes.nLogstashForwState).all()
        mnList = []
        for nm in qNodes:
            mNode = {}
            mNode['NodeFQDN'] = nm[0]
            mNode['NodeIP'] = nm[1]
            mNode['Monitored'] = nm[2]
            mNode['Status'] = nm[3]
            mNode['Collectd'] = nm[4]
            mNode['LSF'] = nm[5]
            mnList.append(mNode)
        # print >> sys.stderr, nm
        app.logger.info('[%s] : [INFO] Nodes -> %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(mnList))
        response = jsonify({'Aux Status': mnList})
        response.status_code = 200
        return response


@dmon.route('/v2/overlord/aux/deploy')  # TODO: gets current status of aux components and deploy them based on roles
class AuxDeployThread(Resource):
    # def put(self):  # TODO: used to enact new configurations
    #     return "Reload new Configuration"

    def post(self):
        qNodes = db.session.query(dbNodes.nodeIP, dbNodes.nRoles).all()
        if not qNodes:
            response = jsonify({'Status': 'No nodes registered'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No nodes registered',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        nrList = []
        for nr in qNodes:
            nrNode = {}
            nrNode[nr[0]] = nr[1].split(',')
            nrList.append(nrNode)

        app.logger.info('[%s] : [INFO] Node list -> %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nrList))
        resFin = {}
        for e in nrList:
            for k, v in e.iteritems():
                nodeList = []
                nodeList.append(k)
                agentr = AgentResourceConstructor(nodeList, '5222')
                resourceList = agentr.deploy()
                r = {'roles': v}
                resFin[resourceList[-1]] = r

        app.logger.info('[%s] : [INFO] Resource List %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), resFin)
        dmon = GreenletRequests(resFin)
        nodeRes = dmon.parallelPost(None)
        app.logger.info('[%s] : [INFO] Node resources %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nodeRes))
        # print >> sys.stderr, str(nodeRes)
        failedNodes = []
        NodeDict = {}
        for n in nodeRes:
            nodeIP = urlparse(n['Node'])
            qNode = dbNodes.query.filter_by(nodeIP=nodeIP.hostname).first()
            qNode.nMonitored = 1  # TODO: Recheck nStatus and nMonitored roles when are they true and when are they false
            if n['StatusCode'] != 201:
                failedNodes.append({'NodeIP': str(nodeIP.hostname),
                                    'Code': n['StatusCode']})
            # print >> sys.stderr, str(n['Data']['Components'])
            # print >> sys.stderr, str(n)
            app.logger.debug('[%s] : [DEBUG] Node response -> %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(n))
            try:
                NodeDict[nodeIP.hostname] = n['Data']['Components']
            except Exception as inst:
                # print >> sys.stderr, type(inst)
                # print >> sys.stderr, inst.args
                app.logger.error('[%s] : [ERROR] Keys missing, exception %s with %s',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                NodeDict[nodeIP.hostname] = "Failed"
        response = jsonify({'Status': 'Installed Aux ',
                            'Message': NodeDict,
                            'Failed': failedNodes})
        response.status_code = 200
        dmon.reset()
        return response


@dmon.route('/v2/overlord/aux/deploy/check')
class AuxDeployCheckThread(Resource):
    def get(self):
        agentPort = '5222'
        nodesAll = db.session.query(dbNodes.nodeFQDN, dbNodes.nodeIP).all()
        if nodesAll is None:
            response = jsonify({'Status': 'No monitored nodes found'})
            response.status_code = 404
            return response
        nodeList = []
        for n in nodesAll:
            nodeList.append(n[1])

        agentr = AgentResourceConstructor(nodeList, agentPort)
        resourceList = agentr.check()

        dmon = GreenletRequests(resourceList)
        nodeRes = dmon.parallelGet()

        failedNodes = []
        for i in nodeRes:
            nodeIP = urlparse(i['Node'])
            qNode = dbNodes.query.filter_by(nodeIP=nodeIP.hostname).first()

            if i['Data'] != 'n/a':
                qNode.nMonitored = 1
                qNode.nStatus = 1
                if i['Data']['LSF'] == 1:
                    qNode.nLogstashForwState = "Running"
                elif i['Data']['LSF'] == 0:
                    qNode.nLogstashForwState = "Stopped"
                else:
                    qNode.nLogstashForwState = "None"

                if i['Data']['Collectd'] == 1:
                    qNode.nCollectdState = "Running"
                elif i['Data']['Collectd'] == 0:
                    qNode.nCollectdState = "Stopped"
                else:
                    qNode.nCollectdState = "None"
            else:
                qNode.nLogstashForwState = "None"
                qNode.nCollectdState = "None"

            if i['StatusCode'] != 200:
                failedNodes.append({'NodeIP': str(nodeIP.hostname),
                                    'Code': i['StatusCode']})
                qNode.nMonitored = 0

        response = jsonify({'Status': 'Update',
                            'Message': 'Nodes updated!',
                            'Failed': failedNodes})
        response.status_code = 200

        dmon.reset()
        return response


@dmon.route('/v1/overlord/aux/deploy/<auxComp>/<nodeFQDN>')  # TODO check parameter redeploy functionality
@api.doc(params={'auxComp': 'Aux Component',
                 'nodeFQDN': 'Node FQDN'})  # TODO document nMonitored set to true when first started monitoring
class AuxDeploySelective(Resource):
    @api.doc(parser=dmonAux)
    def post(self, auxComp, nodeFQDN):
        auxList = ['collectd', 'lsf']
        # status = {}
        if auxComp not in auxList:
            response = jsonify({'Status': 'No such such aux component ' + auxComp})
            response.status_code = 400
            return response
        qAux = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
        if qAux is None:
            response = jsonify({'Status': 'Unknown node ' + nodeFQDN})
            response.status_code = 404
            return response

        args = dmonAux.parse_args()

        node = []
        node.append(qAux.nodeIP)
        if auxComp == 'collectd':
            if args == 'redeploy':
                if qAux.nCollectdState != 'Running':
                    response = jsonify({'Status:No collectd instance to restart!'})
                    response.status_code = 404
                    return response
                try:
                    serviceCtrl(node, qAux.nUser, qAux.nPass, 'collectd', 'restart')
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Cannot start collectd with %s and  %s',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                     inst.args)
                    # print >> sys.stderr, type(inst)
                    # print >> sys.stderr, inst.args
                    response = jsonify({'Status': 'Error restarting Collectd on ' + nodeFQDN + '!'})
                    response.status_code = 500
                    return response
                response = jsonify({'Status': 'Collectd restarted on ' + nodeFQDN})
                response.status_code = 200
                return response
            if qAux.nCollectdState == 'None':
                try:
                    installCollectd(node, qAux.nUser, qAux.nPass, confDir=cfgDir)
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Cannot install collectd with %s and  %s',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                     inst.args)
                    # print >> sys.stderr, type(inst)
                    # print >> sys.stderr, inst.args
                    response = jsonify({'Status': 'Error Installing Collectd on ' + qAux.nodeFQDN + '!'})
                    response.status_code = 500
                    return response
                # status[auxComp] = 'Running'
                qAux.nCollectdState = 'Running'
                response = jsonify({'Status': 'Collectd started on ' + nodeFQDN + '.'})
                response.status_code = 201
                return response
            else:
                response = jsonify({'Status': 'Node ' + nodeFQDN + 'collectd already started!'})
                response.status_code = 200
                return response
        elif auxComp == 'lsf':
            if args == 'redeploy':
                if qAux.nLogstashForwState != 'Running':
                    response = jsonify({'Status:No LSF instance to restart!'})
                    response.status_code = 404
                    return response
                try:
                    serviceCtrl(node, qAux.nUser, qAux.nPass, 'logstash-forwarder', 'restart')
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Cannot start lsf with %s and  %s',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                     inst.args)
                    # print >> sys.stderr, type(inst)
                    # print >> sys.stderr, inst.args
                    response = jsonify({'Status': 'Error restarting LSF on ' + nodeFQDN + '!'})
                    response.status_code = 500
                    return response
                response = jsonify({'Status': 'LSF restarted on ' + nodeFQDN})
                response.status_code = 200
                return response
            if qAux.nLogstashForwState == 'None':
                try:
                    installLogstashForwarder(node, qAux.nUser, qAux.nPass, confDir=cfgDir)
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Cannot install lsf with %s and  %s',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                     inst.args)
                    # print >> sys.stderr, type(inst)
                    # print >> sys.stderr, inst.args
                    response = jsonify({'Status': 'Error Installing LSF on ' + qAux.nodeFQDN + '!'})
                    response.status_code = 500
                    return response
                # status[auxComp] = 'Running'
                qAux.nLogstashForwState = 'Running'
                response = jsonify({'Status': 'LSF started on ' + nodeFQDN + '.'})
                response.status_code = 201
                return response
            else:
                response = jsonify({'Status': 'Node ' + nodeFQDN + ' LSF already started!'})
                response.status_code = 200
                return response


@dmon.route('/v2/overlord/aux/<auxComp>/<nodeFQDN>/configure')  # TODO: deploy specific configuration on the specified node
@api.doc(params={'auxComp': 'Aux Component', 'nodeFQDN': 'Node FQDN'})
class AuxDeploySelectiveThread(Resource):
    def post(self, auxComp, nodeFQDN):
        auxList = ['collectd', 'lsf', 'jmx']
        if auxComp not in auxList:
            response = jsonify({'Status': 'No such such aux component ' + auxComp})
            response.status_code = 400
            app.logger.warning('[%s] : [WARN] Component %s not in supported list %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), auxComp, str(auxList))
            return response
        qAux = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
        if qAux is None:
            response = jsonify({'Status': 'Unknown node ' + nodeFQDN})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] Node %s not found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN)
            return response
        if auxComp == 'collectd':
            return 'collectd'
        elif auxComp == 'lsf':
            return 'lsf'
        elif auxComp == 'jmx':
            return 'jmx'
        else:
            return 'error'


@dmon.route('/v1/overlord/aux/<auxComp>/config')
@api.doc(params={'auxComp': 'Aux Component'})
class AuxConfigSelective(Resource):
    def get(self, auxComp):
        allowed = ['collectd', 'lsf']
        if auxComp not in allowed:
            response = jsonify({'Status': 'unrecognized aux component ' + auxComp})
            response.status_code = 404
            return response

        if not os.path.isdir(cfgDir):
            response = jsonify({'Error': 'Config dir not found !'})
            response.status_code = 404
            return response

        if auxComp == 'collectd':
            if not os.path.isfile(os.path.join(cfgDir, 'collectd.conf')):
                response = jsonify({'Error': 'Config file not found !'})
                response.status_code = 404
                return response
            try:
                Cfgfile = open(os.path.join(cfgDir, 'collectd.conf'), 'r')
            except EnvironmentError:
                response = jsonify({'EnvError': 'file not found'})
                response.status_code = 500
                return response

        if auxComp == 'lsf':
            if not os.path.isfile(os.path.join(cfgDir, 'logstash-forwarder.conf')):
                response = jsonify({'Error': 'Config file not found !'})
                response.status_code = 404
                return response
            try:
                Cfgfile = open(os.path.join(cfgDir, 'logstash-forwarder.conf'), 'r')
            except EnvironmentError:
                response = jsonify({'EnvError': 'file not found'})
                response.status_code = 500
                return response
        return send_file(Cfgfile, mimetype='text/plain', as_attachment=True)

    def put(self, auxComp): #todo remove or leave
        return "Sets configuration of aux components use parameters (args) -unsafe"


@dmon.route('/v1/overlord/aux/<auxComp>/start')
@api.doc(params={'auxComp': 'Aux Component'})
class AuxStartAll(Resource):
    def post(self, auxComp):  # TODO create function that can be reused for both start and stop of all components
        auxList = ['collectd', 'lsf']
        if auxComp not in auxList:
            response = jsonify({'Status': 'No such such aux component ' + auxComp})
            response.status_code = 400
            return response

        if auxComp == "collectd":
            qNCollectd = dbNodes.query.filter_by(nCollectdState='Stopped').all()

            if not qNCollectd:
                response = jsonify({'Status': 'No nodes in state Stopped!'})
                response.status_code = 404
                return response

            nodeCollectdStopped = []
            for i in qNCollectd:
                node = []
                node.append(i.nodeIP)
                try:
                    serviceCtrl(node, i.nUser, i.nPass, 'collectd', 'start')
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Cannot start collectd with %s and  %s',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                     inst.args)
                    # print >> sys.stderr, type(inst)
                    # print >> sys.stderr, inst.args
                # response = jsonify({'Status':'Error Starting collectd on '+ i.nodeFQDN +'!'})
                # response.status_code = 500 # todo check if return is required for collectd
                # return response

                CollectdNodes = {}
                CollectdNodes['Node'] = i.nodeFQDN
                CollectdNodes['IP'] = i.nodeIP
                nodeCollectdStopped.append(CollectdNodes)
                i.nCollectdState = 'Running'
            response = jsonify({'Status': 'Collectd started', 'Nodes': nodeCollectdStopped})
            response.status_code = 200
            return response

        if auxComp == "lsf":
            qNLsf = dbNodes.query.filter_by(nLogstashForwState='Stopped').all()
            if not qNLsf:
                response = jsonify({'Status': 'No nodes in state Stopped!'})
                response.status_code = 404
                return response

            nodeLsfStopped = []
            for i in qNLsf:
                node = []
                node.append(i.nodeIP)
                try:
                    serviceCtrl(node, i.nUser, i.nPass, 'logstash-forwarder', 'start')
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Cannot start lsf with %s and  %s',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                     inst.args)
                    # print >> sys.stderr, type(inst)
                    # print >> sys.stderr, inst.args
                    # response = jsonify({'Status': 'Error Starting LSF on ' + i.nodeFQDN + '!'})
                    # response.status_code = 500 # todo check if return is required for collectd
                    # return response

                LsfNodes = {}
                LsfNodes['Node'] = i.nodeFQDN
                LsfNodes['IP'] = i.nodeIP
                nodeLsfStopped.append(LsfNodes)
                i.nLogstashForwState = 'Running'
            response = jsonify({'Status': 'LSF started', 'Nodes': nodeLsfStopped})
            response.status_code = 200
            return response


@dmon.route('/v1/overlord/aux/<auxComp>/stop')  # auxCtrl(auxComp,'stop') #TODO revise from pysshCore and make it work!
@api.doc(params={'auxComp': 'Aux Component'})
class AuxStopAll(Resource):
    def post(self, auxComp):
        auxList = ['collectd', 'lsf']
        if auxComp not in auxList:
            response = jsonify({'Status': 'No such aux component ' + auxComp})
            response.status_code = 400
            return response

        if auxComp == "collectd":
            qNCollectd = dbNodes.query.filter_by(nCollectdState='Running').all()

            if not qNCollectd:
                response = jsonify({'Status': 'No nodes in Running state!'})
                response.status_code = 404
                return response

            nodeCollectdRunning = []
            for i in qNCollectd:
                node = []
                node.append(i.nodeIP)
                try:
                    serviceCtrl(node, i.nUser, i.nPass, 'collectd', 'stop')
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Cannot stop collectd with %s and  %s',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                     inst.args)
                    # print >> sys.stderr, type(inst)
                    # print >> sys.stderr, inst.args
                    response = jsonify({'Status': 'Error Stopping collectd on ' + i.nodeFQDN + '!'})
                    response.status_code = 500
                    return response

                CollectdNodes = {}
                CollectdNodes['Node'] = i.nodeFQDN
                CollectdNodes['IP'] = i.nodeIP
                nodeCollectdRunning.append(CollectdNodes)
                i.nCollectdState = 'Stopped'
            response = jsonify({'Status': 'Collectd stopped', 'Nodes': nodeCollectdRunning})
            response.status_code = 200
            return response

        if auxComp == "lsf":
            qNLsf = dbNodes.query.filter_by(nLogstashForwState='Running').all()
            if not qNLsf:
                response = jsonify({'Status': 'No nodes in state Running!'})
                response.status_code = 404
                return response

            nodeLsfRunning = []
            for i in qNLsf:
                node = []
                node.append(i.nodeIP)
                try:
                    serviceCtrl(node, i.nUser, i.nPass, 'logstash-forwarder', 'stop')
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Cannot stop lsf with %s and  %s',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                     inst.args)
                    # print >> sys.stderr, type(inst)
                    # print >> sys.stderr, inst.args
                    response = jsonify({'Status': 'Error Stopping LSF on ' + i.nodeFQDN + '!'})
                    response.status_code = 500
                    return response

                LsfNodes = {}
                LsfNodes['Node'] = i.nodeFQDN
                LsfNodes['IP'] = i.nodeIP
                nodeLsfRunning.append(LsfNodes)
                i.nLogstashForwState = 'Stopped'
            response = jsonify({'Status': 'LSF stopped', 'Nodes': nodeLsfRunning})
            response.status_code = 200
            return response


@dmon.route('/v1/overlord/aux/<auxComp>/<nodeFQDN>/start')
@api.doc(params={'auxComp': 'Aux Component', 'nodeFQDN': 'Node FQDN'})
class AuxStartSelective(Resource):
    def post(self, auxComp, nodeFQDN):
        auxList = ['collectd', 'lsf']
        if auxComp not in auxList:
            response = jsonify({'Status': 'No such such aux component ' + auxComp})
            response.status_code = 400
            return response

        qAux = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
        if qAux is None:
            response = jsonify({'Status': 'Unknown node ' + nodeFQDN})
            response.status_code = 404
            return response

        node = []
        node.append(qAux.nodeIP)
        if auxComp == 'collectd':
            if qAux.nCollectdState != 'None':
                try:
                    serviceCtrl(node, qAux.nUser, qAux.nPass, 'collectd', 'restart')
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Cannot restart collectd with %s and  %s',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                     inst.args)
                    # print >> sys.stderr, type(inst)
                    # print >> sys.stderr, inst.args
                    response = jsonify({'Status': 'Error restarting collectd on ' + nodeFQDN + '!'})
                    response.status_code = 500
                    return response
                response = jsonify({'Status': 'Collectd restarted on ' + nodeFQDN})
                response.status_code = 200
                return response
            else:
                response = jsonify({'Status': 'Need to deploy collectd first!'})
                response.status_code = 403
                return response

        if auxComp == 'lsf':
            if qAux.nLogstashForwState != 'None':
                try:
                    serviceCtrl(node, qAux.nUser, qAux.nPass, 'logstash-forwarder', 'restart')
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Cannot restart lsf with %s and  %s',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                     inst.args)
                    # print >> sys.stderr, type(inst)
                    # print >> sys.stderr, inst.args
                    response = jsonify({'Status': 'Error restarting LSF on ' + nodeFQDN + '!'})
                    response.status_code = 500
                    return response
                response = jsonify({'Status': 'LSF restarted on ' + nodeFQDN})
                response.status_code = 200
                return response
            else:
                response = jsonify({'Status': 'Need to deploy LSF first!'})
                response.status_code = 403
                return response


@dmon.route('/v1/overlord/aux/<auxComp>/<nodeFQDN>/stop')
@api.doc(params={'auxComp': 'Aux Component', 'nodeFQDN': 'Node FQDN'})
class AuxStopSelective(Resource):
    def post(self, auxComp, nodeFQDN):
        auxList = ['collectd', 'lsf']
        if auxComp not in auxList:
            response = jsonify({'Status': 'No such  aux component ' + auxComp})
            response.status_code = 400
            return response

        qAux = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
        if qAux is None:
            response = jsonify({'Status': 'Unknown node ' + nodeFQDN})
            response.status_code = 404
            return response

        node = []
        node.append(qAux.nodeIP)
        if auxComp == 'collectd':
            if qAux.nCollectdState == 'Running':
                try:
                    serviceCtrl(node, qAux.nUser, qAux.nPass, 'collectd', 'stop')
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Cannot stop collectd with %s and  %s',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                     inst.args)
                    # print >> sys.stderr, type(inst)
                    # print >> sys.stderr, inst.args
                    response = jsonify({'Status': 'Error stopping collectd on ' + nodeFQDN + '!'})
                    response.status_code = 500
                    return response
                qAux.nCollectdState = 'Stopped'
                response = jsonify({'Status': 'Collectd stopped on ' + nodeFQDN})
                response.status_code = 200
                return response
            else:
                response = jsonify({'Status': 'No running Collectd instance found!'})
                response.status_code = 403
                return response

        if auxComp == 'lsf':
            if qAux.nLogstashForwState == 'Running':
                try:
                    serviceCtrl(node, qAux.nUser, qAux.nPass, 'logstash-forwarder', 'stop')
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Cannot stop lsf with %s and  %s',
                                     datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                     inst.args)
                    # print >> sys.stderr, type(inst)
                    # print >> sys.stderr, inst.args
                    response = jsonify({'Status': 'Error stopping LSF on ' + nodeFQDN + '!'})
                    response.status_code = 500
                    return response

                qAux.nCollectdState = 'Stopped'
                response = jsonify({'Status': 'LSF stopped on ' + nodeFQDN})
                response.status_code = 200
                return response
            else:
                response = jsonify({'Status': 'No running LSF instance found!'})
                response.status_code = 403
                return response


@dmon.route('/v2/overlord/aux/<auxComp>/<nodeFQDN>/start')
@api.doc(params={'auxComp': 'Aux Component', 'nodeFQDN': 'Node FQDN'})
class AuxStartSelectiveThreaded(Resource):
    def post(self, auxComp, nodeFQDN):
        auxList = ['collectd', 'lsf', 'jmx', 'all']
        if auxComp not in auxList:
            response = jsonify({'Status': 'No such such aux component ' + auxComp})
            response.status_code = 400
            return response

        qAux = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()

        if qAux is None:
            response = jsonify({'Status': 'Node ' + nodeFQDN + ' not found!'})
            response.status_code = 404
            return response

        node = []
        node.append(qAux.nodeIP)
        agentr = AgentResourceConstructor(node, '5222')

        if auxComp == 'all':
            resourceList = agentr.start()
        else:
            resourceList = agentr.startSelective(auxComp)

        try:
            r = requests.post(resourceList[0], timeout=DMON_TIMEOUT)
        # data = r.text
        except requests.exceptions.Timeout:
            response = jsonify({'Status': 'Timeout',
                                'Message': 'Request timedout!'})
            response.status_code = 408
            return response
        except requests.exceptions.ConnectionError:
            response = jsonify({'Status': 'Error',
                                'Message': 'Connection Error!'})
            response.status_code = 404
            return response

        if auxComp is 'collectd':
            qAux.nCollectdState = 'Running'
        elif auxComp is 'lsf':
            qAux.nLogstashForwState = 'Running'
        else:
            qAux.nCollectdState = 'Running'
            qAux.nLogstashForwState = 'Running'

        response = jsonify({'Status': 'Success',
                            'Message': 'Component ' + auxComp + ' started!'})
        response.status_code = 200
        return response


@dmon.route('/v2/overlord/aux/<auxComp>/<nodeFQDN>/stop')
@api.doc(params={'auxComp': 'Aux Component', 'nodeFQDN': 'Node FQDN'})
class AuxStopSelectiveThreaded(Resource):
    def post(self, auxComp, nodeFQDN):
        auxList = ['collectd', 'lsf', 'jmx', 'all']
        if auxComp not in auxList:
            response = jsonify({'Status': 'No such such aux component ' + auxComp})
            response.status_code = 400
            return response

        qAux = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()

        if qAux is None:
            response = jsonify({'Status': 'Node ' + nodeFQDN + ' not found!'})
            response.status_code = 404
            return response

        node = []
        node.append(qAux.nodeIP)
        agentr = AgentResourceConstructor(node, '5222')

        if auxComp == 'all':
            resourceList = agentr.stop()
        else:
            resourceList = agentr.stopSelective(auxComp)

        try:
            r = requests.post(resourceList[0], timeout=DMON_TIMEOUT)
        # data = r.text
        except requests.exceptions.Timeout:
            response = jsonify({'Status': 'Timeout',
                                'Message': 'Request timedout!'})
            response.status_code = 408
            return response
        except requests.exceptions.ConnectionError:
            response = jsonify({'Status': 'Error',
                                'Message': 'Connection Error!'})
            response.status_code = 404
            return response

        if auxComp is 'collectd':
            qAux.nCollectdState = 'Stopped'
        elif auxComp is 'lsf':
            qAux.nLogstashForwState = 'Stopped'
        else:
            qAux.nCollectdState = 'Stopped'
            qAux.nLogstashForwState = 'Stopped'

        response = jsonify({'Status': 'Success',
                            'Message': 'Component ' + auxComp + ' stopped!'})
        response.status_code = 200
        return response

    # return "same as v1"  # TODO: stop selected component


@dmon.route('/v2/overlord/aux/<auxComp>/start')
@api.doc(params={'auxComp': 'Aux Component'})
class AuxStartAllThreaded(Resource):
    def post(self, auxComp):
        auxList = ['collectd', 'lsf', 'jmx', 'all']
        if auxComp not in auxList:
            response = jsonify({'Status': 'No such such aux component ' + auxComp})
            response.status_code = 400
            return response
        qNodes = db.session.query(dbNodes.nodeIP).all()
        if not qNodes:
            response = jsonify({'Status': 'No nodes registered'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No nodes registrerd',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        nList = []
        for n in qNodes:
            nList.append(n[0])

        agentr = AgentResourceConstructor(nList, '5222')
        if auxComp == 'all':
            resourceList = agentr.start()
        else:
            resourceList = agentr.startSelective(auxComp)

        dmon = GreenletRequests(resourceList)
        nodeRes = dmon.parallelPost(None)

        # TODO: create parallel request response parse function
        failedNodes = []
        for n in nodeRes:
            nodeIP = urlparse(n['Node'])
            qNode = dbNodes.query.filter_by(nodeIP=nodeIP.hostname).first()
            # print n['StatusCode']
            if n['StatusCode'] != 200:
                failedNodes.append({'NodeIP': str(nodeIP.hostname),
                                    'Code': n['StatusCode']})
                qNode.nCollectdState = 'unknown'
                qNode.nLogstashForwState = 'unknown'
            else:
                qNode.nCollectdState = 'Running'
                qNode.nLogstashForwState = 'Running'

        response = jsonify({'Status': 'Running ' + auxComp,
                            'Message': 'Updated Status',
                            'Failed': failedNodes})

        response.status_code = 200

        dmon.reset()

        return response


@dmon.route('/v2/overlord/aux/<auxComp>/stop')
@api.doc(params={'auxComp': 'Aux Component'})
class AuxStopAllThreaded(Resource):
    def post(self, auxComp):
        auxList = ['collectd', 'lsf', 'jmx', 'all']
        if auxComp not in auxList:
            response = jsonify({'Status': 'No such such aux component supported' + auxComp})
            response.status_code = 400
            return response
        qNodes = db.session.query(dbNodes.nodeIP).all()
        if not qNodes:
            response = jsonify({'Status': 'No nodes registered'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No nodes registrerd',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        nList = []
        for n in qNodes:
            nList.append(n[0])

        agentr = AgentResourceConstructor(nList, '5222')
        if auxComp == 'all':
            resourceList = agentr.stop()
        else:
            resourceList = agentr.stopSelective(auxComp)

        dmon = GreenletRequests(resourceList)
        nodeRes = dmon.parallelPost(None)

        # TODO: create parallel request response parse function
        failedNodes = []
        for n in nodeRes:
            nodeIP = urlparse(n['Node'])
            qNode = dbNodes.query.filter_by(nodeIP=nodeIP.hostname).first()
            # print n['StatusCode']
            if n['StatusCode'] != 200:
                failedNodes.append({'NodeIP': str(nodeIP.hostname),
                                    'Code': n['StatusCode']})
                qNode.nCollectdState = 'unknown'
                qNode.nLogstashForwState = 'unknown'
            elif len(resourceList) == 1:
                if auxComp == 'collectd':
                    qNode.nCollectdState = 'Stopped'
                if auxComp == 'lsf':
                    qNode.nLogstashForwState = 'Stopped'
            else:
                qNode.nCollectdState = 'Stopped'
                qNode.nLogstashForwState = 'Stopped'

        response = jsonify({'Status': 'Stopped ' + auxComp,
                            'Message': 'Updated Status',
                            'Failed': failedNodes})

        response.status_code = 200

        dmon.reset()
        return response


@dmon.route('/v2/overlord/aux/<auxComp>/configure') #this is the correct one for configuring components
class AuxConfigureCompTreaded(Resource):
    def post(self, auxComp):
        auxList = ['collectd', 'lsf', 'jmx'] #TODO: add all, will need some concurency on dmon-agent part
        if auxComp not in auxList:
            response = jsonify({'Status': 'No such such aux component supported ' + auxComp})
            response.status_code = 400
            app.logger.warning('[%s] : [WARNING] Aux Components %s not supported',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), auxComp)
            return response
        qNodes = db.session.query(dbNodes.nodeIP, dbNodes.nMonitored, dbNodes.nRoles).all()
        nList = []
        nRoles = []
        for n in qNodes:
            if not n[1]:
                break
            nList.append(n[0])
            nRoles.append(n[2])
        if not nList:
            response = jsonify({'Status': 'No monitored nodes found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No monitored nodes found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), auxComp)
            return response

        uList = []
        for r in nRoles:
            uList.append(r.split(', '))
        uniqueRoles = set(x for l in uList for x in l)
        uniqueRolesList = list(uniqueRoles)
        # todo ad support on a per node bases for roles not global unique list
        app.logger.info('[%s] : [INFO] Unique roles %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(uniqueRolesList))
        agentr = AgentResourceConstructor(nList, '5222')
        qMetPer = dbMetPer.query.first()
        if auxComp == 'collectd':
            resFin = {}
            resourceList = agentr.collectd()
            for n in resourceList:
                payload = {}
                nIP = urlparse(n).hostname
                qNodeSpec = dbNodes.query.filter_by(nodeIP=nIP).first() #TODO: unify db foreign keys in tables
                qLSSpec = dbSCore.query.filter_by(hostIP=qNodeSpec.nLogstashInstance).first()
                if qLSSpec is None:
                    response = jsonify({'Status': 'No logstash instance found'})
                    response.status_code = 404
                    app.logger.warning('[%s] : [WARNING] No Logstash instance found with IP %s',
                                       datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(qNodeSpec.nLogstashInstance))
                    return response
                payload['Interval'] = qMetPer.sysMet
                payload['LogstashIP'] = qNodeSpec.nLogstashInstance
                payload['UDPPort'] = str(qLSSpec.udpPort)
                if 'cassandra' in uniqueRolesList:
                    payload['Cassandra'] = 1
                else:
                    payload['Cassandra'] = 0
                if 'mongodb' in uniqueRolesList:
                    qBDS = dbBDService.query.first()
                    if qBDS is None:
                        app.logger.warning('[%s] : [WARNING] MongoDB role found but no settings detected',
                                           datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                        pass
                    else:
                        payload['MongoDB'] = 1
                        payload['MongoHost'] = qBDS.mongoHost
                        payload['MongoDBPort'] = qBDS.mongoPort
                        payload['MongoDBUser'] = qBDS.mongoUser
                        payload['MongoDBPasswd'] = qBDS.mongoPswd
                        payload['MongoDBs'] = qBDS.mongoDBs
                        app.logger.info('[%s] : [INFO] MongoDB role found added settings to queue',
                                           datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                resFin[n] = payload

        if auxComp == 'lsf':
            resFin = {}
            resourceList = agentr.lsf()
            for n in resourceList:
                payload = {}
                nIP = urlparse(n).hostname
                qNodeSpec = dbNodes.query.filter_by(nodeIP=nIP).first() #TODO: same as for collectd remove duplicate code
                qLSSpec = dbSCore.query.filter_by(hostIP=qNodeSpec.nLogstashInstance).first()
                payload['LogstashIP'] = qNodeSpec.nLogstashInstance
                payload['LumberjackPort'] = qLSSpec.inLumberPort
                resFin[n] = payload

        if auxComp == 'jmx':
            response = jsonify({'Status': 'Deprecated', 'Message': 'Use GenericJMX'})
            response.status_code = 200
            return response


        # if auxComp == 'all':
        #     resourceCollectd = agentr.collectd()
        #     resourceLSF = agentr.lsf()
        app.logger.info('[%s] : [INFO] Resources with payload -> %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(resFin))

        dmon = GreenletRequests(resFin)
        nodeRes = dmon.parallelPost(None)
        app.logger.info('[%s] : [INFO] Resources responses -> %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(nodeRes))
        failedNodes = []
        for n in nodeRes:
            nodeIP = urlparse(n['Node'])
            qNode = dbNodes.query.filter_by(nodeIP=nodeIP.hostname).first()
            # print n['StatusCode']
            if n['StatusCode'] != 200:
                failedNodes.append({'NodeIP': str(nodeIP.hostname),
                                    'Code': n['StatusCode']})
                qNode.nCollectdState = 'unknown'
                qNode.nLogstashForwState = 'unknown'
        response = jsonify({'Status': 'Reconfigured ' + auxComp,
                            'Message': 'Updated Status',
                            'Failed': failedNodes})
        response.status_code = 200
        app.logger.info('[%s] : [INFO] Component %s reconfigure, failed %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(auxComp), str(failedNodes))
        dmon.reset()
        return response


@dmon.route('/v1/overlord/aux/interval')
class AuxInterval(Resource):
    def get(self):
        qInterv = dbMetPer.query.first()
        if qInterv is None:
            response = jsonify({'Status': 'No metrics interval has been set'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARNING] No metrics interval has been set',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        else:
            response = jsonify({'System': qInterv.sysMet,
                        'YARN': qInterv.yarnMet,
                        'Spark': qInterv.sparkMet,
                        'Storm': qInterv.stormMet})
            response.status_code = 200
            app.logger.info('[%s] : [INFO] Returned metrics poll rate; System -> %s, YARN -> %s, Spark -> %s, Storm -> %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                            qInterv.sysMet, qInterv.yarnMet, qInterv.sparkMet, qInterv.stormMet)
        return response

    @api.expect(resInterval)
    def put(self):
        if not request.json:
            abort(400)

        if 'Spark' not in request.json:
            spark = '15'
        else:
            spark = request.json['Spark']
        if 'Storm' not in request.json:
            storm = '60'
        else:
            storm = request.json['Storm']
        if 'YARN' not in request.json:
            yarn = '15'
        else:
            yarn = request.json['YARN']
        if 'System' not in request.json:
            system = '15'
        else:
            system = request.json['System']
        app.logger.info('[%s] : [INFO] Values; System -> %s, YARN -> %s, Spark -> %s, Storm -> %s',
                      datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), system, yarn, spark, storm)
        qInterv = dbMetPer.query.first()
        if qInterv is None:
            upMet = dbMetPer(sysMet=system, yarnMet=yarn, stormMet=storm, sparkMet=spark)
            db.session.add(upMet)
            db.session.commit()
            response = jsonify({'Status': 'Added metrics interval values'})
            response.status_code = 201
            app.logger.info('[%s] : [INFO] Added Metrics interval values',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        else:
            if 'Spark' not in request.json:
                app.logger.info('[%s] : [INFO] Spark not in request. Value unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                pass
            elif request.json['Spark'] == spark:
                qInterv.sparkMet = spark
            if 'Storm' not in request.json:
                app.logger.info('[%s] : [INFO] Storm not in request. Value unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                pass
            elif request.json['Storm'] == storm:
                qInterv.stormMet = storm
            if 'YARN' not in request.json:
                app.logger.info('[%s] : [INFO] YARN not in request. Value unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                pass
            elif request.json['YARN'] == yarn:
                qInterv.yarnMet = yarn
            if 'System' not in request.json:
                app.logger.info('[%s] : [INFO] System not in request. Value unchanged',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                pass
            elif request.json['System'] == system:
                qInterv.sysMet = system
            db.session.commit()
            response = jsonify({'Status': 'Updated metrics interval values'})
            response.status_code = 200
            app.logger.info('[%s] : [INFO] Updated Metrics interval values',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        return response


@dmon.route('/vx/reset/<type>')
class DMONReset(Resource):
    def post(self, type):
        listP = ['status', 'monitored']
        if type not in listP:
            return "Not Supported"
        qn = dbNodes.query.all()
        for n in qn:
            if type == 'status':
                print str(n.nStatus)
                n.nStatus = 0
                print str(n.nStatus)
            elif type == 'monitored':
                print str(n.nMonitored)
                n.nMonitored = 0
                print str(n.nMonitored)
        return "Done"


@dmon.route('/vx/test')
class WTF(Resource):
    def get(self):
        qESCore = dbESCore.query.filter_by(MasterNode=1).first()

        return qESCore.nodePort

@dmon.route('/vx/timeout')
class CheckTimeout(Resource):
    def get(self):
        try:
            timeOut = os.environ.get('DMON_TIMEOUT')
        except Exception as inst:
            response = jsonify({'Status': 'Error fetching env variable'})
            response.status_code = 500
            return response
        response = jsonify({'Timeout': timeOut,
                            'Default': os.getenv('DMON_TIMEOUT', 5)})
        response.status_code = 200
        return response


"""
Custom errot Handling

"""


@app.errorhandler(403)
def forbidden(e):
    response = jsonify({'error': 'forbidden'})
    response.status_code = 403
    return response


@app.errorhandler(404)
def page_not_found(e):
    response = jsonify({'error': 'not found'})
    response.status_code = 404
    return response


@app.errorhandler(500)
def internal_server_error(e):
    response = jsonify({'error': 'internal server error'})
    response.status_code = 500
    return response


@app.errorhandler(405)
def meth_not_allowed(e):
    response = jsonify({'error': 'method not allowed'})
    response.status_code = 405
    return response


@api.errorhandler(400)
def bad_request(e):
    response = jsonify({'error': 'bad request'})
    response.status_code = 400
    return response


@api.errorhandler(415)
def bad_mediatype(e):
    response = jsonify({'error': 'unsupported media type'})
    response.status_code = 415
    return response


if __name__ == '__main__':
    handler = RotatingFileHandler(logDir + '/dmon-controller.log', maxBytes=10000000, backupCount=5)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)
    #DB Initialization
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(baseDir, 'dmon.db')
    # app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
    # db.create_all()
    if len(sys.argv) == 1:
        app.run(port=5001, debug=True, threaded=True)
    else:
        app.run(host='0.0.0.0', port=8080, debug=True)
