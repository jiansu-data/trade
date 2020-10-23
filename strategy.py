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

def strategy_by_name(name):
    strategy_map = { "bband":  BBS,"kd":KDS,"macd": MACDS,"rsi":  RSIS,"dmi":  DMIS ,"cci": CCIS, "":StrategyFramework,
                     "bbtk":StrategyBBand,"ma":StrategyMA}
    if name in strategy_map: return strategy_map[name]
    return StrategyFramework

class StrategyLogger(bt.SignalStrategy):
    log_enable = True
    log_file = None
    params = (
        ('enddate', None),
        ('startdate',None),
        #('order_requests',collections.OrderedDict())
    )
    def order_requests(self, order_datetime, order_type,order_num, order_price):
        if 'order_requests_data' not in self.__dict__: self.order_requests_data = collections.OrderedDict()
        self.order_requests_data[str(self.order_date)] = [order_type, order_num,order_price]
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
    def buy(self,*args,**kwargs):
        #self.log("buy")
        self.order_date = self.datas[0].datetime.date(0)
        super().buy(*args,**kwargs)
    def sell(self,*args,**kwargs):
        #self.log("sell")
        self.order_date = self.datas[0].datetime.date(0)
        super().sell(*args,**kwargs)
    def close(self,*args,**kwargs):
        #self.log("close")
        self.order_date = self.datas[0].datetime.date(0)
        super().close(*args,**kwargs)
    def notify_order(self, order):
        #self.log(order.Status[order.status])
        if order.status  == order.Created:
            self.log('Order Submitted/Accepted' + ":" + order.Status[order.status])
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

class Trick:
    sg_tp = ["+" , "-" , ""]
    sg_up = "+"
    sg_down = "-"
    sg_wait = ""
    st_tp = [90, 70,50,30,10]
    name = "trick"
    def __init__(self,strategy, datas):
        self.st = strategy
        self.datas = datas
    def signal(self):
        return  self.sg_tp[0]
    def strength(self):
        return self.st_tp[0]
    def action(self):
        """
        more stock?
        :return:
        """
        return
    def cross(self,up,a,b):
        gt, lt = ((lambda  x,y: x> y), (lambda x,y:x<y))
        f1,f2 = gt,lt
        if not up:
            f1,f2  = lt,gt
        if f1(a[0] , b[0]) and f2(a[-1] , b[-1]):
            return True
        return False
    def cross_up(self,a,b):
        return self.cross(True,a,b)
    def cross_down(self,a,b):
        return self.cross(False,a,b)

class DrawDown_Trick(Trick):
    name = "dd"

    def __init__(self, limit=10, strategy=None):
        self.highest  = 0
        self.dd = 0
        self.limit = limit
        pass

    def signal(self):
        if self.dd > self.limit :
            return self.sg_down
        return self.sg_wait

    def strength(self):
        return 100 - self.dd*100

    def next(self, value,position):
        if value > self.highest:
            self.highest = value
        if value == 0 or not position:
            self.highest = 0
        #if value and self.highest != value:
        #    print( ( self.highest -value)/self.highest , self.highest,value )
        self.dd =  ( self.highest -value)/self.highest if self.highest else 0
        return self.dd

class MACD_Trick(Trick):
    name = "macd"
    def __init__(self, strategy,datas):
        super(MACD_Trick,self).__init__(strategy,datas)
        self.macd  = datas[0]

    def signal(self):
        if self.cross_up(self.macd.macd,self.macd.signal) and self.macd.macd < 0 and self.macd.signal < 0:
            #self.st.log('%s signal, %s' % (self.name,self.sg_up))
            return self.sg_up
        """
        if self.cross_up(self.macd.macd,self.macd.signal):
            self.st.log('%s signal, %s' % (self.name,self.sg_up))
            return self.sg_up
        """
        if self.cross_down(self.macd.macd,self.macd.signal):
            #self.st.log('%s signal, %s' % (self.name,self.sg_down))
            return self.sg_down
        return self.sg_wait

    def strength(self):
        if self.macd.macd > 0 and self.macd.signal > 0:
            return 75
        if self.macd.macd < 0 and self.macd.signal < 0:
            return 25
        return 50

