import visa
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from srs import SR570
from ametek import SR7230
from arc import SpecPro
from time import sleep, time
from aopliab_common import DynamicPlot


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

lam = np.arange(1050, 1305, 5)

dwell = lia.filter_time_constant*8


sens = tia.sensitivity

mvolt = np.zeros(lam.shape)
mphas = np.zeros(lam.shape)
mlam = np.zeros(lam.shape)
mcur = np.zeros(lam.shape)
mpow = np.zeros(lam.shape)

p = DynamicPlot()

for idx, l in enumerate(lam):
    mon.wavelength = l
    sleep(dwell)
    mlam[idx] = mon.wavelength
    tmp = lia.magphase
    mvolt[idx] = tmp[0]
    mphas[idx] = tmp[1]
    mcur[idx] = mvolt[idx]*sens
    mpow[idx] = mcur[idx]/GeR(mlam[idx])
    p.update(mlam[idx], mpow[idx])

tia.sensitivity = 1e-3
mon.wavelength = 550.0


lam = np.arange(1220, 1305, 5)

dwell = lia.filter_time_constant*8


sens = tia.sensitivity

mvolt = np.zeros(lam.shape)
mphas = np.zeros(lam.shape)
mlam = np.zeros(lam.shape)
mcur = np.zeros(lam.shape)

p = DynamicPlot()

for idx, l in enumerate(lam):
    mon.wavelength = l
    sleep(dwell)
    mlam[idx] = mon.wavelength
    tmp = lia.magphase
    mvolt[idx] = tmp[0]
    mphas[idx] = tmp[1]
    mcur[idx] = mvolt[idx]*sens
    p.update(mlam[idx], mcur[idx])

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