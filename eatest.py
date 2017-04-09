# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 05:54:35 2016

@author: Maxwell-Ampere
"""

import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
from thorlabs import FW102C
from keithley import K2400
import scipy.constants as PC


rm = visa.ResourceManager()


mon = eqe.get_mono(rm)
lia = eqe.get_lia(rm)
fwi = ac.getInstr(rm, "FilterWheel")
fw = FW102C(fwi)
smui = ac.getInstr(rm, "LasPow")
smu = K2400(smui)
tmp = ac.json_load("local.json")
fw.filters = np.array(tmp['FilterWheel']['filters'], dtype=np.float64)
tia = eqe.get_tia(rm)
tia.freq = 389.

smu.set_current(0.)
smu.output = True

lia.preamps = np.array([tia])
lia.auto_dewll = True
lia.auto_scale = True
lia.tol_abs = np.array([5e-15])
lia.tol_rel = np.array([5e-7])
lia.tol_maxsettle = 60.



mon.wavelength = 873.24
lia.time_constant = 5.
lia.slope = 24
sleep(lia.wait_time)
lia.system_auto_phase(0)
sleep(lia.wait_time)
lia.system_auto_phase(0)

mon.wavelength = 835
mon.wavelength = 873.24
tmp = lia.noise_measure(10e-3, 5., 12, 24)
tmpM = smu.measure[0]

lia.noise_ratio = tmp[0, 1]/tmpM


tmp = lia.noise_measure(10e-3, 10e-3, 12, 12)
lia.noise_base = tmp[0, 1]

lia.waittimes.mask = ((np.atleast_2d(lia.tcons).T < 1e-2)+ 
                      (np.atleast_2d(lia.slopes) < 12)) > 0
lia.enbws.mask = lia.waittimes.mask

tia.adc = lambda: np.abs((smu.measure)[0])


hc = PC.h*PC.c/PC.e*1e9


def meas():
    scaled = True
    dwelled = True
    dcvals = []
    while (scaled or dwelled):
        dcvals = []
        scaled = lia.update_scale(lia.last_mags)
        dwelled = lia.update_timeconstant(np.array([(smu.measure)[0]*(tia.sensitivity)]))
        t0 = time()
        while (time()-t0) < lia.wait_time:
            dcvals.append((smu.measure)[0])
        tmp0 = np.array([np.abs(np.hstack((lia.cmags, lia.noise_ratio*smu.measure[0]*(tia.sensitivity)*np.sqrt(lia.enbw), lia.noise_base*np.sqrt(lia.enbw)))).max()])
        tmp1 = lia.last_mags
        if np.any(np.abs(1.-tmp0/tmp1) > 0.5):
            scaled = True
        lia.last_mags = np.array([np.abs(np.hstack((lia.cmags, lia.noise_ratio*smu.measure[0]*(tia.sensitivity)*np.sqrt(lia.enbw), lia.noise_base*np.sqrt(lia.enbw)))).max()])
    msr0 = lia.cmeas
    dcvals = np.array(dcvals)
    msr2 = dcvals.mean()
    return np.hstack((msr0[:2], msr2, msr0[0]/msr2))
    
    
def meas2():
    dcvals = []
    t0 = time()
    while (time()-t0) < lia.wait_time:
        dcvals.append((smu.measure)[0]*(tia.sensitivity))
    msr0 = lia.cmeas
    dcvals = np.array(dcvals)
    msr2 = dcvals.mean()
    return np.hstack((msr0[:2], msr2, msr0[0]/msr2))

svepth = "G:/2016-08-15/"
p = ac.DynamicPlot()

es = np.arange(3.1, 3.7, 0.01)
dta = np.zeros((es.size, 4))

mon.wavelength = hc/es[0]
fw.position = 6

p.addnew()
k0 = 18
for k, e in enumerate(es[k0:]):
    mon.wavelength = hc/e
    if hc/e < 1.02*fw.current_filter_off and not np.isnan(fw.current_filter_off):
        if fw.position == 1:
            fw.position = 6
        else:
            fw.position = fw.position-1
    dta[k+k0, :] = meas()
    p.update(e, np.sqrt(2.)*dta[k+k0, -1])
    np.savez_compressed(svepth+"eatstSi.npz", es, dta)
    
plt.plot(es, np.rad2deg(np.arctan2(dta[:, 1], dta[:, 0])))