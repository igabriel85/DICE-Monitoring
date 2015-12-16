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
import os
import jinja2
import sys
import subprocess
import platform

#directory location

tmpDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
pidDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pid')
logDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
cfgDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')

app = Flask("dmon-elasticsearch")
api = Api(app, version='0.0.1', title='DICE Monitoring Elasticsearch API',
          description="RESTful API for the DICE Monitoring Platform  Elasticsearch agent (dmon-elasticsearch)",
          )

# changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
agent = api.namespace('agent', description='dmon elasticsearch operations')


@agent.route('/v1/log')
class NodeLog(Resource):
    def get(self):
        return "Get ES Agent log!"


@agent.route('/v1/host')
class NodeInfo(Resource):
    def get(self):
        return "Host Info!"


@agent.route('/v1/cert')
class ESCertificates(Resource):
    def get(self):
        return "List of certificates from certificate directory"

    def post(self):
        return "Send new certificate!"


@agent.route('/v1/elasticsearch')
class ESController(Resource):
    def get(self):
        return "Current Status of ES Core!"


@agent.route('/v1/elasticsearch/config')
class ESControllerConfig(Resource):
    def get(self):
        return "Get current configuration"

    def post(self):
        return "Generate new configuration"


@agent.route('/v1/elasticsearch/config/<parameter>')
class ESControllerConfigODF(Resource):
    def get(self):
        return "Get current parameter settings from ES instance!"

    def put(self):
        return "Change current parameter setting for ES instance!"


@agent.route('/v1/elasticsearch/cmd')
class ESControllerCmd(Resource):
    def post(self):
        return "Execute specific command!"


@agent.route('/v1/elasticsearch/logs')
class ESControllerLogs(Resource):
    def get(self):
        return "Get current list of logs"


@agent.route('/v1/elasticsearch/logs/<log>')
class ESControllerLog(Resource):
    def get(self):
        return "Get specific log!"


if __name__ == '__main__':
    app.run(debug=True)
