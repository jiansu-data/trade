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

from strategy import *

output_dir = "output"
if not os.path.isdir(output_dir):
    os.mkdir(output_dir)


def test_stock(stock_id,result_show = False,strategy = BBS,plot = False,enable_log = False,
               fromdate=datetime(2019, 1, 1),todate=datetime(2019, 12, 31),taskname = None):
    from datetime import datetime
    import backtrader as bt
    import helper.datah5 as datah5
    import pandas as pd
    import numpy as np
    from datetime import datetime
    #print(stock_id)
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy)
    strategy.log_enable = enable_log
    datah5.cache_mode = True
    data0_df = datah5.datafromh5( stock_id=stock_id,fromdate=fromdate,todate=todate,ret_df = True)
    #print(data0_df)
    cerebro.adddata(bt.feeds.PandasData(dataname=data0_df))
    #cerebro.addsizer(bt.sizers.AllInSizer)
    #cerebro.addanalyzer(bt.analyzers.AnnualReturn)
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)
    cerebro.addanalyzer(bt.analyzers.Returns)
    cerebro.addanalyzer(bt.analyzers.PyFolio)
    global output_dir
    if not os.path.isdir(output_dir+"/"+taskname):
        os.mkdir(output_dir+"/"+taskname)
    if configs["save_result"]:
        fn = output_dir+"/"+taskname+"/"+"%s_writer.csv" %stock_id
        cerebro.addwriter(bt.WriterFile, csv=True,out=fn)
    strats = cerebro.run()
    result = {}
    for e in strats[0].analyzers:
        if result_show :print(type(e),e.get_analysis())
        result[type(e).__name__] = e.get_analysis()
    result['growth'] = data0_df.iloc[-1]['close']/data0_df.iloc[0]['close']
    if plot:cerebro.plot()

    return result

def db_attr(db,attr,f):
    l = {}
    for e in db:
        #print(e,db[e][attr])
        l[e] = f(db[e][attr])
    return l

def db_attrs(db,attr,f):
    df = pd.DataFrame()
    for e in db:
        #print(e,db[e][attr])
        df_ = pd.DataFrame(f(db[e][attr]))
        df_.rename(index={0:str(e),'Backtest':str(e)},inplace=True)
        df = pd.concat([df,df_])
    return df


def worker(q,oq,args):
    while(not q.empty()):
        stock = q.get()
        ret = test_stock(stock,**args)
        oq.put((stock,ret))
        print(stock)
    print("exit worker")


def ta_attr(x):
    ret = {}
    ret['total'] = [x['total']['total']] if 'total' in x else [0]
    ret['won'] = [x['won']['total']]  if 'won' in x else [0]
    ret['lost'] = [x['lost']['total']] if 'lost' in x else [0]
    ret['score'] = [float(ret['won'][0])/float(ret['total'][0])]
    return ret

def pyfolio_attr(x):
    import helper.perfstat as perfstat
    ret = perfstat.get_perf_stats(pd.Series(x['returns']))
    ret = ret.transpose()
    ret = ret.applymap(perfstat.stof)
    return ret

def timestamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def multi_stock_test():
    """
    for e in t50[0]:
        print(e)
        db[str(e)] = test_stock(str(e),strategy=st)
    """
    t50= pd.read_csv("data/tw50.csv",header=None)
    db = {}
    ps = []
    m = mp.Manager()
    q = m.JoinableQueue()
    oq = m.JoinableQueue()
    cpu = 10
    for e in t50[0]: q.put(str(e))
    for i in range(cpu):
        ps.append(mp.Process(target=worker, args=(q, oq)))
    for e in ps:e.start()
    # print("all start")
    for e in ps:e.join()
    # print("all done")

    while (not oq.empty()):
        (stock_id, ret) = oq.get()
        db[stock_id] = ret

    db_ta = db_attrs(db, 'TradeAnalyzer', ta_attr)
    # print("win rate:", (ar_sr>0).sum()/ar_sr.count())
    #print(db_ta)
    x = db_attrs(db, 'PyFolio', pyfolio_attr)
    #x = x.applymap(stof)
    db_df = pd.concat([x, db_ta], axis=1)
    db_df['growth'] = db["2317"]["growth"]
    print(db_df)
    db_df.to_csv( output_dir + "/" + taskname +"/"+"result.csv")

