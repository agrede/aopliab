# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 09:14:07 2016

@author: jspri
"""

import numpy as np
import visa
import aopliab_common as ac
from keithley import K2400
import time

rm = visa.ResourceManager()

def ivs(smu, vs, climit):
    smu.output = False
    smu.front_terminal = True
    smu.set_voltage(vs[0])
    smu.current_limit = climit
    ms = np.zeros((vs.size, 2))
    smu.outut = True
    for k, v in enumerate(vs):
        smu.set_voltage(v)
        ms[k, :] = smu.measurement()[:2]
    smu.output = False
    return ms
    
def suns(smu, climit):
    smu.output = False
    smu.font_terminal = False
    smu.set_voltage(0.)
    smu.current_limit = climit
    smu.output = True
    ms = smu.measurement()[:2]
    smu.output = False
    return ms
    
def align(smu, climit):
    smu.output = False
    smu.font_terminal = True
    smu.set_voltage(0.)
    smu.current_limit = climit
    smu.output = True
    smu.inst.write("INIT")
    input("Press Enter for next measurement...")
    smu.inst.write("ABOR")
    smu.output = False
    
pth = "./dta/outdoor%d.npz"
rm = visa.ResourceManager()
smui = ac.getInstr(rm, "SMU")
smu = K2400(smui)
vs = np.arange(-1., 1.01, 0.01)
climit = 40e-3
dta = []
k = 0
while(True):
    align(smu, climit)
    a = ivs(smu, vs, climit)
    b = suns(smu, climit)
    tme = time.localtime()
    dta.append((tme, a, b))
    np.savez_compressed(pth % k, dta)
