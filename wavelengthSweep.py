import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
import scipy.constants as PC
from scipy.interpolate import interp1d
from thorlabs import FW102C, PM100D, MC2000
from lakeshore import LKS335
import zaber.serial as zs

plt.hold(True)

rm = visa.ResourceManager()
mon = eqe.get_mono(rm)
lia = eqe.get_lia(rm)
tia = eqe.get_tia(rm)
fwi = ac.getInstr(rm, "FilterWheel")
fw = FW102C(fwi)
tmp = ac.json_load("local.json")
fw.filters = np.array(tmp['FilterWheel']['filters'], dtype=np.float64)
cryi = ac.getInstr(rm, "CryoTemp")
cry = LKS335(cryi)

zp0 = zs.AsciiSerial("COM12")
zd1 = zs.AsciiDevice(zp0, 1)
zd2 = zs.AsciiDevice(zp0, 2)
a1 = zs.AsciiAxis(zd1, 1)
a2 = zs.AsciiAxis(zd2, 1)

rtpos = np.array([int(a1.send("get pos").data), 
                  int(a2.send("get pos").data)])

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
svepth = "C:/Users/Maxwell/Desktop/Student Data/Grede/2017-03-18/"#test1.npz"

sical = np.load(svepth+"SiDet_run01_.npz")
gecal = np.load(svepth+"GeDet_run01_.npz")

lamC = np.arange(400, 1805, 5)
calC = np.hstack((
                    sical['arr_1'][:60, 0],
                    0.5*(sical['arr_1'][60:, 0]+gecal['arr_1'][:81, 0]),
                    gecal['arr_1'][81:, 0]
                  ))
phi = interp1d(lamC, calC, kind='cubic')
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
                      lia.phaseoff[0], lia.sensitivity, tia.sensitivity,
                      cry.temperature[0]])
    return np.hstack((msr0[:2], stngs))

def chgTemp(T, tmax=10*60, Tdelta=1.):
    t0 = time()
    T0 = (cry.temperature)[0]
    Tdir = np.sign(T-T0)
    cry.heater1_setpoint = T
    while (Tdir*(T-(cry.temperature)[0]) > 0 and (time()-t0) < tmax):
        sleep(0.1)
        
    T0 = (cry.temperature)[0]
    sleep(1)
    while (np.sign(T-T0) == np.sign(T0-(cry.temperature)[0]) and (time()-t0) < tmax):
        T0 = (cry.temperature)[0]
        sleep(1)
        
    while (np.abs(T-(cry.temperature)[0]) > Tdelta and (time()-t0) < tmax):
        sleep(1)
    return ((cry.temperature)[0], time()-t0)

    
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

#tia.bias_volt = 5.
#tia.volt_output = True

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

smple = "14nm-cSi_11"
np.savez_compressed(svepth+smple+"_noise300K.npz", lia.noise_ratio, 
                    lia.noise_base)

tmp = np.load(svepth+smple+"_noise.npz")

lia.noise_ratio = tmp['arr_0']
lia.noise_base = tmp['arr_1']


lia.tol_abs = np.array([1e-14]) # , 3e-6])
lia.tol_rel = np.array([5e-3]) # , 5e-3])
lia.tol_maxsettle = 40.

lia.auto_dwell = True
lia.auto_phase = False
lia.auto_scale = True
lam = np.arange(430, 1155, 5)
Ts = np.array([300, 280, 260, 240, 220, 200, 180, 160, 140, 120, 100])

meass = np.zeros((lam.size, 8, Ts.size))
eqes = np.zeros((lam.size, Ts.size))
cryInfo = np.zeros((Ts.size, 2))

tia.sensitivity = 5e-7
lia.sensitivity = (0, 500e-3)
lia.time_constant = 100e-3
lia.slope = 12
mon.wavelength = lam[0]
mon.grating = 1
fw.position = 6


lia.last_mags = lia.cmags

runno = "_run01_"
p = ac.DynamicPlot("semilogy")

poss0 = readPos()

