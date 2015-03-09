import visa
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from srs import SR570
from ametek import SR7230
from arc import SpecPro
from time import sleep, time
import scipy.constants as PC
from aopliab_common import DynamicPlot, json_write

hc = PC.h*PC.c/PC.e*1e9

def runMean(x, N):
    return np.convolve(x, np.ones((N,))/N)[(N-1):]

plt.interactive(True)
plt.hold(False)
SiRd = np.genfromtxt("12187.csv", skip_header=1, delimiter=",")
SiR = interp1d(SiRd[:,0], SiRd[:,1], kind='cubic')
GeRd = np.genfromtxt("12169.csv", skip_header=1, delimiter=",")
GeR = interp1d(GeRd[:,0], GeRd[:,1]*0.071, kind='cubic')

rm = visa.ResourceManager()

tia_in = rm.open_resource("ASRL1::INSTR", baud_rate=9600, data_bits=8, stop_bits=visa.constants.StopBits.two,write_termination='\r\n')
tia = SR570(tia_in)
tia.sensitivity = 50e-6

lia_in = rm.open_resource("TCPIP::169.254.150.230::50000::SOCKET", read_termination='\0',  write_termination='\0')
lia = SR7230(lia_in)

mon = SpecPro(4)


outd = {}
outd['cal'] = {}
outd['cal']['sens'] = np.ones(3)
outd['cal']['pd'] = np.array(["Si", "Si", "Ge"])
nm = 'LVO_LSAT_36mT'
outd[nm] = {}

ivd = np.genfromtxt(wd+nm+".txt", delimiter='\t')

outd[nm]['iv'] = ivd
m,b = np.linalg.lstsq(np.hstack((ivd[:,[0]],ivd[:,[0]]**0)), ivd[:,1])[0]
outd[nm]['R'] = 1/m

json_write(outd, wd+"data.json")

tia.bias_volt = 1.0
tia.volt_output = True
tia.sensitivity = 500e-9

dwell = lia.filter_time_constant*8

outd[nm]['eqe'] = {}
outd[nm]['eqe']['settings'] = {
    'bias': tia.bias_volt, 
    'sens': tia.sensitivity,
    'tc': lia.filter_time_constant,
    'dwell': dwell}

json_write(outd, wd+"data.json")

lam = np.array([
    np.arange(300, 580, 5),
    np.arange(535, 850, 5),
    np.arange(815, 1405, 5)])

dwell = lia.filter_time_constant*8


sens = tia.sensitivity

cvolt = np.array([np.zeros(x.shape) for x in lam])
cphas = np.array([np.zeros(x.shape) for x in lam])
clam = np.array([np.zeros(x.shape) for x in lam])
ccur = np.array([np.zeros(x.shape) for x in lam])
cpow = np.array([np.zeros(x.shape) for x in lam])
cphi = np.array([np.zeros(x.shape) for x in lam])

sens = tia.sensitivity
dwell = lia.filter_time_constant*8
p = DynamicPlot()
m = 2
for idx, l in enumerate(lam[m]):
    mon.wavelength = l
    sleep(dwell)
    clam[m][idx] = mon.wavelength
    tmp = lia.magphase
    cvolt[m][idx] = tmp[0]
    cphas[m][idx] = tmp[1]
    ccur[m][idx] = cvolt[m][idx]*sens
    cpow[m][idx] = ccur[m][idx]/GeR(clam[m][idx])
    cphi[m][idx] = cpow[m][idx]*clam[m][idx]/hc
    p.update(clam[m][idx], cphi[m][idx])

outd['cal']['sens'][m] = tia.sensitivity
outd['cal']['volt'] = cvolt
outd['cal']['phas'] = cphas
outd['cal']['cur'] = ccur
outd['cal']['pow'] = cpow
outd['cal']['phi'] = cphi
outd['cal']['lam'] = clam
json_write(outd, wd+"data.json")
tia.sensitivity = 1e-3
mon.wavelength = 550.0

