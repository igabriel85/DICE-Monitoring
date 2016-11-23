"""

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
"""

import gevent
import gevent.queue
import requests
import json
from app import *
from datetime import *
import time


headers = {'content-type': 'application/json'}


class GreenletRequests():
    NodeResponsesGet = []
    NodeResponsesPost = []
    NodeResponsesPut = []
    NodeResponsesDelete = []
    ng = 0
    np = 0
    npo = 0
    nd = 0

    def __init__(self, resourceList):
        self.resourceList = resourceList

    def parallelGet(self):
        queue = gevent.queue.Queue()
        for i in self.resourceList:
            queue.put(i)

        gList = []
        for t in range(len(self.resourceList)):
            gl = gevent.spawn(getRequest, queue)
            gList.append(gl)

        # print str(gList)
        app.logger.info('[%s] : [INFO] gList %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        str(gList))
        gevent.joinall(gList)

        return GreenletRequests.NodeResponsesGet

    def parallelPost(self, payload):
        queue = gevent.queue.Queue()
        gList = []
        if type(self.resourceList) is list:
            for i in self.resourceList:
                queue.put(i)

            for t in range(len(self.resourceList)):
                gl = gevent.spawn(postRequest, queue, payload)
                gList.append(gl)

            # print str(gList)
            app.logger.info('[%s] : [INFO] gList %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        str(gList))
            gevent.joinall(gList)

            return GreenletRequests.NodeResponsesPost

        if type(self.resourceList) is dict:
            for k, v in self.resourceList.iteritems():
                # print k
                app.logger.info('[%s] : [INFO] Key %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        str(k))
                queue.put(k)

            for k, v in self.resourceList.iteritems():
                gl = gevent.spawn(postRequest, queue, v)
                gList.append(gl)

            # print str(gList)
            app.logger.info('[%s] : [INFO] gList %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        str(gList))
            gevent.joinall(gList)

            return GreenletRequests.NodeResponsesPost

    def parallelPut(self, payload):
        queue = gevent.queue.Queue()
        for i in self.resourceList:
            queue.put(i)

        gList = []
        for p in range(len(self.resourceList)):
            gl = gevent.spawn(putRequest, queue, payload)
            gList.append(gl)

        # print str(gList)
        app.logger.info('[%s] : [INFO] gList %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        str(gList))
        gevent.joinall(gList)

        return GreenletRequests.NodeResponsesPut


    def parallelDelete(self):
        queue = gevent.queue.Queue()
        for i in self.resourceList:
            queue.put(i)

        gList = []
        for t in range(len(self.resourceList)):
            gl = gevent.spawn(deleteRequest, queue)
            gList.append(gl)

        # print str(gList)
        app.logger.info('[%s] : [INFO] gList %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        str(gList))
        gevent.joinall(gList)

        return GreenletRequests.NodeResponsesDelete

    def reset(self):  # TODO:  Check if reset is required for all attributes separately or general one is ok
        GreenletRequests.NodeResponsesGet = []
        GreenletRequests.NodeResponsesPost = []
        GreenletRequests.NodeResponsesPut = []
        GreenletRequests.NodeResponsesDelete = []


def randomT(queue, name):
    while not queue.empty():
        t = queue.get(timeout=1)
        gevent.sleep(5)
        # print 'I am + ' + name + ' executing ' + str(GreenletRequests.ng)
        app.logger.info('[%s] : [INFO] %s executing %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        name, str(GreenletRequests.ng))
        GreenletRequests.ng += 1
        gevent.sleep(0)


def getRequest(queue):
    response = {}
    while not queue.empty():
        resURI = queue.get(timeout=1)
        try:
            r = requests.get(resURI, timeout=2)
            data = r.json()
            response['Node'] = resURI
            response['StatusCode'] = r.status_code
            response['Data'] = data
        except requests.exceptions.Timeout:
            response['Node'] = resURI
            response['StatusCode'] = 408
            response['Data'] = 'n/a'
        except requests.exceptions.ConnectionError:
            response['Node'] = resURI
            response['StatusCode'] = 404
            response['Data'] = 'n/a'

        GreenletRequests.NodeResponsesGet.append(response)
        # print 'Threaded GET with ID ' + str(GreenletRequests.ng) + ' executed for ' + resURI
        app.logger.info('[%s] : [INFO] Thread GET with ID %s executed for %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        str(GreenletRequests.ng), resURI)
        GreenletRequests.ng += 1
        gevent.sleep(0)


def postRequest(queue, payload=None):
    response = {}
    statusCode = {}
    data = {}
    while not queue.empty():
        resourceURI = queue.get(timeout=1)
        print payload
        try:
            if payload is None:
                r = requests.post(resourceURI, timeout=20, headers=headers)
            else:
               # print "$$$$$$$$" + str(payload)
                r = requests.post(resourceURI, data=json.dumps(payload), timeout=20, headers=headers)
            if r.headers['Content-Type'] == 'application/json':
                data = r.json()
            else:
                data = r.text
            response['Node'] = resourceURI
            response['StatusCode'] = r.status_code
            response['Data'] = data
        except requests.exceptions.Timeout:
            response['Node'] = resourceURI
            response['StatusCode'] = 408
            response['Data'] = data
        except requests.exceptions.ConnectionError:
            response['Node'] = resourceURI
            response['StatusCode'] = 404
            response['Data'] = 'n/a'

        GreenletRequests.NodeResponsesPost.append(response)
        # print 'Threaded POST with ID ' + str(GreenletRequests.np) + ' executed for ' + resourceURI
        app.logger.info('[%s] : [INFO] Thread POST with ID %s executed for %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        str(GreenletRequests.ng), resourceURI)
        GreenletRequests.np += 1
        gevent.sleep(0)


def putRequest(queue, payload=None):
    response = {}
    statusCode = {}
    data = {}
    while not queue.empty():
        resourceURI= queue.get(timeout=1)
        response['Node'] = resourceURI
        try:
            if payload is None:
                r = requests.put(resourceURI, timeout=20)
            else:
                r = requests.put(resourceURI, data=payload, timeout=20)
            if r.headers['Content-Type'] == 'application/json':
                data = r.json
            else:
                data = r.text
            response['StatusCode'] = r.status_code
            response['Data'] = data
        except requests.exceptions.Timeout:
            response['StatusCode'] = 408
            response['Data'] = data
        except requests.exceptions.ConnectionError:
            response['Node'] = resourceURI
            statusCode['StatusCode'] = 404
            response['Data'] = 'n/a'

        GreenletRequests.NodeResponsesPost.append(response)
        # print 'Threaded PUT with ID ' + str(GreenletRequests.npo) + ' executed for ' + resourceURI
        app.logger.info('[%s] : [INFO] Thread PUT with ID %s executed for %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        str(GreenletRequests.ng), resourceURI)
        GreenletRequests.npo += 1
        gevent.sleep(0)


def deleteRequest(queue):
    response = {}
    while not queue.empty():
        resURI = queue.get(timeout=1)
        try:
            r = requests.delete(resURI, timeout=2)
            data = r.json()
            response['Node'] = resURI
            response['StatusCode'] = r.status_code
            response['Data'] = data
        except requests.exceptions.Timeout:
            response['Node'] = resURI
            response['StatusCode'] = 408
            response['Data'] = 'n/a'
        except requests.exceptions.ConnectionError:
            response['Node'] = resURI
            response['StatusCode'] = 404
            response['Data'] = 'n/a'

        GreenletRequests.NodeResponsesGet.append(response)
        # print 'Threaded DELETE with ID ' + str(GreenletRequests.nd) + ' executed for ' + resURI
        app.logger.info('[%s] : [INFO] Thread DELETE with ID %s executed for %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        str(GreenletRequests.ng), resURI)
        GreenletRequests.nd += 1
        gevent.sleep(0)

#resourceList = ['http://109.231.121.135:5000/agent/v1/check', 'http://109.231.121.194:5000/agent/v1/check']
#resourceList = ['http://109.231.121.135:5000/agent/v1/deploy','http://109.231.121.134:5000/agent/v1/deploy','http://109.231.121.156:5000/agent/v1/deploy','http://109.231.121.194:5000/agent/v1/deploy']
#test = GreenletRequests(resourceList)
#
#testG = test.parallelGet()
#ff = {"roles": ["hdfs"]}
#testP = test.parallelPost(ff)

#print testG
#print testP



