from pyDMON import db
from datetime import datetime

#%--------------------------------------------------------------------%
class dbNodes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nodeFQDN = db.Column(db.String(64), index=True, unique=True)
    nodeIP = db.Column(db.String(64), index=True, unique=True)
    nodeUUID = db.Column(db.String(64), index=True, unique=True)
    nodeOS = db.Column(db.String(120), index=True, unique=False)
    nUser = db.Column(db.String(64), index=True, unique=False)
    nPass = db.Column(db.String(64), index=True, unique=False)
    nkey = db.Column(db.String(120), index=True, unique=False)
    nRoles = db.Column(db.String(120), index=True, unique=False, default='unknown') #hadoop roles running on server
    nStatus = db.Column(db.Boolean,index=True, unique=False, default='1')
    nMonitored = db.Column(db.Boolean,index=True, unique=False, default='0')
    nCollectdState = db.Column(db.String(64), index=True, unique=False,default='None') #Running, Pending, Stopped, None
    nLogstashForwState = db.Column(db.String(64), index=True, unique=False,default='None') #Running, Pending, Stopped, None
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    #ES = db.relationship('ESCore', backref='nodeFQDN', lazy='dynamic')

    #TODO: Create init function/method to populate db.Model

    def __repr__(self):
        return '<dbNodes %r>' % (self.nickname)


class dbESCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    nodeName = db.Column(db.String(64), index=True, unique=True)
    nodePort = db.Column(db.Integer, index=True, unique=False,default = 9200)
    clusterName = db.Column(db.String(64), index=True, unique=False)
    conf = db.Column(db.LargeBinary, index=True, unique=False)
    ESCoreStatus = db.Column(db.String(64), index=True, default='unknown', unique=False)#Running, Pending, Stopped, unknown
    ESCorePID = db.Column(db.Integer, index=True, default = 0, unique=False) # pid of current running process
    MasterNode = db.Column(db.Boolean,index=True, unique=False) # which node is master
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbESCore %r>' % (self.body)

class dbSCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    inLumberPort = db.Column(db.Integer, index=True, unique=False,default = 5000)
    sslCert = db.Column(db.String(120), index=True, unique=False)
    sslKey = db.Column(db.String(120), index=True, unique=False)
    udpPort = db.Column(db.Integer, index=True, unique=False,default = 25826) #collectd port same as collectd conf
    outESclusterName = db.Column(db.String(64), index=True, unique=False )# same as ESCore clusterName
    outKafka = db.Column(db.String(64), index=True, unique=False) # output kafka details
    outKafkaPort = db.Column(db.Integer, index=True, unique=False)
    conf = db.Column(db.String(140), index=True, unique=False)
    LSCoreStatus = db.Column(db.String(64), index=True, unique=False)#Running, Pending, Stopped, None
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbLSCore %r>' % (self.body)

class dbKBCore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostFQDN = db.Column(db.String(64), index=True, unique=True)
    hostIP = db.Column(db.String(64), index=True, unique=True)
    hostOS = db.Column(db.String(120), index=True, unique=False)
    kbPort = db.Column(db.Integer, index=True, unique=False,default = 5601)
    conf = db.Column(db.String(140), index=True, unique=False)
    KBCoreStatus = db.Column(db.String(64), index=True, unique=False)#Running, Pending, Stopped, None
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<dbKBCore %r>' % (self.body)

#Not Used Yet
class dbApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appName = db.Column(db.String(64), index=True, unique=False)
    appVersion = db.Column(db.String(64), index=True, unique=False)
    jobID = db.Column(db.String(64), index=True, unique=True)
    startTime = db.Column(db.String(64), index=True, unique=False)
    stopTime = db.Column(db.String(64), index=True, unique=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self):
        return '<dbApp %r>' % (self.body)

class dbCDHMng(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cdhMng =  db.Column(db.String(64), index=True, unique=True)
    cdhMngPort = db.Column(db.Integer, index=True, unique=False,default = 7180)
    cpass = db.Column(db.String(64), index=True, default = 'admin',unique=False)
    cuser = db.Column(db.String(64), index=True, default = 'admin',unique=False)
    
    def __repr__(self):
        return '<dbCDHMng %r>' % (self.body)



#%--------------------------------------------------------------------%