# Arunachal V1 May 25 2020
##Getting and plotting data

"""
This code creates, gets and/or updates the data
based on the tickers scraped from Wikipedia.

Sequence of code execution: stock_get_data.py > stock_data_transformations.py > stock_dashboards.py
"""


#Importing Modules
from __future__ import with_statement
import bs4 as bs
import datetime
from datetime import date, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from matplotlib import style
import matplotlib.dates as mdates
import matplotlib.animation as animation
import mplfinance as mpf
from mplfinance.original_flavor import candlestick_ohlc
import nsepy
from nsepy import get_history
import numpy as np
import os
import pandas as pd
import pandas_datareader.data as pdr
import pickle
import requests
from sklearn import preprocessing
import yfinance as yf


#Getting and Setting the inputs

chart_input = str(input("""
Market to chart:

For Nifty India (enter Nifty or N):
For S&P500 USA (enter SP500 or S):
""") or "N")

ticker_input = str(input("""Ticker to chart:
"""))

start_day = str(input("""Start Date (YYYY,MM,DD). Don't prefix zero. (default = 400 sessions)
"""))


end_day = datetime.date.today()

if not start_day:
    start_day = end_day - timedelta(300)



#Start the Calcualtions:
    
#Function to get the SP500 data
def save_sp500_tickers():
    
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    
    tickers = []
    
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text.replace('.', '-')
        ticker = ticker[:-1]
        tickers.append(ticker)
    with open("sp500tickers.pickle", "wb") as f:
        pickle.dump(tickers, f)
        
    return tickers

save_sp500_tickers()

#Function to get the Nifty data
def save_nifty_tickers():
    
    resp = requests.get('http://en.wikipedia.org/wiki/NIFTY_50')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    
    tickers = []
    
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[1].text.replace('.', '-')
        ticker = ticker[:-3]+".NS"
        tickers.append(ticker)
        
    with open("niftytickers.pickle", "wb") as f:
        pickle.dump(tickers, f)
        
    return tickers

save_nifty_tickers()


#Setting some default values and validating inputs
if chart_input in ['NSE', 'nse', 'Nifty', 'NIFTY', 'nifty', 'N', 'n']:
    market_to_chart = "Nifty"
    if not ticker_input:
        ticker_input = "SBIN"
        tickers = ticker_input
else:
    if chart_input in ['sp500', 'SP500', 'S&P500', 'S', 's']:
        market_to_chart = "SP500"
        if not ticker_input:
            ticker_input = "MSFT"
            tickers = ticker_input

            
            
#Get Start Day calculation for updates
def get_start_day(ticker):
    df_temp = pd.read_csv('stock_dataset_nifty/{}.csv'.format(ticker), parse_dates = True)
    
    if len(df_temp['Date']) > 0:
        if df_temp['Date'].iloc[-1] != datetime.date.today():
            print (f'Trying to update the {ticker} chart')
            start_day = df_temp['Date'].iloc[-2]
    return start_day



