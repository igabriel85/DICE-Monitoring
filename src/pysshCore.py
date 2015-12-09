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
from pssh import *
import os.path
import os
import nmap
import sys, getopt
from flask import Flask, jsonify, Response


#fix for UNicodeDecoder Error -> ascii codec
reload(sys) 
sys.setdefaultencoding('utf8')

#folder locations
basedir = os.path.abspath(os.path.dirname(__file__))
confDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')
credDir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys')

#monitoring endpoints
#logstashsip = ''
#logstashport = ''


#initialize hostlist
#hostlist = [ ]
#userName = ''
#uPassword = ''

def listOutput(out):
	'''
	Prints the output for each host after a command
	'''
	for host in out:
		for line in out[host]['stdout']:
			print line

def installCollectd(hostlist,userName,uPassword,confDir=confDir):
	'''
	Installs and uploads a conf file to selected hosts.

	TODO: 
	- check if conf file exists if not allow to specify location of config
	- revise exceptions
	- use jinja2 template to generate config for each defined host
	'''
	client = ParallelSSHClient(hostlist, user=userName, password=uPassword)
	#create path to file
	localCopy = os.path.join(confDir, 'collectd.conf')
	try:
		#Installing Collectd to hosts ...
		output = client.run_command('apt-get install -y collectd', sudo=True)
		listOutput(output)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured Installing collectd!"
		raise
	
	try:	
		print "Copying collectd conf files ....."
		client.copy_file(localCopy, "collectd.conf")
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured copying collectd.conf!"
		raise
		#client.pool.join()

	
		
	print "Stopping Collectd...."

	try:	
		client.run_command('nohup service collectd stop', sudo=True)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured stopping collectd service!"
		raise

	try:
		client.run_command('mv /etc/collectd/collectd.conf /etc/collectd/collectd.default', sudo=True)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured renaming collectd.conf!"
		raise
	
	try:		
		client.run_command('mv collectd.conf /etc/collectd/collectd.conf', sudo=True)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured moving new collectd.conf to /etc!"	
		raise
		#client.pool.join()
		#print 'collectd -C ' +localCopy

	try:
		print "Adding Comment to File..."
		client.run_command('echo >> /etc/collectd/collectd.conf')
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while editing collectd.conf!"
		raise	
			
	print "Starting Collectd ..."
	try:
		#out = client.exec_command('collectd',sudo=True,pty=False)
		out = client.run_command('nohup service collectd restart',sudo=True)
		listOutput(out)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured starting collectd!"
		raise
		#client.run_command('service collectd start', sudo=True)
	del client
	print "Done Collectd"

def installJmxtrans(hostlist,userName,uPassword,confDir,confName):
	'''
	Installs and configures jmxtrans for both storm and spark 
	JVM metrics collection.

	confName -> name of the configuration to be uploaded
	'''
	if not os.path.isdir(confDir):
		print >> sys.stderr, "Configuration dir not found!"
	
	print "Installing jmxtrans ..."	
	localCopyConf = os.path.join(confDir,confName)
	client = ParallelSSHClient(hostlist, user=userName,password=uPassword)
	try:
		client.run_command('wget http://jmxtrans.googlecode.com/files/jmxtrans_250-1_all.deb')
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while downloading jmxtrans!"
		raise

	try:
		install = client.run_comand('dpkg -i jmxtrans_250-1_all.deb', sudo=True)
		listOutput(install)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while installing jmxtrans!"
		raise





	#http://jmxtrans.googlecode.com/files/jmxtrans_250-1_all.deb
	
