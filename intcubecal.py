import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
import scipy.constants as PC
from scipy.interpolate import interp1d
from thorlabs import FW102C, PM100D
from keysight import Keysight2900


plt.hold(True)

rm = visa.ResourceManager()
mon = eqe.get_mono(rm)
fwi = ac.getInstr(rm, "FilterWheel")
fw = FW102C(fwi)
tmp = ac.json_load("local.json")
fw.filters = np.array(tmp['FilterWheel']['filters'], dtype=np.float64)
# filter
fw.inst.read_raw()
fw.inst.read_raw()

smui = ac.getInstr(rm, "SMU")
smu = Keysight2900(smui)

pam = ac.getInstr(rm, "PAM")
svepth = "C:/Users/Maxwell/Desktop/Student Data/Grede/2017-04-20/"#test1.npz"

def meas(N=20):
    msr = np.zeros(N)
    for k in range(N):
        sleep(0.1)
        msr[k] = (smu.measurement_single(True, False))[1]
    return np.array([msr.mean(), msr.std()])

    
mon.wavelength = 550
mon.grating = 1
fw.position = 6
    
smple = "IntCube"

p = ac.DynamicPlot("semilogy")

lam = np.arange(430, 1105, 5)

meass = np.zeros((lam.size, 2))


mon.wavelength = lam[0]
mon.grating = 1
fw.position = 6

runno = "_sandedplastic_02"
p.addnew()
k0 = 0
n0 = 0

# done fucked up
n0 = n0+k0
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
    meass[k0+n0, :] = meas()
    p.update(l, np.abs(meass[k0+n0, 0]))
    np.savetxt(svepth+smple+runno+".csv", 
               np.hstack((np.atleast_2d(lam).T, meass)), 
               delimiter=',', 
               header="wave,cur,std\n")
    np.savez_compressed(svepth+smple+runno+".npz", lam, meass)

m0 = np.load(svepth+smple+"_newport818_02.npz")['arr_1']

cald = np.genfromtxt("21927.csv", delimiter=',')
cal = interp1d(cald[:, 0], cald[:, 1])

e = 1240./lam

phi = np.abs(m0[:, 0])/(cal(lam)*e)

eqe = np.abs(meass[:, 0]/phi)