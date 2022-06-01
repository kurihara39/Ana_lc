# %%
today = 20220601
fac = 0.75

from colour import Color
red = Color('red')
blue = Color('blue')
# 5分割 [<Color red>, <Color yellow>, <Color lime>, <Color cyan>, <Color blue>]

from bin.module import *
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
from plotly.subplots import make_subplots

# %% [markdown]
# ### Function

# %%
def hardness(hard, soft):
    return (hard-soft)/(hard+soft)

# %%
def hardness2(hard, soft):
    hard += min(hard.min(), soft.min())
    soft += min(hard.min(), soft.min())
    return hard/soft

# %%
def get_hardness_error(hard, soft, hard_e, soft_e):
    denomi = hard
    nume = soft
    denomi_e = hard_e
    nume_e = soft_e
    return np.sqrt((denomi_e/denomi)**2 + (nume_e*nume/denomi**2)**2)

# %%
def detection(mtime0, mrate0, period = 10, padding = 50, factor = 3):
    
    thrs = factor * np.std(mrate0) + np.mean(mrate0)
    b_start=np.array([])
    b_end=np.array([])
    flag = True

    for i in range(padding, len(mtime0)-period-padding):
        ave = np.mean(mrate0[i:i+period])
        if flag == True:
            if ave > thrs:
                b_start=np.append(b_start,i-padding)
                flag = False
        if flag == False:
            if ave < np.std(mrate0) + np.mean(mrate0):
                b_end = np.append(b_end,i+padding)
                flag = True
    
    print(b_start)
    print(b_end)

    return b_start, b_end

# %%
def label_anomaly(tbl, target, yaml, padding=30):
    _tbl = tbl
    _tbl["MBURST0"] = "-1" 

    b_start, b_end = detection(_tbl["TIME"], _tbl["MRATE0"], padding=padding)
    # b_start, b_end = detection(_tbl["TIME"], _tbl["MRATE0"])

    outburst_num = len(b_end)
    # outburst_num = yaml[target]["M_outburst#"]

    for j in range(0, outburst_num):
        start = b_start[j]
        end = b_end[j]

        # start = yaml[target][f"M{j}_MJD"][0]
        # end =  yaml[target][f"M{j}_MJD"][1] 
        _tbl.loc[start:end,"MBURST0"] = f"{j}"
        # _tbl.loc[(_tbl["TIME"]>=start)&(_tbl["TIME"]<=end),"MBURST0"] = f"{j}"
        print(start)
        print(end)
    try:
        _tbl["SBURST0"] = "-1" 
        _tbl.loc[(_tbl["TIME"]>=start)&(_tbl["TIME"]<=end),"SBURST0"] = f"{j}"
    except KeyError:
        print("No Swift data")
    return _tbl

# %%
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

# %%
def tbl_hardness(tbl):
    _tbl = tbl
    _tbl["MHARDNESS"] = _tbl["MRATE1"]/_tbl["MRATE0"]
    _tbl["MHARDNESS_ERROR"] = get_hardness_error(_tbl["MRATE1"], _tbl["MRATE0"], _tbl["MERROR1"], _tbl["MERROR0"])
    _tbl.loc[_tbl["MRATE0"]<0, "MHARDNESS"] = np.nan
    _tbl.loc[_tbl["MRATE1"]<0, "MHARDNESS"] = np.nan
    _tbl.loc[_tbl["MRATE0"]<0, "MHARDNESS_ERROR"] = np.nan
    _tbl.loc[_tbl["MRATE1"]<0, "MHARDNESS_ERROR"] = np.nan

    return _tbl

# %%
def minimax(x):
    return (x - x.min())/(x.max()-x.min())

# %% [markdown]
# ### main

# %%
PATH_yaml = "/home/kurihara/2_lc_similarity/BATSURVEY/catalog/objects.yaml"
with open(PATH_yaml, 'r') as yml:
    b = yaml.safe_load(yml)


