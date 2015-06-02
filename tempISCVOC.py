# -*- coding: utf-8 -*-
"""
Created on Tue May 26 06:04:01 2015

@author: Alex J. Grede
"""

import time
import numpy as np
from aopliab_common import json_write
from distutils.util import strtobool


def changeTemp(T, cry, acc=0.5, stab=0.5, stabt=30.0, tmax=720):
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


def ivmeas(smu, voltages, plt):
    meas = np.zeros((voltages.size, 2))
    # Set initial voltage and turn on output
    smu.set_voltage(voltages[0])
    smu.output = True
    # Sweep voltages
    for k, v in enumerate(voltages):
        smu.set_voltage(v)
        val = smu.measurement()  # Measure and read
        plt.update(val[0], abs(val[1]))
        meas[k, :] = np.array([val[0], val[1]])
    # Turn off output and close connections
    smu.output = False
    return meas


def themeasure(path, smu, las, cry, pm, pltvoc, pltiv,
               voltages, laser_currents, Temps, laserCorr=1.0):
    res = {}
    res['settings'] = {}
    res['settings']['voltages'] = voltages
    res['settings']['laser_currents'] = laser_currents
    res['settings']['Temps'] = Temps
    res['settings']['laserCorr'] = laserCorr
    res['voc'] = np.zeros((laser_currents.size, Temps.size))
    res['iv'] = np.zeros((voltages.size, 2, Temps.size))
    res['lp'] = np.zeros((laser_currents.size, Temps.size))
    res['T'] = np.zeros((laser_currents.size, 2, Temps.size))
    for k1, T in enumerate(Temps):
        changeTemp(T, cry)
        res['iv'][:, :, k1] = ivmeas(smu, voltages, pltiv)
        if (not strtobool(input("Continue [y/n]: "))):
            break
        pltiv.clear()
        las.set_current(laser_currents[0])
        las.output = True
        pltvoc.clear()
        for k2, lc in enumerate(laser_currents):
            las.set_current(lc)
            res['T'][k2, :, k1] = np.array(cry.temperature)
            res['lp'][k2, k1] = pm.power*laserCorr
            res['voc'][k2, k1] = voc(smu)
            pltvoc.update(abs(res['lp'][k2, k1]), res['voc'][k2, k1])
            json_write(res, path)
        las.output = False
        if (not strtobool(input("Continue [y/n]: "))):
            break
    return res


def voc(smu, drift_acc=0.001, drift_t=0.5, tmax=120.0):
    smu.set_current(0.0)
    smu.output = True
    t0 = time.time()
    tm = t0 + tmax
    voc0 = smu.measurement()[0]
    time.sleep(drift_t)
    voc = smu.measurement()[0]
    while (time.time() < tm and np.abs(1.0-voc/voc0) > drift_acc):
        voc0 = voc
        time.sleep(drift_t)
        voc = smu.measurement()[0]
    smu.output = False
    return voc


def laserVoc(smu, las, pm, lascur, plt=None, lascor=1.0):
    lp = np.zeros(lascur.shape)
    vo = np.zeros(lascur.shape)
    las.set_current(lascur[0])
    las.output = True
    for k, lc in enumerate(lascur):
        las.set_current(lc)
        vo[k] = voc(smu)
        lp[k] = pm.power*lascor
        if plt is not None:
            plt.update(abs(lp[k]), vo[k])
    las.output = False
    return (lp, vo)
