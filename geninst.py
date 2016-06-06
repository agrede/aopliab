import numpy as np
import numpy.ma as ma
import timeit.default_timer as timer
from aopliab_common import within_limits, nearest_index
from sleep import sleep


class PreAmp():
    inst = None
    freqs = np.array([])
    senss = np.array([])
    phases = np.array([])
    max_output = 1.
    current_freq = 1e3
    detects_overload = False
    overload_delay = 0.1
    adc = None

    def __init__(self, inst):
        pass

    def close(self):
        pass

    @property
    def sensitivity_index(self):
        pass

    @property
    def sensitivity(self):
        pass

    @sensitivity.setter
    def sensitivity(self):
        pass

    def freq_cutoff(self, sens):
        pass

    @property
    def inc_sensitivity(self):
        if self.adc is not None:
            curlev = np.abs(self.adc()*self.sensitivity)
        else:
            curlev = -1.
        nidx = self.sensitivity_index - 1
        if nidx < 0 or self.max_output < curlev/self.senss[nidx]:
            return np.nan
        return self.senss[nidx]

    @property
    def dec_sensitivity(self):
        nidx = self.sensitivity_index + 1
        if nidx >= self.senss.size:
            return np.nan
        nsens = self.senss[nidx]
        if self.freq_cutoff(nsens) >= self.current_freq:
            return np.nan
        return nsens

    @property
    def phase_shift(self):
        return self.phases[self.sensitivity_index]

    @phase_shift.setter
    def phase_shift(self, value):
        self.phases[self.sensitivity_index] = value

    @property
    def overload(self):
        if self.adc is not None:
            return (self.max_output < np.abs(self.adc()))
        else:
            return False

    def fix_overload(self):
        while (self.overload and not np.isnan(self.dec_sensitivity)):
            self.sensitivity = self.dec_sensitivity
        return self.overload

    @property
    def noise_base(self):
        pass