# %%
obj_list = pd.read_csv("/home/kurihara/2_lc_similarity/BATSURVEY/catalog/newest_list.csv")


# # %%
# fig = make_subplots(rows=len(obj_list), cols = 1, subplot_titles=obj_list.loc[:,"target"] )
# fig.update_layout(width = 1200, height = 3000)

# for num in range(0, 3):
# # for num in range(len(obj_list)):
#     target = obj_list.loc[num, "target"]
#     _tbl = label_anomaly(make_table0(target), target, b)
#     # _tbl = label_anomaly2(make_table0(target), target, b)
#     # _tbl = make_table0(target)

#     # tr = get_trace(_tbl["TIME"], _tbl["SRATE0"], _tbl["SERROR0"], c_num=6, s_num=2, name=f"{obj_list.loc[num,'target']}_S")
#     # fig.add_trace(tr, row=num+1, col=1)    

#     # tr = get_trace(_tbl["TIME"], _tbl["MRATE1"], _tbl["MERROR1"], c_num=1, s_num=0, name=f"{obj_list.loc[num,'target']}_Mh")
#     # fig.add_trace(tr, row=num+1, col=1)

#     tr = get_trace(_tbl["TIME"], _tbl["MRATE0"], _tbl["MERROR0"], c_num=3, s_num=1, name=f"{obj_list.loc[num,'target']}_Ms")
#     fig.add_trace(tr, row=num+1, col=1)

#     tr = get_trace(_tbl.loc[_tbl["MBURST0"]!=str(-1), "TIME"], _tbl.loc[_tbl["MBURST0"]!=str(-1), "MRATE0"], _tbl.loc[_tbl["MBURST0"]!=str(-1), "MERROR0"], c_num=8, s_num=4, name=f"{obj_list.loc[num,'target']}_Ms_burst")
#     fig.add_trace(tr, row=num+1, col=1)

# fig.show()
# # fig.write_html("/home/kurihara/2_lc_similarity/BATSURVEY/output/maxi/Analysis/20220510/burst_period_3.html")
# # fig.write_html("/home/kurihara/2_lc_similarity/BATSURVEY/output/maxi/Analysis/20220510/burst_period_DTW.html")


# %% [markdown]
# ### for hardness





# %%

fig = make_subplots(rows=len(obj_list), cols = 1, subplot_titles=obj_list.loc[:,"target"] )
fig.update_layout(width = 1600, height = 3200, title = "Positive counts (for Hardness ratio)")

for num in range(len(obj_list)):
    target = obj_list.loc[num, "target"]
    _tbl = tbl_hardness(label_anomaly(make_table0(target), target, b))
    # _tbl = label_anomaly2(make_table0(target), target, b)
    # _tbl = make_table0(target)

    # tr = get_trace(_tbl["TIME"], _tbl["SRATE0"], _tbl["SERROR0"], c_num=6, s_num=2, name=f"{obj_list.loc[num,'target']}_S")
    # fig.add_trace(tr, row=num+1, col=1)    

    # tr = get_trace(_tbl["TIME"], _tbl["MRATE1"], _tbl["MERROR1"], c_num=1, s_num=0, name=f"{obj_list.loc[num,'target']}_Mh")
    # fig.add_trace(tr, row=num+1, col=1)

    tr = get_trace(_tbl["TIME"], _tbl["MRATE0"], _tbl["MERROR0"], c_num=3, s_num=1, name=f"{obj_list.loc[num,'target']}_Ms")
    fig.add_trace(tr, row=num+1, col=1)

    tr = get_trace(_tbl.loc[_tbl["MHARDNESS"].isnull()==False, "TIME"], _tbl.loc[_tbl["MHARDNESS"].isnull()==False, "MRATE0"], _tbl.loc[_tbl["MHARDNESS"].isnull()==False, "MERROR0"], c_num=8, s_num=4, name=f"{obj_list.loc[num,'target']}_Ms_forHI")
    fig.add_trace(tr, row=num+1, col=1)

    trace_burst= go.Scattergl(
    x=_tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "TIME"],
    # error_x = dict(array=xe),
    y=_tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "MRATE0"],
    error_y=dict(array= _tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "MERROR0"]), 
    mode = "markers",
    marker=dict(color=minimax(_tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "TIME"]).values,
            colorscale="RdBu", showscale=True),
    name=f"{obj_list.loc[num,'target']}_M_forHI_>{fac}"
    )
    fig.add_trace(trace_burst, row=num+1, col=1)


    # tr = get_trace(_tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "TIME"], _tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "MRATE0"],
    #  _tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "MERROR0"], c_num=0, s_num=2, name=f"{obj_list.loc[num,'target']}_Ms_forHI_>{fac}")
    # fig.add_trace(tr, row=num+1, col=1)

