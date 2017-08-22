import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
from matplotlib import path
import scipy.constants as PC
from scipy.interpolate import interp1d, interp2d
import zaber.serial as zs
from srs import DS345
import thorlabs_apt as apt
from numpy.linalg import norm, lstsq
import numpy.ma as ma
from keysight import InfiniiVision5000, InfiniiVision5000Channel
from keithley import K2400

rm = visa.ResourceManager()
lia = eqe.get_lia(rm)
lia.ac_auto_gain = False
lia.preamps = np.array([None, None])
fgi = ac.getInstr(rm, "FuncGen")
fg = DS345(fgi)
smu = K2400(ac.getInstr(rm, "SMU"))

fg.output_center = 1.
fg.highz = True

pol = apt.Motor(27000743)
pol.move_to(0)

zp0 = zs.AsciiSerial("COM25")
zd1 = zs.AsciiDevice(zp0, 1)
zd2 = zs.AsciiDevice(zp0, 2)
zd3 = zs.AsciiDevice(zp0, 3)
ax = zs.AsciiAxis(zd1, 1)
ay = zs.AsciiAxis(zd2, 1)
az = zs.AsciiAxis(zd3, 1)

osci = ac.getInstr(rm, "OScope")
osc = InfiniiVision5000(osci)
osc1 = InfiniiVision5000Channel(osc, 1)
osc2 = InfiniiVision5000Channel(osc, 2)
osc3 = InfiniiVision5000Channel(osc, 3)
osc4 = InfiniiVision5000Channel(osc, 4)

svepth = "C:/Users/Maxwell/Desktop/Student Data/Grede/2017-06-18/"#test1.npz"

tmp = np.load(svepth+"CaRuO_focus_p45.npz")
X, Y = np.meshgrid(tmp['arr_0'], tmp['arr_1'])
Z = tmp['arr_2']
bnds = tmp['arr_3']
bpth = path.Path(bnds)

X = X.reshape((-1,))
Y = Y.reshape((-1,))
Z = Z.reshape((-1,))

k = np.where(~np.isnan(Z))[0]
A = lstsq(np.vstack((X[k], Y[k], np.ones(k.size))).T, Z[k])[0]

def zpos(x, y):
    return (A[0]*x+A[1]*y+A[2])

#xs = np.linspace(tmp['arr_5'][0, 0], tmp['arr_5'][0, 1], 50)
#ys = np.linspace(tmp['arr_5'][1, 0], tmp['arr_5'][1, 1], 50)
#xs = np.arange(tmp['arr_5'][0, 0], tmp['arr_5'][0, 1]+46, 46)
#ys = np.arange(tmp['arr_5'][1, 0], tmp['arr_5'][1, 1]+46, 46)
xs = np.arange(tmp['arr_5'][0, 1], tmp['arr_5'][0, 0]-46, -46)
ys = np.arange(tmp['arr_5'][1, 1], tmp['arr_5'][1, 0]-46, -46)
xs = np.arange(tmp['arr_5'][0, 1], tmp['arr_5'][0, 0]-23, -23)
ys = np.arange(tmp['arr_5'][1, 1], tmp['arr_5'][1, 0]-23, -23)

p1 = 0.8*bnds[0, :]+0.2*bnds[3, :]
p2 = 0.8*bnds[1, :]+0.2*bnds[2, :]
p1 = bnds[[0, 3], :].mean(axis=0)
p2 = bnds[[1, 2], :].mean(axis=0)


def readPos():
    return np.array([int(ax.send("get pos").data), 
                     int(ay.send("get pos").data),
                    int(az.send("get pos").data)])


def setPos(pos):
    if bpth.contains_point(pos[:2]):
        ax.move_abs(int(pos[0]))
        ay.move_abs(int(pos[1]))
        return True
    else:
        return False
        
def linPos(x):
    p = x*p1+(1.-x)*p2
    if bpth.contains_point(p):
        ax.move_abs(int(p[0]))
        ay.move_abs(int(p[1]))
        return True
    else:
        return False


