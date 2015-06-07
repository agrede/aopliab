# -*- coding: utf-8 -*-
"""
Created on Wed May 27 06:30:15 2015

@author: Alex J. Grede
"""

import numpy as np
import aopliab_common as ac
import visa
from keithley import K2400, K6430
from thorlabs import PM100D, CLD1015
from time import sleep
# import matplotlib.pyplot as plt
# from lakeshore import LKS335
import tempISCVOC as ti

rm = visa.ResourceManager()

pth = "cTest.json"
iv_volts = np.linspace(-1.5, 2.5, 501)
# temperatures = np.arange(300, 175, -25)
laser_currents = np.linspace(140e-3, 620e-3, 51)
laserCorr = 7.3663102104835128

#smui = ac.getInstr(rm, "SMU")
sfai = ac.getInstr(rm, "SfA")
lasi = ac.getInstr(rm, "LasPow")
pmi = ac.getInstr(rm, "PowMeter")
# liri = ac.getInstr(rm, "IRLaser")
# cryi = ac.getInstr(rm, "CryoTemp")

#smu = K2400(smui)
sfa = K6430(sfai)
las = K2400(lasi)
pm = PM100D(pmi)
# lir = CLD1015(liri)
# cry = LKS335(cryi)

pm.wavelength = 532
las.set_current(140e-3)

# smu.current_limit = 1e-1
las.voltage_limit = 3.0


#pltiv = ac.DynamicPlot(ptype="semilogy")
pltvoc = ac.DynamicPlot(ptype="semilogx")
#pltiv = ac.DynamicPlot(ptype="semilogy")

# IV Measure
smu.set_voltage(0.0)
smu.current_limit = 0.02
iv = ti.ivmeas(smu, iv_volts, pltiv)
np.savetxt("Alyssa/IV_292.8.csv", iv, delimiter=",")
pltiv.addnew()

# VOC measure
sfa.auto_current = False
sfa.current_range = 0.0
sfa.current = 0.0
sfa.voltage_limit = 3.0
(lp, vo) = ti.laserVoc(sfa, las, pm, laser_currents, plt=pltvoc, lascor=laserCorr)
np.savetxt("../Alyssa/293K_run3.csv", np.vstack((lp, vo)).T, delimiter=",")
pltvoc.addnew()
#res = ti.themeasure(pth, smu, las, cry, pm, pltvoc, pltiv,
#                    iv_volts, laser_currents, temperatures, laserCorr)

# oh fuck
smu = None
smui.close()

smui = ac.getInstr(rm, "SMU")
smu = K2400(smui)
smui.query("*IDN?")


# no fuck
pows = np.zeros(laser_currents.shape)
powb = np.zeros(laser_currents.shape)

# Cryo position
las.set_current(laser_currents[0])
las.output = True
for k, c in enumerate(laser_currents):
    las.set_current(c)
    sleep(1)
    pows[k] = pm.power
las.output = False

# after beamsplitter
las.set_current(laser_currents[0])
las.output = True
for k, c in enumerate(laser_currents):
    las.set_current(c)
    sleep(1)
    powb[k] = pm.power
np.savetxt("../Alyssa/PowerTest532.csv", np.vstack((laser_currents, pows, powb)).T, delimiter=",")

laserCorr = (pows/powb).mean()



# Testing
