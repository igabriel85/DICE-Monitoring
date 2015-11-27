import threading
import Queue
import time
import requests
from flask import copy_current_request_context


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
        print "Starting thread " + str(self.threadID)
        tRequest(self.resource, self.q, self.lock)
        print "Exiting thread " + str(self.threadID)


class postThread(threading.Thread):
    def __init__(self, threadID, resource, q, payload):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.resource = resource
        self.q = q
        self.payload = payload

    def run(self):
        print "Starting thread  " + str(self.threadID)
        tRequestPost(self.resource, self.q, self.payload)
        print "Exiting thread " + str(self.threadID)


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
            print "%s response %s" % (resourceURI, data)
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
            print "%s response %s" % (resourceURI, data)
        else:
            q.release()
        time.sleep(1)


class DmonRequest():

    def __init__(self, resourceList):
        self.resourceList = resourceList

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
        # Fill the queue
        queueLock.acquire()
        for word in self.resourceList:
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





if __name__ == '__main__':
   # resourceList = ['http://109.231.121.135:5000/agent/v1/check', 'http://109.231.121.135:5000/agent/v1/check', 'http://109.231.121.135:5000/agent/v1/check' ]
    #testLits = ['http://19.231.121.135:5000/agent/v1/check', 'http://19.231.121.135:5000/agent/v1/check', 'http://19.231.121.135:5000/agent/v1/check' ]
    resourceList = ['http://109.231.121.135:5000/agent/v1/check', 'http://109.231.121.194:5000/agent/v1/check', 'http://109.231.121.134:5000/agent/v1/check']

    #test1 = DmonRequest(testLits)
    test2 = DmonRequest(resourceList)

    testText = test2.getRequests()
    print testText

   # testtext2 = test1.getRequests()
   # print testtext2
    #test = dmonRequestGet(resourceList)
    #print test

    # queueLock = threading.Lock()
    # workQueue = Queue.Queue(len(resourceList))
    #
    # threads = []
    # threadID = 1
    # exitFlag = 0
    #
    # # List containing Responses
    # NodeResponses = []
    #
    # # Max number of threads set to 10
    # threadList = []
    # if len(resourceList) < 10:
    #     tIter = len(resourceList)
    # else:
    #     tIter = 10
    #
    # for x in range(0, tIter):
    #     tStr = "Thread-%s" % x
    #     x += 1
    #     threadList.append(tStr)
    #
    # print threadList
    # # Create new threads
    # for tName in threadList:
    #     thread = getThread(threadID, tName, workQueue, queueLock)
    #     thread.start()
    #     threads.append(thread)
    #     threadID += 1
    #
    # # Fill the queue
    # queueLock.acquire()
    # for word in resourceList:
    #     workQueue.put(word)
    # queueLock.release()
    #
    # # Wait for queue to empty
    # while not workQueue.empty():
    #     pass
    #
    # # Notify threads it's time to exit
    # exitFlag = 1
    #
    # # Wait for all threads to complete
    # for t in threads:
    #     t.join()
    #
    # print NodeResponses
    # print "Exiting Main Thread"
