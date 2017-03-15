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

import json
import os
import sys
from pprint import pprint
from fabric.api import *


agent_loc = "https://github.com/dice-project/DICE-Monitoring/releases/download/latest-agent/dmon-agent.tar.gz"


def readCfg(fileLoc):
    '''
    :param fileLoc: location of json file
    :return: dict
    '''
    if not os.path.isfile(fileLoc):
        print "Config File not found at: %s" %str(fileLoc)
        sys.exit(1)
    with open(fileLoc) as data_file:
        try:
            data = json.load(data_file)
        except:
            print "Invalid file %s must be valid JSON!" %str(fileLoc)
            sys.exit(1)
    print "Config file:"
    pprint(data)
    return data


def set_hosts(dataDict, key_file=None):
    '''
    :param dataDict: node setup dictionary
    :param key_file: location of ssh key
    :return: sets envhosts, password and username
    '''
    nodeList = []
    for node in dataDict['Nodes']:
        nodeList.append(node['NodeIP'])
    print "Nodes are set to: %s" % str(nodeList)
    print "User: %s" % str(dataDict['Nodes'][0]['username'])
    print "Password: %s" % str(dataDict['Nodes'][0]['password'])
    if key_file is not None:
        if not os.path.isfile(key_file):
            print "SSH key not found at %s" % str(key_file)
            sys.exit(1)
        else:
            env.key_filename = key_file
            print "SSH Key: %s" % str(key_file)
    env.hosts = nodeList
    env.user = dataDict['Nodes'][0]['username']
    env.password = dataDict['Nodes'][0]['password']

if __name__ == '__main__':
    loc = 'nodes.json'
    nodesDict = readCfg(loc)
    set_hosts(nodesDict)
