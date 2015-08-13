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
    'size': fields.Integer(required=False,default=500, description='Number of record'),
    'ordering': fields.String(required=False,default='desc', description='Ordering of records'),
    'queryString': fields.String(required=True,description='ElasticSearc Query'),
    'tstart': fields.Integer(required=True,description='Start Date'),
    'tstop': fields.Integer(required=True,description='Stop Date')

})
#Nested JSON input 
dMONQuery = api.model('queryES Model',{
	'DMON':fields.Nested(queryES, description="Query details")
	})





@dmon.route('/v1/observer/query/<ftype>', endpoint='my-resource')
@api.doc(params={'ftype':'output type'})
class queryEsCore(Resource):
	#@api.doc(parser=pQueryES) #inst parser
	#@api.marshal_with(dMONQuery) # this is for response
	@api.expect(dMONQuery)# this is for payload
	def post(self, ftype):
		#args = pQueryES.parse_args()#parsing query arguments in URI
			
		if ftype == 'csv':
			return request.json['DMON']['tstart']
			#return "Hello"
		else:
			return {"Status":"What"}














if __name__ == '__main__':
	#print >>sys.stderr, "Running as: %s:%s" % (os.getuid(), os.getgid())
	app.run(debug=True)