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
pth = "./dta/dark%d.npz"

dta = []
k = 0


def ivs(smu, start, stop, points, climit, port):
    smu.output = False
    smu.source_volt = True
    smu.front_terminal = port
    smu.current_limit = climit
    smu.voltage = start
    tmp = smu.voltage_sweep(start, stop, points)
    return np.reshape(tmp[1], (-1, 5))[:, :2]


def suns(ard):
    return ard.query_ascii_values("meas")[0]


def align(smu, climit, ard):
    smu.output = False
    smu.front_terminal = True
    smu.voltage = 0.
    smu.current_limit = climit
    smu.output = True
    # ard.write("start")
    while True:
        user_input = input('Continue (y/n): ')
        if user_input in ['y', 'n']:
            break
    # ard.write("stop")
    # input("Press Enter When Stopped...")
    smu.output = False
    return (user_input == 'y')


p = ac.DynamicPlot(ptype="semilogy")
cont = True
while(cont):
    cont = align(smu, climit, ard)
    if not cont:
        break
    a = ivs(smu, start, stop, points, climit, True)
    b = ivs(smu, start, stop, points, climit, False)
    c = suns(ard)
    tme = time.localtime()
    x = tme.tm_hour+tme.tm_min/60.+tme.tm_sec/3600.
    y = (-a[:, 0]*a[:, 1]).max()/(-b[:, 0]*b[:, 1]).max()
    p.update(x, y)
    dta.append((tme, a, b, c))
    np.savez_compressed(pth % k, dta)
    k = k+1
