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
import collections
def datetime_from_string(string):
    return datetime(*list(map(lambda x: int(x), string.split("-"))))
class StrategyLogger(bt.SignalStrategy):
    log_enable = True
    log_file = None
    params = (
        ('enddate', None),
        ('startdate',None),
        ('order_requests',collections.OrderedDict())
    )
    def order_requests(self, order_datetime, order_type,order_num, order_price):
        #if self.params.order_requests: self.params.order_requests = collections.OrderedDict()
        self.params.order_requests[str(self.datas[0].datetime.date(0))] = [order_type, order_num,order_price]
    def __init__(self,log_enable = True):
        self.enddate = self.params.enddate
        self.startdate = self.params.startdate
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
            #self.log('Order Submitted/Accepted'+":"+order.Status[order.status])
            if order.status == order.Accepted:
                self.order_requests(order.created.dt,order.ordtype, order.created.size,order.created.price)
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

    def starttrade(self):
        #print(self.params.startdate, )
        if self.params.startdate and self.datas[0].datetime.date(0) >self.params.startdate.date():
            return True
        else:
            return False

    def endtrade(self):
        if  self.position:
            if self.params.enddate and self.datas[0].datetime.date(0) == self.params.enddate.date():
                self.log('LAST CLOSE, %.2f' % self.data.close[0])
                self.close()
                return True
        else :
            return False
    def runtrade(self):
        if not  self.starttrade():return False
        if self.endtrade(): return False
        return True

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
        #self.enddate = self.params.enddate


    def next(self):
        if not self.runtrade():return

        #if self.cross_up_mid[0]: print(self.cross_up_mid[0])
        #self.log('Close, %.2f' % self.data.close[0])
        if not self.position:
            #if self.data.close >self.bb.mid[0] and self.data.close <self.bb.mid[-1]:
            if self.cross_up_mid[0]:
                self.log('BUY CREATE, %.2f' % self.data.close[0])
                self.buy()
            if self.cross_up_bot[0] and (self.bb.mid[0] > self.bb.mid[-2])/self.bb.mid[-2] > 0.01:
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
            if self.crossdown_mid or self.crossdown_top:
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

class MACDS(StrategyLogger):
    def __init__(self, enddate=None):
        self.macd= bt.ind.MACDHisto()

        self.crossup = bt.ind.CrossUp(self.macd.macd, self.macd.signal)
        self.crossdown = bt.ind.CrossDown(self.macd.macd, self.macd.signal)
        #self.signal_add(bt.SIGNAL_LONG, self.cross_up_mid)
        #self.signal_add(bt.SIGNAL_SHORT, self.crossdown_top)
        self.enddate = self.params.enddate

    def next(self):
        if not self.runtrade():return
        #if self.cross_up_mid[0]: print(self.cross_up_mid[0])
        if  not self.position:
            #if self.data.close >self.bb.mid[0] and self.data.close <self.bb.mid[-1]:
            if self.crossup[0]:
                self.buy()
        else:

            if self.crossdown[0]:
                self.close()

        pass

class KDS(StrategyLogger):
    def __init__(self, enddate=None):
        self.kds = bt.ind.StochasticFull(self.datas[0], period = 9, period_dfast= 3, period_dslow = 3)

        self.crossup = bt.ind.CrossUp(self.kds.lines.percK, self.kds.lines.percD)
        self.crossdown = bt.ind.CrossDown(self.kds.lines.percK, self.kds.lines.percD)
        self.enddate = self.params.enddate
    def next(self):
        if not self.runtrade():return
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

class RSIS(StrategyLogger):
    def __init__(self, enddate=None):
        self.rsi = bt.ind.RelativeStrengthIndex()

        #self.signal_add(bt.SIGNAL_LONG, self.cross_up_mid)
        #self.signal_add(bt.SIGNAL_SHORT, self.crossdown_top)
        self.hold = False
        self.enddate = self.params.enddate
    def next(self):
        if not self.runtrade():return
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

