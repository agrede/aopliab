import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
from matplotlib import path
import scipy.constants as PC
from srs import DS345
from numpy.linalg import norm, lstsq
from keysight import InfiniiVision5000, InfiniiVision5000Channel, E3640

rm = visa.ResourceManager()
tia = eqe.get_tia(rm)
fgi = ac.getInstr(rm, "FuncGen")
fg = DS345(fgi)
dci = ac.getInstr(rm, "DCSupply")
dc = E3640(dci)

fg.output_center = 1.
fg.highz = True


tia.gain_mode = 1
tia.sensitivity = 20e-6

osci = ac.getInstr(rm, "OScope")
osc = InfiniiVision5000(osci)
osc1 = InfiniiVision5000Channel(osc, 1)
osc2 = InfiniiVision5000Channel(osc, 2)
osc3 = InfiniiVision5000Channel(osc, 3)

svepth = "C:/Users/Maxwell/Desktop/Student Data/Mike Lopez/7-12-17_LED/"#test1.npz"


p = ac.DynamicPlot("semilogy")
vs = np.arange(5., 20.2, 0.2)
Rs = 10.
tms = osc.times
N = 10
dta = np.zeros((tms.size, 3, vs.size, N))
p.addnew()

for k0, v in enumerate(vs):
    dc.voltage = v
    sleep(0.2)
    for k1 in range(N):
        osc.trig_single()
        sleep(0.1)
        fgi.write("*TRG")
        sleep(0.3)
        dta[:, 0, k0, k1] = osc1.voltages
        dta[:, 1, k0, k1] = (osc2.voltages)/Rs
        dta[:, 2, k0, k1] = (osc3.voltages)*(tia.sensitivity)
        p.update(v, np.abs(dta[500, 1, k0, k1]))
    np.savez_compressed(svepth+"sweepDCsupply.npz", tms, dta)