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
import os
import sys
import signal
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
import jinja2
import requests
import shutil
#from werkzeug import secure_filename #unused
#DICE Imports
from pyESController import *
from pysshCore import *
#from dbModel import *
from pyUtil import *


#directory Location
outDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
tmpDir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
cfgDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')
baseDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db')
pidDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pid')


esDir = '/opt/elasticsearch' #TODO: only provisory for testing


app = Flask("D-MON")
api = Api(app, version='0.1', title='DICE MOnitoring API',
    description='RESTful API for the DICE Monitoring Platform  (D-MON)',
)

db = SQLAlchemy(app)
#%--------------------------------------------------------------------%
class dbNodes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nodeFQDN = db.Column(db.String(64), index=True, unique=True)
    nodeIP = db.Column(db.String(64), index=True, unique=True)
    nodeUUID = db.Column(db.String(64), index=True, unique=True)
    nodeOS = db.Column(db.String(120), index=True, unique=False)
    nUser = db.Column(db.String(64), index=True, unique=False)
    nPass = db.Column(db.String(64), index=True, unique=False)
    nkey = db.Column(db.String(120), index=True, unique=False)
    nRoles = db.Column(db.String(120), index=True, unique=False, default='unknown') #hadoop roles running on server
    nStatus = db.Column(db.Boolean,index=True, unique=False, default='0')
    nMonitored = db.Column(db.Boolean,index=True, unique=False, default='0')
    nCollectdState = db.Column(db.String(64), index=True, unique=False,default='None') #Running, Pending, Stopped, None
    nLogstashForwState = db.Column(db.String(64), index=True, unique=False,default='None') #Running, Pending, Stopped, None
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    #ES = db.relationship('ESCore', backref='nodeFQDN', lazy='dynamic')

    #TODO: Create init function/method to populate db.Model

    def __repr__(self):
        return '<dbNodes %r>' % (self.nickname)


class dbESCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    nodeName = db.Column(db.String(64), index=True, unique=True)
    nodePort = db.Column(db.Integer, index=True, unique=False,default = 9200)
    clusterName = db.Column(db.String(64), index=True, unique=False)
    conf = db.Column(db.LargeBinary, index=True, unique=False)
    ESCoreStatus = db.Column(db.String(64), index=True, default='unknown', unique=False)#Running, Pending, Stopped, unknown
    ESCorePID = db.Column(db.Integer, index=True, default = 0, unique=False) # pid of current running process
    MasterNode = db.Column(db.Boolean,index=True, unique=False) # which node is master
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
   

    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbESCore %r>' % (self.body)

class dbSCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    inLumberPort = db.Column(db.Integer, index=True, unique=False,default = 5000)
    sslCert = db.Column(db.String(120), index=True, unique=False,default = 'unknown')
    sslKey = db.Column(db.String(120), index=True, unique=False,default = 'unknown')
    udpPort = db.Column(db.Integer, index=True, unique=False,default = 25826) #collectd port same as collectd conf
    outESclusterName = db.Column(db.String(64), index=True, unique=False )# same as ESCore clusterName
    outKafka = db.Column(db.String(64), index=True, unique=False,default = 'unknown') # output kafka details
    outKafkaPort = db.Column(db.Integer, index=True, unique=False,default = 'unknown')
    conf = db.Column(db.String(140), index=True, unique=False)
    LSCoreStatus = db.Column(db.String(64), index=True, unique=False,default = 'unknown')#Running, Pending, Stopped, None
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbLSCore %r>' % (self.body)

class dbKBCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    kbPort = db.Column(db.Integer, index=True, unique=False,default = 5601)
    conf = db.Column(db.String(140), index=True, unique=False)
    KBCoreStatus = db.Column(db.String(64), index=True, unique=False)#Running, Pending, Stopped, None
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
	cdhMng =  db.Column(db.String(64), index=True, unique=True)
	cdhMngPort = db.Column(db.Integer, index=True, unique=False,default = 7180)
	cpass = db.Column(db.String(64), index=True, default = 'admin',unique=False)
	cuser = db.Column(db.String(64), index=True, default = 'admin',unique=False)
	
	def __repr__(self):
		return '<dbCDHMng %r>' % (self.body)



#%--------------------------------------------------------------------%

#changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
dmon = api.namespace('dmon', description='D-MON operations')

#argument parser
pQueryES = api.parser() 
#pQueryES.add_argument('task',type=str, required=True, help='The task details', location='form')


