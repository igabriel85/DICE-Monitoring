import os

class ESAgentController():
    '''
        Controlls local deployment of elasticsearch
    '''

    def __init__(self, esLoc, tempLoc, pidLoc, logLoc, configLoc):
        self.esLoc = esLoc
        self.tempLoc = tempLoc
        self.pidLoc = pidLoc
        self.logLoc = logLoc
        self.configLoc = configLoc

    def generateConfig(self, state):
        return 'Something'

    def start(self):
        return 'Something'

    def stop(self):
        return 'Something'

    def execCmd(self, cmd):
        return 'Execute Something'

    def addTemplate(self):
        return "New Template addition"

    def generateJSONSchema(self, jsonTemplate):
        return "JSON Schema"

    def checkInput(self):
        return "Check Input"


def checkPID(pid):
    '''
    :param pid: pid to check
    :return: return 1 if pid found 0 if not
    '''
    if pid == 0:
        return 0
    try:
        os.kill(pid, 0)
    except OSError:
        return 0
    else:
        return 1