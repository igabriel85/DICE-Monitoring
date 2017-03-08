#encoding=utf8
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
#!flask/bin/python

from pyDMON import *
#from dbMode import *
from pyESController import *
import datetime
import time
from sqlalchemy import desc
import sqlite3, os
import socket
from flask.ext.sqlalchemy import SQLAlchemy
from logging.handlers import RotatingFileHandler
from datetime import datetime


def main(argv):
    '''
        Starts
    '''
    port = 5001
    ip = '0.0.0.0'

    try:
        opts, args = getopt.getopt(argv, "hi:p:e:l:", ["core-install", "port", "endpoint-ip", "local"])
    except getopt.GetoptError:
        print "%-------------------------------------------------------------------------------------------%"
        print "Invalid argument! Arguments must take the form:"
        print ""
        print "start.py -i -l <local_ip> -p <port> -e <host IP>"
        print ""
        print "%-------------------------------------------------------------------------------------------%"
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print "%-------------------------------------------------------------------------------------------%"
            print "The DICE Monitoring Platform (D-Mon) is a web service that facilitates the monitoring of big data frameworks. "
            print "It uses a REST API with the aid of which nodes can be subscribed to the monitoring platform."
            print "Currently it supports HDFS and YARN metrics. For further details please consult the README file."
            print""
            print 'Arguments:'
            print '-h 	-> help'
            print '-i 	-> install D-Mon core componets (WARNING: sudo required)'
            print '-l 	-> deploys D-Mon in local mode (also populates ES and LS Core component settings)'
            print '-p 	-> designate port for D-Mon web service (default is 5001)'
            print '-e 	-> designate IP for D-Mon web service (default is 0.0.0.0)'
            print "Usage Example:"
            print" start.py -i -p 8088 -e 127.0.0.1 "
            print "%-------------------------------------------------------------------------------------------%"
            sys.exit()
        if opt in ("-i", "--core-install"):
            #hostfile=arg
            if os.path.isfile('dmon.lock') is True:
                # print >>sys.stderr, "D-Mon Core already installed!"
                app.logger.warning('[%s] : [WARNING] D-Mon Core already installed!',
                                   datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                #sys.exit(2) #uncoment if exit upon
            else:
                try:
                    app.logger.info('[%s] : [INFO] Bootstrapping D-Mon Core please wait...',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    procStart = subprocess.Popen(['./bootstrap.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False).communicate()
                    app.logger.info('[%s] : [INFO] Bootstrap finished!',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                except Exception as inst:
                    app.logger.error('[%s] : [ERROR] Error while executing bootstrap script with %s and %s',
                                    datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                    sys.exit(2)
                lock = open('dmon.lock', "w+")
                lock.write(datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                lock.close()
                app.logger.info('[%s] : [INFO] Stopping D-Mon Controller',
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                sys.exit(0) #exit when done
        if opt in ("-p", "--port"):
            try:
                port = int(arg)
            except Exception as inst:
                app.logger.error('[%s] : [ERROR] Port must be integer. Exiting %s with %s',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args )
                sys.exit(2)
        if opt in ("-e", "--endpoint-ip"):
            if not isinstance(arg, str):
                app.logger.error('[%s] : [ERROR] Endpoint must be string. Exiting',
                                 datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                sys.exit(2)
            ip = arg
        if opt in ("-l", "--local"):
            if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
                if opt in ("-l", "--local"):
                    if socket.getfqdn().isspace():
                        app.logger.error('[%s] : [ERROR] FQDN not set',
                                         datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                        print >> sys.stderr, "FQDN not set!"
                        sys.exit(2)
                    if isinstance(arg, str) is not True:
                        print >> sys.stderr, "Argument must be string!"
                    chkESCoreDB = db.session.query(dbESCore.hostFQDN).all()
                    if chkESCoreDB is not None: #TODO read heap from env variable and set in db
                        corePopES = dbESCore(hostFQDN=socket.getfqdn(), hostIP='127.0.0.1', hostOS='ubuntu', nodeName='esCoreMaster',
                            clusterName='diceMonit', conf='None', nodePort=9200, MasterNode=1, DataNode=1,
                                             ESCoreHeap=os.getenv('ES_HEAP_SIZE', '1g'))
                        db.session.add(corePopES)
                        try:
                            db.session.commit()
                        except Exception as inst:
                            app.logger.warning('[%s] : [WARNING] Duplicate ES entry exception! Local deployment can be run only once. With %s and %s',
                                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                            pass

                    chkLSCoreDB = db.session.query(dbSCore.hostFQDN).all()
                    if chkLSCoreDB is not None:
                        corePopLS = dbSCore(hostFQDN=socket.getfqdn(), hostIP=socket.gethostbyname(socket.gethostname()),
                                          hostOS='ubuntu', outESclusterName='diceMonit', udpPort=25680,
                                          inLumberPort=5000, LSCoreHeap=os.getenv('LS_HEAP_SIZE', '512m'))
                        db.session.add(corePopLS)
                        try:
                            db.session.commit()
                        except Exception as inst:
                            app.logger.warning('[%s] : [WARNING] Duplicate LS entry exception! Local deployment can be run only once. With %s and %s',
                                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                            pass

                    chkKBCoreDB = db.session.query(dbKBCore.hostFQDN).all()
                    # print >> sys.stderr, chkLSCoreDB
                    if chkKBCoreDB is not None:
                        corePopKB = dbKBCore(hostFQDN=socket.getfqdn(),
                                             hostIP=socket.gethostbyname(socket.gethostname()), hostOS='ubuntu',
                                             kbPort=5601)
                        db.session.add(corePopKB)
                        try:
                            db.session.commit()
                        except Exception as inst:
                            app.logger.warning('[%s] : [WARNING] Duplicate KB entry exception! Local deployment can be run only once. With %s and %s',
                                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                            pass

                    chkMetPer = dbMetPer.query.first()
                    app.logger.warning('[%s] : [WARNING] chkMetPer value -> %s',
                                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(chkMetPer))
                    if chkMetPer is None:
                        chkMetPerCore = dbMetPer(sysMet="15", yarnMet="15", sparkMet="5", stormMet="60")
                        db.session.add(chkMetPerCore)
                        try:
                            db.session.commit()
                        except Exception as inst:
                            app.logger.warning('[%s] : [WARNING] Duplicate MetPer entry exception! Local deployment can be run only once. With %s and %s',
                                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
                            pass
    app.logger.info('[%s] : [INFO] Checking status of Core services')
    esPidFile = os.path.join(pidDir, 'elasticsearch.pid')
    lsPidFile = os.path.join(pidDir, 'logstash.pid')
    kbPidFile = os.path.join(pidDir, 'kibana.pid')
    checkCoreState(esPidFile, lsPidFile, kbPidFile)
    app.run(host=ip, port=port, debug=True)

if __name__ == '__main__':
    #directory locations
    outDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    tmpDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    cfgDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')
    baseDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db')
    pidDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pid')
    #TODO add escore and lscore executable locations

    #DB Initialization
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(baseDir, 'dmon.db')
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
    db.create_all()

    #Logger settings
    handler = RotatingFileHandler(logDir + '/dmon-controller.log', maxBytes=10000000, backupCount=5)
    logLevel = os.getenv('DMON_LOGGING', 'WARN')
    if logLevel == 'INFO':
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.DEBUG)
    elif logLevel == 'WARN':
        handler.setLevel(logging.WARNING)
        app.logger.addHandler(handler)
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.DEBUG)
    elif logLevel == 'ERROR':
        handler.serLevel(logging.ERROR)
        app.logger.addHandler(handler)
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
    else:
        handler.setLevel(logging.WARNING)
        app.logger.addHandler(handler)
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.DEBUG)

    log.addHandler(handler)

    print '''
    ██████╗       ███╗   ███╗ ██████╗ ███╗   ██╗
    ██╔══██╗      ████╗ ████║██╔═══██╗████╗  ██║
    ██║  ██║█████╗██╔████╔██║██║   ██║██╔██╗ ██║
    ██║  ██║╚════╝██║╚██╔╝██║██║   ██║██║╚██╗██║
    ██████╔╝      ██║ ╚═╝ ██║╚██████╔╝██║ ╚████║
    ╚═════╝       ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
    '''

    if len(sys.argv) == 1:
        app.run('0.0.0.0', port=5001, debug=True)

    else:
        main(sys.argv[1:])