class RSI_Trick(Trick):
    name = "rsi"
    def __init__(self, strategy,datas):
        super(RSI_Trick,self).__init__(strategy,datas)
        self.rsi  = datas[0]

    def signal(self):
        if self.rsi.rsi[0] <30   and self.rsi.rsi[0] and self.rsi.rsi[0] > self.rsi.rsi[-2]:
            #self.st.log('%s signal, %s' % (self.name,self.sg_up))
            return self.sg_up
        if self.rsi.rsi[0] >70  and self.rsi.rsi[0] and self.rsi.rsi[0] > self.rsi.rsi[-2]:
            #self.st.log('%s signal, %s' % (self.name,self.sg_down))
            return self.sg_down
        return self.sg_wait

    def strength(self):
        if self.rsi.rsi[0] > 30 and self.rsi.rsi[0] <50:
            return 25
        if self.rsi.rsi[0] > 70 and self.rsi.rsi[0] > 50:
            return 75
        return 50

class CCI_Trick(Trick):
    name = "rsi"
    def __init__(self, strategy,datas):
        super(CCI_Trick,self).__init__(strategy,datas)
        self.ind  = datas[0]

    def signal(self):
        return self.sg_wait

    def strength(self):
        if self.ind.cci[0] > 30 and self.ind.cci[0] <50:
            return 25
        if self.ind.rsi[0] > 70 and self.ind.cci[0] > 50:
            return 75
        return 50

class  KD_Trick(Trick):
    name = "rsi"
    def __init__(self, strategy,datas):
        super(KD_Trick,self).__init__(strategy,datas)
        self.kd  = datas[0]

    def signal(self):
        if self.cross_up(self.kd.lines.percK,self.kd.lines.percD):
            #self.st.log('%s signal, %s' % (self.name,self.sg_up))
            return self.sg_up
        if self.cross_down(self.kd.lines.percK,self.kd.lines.percD):
            #self.st.log('%s signal, %s' % (self.name,self.sg_down))
            return self.sg_down
        return self.sg_wait

    def strength(self):
        if self.kd.lines.percK[0] > 20 and self.kd.lines.percK[0] <50:
            return 25
        if self.kd.lines.percK[0] < 70 and self.kd.lines.percK[0] > 50:
            return 75
        return 50
class  BB_Trick(Trick):
    name = "bband"
    def __init__(self, strategy,datas):
        super(BB_Trick,self).__init__(strategy,datas)
        self.bband  = datas[0]

    def signal(self):

        if self.cross_up(self.st.data.close,self.bband.lines.bot):
            #self.st.log('%s signal, %s' % (self.name,self.sg_up))
            return self.sg_up
        if self.cross_down(self.st.data.close,self.bband.lines.top):
            #self.st.log('%s signal, %s' % (self.name,self.sg_down))
            return self.sg_down
        return self.sg_wait

    def strength(self):
        #if self.st.data.close[0 ]> self.bband.lines.bot[0] and \
        if self.st.data.close[0 ]< self.bband.lines.mid[0]:
            return 25
        #if self.st.data.close[0 ]<  self.bband.lines.top[0]  and
        if self.st.data.close[0 ]> self.bband.lines.mid[0]:
            return 75
        return 50
class MA_Trick(Trick):
    name = "ma"
    def __init__(self, strategy,datas):
        super(MA_Trick,self).__init__(strategy,datas)
        self.ma  = datas[0]

    def signal(self):
        if self.cross_up(self.st.data,self.ma.sma) :
            #self.st.log('%s signal, %s' % (self.name,self.sg_up))
            return self.sg_up
        if self.cross_down(self.st.data,self.ma.sma):
            #self.st.log('%s signal, %s' % (self.name,self.sg_down))
            return self.sg_down
        return self.sg_wait

    def strength(self):
        return 50

class StrategyFramework(StrategyLogger):
    def __init__(self):
        self.macd = bt.ind.MACDHisto()
        self.macd_tk = MACD_Trick(strategy=self, datas=[self.macd])
        self.dd = DrawDown()
        self.rsi = bt.ind.RelativeStrengthIndex()
        self.rsi_tk = RSI_Trick(strategy=self, datas=[self.rsi])
        self.kd = bt.ind.StochasticFull()
        self.kd_tk = KD_Trick(strategy=self, datas=[self.kd])
        self.tks = [self.macd_tk ,self.rsi_tk ,self.kd_tk]

    def trick_infomation(self):
        for e in self.tks:
            print(e.name, "signal : ",e.signal(),"strength:",e.strength())
    def next(self):
        if not self.runtrade(): return
        macd_signal = self.macd_tk.signal()
        kd_signal = self.kd_tk.signal()
        rsi_signal = self.rsi_tk.signal()


        down  = self.dd.next(self.data.close[0] if self.position else 0,self.position)
        if not self.position:
            if macd_signal== Trick.sg_up:
                """
                if self.rsi_tk.strength() < 50:
                    self.log('ignore because rsi %d ' % self.rsi_tk.strength())
                    return
                if self.kd_tk.strength() < 50:
                    self.log('ignore because kd %d ' % self.kd_tk.strength())
                    return
                """
                self.log('BUY CREATE, %.2f' % self.data.close[0])
                self.buy()
        else:
            """
            if self.rsi_tk.strength() < 50:
                self.log('close because rsi %d ' % self.rsi_tk.strength())
                self.close()
                return
            if self.kd_tk.strength() < 50:
                self.log('close  because kd %d ' % self.kd_tk.strength())
                self.close()
                return
            
            if kd_signal == Trick.sg_down:
                self.close()
                return
            """
            if macd_signal == Trick.sg_down:
                self.close()
                return
            """
            if down > 0.05:
                self.log('down %f close' % down)
                self.close()
                return
            """


