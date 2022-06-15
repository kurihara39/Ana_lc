today=20220603

import numpy as np
from scipy import interpolate

from scipy.spatial.distance import euclidean
from fastdtw import fastdtw

import astropy.io.fits as pyfits
import matplotlib.pyplot as plt
import pandas as pd
import math

import yaml

import os,sys,glob,re, argparse
import pandas as pd
import astropy.io.fits as pyfits
from astropy.time import Time
import matplotlib.pyplot as plt
from plotly.offline import init_notebook_mode, iplot_mpl
import plotly.graph_objects as go
import plotly.offline as offline

from bin.module import get_trace


PATH_yaml = "/home/kurihara/2_lc_similarity/BATSURVEY/catalog/objects.yaml"

with open(PATH_yaml, 'r') as yml:
    b = yaml.safe_load(yml)



#####################################
# Swift web data
#####################################

obj_list = pd.read_csv("/home/kurihara/2_lc_similarity/BATSURVEY/catalog/newest_list.csv")

def bin_day_mfits(fits, extname):
    data=fits[extname].data
    # print(data.columns)
    time0= 0.5*(data["START"]+data["STOP"])
    rate0=data["RATE"]
    error0=data["ERROR"]
    
    #sort
    new = np.argsort(time0)
    time0=time0[new]
    rate0=rate0[new]
    error0=error0[new]

    time = np.array([])
    rate = np.array([]) 
    error = np.array([]) 
    
    i = 0
    a = math.floor(time0[0])
    
    for a in range(math.floor(time0[0]), math.floor(time0[-1])):
        store_r = np.array([])
        store_e = np.array([])
 #       print(store_r)
        #欠損用flag
        flag = 0
        while math.floor(time0[i]) == a:
            flag = 1.0
            store_r = np.append(store_r, rate0[i])
            store_e = np.append(store_e, error0[i])
            i += 1

        if flag == 1:
            time = np.append(time, a)
            rate = np.append(rate, np.mean(store_r))
            error = np.append(error, np.sqrt(np.mean(store_e**2)/store_e.size))
#        else:
#            print("{0}に欠損あり".format(a))
            
    return time, rate, error


def read_slink(link):
    _sfits = pyfits.open(link)
    _sdata = _sfits[1].data
    # print(_sdata.columns)
    _stime = _sdata['TIME'] 
    _srate = _sdata['RATE']
    _serror = _sdata['ERROR']
    return _stime, _srate, _serror

def hardness(hard, soft):
    return (hard-soft)/(hard+soft)

def hardness2(hard, soft):
    hard += min(hard.min(), soft.min())
    soft += min(hard.min(), soft.min())
    return hard/soft

def get_hardness2_error(hard, soft, hard_e, soft_e):
    denomi = hard
    nume = soft
    denomi_e = hard_e
    nume_e = soft_e
    return np.sqrt((denomi_e/denomi)**2 + (nume_e*nume/denomi**2)**2)

