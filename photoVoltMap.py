import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
from matplotlib import path
import scipy.constants as PC
from scipy.interpolate import interp1d, interp2d
import zaber.serial as zs

rm = visa.ResourceManager()
lia = eqe.get_lia(rm)
lia.ac_auto_gain = False
lia.preamps = np.array([None])

zp0 = zs.AsciiSerial("COM25")
zd1 = zs.AsciiDevice(zp0, 1)
zd2 = zs.AsciiDevice(zp0, 2)
zd3 = zs.AsciiDevice(zp0, 3)
ax = zs.AsciiAxis(zd1, 1)
ay = zs.AsciiAxis(zd2, 1)
az = zs.AsciiAxis(zd3, 1)

svepth = "C:/Users/Maxwell/Desktop/Student Data/Grede/2017-04-08/"#test1.npz"

zdta = np.genfromtxt(svepth+"zdata.csv", delimiter=',')
zpos = interp2d(zdta[:, 0], zdta[:, 1], zdta[:, 2])

bnds = zdta[:4, :2]-np.array([
        [1000., 0.],
        [0., -1000.],
        [-1000., 0.],
        [-1000., 1000.]])+np.atleast_2d([0., 1000.])

bpth = path.Path([tuple(x) for x in bnds])


def readPos():
    return np.array([int(ax.send("get pos").data), 
                     int(ay.send("get pos").data),
                    int(az.send("get pos").data)])


def setPos(pos):
    if bpth.contains_point(pos[:2]):
        ax.move_abs(int(pos[0]))
        ay.move_abs(int(pos[1]))
        return True
    else:
        return False


def liftProbes():
    az.move_rel(int(800))


def dropProbes():
    (x, y, z) = readPos()
    z = int(zpos(x, y))
    az.move_abs(z)


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
                      lia.phaseoff[0], lia.sensitivity])
    return np.hstack((msr0[:2], stngs))

    

lia.waittimes.mask = ((np.atleast_2d(lia.tcons).T < 50e-3)+ 
                      (np.atleast_2d(lia.slopes) < 12)) > 0
lia.enbws.mask = lia.waittimes.mask

tmp = lia.noise_measure(10e-3, 1., 6, 24)
lia.noise_ratio = tmp[:, 1]/tmp[:, 0]

# Autoscale
tmp = lia.noise_measure(10e-3, 10e-3, 12, 12)
lia.noise_base = tmp[:, 1]

lia.auto_dwell = True
lia.auto_phase = False
lia.auto_scale = True

lia.tol_abs = np.array([1e-5]) # , 3e-6])
lia.tol_rel = np.array([2e-2]) # , 5e-3])
lia.tol_maxsettle = 5.

smple = "ca3ru2o7"
np.savez_compressed(svepth+smple+"_noise.npz", lia.noise_ratio, 
                    lia.noise_base)

tmp = np.load(svepth+smple+"_noise.npz")

lia.noise_ratio = tmp['arr_0']
lia.noise_base = tmp['arr_1']


xs = np.linspace(bnds[:, 0].min(), bnds[:, 0].max(), 152)
ys = np.linspace(bnds[:, 1].min(), bnds[:, 1].max(), 148)

meass = np.nan*np.ones((ys.size, xs.size, 2))

p = ac.DynamicPlot()
lia.last_mags = np.array([100e-3])
liftProbes()
n0 = 0
n1 = 0
k0 = 0
k1 = 0
nt = 0

liftProbes()
n0 = n0+k0
n1 = n1+k1
for k0, y in enumerate(ys[n0:]):
    for k1, x in enumerate(xs[n1:]):
        liftProbes()
        if setPos(np.array([x, y])):
            dropProbes()
            sleep(lia.wait_time)
            meass[n0+k0, n1+k1, :] = (lia.cmeas)[:2]
            liftProbes()
            nt = nt + 1
        p.update(nt, meass[n0+k0, n1+k1, 0])
        np.savez_compressed(svepth+smple+"_meas.npz", xs, ys, meass)
    n1 = 0
liftProbes()