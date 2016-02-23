from flask import Flask
from flask.ext.restplus import Api

app = Flask("dmon-agent")
api = Api(app, version='0.0.4', title='DICE Monitoring Agent API',
          description="RESTful API for the DICE Monitoring Platform  Agent (dmon-agent)",
          )


# changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
agent = api.namespace('agent', description='dmon agent operations')