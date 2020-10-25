from datetime import datetime
import backtrader as bt
import pandas as pd
from datetime import datetime
from datetime import timedelta
import backtrader as bt
import numpy as np
import time
import os.path

cache_mode = False
cache_map = {}
def datafromh5(h5_file= "data/historical_data.h5",stock_id="2330",fromdate=None, todate=None, ret_df = False):
    global cache_map
    global cache_mode
    t1 = datetime.now()
    df = None
    if not cache_mode :
        df  = pd.read_hdf(h5_file)
    if cache_mode :
        if h5_file not in cache_map:
            df = pd.read_hdf(h5_file)
            cache_map[h5_file] = df
        else:
            df = cache_map[h5_file]
    df.columns = ['open', 'high', 'low', 'close', 'volume', 'Dividends', 'Stock Splits',
       'STOCK_ID', 'Adj Close']
    """
    除權息參考價（平盤價）＝（除權息前一日收盤價− 現金股利 ） ／ （每1張＋配股張數）
    df.iloc[0,7] = 0
    (x,y)  = df.shape
    df['adjust_diff'] = []
    for i in range(1,x):
        adjust_diff = df.iloc[i-1, 3]*(1+ df.iloc[i, 6])+ df.iloc[i,5]  - df.iloc[i-1, 3]
        
        df.iloc[i, 8] = df.iloc[i-1, 8]+ adjust_diff
    
    for 
    df.open = df.open+ df['adjust_diff']]
    df.high = df.high+ df['adjust_diff']]
    df.low = df.low+ df['adjust_diff']]
    df.close = df.close+ df['adjust_diff']]
    
    """
    stock_df = df[df.STOCK_ID == stock_id]
    stock_df = stock_df.drop(columns  = "STOCK_ID")
    if fromdate:
        stock_df = stock_df[stock_df.index >= fromdate]
    if todate:
        stock_df = stock_df[stock_df.index<= todate]
    t2 = datetime.now()
    #print("time:",(t2-t1).seconds)
    if ret_df:
        return stock_df
    return bt.feeds.PandasData(dataname=stock_df)


def get_yahoo_data( stock_id, start = None, end = datetime.now().date() ):
    import yfinance as yf
    data = yf.Ticker(stock_id)
    if start == None:
        df = data.history(start=start, end = end)
    else:
        df = data.history(period="max")
    return df


def update_h5(h5_file= "data/historical_data.h5",start = None):
    import twstock
    global cache_map
    global cache_mode
    last_date = None

    t1 = datetime.now()
    src_df = None
    if not cache_mode and os.path.exists(h5_file):
        src_df = pd.read_hdf(h5_file)
        last_date = src_df.index.max().date() + datetime.timedelta(days=1)
    if start:
        last_date = start

    if cache_mode :
        if h5_file not in cache_map:
            if os.path.exists(h5_file):
                src_df = pd.read_hdf(h5_file)
                cache_map[h5_file] = src_df
                last_date = src_df.index.max().date() + datetime.timedelta(days=1)

        else:
            df = cache_map[h5_file]
    stock_list = {}
    for e in twstock.twse:
        stock = (twstock.twse[e])
        if stock.type == "股票":
            stock_list[stock.code] = stock.name
    # stock_list = pd.read_csv("data" + '/stock_id.csv')
    # stock_list.rename(columns={'證券代號':'STOCK_ID','證券名稱':'NAME'}, inplace=True)

    historical_data = pd.DataFrame()

    stock_done = []
    for e in stock_list:
        stock_id = e + '.TW'
        new_df = get_yahoo_data(stock_id, last_date)
        new_df['STOCK_ID'] = e
        historical_data = pd.concat([historical_data, new_df])

        time.sleep(0.8)
        stock_done.append(stock_id)
        print(stock_id, "progress: ", len(stock_done) / len(stock_list) * 100)
    if src_df:
        historical_data = pd.concat([src_df, historical_data])
    historical_data.to_hdf( h5_file, key='s')
    if h5_file in cache_map:
        del cache_map[h5_file]

def get_sanda_df(date):
    import requests
    import pandas as pd
    import re

    link = "https://www.twse.com.tw/fund/T86?response=csv&date=%s&selectType=ALL"%(date.strftime("%Y%m%d"))
    r = requests.get(link)
    if r.status_code == 200:
        import functools
        db = []
        lines = r.text.split("\r\n")
        #print("line",lines)
        if len(lines) <=10 :
            #print(len(lines))
            return None
        header = lines[1].split('","')[:-1]
        header  = list(map(lambda x: x.replace(',',"").replace('"',"").replace(" ","") , header))
        #print(header)
        for e in lines[2:-10]:
            #print(e)
            #print(e.split(",")[:-1])
            #db.append(e.split('","')[:-1])
            rows = e.split('","')[:-1]
            row_data =list(map(lambda x: x.replace(',',"").replace('"',"").replace(" ","") , rows))
            db.append(row_data)
        #print(db)
        df = pd.DataFrame(db)
        #df['date']
        df.columns = header
        df['datetime']= date
        #print("show",date)
        #df = df.dropna(how='all',inplace=True)
        return df
    else:
        print("fail :", r.status_code,link)
        return None


def build_sd_date(filename,start, end):
    import numpy
    import random
    date = start
    df_sd = pd.DataFrame()
    while date != end:
        time.sleep(random.random() * 5)
        df = get_sanda_df(date.date())
        print(date)
        #print(df,type(df))
        if type(df) != type(df_sd):
            date += timedelta(days=1)
            #print("conti")
            continue
        #print(df)

        print("na check each:",pd.isna(df).any().any())
        if(pd.isna(df).any().any()):
            input("to go")
        if type(df) == type(df_sd):
            df_sd = pd.concat([df_sd, df])
        date += timedelta(days=1)
    print(df_sd.columns)
    df_sd.to_hdf(filename,key= 's')
    print("check na",pd.isna(df_sd).any().any())
    #print(df_sd[pd.isna(df_sd)])
    for e in df_sd.columns:
        #print(e)
        if e != None and e != '證券名稱' and e != '證券代號'  and e != 'datetime':
            print("run string to num",e)
            #print(df_sd[e])
            df_sd[e] = df_sd[e].astype(np.int32)
    df_sd.to_hdf(filename,key= 's')
    return df_sd


def update_sd(filename, end = datetime.now().date() ):
    df = pd.read_hdf(filename)
    last_date = df['datetime'].max().date() + datetime.timedelta(days=1)
    new_df = build_sd_date(filename,last_date, end)
    return  pd.concat([df, new_df])


if __name__ == "__main__":
    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    # Add a strategy
    cerebro.addstrategy(bt.Strategy)

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = datafromh5(fromdate=datetime(2018,1,1))#bt.feeds.PandasData(dataname=dataframe)

    cerebro.adddata(data)

    # Run over everything
    cerebro.run()

    # Plot the result
    cerebro.plot(style='bar')