class StrategyMA(StrategyLogger):
    def __init__(self):
        """
        self.macd = bt.ind.MACDHisto()
        self.macd_tk = MACD_Trick(strategy=self, datas=[self.macd])
        self.dd = DrawDown()
        self.rsi = bt.ind.RelativeStrengthIndex()
        self.rsi_tk = RSI_Trick(strategy=self, datas=[self.rsi])
        self.kd = bt.ind.StochasticFull()
        self.kd_tk = KD_Trick(strategy=self, datas=[self.kd])
        self.tks = [self.macd_tk, self.rsi_tk, self.kd_tk]

        """
        self.ma5 = bt.ind.MovingAverageSimple(period = 5)
        self.ma20 = bt.ind.MovingAverageSimple(period = 20)
        self.ma_tk = MA_Trick(strategy=self, datas=[self.ma5])
        self.dd = DrawDown_Trick(5)
        self.kd = bt.ind.StochasticFull()
        self.cci = bt.ind.CommodityChannelIndex()

    def trick_infomation(self):
        for e in self.tks:
            print(e.name, "signal : ", e.signal(), "strength:", e.strength())

    def next(self):
        if not self.runtrade(): return
        if not self.position:
            if self.ma_tk.cross_up(self.ma5.lines.sma, self.ma20.lines.sma):
                #if self.kd.lines.percK[0]<80:
                if self.cci.lines.cci[0] < 100:
                    self.buy()
        else:
            if self.ma_tk.cross_down(self.ma5.lines.sma, self.ma20.lines.sma):
                self.close()
        """
        signal = self.ma_tk.signal()

        down = self.dd.next(self.data.close[0] if self.position else 0,self.position)
        if not self.position:
            if signal == Trick.sg_up:

                if self.data.close[0]  > self.ma20.lines.sma[0]:
                    self.log('BUY CREATE, %.2f' % self.data.close[0])
                    self.buy()
        else:
            if signal == Trick.sg_down :
                self.close()
                return
                
        """
class StrategyBBand(StrategyLogger):
    def __init__(self):
        #self.macd = bt.ind.MACDHisto()
        #self.macd_tk = MACD_Trick(strategy=self, datas=[self.macd])
        self.dd_tk = DrawDown_Trick(0.05)
        #self.rsi = bt.ind.RelativeStrengthIndex()
        #self.rsi_tk = RSI_Trick(strategy=self, datas=[self.rsi])
        #self.kd = bt.ind.StochasticFull()
        #self.kd_tk = KD_Trick(strategy=self, datas=[self.kd])
        #self.tks = [self.macd_tk, self.rsi_tk, self.kd_tk,self.bband_tk]
        self.bband = bt.ind.BollingerBands()
        self.bband_tk = BB_Trick(strategy=self, datas=[self.bband])
        self.ma5 = bt.ind.MovingAverageSimple(period=5)


        self.delay_buy = -1
        self.buy_price = 0
    def trick_infomation(self):
        return
        info = ""
        for e in self.tks:
            print(e.name, "signal : ", e.signal(), "strength:", e.strength())
            _ = "%s sig:%s sth:%s " %(e.name, e.signal(),e.strength())
            info+= _
        self.log(info)
    def next(self):
        if not self.runtrade(): return
        #macd_signal = self.macd_tk.signal()
        #kd_signal = self.kd_tk.signal()
        #rsi_signal = self.rsi_tk.signal()
        bband_signal = self.bband_tk.signal()

        down = self.dd_tk.next(self.data.close[0] ,self.position)
        dd_signal = self.dd_tk.signal()

        if not self.position:
            tobuy = False
            if bband_signal == Trick.sg_up:
                tobuy = True
                #self.delay_buy = 5
                #return

            if self.delay_buy > 0:
                self.delay_buy -=1
                if self.data.close[0] >self.ma5.lines.sma[0]  :
                    tobuy = True
                if self.data.close[0]  > self.data.close[-2]  :
                    tobuy = True and tobuy
            if tobuy:
                self.delay_buy -= 1
                self.trick_infomation()
                self.buy_price = self.data.close[0]
                self.buy()
        else:
            """
            if self.rsi_tk.strength() < 50:
                self.log('close because rsi %d ' % self.rsi_tk.strength())
                self.close()
                return
            if self.kd_tk.strength() < 50:
                self.log('close  because kd %d ' % self.kd_tk.strength())
                self.close()
                return

            if kd_signal == Trick.sg_down:
                self.close()
                return
            """
            """
            if self.buy_price >self.data.close[0] :
                self.log("buy price lose %f" % (self.data.close[0]))
                self.close()
                return 
            """
            """
            if self.buy_price  *0.98 > self.data.close[0]:
                self.log("down trend? ")
                self.close()
                return
            """
            if dd_signal :
                self.log("drowdown signal %f" %(self.dd_tk.dd))
                self.close()
                return

            if bband_signal == Trick.sg_down:
                self.close()
                self.buy_price = 0
                return
            """
            if down > 0.05:
                self.log('down %f close' % down)
                self.close()
                return
            """
