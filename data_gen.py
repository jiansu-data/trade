import helper.datah5 as datah5
import helper.wantgoo as wantgoo
import datetime
import pandas as pd
import numpy as np
import helper.data_clean as dc


if __name__ == "__main__":
    print("u:update hloc, c:create hloc  s : create sanda i: update sanda  q: quater report")
    print("m:month report")
    c = input("function :")
    if c == "s":
        datah5.build_sd_date("data/sanda.h5",datetime.datetime(2019,1,1),datetime.datetime(2020,10,1))
        #datah5.build_sd_date("data/sanda.h5",datetime.datetime(2019,1,1),datetime.datetime(2019,3,1))
    if c == "u":
        datah5.update_h5()

    if c == "c":
        pass

    if c == "i":
        datah5.update_sd("data/sanda.h5")

    if c == 'q':
        t50 = pd.read_csv("data/tw50_100.csv")
        #print(t50)
        w = wantgoo.wantgoo()
        df = pd.DataFrame()
        for e in t50['stock']:
        #for e in ["2881","2330",]:
        #if 1:
            #e = "6409"
            print(e)
            w.get_stock_page(e)
            df_ = w.get_quater_report()
            df_['STOCK']= [e]*df_.shape[0]
            df =pd.concat([df,df_])
            print(df)
            #break
        df.to_hdf("data/finance_quater.h5")
        df.to_excel("data/finance_quater.xls")

    if c == 'm':
        t50 = pd.read_csv("data/tw50_100.csv")
        #print(t50)
        w = wantgoo.wantgoo()
        df = pd.DataFrame()
        for e in t50['stock']:
        #for e in ["2881","2330",]:
        #if 1:
            #e = "6409"
            print(e)
            w.get_stock_page(e)
            try:
                df_ = w.get_table('每月營收')
            except:
                w.get_stock_page(e)
                df_ = w.get_table('每月營收')
            df_['STOCK']= [e]*df_.shape[0]
            df =pd.concat([df,df_])
            #print(df)
            #break
        for e in df.columns:
            if e != '年度/月份' and e != 'STOCK':
                #print(e)
                df = df.df_string_to_number(df, e, )
        df.to_hdf("data/finance_month.h5",key='s')
        df.to_excel("data/finance_month.xls")
