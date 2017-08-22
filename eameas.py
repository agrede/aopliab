import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
import scipy.constants as PC
from scipy.interpolate import interp1d
from thorlabs import FW102C
from keithley import K2400

plt.hold(True)

rm = visa.ResourceManager()
mon = eqe.get_mono(rm)
lia = eqe.get_lia(rm)
tia = eqe.get_tia(rm)
fwi = ac.getInstr(rm, "FilterWheel")
fw = FW102C(fwi)
tmp = ac.json_load("local.json")
fw.filters = np.array(tmp['FilterWheel']['filters'], dtype=np.float64)
smui = ac.getInstr(rm, "SMU")
smu = K2400(smui)
# filter
fw.inst.read_raw()
fw.inst.read_raw()

lia.preamps = np.array([tia])
tia.current_freq = lia.freq
smu.source_volt = False
smu.current = 0.
tia.max_output = 4.


def adc():
    ms1 = np.abs((smu.measure)[0])
    return ms1


def ovld():
    return (adc() > 4.0)


tia.adc = adc
tia.ovrld = ovld
lia.waittimes.mask = ((np.atleast_2d(lia.tcons).T < 30e-3)+
                      (np.atleast_2d(lia.slopes) < 12)) > 0
lia.enbws.mask = lia.waittimes.mask

tia.sensitivity = 10e-6
svepth = "C:/Users/Maxwell/Desktop/Student Data/Grede/test/"#test1.npz"

lia.ac_auto_gain = False


def mags():
    mag = np.abs(adc())*tia.sensitivity
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
        t0 = time()
        lwt = lia.wait_time
        while ((time() - t0) < lwt):
            pmcurs = (smu.measure)[0]
        tmp0 = mags()
        tmp1 = lia.last_mags
        if np.any(np.abs(1.-tmp0/tmp1) > 0.5):
            scaled = True
        lia.last_mags = tmp0
    msr0 = lia.cmeas
    pmcurs = np.array(pmcurs)
    msr1 = np.array(pmcurs.mean(), pmcurs.std())*(tia.sensitivity)
    stngs = np.array([lia.time_constant, lia.slope,
                      lia.phaseoff[0], lia.sensitivity, tia.sensitivity])
    return np.hstack((msr0[:2], msr1, stngs))


while not np.isnan(tia.inc_sensitivity):
    tia.sensitivity = tia.inc_sensitivity
    plt.pause(0.1)
    
    
tmp0 = lia.noise_measure(10e-3, 10e-3, 6, 12)
tmp1 = np.abs(np.array([(smu.measure)[0] for i in range(20)]).mean())*tia.sensitivity
lia.noise_ratio = tmp0[:, 1]/tmp1

tmp = lia.noise_measure(10e-3, 10e-3, 12, 12)
lia.noise_base = tmp[:, 1]

tia.sensitivity = 1e-5
lia.sensitivity = (0, 500e-3)
lia.time_constant = 100e-3
lia.slope = 12

smple = "sidet"
np.savez_compressed(svepth+smple+"_noise.npz", lia.noise_ratio,
                    lia.noise_base)

tmp = np.load(svepth+smple+"_noise.npz")

lia.noise_ratio = tmp['arr_0']
lia.noise_base = tmp['arr_1']


lia.tol_abs = np.array([1e-14]) # , 3e-6])
lia.tol_rel = np.array([5e-3]) # , 5e-3])
lia.tol_maxsettle = 10.

lia.auto_dwell = True
lia.auto_phase = False
lia.auto_scale = True


p = ac.DynamicPlot("semilogy")

lam = np.arange(400, 1105, 5)

meass = np.zeros((lam.size, 7))
dRoR = np.zeros(lam.size)

tia.sensitivity = 10e-6
lia.sensitivity = (0, 500e-3)
lia.time_constant = 100e-3
lia.slope = 12
mon.wavelength = lam[0]
mon.grating = 1
fw.position = 6

lia.last_mags = mags()


runno = "_run01_"
p.addnew()
k0 = 0
n0 = 0

# done fucked up
n0 = n0+k0
for k0, l in enumerate(lam[n0:]):
    mon.wavelength = l
    if l >= 1050 and mon.grating != 2:
        mon.grating = 2
    if l < 1050 and mon.grating != 1:
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
    tmp = np.sqrt(np.power(meass[k0+n0, :2], 2).sum())/np.abs(meass[k0+n0, 2])
    p.update(l, tmp)
    np.savetxt(
        svepth+smple+runno+".csv",
        np.hstack((
            np.atleast_2d(lam).T, meass, np.atleast_2d(dRoR).T)),
        delimiter=',',
        header="wave,x,y,DC,std,timeconst,slope,phaseoff,liaSens,tiasens,dRoR\n")
    np.savez_compressed(svepth+smple+runno+".npz", lam, meass, dRoR)
