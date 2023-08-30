from flask import Flask, redirect, url_for, request, render_template, session, Response
from werkzeug.utils import secure_filename
import os, glob
from dataUtils import Report, get_index_data

UPLOAD_PATH = "uploaded/"
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_PATH
app.secret_key = 'any random string'
if not os.path.exists(UPLOAD_PATH):
    os.makedirs(UPLOAD_PATH)
Reports = {}
IndexData = {}

@app.route('/')
def index():
   files = [os.path.basename(x) for x in glob.glob(f"{UPLOAD_PATH}*.xlsx")]
   return render_template('index.html', files = files)

@app.route('/report/<string:filename>')
def report(filename):
   file_address = f"{UPLOAD_PATH}{filename}"
   if os.path.isfile(file_address):
      return report_valid(filename, file_address)
   else:
      return f"<h3>File with name {filename} was not found.</h3>"

def report_valid(filename, file_address):
   global Reports
   global IndexData
   report = Report(file_address)
   Reports[filename] = report
   if report.FinishingDate not in IndexData.keys():
      try:
         IndexData = get_index_data(report.FinishingDate)
      except Exception as e:
         report.IndexInCharts = False
   return render_template("report.html", report = report,
                          df_raw = Report.display_df_summary(report.df_raw), 
                          df_exceptional = Report.display_df_summary(report.df_exceptional),
                          df = Report.display_df_head(report.df),
                          df_excluded_instruments = Report.display_df_custom(report.df_excluded_instruments, classes="df-table-mini")
                          )

@app.route('/report/<string:filename>/initialInvestment', methods = ['POST'])
def updateInitialInvestment(filename):
   global IndexData
   report = Reports[filename]
   data_raw = request.get_data().decode("utf-8")
   initialInvestment = int(data_raw)
   report.InitialInvestment = initialInvestment
   report.charts_calculations(IndexData)
   return ('', 204)

@app.route('/report/<string:filename>/profitHistogramWindowSize', methods = ['POST'])
def updateProfitHistogramWindowSize(filename):
   global IndexData
   report = Reports[filename]
   data_raw = request.get_data().decode("utf-8")
   profitHistogramWindowSize = int(data_raw)
   report.ProfitHistogramWindowSize = profitHistogramWindowSize
   report.charts_profit_histogram_calculations()
   return ('', 204)

@app.route('/report/<string:filename>/chart-profit-value')
def chart_profit_value(filename):
   report = Reports[filename]
   output = report.chart_profit_value()
   return Response(output.getvalue(), mimetype='image/png')

@app.route('/report/<string:filename>/chart-profit-percentage')
def chart_profit_percentage(filename):
   report = Reports[filename]
   output = report.chart_profit_percentage()
   return Response(output.getvalue(), mimetype='image/png')

@app.route('/report/<string:filename>/chart-trade-volume')
def chart_trade_volume(filename):
   report = Reports[filename]
   output = report.chart_trade_volume()
   return Response(output.getvalue(), mimetype='image/png')

@app.route('/report/<string:filename>/chart-profit-histogram')
def chart_profit_histogram(filename):
   report = Reports[filename]
   output = report.chart_profit_histogram()
   return Response(output.getvalue(), mimetype='image/png')

@app.route('/upload', methods = ['POST'])
def upload_file_page():
   f = request.files['file']
   if f.filename.endswith(".xlsx"):
      f.save(f"{UPLOAD_PATH}{secure_filename(f.filename)}")
      return redirect("/")
   else:
      return "File was not of xlsx format."

@app.route('/daily_data_report')
def daily_data_report():
   date = request.args.get('date', None)
   filename = request.args.get('filename', None)
   report = Reports[filename]
   daily = report.dailyData[date]
   return Report.daily_data_display(daily)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
