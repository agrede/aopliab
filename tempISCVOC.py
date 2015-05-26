# -*- coding: utf-8 -*-
"""
Created on Tue May 26 06:04:01 2015

@author: Alex J. Grede
"""

import time
import numpy as np
from aopliab_common import json_write

def changeTemp(T, cry, acc=0.5, stab=0.5, stabt=10.0, tmax=300):
    cry.heater1_setpoint = T
    t0 = time.time()
    tm = t0 + tmax
    cT0 = cry.temperature
    time.sleep(stabt)
    cT = cry.temperature
    Tdrift = abs(cT[1]-cT0[1])
    Terr = abs(T-cT[0])
    while (time.time() < tm and (Terr > acc or Tdrift > stab)):
        cT0 = cT
        time.sleep(stabt)
        cT = cry.temperature
        Tdrift = abs(cT[1]-cT0[1])
        Terr = abs(T-cT[0])
        

def ivmeas(smu, voltages):
    meas = np.zeros((voltages.size, 2))
    # Set initial voltage and turn on output
    smu.set_voltage(voltages[0])
    smu.output = True
    # Sweep voltages
    for k, v in enumerate(voltages):
        smu.set_voltage(v)
        val = smu.measurement()  # Measure and read
        meas[k, :] = np.array([val[0], val[1]])
    # Turn off output and close connections
    smu.output = False
    return meas
    

def themeasure(path, smu, las, cry, pm, 
               voltages, laser_currents, Temps, laserCorr=1.0):
    res = {}
    res['settings'] = {}
    res['settings']['voltages'] = voltages
    res['settings']['laser_currents'] = laser_currents
    res['settings']['Temps'] = Temps
    res['settings']['laserCorr'] = laserCorr
    res['iv'] = np.zeros((voltages.size, 2, Temps.size, laser_currents.size))
    res['lp'] = np.zeros((Temps.size, laser_currents.size))
    res['T'] = np.zeros((Temps.size, 2, laser_currents.size))
    for k1, T in enumerate(Temps):
        changeTemp(T, cry)
        las.set_current(laser_currents[0])
        las.output = True
        for k2, lc in enumerate(laser_currents):
            las.set_current(lc)
            res['T'][k1, :, k2] = np.array(cry.temperature)
            res['lp'][k1, k2] = pm.power*laserCorr
            res['iv'][:, :, k1, k2] = ivmeas(smu, voltages)
            json_write(res, path)
    las.output = False