class DMIS(StrategyLogger):

    def __init__(self, enddate=None):
        self.dmi = bt.ind.DirectionalMovement()
        self.crossup = bt.ind.CrossUp(self.dmi.plusDI, self.dmi.minusDI)
        self.crossdown = bt.ind.CrossDown(self.dmi.plusDI, self.dmi.minusDI)
    def next(self):
        """
    1.攻擊訊號
    ADX為趨勢動量指標，ADX可作為趨勢行情是否出現的判斷依據，在漲勢或跌勢明顯的階段，ADX數值都會顯著上升。
    當行情明顯朝某一方向進行時(不管往多方或空方)，只要ADX向上，表示正在上漲或正在下跌的趨勢力道都會增強。
    多方：+DI > –DI，此時ADX向上，表多方在攻擊。
    空方： –DI> +DI，此時ADX向上，表空方在攻擊。
    故當ADX線上升時常為多方或空方強勢股。
    ADX線數值25 以上可判断攻擊趨勢將展開，配合均線(MA)效用更好，能把握住一波好行情。

    2.盤整訊號
    若行情呈現盤整格局時，ADX會低於+DI與–DI二條線。
    若ADX數值低於20，則不論DI如何，均顯示市場沒有明顯趨勢。此時投資人應該退場以靜待行情的出現。
    3.反轉訊號
    當ADX從上升趨勢轉為下降時，代表目前價格變動趨勢減弱，行情可能即將反轉。是輔助判斷漲勢和跌勢的強弱是否延續的反轉訊號。
        """
        if not self.runtrade():return
        #if self.cross_up_mid[0]: print(self.cross_up_mid[0])
        if not self.position and self.dmi.adx[0] >self.dmi.adx[-2]:
            #if self.data.close >self.bb.mid[0] and self.data.close <self.bb.mid[-1]:
            #if self.kds.k > self.kds.d:
            if self.crossup:
                #print("up",self.crossup)
                self.hold = True
                self.buy()
        else:
            #if self.kds.k < self.kds.d:
            if self.crossdown:
                #print("down", self.crossdown)
                self.hold = False
                self.close()
        pass

class CCIS(StrategyLogger):
    def __init__(self, enddate=None):
        self.cci = bt.ind.CommodityChannelIndex()

        self.buysignal = bt.ind.CrossUp(self.cci.cci,self.cci.params.lowerband )
        self.sellsignal = bt.ind.CrossDown(self.cci.cci,self.cci.params.upperband )
    def next(self):
        if not self.runtrade():return
        if not self.position:
            if self.buysignal:
                #print("up",self.crossup)
                self.buy()
        else:
            if self.sellsignal:
                #print("down", self.crossdown)
                self.close()
        pass

class OnBalanceVolume(bt.Indicator):
    '''
    REQUIREMENTS
    ----------------------------------------------------------------------
    Investopedia:
    ----------------------------------------------------------------------
    https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:on_balance_volume_obv

    1. If today's closing price is higher than yesterday's closing price,
       then: Current OBV = Previous OBV + today's volume

    2. If today's closing price is lower than yesterday's closing price,
       then: Current OBV = Previous OBV - today's volume

    3. If today's closing price equals yesterday's closing price,
       then: Current OBV = Previous OBV
    ----------------------------------------------------------------------
    '''

    alias = 'OBV'
    lines = ('obv',)

    plotlines = dict(
        obv=dict(
            _name='OBV',
            color='purple',
            alpha=0.50
        )
    )

    def __init__(self):

        # Plot a horizontal Line
        self.plotinfo.plotyhlines = [0]

    def nextstart(self):
        # We need to use next start to provide the initial value. This is because
        # we do not have a previous value for the first calcuation. These are
        # known as seed values.

        # Create some aliases
        c = self.data.close
        v = self.data.volume
        obv = self.lines.obv

        if c[0] > c[-1]:
            obv[0] = v[0]

        elif c[0] < c[-1]:
            obv[0] = -v[0]
        else: obv[0] = 0

    def next(self): # Aliases to avoid long lines
        c = self.data.close
        v = self.data.volume
        obv = self.lines.obv
        if c[0] > c[-1]:
            obv[0] = obv[-1] + v[0]
        elif c[0] < c[-1]:
            obv[0] = obv[-1] - v[0]
        else:
            obv[0] = obv[-1]
class OBVS(StrategyLogger):
    def __init__(self, enddate=None):
        self.obv = OnBalanceVolume()

        self.buysignal = bt.ind.CrossUp(self.cci.cci,self.cci.params.lowerband )
        self.sellsignal = bt.ind.CrossDown(self.cci.cci,self.cci.params.upperband )
    def next(self):
        """
三、ＯＢＶ線的應用法則：
1.ＯＢＶ線下降，且股價上升，為賣出信號。
2.ＯＢＶ線上升，且股價下跌，為買進信號。
3.ＯＢＶ線緩慢上升，屬於買進信號，表示買盤力量加強。
4.ＯＢＶ線急速上升，屬於賣出信號，表示買盤已盡全力，即將力竭。
        """
        if not self.runtrade():return
        if not self.position:
            if self.buysignal:
                #print("up",self.crossup)
                self.buy()
        else:
            if self.sellsignal:
                #print("down", self.crossdown)
                self.close()
        pass