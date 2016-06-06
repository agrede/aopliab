import json
import numpy as np
from aopliab_common import within_limits, nearest_index
import numpy.ma as ma
from scipy.interpolate import interp1d
from geninst import PreAmp, LockInAmplifier


class SR570(PreAmp):
    """
    PyVISA wrapper for SRS SR570 Transimpedance amplifier
    """

    inst = None
    _volt_bias_enabled = False
    _curr_bias_enabled = False
    _curr_bias_sign = 1
    _curr_bias_index = 0
    _volt_bias_index = 0
    _sens_index = 27
    _gain_mode_index = 0
    _invert_output = 0
    _output = True
    _lp_freq_index = 15
    _hp_freq_index = 0
    _filter_index = 5
    currs = np.array([])
    config = None
    preamps = np.array([None])

    def __init__(self, inst):
        self.inst = inst
        self.inst.write("*RST")
        cfg_file = open("configs/srs.json")
        cfg = json.load(cfg_file)
        cfg_file.close()
        self.config = cfg['SR570']
        self.freqs = np.array(self.config['frequencies'])
        self.currs = np.array(self.config['currents'])
        tmp = np.array(self.config['sensitivities'])
        self.senss = ma.masked_where(tmp < 0, tmp)
        self.limits = np.array(self.config['sensitivity_limits'])
        self.bw = np.array([
            interp1d(np.log(self.limits[:, 0]),
                     np.log(self.limits[:, 2])),
            interp1d(np.log(self.limits[:, 0]),
                     np.log(self.limits[:, 1]))])
        self.noise_bases = np.array([
            interp1d(np.log(self.limits[:, 0]),
                     np.log(self.limits[:, 4])),
            interp1d(np.log(self.limits[:, 0]),
                     np.log(self.limits[:, 3]))])
        self.sensitivity = 1e-3
        self.gain_mode = 0

    def close(self):
        self.inst.close()

    def nearest_volt_index(self, v):
        if (abs(int(v*1e3)) > 5000):
            return int(np.sign(v)*5000)
        return int(v*1e3)

    def nearest_freq_index(self, freq, rndup):
        return nearest_index(freq, self.freqs, rndup)

    @property
    def filter_type(self):
        return self._filter_index

    @filter_type.setter
    def filter_type(self, value):
        if (within_limits(int(value), [0, 5])):
            self._filter_index = int(value)
            self.inst.write("FLTT%d" % value)
            if (self._filter_index <= 2):
                self.inst.write("HFRQ%d" % self._hp_freq_index)
            if (self._filter_index >= 2):
                self.inst.write("LFRQ%d" % self._lp_freq_index)

    @property
    def lp_freq(self):
        return self.freqs[self._lp_freq_index]

    @lp_freq.setter
    def lp_freq(self, value):
        self._lp_freq_index = self.nearest_freq_index(value, True)
        if (within_limits(self._filter_index, [2, 4])):
            self.inst.write("LFRQ%d" % self._lp_freq_index)

    @property
    def hp_freq(self):
        return self.freqs[self._hp_freq_index]

    @hp_freq.setter
    def hp_freq(self, value):
        self._hp_freq_index = self.nearest_freq_index(value, False)
        if (within_limits(self._filter_index, [0, 2])):
            self.inst.write("HFRQ%d" % self._hp_freq_index)

    @property
    def bias_volt(self):
        return float(self._volt_bias_index)*1e-3

    @bias_volt.setter
    def bias_volt(self, value):
        self._volt_bias_index = self.nearest_volt_index(value)
        self.inst.write("BSLV%d" % self._volt_bias_index)

    @property
    def volt_output(self):
        return self._volt_bias_enabled

    @volt_output.setter
    def volt_output(self, value):
        if (value):
            self._volt_bias_enabled = True
            self.inst.write("BSON1;BSLV%d" % self._volt_bias_index)
        else:
            self._volt_bias_enabled = False
            self.inst.write("BSON0")

    def nearest_curr_index(self, curr, rndup=False):
        return nearest_index(abs(curr), self.currs, rndup)

    @property
    def bias_curr(self):
        return self.currs[self._curr_bias_index]

    @bias_curr.setter
    def bias_curr(self, value):
        self._curr_bias_index = self.nearest_curr_index(value)
        if (np.signbit(value)):
            self._curr_bias_sign = 0
        else:
            self._curr_bias_sign = 1
        self.inst.write("IOSN%d;IOLV%d" % (
                    self._curr_bias_sign, self._curr_bias_index))

    @property
    def curr_output(self):
        return self._curr_bias_enabled

    @curr_output.setter
    def curr_output(self, value):
        if (value):
            self._curr_bias_enabled = True
            self.inst.write("IOON1;IOSN%d;IOLV%d" % (
                self._curr_bias_sign, self._curr_bias_index))
        else:
            self._curr_bias_enabled = False
            self.inst.write("IOON0")

    def nearest_sens_index(self, sens, rndup=True):
        return nearest_index(sens, self.senss, rndup)

    @property
    def sensitivity_index(self):
        return self._sens_index

    @property
    def sensitivity(self):
        return self.senss[self._sens_index]

    @sensitivity.setter
    def sensitivity(self, value):
        self._sens_index = self.nearest_sens_index(value)
        self.inst.write("SENS%d" % self._sens_index)

    @property
    def gain_mode(self):
        return self._gain_mode_index

    @gain_mode.setter
    def gain_mode(self, value):
        if (within_limits(int(value), [0, 2])):
            self._gain_mode_index = int(value)
            self.inst.write("GNMD%d" % self._gain_mode_index)

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, value):
        if (value):
            self._output = True
            self.inst.write("BLNK0")
        else:
            self._output = False
            self.inst.write("BLNK1")

    @property
    def invert_output(self):
        return self._invert_output

    @invert_output.setter
    def invert_output(self, value):
        if (value):
            self._invert_output = True
            self.inst.write("INVT1")
        else:
            self._invert_output = False
            self.inst.write("INVT0")

    def reset_overload(self):
        self.inst.write("ROLD")

    def freq_cutoff(self, sens):
        gmi = self._gain_mode_index
        if gmi > 1:
            gmi = 0
        return self.bw[gmi](sens)

    @property
    def noise_base(self):
        gmi = self._gain_mode_index
        if gmi > 1:
            gmi = 0
        return self.bw[gmi](self.sensitivity)


