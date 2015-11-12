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

from pyUtil import *


# directory location
tmpDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
pidDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pid')
collectdlog = '/var/log/collectd.log'
collectdpid = os.path.join(pidDir, 'collectd.pid')
lsflog = '/var/log/logstash-fowarder/logstash-fowarder.log'
lsferr = 'var/log/logstash-fowarder/logstash-fowarder.err'
collectdConf = '/etc/collecd/collectd.conf'
lsfConf = '/etc/logstash-forwarder.conf'
lsfList = os.path.join(tmpDir, 'logstashforwarder.list')
lsfGPG = os.path.join(tmpDir, 'GPG-KEY-elasticsearch')

# supported aux components
auxList = ['collectd', 'lsf', 'jmx']

app = Flask("dmon-agent")
api = Api(app, version='0.0.1', title='DICE Monitoring Agent API',
          description="RESTful API for the DICE Monitoring Platform  Agent (dmon-agent)",
          )


# changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
agent = api.namespace('agent', description='dmon agent operations')

nodeRoles = api.model('query details Model', {
    'roles': fields.List(fields.String(required=False, default='hdfs',
                                       description='Roles assigned to this node!'))
})

# Instance of AuxComponent Class
aux = AuxComponent(lsfList, lsfGPG)

@agent.route('/v1/node')
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


@agent.route('/v1/deploy')
class NodeDeploy(Resource):
    @api.expect(nodeRoles)
    def post(self):  # TODO: Install components based on the rolls assigned for each VM.
        rolesList = request.json['roles']
        aComp = aux.install(rolesList)
        return aComp
        # test = []
        # if 'yarn' or 'hdfs' in request.json['roles']:
        #     test.append('yarn or hdfs')
        # if 'spark' in request.json['roles']:
        #     test.append('spark')
        # if 'kafka' in request.json['roles']:
        #     test.append('kafka')
        # if 'storm' in request.json['roles']:
        #     test.append('storm')

        # return str(test)
        # try:
        #     subprocess.Popen('sudo apt-get install -y collectd', shell=True)
        # except Exception as inst:
        #     print >> sys.stderr, type(inst)
        #     print >> sys.stderr, inst.args
        #     response = jsonify({'Status': 'subprocess error',
        #                         'Message': 'Collectd installation failed!'})
        #     response.status_code = 500
        #     return response
        #
        # response = jsonify({'Status': 'Done',
        #                    'Message': 'Collectd Installation Complete!'})
        # response.status_code = 201
        # return response


@agent.route('/v1/deploy/<auxComp>')
class NodeDeploySelective(Resource):
    def get(self, auxComp):
        return 'Same as node/deploy but for a component ' + auxComp


@agent.route('/v1/start')
class NodeMonitStartAll(Resource):
    def post(self):
        try:
            subprocess.Popen('sudo service collectd start', shell=True)
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args

        try:
            subprocess.Popen('sudo service logstash-forwarder start', shell=True)
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args

        response = jsonify({'Status': 'Started',
                            'Message': 'Auxiliary components started!'})
        response.status_code = 200
        return response


@agent.route('/v1/stop')
class NodeMonitStopAll(Resource):
    def post(self):
        try:
            subprocess.Popen('sudo service collectd stop', shell=True)
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args

        try:
            subprocess.Popen('sudo service logstash-forwarder stop', shell=True)
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args

        response = jsonify({'Status': 'Stopped',
                            'Message': 'Auxiliary components stopped!'})
        response.status_code = 200
        return response


@agent.route('/v1/start/<auxComp>')
class NodeMonitStartSelective(Resource):
    def post(self, auxComp):
        if auxComp not in auxList:
            response = jsonify({'Status': 'parameter error',
                                'Message': 'Component '+auxComp+' not supported!'})
            response.status_code = 404
            return response

        try:
            aux.controll(auxComp, 'start')
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            response = jsonify({'Status': type(inst),
                               'Message': inst.args})
            response.status_code = 500
            return response

        # if auxComp == 'collectd':
        #     try:
        #         subprocess.Popen('sudo service collectd start', shell=True)
        #     except Exception as inst:
        #         print >> sys.stderr, type(inst)
        #         print >> sys.stderr, inst.args
        #
        # if auxComp == 'lsf':
        #     try:
        #         subprocess.Popen('sudo service logstash-forwarder start', shell=True)
        #     except Exception as inst:
        #         print >> sys.stderr, type(inst)
        #         print >> sys.stderr, inst.args
        #
        # if auxComp == 'jmx':  # TODO: jmxtrans handeling
        #     return 'jmx'

        response = jsonify({'Status': 'Done',
                            'Message': 'Component '+auxComp+' started!'})
        response.status_code = 200
        return response


@agent.route('/v1/stop/<auxComp>')
class NodeMonitStopSelective(Resource):
    def post(self, auxComp):
        if auxComp not in auxList:
            response = jsonify({'Status': 'parameter error',
                                'Message': 'Component '+auxComp+' not supported!'})
            response.status_code = 404
            return response

        if auxComp == 'collectd':
            try:
                subprocess.Popen('sudo service collectd stop', shell=True)
            except Exception as inst:
                print >> sys.stderr, type(inst)
                print >> sys.stderr, inst.args

        if auxComp == 'lsf':
            try:
                subprocess.Popen('sudo service logstash-forwarder stop', shell=True)
            except Exception as inst:
                print >> sys.stderr, type(inst)
                print >> sys.stderr, inst.args

        if auxComp == 'jmx':  # TODO: jmxtrans handeling
            return 'jmx'

        response = jsonify({'Status': 'Done',
                            'Message': 'Component '+auxComp+' stopped!'})
        response.status_code = 200
        return response


@agent.route('/v1/logs/<auxComp>')
class NodeMonitLogs(Resource):
    def get(self, auxComp):
        if auxComp not in auxList:
            response = jsonify({'Status': 'parameter error',
                                'Message': 'Component '+auxComp+' not supported!'})
            response.status_code = 404
            return response
        if auxComp == 'collectd':
            try:
                clog = open(collectdlog, 'w+')
            except Exception as inst:
                print >> sys.stderr, type(inst)
                print >> sys.stderr, inst.args

            return send_file(clog, mimetype='text/plain', as_attachment=True)


@agent.route('/v1/conf/<auxComp>')
class NodeMonitConf(Resource):
    def get(self, auxComp):
        if auxComp not in auxList:
            response = jsonify({'Status': 'parameter error',
                                'Message': 'Component '+auxComp+' not supported!'})
            response.status_code = 404
            return response
        if auxComp == 'collectd':
            try:
                cConf = open(collectdConf, '+w')
            except Exception as inst:
                print >> sys.stderr, type(inst)
                print >> sys.stderr, inst.args
            return send_file(cConf, mimetype='text/plain', as_attachment=True)
        if auxComp == 'lsf':
            try:
                lConf = open(lsfConf, '+w')
            except Exception as inst:
                print >> sys.stderr, type(inst)
                print >> sys.stderr, inst.args
            return send_file(lConf, mimetype='application/json', as_attachment=True)
        if auxComp == 'jmx':  # TODO: jmxtrans handeling
            return 'jmx'


if __name__ == '__main__':
    app.run(host='0.0.0.0')