def installLogstashForwarder(hostlist,userName,uPassword,confDir):
	'''
		Installs and configures logstash-forwarder on all listed hosts.
		The file logstashforwarder.list contains the string 

		'deb http://packages.elasticsearch.org/logstashforwarder/debian stable main'

		This is added to apt source list.

		TODO:
		- currently fails if an exception occurs
		- parsing ouput from listOutput
	'''

	if not os.path.isdir(confDir):
		print "Configuration dir not found!"

	print "Install logstash-forwarder"
	client = ParallelSSHClient(hostlist, user=userName, password=uPassword)
	localCopyCrt = os.path.join(credDir, 'logstash-forwarder.crt')
	localCopyConf = os.path.join(confDir, 'logstash-forwarder.conf')
	localLFList = os.path.join(confDir, 'logstashforwarder.list')
	try:
		print "Creating folders..."
		client.run_command('mkdir /opt/certs', sudo=True)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured creating /opt/certs!"
		raise	
	
	print "Copying certificate..."
	
	try:	
		client.copy_file(localCopyCrt,"logstash-forwarder.crt")
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while moving cert!"
		raise

	try:	
		client.run_command('mv logstash-forwarder.crt /opt/certs',sudo=True)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while moving cert to /opt/certs"
		raise

	print "Adding Logstash forwarder to apt ..."
		#output = client.run_command('echo \'deb http://packages.elasticsearch.org/logstashforwarder/debian stable main\' | sudo tee /etc/apt/sources.list.d/logstashforwarder.list',sudo=True)
	
	try:	
		client.copy_file(localLFList,"logstashforwarder.list")
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while uploading lfs list!"
		raise

	try:
		client.run_command('mv logstashforwarder.list /etc/apt/sources.list.d/logstashforwarder.list',sudo=True)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while adding lsf list to sourcelist!"
		raise

	try:	
		output = client.run_command('wget http://packages.elasticsearch.org/GPG-KEY-elasticsearch')
		listOutput(output)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while downloading ES GPG Key!"
		raise

	try:	
		output1 = client.run_command('apt-key add GPG-KEY-elasticsearch', sudo=True)
		listOutput(output1)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while adding GPG-Key to apt!"
		raise

		#output2= client.run_command('wget -O - http://packages.elasticsearch.org/GPG-KEY-elasticsearch | sudo apt-key add -',sudo=True)
	print "Installing Logstash-forwarder..."
	
	try:
		update=client.run_command('apt-get update', sudo=True)
		listOutput(update)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while apt-get update!"
		raise
	
	try:	
		install =client.run_command('apt-get install -y logstash-forwarder',sudo=True)
		listOutput(install)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while installing LFS!"
		raise
			
	print "Copying Logstash-forwarder configuration to hosts..."

	try:
		client.copy_file(localCopyConf,"logstash-forwarder.conf")
		client.run_command('mv logstash-forwarder.conf /etc/logstash-forwarder.conf',sudo=True)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while uploading lsf conf!"
		raise

	print "Starting logstash-forwarder ...."
	try:
		run = client.run_command('nohup service logstash-forwarder restart', sudo=True)
		listOutput(run)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured starting LSF"
		raise	
		


		
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured!"
	del client
	print "All DONE!"
# client = ParallelSSHClient(['109.231.126.221','109.231.126.222'], user=userName,password=uPassword)
# try:
# 	output = client.run_command('mkdir this_is_a_test_2', sudo=True)
# 	for host in output:
# 		for line in output[host]['stdout']:
# 			print line
# except (AuthenticationException, UnknownHostException, ConnectionErrorException):
# 	print "Stff"

def uploadFile(hostlist,userName,password,fileLoc,fileName, upLoc):
	'''
		Uploads a specified file to target servers via ssh.

		hostlist -> list of hosts to connect to 
		userName -> username for the hosts
		password -> password of the hosts
		fileLoc  -> absolute path to the file that needs to be updated
		fileName -> name of the file to be uploaded
		upLoc    -> absolute path where the file needs to be saved in the target host

	'''
	client = ParallelSSHClient(hostlist, user=userName,password=uPassword)
	cmdMove = 'mv '+fileName+' '+upLoc
	try:	
		client.copy_file(fileLoc,fileName)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while uploading file!"
	try:	
		client.run_command(cmdMove,sudo=True)
		client.run_command('echo >> '+upLoc,sudo=True) #TODO replace ugly fix
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured while moving file"
		raise

def serviceCtrl(hostlist,userName,uPassword,serviceName, command):
	'''
		Checks the status of aservice on remote servers.
		Only supported commands are start, stop, status

		TODO: 
		- return hosts on which services are not running

	'''
	
	if command not in ['status','stop','start','force-start']:
		print "Command "+ command +" unsupported!"
		exit()
	try:
		client = ParallelSSHClient(hostlist, user=userName,password=uPassword)
		cmdStr = 'nohup service ' + serviceName +' ' + command
		output = client.run_command(cmdStr, sudo=True)
		for host in output:
			for line in output[host]['stdout']:
				#print line
				if 'not' in line:
					print "Service " + serviceName+" is not Runnning on host " + host
				elif 'unrecognized' in line:
					print "Service " + serviceName + " is unrecognized on host " + host
				elif 'running' in line:
					sline = line.split()
					slineLength = len(sline)
					print "Service " + serviceName + " is running as process " +str(sline[slineLength-1]) + " on host " + host
				elif 'started' or 'Starring' in line:
					print "Service " + serviceName+" has started Runnning on host " + host
				else:
					print "Unknown output!"
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured!"
		raise
		#response = jsonify({'Status':'Error stopping LSF on '+ nodeFQDN +'!'})
        #response.status_code = 500
        #return response
	

