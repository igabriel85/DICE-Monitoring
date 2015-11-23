import threading
import Queue
import time
import requests


class getThread(threading.Thread):
    def __init__(self, threadID, resource, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.resource = resource
        self.q = q

    def run(self):
        print "Starting thread " + str(self.threadID)
        tRequest(self.resource, self.q)
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


def tRequest(resource, q):
    response = {}
    statusCode = {}
    data = {}
    while not exitFlag:
        queueLock.acquire()
        if not workQueue.empty():
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

            NodeResponses.append(response)
            queueLock.release()
            print "%s response %s" % (resourceURI, data)
        else:
            queueLock.release()
        time.sleep(1)


def tRequestPost(resource, q, payload=None):
    response = {}
    statusCode = {}
    data = {}
    while not exitFlag:
        queueLock.acquire()
        if not workQueue.empty():
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

            NodeResponses.append(response)
            queueLock.release()
            print "%s response %s" % (resourceURI, data)
        else:
            queueLock.release()
        time.sleep(1)

if __name__ == '__main__':
    resourceList = ['http://127.0.1.1:5000/agent/v1/node', 'http://127.0.0.1:5000/agent/v1/node']

    queueLock = threading.Lock()
    workQueue = Queue.Queue(len(resourceList))

    threads = []
    threadID = 1
    exitFlag = 0

    # List containing Responses
    NodeResponses = []

    # Max number of threads set to 10
    threadList = []
    if len(resourceList) < 10:
        tIter = len(resourceList)
    else:
        tIter = 10

    for x in range(0, tIter):
        tStr = "Thread-%s" % x
        x += 1
        threadList.append(tStr)

    print threadList
    # Create new threads
    for tName in threadList:
        thread = getThread(threadID, tName, workQueue)
        thread.start()
        threads.append(thread)
        threadID += 1

    # Fill the queue
    queueLock.acquire()
    for word in resourceList:
        workQueue.put(word)
    queueLock.release()

    # Wait for queue to empty
    while not workQueue.empty():
        pass

    # Notify threads it's time to exit
    exitFlag = 1

    # Wait for all threads to complete
    for t in threads:
        t.join()

    print NodeResponses
    print "Exiting Main Thread"
