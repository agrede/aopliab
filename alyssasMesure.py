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
from arc import SpecPro
import matplotlib.pyplot as plt
# from lakeshore import LKS335
import tempISCVOC as ti
from ametek import SR7230

rm = visa.ResourceManager()

pth = "C:/Users/Maxwell/Desktop/Grede/2015-11-18/"
iv_volts = np.linspace(-1.5, 2.5, 501)
# temperatures = np.arange(300, 175, -25)
laser_currents = np.linspace(140e-3, 620e-3, 51)
laserCorr = 7.3663102104835128

#smui = ac.getInstr(rm, "SMU")
sfai = ac.getInstr(rm, "SfA")
lasi = ac.getInstr(rm, "LasPow")
pmi = ac.getInstr(rm, "PowMeter")
liai = ac.getInstr(rm, "LockInAmp")
# liri = ac.getInstr(rm, "IRLaser")
# cryi = ac.getInstr(rm, "CryoTemp")

#smu = K2400(smui)
sfa = K6430(sfai)
las = K2400(lasi)
pm = PM100D(pmi)
lia = SR7230(liai)
# lir = CLD1015(liri)
# cry = LKS335(cryi)
m1, m2 = ac.getInstr(rm, "Monochromator")
mon = SpecPro(m1, dll_path=m2)

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

#
lam0 = np.arange(-5,5.5,0.5)+549.
td = np.zeros(lam0.shape)
for k, l in enumerate(lam0):
    mon.wavelength = l
    pm.wavelength = l
    sleep(0.1)
    td[k] = pm.power
plt.plot(lam0,td*1e6)

# Testing

def setl(l):
    mon.wavelength = l
    pm.wavelength = 1

lam = np.arange(pm.wavelength_range[0],pm.wavelength_range[1]+5,5)
rsp = np.zeros(lam.shape)
for k, l in enumerate(lam):
    pm.wavelength = l
    rsp[k] = pm.response
    
sp = "PowerMeas20151104.csv"
dal = np.zeros((0,31))

lam = 477.
mon.wavelength = lam
pm.wavelength = lam
dta = np.zeros((1,31))
dta[0, 0] = lam
for k in np.arange(dta.shape[1]-1):
    sleep(1)
    dta[0, k+1] = pm.power

dal = np.vstack((dal, dta))
np.savetxt(sp, dal, delimiter=",")

lam = np.unique(dal[:, 0])
sp = "Incident20151104.csv"
di = np.zeros((lam.shape[0], 2))
for k, l in enumerate(lam):
    mon.wavelength = l
    pm.wavelength = l
    sleep(0.5)
    di[k, :] = np.array([l, pm.power])

np.savetxt(sp, di, delimiter=",")

sp = "Trans20151030.csv"
dt = np.zeros((lam.shape[0], 2))
for k, l in enumerate(lam):
    mon.wavelength = l
    pm.wavelength = l
    sleep(0.5)
    dt[k, :] = np.array([l, pm.power])

np.savetxt(sp, dt, delimiter=",")

sp = "Refl20151104.csv"
dr = np.zeros((lam.shape[0], 2))
for k, l in enumerate(lam):
    mon.wavelength = l
    pm.wavelength = l
    sleep(0.5)
    dr[k, :] = np.array([l, pm.power])

np.savetxt(sp, dr, delimiter=",")

Ap = 1-(dr[:,1])/di[:,1]

np.savetxt("Abs20151104.csv", np.vstack((lam,Ap)).T,delimiter=",")

dal2 = np.zeros((lam.shape[0], 2))
for k, l in enumerate(lam):
    mon.wavelength = l
    pm.wavelength = l
    sleep(0.5)
    dal2[k, :] = np.array([l, pm.power])
    
    
sp = "SphTrans20151030.csv"
st = np.zeros((lam.shape[0],3))
for k, l in enumerate(lam):
    mon.wavelength = l
    sleep(6*lia.filter_time_constant)
    st[k, :] = np.hstack((l, lia.magphase))
    
np.savetxt(sp, st,delimiter=",")

sp = "SphInc20151030.csv"
si = np.zeros((lam.shape[0],3))
for k, l in enumerate(lam):
    mon.wavelength = l
    sleep(6*lia.filter_time_constant)
    si[k, :] = np.hstack((l, lia.magphase))
    
np.savetxt(sp, si,delimiter=",")

As = 1-(st[:,1])/si[:,1]

np.savetxt("Abs20151030.csv", np.vstack((lam,Ap,As)).T,delimiter=",")