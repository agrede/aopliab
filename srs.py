import json
import numpy as np
from aopliab_common import within_limits, nearest_index, get_bool, set_bool
import numpy.ma as ma
from scipy.interpolate import interp1d
from geninst import PreAmp, LockInAmplifier
from time import sleep
import weakref

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
        self.phases = np.zeros(self.senss.size)

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
        return np.exp(self.bw[gmi](np.log(sens)))

    @property
    def noise_base(self):
        gmi = self._gain_mode_index
        if gmi > 1:
            gmi = 0
        return np.exp(self.noise_bases[gmi](np.log(self.sensitivity)))


class SR830(LockInAmplifier):
    """
    PyVISA wrapper for SR830 Lock-in amplifier
    """

    inst = None
    config = None
    preamps = np.array([None])
    auto_dewll = False

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
        return self.senssall[:, [self.imode]]

    @property
    def sensitivity_index(self):
        return np.array([int(self.inst.query_ascii_values("SENS?")[0])])

    @property
    def sensitivity(self):
        return np.array([self.senss[self.sensitivity_index[0], 0]])

    @sensitivity.setter
    def sensitivity(self, value):
        if type(value) is np.ndarray:
            for k, v in value:
                idx = nearest_index(v, self.senss[:, k], True)
                if k == 0:
                    self.inst.write("SENS %d" % idx)
        elif type(value) is tuple:
            k, v = value
            idx = nearest_index(v, self.senss[:, k], True)
            if k == 0:
                self.inst.write("SENS %d" % idx)
        else:
            idx = nearest_index(value, self.senss[:, 0], True)
            self.inst.write("SENS %d" % idx)

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
        """ Source Level """
        if within_limits(value, [0.004, 5.00]):
            self.inst.write("SLVL %0.3e" % value)

    @property
    def phaseoff(self):
        return np.array(self.inst.query_ascii_values("PHAS?"))

    @phaseoff.setter
    def phaseoff(self, value):
        if within_limits(value, [-360.0, 729.99]):
            self.inst.write("PHAS %0.2e" % value)

    @property
    def ref_freq(self):
        return self.inst.query_ascii_values("FREQ?")[0]

    @ref_freq.setter
    def ref_freq(self, value):
        if within_limits(value, [0.001, 102e3]):
            self.inst.write("FREQ %0.5e" % value)

    @property
    def time_constant_index(self):
        return int(self.inst.query_ascii_values("OFLT?")[0])

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
        self.inst.write("OFSL %d" % idx)

    def system_auto_phase(self, idx):
        self.inst.write("APHS")

    @property
    def wait_time(self):
        return self.waittimes.data[self.time_constant_index, self.slope_index]

    @property
    def enbw(self):
        return self.enbws.data[self.time_constant_index, self.slope_index]

    @property
    def cmags(self):
        rtn = np.array(self.inst.query_ascii_values("OUTP? 3"))
        if self.preamps[0] is not None:
            rtn = rtn*self.preamps[0].sensitivity
        return rtn

    def adc(self, index):
        if within_limits(index, [0, 3]):
            return self.inst.query_ascii_values(
                "OAUX? %d" % (index+1))[0]
        return np.nan

    @property
    def cmeas(self):
        rtn = np.array(self.inst.query_ascii_values("SNAP? 1,2,5,6,7,8"))
        if self.preamps[0] is not None:
            rtn[:2] = rtn[:2]*self.preamps[0].sensitivity
        return rtn

    def noise_measure(self, tc_noise, tc_mag, slope_noise,
                      slope_mag):
        cs = self.slope
        ctc = self.time_constant
        rtn = np.zeros((1, 2))
        self.inst.write("DDEF 1,2,0")
        self.inst.write("DDEF 2,2,0")
        self.time_constant = tc_noise
        self.slope = slope_noise
        sleep(5.)
        rtn[0, 1] = np.sqrt(np.power(
            np.array(self.inst.query_ascii_values("SNAP? 10,11")),
            2).sum()/self.enbw)
        self.slope = slope_mag
        self.time_constant = tc_mag
        sleep(self.wait_time)
        rtn[0, 0] = self.mag
        if self.preamps[0] is not None:
            rtn = rtn*self.preamps[0].sensitivity
        self.slope = cs
        self.time_constant = ctc
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


