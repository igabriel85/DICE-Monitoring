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
import socket
import sys
import signal
import subprocess
from datetime import datetime
import time
import requests
import os
import jinja2
from flask import jsonify
from app import *
from dbModel import *
from greenletThreads import *
from urlparse import urlparse
import pandas as pd
import psutil


def portScan(addrs, ports):
    '''
        Check if a range of ports are open or not
    '''
    t1 = datetime.now()
    for address in addrs:
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sockTest = sock.connect_ex((address, int(port)))
                if sockTest == 0:
                    app.logger.info('[%s] : [INFO] Port %s on %s Open',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(port), str(address))
                    print "Port %s \t on %s Open" % (port, address)
                sock.close()
            except KeyboardInterrupt:
                print "User Intrerupt detected!"
                print "Closing ...."
                app.logger.info('[%s] : [INFO] User Intrerupt detected. Exiting',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                sys.exit()
            except socket.gaierror:
                print 'Hostname not resolved. Exiting'
                app.logger.warning('[%s] : [WARN] Hostname unresolved. Exiting',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                sys.exit()
            except socket.error:
                print 'Could not connect to server'
                app.logger.warning('[%s] : [WARN] Could not connect to server',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                sys.exit()
    #stop time
    t2 = datetime.now()

    #total time
    total = t2 - t1

    print 'Scanning Complete in: ', total
    app.logger.info('[%s] : [INFO] Scanning Complete in:  %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), total)


def checkPID(pid):
    """
    Check For the existence of a unix pid.
    Sending signal 0 to a pid will raise an OSError exception if the pid is not running, and do nothing otherwise.
    """
    if pid == 0:	#If PID newly created return False
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def startLocalProcess(command):
    '''
    Starts a process in the background and writes a pid file.
    command -> needs to be in the form of a list of basestring
            -> 'yes>/dev/null' becomes ['yes','>','/dev/null']

    Returns integer: PID
    '''
    process = subprocess.Popen(command, shell=True)
    return process.pid


def checkUnique(nodeList):
    '''
    Checks for unique values in a dictionary.
    '''
    seen = {}
    result = set()
    sameCredentials = []
    ipNode = []
    for d in nodeList:
        for k, v in d.iteritems():
            if v in seen:
                ipNode.append(k)
                sameCredentials.append(v)
                result.discard(seen[v])
            else:
                seen[v] = k
                result.add(k)
    return list(result), sameCredentials, ipNode



#print {v['nPass']:v for v in test}.values()
#print checkUnique(test)

class AgentResourceConstructor():
    uriRoot = '/agent/v1'
    uriRoot2 = '/agent/v2'
    chck = '/check'
    clctd = '/collectd'
    logsf = '/lsf'
    jmxr = '/jmx'
    confr = '/conf'
    logsr = '/logs'
    deployr = '/deploy'
    noder = '/node'
    startr = '/start'
    stopr = '/stop'
    slogs = '/bdp/storm/logs'
    shutDown = '/shutdown'

    def __init__(self, IPList, Port):
        self.IPList = IPList
        self.Port = Port

    def check(self):
        resourceList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot,
                                            AgentResourceConstructor.chck)
            resourceList.append(resource)
        return resourceList

    def collectd(self):
        cList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot,
                                            AgentResourceConstructor.clctd)
            cList.append(resource)
        return cList

    def lsf(self):
        lList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot,
                                            AgentResourceConstructor.logsf)
            lList.append(resource)
        return lList

    def jmx(self):
        jList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot,
                                            AgentResourceConstructor.jmxr)
            jList.append(resource)
        return jList

    def deploy(self):
        dList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot,
                                            AgentResourceConstructor.deployr)
            dList.append(resource)
        return dList

    def node(self):
        nList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot,
                                            AgentResourceConstructor.noder)
            nList.append(resource)
        return nList

    def start(self):
        sList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot,
                                            AgentResourceConstructor.startr)
            sList.append(resource)
        return sList

    def stop(self):
        stList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot,
                                            AgentResourceConstructor.stopr)
            stList.append(resource)
        return stList

    def startSelective(self, comp):
        ssList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s/%s' %(ip, self.Port, AgentResourceConstructor.uriRoot,
                                               AgentResourceConstructor.startr, comp)
            ssList.append(resource)
        return ssList

    def stopSelective(self, comp):
        stsList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s/%s' %(ip, self.Port, AgentResourceConstructor.uriRoot,
                                               AgentResourceConstructor.stopr, comp)
            stsList.append(resource)
        return stsList

    def logs(self, comp):
        logList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s/%s' %(ip, self.Port, AgentResourceConstructor.uriRoot,
                                               AgentResourceConstructor.logsr, comp)
            logList.append(resource)
        return logList

    def conf(self, comp):
        confList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s/%s' %(ip, self.Port, AgentResourceConstructor.uriRoot,
                                               AgentResourceConstructor.stopr, comp)
            confList.append(resource)
        return confList

    def stormLogs(self):
        logList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot2, AgentResourceConstructor.slogs)
            logList.append(resource)
        return logList

    def shutdownAgent(self):
        shutdownList = []
        for ip in self.IPList:
            resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot, AgentResourceConstructor.shutDown)
            shutdownList.append(resource)
        return shutdownList


