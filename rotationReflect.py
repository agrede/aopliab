import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
import scipy.constants as PC
from scipy.interpolate import interp1d
import zaber.serial as zs
from numpy.linalg import norm
from thorlabs import FW102C


rm = visa.ResourceManager()
mon = eqe.get_mono(rm)
lia = eqe.get_lia(rm)
tia = eqe.get_tia(rm)

lia.preamps = np.array([tia])
tia.current_freq = lia.freq

zp0 = zs.BinarySerial("COM24")
zd1 = zs.BinaryDevice(zp0, 1)
zd2 = zs.BinaryDevice(zp0, 2)

fwi = ac.getInstr(rm, "FilterWheel")
fw = FW102C(fwi)
tmp = ac.json_load("local.json")
fw.filters = np.array(tmp['FilterWheel']['filters'], dtype=np.float64)


mxd1 = np.array([138380,  547065])
angls = np.linspace(mxd1[0]/2., mxd1[2]/2., 11).astype(np.int)

def getPos():
    t1 = zd1.send(60, True)
    t2 = zd2.send(60, True)
    return np.array([t1.data, t2.data])

def setAng(stp):
    if ac.within_limits(stp*2, mxd1):
        zd1.move_abs(int(stp*2))
        sleep(0.1)
        zd2.move_abs(int(stp))
        return True
    else:
        return False
    

def adc():
    sleep(lia.wait_time)
    return (lia.cmags/tia.sensitivity)[0]*2.5

def ovld():
    return (adc() > 1.)

tia.adc = adc
tia.ovrld = ovld
lia.waittimes.mask = ((np.atleast_2d(lia.tcons).T < 30e-3)+ 
                      (np.atleast_2d(lia.slopes) < 12)) > 0
lia.enbws.mask = lia.waittimes.mask

tia.sensitivity = 1e-3
svepth = "C:/Users/Maxwell/Desktop/Student Data/Grede/2017-08-16/"#test1.npz"

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

lia.tol_abs = np.array([1e-13]) # , 3e-6])
lia.tol_rel = np.array([5e-3]) # , 5e-3])
lia.tol_maxsettle = 10.

lia.auto_dwell = True
lia.auto_phase = False
lia.auto_scale = True

lam = np.arange(300, 810, 10)

calMeas = np.zeros((lam.size, 7))
cal = np.zeros(lam.size)


tia.sensitivity = 2e-6
lia.sensitivity = (0, 500e-3)
lia.time_constant = 100e-3
lia.slope = 12
mon.wavelength = lam[0]
mon.grating = 1
fw.position = 6

lia.last_mags = mags()

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
    calMeas[k0+n0, :] = meas()
    cal[k0+n0] = norm(calMeas[k0+n0, :2])
    p.update(l, cal[k0+n0])
    np.savez_compressed(svepth+"cal90deg.npz", lam, calMeas, cal)


rMeas = np.zeros((lam.size, 7, angls.size))
r = np.zeros((lam.size, angls.size))


tia.sensitivity = 2e-6
lia.sensitivity = (0, 500e-3)
lia.time_constant = 100e-3
lia.slope = 12
mon.wavelength = lam[0]
mon.grating = 1
fw.position = 6

lia.last_mags = mags()

p = ac.DynamicPlot("semilogy")

n0 = 0
k0 = 0
n2 = 0
k2 = 0

n0 = n0+k0
n2 = n2+k2
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
    rMeas[k0+n0, :, k2+n2] = meas()
    r[k0+n0, k2+n2] = norm(rMeas[k0+n0, :2, k2+n2])/cal[k0+n0]
    p.update(l, r[k0+n0, k2+n2])
    np.savez_compressed(svepth+"refl90deg.npz", lam, rMeas, r)

tmp = np.load(svepth+"refl.npz")
r2 = tmp['arr_2']

