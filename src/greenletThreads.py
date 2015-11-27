import gevent
import gevent.queue
import requests


class GreenletRequests():
    NodeResponsesGet = []
    NodeResponsesPost = []
    ng = 0
    np = 0

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

        print str(gList)
        gevent.joinall(gList)

        return GreenletRequests.NodeResponsesGet

    def parallelPost(self, payload):
        queue = gevent.queue.Queue()
        for i in self.resourceList:
            queue.put(i)

        gList = []
        for t in range(len(self.resourceList)):
            gl = gevent.spawn(postRequest, queue, payload)
            gList.append(gl)

        print str(gList)
        gevent.joinall(gList)

        return GreenletRequests.NodeResponsesPost

    def resetGet(self):
        GreenletRequests.NodeResponsesGet = []



def randomT(queue, name):
    while not queue.empty():
        t = queue.get(timeout = 1)
        gevent.sleep(5)
        print 'I am + '+name+ ' executing ' + str(GreenletRequests.ng)
        GreenletRequests.ng+=1
        gevent.sleep(0)


def getRequest(queue):
    response = {}
    statusCode = {}
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
            statusCode['StatusCode'] = 408
            response['Data'] = 'n/a'
        except requests.exceptions.ConnectionError:
            response['Node'] = resURI
            statusCode['StatusCode'] = 404
            response['Data'] = 'n/a'

        GreenletRequests.NodeResponsesGet.append(response)
        print 'Threaded GET with ID '+str(GreenletRequests.ng)+ ' executed for ' + resURI
        GreenletRequests.ng+=1
        gevent.sleep(0)


def postRequest(queue, payload=None):
    response = {}
    statusCode = {}
    data = {}
    while not queue.empty:
        resourceURI = queue.get(timeout=1)
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

        GreenletRequests.NodeResponsesPost.append(response)
        print 'Threaded POST with ID '+str(GreenletRequests.np)+ ' executed for ' + resourceURI
        GreenletRequests.np+=1
        gevent.sleep(0)

# resourceList = ['http://109.231.121.135:5000/agent/v1/check', 'http://109.231.121.194:5000/agent/v1/check']
# test = GreenletRequests(resourceList)
#
# testG = test.parallelGet()
# testP = test.parallelPost(None)
#
# print testG
# print testP



