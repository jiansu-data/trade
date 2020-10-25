import helper.datah5 as datah5
import datetime
if __name__ == "__main__":
    print("u:update hloc, c:create hloc  s : create sanda i: update sanda  ")
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
