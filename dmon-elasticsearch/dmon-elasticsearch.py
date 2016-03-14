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
import json
import logging
from logging.handlers import RotatingFileHandler
import datetime
import time


from app import *
from pyESAgentController import *

#directory location

tmpDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
pidDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pid')
logDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
cfgDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
pldDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'payload')
esDir = '/opt/elasticsearch'

schema = 'dummy'

esController = ESAgentController(configLoc=cfgDir, tempLoc=tmpDir,
                                 esLoc=esDir, pidLoc=pidDir, logLoc=logDir, schema=schema)


esCacheModel = api.model('ES Cache Model', {
    'fieldDataCacheSize': fields.String(required=False, default="20%", description='Cache Size for field data'),
    'fieldDataCacheExpires': fields.String(required=False, default="6h", description='Field data expiration time'),
    'cacheFilterSize': fields.String(required=False, default="20%", description='Cache filter size'),
    'cacheFilterExpires': fields.String(required=False, default="6h", description='Cache filter expiration time')
})

esIndexSettingModel = api.model('ES Index Model', {
    'bufferSize': fields.String(required=False, default="30%", description='Index Buffer Size'),
    'minShardBufferSize': fields.String(required=False, default="12mb", description='Min Shard Index  Buffer Size'),
    'minIndexBufferSize': fields.String(required=False, default="96mb", description='Min Index Buffer Size')
})

esConfModel = api.model('ES Conf Model', {
    'clusterName': fields.String(required=True, default="diceMonit", description='The name given to the ES cluster'),
    'nodeID': fields.String(required=True, default="esMaster", description='The name given to the ES node'),
    'nodeMaster': fields.String(required=True, default="True", description='Set node as Master'),
    'nodeData': fields.String(required=True, default="True", description='Allow node to store data'),
    'shards': fields.Integer(required=True, default=5, description='Number of shards'),
    'replicas': fields.Integer(required=True, default=1, description='Number of replicas'),
    'networkHost': fields.String(required=True, default="0.0.0.0", description='Network host IP'),
    'cacheSettings': fields.Nested(esCacheModel, description="Cache settings"),
    'indexSettings': fields.Nested(esIndexSettingModel, description="Index settings")
})


@agent.route('/v1/logs')
class NodeLogs(Resource):
    def get(self):
        logList = os.listdir(logDir)
        response = jsonify({'Logs': logList})
        response.status_code = 200
        return response


@agent.route('/v1/logs/<log>')
class NodeLog(Resource):
    def get(self, log):
        delasticlog = os.path.join(logDir, log)

        if not os.path.isfile(delasticlog):
            response = jsonify({'Status': 'Env Error',
                                'Message': 'Log file not found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No log found at: %s',
                               datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(delasticlog))
            return response
        try:
            logFile = open(os.path.join(logDir, log), 'r')
        except IOError:
            response = jsonify({'Error': 'File I/O!'})
            response.status_code = 500
            app.logger.error('[%s] : [ERROR] Error reading log file',
                        datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        return send_file(logFile, mimetype='text/plain', as_attachment=True)


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
class ESCertificates(Resource):
    def get(self):
        return "List of certificates from certificate directory"

    def post(self):
        return "Send new certificate!"


@agent.route('/v1/elasticsearch')
class ESController(Resource):
    def get(self):
        if not os.path.isfile(os.path.join(pidDir, 'elasticsearch.pid')):
            response = jsonify({'Status': 'Env Error',
                                'Message': 'PID file not found!'})
            response.status_code = 404
            app.logger.warning('[%s]: [WARN] No Elasticsearch pid file found',
                               datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        status = esController.checkPID

        if not status:
            response = jsonify({'Status': 'Stopped',
                                'Message': 'No ES instance found'})
            response.status_code = 200
            app.logger.info('[%s]: [INFO] No running Elastcisearch instance found',
                            datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        else:
            response = jsonify({'Status': 'Running',
                                'Message': 'PID ' + status})
            response.status_code = 200
            app.logger.info('[%s]: [INFO] Elasticsearch instance runnning with PID %s',
                            datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(status))
        return response


@agent.route('/v1/elasticsearch/state')
class ESControllerState(Resource):
    def get(self):
        return "Last succesfull JSON config!"


@agent.route('/v1/elasticsearch/config')
class ESControllerConfig(Resource):
    def get(self):
        return "Get current configuration"

    @api.expect(esConfModel)
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


if __name__ == '__main__':
    handler = RotatingFileHandler(logDir + '/dmon-elasticsearch.log', maxBytes=10000000, backupCount=5)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)
    app.run(host='0.0.0.0', port=5000, debug=True)
