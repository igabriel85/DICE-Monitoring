from flask import Flask
from flask.ext.restplus import Api


app = Flask("dmon-logstash")
app.config['RESTPLUS_VALIDATE'] = True
api = Api(app, version='0.0.2', title='DICE Monitoring Logstash API',
          description="RESTful API for the DICE Monitoring Platform  Logstash agent (dmon-logstash)",
          )

# changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
agent = api.namespace('agent', description='dmon logstash operations')