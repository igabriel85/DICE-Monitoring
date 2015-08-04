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


#folder locations
basedir = os.path.abspath(os.path.dirname(__file__))
confDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')

#monitoring endpoints
#logstashsip = ''
#logstashport = ''


#initialize hostlist
hostlist = [ ]
userName = ''
uPassword = ''

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

# client = ParallelSSHClient(['109.231.126.221','109.231.126.222'], user=userName,password=uPassword)
# try:
# 	output = client.run_command('mkdir this_is_a_test_2', sudo=True)
# 	for host in output:
# 		for line in output[host]['stdout']:
# 			print line
# except (AuthenticationException, UnknownHostException, ConnectionErrorException):
# 	print "Stff"

def tests():
	client = ParallelSSHClient(['109.231.126.221','109.231.126.222'], user='ubuntu',password='rexmundi220')
	#create path to file
	localCopy = os.path.join(confDir,'test.conf')
	#copy to home dire after connection
	try:
		output = client.copy_file(localCopy,"test2.conf")
		#used to block and wait for all parallel commands to finish
		client.pool.join()
	except (AuthenticationException, UnknownHostException, ConnectionErrorException):
		print "Stff"




if __name__=='__main__':
	hostlist = ['109.231.126.190','109.231.126.222','109.231.126.221','109.231.126.94',
	'109.231.126.102','109.231.126.166','109.231.126.70','109.231.126.136','109.231.126.146']
	#,'109.231.126.190','109.231.126.222','109.231.126.221','109.231.126.94',
	#'109.231.126.102','109.231.126.166','109.231.126.70','109.231.126.136','109.231.126.146','109.231.126.145'
	userName = 'ubuntu'
	uPassword = 'rexmundi220'
	#installCollectd(hostlist,userName,uPassword)
	installLogstashForwarder(hostlist,userName,uPassword)
	#tests()
