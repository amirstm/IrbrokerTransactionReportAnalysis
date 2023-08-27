from flask import Flask, redirect, url_for, request, render_template, session
from werkzeug.utils import secure_filename
import os, glob
from dataUtils import Report

print("Hello world!")

UPLOAD_PATH = "uploaded/"
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_PATH
app.secret_key = 'any random string'
if not os.path.exists(UPLOAD_PATH):
    os.makedirs(UPLOAD_PATH)
Reports = {}

@app.route('/')
def index():
   files = [os.path.basename(x) for x in glob.glob(f"{UPLOAD_PATH}*.xlsx")]
   return render_template('index.html', files = files)

@app.route('/report/<string:filename>')
def report(filename):
   file_address = f"{UPLOAD_PATH}{filename}"
   if os.path.isfile(file_address):
      return report_valid(file_address)
   else:
      return f"<h3>File with name {filename} was not found.</h3>"

def report_valid(file_address):
   report = Report(file_address)
   Reports["filename"] = report
   return render_template("report.html", df_raw = report.display_df_full(report.df_raw), 
                          df_exceptional = report.display_df_full(report.df_exceptional),
                          df = report.display_df_head(report.df))

@app.route('/upload', methods = ['POST'])
def upload_file_page():
   f = request.files['file']
   if f.filename.endswith(".xlsx"):
      f.save(f"{UPLOAD_PATH}{secure_filename(f.filename)}")
      return redirect("/")
   else:
      return "File was not of xlsx format."

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
