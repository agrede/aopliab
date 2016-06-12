# -*- coding: utf-8 -*-
"""
Created on Sat Jun 11 06:48:40 2016

@author: Maxwell-Ampere
"""

import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep
import matplotlib.pyplot as plt
from srs import SR830
from thorlabs import FW102C
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
fw = FW102C
tmp = ac.json_load("local.json")
fw.filters = np.array(tmp['FilterWheel']['filters'], dtype=np.float64)

sli.preamps = np.array([None])
lia.preamps = np.array([tia, None])
tia.current_freq = lia.freq

tia.sensitivity = 50e-6
svepth = "G:/2016-06-11/test1.npz"

lia.ac_auto_gain = True

tmp = np.genfromtxt("./21927.csv", delimiter=',')
SiR = interp1d(tmp[:, 0], tmp[:, 1], bounds_error=False, kind='cubic')
tmp = np.genfromtxt("./12169.csv", delimiter=',', skip_header=1)
GeR = interp1d(tmp[:, 0], tmp[:, 1], bounds_error=False, kind='cubic')


lia.time_constant = 1.
lia.slope = 24
sli.time_constant = 1.
sli.slope = 24
wtme = np.array([lia.wait_time, sli.wait_time]).max()
sleep(wtme)
lia.system_auto_phase(0)
lia.system_auto_phase(1)
sli.system_auto_phase(0)
sleep(wtme)
lia.system_auto_phase(0)
lia.system_auto_phase(1)
sli.system_auto_phase(0)
tia.phase_shift = lia.phaseoff[0]

tmp = lia.noise_measure(5e-3, 1., 6, 24)
lia.noise_ratio = tmp[:, 1]/tmp[:, 0]
tmp = sli.noise_measure(3e-3, 1., 6, 24)
sli.noise_ratio = tmp[:, 1]/tmp[:, 0]

while not np.isnan(tia.inc_sensitivity):
    tia.sensitivity = tia.inc_sensitivity
    
# Autoscale
tmp = lia.noise_measure(5e-3, 5e-3, 6, 6)
lia.noise_base = tmp[:, 1]
tmp = sli.noise_measure(3e-3, 3e-3, 6, 6)
sli.noise_base = tmp[:, 1]



tia.sensitivity = 50e-6
lia.sensitivity = np.array([1., 1.])
sli.sensitivity = (0, 1.)
lia.time_constant = 10e-3
sli.time_constant = 10e-3
lia.slope = 24
sli.slope = 24

# np.savez_compressed(svepth, lia.noise_ratio, lia.noise_base, 
#                     sli.noise_ratio, sli.noise_base)

             
mon.wavelength = 1200

tmp = np.load(svepth)

lia.noise_ratio = tmp['arr_0']
lia.noise_base = tmp['arr_1']
sli.noise_ratio = tmp['arr_2']
sli.noise_base = tmp['arr_3']

sli.tol_abs = np.array([1e-6])
sli.tol_rel = np.array([1e-3])
sli.sensitivity = 1.

lia.tol_abs = np.array([10e-15, 3e-6])
lia.tol_rel = np.array([1e-3, 1e-3])


def meas():
    scaled = False
    dwelled = False
    while (not scaled or not dwelled):
        scaled = lia.update_scale(lia.last_mags) or sli.update_scale(sli.last_mags)
        dwelled = (lia.update_timeconstant(lia.last_mags) or 
                    sli.update_timeconstant(sli.last_mags))
        wtmes = np.array([lia.wait_time, sli.wait_time])
        if lia.wait_time < wtmes.max():
            tc, slope, wt = lia.best_tc_for_wait(wtmes.max())
            lia.time_constant = tc
            lia.time_constant = tc
            lia.slope = slope
        if sli.wait_time < wtmes.max():
            tc, slope, wt = sli.best_tc_for_wait(wtmes.max())
            sli.time_constant = tc
            sli.time_constant = tc
            sli.slope = slope
        sleep(wtmes.max())
        tmp0 = np.hstack((lia.cmags, sli.cmags))
        tmp1 = np.hstack((lia.last_mags, sli.last_mags))
        if np.any(np.abs(1.-tmp0/tmp1) > 0.5):
            scaled = False
        lia.last_mags = lia.cmags
        sli.last_mags = sli.cmags
    msr0 = lia.cmeas
    msr1 = sli.cmeas
    return np.hstack([msr0[[0, 1, -2, -1]], msr1[:2]])
    
lam = np.arrange(400, 1100, 5)
meass = np.zeros((lam.size, 6))
ulita = lia.tol_abs
uslta = sli.tol_abs
slita = np.array([lia.tol_abs[0], 1.])
sslta = np.array([1.])

