import threading
import Queue
import time
import requests


class getThread (threading.Thread):
    def __init__(self, threadID, resource, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.resource = resource
        self.q = q
    def run(self):
        print "Starting thread " + str(self.threadID)
        tRequest(self. resource, self.q)
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
        tRequestPost(self. resource, self.q, self.payload)
        print "Exiting thread " + str(self.threadID)


def tRequest(resource,  q):
    response ={}
    statusCode = {}
    data = {}
    while not exitFlag:
        queueLock.acquire()
        if not workQueue.empty():
            resourceURI = q.get()
            try:
                r = requests.get(resourceURI, timeout=2)
                data = r.json()
                response['Node']= resourceURI
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


def tRequestPost(resource, q, payload):
    response ={}
    statusCode = {}
    while not exitFlag:
        queueLock.acquire()
        if not workQueue.empty():
            data = q.get()
            r = requests.post(resource, data=payload, timeout=2)
            statusCode[resource] = r.status_code
            queueLock.release()
            print "%s response %s" % (data, r.json()['Node'])
        else:
            queueLock.release()
        time.sleep(1)


# class ParallelRequest():  # TODO: finish parallel request class
#     #exitFlag = 0
#     #threadID = 1
#     #threads = []
#     #queueLock = threading.Lock()
#
#
#     def __init__(self, threadCount, queueSize, threadID):
#         self.threadCount = threadCount
#         self.queueSize = queueSize
#         self.threadID = threadID
#
#     def executeGet(self, nodeList, resource):
#         for node in nodeList:
#             workQueue = Queue.Queue(self.queueSize)
#             thread = getThread(self.threadID, node, resource, workQueue)
#             thread.start()
#             threads.append(thread)
#             self.threadID += 1
#
#         #Fill the queue
#         queueLock.acquire()
#         for node in nodeList:
#             workQueue.put(node)
#         queueLock.release()
#
#         # Wait for queue to empty
#         while not workQueue.empty():
#             pass
#
#         # Notify threads it's time to exit
#         exitFlag = 1
#
#         # Wait for all threads to complete
#         for t in threads:
#             t.join()
#         print "Exiting Main Thread"
#         return 'get'
#
#     def executePut(self, nodeList, resource, content):
#         return 'put'
#
#     def executePost(self, nodeList, resource, content):
#         return 'post'
#
#     def executeDelete(self, nodeList, resource):
#         return 'delete'



# nodel = [1,2,3,4,5,6,8,7]
# resourceURI = 'http://127.0.0.1:5000/agent/v1/node'
# test = ParallelRequest(4,11)
#
#test.executeGet(nodel, resourceURI)


resourceList = ['http://127.0.1.1:5000/agent/v1/node', 'http://127.0.0.1:5000/agent/v1/node']


queueLock = threading.Lock()
workQueue = Queue.Queue(len(resourceList))



threads = []
threadID = 1
exitFlag = 0

# List containing Responses
NodeResponses = []

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