#descripes universal json @api.marshal_with for return or @api.expect for payload model
queryES = api.model('query details Model', {
	'fname': fields.String(required=False,default="output", description='Name of output file.'),
    'size': fields.Integer(required=True,default=500, description='Number of record'),
    'ordering': fields.String(required=True,default='desc', description='Ordering of records'),
    'queryString': fields.String(required=True,default = "hostname:\"dice.cdh5.s4.internal\" AND serviceType:\"dfs\""
    	,description='ElasticSearc Query'),
    'tstart': fields.Integer(required=True,default=1438939155342,description='Start Date'),
    'tstop': fields.Integer(required=True,default=1438940055342,description='Stop Date'),
    'metrics': fields.List(fields.String(required=False, default = ' ', description = 'Desired Metrics'))

})
#Nested JSON input 
dMONQuery = api.model('queryES Model',{
	'DMON':fields.Nested(queryES, description="Query details")
	})



nodeSubmitCont = api.model('Submit Node Model Info',{
	'NodeName':fields.String(required=True, description="Node FQDN"),
	'NodeIP':fields.String(required=True, description="Node IP"),
	'NodeOS':fields.String(required=False, description="Node OS"),
	'key':fields.String(required=False, description="Node Pubilc key"),
	'username':fields.String(required=False, description="Node User Name"),
	'password':fields.String(required=False, description="Node Password"),
	})


nodeSubmit = api.model('Submit Node Model',{
	'Nodes':fields.List(fields.Nested(nodeSubmitCont,required=True, description="Submit Node details"))
	})


esCore = api.model('Submit ES conf',{
	'HostFQDN':fields.String(required=True, description='Host FQDN'),
	'IP':fields.String(required=True, description='Host IP'),
	'OS':fields.String(required=False,default='unknown',description='Host OS'),
	'NodeName':fields.String(required=True,description='ES Host Name'),
	'NodePort':fields.Integer(required=False, default=9200,description='ES Port'),
	'ClusterName':fields.String(required=True,description='ES Host Name')
	})


nodeUpdate = api.model('Update Node Model Info',{
	'IP':fields.String(required=True, description="Node IP"),
	'OS':fields.String(required=False, description="Node OS"),
	'Key':fields.String(required=False, description="Node Pubilc key"),
	'User':fields.String(required=False, description="Node User Name"),
	'Password':fields.String(required=False, description="Node Password")
	})

lsCore=api.model('Submit LS conf',{
	'HostFQDN':fields.String(required=True, description='Host FQDN'),
	'IP':fields.String(required=True, description='Host IP'),
	'OS':fields.String(required=False, description='Host OS'),
	'LPort':fields.Integer(required=True, description='Lumberhack port'),
	'udpPort':fields.String(required=True,default= 25826 ,description='UDP Collectd Port'),
	'ESClusterName':fields.String(required=True, description='ES cluster name')
	})
# monNodes = api.model('Monitored Nodes',{
# 	'Node':fields.List(fields.Nested(nodeDet, description="FQDN and IP of nodes"))
# 	})
# nodeDet = api.model('Node Info',{
# 	'FQDN' : field
# 	})#[{'FQDN':'IP'}]

@dmon.route('/v1/observer/applications')
class ObsApplications(Resource):
	def get(self):
		return 'Returns a list of all applications from YARN.'

@dmon.route('/v1/observer/application/<appID>')
class ObsAppbyID(Resource):
	def get(self,appID):
		return 'Returns information on a particular YARN applicaiton identified by '+appID+'!'

@dmon.route('/v1/observer/nodes')
class NodesMonitored(Resource):
	#@api.marshal_with(monNodes) # this is for response
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


@dmon.route('/v1/observer/nodes/<nodeFQDN>/services')
@api.doc(params={'nodeFQDN':'Nodes FQDN'})
class NodeStatusServices(Resource):
	def get(self,nodeFQDN):
		return "Node " + nodeFQDN +" status of services!"		






