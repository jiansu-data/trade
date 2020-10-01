from datetime import datetime
import backtrader as bt
import pandas as pd
from datetime import datetime
import backtrader as bt
import numpy as np

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
    df.columns = ['open', 'high', 'low', 'close', 'volume', 'openinterest', 'Stock Splits',
       'STOCK_ID', 'Adj Close']
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
