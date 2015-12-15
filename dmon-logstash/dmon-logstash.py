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
logDit = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')

app = Flask("dmon-logstash")
api = Api(app, version='0.0.1', title='DICE Monitoring Logstash API',
          description="RESTful API for the DICE Monitoring Platform  Logstash agent (dmon-logstash)",
          )

# changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
agent = api.namespace('agent', description='dmon logstash operations')


@agent.route('/v1/host')
class NodeInfo(Resource):
    def get(self):
        return "Host info!"


@agent.route('/v1/cert')
class LSCertificates(Resource):
    def get(self):
        return "List of certificates from certificate directory!"

    def post(self):
        return "Send new certificate!"


@agent.route('/v1/logstash')
class LSStatus(Resource):
    def get(self):
        return "Get current status of logstash server"


@agent.route('/v1/logstash/config')
class LSController(Resource):
    def get(self):
        return "Get current configuration!"

    def post(self):
        return "Generate new configuration and start LS!"


@agent.route('/v1/logstash/start')
class LSControllerStart(Resource):
    def post(self):
        return "Start/Restart LS instance!"


@agent.route('/v1/logstash/stop')
class LSControllerStop(Resource):
    def post(self):
        return "Stop LS instances!"


@agent.route('/v1/logstash/deploy')
class LSControllerDeploy(Resource):
    def post(self):
        return "Install LS Config!"


@agent.route('/v1/logstash/log')
class LSControllerLog(Resource):
    def get(self):
        return "Logstash log file!"


if __name__ == '__main__':
    app.run(debug=True)
