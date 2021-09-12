import re
from aopliab.aopliab_common import within_limits, json_load, get_bool, set_bool
from aopliab.geninst import ParameterAnalyzer, SMU
import numpy as np
import weakref
from time import time
from numbers import Number
import os


PKGPTH = os.path.dirname(__file__)+"/"


class HP4192A():
    """
    PyVISA wrapper fro HP 4192A impedence analyzer
    """

    config = {}
    freq_range = None
    bias_range = None
    osc_range = None
    _osc = 0.005
    _bias = 0.00
    _freq = 1e3
    _series = True
    rdrgx = re.compile(r'([+-]\d+\.\d+E[+-]\d+).+([+-]\d+\.\d+E[+-]\d+)')
    timeout = 10.

    def __init__(self, inst):
        self.inst = inst
        cfg = json_load(PKGPTH+"configs/keysight.json")
        self.config = cfg['HP4192A']
        self.freq_range = np.array(self.config['freq_range'])
        self.bias_range = np.array(self.config['bias_range'])
        self.osc_range = np.array(self.config['osc_range'])
        self.inst.write("DC1")
        self.inst.write("A2B1C2R8D1F0H0V1T3")

    @property
    def series(self):
        return self._series

    @series.setter
    def series(self, value):
        if (self._series != value):
            self._series = bool(value)
            if (value):
                self.inst.write("C2")
            else:
                self.inst.write("C3")

    @property
    def freq(self):
        return self._freq

    @freq.setter
    def freq(self, value):
        if within_limits(value, self.freq_range):
            self._freq = value
            self.inst.write("FR"+("%0.8f" % (value*1e-3))[:9]+"EN")

    @property
    def bias(self):
        return self._bias

    @bias.setter
    def bias(self, value):
        if within_limits(value, self.bias_range):
            self._bias = value
            self.inst.write("BI%0.2fEN" % value)

    def bias_off(self):
        self.inst.write("I0")

    @property
    def osc(self):
        return self._osc

    @osc.setter
    def osc(self, value):
        if within_limits(value, self.osc_range):
            self._osc = value
            self.inst.write("OL%0.3fEN" % value)

    @property
    def measurement(self):
        t0 = time()
        self.inst.write("EX")
        tmp = 0
        while ((tmp & 1) != 1 and time()-t0 < self.timeout):
            tmp = self.inst.stb
        mt = self.rdrgx.search(str(self.inst.read_raw()))
        return np.array([float(mt.group(1)), float(mt.group(2))])


class InfiniiVision5000():
    """
    PyVISA wrapper for InfiniiVision 5000 Oscilloscope
    """

    config = {}
    last_wav_sour = None
    chan_range = None

    def __init__(self, inst):
        self.inst = inst
        #self.inst.write("*RST; *CLS")
        cfg = json_load(PKGPTH+'configs/keysight.json')
        self.config = cfg['InfiniiVision5000']
        self.chan_range = self.config['chan_range']
        self.wave_source = 1

    @property
    def wave_source(self):
        return self.last_wav_source

    @wave_source.setter
    def wave_source(self, value):
        if within_limits(int(value), self.chan_range):
            if self.last_wav_sour != int(value):
                self.inst.write("WAV:SOUR CHAN%d" % value)
                self.last_wav_sour = int(value)

    @property
    def acq_type(self):
        tmp = self.inst.query("ACQ:TYPE?")
        for idx, x in enumerate(self.config['acqtypes']):
            if (re.match(x+".*", tmp)):
                return idx

    @acq_type.setter
    def acq_type(self, value):
        if within_limits(value, [0, 3]):
            self.inst.write("ACQ:TYPE " + self.config['acqtypes'][int(value)])

    @property
    def acq_count(self):
        return self.inst.query_ascii_values("ACQ:COUN?")[0]

    @acq_count.setter
    def acq_count(self, value):
        if within_limits(value, [2, 65536]):
            self.inst.write("ACQ:COUN %d" % value)

    @property
    def format(self):
        tmp = self.inst.query("WAV:FORM?")
        for idx, x in enumerate(self.config['formats']):
            if (re.match(x+".*", tmp)):
                return idx

    @format.setter
    def format(self, value):
        if within_limits(value, [0, 2]):
            self.inst.write("WAV:FORM " + self.config['formats'][int(value)])

    @property
    def points_mode(self):
        tmp = self.inst.query("WAV:POIN:MODE?")
        for idx, x in enumerate(self.config['points_modes']):
            if (re.match(x+".*", tmp)):
                return idx

    @points_mode.setter
    def points_mode(self, value):
        if within_limits(value, [0, 2]):
            self.inst.write("WAV:POIN:MODE " +
                            self.config['points_modes'][int(value)])

    @property
    def points(self):
        return int(self.query_ascii_values("WAV:POIN?")[0])

    @points.setter
    def points(self, value):
        M = np.floor(np.log10(value))
        m = value/10**M
        v = self.points
        if (M == 2 and m < 5 and m >= 2.5):
            v = 250
        elif ((M == 6 and m >= 8) or M > 6):
            v = 8e6
        elif (m >= 5):
            v = m*10**M
        elif (m >= 2):
            v = m*10**M
        else:
            v = 10**M
        self.inst.write("WAV:POIN %d" % v)


    @property
    def times(self):
        pre = self.preamble
        return (np.arange(pre[2])-pre[6])*pre[4]+pre[5]

    @property
    def preamble(self):
        return self.inst.query_ascii_values("WAV:PRE?")

    def trig_single(self):
        self.inst.write("SING")

    def trig_run(self):
        self.inst.write("RUN")

    def trig_stop(self):
        self.inst.write("STOP")

    def digitize(self):
        self.inst.write("DIG")


