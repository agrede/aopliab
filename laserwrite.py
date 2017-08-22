import numpy as np
import aopliab_common as ac
import visa
from time import sleep, time
import matplotlib.pyplot as plt
from matplotlib import path
import scipy.constants as PC
from scipy.interpolate import interp1d, interp2d
import zaber.serial as zs
from numpy.linalg import norm, lstsq
import numpy.ma as ma

rm = visa.ResourceManager()

zp0 = zs.AsciiSerial("COM25")
zd1 = zs.AsciiDevice(zp0, 1)
zd2 = zs.AsciiDevice(zp0, 2)
zd3 = zs.AsciiDevice(zp0, 3)
ax = zs.AsciiAxis(zd1, 1)
ay = zs.AsciiAxis(zd2, 1)
az = zs.AsciiAxis(zd3, 1)

svepth = "C:/Users/Maxwell/Desktop/Student Data/Grede/2017-07-08/"#test1.npz"


tmp = np.load(svepth+"caruoFocus.npz")
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

xs = np.arange(tmp['arr_5'][0, 1], tmp['arr_5'][0, 0]-10, -10)
ys = np.arange(tmp['arr_5'][1, 1], tmp['arr_5'][1, 0]-10, -10)



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
    
    
np.savez_compressed(svepth+"points.npz", xs, ys)

p = ac.DynamicPlot()
n0 = 0
n1 = 0
k0 = 0
k1 = 0
nt = 0
nT = 0
NT = ys.size*xs.size

n0 = n0+k0
n1 = n1+k1
for k0, y in enumerate(ys[n0:]):
    for k1, x in enumerate(xs[n1:]):
        nT = nT+1
        if setPos(np.array([x, y])):
            dropProbes()
            sleep(0.4)
            nt = nt+1
            p.update(nt, nT/NT)
