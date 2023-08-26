import pandas as pd
import numpy as np
import jdatetime, datetime, json
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from flask import Flask, redirect, url_for, request, render_template, session
from werkzeug.utils import secure_filename
import os
import glob

print("Hello world!")

UPLOAD_PATH = "uploaded/"
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_PATH
app.secret_key = 'any random string'
if not os.path.exists(UPLOAD_PATH):
    os.makedirs(UPLOAD_PATH)

@app.route('/')
def index():
   files = [os.path.basename(x) for x in glob.glob(f"{UPLOAD_PATH}*.xlsx")]
   return render_template('index.html', files = files)

@app.route('/report/<string:filename>')
def report(filename):
   if os.path.isfile(f"{UPLOAD_PATH}{filename}"):
      return f'''
      <h1>Hooray, file exists.</h1>
      '''
   else:
      return f"<h3>File with name {filename} was not found.</h3>"

@app.route('/upload', methods = ['POST'])
def upload_file_page():
   f = request.files['file']
   if f.filename.endswith(".xlsx"):
      f.save(f"{UPLOAD_PATH}{secure_filename(f.filename)}")
      return redirect("/")
   else:
      return "File was not of xlsx format."
	
@app.route("/login", methods=["POST", "GET"])
def login():
   if request.method == 'POST':
      session['username'] = request.form['username']
      return redirect(url_for('login'))
   else:
      if 'username' in session:
         username = session['username']
         return f'Logged in as {username}' + \
            "<br><b><a href='/'>Home</a></b>" + \
            "<br><br><b><a href='/logout'>click here to log out</a></b>"
      else:
         return render_template('login.html', time_display = datetime.datetime.now())
   
@app.route('/logout')
def logout():
   del session['username']
   return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
