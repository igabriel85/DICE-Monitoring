'''

Copyright 2015, Institute e-Austria, Timisoara, Romania
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
'''



#!flask/bin/python
from flask import Flask, jsonify
from flask import request
from flask import redirect
from flask import make_response
from flask import abort
from flask import url_for
from flask import render_template
from flask import Response
from flask import send_file
from flask import send_from_directory
from sqlalchemy import desc
import jinja2
import sys
import socket
import re
import urllib2
import urllib
import sqlite3, os
import subprocess
import signal
from subprocess import call
from multiprocessing import Process
import os.path
import json
from datetime import datetime
from flask.ext.sqlalchemy import SQLAlchemy
import tempfile
import random
from werkzeug import secure_filename

basedir = os.path.abspath(os.path.dirname(__file__))
template_loc = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
host = '0.0.0.0'

app = Flask('DICE-Monitoring')

"""
Uncoment if use from flask.ext.moment import Moment
"""
#moment = Moment(app)

"""
Data Base Initialization
"""

app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

db = SQLAlchemy(app)
#this creates a table with 5 columns
class db_diceMonit(db.Model):
	__tablename__='Gateways'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), unique=True)
	revision=db.Column(db.String(64), unique=False)
	schema = db.Column(db.String(64), unique=False)
	schemaVerion=db.Column(db.String(64), unique=False)
	mode = db.Column(db.String(64), unique=False, default = "http")
	defBack = db.Column(db.String(64), unique=False, default = 'None')
	data=db.Column(db.LargeBinary, unique=False)
	endpoints = db.relationship('db_endpoints',backref='name',lazy='dynamic') # added for relationship

	def __rep__(self):
		return '<db_diceMonit %r>' % self.name



"""
Resources

"""


@app.route('/v1/monitoring',methods=['GET'])
def getCurrentSettings():
	response = jsonify({"VM Monitored":"This will be a list"})
	response.status_code = 200
	return response
    


    

"""
Custom errot Handling

"""	


@app.errorhandler(403)
def forbidden(e):
    response = jsonify({'error': 'forbidden'})
    response.status_code = 403
    return respons


@app.errorhandler(404)
def page_not_found(e):
    response = jsonify({'error': 'not found'})
    response.status_code = 404
    return response
   


@app.errorhandler(500)
def internal_server_error(e):
    response = jsonify({'error': 'internal server error'})
    response.status_code = 500
    return response
   

@app.errorhandler(405)
def meth_not_allowed(e):
	response=jsonify({'error':'method not allowed'})
	response.status_code=405
	return response

@app.errorhandler(400)
def bad_request(e):
	response=jsonify({'error':'bad request'})
	response.status_code=400
	return response

@app.errorhandler(415)
def bad_mediatype(e):
	response=jsonify({'error':'unsupported media type'})
	response.status_code = 415
	return response
	


if __name__ == '__main__':
	tmp_loc = tempfile.gettempdir()
	app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(basedir,'default.db')
	db.create_all()
	app.run(host='0.0.0.0', port=8088, debug = True)
	

	
		
	