import numpy as np 
import visa
import aopliab_common as ac
from keithley import K2400
import time
import matplotlib.pyplot as plt


rm = visa.ResourceManager()
smui = ac.getInstr(rm, "SMU")
# pyri = ac.getInstr(rm, "LasPow")
smu = K2400(smui)
# pyr = K2400(pyri)
ard = ac.getInstr(rm, "ARD")
start = -0.2
stop = 3.5
points = 351
climit = 50e-3
vlimit = 5.
pth = "./dta/20161006%d_AR.npz"

ard.query("setcpv 5")
dta = []
k = 0


def ivs(smu, start, stop, points, climit, port):
    smu.output = False
    smu.source_volt = True
    smu.front_terminal = port
    smu.current_limit = climit
    smu.voltage = start
    tmp = smu.voltage_sweep(start, stop, points)
    smu.output = False
    return np.reshape(tmp[1], (-1, 5))[:, :2]

    
def iscvoc(smu, vlimit, climit, port):
    smu.output = False
    smu.front_terminal = port
    smu.source_volt = True
    smu.current_limit = climit
    smu.voltage = 0.
    smu.output = True
    isc = smu.measure[1]
    smu.output = False
    smu.source_volt = False
    smu.voltage_limit = vlimit
    smu.current = 0.
    smu.output = True
    voc = smu.measure[0]
    smu.output = False
    return (isc, voc)


def suns(ard):
    return ard.query_ascii_values("measpyr")[0]


def align(ard):
    ard.write("cpvsmu")  # actually switches to TIA
    ard.write("startcpv")
    a = input("Angle? ")
    ard.write("stopcpv")
    time.sleep(10.)  # Wait for algorithm to stop
    ard.write("cpvtia")  # actually switches to SMU
    # input("Press Enter When Stopped...")
    return a


p0 = ac.DynamicPlot(ptype="semilogy")
p1 = ac.DynamicPlot(ptype="semilogy")
Area = np.pi*(10e-3)**2
calconst = 1000./54.57e-6
cont = True
while(cont):
    angle = align(ard)
    cont = (angle != '')
    if not cont:
        break
    am = iscvoc(smu, vlimit, climit, True)
    a = ivs(smu, start, stop, points, climit, True)
    tme = time.localtime()
    x = float(angle)
    y = am[0]
    p0.update(x, y)
    dta.append((tme, angle, a, am))
    np.savez_compressed(pth % k, dta)
    k = k+1
