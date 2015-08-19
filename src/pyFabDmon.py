import fabric
from fabric.api import *
from fabric.contrib.console import confirm

env.hosts = ['109.231.126.177','109.231.126.189']
# Set the username
env.user   = "ubuntu"

# Set the password [NOT RECOMMENDED]
env.password = "rexmundi220"

def startCollectd():
	sudo('collectd',pty=False)# pty must be set to false else it does not work

def checkCollectd():
	sudo('service collectd status',pty=False)# pty must be set to false else it does not work