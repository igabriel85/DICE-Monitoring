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
collectdConf = '/etc/collectd/collectd.conf'
lsfConf = '/etc/logstash-forwarder.conf'
lsfList = os.path.join(tmpDir, 'logstashforwarder.list')
lsfGPG = os.path.join(tmpDir, 'GPG-KEY-elasticsearch')

# supported aux components
# auxList = ['collectd', 'lsf', 'jmx']

app = Flask("dmon-agent")
api = Api(app, version='0.0.3', title='DICE Monitoring Agent API',
          description="RESTful API for the DICE Monitoring Platform  Agent (dmon-agent)",
          )


# changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
agent = api.namespace('agent', description='dmon agent operations')

nodeRoles = api.model('query details Model', {
    'roles': fields.List(fields.String(required=False, default='hdfs',
                                       description='Roles assigned to this node!'))
})


collectdConfModel = api.model('configuration details Model for collectd', {
    'LogstashIP': fields.String(required=True, default='127.0.0.1', description='IP of the Logstash Server'),
    'UDPPort': fields.String(required=True, default='25826', description='Port of UDP plugin from Logstash Server'),
})

lsfConfModel = api.model('configuration details Model for LSF', {
    'LogstashIP': fields.String(required=True, default='127.0.0.1', description='IP of the Logstash Server'),
    'LumberjackPort': fields.String(required=True, default='5000', description='Logstash Lumberjack input port')
})

yarnProperties = api.model('Yarn properties configuration Model', {
    'Period': fields.String(required=True, default='10', description='Polling period for all Yarn/HDFS metrics')
})