class InfiniiVision5000Channel:
    """
    Channel related commands
    """

    number = None
    _preamble = None
    cache_preamble = False

    def __init__(self, parent, number):
        self.parent = weakref.proxy(parent)
        self.number = number
        self.parent.wave_source = self.number
        self.parent.inst.write("WAV:UNS 0")

    @property
    def bwlimit(self):
        return get_bool(self.parent.inst, "CHAN%d:BWL" % self.number)

    @bwlimit.setter
    def bwlimit(self, value):
        set_bool(self.parent.inst, "CHAN%d:BWL" % self.number, value)

    @property
    def dccoupling(self):
        return (self.parent.inst.query(
            "CHAN%d:COUP?" % self.number)[:2] == "DC")

    @dccoupling.setter
    def dccoupling(self, value):
        if (value):
            self.parent.inst.write("CHAN%d:COUP DC" % self.number)
        else:
            self.parent.inst.write("CHAN%d:COUP AC" % self.number)

    @property
    def display(self):
        return get_bool(self.parent.inst, "CHAN%d:DISP" % self.number)

    @display.setter
    def display(self, value):
        set_bool(self.parent.inst, "CHAN%d:DISP" % self.number, value)

    @property
    def lowimped(self):
        return (
            self.parent.inst.query(
                "CHAN%d:IMP?" % self.number)[:4] == "FIFT")

    @lowimped.setter
    def lowimp(self, value):
        if (value):
            self.parent.inst.write("CHAN%d:IMP FIFT" % self.number)
        else:
            self.parent.inst.write("CHAN%d:IMP ONEM" % self.number)

    @property
    def invert(self):
        return get_bool(self.parent.inst, "CHAN%d:INV" % self.number)

    @invert.setter
    def invert(self, value):
        set_bool(self.parent.inst, "CHAN%d:INV" % self.number, value)

    @property
    def label(self):
        return self.parent.inst.query("CHAN%d:LAB?" % self.number)[:-1]

    @label.setter
    def label(self, value):
        try:
            s = str(value)
        except TypeError:
            s = "CHAN 1"
        if (len(s) > 10):
            s = s[:10]
        self.parent.write("CHAN%d:LAB \"%s\"" % (self.number, s))

    @property
    def offset(self):
        return self.parent.query_ascii_values("CHAN%d:OFFS?" % self.number)[0]

    @offset.setter
    def offset(self, value):
        if isinstance(value, Number):
            self.parent.inst.write("CHAN%d:OFFS %f" % (self.number, value))

    @property
    def voltages(self):
        self.parent.wave_source = self.number
        pre = self.parent.preamble
        typ = 'b'
        if (pre[0] == 4):
            return self.parent.inst.query_ascii_values("WAV:DATA?")
        elif (pre[0] == 1):
            typ = 'h'
        wav = self.parent.inst.query_binary_values("WAV:DATA?", datatype=typ)
        return (np.array(wav)-pre[9])*pre[7]+pre[8]

    @property
    def preamble(self):
        if (self.cache_preamble and self._preamble is not None):
            return self._preamble
        self.parent.wave_source = self.number
        if (self.cache_preamble):
            self._preamble = self.parent.preamble
            return self._preamble
        else:
            return self.parent.preamble


