"""

Copyright 2017, Institute e-Austria, Timisoara, Romania
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
from app import *
from flask.ext.restplus import Resource
import lib
import os


repoDefault = outDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'repository')
repoPath = os.getenv('DMON_REPO', repoDefault)

arApiPath = lib.Config().apiVersion
lf = lib.Functions()
la = lib.Artifact()


@dmon.route('/v1/overlord/repositories')
class DICEArtifactRepositories(Resource):
    def get(self):
        _ret = {}
        _ret['apiVersion'] = arApiPath
        _ret['documenation'] = 'https://github.com/dice-project/DICE-Monitoring/wiki'
        return jsonify(lf.getReturnMessage(0, "DICE Artifact Repository", _ret))


@dmon.route('/v1/overlord/repositories/<repository>/artifacts')
class DICEArtifactRepositoryArtifacts(Resource):
    def get(self, repository):
        _c, _m = la.checkRepository(repoPath, repository)
        if _c == 1:
            _m['data'] = repository
            return jsonify(_m)
        _repoPath = os.path.join(repoPath, repository)
        _artiList = os.listdir(_repoPath)
        return jsonify(lf.getReturnMessage(0, "The list of artifacts in repository: " + repository, _artiList))


@dmon.route('/v1/overlord/repositories/<repository>/artifacts/<artifact>')
class DICEArtifactRepositoryArtifact(Resource):
    def get(self, repository, artifact):
        _rd = repository + "/" + artifact
        _c, _m = la.checkArtifact(repoPath, repository, artifact)
        if _c == 1:
            _m['data'] = _rd
            return jsonify(_m)
        _artiPath = os.path.join(repoPath, repository, artifact)
        _artiVersList = os.listdir(_artiPath)
        return jsonify(lf.getReturnMessage(0, "The list of available versions of artifact: " + artifact, _artiVersList))

    def delete(self, repository, artifact):
        _rd = repository + "/" + artifact
        _c, _m = la.checkArtifact(repoPath, repository, artifact)
        if _c == 1:
            return jsonify(_m)
        try:
            shutil.rmtree(os.path.join(repoPath, repository, artifact))
        except:
            return jsonify(lf.getReturnMessage(1, "An error occured when tried to delete artifact", _rd))
        return jsonify(lf.getReturnMessage(0, "Artifact removed with all its content", _rd))


@dmon.route('/v1/overlord/repositories/<repository>/artifacts/<artifact>/<version>/files')
class DICEArtifactRepositoryArtifactFiles(Resource):
    def get(self, repository, artifact, version):
        _rd = repository + "/" + artifact + "/" + version
        _c, _m = la.checkArtifactVersion(repoPath, repository, artifact, version)
        if _c == 1:
            _m['data'] = _rd
            return jsonify(_m)
        _artiVerPath = os.path.join(repoPath, repository, artifact, version)
        _artiVerFilesList = os.listdir(_artiVerPath)
        return jsonify(
            lf.getReturnMessage(0, "The list of available files of artifact version: " + artifact + "/" + version,
                                _artiVerFilesList))


@dmon.route('/v1/overlord/repositories/<repository>/artifacts/<artifact>/<version>')
class DICEArtifactRepositoryArtifactVersion(Resource):
    def put(self, repository, artifact, version):
        _rd = repository + "/" + artifact + "/" + version
        _c, _m = la.checkArtifact(repoPath, repository, artifact)
        if _c == 1:
            try:
                os.makedirs(os.path.join(repoPath, repository, artifact, version))
            except:
                return jsonify(lf.getReturnMessage(1, "Error creating artifact directory", repository + "/" + artifact))
        else:
            _c, _m = la.checkArtifactVersion(repoPath, repository, artifact, version)
            if _c == 0:
                return jsonify(lf.getReturnMessage(1, "The requested artifact version already exists", _rd))
            else:
                try:
                    os.makedirs(os.path.join(repoPath, repository, artifact, version))
                except:
                    return jsonify(lf.getReturnMessage(1, "Error creating artifact version directory", _rd))
        return jsonify(lf.getReturnMessage(0, "Artifact version created successfully", _rd))

    def delete(self, repository, artifact, version):
        _rd = repository + "/" + artifact + "/" + version
        _c, _m = la.checkArtifactVersion(repoPath, repository, artifact, version)
        if _c == 1:
            return jsonify(_m)
        try:
            shutil.rmtree(os.path.join(repoPath, repository, artifact, version))
        except:
            return jsonify(lf.getReturnMessage(1, "An error occured when tried to delete artifact version", _rd))
        return jsonify(lf.getReturnMessage(0, "Artifact version removed with all its content", _rd))


@dmon.route('/v1/overlord/repositories/<repository>/artifacts/<artifact>/<version>/files/<file>')
class DICEArtifactRepositoryArtifactVersionFile(Resource):
    def get(self, repository, artifact, version):
        _rd = repository + "/" + artifact + "/" + version + "/" + file
        _c, _m = la.checkArtifactVersion(repoPath, repository, artifact, version)
        if _c == 1:
            return jsonify(_m)
        _c, _m = lf.isArtifactVersionFile(os.path.join(repoPath, repository, artifact, version), file)
        if _c == 0:
            return send_from_directory(os.path.join(repoPath, repository, artifact, version), file)
        return "stuff"

    def put(self, repository, artifact, version):
        _rd = repository + "/" + artifact + "/" + version + "/" + file
        _c, _m = la.checkArtifactVersion(repoPath, repository, artifact, version)
        if _c == 1:
            return jsonify(_m)
        _c, _m = lf.isArtifactVersionFile(os.path.join(repoPath, repository, artifact, version), file)
        _fileContent = request.get_data()
        try:
            _fp = open(os.path.join(repoPath, repository, artifact, version, file), "w")
            _fp.write(_fileContent)
            _fp.close()
        except:
            return jsonify(lf.getReturnMessage(1, "An error occurred when tried to save the file.", "PUT: " + _rd))
        return jsonify(lf.getReturnMessage(0, "File " + file + " has been upload successfully.", _rd))

    def delete(self, repository, artifact, version):
        _rd = repository + "/" + artifact + "/" + version + "/" + file
        _c, _m = la.checkArtifactVersionFile(repoPath, repository, artifact, version, file)
        if _c == 1:
            return jsonify(_m)
        try:
            os.remove(os.path.join(repoPath, repository, artifact, version, file))
        except:
            jsonify(lf.getReturnMessage(1, "An error occured when tried to delete the file from artifact version", _rd))
        return jsonify(lf.getReturnMessage(0, "File removed from artifact version", _rd))

