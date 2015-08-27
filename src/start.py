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
from sqlalchemy import desc
import sqlite3, os
import socket
from flask.ext.sqlalchemy import SQLAlchemy


def main(argv):
	'''
		Starts 
	'''
	port = 5000
	ip = '0.0.0.0'
	try:
		opts, args=getopt.getopt(argv,"hi:p:e:s",["core-install","port","endpoint-ip","start"])
	except getopt.GetoptError:
		print "%-------------------------------------------------------------------------------------------%"
		print "Invalid argument! Arguments must take the form:"
		print ""
		print "start.py -i  -p <port> -e <IP>"
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
			print '-p 	-> designate port for D-Mon web service (default is 5000)'
			print '-e 	-> designate IP for D-Mon web service (default is 0.0.0.0)'
			print "Usage Example:"
			print" start.py -i -p 8088 -e 127.0.0.1 "
			print "%-------------------------------------------------------------------------------------------%"
			sys.exit()
		elif opt in ("-i","--core-install"):
			#hostfile=arg
			if os.path.isfile('dmon.lock') is True: 
				print >>sys.stderr, "D-Mon Core already installed!"
				#sys.exit(2) #uncoment if exit upon 
			else:
				try:
					procStart = subprocess.Popen(['./bootstrap.sh'],stdout=subprocess.PIPE)
				except Exception as inst:
					print >> sys.stderr, type(inst)
					print >> sys.stderr, inst.args
				lock =  open('dmon.lock',"w+")
				lock.write(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
				lock.close()
		elif opt in ("-p","--port"):
			if isinstance(arg,int) is not True:
				print >> sys.stderr, "Argument must be an integer!"
				sys.exit(2)
			port = arg
		elif opt in ("-e", "--endpoint-ip"):
			if isinstance(arg,str) is not True:
				print >> sys.stderr, "Argument must be string!"
			ip = arg

	chkESCoreDB = db.session.query(dbESCore.hostFQDN).all()
	if chkESCoreDB is not None:
		corePopES = dbESCore(hostFQDN=socket.getfqdn(),hostIP = '127.0.0.1',hostOS='ubuntu', nodeName = 'esCoreMaster',
			clusterName='dice-monit', conf = 'None', nodePort=9200, MasterNode=1)
		db.session.add(corePopES) 
		db.session.commit()

	chkLSCoreDB = db.session.query(dbESCore.hostFQDN).all()
	if chkLSCoreDB is not None:
		corePopLS=dbSCore(hostFQDN=socket.getfqdn(),hostIP = '127.0.0.1',hostOS='ubuntu',
			 outESclusterName='dice-monit', udpPort = 25680, inLumberPort=5000)
		db.session.add(corePopLS) 
		db.session.commit()

	app.run(host = ip,port=port,debug=True)

if __name__=='__main__':
	#directory locations
	outDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
	tmpDir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
	cfgDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')
	baseDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db')
	pidDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pid')
	#TODO add escore and lscore executable locations
	
	app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(baseDir,'dmon.db')
	app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
	db.create_all()
	
	print '''
	██████╗       ███╗   ███╗ ██████╗ ███╗   ██╗
	██╔══██╗      ████╗ ████║██╔═══██╗████╗  ██║
	██║  ██║█████╗██╔████╔██║██║   ██║██╔██╗ ██║
	██║  ██║╚════╝██║╚██╔╝██║██║   ██║██║╚██╗██║
	██████╔╝      ██║ ╚═╝ ██║╚██████╔╝██║ ╚████║
	╚═════╝       ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
	'''

	if len(sys.argv)==1:
		app.run('0.0.0.0',debug=True)
		
	else:
		main(sys.argv[1:])