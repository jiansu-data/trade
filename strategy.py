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

class StrategyLogger(bt.SignalStrategy):
    log_enable = True
    log_file = None

    def __init__(self,log_enable = True):
        pass
    def __del__(self):
        pass
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        if self.log_enable:
            print('%s, %s' % (dt.isoformat(), txt))
            if self.log_file: print('%s, %s' % (dt.isoformat(), txt),file=self.log_file)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected'+":"+order.Status[order.status])#+str(order.status)+

        # Write down: no pending order
        self.order = None
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        #print(trade)
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

class BBS(StrategyLogger):
    def __init__(self):
        self.bb= bt.ind.BBands(period=20)


        self.cross_up_mid = bt.ind.CrossUp(self.data.close, self.bb.mid)
        self.cross_up_bot = bt.ind.CrossUp(self.data.close, self.bb.bot)
        #self.signal_add(bt.SIGNAL_LONG, self.cross_up_mid)

        self.crossdown_top = bt.ind.CrossDown(self.data.close, self.bb.top)
        self.crossdown_mid = bt.ind.CrossDown(self.data.close, self.bb.mid)
        #self.signal_add(bt.SIGNAL_SHORT, self.crossdown_top)


    def next(self):
        #if self.cross_up_mid[0]: print(self.cross_up_mid[0])
        #self.log('Close, %.2f' % self.data.close[0])
        if not self.position:
            #if self.data.close >self.bb.mid[0] and self.data.close <self.bb.mid[-1]:
            if self.cross_up_mid[0]:
                self.log('BUY CREATE, %.2f' % self.data.close[0])
                self.buy()
            if self.cross_up_bot[0] and self.bb.mid[0] > self.bb.mid[-2]:
                self.log('BUY CREATE, %.2f' % self.data.close[0])
                self.buy()
            #crossover = bt.ind.CrossUp(self.data.close, self.bb.mid)
            #self.signal_add(bt.SIGNAL_LONG, crossover)
            #pass
        #if self.cross_up_mid[0] == True:
        #    self.buy()
        else:
            #if self.crossdown_top:
            #    self.close()
            if self.crossdown_mid:
                self.log('CLOSE CREATE, %.2f' % self.data.close[0])
                self.close()

            # if self.bb.mid[0] < self.bb.mid[1]:
                #
                #self.close()
            #    pass

        #if self.crossdown_top[0] == True:
            #self.sell(size=1)
        #    self.close()
        pass

class MACDS(bt.SignalStrategy):
    def __init__(self):
        self.macd= bt.ind.MACDHisto()

        self.crossup = bt.ind.CrossUp(self.macd.macd, self.macd.signal)
        self.crossdown = bt.ind.CrossDown(self.macd.macd, self.macd.signal)
        #self.signal_add(bt.SIGNAL_LONG, self.cross_up_mid)
        #self.signal_add(bt.SIGNAL_SHORT, self.crossdown_top)
    def next(self):
        #if self.cross_up_mid[0]: print(self.cross_up_mid[0])
        if not self.position:
            #if self.data.close >self.bb.mid[0] and self.data.close <self.bb.mid[-1]:
            if self.crossup:
                self.buy()
        else:

            if self.crossdown:
                self.close()

        pass

class KDS(bt.SignalStrategy):
    def __init__(self):
        self.kds = bt.ind.StochasticFull(self.datas[0], period = 9, period_dfast= 3, period_dslow = 3)

        self.crossup = bt.ind.CrossUp(self.kds.lines.percK, self.kds.lines.percD)
        self.crossdown = bt.ind.CrossDown(self.kds.lines.percK, self.kds.lines.percD)
    def next(self):
        #if self.cross_up_mid[0]: print(self.cross_up_mid[0])
        if not self.position:
            #if self.data.close >self.bb.mid[0] and self.data.close <self.bb.mid[-1]:
            #if self.kds.k > self.kds.d:
            if self.crossup:
                #print("up",self.crossup)
                self.buy()
        else:
            #if self.kds.k < self.kds.d:
            if self.crossdown:
                #print("down", self.crossdown)
                self.close()
        pass

class RSIS(bt.SignalStrategy):
    def __init__(self):
        self.rsi = bt.ind.RelativeStrengthIndex()

        #self.signal_add(bt.SIGNAL_LONG, self.cross_up_mid)
        #self.signal_add(bt.SIGNAL_SHORT, self.crossdown_top)
        self.hold = False
    def next(self):
        #if self.cross_up_mid[0]: print(self.cross_up_mid[0])
        if not self.position:
            #if self.data.close >self.bb.mid[0] and self.data.close <self.bb.mid[-1]:
            #if self.kds.k > self.kds.d:
            if self.rsi.rsi <30:
                #print("up",self.crossup)
                self.hold = True
                self.buy()
        else:
            #if self.kds.k < self.kds.d:
            if self.rsi.rsi  >70:
                #print("down", self.crossdown)
                self.hold = False
                self.close()

        pass
