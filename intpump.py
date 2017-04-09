import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
from srs import SR830
import scipy.constants as PC
from scipy.interpolate import interp1d
from scipy.signal import sawtooth

plt.hold(False)

rm = visa.ResourceManager()

lia = eqe.get_lia(rm)
tia = eqe.get_tia(rm)
slii = ac.getInstr(rm, "SRSLockin")
sli = SR830(slii)
tmp = ac.json_load("local.json")

dly = ac.getInstr(rm, "DelayLine")

sli.preamps = np.array([None])
lia.preamps = np.array([None])

ts = np.arange(10e-6, 0.01-600e-6, 62e-6)
msrs = np.zeros((ts.size, 4))
dwell = 1.*6
p1 = ac.DynamicPlot()

for k, t in enumerate(ts):
    dly.write("delay %d" % (t*1e6))
    sleep(dwell)
    msrs[k, :2] = (lia.cmeas)[:2]
    msrs[k, 2:] = (sli.cmeas)[:2]
    p1.update(k, np.sqrt(np.power(msrs[k, :2], 2).sum()))
    p1.update(k, np.sqrt(np.power(msrs[k, 2:], 2).sum()))
    
np.savetxt("intpumptest62us_400mVtri1sdwellsamp2forrealpos2.csv", np.hstack((np.atleast_2d(ts).T, msrs)), delimiter=',')
y9 = np.sqrt(np.power(msrs[:, :2], 2).sum(axis=1)); y9 = y9/y9.max()
y10 = np.sqrt(np.power(msrs[:, 2:], 2).sum(axis=1)); y10 = y10/y10.max()

y7 = np.sqrt(np.power(msrs[:, :2], 2).sum(axis=1)); y7 = y7/y7.max()
y8 = np.sqrt(np.power(msrs[:, 2:], 2).sum(axis=1)); y8 = y8/y8.max()

y5 = np.sqrt(np.power(msrs[:, :2], 2).sum(axis=1)); y5 = y5/y5.max()
y6 = np.sqrt(np.power(msrs[:, 2:], 2).sum(axis=1)); y6 = y6/y6.max()

y3 = np.sqrt(np.power(msrs[:, :2], 2).sum(axis=1)); y3 = y3/y3.max()
y4 = np.sqrt(np.power(msrs[:, 2:], 2).sum(axis=1)); y4 = y4/y4.max()


y1 = np.sqrt(np.power(msrs[:, :2], 2).sum(axis=1)); y1 = y1/y1.max()
y2 = np.sqrt(np.power(msrs[:, 2:], 2).sum(axis=1)); y2 = y2/y2.max()