class E3640():
    """
    PyVISA wrapper for E3640 DC power supply
    """

    config = {}

    def __init__(self, inst):
        self.inst = inst

    @property
    def voltage_range(self):
        mn = self.inst.query_ascii_values("VOLT? MIN")[0]
        mx = self.inst.query_ascii_values("VOLT? MAX")[0]
        return np.array([mn, mx])

    @property
    def current_range(self):
        mn = self.inst.query_ascii_values("CURR? MIN")[0]
        mx = self.inst.query_ascii_values("CURR? MAX")[0]
        return np.array([mn, mx])

    @property
    def voltage(self):
        return self.inst.query_ascii_values("VOLT?")[0]

    @voltage.setter
    def voltage(self, value):
        if within_limits(value, self.voltage_range):
            self.inst.write("VOLT %f" % value)

    @property
    def current(self):
        return self.inst.query_ascii_values("CURR?")[0]

    @current.setter
    def current(self, value):
        if within_limits(value, self.current_range):
            self.inst.write("CURR %f" % value)

    @property
    def low_range(self):
        return (self.inst.query("VOLT:RANG?") == "P8V")

    @low_range.setter
    def low_range(self, value):
        if value:
            self.inst.write("VOLT:RANG LOW")
        else:
            self.inst.write("VOLT:RANG HIGH")

    @property
    def output(self):
        return (self.query_ascii_values("OUTP?")[0] == 1)

    @output.setter
    def output(self, value):
        if value:
            self.inst.write("OUTP ON")
        else:
            self.inst.write("OUTP OFF")



class B2900(ParameterAnalyzer):
    """
    Wrapper for B2900
    """

    def __init__(self, inst):
        self.inst = inst

