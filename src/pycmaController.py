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

from cm_api.api_client import ApiResource

cmHost = "109.231.126.94"

def getcdhMStatus(cmHost,port=7180 ,cmuser='admin',cmpass='admin'):
	'''
		This function returns the current hosts managed by a particular Cloudera Manager Instance.
		It also lists the available Clusters and the services running on each cluster.

		TODO: ...
	'''
	cmHosts = []
	cmClusters = []
	dictCluster = {}
	api=ApiResource(cmHost,7180,cmuser,cmpass)
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



#test for 
a,b,c = getcdhMStatus(cmHost)

print a
print b
print c 