def single_stock_test():
    db = {}
    db["2317"] = test_stock("2317", result_show=True, plot=True, strategy=st)

    db_ta = db_attrs(db, 'TradeAnalyzer', ta_attr)
    # print(db_ta)
    x = db_attrs(db, 'PyFolio', pyfolio_attr)
    # print(x)
    db_df = pd.concat([x, db_ta], axis=1)
    db_df['growth'] = pd.Series(db_attr(db,'growth',lambda  x: x))

    print(db_df)
#config_file = "config.json"
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--cpu", help="the process number , 0 for default")
parser.add_argument("-f","--config", help="config file, default:config.json",default= "config.json",dest="config")
parser.add_argument("-t","--taskname", help="taskname")



args = parser.parse_args()
config_file = args.config
#method = ""

configs = json.load(open(config_file))
if args.cpu : configs['cpu'] = args.cpu
if args.taskname: configs['taskname'] = args.taskname
method = configs['mode']
if configs['strategy']  == "bb and":configs['strategy']  = BBS
if configs['strategy']  == "kd":configs['strategy']  = KDS
if configs['strategy']  == "macd":configs['strategy']  = MACDS
if configs['strategy']  == "rsi":configs['strategy']  = RSIS
if not configs['strategy']  :configs['strategy']  = BBS

taskname = configs["taskname"] or timestamp()

def datetime_from_string(string):
    return datetime(*list(map(lambda x: int(x), string.split("-"))))

if __name__ == "__main__":
    st = configs['strategy']

    if method == "one":
        db = {}
        sid = configs["stock_id"]
        enable_log = configs["enable_log"]

        db[sid] = test_stock(sid,result_show= True,plot = True,strategy=st,enable_log = True,taskname = taskname)

        db_ta  = db_attrs(db, 'TradeAnalyzer', ta_attr )
        #print(db_ta)
        x  = db_attrs(db, 'PyFolio', pyfolio_attr )
        #print(x)
        db_df =pd.concat([x,db_ta],axis = 1)
        db_df['growth'] = db[sid]["growth"]
        print(db_df)

    else:
        #multi_stock_test()
        taskname = configs["taskname"] or timestamp()
        t50 = pd.read_csv("data/tw50.csv", header=None)
        db = {}
        ps = []
        m = mp.Manager()
        q = m.JoinableQueue()
        oq = m.JoinableQueue()
        args = {"taskname":taskname, "fromdate":datetime_from_string(configs['fromdate']),"todate":datetime_from_string(configs['todate'])}
        cpu = configs["cpu"] or int(os.cpu_count() *3//4)
        for e in t50[0]: q.put(str(e))
        for i in range(cpu):ps.append(mp.Process(target=worker, args=(q, oq,args)))
        for e in ps:e.start()
        for e in ps:e.join()

        while (not oq.empty()):
            (stock_id, ret) = oq.get()
            db[stock_id] = ret

        db_ta = db_attrs(db, 'TradeAnalyzer', ta_attr)
        # print("win rate:", (ar_sr>0).sum()/ar_sr.count())
        # print(db_ta)
        x = db_attrs(db, 'PyFolio', pyfolio_attr)
        #x = x.applymap(stof)
        db_df = pd.concat([x, db_ta], axis=1)
        db_df['growth'] = pd.Series(db_attr(db, 'growth', lambda x: x))
        print(db_df)
        print("win rate:",db_df[db_df['Cumulative returns']>0]['Cumulative returns'].count()/db_df['Cumulative returns'].count())
        #db_df.to_csv(tasktime+".csv")
        #global tasktimestamp
        db_df.to_csv( output_dir + "/" + taskname +"/"+"result.csv")