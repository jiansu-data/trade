from datetime import datetime
import backtrader as bt
import helper.datah5 as datah5
import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timedelta
import multiprocessing as mp
import json
import os
import os.path

from test_ind import  *
from strategy import *
import pickle
### get buy information data.

class Viewer(StrategyLogger):
    session = None
    def __init__(self,enddate=None):
        self.macd= bt.ind.MACDHisto()
        self.bband = bt.ind.BollingerBands()
        self.kds = bt.ind.StochasticFull()#bt.ind.StochasticFull(self.datas[0], period = 9, period_dfast= 3, period_dslow = 3)
        self.rsi = bt.ind.RelativeStrengthIndex()
        self.roc = bt.ind.RateOfChange100()
        #self.mtm = bt.ind.Momentum()
        self.cci = bt.ind.CommodityChannelIndex()
        self.atr = bt.ind.ATR()
        self.dmi = bt.ind.DirectionalMovement()
        self.obv = OnBalanceVolume()
        self.ma5 = bt.ind.MovingAverageSimple(period= 5)
        #self.ma20 = bt.ind.MovingAverageSimple(period=20)
    def next(self):

        if self.session:
            orders = self.session['orders']
            if orders == None:
                return
            cur_datetime = self.datas[0].datetime.datetime(0)
            cur_datetime_str = str(cur_datetime.date())
            #print(cur_datetime)
            if cur_datetime_str in orders:
                # amount	 price	 sid	 symbol	 value
                #print("key",cur_datetime_str)
                (type_,amount,price)= orders[cur_datetime_str]
                del orders[cur_datetime_str]
                if type_ == 0:
                    print("buy",cur_datetime)
                    self.buy()
                elif type_ == 1 :
                    print("sell",cur_datetime)
                    self.sell()
            else:
                #print("no time", cur_datetime)
                pass

        pass
if __name__ == "__main__":
        db = {}
        taskname = "test-kd"
        task_st = taskname.split("-")[1]
        result_df = pd.read_csv("output/%s/result.csv"%(taskname))

        #print(result_df)
        while True:
            print(result_df[result_df['profit'] < 0][['id', 'profit','score','growth']].sort_values(by=['profit']))
            print("---win--")
            print(result_df[result_df['profit'] >= 0][['id', 'profit','score','growth']].sort_values(by=['profit']))
            idx = input("test :").strip()
            #try:
            if(1):
                (sid,fromdate,todate) = result_df.iloc[int(idx)]['id'].split("_")
                if not sid:
                    break
                #sid = "2301"#"9910"
                #st = Viewer
                Viewer.session = pickle.load(open("output/%s/%s.pickle"%(taskname,result_df.iloc[int(idx)]['id']),"rb"))
                print("order",Viewer.session['orders'])
                fromdate = datetime.strptime(fromdate,"%Y-%m-%d")
                todate = datetime.strptime(todate, "%Y-%m-%d")
                real_test = input("real test :")
                st = Viewer
                if real_test: st = strategy_by_name(task_st)

                db[sid] = test_stock(sid,result_show= True,plot = True,strategy=st,enable_log = True,taskname = timestamp(),fromdate= fromdate,todate=todate)
                print("order",Viewer.session['orders'])
            #except:
            if 0:
                print("exit")
                exit(9)
                pass