fig.show()
fig.write_html(f"/home/kurihara/2_lc_similarity/BATSURVEY/output/maxi/Analysis/{today}/maxi_lc_positive_{fac}.html")
fig.write_html(f"/home/kurihara/2_lc_similarity/BATSURVEY/Ana_lc/{today}/maxi_lc_positive_{fac}.html")



# %%
# fac = 0.75
fig = make_subplots(rows=len(obj_list)//4 +1, cols = 4, subplot_titles=obj_list.loc[:,"target"] )
fig.update_layout(width = 3000, height = 5000, title = f"Hardness v.s. Intensity (>{fac} sigma)", template="presentation")
# fig.update_layout(width = 3000, height = 3000, title = "Hardness v.s. Intensity", showlegend=False)

# for num in range(4):
for num in range(len(obj_list)):
    target = obj_list.loc[num, "target"]
    _tbl = tbl_hardness(label_anomaly(make_table0(target), target, b))

    tr = get_trace(_tbl["MHARDNESS"], _tbl["INTENSITY"], _tbl["INT_ERROR"], c_num=8, s_num=4, name=f"{obj_list.loc[num,'target']}_M_HI")
    fig.add_trace(tr, row=(num)//4+1, col=(num)%4 +1)

    trace_burst= go.Scattergl(
        x=_tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "MHARDNESS"],
        # error_x = dict(array=xe),
        y=_tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "INTENSITY"],
        error_y=dict(array= _tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "INT_ERROR"]), 
        mode = "markers",
        marker=dict(color=minimax(_tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "TIME"]).values,
                colorscale="RdBu", showscale=True),
        name=f"{obj_list.loc[num,'target']}_M_HI_burst"
        )
    fig.add_trace(trace_burst, row=(num)//4+1, col=(num)%4 +1)

    # tr = get_trace(_tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "MHARDNESS"], _tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "INTENSITY"],
    #  _tbl.loc[(_tbl["MRATE0"]-_tbl["MRATE0"].mean())>fac*_tbl["MRATE0"].std(), "INT_ERROR"], c_num=8, s_num=2, name=f"{obj_list.loc[num,'target']}_M_HI_burst")
    # fig.add_trace(tr, row=(num)//4+1, col=(num)%4 +1)

    fig.update_yaxes(title='X-ray Intensity (counts/sm^2/sec)', ticks='inside', type="log")
    fig.update_xaxes(title='Hardness (MAXI hard & MAXI soft)', ticks='inside', type="log")

fig.show()
fig.write_html(f"/home/kurihara/2_lc_similarity/BATSURVEY/output/maxi/Analysis/{today}/HI_{fac}_color.html")
# fig.write_html(f"/home/kurihara/2_lc_similarity/BATSURVEY/output/maxi/Analysis/{today}/HI_{fac.replace(".","-")}.html")
fig.write_html(f"/home/kurihara/2_lc_similarity/BATSURVEY/Ana_lc/{today}/HI_{fac}_color.html")
# fig.write_html(f"/home/kurihara/2_lc_similarity/BATSURVEY/Ana_lc/{today}/HI_{fac.replace(".","-")}.html")




