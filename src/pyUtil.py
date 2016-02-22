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
		os.kill(pid, 0)
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
	seen = {}
	result = set()
	sameCredentials = []
	ipNode = []
	for d in nodeList:
		for k, v in d.iteritems():
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

class AgentResourceConstructor():
	uriRoot = '/agent/v1'
	chck = '/check'
	clctd = '/collectd'
	logsf = '/lsf'
	jmxr = '/jmx'
	confr = '/conf'
	logsr = '/logs'
	deployr = '/deploy'
	noder = '/node'
	startr = '/start'
	stopr = '/stop'

	def __init__(self, IPList, Port):
		self.IPList = IPList
		self.Port = Port



	def check(self):
		resourceList = []
		for ip in self.IPList:
			resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot, AgentResourceConstructor.chck)
			resourceList.append(resource)
		return resourceList

	def collectd(self):
		cList = []
		for ip in self.IPList:
			resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot, AgentResourceConstructor.clctd)
			cList.append(resource)
		return cList

	def lsf(self):
		lList = []
		for ip in self.IPList:
			resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot, AgentResourceConstructor.logsf)
			lList.append(resource)
		return lList

	def jmx(self):
		jList = []
		for ip in self.IPList:
			resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot, AgentResourceConstructor.jmxr)
			jList.append(resource)
		return jList

	def deploy(self):
		dList = []
		for ip in self.IPList:
			resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot, AgentResourceConstructor.deployr)
			dList.append(resource)
		return dList

	def node(self):
		nList = []
		for ip in self.IPList:
			resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot, AgentResourceConstructor.noder)
			nList.append(resource)
		return nList

	def start(self):
		sList = []
		for ip in self.IPList:
			resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot, AgentResourceConstructor.startr)
			sList.append(resource)
		return sList

	def stop(self):
		stList = []
		for ip in self.IPList:
			resource = 'http://%s:%s%s%s' %(ip, self.Port, AgentResourceConstructor.uriRoot, AgentResourceConstructor.stopr)
			stList.append(resource)
		return stList

	def startSelective(self, comp):
		ssList = []
		for ip in self.IPList:
			resource = 'http://%s:%s%s%s/%s' %(ip, self.Port, AgentResourceConstructor.uriRoot, AgentResourceConstructor.startr, comp)
			ssList.append(resource)
		return ssList

	def stopSelective(self, comp):
		stsList = []
		for ip in self.IPList:
			resource = 'http://%s:%s%s%s/%s' %(ip, self.Port, AgentResourceConstructor.uriRoot, AgentResourceConstructor.stopr, comp)
			stsList.append(resource)
		return stsList

	def logs(self, comp):
		logList = []
		for ip in self.IPList:
			resource = 'http://%s:%s%s%s/%s' %(ip, self.Port, AgentResourceConstructor.uriRoot, AgentResourceConstructor.logsr, comp)
			logList.append(resource)
		return logList

	def conf(self, comp):
		confList = []
		for ip in self.IPList:
			resource = 'http://%s:%s%s%s/%s' %(ip, self.Port, AgentResourceConstructor.uriRoot, AgentResourceConstructor.stopr, comp)
			confList.append(resource)
		return confList

def dbBackup(db, source, destination, version=1):
	'''

	:param db: -> database
	:param source: -> original name
	:param destination: -> new name
	:return:
	'''


	vdest = destination+str(version)
	if os.path.isfile(source) is True:
		if os.path.isfile(vdest) is True:
			return dbBackup(db, source, destination, version + 1)
		os.rename(source, destination)


# test = AgentResourceConstructor(['192.12.12.12'], '5000')
#
# t = test.check()
# c = test.collectd()
# l = test.lsf()
# j = test.jmx()
# d = test.deploy()
# n = test.node()
# s = test.start()
# st = test.stop()
# ss = test.startSelective('lsf')
# sts = test.stopSelective('collectd')
# log = test.logs('lsf')
# conf = test.conf('collectd')
# print t
# print c
# print l
# print j
# print d
# print n
# print s
# print st
# print ss
# print sts
# print log
# print conf
