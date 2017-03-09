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
from urlparse import urlparse
import os
import shutil
import glob
import tarfile


headers = {'content-type': 'application/json'}
# Global variable to denote the timeout of requests, default to 5 set by env variable DMON-TIMEOUT
DMON_TIMEOUT = os.getenv('DMON_TIMEOUT', 5)

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
        self.outputDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

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

    def parallelFileGet(self):
        queue = gevent.queue.Queue()
        for i in self.resourceList:
            queue.put(i)

        gList = []
        for t in range(len(self.resourceList)):
            gl = gevent.spawn(getrequestFile, queue, self.outputDir)
            gList.append(gl)

        # print str(gList)
        app.logger.info('[%s] : [INFO] gFileList %s', datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
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
        resURI = queue.get(timeout=DMON_TIMEOUT)
        try:
            r = requests.get(resURI, timeout=DMON_TIMEOUT)
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


def getrequestFile(queue, output):
    response = {}
    while not queue.empty():
        resURI = queue.get(timeout=1)
        app.logger.info('[%s] : [INFO] Thread File GET with ID %s starts execution for %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        str(GreenletRequests.ng), resURI)
        hostURL = urlparse(resURI)
        hostID = hostURL.hostname
        logName = 'worker-%s.tar' % hostID
        logDump = os.path.join(output, logName)
        try:
            r = requests.get(resURI, timeout=DMON_TIMEOUT, stream=True)
            if r.status_code == 200:
                with open(logDump, 'wb') as out_file:  # TODO investaigate chunck writter
                    shutil.copyfileobj(r.raw, out_file)

            response['Node'] = resURI
            response['StatusCode'] = r.status_code
            response['LogName'] = logDump
            response['Headers'] = r.headers
            del r
        except requests.exceptions.Timeout:
            response['Node'] = resURI
            response['StatusCode'] = 408
            response['LogName'] = logDump
        except requests.exceptions.ConnectionError:
            response['Node'] = resURI
            response['StatusCode'] = 404
            response['LogName'] = logDump

        GreenletRequests.NodeResponsesGet.append(response)
        # print 'Threaded GET with ID ' + str(GreenletRequests.ng) + ' executed for ' + resURI
        app.logger.info('[%s] : [INFO] Thread File GET with ID %s executed for %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
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
        resourceURI= queue.get(timeout=DMON_TIMEOUT)
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
        resURI = queue.get(timeout=DMON_TIMEOUT)
        try:
            r = requests.delete(resURI, timeout=DMON_TIMEOUT)
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


def getStormLogsGreen(resourceList):
    bworker = GreenletRequests(resourceList)
    rsp = bworker.parallelFileGet()
    print rsp
    lFile = []
    workerFile = 'worker-*.tar'
    outDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    # logFile = os.path.join(stDir, workerFile)
    for name in glob.glob(os.path.join(outDir, workerFile)):
        lFile.append(name)
    ts = time.time()
    st = datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H:%M:%S')
    concatLogname = 'workerlogs_%s.tar' % st
    tarlog = os.path.join(outDir, concatLogname)
    out = tarfile.open(tarlog, mode='w')
    try:
        for file in lFile:
            path, filename = os.path.split(file)
            out.add(file, arcname=filename)
    finally:
        out.close()

    # clean up
    for el in lFile:
        os.remove(el)


if __name__ == '__main__':
    resourceList = ['http://85.120.206.45:5222/agent/v2/bdp/storm/logs', 'http://85.120.206.47:5222/agent/v2/bdp/storm/logs', 'http://85.120.206.48:5222/agent/v2/bdp/storm/logs', 'http://85.120.206.49:5222/agent/v2/bdp/storm/logs']
    getStormLogsGreen(resourceList)
    #ff = {"roles": ["hdfs"]}
    #testP = test.parallelPost(ff)

    #print testG
    #print testP



