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



def getcdhMStatus(api,list=True):
	'''
		This function returns a host list, cluster list and a dictionary containing
		each service running per cluster.

		The function arguments are:
		api  -> ApiResource object
		list -> if set to False it returns host, cluster and service objects.
			 -> if set to True it return only host, cluster and service names
		
		TODO:
		- probably should remove dictClusterService from return, 
		  as cluster object is not iterable
	'''
	cmHosts = []
	cmClusters = []
	dictClusterServices = {}
	#print all hosts
	for h in api.get_all_hosts():
		if list == True:
			#append only h.hostname string not object
			cmHosts.append(h.hostname)
		else:
			#append host object h
			cmHosts.append(h)
	#get all  cluster names
	for c in api.get_all_clusters():
		if list == True:
			#same as host name
			cmClusters.append(c.name)
		else:
			#same as host name
			cmClusters.append(c)
		
	for cluster in cmClusters:
		serviceList = []
		for s in api.get_cluster('cluster').get_all_services():
			serviceList.append(s.name)
			#print s.name, s.serviceState, s.healthSummary, s.serviceUrl
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
		#appends only cluster object
		clusterList.append(cluster)
	return clusterList


def getServiceList(api, clusterObj):
	'''
		Function that returns a list of service object of a given cluster object.
		It also returns a dictionary that contains information aboutthe services such as:
		service state, health, and URL.

		It has the following arguments:
		api 	   -> ApiResource object 
		clusterObj -> a cluster object

	'''
	serviceList = []
	serviceListInfo={}
	for s in clusterObj.get_all_services():
		serviceInfo={}
		serviceList.append(s)
		serviceInfo.update({"ServiceStatus":s.serviceState})
		serviceInfo.update({"ServiceHealth":s.healthSummary})
		serviceInfo.update({"ServiceUrl":s.serviceUrl})
		serviceListInfo[s.name] = serviceInfo
	return serviceList, serviceListInfo


def getServiceStatus(serviceList):
	'''
		Function receives a list of service objects as argument and prints
		the service name, state, health and URL as well as performing a health
		check on all services printing the current summary.

		The function argumetns are:
		serviceList  -> list of service objects
	'''
	for s in serviceList:
		print s.name, s.serviceState, s.healthSummary, s.serviceUrl
		for chk in s.healthChecks:
			print "%s --- %s" % (chk['name'], chk['summary'])


def getRoles(serviceList, stdOut=False):
	'''
		Function returns a dictionary containing service role information such as:
		role type, state, health, reference  and reference id.

		The function arguments are:
		serviceList   ->  list of service objects
		stdOut		  ->  if True enables debug messages
					  ->  default is False
	'''
	dictRoles = {}
	for s in serviceList:
		print s
		for r in s.get_all_roles():
			roleList = {}
			roleList["type"]={r.type}
			roleList["RoleState"]={r.roleState}
			roleList["RoleHealth"]={r.healthSummary}
			roleList["HostRef"]={r.hostRef}
			roleList["HostRefID"]={r.hostRef.hostId}
			dictRoles[s]=roleList
			if stdOut == True:
				print "%---------------------------------------------------------%"
				print "Role name: %s\nState: %s\nHealth: %s\nHostRef %s\nHost: %s" % (r.name, r.roleState, r.healthSummary, r.hostRef, r.hostRef.hostId)
				print "%---------------------------------------------------------%"
	return dictRoles
			

def getHostRoles(api, hostsObjList):
	print hosts
	#for h in hosts:
		#print h.hostname
		#print h.roleRefs

	#print hosts[0].get_all_roles()
	# for host in hosts:
	# 	print host.roleRefs
	# 	for role_ref in host.roleRefs:
	# 		if role_ref.get('clusterName') is None:
	# 			continue

	# 		role = api.get_cluster(role_ref['clusterName']).get_service(role_ref['serviceName']).get_role(role_ref['roleName'])
	# 		LOG.debug("Eval %s (%s)" % (role.name, host.hostname))

		# 	if role.type == "DATANODE":
		# 		print "Found DATANODE"
		# 	elif role.type == 'KAFKA':
		# 		print "Found KAFKA"
		# 	else:
		# 		continue


def main(argv):
  try:
    opts, args=getopt.getopt(argv,"hdi:p:u:s:",["hostEndpoint","port","user","password"])
  except getopt.GetoptError:
    print "%-------------------------------------------------------------------------------------------%"
    print "Invalid argument! Arguments must take the form:"
    print ""
    print "pycmaController.py { -h|-d|-i <CM_IP> -p <PORT> -u <USERNAME> -s <PASSWORD>}"
    print ""
    print "%-------------------------------------------------------------------------------------------%"
    sys.exit(2)
  for opt, arg in opts:
      if opt == '-h':
        print "%-------------------------------------------------------------------------------------------%"
        print ""
        print "pycmaController is desigend to facilitate the querying Cloudera Manager Current deployment Status."
        print "It currently supports 6 arguments: -h for help or -d for debug mode"
        print "-h -> help"
        print "-d -> debug mode"
        print "-i -> is used to specify Cloudera Management endpoint IP address"
        print "	  -> -i <CM-IP>"
        print "-p -> is used to specify the Cloudera Manager port"
        print "   -> by default it is set to 7180"
        print "-u -> is used to specify the Cloudera Manager username"
        print "	  -> -u <USERNAME>"
        print "-s -> is used to specify the Cloudera Manager password"
        print "	  -> -s <PASSWORD>"
        print "Usage Example:"
        print "pycmaController.py {-h|-d}"
        print "                                                                                              "
        print "%-------------------------------------------------------------------------------------------%"
        sys.exit()
      elif opt in ("-d"):
      	print "Entering DebugMode"

if __name__=='__main__':
	if len(sys.argv) == 1:
		cmdHost = "109.231.126.94"
		api = ApiResource(cmdHost,7180, "admin", "admin")

		#%--------------------------%
		#getClusterList() usecase
		# clist = getClusterList(api)
		# for c in clist:
		# 	print c.name
		#%--------------------------%

		#%--------------------------%
		#getCDHMStatus usecase
		hosts,clusters,clusterServices = getcdhMStatus(api,False)
		#print hosts
		#print clusters
		#print clusterServices
		#%--------------------------%
		#getServiceList usecase
		for c in clusters:
			cluster_services, cluster_service_vb= getServiceList(api, c)
			#print cluster_services
			#print cluster_service_vb
			getServiceStatus(cluster_services)
			for s in cluster_services:
				#print s.name, s.serviceState
				print s.get_all_roles()
				

		#%--------------------------%
		#print getRoles(cluster_services, stdOut = True)
		#getHostRoles(api,hosts)

		#%--------------------------%
	else:
		main(sys.argv[1:])