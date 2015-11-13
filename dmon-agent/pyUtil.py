import subprocess
import sys
import os
import datetime
import time
import jinja2


lockDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lock')


def installCollectd():
    '''
        Installs collectd on local node.
    '''
    collectdLock = os.path.join(lockDir, 'collectd.lock')
    if os.path.isfile(collectdLock) is True:
        print >>sys.stderr, "Collectd already installed!"
    else:
        try:
            p1 = subprocess.Popen('sudo apt-get install -y collectd', shell=True)
            p1.wait()
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            raise
        lock = open(collectdLock, "w+")
        lock.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        lock.close()


def installLsf(listLocation, lsfGPG):
    lsfLock = os.path.join(lockDir, 'lsf.lock')
    if os.path.isfile(lsfLock) is True:
        print >>sys.stderr, "Logstash-forwarder already installed!"
    else:
        try:
            p1 = subprocess.Popen('sudo mv '+listLocation+' /etc/apt/source.list.d/logstashforwarder.list', shell=True)
            p1.wait()
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            raise
        try:
            pro = subprocess.Popen('wget http://packages.elasticsearch.org/GPG-KEY-elasticsearch -O '+ lsfGPG, shell=True)
            pro.wait()
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            raise
        try:
            p2 = subprocess.Popen('sudo apt-key add '+lsfGPG, shell=True)
            p2.wait()
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            raise
        try:
            p3 = subprocess.Popen('sudo apt-get update', shell=True)
            p3.wait()
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            raise
        try:
            p4 = subprocess.Popen('sudo apt-get install -y logstash-forwarder', shell=True)
            p4.wait()
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            raise
        lock = open(lsfLock, "w+")
        lock.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        lock.close()


def installJmxTrans():  # TODO: create jmxtrans instalation
    return "Install jmxtrans"


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
        if 'yarn' or 'hdfs' in component:
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
        if 'kafka'in component:
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
            if 'jmx'in compInstalled:
                pass
            else:
                compInstalled.append('jmx')
        return compInstalled

    def controll(self, component, cmd):
        try:
            subprocess.Popen('sudo service ' + component + ' ' + cmd, shell=True)
        except Exception as inst:
            print >> sys.stderr, type(inst)
            print >> sys.stderr, inst.args
            raise

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
            return "response"
        confInfo=template.render(settingsDict)
        confFile = open(filePath, "w+")
        confFile.write(confInfo)
        confFile.close()

    def getRoles(self):
        return 'check vm roles using JPS!'