class LockInAmplifier():
    senss = np.array([])
    tcons = np.array([])
    slopes = np.array([])
    noise_base = np.array([])
    noise_ratio = np.array([])
    tol_maxsettle = 20.
    tol_rel = np.array([])
    tol_abs = np.array([])
    preamps = np.array([])
    auto_scale = False
    auto_dewll = False
    auto_phase = False
    auto_phase_tc = 5.
    monitors = np.array([])
    measures = np.array([])
    last_meas = np.array([])
    min_sleep = 0.001
    enbws = ma.array([])
    waittimes = ma.array([])
    lock_time_constant = True

    def __init__(self, inst):
        pass

    @property
    def sensitivity_index(self):
        pass

    @property
    def sensitivity(self):
        pass

    @sensitivity.setter
    def sensitivity(self, value):
        pass

    @property
    def inc_sensitivity(self):
        nidx = self.sensitivity_index - 1
        rtn = np.ones(nidx.size)
        for k, n in enumerate(nidx):
            if n < 0:
                rtn[k] = np.nan
            else:
                rtn[k] = self.senss[n]
        return rtn

    @property
    def dec_sensitivity(self):
        nidx = self.sensitivity_index + 1
        rtn = np.ones(nidx.size)
        for k, n in enumerate(nidx):
            if n >= self.senss.shape[0]:
                rtn[k] = np.nan
            elif n >= self.senss.size:
                rtn[k] = np.nan
            else:
                rtn[k] = self.senss[n]
        return rtn

    def noise_measure(self, tc_noise, tc_mag, slope_noise,
                      slope_mag):
        pass

    @property
    def time_constant(self):
        pass

    @time_constant.setter
    def time_constant(self, value):
        pass

    @property
    def dwell(self):
        pass

    @property
    def slope(self):
        pass

    @slope.setter
    def slope(self):
        pass

    @property
    def enbw(self):
        pass

    @property
    def freq(self):
        pass

    @property
    def phaseoff(self):
        pass

    @phaseoff.setter
    def phaseoff(self, value):
        pass

    def system_auto_phase(self):
        pass

    @property
    def cmeas(self):
        pass

    @property
    def cmags(self):
        pass

    def adc(self, index):
        pass

    @property
    def jointSensitivity(self):
        sens = self.sensitivity
        for k, slia, pre in zip(range(sens.size), sens, self.preamps):
            if pre is not None:
                sens[k] = slia*pre.sensitivity
        return sens

    @property
    def meas(self):
        if np.any(np.isnan(self.last_mags)):
            self.last_mags = self.cmags
        scaled = False
        dwelled = False
        while ((self.auto_scale and not scaled) or
               (self.auto_dewll and not dwelled)):
            if self.auto_scale:
                scaled = not self.update_scale(self.last_mags)
            if self.auto_dewll:
                dwelled = not self.update_timeconstant(self.last_mags)
            self.last_mags = self.cmags
        return self.cmeas

    def update_scale(self, mags):
        remeas = False
        js = self.jointSensitivity
        for k, m in enumerate(mags):
            change = False
            if self.preamps[k] is not None:
                cps = self.preamps[k].sensitivity
                if self.preamps[k].overload:
                    self.preamps[k].fix_overload()
                    m = m*self.preamps[k].sensitivity/cps
                    js[k] = js[k]*self.preamps[k].sensitivity/cps
                    cps = self.preamps[k].sensitivity
                    change = True
                elif m <= 0.3*js:
                    nps = self.preamps.inc_sensitivity
                    if not np.isnan(nps):
                        self.preamps[k].sensitivity = nps
                        cps = nps
                        change = True
                if m >= 0.9*js:
                    nps = self.preamps[k].dec_sensitivity
                    if not np.isnan(nps):
                        self.preamps[k].sensitivity = nps
                        cps = nps
                        change = True
                if self.preamps[k].overload:
                    self.preamps[k].fix_overload()
                    m = m*self.preamps[k].sensitivity/cps
                    js[k] = js[k]*self.preamps[k].sensitivity/cps
                    cps = self.preamps[k].sensitivity
                    change = True
                if self.auto_phase and change:
                    if np.isnan(self.preamps[k].phase_shift):
                        ctc = self.time_constant
                        self.time_constant = self.auto_phase_tc
                        sleep(self.dwell)
                        self.system_auto_phase()
                        self.time_constant = ctc
                        self.preamps[k].phase_shift = self.phaseoff
                    else:
                        self.phaseoff = self.preamps[k].phase_shift
                remeas = (change and (remeas or m > js or m < 0.01))
            if (not change and m <= 0.3*js[k] and
                    not np.isnan(self.inc_sensitivity[k])):
                self.sensitivity = (k, self.inc_sensitivity[k])
                remeas = (remeas or m < 0.01)
            elif (not change and m >= 0.9*self.sensitivity[k] and
                  not np.isnan(self.dec_sensitivity[k])):
                self.sensitivity = (k, self.dec_sensitivity[k])
                remeas = (remeas or m > self.sensitivity[k])
        return remeas

    def update_timeconstant(self, mags):
        remeas = np.any(
            self.tolerance(mags) >
            (self.approx_noise(mags)/np.sqrt(self.enbw)))
        dfs = np.power(self.tolerance(mags)/self.approx_noise(mags), 2)
        tcs = np.zeros(mags.size)
        slopes = np.zeros(mags.size)
        wts = np.zeros(mags.size)
        for k, df in enumerate(dfs):
            k0, k1 = np.where(
                self.waittimes == self.waittimes[
                    (self.enbws <= df)].min())
            if k0.size > 0 and k1.size > 0:
                k0, k1 = np.argmin(self.enbws)
            tcs[k] = self.tcons[k0]
            slopes[k] = self.slopes[k1]
            wts[k] = self.waittimes[k0, k1]
        k = np.argmax(wts)
        tc = tcs[k]
        slope = slopes[k]
        wait = wts[k]
        if wait > self.tol_maxsettle:
            tc, slope, wait = self.best_tc_for_wait(self.tol_maxsettle)
        remeas = (remeas and self.wait_time < wait)
        self.time_constant = tc
        self.slope = slope
        return remeas

    def best_tc_for_wait(self, wait):
        k0, k1 = np.argmin(self.enbws[self.waittimes <= wait])
        return (self.tcons[k0], self.slopes[k1], self.waittimes[k0, k1])

    def tolerance(self, mags):
        return np.vstack((
            mags*self.tol_abs,
            self.tol_rel)).max(axis=0)

    def approx_noise(self, mags):
        return (np.vstack((
            mags*self.noise_ratio,
            self.noise_base)).max(axis=0))
