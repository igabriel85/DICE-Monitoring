from flask import Flask
from flask.ext.restplus import Api

app = Flask("dmon-elasticsearch")
api = Api(app, version='0.0.1', title='DICE Monitoring Elasticsearch API',
          description="RESTful API for the DICE Monitoring Platform  Elasticsearch agent (dmon-elasticsearch)",
          )

# changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
agent = api.namespace('agent', description='dmon elasticsearch operations')