@dmon.route('/v1/observer/query/<ftype>')
@api.doc(params={'ftype':'output type'})
class QueryEsCore(Resource):
	#@api.doc(parser=pQueryES) #inst parser
	#@api.marshal_with(dMONQuery) # this is for response
	@api.expect(dMONQuery)# this is for payload 
	def post(self, ftype):
		#args = pQueryES.parse_args()#parsing query arguments in URI
		supportType = ["csv","json","plain"]
		if ftype not in supportType:
			response = jsonify({'Supported types':supportType, "Submitted Type":ftype })
			response.status_code = 415
			return response
		query = queryConstructor(request.json['DMON']['tstart'],request.json['DMON']['tstop'],
			request.json['DMON']['queryString'],size=request.json['DMON']['size'],ordering=request.json['DMON']['ordering'])
		#return query
		if not 'metrics'  in request.json['DMON'] or request.json['DMON']['metrics'] == " ":
			ListMetrics, resJson = queryESCore(query, debug=False)
			if ftype == 'csv':
				if not 'fname' in request.json['DMON']:
					fileName = 'output'+'.csv'
					dict2CSV(ListMetrics)
				else:
					fileName = request.json['DMON']['fname']+'.csv'
					dict2CSV(ListMetrics,request.json['DMON']['fname'])

				csvOut = os.path.join(outDir,fileName)
				try:
					csvfile=open(csvOut,'r')
				except EnvironmentError:
					response = jsonify({'EnvError':'file not found'})
					response.status_code = 500
					return response
				return send_file(csvfile,mimetype = 'text/csv',as_attachment = True)
			if ftype == 'json':
				response = jsonify({'DMON':resJson})
				response.status_code = 200
				return response
			if ftype == 'plain':
				return Response(str(ListMetrics),status=200 ,mimetype='text/plain')

		else:
			metrics = request.json['DMON']['metrics']
			ListMetrics, resJson = queryESCore(query, allm=False,dMetrics=metrics, debug=False)
			#repeated from before create function
			if ftype == 'csv':
				if not 'fname' in request.json['DMON']:
					fileName = 'output'+'.csv'
					dict2CSV(ListMetrics)
				else:
					fileName = request.json['DMON']['fname']+'.csv'
					dict2CSV(ListMetrics,request.json['DMON']['fname'])
				csvOut = os.path.join(outDir,fileName)
				try:
					csvfile=open(csvOut,'r')
				except EnvironmentError:
					response = jsonify({'EnvError':'file not found'})
					response.status_code = 500
					return response
				return send_file(csvfile,mimetype = 'text/csv',as_attachment = True)
			if ftype == 'json':
				response = jsonify({'DMON':resJson})
				response.status_code = 200
				return response
			if ftype == 'plain':
				return Response(str(ListMetrics),status=200 ,mimetype='text/plain')


@dmon.route('/v1/overlord')
class OverlordInfo(Resource):
	def get(self):
		message = 'Message goes Here and is not application/json (TODO)!'
		return message

@dmon.route('/v1/overlord/applicaiton')
class OverlordAppSubmit(Resource):
	def put(self):
		return 'Registers an applicaiton with DMON and creates a unique tag!'

@dmon.route('/v1/overlord/core')
class OverlordBootstrap(Resource):
	def post(self):
		return "Deploys all monitoring core components with default configuration"

@dmon.route('/v1/overlord/core/status')
class OverlordCoreStatus(Resource):
	def get(self):
		rspD = {}
		qESCore = dbESCore.query.filter_by(MasterNode = 1).first() #TODO -> curerntly only generates config file for master node
		if qESCore is None:
			response = jsonify({"Status":"No master ES instances found!"})
			response.status_code = 500
			return response
		try:
			esCoreUrl='http://'+qESCore.hostIP+':'+str(qESCore.nodePort)
			r = requests.get(esCoreUrl,timeout=2) #timeout in seconds
		except:
			response = jsonify({"Error":"Masteraster ES instances not reachable!"})
			response.status_code = 500
			return response

		rsp = r.json()
		rspES={'ElasticSearch':rsp}
		rspLS = {'Logstash':{'Status':'TODO','Version':'TODO'}}
		rspKB = {'Kibana':{'Status':'TODO','Version':'TODO'}}

		rspD.update(rspES)
		rspD.update(rspLS) #TODO
		rspD.update(rspKB) #TODO
		response = jsonify(rspD)
		response.status_code = 200
		return response

