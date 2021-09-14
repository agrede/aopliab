import numpy as np
from scipy.interpolate import interp1d
from aopliab.srs import SR570
from aopliab.ametek import SR7230
from aopliab.princeton import SP2150
from time import sleep
import scipy.constants as PC
from aopliab.aopliab_common import json_load, getInstr
import os


PKGPTH = os.path.dirname(__file__)+"/"


def altIfNan(xs):
    for x in xs:
        if (not np.isnan(x)):
            return x
    return xs[-1]


def measureResponse(lam, mon, lia, dwell, plot=None, N=1, tia=None,
                    res=None, incPow=None):
    hc = PC.h*PC.c/PC.e*1e9
    rtn = {}
    rtn['mlam'] = np.zeros(lam.shape)
    rtn['cur'] = np.zeros((lam.size, N))
    rtn['phas'] = np.zeros((lam.size, N))
    sens = 1
    if (incPow is not None):
        rtn['res'] = np.zeros(lam.shape)
        rtn['eqe'] = np.zeros(lam.shape)
        dvsr = incPow
        dvsr.bounds_error = False
    elif (res is not None):
        rtn['pow'] = np.zeros(lam.shape)
        rtn['phi'] = np.zeros(lam.shape)
        dvsr = res
        dvsr.bounds_error = False
    else:
        dvsr = lambda x: 1.0
    if (tia is not None):
        sens = tia.sensitivity
        rtn['volt'] = np.zeros((lam.size, N))
    for k, l in enumerate(lam):
        mon.wavelength = l
        rtn['mlam'][k] = mon.wavelength
        d = altIfNan([dvsr(rtn['mlam'][k]), dvsr(l)])
        sleep(dwell)
        for n in range(N):
            tmp = lia.magphase
            if (tia is not None):
                rtn['volt'][k, n] = tmp[0]
            rtn['cur'][k, n] = tmp[0]*sens
            rtn['phas'][k, n] = tmp[1]
        if (incPow is not None):
            rtn['res'][k] = np.nanmean(rtn['cur'][k, :])/d
            rtn['eqe'][k] = rtn['res'][k]*hc/rtn['mlam'][k]
            y = rtn['eqe'][k]
        elif (res is not None):
            rtn['pow'][k] = np.nanmean(rtn['cur'][k, :])/d
            rtn['phi'][k] = rtn['pow'][k]*rtn['mlam'][k]/hc
            y = rtn['phi'][k]
        else:
            y = np.nanmean(rtn['cur'][k, :])
        if (plot is not None):
            plot(rtn['mlam'][k], y)
    return rtn


def brk_wavelength(start, stop, step, filters, overlap=3):
    if (len(filters) < 1):
        return [np.arange(start, stop+step, step)]
    if (overlap < 0):
        overlap = 0
    overlap = overlap+1
    rtn = []
    last_stop = start
    for filt in filters[1:]:
        tstart = last_stop-np.floor(overlap/2.0)*step
        tstop = last_stop+np.ceil((filt-last_stop)/step+overlap/2.0)*step
        last_stop = np.ceil((filt-last_stop)/step+1)*step+last_stop
        if (tstart < start):
            tstart = start
        if (tstop > stop + step):
            tstop = stop + step
            last_stop = stop
        rtn.append(np.arange(tstart, tstop, step))
    if (last_stop < stop):
        tstart = last_stop-(overlap-1)*step
        rtn.append(np.arange(tstart, stop+step, step))
    return rtn


def set_response(paths):
    pass


def get_pds(cal_file=PKGPTH+"calibrations.json"):
    cal = json_load(cal_file)
    pds = cal['PhotoDiodes']
    for mod, pdm in pds.items():
        for sn, r in pdm['responsivity'].items():
            tmp = np.array(r)
            pds[mod]['responsivity'][sn] = interp1d(1e9*tmp[:, 0], tmp[:, 1],
                                                    kind='cubic',
                                                    bounds_error=False)
    return pds


def merge_meas(dtaold, dtanew, idx):
    for key, val in dtanew.items():
        if key not in dtaold.keys():
            dtaold[key] = val
        else:
            dtaold[key][idx] = val
    return dtaold


def get_mono(rm, name="Monochromator"):
    monoi = getInstr(rm, name)
    return SP2150(monoi)


def get_tia(rm, name="TransImpedanceAmp"):
    inst = getInstr(rm, name)
    return SR570(inst)


def get_lia(rm, name="LockInAmp"):
    inst = getInstr(rm, name)
    return SR7230(inst)


def get_filters():
    lc = json_load(PKGPTH+"local.json")
    return lc['FilterWheel']['filters']


def read_file(path):
    dta = json_load(path)
    kys = np.array(['mlam', 'volt', 'cur', 'phas', 'phi', 'res', 'eqe'])
    for k in kys:
        if k in dta.keys():
            dta[k] = [np.array(x) for x in dta[k]]
    dta['settings']['wavelength'] = [np.array(x)
                                     for x in dta['settings']['wavelength']]
    return dta
