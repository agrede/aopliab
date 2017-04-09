# -*- coding: utf-8 -*-
"""
Created on Fri Sep  2 05:14:58 2016

@author: Maxwell-Ampere
"""

import numpy as np
import aopliab_common as ac
import visa
from time import sleep, time
import matplotlib.pyplot as plt
from keithley import K2400

rm = visa.ResourceManager()

smui = ac.getInstr(rm, "SMU")
smu = K2400(smui)

ard = ac.getInstr(rm, "ArdMeg")

vs = np.arange(-1., 3.71, 0.01)

smu.current_limit = 105e-3

msr = smu.voltage_sweep(vs[0], vs[-1], vs.size, tmeout=3600)
iv = np.reshape(msr[1], (-1, 5))

ard.write("cpvsmu")

msr = smu.voltage_sweep(vs[0], vs[-1], vs.size, tmeout=3600)
iv2 = np.reshape(msr[1], (-1, 5))

np.savez_compressed("ardShieldTest.npz", iv, iv2)

smu.source_volt = False
smu.voltage_limit = 5.
smu.current = -1e-6

curs = np.arange(1, 71, 1)*-1e-6
adc = np.zeros(curs.size)
smu.current = curs[0]
smu.output = True
for k, c in enumerate(curs):
    smu.current = c
    sleep(0.01)
    adc[k] = ard.query_ascii_values("measpyr")[0]

np.savez_compressed("ardShieldTestPyr.npz", curs, adc)

cs2 = np.arange(0, 101, 1)*-1e-6
ms = np.zeros((cs2.size, 3))
smu.current = cs2[0]
smu.output = True
for k, c in enumerate(cs2):
    smu.current = c
    sleep(0.01)
    ms[k, :2] = smu.measure[:2]
    ms[k, 2] = ard.query_ascii_values("measpyr")[0]

smu.output = False
np.savez_compressed("ardShieldTestPyrV.npz", cs2, ms)

for k in range(25):
    ard.write("cpvsmu")
    sleep(1)
    ard.write("cpvtia")
    sleep(1)