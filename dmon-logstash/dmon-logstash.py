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
from flask import Flask
from flask import jsonify
from flask import send_file
from flask import request
from flask.ext.restplus import Api, Resource, fields
from flask import abort
import os
import jinja2
import sys
import subprocess
import platform
import requests
import json

from pyLogstash import *
from jsonvalidation import *
from jsonschema import *


#directory location

tmpDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
pidDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pid')
logDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
cfgDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
credDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials')
lockDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lock')
logstashDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logstash')

app = Flask("dmon-logstash")
app.config['RESTPLUS_VALIDATE'] = True
api = Api(app, version='0.0.1', title='DICE Monitoring Logstash API',
          description="RESTful API for the DICE Monitoring Platform  Logstash agent (dmon-logstash)",
          )

# changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
agent = api.namespace('agent', description='dmon logstash operations')

lsConfig = api.model('LS Configuration options', {
    'UDPPort': fields.String(required=True, default='25826', description='Port of UDP plugin from Logstash Server'),
    'ESCluster': fields.String(required=True, default='esCore', description='Name of ES cluster'),
    'EShostIP': fields.String(required=True, default='localhost', description='ES endpoint IP'),
    'EShostPort': fields.String(required=True, default='9200', description='ES endpoint Port'),
    'LSWorkers': fields.String(required=True, default='2', description='Number of workers'),
    'LSHeap': fields.String(required=True, default='512m', description='Size of JVM Heap'),
    'StormRestIP': fields.String(required=False, default='none', description='Storm REST API endpoint IP'),
    'StormRestPort': fields.String(required=False, default='none', description='Storm REST API endpoint Port'),
    'StormTopologyID': fields.String(required=False, default='none', description='Storm Topology')
})

lsagent = pyLogstashInstance()
valid = LSValidation()


@agent.route('/v1/host')
class NodeInfo(Resource):
    def get(self):
        mType = platform.uname()
        response = jsonify({'System': mType[0],
                            'Node': mType[1],
                            'Release': mType[2],
                            'Version': mType[3],
                            'Machine': mType[4],
                            'Processor': mType[5]})
        response.status_code = 200
        return response


@agent.route('/v1/cert')
class LSCertificates(Resource):
    def get(self):
        dirContent = os.listdir(credDir)
        if dirContent == []:
            response = jsonify({'Status': 'Env Error',
                                'Message': 'Credential folder empty'})
            response.status_code = 404
            return response
        pubFile = []
        privateFile = []
        for f in dirContent:
           if os.path.splitext(f)[1] == 'crt':
               pubFile.append(f)
           elif os.path.splitext(f)[1] == 'key':
               privateFile.append(f)

        response = jsonify({'certificates': pubFile,
                            'keys': privateFile})
        response.status_code = 200
        return response

    def post(self):
        return "Send new certificate!"


@agent.route('/v1/logstash')
class LSStatus(Resource):
    def get(self):

        if not os.path.isfile(os.path.join(pidDir, 'logstash.pid')):
            response = jsonify({'Status': 'Env Error',
                                'Message': 'PID file not found!'})
            response.status_code = 404
            return response
        status = lsagent.check()

        if not status:
            response = jsonify({'Status': 'Stopped',
                                'Message': 'No LS instance found'})
            response.status_code = 200
            return response
        else:
            response = jsonify({'Status': 'Running',
                                'Message': 'PID ' + status})
            response.status_code = 200
            return response


