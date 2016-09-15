# -*- coding: utf-8 -*-
"""
Created on Sat Jun 11 06:48:40 2016

@author: Maxwell-Ampere
"""

import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
from srs import SR830
from thorlabs import FW102C, PM100D
import scipy.constants as PC
from scipy.interpolate import interp1d


plt.hold(False)

rm = visa.ResourceManager()

mon = eqe.get_mono(rm)
lia = eqe.get_lia(rm)
tia = eqe.get_tia(rm)
slii = ac.getInstr(rm, "SRSLockin")
sli = SR830(slii)
fwi = ac.getInstr(rm, "FilterWheel")
fw = FW102C(fwi)
tmp = ac.json_load("local.json")
fw.filters = np.array(tmp['FilterWheel']['filters'], dtype=np.float64)
pmi = ac.getInstr(rm, "PowMeter")
pm = PM100D(pmi)

sli.preamps = np.array([None])
lia.preamps = np.array([tia])
tia.current_freq = lia.freq

def adc():
    ms0 = (lia.cmeas)[-2]
    sleep(0.1)
    ms1 = (lia.cmeas)[-2]
    while ms1 < ms0:
        ms0 = ms1
        sleep(0.1)
        ms1 = (lia.cmeas)[-2]
    return ms1

tia.adc = adc
tia.ovrld = lambda: not lia.ioread(4)
lia.waittimes.mask = ((np.atleast_2d(lia.tcons).T < 30e-3)+ 
                      (np.atleast_2d(lia.slopes) < 12)) > 0
lia.enbws.mask = lia.waittimes.mask
sli.waittimes.mask = ((np.atleast_2d(sli.tcons).T < 5./lia.freq)+ 
                      (np.atleast_2d(sli.slopes) < 12)) > 0
sli.enbws.mask = sli.waittimes.mask

tia.sensitivity = 100e-6
svepth = "G:/2016-08-14/"#test1.npz"

lia.ac_auto_gain = False

tmp = np.genfromtxt("./21927.csv", delimiter=',')
SiR = interp1d(tmp[:, 0], tmp[:, 1], bounds_error=False, kind='cubic')
tmp = np.genfromtxt("./12169.csv", delimiter=',', skip_header=1)
GeR = interp1d(tmp[:, 0], tmp[:, 1], bounds_error=False, kind='cubic')

mon.grating = 2
mon.wavelength = 1064
fw.position = 4
while not np.isnan(tia.inc_sensitivity):
    tia.sensitivity = tia.inc_sensitivity
lia.time_constant = 5.
lia.slope = 24
#sli.time_constant = 3.
#sli.slope = 24
wtme = np.array([lia.wait_time, sli.wait_time]).max()
sleep(wtme)
lia.system_auto_phase(0)
#sli.system_auto_phase(0)
sleep(wtme)
lia.system_auto_phase(0)
#sli.system_auto_phase(0)
tia.phases = np.nan*tia.phases
tia.phase_shift = lia.phaseoff[0]

lia.time_constant = 100e-3
sli.time_constant = 100e-3

tmp = lia.noise_measure(10e-3, 1., 6, 24)
lia.noise_ratio = tmp[:, 1]/tmp[:, 0]
tmp = sli.noise_measure(3e-3, 1., 6, 24)
sli.noise_ratio = tmp[:, 1]/tmp[:, 0]

while not np.isnan(tia.inc_sensitivity):
    tia.sensitivity = tia.inc_sensitivity
    
# Autoscale
tmp = lia.noise_measure(10e-3, 10e-3, 12, 12)
lia.noise_base = tmp[:, 1]
tmp = sli.noise_measure(10e-3, 10e-3, 12, 12)
sli.noise_base = tmp[:, 1]



tia.sensitivity = 100e-6
lia.sensitivity = (0, 1.)
sli.sensitivity = (0, 1.)
lia.time_constant = 20e-3
sli.time_constant = 30e-3
lia.slope = 12
sli.slope = 12

np.savez_compressed(svepth+"genoise", lia.noise_ratio, lia.noise_base, 
                    sli.noise_ratio, sli.noise_base)

             
mon.wavelength = 1200

tmp = np.load(svepth+"sinoise.npz")

lia.noise_ratio = tmp['arr_0']
lia.noise_base = tmp['arr_1']
sli.noise_ratio = tmp['arr_2']
sli.noise_base = tmp['arr_3']

sli.tol_abs = np.array([2e-4])
sli.tol_rel = np.array([5e-3])
sli.sensitivity = (0, 1.)

lia.tol_abs = np.array([10e-15]) # , 3e-6])
lia.tol_rel = np.array([5e-3]) # , 5e-3])
lia.tol_maxsettle = 40.
sli.tol_maxsettle = 40.

sli.auto_dwell = True
sli.auto_scale = True
lia.auto_dwell = True
lia.auto_phase = True
lia.auto_scale = True