class DS345():
    """
    PyVISA wrapper for SRS DS345 Waveform Generator
    """

    inst = None
    config = None
    _highz = 1.
    frequency_limits = None
    output_range = None
    output_center = 0.0   # 0.0: disabled, 1.0: +Vpp/2, -1.0: -Vpp/2

    def __init__(self, inst):
        self.inst = inst
        cfg_file = open("configs/srs.json")
        cfg = json.load(cfg_file)
        cfg_file.close()
        self.config = cfg['DS345']
        self.frequency_limits = np.array(self.config['frequency_limits'])
        self.output_range = self.config['output_range']

    def close(self):
        self.inst.close()

    def cls(self):
        self.inst.write("*CLS")

    def triger(self):
        self.inst.write("*TRG")
        
    @property
    def highz(self):
        return (self._highz > 1.)

    @highz.setter
    def highz(self, value):
        if value:
            self._highz = 2.0
        else:
            self._highz = 1.0

    @property
    def func(self):
        return int(self.inst.query_ascii_values("FUNC?")[0])

    @func.setter
    def func(self, value):
        if within_limits(int(value), [0, 5]):
            self.inst.write("FUNC %d" % value)

    @property
    def freq(self):
        return self.inst.query_ascii_values("FREQ?")[0]

    @freq.setter
    def freq(self, value):
        if within_limits(value, self.frequency_limits[self.func]):
            self.inst.write("FREQ %.11e" % value)

    def setOutput(self, coff, camp, noff, namp):
        if noff is not None:
            if namp is not None:
                if (np.abs(noff)+camp/2. <= self.output_range):
                    self.inst.write("OFFS %.3e" % noff)
                    self.inst.write("AMPL %.3eVP" % namp)
                elif (np.abs(coff)+namp/2. <= self.output_range):
                    self.inst.write("AMPL %.3eVP" % namp)
                    self.inst.write("OFFS %.3e" % noff)
                else:
                    self.inst.write("OFFS 0")
                    self.inst.write("AMPL %.3eVP" % namp)
                    self.inst.write("OFFS %.3e" % noff)
            else:
                self.inst.write("OFFS %.3e" % noff)
        elif namp is not None:
            self.inst.write("AMPL %.3eVP" % namp)

    @property
    def offs(self):
        return self.inst.query_ascii_values("OFFS?")[0]

    @offs.setter
    def offs(self, value):
        coff = self.offs/self._highz
        camp = self.ampl/self._highz
        noff = value/(self._highz)
        namp = None
        if (np.abs(self.output_center) < 1.):
            if (np.abs(noff) > self.output_range):
                namp = 0.
                noff = np.sign(noff)*self.output_range
            elif (camp/2.+np.abs(noff) > self.output_range):
                namp = 2.*(self.output_range - np.abs(noff))
            self.setOutput(coff, camp, noff, namp)

    @property
    def ampl(self):
        return (self._highz*float((self.inst.query("AMPL?"))[:-3]))

    @ampl.setter
    def ampl(self, value):
        coff = self.offs/self._highz
        camp = self.ampl/self._highz
        noff = None
        namp = np.abs(value)/(self._highz)
        if (np.abs(self.output_center) < 1.):
            if (namp/2. > self.output_range):
                namp = 2.*self.output_range
                noff = 0.
            elif (namp/2.+np.abs(coff) > self.output_range):
                noff = np.sign(coff)*(self.output_range - namp/2.)
        else:
            if (namp/2. > self.output_range):
                namp = self.output_range/2.
            noff = namp/2.*self.output_range
        self.setOutput(coff, camp, noff, namp)


