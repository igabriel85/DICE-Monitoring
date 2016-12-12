import subprocess
import sys
import os
import datetime
import time
import jinja2
from flask import jsonify
from app import *

lockDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lock')
pidDir = '/var/run'


def installCollectd():
    '''
        Installs collectd on local node.
    '''
    collectdLock = os.path.join(lockDir, 'collectd.lock')
    if os.path.isfile(collectdLock) is True:
        # print >> sys.stderr, "Collectd already installed!"
        app.logger.warning('[%s] : [WANR] Collectd alrady installed',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
    else:
        try:
            p1 = subprocess.Popen('sudo apt-get install -y collectd', shell=True)
            p1.wait()
            app.logger.info('[%s] : [INFO] Done installing collectd',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        except Exception as inst:
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            app.logger.warning('[%s] : [WARN] Cannot install collectd: %s with %s',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            raise
        #todo install new dice.db containing new defined types
        lock = open(collectdLock, "w+")
        lock.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        lock.close()


def installLsf(listLocation, lsfGPG):
    lsfLock = os.path.join(lockDir, 'lsf.lock')
    if os.path.isfile(lsfLock) is True:
        # print >> sys.stderr, "Logstash-forwarder already installed!"
        app.logger.warning('[%s] : [WARN] LSF already installed!',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
    else:
        try:
            p1 = subprocess.Popen('sudo mv ' + listLocation + ' /etc/apt/sources.list.d/',
                                  shell=True)
            p1.wait()
            app.logger.info('[%s] : [INFO] Moved sourcelist for lsf',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        except Exception as inst:
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            app.logger.warning('[%s] : [WARN] Cannot copy lsf sourcelist: %s with %s',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            raise
        try:
            pro = subprocess.Popen('wget http://packages.elasticsearch.org/GPG-KEY-elasticsearch -O ' + lsfGPG,
                                   shell=True)
            pro.wait()
            app.logger.info('[%s] : [INFO] Done moving GPG key to %s',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), lsfGPG)
        except Exception as inst:
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            app.logger.warning('[%s] : [WARN] Cannot download GPG key for elasticsearch: %s with %s',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            raise
        try:
            p2 = subprocess.Popen('sudo apt-key add ' + lsfGPG, shell=True)
            p2.wait()
            app.logger.info('[%s] : [INFO] Added Elasticsearch GPG Key',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        except Exception as inst:
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            app.logger.warning('[%s] : [WARN] Cannot add lsf to application repository: %s with %s',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            raise
        try:
            p3 = subprocess.Popen('sudo apt-get update', shell=True)
            p3.wait()
            app.logger.info('[%s] : [INFO] Finished updating repository',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        except Exception as inst:
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            app.logger.warning('[%s] : [WARN] Cannot update application repository: %s with %s',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            raise
        try:
            p4 = subprocess.Popen('sudo apt-get install -y logstash-forwarder', shell=True)
            p4.wait()
            app.logger.info('[%s] : [INFO] Finished installing logstash-forwarder',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        except Exception as inst:
            # print >> sys.stderr, type(inst)
            # print >> sys.stderr, inst.args
            app.logger.warning('[%s] : [WARN] Cannot install logstash-forwarder: %s with %s',
                                datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            raise
        lock = open(lsfLock, "w+")
        lock.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        lock.close()


def checkPID(pid):
    """
    Check For the existence of a unix pid.
    Sending signal 0 to a pid will raise an OSError exception if the pid is not running, and do nothing otherwise.
    """
    if pid == 0:	#If PID newly created return False
        return 0
    try:
        os.kill(pid, 0)
    except OSError:
        return 0
    else:
        return 1


class AuxComponent():
    """Controlling auxiliary monitoring components
       listLocation -> location of lsf list
       GPGLocation  -> ElasticSearch GPG key Location
    """

    supported = ['collectd', 'lsf', 'jmx']

    def __init__(self, listLocation, GPGLocation):
        self.listLocation = listLocation
        self.GPGLocation = GPGLocation

    def check(self, component):
        if component not in AuxComponent.supported:
            return 0
        else:
            return 1

    def install(self, component):
        compInstalled = []
        if 'yarn' in component or 'hdfs' in component:
            if 'lsf' in compInstalled:
                pass
            else:
                installLsf(self.listLocation, self.GPGLocation)
                compInstalled.append('lsf')
            if 'collectd' in compInstalled:
                pass
            else:
                installCollectd()
                compInstalled.append('collectd')
        if 'spark' in component:
            if 'collectd' in compInstalled:
                pass
            else:
                installCollectd()
                compInstalled.append('collectd')
        if 'kafka' in component:
            if 'collectd' in compInstalled:
                pass
            else:
                installCollectd()
                compInstalled.append('collectd')
            if 'jmx' in component:
                pass
            else:
                compInstalled.append('jmx')
        if 'storm' in component:
            if 'collectd' in compInstalled:
                pass
            else:
                installCollectd()
                compInstalled.append('collectd')
            if 'jmx' in compInstalled:
                pass
            else:
                compInstalled.append('jmx')
        return compInstalled

    def controll(self, component, cmd):
        if component == 'lsf':
            component = 'logstash-forwarder'
        try:
            pro = subprocess.Popen('sudo service ' + component + ' ' + cmd, shell=True)
            pro.wait()
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            raise

    def collectdStop(self):
        try:
            cPid = open('/var/run/collectd.pid', 'r').readline()
            pidString = cPid.strip()
            pid = int(pidString)
        except IOError:
            return 0

    def checkAux(self, component):
        if component == 'collectd':
            if os.path.isfile(os.path.join(pidDir, 'collectdmon.pid')):
                app.logger.info('[%s] : [INFO] collectdmon pid file found',
                                   datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                component = 'collectdmon'
        pidPath = os.path.join(pidDir, component + '.pid')
        app.logger.info('[%s] : [INFO] Component name - %s pid file location  %s',
                        datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), component, pidPath)
        if not os.path.isfile(pidPath):
            app.logger.info('[%s] : [INFO] collectd pid file not found',
                                   datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            return 0

        try:
            pid = open(pidPath).readline()
            pidString = pid.strip()
            pidint = int(pidString)
            app.logger.info('[%s] : [INFO] Collectd started with PID: %s',
                                   datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), pidString)
        except IOError:
            return 0

        try:
            os.kill(pidint, 0)
        except OSError:
            app.logger.warning('[%s] : [WARN] PID check failed for %s',
                               datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), component)
            return 0
        else:
            return 1

        # try:
        #     p = subprocess.Popen(['service', component, 'status'], stdout=subprocess.PIPE)
        #     pOut = p.communicate()[0]
        # except Exception as inst:
        #     print >> sys.stderr, type(inst)
        #     print >> sys.stderr, inst.args
        #     raise
        #
        # if 'running' in pOut:
        #     return 1
        # elif 'unrecognized' in pOut:
        #     return 'unknown'
        # else:
        #     return 0

    def configureComponent(self, settingsDict, tmpPath, filePath):
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
        except:
            response = jsonify({'Status': 'Template Error',
                'Message': 'File not found!'})
            response.status_code = 500
            return response
        confInfo = template.render(settingsDict)
        confFile = open(filePath, "w+")
        confFile.write(confInfo)
        confFile.close()
        try:
            subprocess.Popen('echo >> ' + filePath, shell=True) # TODO fix this
            # subprocess.call(["echo", ">>", filePath])
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Cannot find %s, with %s and %s',
                             datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), filePath,
                             type(inst), inst.args)


class BDPlatform():
    sparkLoc = '/etc/spark/conf/metrics.properties'
    yarnLoc = '/etc/hadoop/conf.cloudera.yarn/hadoop-metrics2.properties'
    hdfsLoc = '/etc/hadoop/conf.cloudera.hdfs/hadoop-metrics2.properties'

    def __init__(self, tmpDir):
        self.sparkTmp = os.path.join(tmpDir, 'spark-metrics.tmp')
        self.yarnTmp = os.path.join(tmpDir, 'hadoop-metrics2.tmp')

    def generateYarnConfig(self, settingsDict):
        print "Adding Yarn properties ..."
        generateConf(self.yarnTmp, settingsDict, BDPlatform.yarnLoc)
        print "Adding HDFS Properties ..."
        generateConf(self.yarnTmp, settingsDict, BDPlatform.hdfsLoc)
        print "Done"


    def generateSparkConfig(self, settingsDict):
        print "Adding Spark properties ..."
        generateConf(self.sparkTmp, settingsDict, BDPlatform.sparkLoc)
        print "Done"


    def getRoles(self): # TODO: if no processes detected check dir structure /etc/hadoop etc.
        roleList = []
        p = subprocess.Popen(['sudo', 'jps'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate()
        if 'DataNode' in output:
            roleList.append('yarn')
        if 'NameNode' in output:
            roleList.append('yarn')
        if 'SecondaryNameNode' in output:
            roleList.append('yarn')
        if 'NodeManager' in output:
            roleList.append('yarn')
        if 'ResourceManager' in output:
            roleList.append('yarn')
        roleSet = set(roleList)
        return roleSet


def generateConf(tmpPath, settingsDict, filePath):
    '''
    :param tmpPath: path to template file
    :param settingsDict: settings dict
    :param filePath: path to saved config file
    :return:
    '''
    templateLoader = jinja2.FileSystemLoader(searchpath="/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    try:
        template = templateEnv.get_template(tmpPath)
    except:
        return "response"
    confInfo = template.render(settingsDict)
    confFile = open(filePath, "w+")
    confFile.write(confInfo)
    confFile.close()
