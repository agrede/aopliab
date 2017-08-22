import sys
import numpy as np
from msvcrt import getch
import matplotlib.path as pth
import zaber.serial as zs

svepth = sys.argv[1]
N = int(sys.argv[2])

zp0 = zs.AsciiSerial("COM25")
zd1 = zs.AsciiDevice(zp0, 1)
zd2 = zs.AsciiDevice(zp0, 2)
zd3 = zs.AsciiDevice(zp0, 3)
ax = zs.AsciiAxis(zd1, 1)
ay = zs.AsciiAxis(zd2, 1)
az = zs.AsciiAxis(zd3, 1)


def getPos():
    return np.array([int(ax.send("get pos").data), 
                     int(ay.send("get pos").data),
                    int(az.send("get pos").data)])

def moveTo(x, y, bpth):
    if bpth.contains_point(np.array([int(x), int(y)])):
        az.move_rel(800)
        ax.move_abs(int(x))
        ay.move_abs(int(y))
        az.move_rel(-600)
        return True
    else:
        return False


def move_to_point():
    retry = True
    res = 100
    while retry:
        cont = True
        while cont:
            ky = getch()
            if ky == b'w':
                ay.move_rel((-20*res))
            elif ky == b's':
                ay.move_rel((20*res))
            elif ky == b'a':
                ax.move_rel((20*res))
            elif ky == b'd':
                ax.move_rel((-20*res))
            elif ky == b'j':
                az.move_rel((2*res))
            elif ky == b'k':
                az.move_rel((-2*res))
            elif ky == b' ':
                if res > 10:
                    res = 1
                elif res > 1:
                    res = 100
                else:
                    res = 10
            elif ky == b'`':
                return None
            elif ky == b'\r':
                cont = False
        tmp = input("Continue?")
        if tmp != 'n':
            retry = False
    return getPos()


def set_zoom():
    retry = True
    res = 10
    while retry:
        cont = True
        while cont:
            ky = getch()
            if ky == b'j':
                az.move_rel((2*res))
            elif ky == b'k':
                az.move_rel((-2*res))
            elif ky == b' ':
                if res > 10:
                    res = 1
                elif res > 1:
                    res = 100
                else:
                    res = 10
            elif ky == b'`':
                return None
            elif ky == b'\r':
                cont = False
        tmp = input("Continue?")
        if tmp != 'n':
            retry = False
    return getPos()[2]


def def_bounds():
    print("Define Bounds\n")
    bnds = []
    cont = True
    while cont:
        print("Move to point")
        pos = move_to_point()
        if pos is None:
            return None
        bnds.append((pos[0], pos[1]))
        tmp = input("Add new?")
        if tmp == 'n':
            cont = False
    return bnds

    
def def_zmap(bPth, xs, ys):
    print("Zmap\n")
    zmap = np.nan*np.ones((xs.size, ys.size))
    for k0, y in enumerate(ys):
        for k1, x in enumerate(xs):
            if moveTo(x, y, bPth):
                tmp = set_zoom()
                if tmp is None:
                    return None
                zmap[k0, k1] = tmp
    return zmap

    
def main():
    
    bnds = def_bounds()
    if bnds is None:
        return None
    bPth = pth.Path(bnds)
    xmx = max([x[0] for x in bnds])
    xmn = min([x[0] for x in bnds])
    ymx = max([x[1] for x in bnds])
    ymn = min([x[1] for x in bnds])

    xs = np.linspace(xmn, xmx, N)
    ys = np.linspace(ymn, ymx, N)

    zmap = def_zmap(bPth, xs, ys)
    if zmap is None:
        return None
    np.savez_compressed(svepth, xs, ys, zmap, bnds, bPth,
                        np.array([[xmn, xmx], [ymn, ymx]]))

    
if __name__ == '__main__':
    main()