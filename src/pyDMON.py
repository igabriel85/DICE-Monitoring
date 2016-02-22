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
#from werkzeug import secure_filename #unused
from urlparse import urlparse
#DICE Imports
from pyESController import *
from pysshCore import *
#from dbModel import *
from pyUtil import *
# from threadRequest import *
from greenletThreads import *
# import Queue
# from threading import Thread
import requests


#directory Location
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


app = Flask("D-MON")
api = Api(app, version='0.1.4', title='DICE MONitoring API',
    description='RESTful API for the DICE Monitoring Platform  (D-MON)',
)


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
    nRoles = db.Column(db.String(120), index=True, unique=False, default='unknown') # hadoop roles running on server
    nStatus = db.Column(db.Boolean, index=True, unique=False, default='0')
    nMonitored = db.Column(db.Boolean, index=True, unique=False, default='0')
    nCollectdState = db.Column(db.String(64), index=True, unique=False, default='None') # Running, Pending, Stopped, None
    nLogstashForwState = db.Column(db.String(64), index=True, unique=False, default='None') # Running, Pending, Stopped, None
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # ES = db.relationship('ESCore', backref='nodeFQDN', lazy='dynamic')

    # TODO: Create init function/method to populate db.Model

    def __repr__(self):
        return '<dbNodes %r>' % (self.nickname)


class dbESCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    nodeName = db.Column(db.String(64), index=True, unique=True)
    nodePort = db.Column(db.Integer, index=True, unique=False,default=9200)
    clusterName = db.Column(db.String(64), index=True, unique=False)
    conf = db.Column(db.LargeBinary, index=True, unique=False)
    ESCoreStatus = db.Column(db.String(64), index=True, default='unknown', unique=False)  # Running, Pending, Stopped, unknown
    ESCorePID = db.Column(db.Integer, index=True, default=0, unique=False)  # pid of current running process
    MasterNode = db.Column(db.Boolean, index=True, unique=False)  # which node is master
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
   

    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbESCore %r>' % (self.body)


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
    outKafka = db.Column(db.String(64), index=True, unique=False, default='unknown') # output kafka details
    outKafkaPort = db.Column(db.Integer, index=True, unique=False, default='unknown')
    conf = db.Column(db.String(140), index=True, unique=False)
    LSCoreStatus = db.Column(db.String(64), index=True, unique=False, default='unknown')#Running, Pending, Stopped, None
    LSCorePID = db.Column(db.Integer, index=True, unique=False, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbLSCore %r>' % (self.body)


class dbKBCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    kbPort = db.Column(db.Integer, index=True, unique=False, default=5601)
    KBCorePID = db.Column(db.Integer, index=True, default=0, unique=False) # pid of current running process
    conf = db.Column(db.String(140), index=True, unique=False)
    KBCoreStatus = db.Column(db.String(64), index=True, default='unknown', unique=False)#Running, Pending, Stopped, None
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbKBCore %r>' % (self.body)

#Not Used Yet
class dbApp(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	appName = db.Column(db.String(64), index=True, unique=False)
	appVersion = db.Column(db.String(64), index=True, unique=False)
	jobID = db.Column(db.String(64), index=True, unique=True)
	startTime = db.Column(db.String(64), index=True, unique=False)
	stopTime = db.Column(db.String(64), index=True, unique=False)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)
	def __repr__(self):
		return '<dbApp %r>' % (self.body)

class dbCDHMng(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	cdhMng = db.Column(db.String(64), index=True, unique=True)
	cdhMngPort = db.Column(db.Integer, index=True, unique=False, default=7180)
	cpass = db.Column(db.String(64), index=True, default='admin', unique=False)
	cuser = db.Column(db.String(64), index=True, default='admin', unique=False)
	
	def __repr__(self):
		return '<dbCDHMng %r>' % (self.body)



#%--------------------------------------------------------------------%

#changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
dmon = api.namespace('dmon', description='D-MON operations')

#argument parser
dmonAux = api.parser() 
dmonAux.add_argument('redeploy', type=str, required=False, help='Redeploys configuration of Auxiliary components on the specified node.')
dmonAuxAll=api.parser()
dmonAuxAll.add_argument('redeploy-all', type=str, required=False, help='Redeploys configuration of Auxiliary components on all nodes.')
#pQueryES.add_argument('task',type=str, required=True, help='The task details', location='form')


#descripes universal json @api.marshal_with for return or @api.expect for payload model
queryES = api.model('query details Model', {
	'fname': fields.String(required=False, default="output", description='Name of output file.'),
    'size': fields.Integer(required=True, default=500, description='Number of record'),
    'ordering': fields.String(required=True,default='desc', description='Ordering of records'),
    'queryString': fields.String(required=True, default="hostname:\"dice.cdh5.s4.internal\" AND serviceType:\"dfs\""
    	,description='ElasticSearc Query'),
    'tstart': fields.Integer(required=True, default="now-1d", description='Start Date'),
    'tstop': fields.Integer(required=False, default="None", description='Stop Date'),
    'metrics': fields.List(fields.String(required=False, default=' ', description='Desired Metrics'))

})
#Nested JSON input 
dMONQuery = api.model('queryES Model', {
	'DMON':fields.Nested(queryES, description="Query details")
	})


nodeSubmitCont = api.model('Submit Node Model Info',{
	'NodeName': fields.String(required=True, description="Node FQDN"),
	'NodeIP': fields.String(required=True, description="Node IP"),
	'NodeOS': fields.String(required=False, description="Node OS"),
	'key': fields.String(required=False, description="Node Pubilc key"),
	'username': fields.String(required=False, description="Node User Name"),
	'password': fields.String(required=False, description="Node Password"),
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
	'ESClusterName': fields.String(required=True, description='ES Host Name')
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
	'Key': fields.String(required=False, description="Node Pubilc key"),
	'User': fields.String(required=False, description="Node User Name"),
	'Password': fields.String(required=False, description="Node Password")
	})

nodeRoles = api.model('Update Node Role Model Info', {
	'Roles': fields.List(fields.String(required=True, default='yarn', description='Node Roles'))
	})

listNodesRolesInternal = api.model('Update List Node Role Model Info Nested', {
	"NodeName": fields.String(required=True, description="Node FQDN"),
	"Roles": fields.List(fields.String(required=True, default='yarn', description='Node Roles'))
})

listNodeRoles = api.model('Update List Node Role Model Info', {
	"Nodes": fields.List(fields.Nested(listNodesRolesInternal, required=True, description='List of nodes and their roles'))
})

lsCore = api.model('Submit LS conf',{
	'HostFQDN': fields.String(required=True, description='Host FQDN'),
	'IP': fields.String(required=True, description='Host IP'),
	'OS': fields.String(required=False, description='Host OS'),
	'LPort': fields.Integer(required=True, description='Lumberjack port'),
	'udpPort': fields.String(required=True, default=25826, description='UDP Collectd Port'),
	'ESClusterName': fields.String(required=True, description='ES cluster name') # TODO: use as foreign key same as ClusterName in esCore
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

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(baseDir, 'dmon.db')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db.create_all()


@dmon.route('/v1/log')
class DmonLog(Resource):
    def get(self):
        try:
            logfile = open(os.path.join(logDir, 'dmon.log'), 'r')
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
class ObsAppbyID(Resource):
	def get(self, appID):
		return 'Returns information on a particular YARN applicaiton identified by ' + appID + '!'


@dmon.route('/v1/observer/nodes')
class NodesMonitored(Resource):
	#@api.marshal_with(monNodes) # this is for response
	def get(self):
		nodeList = []
		nodesAll=db.session.query(dbNodes.nodeFQDN, dbNodes.nodeIP).all()
		if nodesAll is None:
			response = jsonify({'Status': 'No monitored nodes found'})
			response.status_code = 404
			return response
		for nl in nodesAll:
			nodeDict = {}
			print >>sys.stderr, nl[0]
			nodeDict.update({nl[0]: nl[1]})
			nodeList.append(nodeDict)
		response = jsonify({'Nodes': nodeList})
		response.status_code = 200
		return response


@dmon.route('/v1/observer/nodes/<nodeFQDN>')
@api.doc(params={'nodeFQDN':'Nodes FQDN'})
class NodeStatus(Resource):
	def get(self, nodeFQDN):
		qNode = dbNodes.query.filter_by(nodeFQDN = nodeFQDN).first()
		if qNode is None:
			response = jsonify({'Status':'Node ' +nodeFQDN+' not found!'})
			response.status_code = 404
			return response
		else:
			response = jsonify({nodeFQDN:{
				'Status':qNode.nStatus,
				'IP':qNode.nodeIP,
				'Monitored':qNode.nMonitored,
				'OS':qNode.nodeOS}})
			response.status_code = 200	
		return response


@dmon.route('/v1/observer/nodes/<nodeFQDN>/roles')
@api.doc(params={'nodeFQDN':'Nodes FQDN'})
class NodeStatusServices(Resource):
	def get(self,nodeFQDN):
		qNode = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
		if qNode.nRoles == 'unknown':
			response=jsonify({'Status': 'No known service on ' + nodeFQDN})
			response.status_code = 200
			return response
		else:
			roleList = qNode.nRoles
			response = jsonify({'Roles': roleList.split()})
			response.status_code = 200
			return response		


@dmon.route('/v1/observer/query/<ftype>')
@api.doc(params={'ftype':'output type'})
class QueryEsCore(Resource):
	#@api.doc(parser=pQueryES) #inst parser
	#@api.marshal_with(dMONQuery) # this is for response
	@api.expect(dMONQuery)# this is for payload 
	def post(self, ftype):
		#args = pQueryES.parse_args()#parsing query arguments in URI
		supportType = ["csv", "json", "plain"]
		if ftype not in supportType:
			response = jsonify({'Supported types': supportType, "Submitted Type": ftype})
			response.status_code = 415
			return response

		if 'tstop'not in request.json['DMON']:
			query = queryConstructor(tstart=request.json['DMON']['tstart'], queryString=request.json['DMON']['queryString'],
				size=request.json['DMON']['size'],ordering=request.json['DMON']['ordering'])
		else:
			query = queryConstructor(tstart=request.json['DMON']['tstart'], tstop=request.json['DMON']['tstop'],
				queryString=request.json['DMON']['queryString'], size=request.json['DMON']['size'], ordering=request.json['DMON']['ordering'])
		
		if not 'metrics'  in request.json['DMON'] or request.json['DMON']['metrics'] == " ":
			ListMetrics, resJson = queryESCore(query, debug=False) #TODO enclose in Try Catch if es instance unreachable
			if not ListMetrics:
				response = jsonify({'Status': 'No results found!'})
				response.status_code = 404
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
					csvfile=open(csvOut, 'r')
				except EnvironmentError:
					response = jsonify({'EnvError': 'file not found'})
					response.status_code = 500
					return response
				return send_file(csvfile, mimetype='text/csv', as_attachment=True)
			if ftype == 'json':
				response = jsonify({'DMON': resJson})
				response.status_code = 200
				return response
			if ftype == 'plain':
				return Response(str(ListMetrics), status=200, mimetype='text/plain')

		else:
			metrics = request.json['DMON']['metrics']
			ListMetrics, resJson = queryESCore(query, allm=False,dMetrics=metrics, debug=False)
			if not ListMetrics:
				response = jsonify({'Status': 'No results found!'})
				response.status_code = 404
				return response
			#repeated from before create function
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
					return response
				return send_file(csvfile, mimetype='text/csv', as_attachment=True)
			if ftype == 'json':
				response = jsonify({'DMON': resJson})
				response.status_code = 200
				return response
			if ftype == 'plain':
				return Response(str(ListMetrics), status=200, mimetype='text/plain')


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
class OverlordFrameworkProperties(Resource):
	def get(self, fwork):
		if fwork not in lFrameworks:
			response = jsonify({'Status': 'Malformed URI', 'Message': 'Unknown framework ' + fwork})
			response.status_code = 404
			return response
		if fwork == 'hdfs' or fwork == 'yarn':
			propFile = os.path.join(tmpDir, 'metrics/hadoop-metrics2.tmp')
			try:
				propCfg = open(propFile, 'r')
			except EnvironmentError:
				response = jsonify({'Status': 'Environment Error!', 'Message': 'File not Found!'})
				response.status_code = 500
				return response 
			return send_file(propCfg, mimetype='text/x-java-properties', as_attachment = True)

		if fwork == 'spark':
			templateLoader = jinja2.FileSystemLoader(searchpath="/")
			templateEnv = jinja2.Environment(loader=templateLoader)
			propSparkTemp= os.path.join(tmpDir, 'metrics/spark-metrics.tmp')
			propSparkFile = os.path.join(cfgDir, 'metrics.properties')
			try:
				template = templateEnv.get_template(propSparkTemp)
			except:
				response = jsonify({'Status': 'I/O Error', 'Message': 'Template file missing!'})
				response.status_code = 500
				return response

			qLSCore = dbSCore.query.first() #TODO: Only works for single deployment
			if qLSCore is None:
				response = jsonify({'Status': 'Missing Instance', 'Message': 'No Logstash Instance Configured'})
				response.status_code = 404
				return response
			infoSpark = {'logstashserverip': qLSCore.hostIP, 'logstashportgraphite': '5002', 'period': '10'}
			propSparkInfo = template.render(infoSpark)
			propSparkConf = open(propSparkFile, "w+")
			propSparkConf.write(propSparkInfo)
			propSparkConf.close()

			rSparkProp = open(propSparkFile, 'r')
			return send_file(rSparkProp, mimetype='text/x-java-properties', as_attachment=True) #TODO: Swagger returns same content each time, however sent file is correct
			
		

@dmon.route('/v1/overlord/applicaiton/<appID>')
class OverlordAppSubmit(Resource):
	def put(self):
		return 'Registers an applicaiton with DMON and creates a unique tag!'


@dmon.route('/v1/overlord/core')
class OverlordBootstrap(Resource):
	def post(self):
		return "Deploys all monitoring core components with default configuration"


@dmon.route('/v1/overlord/core/database')
class OverlordCoredb(Resource):
    def get(self):
        try:
            dbFile = open(os.path.join(baseDir, 'dmon.db'), 'r')
        except EnvironmentError:
            response = jsonify({'EnvError': 'file not found'})
            response.status_code = 500
            return response

        return send_file(dbFile, mimetype='application/x-sqlite3', as_attachment=True)

    def put(self):
        dbLoc = os.path.join(baseDir, 'dmon.db')
        file = request.files['dmon.db']
        if os.path.isfile(os.path.join(baseDir, 'dmon.db')) is True:
            os.rename(dbLoc, dbLoc + '.backup')
        file.save(dbLoc)

        response = jsonify({'Status': 'Done',
                            'Message': 'New DB loaded'})
        response.status_code = 201
        return response


@dmon.route('/v1/overlord/core/status')
class OverlordCoreStatus(Resource):
	def get(self):
		rspD = {}
		qESCore = dbESCore.query.filter_by(MasterNode=1).first() #TODO -> curerntly only generates config file for master node
		if qESCore is None:
			response = jsonify({"Status": "No master ES instances found!"})
			response.status_code = 500
			return response
		try:
			esCoreUrl='http://' + qESCore.hostIP + ':' + str(qESCore.nodePort)
			r = requests.get(esCoreUrl, timeout=2) #timeout in seconds
		except:
			response = jsonify({"Error": "Master ES instances not reachable!"})
			response.status_code = 500
			return response

		rsp = r.json()
		rspES = {'ElasticSearch': rsp}
		rspLS = {'Logstash': {'Status': 'Running', 'Version': '1.5.4'}} # TODO
		rspKB = {'Kibana': {'Status': 'Running', 'Version': '4.3.1'}} # TODO

		rspD.update(rspES)
		rspD.update(rspLS) #TODO
		rspD.update(rspKB) #TODO
		response = jsonify(rspD)
		response.status_code = 200
		return response

@dmon.route('/v1/overlord/core/chef')
class ChefClientStatus(Resource):
	def get(self):
		return "Monitoring Core Chef Client status"

@dmon.route('/v1/overlord/nodes/chef')
class ChefClientNodes(Resource):
	def get(self):
		return "Chef client status of monitored Nodes"


@dmon.route('/v1/overlord/nodes') #TODO -checkOS and -checkRoles
class MonitoredNodes(Resource):
	def get(self):
		nodeList = []
		nodesAll=db.session.query(dbNodes.nodeFQDN,dbNodes.nodeIP).all()
		if nodesAll is None:
			response = jsonify({'Status':'No monitored nodes found'})
			response.status_code = 404
			return response
		for nl in nodesAll:
			nodeDict= {}
			print >>sys.stderr, nl[0]
			nodeDict.update({nl[0]:nl[1]})
			nodeList.append(nodeDict)
		response = jsonify({'Nodes':nodeList})
		response.status_code=200
		return response

	@api.expect(nodeSubmit)	
	def put(self):
		if not request.json:
			abort(400)
		listN = []
		for nodes in request.json['Nodes']:
			qNodes = dbNodes.query.filter_by(nodeFQDN=nodes['NodeName']).first()
			if qNodes is None:
				e = dbNodes(nodeFQDN=nodes['NodeName'], nodeIP=nodes['NodeIP'], nodeOS=nodes['NodeOS'],
					nkey=nodes['key'], nUser=nodes['username'], nPass=nodes['password'])
				db.session.add(e)
			else:
				qNodes.nodeIP = nodes['NodeIP']
				qNodes.nodeOS = nodes['NodeOS']
				qNodes.nkey = nodes['key']
				qNodes.nUser = nodes['username']
				qNodes.nPass = nodes['password']
				db.session.add(qNodes)
			db.session.commit
		response = jsonify({'Status': "Nodes list Updated!"})
		response.status_code = 201
		return response	

	def post(self):
		return "Bootstrap monitoring"


@dmon.route('/v1/overlord/nodes/roles')
class ClusterRoles(Resource):
	def get(self):
		nodeList = []
		nodesAll=db.session.query(dbNodes.nodeFQDN, dbNodes.nRoles).all()
		if nodesAll is None:
			response = jsonify({'Status': 'No monitored nodes found'})
			response.status_code = 404
			return response
		for nl in nodesAll:
			nodeDict= {}
			print >>sys.stderr, nl[0]
			nodeDict.update({nl[0]: nl[1].split(',')})
			nodeList.append(nodeDict)
		response = jsonify({'Nodes': nodeList})
		response.status_code = 200
		return response

	@api.expect(listNodeRoles)
	def put(self):
		if not request.json or not "Nodes" in request.json:
			response = jsonify({'Status': 'Mimetype Error',
								'Message': 'Only JSON requests are permitted'})
			response.status_code = 400
			return response

		nList = request.json["Nodes"]

		for n in nList:
			#print n["NodeName"]
			#print n["Roles"]
			upRoles = dbNodes.query.filter_by(nodeFQDN=n["NodeName"]).first()
			if upRoles is None:
				response = jsonify({'Status': 'Node Name Error',
									'Message': 'Node' + n["NodeName"] + ' not found!'})
				response.status_code = 404
				return response
			upRoles.nRoles = ', '.join(map(str, n["Roles"]))

		response = jsonify({'Status': 'Done',
							'Message': 'All roles updated!'})

		response.status_code = 201
		return response


	def post(self):
		nodes = db.session.query(dbNodes.nodeFQDN, dbNodes.nodeIP, dbNodes.nUser, dbNodes.nPass, dbNodes.nRoles).all()
		if nodes is None:
			response = jsonify({'Status': 'No monitored nodes found'})
			response.status_code = 404
			return response

		yarnList = []
		sparkList = []
		stormList = []
		unknownList = []	
		for node in nodes:
			roleList = node[4].split(',')
			if 'yarn' in roleList or 'hdfs' in roleList:
				yarnPropertiesLoc = os.path.join(tmpDir, 'hadoop-metrics2.tmp')
				nl = []
				nl.append(node[1])
				uploadFile(nl, node[2], node[3], yarnPropertiesLoc, 'hadoop-metrics2.tmp', '/etc/hadoop/conf.cloudera.yarn/hadoop-metrics2.properties')  # TODO better solution
				uploadFile(nl, node[2], node[3], yarnPropertiesLoc, 'hadoop-metrics2.tmp', '/etc/hadoop/conf.cloudera.hdfs/hadoop-metrics2.properties')  # TODO better solution
				uploadFile(nl, node[2], node[3], yarnPropertiesLoc, 'hadoop-metrics2.tmp', '/etc/hadoop/conf/hadoop-metrics2.properties')  # TODO better solution
				yarnList.append(node[0])
			if 'spark' in roleList:  # TODO Same as /v1/overlord/framework/<fwork>, needs unification
				templateLoader = jinja2.FileSystemLoader( searchpath="/")
				templateEnv = jinja2.Environment(loader=templateLoader)
				propSparkTemp= os.path.join(tmpDir, 'metrics/spark-metrics.tmp')
				propSparkFile = os.path.join(cfgDir, 'metrics.properties')
				try:
					template = templateEnv.get_template(propSparkTemp)
				except:
					response = jsonify({'Status':'I/O Error', 'Message': 'Template file missing!'})
					response.status_code = 500
					return response

				qLSCore = dbSCore.query.first() #TODO: Only works for single deployment
				if qLSCore is None:
					response = jsonify({'Status':'Missing Instance','Message':'No Logstash Instance Configured'})
					response.status_code = 404
					return response
				infoSpark = {'logstashserverip':qLSCore.hostIP, 'logstashportgraphite': '5002', 'period': '10'}
				propSparkInfo=template.render(infoSpark)
				propSparkConf = open(propSparkFile,"w+")
				propSparkConf.write(propSparkInfo)
				propSparkConf.close()

				nl = []
				nl.append(node[1])
				uploadFile(nl,node[2],node[3],propSparkFile, 'metrics.properties', '/etc/spark/conf/metrics.properties')  # TODO better solution
				sparkList.append(node[0])
			if 'storm' in roleList:
				stormList.append(node[0]) # TODO
			
			if 'unknown' in roleList:
				unknownList.append(node[0])

		response = jsonify({'Status': {'yarn': yarnList, 'spark': sparkList, 'storm': stormList, 'unknown': unknownList}})
		response.status_code = 200
		return response


@dmon.route('/v1/overlord/nodes/<nodeFQDN>')
@api.doc(params={'nodeFQDN':'Nodes FQDN'})
class MonitoredNodeInfo(Resource):
	def get(self, nodeFQDN):
		qNode = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
		if qNode is None:
			response = jsonify({'Status': 'Node ' + nodeFQDN + ' not found!'})
			response.status_code = 404
			return response
		else:
			response = jsonify({
				'NodeName': qNode.nodeFQDN,
				'Status': qNode.nStatus,
				'IP': qNode.nodeIP,
				'Monitored': qNode.nMonitored,
				'OS': qNode.nodeOS,
				'Key': qNode.nkey,
				'Password': qNode.nPass,
				'User': qNode.nUser,
				'ChefClient': "TODO",
				'CDH': 'TODO',
				'Roles': qNode.nRoles})
			response.status_code = 200	
			return response

	@api.expect(nodeUpdate)	
	def put(self, nodeFQDN):
		if not request.json:
			abort(400)
		qNode = dbNodes.query.filter_by(nodeFQDN = nodeFQDN).first()
		if qNode is None:
			response = jsonify({'Status':'Node ' +nodeFQDN+' not found!'})
			response.status_code = 404
			return response
		else:
			qNode.nodeIP = request.json['IP']
			qNode.nodeOS = request.json['OS']
			qNode.nkey = request.json['Key']
			qNode.nPass = request.json['Password']
			qNode.nUser = request.json['User']
			response = jsonify({'Status': 'Node ' + nodeFQDN + ' updated!'})
			response.status_code = 201
			return response

	def post(self, nodeFQDN):
		return "Bootstrap specified node!"	

	def delete(self, nodeFQDN):
		dNode = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
		if dNode is None:
			response = jsonify({'Status': 'Node ' + nodeFQDN + ' not found'})
			response.status_code = 404
			return response
		dlist = []
		dlist.append(dNode.nodeIP)
		try:
			serviceCtrl(dlist, dNode.nUser, dNode.nPass, 'collectd', 'stop')
		except Exception as inst:
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args
			response = jsonify({'Error': 'Collectd stopping error!'})
			response.status_code = 500
			return response

		try:
			serviceCtrl(dlist, dNode.nUser, dNode.nPass, 'logstash-forwarder', 'stop')
		except Exception as inst:
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args
			response = jsonify({'Error': 'LSF stopping error!'})
			response.status_code = 500
			return response
		dNode.nMonitored = 0
		dNode.nCollectdState = 'Stopped'
		dNode.nLogstashForwState = 'Stopped'
		response =jsonify({'Status': 'Node ' + nodeFQDN + ' monitoring stopped!'})
		response.status_code = 200
		return response


@dmon.route('/v1/overlord/nodes/<nodeFQDN>/roles')
class ClusterNodeRoles(Resource):
	@api.expect(nodeRoles)	
	def put(self, nodeFQDN):  # TODO validate role names
		qNode = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
		if qNode is None:
			response = jsonify({'Status': 'Node ' + nodeFQDN + ' not found'})
			response.status_code = 404
			return response	
		else:
			listRoles = request.json['Roles']
			qNode.nRoles = ', '.join(map(str, listRoles))
			response = jsonify({'Status': 'Node ' + nodeFQDN + ' roles updated!'})
			response.status_code = 201
			return response

	def post(self,nodeFQDN):
		return 'Redeploy configuration for node ' + nodeFQDN + '!'


@dmon.route('/v1/overlord/nodes/<nodeFQDN>/purge')
@api.doc(params={'nodeFQDN': 'Nodes FQDN'})
class PurgeNode(Resource):
	def delete(self, nodeFQDN):
		qPurge = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
		if qPurge is None:
			abort(404)

		lPurge = []
		lPurge.append(qPurge.nodeIP)
		try:
			serviceCtrl(lPurge, qPurge.uUser, qPurge.uPass, 'logstash-forwarder', 'stop')
		except Exception as inst:
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args
			response = jsonify({'Error': 'Stopping LSF!'})
			response.status_code = 500
			return response

		try:
			serviceCtrl(lPurge,qPurge.uUser,qPurge.uPass,'collectd', 'stop')
		except Exception as inst:
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args
			response = jsonify({'Error':'Stopping collectd!'})
			response.status_code = 500
			return response
				
		db.session.delete(qPurge)
		db.session.commit()
		response = jsonify({'Status': 'Node ' + nodeFQDN + ' deleted!'})
		response.status_code = 200
		return response




@dmon.route('/v1/overlord/core/es/config')#TODO use args for unsafe cfg file upload
class ESCoreConfiguration(Resource):
	def get(self): #TODO same for all get config file createfunction
		if not os.path.isdir(cfgDir):
			response = jsonify({'Error': 'Config dir not found !'})
			response.status_code = 404
			return response
		if not os.path.isfile(os.path.join(cfgDir, 'elasticsearch.yml')):
			response = jsonify({'Status': 'Config file not found !'})
			response.status_code = 404
			return response
		try:
			esCfgfile = open(os.path.join(cfgDir, 'elasticsearch.yml'), 'r')
		except EnvironmentError:
			response = jsonify({'EnvError': 'file not found'})
			response.status_code = 500
			return response

		return send_file(esCfgfile, mimetype='text/yaml', as_attachment=True)

	@api.expect(esCore)	
	def put(self):
		requiredKeys=['ESClusterName', 'HostFQDN', 'IP', 'NodeName', 'NodePort']
		if not request.json:
			abort(400)
		for key in requiredKeys:
			if key not in request.json:
				response = jsonify({'Error': 'malformed request, missing key(s)'})
				response.status_code = 400
				return response 
		test = db.session.query(dbESCore.hostFQDN).all()
		if not test:
			master = 1
		else:
			master = 0
				
		qESCore = dbESCore.query.filter_by(hostIP = request.json['IP']).first()
		if request.json["OS"] is None:
			os = "unknown"
		else:
			os=request.json["OS"]

		if qESCore is None:
			upES = dbESCore(hostFQDN=request.json["HostFQDN"],hostIP = request.json["IP"],hostOS=os, nodeName = request.json["NodeName"],
			 clusterName=request.json["ESClusterName"], conf = 'none', nodePort=request.json['NodePort'], MasterNode=master)
			db.session.add(upES) 
			db.session.commit()
			response = jsonify({'Added':'ES Config for '+ request.json["HostFQDN"]})
			response.status_code = 201
			return response
		else:
			#qESCore.hostFQDN =request.json['HostFQDN'] #TODO document hostIP and FQDN may not change in README.md
			qESCore.hostOS = os
			qESCore.nodename = request.json['NodeName']
			qESCore.clusterName=request.json['ESClusterName']
			qESCore.nodePort=request.json['NodePort']
			db.session.commit()
			response=jsonify({'Updated':'ES config for '+ request.json["HostFQDN"]})
			response.status_code = 201
			return response

@dmon.route('/v1/overlord/core/es/<hostFQDN>')
@api.doc(params={'hostFQDN':'Host FQDN.'})
class ESCoreRemove(Resource):
	def delete(self,hostFQDN):
		qESCorePurge = dbESCore.query.filter_by(hostFQDN = hostFQDN).first()
		if qESCorePurge is None:
			response =  jsonify({'Status':'Unknown host '+hostFQDN})
			response.status_code = 404
			return response

		os.kill(qESCorePurge.ESCorePID, signal.SIGTERM)

		db.session.delete(qESCorePurge)
		db.session.commit()
		response = jsonify ({'Status':'Deleted ES at host '+hostFQDN})
		response.status_code = 200
		return response

@dmon.route('/v1/overlord/core/ls/<hostFQDN>')
@api.doc(params={'hostFQDN': 'Host FQDN.'})
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
		hostsAll=db.session.query(dbESCore.hostFQDN,dbESCore.hostIP,dbESCore.hostOS,dbESCore.nodeName,dbESCore.nodePort,
			dbESCore.clusterName,dbESCore.ESCoreStatus, dbESCore.ESCorePID,dbESCore.MasterNode).all()
		resList=[]
		for hosts in hostsAll:
			confDict={}
			confDict['HostFQDN']=hosts[0]
			confDict['IP']=hosts[1]
			confDict['OS']=hosts[2]
			confDict['NodeName']=hosts[3]
			confDict['NodePort']=hosts[4]
			confDict['ESClusterName']=hosts[5]
			confDict['Status']=hosts[6]
			confDict['PID']=hosts[7]
			confDict['Master']=hosts[8]
			resList.append(confDict)
		response = jsonify({'ES Instances':resList})
		response.status_code = 200
		return response

	def post(self):
		templateLoader = jinja2.FileSystemLoader( searchpath="/" )
		templateEnv = jinja2.Environment( loader=templateLoader )
		esTemp= os.path.join(tmpDir,'elasticsearch.tmp')#tmpDir+"/collectd.tmp"
		esfConf = os.path.join(cfgDir,'elasticsearch.yml')
		qESCore = dbESCore.query.filter_by(MasterNode = 1).first() #TODO -> curerntly only generates config file for master node
		if qESCore is None:
			response = jsonify({"Status":"No master ES instances found!"})
			response.status_code = 500
			return response

		if checkPID(qESCore.ESCorePID) is True:
			subprocess.call(["kill", "-9", str(qESCore.ESCorePID)])

		try:
			template = templateEnv.get_template( esTemp )
			#print >>sys.stderr, template
		except:
			return "Tempalte file unavailable!"

		infoESCore = {"clusterName":qESCore.clusterName,"nodeName":qESCore.nodeName, "esLogDir":logDir}			
		esConf = template.render(infoESCore)
		qESCore.conf = esConf
		#print >>sys.stderr, esConf
		db.session.commit()
		esCoreConf = open(esfConf,"w+")
		esCoreConf.write(esConf)
		esCoreConf.close()

		#TODO find better solution
		os.system('rm -rf /opt/elasticsearch/config/elasticsearch.yml')
		os.system('cp '+esfConf+' /opt/elasticsearch/config/elasticsearch.yml ')
		
		esPid = 0
		try:
			esPid = subprocess.Popen('/opt/elasticsearch/bin/elasticsearch', stdout=subprocess.PIPE).pid #TODO: Try -p to set pid file location
		except Exception as inst:
			print >> sys.stderr, 'Error while starting elasticsearch'
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args
		qESCore.ESCorePID = esPid
		#ES core pid location
		pidESLoc = os.path.join(pidDir,'elasticsearch.pid')
		try:
			esPIDFile = open(pidESLoc,'w+')
			esPIDFile.write(str(esPid))
			esPIDFile.close()
		except IOError:
			response = jsonify({'Error':'File I/O!'})
			response.status_code = 500
			return response
		response = jsonify({'Status':'ElasticSearch Core  PID '+str(esPid)})
		response.status_code = 200
		return response
		

@dmon.route('/v1/overlord/core/kb/config')
class KBCoreConfiguration(Resource):
	def get(self):
		if not os.path.isdir(cfgDir):
			response = jsonify({'Error':'Config dir not found !'})
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

	@api.expect(kbCore)#TODO same for all 3 core services create one class for all
	def put(self):
		requiredKeys=['HostFQDN', 'IP']
		if not request.json:
			abort(400)
		for key in requiredKeys:
			if key not in request.json:
				response = jsonify({'Error':'malformed request, missing key(s)'})
				response.status_code = 400
				return response 
				
		qKBCore = dbKBCore.query.filter_by(hostIP = request.json['IP']).first()
		if request.json["OS"] is None:
			os = "unknown"
		else:
			os=request.json["OS"]

		if qKBCore is None:
			upKB = dbKBCore(hostFQDN=request.json["HostFQDN"],hostIP = request.json["IP"],hostOS=os, kbPort = request.json["KBPort"],KBCoreStatus = 'Stopped')
			db.session.add(upKB) 
			db.session.commit()
			response = jsonify({'Added':'KB Config for '+ request.json["HostFQDN"]})
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
		resList=[]
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
		kbTemp= os.path.join(tmpDir, 'kibana.tmp')#tmpDir+"/collectd.tmp"
		kbfConf = os.path.join(cfgDir, 'kibana.yml')
		qKBCore = dbKBCore.query.first() # TODO: only one instance is supported
		if qKBCore is None:
			response = jsonify({"Status": "No KB instance found!"})
			response.status_code = 500
			return response

		if checkPID(qKBCore.KBCorePID) is True:
			subprocess.call(["kill", "-9", str(qKBCore.KBCorePID)])

		try:
			template = templateEnv.get_template(kbTemp)
			#print >>sys.stderr, template
		except:
			return "Tempalte file unavailable!"

		#Log and PID location for kibana
		
		kbPID = os.path.join(pidDir, 'kibana.pid')
		kbLog = os.path.join(logDir, 'kibana.log')

		infoKBCore = {"kbPort": qKBCore.kbPort, "kibanaPID": kbPID, "kibanaLog": kbLog}
		kbConf = template.render(infoKBCore)
		qKBCore.conf = kbConf
		#print >>sys.stderr, esConf
		db.session.commit()
		kbCoreConf = open(kbfConf, "w+")
		kbCoreConf.write(kbConf)
		kbCoreConf.close()

		#TODO find better solution
		os.system('rm -rf /opt/kibana/config/kibana.yml')
		os.system('cp '+kbfConf+' /opt/kibana/config/kibana.yml ')
		
		kbPid = 0
		FNULL = open(os.devnull, 'w')
		try:
			kbPid = subprocess.Popen('/opt/kibana/bin/kibana', stdout=FNULL, stderr=subprocess.STDOUT).pid
		except Exception as inst:
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args
		qKBCore.KBCorePID = kbPid
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

		if qSCore is None:
			upS = dbSCore(hostFQDN=request.json["HostFQDN"], hostIP=request.json["IP"],hostOS=os,
			 outESclusterName=request.json["ESClusterName"], udpPort = request.json["udpPort"], inLumberPort=request.json['LPort'])
			db.session.add(upS) 
			db.session.commit()
			response = jsonify({'Added': 'LS Config for ' + request.json["HostFQDN"]})
			response.status_code = 201
			return response
		else:
			#qESCore.hostFQDN =request.json['HostFQDN'] #TODO document hostIP and FQDN may not change in README.md
			qSCore.hostOS = os
			qSCore.outESclusterName = request.json['ESClusterName']
			qSCore.udpPort = request.json['udpPort']
			qSCore.inLumberPort = request.json['LPort']
			db.session.commit()
			response = jsonify({'Updated': 'LS config for ' + request.json["HostFQDN"]})
			response.status_code = 201
			return response
		#return "Changes configuration fo logstash server"


@dmon.route('/v1/overlord/core/ls')
class LSCoreController(Resource):
	def get(self):
		hostsAll = db.session.query(dbSCore.hostFQDN,dbSCore.hostIP,dbSCore.hostOS,dbSCore.inLumberPort,
			dbSCore.sslCert, dbSCore.sslKey, dbSCore.udpPort, dbSCore.outESclusterName, dbSCore.LSCoreStatus).all()
		resList = []
		for hosts in hostsAll:
			confDict = {}
			confDict['HostFQDN'] = hosts[0]
			confDict['IP'] = hosts[1]
			confDict['OS'] = hosts[2]
			confDict['LPort'] = hosts[3]
			confDict['udpPort'] = hosts[6]
			confDict['ESClusterName'] = hosts[7]
			confDict['Status'] = hosts[8]
			resList.append(confDict)
		response = jsonify({'LS Instances': resList})
		response.status_code = 200
		return response

	def post(self):
		templateLoader = jinja2.FileSystemLoader(searchpath="/")
		templateEnv = jinja2.Environment(loader=templateLoader)
		lsTemp = os.path.join(tmpDir, 'logstash.tmp')#tmpDir+"/collectd.tmp"
		lsfCore = os.path.join(cfgDir, 'logstash.conf')
		#qSCore = db.session.query(dbSCore.hostFQDN).first()
		qSCore = dbSCore.query.first()# TODO: currently only one LS instance supported
		#return qSCore
		if qSCore is None:
			response = jsonify({"Status": "No LS instances registered"})
			response.status_code = 500
			return response

		if checkPID(qSCore.LSCorePID) is True:
			subprocess.call(['kill', '-9', str(qSCore.LSCorePID)])

		try:
			template = templateEnv.get_template(lsTemp)
			#print >>sys.stderr, template
		except Exception as inst:
			return "LS Tempalte file unavailable!"
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args

		if qSCore.sslCert == 'default':
			certLoc = os.path.join(credDir, 'logstash-forwarder.crt')
		else:
			certLoc = os.path.join(credDir, qSCore.sslCert + '.crt')


		if qSCore.sslKey == 'default':
			keyLoc = os.path.join(credDir, 'logstash-forwarder.key')
		else:
			keyLoc = os.path.join(credDir, qSCore.sslKey + '.key')

		infoSCore = {"sslcert": certLoc, "sslkey": keyLoc, "udpPort": qSCore.udpPort, "ESCluster":qSCore.outESclusterName}
		sConf = template.render(infoSCore)
		qSCore.conf = sConf
		#print >>sys.stderr, esConf
		db.session.commit()

		lsCoreConf = open(lsfCore, "w+")
		lsCoreConf.write(sConf)
		lsCoreConf.close()

		#TODO find better solution
		#subprocess.call(['cp',lsfCore,lsCDir+'/logstash.conf'])
		lsLogfile = os.path.join(logDir, 'logstash.log')
		lsPid = 0
		try:
			lsPid = subprocess.Popen('/opt/logstash/bin/logstash agent  -f ' + lsfCore + ' -l ' + lsLogfile + ' -w 4', shell=True).pid
		except Exception as inst:
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args		
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

		response = jsonify({'Status': 'Logstash Core PID ' + str(lsPid)})
		response.status_code = 200
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
			print >>sys.stderr, nl[0]
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
	def get(self,certName):
		qSCoreCert = dbSCore.query.filter_by(sslCert = certName).all()
		certList = []
		for i in qSCoreCert:
			certList.append(i.hostFQDN)

		if not certList:
			response = jsonify({'Status':certName+' not found!'})
			response.status_code = 404
			return response
		else:
			response = jsonify({'Hosts':certList})
			response.status_code =200
			return response

@dmon.route('/v1/overlord/core/ls/cert/<certName>/<hostFQDN>')
@api.doc(params={'certName': 'Name of the certificate',
	'hostFQDN':'Host FQDN'})
class LSCertControl(Resource):
	@api.expect(certModel)	#TODO FIX THIS
	def put(self,certName,hostFQDN):
		if request.headers['Content-Type'] == 'application/x-pem-file':
			pemData = request.data
		else:
			abort(400)
		qSCoreCert = dbSCore.query.filter_by(hostFQDN = hostFQDN).first()
		if qSCoreCert is None:
			response=jsonify({'Status':'unknown host'})
			response.status_code = 404
			return response
		else:
			if certName == 'default':
				crtFile = os.path.join(credDir,'logstash-forwarder.crt')
			else:
				crtFile = os.path.join(credDir,certName+'.crt')
			try:
				cert = open(crtFile,'w+')
				cert.write(pemData)
				cert.close()
			except IOError:
				response = jsonify({'Error':'File I/O!'})
				response.status_code = 500
				return response	

		qSCoreCert.sslCert = certName
		response = jsonify({'Status':'updated certificate!'})
		response.status_code=201
		return response

@dmon.route('/v1/overlord/core/ls/key/<keyName>')
@api.doc(params={'keyName': 'Name of the private key.'})
class LSKeyQuery(Resource):
	def get(self, keyName):
		if keyName == 'default':
			response = jsonify({'Key' : 'default'})
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
@api.doc(params={'keyName': 'Name of the private key.','hostFQDN':'Host FQDN'})
class LSKeyControl(Resource):
	def put(self,keyName, hostFQDN):
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
		qNodes=db.session.query(dbNodes.nodeFQDN, dbNodes.nodeIP, dbNodes.nMonitored,
			dbNodes.nCollectdState, dbNodes.nLogstashForwState).all()
		mnList = []
		for nm in qNodes:
			mNode = {}
			mNode['NodeFQDN'] = nm[0]
			mNode['NodeIP'] = nm[1]
			mNode['Monitored'] = nm[2]
			mNode['Collectd'] = nm[3]
			mNode['LSF'] = nm[4]
			mnList.append(mNode)
			#print >> sys.stderr, nm
		response = jsonify({'Aux Status': mnList})
		response.status_code = 200
		return response

	@api.doc(parser=dmonAuxAll)#TODO Status handling (Running, Stopped, None )Needs Checking 
	def post(self): #TODO currently works only if the same username and password is used for all Nodes
		templateLoader = jinja2.FileSystemLoader(searchpath="/")
		templateEnv = jinja2.Environment(loader=templateLoader)
		lsfTemp= os.path.join(tmpDir, 'logstash-forwarder.tmp')#tmpDir+"/collectd.tmp"
		collectdTemp = os.path.join(tmpDir, 'collectd.tmp')
		collectdConfLoc = os.path.join(cfgDir, 'collectd.conf')
		lsfConfLoc = os.path.join(cfgDir, 'logstash-forwarder.conf')
		qNodes = db.session.query(dbNodes.nodeFQDN, dbNodes.nMonitored,
			dbNodes.nCollectdState, dbNodes.nLogstashForwState, dbNodes.nUser, dbNodes.nPass, dbNodes.nodeIP).all()
		result = []
		credentials ={}
		for n in qNodes:
			credentials['User'] = n[4] #TODO need a more elegant solution, currently it is rewriten every iteration
			credentials['Pass'] = n[5]
			print >> sys.stderr, credentials
			rp = {}
			if n[1] == False: #check if node is monitored
				rp['Node'] = n[0]
				rp['Collectd']=n[2]
				rp['LSF']=n[3]
				rp['IP']=n[6]
				#rp['User']=n[4]
				#rp['Pass']=n[5]
				result.append(rp) 
		collectdList=[]
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

		if args == 'redeploy-all': #TODO check if conf files exist if not catch error
			uploadFile(allNodes, credentials['User'], credentials['Pass'], collectdConfLoc, 'collectd.conf', '/etc/collectd/collectd.conf')
			uploadFile(allNodes, credentials['User'], credentials['Pass'], lsfConfLoc, 'logstash-forwarder.conf', '/etc/logstash-forwarder.conf')
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

		qSCore = dbSCore.query.first() #TODO Change for distributed deployment
		if qSCore is None:
			response = jsonify({'status': 'db empty',
								'message': 'there is no logstash instance registered!'})
			response.status_code = 400
			return response
		try:
			lsfTemplate = templateEnv.get_template(lsfTemp)
			#print >>sys.stderr, template
		except:
			return "Tempalte file unavailable!"

		#{{ESCoreIP}}:{{LSLumberPort}}	
		infolsfAux = {"ESCoreIP": qSCore.hostIP, "LSLumberPort": qSCore.inLumberPort}
		lsfConf = lsfTemplate.render(infolsfAux)
		
		lsfConfFile = open(lsfConfLoc, "wb") #TODO trycatch
		lsfConfFile.write(lsfConf)
		lsfConfFile.close()

		#{{logstash_server_ip}}" "{{logstash_server_port}}
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
		except Exception as inst:    # TODO if exceptions is detected check to see if collectd started if not return fail if yes return warning
			print >> sys.stderr, type(inst) 
			print >> sys.stderr, inst.args
			response = jsonify({'Status': 'Error Installing collectd!'})
			response.status_code = 500
			return response

		try:
			installLogstashForwarder(LSFList, userName=credentials['User'], uPassword=credentials['Pass'], confDir=cfgDir)
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
		try:
			deployAgent(noAgent, user, password)
		except Exception as inst:
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args
			response = jsonify({'Status': 'Agent Error',
								'Message': 'Error while deploying agent!'})
			response.status_code = 500
			return response


		for a in noAgent:
			updateAll = dbNodes.query.filter_by(nodeIP=a).first()
			updateAll.nStatus = 1


		response = jsonify ({'Status': 'Done',
							 'Message': 'Agents Deloyed!'})
		response.status_code = 201
		return response


@dmon.route('/v2/overlord/aux/deploy')  # TODO: gets current status of aux components and deploy them based on roles
class AuxDeployThread(Resource):
	def get(self):
		qNodes=db.session.query(dbNodes.nodeFQDN, dbNodes.nodeIP, dbNodes.nMonitored,
			dbNodes.nCollectdState, dbNodes.nLogstashForwState).all()
		mnList = []
		for nm in qNodes:
			mNode = {}
			mNode['NodeFQDN'] = nm[0]
			mNode['NodeIP'] = nm[1]
			mNode['Monitored'] = nm[2]
			mNode['Collectd'] = nm[3]
			mNode['LSF'] = nm[4]
			mnList.append(mNode)
			#print >> sys.stderr, nm
		response = jsonify({'Aux Status': mnList})
		response.status_code = 200
		return response

	def put(self): #TODO: used to enact new configurations
		return "Reload new Configuration"

	def post(self):
		qNodes=db.session.query(dbNodes.nodeIP, dbNodes.nRoles).all()
		nrList = []
		for nr in qNodes:
			nrNode = {}
			nrNode[nr[0]] = nr[1].split(',')
			nrList.append(nrNode)

		resFin = {}
		for e in nrList:
			for k, v in e.iteritems():
				nodeList = []
				nodeList.append(k)
				agentr = AgentResourceConstructor(nodeList, '5000')
				resourceList = agentr.deploy()
				r = {'roles': v}
				resFin[resourceList[-1]] = r

		dmon = GreenletRequests(resFin)
		nodeRes = dmon.parallelPost(None)

		failedNodes = []
		NodeDict = {}
		for n in nodeRes:
			nodeIP = urlparse(n['Node'])
			qNode = dbNodes.query.filter_by(nodeIP=nodeIP.hostname).first()
			qNode.nStatus = 1  # TODO: Recheck nStatus and nMonitored roles when are they true and when are they false
			if n['StatusCode'] != 201:
				failedNodes.append({'NodeIP': str(nodeIP.hostname),
									'Code': n['StatusCode']})
			NodeDict[nodeIP.hostname] = n['Data']['Components']
		response = jsonify({'Status': 'Installed Aux ',
							'Message': NodeDict,
							'Failed': failedNodes})
		response.status_code = 200

		dmon.reset()

		return response


@dmon.route('/v2/overlord/aux/deploy/check')  #   TODO: polls all dmon-agents for current status
class AuxDeployCheckThread(Resource):
	def get(self):
		agentPort = '5000'
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

		response=jsonify({'Status': 'Update',
						  'Message': 'Nodes updated!',
						  'Failed':failedNodes})
		response.status_code = 200

		dmon.reset()

		return response


@dmon.route('/v1/overlord/aux/deploy/<auxComp>/<nodeFQDN>')#TODO check parameter redeploy functionality 
@api.doc(params={'auxComp': 'Aux Component', 'nodeFQDN': 'Node FQDN'})#TODO document nMonitored set to true when first started monitoring
class AuxDeploySelective(Resource):
	@api.doc(parser=dmonAux)
	def post(self, auxComp, nodeFQDN):
		auxList = ['collectd', 'lsf']
		#status = {}
		if auxComp not in auxList:
			response = jsonify({'Status': 'No such such aux component ' + auxComp})
			response.status_code = 400
			return response
		qAux = dbNodes.query.filter_by(nodeFQDN=nodeFQDN).first()
		if qAux is None:
			response = jsonify({'Status':'Unknown node ' + nodeFQDN})
			response.status_code=404
			return response

		args = dmonAux.parse_args()
		
		node = []
		node.append(qAux.nodeIP)
		if auxComp == 'collectd':
			if args == 'redeploy':
				if qAux.nCollectdState != 'Running':
					response = jsonify({'Status:No collectd instance to restart!'})
					response.status_code=404
					return response 
				try:
					serviceCtrl(node,qAux.nUser,qAux.nPass,'collectd', 'restart')
				except Exception as inst:
					print >> sys.stderr, type(inst)
					print >> sys.stderr, inst.args
					response = jsonify({'Status':'Error restarting Collectd on '+ nodeFQDN +'!'})
					response.status_code = 500
					return response
				response = jsonify({'Status':'Collectd restarted on '+nodeFQDN})
				response.status_code = 200
				return response
			if qAux.nCollectdState == 'None':
				try:
					installCollectd(node,qAux.nUser,qAux.nPass,confDir=cfgDir)
				except Exception as inst:
					print >> sys.stderr, type(inst)
					print >> sys.stderr, inst.args
					response = jsonify({'Status':'Error Installig Collectd on '+ qAux.nodeFQDN +'!'})
					response.status_code = 500
					return response
				#status[auxComp] = 'Running'	
				qAux.nCollectdState = 'Running'
				response = jsonify({'Status':'Collectd started on '+nodeFQDN+'.'})
				response.status_code = 201
				return response
			else:
				response = jsonify({'Status':'Node '+ nodeFQDN +' collectd already started!' })
				response.status_code = 200
				return response 
		elif auxComp == 'lsf':
			if args == 'redeploy':
				if qAux.nLogstashForwState != 'Running':
					response = jsonify({'Status:No LSF instance to restart!'})
					response.status_code=404
					return response 
				try:
					serviceCtrl(node,qAux.nUser,qAux.nPass,'logstash-forwarder', 'restart')
				except Exception as inst:
					print >> sys.stderr, type(inst)
					print >> sys.stderr, inst.args
					response = jsonify({'Status':'Error restarting LSF on '+ nodeFQDN +'!'})
					response.status_code = 500
					return response
				response = jsonify({'Status':'LSF restarted on '+nodeFQDN})
				response.status_code = 200
				return response
			if qAux.nLogstashForwState == 'None':
				try:
					installLogstashForwarder(node,qAux.nUser,qAux.nPass,confDir=cfgDir)
				except Exception as inst:
					print >> sys.stderr, type(inst)
					print >> sys.stderr, inst.args
					response = jsonify({'Status':'Error Installig LSF on '+qAux.nodeFQDN+'!'})
					response.status_code = 500
					return response
				#status[auxComp] = 'Running'	
				qAux.nLogstashForwState = 'Running'
				response = jsonify({'Status':'LSF started on '+nodeFQDN+'.'})
				response.status_code = 201
				return response
			else:
				response = jsonify({'Status':'Node '+ nodeFQDN +' LSF already started!' })
				response.status_code = 200
				return response


@dmon.route('/v2/overlord/aux/deploy/<auxComp>/<nodeFQDN>')  # TODO: deploy specific configuration on the specified node
@api.doc(params={'auxComp': 'Aux Component', 'nodeFQDN': 'Node FQDN'})
class AuxDeploySelectiveThread(Resource):
    def post(self, auxComp, nodeFQDN):
        return 'same as v1'


@dmon.route('/v1/overlord/aux/<auxComp>/config')
@api.doc(params={'auxComp': 'Aux Component'})
class AuxConfigSelective(Resource):
	def get(self, auxComp):
		allowed = ['collectd', 'lsf']
		if auxComp not in allowed:
			response = jsonify({'Status':'unrecognized aux component ' +auxComp})
			response.status_code = 404
			return response

		if not os.path.isdir(cfgDir):
			response = jsonify({'Error':'Config dir not found !'})
			response.status_code = 404
			return response

		if auxComp == 'collectd':
			if not os.path.isfile(os.path.join(cfgDir,'collectd.conf')):
				response = jsonify({'Error':'Config file not found !'})
				response.status_code = 404
				return response
			try:
				Cfgfile=open(os.path.join(cfgDir,'collectd.conf'),'r')
			except EnvironmentError:
				response = jsonify({'EnvError':'file not found'})
				response.status_code = 500
				return response
		
		if auxComp == 'lsf':
			if not os.path.isfile(os.path.join(cfgDir, 'logstash-forwarder.conf')):
				response = jsonify({'Error':'Config file not found !'})
				response.status_code = 404
				return response
			try:
				Cfgfile=open(os.path.join(cfgDir, 'logstash-forwarder.conf'), 'r')
			except EnvironmentError:
				response = jsonify({'EnvError':'file not found'})
				response.status_code = 500
				return response
		return send_file(Cfgfile, mimetype='text/plain', as_attachment=True)

	def put(self, auxComp):
		return "Sets configuration of aux components use parameters (args) -unsafe"


@dmon.route('/v1/overlord/aux/<auxComp>/start')
@api.doc(params={'auxComp':'Aux Component'})
class AuxStartAll(Resource):
	def post(self, auxComp): #TODO create function that can be reused for both start and stop of all components
		auxList = ['collectd','lsf']
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
					#response = jsonify({'Status':'Error Starting collectd on '+ i.nodeFQDN +'!'})
					#response.status_code = 500
					#return response

				CollectdNodes = {}
				CollectdNodes['Node'] = i.nodeFQDN
				CollectdNodes['IP'] = i.nodeIP
				nodeCollectdStopped.append(CollectdNodes)
				i.nCollectdState = 'Running'
			response = jsonify({'Status': 'Collectd started', 'Nodes': nodeCollectdStopped})
			response.status_code = 200
			return response

		if auxComp == "lsf":
			qNLsf = dbNodes.query.filter_by(nLogstashForwState = 'Stopped').all()
			if qNLsf is None:
				response = jsonify({'Status':'No nodes in state Stopped!'})
				response.status_code = 404
				return response

			nodeLsfStopped = []
			for i in qNLsf:
				node = []
				node.append(i.nodeIP)
				try:
					serviceCtrl(node,i.nUser,i.nPass,'logstash-forwarder', 'start')
				except Exception as inst:
					print >> sys.stderr, type(inst)
					print >> sys.stderr, inst.args
					response = jsonify({'Status':'Error Starting LSF on ' + i.nodeFQDN + '!'})
					response.status_code = 500
					return response

				LsfNodes = {}
				LsfNodes['Node'] = i.nodeFQDN
				LsfNodes['IP'] = i.nodeIP
				nodeLsfStopped.append(LsfNodes)
				i.nLogstashForwState = 'Running'
			response = jsonify({'Status':'LSF started','Nodes':nodeLsfStopped})
			response.status_code = 200
			return response	
			#return nodeCollectdStopped


@dmon.route('/v1/overlord/aux/<auxComp>/stop')#auxCtrl(auxComp,'stop') #TODO revise from pysshCore and make it work!
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
					response = jsonify({'Status':'Error Stopping collectd on ' + i.nodeFQDN + '!'})
					response.status_code = 500
					return response
				CollectdNodes = {}
				CollectdNodes['Node'] = i.nodeFQDN
				CollectdNodes['IP'] = i.nodeIP
				nodeCollectdRunning.append(CollectdNodes)
				i.nCollectdState = 'Stopped'
			response = jsonify({'Status':'Collectd stopped','Nodes':nodeCollectdRunning})
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
					serviceCtrl(node,i.nUser,i.nPass,'logstash-forwarder', 'stop')
				except Exception as inst:
					print >> sys.stderr, type(inst)
					print >> sys.stderr, inst.args
					response = jsonify({'Status':'Error Stopping LSF on '+ i.nodeFQDN +'!'})
					response.status_code = 500
					return response

				LsfNodes = {}
				LsfNodes['Node'] = i.nodeFQDN
				LsfNodes['IP'] = i.nodeIP
				nodeLsfRunning.append(LsfNodes)
				i.nLogstashForwState = 'Stopped'
			response = jsonify({'Status':'LSF stopped','Nodes':nodeLsfRunning})
			response.status_code = 200
			return response


@dmon.route('/v1/overlord/aux/<auxComp>/<nodeFQDN>/start')
@api.doc(params={'auxComp': 'Aux Component', 'nodeFQDN': 'Node FQDN'})
class AuxStartSelective(Resource):
 	def post(self, auxComp, nodeFQDN):
 		auxList = ['collectd','lsf']
 		if auxComp not in auxList:
			response = jsonify({'Status':'No such such aux component '+ auxComp})
			response.status_code = 400
			return response

		qAux =  dbNodes.query.filter_by(nodeFQDN = nodeFQDN).first()
		if qAux is None:
			response = jsonify({'Status':'Unknown node ' + nodeFQDN})
			response.status_code=404
			return response

		node = []
		node.append(qAux.nodeIP)		
		if auxComp == 'collectd':
			if qAux.nCollectdState != 'None': 
				try:
					serviceCtrl(node,qAux.nUser,qAux.nPass,'collectd', 'restart')
				except Exception as inst:
					print >> sys.stderr, type(inst)
					print >> sys.stderr, inst.args
					response = jsonify({'Status':'Error restarting collectd on '+ nodeFQDN +'!'})
					response.status_code = 500
					return response
				response = jsonify({'Status':'Collectd restarted on '+nodeFQDN})
				response.status_code = 200
				return response
			else:
				response=jsonify({'Status':'Need to deploy collectd first!'})
				response.status_code=403
				return response

		if auxComp == 'lsf':
			if qAux.nLogstashForwState != 'None': 
				try:
					serviceCtrl(node,qAux.nUser,qAux.nPass,'logstash-forwarder', 'restart')
				except Exception as inst:
					print >> sys.stderr, type(inst)
					print >> sys.stderr, inst.args
					response = jsonify({'Status':'Error restarting LSF on '+ nodeFQDN +'!'})
					response.status_code = 500
					return response
				response = jsonify({'Status':'LSF restarted on '+nodeFQDN})
				response.status_code = 200
				return response
			else:
				response=jsonify({'Status':'Need to deploy LSF first!'})
				response.status_code = 403
				return response


@dmon.route('/v1/overlord/aux/<auxComp>/<nodeFQDN>/stop')
@api.doc(params={'auxComp': 'Aux Component', 'nodeFQDN': 'Node FQDN'})
class AuxStopSelective(Resource):
	def post(self, auxComp, nodeFQDN):
		auxList = ['collectd', 'lsf']
 		if auxComp not in auxList:
			response = jsonify({'Status':'No such  aux component '+ auxComp})
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
				response = jsonify({'Status': 'LSF stopped on '+nodeFQDN})
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
			response = jsonify({'Status': 'Node ' + nodeFQDN +' not found!'})
			response.status_code = 404
			return response

		node = []
		node.append(qAux.nodeIP)
		agentr = AgentResourceConstructor(node, '5000')

		if auxComp == 'all':
			resourceList = agentr.start()
		else:
			resourceList = agentr.startSelective(auxComp)

		try:
			r = requests.post(resourceList[0])
			#data = r.text
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
			response = jsonify({'Status': 'Node ' + nodeFQDN +' not found!'})
			response.status_code = 404
			return response

		node = []
		node.append(qAux.nodeIP)
		agentr = AgentResourceConstructor(node, '5000')

		if auxComp == 'all':
			resourceList = agentr.stop()
		else:
			resourceList = agentr.stopSelective(auxComp)

		try:
			r = requests.post(resourceList[0])
			#data = r.text
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
		return "same as v1"  # TODO: stop selected component


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

		agentr = AgentResourceConstructor(nList, '5000')
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
			#print n['StatusCode']
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
			response = jsonify({'Status': 'No such such aux component ' + auxComp})
			response.status_code = 400
			return response
		qNodes = db.session.query(dbNodes.nodeIP).all()
		nList = []
		for n in qNodes:
			nList.append(n[0])

		agentr = AgentResourceConstructor(nList, '5000')
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
			#print n['StatusCode']
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

	#print >>sys.stderr, "Running as: %s:%s" % (os.getuid(), os.getgid())
	# testQuery = queryConstructor(1438939155342,1438940055342,"hostname:\"dice.cdh5.s4.internal\" AND serviceType:\"dfs\"")
	# metrics = ['type','@timestamp','host','job_id','hostname','AvailableVCores']
	# test, test2 = queryESCore(testQuery, debug=False)
	# print >>sys.stderr, test2
	if len(sys.argv) == 1:
		#esDir=
		#lsDir=
		#kibanaDir=
		app.run(port = 5001, debug=True, threaded=True)
	else:
		app.run(host='0.0.0.0', port=8080, debug = True)