def liftProbes():
    az.move_rel(int(800))


def dropProbes():
    (x, y, z) = readPos()
    z = int(zpos(x, y))
    az.move_abs(z)
    
    
def movebnds(n):
    ax.move_abs(int(bnds[n, 0]))
    ay.move_abs(int(bnds[n, 1]))
    dropProbes()


def mags():
    mag = lia.cmags
    nse = 2.*lia.approx_noise(mag)*np.sqrt(lia.enbw)
    if mag < nse:
        return nse
    else:
        return mag


def meas():
    scaled = True
    dwelled = True
    n = 0
    while (scaled or dwelled):
        print("%d - %s - %s\n" % (n, scaled, dwelled))
        n = n + 1
        scaled = lia.update_scale(lia.last_mags)
        lwt = lia.wait_time
        dwelled = lia.update_timeconstant(lia.last_mags)
        if lia.wait_time > lwt:
            dwelled = True
        else:
            dwelled = False
        dwelled = False
        plt.pause(lia.wait_time)
        tmp0 = mags()
        tmp1 = lia.last_mags
        if np.any(np.abs(1.-tmp0/tmp1) > 0.5):
            scaled = True
        lia.last_mags = tmp0
    msr0 = lia.cmeas
    stngs = np.array([lia.time_constant, lia.slope,
                      lia.phaseoff[0], lia.sensitivity])
    return np.hstack((msr0[:2], stngs))

    

lia.waittimes.mask = ((np.atleast_2d(lia.tcons).T < 50e-3)+ 
                      (np.atleast_2d(lia.slopes) < 12)) > 0
lia.enbws.mask = lia.waittimes.mask

tmp = lia.noise_measure(10e-3, 1., 6, 24)
lia.noise_ratio = tmp[:, 1]/tmp[:, 0]

# Autoscale
tmp = lia.noise_measure(10e-3, 10e-3, 12, 12)
lia.noise_base = tmp[:, 1]

lia.auto_dwell = True
lia.auto_phase = False
lia.auto_scale = True

lia.tol_abs = np.array([3e-6]) # , 3e-6])
lia.tol_rel = np.array([5e-3]) # , 5e-3])
lia.tol_maxsettle = 5.

smple = "CaRuO_p45"
np.savez_compressed(svepth+smple+"_noise.npz", lia.noise_ratio, 
                    lia.noise_base)

tmp = np.load(svepth+smple+"_noise.npz")

lia.noise_ratio = tmp['arr_0']
lia.noise_base = tmp['arr_1']

Zs = np.nan*np.ones((ys.size, xs.size))
for k0, y in enumerate(ys):
    for k1, x in enumerate(xs):
        if bpth.contains_point([x, y]):
            Zs[k0, k1] = zpos(x, y)
Zss = ma.masked_where(np.isnan(Zs), Zs)
            
#xs = np.linspace(bnds[:, 0].min(), bnds[:, 0].max(), 152)
#ys = np.linspace(bnds[:, 1].min(), bnds[:, 1].max(), 148)


meass = np.nan*np.ones((ys.size, xs.size, 4))

p = ac.DynamicPlot("semilogy")

p.addnew()
runno = "100kHz_run00"
meass = np.nan*np.ones((ys.size, xs.size, 4))
liftProbes()
n0 = 0
n1 = 0
k0 = 0
k1 = 0
nt = 0

liftProbes()
n0 = n0+k0
n1 = n1+k1
for k0, y in enumerate(ys[n0:]):
    for k1, x in enumerate(xs[n1:]):
        liftProbes()
        if setPos(np.array([x, y])):
            dropProbes()
            sleep(lia.wait_time)
            meass[n0+k0, n1+k1, :] = (lia.cmeas)[[0, 1, 6, 7]]
            liftProbes()
            nt = nt + 1
            p.update(nt, norm(meass[n0+k0, n1+k1, :]+1e-9))
        np.savez_compressed(svepth+smple+runno+".npz", xs, ys, meass)
    n1 = 0
