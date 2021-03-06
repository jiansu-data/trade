from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys
import copy
from backtrader import Analyzer
from backtrader.utils import AutoOrderedDict, AutoDict
from backtrader.utils.py3 import MAXINT

class TradeAnalyzerPercentage(Analyzer):

    def create_analysis(self):
        self.rets = AutoOrderedDict()
        self.rets.total.total = 0
        #self.rets.trades = []
        self.rets.eval_static.profit = 0
        self.rets.eval_static.profit_comm = 0
        self.rets.trade_cals = []
        self._maxvalue = 0
        self.mdd = 0
    def stop(self):
        super(TradeAnalyzerPercentage, self).stop()
        self.rets._close()
        #print("stop===============")
        #for i,e in enumerate(self.trades):
        #    print(i, e, "\n")

    def notify_trade(self, trade):
        if trade.justopened:
            self._maxvalue = trade.price

        elif trade.status == trade.Closed:
            self._maxvalue = 0

        if trade.justopened:
            # Trade just opened
            self.rets.total.total += 1
            self.rets.total.open += 1

        elif trade.status == trade.Closed:
            #self.rets.trades.append(copy.copy(trade))
            trades = self.rets
            trade_cal = {}
            """
            """
            #trade_cal  = AutoDict()
            trade_cal['profit'] = trade.pnl/trade.price
            trade_cal['profit_comm'] = trade.pnlcomm/trade.price
            trade_cal['barlen'] = trade.barlen
            trade_cal['price'] = trade.price
            self.rets.trade_cals.append(trade_cal)

            self.rets.eval_static.profit  += trade_cal['profit']
            self.rets.eval_static.profit_comm += trade_cal['profit_comm']


            res = AutoDict()
            # Trade just closed
            #print(trade)
            won = res.won = int(trade.pnlcomm >= 0.0)
            lost = res.lost = int(not won)
            tlong = res.tlong = trade.long
            tshort = res.tshort = not trade.long

            trades.total.open -= 1
            trades.total.closed += 1

            # Streak
            for wlname in ['won', 'lost']:
                wl = res[wlname]

                trades.streak[wlname].current *= wl
                trades.streak[wlname].current += wl

                ls = trades.streak[wlname].longest or 0
                trades.streak[wlname].longest = \
                    max(ls, trades.streak[wlname].current)

            trpnl = trades.pnl
            trpnl.gross.total += trade.pnl
            trpnl.gross.average = trades.pnl.gross.total / trades.total.closed
            trpnl.net.total += trade.pnlcomm
            trpnl.net.average = trades.pnl.net.total / trades.total.closed

            # Won/Lost statistics
            for wlname in ['won', 'lost']:
                wl = res[wlname]
                trwl = trades[wlname]

                trwl.total += wl  # won.total / lost.total

                trwlpnl = trwl.pnl
                pnlcomm = trade.pnlcomm * wl

                trwlpnl.total += pnlcomm
                trwlpnl.average = trwlpnl.total / (trwl.total or 1.0)

                wm = trwlpnl.max or 0.0
                func = max if wlname == 'won' else min
                trwlpnl.max = func(wm, pnlcomm)

            # Long/Short statistics
            for tname in ['long', 'short']:
                trls = trades[tname]
                ls = res['t' + tname]

                trls.total += ls  # long.total / short.total
                trls.pnl.total += trade.pnlcomm * ls
                trls.pnl.average = trls.pnl.total / (trls.total or 1.0)

                for wlname in ['won', 'lost']:
                    wl = res[wlname]
                    pnlcomm = trade.pnlcomm * wl * ls

                    trls[wlname] += wl * ls  # long.won / short.won

                    trls.pnl[wlname].total += pnlcomm
                    trls.pnl[wlname].average = \
                        trls.pnl[wlname].total / (trls[wlname] or 1.0)

                    wm = trls.pnl[wlname].max or 0.0
                    func = max if wlname == 'won' else min
                    trls.pnl[wlname].max = func(wm, pnlcomm)

            # Length
            trades.len.total += trade.barlen
            trades.len.average = trades.len.total / trades.total.closed
            ml = trades.len.max or 0
            trades.len.max = max(ml, trade.barlen)

            ml = trades.len.min or MAXINT
            trades.len.min = min(ml, trade.barlen)

            # Length Won/Lost
            for wlname in ['won', 'lost']:
                trwl = trades.len[wlname]
                wl = res[wlname]

                trwl.total += trade.barlen * wl
                trwl.average = trwl.total / (trades[wlname].total or 1.0)

                m = trwl.max or 0
                trwl.max = max(m, trade.barlen * wl)
                if trade.barlen * wl:
                    m = trwl.min or MAXINT
                    trwl.min = min(m, trade.barlen * wl)

            # Length Long/Short
            for lsname in ['long', 'short']:
                trls = trades.len[lsname]  # trades.len.long
                ls = res['t' + lsname]  # tlong/tshort

                barlen = trade.barlen * ls

                trls.total += barlen  # trades.len.long.total
                total_ls = trades[lsname].total   # trades.long.total
                trls.average = trls.total / (total_ls or 1.0)

                # max/min
                m = trls.max or 0
                trls.max = max(m, barlen)
                m = trls.min or MAXINT
                trls.min = min(m, barlen or m)

                for wlname in ['won', 'lost']:
                    wl = res[wlname]  # won/lost

                    barlen2 = trade.barlen * ls * wl

                    trls_wl = trls[wlname]  # trades.len.long.won
                    trls_wl.total += barlen2  # trades.len.long.won.total

                    trls_wl.average = \
                        trls_wl.total / (trades[lsname][wlname] or 1.0)

                    # max/min
                    m = trls_wl.max or 0
                    trls_wl.max = max(m, barlen2)
                    m = trls_wl.min or MAXINT
                    trls_wl.min = min(m, barlen2 or m)
    def next(self):
        r = self.rets
        if self.strategy.position:
            #print(self._maxvalue,self.data[0],self.mdd)
            cur_price = self.data[0]
            if cur_price > self._maxvalue:
                self._maxvalue = cur_price
            else:
                drawdown = (cur_price - self._maxvalue )/self._maxvalue
                #print(self._maxvalue, self.data[0], self.mdd,drawdown)
                if drawdown <self.mdd :
                    self.mdd = drawdown
                    r.mdd = self.mdd
"""

class MDDPercentage(Analyzer):

    def create_analysis(self):
        self.rets = AutoOrderedDict()
        self._maxvalue = 0
        self.mdd = 0

    def stop(self):
        super(MDDPercentage, self).stop()
        self.rets._close()
        #print("max drawdown ", self.mdd)

    def notify_trade(self, trade):
        if trade.justopened:
            self._maxvalue = trade.price

        elif trade.status == trade.Closed:
            self._maxvalue = 0
            pass

    def next(self):
        r = self.rets
        if self.strategy.position:
            #print(self._maxvalue,self.data[0],self.mdd)
            cur_price = self.data[0]
            if cur_price > self._maxvalue:
                self._maxvalue = cur_price
            else:
                drawdown = (cur_price - self._maxvalue )/self._maxvalue
                print(self._maxvalue, self.data[0], self.mdd,drawdown)
                if drawdown <self.mdd :
                    self.mdd = drawdown
                    r.mdd = self.mdd
"""