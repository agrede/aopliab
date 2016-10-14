import numpy as np
import visa
import aopliab_common as ac
from keithley import K2400
import time
import matplotlib.pyplot as plt


rm = visa.ResourceManager()
smui = ac.getInstr(rm, "SMU")
smu2i = ac.getInstr(rm, "LasPow") # FIIIIIXX
# pyri = ac.getInstr(rm, "LasPow")
smu = K2400(smui)
smu2 = K2400(smu2i)
# pyr = K2400(pyri)
ard = ac.getInstr(rm, "ARD")
start2 = -0.2
stop2 = 1.
points2 = 121
start = -0.2
stop = 3.5
points = 351
climit = 100e-3
climit2 = 1.
vlimit = 5.
pth = "./dta/20161014%d.npz"
ptha = "./dta/20161014%s%d.txt"

ard.query("setcpv 1")
dta = []
k = 3


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


def align(ard, smu):
    ard.write("cpvsmu")  # actually switches to TIA
    ard.write("startcpv")
    time.sleep(60.)  # wait time between measures
    ard.write("stopcpv")
    #You have 10 seconds to move your goddamn hands away
    for k in range(8):
        smu.beep(.2, 25*k)
        time.sleep(.2)
    time.sleep(10.)  # Wait for algorithm to stop
    ard.write("cpvtia")  # actually switches to SMU
    # input("Press Enter When Stopped...")
    return True


p0 = ac.DynamicPlot()
Area = np.pi*(10e-3)**2
calconst = 1000./54.57e-6
cont = True
while(cont):
    cont = align(ard, smu)
    if not cont:
        break
        
    am = iscvoc(smu, vlimit, climit, True)
    bm = iscvoc(smu, vlimit, climit, False)
    dm = iscvoc(smu2, vlimit, climit2, False)      #FIIIIIX
    a = ivs(smu, start, stop, points, climit, True)
    b = ivs(smu, start, stop, points, climit, False)
    d = ivs(smu2, start2, stop2, points2, climit2, False) #FIIIIIX
    c = suns(ard)
    tme = time.localtime()
    x = tme.tm_hour+tme.tm_min/60.+tme.tm_sec/3600.
    y1 = (-a[:, 0]*a[:, 1]).max()*(650e-6)**2/((-b[:, 0]*b[:, 1]).max()*Area)
    y2 = np.abs((-a[:, 0]*a[:, 1]).max()/(am[0]*am[1]))
    pwr = Area*(c*1.02279738e-07+3.43531676e-07)*calconst
    y3 = np.abs((-a[:, 0]*a[:, 1]).max()/pwr)
    p0.update(x, y1)
    p0.update(x, y2)
    p0.update(x, y3)
    dta.append((tme, a, b, c, d, am, bm, dm))  #cheeeeeeck
    np.savez_compressed(pth % k, dta)
    np.savetxt(ptha % ('a', k), a)
    np.savetxt(ptha % ('b', k), b)
    np.savetxt(ptha % ('d', k), d)
    k = k+1