@dmon.route('/v1/overlord/chef')
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
		listN =[]
		for nodes in request.json['Nodes']:
			qNodes = dbNodes.query.filter_by(nodeFQDN = nodes['NodeName']).first()
			if qNodes is None:
				e = dbNodes(nodeFQDN = nodes['NodeName'], nodeIP =nodes['NodeIP'] , nodeOS = nodes['NodeOS'], 
					nkey = nodes['key'],nUser=nodes['username'],nPass=nodes['password'])
				db.session.add(e)
			else:
				qNodes.nodeIP = nodes['NodeIP']
				qNodes.nodeOS =nodes['NodeOS']
				qNodes.nkey = nodes['key']
				qNodes.nUser=nodes['username']
				qNodes.nPass=nodes['password']
				db.session.add(qNodes)
			db.session.commit
		response = jsonify({'Status':"Nodes list Updated!"})
		response.status_code=201
		return response	

	def post(self):
		return "Bootstrap monitoring"


@dmon.route('/v1/overlord/nodes/<nodeFQDN>')
@api.doc(params={'nodeFQDN':'Nodes FQDN'})
class MonitoredNodeInfo(Resource):
	def get(self, nodeFQDN):
		qNode = dbNodes.query.filter_by(nodeFQDN = nodeFQDN).first()
		if qNode is None:
			response = jsonify({'Status':'Node ' +nodeFQDN+' not found!'})
			response.status_code = 404
			return response
		else:
			response = jsonify({
				'NodeName':qNode.nodeFQDN,
				'Status':qNode.nStatus,
				'IP':qNode.nodeIP,
				'Monitored':qNode.nMonitored,
				'OS':qNode.nodeOS,
				'Key':qNode.nkey,
				'Password':qNode.nPass,
				'User':qNode.nUser,
				'ChefClient':"TODO",
				'CDH':'TODO',
				'Roles':'TODO'})
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
			response=jsonify({'Status':'Node '+ nodeFQDN+' updated!'})
			response.status_code = 201
			return response

	def post(self, nodeFQDN):
		return "Bootstrap specified node!"	

	def delete(self, nodeFQDN):
		dNode = dbNodes.query.filter_by(nodeFQDN = nodeFQDN).first()
		if dNode is None:
			response = jsonify({'Status':'Node '+nodeFQDN+' not found'})
			response.status_code = 404
			return response
		dlist = []
		dlist.append(dNode.nodeIP)
		try:
			serviceCtrl(dlist,dNode.nUser,dNode.nPass,'collectd', 'stop')
		except Exception as inst:
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args
			response = jsonify({'Error':'Collectd stopping error!'})
			response.status_code = 500
			return response

		try:
			serviceCtrl(dlist,dNode.nUser,dNode.nPass,'logstash-forwarder', 'stop')
		except Exception as inst:
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args
			response = jsonify({'Error':'LSF stopping error!'})
			response.status_code = 500
			return response
		dNode.nMonitored = 0
		dNode.nCollectdState = 'None'
		dNode.nLogstashForwState = 'None'
		response =jsonify({'Status':'Node '+ nodeFQDN+' monitoring stopped!'})
		response.status_code = 200
		return response

		return "delete specified node!"


@dmon.route('/v1/overlord/nodes/purge/<nodeFQDN>')
@api.doc(params={'nodeFQDN':'Nodes FQDN'})
class PurgeNode(Resource):
	def delete(self,nodeFQDN):
		qPurge = dbNodes.query.filter_by(nodeFQDN = nodeFQDN).first()
		if qPurge is None:
			abort(404)

		lPurge=[]
		lPurge.append(qPurge.nodeIP)
		try:
			serviceCtrl(lPurge,qPurge.uUser,qPurge.uPass,'logstash-forwarder', 'stop')
		except Exception as inst:
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args
			response = jsonify({'Error':'Stopping LSF!'})
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
		response = jsonify ({'Status':'Node ' +nodeFQDN+ ' deleted!'})
		response.status_code = 200
		return response




