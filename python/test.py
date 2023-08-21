import pandas as pd
import numpy as np
import jdatetime, datetime, json
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

print(f"pandas version -> {pd.__version__}")
print(f"numpy version -> {np.__version__}")
print(f"matplotlib version -> {matplotlib.__version__}")
print("Hello world!")

from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
   return '''
   <h1>You are getting closer :)</h1>
   '''

if __name__ == "__main__":
    app.run(host='0.0.0.0')