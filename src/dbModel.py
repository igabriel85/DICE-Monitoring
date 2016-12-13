from datetime import datetime
from app import *
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)


class dbNodes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nodeFQDN = db.Column(db.String(64), index=True, unique=True)
    nodeIP = db.Column(db.String(64), index=True, unique=True)
    nodeUUID = db.Column(db.String(64), index=True, unique=True)
    nodeOS = db.Column(db.String(120), index=True, unique=False)
    nUser = db.Column(db.String(64), index=True, unique=False)
    nPass = db.Column(db.String(64), index=True, unique=False)
    nkey = db.Column(db.String(120), index=True, unique=False)
    nRoles = db.Column(db.String(120), index=True, unique=False, default='unknown')  # hadoop roles running on server
    nStatus = db.Column(db.Boolean, index=True, unique=False, default='0')
    nMonitored = db.Column(db.Boolean, index=True, unique=False, default='0')
    nCollectdState = db.Column(db.String(64), index=True, unique=False,
                               default='None')  # Running, Pending, Stopped, None
    nLogstashForwState = db.Column(db.String(64), index=True, unique=False,
                                   default='None')  # Running, Pending, Stopped, None
    nLogstashInstance = db.Column(db.String(64), index=True, unique=False, default='None')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # ES = db.relationship('ESCore', backref='nodeFQDN', lazy='dynamic')

    # TODO: Create init function/method to populate db.Model

    def __repr__(self):
        return '<dbNodes %r>' % (self.nodeFQDN)


class dbESCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    nodeName = db.Column(db.String(64), index=True, unique=True)
    nodePort = db.Column(db.Integer, index=True, unique=False, default=9200)
    clusterName = db.Column(db.String(64), index=True, unique=False)
    conf = db.Column(db.LargeBinary, index=True, unique=False)
    ESCoreStatus = db.Column(db.String(64), index=True, default='unknown', unique=False)  # Running, Pending, Stopped, unknown
    ESCorePID = db.Column(db.Integer, index=True, default=0, unique=False)  # pid of current running process
    ESCoreHeap = db.Column(db.String(64), index=True, unique=False, default='4g')
    MasterNode = db.Column(db.Boolean, index=True, unique=False, default=True)  # which node is master
    DataNode = db.Column(db.Boolean, index=True, unique=False, default=True)
    NumOfShards = db.Column(db.Integer, index=True, default=5, unique=False)
    NumOfReplicas = db.Column(db.Integer, index=True, default=1, unique=False)
    FieldDataCacheSize = db.Column(db.String(64), index=True, unique=False, default='20%')
    FieldDataCacheExpires = db.Column(db.String(64), index=True, unique=False, default='6h')
    FieldDataCacheFilterSize = db.Column(db.String(64), index=True, unique=False, default='20%')
    FieldDataCacheFilterExpires = db.Column(db.String(64), index=True, unique=False, default='6h')
    IndexBufferSize = db.Column(db.String(64), index=True, unique=False, default='30%')
    MinShardIndexBufferSize = db.Column(db.String(64), index=True, unique=False, default='12mb')
    MinIndexBufferSize = db.Column(db.String(64), index=True, unique=False, default='96mb')
    ESCoreDebug = db.Column(db.String(64), index=True, unique=False, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbESCore %r>' % (self.hostFQDN)


class dbSCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    inLumberPort = db.Column(db.Integer, index=True, unique=False, default=5000)
    sslCert = db.Column(db.String(120), index=True, unique=False, default='default')
    sslKey = db.Column(db.String(120), index=True, unique=False, default='default')
    udpPort = db.Column(db.Integer, index=True, unique=False, default=25826)  # collectd port same as collectd conf
    outESclusterName = db.Column(db.String(64), index=True, unique=False)  # same as ESCore clusterName
    outKafka = db.Column(db.String(64), index=True, unique=False, default='unknown')  # output kafka details
    outKafkaPort = db.Column(db.Integer, index=True, unique=False, default='unknown')
    conf = db.Column(db.String(140), index=True, unique=False)
    LSCoreHeap = db.Column(db.String(120), index=True, unique=False, default='512m')
    LSCoreWorkers = db.Column(db.String(120), index=True, unique=False, default='4')
    LSCoreStatus = db.Column(db.String(64), index=True, unique=False,
                             default='unknown')  # Running, Pending, Stopped, None
    LSCorePID = db.Column(db.Integer, index=True, unique=False, default=0)
    LSCoreStormEndpoint = db.Column(db.String(64), index=True, unique=False, default='None')
    LSCoreStormPort = db.Column(db.String(64), index=True, unique=False, default='None')
    LSCoreStormTopology = db.Column(db.String(64), index=True, unique=False, default='None')
    LSCoreSparkEndpoint = db.Column(db.String(64), index=True, unique=False, default='None')
    LSCoreSparkPort = db.Column(db.String(64), index=True, unique=False, default='None')
    diceIndex = db.Column(db.String(64), index=True, unique=False, default='logstash')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbLSCore %r>' % (self.hostFQDN)


class dbKBCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    kbPort = db.Column(db.Integer, index=True, unique=False, default=5601)
    KBCorePID = db.Column(db.Integer, index=True, default=0, unique=False)  # pid of current running process
    conf = db.Column(db.String(140), index=True, unique=False)
    KBCoreStatus = db.Column(db.String(64), index=True, default='unknown',
                             unique=False)  # Running, Pending, Stopped, None
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbKBCore %r>' % (self.hostFQDN)


# Not Used Yet
class dbApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appName = db.Column(db.String(64), index=True, unique=False)
    appVersion = db.Column(db.String(64), index=True, unique=False)
    jobID = db.Column(db.String(64), index=True, unique=False)
    startTime = db.Column(db.String(64), index=True, unique=False)
    loggingPeriod = db.Column(db.Integer, index=True, unique=False)
    stopTime = db.Column(db.String(64), index=True, unique=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<dbApp %r>' % (self.appName)


class dbCDHMng(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cdhMng = db.Column(db.String(64), index=True, unique=True)
    cdhMngPort = db.Column(db.Integer, index=True, unique=False, default=7180)
    cpass = db.Column(db.String(64), index=True, default='admin', unique=False)
    cuser = db.Column(db.String(64), index=True, default='admin', unique=False)

    def __repr__(self):
        return '<dbCDHMng %r>' % (self.cdhMng)

class dbBDService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    yarnHPort = db.Column(db.Integer, index=True, unique=False, default=19888)
    yarnHEnd = db.Column(db.String(64), index=True, unique=False, default='None')
    yarnHPoll = db.Column(db.Integer, index=True, unique=False, default=30)
    sparkHPort = db.Column(db.Integer, index=True, unique=False, default=18088) #TODO: Change to corect default
    sparkHEnd = db.Column(db.String(64), index=True, unique=False, default='None')
    sparkHPoll = db.Column(db.Integer, index=True, unique=False, default=30)
    mongoHost = db.Column(db.String(64), index=True, unique=False, default='127.0.0.1')
    mongoPort = db.Column(db.String(64), index=True, unique=False, default='27017')
    mongoUser = db.Column(db.String(64), index=True, unique=False, default='')
    mongoPswd = db.Column(db.String(64), index=True, unique=False, default='password')
    mongoDBs = db.Column(db.String(64), index=True, unique=False, default='admin')

    def __repr__(self):
        return '<dbBDService %r>' % (self.dbDBService)


class dbMetPer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sysMet = db.Column(db.String(64), index=True, unique=False, default="15")
    yarnMet = db.Column(db.String(64), index=True, unique=False, default="15")
    sparkMet = db.Column(db.String(64), index=True, unique=False, default="5")
    stormMet = db.Column(db.String(64), index=True, unique=False, default="60")

    def __repr__(self):
        return '<dbMetPer %r>' % (self.dbMetPer)
# %--------------------------------------------------------------------%