@dmon.route('/v1/overlord/core/es/config')#TODO use args for unsafe cfg file upload
class ESCoreConfiguration(Resource):
	def get(self): #TODO same for all get config file createfunction
		if not os.path.isdir(cfgDir):
			response = jsonify({'Error':'Config dir not found !'})
			response.status_code = 404
			return response
		if not os.path.isfile(os.path.join(cfgDir,'elasticsearch.yml')):
			response = jsonify({'Status':'Config file not found !'})
			response.status_code = 404
			return response
		try:
			esCfgfile=open(os.path.join(cfgDir,'elasticsearch.yml'),'r')
		except EnvironmentError:
			response = jsonify({'EnvError':'file not found'})
			response.status_code = 500
			return response

		return send_file(esCfgfile,mimetype = 'text/yaml',as_attachment = True)

	@api.expect(esCore)	
	def put(self):
		requiredKeys=['ClusterName','HostFQDN','IP','NodeName','NodePort']
		if not request.json:
			abort(400)
		for key in requiredKeys:
			if key not in request.json:
				response = jsonify({'Error':'malformed request, missing key(s)'})
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
			 clusterName=request.json["ClusterName"], conf = 'none', nodePort=request.json['NodePort'], MasterNode=master)
			db.session.add(upES) 
			db.session.commit()
			response = jsonify({'Added':'ES Config for '+ request.json["HostFQDN"]})
			response.status_code = 201
			return response
		else:
			#qESCore.hostFQDN =request.json['HostFQDN'] #TODO document hostIP and FQDN may not change in README.md
			qESCore.hostOS = os
			qESCore.nodename = request.json['NodeName']
			qESCore.clusterName=request.json['ClusterName']
			qESCore.nodePort=request.json['NodePort']
			db.session.commit()
			response=jsonify({'Updated':'ES config for '+ request.json["HostFQDN"]})
			response.status_code = 201
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
			confDict['ClusterName']=hosts[5]
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

		infoESCore = {"clusterName":qESCore.clusterName,"nodeName":qESCore.nodeName}			
		esConf = template.render(infoESCore)
		qESCore.conf = esConf
		#print >>sys.stderr, esConf
		db.session.commit()
		esCoreConf = open(esfConf,"w+")
		esCoreConf.write(esConf)
		esCoreConf.close()

		os.rename(os.path.join(esDir,'elasticsearch.yml'),os.path.join(esDir,'elasticsearch.old'))
		shutil.copy(esfConf, os.path.join(esDir,'elasticsearch.yml'))
		esPid = 0
		FNULL = open(os.devnull, 'w')
		try:
			FNULL = open(os.devnull, 'w')
			esPid = subprocess.Popen(['ES_HEAP_SIZE=512m /opt/elasticsearch/bin/elasticsearch -d'],shell=True).pid
		except Exception as inst:
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args
		qESCore.ESCorePID = esPid
		response = jsonify({'Status':'Started ElasticSearch with PID: '+str(esPid)})
		response.status_code = 200
		return response
		#TODO NOW -> use rendered tempalte to load es Core
		#return "Deploys (Start/Stop/Restart/Reload args not json payload) configuration of ElasticSearch"

@dmon.route('/v1/overlord/core/kb/config')
class KBCoreConfiguration(Resource):
	def get(self):
		return "Retruns Kibana current configuration"

	def put(self):
		return "Changes configuration of Kibana"

@dmon.route('/v1/overlord/core/kb')
class KKCoreController(Resource):
	def post(self):
		return "Deploys (Start/Stop/Restart/Reload args not json payload) configuration of Kibana"

@dmon.route('/v1/overlord/core/ls/config')
class LSCoreConfiguration(Resource):
	def get(self):
		if not os.path.isdir(cfgDir):
			response = jsonify({'Error':'Config dir not found !'})
			response.status_code = 404
			return response
		if not os.path.isfile(os.path.join(cfgDir,'logstash.conf')):
			response = jsonify({'Error':'Config file not found !'})
			response.status_code = 404
			return response
		try:
			lsCfgfile=open(os.path.join(cfgDir,'logstash.conf'),'r')
		except EnvironmentError:
			response = jsonify({'EnvError':'file not found'})
			response.status_code = 500
			return response
		return send_file(lsCfgfile,mimetype = 'text/plain',as_attachment = True)

	@api.expect(lsCore)
	def put(self):
		# if request.headers['Content-Type'] == 'text/plain':
		# 	cData = request.data
		# 	#temporaryConf =  open(tmp_loc+'/temporary.conf',"w+")
		# 	#temporaryConf.write(cData)
		# 	#temporaryConf.close()
		# 	print cData
		requiredKeys=['ESClusterName','HostFQDN','IP','LPort','udpPort']
		if not request.json:
			abort(400)
		for key in requiredKeys:
			if key not in request.json:
				response = jsonify({'Error':'malformed request, missing key(s)'})
				response.status_code = 400
				return response 
		
		qESCheck = dbESCore.query.filter_by(clusterName=request.json['ESClusterName'])
		if qESCheck is None:
			response = jsonify({'Status':'Invalid cluster name: '+request.json['ESClusterName']})
			response.status_code = 404
			return response		
		qSCore = dbSCore.query.filter_by(hostIP = request.json['IP']).first()
		if request.json["OS"] is None:
			os = "unknown"
		else:
			os=request.json["OS"]

		if qSCore is None:
			upS = dbSCore(hostFQDN=request.json["HostFQDN"],hostIP = request.json["IP"],hostOS=os,
			 outESclusterName=request.json["ESClusterName"], udpPort = request.json["udpPort"], inLumberPort=request.json['LPort'])
			db.session.add(upS) 
			db.session.commit()
			response = jsonify({'Added':'LS Config for '+ request.json["HostFQDN"]})
			response.status_code = 201
			return response
		else:
			#qESCore.hostFQDN =request.json['HostFQDN'] #TODO document hostIP and FQDN may not change in README.md
			qSCore.hostOS = os
			qSCore.outESclusterName=request.json['ESClusterName']
			qSCore.udpPort=request.json['udpPort']
			qSCore.inLumberPort=request.json['LPort']
			db.session.commit()
			response=jsonify({'Updated':'LS config for '+ request.json["HostFQDN"]})
			response.status_code = 201
			return response
		#return "Changes configuration fo logstash server"

