"""
This code is for tranformation of data with added analysis.

This data is used for the charting / dashboarding using stock_dashboards.py
code.

Sequence of code execution: stock_get_data.py > stock_data_transformations.py > stock_dashboards.py
"""


#Importing Modules [Not all will be used here]
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



#===================================================================
#Tranformations on the Daily Charts
#
sbin['Pivot'] = (sbin['Open'] + sbin['High'] + sbin['Low'] + sbin['Close'] * 2)/5
sbin['Typical'] = (sbin['VWAP'] * 2 + sbin ['Pivot'])/3
sbin['Advantage'] = sbin['Typical'] - sbin['Close']
sbin['M2M'] = (sbin['Advantage'] * sbin['Volume']).cumsum()
million = 1_000_000
sbin['Trades_trunc'] = (sbin['Trades'] / million)
sbin['M2M50ma'] = sbin['M2M'].rolling(window=50, min_periods = 0).mean()
sbin['%Del50ma'] = sbin['%Deliverble'].rolling(window=50, min_periods = 0).mean()
sbin['DelVol50ma'] = sbin['Deliverable Volume'].rolling(window=50, min_periods = 0).mean()
sbin['DelPerTrade'] = (sbin['Deliverable Volume']/sbin['Trades']).round(2)
sbin['DelPerTrade50ma'] = sbin['DelPerTrade'].rolling(window=50, min_periods = 0).mean()
sbin['Typical_200ma'] = sbin['Typical'].rolling(window=200, min_periods = 0).mean()
sbin['Typical_100ma'] = sbin['Typical'].rolling(window=100, min_periods = 0).mean()
sbin['Typical_55ma'] = sbin['Typical'].rolling(window=55, min_periods = 0).mean()
sbin['Volume_200ma'] = sbin['Volume'].rolling(window=200, min_periods = 0).mean()

#===================================================================
#Charting Bolinger Bands
#
sbin['20ma'] = sbin['Typical'].rolling(window=20, min_periods =0).mean()
std_dev = sbin['20ma'].rolling(window=20).std()
sbin['upper_2_band'] = sbin['20ma'] + 2 * std_dev
sbin['lower_2_band'] = sbin['20ma'] - 2 * std_dev
sbin['upper_3_band'] = sbin['20ma'] + 3 * std_dev
sbin['lower_3_band'] = sbin['20ma'] - 3 * std_dev

#===================================================================
#Charting VWAP Std Dev Bands
#
sbin['VWAP_20ma'] = sbin['VWAP'].rolling(window=20, min_periods =0).mean()
std_dev_vwap = sbin['VWAP_20ma'].rolling(window=20).std()
sbin['VWAP_upper_2_band'] = sbin['VWAP_20ma'] + 2 * std_dev_vwap
sbin['VWAP_lower_2_band'] = sbin['VWAP_20ma'] - 2 * std_dev_vwap
sbin['VWAP_upper_3_band'] = sbin['VWAP_20ma'] + 3 * std_dev_vwap
sbin['VWAP_lower_3_band'] = sbin['VWAP_20ma'] - 3 * std_dev_vwap

#===================================================================
#Charting MACD with SMAs
#
sbin['macd_daily_fast'] = sbin['Typical'].rolling(window=27).mean()
sbin['macd_daily_slow'] = sbin['Typical'].rolling(window=55).mean()
sbin['macd_daily_trigger'] = sbin['Typical'].rolling(window=13).mean()
sbin['macd_daily_macd'] = sbin['macd_daily_fast'] - sbin['macd_daily_slow'] 

#===================================================================#
#Charting M2M like MACD with SMAs
#
sbin['m2m_daily_fast'] = sbin['M2M'].rolling(window=27).mean()
sbin['m2m_daily_slow'] = sbin['M2M'].rolling(window=55).mean()
sbin['m2m_daily_trigger'] = sbin['M2M'].rolling(window=13).mean()
sbin['m2m_daily_macd'] = sbin['m2m_daily_fast'] - sbin['m2m_daily_slow'] 