def hostsScan(hostlist):
	'''
		Gets the list of hosts an checks which ones are up.
		It then removes the ones that are down. 
		It returns hostlist, badHosts
	'''
	badHosts = []
	
	for host in hostlist:
		response = os.system( "ping -c 1 " + host)
		if response == 0:
			print host, 'is up!'
		else:
			print host, 'is down!'
			# add to badHost list
			badHosts.append(host)
	#crate goodHosts list
	goodHosts = [x for x in hostlist if x not in badHosts] 
	return goodHosts, badHosts
			
def nmapScan(hostlist, port='22-443'):
	'''
	Takes a list of hosts and checks port 22 (default) ssh status.
	If Host does not exist it returns an exception.
	Use hostsScan() before to generate clean hosts list.

	TODO:
	- identify OS 
	- lots
	'''
	nm = nmap.PortScanner() #instantiate nmap.Scanner object
	for host1 in hostlist:
		nm.scan(host1,str(port))
		nm.command_line()
		nm.scaninfo()
		nm.all_hosts()
		nm[host1].hostname()          # get hostname for host 127.0.0.1
		nm[host1].state()             # get state of host 127.0.0.1 (up|down|unknown|skipped)
		nm[host1].all_protocols()     # get all scanned protocols ['tcp', 'udp'] in (ip|tcp|udp|sctp
		nm[host1]['tcp'].keys()       # get all ports for tcp protocol
		nm[host1].all_tcp()           # get all ports for tcp protocol (sorted version)
		nm[host1].all_udp()           # get all ports for udp protocol (sorted version)
		nm[host1].all_ip()            # get all ports for ip protocol (sorted version)
		nm[host1].all_sctp()          # get all ports for sctp protocol (sorted version)
		if nm[host1].has_tcp(22):         # is there any information for port 22/tcp on host 127.0.0.1
			nm[host1]['tcp'][22]          # get infos about port 22 in tcp on host 127.0.0.1
			nm[host1].tcp(22)             # get infos about port 22 in tcp on host 127.0.0.1
			nm[host1]['tcp'][22]['state'] 
		for host in nm.all_hosts():
			print('----------------------------------------------------')
			print('Host : %s (%s)' % (host, nm[host].hostname()))
			print('State : %s' % nm[host].state())
			for proto in nm[host].all_protocols():
				print('----------')
				print('Protocol : %s' % proto)
				lport = nm[host][proto].keys()
				lport.sort()
				for port in lport:
					print('port : %s\tstate : %s\n' % (port, nm[host][proto][port]['state']))
			if os.getuid() == 0: #check if sudo user
				nm.scan(host, arguments="-O")
				if 'osclass' in nm[host]['osclass']:
					for osclass in nm[host]['osclass']:
						print 'OsClass.type : {0}'.format(osclass['type'])
						print 'OsClass.vendor : {0}'.format(osclass['vendor'])
						print 'OsClass.osfamily : {0}'.format(osclass['osfamily'])
						print 'OsClass.osgen : {0}'.format(osclass['osgen'])
						print 'OsClass.accuracy : {0}'.format(osclass['accuracy'])
						print ''

				if 'osmatch' in nm[host]:
					for osmatch in nm[host]['osmatch']:
						print('OsMatch.name : {0}'.format(osclass['name']))
						print('OsMatch.accuracy : {0}'.format(osclass['accuracy']))
						print('OsMatch.line : {0}'.format(osclass['line']))
						print('')

				if 'fingerprint' in nm[host]:
					print('Fingerprint : {0}'.format(nm[host]['fingerprint']))


def detectOS(hostlist, userName, uPassword):
	hostOS = {}
	client = ParallelSSHClient(hostlist, user=userName,password=uPassword)
	cmdStr = "uname -a"
	try:
		output = client.run_command(cmdStr)
		for host in output:
			for line in output[host]['stdout']:
				if 'Ubuntu' in line or 'ubuntu' in line:
					hostOS.update({host:'Ubuntu'})
				else:
					hostOS.update({host:'Unknown'})
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured!"
		raise
	return hostOS



def checkSetup():
	print "Check the logging remote setup"

def deployOryx2():
	'''
	    Deploy Oryx2 on CDH
	'''
	print "Oryx2 Deploy"