@agent.route('/v1/logstash/config')
class LSController(Resource):
    def get(self):
        conf = os.path.isfile(os.path.join(cfgDir, 'logstash.conf'))
        if not conf:
            response = jsonify({'Status': 'Env Error',
                                'Message': 'No config found!'})
            response.status_code = 404
            return response

        confFile = open(conf, 'r')

        return send_file(confFile, mimetype='text/plain', as_attachment=True)

    @api.expect(lsConfig)
    def post(self):
        sslCert = os.path.join(credDir, 'logstash.crt')
        sslKey = os.path.join(credDir, 'logstash.key')

        if not os.path.isfile(sslCert) or os.path.isfile(sslKey):
            response = jsonify({'Status': 'Credential Error',
                                'Message': 'Missing keys'})
            response.status_code = 404
            return response
        if not request.json:
            abort(400)

        try:
            valid.validate(request.json)
        except ValidationError:
            response = jsonify({'Status': 'json error',
                                'Message': 'Malformed json'})
            response.status_code = 404
            return response

        if not request.json['StormRestIP']:
            StormRestIP = 'none'
        else:
            StormRestIP = request.json['StormRestIP']

        if not request.json['StormRestPort']:
            StormRestPort = 'none'
        else:
            StormRestPort = request.json['StormRestPort']

        if not request.json['StormTopologyID']:
            if not request.json['StormRestIP']:
                StormTopologyID = 'none'
            else:
                if request.json['StormTopologyID'] == 'none':
                    StormTopologyID = 'none'
                else:
                    # Get first topology from storm and use this for monitoring
                    stormTopologyURL = 'http://'+StormRestIP+':'+StormRestPort+'/api/v1/topology/'
                    listTopologies = requests.get(stormTopologyURL + 'summary')
                    plainText = listTopologies.text
                    jsonPayload = json.loads(plainText)
                    topology = jsonPayload['topologies'][0]['encodedId'] #TODO: get list of topologies instead of just the first one
                    #getTopology = request.get(stormTopologyURL + topology)
                    StormTopologyID = topology

        confdict = {"sslcert": sslCert, "sslkey": sslKey, "udpPort": request.json['UDPPort'],
                    "ESCluster": request.json['ESCluster'], "EShostIP": request.json['EShostIP'], "EShostPort": request.json['EShostPort'],
                    "StormRestIP": StormRestIP, "StormRestPort": StormRestPort, "StormTopologyID": StormTopologyID}
        lsagent.generateConfig(confdict)
        pid = lsagent.check()
        if not pid:
            lsagent.start(heap=request.json['LSHeap'], worker=request.json['LSWorker'])
        else:
            subprocess.call(['kill', '-9', pid])
            lsagent.start(heap=request.json['LSHeap'], worker=request.json['LSWorker'])

        response = jsonify({'Status': 'Done',
                            'Message': 'LS config loaded'})
        response.status_code = 200
        return response


@agent.route('/v1/logstash/start')
class LSControllerStart(Resource):
    def post(self):
        return "Start/Restart LS instance!"


@agent.route('/v1/logstash/stop')
class LSControllerStop(Resource):
    def post(self):
        pid = lsagent.check()
        if not pid:
            response = jsonify({'Status': 'Not Found',
                                'Message': 'LS instance not found'})
            response.status_code = 404
            return response
        else:
            subprocess.call(['kill', '-9', pid])
            response = jsonify({'Status': 'Done',
                                'Message': 'LS Instance stopped'})
            response.status_code = 200
            return response


@agent.route('/v1/logstash/deploy')
class LSControllerDeploy(Resource):
    def post(self):
        lsagent.deploy()
        response = jsonify({'Status': 'Done',
                            'Message': 'Logstash installed!'})
        response.status_code = 201
        return response


@agent.route('/v1/logstash/log')
class LSControllerLog(Resource):
    def get(self):
        lslog = os.path.join(logDir, 'logstash.log')

        if not os.path.isfile(lslog):
            response = jsonify({'Status': 'Env Error',
                                'Message': 'No log file found'})
            response.status_code = 404
            return response

        sizeMB = os.path.getsize(lslog) >> 20
        if sizeMB > 10:
            response = jsonify({'Status': 'Size Warning',
                                'Message': 'Log file to big!'})
            response.status_code = 413
            return response

        logCont = open(lslog, 'r')
        return send_file(logCont, mimetype='text/plain', as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
