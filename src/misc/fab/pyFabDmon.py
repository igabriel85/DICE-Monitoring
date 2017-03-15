"""

Copyright 2017, Institute e-Austria, Timisoara, Romania
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
"""

from readConf import *

#fab -f pyFabDmon.py -t 60  uploadBoostrapt
#fab -f pyFabDmon.py -t 60 -P  editHostFile
#fab -f pyFabDmon.py -t 60 -P cleanup

loc = 'nodes.json'
key = 'node.pem'
if not os.path.isfile(key):
    key = None
crt = 'logstash-forwarder.crt'
nodesDict = readCfg(loc)
set_hosts(nodesDict, key)


def uploadSparkConf():
    put('metrics.properties', '~/metrics.properties')
    sudo('mv metrics.properties /etc/spark/conf/metrics.properties')


def experimentaSparkConf():
    put('sparkConf.sh', '~/sparkConf.sh')
    sudo('bash sparkConf.sh')


def sparkCSV():
    put('sparkN.sh', '~/sparkN.sh')
    sudo('bash sparkN.sh')


def uploadBoostrapt():
    put('nodeBootstrapper.sh', '~/nodeBootstrapper.sh')


def editHostFile():
    sudo('chmod +x nodeBootstrapper.sh')
    sudo('./nodeBootstrapper.sh', pty=False)


def cleanup():
    sudo('chown -R ubuntu.ubuntu /opt', pty=False)
    run('cd /home/ubuntu', pty=False)
    sudo('rm -rf /home/ubuntu/*', pty=False)


def startCollectd():
    sudo('collectd', pty=False)# pty must be set to false else it does not work


def checkCollectd():
    sudo('service collectd status', pty=False)# pty must be set to false else it does not work


def stopLSF():
    sudo('service logstash-forwarder stop', pty=False)
    sudo('rm -rf /etc/logstash-forwarder.conf')


def removeLSF():
    sudo('apt-get remove logstash-forwarder -y', pty=False)
    sudo('rm -rf /etc/logstash-forwarder.conf')


def addPubKey():
    key = " "
    sudo('echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDc/9c1v6ZlpX6JF9W91NwJU1IFpxDaRN/T26rVXvutv2tiHBILyBRapv7jOd1eM6pkuS5h+0HwWbz/QJyxfqD8nBnYdlg8jQrUtJoI6ICyf5E2nP4KqYkUINuRcSwBRSIPmpH/iJ66HoR3ydP8K+MXW9HXo0IN7DdI9GLn2YSZtqSlWJValtpEa9rZPk7/MO6vrolOQdLA1iyOZdV/IcG7RPwUvyq/Kbc0q5yJ4Q2AKiH38CTaBQ0PI70YB4EfM0slbcM+ddpFezDNuXVxuhLGxAZGhi/ha8caS5CKOJ0j9GTQONfTnF5/IeZk671nByw0ZNFmFWf4jZ0EcX82nShX eugenio@Eugenios-MacBook-Air.local" >> .ssh/authorized_keys')


def listOPT():
    run('ls -laht /opt')


def moveAgent():
    sudo('mv -v /opt/dmon-agent /opt/backup')


def downloadAgent():
    command = "cd /opt && wget %s" %agent_loc
    sudo(command)


def unpackAgent():
    command = "cd /opt && tar -xvf dmon-agent.tar.gz"
    sudo(command)
    sudo('rm -rf /opt/dmon-agent.tar.gz')


def startAgent():
    command = "cd /opt/dmon-agent && ./dmon-agent.sh"
    sudo(command, pty=False)


def statusAgent():
    command = "ps axjf |grep -i dmon-agent"
    run(command)


def openstackFix():
    sudo('echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf > /dev/null')


def checkLSF():
    sudo('service logstash-forwarder status')


def replaceCRT():
    sudo('cd /opt/certs && mv logstash-forwarder.crt logstash-forwarder.crt.old')
    put(crt, 'logstash-forwarder.crt')
    sudo('mv logstash-forwarder.crt /opt/certs/logstash-forwarder.crt')