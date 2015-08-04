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

basedir = os.path.abspath(os.path.dirname(__file__))
confDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')




client = ParallelSSHClient(['109.231.126.157'], user='ubuntu',password='rexmundi220')
localCopy = os.path.join(confDir,'logstash-forwarder.crt')
client.copy_file(localCopy,'test.conf')
	#used to block and wait for all parallel commands to finish
#client.pool.join()

# def testFundtion(out):
# 	for host in out:
# 		for line in out[host]['stdout']:
# 			print line

# output = client.run_command('apt-get update', sudo=True)
# testFundtion(output)

print basedir
print confDir
print os.path.join(confDir,'installLogstashForwarder')
print localCopy
print os.path.isfile(localCopy)

