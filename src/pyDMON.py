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
#DICE Imports
from pyESController import *


app = Flask("D-MON")
api = Api(app, version='0.1', title='DICE MOnitoring API',
    description='RESTful API for the DICE Monitoring Platform  (D-MON)',
)



#changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
dmon = api.namespace('dmon', description='D-MON operations')

#argument parser
pQueryES = api.parser() 



#/v1/observer/query/ POST
# {
#   "DMON":{
#     "query":{
#       "size":"<SIZEinINT>",
#       "ordering":"<asc|desc>",
#       "queryString":"<query>",
#       "tstart":"<startDate>",
#       "tstop":"<stopDate>"
#     }
#   }
# }




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


# def abort_if_todo_doesnt_exist(todo_id):
#     if todo_id not in TODOS:
#         api.abort(404, "Todo {} doesn't exist".format(todo_id))


@dmon.route('/v1/observer/query/<ftype>')
@api.doc(params={'ftype':'output type'})
class queryEsCore(Resource):
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

@app.errorhandler(415)
def bad_mediatype(e):
	response=jsonify({'error':'unsupported media type'})
	response.status_code = 415
	return response



#109.231.126.38

if __name__ == '__main__':
	#directory Location
	outDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
	#print >>sys.stderr, "Running as: %s:%s" % (os.getuid(), os.getgid())
	# testQuery = queryConstructor(1438939155342,1438940055342,"hostname:\"dice.cdh5.s4.internal\" AND serviceType:\"dfs\"")
	# metrics = ['type','@timestamp','host','job_id','hostname','AvailableVCores']
	# test, test2 = queryESCore(testQuery, debug=False)
	# print >>sys.stderr, test2
	app.run(debug=True)
