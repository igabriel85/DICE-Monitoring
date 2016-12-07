import threading
import Queue
import time
import requests
from flask import copy_current_request_context
from app import *
import shutil
from datetime import datetime
from urlparse import urlparse
import os
import glob
import tarfile


class getThread(threading.Thread):
    exitFlag = 0
    NodeResponses = []

    def __init__(self, threadID, resource, q, lock):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.resource = resource
        self.q = q
        self.lock = lock

    def run(self):
        # print "Starting thread " + str(self.threadID)
        app.logger.info('[%s] : [INFO] Starting GET Thread %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(self.threadID))
        tRequest(self.resource, self.q, self.lock)
        app.logger.info('[%s] : [INFO] Exiting GET Thread %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(self.threadID))
        # print "Exiting thread " + str(self.threadID)


class getFileThread(threading.Thread):
    exitFlag = 0
    Noderesponses = []

    def __init__(self, threadID, resource, q, lock, output):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.resource = resource
        self.q = q
        self.lock = lock
        self.output = output

    def run(self):
        app.logger.info('[%s] : [INFO] Starting GET File Thread %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(self.threadID))
        tRequestFile(self.q, self.lock, self.output)
        app.logger.info('[%s] : [INFO] Exiting GET File Thread %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(self.threadID))


class postThread(threading.Thread):
    def __init__(self, threadID, resource, q, payload):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.resource = resource
        self.q = q
        self.payload = payload

    def run(self):
        # print "Starting thread  " + str(self.threadID)
        app.logger.info('[%s] : [INFO] Starting POST Thread %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(self.threadID))
        tRequestPost(self.resource, self.q, self.payload)
        app.logger.info('[%s] : [INFO] Exiting POST Thread %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(self.threadID))
        # print "Exiting thread " + str(self.threadID)


def tRequest(resource, q, lock):  #  TODO: pass function as argument with context decorator
    response = {}
    statusCode = {}
    data = {}
    while not getThread.exitFlag:
        lock.acquire()
        if not q.empty():
            resourceURI = q.get()
            try:
                r = requests.get(resourceURI, timeout=2)
                data = r.json()
                response['Node'] = resourceURI
                response['StatusCode'] = r.status_code
                response['Data'] = data
            except requests.exceptions.Timeout:
                response['Node'] = resourceURI
                statusCode['StatusCode'] = 408
                response['Data'] = 'n/a'
            except requests.exceptions.ConnectionError:
                response['Node'] = resourceURI
                statusCode['StatusCode'] = 404
                response['Data'] = 'n/a'

            getThread.NodeResponses.append(response)
            lock.release()
            app.logger.info('[%s] : [INFO] %s response %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), resourceURI, data)
            # print "%s response %s" % (resourceURI, data)
        else:
            lock.release()
        time.sleep(1)


def tRequestFile(q, lock, output):
    response = {}
    statusCode = {}
    while not getThread.exitFlag:
        lock.acquire()
        if not q.empty():
            resourceURI = q.get()
            hostURL = urlparse(resourceURI)
            hostID = hostURL.hostname
            logName = 'worker-%s.tar' % hostID
            logDump = os.path.join(output, logName)
            try:
                r = requests.get(resourceURI, timeout=50, stream=True)
                if r.status_code == 200:
                    with open(logDump, 'wb') as out_file: # TODO investaigate chunck writter
                        shutil.copyfileobj(r.raw, out_file)
                response['Node'] = resourceURI
                response['StatusCode'] = r.status_code
                response['LogName'] = logDump
                response['Headers'] = r.headers
                del r
            except requests.exceptions.Timeout:
                response['Node'] = resourceURI
                statusCode['StatusCode'] = 408
                response['LogName'] = 0
            except requests.exceptions.ConnectionError:
                response['Node'] = resourceURI
                statusCode['StatusCode'] = 404
                response['LogName'] = 0

            getThread.NodeResponses.append(response)
            lock.release()
            app.logger.info('[%s] : [INFO] %s response %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), resourceURI, response['LogName'])
            # print "%s response %s" % (resourceURI, data)
        else:
            lock.release()
        time.sleep(1)


def tRequestPost(resource, q, payload=None):
    response = {}
    statusCode = {}
    data = {}
    while not getThread.exitFlag:
        q.acquire()
        if not q.empty():
            resourceURI = q.get()
            response['Node'] = resourceURI
            try:
                if payload is None:
                    r = requests.post(resourceURI, timeout=2)
                else:
                    r = requests.post(resourceURI, data=payload, timeout=2)
                if r.headers['Content-Type'] == 'application/json':
                    data = r.json()
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

            getThread.NodeResponses.append(response)
            q.release()
            # print "%s response %s" % (resourceURI, data)
            app.logger.info('[%s] : [INFO] %s response %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), resourceURI, data)
        else:
            q.release()
        time.sleep(1)


class DmonRequest:

    def __init__(self, resourceList):
        self.resourceList = resourceList
        self.outputDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

    def getRequests(self):
        queueLock = threading.Lock()
        workQueue = Queue.Queue(len(self.resourceList))
        threads = []
        threadID = 1
        getThread.exitFlag = 0

        # Max number of threads set to 10
        threadList = []
        if len(self.resourceList) < 10:
            tIter = len(self.resourceList)
        else:
            tIter = 10

        for x in range(0, tIter):
            tStr = "Thread-%s" % x
            x += 1
            threadList.append(tStr)

        print threadList
        app.logger.info('[%s] : [INFO] Thread List %s',
                               datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(threadList))
        # Fill the queue
        queueLock.acquire()
        for word in self.resourceList:
            app.logger.info('[%s] : [INFO] Word %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), word)
            print word
            workQueue.put(word)
        queueLock.release()

        # Create new threads
        for tName in threadList:
            thread = getThread(threadID, tName, workQueue, queueLock)
            thread.start()
            threads.append(thread)
            threadID += 1

        # Wait for queue to empty
        while not workQueue.empty():
            pass

        # Notify threads it's time to exit
        getThread.exitFlag = 1

        # Wait for all threads to complete
        for t in threads:
            t.join()

        response = getThread.NodeResponses
        getThread.NodeResponses = []
        return response

    def getRequestFiles(self):
        queueLock = threading.Lock()
        workQueue = Queue.Queue(len(self.resourceList))
        threads = []
        threadID = 1
        getThread.exitFlag = 0

        # Max number of threads set to 10
        threadList = []
        if len(self.resourceList) < 10:
            tIter = len(self.resourceList)
        else:
            tIter = 10

        for x in range(0, tIter):
            tStr = "Thread-%s" % x
            x += 1
            threadList.append(tStr)

        print threadList
        app.logger.info('[%s] : [INFO] Thread List %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(threadList))
        # Fill the queue
        queueLock.acquire()
        for word in self.resourceList:
            app.logger.info('[%s] : [INFO] Word %s',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), word)
            print word
            workQueue.put(word)
        queueLock.release()

        # Create new threads
        for tName in threadList:
            thread = getFileThread(threadID, tName, workQueue, queueLock, self.outputDir)
            thread.start()
            threads.append(thread)
            threadID += 1

        # Wait for queue to empty
        while not workQueue.empty():
            pass

        # Notify threads it's time to exit
        getThread.exitFlag = 1

        # Wait for all threads to complete
        for t in threads:
            t.join()

        response = getThread.NodeResponses
        getThread.NodeResponses = []
        return response


def getStormLogs(resourceList):
    bworker = DmonRequest(resourceList)
    rsp = bworker.getRequestFiles()
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
    #getStormLogs(resourceList)
    test2 = DmonRequest(resourceList)
    testText = test2.getRequestFiles()
    print testText


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
    #clean up
    for el in lFile:
        os.remove(el)



