import jinja2
import os
import sys
import datetime
import time
from flask import jsonify
import subprocess


class pyLogstashInstance():
    tmpDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    cfgDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
    lockDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lock')
    pidDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pid')
    logstashDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logstash')
    logstashBin = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logstash/bin/')

    def generateConfig(self, settingsDict):
        templateLoader = jinja2.FileSystemLoader(searchpath="/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        try:
            template = templateEnv.get_template(os.path.join(pyLogstashInstance.tmpDir, 'logstash.tmp'))
        except:
            response = jsonify({'Status': 'Template Error',
                'Message': 'File not found!'})
            response.status_code = 500
            return response
        confInfo = template.render(settingsDict)
        confFile = open(os.path.join(pyLogstashInstance.cfgDir, 'logstash.conf'), "w+")
        confFile.write(confInfo)
        confFile.close()

    def start(self, heap='512m', worker=4):
        config = os.path.join(pyLogstashInstance.cfgDir, 'logstash.conf')
        log = os.path.join(pyLogstashInstance.lockDir, 'logstash.log')
        pidFile = os.path.join(pyLogstashInstance.pidDir, 'logstash.pid')
        pid = pyLogstashInstance.check
        if pid is True:
            subprocess.call(['kill', '-9', str(pid)])

        print 'LS_HEAP_SIZE=' + heap + ' ' + pyLogstashInstance.logstashBin+'logstash agent -f ' + config + ' -l ' + log +' -w '+str(worker)
        try:
            lspid = subprocess.Popen('LS_HEAP_SIZE=' + heap + ' ' + pyLogstashInstance.logstashBin+'logstash agent -f ' + config + ' -l ' + log +
                                     ' -w '+str(worker), shell=True).pid
        except Exception as inst:
            print >> sys.stderr, 'Problem Starting LS!'
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            response = jsonify({'Error': 'Starting LS'})
            response.status_code = 500
            return response

        try:
            newPid = open(pidFile, 'w+')
            newPid.write(str(lspid))
            newPid.close()
        except IOError:
            print >> sys.stderr, 'Problem writing LS pid!'
            response = jsonify({'Error': 'File I/O!'})
            response.status_code = 500
            return response
        return lspid

    def stop(self):
        pid = pyLogstashInstance.check()
        if pid is True:
            try:
                subprocess.call(['kill', '-9', str(pid)])
            except Exception as inst:
                 print >> sys.stderr, 'PID not found!'
                 print >> sys.stderr, type(inst)
                 print >> sys.stderr, inst.args
            return 1
        else:
            return 0

    def deploy(self):
        lslock = os.path.join(pyLogstashInstance.lockDir, 'ls.lock')
        if os.path.isfile(lslock) is True:
            print >> sys.stderr, "Logstash already installed!"
        else:
            try:
                #p4 = subprocess.Popen('plugin install http_poller', shell=True, cwd='/opt/dmon-logstash/logstash/bin')
                #p4.wait()
                ppi = subprocess.Popen(['./bootstrap.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       shell=False).communicate()
            except Exception as inst:
                print >> sys.stderr, "Error while bootstrapping!"
                print >> sys.stderr, type(inst)
                print >> sys.stderr, inst.args

            lock = open(lslock, "w+")
            lock.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            lock.close()

    def check(self):
        lsPIDfile = os.path.join(pyLogstashInstance.pidDir, 'logstash.pid')
        try:
            lsPID = open(lsPIDfile, 'r').readline()
            pidString = lsPID.strip()
            pid = int(pidString)
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            return 0

        if not checkPID(pid):
            return 0
        else:
            return pid

    def validate(self):  #TODO: implement
        return "validate configuration"


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