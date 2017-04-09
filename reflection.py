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
from thorlabs import FW102C, PM100D, MC2000
import scipy.constants as PC
from scipy.interpolate import interp1d

plt.hold(False)

rm = visa.ResourceManager()

mon = eqe.get_mono(rm)
lia = eqe.get_lia(rm)
tia = eqe.get_tia(rm)
fwi = ac.getInstr(rm, "FilterWheel")
fw = FW102C(fwi)
tmp = ac.json_load("local.json")
fw.filters = np.array(tmp['FilterWheel']['filters'], dtype=np.float64)

lia.preamps = np.array([tia])
tia.current_freq = lia.freq

def adc():
    ms0 = (lia.cmeas)[-2]
    if ms0 > 1.5:
        lia.iowrite(3, True)
        sleep(0.01)
        lia.iowrite(3, False)
        sleep(0.1)
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

tia.sensitivity = 1e-3
svepth = "G:/2016-12-06/"#test1.npz"

lia.ac_auto_gain = False

mon.grating = 2
mon.wavelength = 1064
fw.position = 4
while not np.isnan(tia.inc_sensitivity):
    tia.sensitivity = tia.inc_sensitivity
    sleep(0.1)
lia.time_constant = 5.
lia.slope = 24
wtme = lia.wait_time
sleep(wtme)
lia.system_auto_phase(0)
sleep(wtme)
lia.system_auto_phase(0)
tia.phases = np.nan*tia.phases
tia.phase_shift = lia.phaseoff[0]

lia.time_constant = 100e-3

tmp = lia.noise_measure(10e-3, 1., 6, 24)
lia.noise_ratio = tmp[:, 1]/tmp[:, 0]

while not np.isnan(tia.inc_sensitivity):
    tia.sensitivity = tia.inc_sensitivity
    sleep(0.1)
    
# Autoscale
tmp = lia.noise_measure(10e-3, 10e-3, 12, 12)
lia.noise_base = tmp[:, 1]

tia.sensitivity = 100e-6
lia.sensitivity = (0, 1.)
lia.time_constant = 50e-3
lia.slope = 12

np.savez_compressed(svepth+"sinoise", lia.noise_ratio, lia.noise_base)

mon.wavelength = 1200

tmp = np.load(svepth+"sinoise.npz")

lia.noise_ratio = tmp['arr_0']
lia.noise_base = tmp['arr_1']

lia.tol_abs = np.array([1e-14]) # , 3e-6])
lia.tol_rel = np.array([5e-3]) # , 5e-3])
lia.tol_maxsettle = 40.

lia.auto_dwell = True
lia.auto_phase = True
lia.auto_scale = True
    
    
mon.wavelength = 400
mon.grating = 1
fw.position = 6

lam = np.arange(400, 1105, 5)
meass = np.zeros((lam.size, 2))

hc = PC.h*PC.c/PC.e*1e9
p = ac.DynamicPlot(ptype="semilogy")

lia.last_mags = lia.cmags

svepth = "G:/2016-12-06/"
smple = "AlVis"
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
    meass[k+k0, :] = (lia.meas)[:2]
    p.update(l, np.sqrt(np.power(meass[k+k0, :], 2).sum()))
    np.savez_compressed(svepth+smple+".npz", lam, meass)

    
meass2 = meass.copy()
meass4 = meass.copy()
meass6 = meass.copy()
meass8 = meass.copy()


mon.grating = 1
mon.wavelength = 550
fw.position = 6

mon.wavelength = 900
mon.grating = 1
fw.position = 3

lam = np.arange(900, 1305, 5)
meass = np.zeros((lam.size, 2))

lia.last_mags = lia.cmags
hc = PC.h*PC.c/PC.e*1e9
p = ac.DynamicPlot(ptype="semilogy")

smple = "AlIR"
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
    meass[k+k0, :] = (lia.meas)[:2]
    p.update(l, np.sqrt(np.power(meass[k+k0, :], 2).sum()))
    np.savez_compressed(svepth+smple+".npz", lam, meass)

    
meass3 = meass.copy()
meass5 = meass.copy()
meass7 = meass.copy()
meass9 = meass.copy()

lam1 = np.arange(400, 1105, 5)
lam2 = np.arange(900, 1305, 5)
mc1 = np.sqrt(np.power(meass2, 2).sum(axis=1))
ma1 = np.sqrt(np.power(meass4, 2).sum(axis=1))
mc2 = np.sqrt(np.power(meass3, 2).sum(axis=1))
ma2 = np.sqrt(np.power(meass5, 2).sum(axis=1))
mc3 = np.sqrt(np.power(meass6, 2).sum(axis=1))
ma3 = np.sqrt(np.power(meass8, 2).sum(axis=1))
mc4 = np.sqrt(np.power(meass7, 2).sum(axis=1))
ma4 = np.sqrt(np.power(meass9, 2).sum(axis=1))

r1 = mc1/ma1
r2 = mc2/ma2
r3 = mc3/ma3
r4 = mc4/ma4

np.savetxt(svepth+"MeasSi1.csv", np.vstack((lam1, mc1, ma1, r1)).T, 
           delimiter=",",
           header='Wavelength [nm],Cell [A], Al [A], Ratio')
np.savetxt(svepth+"MeasGe1.csv", np.vstack((lam2, mc2, ma2, r2)).T, 
           delimiter=",",
           header='Wavelength [nm],Cell [A], Al [A], Ratio')
np.savetxt(svepth+"MeasSi2.csv", np.vstack((lam1, mc3, ma3, r3)).T, 
           delimiter=",",
           header='Wavelength [nm],Cell [A], Al [A], Ratio')
np.savetxt(svepth+"MeasGe2.csv", np.vstack((lam2, mc4, ma4, r4)).T, 
           delimiter=",",
           header='Wavelength [nm],Cell [A], Al [A], Ratio')
