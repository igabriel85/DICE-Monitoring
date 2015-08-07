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
import copy
from cm_api.api_client import ApiResource



def getcdhMStatus(cmdHost,port=7180 ,cmuser='admin',cmpass='admin'):
	'''
		This function returns the current hosts managed by a particular Cloudera Manager Instance.
		It also lists the available Clusters and the services running on each cluster.

		TODO: ...
	'''
	cmHosts = []
	cmClusters = []
	dictClusterServices = {}
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
			print s.name, s.serviceState, s.healthSummary, s.serviceUrl
		dictClusterServices[cluster] = serviceList
	return cmHosts, cmClusters, dictClusterServices


def getClusterList(api):
	'''
	 Function returns the object list of current clusters managed by the cm

	 Takes as input an api client of the form:

	 api = ApiResource(cm_host, username='admin',password='password')
	'''
	clusterList =[]
	for cluster in api.get_all_clusters():
		#appends only cluster name use cluster.name
		clusterList.append(cluster)
	return clusterList


def getServiceList(api):
	'''
		Returns a dictionary of objects that contains the current cluster and the associated 
		services.
	'''
	dictCluster = {}
	for c in getClusterList(api):
		serviceList = []
		for s in c.get_all_services():
			serviceList.append(s)
		dictCluster[c]=serviceList
	return dictCluster



def getHostRoles(api, hosts):
	for role_ref in hosts.roleRefs:
		if role_ref.get('clusterName') is None:
			continue

		role = api.get_cluster(role_ref['clusterName']).get_service(role_ref['serviceName']).get_role(role_ref['roleName'])
		LOG.debug("Eval %s (%s)" % (role.name, host.hostname))





#test for 


if __name__=='__main__':
	cmdHost = "109.231.126.94"

	api = ApiResource(cmdHost,7180, "admin", "admin")


	cluster =  getClusterList(api)
	print cluster[0]
	test = getServiceList(api)

	print test[cluster[0]]	
	
	#%--------------------------%
	# a,b,c = getcdhMStatus(cmdHost,7180, "admin","rexmundi220")
	# print a
	# print b
	# print c 

	#getHostRoles(api,a)

	#%--------------------------%