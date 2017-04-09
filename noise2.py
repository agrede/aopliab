import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
import scipy.constants as PC
from scipy.interpolate import interp1d
from keithley import K2400


pth = "G:/2017-01-25/"
plt.hold(False)

rm = visa.ResourceManager()

mon = eqe.get_mono(rm)
lia = eqe.get_lia(rm)
tia = eqe.get_tia(rm)

# lia.preamps = np.array([tia])
lia.preamps = np.array([None])

smui = ac.getInstr(rm, "SMU")
smu = K2400(smui)
dpi = ac.getInstr(rm, "LasPow")
dp = K2400(dpi)
smu.source_voltage = False
smu.current = 0.
smu.voltage_limit = 12.

dp.source_volt = False
dp.current = 1e-6
dp.voltage_limit = 3.5

tia.current_freq = lia.freq
lia.auto_scale = True
lia.ac_auto_gain = False

def adc():
    return (smu.measure)[0]

tia.adc = adc
tia.ovrld = lambda: ((smu.measure)[0] > 1.)
#
#def meas(twait):
#    scaled = True
#    curs = []
#    tmp1 = 6.*lia.query("NHZ.")[0]*np.sqrt(lia.enbw)*(tia.sensitivity)
#    while (scaled):
#        curs = []
#        scaled = lia.update_scale(np.array([tmp1]))
#        t0 = time()
#        while (time()-t0) < twait:
#            curs.append((smu.measure)[0])
#        tmp0 = 6.*lia.query("NHZ.")[0]*np.sqrt(lia.enbw)*(tia.sensitivity)
#        if np.any(np.abs(1.-tmp0/tmp1) > 0.5):
#            scaled = True
#        tmp1 = tmp0
#    mag = np.mean(curs)*(tia.sensitivity)
#    nse = lia.query("NHZ.")[0]*(tia.sensitivity)
#    return np.array([mag, nse, nse/mag])


def meas(twait):
    scaled = True
    curs = []
    tmp1 = 6.*lia.query("NHZ.")[0]*np.sqrt(lia.enbw)
    while (scaled):
        curs = []
        scaled = lia.update_scale(np.array([tmp1]))
        t0 = time()
        while (time()-t0) < twait:
            curs.append((smu.measure)[0])
        tmp0 = 6.*lia.query("NHZ.")[0]*np.sqrt(lia.enbw)
        if np.any(np.abs(1.-tmp0/tmp1) > 0.5):
            scaled = True
        tmp1 = tmp0
    mag = np.mean(curs)
    nse = lia.query("NHZ.")[0]
    return np.array([mag, nse, nse/mag])


p = ac.DynamicPlot("loglog")
fs = np.logspace(1, 5, 51)
cs = np.logspace(-6, -2, 21)
meass = np.zeros((cs.size, fs.size, 3))
lia.osc_freq = fs[0]
dp.current = cs[l0]

dp.output = True
l0 = 12
l1 = 0
dp.current = cs[l0]
for k0, c in enumerate(cs[l0:]):
    lia.sensitivity = (0, 0.5)
    dp.current = c
    while tia.overload:
        tia.sensitivity = tia.dec_sensitivity
        sleep(0.1)
    for k1, f in enumerate(fs[l1:]):
        lia.osc_freq = f
        tmp = meas(4.)
        meass[k0+l0, k1+l1, :] = meas(4.)
        p.update(f, tmp[-1])
        np.savez_compressed(pth+"./noiseAB.npz", fs, cs, meass)

dp.output = False

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

                 
p = ac.DynamicPlot("loglog")
fs = np.logspace(1, 5, 51)
meass = np.zeros((fs.size, 3))
lia.osc_freq = fs[0]

l1 = 0
for k1, f in enumerate(fs[l1:]):
    lia.osc_freq = f
    tmp = meas(4.)
    meass[k1+l1, :] = meas(4.)
    p.update(f, tmp[1])
    np.savez_compressed(pth+"./noiseTI.npz", fs, meass)