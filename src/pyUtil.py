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
import socket
import sys
import signal
import subprocess
from datetime import datetime
import requests
import os


def portScan(addrs,ports):
	'''
		Check if a range of ports are open or not
	'''
	t1 = datetime.now()
	for address in addrs:
		for port in ports:
			try:
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sockTest = sock.connect_ex((address,int(port)))
				if sockTest==0:
					print "Port %s \t on %s Open" % (port, address)
				sock.close()	
			except KeyboardInterrupt:
				print "User Intrerupt detected!"
				print "Closing ...."
				sys.exit()
			except socket.gaierror:
				print 'Hostname not resolved. Exiting'
				sys.exit()
			except socket.error:
				print 'Could not connect to server'
				sys.exit()
	#stop time
	t2 = datetime.now()

	#total time
	total = t2 - t1
	
	print 'Scanning Complete in: ', total

def checkPID(pid):
	"""
	Check For the existence of a unix pid.
	Sending signal 0 to a pid will raise an OSError exception if the pid is not running, and do nothing otherwise.
	"""
	if pid == 0:	#If PID newly created return False
		return False
	try:
		os.kill(int(pid), 0)
	except OSError:
		return False
	else:
		return True

def startLocalProcess(command):
	'''
	Starts a process in the background and writes a pid file.
    command -> needs to be in the form of a list of basestring
    	    -> 'yes>/dev/null' becomes ['yes','>','/dev/null']

	Returns integer: PID
	'''
	process = subprocess.Popen(command, shell=True)
	

	return process.pid
	

def checkUnique(nodeList):
	'''
	Checks for unique values in a dictionary.
	'''
	seen={}
	result =set()
	sameCredentials = []
	ipNode = []
	for d in nodeList:
		for k,v in d.iteritems():
			if v in seen:
				ipNode.append(k)
				sameCredentials.append(v)
				result.discard(seen[v])
			else:
				seen[v] = k
				result.add(k)
	return list(result), sameCredentials, ipNode



#print {v['nPass']:v for v in test}.values()
#print checkUnique(test)
