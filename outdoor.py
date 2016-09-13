import numpy as np
import visa
import aopliab_common as ac
from keithley import K2400
import time
import matplotlib.pyplot as plt


rm = visa.ResourceManager()
smui = ac.getInstr(rm, "LasPow")
# pyri = ac.getInstr(rm, "LasPow")
smu = K2400(smui)
# pyr = K2400(pyri)
ard = ac.getInstr(rm, "ARD")
start = -0.2
stop = 3.5
points = 351
climit = 50e-3
vlimit = 5.
pth = "./dta/20160913%d.npz"

ard.write("setcpv 1")
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
    time.sleep(60.)  # wait time between measures
    ard.write("stopcpv")
    time.sleep(5.)  # Wait for algorithm to stop
    ard.write("cpvtia")  # actually switches to SMU
    # input("Press Enter When Stopped...")
    return True


p0 = ac.DynamicPlot(ptype="semilogy")
p1 = ac.DynamicPlot(ptype="semilogy")
Area = np.pi*(10e-3)**2
calconst = 1000./54.57e-6
cont = True
while(cont):
    cont = align(ard)
    if not cont:
        break
    am = iscvoc(smu, vlimit, climit, True)
    bm = iscvoc(smu, vlimit, climit, False)
    a = ivs(smu, start, stop, points, climit, True)
    b = ivs(smu, start, stop, points, climit, False)
    c = suns(ard)
    tme = time.localtime()
    x = tme.tm_hour+tme.tm_min/60.+tme.tm_sec/3600.
    y = (-a[:, 0]*a[:, 1]).max()/(-b[:, 0]*b[:, 1]).max()
    p0.update(x, y)
    pwr = Area*(c*1.02279738e-07+3.43531676e-07)*calconst
    y2 = (-a[:, 0]*a[:, 1]).max()/pwr
    p1.update(x, y2)
    dta.append((tme, a, b, c, am, bm))
    np.savez_compressed(pth % k, dta)
    k = k+1