liftProbes()
fg.ampl = 0
Zs = ma.masked_where(np.isnan(meass[:, :, 0]), meass[:, :, 0])
tX, tY = np.meshgrid(xs, ys)
Xs = ma.masked_where(Zs.mask, tX)
Ys = ma.masked_where(Zs.mask, tY)
Zs1 = ma.masked_where(np.isnan(meass[:, :, 1]), meass[:, :, 1])
Zs2 = ma.masked_where(np.isnan(meass[:, :, 0]), norm(meass, axis=2))
Zs3 = ma.masked_where(np.isnan(meass[:, :, 0]), 
                      np.arctan2(meass[:, :, 1],
                                 meass[:, :, 0]))

ptm = np.array([903066, 2241108])

tmp = np.load(svepth+"CaRuO_map_single_probe_widespot.npz")['arr_2']
Zs0 = ma.masked_where(np.isnan(tmp[:, :, 0]), tmp[:, :, 0])

pts = np.vstack([np.array([xs[x[1]], ys[x[0]]]) for x in np.vstack(np.where(Zs < -1e-7)).T])
p = ac.DynamicPlot("semilogy")
meass = np.zeros(pts.shape)
liftProbes()
for k, pt in enumerate(pts):
    setPos(pt)
    dropProbes()
    sleep(lia.wait_time)
    meass[k, :] = (lia.cmeas)[:2]
    p.update(k, norm(meass[k, :])+1e-10)
    liftProbes()
np.savez_compressed(svepth+smple+"_meas00_line.npz", pts, meass)
fg.ampl = 0
p = ac.DynamicPlot("semilogy")

meass = np.zeros((100, 2))
liftProbes()
for k, pt in enumerate(pts):
    dropProbes()
    sleep(lia.wait_time)
    meass[k, :] = (lia.cmeas)[:2]
    p.update(k, 1e-2*norm(meass[k, :])+1e-8)
    liftProbes()
np.savez_compressed(svepth+smple+"_meas01_sameMaxSpot.npz", meass)

tmp = np.load(svepth+"focus90.npz")
bnds2 = tmp['arr_3']
B = lstsq(
        np.hstack((bnds, np.ones((bnds.shape[0], 1)))), 
        np.hstack((bnds2, np.ones((bnds2.shape[0], 1)))))[0]

tmp = np.load(svepth+"90map_measF01.npz")
Xs1, Ys1 = np.meshgrid(tmp['arr_0'], tmp['arr_1'])
m1 = tmp['arr_2']
Zs1 = ma.masked_where(np.isnan(m1[:, :, 0]), norm(m1, axis=2))
M1 = ma.masked_where(np.isnan(m1[:, :, 0]), m1[:, :, 0])
M2 = ma.masked_where(np.isnan(meass[:, :, 0]), meass[:, :, 0])
Xs2, Ys2 = np.meshgrid(xs, ys)
for k0, y in enumerate(ys):
    for k1, x in enumerate(xs):
        tmp = np.dot(np.atleast_2d([x, y, 1.]), B)
        Xs2[k0, k1] = tmp[0, 0]
        Ys2[k0, k1] = tmp[0, 1]


m1 = np.load(svepth+smple+"_meas01.npz")['arr_2']
mag1 = norm(m1, axis=2)
angs1 = np.arctan2(m1[:, :, 1], m1[:, :, 0]).reshape((-1,))
ks1 = np.where(~np.isnan(angs1))[0]
a1c = angs1[ks1]
m1c = (mag1.reshape((-1,)))[ks1]
xys1 = m1.reshape((-1, 2))
a10 = np.average(a1c, weights=m1c)
xys1c = (np.atleast_2d(m1c)*np.vstack((
         np.cos(a1c-a10), np.sin(a1c-a10)))).T
         
