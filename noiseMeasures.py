# -*- coding: utf-8 -*-
"""
Created on Sun Sep  4 05:17:26 2016

@author: Maxwell-Ampere
"""

import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
from thorlabs import FW102C
import scipy.constants as PC
from scipy.interpolate import interp1d
from keithley import K2400


plt.hold(False)

rm = visa.ResourceManager()

mon = eqe.get_mono(rm)
lia = eqe.get_lia(rm)
tia = eqe.get_tia(rm)
fwi = ac.getInstr(rm, "FilterWheel")
fw = FW102C(fwi)
tmp = ac.json_load("local.json")
fw.filters = np.array(tmp['FilterWheel']['filters'], dtype=np.float64)
smui = ac.getInstr(rm, "LasPow")
smu = K2400(smui)

lia.preamps = np.array([tia])


fs = np.logspace(5, 1, 51)
meas = np.zeros((fs.size, 10, 3))
bw = np.zeros(fs.size)
lia.osc_freq = fs[0]
k0 = 50
for k, f in enumerate(fs[k0:]):
    lia.sensitivity = np.array([100e-3])
    lia.osc_freq = f
    tia.current_freq = f
    while (tia.inc_sensitivity is not np.nan):
        tia.sensitivity = tia.inc_sensitivity
    bw[k+k0] = lia.enbw
    nse = (tia.noise_base)/(tia.sensitivity)*np.sqrt(lia.enbw)
    if f > 15.:
        lia.sensitivity = np.array([nse*3.])
    sleep(12.)
    for k1 in range(meas.shape[1]):
        sleep(lia.wait_time)
        meas[k+k0, k1, :2] = (lia.cmeas)[:2]
        meas[k+k0, k1, 2] = lia.query("NHZ.")[0]*(tia.sensitivity)
    np.savez_compressed("./noiseSMUBase.npz", fs, bw, meas)

while (tia.inc_sensitivity is not np.nan):
        tia.sensitivity = tia.inc_sensitivity
fs = np.logspace(5, 1, 51)
meas = np.zeros((fs.size, 10, 4))
bw = np.zeros(fs.size)
lia.osc_freq = fs[0]
tia.current_freq = fs[0]
while (tia.inc_sensitivity is not np.nan):
        tia.sensitivity = tia.inc_sensitivity
k0 = 0
for k, f in enumerate(fs[k0:]):
    lia.sensitivity = np.array([200e-3])
    lia.osc_freq = f
    tia.current_freq = f
    lsens = tia.sensitivity
    while (tia.inc_sensitivity is not np.nan):
        tia.sensitivity = tia.inc_sensitivity
    bw[k+k0] = lia.enbw
    nse = (tia.noise_base)/(tia.sensitivity)*np.sqrt(lia.enbw)
    if k == 0:
        nse = 0.3e-6*np.sqrt(lia.enbw)
    elif k+k0 > 0:
        nse = meas[k+k0-1, 0, 2]/lsens*np.sqrt(lia.enbw)
    lia.sensitivity = np.array([nse*3.])
    sleep(12.)
    for k1 in range(meas.shape[1]):
        sleep(lia.wait_time)
        meas[k+k0, k1, :2] = (lia.cmeas)[:2]
        meas[k+k0, k1, 2] = lia.query("NHZ.")[0]*(tia.sensitivity)
        meas[k+k0, k1, 3] = (smu.measure)[0]*(tia.sensitivity)
    np.savez_compressed("./noise2ndsmallGaAsDark.npz", fs, bw, meas)

fs = np.load("./noiseSMUNewport25um.npz")['arr_0']
m0 = np.load("./noiseSMUNewport25um.npz")['arr_2']
m1 = np.load("./noiseSMUNewport50um.npz")['arr_2']
m2 = np.load("./noiseSMUNewport100um.npz")['arr_2']
m3 = np.load("./noiseSMUNewport200um.npz")['arr_2']
ms = np.vstack((
    m0[:, :, 2].mean(axis=1)/m0[:, :, 3].mean(axis=1),
    m1[:, :, 2].mean(axis=1)/m1[:, :, 3].mean(axis=1),
    m2[:, :, 2].mean(axis=1)/m1[:, :, 3].mean(axis=1),
    m3[:, :, 2].mean(axis=1)/m1[:, :, 3].mean(axis=1))).T
mgs = np.abs(np.vstack((
    m0[:, :, 3].mean(axis=1),
    m1[:, :, 3].mean(axis=1),
    m2[:, :, 3].mean(axis=1),
    m3[:, :, 3].mean(axis=1))).T)
sws = np.array([25, 50, 100, 200])
msrs = np.zeros((20, 2))
for k in range(msrs.shape[0]):
    msrs[k, :] = (lia.cmeas)[:2]
    sleep(lia.wait_time)

np.savez_compressed("./noise20s12dB.npz", msrs)


sn0 = np.load("./noiseSMUNewportSC1MHz25um.npz")['arr_2']
sn1 = np.load("./noiseSMUNewportSC2MHz25um.npz")['arr_2']
sn2 = np.load("./noiseSMUNewportSC5MHz25um.npz")['arr_2']
sn3 = np.load("./noiseSMUNewportSC10MHz25um.npz")['arr_2']
sn4 = np.load("./noiseSMUNewportSC10MHz100um.npz")['arr_2']
sns = np.vstack((
    sn0[:, :, 2].mean(axis=1)/sn0[:, :, 3].mean(axis=1),
    sn1[:, :, 2].mean(axis=1)/sn1[:, :, 3].mean(axis=1),
    sn2[:, :, 2].mean(axis=1)/sn2[:, :, 3].mean(axis=1),
    sn3[:, :, 2].mean(axis=1)/sn3[:, :, 3].mean(axis=1),
    sn4[:, :, 2].mean(axis=1)/sn4[:, :, 3].mean(axis=1))).T

gn0 = np.load("./noise1sqcmGaAsDark.npz")['arr_2']
gn1 = np.load("./noise2ndsmallGaAsDark.npz")['arr_2']
gns = np.vstack((
    gn0[:, :, 2].mean(axis=1),
    gn1[:, :, 2].mean(axis=1))).T
