import numpy as np
import numpy.ma as ma
from aopliab_common import within_limits, nearest_index
from time import sleep


class PreAmp():
    """
    Generic base class for preamplifiers
    """
    inst = None
    freqs = np.array([])
    senss = np.array([])
    phases = np.array([])
    max_output = 1.
    current_freq = 1e3
    detects_overload = False
    overload_delay = 0.1
    adc = None
    ovrld = None

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
        """Returns next higher incremental sensitivity"""
        if self.adc is not None:
            curlev = np.abs(self.adc()*self.sensitivity)
        else:
            curlev = -1.
        nidx = self.sensitivity_index - 1
        if nidx < 0 or self.max_output < curlev/self.senss[nidx]:
            return np.nan
        if self.freq_cutoff(self.senss[nidx]) <= self.current_freq:
            return np.nan
        return self.senss[nidx]

    @property
    def dec_sensitivity(self):
        """Returns next lower incremental sensitivity"""
        nidx = self.sensitivity_index + 1
        if nidx >= self.senss.size:
            return np.nan
        nsens = self.senss[nidx]
        return nsens

    @property
    def phase_shift(self):
        """Phase shift for current sensitivity"""
        return self.phases[self.sensitivity_index]

    @phase_shift.setter
    def phase_shift(self, value):
        self.phases[self.sensitivity_index] = value

    @property
    def overload(self):
        """Returns True if currently overloaded"""
        if self.ovrld is not None:
            if self.ovrld():
                if self.adc is None:
                    return True
            else:
                return False
        if self.adc is not None:
            ms0 = self.adc()
            if (self.max_output < ms0):
                    sleep(0.02)
                    ms1 = self.adc()
                    while ms1 < ms0:
                        ms0 = ms1
                        sleep(0.02)
                        ms1 = self.adc()
            return (self.max_output < np.abs(self.adc()))
        else:
            return False

    def fix_overload(self):
        """Attempts to fix overload error and returns final overload state"""
        while (self.overload and not np.isnan(self.dec_sensitivity)):
            self.sensitivity = self.dec_sensitivity
        return self.overload

    @property
    def noise_base(self):
        """Returns baseline noise level of current settings"""
        pass


