import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
import scipy.constants as PC
from scipy.interpolate import interp1d
from thorlabs import FW102C


rm = visa.ResourceManager()
mon = eqe.get_mono(rm)
lia = eqe.get_lia(rm)
tia = eqe.get_tia(rm)
fwi = ac.getInstr(rm, "FilterWheel")
fw = FW102C(fwi)
tmp = ac.json_load("local.json")
fw.filters = np.array(tmp['FilterWheel']['filters'], dtype=np.float64)

tmp = np.genfromtxt("21927.csv", delimiter=',', skip_header=1)
SiR = interp1d(tmp[:, 0], tmp[:, 1], kind='cubic')

lia.preamps = np.array([tia])
tia.current_freq = lia.freq

#def adc():
#    ms0 = (lia.cmeas)[-2]
#    if ms0 > 1.5:
#        lia.iowrite(3, True)
#        sleep(0.01)
#        lia.iowrite(3, False)
#        sleep(0.1)
#        ms0 = (lia.cmeas)[-2]
#    sleep(0.1)
#    ms1 = (lia.cmeas)[-2]
#    while ms1 < ms0:
#        ms0 = ms1
#        sleep(0.1)
#        ms1 = (lia.cmeas)[-2]
#    return ms1

def adc():
    sleep(lia.wait_time)
    return (lia.cmags/tia.sensitivity)[0]*2.5

def ovld():
    return (adc() > 1.)

tia.adc = adc
# tia.ovrld = lambda: not lia.ioread(4)
tia.ovrld = ovld
lia.waittimes.mask = ((np.atleast_2d(lia.tcons).T < 30e-3)+ 
                      (np.atleast_2d(lia.slopes) < 12)) > 0
lia.enbws.mask = lia.waittimes.mask

tia.sensitivity = 1e-3
svepth = "C:/Users/Maxwell/Desktop/Student Data/Grede/2017-06-01/"#test1.npz"


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
    n = 0
    while (scaled or dwelled):
        print("%d - %s - %s\n" % (n, scaled, dwelled))
        n = n + 1
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



lia.time_constant = 100e-3

tmp = lia.noise_measure(10e-3, 1., 6, 24)
lia.noise_ratio = tmp[:, 1]/tmp[:, 0]

while not np.isnan(tia.inc_sensitivity):
    tia.sensitivity = tia.inc_sensitivity
    plt.pause(0.1)
    
# Autoscale
tmp = lia.noise_measure(10e-3, 10e-3, 12, 12)
lia.noise_base = tmp[:, 1]

tia.sensitivity = 5e-7
lia.sensitivity = (0, 500e-3)
lia.time_constant = 100e-3
lia.slope = 12


smple = "SiCal"
np.savez_compressed(svepth+smple+"_noise.npz", lia.noise_ratio, 
                    lia.noise_base)

tmp = np.load(svepth+smple+"_noise.npz")

lia.noise_ratio = tmp['arr_0']
lia.noise_base = tmp['arr_1']

lia.noise_ratio = np.array([2e-3])
lia.noise_base = np.array([1e-13])


lia.tol_abs = np.array([1e-14]) # , 3e-6])
lia.tol_rel = np.array([5e-3]) # , 5e-3])
lia.tol_maxsettle = 30.

lia.auto_dwell = True
lia.auto_phase = False
lia.auto_scale = True

hc = PC.h*PC.c/PC.e*1e9
p = ac.DynamicPlot("semilogy")

lam = np.arange(430, 1100, 5)

meass = np.zeros((lam.size, 7))
phis = np.zeros(lam.size)

tia.sensitivity = 100e-6
lia.sensitivity = (0, 500e-3)
lia.time_constant = 100e-3
lia.slope = 12
mon.wavelength = lam[0]
mon.grating = 1
fw.position = 6


lia.last_mags = mags()

runno = "_run00_"
p.addnew()
n0 = 0
k0 = 0

n0 = n0+k0
for k0, l in enumerate(lam[n0:]):
    mon.wavelength = l
    if l >= 1020 and mon.grating != 2:
        mon.grating = 2
    if l < 1020 and mon.grating != 1:
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
    meass[k0+n0, :] = meas()
    tmp = np.sqrt(np.power(meass[k0+n0, :2], 2).sum())
    phis[k0+n0] = (tmp/SiR(l))/(hc/l)
    p.update(l, phis[k0+n0])
    np.savez_compressed(svepth+smple+runno+".npz", lam, meass, phis)


meass = np.zeros((lam.size, 7))
eqes = np.zeros(lam.size)

tia.sensitivity = 2e-6
lia.sensitivity = (0, 500e-3)
lia.time_constant = 100e-3
lia.slope = 12
mon.wavelength = lam[0]
mon.grating = 1
fw.position = 6


lia.last_mags = mags()

runno = "_run01_"
p = ac.DynamicPlot("semilogy")

n0 = 0
k0 = 0

n0 = n0+k0
for k0, l in enumerate(lam[n0:]):
    mon.wavelength = l
    if l >= 1020 and mon.grating != 2:
        mon.grating = 2
    if l < 1020 and mon.grating != 1:
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
    meass[k0+n0, :] = meas()
    tmp = np.sqrt(np.power(meass[k0+n0, :2], 2).sum())
    eqes[k0+n0] = tmp/phis[k0+n0]
    p.update(l, eqes[k0+n0])
    np.savez_compressed(svepth+smple+runno+".npz", lam, meass, eqes)

