from aopliab_common import within_limits, json_load, twos_complement
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

    @property
    def current(self):
        return self.inst.query_ascii_values("MEAS:CURR?")[0]


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


class FW102C():
    """
    PyVisa wrapper for motorized filter wheel
    """

    _filters = None
    _qrx = re.compile('.*\r(.*)')

    def __init__(self, inst):
        self.inst = inst

    def close(self):
        self.inst.close()

    def query(self, value):
        tmp = self.inst.query(value)
        return float(self._qrx.match(tmp).group(1))
        
    def write(self, value):
        self.inst.write(value)
        self.inst.read_raw()

    @property
    def position(self):
        return int(self.query("pos?"))

    @position.setter
    def position(self, value):
        value = int(value)
        if within_limits(value, self.position_limits):
            self.write("pos=%d" % value)

    @property
    def position_limits(self):
        tmp = int(self.query("pcount?"))
        return np.array([1, tmp])

    @property
    def fast_change(self):
        return (int(self.query("speed?")) == 1)

    @fast_change.setter
    def fast_change(self, value):
        if value:
            self.write("speed=1")
        else:
            self.write("speed=0")

    @property
    def trig_out(self):
        return (int(self.query("trig?")) == 1)

    @trig_out.setter
    def trig_out(self, value):
        if value:
            self.write("trig=1")
        else:
            self.write("trig=0")

    @property
    def sensors_active(self):
        return (int(self.query("sensors?")) == 1)

    @sensors_active.setter
    def sensors_active(self, value):
        if value:
            self.write("sensors=1")
        else:
            self.write("sensors=0")

    @property
    def next_filter_on(self):
        if self.filters is not None:
            idx = self.position
            if self.position >= self.filters.shape[0]:
                idx = 0
            return self.filters[idx, 4]
        else:
            return np.nan

    @property
    def current_filter_off(self):
        if self.filters is not None:
            idx = self.position
            return (self.filters[idx-1, 4])
        else:
            return np.nan

    def higher_order_od(self, wavelength):
        if self.filters is not None:
            if np.all(~np.isnan(self.filters[self.position-1, :])):
                fltr = self.filters[self.position-1, :]
                if wavelength < fltr[3]:
                    return fltr[1]
                elif wavelength > fltr[4]:
                    return fltr[2]
                else:
                    slp = np.diff(fltr[1:3])/np.diff(fltr[3:])
                    return (slp*(wavelength-fltr[3])+fltr[1])
        return np.nan


class ELL_translation():
    """
    PyVisa wrapperfor linear stepper translation stage
    """
    _num = 0
    _res = 1024e3
    _limits = np.array([0.0, 0.0])
    
    def __init__(self, inst, number=0):
        self.inst = inst
        self._num = 0
        self.inst.clear()
        info = self.inst.query("{:X}in".format(self._num))
        self._res = 1e3*int(info[25:], 16)
        self._limits[1] = 1e-3*int(info[21:25], 16)

    def close(self):
        self.inst.close()
        
    def write(self, value):
        self.inst.write(value)
        self.inst.read_raw()
        
    def query(self, command):
        return self.inst.query("{:X}{:s}".format(self._num, command))
        
    def query_2scomplement(self, command, nbits=32):
        self.inst.clear()
        tmp = self.inst.query("{:X}{:s}".format(self._num, command))
        val = int(tmp[3:], 16)
        return twos_complement(val, nbits)
    
    def set_2scomplement(self, command, val, nbits=32):
        self.inst.clear()
        return self.inst.query(
                "{:X}{:s}{val:0{width}X}".format(
                        self._num,
                        command,
                        val=twos_complement(val, nbits),
                        width=nbits//4))
        
    def home(self):
        return self.query("ho")
        
    @property
    def position(self):
        """
        position of stage in meters
        """
        return self.query_2scomplement("gp")/self._res
    
    @position.setter
    def position(self, value):
        if within_limits(value, self._limits):
            self.set_2scomplement("ma", int(value*self._res))
        
    @property
    def jog_step(self):
        """
        jog step size in meters
        """
        return self.query_2scomplement("gj")/self._res
    
    @jog_step.setter
    def jog_step(self, value):
        if within_limits(value, self._limits):
            self.set_2scomplement("sj", int(value*self._res))
            
    def forward(self):
        return self.query("fw")
        
    def backward(self):
        return self.query("bw")