class LockInAmplifier():
    """Generic base class for lockin-amplifiers"""
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
    last_mags = np.array([])
    last_meas = np.array([])
    min_sleep = 0.001
    enbws = ma.array([])
    waittimes = ma.array([])
    lock_time_constant = True
    auto_phase_slope = 12

    def __init__(self, inst):
        pass

    @property
    def senss(self):
        """List of available sensitivities"""
        pass

    @property
    def sensitivity_index(self):
        pass

    @property
    def sensitivity(self):
        """Current sensitivity (full scale range)"""
        pass

    @sensitivity.setter
    def sensitivity(self, value):
        pass

    @property
    def inc_sensitivity(self):
        """Next higher sensitivity (more sensitive)"""
        nidx = self.sensitivity_index - 1
        rtn = np.ones(nidx.size)
        for k, n in enumerate(nidx):
            if n < 0:
                rtn[k] = np.nan
            else:
                rtn[k] = self.senss[n, k]
        return rtn

    @property
    def dec_sensitivity(self):
        """Next lower sensitivity (less sensitive)"""
        nidx = self.sensitivity_index + 1
        rtn = np.ones(nidx.size)
        for k, n in enumerate(nidx):
            if n >= self.senss.shape[0]:
                rtn[k] = np.nan
            else:
                rtn[k] = self.senss[n, k]
        return rtn

    def noise_measure(self, tc_noise, tc_mag, slope_noise,
                      slope_mag):
        """
        Perform noise measurement

        Parameters
        ----------
        tc_noise : Filter time constant for noise measurement
        tc_mag : Filter time constant for magnitude measurement
        slope_noise: Filter slope for noise measurement
        slope_mag: Filter slope for magnitude measurement
        """
        pass

    @property
    def time_constant(self):
        pass

    @time_constant.setter
    def time_constant(self, value):
        pass

    @property
    def wait_time(self):
        """Dwell time needed to reach 99 percent of value"""
        pass

    @property
    def slope(self):
        pass

    @slope.setter
    def slope(self):
        pass

    @property
    def enbw(self):
        """Equivalent noise bandwidth for current settings"""
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
        """Current measurement values (accounting for preamp)"""
        pass

    @property
    def cmags(self):
        """Current magnitude values (accounting for preamp)"""
        pass

    def adc(self, index):
        """Reading of analog to digital converter"""
        pass

    @property
    def jointSensitivity(self):
        """Product of sensitivity with preamp sensitivity"""
        sens = self.sensitivity
        for k, slia, pre in zip(range(sens.size), sens, self.preamps):
            if pre is not None:
                sens[k] = slia*pre.sensitivity
        return sens

    @property
    def meas(self):
        """Measurement function with automatic functions"""
        if np.any(np.isnan(self.last_mags)):
            self.last_mags = self.cmags
        scaled = False
        dwelled = False
        while ((self.auto_scale and not scaled) or
               (self.auto_dewll and not dwelled)):
            if self.auto_scale:
                scaled = not self.update_scale(self.last_mags)
            if self.auto_dwell:
                dwelled = not self.update_timeconstant(self.last_mags)
                sleep(self.wait_time)
            tmp = self.cmags
            if self.auto_scale and np.any(np.abs(1.-tmp/self.last_mags) > 0.5):
                scaled = False
            self.last_mags = tmp
        return self.cmeas

    def update_scale(self, mags):
        """
        Update sensitivities from last measurement magnitudes
        """
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
                elif m <= 0.3*js[k]:
                    nps = self.preamps[k].inc_sensitivity
                    if not np.isnan(nps):
                        self.preamps[k].sensitivity = nps
                        cps = nps
                        change = True
                    sleep(0.1)
                    if self.preamps[k].overload:
                        print("GAHH FUCK")
                        self.preamps[k].fix_overload()
                        m = m*self.preamps[k].sensitivity/cps
                        js[k] = js[k]*self.preamps[k].sensitivity/cps
                        cps = self.preamps[k].sensitivity
                        change = True
                if m >= 0.9*js[k]:
                    if not np.isnan(self.dec_sensitivity[k]):
                        self.sensitivity = (k, self.dec_sensitivity[k])
                        change = True
                    else:
                        nps = self.preamps[k].dec_sensitivity
                        if not np.isnan(nps):
                            self.preamps[k].sensitivity = nps
                            cps = nps
                            change = True
                if self.auto_phase and change:
                    if np.isnan(self.preamps[k].phase_shift):
                        ctc = self.time_constant
                        csl = self.slope
                        self.time_constant = self.auto_phase_tc
                        self.slope = self.auto_phase_slope
                        sleep(self.wait_time)
                        self.system_auto_phase(k)
                        self.time_constant = ctc
                        self.slope = csl
                        self.preamps[k].phase_shift = self.phaseoff[k]
                    else:
                        self.phaseoff = (k, self.preamps[k].phase_shift)
                remeas = (remeas or (change and (m > js[k] or m < 0.1*js[k])))
            if (not change and m <= 0.3*js[k] and
                    not np.isnan(self.inc_sensitivity[k])):
                self.sensitivity = (k, self.inc_sensitivity[k])
                remeas = (remeas or m < 0.1*js[k])
            elif (not change and m >= 0.9*js[k] and
                  not np.isnan(self.dec_sensitivity[k])):
                self.sensitivity = (k, self.dec_sensitivity[k])
                remeas = (remeas or m > js[k])
        return remeas

    def update_timeconstant(self, mags):
        """
        Update time constant from last magnitudes

        Uses noise estimates and tolerance settings
        """
        remeas = np.any(
            self.tolerance(mags) <
            (self.approx_noise(mags)*np.sqrt(self.enbw)))
        dfs = np.power(self.tolerance(mags)/self.approx_noise(mags), 2)
        tcs = np.zeros(mags.size)
        slopes = np.zeros(mags.size)
        wts = np.zeros(mags.size)
        for k, df in enumerate(dfs):
            if np.any(self.enbws <= df):
                k0, k1 = np.where(
                    self.waittimes == self.waittimes[
                        (self.enbws <= df)].min())
            else:
                k0, k1 = np.where(
                    self.waittimes == self.waittimes.max())
            if k0.size > 1 and k1.size > 1:
                k2 = np.argmin(np.array([
                                self.enbws[n0, n1] for n0, n1 in zip(k0, k1)]))
                k0 = k0[k2]
                k1 = k1[k2]
            else:
                k0 = k0[0]
                k1 = k1[0]
            tcs[k] = self.tcons[k0]
            slopes[k] = self.slopes[k1]
            wts[k] = self.waittimes[k0, k1]
        k = np.argmax(wts)
        tc = tcs[k]
        slope = slopes[k]
        wait = wts[k]
        if wait > self.tol_maxsettle:
            tc, slope, wait = self.best_tc_for_wait(self.tol_maxsettle)
            if self.wait_time >= wait:
                remeas = False
                return False
        if wait == self.wait_time:
            remeas = False
            return False
        remeas = (remeas or self.wait_time < wait)
        self.time_constant = tc
        self.slope = slope
        return remeas

    def best_tc_for_wait(self, wait):
        """Time constant that will reach at least 99 percent within time"""
        k0, k1 = np.where(self.enbws == self.enbws[self.waittimes <= wait].min())
        return (self.tcons[k0[0]], self.slopes[k1[0]], self.waittimes[k0[0], k1[0]])

    def tolerance(self, mags):
        """Tolerance based on last measured values"""
        return np.vstack((
            mags*self.tol_rel,
            self.tol_abs)).max(axis=0)

    def approx_noise(self, mags):
        """Noise approximation based on slope and baseline"""
        return (np.vstack((
            mags*self.noise_ratio,
            self.noise_base)).max(axis=0))
