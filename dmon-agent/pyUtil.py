import subprocess
import sys
import os
import datetime
import time


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
        if not component in AuxComponent.supported:
            return 0

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

    def configureCollectd(self, settingsDict):  # TODO
        return "Genereted collectd Config"

    def configureLsf(self, settingsDict):  # TODO
        return "Generated lsf Config"

    def configureJMX(self, settingsDict):  # TODO
        return "Generated jmxtrans Config"