import pandas as pd
import numpy as np
import jdatetime, datetime, json
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

class Report():
    
    def __init__(self, file_address):
        self.df_raw = pd.read_excel(file_address, skiprows=2, header=None, 
                   names=["Date", "Detail", "NegativeTransaction", "PositiveTransaction", "Remain", "Branch"])[:-1]
        self.process_df_raw()

    def display_df_full(self, df):
        if isinstance(df, pd.DataFrame):
            return df.to_html(max_rows=5, show_dimensions=True, classes="df-table-full", justify="left")
        else:
            return "<p>No display</p>"

    def display_df_head(self, df, rows=5):
        if isinstance(df, pd.DataFrame):
            return df.head(rows).to_html(classes="df-table-head", justify="left")
        else:
            return "<p>No display</p>"

    def process_df_raw(self):
        self.df = self.df_raw.copy()
        self.df = pd.concat([self.df, Report.getDetailRowBrokenDown(self.df)], axis=1)
        self.df_exceptional = self.df[self.df.isnull().any(axis=1)]
        self.df_exceptional.drop(columns=['Side', 'Quantity', 'InstrumentName', 'Price'], inplace=True)
        self.df.dropna(inplace=True)
        self.df["Quantity"] = pd.to_numeric(self.df["Quantity"].replace(',','', regex=True))
        self.df["Price"] = pd.to_numeric(self.df["Price"].replace(',','', regex=True))
        self.df["Value"] = self.df["Quantity"] * self.df["Price"]
        self.df["InstrumentName"] = self.df["InstrumentName"].apply(Report.InstrumentNameTrimmer)
        self.df["Side"] = self.df["Side"].apply(Report.SideProcessor)
        self.df.drop(columns=['Detail', 'NegativeTransaction', 'PositiveTransaction', 'Remain', 'Branch'], inplace=True)
        self.df.reset_index(inplace=True, drop=True)

    def getDetailRowBrokenDown(df):
        pattern = r"(?P<Side>\w+)\s+(?P<Quantity>[\d,]+) (?:مشاركت|سهم|واحد|تقدم) (?P<InstrumentName>[\w\d\s/\(\)\u200c,.-]+)(?=[\s]{2,}(?P<Price>[\d,]+))"
        return df['Detail'].str.extract(pattern)

    def InstrumentNameTrimmer(x):
        x = x.removesuffix(' متوسط')
        x = x.removesuffix(' ')
        return x

    def SideProcessor(x):
        if x == "فروش":
            return "Sell"
        elif x == "خريد":
            return "Buy"
        else:
            return None

    # Converts Jalali date in the format of "1402/05/25" into a datetime.date object
    def getGregorianDate(jllString):
        jllParts = jllString.split("/")
        return jdatetime.date(int(jllParts[0]),int(jllParts[1]),int(jllParts[2])).togregorian()

    # Returns the number of dates between two Jalali dates of the format "1402/05/25"
    def getDaysBetweenDates(start, finish):
        return (Report.getGregorianDate(finish) - Report.getGregorianDate(start)).days

    # Converts datetime.date object to Jalali date of format "1402/05/25"
    def getJalaliFromGreogorian(date):
        d = jdatetime.date.fromgregorian(date=date)
        return f"{d.year}/{d.month:02}/{d.day:02}"

    # Finding the unsettled records to exclude
    def getDateBeforeStart(df):
        minDate = df["Date"][0]
        minDateGregorian = Report.getGregorianDate(minDate)
        beforeDateGregorian = minDateGregorian + datetime.timedelta(days=-1)
        return Report.getJalaliFromGreogorian(beforeDateGregorian)
    