m2 = np.load(svepth+smple+"_meas02.npz")['arr_2']
mag2 = norm(m2, axis=2)
angs2 = np.arctan2(m2[:, :, 1], m2[:, :, 0]).reshape((-1,))
ks2 = np.where(~np.isnan(angs2))[0]
a2c = angs2[ks2]
m2c = (mag2.reshape((-1,)))[ks2]
xys2 = m2.reshape((-1, 2))
a20 = np.average(a2c, weights=m2c)
xys2c = (np.atleast_2d(m2c)*np.vstack((
         np.cos(a2c-a10), np.sin(a2c-a10)))).T

n0 = 0
n1 = 0
k0 = 0
k1 = 0

liftProbes()
n0 = n0+k0
n1 = n1+k1
for k0, y in enumerate(ysd[n0:]):
    for k1, x in enumerate(xsd[n1:]):
        liftProbes()
        if setPos(np.array([x, y])):
            dropProbes()
            sleep(1)
            liftProbes()
    n1 = 0
liftProbes()

ps = np.linspace(0, 1, 801)
meass = np.nan*np.ones((ps.size, 2))

pd = ac.DynamicPlot()
runno = "_part0_line00_normProbe_normPol"
ps = np.linspace(0, 1, 801)
meass = np.nan*np.ones((ps.size, 2))
liftProbes()
n0 = 0
k0 = 0
nt = 0
pd.addnew()

liftProbes()
n0 = n0+k0
for k0, p in enumerate(ps[n0:]):
    liftProbes()
    if linPos(p):
        dropProbes()
        sleep(lia.wait_time)
        meass[n0+k0, :] = (lia.cmeas)[:2]
        liftProbes()
        nt = nt + 1
        pd.update(p, meass[n0+k0, 0])
    np.savez_compressed(svepth+smple+runno+".npz", p1, p2, ps, meass)
liftProbes()


ps = np.linspace(0, 1, 801)
meass = np.nan*np.ones((ps.size, 2))


pd = ac.DynamicPlot("semilogy")
fg.output_center = 0
fg.offs = 2.5
fg.ampl = 0.03
runno = "_linePower00_10kHz_80_constAvgLowtoHigh"
ps = np.linspace(0, 1, 75)
pwrs = np.logspace(np.log10(0.03), np.log10(5), 21)
meass = np.nan*np.ones((ps.size, pwrs.size, 4))
liftProbes()
n0 = 0
k0 = 0
n1 = 0
k1 = 0

liftProbes()
n0 = n0+k0
n1 = n1+k1
for k1, pwr in enumerate(pwrs[n1:]):    
    pd.addnew()
    fg.ampl = pwr
    for k0, p in enumerate(ps[n0:]):
        liftProbes()
        if linPos(p):
            dropProbes()
            sleep(lia.wait_time)
            meass[n0+k0, n1+k1, :] = (lia.cmeas)[[0, 1, 6, 7]]
            liftProbes()
            pd.update(p, norm(meass[n0+k0, n1+k1, :2]))
    np.savez_compressed(svepth+smple+runno+".npz", p1, p2, ps,
                        pwrs, meass)
liftProbes()
fg.ampl = 0
fg.offs = 0

pol.move_to()
#polarization
ang = np.arange(0, 183, 3)
np.random.shuffle(ang)
#ang = np.array([0, 45])
#subang = np.arange(0, 1.05, 0.05)
subang = np.zeros(2)
N = 300
meass = np.zeros((ang.size, N, 3))

n0 = 0
k0 = 0
n1 = 0
k1 = 0

p = ac.DynamicPlot()
pol.move_to(ang[0]+subang[0])
dwell = (lia.wait_time)

n0 = n0+k0
n1 = n1+k1
for k0, a in enumerate(ang[n0:]):
    pol.move_to(a, blocking=True)
    fg.ampl = 5
    sleep(dwell)
    t0 = time()
    p.addnew()
    for k1 in range(n1, N):
        ts = time()-t0
        sleep(dwell)
        tmp = (lia.cmeas)[:2]
        meass[n0+k0, n1+k1, 0] = ts
        meass[n0+k0, n1+k1, 1:] = tmp
        p.update(ts, norm(tmp))
    fg.ampl = 0
    sleep(60)
    n1 = 0
    np.savez_compressed(svepth+smple+"_polarDep_test0.npz", ang, meass, lia.phaseoff[0])

    