calLam = np.hstack((clam[0][:-1], clam[1][8:-1], clam[2][6:]))
X = np.vstack((calLam, np.ones(calLam.size))).T
calPhi = interp1d(calLam, np.hstack((cphi[0][:-1], cphi[1][8:-1], cphi[2][6:])),kind='cubic')
calPow = interp1d(calLam, np.hstack((cpow[0][:-1], cpow[1][8:-1], cpow[2][6:])),kind='cubic')

mvolt = np.array([np.zeros(x.shape) for x in lam])
mphas = np.array([np.zeros(x.shape) for x in lam])
mlam = np.array([np.zeros(x.shape) for x in lam])
mcur = np.array([np.zeros(x.shape) for x in lam])
mres = np.array([np.zeros(x.shape) for x in lam])
meqe = np.array([np.zeros(x.shape) for x in lam])

nm = 'LV8_STO_25mT'
outd[nm] = {}

ivd = np.genfromtxt(wd+nm+".txt", delimiter='\t')

outd[nm]['iv'] = ivd
m1,b1 = np.linalg.lstsq(np.hstack((ivd[:,[0]],ivd[:,[0]]**0)), ivd[:,1])[0]
outd[nm]['R'] = 1/m1

outd[nm]['eqe'] = {}
outd[nm]['eqe']['settings'] = {
    'bias': np.zeros(3), 
    'sens': np.ones(3),
    'lisens': np.ones(3),
    'tc': np.ones(3),
    'dwell': np.ones(3)}

p = DynamicPlot()
tia.bias_volt = 1.0
tia.volt_output = True
tia.sensitivity = 10e-6

dwell = lia.filter_time_constant*8
sens = tia.sensitivity
m = 0
for idx, l in enumerate(lam[m]):
    mon.wavelength = l
    sleep(dwell)
    mlam[m][idx] = mon.wavelength
    tmp = lia.magphase
    mvolt[m][idx] = tmp[0]
    mphas[m][idx] = tmp[1]
    mcur[m][idx] = mvolt[m][idx]*sens
    mres[m][idx] = mcur[m][idx]/calPow(mlam[m][idx])
    meqe[m][idx] = mcur[m][idx]/calPhi(mlam[m][idx])
    p.update(mlam[m][idx], meqe[m][idx])

outd[nm]['eqe']['settings']['sens'][m] = tia.sensitivity
outd[nm]['eqe']['settings']['lisens'][m] = lia.sensitivity
outd[nm]['eqe']['settings']['bias'][m] = tia.bias_volt
outd[nm]['eqe']['settings']['tc'][m] = lia.filter_time_constant
outd[nm]['eqe']['settings']['dwell'][m] = dwell
outd[nm]['eqe']['lam'] = mlam
outd[nm]['eqe']['volt'] = mvolt
outd[nm]['eqe']['phas'] = mphas
outd[nm]['eqe']['cur'] = mcur
outd[nm]['eqe']['res'] = mres
outd[nm]['eqe']['eqe'] = meqe

json_write(outd, wd+"data.json")
tia.sensitivity = 1e-3
mon.wavelength = 550.0

tia.sensitivity = 1e-3
mon.wavelength = 550.0

# Decay test
K = 5001
mon.wavelength = 300
t = np.zeros(K)
mvolt = np.zeros(K)
mphas = np.zeros(K)
st = np.zeros(K)
svolt = np.zeros(K)
sphas = np.zeros(K)

t0 = time()
mon.wavelength = 870
for k in np.arange(K):
    t[k] = time()
    tmp = lia.magphase
    mvolt[k] = tmp[0]
    mphas[k] = tmp[1]

mon.wavelength = 880
st0 = time()
for k in np.arange(K):
    st[k] = time()
    tmp = lia.magphase
    svolt[k] = tmp[0]
    sphas[k] = tmp[1]

mon.close()
tia_in.close()
lia_in.close()

from lakeshore import LKS335
cry_in = rm.open_resource("GPIB0::12::INSTR")
cry = LKS335(cry_in)