class BBS(StrategyLogger):

    def __init__(self):
        self.bb= bt.ind.BBands(period=20)
        self.cci = bt.ind.CommodityChannelIndex()
        self.kd = bt.ind.StochasticFull()
        self.rsi = bt.ind.RelativeStrengthIndex()
        self.macd = bt.ind.MACDHisto()
        self.ma5 = bt.ind.MovingAverageSimple(period=5)

        self.cross_up_mid = bt.ind.CrossUp(self.data.close, self.bb.mid)
        self.cross_up_bot = bt.ind.CrossUp(self.data.close, self.bb.bot)
        #self.signal_add(bt.SIGNAL_LONG, self.cross_up_mid)

        self.crossdown_top = bt.ind.CrossDown(self.data.close, self.bb.top)
        self.crossdown_mid = bt.ind.CrossDown(self.data.close, self.bb.mid)
        #self.signal_add(bt.SIGNAL_SHORT, self.crossdown_top)
        #self.enddate = self.params.enddate

        self.prepare_buy = -1
        self.signal_price = -1
        self.signal_rsi = -1
        self.buy_price = -1
    def next(self):
        if not self.runtrade():return

        #if self.cross_up_mid[0]: print(self.cross_up_mid[0])
        #self.log('Close, %.2f' % self.data.close[0])
        if not self.position:
            #if self.data.close >self.bb.mid[0] and self.data.close <self.bb.mid[-1]:
            """
            #not stable.
            if self.cross_up_mid[0]:
                self.log('BUY CREATE, %.2f' % self.data.close[0])
                self.buy()
            if self.cross_up_bot[0] and (self.bb.mid[0] > self.bb.mid[-2])/self.bb.mid[-2] > 0.01:
                self.log('BUY CREATE, %.2f' % self.data.close[0])
                self.buy()
            """
            tobuy = False
            """
            if self.prepare_buy > 0:
                self.prepare_buy -=1
            if self.prepare_buy == 0:
                if  self.macd.lines.histo[0] > self.macd.lines.histo[-4]:
                    tobuy = True

            if self.cross_up_bot[0] :
                #tobuy = True
                self.prepare_buy = 5
            """


            if self.cross_up_bot[0]:
                self.signal_price = self.data.close[0]
                self.signal_rsi = self.rsi.rsi[0]
                #tobuy = True
            else:
                if self.signal_price > 0:
                    # if self.signal_price < self.data.close[0]  and \\
                    """
                    if self.rsi.rsi[0] > self.signal_rsi +5:
                        tobuy = True
                        self.signal_price = -1
                        self.signal_rsi = -1
                    """
                    if self.data.close[0] > self.ma5.lines.sma[0] :
                        tobuy = True
                        self.signal_price = -1
                        self.signal_rsi = -1


            if tobuy:
                self.buy()
                self.buy_price = self.data.close[0]
                self.prepare_buy = -1
            if self.buy_price >0 and self.buy_price < self.data.close[0]:
                self.buy_price = self.data.close[0]
            #pass
        #if self.cross_up_mid[0] == True:
        #    self.buy()
        else:
            #if self.crossdown_top:
            #    self.close()
            if self.buy_price *0.9 > self.data.close[0] :
                self.close()
                self.buy_price = -1

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
property_show = False
class MACDS(StrategyLogger):
    def __init__(self, enddate=None):
        self.macd= bt.ind.MACDHisto()
        self.kd = bt.ind.StochasticFull()
        self.dmi = bt.ind.DirectionalMovement()
        self.roc = bt.ind.RateOfChange100()
        self.bband = bt.ind.BollingerBands()
        self.rsi = bt.ind.RelativeStrengthIndex()

        self.crossup = bt.ind.CrossUp(self.macd.macd, self.macd.signal)
        self.crossdown = bt.ind.CrossDown(self.macd.macd, self.macd.signal)
        #self.signal_add(bt.SIGNAL_LONG, self.cross_up_mid)
        #self.signal_add(bt.SIGNAL_SHORT, self.crossdown_top)
        self.enddate = self.params.enddate
        self.sell_k80 = False
        self.sell_kover = True
        self.buy_when_warm = True
        self.buy_when_trend = False
        self.buy_when_trend_roc = True
        global property_show
        if not property_show:
            print("sell if  k over 80:",self.sell_k80)
            print("sell if  k over :", self.sell_kover)
            print("sell if buy_when_warm  :", self.buy_when_warm)
            print("sell if buy_when_trend  :", self.buy_when_trend)
            print("sell if buy_when_trend_roc  :", self.buy_when_trend_roc)
            property_show = True


    def next(self):
        if not self.runtrade():return
        #if self.cross_up_mid[0]: print(self.cross_up_mid[0])
        if  not self.position:
            #if self.data.close >self.bb.mid[0] and self.data.close <self.bb.mid[-1]:

            tobuy = False
            if self.crossup: tobuy = True
            if self.buy_when_warm: tobuy  = False if self.kd.lines.percK[0] >  80 else tobuy
            if self.buy_when_trend: tobuy = tobuy if self.dmi.lines.adx[0] > 25 else False
            if self.buy_when_warm: tobuy = False if self.rsi.lines.rsi[0] > 70 else tobuy

            if tobuy:self.buy()
        else:

            if self.sell_kover:
                if self.kd.lines.percK[0] > 80 and self.kd.lines.percK[0] < self.kd.lines.percK[-2]  :
                    self.close()
                    return

            if self.sell_k80:
                if self.kd.lines.percK[0] > 80 :
                    self.close()
                    return

            if self.crossdown:
                self.close()

        pass