class SR830():
    """
    PyVISA wrapper for SR830 Lock-in amplifier
    """

    inst = None
    config = None

    def __init__(self, inst):
        self.inst = inst
        cfg_file = open("configs/srs.json")
        cfg = json.load(cfg_file)
        cfg_file.close()
        self.config = cfg['SR830']
        tmp = np.array(self.config['time_constants'])
        self.tcons = ma.masked_where(tmp < 0., tmp)
        tmp = np.array(self.config['sensitivities'])
        self.senssall = ma.masked_where(tmp < 0., tmp)
        tmp = np.array(self.config['slopes'])
        self.slopes = ma.masked_where(tmp < 0., tmp)
        bwm = np.atleast_2d(self.config['slope_enbw'])
        sw = np.atleast_2d(self.config['slope_wait'])
        tc = np.atleast_2d(self.tcons).T
        self.enbws = bwm/tc
        self.waittimes = sw*tc

    @property
    def imode(self):
        return int(self.inst.query_ascii_values("ISRC?")[0])

    @imode.setter
    def imode(self, value):
        if within_limits(value, [0, 3]):
            self.inst.write("ISRC %d" % value)

    @property
    def float_shield(self):
        return (int(self.inst.query_ascii_values("IGND?")[0]) == 0)

    @float_shield.setter
    def float_shield(self, value):
        if (value):
            self.inst.write("IGND 0")
        else:
            self.inst.write("IGND 1")

    @property
    def dc_couple(self):
        return (int(self.inst.query_ascii_values("ICPL?")) == 1)

    @dc_couple.setter
    def dc_couple(self, value):
        if (value):
            self.inst.write("ICPL 1")
        else:
            self.inst.write("ICPL 0")

    @property
    def senss(self):
        return self.senssall[:, self.imode]

    @property
    def sensitivity(self):
        sen = int(self.inst.query_ascii_values("SENS?")[0])
        return self.senss[sen]

    @sensitivity.setter
    def sensitivity(self, value):
        idx = nearest_index(value, self.senss, True)
        self.inst.write("SENS %d" % self.senss[idx])

    @property
    def reserve_mode(self):
        return int(self.inst.query_ascii_values("RMOD?")[0])

    @reserve_mode.setter
    def reserve_mode(self, value):
        if within_limits(value, [0, 2]):
            self.inst.write("RMOD %d" % value)

    @property
    def line_filter(self):
        return int(self.inst.query_ascii_values("ILIN?")[0])

    @line_filter.setter
    def line_filter(self, value):
        if within_limits(value, [0, 3]):
            self.inst.write("ILIN %d" % value)

    @property
    def fmod(self):
        return int(self.inst.query_ascii_values("FMOD?")[0])

    @fmod.setter
    def fmod(self, value):
        if within_limits(value, [0, 1]):
            self.inst.write("FMOD %d" % value)

    @property
    def rslp(self):
        return int(self.inst.query_ascii_values("RSLP?")[0])

    @rslp.setter
    def rslp(self, value):
        if within_limits(value, [0, 2]):
            self.inst.write("RSLP %d" % value)

    @property
    def harm(self):
        return int(self.inst.query_ascii_values("HARM?")[0])

    @harm.setter
    def harm(self, value):
        if within_limits(value, [1, 19999]):
            self.inst.write("HARM %d" % value)

    @property
    def slvl(self):
        return self.inst.query_ascii_values("SLVL?")

    @slvl.setter
    def slvl(self, value):
        if within_limits(value, [0.004, 5.00]):
            self.inst.write("SLVL %0.3e" % value)

    @property
    def ref_phase(self):
        return self.inst.query_ascii_values("PHAS?")[0]

    @ref_phase.setter
    def ref_phase(self, value):
        if within_limits(value, [-360.0, 729.99]):
            self.inst.write("PHAS %0.2e" % value)

    @property
    def ref_freq(self):
        return self.inst.query_ascii_values("FREQ?")

    @ref_freq.setter
    def ref_freq(self, value):
        if within_limits(value, [0.001, 102e3]):
            self.inst.write("FREQ %0.5e" % value)

    @property
    def time_constant_index(self):
        return int(self.query_ascii_values("OFLT?")[0])

    @property
    def time_constant(self):
        return self.tcons[self.time_constant_index]

    @time_constant.setter
    def time_constant(self, value):
        idx = nearest_index(value, self.tcons, True)
        self.inst.write("OFLT %d" % idx)

    @property
    def filter_sync(self):
        return (int(self.inst.query_ascii_values("SYNC?")[0]) == 1)

    @filter_sync.setter
    def filter_sync(self, value):
        if (value):
            self.inst.write("SYNC 1")
        else:
            self.isnt.write("SYNC 0")

    @property
    def slope_index(self):
        return int(self.inst.query_ascii_values("OFSL?")[0])

    @property
    def slope(self):
        return self.slopes[self.slope_index]

    @slope.setter
    def slope(self, value):
        idx = nearest_index(value, self.slopes, False)
        self.inst.write("SLOPE %d" % idx)

    def system_auto_phase(self, idx):
        self.inst.write("APHS")

    @property
    def wait_time(self):
        return self.waittimes[self.time_constant_index, self.slope_index]

    @property
    def enbw(self):
        return self.enbws[self.time_constant_index, self.slope_index]

    @property
    def cmags(self):
        rtn = self.inst.query_ascii_values("OUTP? 3")
        if self.preamps[0] is not None:
            rtn = rtn[0]*self.preamps[0].sensitivity
        return rtn

    def adc(self, index):
        if within_limits(index, [0, 3]):
            return self.inst.query_ascii_values("OAUX? %d" (index+1))[0]
        return np.nan

    @property
    def cmeas(self):
        rtn = self.inst.query_ascii_values("SNAP? 1,2,5,6,7,8")
        if self.preamps[0] is not None:
            rtn[:2] = rtn[:2]*self.preamps[0].sensitivity
        return rtn

    @property
    def x(self):
        return self.inst.query_ascii_values("OUTP? 1")[0]

    @property
    def y(self):
        return self.inst.query_ascii_values("OUTP? 1")[0]

    @property
    def xy(self):
        return self.inst.query_ascii_values("SNAP? 1,2")

    @property
    def mag(self):
        return self.inst.query_ascii_values("OUTP? 3")[0]

    @property
    def phase(self):
        return self.inst.query_ascii_values("OUTP? 4")[0]

    @property
    def magphase(self):
        return self.inst.query_ascii_values("SNAP? 3,4")