p = ac.DynamicPlot()

runno = "_finalpol_140deg"
ang = np.arange(0, 183, 3)
meass = np.zeros((ang.size, 6))
n0 = 0
k0 = 0
n1 = 0
k1 = 0
pol.move_to(ang[0])
p.addnew()

n0 = n0+k0
n1 = n1+k1
for k0, a in enumerate(ang[n0:]):
    pol.move_to(a, blocking=True)
    tmp = meas()
    meass[k0+n0, :] = tmp
    p.update(a, norm(tmp[:2]))
    np.savez_compressed(svepth+smple+runno+".npz", ang, meass)
    

np.savez_compressed(svepth+smple+"_polar_trans_polaroid.npz", ang, meass)




ts = np.zeros(1000)
meast = np.zeros((ts.size, 2))
p = ac.DynamicPlot()

dwell = (lia.wait_time)

t0 = time()
for k0 in range(ts.size):
    ts[k0] = time()-t0
    sleep(dwell)
    meast[k0, :] = (lia.cmeas)[:2]
    p.update(ts[k0], meast[k0, 0])

np.savez_compressed(svepth+smple+"_timedep3.npz", ts, meast)


p = ac.DynamicPlot("loglog")
#vs = np.logspace(-1, np.log10(5.), 71)
vs = np.logspace(np.log10(5.), np.log10(0.03), 21)
#vs = np.logspace(np.log10(0.03), np.log10(5.), 71)
measv = np.zeros((vs.size, 4))

n0 = 0
k0 = 0
fg.ampl = vs[n0+k0]
p.addnew()


n0 = n0+k0
for k0, v in enumerate(vs[n0:]):
    fg.ampl = v
    sleep(0.2)
    sleep(lia.wait_time)
    measv[n0+k0, :] = (lia.cmeas)[[0, 1, 6, 7]]
    p.update(v, norm(measv[n0+k0, :2]))
    np.savez_compressed(svepth+smple+"_powdepMeas121_5uApV.npz", vs, measv)
    

m1 = np.load(svepth+smple+"_powdepMeas.npz")['arr_1']



p = ac.DynamicPlot("loglog")
fs = np.logspace(1, 5, 21)
N = 1
meass = np.nan*np.ones((fs.size, 2, N))

p.addnew()
n0 = 0
k0 = 0
n1 = 0
k1 = 0

n1 = k1
n0 = n0+k0
for k1 in np.arange(n1, N):
    if (n0+k0 == 0):
        p.addnew()
    for k0, f in enumerate(fs[n0:]):
        fg.freq = f
        sleep(lia.wait_time+2)
        meass[n0+k0, :, k1] = (lia.cmeas)[:2]
        p.update(f, norm(meass[n0+k0, :, k1]))
    n0 = 0
    k0 = 0
    np.savez_compressed(svepth+smple+"_freqResp02.npz", fs, meass)
    
    
    
smu.current_limit = 1e-3
smu.voltage = -5.
smu.output = True
rslt0 = smu.voltage_sweep(-5., 5, 201, 600)
rslt1 = smu.voltage_sweep(5., -5, 201, 600)
smu.output = False
np.savez_compressed(svepth+smple+"_lightIV.npz", rslt0[1], rslt1[1])




def saveOscope(cmnt):
    tms = osc.times
    sens = (lia.sensitivity)[0]
    v1 = osc1.voltages/10.*sens
    v2 = osc2.voltages/10.*sens
    v3 = osc3.voltages*np.power(10., -(lia.ac_gain)/20.)
    v4 = osc4.voltages
    np.savetxt(svepth+smple+"oscope_"+cmnt+".csv", np.vstack((tms, v1, v2, v3, v4)).T, delimiter=',')
    return (tms, np.vstack((v3, v4)).T)
    
    
    
ks = np.array([9, 20])