@dmon.route('/v1/overlord/core/ls')
class LSCoreController(Resource):
	def post(self):
		templateLoader = jinja2.FileSystemLoader( searchpath="/" )
		templateEnv = jinja2.Environment( loader=templateLoader )
		esTemp= os.path.join(tmpDir,'logstash.tmp')#tmpDir+"/collectd.tmp"
		#qSCore = db.session.query(dbSCore.hostFQDN).first()
		qSCore=dbSCore.query.first()
		#return qSCore
		if qSCore is None:
			response = jsonify({"Status":"No LS instances registered"})
			response.status_code = 404
			return response
		try:
			template = templateEnv.get_template( esTemp )
			#print >>sys.stderr, template
		except:
			return "Tempalte file unavailable!"

		infoSCore = {"sslcert":qSCore.sslCert,"sslkey":qSCore.sslKey,"udpPort":qSCore.udpPort,"ESCluster":qSCore.outESclusterName}			
		sConf = template.render(infoSCore)
		qSCore.conf = sConf
		#print >>sys.stderr, esConf
		db.session.commit()
		#TODO NOW -> use rendered tempalte to load ls Core
		return "Deploys (Start/Stop/Restart/Reload args not json payload) configuration of Logstash Server"



@dmon.route('/v1/overlord/aux')
class AuxInfo(Resource):
	def get(self):
		return "Returns Information about AUX components"


