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
# from dbModel import *
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

# directory Location
outDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
tmpDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
cfgDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')
baseDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db')
pidDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pid')
logDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
credDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys')

# TODO: only provisory for testing
esDir = '/opt/elasticsearch'
lsCDir = '/etc/logstash/conf.d/'

# D-Mon Supported frameworks
lFrameworks = ['hdfs', 'yarn', 'spark', 'storm']

# app = Flask("D-MON")
# api = Api(app, version='0.2.0', title='DICE MONitoring API',
#     description='RESTful API for the DICE Monitoring Platform  (D-MON)',
# )


db = SQLAlchemy(app)


# %--------------------------------------------------------------------%


class dbNodes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nodeFQDN = db.Column(db.String(64), index=True, unique=True)
    nodeIP = db.Column(db.String(64), index=True, unique=True)
    nodeUUID = db.Column(db.String(64), index=True, unique=True)
    nodeOS = db.Column(db.String(120), index=True, unique=False)
    nUser = db.Column(db.String(64), index=True, unique=False)
    nPass = db.Column(db.String(64), index=True, unique=False)
    nkey = db.Column(db.String(120), index=True, unique=False)
    nRoles = db.Column(db.String(120), index=True, unique=False, default='unknown')  # hadoop roles running on server
    nStatus = db.Column(db.Boolean, index=True, unique=False, default='0')
    nMonitored = db.Column(db.Boolean, index=True, unique=False, default='0')
    nCollectdState = db.Column(db.String(64), index=True, unique=False,
                               default='None')  # Running, Pending, Stopped, None
    nLogstashForwState = db.Column(db.String(64), index=True, unique=False,
                                   default='None')  # Running, Pending, Stopped, None
    nLogstashInstance = db.Column(db.String(64), index=True, unique=False, default='None')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # ES = db.relationship('ESCore', backref='nodeFQDN', lazy='dynamic')

    # TODO: Create init function/method to populate db.Model

    def __repr__(self):
        return '<dbNodes %r>' % (self.nodeFQDN)


class dbESCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    nodeName = db.Column(db.String(64), index=True, unique=True)
    nodePort = db.Column(db.Integer, index=True, unique=False, default=9200)
    clusterName = db.Column(db.String(64), index=True, unique=False)
    conf = db.Column(db.LargeBinary, index=True, unique=False)
    ESCoreStatus = db.Column(db.String(64), index=True, default='unknown',
                             unique=False)  # Running, Pending, Stopped, unknown
    ESCorePID = db.Column(db.Integer, index=True, default=0, unique=False)  # pid of current running process
    ESCoreHeap = db.Column(db.String(64), index=True, unique=False, default='4g')
    MasterNode = db.Column(db.Boolean, index=True, unique=False, default=True)  # which node is master
    DataNode = db.Column(db.Boolean, index=True, unique=False, default=True)
    NumOfShards = db.Column(db.Integer, index=True, default=5, unique=False)
    NumOfReplicas = db.Column(db.Integer, index=True, default=1, unique=False)
    FieldDataCacheSize = db.Column(db.String(64), index=True, unique=False, default='20%')
    FieldDataCacheExpires = db.Column(db.String(64), index=True, unique=False, default='6h')
    FieldDataCacheFilterSize = db.Column(db.String(64), index=True, unique=False, default='20%')
    FieldDataCacheFilterExpires = db.Column(db.String(64), index=True, unique=False, default='6h')
    IndexBufferSize = db.Column(db.String(64), index=True, unique=False, default='30%')
    MinShardIndexBufferSize = db.Column(db.String(64), index=True, unique=False, default='12mb')
    MinIndexBufferSize = db.Column(db.String(64), index=True, unique=False, default='96mb')
    ESCoreDebug = db.Column(db.String(64), index=True, unique=False, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbESCore %r>' % (self.hostFQDN)


class dbSCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    inLumberPort = db.Column(db.Integer, index=True, unique=False, default=5000)
    sslCert = db.Column(db.String(120), index=True, unique=False, default='default')
    sslKey = db.Column(db.String(120), index=True, unique=False, default='default')
    udpPort = db.Column(db.Integer, index=True, unique=False, default=25826)  # collectd port same as collectd conf
    outESclusterName = db.Column(db.String(64), index=True, unique=False)  # same as ESCore clusterName
    outKafka = db.Column(db.String(64), index=True, unique=False, default='unknown')  # output kafka details
    outKafkaPort = db.Column(db.Integer, index=True, unique=False, default='unknown')
    conf = db.Column(db.String(140), index=True, unique=False)
    LSCoreHeap = db.Column(db.String(120), index=True, unique=False, default='512m')
    LSCoreWorkers = db.Column(db.String(120), index=True, unique=False, default='4')
    LSCoreStatus = db.Column(db.String(64), index=True, unique=False,
                             default='unknown')  # Running, Pending, Stopped, None
    LSCorePID = db.Column(db.Integer, index=True, unique=False, default=0)
    LSCoreStormEndpoint = db.Column(db.String(64), index=True, unique=False, default='None')
    LSCoreStormPort = db.Column(db.String(64), index=True, unique=False, default='None')
    LSCoreStormTopology = db.Column(db.String(64), index=True, unique=False, default='None')
    LSCoreSparkEndpoint = db.Column(db.String(64), index=True, unique=False, default='None')
    LSCoreSparkPort = db.Column(db.String(64), index=True, unique=False, default='None')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbLSCore %r>' % (self.hostFQDN)


class dbKBCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    kbPort = db.Column(db.Integer, index=True, unique=False, default=5601)
    KBCorePID = db.Column(db.Integer, index=True, default=0, unique=False)  # pid of current running process
    conf = db.Column(db.String(140), index=True, unique=False)
    KBCoreStatus = db.Column(db.String(64), index=True, default='unknown',
                             unique=False)  # Running, Pending, Stopped, None
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbKBCore %r>' % (self.hostFQDN)


# Not Used Yet
class dbApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appName = db.Column(db.String(64), index=True, unique=False)
    appVersion = db.Column(db.String(64), index=True, unique=False)
    jobID = db.Column(db.String(64), index=True, unique=True)
    startTime = db.Column(db.String(64), index=True, unique=False)
    loggingPeriod = db.Column(db.Integer, index=True, unique=False)
    stopTime = db.Column(db.String(64), index=True, unique=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<dbApp %r>' % (self.appName)


class dbCDHMng(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cdhMng = db.Column(db.String(64), index=True, unique=True)
    cdhMngPort = db.Column(db.Integer, index=True, unique=False, default=7180)
    cpass = db.Column(db.String(64), index=True, default='admin', unique=False)
    cuser = db.Column(db.String(64), index=True, default='admin', unique=False)

    def __repr__(self):
        return '<dbCDHMng %r>' % (self.cdhMng)

class dbMetPer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sysMet = db.Column(db.String(64), index=True, unique=False, default="15")
    yarnMet = db.Column(db.String(64), index=True, unique=False, default="15")
    sparkMet = db.Column(db.String(64), index=True, unique=False, default="5")
    stormMet = db.Column(db.String(64), index=True, unique=False, default="60")

    def __repr__(self):
        return '<dbCDHMng %r>' % (self.id)


# %--------------------------------------------------------------------%

# changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
# dmon = api.namespace('dmon', description='D-MON operations')

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
    'queryString': fields.String(required=True, default="hostname:\"dice.cdh5.s4.internal\" AND serviceType:\"dfs\""
                                 , description='ElasticSearc Query'),
    'tstart': fields.Integer(required=True, default="now-1d", description='Start Date'),
    'tstop': fields.Integer(required=False, default="None", description='Stop Date'),
    'metrics': fields.List(fields.String(required=False, default=' ', description='Desired Metrics')),
    'index': fields.String(required=False, default='logstash-*', description='Name of ES Core index')
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
    'LPort': fields.Integer(required=True, description='Lumberjack port'),
    'udpPort': fields.String(required=True, default=25826, description='UDP Collectd Port'),
    'LSCoreHeap': fields.String(required=False, default='512m', description='Heap size for LS server'),
    'LSCoreWorkers': fields.String(required=False, default='4', description='Number of workers for LS server'),
    'ESClusterName': fields.String(required=True, description='ES cluster name'),
# TODO: use as foreign key same as ClusterName in esCore
    'LSCoreStormEndpoint': fields.String(required=False, default='None', description='Storm REST Endpoint'),
    'LSCoreStormPort': fields.String(required=False, default='None', description='Storm REST Port'),
    'LSCoreStormTopology': fields.String(required=False, default='None', description='Storm Topology ID'),
    'LSCoreSparkEndpoint': fields.String(required=False, default='None', description='Spark REST Endpoint'),
    'LSCoreSparkPort': fields.String(required=False, default='None', description='Spark REST Port')
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
        return 'Returns a list of all applications from YARN.'


@dmon.route('/v1/observer/applications/<appID>')
@api.doc(params={'appID': 'Application identification'})
class ObsAppbyID(Resource):
    def get(self, appID):
        return 'Returns information on a particular YARN applicaiton identified by ' + appID + '!'


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
            print >> sys.stderr, nl[0]
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
            ListMetrics, resJson = queryESCore(query, debug=False,
                                               myIndex=myIndex)  # TODO enclose in Try Catch if es instance unreachable
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
            ListMetrics, resJson = queryESCore(query, allm=False, dMetrics=metrics, debug=False, myIndex=myIndex)
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


@dmon.route('/v1/overlord')
class OverlordInfo(Resource):
    def get(self):
        message = 'Message goes Here and is not application/json (TODO)!'
        return message


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


@dmon.route('/v1/overlord/applicaiton/<appID>')
@api.doc(params={'appID': 'Application identification'})
class OverlordAppSubmit(Resource):
    def put(self):
        return 'Registers an applicaiton with DMON and creates a unique tag!'


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
            r = requests.get(esCoreUrl, timeout=2)  # timeout in seconds
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
                                        qNodes.nodeFQDN, qNodeLSinstance.hostFQDN)
                else:
                    nLSI = nodes['LogstashInstance']
                    app.logger.info('[%s] : [INFO] LS Instance at %s assigned to %s',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                    nLSI, nodes['NodeName'])

                e = dbNodes(nodeFQDN=nodes['NodeName'], nodeIP=nodes['NodeIP'], nodeOS=nodes['NodeOS'],
                            nkey=nodes['key'], nUser=nodes['username'], nPass=nodes['password'], nLogstashInstance=nLSI)
                db.session.add(e)
            else:
                qNodes.nodeIP = nodes['NodeIP']
                qNodes.nodeOS = nodes['NodeOS']
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

    def post(self):
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
            print >> sys.stderr, nl[0]
            nodeDict.update({nl[0]: nl[1].split(',')})
            nodeList.append(nodeDict)
        response = jsonify({'Nodes': nodeList})
        app.logger.info('[%s] : [INFO] Nodes and their associted roles ',
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

        if "Nodes" not in request.json or "NodeName" not in request.jdon:
            response = jsonify({'Status': 'Malformed Request',
                                'Message': 'Missing key(s)'})
            response.status_code = 400
            app.logger.warning('[%s] : [WARN] Malformed request, missing keys',
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
                app.logger.warrning('[%s] : [WARN] Node %s not found',
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
                uploadFile(nl, node[2], node[3], propYarnFile, 'hadoop-metrics2.tmp',
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
                'Key': qNode.nkey,  # TODO Chef client status, and CDH status
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

    def post(self, nodeFQDN):
        return "Bootstrap specified node!"

    def delete(self, nodeFQDN):
        dNode = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
        if dNode is None:
            response = jsonify({'Status': 'Node ' + nodeFQDN + ' not found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No node %s found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN)
            return response
        dlist = []
        dlist.append(dNode.nodeIP)
        try:
            serviceCtrl(dlist, dNode.nUser, dNode.nPass, 'collectd', 'stop')
        except Exception as inst:
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            response = jsonify({'Error': 'Collectd stopping error!'})
            response.status_code = 500
            app.logger.error('[%s] : [ERROR] Error while stopping collectd with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            return response

        try:
            serviceCtrl(dlist, dNode.nUser, dNode.nPass, 'logstash-forwarder', 'stop')
        except Exception as inst:
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            response = jsonify({'Error': 'LSF stopping error!'})
            response.status_code = 500
            app.logger.error('[%s] : [ERROR] Error while stopping lsf with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            return response
        dNode.nMonitored = 0
        dNode.nCollectdState = 'Stopped'
        dNode.nLogstashForwState = 'Stopped'
        response = jsonify({'Status': 'Node ' + nodeFQDN + ' monitoring stopped!'})
        response.status_code = 200
        app.logger.info('[%s] : [INFO] Monitoring stopped on node %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN)
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

    def post(self, nodeFQDN):
        return 'Redeploy configuration for node ' + nodeFQDN + '!'


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
            serviceCtrl(lPurge, qPurge.uUser, qPurge.uPass, 'logstash-forwarder', 'stop')
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
            serviceCtrl(lPurge, qPurge.uUser, qPurge.uPass, 'collectd', 'stop')
        except Exception as inst:
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            response = jsonify({'Error': 'Stopping collectd!'})
            response.status_code = 500
            app.logger.error('[%s] : [ERROR] While stopping collectd on %s with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), nodeFQDN, type(inst),
                             inst.args)
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
        requiredKeys = ['ESClusterName', 'HostFQDN', 'IP', 'NodeName', 'NodePort']
        if not request.json:
            abort(400)
        for key in requiredKeys:
            if key not in request.json:
                response = jsonify({'Error': 'malformed request, missing key(s)'})
                response.status_code = 400
                app.logger.warning('[%s] : [WARN] Malformed Request, missing key(s)',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                return response

        qESCore = dbESCore.query.filter_by(hostIP=request.json['IP']).first()
        if request.json["OS"] is None:
            os = "unknown"
        else:
            os = request.json["OS"]
        if request.json['ESCoreHeap'] is None:
            ESHeap = '4g'
        else:
            ESHeap = request.json['ESCoreHeap']
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
            upES = dbESCore(hostFQDN=request.json["HostFQDN"], hostIP=request.json["IP"], hostOS=os,
                            nodeName=request.json["NodeName"], clusterName=request.json["ESClusterName"],
                            conf='None', nodePort=request.json['NodePort'], MasterNode=master, DataNode=data,
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
            qESCore.nodePort = request.json['NodePort']
            if 'DataNode' not in request.json:
                print >> sys.stderr, 'DataNode unchanged'
            elif request.json['DataNode'] == data:
                qESCore.DataNode = data
                print >> sys.stderr, 'DataNode set to ' + data
            if 'ESCoreHeap' not in request.json:
                print >> sys.stderr, 'ESCoreHeap unchanged'
            elif request.json['ESCoreHeap'] == ESHeap:
                qESCore.ESCoreHeap = ESHeap
                print >> sys.stderr, 'ESCoreHeap set to ' + ESHeap
            if 'NumOfShards' not in request.json:
                print >> sys.stderr, 'NumOfShards unchanged'
            elif request.json['NumOfShards'] == shards:
                qESCore.NumOfShards = shards
                print >> sys.stderr, 'NumOfShards set to ' + shards
            if 'NumOfReplicas' not in request.json:
                print >> sys.stderr, 'NumOfReplicas unchanged'
            elif request.json['NumOfReplicas'] == rep:
                qESCore.NumOfReplicas = rep
                print >> sys.stderr, 'NumOfReplicas set to ' + rep
            if 'FieldDataCacheSize' not in request.json:
                print >> sys.stderr, 'FieldDataCacheSize unchanged'
            elif request.json['FieldDataCacheSize'] == fdcs:
                qESCore.FieldDataCacheSize = fdcs
                print >> sys.stderr, 'FieldDataCacheSize set to ' + fdcs
            if 'FieldDataCacheExpires' not in request.json:
                print >> sys.stderr, 'FieldDataCacheExpires unchanged'
            elif request.json['FieldDataCacheExpires'] == fdce:
                qESCore.FieldDataCacheExpires = fdce
                print >> sys.stderr, 'FieldDataCacheExpires set to ' + fdce
            if 'FieldDataCacheFilterSize' not in request.json:
                print >> sys.stderr, 'FieldDataCacheFilterSize unchanged'
            elif request.json['FieldDataCacheFilterSize'] == fdcfs:
                qESCore.FieldDataCacheFilterSize = fdcfs
                print >> sys.stderr, 'FieldDataCacheFilterSize set to ' + fdcfs
            if 'FieldDataCacheFilterExpires' not in request.json:
                print >> sys.stderr, 'FieldDataCacheFilterExpires unchanged'
            elif request.json['FieldDataCacheFilterExpires'] == fdcfe:
                qESCore.FieldDataCacheFilterExpires = fdcfe
                print >> sys.stderr, 'FieldDataCacheFilterExpires set to ' + fdcfe
            if 'IndexBufferSize' not in request.json:
                print >> sys.stderr, 'IndexBufferSize unchanged'
            elif request.json['IndexBufferSize'] == ibs:
                qESCore.IndexBufferSize = ibs
                print >> sys.stderr, 'IndexBufferSize set to ' + ibs
            if 'MinShardIndexBufferSize' not in request.json:
                print >> sys.stderr, 'MinShardIndexBufferSize unchanged'
            elif request.json['MinShardIndexBufferSize'] == msibs:
                qESCore.MinShardIndexBufferSize = msibs
                print >> sys.stderr, 'MinShardIndexBufferSize set to ' + msibs
            if 'MinIndexBufferSize' not in request.json:
                print >> sys.stderr, 'MinIndexBufferSize unchanged'
            elif request.json['MinIndexBufferSize'] == mibs:
                qESCore.MinIndexBufferSize = mibs
                print >> sys.stderr, 'MinIndexBufferSize set to ' + mibs
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

        os.kill(qESCorePurge.ESCorePID, signal.SIGTERM)

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

        os.kill(qLSCorePurge.LSCorePID, signal.SIGTERM)
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
                                    dbESCore.ESCoreDebug).all()
        resList = []
        for hosts in hostsAll:
            confDict = {}
            confDict['HostFQDN'] = hosts[0]
            confDict['IP'] = hosts[1]
            confDict['OS'] = hosts[2]
            confDict['NodeName'] = hosts[3]
            confDict['NodePort'] = hosts[4]
            confDict['ESClusterName'] = hosts[5]
            confDict['Status'] = hosts[6]
            confDict['PID'] = hosts[7]
            confDict['Master'] = hosts[8]
            confDict['Data'] = hosts[9]
            confDict['Shards'] = hosts[10]
            confDict['Replicas'] = hosts[11]
            confDict['FieldDataCacheSize'] = hosts[12]
            confDict['FieldDataCacheExpire'] = hosts[13]
            confDict['FieldDataCacheFilterSize'] = hosts[14]
            confDict['FieldDataCacheFilterExpires'] = hosts[15]
            confDict['IndexBufferSize'] = hosts[16]
            confDict['MinShardIndexBufferSize'] = hosts[17]
            confDict['MinIndexBufferSize'] = hosts[18]
            confDict['Debug'] = hosts[19]
            resList.append(confDict)
        response = jsonify({'ES Instances': resList})
        response.status_code = 200
        return response

    def post(self):
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        esTemp = os.path.join(tmpDir, 'elasticsearch.tmp')  # tmpDir+"/collectd.tmp"
        esfConf = os.path.join(cfgDir, 'elasticsearch.yml')
        qESCore = dbESCore.query.filter_by(
            MasterNode=1).first()  # TODO -> curerntly only generates config file for master node
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
            return "Tempalte file unavailable!"

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
                                     stdout=subprocess.PIPE).pid  # TODO: Try -p to set pid file location
        except Exception as inst:
            print >> sys.stderr, 'Error while starting elasticsearch'
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
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


@dmon.route('/v1/overlord/core/es/status/<intComp>/property/<intProp>')
@api.doc(params={'intComp': 'ES specific component', 'intProp': 'Component specific property'})
class ESCOntrollerStatus(Resource):
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
        data = ''
        qESCore = dbESCore.query.filter_by(MasterNode=1).first()
        if qESCore is None:
            response = jsonify({"Status": "No master ES instances found!"})
            response.status_code = 500
            return response
        if intComp == 'cluster':
            try:
                esCoreUrl = 'http://%s:%s/%s/%s' % (qESCore.hostIP, qESCore.nodePort, '_cluster', intProp)
                print >> sys.stderr, esCoreUrl
                r = requests.get(esCoreUrl, timeout=2)  # timeout in seconds
                data = r.json()
            except:
                response = jsonify({"Error": "Master ES instances not reachable!"})
                response.status_code = 500
                return response
        elif intComp == 'shards' and intProp == 'list':
            try:
                shardUrl = 'http://%s:%s/%s/%s' % (qESCore.hostIP, qESCore.nodePort, '_cat', intComp)
                print >> sys.stderr, shardUrl
                r = requests.get(shardUrl, timeout=2)
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


@dmon.route('/v1/overlord/core/es/<hostFQDN>/start')
@api.doc(params={'hostFQDN': 'Host FQDN'})
class ESControllerStart(Resource):
    def get(self, hostFQDN):
        qESCoreStatus = dbESCore.query.filter_by(hostFQDN=hostFQDN).first()
        if qESCoreStatus is None:
            response = jsonify({'Status': 'Unknown host ' + hostFQDN})
            response.status_code = 404
            return response
        response = jsonify({'Status': qESCoreStatus.ESCoreStatus,
                            'PID': qESCoreStatus.ESCorePID})
        response.status_code = 200
        return response

    def post(self, hostFQDN):
        qESCoreStart = dbESCore.query.filter_by(hostFQDN=hostFQDN).first()
        if qESCoreStart is None:
            response = jsonify({'Status': 'Unknown host ' + hostFQDN})
            response.status_code = 404
            return response

        if checkPID(qESCoreStart.ESCorePID) is True:
            proc = psutil.Process(qESCoreStart.ESCorePID)
            if proc.status() == psutil.STATUS_ZOMBIE:
                print >> sys.stderr, 'Process ' + str(qESCoreStart.ESCorePID) + ' is zombie!'
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
            print >> sys.stderr, 'Error while starting elasticsearch'
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
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

    # os.kill(qESCoreStart.ESCorePID, signal.SIGTERM)


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
            confDict['PID'] = hosts[4]
            confDict['KBStatus'] = hosts[5]
            resList.append(confDict)
        response = jsonify({'KB Instances': resList})
        response.status_code = 200
        return response

    def post(self):
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        kbTemp = os.path.join(tmpDir, 'kibana.tmp')  # tmpDir+"/collectd.tmp"
        kbfConf = os.path.join(cfgDir, 'kibana.yml')
        qKBCore = dbKBCore.query.first()  # TODO: only one instance is supported
        if qKBCore is None:
            response = jsonify({"Status": "No KB instance found!"})
            response.status_code = 500
            return response

        if checkPID(qKBCore.KBCorePID) is True:
            subprocess.call(["kill", "-9", str(qKBCore.KBCorePID)])

        try:
            template = templateEnv.get_template(kbTemp)
        # print >>sys.stderr, template
        except:
            return "Tempalte file unavailable!"

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
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
        qKBCore.KBCorePID = kbPid
        qKBCore.KBCoreStatus = 'Running'
        response = jsonify({'Status': 'Kibana Core  PID ' + str(kbPid)})
        response.status_code = 200
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
        # if request.headers['Content-Type'] == 'text/plain':
        # 	cData = request.data
        # 	#temporaryConf =  open(tmp_loc+'/temporary.conf',"w+")
        # 	#temporaryConf.write(cData)
        # 	#temporaryConf.close()
        # 	print cData
        requiredKeys = ['ESClusterName', 'HostFQDN', 'IP', 'LPort', 'udpPort']
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
        qSCore = dbSCore.query.filter_by(hostIP=request.json['IP']).first()
        if request.json["OS"] is None:
            os = "unknown"
        else:
            os = request.json["OS"]

        if request.json["LSCoreHeap"] is None:
            lsHeap = '4g'
        else:
            lsHeap = request.json["LSCoreHeap"]

        if request.json["LSCoreWorkers"] is None:
            lsWorkers = '4'
        else:
            lsWorkers = request.json["LsCoreWorkers"]

        if request.json['LSCoreStormEndpoint'] is None:
            StormEnd = 'None'
        else:
            StormEnd = request.json['LSCoreStormEndpoint']

        if request.json['LSCoreStormPort'] is None:
            StormPort = 'None'
        else:
            StormPort = request.json['LSCoreStormPort']

        if request.json['LSCoreStormTopology'] is None:
            StormTopo = 'None'
        else:
            StormTopo = request.json['LSCoreStormTopology']

        if request.json['LSCoreSparkEndpoint'] is None:
            SparkEnd = 'None'
        else:
            SparkEnd = request.json['LSCoreSparkEndpoint']

        if request.json['LSCoreSparkPort'] is None:
            SparkPort = 'None'
        else:
            SparkPort = request.json['LSCoreSparkPort']

        if qSCore is None:
            upS = dbSCore(hostFQDN=request.json["HostFQDN"], hostIP=request.json["IP"], hostOS=os,
                          outESclusterName=request.json["ESClusterName"], udpPort=request.json["udpPort"],
                          inLumberPort=request.json['LPort'], LSCoreWorkers=lsWorkers, LSCoreHeap=lsHeap,
                          LSCoreStormEndpoint=StormEnd, LSCoreStormPort=StormPort, LSCoreStormTopology=StormTopo,
                          LSCoreSparkEndpoint=SparkEnd, LSCoreSparkPort=SparkPort)
            db.session.add(upS)
            db.session.commit()
            response = jsonify({'Added': 'LS Config for ' + request.json["HostFQDN"]})
            response.status_code = 201
            return response
        else:
            # qESCore.hostFQDN =request.json['HostFQDN'] #TODO document hostIP and FQDN may not change in README.md
            qSCore.hostOS = os
            qSCore.LSCoreWorkers = lsWorkers
            qSCore.LSCoreHeap = lsHeap
            qSCore.outESclusterName = request.json['ESClusterName']
            qSCore.udpPort = request.json['udpPort']
            qSCore.inLumberPort = request.json['LPort']
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
                                    dbSCore.LSCoreSparkEndpoint, dbSCore.LSCoreSparkPort).all()
        resList = []
        for hosts in hostsAll:
            confDict = {}
            confDict['HostFQDN'] = hosts[0]
            confDict['IP'] = hosts[1]
            confDict['OS'] = hosts[2]
            confDict['LPort'] = hosts[3]
            confDict['udpPort'] = hosts[6]
            confDict['ESClusterName'] = hosts[7]
            confDict['StormRestIP'] = hosts[9]
            confDict['StormRestPort'] = hosts[10]
            confDict['StormTopology'] = hosts[11]
            confDict['SparkRestIP'] = hosts[12]
            confDict['SparkRestPort'] = hosts[13]
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
            return response
        qESCore = dbESCore.query.filter_by(MasterNode=1).first()  # TODO: only works with the master node
        if qESCore is None:
            response = jsonify({"Status": "No ES instances registered"})
            response.status_code = 500
            return response

        if checkPID(qSCore.LSCorePID) is True:
            subprocess.call(['kill', '-9', str(qSCore.LSCorePID)])

        try:
            template = templateEnv.get_template(lsTemp)
        # print >>sys.stderr, template
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            return "LS Tempalte file unavailable!"

        if qSCore.sslCert == 'default':
            certLoc = os.path.join(credDir, 'logstash-forwarder.crt')
        else:
            certLoc = os.path.join(credDir, qSCore.sslCert + '.crt')

        if qSCore.sslKey == 'default':
            keyLoc = os.path.join(credDir, 'logstash-forwarder.key')
        else:
            keyLoc = os.path.join(credDir, qSCore.sslKey + '.key')

        StormRestIP = ''
        if qSCore.LSCoreStormEndpoint == 'None':
            StormRestIP = 'None'
        else:
            StormRestIP = qSCore.LSCoreStormEndpoint

        infoSCore = {"sslcert": certLoc, "sslkey": keyLoc, "udpPort": qSCore.udpPort,
                     "ESCluster": qSCore.outESclusterName, "EShostIP": qESCore.hostIP,
                     "EShostPort": qESCore.nodePort,
                     "StormRestIP": StormRestIP, "StormRestPort": qSCore.LSCoreStormPort,
                     "StormTopologyID": qSCore.LSCoreStormTopology}
        sConf = template.render(infoSCore)
        qSCore.conf = sConf
        # print >>sys.stderr, esConf
        db.session.commit()

        lsCoreConf = open(lsfCore, "w+")
        lsCoreConf.write(sConf)
        lsCoreConf.close()

        os.environ['LS_HEAP_SIZE'] = os.getenv('LS_HEAP_SIZE',
                                               qSCore.LSCoreHeap)  # TODO: if heap size set in env then use it if not use db one

        lsLogfile = os.path.join(logDir, 'logstash.log')
        lsPid = 0
        LSServerCmd = '/opt/logstash/bin/logstash agent  -f %s -l %s -w %s' % (lsfCore, lsLogfile, qSCore.LSCoreWorkers)
        try:
            lsPid = subprocess.Popen(LSServerCmd, shell=True).pid
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
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
            return response
        qSCore.LSCoreStatus = 'Running'
        response = jsonify({'Status': 'Logstash Core PID ' + str(lsPid)})
        response.status_code = 200
        return response


@dmon.route('/v1/overlord/core/ls/<hostFQDN>/start')
@api.doc(params={'hostFQDN': 'Host FQDN'})
class LSCoreCOntrollerStart(Resource):
    def get(self, hostFQDN):
        qLSCoreStatus = dbSCore.query.filter_by(hostFQDN=hostFQDN).first()
        if qLSCoreStatus is None:
            response = jsonify({'Status': 'Unknown host ' + hostFQDN})
            response.status_code = 404
            return response
        response = jsonify({'Status': qLSCoreStatus.LSCoreStatus,
                            'PID': qLSCoreStatus.LSCorePID})
        response.status_code = 200
        return response

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
                print >> sys.stderr, 'Process ' + str(qLSCoreStart.LSCorePID) + ' is zombie!'
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
            print >> sys.stderr, 'Error while starting logstash'
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
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
            print >> sys.stderr, nl[0]
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
        return "Returns Information about AUX components"


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
            print >> sys.stderr, credentials
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
                print >> sys.stderr, 'No collectd!'
                collectdList.append(res['IP'])
            if res['LSF'] == 'None':
                LSFList.append(res['IP'])
                print >> sys.stderr, 'No LSF!'
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

        print >> sys.stderr, collectdList
        print >> sys.stderr, LSFList
        print >> sys.stderr, credentials['User']
        print >> sys.stderr, confDir

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
            return "Tempalte file unavailable!"

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
            return "Template file unavailable!"

        infocollectdAux = {"logstash_server_ip": qSCore.hostIP, "logstash_server_port": qSCore.udpPort}
        collectdConf = collectdTemplate.render(infocollectdAux)

        collectdConfFile = open(collectdConfLoc, "wb")
        collectdConfFile.write(collectdConf)
        collectdConfFile.close()

        try:
            installCollectd(collectdList, credentials['User'], credentials['Pass'], confDir=cfgDir)
        except Exception as inst:  # TODO if exceptions is detected check to see if collectd started if not return fail if yes return warning
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            response = jsonify({'Status': 'Error Installing collectd!'})
            response.status_code = 500
            return response
        # TODO Assign logsash server instance to each node
        try:
            installLogstashForwarder(LSFList, userName=credentials['User'], uPassword=credentials['Pass'],
                                     confDir=cfgDir)
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            response = jsonify({'Status': 'Error Installig LSF!'})
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

    def post(self):  # TODO: only works if all nodes have the same authentication
        qN = db.session.query(dbNodes.nodeIP, dbNodes.nStatus, dbNodes.nUser, dbNodes.nPass).all()

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
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
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
        if qNodeStatus is None:
            response = jsonify({'Status': 'Agent Exception',
                                'Message': 'No agents are registered'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No agents registered',
					datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        dnode = []
        for ns in qNodeStatus:
            node = []
            if ns.nMonitored is True:
                break
            else:
                node.append(ns.nodeIP)
            app.logger.info('[%s] : [INFO] Unmonitored nodes %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(node))

            try:
                startAgent(node, ns.nUser, ns.nPass)
            except Exception as inst:
                # print >> sys.stderr, type(inst)
                # print >> sys.stderr, inst.args
                response = jsonify({'Status': 'Error Starting agent on  ' + ns.nodeFQDN + '!'})
                response.status_code = 500
                app.logger.error('[%s] : [INFO] Error starting agent on %s with exception %s and %s',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                 str(ns.nodeFQDN), type(inst), inst.args)
                return response
            app.logger.info('[%s] : [INFO] Started agent at %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(node))
            AgentNodes = {}
            AgentNodes['Node'] = ns.nodeFQDN
            AgentNodes['IP'] = ns.nodeIP
            dnode.append(AgentNodes)
            ns.nMonitored = 1
        response = jsonify({'Status': 'Agents Started',
                            'Nodes': dnode})
        response.status_code = 200
        app.logger.info('[%s] : [INFO] Agents started on nodes %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(dnode))
        return response


@dmon.route('/v2/overlord/aux/deploy')  # TODO: gets current status of aux components and deploy them based on roles
class AuxDeployThread(Resource):
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

    def put(self):  # TODO: used to enact new configurations
        return "Reload new Configuration"

    def post(self):
        qNodes = db.session.query(dbNodes.nodeIP, dbNodes.nRoles).all()
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
            print >> sys.stderr, str(n)
            try:
                NodeDict[nodeIP.hostname] = n['Data']['Components']
            except Exception as inst:
                print >> sys.stderr, type(inst)
                print >> sys.stderr, inst.args
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
                    print >> sys.stderr, type(inst)
                    print >> sys.stderr, inst.args
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
                    print >> sys.stderr, type(inst)
                    print >> sys.stderr, inst.args
                    response = jsonify({'Status': 'Error Installig Collectd on ' + qAux.nodeFQDN + '!'})
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
                    print >> sys.stderr, type(inst)
                    print >> sys.stderr, inst.args
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
                    print >> sys.stderr, type(inst)
                    print >> sys.stderr, inst.args
                    response = jsonify({'Status': 'Error Installig LSF on ' + qAux.nodeFQDN + '!'})
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


@dmon.route('/v2/overlord/aux/deploy/<auxComp>/<nodeFQDN>')  # TODO: deploy specific configuration on the specified node
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

    def put(self, auxComp):
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

            if qNCollectd is None:
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
                    print >> sys.stderr, type(inst)
                    print >> sys.stderr, inst.args
                # response = jsonify({'Status':'Error Starting collectd on '+ i.nodeFQDN +'!'})
                # response.status_code = 500
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
            if qNLsf is None:
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
                    print >> sys.stderr, type(inst)
                    print >> sys.stderr, inst.args
                    response = jsonify({'Status': 'Error Starting LSF on ' + i.nodeFQDN + '!'})
                    response.status_code = 500
                    return response

                LsfNodes = {}
                LsfNodes['Node'] = i.nodeFQDN
                LsfNodes['IP'] = i.nodeIP
                nodeLsfStopped.append(LsfNodes)
                i.nLogstashForwState = 'Running'
            response = jsonify({'Status': 'LSF started', 'Nodes': nodeLsfStopped})
            response.status_code = 200
            return response
        # return nodeCollectdStopped


@dmon.route('/v1/overlord/aux/<auxComp>/stop')  # auxCtrl(auxComp,'stop') #TODO revise from pysshCore and make it work!
@api.doc(params={'auxComp': 'Aux Component'})
class AuxStopAll(Resource):
    def post(self, auxComp):
        auxList = ['collectd', 'lsf']
        if auxComp not in auxList:
            response = jsonify({'Status': 'No such such aux component ' + auxComp})
            response.status_code = 400
            return response

        if auxComp == "collectd":
            qNCollectd = dbNodes.query.filter_by(nCollectdState='Running').all()

            if qNCollectd is None:
                response = jsonify({'Status': 'No nodes in state Running!'})
                response.status_code = 404
                return response

            nodeCollectdRunning = []
            for i in qNCollectd:
                node = []
                node.append(i.nodeIP)
                try:
                    serviceCtrl(node, i.nUser, i.nPass, 'collectd', 'stop')
                except Exception as inst:
                    print >> sys.stderr, type(inst)
                    print >> sys.stderr, inst.args
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
            if qNLsf is None:
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
                    print >> sys.stderr, type(inst)
                    print >> sys.stderr, inst.args
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
                    print >> sys.stderr, type(inst)
                    print >> sys.stderr, inst.args
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
                    print >> sys.stderr, type(inst)
                    print >> sys.stderr, inst.args
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
                    print >> sys.stderr, type(inst)
                    print >> sys.stderr, inst.args
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
                    print >> sys.stderr, type(inst)
                    print >> sys.stderr, inst.args
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
            r = requests.post(resourceList[0])
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
            r = requests.post(resourceList[0])
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
            else:
                qNode.nCollectdState = 'Stopped'
                qNode.nLogstashForwState = 'Stopped'

        response = jsonify({'Status': 'Stopped ' + auxComp,
                            'Message': 'Updated Status',
                            'Failed': failedNodes})

        response.status_code = 200

        dmon.reset()
        return response


@dmon.route('/v2/overlord/aux/<auxComp>/configure')
class AuxConfigureCompTreaded(Resource):
    def post(self, auxComp):
        auxList = ['collectd', 'lsf', 'jmx'] #TODO: add all, will need some concurency on dmon-agent part
        if auxComp not in auxList:
            response = jsonify({'Status': 'No such such aux component supported ' + auxComp})
            response.status_code = 400
            app.logger.warning('[%s] : [WARNING] Aux Components %s not supported',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), auxComp)
            return response
        qNodes = db.session.query(dbNodes.nodeIP, dbNodes.nMonitored).all()
        nList = []
        for n in qNodes:
            if not n[1]:
                break
            nList.append(n[0])
        if not nList:
            response = jsonify({'Status': 'No monitored nodes found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARNING] No monitored nodes found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), auxComp)
            return response

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
                payload['Interval'] = qMetPer.sysMet
                payload['LogstashIP'] = qNodeSpec.nLogstashInstance
                payload['UDPPort'] = str(qLSSpec.udpPort)
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
            return "Not available in this version!"


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
        if 'Systen' not in request.json:
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


@dmon.route('/v1/reset')
class DMONReset(Resource):
    def post(self):
        qn = dbNodes.query.all()
        listT = []
        for n in qn:
            print str(n.nStatus)
            n.nStatus = 0
            print str(n.nStatus)



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
    # app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(baseDir,'dmon.db')
    # app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
    # db.create_all()

    # print >>sys.stderr, "Running as: %s:%s" % (os.getuid(), os.getgid())
    # testQuery = queryConstructor(1438939155342,1438940055342,"hostname:\"dice.cdh5.s4.internal\" AND serviceType:\"dfs\"")
    # metrics = ['type','@timestamp','host','job_id','hostname','AvailableVCores']
    # test, test2 = queryESCore(testQuery, debug=False)
    # print >>sys.stderr, test2
    handler = RotatingFileHandler(logDir + '/dmon-controller.log', maxBytes=10000000, backupCount=5)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)
    if len(sys.argv) == 1:
        # esDir=
        # lsDir=
        # kibanaDir=
        app.run(port=5001, debug=True, threaded=True)
    else:
        app.run(host='0.0.0.0', port=8080, debug=True)
