import pandas as pd
import numpy as np
import jdatetime, datetime, json
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from flask import Flask, redirect, url_for, request, render_template
from werkzeug.utils import secure_filename

print("Hello world!")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "/uploaded/"
           
@app.route('/')
def hello_world():
   return render_template('index.html')

@app.route('/closer')
def closer():
   return '''
   <h1>You are getting closer :)</h1>
   '''

@app.route('/closer/<int:userId>')
def closer_userId(userId):
   return f'''
   <h1>You are getting closer user number {userId} :)</h1>
   '''

@app.route('/closer/<string:username>')
def closer_username(username):
   return f'''
   <h1>You are getting closer user {username} :)</h1>
   '''

@app.route('/close')
def close():
   name = request.cookies["username"]
   if name.isdigit():
      return redirect(url_for('closer_userId', userId = name))
   else:
      return redirect(url_for('closer_username', username = name))
   
@app.route('/login',methods = ['POST', 'GET'])
def login():
   if request.method == 'POST':
      user = request.form['name']
      resp = redirect(url_for('close'))
      resp.set_cookie("username", user)
      return resp
   else:
      return render_template('login.html', time_display = datetime.datetime.now())

@app.route('/upload')
def upload_file_page():
   return render_template('upload.html')
	
@app.route('/uploader', methods = ['POST'])
def upload_file():
   f = request.files['file']
   f.save(f"uploaded/{secure_filename(f.filename)}")
   return 'file uploaded successfully'

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
