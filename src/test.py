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
import nmap

basedir = os.path.abspath(os.path.dirname(__file__))
confDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')


#---------------------------------------------------------------
# def testFunction(serviceName, command):
# 	client = ParallelSSHClient(['109.231.126.157'], user='ubuntu',password='rexmundi220')
# 	cmdStr = 'service ' + serviceName +' ' + command
# 	if command not in ['status','stop','start']:
# 		print "Command "+ command +" unsupported!"
# 		exit()
# 	try:
# 		output = client.run_command(cmdStr, sudo=True)
# 		for host in output:
# 			for line in output[host]['stdout']:
# 				print line
# 				if 'not' in line:
# 					print "Service " + serviceName+" is not Runnning."
# 				elif 'unrecognized' in line:
# 					print "Service " + serviceName + " is unrecognized."
# 				elif 'running' in line:
# 					sline = line.split()
# 					print "Service " + serviceName + " is running as process " +str(sline[3])
# 				elif 'started' in line:
# 					print "Service " + serviceName+" has started Runnning."
# 	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
# 		print "Stff"

#testFunction('logstash-forwarder','status')

#---------------------------------------------------------------

nm = nmap.PortScanner() #instantiate nmap.Scanner object
nm.scan('109.231.126.190','22')
nm.command_line()
nm.scaninfo()
nm.all_hosts()
nm['109.231.126.190'].hostname()          # get hostname for host 127.0.0.1
nm['109.231.126.190'].state()             # get state of host 127.0.0.1 (up|down|unknown|skipped)
nm['109.231.126.190'].all_protocols()     # get all scanned protocols ['tcp', 'udp'] in (ip|tcp|udp|sctp
nm['109.231.126.190']['tcp'].keys()       # get all ports for tcp protocol
nm['109.231.126.190'].all_tcp()           # get all ports for tcp protocol (sorted version)
nm['109.231.126.190'].all_udp()           # get all ports for udp protocol (sorted version)
nm['109.231.126.190'].all_ip()            # get all ports for ip protocol (sorted version)
nm['109.231.126.190'].all_sctp()          # get all ports for sctp protocol (sorted version)
nm['109.231.126.190'].has_tcp(22)         # is there any information for port 22/tcp on host 127.0.0.1
nm['109.231.126.190']['tcp'][22]          # get infos about port 22 in tcp on host 127.0.0.1
nm['109.231.126.190'].tcp(22)             # get infos about port 22 in tcp on host 127.0.0.1
nm['109.231.126.190']['tcp'][22]['state'] 

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
			print('port : %s\tstate : %s' % (port, nm[host][proto][port]['state']))

# ping hosts to see if they are up
hosts = ['109.231.126.190','109.231.126.222','109.231.126.221',
	'109.231.126.102','109.231.126.166','109.231.126.70','109.231.126.136','109.231.126.146']
for host in hosts:
	response = os.system( "ping -c 1 " + host)
	if response == 0:
		print host, 'is up!'
	else:
		print host, 'is down!'



# client = ParallelSSHClient(['109.231.126.157'], user='ubuntu',password='rexmundi220')
# localCopy = os.path.join(confDir,'logstash-forwarder.crt')
# client.copy_file(localCopy,'test.conf')
	#used to block and wait for all parallel commands to finish
#client.pool.join()

# def testFundtion(out):
# 	for host in out:
# 		for line in out[host]['stdout']:
# 			print line

# output = client.run_command('apt-get update', sudo=True)
# testFundtion(output)



# print basedir
# print confDir
# print os.path.join(confDir,'installLogstashForwarder')
# print localCopy
# print os.path.isfile(localCopy)

