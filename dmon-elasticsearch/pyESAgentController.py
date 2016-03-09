import os
from jsonschema import validate
import jinja2
from flask import jsonify
from app import *
import datetime
import time
import subprocess

class ESAgentController():
    """
        Controlls local deployment of elasticsearch
    """

    def __init__(self, esLoc, tempLoc, pidLoc, logLoc, configLoc, schema):
        self.esLoc = esLoc
        self.tempLoc = tempLoc
        self.pidLoc = pidLoc
        self.logLoc = logLoc
        self.configLoc = configLoc
        self.schema = schema

    def generateConfig(self, stateDict):
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        try:
            template = templateEnv.get_template(os.path.join(ESAgentController.tempLoc, 'elasticsearch.tmp'))
        except:
            response = jsonify({'Status': 'Template Error',
                'Message': 'File not found!'})
            response.status_code = 500
            app.logger.error('[%s] : [ERROR] Template file not found',
                        datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        confInfo = template.render(stateDict)
        confFile = open(os.path.join(ESAgentController.configLoc, 'elasticsearch.yml'), "w+")
        confFile.write(confInfo)
        confFile.close()

        #TODO: better solution
        os.system('rm -rf /opt/elasticsearch/config/elasticsearch.yml')
        os.system('cp %s /opt/elasticsearch/config/elasticsearch.yml',
                  os.path.join(ESAgentController.configLoc, 'elasticsearch.yml'))

        app.logger.info('[%s] : [INFO] ElasticSearch config generated.',
                        datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

    def checkPID(self):
        esPIDFile = os.path.join(ESAgentController.pidLoc, 'elasticsearch.pid')
        try:
            esPID = open(esPIDFile, 'r').readline()
            pidStr = esPID.strip()
            pid = int(pidStr)
        except Exception as inst:
            app.logger.warning('[%s] : [WARN] Reading PID file with: %s, %s', type(inst), inst.args)
            return 0

        if not checkPID(pid):
            return 0
        else:
            return pid

    def start(self):
        pid = ESAgentController.checkPID
        if pid is True:
            subprocess.call(['kill', -15, str(pid)])
            app.logger.info('[%s] : [INFO] Stopping Elasticsearch detected instance with PID:  %s',
                        datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(pid))
        esCommandString = os.path.join(ESAgentController.esLoc, 'bin/elasticsearch')
        try:
            esPID = subprocess.Popen(esCommandString, shell=True).pid
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Error starting Elasticsearch with :%s args:%s',
                        datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                             inst.args)
            response = jsonify({'Error': 'Starting ES'})
            response.status_code = 500
            return response
        app.logger.info('[%s] : [INFO]  Elasticsearch Started with  PID:  %s',
                        datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(esPID))
        try:
            newPid = open(os.path.join(ESAgentController.pidLoc, 'elasticsearch.pid'), 'w+')
            newPid.write(str(esPID))
            newPid.close()
        except IOError:
            response = jsonify({'Error': 'File I/O!'})
            response.status_code = 500
            app.logger.error('[%s] : [ERROR] Error reading Elasticsearch PID',
                        datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        return esPID

    def stop(self):
        pid = ESAgentController.check
        if pid is True:
            try:
                subprocess.call(['kill', '-15', str(pid)])
            except Exception as inst:
                app.logger.warning('[%s]: [WARN] No Elasticsearch instance found with PID: %s',
                                   datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(pid))
                return 1
        else:
            return 0

    def execCmd(self, cmd):
        return 'Execute Something'

    def addTemplate(self):
        return "New Template addition"

    def generateJSONSchema(self, jsonTemplate):
        return "JSON Schema"

    def checkInput(self, request):
        validate(request, ESAgentController.schema)


def checkPID(pid):
    '''
    :param pid: pid to check
    :return: return 1 if pid found 0 if not
    '''
    if pid == 0:
        return 0
    try:
        os.kill(pid, 0)
    except OSError:
        return 0
    else:
        return 1