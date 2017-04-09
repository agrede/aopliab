import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
import scipy.constants as PC
from scipy.interpolate import interp1d


plt.hold(True)

rm = visa.ResourceManager()
lia = eqe.get_lia(rm)
tia = eqe.get_tia(rm)

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

tia.sensitivity = 1e-6
svepth = "C:/Users/Maxwell/Desktop/Student Data/Grede/2017-03-26/"#test1.npz"

lia.ac_auto_gain = False


def mags():
    mag = lia.cmags
    nse = 2.*lia.approx_noise(mag)*np.sqrt(lia.enbw)
    if mag < nse:
        return nse
    else:
        return mag


def meas():
    scaled = True
    dwelled = True
    pmcurs = []
    n = 0
    while (scaled or dwelled):
        print("%d - %s - %s\n" % (n, scaled, dwelled))
        n = n + 1
        pmcurs = []
        scaled = lia.update_scale(lia.last_mags)
        lwt = lia.wait_time
        dwelled = lia.update_timeconstant(lia.last_mags)
        if lia.wait_time > lwt:
            dwelled = True
        else:
            dwelled = False
        dwelled = False
        plt.pause(lia.wait_time)
        tmp0 = mags()
        tmp1 = lia.last_mags
        if np.any(np.abs(1.-tmp0/tmp1) > 0.5):
            scaled = True
        lia.last_mags = tmp0
    msr0 = lia.cmeas
    stngs = np.array([lia.time_constant, lia.slope,
                      lia.phaseoff[0], lia.sensitivity, tia.sensitivity])
    return np.hstack((msr0[:2], stngs))
    

while not np.isnan(tia.inc_sensitivity):
    tia.sensitivity = tia.inc_sensitivity
    sleep(0.1)
lia.time_constant = 5.
lia.slope = 24
wtme = lia.wait_time
plt.pause(wtme)
lia.system_auto_phase(0)
plt.pause(wtme)
lia.system_auto_phase(0)
tia.phases = np.nan*tia.phases
tia.phase_shift = lia.phaseoff[0]

lia.time_constant = 100e-3

tia.bias_volt = 5.
tia.volt_output = True

tmp = lia.noise_measure(10e-3, 1., 6, 24)
lia.noise_ratio = tmp[:, 1]/tmp[:, 0]

while not np.isnan(tia.inc_sensitivity):
    tia.sensitivity = tia.inc_sensitivity
    plt.pause(0.1)
    
# Autoscale
tmp = lia.noise_measure(10e-3, 10e-3, 12, 12)
lia.noise_base = tmp[:, 1]

tia.sensitivity = 100e-6
lia.sensitivity = (0, 1.)
lia.time_constant = 100e-3
lia.slope = 12

np.savez_compressed(svepth+"Ca3Ru2O7noisep45deg", lia.noise_ratio, 
                    lia.noise_base)

tmp = np.load(svepth+"30nm_14_375nm_5Vnoise.npz")

lia.noise_ratio = tmp['arr_0']
lia.noise_base = tmp['arr_1']


lia.tol_abs = np.array([1e-14]) # , 3e-6])
lia.tol_rel = np.array([5e-3]) # , 5e-3])
lia.tol_maxsettle = 40.

lia.auto_dwell = True
lia.auto_phase = False
lia.auto_scale = True

oas = np.logspace(np.log10(5.), np.log10(0.06), 21)
# oas = np.logspace(np.log10(5.), np.log10(0.06), 51)
# oas = np.logspace(np.log10(0.333333), np.log10(0.003333), 51)
vs = np.arange(5., -0.1, -0.1)

p = ac.DynamicPlot("loglog")


p.addnew()
meass = np.zeros((vs.size, 7))

k0 = 0
for k, v in enumerate(vs[k0:]):
    tia.bias_volt = v
    meass[k+k0, :] = meas()
    p.update(v, np.sqrt(np.power(meass[k+k0, :2], 2).sum()))
    np.savez_compressed(svepth+"asdf.npz", vs, meass)

    
p = ac.DynamicPlot("loglog")

p.addnew()
meass = np.zeros((oas.size, 7))

k0 = 0
for k, oa in enumerate(oas[k0:]):
    lia.osc_amp = oa
    meass[k+k0, :] = meas()
    p.update(oa, np.sqrt(np.power(meass[k+k0, :2], 2).sum()))
    np.savez_compressed(svepth+"Ca3Ru2O7noisep45deg.npz", oas, meass)