sparkProperties = api.model('Spark properties configuration Model', {
    'LogstashIP': fields.String(required=True, default='109.231.121.210', description='Logstash IP (only Spark)'),
    'GraphitePort': fields.String(required=True, default='5002', description='Logstash Graphite input Port (only Spark)'),
    'Period': fields.String(required=True, default='5', description='Spark Polling Period')
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
    def post(self):
        rolesList = request.json['roles']
        try:
            aComp = aux.install(rolesList)
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            response = jsonify({'Status': 'System Error',
                               'Message': 'Error while installing components'})
            response.status_code = 500
            return response
        response = jsonify({'Status': 'Done',
                            'Components': aComp})
        response.status_code = 201
        return response


@agent.route('/v1/collectd')
class NodeDeployCollectd(Resource):
    @api.expect(collectdConfModel)
    def post(self):
        collectdTemp = os.path.join(tmpDir, 'collectd.tmp')
        settingsDict = {'logstash_server_ip': request.json['LogstashIP'], 'logstash_server_port': request.json['UDPPort'],
                        'collectd_pid_file': '/var/run/collectd.pid'}
        aux.configureComponent(settingsDict, collectdTemp, collectdConf)
        aux.controll('collectd', 'restart')
        response = jsonify({'Status': 'Done',
                            'Message': 'Collectd Started'})
        response.status_code = 200
        return response


@agent.route('/v1/lsf')
class NodeDeployLSF(Resource):
    @api.expect(lsfConfModel)
    def post(self):
        lsfTemp = os.path.join(tmpDir, 'logstash-forwarder.tmp')
        settingsDict  = {'ESCoreIP': request.json['LogstashIP'], 'LSLumberPort': request.json['LumberjackPort']}
        aux.configureComponent(settingsDict, lsfTemp)
        aux.controll('logstash-forwarder', 'restart')
        response = jsonify({'Status': 'Done',
                            'Message': 'LSF Stated'})
        response.status_code = 200
        return response


@agent.route('/v1/jmx')
class NodeDeployJMX(Resource):
    def post(self):
        return "JMX redeploy"


@agent.route('/v1/start')
class NodeMonitStartAll(Resource):
    def post(self):
        try:
            aux.controll('collectd', 'start')
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            response = jsonify({'Status': type(inst),
                               'Message': inst.args})
            response.status_code = 500
            return response
        try:
            aux.controll('logstash-forwarder', 'start')
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            response = jsonify({'Status': type(inst),
                               'Message': inst.args})
            response.status_code = 500
            return response
        response = jsonify({'Status': 'Started',
                            'Message': 'Auxiliary components started!'})
        response.status_code = 200
        return response


@agent.route('/v1/stop')
class NodeMonitStopAll(Resource):
    def post(self):
        try:
            aux.controll('collectd', 'stop')
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            response = jsonify({'Status': type(inst),
                               'Message': inst.args})
            response.status_code = 500
            return response
        try:
            aux.controll('logstash-forwarder', 'stop')
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            response = jsonify({'Status': type(inst),
                               'Message': inst.args})
            response.status_code = 500
            return response
        response = jsonify({'Status': 'Stopped',
                            'Message': 'Auxiliary components stopped!'})
        response.status_code = 200
        return response


@agent.route('/v1/start/<auxComp>')
class NodeMonitStartSelective(Resource):
    def post(self, auxComp):
        if not aux.check(auxComp):
            response = jsonify({'Status': 'Parameter error',
                                'Message': 'Unsupported Parameter' + auxComp})
            response.status_code = 400
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
        response = jsonify({'Status': 'Done',
                            'Message': 'Component ' + auxComp + ' started!'})
        response.status_code = 200
        return response


@agent.route('/v1/stop/<auxComp>')
class NodeMonitStopSelective(Resource):
    def post(self, auxComp):
        if not aux.check(auxComp):
            response = jsonify({'Status': 'Parameter error',
                                'Message': 'Unsupported Parameter' + auxComp})
            response.status_code = 400
            return response

        try:
            aux.controll(auxComp, 'stop')
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            response = jsonify({'Status': type(inst),
                               'Message': inst.args})
            response.status_code = 500
            return response
        response = jsonify({'Status': 'Done',
                            'Message': 'Component '+auxComp+' stopped!'})
        response.status_code = 200
        return response


@agent.route('/v1/logs/<auxComp>')
class NodeMonitLogs(Resource):
    def get(self, auxComp):
        if not aux.check(auxComp):
            response = jsonify({'Status': 'Parameter error',
                                'Message': 'Unsupported Parameter' + auxComp})
            response.status_code = 400
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
        if not aux.check(auxComp):
            response = jsonify({'Status': 'Parameter error',
                                'Message': 'Unsupported Parameter' + auxComp})
            response.status_code = 400
            return response
        if auxComp == 'collectd':
            try:
                cConf = open(collectdConf, 'r')
            except Exception as inst:
                print >> sys.stderr, type(inst)
                print >> sys.stderr, inst.args
            return send_file(cConf, mimetype='text/plain', as_attachment=True)
        if auxComp == 'lsf':
            try:
                lConf = open(lsfConf, 'r')
            except Exception as inst:
                print >> sys.stderr, type(inst)
                print >> sys.stderr, inst.args
            return send_file(lConf, mimetype='application/json', as_attachment=True)
        if auxComp == 'jmx':  # TODO: jmxtrans handeling
            return 'jmx'

@agent.route('/v1/check')
class NodeCheck(Resource):  # TODO: implement check functionality
    def get(self):
        rCollectd = aux.checkAux('collectd')
        rLSF = aux.checkAux('logstash-forwarder')
        response = jsonify({'Collectd': rCollectd,
                            'LSF': rLSF})
        response.status_code = 200
        return response


@agent.route('/v1/bdp/<platform>')  #TODO: Needs testing
class AgentMetricsSystem(Resource):
    @api.expect(sparkProperties)
    def post(self, platform):
        if not request.json:
            response = jsonify({'Status': 'Request Error',
                                'Message': 'Request body must be JSON'})
            response.status_code = 400
            return response
        BDService = BDPlatform(tmpDir)
        if platform == 'yarn':
            if not BDService.checkRole('yarn'):
                response = jsonify({'Status': 'Error',
                                    'Message': 'Yarn not detected!'})
                response.status_code = 404
                return response
            if 'Period' not in request.json:
                response = jsonify({'Status': 'Request Error',
                                'Message': 'Must contain Period field'})
                response.status_code = 400
                return response
            settingsDict = {'metrics2_period': request.json['Period']}
            BDService.generateYarnConfig(settingsDict)
            response = jsonify({'Status': 'Done',
                            'Message': 'Yarn properties uploaded'})
            response.status_code = 200
            return response
        if platform == 'spark':
            if not BDService.checkRole('spark'):
                response = jsonify({'Status': 'Error',
                                    'Message': 'Spark not detected!'})
                response.status_code = 404
                return response
            if 'Period' or 'LogstashIP' or 'GraphitePort' not in request.json:
                response = jsonify({'Status': 'Request Error',
                                'Message': 'Must contain Period, Logstash IP and Graphite Port fields'})
                response.status_code = 400
                return response
            settingsDict = {'logstashserverip': request.json['LogstashIP'],
                        'logstashportgraphite': request.json['GraphitePort'],
                        'period': request.json['Period']}
            BDService.generateSparkConfig(settingsDict)
            response = jsonify({'Status': 'Done',
                            'Message': 'Spark properties uploaded'})
            response.status_code = 200
            return response
        else:
            response = jsonify({'Status': 'Unsupported',
                                'Message': 'Platform Unsupported'})
            response.status_code = 404
            return response


if __name__ == '__main__':
    app.run(host='0.0.0.0')
