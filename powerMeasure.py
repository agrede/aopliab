# -*- coding: utf-8 -*-
"""
Created on Wed Mar  8 05:43:05 2017

@author: Maxwell-Ampere
"""
import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
import scipy.constants as PC
from scipy.interpolate import interp1d
from thorlabs import FW102C, PM100D

plt.hold(True)

rm = visa.ResourceManager()
mon = eqe.get_mono(rm)
fwi = ac.getInstr(rm, "FilterWheel")
fw = FW102C(fwi)
tmp = ac.json_load("local.json")
fw.filters = np.array(tmp['FilterWheel']['filters'], dtype=np.float64)
pmi = ac.getInstr(rm, "PowMeter")
pm = PM100D(pmi)

svepth = "C:/Users/Maxwell/Desktop/Student Data/Grede/2017-03-26/"#test1.npz"


def meas(l, N):
    msrs = np.zeros(N)
    for k in range(N):
        sleep(0.01)
        pm.wavelength = l
        msrs[k] = pm.power
    return (np.array([msrs.mean(), msrs.std()])*l/1240.)
    

p = ac.DynamicPlot("semilogy")
smple = "SiDet"

lam = np.arange(400, 1105, 5)
meass = np.zeros((lam.size, 2))

mon.wavelength = lam[0]
mon.grating = 1
fw.position = 6

runno = "_run01_"
N = 20
p.addnew()
k0 = 0
for k, l in enumerate(lam[k0:]):
    mon.wavelength = l
    if l >= 1000 and mon.grating != 2:
        mon.grating = 2
    if l < 1000 and mon.grating != 1:
        mon.grating = 1
    if l > fw.next_filter_on*1.02:
        if fw.position == 6:
            fw.position = 1
        else:
            fw.position = fw.position + 1
    if l < fw.current_filter_off*1.02:
        if fw.position == 1:
            fw.position = 6
        else:
            fw.position = fw.position - 1
    meass[k+k0, :] = meas(l, N)
    p.update(l, meass[k+k0, 0])
    np.savez_compressed(svepth+smple+runno+".npz", lam, meass)


mon.wavelength = 550
mon.grating = 1
fw.position = 6

smple = "GeDet"
lam = np.arange(700, 1805, 5)
meass = np.zeros((lam.size, 2))

mon.wavelength = lam[0]
mon.grating = 1
fw.position = 6

runno = "_run01_"
N = 20
p.addnew()
k0 = 0
for k, l in enumerate(lam[k0:]):
    mon.wavelength = l
    if l >= 1000 and mon.grating != 2:
        mon.grating = 2
    if l < 1000 and mon.grating != 1:
        mon.grating = 1
    if l > fw.next_filter_on*1.02:
        if fw.position == 6:
            fw.position = 1
        else:
            fw.position = fw.position + 1
    if l < fw.current_filter_off*1.02:
        if fw.position == 1:
            fw.position = 6
        else:
            fw.position = fw.position - 1
    meass[k+k0, :] = meas(l, N)
    p.update(l, meass[k+k0, 0])
    np.savez_compressed(svepth+smple+runno+".npz", lam, meass)

# No filter wheel Change
fw.position = 6
p.addnew()
k0 = 0
for k, l in enumerate(lam[k0:]):
    mon.wavelength = l
    if l >= 1000 and mon.grating != 2:
        mon.grating = 2
    if l < 1000 and mon.grating != 1:
        mon.grating = 1
    meass[k+k0, :] = meas(l, N)
    p.update(l, meass[k+k0, 0])
    np.savez_compressed(svepth+smple+runno+".npz", lam, meass)