n4 = 0
n0 = 0
n3 = 10
for k3, T in enumerate(Ts[n3:]):
    if (T != (cry.heater1_setpoint)):
        p.addnew()
        tia.sensitivity = 5e-7
        lia.sensitivity = (0, 500e-3)
        lia.time_constant = 100e-3
        lia.slope = 12
        mon.wavelength = lam[0]
        mon.grating = 1
        fw.position = 6
        a1.move_rel(-1920)
        (tmp0, tmp1) = chgTemp(T)
        cryInfo[k3+n3, :] = np.array([tmp0, tmp1])
        input("Press enter to continue...")
        sleep(lia.wait_time)
        lia.last_mags = mags()
        n0 = 0
    for k0, l in enumerate(lam[n0:]):
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
        meass[k0+n0, :, k3+n3] = meas()
        tmp = np.sqrt(np.power(meass[k0+n0, :2, k3+n3], 2).sum())
        eqes[k0+n0, k3+n3] = tmp/phi(l)
        p.update(l, eqes[k0+n0, k3+n3])
        np.savez_compressed(svepth+smple+runno+".npz", lam, meass, eqes, cryInfo)

p = ac.DynamicPlot()
cryTemps = np.zeros((Ts.size, 5))

n3 = 6
for k3, T in enumerate(Ts[n3:]):
    (tmp0, tmp1) = chgTemp(T)
    T0 = cry.temperature
    p.update(n3+k3, T0[0])
    p.update(n3+k3, T0[1])
    t0 = time()
    while (time() - t0 < 10*60):
        sleep(1)
    T1 = cry.temperature
    cryTemps[n3+k3, :] = np.hstack((np.array([tmp1]), T0, T1))
    p.update(n3+k3+0.25, T1[0])
    p.update(n3+k3+0.25, T1[1])
    np.savez_compressed(svepth+"TempCal.npz", Ts, cryTemps)
    
    
p = ac.DynamicPlot("semilogy")
vs = np.linspace(5, 0, 51)
meass = np.zeros((vs.size, 8, Ts.size))
cryInfo = np.zeros((Ts.size, 2))

tia.sensitivity = 2e-8
lia.sensitivity = (0, 200e-3)
lia.time_constant = 100e-3
lia.slope = 12

lia.last_mags = lia.cmags

runno = "_run01_375nmVsweep"
p = ac.DynamicPlot("semilogy")

n0 = 36
n3 = 7
for k3, T in enumerate(Ts[n3:]):
    if (T != (cry.heater1_setpoint)):
        p.addnew()
        tia.sensitivity = 2e-8
        lia.sensitivity = (0, 200e-3)
        lia.time_constant = 100e-3
        lia.slope = 12
        tia.bias_volt = vs[0]
        (tmp0, tmp1) = chgTemp(T)
        cryInfo[k3+n3, :] = np.array([tmp0, tmp1])
        sleep(lia.wait_time)
        lia.last_mags = mags()
        n0 = 0
    for k0, v in enumerate(vs[n0:]):
        tia.bias_volt = v
        meass[k0+n0, :, k3+n3] = meas()
        tmp = np.sqrt(np.power(meass[k0+n0, :2, k3+n3], 2).sum())
        p.update(v, tmp)
        np.savez_compressed(svepth+smple+runno+".npz", vs, meass, cryInfo)

        
p = ac.DynamicPlot("semilogy")
vs = np.linspace(-5, 5, 100)
meass = np.zeros((vs.size, 8))

tia.sensitivity = 2e-8
lia.sensitivity = (0, 200e-3)
lia.time_constant = 100e-3
lia.slope = 12

lia.last_mags = lia.cmags

runno = "_run03_375nmVsweep"
p = ac.DynamicPlot("semilogy")
vs = np.linspace(-5, 5, 100)


n0 = 36
n3 = 7

T = 100
runno = "_run04_375nm_%dK" % T
p.addnew()
meass = np.zeros((vs.size, 8))
(tmp0, tmp1) = chgTemp(T)

tia.sensitivity = 2e-8
lia.sensitivity = (0, 200e-3)
lia.time_constant = 100e-3
lia.slope = 12
tia.bias_volt = vs[0]
sleep(lia.wait_time)
lia.last_mags = mags()


n0 = 28
for k0, v in enumerate(vs[n0:]):
        tia.bias_volt = v
        meass[k0+n0, :] = meas()
        tmp = np.sqrt(np.power(meass[k0+n0, :2], 2).sum())
        p.update(v, tmp)
        np.savez_compressed(svepth+smple+runno+".npz", vs, meass)
        
        
poss = np.zeros((Ts.size, 2))

def readPos():
    return np.array([int(a1.send("get pos").data), 
                     int(a2.send("get pos").data)])
    
def setPos(pos):
    a1.move_abs(int(pos[0]))
    a2.move_abs(int(pos[1]))
    
k = 10
chgTemp(Ts[k])
poss[k, :] = readPos()

np.savez_compressed(svepth+smple+"TempPosCal.npz", Ts, poss)