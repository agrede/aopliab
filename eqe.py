import visa
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from srs import SR570
from ametek import SR7230
from arc import SpecPro
from time import sleep, time
import scipy.constants as PC
from aopliab_common import DynamicPlot, json_write, json_load, getInstr


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


def get_pds(cal_file="calibrations.json"):
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
    (com, dll) = getInstr(rm, name)
    return SpecPro(com, dll)


def get_tia(rm, name="TransImpedanceAmp"):
    inst = getInstr(rm, name)
    return SR570(inst)


def get_lia(rm, name="LockInAmp"):
    inst = getInstr(rm, name)
    return SR7230(inst)


def get_filters():
    lc = json_load("local.json")
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

#hc = PC.h*PC.c/PC.e*1e9
#wd = "C:\\Users\\Maxwell\\Desktop\\Grede\\2015-03-10\\"
#
#
#def runMean(x, N):
#    return np.convolve(x, np.ones((N,))/N)[(N-1):]
#
#plt.interactive(True)
#plt.hold(False)
#SiRd = np.genfromtxt("12187.csv", skip_header=1, delimiter=",")
#SiR = interp1d(SiRd[:,0], SiRd[:,1], kind='cubic')
#GeRd = np.genfromtxt("12169.csv", skip_header=1, delimiter=",")
#GeR = interp1d(GeRd[:,0], GeRd[:,1]*0.071, kind='cubic')
#
#rm = visa.ResourceManager()
#
#tia_in = rm.open_resource("ASRL1::INSTR", baud_rate=9600, data_bits=8, stop_bits=visa.constants.StopBits.two,write_termination='\r\n')
#tia = SR570(tia_in)
#tia.sensitivity = 1e-3
#
#lia_in = rm.open_resource("TCPIP::169.254.150.230::50000::SOCKET", read_termination='\0',  write_termination='\0')
#lia = SR7230(lia_in)
#
#mon = SpecPro(4)
#
#
#outd = {}
#outd['cal2'] = {}
#outd['cal2']['sens'] = np.ones(5)
#outd['cal2']['dwell'] = np.zeros(5)
#outd['cal2']['tc'] = np.zeros(5)
#outd['cal2']['pd'] = np.array(["Si", "Si", "Si", "Si", "Ge"])
#
#json_write(outd, wd+"data.json")
#
#lam = np.array([
#    np.arange(200, 300, 5),
#    np.arange(300, 415, 5),
#    np.arange(390, 565, 5),
#    np.arange(540, 845, 5),
#    np.arange(820, 1605, 5)])
#
#N = 10
#cvolt = np.array([np.zeros((x.size, N)) for x in lam])
#cphas = np.array([np.zeros((x.size, N)) for x in lam])
#clam = np.array([np.zeros(x.shape) for x in lam])
#ccur = np.array([np.zeros(x.shape) for x in lam])
#cpow = np.array([np.zeros(x.shape) for x in lam])
#cphi = np.array([np.zeros(x.shape) for x in lam])
#
#p = DynamicPlot()
#tia.sensitivity = 1e-4
#sens = tia.sensitivity
#dwell = lia.filter_time_constant*8
#m = 1
#for idx, l in enumerate(lam[m]):
#    mon.wavelength = l
#    sleep(dwell)
#    for n in range(N):
#        tmp = lia.magphase
#        cvolt[m][idx, n] = tmp[0]
#        cphas[m][idx, n] = tmp[1]
#    clam[m][idx] = mon.wavelength
#    ccur[m][idx] = np.nanmean(cvolt[m][idx,:])*sens
#    if (m == 0 and idx == 0):
#        cpow[m][idx] = ccur[m][idx]/SiR(l)
#    elif (outd['cal2']['pd'][m] == "Si"):
#        cpow[m][idx] = ccur[m][idx]/SiR(clam[m][idx])
#    else:
#        cpow[m][idx] = ccur[m][idx]/GeR(clam[m][idx])
#    cphi[m][idx] = cpow[m][idx]*clam[m][idx]/hc
#    p.update(clam[m][idx], cphi[m][idx])
#
#outd['cal2']['sens'][m] = tia.sensitivity
#outd['cal2']['dwell'][m] = dwell
#outd['cal2']['tc'][m] = lia.filter_time_constant
#outd['cal2']['volt'] = cvolt
#outd['cal2']['phas'] = cphas
#outd['cal2']['cur'] = ccur
#outd['cal2']['pow'] = cpow
#outd['cal2']['phi'] = cphi
#outd['cal2']['lam'] = clam
#json_write(outd, wd+"data.json")
#tia.sensitivity = 1e-3
#mon.wavelength = 550.0
#
#
#calLam = np.hstack((clam[0], clam[1][:-1], clam[2][4:-1], clam[3][4:-1], clam[4][4:]))
#calPhi = interp1d(calLam, np.hstack((cphi[0], cphi[1][:-1], cphi[2][4:-1], cphi[3][4:-1], cphi[4][4:])),kind='cubic')
#calPow = interp1d(calLam, np.hstack((cphi[0], cpow[1][:-1], cpow[2][4:-1], cpow[3][4:-1], cpow[4][4:])),kind='cubic')
#
#
#
#nm = 'LVO_LSAT_36mT_2'
#outd[nm] = {}
#mvolt = np.array([np.zeros(x.shape) for x in lam])
#mphas = np.array([np.zeros(x.shape) for x in lam])
#mlam = np.array([np.zeros(x.shape) for x in lam])
#mcur = np.array([np.zeros(x.shape) for x in lam])
#mres = np.array([np.zeros(x.shape) for x in lam])
#meqe = np.array([np.zeros(x.shape) for x in lam])
#
#ivd = np.genfromtxt(wd+nm+".txt", delimiter='\t')
#
#outd[nm]['iv'] = ivd
#m1,b1 = np.linalg.lstsq(np.hstack((ivd[:,[0]],ivd[:,[0]]**0)), ivd[:,1])[0]
#outd[nm]['R'] = 1/m1
#
#outd[nm]['eqe'] = {}
#outd[nm]['eqe']['settings'] = {
#    'bias': np.zeros(5),
#    'sens': np.ones(5),
#    'lisens': np.ones(5),
#    'tc': np.ones(5),
#    'dwell': np.ones(5)}
#
#p = DynamicPlot()
##tia.bias_curr = 5e-3
#tia.bias_volt = 1.0
##tia.filter_type = 1
##tia.hp_freq = 300.0
#tia.volt_output = True
##tia.curr_output = False
#tia.sensitivity = 1e-6
#
#dwell = lia.filter_time_constant*8
#sens = tia.sensitivity
#m = 4
#for idx, l in enumerate(lam[m]):
#    mon.wavelength = l
#    sleep(dwell)
#    mlam[m][idx] = mon.wavelength
#    tmp = lia.magphase
#    mvolt[m][idx] = tmp[0]
#    mphas[m][idx] = tmp[1]
#    mcur[m][idx] = mvolt[m][idx]*sens
#    mres[m][idx] = mcur[m][idx]/calPow(mlam[m][idx])
#    meqe[m][idx] = mcur[m][idx]/calPhi(mlam[m][idx])
#    p.update(mlam[m][idx], meqe[m][idx])
#
#outd[nm]['eqe']['settings']['sens'][m] = tia.sensitivity
#outd[nm]['eqe']['settings']['lisens'][m] = lia.sensitivity
#outd[nm]['eqe']['settings']['bias'][m] = tia.bias_volt
#outd[nm]['eqe']['settings']['tc'][m] = lia.filter_time_constant
#outd[nm]['eqe']['settings']['dwell'][m] = dwell
#outd[nm]['eqe']['lam'] = mlam
#outd[nm]['eqe']['volt'] = mvolt
#outd[nm]['eqe']['phas'] = mphas
#outd[nm]['eqe']['cur'] = mcur
#outd[nm]['eqe']['res'] = mres
#outd[nm]['eqe']['eqe'] = meqe
#
#json_write(outd, wd+"data.json")
#
#tia.volt_output = False
#tia.curr_output = False
#tia.filter_type = 5
#tia.sensitivity = 1e-3
#mon.wavelength = 550.0
#
#tia.sensitivity = 1e-3
#mon.wavelength = 550.0
#
## Decay test
#K = 5001
#mon.wavelength = 300
#t = np.zeros(K)
#mvolt = np.zeros(K)
#mphas = np.zeros(K)
#st = np.zeros(K)
#svolt = np.zeros(K)
#sphas = np.zeros(K)
#
#t0 = time()
#mon.wavelength = 870
#for k in np.arange(K):
#    t[k] = time()
#    tmp = lia.magphase
#    mvolt[k] = tmp[0]
#    mphas[k] = tmp[1]
#
#mon.wavelength = 880
#st0 = time()
#for k in np.arange(K):
#    st[k] = time()
#    tmp = lia.magphase
#    svolt[k] = tmp[0]
#    sphas[k] = tmp[1]
#
#mon.close()
#tia_in.close()
#lia_in.close()
#
#def ftest(a, b='Defb', c='Defc'):
#    return (a, b, c)
#
#from lakeshore import LKS335
#cry_in = rm.open_resource("GPIB0::12::INSTR")
#cry = LKS335(cry_in)