def startOryx2():
	'''
		Start Oryx2 Installation
	'''
	oryx2Deployment = {"speedLayer":"","batchLayer":"","servingLayer":""}
	print "Oryx2 Start"



def auxCtrl(auxComp,command):
	'''
	Function used to start and stop all auxiliary components.

	Parameters:
	----------

	auxComp -> A string that represents the name of the auxiliary component.
			   Can be collectd and lsf.
    command -> Command to be executed on the auxiliary components.
    		   Can be start or stop
	'''
	auxList = ['collectd','lsf']
	cState = ''
	if auxComp not in auxList:
		response = jsonify({'Status':'No such such aux component '+ auxComp})
		response.status_code = 400
		return response

	if command == 'start':
		cState = 'Stopped'
	elif command == 'stop':
		cState = 'Running'
	else:
		print "Unknown command! Only Start and Stop is supported"

	if auxComp == "collectd":
		qNCollectd = dbNodes.query.filter_by(nCollectdState=cState).all()
		if qNCollectd is None:
			response = jsonify({'Status': 'No nodes in state ' + cState + ' !'})
			response.status_code = 404
			return response

		nodeCollectdStopped = []
		for i in qNCollectd:
			node = []
			node.append(i.nodeIP)
			try:
				serviceCtrl(node,i.nUser,i.nPass,'collectd', command)
			except Exception as inst:
				print >> sys.stderr, type(inst)
				print >> sys.stderr, inst.args
				response = jsonify({'Status':'Error exec '+command+' on collectd. Node '+ i.nodeFQDN +'!'})
				response.status_code = 500
				return response
			CollectdNodes = {}
			CollectdNodes['Node'] = i.nodeFQDN
			CollectdNodes['IP'] = i.nodeIP
			nodeCollectdStopped.append(CollectdNodes)
			response = jsonify({'Status':'Collectd '+command+' successfull','Nodes':nodeCollectdStopped})
			response.status_code = 200
			return response

	if auxComp == "lsf":
		qNLsf = dbNodes.query.filter_by(nLogstashForwState=cState).all()
		if qNLsf is None:
			response = jsonify({'Status': 'No nodes in state ' + cState + '!'})
			response.status_code = 404
			return response

		nodeLsfStopped = []
		for i in qNLsf:
			node = []
			node.append(i.nodeIP)
			try:
				serviceCtrl(node, i.nUser, i.nPass, 'logstash-forwarder', command)
			except Exception as inst:
				print >> sys.stderr, type(inst)
				print >> sys.stderr, inst.args
				response = jsonify({'Status': 'Error exec ' + command + ' on LSF. Node ' + i.nodeFQDN + '!'})
				response.status_code = 500
				return response

			LsfNodes = {}
			LsfNodes['Node'] = i.nodeFQDN
			LsfNodes['IP'] = i.nodeIP
			nodeLsfStopped.append(LsfNodes)
			response = jsonify({'Status': 'LSF ' + command + ' sucessfull', 'Nodes': nodeLsfStopped})
			response.status_code = 200
			return response


def deployAgent(hostlist, userName, uPassword):
	'''
	:param hostlist: list of host IO
	:param userName: username
	:param uPassword: password
	'''

	if not os.path.isdir(credDir):
		print "Configuration dir not found!"

	print "Copying Certificate ...."
	client = ParallelSSHClient(hostlist, user=userName, password=uPassword)
	localCopyCrt = os.path.join(credDir, 'logstash-forwarder.crt')

	try:
		print "Creating certificate folders..."
		client.run_command('mkdir /opt/test/certs', sudo=True)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured creating /opt/test/certs!"
		raise

	print "Copying certificate..."

	# try:
	# 	client.copy_file(localCopyCrt, "logstash-forwarder.crt")
	# except (AuthenticationException, UnknownHostException, ConnectionErrorException):
	# 	print "An exception has occured while moving cert!"
	# 	raise

	try:
		print "Copying dmon-agent ..."
		client.run_command('wget https://github.com/igabriel85/IeAT-DICE-Repository/releases/download/0.0.3/dmon-agent.tar.gz')
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "Error while downloading dmon-agent"
		raise

	try:
		client.run_command('mv dmon-agent.tar.gz /opt')
		client.run_command('tar xvf /opt/dmon-agent.tar.gz')
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "Error while unpacking dmon-agent"
		raise

	try:
		client.run_command('pip install -r /opt/dmon-agent/requirements.txt')
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "Error while installing dmon-agent dependencies"
		raise

