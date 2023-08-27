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
        self.prune_unsettled()

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

    def prune_unsettled(self):
        self.LastDateBeforeStart = Report.getDateBeforeStart(self.df)
        last_date = self.LastDateBeforeStart
        self.DailyPortfolio = {last_date: {}}

        for i in range(len(self.df)):
            date = self.df["Date"][i]
            if date not in self.DailyPortfolio.keys():
                self.DailyPortfolio[date] = self.DailyPortfolio[last_date].copy()
                last_date = date
            instrumentName = self.df["InstrumentName"][i]
            if instrumentName not in self.DailyPortfolio[date].keys():
                self.DailyPortfolio[date][instrumentName] = 0
            self.DailyPortfolio[date][instrumentName] += (1 if self.df["Side"][i] == "Buy" else -1) * self.df["Quantity"][i]

        for date in self.DailyPortfolio.keys():
            date_keys = list(self.DailyPortfolio[date].keys())
            for instrument in date_keys:
                if self.DailyPortfolio[date][instrument] == 0:
                    del self.DailyPortfolio[date][instrument]

        instrumentsToExcludeAfterDate = {}
        allDates = list(self.DailyPortfolio.keys())
        for instrument in self.DailyPortfolio[last_date]:
            instrumentsToExcludeAfterDate[instrument] = allDates[0]
            for date in allDates[::-1]:
                if instrument not in self.DailyPortfolio[date]:
                    instrumentsToExcludeAfterDate[instrument] = date
                    break
        self.df_excluded_instruments = pd.DataFrame(instrumentsToExcludeAfterDate.items(), columns=['Instrument', 'Latest Settled Date'])

        recordsToExclude = []
        for i in range(len(self.df)):
            if self.df["InstrumentName"][i] in instrumentsToExcludeAfterDate.keys():
                if self.df["Date"][i] > instrumentsToExcludeAfterDate[self.df["InstrumentName"][i]]:
                    recordsToExclude.append(i)

        self.len_transactions_processed = len(self.df)
        self.len_transactions_unsettled = len(recordsToExclude)
        self.len_transactions_settled = self.len_transactions_processed - self.len_transactions_unsettled
        self.df_settled = self.df.drop(recordsToExclude, axis=0)
        self.df_settled.reset_index(inplace=True, drop=True)

    def display_df_custom(df, classes=""):
        if isinstance(df, pd.DataFrame):
            return df.to_html(classes=classes, justify="left")
        else:
            return "<p>No display</p>"

    def display_df_summary(df):
        if isinstance(df, pd.DataFrame):
            return df.to_html(max_rows=5, show_dimensions=True, classes="df-table-summary", justify="left")
        else:
            return "<p>No display</p>"

    def display_df_head(df, rows=5):
        if isinstance(df, pd.DataFrame):
            return df.head(rows).to_html(classes="df-table-head", justify="left")
        else:
            return "<p>No display</p>"

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
    