#===================================================================
#Ichimoku Shinko - Normal
#
#Tenkan Sen
tenkan_max = sbin['High'].rolling(window = 9, min_periods = 0).max()
tenkan_min = sbin['Low'].rolling(window = 9, min_periods = 0).min()
sbin['tenkan_avg'] = (tenkan_max + tenkan_min) / 2

#Kijun Sen
kijun_max = sbin['High'].rolling(window = 26, min_periods = 0).max()
kijun_min = sbin['Low'].rolling(window = 26, min_periods = 0).min()
sbin['kijun_avg'] = (kijun_max + kijun_min) / 2

#Senkou Span A
#(Kijun + Tenkan) / 2 Shifted ahead by 26 periods
sbin['senkou_a'] = ((sbin['kijun_avg'] + sbin['tenkan_avg']) / 2).shift(26)

#Senkou Span B
#52 period High + Low / 2
senkou_b_max = sbin['High'].rolling(window = 52, min_periods = 0).max()
senkou_b_min = sbin['Low'].rolling(window = 52, min_periods = 0).min()
sbin['senkou_b'] = ((senkou_b_max + senkou_b_min) / 2).shift(52)

#Chikou Span
#Current close shifted -26
sbin['chikou'] = (sbin['Close']).shift(-26)

#===================================================================
# Making Data for Candlestick Charts

candle_data = list(zip(mdates.date2num(sbin.index.to_pydatetime()),
                         sbin['Open'], sbin['High'],
                         sbin['Low'], sbin['Close']))

#===================================================================
# Making Daily Data for Market and Volume Profile

sbin_daily_volPro = sbin[['Close', 'Volume', 'Deliverable Volume', 'High', 'Low']].copy()
sbin_daily_volPro.set_index('Close', inplace = True)
sbin_daily_volPro['delvolchange'] = sbin_daily_volPro['Deliverable Volume'].groupby(['Close']).sum()
sbin_daily_volPro['sum_vol'] = sbin_daily_volPro[['Volume']].groupby(['Close']).sum()
sbin_daily_volPro.reset_index(inplace=True)
sbin_daily_volPro['last_count'] = sbin_daily_volPro['Close'].agg('count')
sbin_daily_volPro['pct_change'] = sbin_daily_volPro['Close'].pct_change()

#===================================================================
         
sbin.reset_index()


##===================================================================
#Tranformations on the Weekly Charts
##===================================================================

#Creating DF for the Weekly data
sbin_weekly = sbin.copy()
sbin_weekly.reset_index(drop=False, inplace=True)

sbin_weekly['Week_Number'] = sbin_weekly['Date'].dt.week
sbin_weekly['Year'] = sbin_weekly['Date'].dt.year

#Dict for transformations
tranformations_for_weekly = {
                            'Date':'last', 
                            'Open':'first',
                            'High':'max',
                            'Low':'min',
                            'Close':'last',
                            'Volume':'sum',
                            'Trades': 'sum',
                            'VWAP': 'mean',
                            '%Deliverble': 'mean',
                            'Deliverable Volume': "sum"
                            }

#Applying Transformations on Weekly DF
sbin_weekly = sbin_weekly.groupby([sbin_weekly['Year'], sbin_weekly['Week_Number']]).agg(tranformations_for_weekly)
sbin_weekly.sort_values(['Date'], ascending=True, inplace=True)