def startAgent(hostlist, username, password):
	'''
	:param hostlist:
	:param username:
	:param password:
	'''
	print "Start Agents"
	client = ParallelSSHClient(hostlist, user=userName, password=uPassword)
	try:
		print "Start Agent..."
		client.run_command('./opt/dmon-agent/agent-start.sh', sudo=True)
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occurred while starting dmon-agent!"
		raise


def main(argv):
	'''
		This is the main function that handles command line arguments.

		TODO: ....
	'''
	hostlist = []
	userName = ''
	uPassword = ''
	uKey = ' ' #location of secret key
	try:
		opts, args=getopt.getopt(argv,"hi:u:p:k:tdc",["hostFile","username","password","key","test","deploy","check"])
	except getopt.GetoptError:
		print "%-------------------------------------------------------------------------------------------%"
		print "Invalid argument! Arguments must take the form:"
		print ""
		print "pysshCore.py -i <hostfile> -u <username> -p <password> -k <key>"
		print ""
		print "%-------------------------------------------------------------------------------------------%"
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print "%-------------------------------------------------------------------------------------------%"
			print ""
			print "pysshCore is desigend to facilitate the deployment of the DICE Monitoring Collectors."
			print "You must specify a valid hostfile, username, password and/or secret key location."
			print "Usage Example:"
			print "pysshCore -i <hostfile> -u <username> -p <password> -k <key>"
			print"                                                                                              "
 			print "NOTE: Secret key not yet suported only user and password auth!"
			print "%-------------------------------------------------------------------------------------------%"
			sys.exit()
		elif opt in ("-i","--hostFile"):
			#hostfile=arg
			if os.path.isfile(arg) is not True:
				print "ERROR: No such file", arg
				sys.exit(2)
			try:
				with open(arg,'r') as f:
					hostlist = [line.strip() for line in f] #strip new line char from end of file
					#print "These are the submitted hosts:"
					#print hostlist
					#print ""
					#print "&--------------------&"
			except:
				print "Caught Exception while opening file", arg
		elif opt in ("-u","--username"):
			userName=arg
			#print userName
		elif opt in ("-p","--password"):
			uPassword = arg
			#print uPassword
		elif opt in ("-t","--test"):
			if len(userName)==0 or len(uPassword)==0:
				print "Must specify valid User Name and Password!"
			else:
				#Scan listed hosts
				print "%-------------------------------------------------------------------------------------------%"
				print "Starting host scan first pass:"
				print ""
				good, bad = hostsScan(hostlist)
				print "&--------------------&"
				print "Results"
				print 'These are the good hosts', str(good)
				print 'These are the bad hosts', str(bad)
				print ""
				print "Starting host scan second pass:"
				#passing only active nodes to nmap
				nmapScan(good)
				print "%-------------------------------------------------------------------------------------------%"
		elif opt in ("-d","--deploy"):
			if len(userName)==0 or len(uPassword)==0:
				print "Must specify valid User Name and Password!"
			else:
				print "%-------------------------------------------------------------------------------------------%"
				print "Starting Collectd deployment on hosts."
				installCollectd(hostlist,userName,uPassword,confDir)
				print ""
				print "Starting Logstash-Forwarder deployment on hosts."
				installLogstashForwarder(hostlist,userName,uPassword,confDir)
				print ""
				print "Deployment DONE!"
				print "%-------------------------------------------------------------------------------------------%"
		elif opt in ("-c","--check"):
			print "TODO Check deployment"

if __name__=='__main__':
	if len(sys.argv) == 1:
		hostlist = ['109.231.126.190','109.231.126.222','109.231.126.221','109.231.126.102','109.231.126.166','109.231.126.70','109.231.126.136',
		'109.231.126.146','109.231.126.157']
		hostlist = ['109.231.126.189','109.231.126.177']
		
		userName = 'ubuntu'
		uPassword = 'rexmundi220'
		#installCollectd(hostlist,userName,uPassword)
		#mf(hostlist,userName,uPassword)
		installLogstashForwarder(hostlist,userName,uPassword,confDir)
		#serviceCtrl(hostlist,userName,uPassword,'collectd','start')
		#print detectOS(hostlist, 'ubuntu','rexmundi220')
		#nmapScan(hostlist)
		# #----------------------------------------------------
		# good, bad = hostsScan(hostlist)
		# print 'These are the good hosts '+str(good)
		# print 'These are the bad hosts ', str(bad)
		#----------------------------------------------------
		#tests(hostlist)
	else:
		main(sys.argv[1:])

		


