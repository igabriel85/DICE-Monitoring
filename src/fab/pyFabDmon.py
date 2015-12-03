import fabric
from fabric.api import *
from fabric.contrib.console import confirm

#fab -f pyFabDmon.py -t 60  uploadBoostrapt
#fab -f pyFabDmon.py -t 60 -P  editHostFile
#fab -f pyFabDmon.py -t 60 -P cleanup

#env.hosts = ['109.231.122.187' ,'109.231.122.173' ,'109.231.122.164' ,'109.231.122.233' ,'109.231.122.201' ,'109.231.122.130' ,'109.231.122.231' ,'109.231.122.194' ,'109.231.122.182' ,'109.231.122.207' ,'109.231.122.156','109.231.122.240' ,'109.231.122.127']


#full = ['109.231.122.228' ,'109.231.122.187' ,'109.231.122.173' ,'109.231.122.164' ,'109.231.122.233' ,'109.231.122.201' ,'109.231.122.130' ,'109.231.122.231' ,'109.231.122.194' ,'109.231.122.182' ,'109.231.122.207' ,'109.231.122.156','109.231.122.240' ,'109.231.122.127']

#hostFQDN = ['dice.cdh5.mng.internal', 'dice.cdh5.w1.internal','dice.cdh5.w2.internal','dice.cdh5.w3.internal','dice.cdh5.w4.internal','dice.cdh5.w5.internal','dice.cdh5.w6.internal','dice.cdh5.w7.internal','dice.cdh5.w8.internal','dice.cdh5.w9.internal','dice.cdh5.w10.internal','dice.cdh5.w11.internal','dice.cdh5.w12.internal','dice.cdh5.w13.internal']

#env.hosts = ['109.231.121.135', '109.231.121.194', '109.231.121.134', '109.231.121.156', '109.231.121.210'] 
env.hosts = ['109.231.126.18'] 

# Set the username
env.user   = "<user>"

# Set the password [NOT RECOMMENDED]
env.password = "<password>"


def uploadBoostrapt():
	put('nodeBootstrapper.sh','~/nodeBootstrapper.sh')

def editHostFile():
	sudo('chmod +x nodeBootstrapper.sh')
	sudo('./nodeBootstrapper.sh',pty=False)

def cleanup():
	sudo('chown -R ubuntu.ubuntu /opt',pty=False)
	run('cd /home/ubuntu', pty=False)
	sudo('rm -rf /home/ubuntu/*', pty=False)

def startCollectd():
	sudo('collectd',pty=False)# pty must be set to false else it does not work

def checkCollectd():
	sudo('service collectd status',pty=False)# pty must be set to false else it does not work

def stopLSF():
	sudo('service logstash-forwarder stop', pty=False)
	sudo('rm -rf /etc/logstash-forwarder.conf')

def removeLSF():
	sudo('apt-get remove logstash-forwarder -y', pty=False)
	sudo('rm -rf /etc/logstash-forwarder.conf')

def addPubKey():
	key = " "
	sudo('echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDc/9c1v6ZlpX6JF9W91NwJU1IFpxDaRN/T26rVXvutv2tiHBILyBRapv7jOd1eM6pkuS5h+0HwWbz/QJyxfqD8nBnYdlg8jQrUtJoI6ICyf5E2nP4KqYkUINuRcSwBRSIPmpH/iJ66HoR3ydP8K+MXW9HXo0IN7DdI9GLn2YSZtqSlWJValtpEa9rZPk7/MO6vrolOQdLA1iyOZdV/IcG7RPwUvyq/Kbc0q5yJ4Q2AKiH38CTaBQ0PI70YB4EfM0slbcM+ddpFezDNuXVxuhLGxAZGhi/ha8caS5CKOJ0j9GTQONfTnF5/IeZk671nByw0ZNFmFWf4jZ0EcX82nShX eugenio@Eugenios-MacBook-Air.local" >> .ssh/authorized_keys')