def make_table(target, PATH_maxifits = "/home/kurihara/2_lc_similarity/BATSURVEY/output/maxi/RawData"):
    print(target)

    #MAXI
    try:
        mfits = pyfits.open(f"{PATH_maxifits}/{target}/{target}_gsc.flc.gz")
    except FileNotFoundError:
        mfits = pyfits.open(f"{PATH_maxifits}/{target}/{target}_rev_gsc.flc.gz")
        
    mtime0, mrate0, merror0 = bin_day_mfits(mfits, "SCANLC0")
    mtime1, mrate1, merror1 = bin_day_mfits(mfits, "SCANLC1")

    mdf0 = pd.DataFrame([mtime0, mrate0, merror0]).T
    mdf1 = pd.DataFrame([mtime1, mrate1, merror1]).T
    header0 = ["TIME", "MRATE0", "MERROR0"]
    header1 = ["TIME", "MRATE1", "MERROR1"]

    mdf0.columns = header0
    mdf1.columns = header1

    mdf = pd.merge(mdf0, mdf1, on = "TIME")

    mdf["INTENSITY"] = mdf["MRATE0"] + mdf["MRATE1"]
    mdf["INT_ERROR"] = mdf["MERROR0"] + mdf["MERROR1"]

    # mdf["MHARDNESS"] = hardness2(mdf["MRATE1"]/mdf["MRATE1"].std(), mdf["MRATE0"]/mdf["MRATE0"].std())
    # mdf["MHARDNESS_ERROR"] = get_hardness2_error(mdf["MRATE1"]/mdf["MRATE1"].std(),
    #                                     mdf["MRATE0"]/mdf["MRATE0"].std(), 
    #                                        mdf["MERROR1"]/mdf["MRATE1"].std(),                                         
    #                                       mdf["MERROR0"]/mdf["MRATE0"].std())


    #Swift
    slink = obj_list[obj_list["target"]==target]["Swift_link"].values[0]
    

    try:
        stime, srate, serror = read_slink(slink)
        sdf = pd.DataFrame([stime, srate, serror]).T
        header = ["TIME", "SRATE0", "SERROR0"]
        sdf.columns = header    
        
        #merge
        _df = pd.merge(mdf, sdf, on = "TIME", how="outer")

        #
        # # print(_df.MRATE0.quantile(0.01))
        # _df = _df.query('MRATE0 > @_df.MRATE0.quantile(0.01)')    
        # _df = _df.query('MRATE1 > @_df.MRATE1.quantile(0.01)')  

        # _df["MHARDNESS2"] = hardness2(_df["MRATE1"]/_df["MRATE1"].std(), _df["MRATE0"]/_df["MRATE0"].std())
        # _df["MHARDNESS2_ERROR"] = get_hardness2_error(_df["MRATE1"]/_df["MRATE1"].std(),
        #                                 _df["MRATE0"]/_df["MRATE0"].std(), 
        #                                    _df["MERROR1"]/_df["MRATE1"].std(),                                         
        #                                   _df["MERROR0"]/_df["MRATE0"].std())          
        
    except OSError:
        print("No Swift data")
        mdf["SRATE0"] = 0
        mdf["SERROR0"] = 0
        _df = mdf

        # _df = _df.query('MRATE0 > @_df.MRATE0.quantile(0.01)')    
        # _df = _df.query('MRATE1 > @_df.MRATE1.quantile(0.01)')  

        # _df["MHARDNESS2"] = hardness2(_df["MRATE1"]/_df["MRATE1"].std(), _df["MRATE0"]/_df["MRATE0"].std())
        # _df["MHARDNESS2_ERROR"] = get_hardness2_error(_df["MRATE1"]/_df["MRATE1"].std(),
        #                                 _df["MRATE0"]/_df["MRATE0"].std(), 
        #                                    _df["MERROR1"]/_df["MRATE1"].std(),                                         
        #                                   _df["MERROR0"]/_df["MRATE0"].std())          


    return _df
    
def label_anomaly2(tbl, target, yaml):
    _tbl = tbl
    _tbl["MBURST0"] = "-1" 
    outburst_num = yaml[target]["M_outburst#"]

    for j in range(0, outburst_num):
        start = yaml[target][f"M{j}_MJD"][0]
        end =  yaml[target][f"M{j}_MJD"][1] 
        _tbl.loc[(_tbl["TIME"]>=start)&(_tbl["TIME"]<=end),"MBURST0"] = f"{j}"
        print(start)
        print(end)
    try:
        _tbl["SBURST0"] = "-1" 
        _tbl.loc[(_tbl["TIME"]>=start)&(_tbl["TIME"]<=end),"SBURST0"] = f"{j}"
    except KeyError:
        print("No Swift data")
    return _tbl


### main

PATH_savedata = f"/data01/kurihara/Data/swift/lc_{today}"

for num in range(0, len(b)): 
    target = obj_list.loc[num, "target"]
    _tbl = make_table(target)
    # _tbl = label_anomaly2(make_table(target), target, b)

    os.makedirs(f"{PATH_savedata}/{target}/web", exist_ok=True)
    _tbl.to_csv(f"{PATH_savedata}/{target}/web/lc_web_{target}.csv", index=None)
    print(f"file saved at {PATH_savedata}/{target}/web/lc_web_{target}.csv")

## END OF Swift web data
#####################################
#####################################

#####################################
# Swift batsurvey data
#####################################

from bin.module import get_trace