class B2900Channel(SMU):
    use_ascii = True
    def __init__(self, inst=None, parent=None, number=None):
        if parent is not None:
            self.number = number
            self.parent = weakref.proxy(parent)

    def get_value(self, query):
        qstr = query.format(n=self.number)
        return self.parent.inst.query(qstr+"?")

    def get_values(self, query):
        qstr = query.format(n=self.number)
        if self.use_ascii:
            return self.parent.inst.query_ascii_values(qstr)
        else:
            return self.parent.inst.query_binary_values(qstr)

    def set_float(self, command, value):
        wstr = (command+"{v:0.5E}").format(n=self.number, v=value)
        return self.parent.inst.write(wstr)

    def set_value(self, command, value):
        wstr = (command+"{v}").format(n=self.number, v=value)
        return self.parent.inst.write(wstr)

    def get_bool(self, query):
        return get_bool(self.parent.inst,
                        query.format(n=self.number))

    def set_bool(self, command, value):
        return set_bool(self.parent.inst,
                        command.format(n=self.number), value)


    @property
    def output(self):
        return self.get_bool("OUTP{n:d}")

    @output.setter
    def output(self, value):
        self.set_bool("OUTP{n:d}", value)

    @property
    def source_range(self):
        """
        Source range (None=Auto)
        """
        sstr = self._source_string
        if self.get_bool("SOUR{n:d}:"+sstr+":RANG:AUTO"):
            return None
        else:
            return self.get_value("SOUR{n:d}:"+sstr+":RANG")

    @source_range.setter
    def source_range(self, value):
        sstr = self._source_string
        if value is None:
            self.set_bool("SOUR{n:d}:"+sstr+":RANGE:AUTO", True)
        else:                   #TODO check within limits
            self.set_bool("SOUR{n:d}:"+sstr+":RANGE:AUTO", False)
            self.set_float("SOUR{n:d}:"+sstr+"RANGE", value)

    @property
    def source_voltage(self):
        """
        Source in voltage mode (True=Voltage, False=Current)
        """
        return self.get_value("SOUR{n:d}:FUNC:MODE") == 'VOLT'

    @source_voltage.setter
    def source_voltage(self, value):
        """
        Source in voltage mode (True=Voltage, False=Current)
        """
        if value:
            self.set_value("SOUR{n:d}:FUNC:MODE", "VOLT")
        else:
            self.set_value("SOUR{n:d}:FUNC:MODE", "CURR")

    @property
    def _source_string(self):
        if self.source_voltage:
            return "VOLT"
        else:
            return "CURR"

    @property
    def source_mode(self):
        """
        Source mode ('LINear' / 'LOGarithmic' / 'LIST' / 'FIXed')
        """
        pass

    @source_mode.setter
    def source_mode(self, value):
        """
        Source mode ('LINear' / 'LOGarithmic' / 'LIST' / 'FIXed')
        """
        pass

    @property
    def sweep_up(self):
        """

        bool sweep up == True
        """
        pass

    @sweep_up.setter
    def sweep_up(self):
        """
        bool sweep up == True
        """
        pass

    @property
    def sweep_points(self):
        """
        int number of points
        """
        pass

    @sweep_points.setter
    def sweep_points(self, value):
        """
        int number of points
        """
        pass

    @property
    def sweep_bidirectional(self):
        """
        bool bi-directional sweep (double)
        """
        pass

    @sweep_bidirectional.setter
    def sweep_bidirectional(self, value):
        """
        bool bi-directional sweep (double)
        """
        pass

    @property
    def bias(self):
        """
        Source value/range/values
        """
        pass

    @bias.setter
    def bias(self, value):
        """
        Source value/range/values
        """
        pass

    @property
    def compliance(self):
        """
        Compliance value
        """
        pass

    @compliance.setter
    def compliance(self, value):
        """
        Compliance value
        """
        pass

    @property
    def kelvin(self):
        """
        bool Kelvin or 4 point probe mode
        """
        pass

    @kelvin.setter
    def kelvin(self, value):
        """
        bool Kelvin or 4 point probe mode
        """
        pass

    @property
    def integration_time(self):
        """
        Integration time in seconds
        """
        pass

    @integration_time.setter
    def integration_time(self, value):
        """
        Integration time in seconds
        """
        pass

    @property
    def integration_time_NPLC(self):
        """
        Integration time in power line cycles
        """
        pass

    @integration_time_NPLC.setter
    def integration_time_NPLC(self, value):
        """
        Integration time in power line cycles
        """
        pass

    @property
    def sense_range(self):
        """
        Measurement range None = Auto
        """
        pass

    @sense_range.setter
    def sense_range(self, value):
        """
        Measurement range
        """
        pass

    @property
    def sense_threshold(self):
        """
        Threshold to auto change range in %
        """
        pass

    @sense_threshold.setter
    def sense_threshold(self, value):
        """
        Threshold to auto change range in %
        """
        pass

    @property
    def sense_range_auto_llim(self):
        """
        Minimum range to switch to for auto-ranging
        """
        pass

    @sense_range_auto_llim.setter
    def sense_range_auto_llim(self, value):
        """
        Minimum range to switch to for auto-ranging
        """
        pass

    @property
    def sense_range_auto_ulim(self):
        """
        Maximum range to switch to for auto-ranging
        """
        pass

    @sense_range_auto_ulim.setter
    def sense_range_auto_ulim(self, value):
        """
        Maximum range to switch to for auto-ranging
        """
        pass

    @property
    def pulse(self):
        """
        bool Pulsed mode
        """
        pass

    @pulse.setter
    def pulse(self, value):
        """
        bool Pulsed mode
        """
        pass

    @property
    def trigger_source(self):
        """
        source to trigger off of
        """
        pass

    @trigger_source.setter
    def trigger_source(self, value):
        """
        source to trigger off of
        """
        pass

    @property
    def timer_interval(self):
        """
        interval in seconds between internal triggers
        """
        pass

    @timer_interval.setter
    def timer_interval(self):
        """
        interval in seconds between internal triggers
        """
        pass

    @property
    def trigger_transition_delay(self):
        """
        delay time for value transition in seconds
        """
        pass

    @trigger_transition_delay.setter
    def trigger_transition_delay(self, value):
        """
        delay time for value transition in seconds
        """
        pass

    @property
    def trigger_aquire_delay(self):
        """
        delay time for measurement start in seconds
        """
        pass

    @trigger_aquire_delay.setter
    def trigger_aquire_delay(self, value):
        """
        delay time for measurement start in seconds
        """
        pass

    @property
    def source_wait(self):
        """
        wait time for source in seconds
        """
        pass

    @source_wait.setter
    def source_wait(self, value):
        """
        wait time for source in seconds
        """
        pass

    @property
    def sense_wait(self):
        """
        wait time for sense in seconds
        """
        pass

    @sense_wait.setter
    def sense_wait(self, value):
        """
        wait time for sense in seconds
        """
        pass

    @property
    def pulse_delay(self):
        """
        delay time before pulse in seconds
        """
        pass

    @pulse_delay.setter
    def pulse_delay(self):
        """
        delay time before pulse in seconds
        """
        pass

    @property
    def pulse_width(self):
        """
        pulse width in seconds
        """
        pass

    @pulse_width.setter
    def pulse_width(self, value):
        """
        pulse width in seconds
        """
        pass
