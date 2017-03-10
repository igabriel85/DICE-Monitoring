from flask import Flask, jsonify, request
from flask.ext.restplus import Api, Resource, fields
from flask import send_from_directory
import shutil


app = Flask("D-MON")
api = Api(app, version='0.2.4', title='DICE MONitoring API',
    description='RESTful API for the DICE Monitoring Platform  (D-MON)',
)

backProc = None

#changes the descriptor on the Swagger WUI and appends to api /dmon and then /v1
dmon = api.namespace('dmon', description='D-MON operations')