#
#The main function that calculates and updates
def get_data_from_yahoo(reload=False):
    
    global start_day, end_day, tickers, chart_input, ticker_input
    
    
    if reload == True:
        if chart_input in ['NSE', 'nse', 'Nifty', 'NIFTY', 'nifty', 'N', 'n']:
            save_nifty_tickers()
        else:
            if chart_input in ['sp500', 'SP500', 'S&P500', 'S', 's']:
                save_sp500_tickers()
            
    else:
        if market_to_chart == "Nifty":
            
            if not os.path.exists('stock_dataset_nifty'):
                os.makedirs('stock_dataset_nifty')
                
            with open("niftytickers.pickle", "rb") as f:
                tickers = pickle.load(f)
                
        else:
            if market_to_chart == "SP500":
    
                if not os.path.exists('stock_dataset_sp500'):
                    os.makedirs('stock_dataset_sp500')
    
                with open("sp500tickers.pickle", "rb") as f:
                    tickers = pickle.load(f)
            
            
    for ticker in tickers[0:]:
        print (ticker)

        if market_to_chart == "Nifty":
            
            ticker = ticker[:-3]
            
            print ("""Updating SP500...
            """)
            
            if not os.path.exists('stock_dataset_nifty/{}.csv'.format(ticker)):
                df = get_history(ticker, start_day, end_day)
                df.reset_index(inplace=True)
                df.set_index("Date", inplace=True)
                print (f'Creating the following {ticker} file')
                df.to_csv('stock_dataset_nifty/{}.csv'.format(ticker))
                
                
            else:
                
                print('{}: File exists. Checking for updates.'.format(ticker))
                df_temp = pd.read_csv('stock_dataset_nifty/{}.csv'.format(ticker), parse_dates = True)
                
                if len(df_temp['Date']) > 0:                              
                    if df_temp['Date'].iloc[-1] != datetime.date.today(): 
                        print (f'{ticker}: Updating chart.')
                
                        try:
                            with open('stock_dataset_nifty/{}.csv'.format(ticker),'a') as file:
                                start_day = end_day - timedelta(400)
                                            
                                get_file = get_history(ticker, start_day, end_day)
                                file.write(get_file.to_string(index=True, header=False))
                                print (f'{ticker}: Chart updated.')
                                
                        except EnvironmentError:
                            print (f'{ticker}: Error in updating the file.')
         
            
            
            temp_read = pd.read_csv('stock_dataset_nifty/{}.csv'.format(ticker), parse_dates=True, index_col=0)
            if temp_read.duplicated(subset = ['VWAP', 'Volume','Trades']).any() == True:
                print (f'{ticker}: Checking for duplicate entries.')
                temp_read.drop_duplicates(subset= ['VWAP', 'Volume','Trades', 'Close'], keep='first', inplace = True)
                temp_read.to_csv('stock_dataset_nifty/{}.csv'.format(ticker))
            else:
                pass
            
            print (f'{ticker}: Done.')
            
            
            
        
        if market_to_chart == "SP500":
            
            print ("""Updating SP500...
                """)

            if not os.path.exists('stock_dataset_sp500/{}.csv'.format(ticker)):
                df = pdr.get_data_yahoo(ticker, start_day, end_day)
                df.reset_index(inplace=True)
                df.set_index("Date", inplace=True)
                print (f'Creating the {ticker} file')
                df.to_csv('stock_dataset_sp500/{}.csv'.format(ticker))
                            
            else:
                
                print('{}: File exists. Checking for updates.'.format(ticker))

                df_temp = pd.read_csv('stock_dataset_sp500/{}.csv'.format(ticker), parse_dates = True)
                
                if len(df_temp['Date']) > 0:                              
                    if df_temp['Date'].iloc[-1] != datetime.date.today(): 
                        print (f'{ticker}: Updating chart.')
                
                        try:
                            with open('stock_dataset_sp500/{}.csv'.format(ticker),'a') as file:
                                start_day = end_day - timedelta(400)
                                get_file = pdr.get_data_yahoo(ticker, start_day, end_day)
                                file.write(get_file.to_string(index=True, header=False))
                                print (f'{ticker}: Chart updated.')
                                
                        except EnvironmentError:
                            print (f'{ticker}: Error in updating the file.')
           
            
            temp_read = pd.read_csv('stock_dataset_sp500/{}.csv'.format(ticker), parse_dates=True, index_col=0)
            if temp_read.duplicated(subset = ['Open','High', 'Low', 'Close']).any() == True:
                print (f'{ticker}: Checking for duplicate entries.')
                temp_read.drop_duplicates(subset= ['Open', 'High','Low', 'Close'], keep='first', inplace = True)
                temp_read.to_csv('stock_dataset_sp500/{}.csv'.format(ticker))
            else:
                pass
            
            print (f'{ticker}: Done.')
            
            
get_data_from_yahoo()