#Applying further transformation and Creating columns
sbin_weekly['Pivot'] = (sbin_weekly['Open'] + sbin_weekly['High'] + sbin_weekly['Low'] + sbin_weekly['Close'] * 2)/5
sbin_weekly['Typical'] = (sbin_weekly['VWAP'] * 2 + sbin_weekly ['Pivot'])/3
sbin_weekly['Advantage'] = sbin_weekly['Typical'] - sbin_weekly['Close']
sbin_weekly['M2M'] = (sbin_weekly['Advantage'] * sbin_weekly['Volume']).cumsum()
sbin_weekly['M2M50ma'] = sbin_weekly['M2M'].rolling(window=50, min_periods = 0).mean()
sbin_weekly['%Del50ma'] = sbin_weekly['%Deliverble'].rolling(window=50, min_periods = 0).mean()
sbin_weekly['DelVol50ma'] = sbin_weekly['Deliverable Volume'].rolling(window=50, min_periods = 0).mean()
sbin_weekly['DelPerTrade'] = (sbin_weekly['Deliverable Volume']/sbin_weekly['Trades']).round(2)
sbin_weekly['DelPerTrade50ma'] = sbin_weekly['DelPerTrade'].rolling(window=50, min_periods = 0).mean()
sbin_weekly['Typical_200ma'] = sbin_weekly['Typical'].rolling(window=200).mean()
sbin_weekly['Typical_100ma'] = sbin_weekly['Typical'].rolling(window=100).mean()
sbin_weekly['Typical_55ma'] = sbin_weekly['Typical'].rolling(window=55).mean()
sbin_weekly['Volume_55ma'] = sbin_weekly['Volume'].rolling(window=55).mean()

#===================================================================
#Charting Bolinger Bands
#
sbin_weekly['20ma'] = sbin_weekly['Typical'].rolling(window=20, min_periods =0).mean()
std_dev_weekly = sbin_weekly['20ma'].rolling(window=20).std()
sbin_weekly['upper_2_band'] = sbin_weekly['20ma'] + 2 * std_dev_weekly
sbin_weekly['lower_2_band'] = sbin_weekly['20ma'] - 2 * std_dev_weekly
sbin_weekly['upper_3_band'] = sbin_weekly['20ma'] + 3 * std_dev_weekly
sbin_weekly['lower_3_band'] = sbin_weekly['20ma'] - 3 * std_dev_weekly

#===================================================================
#Charting VWAP Std Dev Bands
#
sbin_weekly['VWAP_20ma'] = sbin_weekly['VWAP'].rolling(window=20, min_periods =0).mean()
std_dev_vwap_weekly = sbin_weekly['VWAP_20ma'].rolling(window=20).std()
sbin_weekly['VWAP_upper_2_band'] = sbin_weekly['VWAP_20ma'] + 2 * std_dev_vwap_weekly
sbin_weekly['VWAP_lower_2_band'] = sbin_weekly['VWAP_20ma'] - 2 * std_dev_vwap_weekly
sbin_weekly['VWAP_upper_3_band'] = sbin_weekly['VWAP_20ma'] + 3 * std_dev_vwap_weekly
sbin_weekly['VWAP_lower_3_band'] = sbin_weekly['VWAP_20ma'] - 3 * std_dev_vwap_weekly

#===================================================================
#Charting MACD with SMAs
#
sbin_weekly['macd_daily_fast'] = sbin_weekly['Typical'].rolling(window=14).mean()
sbin_weekly['macd_daily_slow'] = sbin_weekly['Typical'].rolling(window=28).mean()
sbin_weekly['macd_daily_trigger'] = sbin_weekly['Typical'].rolling(window=7).mean()
sbin_weekly['macd_daily_macd'] = sbin_weekly['macd_daily_fast'] - sbin_weekly['macd_daily_slow'] 

#===================================================================#
#Charting M2M like MACD with SMAs
#
sbin_weekly['m2m_daily_fast'] = sbin_weekly['M2M'].rolling(window=14).mean()
sbin_weekly['m2m_daily_slow'] = sbin_weekly['M2M'].rolling(window=28).mean()
sbin_weekly['m2m_daily_trigger'] = sbin_weekly['M2M'].rolling(window=7).mean()
sbin_weekly['m2m_daily_macd'] = sbin_weekly['m2m_daily_fast'] - sbin_weekly['m2m_daily_slow'] 

#===================================================================
#Ichimoku Shinko - Normal
#
#Tenkan Sen
tenkan_max_weekly = sbin_weekly['High'].rolling(window = 9, min_periods = 0).max()
tenkan_min_weekly = sbin_weekly['Low'].rolling(window = 9, min_periods = 0).min()
sbin_weekly['tenkan_avg'] = (tenkan_max_weekly + tenkan_min_weekly) / 2

