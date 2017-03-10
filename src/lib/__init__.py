'''
Copyright 2014, Institute e-Austria, Timisoara, Romania
    http://www.ieat.ro/
Developers:
 * Silviu Panica, silviu.panica@e-uvt.ro
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

import os, json


class Config(object):
    apiVersion = '/v1'


class Artifact(object):
    def checkRepository(self, arPath, repository):
        _c, _m = Functions().isRepository(os.path.join(arPath, repository))
        if _c == 1:
            return _c, _m
        else:
            return 0, ""

    def checkArtifact(self, arPath, repository, artifact):
        _c, _m = self.checkRepository(arPath, repository)
        if _c == 1:
            return _c, _m
        else:
            return Functions().isArtifact(os.path.join(arPath, repository, artifact))

    def checkArtifactVersion(self, arPath, repository, artifact, version):
        _c, _m = self.checkArtifact(arPath, repository, artifact)
        if _c == 1:
            return _c, _m
        else:
            return Functions().isArtifactVersion(os.path.join(arPath, repository, artifact), version)

    def checkArtifactVersionFile(self, arPath, repository, artifact, version, ufile):
        _c, _m = self.checkArtifactVersion(arPath, repository, artifact, version)
        if _c == 1:
            return _c, _m
        else:
            return Functions().isArtifactVersionFile(os.path.join(arPath, repository, artifact, version), ufile)


class Functions(object):
    def getReturnMessage(self, code, message, data):
        _retMessage = {}
        _retMessage['code'] = code
        _retMessage['message'] = message
        _retMessage['data'] = data
        return _retMessage

    def isRepository(self, repoPath):
        if not os.path.isdir(repoPath):
            return 1, self.getReturnMessage(1, "The requested repository doesn't exist", "")
        else:
            return 0, ""

    def isArtifact(self, artiPath):
        if not os.path.isdir(artiPath):
            return 1, self.getReturnMessage(1, "The requested artifact doesn't exist", "")
        else:
            return 0, ""

    def isArtifactVersion(self, artiPath, version):
        if not os.path.isdir(os.path.join(artiPath, version)):
            return 1, self.getReturnMessage(1, "The requested artifact version doesn't exist", "")
        else:
            return 0, ""

    def isArtifactVersionFile(self, artiVersPath, ufile):
        if not os.path.exists(os.path.join(artiVersPath, ufile)):
            return 1, self.getReturnMessage(1, "The requested file doesn't exist in artifact version", "")
        else:
            return 0, ""