class DG645():
    """
    Wrapper for DG645 Delay generator
    """

    inst = None
    delay_range = None
    ampl_range = None
    output_range = None
    offset_range = None
    inhibit_range = None
    chan_range = None
    chan_out_range = None
    trig_rate_range = None
    trig_thresh_range = None
    trig_source_range = None

    def __init__(self, inst):
        self.inst = inst
        cfg_file = open("configs/srs.json")
        cfg = json.load(cfg_file)
        cfg_file.close()
        self.config = cfg['DG645']
        self.delay_range = np.array(self.config['delay_range'])
        self.ampl_range = np.array(self.config['ampl_range'])
        self.output_range = np.array(self.config['output_range'])
        self.offset_range = np.array(self.config['offset_range'])
        self.inhibit_range = np.array(self.config['inhibit_range'])
        self.chan_range = np.array(self.config['channel_range'])
        self.chan_out_range = np.array(
            self.config['channel_output_range'])
        self.trig_rate_range = np.array(
            self.config['trigger_rate_range'])
        self.trig_thresh_range = np.array(
            self.config['trigger_threshold_range'])
        self.trig_source_range = np.array(
            self.config['trigger_source_range'])

    @property
    def trig_adv(self):
        return get_bool(self.inst, "ADVT")

    @trig_adv.setter
    def trig_adv(self, value):
        set_bool(self.inst, "ADVT", value)

    @property
    def trig_hold(self):
        return self.inst.query_ascii_values("HOLD?")[0]

    @trig_hold.setter
    def trig_hold(self, value):
        if within_limits(value, self.delay_range):
            self.inst.write("HOLD {}".format(value))

    @property
    def inhibit(self):
        return int(self.inst.query_ascii_values("INHB?")[0])

    @inhibit.setter
    def inhibit(self, value):
        if within_limits(int(value), self.inhibit_range):
            self.inst.write("INHB %d" % value)

    @property
    def trig_thresh(self):
        return self.inst.query_ascii_values("TLVL?")[0]

    @trig_thresh.setter
    def trig_thresh(self, value):
        if within_limits(value, self.trig_thresh_range):
            self.inst.write("TLVL %f" % value)

    @property
    def trig_rate(self):
        return self.inst.query_ascii_values("TRAT?")[0]

    @trig_rate.setter
    def trig_rate(self, value):
        if within_limits(value, self.trig_rate_range):
            self.inst.write("TRAT %e" % value)

    @property
    def trig_source(self):
        return int(self.inst.query_ascii_values("TSRC?")[0])

    @trig_source.setter
    def trig_source(self, value):
        if within_limits(int(value), self.trig_source_range):
            self.inst.write("TSRC %d" % value)

    def t0_delay(self, chan):
        if chan == 0:
            return 0.
        tmp = self.inst.query_ascii_values("DLAY? %d" % chan)
        return (tmp[1]+self.t0_delay(int(tmp[0])))


class DG645Channel():
    """
    Delay channel for DG645
    """
    _parent = None
    _number = None

    def __init__(self, parent, number):
        self._parent = weakref.proxy(parent)
        self._number = int(number)
        self.write("LINK %d,%d" % (self.intNum[1], self.intNum[0]))

    def write(self, value):
        return self._parent.inst.write(value)

    def query(self, value):
        return self._parent.inst.query_ascii_values(value)

    @property
    def intNum(self):
        return (np.array([0, 1])+2*(self._number))

    @property
    def link(self):
        return int(self.query("LINK? %d" % self.intNum[0])[0])

    @link.setter
    def link(self, value):
        if within_limits(int(value), self._parent.chan_range):
            self.write("LINK %d,%d" % (self.intNum[0], value))

    @property
    def delay(self):
        return self.query("DLAY? %d" % self.intNum[0])[1]

    @delay.setter
    def delay(self, value):
        if within_limits(value, self._parent.delay_range):
            tmp = "{}".format(value)
            self.write(
                "DLAY %d,%d,%s" % (self.intNum[0], self.link, tmp))

    @property
    def ampl(self):
        return self.query("LAMP? %d" % self._number)[0]

    @ampl.setter
    def ampl(self, value):
        if within_limits(value, self._parent.ampl_range):
            self.write("LAMP %d,%f" % (self._number, value))

    @property
    def offset(self):
        return self.query("LOFF? %d" % self._number)[0]

    @offset.setter
    def offset(self, value):
        if within_limits(value, self._parent.offset_range):
            self.write("LOFF %d,%f" % (self._number, value))

    @property
    def polarity_positive(self):
        return (self.query("LPOL? %d" % self._number)[0] > 0)

    @polarity_positive.setter
    def polarity_positive(self, value):
        if value:
            self.write("LPOL %d,1" % self._number)
        else:
            self.write("LPOL %d,0" % self._number)

    @property
    def width(self):
        return self.query("DLAY? %d" % self.intNum[1])[1]

    @width.setter
    def width(self, value):
        if within_limits(value, self._parent.delay_range):
            tmp = "{}".format(value)
            self.write(
                "DLAY %d,%d,%s" % (self.intNum[1], self.intNum[0], tmp))

    def out_ttl(self):
        self.offset = 0.
        self.ampl = 4.
        self.polarity_positive = True

    def out_nim(self):
        self.offset = 0.
        self.ampl = 0.8
        self.polarity_positive = False
