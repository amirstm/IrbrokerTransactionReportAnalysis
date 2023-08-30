import pandas as pd
import numpy as np
import jdatetime, datetime, json, os, requests, io
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

class Report():
    
    def __init__(self, file_address):
        self.IndexInCharts = True
        self.df_raw = pd.read_excel(file_address, skiprows=2, header=None, 
                   names=["Date", "Detail", "NegativeTransaction", "PositiveTransaction", "Remain", "Branch"])[:-1]
        self.process_df_raw()
        self.prune_unsettled()
        self.trade_summary()
        self.daily_trend()

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
        lastDateBeforeStart = Report.getDateBeforeStart(self.df)
        last_date = lastDateBeforeStart
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

    def trade_summary(self):
        self.buyNum = len(self.df_settled[self.df_settled["Side"] == "Buy"])
        self.sellNum = len(self.df_settled[self.df_settled["Side"] == "Sell"]["Value"])
        self.buySum = self.df_settled[self.df_settled["Side"] == "Buy"]["Value"].sum()
        self.sellSum = self.df_settled[self.df_settled["Side"] == "Sell"]["Value"].sum()
        self.LastDateBeforeStart = Report.getDateBeforeStart(self.df_settled)
        self.StartingDate = self.df_settled["Date"][0]
        self.FinishingDate = self.df_settled["Date"].values[-1]

    # This rather elaborate method extracts the daily trends consisting of:\
    # portfolio, realised profit, and excess investment at the end of the day
    def daily_trend(self):
        self.dailyData = {} # "_date_" : {"Profit": 0, "Investment": 0, "Portfolio": {}}
        portfolio = {} # "_Instrument_" : {"Quantity":0, "Value":0}
        investment = 0
        profit = 0
        last_date = self.StartingDate

        for i in range(len(self.df_settled)):
            instrument = self.df_settled["InstrumentName"][i]
            date = self.df_settled["Date"][i]
            if date != last_date:
                self.dailyData[last_date] = {
                    "Profit": profit,
                    "Investment": investment,
                    "Portfolio": dict([(key, portfolio[key].copy()) for key in portfolio.keys()])
                }
                last_date = date
            value = (1 if self.df_settled["Side"][i] == "Buy" else -1) * self.df_settled["Value"][i]
            quantity = (1 if self.df_settled["Side"][i] == "Buy" else -1) * self.df_settled["Quantity"][i]
            if instrument in portfolio.keys():
                if portfolio[instrument]["Quantity"] * quantity > 0:
                    portfolio[instrument]["Quantity"] += quantity
                    portfolio[instrument]["Value"] += value
                    investment += abs(value)
                else:
                    if abs(quantity) <= abs(portfolio[instrument]["Quantity"]):
                        settledInvestment = int(-portfolio[instrument]["Value"] * quantity/portfolio[instrument]["Quantity"])
                        investment -= abs(settledInvestment)
                        profit += - settledInvestment - value
                        portfolio[instrument]["Value"] -= settledInvestment
                        portfolio[instrument]["Quantity"] += quantity
                    else:
                        settledValue = int(-value * portfolio[instrument]["Quantity"] / quantity)
                        profit += - portfolio[instrument]["Value"] - settledValue
                        investment -= abs(portfolio[instrument]["Value"])
                        newInvested = value - settledValue
                        portfolio[instrument]["Quantity"] += quantity
                        portfolio[instrument]["Value"] = newInvested
                        investment += abs(newInvested)                
                if portfolio[instrument]["Quantity"] == 0:
                    del portfolio[instrument]
            else:
                portfolio[instrument] = {"Quantity": quantity, "Value": value}
                investment += abs(value)
        self.dailyData[last_date] = {
            "Profit": profit,
            "Investment": investment,
            "Portfolio": dict([(key, portfolio[key].copy()) for key in portfolio.keys()])
        }
        for key in self.dailyData.keys():
            self.dailyData[key]["TradeValue"] = self.df_settled[self.df_settled["Date"] == key]["Value"].sum()
        DailyExcessInvestment = [self.dailyData[key]["Investment"] - self.dailyData[key]["Profit"] for key in self.dailyData.keys()]
        self.MaxExcessInvestment = max(DailyExcessInvestment)
        self.InitialInvestment = self.MaxExcessInvestment

    def charts_calculations(self, IndexData):
        self.xLabels = [i for i in self.dailyData.keys()]
        self.xs = [Report.getDaysBetweenDates(self.LastDateBeforeStart, i) for i in self.xLabels]
        self.yProfits = [self.dailyData[i]["Profit"] for i in self.dailyData.keys()]
        self.yInvestments = [self.dailyData[i]["Investment"] for i in self.dailyData.keys()]
        self.yProfitCoefs = [i / self.InitialInvestment for i in self.yProfits]
        self.yTradeValues = [self.dailyData[i]["TradeValue"] for i in self.dailyData.keys()]

        if self.IndexInCharts:
            market_index_days = list(IndexData.keys())
            market_index_day_before_start = IndexData[market_index_days[market_index_days.index(self.StartingDate)-1]]
            self.yMarketIndexProfitCoefs = [IndexData[xl] / market_index_day_before_start - 1.0 for xl in self.xLabels]
            self.yMarketIndexProfit = [i * self.InitialInvestment for i in self.yMarketIndexProfitCoefs]

    def chart_profit_value(self):
        fig = plt.figure(figsize=(10, 6), dpi=150)
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(self.xs, self.yProfits, linestyle='--', marker='o', c='#bde4ff', markerfacecolor='#4100c2', label="Realized Return")
        if self.IndexInCharts:
            ax.plot(self.xs, self.yMarketIndexProfit, linestyle=':', c='#f79a97', label="Market Index Return")
        ax.set_facecolor('#' + 'f9'*3)
        ax.yaxis.grid(True, linestyle='--', c="#adadad")
        ax.set_title('Profits in Rials')
        ax.xaxis.set_major_formatter(FuncFormatter(self.dayToJllDateFormatter))
        ax.legend(loc="upper left")
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
        return output

    def chart_profit_percentage(self):
        fig = plt.figure(figsize=(10, 6), dpi=150)
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(self.xs, self.yProfitCoefs, linestyle='--', marker='o', c='#bde4ff', markerfacecolor='#4100c2', label="Realized Return")
        if self.IndexInCharts:
            ax.plot(self.xs, self.yMarketIndexProfitCoefs, linestyle=':', c='#f79a97', label="Market Index Return")
        ax.set_facecolor('#' + 'f9'*3)
        ax.yaxis.grid(True, linestyle='--', c="#adadad")
        ax.set_title('Profit Percentage')
        ax.xaxis.set_major_formatter(FuncFormatter(self.dayToJllDateFormatter))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y_val, pos: f"{y_val*100:0.0f}%"))
        ax.legend(loc="upper left")
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
        return output

    def chart_trade_volume(self):
        fig = plt.figure(figsize=(10, 6), dpi=150)
        ax = fig.add_subplot(1, 1, 1)
        ax.bar(self.xs, self.yTradeValues, color="#4100c2")
        ax.set_facecolor('#' + 'f9'*3)
        ax.yaxis.grid(True, linestyle='--', c="#adadad")
        ax.set_title('Daily Trade Volume in Rials')
        ax.xaxis.set_major_formatter(FuncFormatter(self.dayToJllDateFormatter))
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
        return output

    def dayToJllDateFormatter(self, x, pos):
        grgDate = Report.getGregorianDate(self.StartingDate) + datetime.timedelta(days=x)
        return Report.getJalaliFromGreogorian(grgDate)

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

    def daily_data_display(daily):
        portfolio = pd.DataFrame([[key, daily["Portfolio"][key]["Quantity"]] for key in daily["Portfolio"].keys()], columns=['Instrument', 'Latest Settled Date'])
        portfolio_html = portfolio.to_html(classes="daily-data-portfolio df-table-mini", justify="left")
        profit_html = f"<p>Profit on this day: <b>{daily['Profit']:,}</b></p>"
        return f"<div class='df-daily-data-wrapper'>{portfolio_html}</div>\n{profit_html}"

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

def get_index_data(last_date):
    file_name = "32097828799138957"
    url = "http://cdn.tsetmc.com/api/Index/GetIndexB2History/32097828799138957"
    if os.path.isfile(file_name):
        try:
            market_index = read_index_data_file(file_name)
        except:
            market_index = {}
        if last_date in market_index.keys():
            return market_index
    with open(file_name, "wb") as file:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        response = requests.get(url, headers=headers)
        file.write(response.content)
    return read_index_data_file(file_name)

def read_index_data_file(file_name):
    with open(file_name) as file:
        market_index_raw = json.load(file)["indexB2"]
    market_index = dict([
        (Report.getJalaliFromGreogorian(datetime.date(year=row["dEven"]//10000,month=row["dEven"]//100%100,day=row["dEven"]%100)), 
        row["xNivInuClMresIbs"]) for row in market_index_raw])
    return market_index