def dbBackup(db, source, destination, version=1):
    '''
    :param db: -> database
    :param source: -> original name
    :param destination: -> new name
    :return:
    '''

    vdest = destination + str(version)
    if os.path.isfile(source) is True:
        if os.path.isfile(vdest) is True:
            return dbBackup(db, source, destination, version + 1)
        os.rename(source, destination)


def detectStormTopology(ip, port=8080):
    '''
    :param ip: IP of the Storm REST API
    :param port: Port of the Storm REST API
    :return: topology name
    '''
    url = 'http://%s:%s/api/v1/topology/summary' %(ip, port)
    try:
        r = requests.get(url, timeout=DMON_TIMEOUT)
    except requests.exceptions.Timeout:
        app.logger.error('[%s] : [ERROR] Cannot connect to %s timedout',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(url))
        raise
    except requests.exceptions.ConnectionError:
        app.logger.error('[%s] : [ERROR] Cannot connect to %s error',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(url))
        raise

    topologySummary = r.json()
    app.logger.info('[%s] : [INFO] Topologies detected at %s are: %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(ip), str(topologySummary))
    return topologySummary.get('topologies')[0]['id']


def validateIPv4(s):
    '''
    :param s: -> IP as string
    :return:
    '''
    pieces = s.split('.')
    if len(pieces) != 4:
        return False
    try:
        return all(0 <= int(p) < 256 for p in pieces)
    except ValueError:
        return False


def checkStormSpoutsBolts(ip, port, topology):
    '''
    :param ip: IP of the Storm REST API
    :param port: Port of th Storm REST API
    :param topology: Topology ID
    :return:
    '''
    ipTest = validateIPv4(ip)
    if not ipTest:
        return 0, 0
    if not port.isdigit():
        return 0, 0
    url = 'http://%s:%s/api/v1/topology/%s' %(ip, port, topology)
    try:
        r = requests.get(url, timeout=DMON_TIMEOUT)
    except requests.exceptions.Timeout:
        app.logger.error('[%s] : [ERROR] Cannot connect to %s timedout',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(url))
        return 0, 0
    except requests.exceptions.ConnectionError:
        app.logger.error('[%s] : [ERROR] Cannot connect to %s error',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(url))
        return 0, 0
    if r.status_code != 200:
        return 0, 0

    return len(r.json()['bolts']), len(r.json()['spouts'])


def configureComponent(settingsDict, tmpPath, filePath): #TODO modify /v1/overlord/aux/<auxComp>/config using this function
        '''
        :param settingsDict: dictionary containing the template information
        :param tmpPath:  path to template file
        :param filePath: path to save config file
        :return:
        '''
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        try:
            template = templateEnv.get_template(tmpPath)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Cannot find %s, with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), filePath,
                             type(inst), inst.args)
            return 0
        confInfo = template.render(settingsDict)
        confFile = open(filePath, "w+")
        confFile.write(confInfo)
        confFile.close()
        try:
            subprocess.Popen('echo >> ' + filePath, shell=True) # TODO fix this
            # subprocess.call(["echo", ">>", filePath])
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Cannot find %s, with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), filePath,
                             type(inst), inst.args)
            return 0
        return 1


