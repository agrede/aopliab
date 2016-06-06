from aopliab_common import within_limits, json_load
import json
import numpy as np
import re


class MC2000():
    _harmonic_limits = [1, 15]
    _display_limits = [1, 10]
    _phase_limits = [0, 360]
    _qrx = re.compile('.*\r(.*)')

    def __init__(self, inst):
        self.inst = inst
        cfg_file = open('configs/thorlabs.json')
        cfg = json.load(cfg_file)
        cfg_file.close()
        self.config = cfg['MC2000']
        self.blades = np.array(cfg['MC2000']['blades'])

    def close(self):
        self.inst.close()

    def query(self, value):
        tmp = self.inst.query(value)
        return float(self._qrx.match(tmp).group(1))

    def write(self, value):
        self.inst.write(value)
        self.inst.read_raw()

    @property
    def blade(self):
        idx = int(self.query('blade?'))
        return (idx, self.blades[idx, 0])

    @blade.setter
    def blade(self, value):
        if (type(value) is int):
            if (within_limits(value, [0, (self.blades.size-1)])):
                self.write('blade=%d' % value)
        elif (value in self.blades[:, 0]):
            v = np.where(value == self.blades[:, 0])[0][0]
            self.write('blade=%d' % v)

    @property
    def freq_limits(self):
        return self.blades[self.blade[0]][[1, 2]]

    @property
    def freq(self):
        if (self.ext_ref):
            return self.query('input?')
        else:
            return self.query('freq?')

    @freq.setter
    def freq(self, value):
        if (within_limits(value, self.freq_limits)):
            self.write('freq=%d' % value)

    @property
    def phase(self):
        return self.query('phase?')

    @phase.setter
    def phase(self, value):
        if (within_limits(value, self._phase_limits)):
            self.write('phase=%d' % value)

    @property
    def enable(self):
        return (int(self.query('enable?')) == 1)

    @enable.setter
    def enable(self, value):
        if (value):
            self.write('enable=1')
        else:
            self.write('enable=0')

    @property
    def harmonic_mult(self):
        return int(self.query('nharmonic?'))

    @harmonic_mult.setter
    def harmonic_mult(self, value):
        if (within_limits(value, self._harmonic_limits)):
            self.write('nharmonic=%d' % value)

    @property
    def harmonic_div(self):
        return int(self.query('dharmonic?'))

    @harmonic_div.setter
    def harmonic_div(self, value):
        if (within_limits(value, self._harmonic_limits)):
            self.write('dharmonic=%d' % value)

    @property
    def ext_ref(self):
        return (int(self.query('ref?')) == 1)

    @ext_ref.setter
    def ext_ref(self, value):
        if (value):
            self.write('ref=1')
        else:
            self.write('ref=0')

    @property
    def ref_out_actual(self):
        return (int(self.query('output?')) == 1)

    @ref_out_actual.setter
    def ref_out_actual(self, value):
        if (value):
            self.write('output=1')
        else:
            self.write('output=0')

    @property
    def display(self):
        return int(self.query('intensity?'))

    @display.setter
    def display(self, value):
        if (within_limits(value, self._display_limits)):
            self.write('intensity=%d' % value)


class PM100D():
    """
    PyVISA driver for PM100D power meter
    """

    def __init__(self, inst):
        self.inst = inst

    @property
    def wavelength_range(self):
        mn = self.inst.query_ascii_values("CORR:WAV? MIN")[0]
        mx = self.inst.query_ascii_values("CORR:WAV? MAX")[0]
        return [mn, mx]

    @property
    def wavelength(self):
        return self.inst.query_ascii_values("CORR:WAV?")[0]

    @wavelength.setter
    def wavelength(self, value):
        if within_limits(value, self.wavelength_range):
            self.inst.write("CORR:WAV %d" % value)

    @property
    def power(self):
        return self.inst.query_ascii_values("READ?")[0]

    @property
    def response(self):
        return self.inst.query_ascii_values("SENS:CORR:POW:RESP?")[0]


class CLD1015():
    """
    PyVISA wrapper for CLD1015 laser controler
    """

    def __init__(self, inst):
        self.inst = inst
        # cfg = json_load("configs/thorlabs.json")
        # self.config = cfg['CLD1015']

    @property
    def current_mode(self):
        return (self.query("SOUR:FUNC?") is "CURR\n")

    @current_mode.setter
    def current_mode(self, value):
        if (not self.output):
            if (value):
                self.inst.write("SOUR:FUNC CURR")
            else:
                self.inst.write("SOUR:FUNC POW")

    @property
    def output(self):
        return (self.inst.query_ascii_values("OUTP?")[0] == 1.0)

    @output.setter
    def output(self, value):
        if (value):
            self.inst.write("OUTP 1")
        else:
            self.inst.write("OUTP 0")

    @property
    def current_limits(self):
        return [self.inst.query_ascii_values("SOUR:LIM? MIN")[0],
                self.inst.query_ascii_values("SOUR:LIM? MAX")[0]]

    @property
    def power_limits(self):
        return [self.inst.query_ascii_values("SOUR:POW? MIN")[0],
                self.inst.query_ascii_values("SOUR:POW? MAX")[0]]

    @property
    def current(self):
        if (self.current_mode):
            return self.inst.query_ascii_values("SOUR:CURR?")[0]
        elif (self.output):
            return self.query_ascii_values("MEAS:CURR?")[0]

    @current.setter
    def current(self, value):
        if within_limits(value, self.current_limits):
            self.inst.write("SOUR:CURR %f" % value)

    def set_current(self, value):
        """ legacy """
        self.current = value

    @property
    def power(self):
        if (not self.current_mode):
            return self.query_ascii_values("SOUR:POW?")[0]
        elif (self.output):
            return self.query_ascii_values("MEAS:POW?")[0]
        else:
            return 0.0

    @power.setter
    def power(self, value):
        if within_limits(value, self.power_limits):
            self.inst.write("SOUR:POW %f" % value)

    @property
    def temperature(self):
        return self.inst.query_ascii_values("MEAS:TEMP?")[0]
