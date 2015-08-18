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


#folder locations
basedir = os.path.abspath(os.path.dirname(__file__))
confDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')

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

def installCollectd(hostlist,userName,uPassword):
	'''
	Installs and uploads a conf file to selected hosts.

	TODO: 
	- check if conf file exists if not allow to specify location of config
	- revise exceptions
	- use jinja2 template to generate config for each defined host
	'''
	client = ParallelSSHClient(hostlist, user=userName,password=uPassword)
	#create path to file
	localCopy = os.path.join(confDir,'collectd.conf')
	try:
		#Installing Collectd to hosts ...
		output = client.run_command('apt-get install -y collectd', sudo=True)
		listOutput(ouput)
		print "Copying collectd conf files ....."
		client.copy_file(localCopy,"collectd.conf")
		client.pool.join()

		print "Stopping Collectd...."
		client.run_command('service collectd stop', sudo=True)
		client.pool.join()
		client.run_command('mv /etc/collectd/collectd.conf /etc/collectd/collectd.default', sudo=True)
		client.run_command('mv collectd.conf /etc/collectd/collectd.conf', sudo=True)
		client.run_command('service collectd restart', sudo=True)
		print "Done Collectd"

	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured!"
	return True

def installLogstashForwarder(hostlist,userName,uPassword):
	'''
		Installs and configures logstash-forwarder on all listed hosts.
		The file logstashforwarder.list contains the string 

		'deb http://packages.elasticsearch.org/logstashforwarder/debian stable main'

		This is added to apt source list.

		TODO:
		- currently fails if an exception occurs
		- parsing ouput from listOutput
	'''
	print "Install logstash-forwarder"
	client = ParallelSSHClient(hostlist, user=userName,password=uPassword)
	localCopyCrt = os.path.join(confDir,'logstash-forwarder.crt')
	localCopyConf = os.path.join(confDir,'logstash-forwarder.conf')
	localLFList = os.path.join(confDir,'logstashforwarder.list')
	try:
		print "Creating folders..."
		client.run_command('mkdir /opt/certs', sudo=True)
		
		print "Copying certificate..."
		client.copy_file(localCopyCrt,"logstash-forwarder.crt")
		client.run_command('mv logstash-forwarder.crt /opt/certs',sudo=True)

		print "Adding Logstash forwarder to apt ..."
		#output = client.run_command('echo \'deb http://packages.elasticsearch.org/logstashforwarder/debian stable main\' | sudo tee /etc/apt/sources.list.d/logstashforwarder.list',sudo=True)
		client.copy_file(localLFList,"logstashforwarder.list")
		client.run_command('mv logstashforwarder.list /etc/apt/sources.list.d/logstashforwarder.list',sudo=True)
		output = client.run_command('wget http://packages.elasticsearch.org/GPG-KEY-elasticsearch')
		listOutput(output)
		output1 = client.run_command('apt-key add GPG-KEY-elasticsearch', sudo=True)
		listOutput(output1)

		#output2= client.run_command('wget -O - http://packages.elasticsearch.org/GPG-KEY-elasticsearch | sudo apt-key add -',sudo=True)
		print "Installing Logstash-forwarder..."
		update=client.run_command('apt-get update',sudo=True)
		listOutput(update)
		install =client.run_command('apt-get install -y logstash-forwarder',sudo=True)
		listOutput(install)

		print "Copying Logstash-forwarder configuration to hosts..."
		client.copy_file(localCopyConf,"logstash-forwarder.conf")
		client.run_command('mv logstash-forwarder.conf /etc/logstash-forwarder.conf',sudo=True)

		print "Starting logstash-forwarder ...."
		run = client.run_command('service logstash-forwarder restart', sudo=True)
		listOutput(run)
		client.pool.join()

		print "All DONE!"
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured!"
	return True

# client = ParallelSSHClient(['109.231.126.221','109.231.126.222'], user=userName,password=uPassword)
# try:
# 	output = client.run_command('mkdir this_is_a_test_2', sudo=True)
# 	for host in output:
# 		for line in output[host]['stdout']:
# 			print line
# except (AuthenticationException, UnknownHostException, ConnectionErrorException):
# 	print "Stff"


def serviceCtrl(hostlist,userName,uPassword,serviceName, command):
	'''
		Checks the status of aservice on remote servers.
		Only supported commands are start, stop, status

		TODO: 
		- Some bugs in starting services
		- return hosts on which services are not running

	'''
	client = ParallelSSHClient(hostlist, user=userName,password=uPassword)
	cmdStr = 'service ' + serviceName +' ' + command
	if command not in ['status','stop','start','force-start']:
		print "Command "+ command +" unsupported!"
		exit()
	try:
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
				elif 'started' in line:
					print "Service " + serviceName+" has started Runnning on host " + host
				else:
					print "Unknown output!"
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "An exception has occured!"


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
	oryx2Deployment = {speedLayer:"",batchLayer:"",servingLayer:""}
	print "Oryx2 Start"

def tests(hostlist):
	client = ParallelSSHClient(hostlist, user='ubuntu',password='rexmundi220')
	#create path to file
	localCopyConf = os.path.join(confDir,'logstash-forwarder.conf')
	#copy to home dire after connection
	try:
		output = client.copy_file(localCopyConf,"logstash-forwarder.conf")
		client.run_command('rm -rf /etc/logstash-forwarder.conf', sudo=True)
		client.run_command('mv logstash-forwarder.conf /etc/logstash-forwarder.conf')
		output = client.run_command('service logstash-forwarder restart', sudo=True)
		listOutput(output)
		#used to block and wait for all parallel commands to finish
		#client.pool.join()
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "Stff"

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
				installCollectd(hostlist,userName,uPassword)
				print ""
				print "Starting Logstash-Forwarder deployment on hosts."
				installLogstashForwarder(hostlist,userName,uPassword)
				print ""
				print "Deployment DONE!"
				print "%-------------------------------------------------------------------------------------------%"
		elif opt in ("-c","--check"):
			print "TODO Check deployment"

if __name__=='__main__':
	if len(sys.argv) == 1:
		hostlist = ['109.231.126.190','109.231.126.222','109.231.126.221','109.231.126.102','109.231.126.166','109.231.126.70','109.231.126.136',
		'109.231.126.146','109.231.126.157']
		
		
		userName = 'na'
		uPassword = 'na'
		#installCollectd(hostlist,userName,uPassword)
		#installLogstashForwarder(hostlist,userName,uPassword)
		#serviceCtrl(hostlist,userName,uPassword,'logstash-forwarder','status')
		#print detectOS(hostlist, 'ubuntu','rexmundi220')
		nmapScan(hostlist)
		# #----------------------------------------------------
		# good, bad = hostsScan(hostlist)
		# print 'These are the good hosts '+str(good)
		# print 'These are the bad hosts ', str(bad)
		#----------------------------------------------------
		#tests(hostlist)
	else:
		main(sys.argv[1:])

		


