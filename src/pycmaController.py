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
import getopt
import inspect
import logging
import sys
import textwrap
from cm_api.api_client import ApiResource



def getcdhMStatus(cmdHost,port=7180 ,cmuser='admin',cmpass='admin'):
	'''
		This function returns the current hosts managed by a particular Cloudera Manager Instance.
		It also lists the available Clusters and the services running on each cluster.

		TODO: ...
	'''
	cmHosts = []
	cmClusters = []
	dictCluster = {}
	api=ApiResource(cmdHost,7180,cmuser,cmpass)
	#print all hosts
	for h in api.get_all_hosts():
		cmHosts.append(h.hostname)
	
	#get all  cluster names
	for c in api.get_all_clusters():
		cmClusters.append(c.name)
		
	for cluster in cmClusters:
		serviceList = []
		for s in api.get_cluster('cluster').get_all_services():
			serviceList.append(s.name)
		dictCluster[cluster] = serviceList
	return cmHosts, cmClusters, dictCluster



def getHostRoles(api, hosts):
	for role_ref in hosts.roleRefs:
		if role_ref.get('clusterName') is None:
			continue

		role = api.get_cluster(role_ref['clusterName']).get_service(role_ref['serviceName']).get_role(role_ref['roleName'])
		LOG.debug("Eval %s (%s)" % (role.name, host.hostname))





#test for 


if __name__=='__main__':
	cmdHost = "hal720m.info.uvt.ro"

	api = ApiResource(cmdHost, "admin", "admin")
	#%--------------------------%
	a,b,c = getcdhMStatus(cmdHost)
	print a
	print b
	print c 

	getHostRoles(api,a)

	#%--------------------------%