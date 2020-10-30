from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd


class wantgoo:
    def __init__(self, browser=None,chrome_path = None):
        if not browser:
            options = Options()
            options.add_argument("--disable-notifications")
            if chrome_path:
                browser = webdriver.Chrome(chrome_path, chrome_options=options)
            else:
                browser = webdriver.Chrome(chrome_options=options)
        self.browser = browser
        self.links = None
        self.support_link = ['利潤比率', '報酬率', '杜邦分析', '營運週轉能力', '固定資產週轉', '總資產週轉', '營運週轉天數',
                             '營業現金流對淨利比', '現金股利發放率', '負債佔資產比', '長期資金佔固定資產比', '流速動比率',
                             '利息保障倍數', '現金流量分析', '盈餘再投資比率', '毛利成長率', '營業利益成長率', '稅後淨利成長率', '每股淨值', '損益表', '資產負債表',
                             '股東權益', '現金流量表', '股利政策', '本益比', '股價淨值比', '每月營收', '每股盈餘','現金殖利率']

    def get_stock_page(self, stock):
        first_page = "https://www.wantgoo.com/stock/%s?searchType=stocks" % (stock)
        self.browser.get(first_page)
        time.sleep(5)
        self.get_links()

    def list_link(self, element):
        # print(element,element.get_attribute('textContent'))
        link = element.find_element_by_tag_name("a")
        # print(element.get_attribute('textContent'), "==>",link.get_attribute('href'))

        # print("exit link")
        # print({element.get_attribute('textContent'): link.get_attribute('href')})
        return {element.get_attribute('textContent'): link.get_attribute('href')}

    def get_links(self):
        chrome = self.browser
        _ = chrome.find_elements_by_class_name("sub-menu")
        _ = chrome.find_elements_by_class_name("index-menu")
        dict_link = {}
        # print(_[0].get_attribute('innerHTML').split("\n"))
        for e in _[0].find_elements_by_tag_name("li"):
            # print (e.get_attribute('innerHTML'))
            # print(e.text)
            link = e.find_element_by_tag_name('a').get_attribute('href')
            if link == "javascript:;":
                # print("nest")
                data = e.find_elements_by_tag_name('li')
                i = 0
                for data_ in data:
                    # print(i,data_.get_attribute('innerHTML'))
                    # print("text",e.text)
                    i = i + 1
                    if data_.find_elements_by_tag_name("li") == []:
                        # print(data_.get_attribute('innerHTML'))
                        dict_link.update(self.list_link(data_))
            else:
                # print("simple")
                dict_link.update(self.list_link(e))

            # print("["+e.find_element_by_tag_name('a').get_attribute('href')+"]")
            self.links = dict_link

            # print("=======")
        return dict_link

    def go_table(self, table):
        self.browser.get(self.links[table])

    def month_header(self, table):
        header = table.find_element_by_class_name("thd")
        # print(header.get_attribute('innerHTML'))
        hd_tr = header.find_elements_by_tag_name("tr")[1].find_elements_by_tag_name("th")
        hds = list(map(lambda x: (x.get_attribute('innerHTML')), hd_tr))
        hds.insert(0, '年度/月份')
        return hds

    def normal_header(self, table):
        header = table.find_element_by_class_name("thd")
        # print(header.get_attribute('innerHTML'))
        hd_tr = header.find_elements_by_tag_name("tr")[0].find_elements_by_tag_name("th")
        hds = list(map(lambda x: (x.get_attribute('innerHTML')), hd_tr))
        return hds

    def normal_header_org(self, table):
        # header = table.find_elements_by_class_name("trs")
        # print(table.text)
        # for e in header:print(e.text)
        # print(header.get_attribute('innerHTML'))
        # hd_tr = header.find_elements_by_tag_name("tr")[0].find_elements_by_tag_name("th")
        # hds = list(map(lambda x: (x.get_attribute('innerHTML')),hd_tr))
        hds = [
            '日期',
            '外資不含自營', '外資自營', '投信', '自營商自行買賣', '自營商避險', '總合',
            '外資持股 ', '投信持股 ', '自營商持股 ', '總合持股', '外資比重', '三大法人比重'

        ]
        return hds

    def header_th(self, table):
        header = table.find_elements_by_tag_name("thead")
        hds = []
        for e in header:
            if e.text == "": continue
            # print(e.text)
            hds.append(e.text)
        hds = table.find_element_by_tag_name("thead").text.split(" ")
        print(hds)
        return hds

    def _get_table(self, header, poster=None):
        # print(page)
        # table = chrome.find_element_by_class_name("br-trl")
        # table.get_attribute('innerHTML').split("\n")
        table = self.browser.find_element_by_tag_name("table")
        if  self.browser.find_elements_by_class_name("nodata"):
            print("no data")
            return None
        #print(table.get_attribute('innerHTML').split("\n"))

        # hd_tr.get_attribute('innerHTML')
        hds = header(table)
        body = table.find_element_by_tag_name("tbody")

        # print(body.get_attribute('innerHTML'))
        def get_line(tr):
            tds = tr.find_elements_by_tag_name("td")
            line_data = list(map(lambda x: x.get_attribute('innerHTML'), tds))
            return line_data

        lines = []
        for e in body.find_elements_by_tag_name("tr"):
            # print(e.get_attribute('innerHTML'))
            _ = get_line(e)
            # print(_)
            lines.append(_)
        # print(hds)
        # print(lines)
        df = pd.DataFrame(lines, columns=hds)
        if poster:
            df = poster(df)
        # df.index = df['年度/月份']
        return df

    def eps_poster(self, df):
        return df[~(df['年度/季別'] == '總計')]

    def get_table(self, table):
        if table not in self.support_link: return None
        header = self.normal_header
        poster = None
        self.go_table(table)
        if table == '每月營收': header = self.month_header
        if table == '每股盈餘': poster = self.eps_poster
        # if table == '股價淨值比':
        return self._get_table(header, poster)

    def __del__(self):
        #self.browser.close()
        pass

    def get_quater_report(self):
        quater_report = ['每股盈餘', '現金流量表', '損益表', '資產負債表', '每股淨值', '利潤比率', '報酬率', '杜邦分析', '流速動比率']
        #quater_report = ['每股盈餘','流速動比率']
        df = None
        for e in quater_report:
            print("get",e)
            df_ = self.get_table(e)
            if type(df_) == type(None):
                continue
            df_["年度/季別"] = df_["年度/季別"].apply(lambda x: x.replace(" ", ""))
            #print(df_)
            if type(df) == type(None):
                df = df_.copy()
            else:
                #print("df source",df)
                df = pd.merge(df,df_)
            #print("df_result,", df)
            time.sleep(1)
        df = df.rename(
            columns={'營業利益率%<br>(累計)': '營業利益率%(累計)', '稅前淨利率%<br>(累計)': '稅前淨利率%(累計)', '稅後淨利率%<br>(累計)': '稅後淨利率%(累計)'})

        return df


if __name__ == "__main__":
    w = wantgoo()
    w.get_stock_page('2330')
    df = w.get_table('現金殖利率')
    quater_report = ['每股盈餘','現金流量表','損益表','資產負債表','每股淨值','利潤比率','報酬率','杜邦分析','流速動比率']
    quater_report = [ '本益比', '股價淨值比','現金殖利率']
    #營運週轉能力,固定資產週轉,總資產週轉,營運週轉天數,營業現金流對淨利比  ,負債佔資產比', '長期資金佔固定資產比','毛利成長率', '營業利益成長率', '稅後淨利成長率'
    #股東權益
    print(df)