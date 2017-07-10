import re
from aopliab_common import within_limits, json_load, get_bool, set_bool
import numpy as np
import weakref
from time import time


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
        cfg = json_load("configs/keysight.json")
        self.config = cfg['HP4192A']
        self.freq_range = np.array(self.config['freq_range'])
        self.bias_range = np.array(self.config['bias_range'])
        self.osc_range = np.array(self.config['osc_range'])
        self.inst.write("DC1")
        self.inst.write("A2B1C2R8D1F0H0V1T3")

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
        return np.array([mt.group(1), mt.group(2)])



class InfiniiVision5000():
    """
    PyVISA wrapper for InfiniiVision 5000 Oscilloscope
    """

    config = {}

    def __init__(self, inst):
        self.inst = inst
        self.inst.write("*RST; *CLS")
        cfg = json_load('configs/keysight.json')
        self.config = cfg['InfiniiVision5000']

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
    def voltages(self):
        pre = self.preamble
        self.inst.write("DIG 1")
        typ = 'b'
        if (pre[0] == 4):
            return self.inst.query_ascii_values("WAV:DATA?")
        elif (pre[0] == 1):
            typ = 'h'
        wav = self.inst.query_binary_values("WAV:DATA?", datatype=typ)
        return (np.array(wav)-pre[9])*pre[7]+pre[8]

    @property
    def times(self):
        pre = self.preamble
        return (np.arange(pre[2])-pre[6])*pre[4]+pre[5]

    @property
    def preamble(self):
        return self.inst.query_ascii_values("WAV:PRE?")


class InfiniiVision5000Channel:
    """
    Channel related commands
    """

    number = None

    def __init__(self, parent, number):
        self.parent = weakref.proxy(parent)
        self.number = number

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
        pass


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
