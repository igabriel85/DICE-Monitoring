import jinja2
import os

def configureComponent(settingsDict, tmpPath, filePath):
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
            print "template not found"
        confInfo = template.render(settingsDict)
        confFile = open(filePath, 'w+')
        confFile.write(confInfo)
        confFile.close()


tmpDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
cfgDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')

tmpFile = os.path.join(tmpDir, 'logstash.tmp')
cfgFile = os.path.join(cfgDir, 'logstash.conf')
print tmpFile

certLoc = '/cert/loc/now'
keyLoc = '/key/loc/now'
udpPort = '25680'
outESclusterName = 'diceMonit'
hostIP = '127.0.0.1'
nodePort = '9200'
StormRestIP = '127.0.0.1'
LSCoreStormPort = '8080'
LSCoreStormTopology = 'test'
stormInterval = '55555'
nSpout = '4'
nBolt = '4'


#myindex is optional
#if no roles set or set to unknown only collectd will work
#if Storm info set to None no storm http_poller will setup if no info is given this will cause corrupt conf generation
infoSCore = {"sslcert": certLoc, "sslkey": keyLoc, "udpPort": udpPort,
                     "ESCluster": outESclusterName, "EShostIP": hostIP,
                     "EShostPort": nodePort,
                     "StormRestIP": StormRestIP, "StormRestPort": LSCoreStormPort,
                     "StormTopologyID": LSCoreStormTopology, "roles": ['unknown'], 'myIndex':'testhttp', 'storm_interval': stormInterval, 'nSpout': int(nSpout), 'nBolt': int(nBolt)}

configureComponent(infoSCore, tmpFile, cfgFile)