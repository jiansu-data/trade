from datetime import datetime
import backtrader as bt
import helper.datah5 as datah5
import pandas as pd
import numpy as np
from datetime import datetime
import multiprocessing as mp
import json
import os
import os.path

from test_ind import  *
from strategy import *
### get buy information data.

class Viewer(bt.SignalStrategy):
    def __init__(self,enddate=None):
        self.macd= bt.ind.MACDHisto()
        self.kds = bt.ind.StochasticFull(self.datas[0], period = 9, period_dfast= 3, period_dslow = 3)
        self.rsi = bt.ind.RelativeStrengthIndex()
        self.roc = bt.ind.RateOfChange100()
        self.mtm = bt.ind.Momentum()
        self.cci = bt.ind.CommodityChannelIndex()
        self.atr = bt.ind.ATR()

    def next(self):


        pass
if __name__ == "__main__":
        db = {}
        result_df = pd.read_csv("output/test/result.csv")
        #print(result_df)
        while True:
            print(result_df[result_df['profit'] < 0][['id', 'profit']])
            sid = input("test :").strip()
            if not sid:
                break
            #sid = "2301"#"9910"
            #st = Viewer
            db[sid] = test_stock(sid,result_show= True,plot = True,strategy=MACDS,enable_log = True,taskname = timestamp())