@dmon.route('/v1/overlord/aux/deploy')
class AuxDeploy(Resource):
	def get(self):
		qNodes=db.session.query(dbNodes.nodeFQDN,dbNodes.nodeIP,dbNodes.nMonitored,
			dbNodes.nCollectdState,dbNodes.nLogstashForwState).all()
		mnList = []
		for nm in qNodes:
			mNode = {}
			mNode['NodeFQDN']=nm[0]
			mNode['NodeIP']=nm[1]
			mNode['Monitored']=nm[2]
			mNode['Collectd']=nm[3]
			mNode['LSF']=nm[4]
			mnList.append(mNode)
			#print >> sys.stderr, nm
		response = jsonify({'Aux Status':mnList})
		response.status_code=200
		return response

	def post(self): #TODO currently works only if the same username and password is used for all Nodes
		qNodes=db.session.query(dbNodes.nodeFQDN,dbNodes.nMonitored,
			dbNodes.nCollectdState,dbNodes.nLogstashForwState,dbNodes.nUser,dbNodes.nPass,dbNodes.nodeIP).all()
		result = []
		credentials ={}
		for n in qNodes:
			credentials['User'] = n[4]#TODO need a more elegant solution, currently it is rewriten every iteration
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
		for res in result:
			if res['Collectd'] == 'None':
				print >> sys.stderr, 'No collectd!'
				collectdList.append(res['IP'])
			if res['LSF'] == 'None':
				LSFList.append(res['IP'])
				print >> sys.stderr, 'No LSF!'

		if not collectdList and not LSFList:
			response = jsonify({'Status':'All registred nodes are already monitored!'})
			response.status_code=200
			return response	

		print >> sys.stderr, collectdList
		print >> sys.stderr, LSFList		
		print >> sys.stderr, credentials['User']
		print >> sys.stderr, confDir

		
		try:
			installCollectd(collectdList,credentials['User'],credentials['Pass'],confDir=cfgDir)
		except Exception as inst:#TODO if exceptions is detected check to see if collectd started if not return fail if yes return warning
			print >> sys.stderr, type(inst) #TODO change all exceptions to this for debuging
			print >> sys.stderr, inst.args
			response = jsonify({'Status':'Error Installing collectd!'})
			response.status_code = 500
			return response

		try:
			installLogstashForwarder(LSFList,userName=credentials['User'],uPassword=credentials['Pass'],confDir=cfgDir)
		except Exception as inst:
			print >> sys.stderr, type(inst)
			print >> sys.stderr, inst.args
			response = jsonify({'Status':'Error Installig LSF!'})
			response.status_code = 500
			return response

		for c in collectdList:
			updateNodesCollectd =  dbNodes.query.filter_by(nodeIP = c).first()
			if updateNodesCollectd is None:
				response = jsonify({'Error':'DB error, IP ' + c + ' not found!'})
				reponse.status_code=500
				return response
			updateNodesCollectd.nCollectdState='Running'

		for l in LSFList:
			updateNodesLSF =  dbNodes.query.filter_by(nodeIP = l).first()
			if updateNodesLSF is None:
				response = jsonify({'Error':'DB error, IP ' + l + ' not found!'})
				reponse.status_code=500
				return response
			updateNodesLSF.nLogstashForwState='Running'	

		updateAll = dbNodes.query.filter_by(nMonitored = 0).all()
		for ua in updateAll:
			ua.nMonitored = 1

		response = jsonify({'Status':'Aux Componnets deployed!'})
		response.status_code = 201		
		return response			

@dmon.route('/v1/overlord/aux/<auxComp>/<nodeFQDN>')
@api.doc(params={'auxComp':'Aux Component','nodeFQDN':'Node FQDN'})#TODO document nMonitored set to true when first started monitoring
class AuxDeploySelective(Resource):
	def post(self, auxComp, nodeFQDN):
		auxList = ['collectd','lsf']
		#status = {}
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
		
@dmon.route('/v1/overlord/aux/<auxComp>/config')
@api.doc(params={'auxComp':'Aux Component'})
class AuxConfigSelective(Resource):
	def get(self, auxComp):
		allowed = ['collectd','lsf']
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
			if not os.path.isfile(os.path.join(cfgDir,'logstash-forwarder.conf')):
				response = jsonify({'Error':'Config file not found !'})
				response.status_code = 404
				return response
			try:
				Cfgfile=open(os.path.join(cfgDir,'logstash-forwarder.conf'),'r')
			except EnvironmentError:
				response = jsonify({'EnvError':'file not found'})
				response.status_code = 500
				return response
		return send_file(Cfgfile,mimetype = 'text/plain',as_attachment = True)

	def put(self,auxComp):
		return "Sets configuration of aux components use parameters (args) -unsafe"

"""
Custom errot Handling

"""	


@app.errorhandler(403)
def forbidden(e):
    response = jsonify({'error': 'forbidden'})
    response.status_code = 403
    return respons


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
	response=jsonify({'error':'method not allowed'})
	response.status_code=405
	return response

@api.errorhandler(400)
def bad_request(e):
	response=jsonify({'error':'bad request'})
	response.status_code=400
	return response

@api.errorhandler(415)
def bad_mediatype(e):
	response=jsonify({'error':'unsupported media type'})
	response.status_code = 415
	return response



#109.231.126.38

if __name__ == '__main__':
	app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(baseDir,'dmon.db')
	app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
	db.create_all()

	#print >>sys.stderr, "Running as: %s:%s" % (os.getuid(), os.getgid())
	# testQuery = queryConstructor(1438939155342,1438940055342,"hostname:\"dice.cdh5.s4.internal\" AND serviceType:\"dfs\"")
	# metrics = ['type','@timestamp','host','job_id','hostname','AvailableVCores']
	# test, test2 = queryESCore(testQuery, debug=False)
	# print >>sys.stderr, test2
	if len(sys.argv) == 1:
		#esDir=
		#lsDir=
		#kibanaDir=
		app.run(debug=True)
	else:
		app.run(host='0.0.0.0', port=8080, debug = True)