def meas():
    scaled = True
    dwelled = True
    pmcurs = []
    while (scaled or dwelled):
        pmcurs = []
        lwt = lia.wait_time
        swt = sli.wait_time
        scaled = lia.update_scale(lia.last_mags) or sli.update_scale(sli.last_mags)
        dwelled = lia.update_timeconstant(lia.last_mags) or sli.update_timeconstant(sli.last_mags)
        if lia.wait_time > lwt and sli.wait_time > swt:
            dwelled = True
        else:
            dwelled = False
        wtmes = np.array([lia.wait_time, sli.wait_time])
        if lia.wait_time < wtmes.max():
            tc, slope, wt = lia.best_tc_for_wait(wtmes.max())
            if wt > lia.wait_time:
                lia.time_constant = tc
                lia.slope = slope
        if sli.wait_time < wtmes.max():
            tc, slope, wt = sli.best_tc_for_wait(wtmes.max())
            if wt > sli.wait_time:
                sli.time_constant = tc
                sli.slope = slope
        
        t0 = time()
        while (time()-t0) < wtmes.max():
            pmcurs.append(pm.current)
        tmp0 = np.hstack((lia.cmags, sli.cmags))
        tmp1 = np.hstack((lia.last_mags, sli.last_mags))
        if np.any(np.abs(1.-tmp0/tmp1) > 0.5):
            scaled = True
        lia.last_mags = lia.cmags
        sli.last_mags = sli.cmags
    msr0 = lia.cmeas
    msr1 = sli.cmeas
    pmcurs = np.array(pmcurs)
    msr2 = np.array([pmcurs.mean(), pmcurs.std()])
    return np.hstack((msr0[:2], msr1[:2], msr2))
    

def meas2():
    scaled = True
    dwelled = True
    pmcurs = []
    while (scaled or dwelled):
        pmcurs = []
        scaled = lia.update_scale(lia.last_mags)
        lwt = lia.wait_time
        dwelled = lia.update_timeconstant(lia.last_mags)
        if lia.wait_time > lwt:
            dwelled = True
        else:
            dwelled = False
        t0 = time()
        while (time()-t0) < lia.wait_time:
            pmcurs.append(pm.current)
        tmp0 = lia.cmags
        tmp1 = lia.last_mags
        if np.any(np.abs(1.-tmp0/tmp1) > 0.5):
            scaled = True
        lia.last_mags = lia.cmags
    msr0 = lia.cmeas
    pmcurs = np.array(pmcurs)
    msr2 = np.array([pmcurs.mean(), pmcurs.std()])
    return np.hstack((msr0[:2], [0., 0.], msr2))
    
    
mon.wavelength = 400
mon.grating = 1
fw.position = 6

lia.last_mags = lia.cmags
sli.last_mags = sli.cmags

lam = np.arange(400, 1105, 5)
meass = np.zeros((lam.size, 6))
uslta = sli.tol_abs
sslta = np.array([1.])

mon.grating = 1
mon.wavelength = 400
fw.position = 6

lia.last_mags = lia.cmags
sli.last_mags = sli.cmags

svepth = "G:/2016-08-14/"
resp = np.zeros((lam.size, 3))
hc = PC.h*PC.c/PC.e*1e9
p = ac.DynamicPlot(ptype="semilogy")
k0 = 0
for k, l in enumerate(lam[k0:]):
    mon.wavelength = l
    if l == 1000:
        mon.grating = 2
    if l > fw.next_filter_on*1.02:
        if fw.position == 6:
            fw.position = 1
        else:
            fw.position = fw.position + 1
    meass[k+k0, :] = meas()
    phc = float(l)*meass[k, 0]/(SiR([l])[0]*hc)
    p.update(l, phc)
    resp[k+k0, :] = np.hstack(([phc], meass[k+k0, [2, 4]]/phc))
    np.savez_compressed(svepth+"calmeasSi", lam, meass, resp)
    
for k, l in enumerate(lam):
    phc = float(l)*meass[k, 0]/(SiR([l])[0]*hc)
    resp[k, :] = np.hstack(([phc], meass[k, [2, 4]]/phc))
tia.phases = np.nan*tia.phases


mon.wavelength = 780
mon.grating = 1
fw.position = 2

lia.last_mags = lia.cmags
sli.last_mags = sli.cmags

lamGe = np.arange(780, 1805, 5)
meassGe = np.zeros((lamGe.size, 6))
uslta = sli.tol_abs
sslta = np.array([1.])

respGe = np.zeros((lamGe.size, 3))
#p = ac.DynamicPlot(ptype="semilogy")
p.addnew()
k0 = 202
for k, l in enumerate(lamGe[k0:]):
    mon.wavelength = l
    if l == 1000:
        mon.grating = 2
    if l > fw.next_filter_on*1.02:
        if fw.position == 6:
            fw.position = 1
        else:
            fw.position = fw.position + 1
    meassGe[k+k0, :] = meas()
    phc = float(l)*meassGe[k+k0, 0]/(GeR([l])[0]*hc)
    p.update(l, np.abs(phc))
    respGe[k+k0, :] = np.hstack(([phc], meassGe[k+k0, [2, 4]]/phc))
    np.savez_compressed(svepth+"calmeasGe", lamGe, meassGe, respGe)


