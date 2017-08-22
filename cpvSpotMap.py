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


rm = visa.ResourceManager()
mon = eqe.get_mono(rm)
lia = eqe.get_lia(rm)
tia = eqe.get_tia(rm)

lia.preamps = np.array([tia])
tia.current_freq = lia.freq

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
svepth = "C:/Users/Maxwell/Desktop/Student Data/Grede/2017-08-14/"#test1.npz"

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

zp0 = zs.AsciiSerial("COM25")
zd1 = zs.AsciiDevice(zp0, 1)
zd2 = zs.AsciiDevice(zp0, 2)
ax = zs.AsciiAxis(zd1, 1)
ay = zs.AsciiAxis(zd2, 1)


def readPos():
    return np.array([int(ax.send("get pos").data), 
                     int(ay.send("get pos").data)])


def setPos(pos):
    ax.move_abs(int(pos[0]))
    ay.move_abs(int(pos[1]))
    
    
xi = np.arange(-1, 1.1, 0.1)
yi = np.arange(-1, 1.1, 0.1)
Xi, Yi = np.meshgrid(xi, yi)

XYip = np.vstack([np.array([x, y]) for x, y in zip(Xi.reshape((-1,)), Yi.reshape((-1,)))])
XYsp = np.array(sorted(XYip, key=lambda x: (norm(x), np.arctan2(x[1], x[0]))))
XYr = XYsp/0.047e-3

XY0 = readPos()

XYm = XYr+XY0

p = ac.DynamicPlot("semilogy")
lia.last_mags = mags()
msrs = np.zeros((XYr.shape[0], 7))
p.addnew()
n0 = 0
k0 = 0

for k0, xy in enumerate(XYm[n0:, :]):
    setPos(xy)
    tmp = meas()
    msrs[k0+n0, :] = tmp
    p.update(k0+n0, norm(tmp[:2]))
    np.savez_compressed(svepth+"0deg.npz", XYsp, XYm, msrs)
    
M = np.zeros(Xi.shape)
for k, xy in enumerate(XYsp):
    k0 = np.where(xy[1]==yi)[0][0]
    k1 = np.where(xy[0]==xi)[0][0]
    M[k0, k1] = norm(msrs[k, :2])
    
np.savez_compressed(svepth+"0deg.npz", XYsp, XYm, msrs, xi, yi, M)