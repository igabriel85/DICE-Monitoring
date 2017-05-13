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
from pyESController import *
import json
from dmonPerfMon import jsonToPerfMon


def asyncQuery(request, query, myIndex, ftype, fileName):
    fileLoc = os.path.join(outDir, fileName)
    if 'metrics' not in request.json['DMON'] or request.json['DMON']['metrics'] == " ":
        start = time.time()
        try:
            ListMetrics, resJson = queryESCore(query, debug=False, myIndex=myIndex)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Cannot connect to ES instance with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            sys.exit(1)
        if not ListMetrics:
            app.logger.info('[%s] : [INFO] No results found',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            sys.exit(2)
        if ftype == 'csv':
            dict2CSV(ListMetrics, fileLoc)
            app.logger.info('[%s] : [INFO] Exported query %s to csv',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fileName.split('.')[0])
        if ftype == 'json':
            with open(fileLoc, 'w') as outfile:
                json.dump(resJson, outfile)
            app.logger.info('[%s] : [INFO] Exported query %s to JSON',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fileName.split('.')[0])
        if ftype == 'plain':
            with open(fileLoc, 'w') as outfile:
                json.dump(ListMetrics, outfile)
            app.logger.info('[%s] : [INFO] Exported query %s to Plain',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fileName.split('.')[0])
        if ftype == 'oslc':
            resOSLC = jsonToPerfMon(resJson)
            with open(fileLoc, 'w') as outfile:
                json.dump(resOSLC, outfile)
            app.logger.info('[%s] : [INFO] Exported query %s to OSLC',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fileName.split('.')[0])
        end = time.time() - start
        app.logger.info('[%s] : [INFO] Exiting Query %s, time %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fileName.split('.')[0], str(end))
        sys.exit(0)
    else:
        metrics = request.json['DMON']['metrics']
        app.logger.info('[%s] : [INFO] Metrics filter set to %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), str(metrics))
        try:
            ListMetrics, resJson = queryESCore(query, allm=False, dMetrics=metrics, debug=False, myIndex=myIndex)
        except Exception as inst:
            app.logger.error('[%s] : [ERROR] Cannot connect to ES instance with %s and %s',
                             datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), type(inst), inst.args)
            sys.exit(1)
        if not ListMetrics:
            app.logger.info('[%s] : [INFO] No results found',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            sys.exit(2)
        if ftype == 'csv':
            dict2CSV(ListMetrics, fileLoc)
            app.logger.info('[%s] : [INFO] Exported query %s to CSV',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fileName.split('.')[0])
        if ftype == 'json':
            with open(fileLoc, 'w') as outfile:
                json.dump(ListMetrics, outfile)
            app.logger.info('[%s] : [INFO] Exported query %s to JSON',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fileName.split('.')[0])
        if ftype == 'plain':
            with open(fileLoc, 'w') as outfile:
                json.dump(ListMetrics, outfile)
            app.logger.info('[%s] : [INFO] Exported query %s to Plain',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fileName.split('.')[0])
        if ftype == 'oslc':
            resOSLC = jsonToPerfMon(resJson)
            with open(fileLoc, 'w') as outfile:
                json.dump(resOSLC, outfile)
            app.logger.info('[%s] : [INFO] Exported query %s to OSLC',
                            datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fileName.split('.')[0])

        app.logger.info('[%s] : [INFO] Exiting Query %s',
                        datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), fileName.split('.')[0])
        sys.exit(0)