tmp = np.load(svepth+"calmeasSi.npz")
lam = tmp['arr_0']
meass = tmp['arr_1']
resp = tmp['arr_2']
tmp = np.load(svepth+"calmeasGe.npz")
lamGe = tmp['arr_0']
meassGe = tmp['arr_1']
respGe = tmp['arr_2']

lamC = np.arange(400, 1805, 5)
respC = np.vstack((resp[:76, 1:], 0.5*(resp[76:, 1:]+respGe[:65, 1:]), respGe[65:, 1:]))

rSi = interp1d(lamC, respC[:, 0], kind='cubic')
rGe = interp1d(lamC, respC[:, 1], kind='cubic')



tia.sensitivity = 1e-6
lia.sensitivity = (0, 50e-3)
sli.sensitivity = (0, 1.)
lia.time_constant = 100e-3
sli.time_constant = 100e-3
lia.slope = 24
sli.slope = 24

mon.grating = 1
mon.wavelength = 400
fw.position = 6
lia.time_constant = 5.
lia.slope = 24
sleep(lia.wait_time)
lia.system_auto_phase(0)
sleep(lia.wait_time)
lia.system_auto_phase(0)

tia.phases = np.nan*tia.phases
tia.phase_shift = lia.phaseoff[0]

lam = np.arange(400, 1300, 5)
meass = np.zeros((lam.size, 6))
deqe = np.zeros((lam.size, 2))
#uslta = sli.tol_abs
#sslta = np.array([1.])
p = ac.DynamicPlot(ptype="semilogy")

mon.grating = 1
mon.wavelength = 400
fw.position = 6

lia.last_mags = lia.cmags
sli.last_mags = sli.cmags


meass = np.zeros((lam.size, 6))
deqe = np.zeros((lam.size, 2))

p.addnew()
k0 = 0
for k, l in enumerate(lam[k0:]):
    mon.wavelength = l
    if l == 1000:
        mon.grating = 2
    elif l == 1100:
        sli.sensitivity = (0, 1.)
        sli.time_constant = 100e-3
    if l > fw.next_filter_on*1.02:
        if fw.position == 6:
            fw.position = 1
        else:
            fw.position = fw.position + 1
    if l < 1120:
        meass[k+k0, :] = meas()
        deqe[k+k0, :] = meass[k+k0, :2]*rSi([l])[0]/meass[k+k0, 2]
    else:
        meass[k+k0, :] = meas2()
        deqe[k+k0, :] = meass[k+k0, :2]*rGe([l])[0]/meass[k+k0, 4]
    p.update(l, np.sqrt(np.power(deqe[k+k0, :], 2).sum()))
    np.savez_compressed(svepth+"14nmcSi_pos22_m5VNewObj", lam, meass, deqe)

    
lia.noise_base = np.array([4.3700000000000002e-12])
lia.noise_ratio = np.array([0.024311183144246355])
tmp = np.load("G:/2016-06-11/")
tmp = np.load(svepth+"14cSi_pos23_9Vx2.npz")
lam = tmp['arr_0']
meass = tmp['arr_1']
deqe = tmp['arr_2']

lk = 136
for l, d in zip(lam[:lk], deqe[:lk, 0]):
    p.update(l, d)
for k, l in zip(range(lk, lam.size), lam[lk:]):
    mon.wavelength = l
    if l == 1000:
        mon.grating = 2
    elif l == 1100:
        sli.sensitivity = (0, 1.)
        sli.time_constant = 100e-3
    if l > fw.next_filter_on*1.02:
        if fw.position == 6:
            fw.position = 1
        else:
            fw.position = fw.position + 1
    if l < 1120:
        meass[k, :] = meas()
        deqe[k, :] = meass[k, :2]*rSi([l])[0]/meass[k, 2]
    else:
        meass[k, :] = meas2()
        deqe[k, :] = meass[k, :2]*rGe([l])[0]/meass[k, 4]
    p.update(l, np.sqrt(np.power(deqe[k, :], 2).sum()))
    np.savez_compressed(svepth+"SiFilm_9Vx2", lam, meass, deqe)
    
tia.sensitivity = 1e-6
vs = np.linspace(-5., 5., 101)
curs = np.zeros((vs.size, 2))
p2 = ac.DynamicPlot()


for k, v in enumerate(vs):
    tia.bias_volt = v
    sleep(lia.wait_time)
    tmp = lia.cmeas
    curs[k, :] = tmp[:2]
    p2.update(v, curs[k, 0])
    
np.savez_compressed(svepth+"14nmcSi_pos22_liv", vs, curs)

p2 = ac.DynamicPlot()
lam = np.arange()


lia.iowrite(3, 1)
ts = np.zeros(1001)
tmp = np.zeros(ts.size)
tme = 20./ts.size
lia.iowrite(3, 0)
t0 = time()
for k in range(tmp.size):
    tmp[k] = lia.cmeas[-2]
    ts[k] = time()-t0
    sleep(tme)
    

ts = np.zeros(1001)
tmp = np.zeros(ts.size)
tme = 20./ts.size
tia.sensitivity = 100e-6
t0 = time()
for k in range(tmp.size):
    tmp[k] = lia.cmeas[-2]
    ts[k] = time()-t0
    sleep(tme)