class DetectBDService():

    def checkRegistered(self, service):
        '''
        :param service: Name of BD service role to check for
        :param dbNodes: Query for all database nodes
        :return:
        '''


        return 'Check registered %s information' %service

    def detectYarnHS(self): #TODO: Document detected at first detection, unchanged if server still responds and updated if it has to be redetected and no longer matches stored values
        '''
        :param dbNodes: Query for all database nodes
        :return:
        '''
        qNode = dbNodes.query.all()
        qDBS = dbBDService.query.first()
        if qDBS is not None:
            yhUrl = 'http://%s:%s/ws/v1/history/mapreduce/jobs'%(qDBS.yarnHEnd, qDBS.yarnHPort)
            try:
                yarnResp = requests.get(yhUrl, timeout=DMON_TIMEOUT)
                yarnData = yarnResp.json()
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Cannot connect to yarn history service with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                             type(inst), inst.args)
                yarnData = 0

            if yarnData:
                rspYarn = {}
                rspYarn['Jobs'] = yarnData['jobs']
                rspYarn['NodeIP'] = qDBS.yarnHEnd
                rspYarn['NodePort'] = qDBS.yarnHPort
                rspYarn['Status'] = 'Unchanged'
                response = jsonify(rspYarn)
                response.status_code = 200
                return response

        if qNode is None:
            response = jsonify({'Status': 'No registered nodes'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No nodes found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        yarnNodes = []
        for n in qNode:
            if "yarn" in n.nRoles:
                yarnNodes.append(n.nodeIP)
        if not yarnNodes:
            response = jsonify({'Status': 'Yarn role not found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARNING] No nodes have yarn role',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        resList = []
        for n in yarnNodes:
            url = 'http://%s:%s/ws/v1/history/mapreduce/jobs' %(n, '19888')
            resList.append(url)
        app.logger.info('[%s] : [INFO] Resource list for yarn history server discovery -> %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), resList)
        dmonYarn = GreenletRequests(resList)
        nodeRes = dmonYarn.parallelGet()
        yarnJobs = {}
        for i in nodeRes:  #TODO: not handled if more than one node resonds as a history server
            nodeIP = urlparse(i['Node'])
            data = i['Data']
            if data !='n/a':
                try:
                    yarnJobs['Jobs'] = data['jobs']['job']
                except Exception as inst:
                    app.logger.warning('[%s] : [WARN] Cannot read job list,  with %s and %s',
                                       datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                       inst.args)
                    response = jsonify({'Status': 'Cannot read job list'})
                    response.status_code = 500
                    return response
                yarnJobs['NodeIP'] = nodeIP.hostname
                yarnJobs['NodePort'] = nodeIP.port
                yarnJobs['Status'] = 'Detected'

        if not yarnJobs:
            response = jsonify({'Status': 'No Yarn history Server detected'})
            response.status_code = 404
            app.logger.error('[%s] : [ERROR] No Yarn History Server detected',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response

        if qDBS is None:
            upBDS = dbBDService(yarnHPort=yarnJobs['NodePort'], yarnHEnd=yarnJobs['NodeIP'])
            db.session.add(upBDS)
            db.session.commit()
            app.logger.info('[%s] : [INFO] Registred Yarn History server at %s and port %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), yarnJobs['NodeIP'],
                         yarnJobs['NodePort'])
        else:
            qDBS.yarnHEnd = yarnJobs['NodeIP']
            qDBS.yarnHPort = yarnJobs['NodePort']
            yarnJobs['Status'] = 'Updated'
            app.logger.info('[%s] : [INFO] Updated Yarn History server at %s and port %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), yarnJobs['NodeIP'],
                         yarnJobs['NodePort'])
        response = jsonify(yarnJobs)
        if yarnJobs['Status'] == 'Updated':
            response.status_code = 201
        else:
            response.status_code = 200
        return response

    def detectStormRS(self, dbNodes):
        '''
        :param dbNodes: Query for all database nodes
        :return:
        '''
        return 'Detect Storm Rest Service'

    def detectSparkHS(self, dbNodes):
        '''
        :param dbNodes: Query for all database nodes
        :return:
        '''
        qNode = dbNodes.query.all()
        qDBS = dbBDService.query.first()
        if qDBS is not None:
            yhUrl = 'http://%s:%s/api/v1/applications'%(qDBS.sparkHEnd, qDBS.sparkHPort)
            try:
                sparkResp = requests.get(yhUrl, timeout=DMON_TIMEOUT)
                ysparkData = sparkResp.json()
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Cannot connect to spark history service with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                             type(inst), inst.args)
                ysparkData = 0

            if ysparkData:
                rspSpark = {}
                rspSpark['Jobs'] = ysparkData['jobs']
                rspSpark['NodeIP'] = qDBS.sparkHEnd
                rspSpark['NodePort'] = qDBS.sparkHPort
                rspSpark['Status'] = 'Unchanged'
                response = jsonify(rspSpark)
                response.status_code = 200
                return response

        if qNode is None:
            response = jsonify({'Status': 'No registered nodes'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARN] No nodes found',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        sparkNodes = []
        for n in qNode:
            if "spark" in n.nRoles:
                sparkNodes.append(n.nodeIP)
        if not sparkNodes:
            response = jsonify({'Status': 'Spark role not found'})
            response.status_code = 404
            app.logger.warning('[%s] : [WARNING] No nodes have spark role',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return response
        resList = []
        for n in sparkNodes:
            url = 'http://%s:%s/api/v1/applications' %(n, '19888')
            resList.append(url)
        app.logger.info('[%s] : [INFO] Resource list for spark history server discovery -> %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), resList)
        dmonSpark = GreenletRequests(resList)
        nodeRes = dmonSpark.parallelGet()
        sparkJobs = {}
        for i in nodeRes:  #TODO: not handled if more than one node resonds as a history server
            nodeIP = urlparse(i['Node'])
            data = i['Data']
            if data !='n/a':
                try:
                    sparkJobs['Jobs'] = data
                except Exception as inst:
                    app.logger.warning('[%s] : [WARN] Cannot read job list,  with %s and %s',
                                       datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst),
                                       inst.args)
                sparkJobs['NodeIP'] = nodeIP.hostname
                sparkJobs['NodePort'] = nodeIP.port
                sparkJobs['Status'] = 'Detected'

        if qDBS is None:
            upBDS = dbBDService(sparkHPort=sparkJobs['NodePort'], sparkHEnd=sparkJobs['NodeIP'])
            db.session.add(upBDS)
            db.session.commit()
            app.logger.info('[%s] : [INFO] Registred Spark History server at %s and port %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), sparkJobs['NodeIP'],
                         sparkJobs['NodePort'])
        else:
            qDBS.yarnHEnd = sparkJobs['NodeIP']
            qDBS.yarnHPort = sparkJobs['NodePort']
            sparkJobs['Status'] = 'Updated'
            app.logger.info('[%s] : [INFO] Updated Spark History server at %s and port %s',
                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), sparkJobs['NodeIP'],
                         sparkJobs['NodePort'])
        response = jsonify(sparkJobs)
        if sparkJobs['Status'] == 'Updated':
            response.status_code = 201
        else:
            response.status_code = 200
        return response

    def detectServiceRA(self, service):
        return 'Generic detection of services'


def checkCoreState(esPidf, lsPidf, kbPidf):  #TODO: works only for local deployment, change for distributed
    '''
    :param esPidf: Elasticserch PID file location
    :param lsPidf: Logstash PID file location
    :param kbPidf: Kibana PID file location
    '''
    qESCore = dbESCore.query.first()
    qLSCore = dbSCore.query.first()
    qKBCore = dbKBCore.query.first()
    if not os.path.isfile(esPidf):
        if qESCore is None:
            app.logger.warning('[%s] : [WARN] No ES Core service registered to DMon',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        else:
            app.logger.info('[%s] : [INFO] PID file not found, setting pid to 0 for local ES Core')
            qESCore.ESCorePID = 0
    else:
        with open(esPidf) as esPid:
            vpid = esPid.read()
            esStatus = checkPID(int(vpid))
            if esStatus:
                if qESCore is None:
                    app.logger.warning('[%s] : [WARN] No ES Core service registered to DMon',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    app.logger.info('[%s] : [INFO] PID file found for LS Core service with value %s',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                    str(vpid))
                    qESCore.ESCorePID = int(vpid)
            else:
                if qESCore is None:
                    app.logger.warning('[%s] : [WARN] No ES Core service registered to DMon',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    app.logger.info('[%s] : [INFO] PID file found for ES Core service, not service tunning at pid %s. Setting value to 0',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                    str(vpid))
                    qESCore.ESCorePID = 0

    if not os.path.isfile(lsPidf):
        if qLSCore is None:
            app.logger.warning('[%s] : [WARN] No LS Core service registered to DMon',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        else:
            app.logger.info('[%s] : [INFO] PID file not found, setting pid to 0 for local LS Core',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            qLSCore.LSCorePID = 0
    else:
        with open(lsPidf) as lsPid:
            wpid = lsPid.read()
            lsStatus = checkPID(int(wpid))
            if lsStatus:
                if qLSCore is None:
                    app.logger.warning('[%s] : [WARN] No LS Core service registered to DMon',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    app.logger.info('[%s] : [INFO] PID file  found for LS Core service, with value %s',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                    str(wpid))
                    qLSCore.LSCorePID = int(wpid)
            else:
                if qLSCore is None:
                    app.logger.warning('[%s] : [WARN] No LS Core service registered to DMon',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    app.logger.info('[%s] : [INFO] PID file found for ES Core service, not service tunning at pid %s. Setting value to 0',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    qLSCore.LSCorePID = 0

    if not os.path.isfile(kbPidf):
        if qKBCore is None:
            app.logger.warning('[%s] : [WARN] No KB Core service registered to DMon',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        else:
            app.logger.info('[%s] : [INFO] PID file not found, setting pid to 0 for local KB Core')
            qKBCore.KBCorePID = 0
    else:
        with open(kbPidf) as kbPid:
            qpid = kbPid.read()
            kbStatus = checkPID(int(qpid))
            if kbStatus:
                if qKBCore is None:
                    app.logger.warning('[%s] : [WARN] No KB Core service registered to DMon',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    app.logger.info('[%s] : [INFO] PID file  found for KB Core service, with value %s',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                                    str(qpid))
                    qKBCore.KBCorePID = int(qpid)
            else:
                if qKBCore is None:
                    app.logger.warning('[%s] : [WARN] No KB Core service registered to DMon',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    app.logger.info('[%s] : [INFO] PID file found for KB Core service, not service tunning at pid %s. Setting value to 0',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    qKBCore.KBCorePID = 0


def str2Bool(st):
    '''
    :param st: -> string to test
    :return: -> if true then returns 1 else 0
    '''
    if type(st) is bool:
        return st
    if st in ['True', 'true', '1']:
        return 1
    elif st in ['False', 'false', '0']:
        return 0
    else:
        return 0


def csvheaders2colNames(csvfile, adname):
    '''
    :param csvfile: -> input csv or dataframe
    :param adname: -> string to add to column names
    :param df: -> if set to false csvfile is used if not df is used
    :return:
    '''
    colNames = {}
    if isinstance(csvfile, pd.DataFrame):
        for e in csvfile.columns.values:
            if e == 'key':
                pass
            else:
                colNames[e] = '%s_%s' % (e, adname)
    else:
        return 0
    return colNames


def check_proc(pidfile, wait=5):
    '''
    :param pidfile: -> location of pid
    :return: -> return pid
    '''
    tick = 0
    time.sleep(wait)
    while not os.path.exists(pidfile):
        time.sleep(1)
        tick += 1
        if tick > wait:
            return 0
    stats_pid = open(pidfile)
    try:
        pid = int(stats_pid.read())
    except ValueError:
        return 0
    return pid


def sysMemoryCheck(needStr):
    '''
    :param needStr: heap size string setting of the format "512m"
    :return: returns True or False depending if check is successful or not and returns the final heap size
    '''
    mem = psutil.virtual_memory().total
    need = int(needStr[:-1])
    unit = needStr[-1]
    if unit == 'm':
        hmem = mem / 1024 / 1024
    elif unit == 'g':
        hmem = mem / 1024 / 1024 / 1024
    else:
        app.logger.error('[%s] : [ERROR] Unknown heap size format %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), needStr)
        hmem = mem / 1024 / 1024
        return False, "%s%s" % (str(hmem / 2), 'm')
    if need > hmem:
        return False, "%s%s" % (str(hmem / 2), unit)
    else:
        return True, needStr

if __name__ == '__main__':
#     db.create_all()
#     test = DetectBDService()
#     what = test.detectYarnHS()
#     print what
    test = AgentResourceConstructor(['85.120.206.45', '85.120.206.47', '85.120.206.48', '85.120.206.49'], '5222')
    listLogs = test.stormLogs()
    print listLogs
    # t = test.check()
    # c = test.collectd()
    # l = test.lsf()
    # j = test.jmx()
    # d = test.deploy()
    # n = test.node()
    # s = test.start()
    # st = test.stop()
    # ss = test.startSelective('lsf')
    # sts = test.stopSelective('collectd')
    # log = test.logs('lsf')
    # conf = test.conf('collectd')
    # print t
    # print c
    # print l
    # print j
    # print d
    # print n
    # print s
    # print st
    # print ss
    # print sts
    # print log
    # print conf