class KDS(StrategyLogger):
    def __init__(self, enddate=None):
        self.kds = bt.ind.StochasticFull(self.datas[0], period = 9, period_dfast= 3, period_dslow = 3)
        self.cci = bt.ind.CommodityChannelIndex()

        self.crossup = bt.ind.CrossUp(self.kds.lines.percK, self.kds.lines.percD)
        self.crossdown = bt.ind.CrossDown(self.kds.lines.percK, self.kds.lines.percD)
        self.enddate = self.params.enddate
        self.buy_only_if_cci_pass = True

    def next(self):
        if not self.runtrade():return
        if not self.position:
            #if self.data.close >self.bb.mid[0] and self.data.close <self.bb.mid[-1]:
            #if self.kds.k > self.kds.d:
            tobuy= False
            if self.crossup[0]:
                #print("up",self.crossup)
                tobuy= True
            if self.kds.lines.percK[0] >70:
                tobuy = False

            if self.cci.lines[0] <-50:
                tobuy = False

            if self.kds.lines.percK[0] <= self.kds.lines.percK[-2]:
                tobuy = False
            if tobuy:
                self.buy()
        else:
            #if self.kds.k < self.kds.d:
            if self.crossdown[0]:
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
        if not self.position :
            #if self.data.close >self.bb.mid[0] and self.data.close <self.bb.mid[-1]:
            #if self.kds.k > self.kds.d:
            if self.crossup and self.dmi.adx [0] >20:
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
"""
class BIAS(bt.ind.MovingAverageSimple):
    '''
    Non-weighted average of the last n periods

    Formula:
      - movav = Sum(data, period) / period

    See also:
      - http://en.wikipedia.org/wiki/Moving_average#Simple_moving_average
    '''
    alias = ('BIAS')
    lines = ('bias',)

    def __init__(self):
        # Before super to ensure mixins (right-hand side in subclassing)
        # can see the assignment operation and operate on the line
        self.lines[0] = Average(self.data, period=self.p.period)

        super(bt.ind.MovingAverageSimple, self).__init__()
        self.bias = 
"""