PATH_yaml = "/home/kurihara/2_lc_similarity/BATSURVEY/catalog/objects.yaml"

with open(PATH_yaml, 'r') as yml:
    b = yaml.safe_load(yml)

obj_list = pd.read_csv("/home/kurihara/2_lc_similarity/BATSURVEY/catalog/miki_catalog_comma.csv")
# obj_list = pd.read_csv("/home/kurihara/2_lc_similarity/BATSURVEY/catalog/newest_list.csv")

swift_to_gps=662342413.000

def get_df(catnum, PATH_survey):
    npz_list=sorted(glob.glob(os.path.join(PATH_survey, f"*_{catnum}-1.npy")))
    print(len(npz_list), "files found")
    
    time        = []
    time_stop   = []
    rate        = []
    rate_err    = []
    exposure    = []
    ngoodpix    = []
    pcoder      = []
    
    for i in range(0, len(npz_list)):
        try:
            data0 = np.load(npz_list[i])[0]
            time.append(data0[0])        
            time_stop.append(data0[1])
            rate.append(data0[2])
            rate_err.append(data0[3])
            exposure.append(data0[4])
            ngoodpix.append(data0[5])
            pcoder.append(data0[6])
    
        except IndexError:
            print(f"no data in {os.path.basename(npz_list[i])}")


    # print(time     )
    # print(time_stop)
    # print(rate     )
    # print(rate_err )
    # print(exposure )
    # print(ngoodpix )
    # print(pcoder   )

    df = pd.DataFrame([])

    df["TIME"] = time     
    df["TIME_STOP"] = time_stop
    df["SRATE0"] = rate     
    df["SERROR0"] = rate_err 
    df["EXPOSURE"] = exposure 
    df["NGOODPIX"] = ngoodpix 
    df["PCODER"] = pcoder   

    return df

def bin_day_swift(time00, rate0, error0):
    #time conversion to mjd
    swift_to_gps=662342413.000
    time0 = Time(time00+swift_to_gps, format='gps').mjd  

    #sort
    new = np.argsort(time0)
    time0=time0[new]
    rate0=rate0[new]
    error0=error0[new]

    time = np.array([])
    rate = np.array([]) 
    error = np.array([]) 
    
    i = 0
    a = math.floor(time0[0])
    
    for a in range(math.floor(time0[0]), math.floor(time0[-1])):
        store_r = np.array([])
        store_e = np.array([])
 #       print(store_r)
        #欠損用flag
        flag = 0
        while math.floor(time0[i]) == a:
            flag = 1.0
            store_r = np.append(store_r, rate0[i])
            store_e = np.append(store_e, error0[i])
            i += 1

        if flag == 1:
            time = np.append(time, a)
            rate = np.append(rate, np.mean(store_r))
            error = np.append(error, np.sqrt(np.mean(store_e**2)/store_e.size))
#        else:
#            print("{0}に欠損あり".format(a))
            
    return time, rate, error

def main(catnum, PATH_survey, need_df = False):

    df0 = get_df(catnum, PATH_survey)
    # print(df0)
    x, y, ye = bin_day_swift(df0["TIME"], df0["SRATE0"], df0["SERROR0"])

    if need_df == True:
        return df0, x, y, ye
    else:
        return x, y, ye


## main

PATH_survey = "/home/kurihara/2_lc_similarity/BATSURVEY/output/swift/toki_batsurvey/lc_batsurvey_220603"

for i in range(0, len(obj_list["CATNUM"])):
    target = obj_list.loc[i,"#NAME"].replace("'", "")
    print(target)
    os.makedirs(f"{PATH_savedata}/{target}/bs", exist_ok=True)

    catnum = obj_list.loc[i,"CATNUM"]
    print(f"catnum: {catnum}")
    try:
        dff, x, y, ye =  main(catnum, PATH_survey, need_df = True)
        dff.to_csv(f"{PATH_savedata}/{target}/bs/lc_bs__unbinned_{target}.csv")

        dff = pd.DataFrame([])
        dff["TIME"] = x
        dff["SRATE0"] = y
        dff["SERROR0"] = ye
        dff.to_csv(f"{PATH_savedata}/{target}/bs/lc_bs_{target}.csv", index=None)

    except IndexError:
        print(f"no data for {target}")
