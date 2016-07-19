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
smui = ac.getInstr(rm, "SMU")
#pyri = ac.getInstr(rm, "LasPow")
smu = K2400(smui)
#pyr = K2400(pyri)
#ard = ac.getInstr(rm, "ARD")
vs = np.arange(-1., 3.01, 0.01)
climit = 100e-3
pth = "./dta/outdoor%d.npz"

dta = []
k = 20

def ivs(smu, vs, climit, port):
    smu.output = False
    smu.front_terminal = port
    smu.set_voltage(vs[0])
    smu.current_limit = climit
    ms = np.zeros((vs.size, 2))
    smu.output = True
    for k, v in enumerate(vs):
        smu.set_voltage(v)
        ms[k, :] = smu.measurement()[:2]
    smu.output = False
    return ms
    
def suns(smu, climit):
    smu.output = False
    smu.front_terminal = False
    smu.set_voltage(0.)
    smu.current_limit = climit
    smu.output = True
    ms = smu.measurement()[:2]
    smu.output = False
    return ms
    
def align(smu, climit, ard):
    smu.output = False
    smu.font_terminal = True
    smu.set_voltage(0.)
    smu.current_limit = climit
    smu.output = True
    #ard.write("start")
    #time.sleep(10.)
    input("Press Enter for next measurement...")
    #ard.write("stop")
    smu.output = False
    

while(True):
    align(smu, climit, None)
    a = ivs(smu, vs, climit, True)
    #b = ivs(smu, vs, climit, False)
    c = suns(smu, climit)
    tme = time.localtime()
    dta.append((tme, a, c))
    np.savez_compressed(pth % k, dta)
    k = k+1