#Kijun Sen
kijun_max_weekly = sbin_weekly['High'].rolling(window = 26, min_periods = 0).max()
kijun_min_weekly = sbin_weekly['Low'].rolling(window = 26, min_periods = 0).min()
sbin_weekly['kijun_avg'] = (kijun_max_weekly + kijun_min_weekly) / 2

#Senkou Span A
#(Kijun + Tenkan) / 2 Shifted ahead by 26 periods
sbin_weekly['senkou_a'] = ((sbin_weekly['kijun_avg'] + sbin_weekly['tenkan_avg']) / 2).shift(26)

#Senkou Span B
#52 period High + Low / 2
senkou_b_max_weekly = sbin_weekly['High'].rolling(window = 52, min_periods = 0).max()
senkou_b_min_weekly = sbin_weekly['Low'].rolling(window = 52, min_periods = 0).min()
sbin_weekly['senkou_b'] = ((senkou_b_max_weekly + senkou_b_min_weekly) / 2).shift(52)

#Chikou Span
#Current close shifted -26
sbin_weekly['chikou'] = (sbin_weekly['Close']).shift(-26)

#===================================================================
# 
#Making Data for Candlestick Charts
# Weekly CandleStick Chart
#

sbin_weekly_for_candle = sbin_weekly.copy()
sbin_weekly_for_candle.head(2)

sbin_weekly_for_candle.reset_index(drop = True, inplace = True)
sbin_weekly_for_candle.set_index('Date', inplace = True)
sbin_weekly_for_candle.head(2)

sbin_weekly_candle_data = list(zip(mdates.date2num(sbin_weekly_for_candle.index.to_pydatetime()),
                         sbin_weekly_for_candle['Open'], sbin_weekly_for_candle['High'],
                         sbin_weekly_for_candle['Low'], sbin_weekly_for_candle['Close']))

#===================================================================
# Making Weekly Data for Market and Volume Profile

sbin_weekly_volPro = sbin_weekly[['Close', 'Volume', 'Deliverable Volume', 'High', 'Low']].copy()
sbin_weekly_volPro.set_index('Close', inplace = True)
sbin_weekly_volPro['delvolchange'] = sbin_weekly_volPro['Deliverable Volume'].groupby(['Close']).sum()
sbin_weekly_volPro['sum_vol'] = sbin_weekly_volPro[['Volume']].groupby(['Close']).sum()
sbin_weekly_volPro.reset_index(inplace=True)
sbin_weekly_volPro['last_count'] = sbin_weekly_volPro['Close'].agg('count')
sbin_weekly_volPro['pct_change'] = sbin_weekly_volPro['Close'].pct_change()

#===================================================================
#Pivot Points [Not used yet, in the charts]

pivot_points =  pd.DataFrame(columns=['PP','R1','R2','R3','S1','S2','S3'], index=['Weekly','Monthly'])

pivot_points['PP']['Weekly'] = (sbin_weekly['High'][-1] + sbin_weekly['Low'][-1] + sbin_weekly['Close'][-1]) / 3
pivot_points['R1']['Weekly'] = pivot_points['PP']['Weekly'] * 2 - sbin_weekly['Low'][-1]
pivot_points['R2']['Weekly'] = pivot_points['PP']['Weekly'] + sbin_weekly['High'][-1] - sbin_weekly['Low'][-1]
pivot_points['R3']['Weekly'] = sbin_weekly['High'][-1] + (2 * (pivot_points['PP']['Weekly'] - sbin_weekly['Low'][-1]))
pivot_points['S1']['Weekly'] = (2* pivot_points['PP']['Weekly']) - sbin_weekly['High'][-1]
pivot_points['S2']['Weekly'] = pivot_points['PP']['Weekly'] - sbin_weekly['High'][-1] + sbin_weekly['Low'][-1]
pivot_points['S3']['Weekly'] = sbin_weekly['Low'][-1] - 2*(sbin_weekly['High'][-1] - pivot_points['PP']['Weekly'])

