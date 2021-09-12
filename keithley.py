import re
from aopliab.aopliab_common import within_limits, json_load, get_limits
import numpy as np
import time
import os


PKGPTH = os.path.dirname(__file__)+"/"


class K2400():
    """
    PyVISA wrapper for Keithley 2400 SMU
    """

    inst = None
    curr_limits = [-1.05, 1.05]
    volt_limits = [-21.0, 21.0]
    speed_limits = [0.01, 10.0]
    delay_limits = [0.0, 999.999]

    def __init__(self, inst):
        self.inst = inst
        self.curr_limits[0] = inst.query_ascii_values("CURR:PROT:LEV? MIN")[0]
        self.curr_limits[1] = inst.query_ascii_values("CURR:PROT:LEV? MAX")[0]
        self.volt_limits[0] = inst.query_ascii_values("VOLT:PROT:LEV? MIN")[0]
        self.volt_limits[1] = inst.query_ascii_values("VOLT:PROT:LEV? MAX")[0]
        self.inst.write("FUNC:CONC ON")
        self.inst.write("FUNC 'VOLT', 'CURR'")
        self.inst.write("SOUR:FUNC VOLT")

    @property
    def output(self):
        return (self.inst.query_ascii_values("OUTP?")[0] == 0.)

    @output.setter
    def output(self, value):
        if (value):
            self.inst.write("OUTP ON")
        else:
            self.inst.write("OUTP OFF")

    def trigger(self):
        if (self.output):
            self.inst.write("INIT")

    def read(self):
        return self.inst.query_ascii_values("DATA?")

    @property
    def source_volt(self):
        return (self.inst.query("SOUR:FUNC?") == "VOLT\n")

    @source_volt.setter
    def source_volt(self, value):
        if value:
            self.inst.write("SOUR:FUNC VOLT")
        else:
            self.inst.write("SOUR:FUNC CURR")

    @property
    def voltage(self):
        return self.inst.query_ascii_values("SOUR:VOLT?")[0]

    @voltage.setter
    def voltage(self, value):
        if within_limits(value, self.volt_limits):
            self.inst.write("SOUR:VOLT %f" % value)

    @property
    def current(self):
        return self.inst.query_ascii_values("SOUR:CURR?")[0]

    @current.setter
    def current(self, value):
        if within_limits(value, self.curr_limits):
            self.inst.write("SOUR:CURR %f" % value)

    @property
    def measure(self):
        return self.inst.query_ascii_values("READ?")

    @property
    def current_limit(self):
        return self.inst.query_ascii_values("CURR:PROT:LEV?")[0]

    @current_limit.setter
    def current_limit(self, value):
        if within_limits(value, self.curr_limits):
            self.inst.write("CURR:PROT:LEV %f" % value)
        else:
            self.inst.write("CURR:PROT:LEV %f" %
                            self.inst.query_ascii_values(
                                                         "CURR:PROT:LEV? DEF"
                                                         )[0])

    @property
    def beep(self):
        return self.inst.write("SYST:BEEP %f, %f" % (1000, 1.0))

    @property
    def voltage_limit(self):
        return self.inst.query_ascii_values("VOLT:PROT:LEV?")[0]

    @voltage_limit.setter
    def voltage_limit(self, value):
        if within_limits(value, self.volt_limits):
            self.inst.write("VOLT:PROT:LEV %f" % value)
        else:
            self.inst.write("VOLT:PROT:LEV %f" %
                            self.inst.query_ascii_values(
                                                         "VOLT:PROT:LEV? DEF"
                                                         )[0])

    @property
    def front_terminal(self):
        tst = self.inst.query("ROUT:TERM?")
        return (tst == "FRON\n")

    @front_terminal.setter
    def front_terminal(self, value):
        if value:
            self.inst.write("ROUT:TERM FRON")
        else:
            self.inst.write("ROUT:TERM REAR")

    def voltage_sweep(self, start, stop, points, tmeout=3000.):
        if points < 1:
            points = 1
        elif points > 2500:
            points = 2500
        lmts = self.volt_limits
        if within_limits(start, lmts) and within_limits(stop, lmts):
            self.inst.write("SOUR:VOLT:MODE SWE")
            self.inst.write("SOUR:VOLT:STAR %f" % start)
            self.inst.write("SOUR:VOLT:STOP %f" % stop)
            self.inst.write("SOUR:SWE:POIN %d" % points)
            self.inst.write("SOUR:SWE:CAB EARL")
            self.inst.write("TRIG:COUN %d" % points)
            self.output = True
            self.inst.write("INIT")
            self.inst.write("*OPC?")
            tm = time.time() + tmeout
            cycles = 0
            opc = False
            while (not opc and time.time() < tm):
                cycles = cycles+1
                if (self.inst.stb > 0):
                    opc = self.inst.read() == "1\n"
                    break
            self.output = False
            rtn = (0, None)
            if opc:
                rtn = (self.inst.query_ascii_values("TRAC:POIN:ACT?")[0],
                       self.inst.query_ascii_values("FETCH?"))
            self.inst.write("TRIG:COUN 1")
            self.inst.write("SOUR:VOLT:MODE FIX")
            return rtn

    def clear_errors(self):
        self.inst.write("STAT:QUE:CLE")


class K2485:
    inst = None
    auto_range_ulimits = [0.0, 2.1e-2]
    auto_range_llimits = [0.0, 2.1e-2]
    integ_cycles_limits = [0.01, 60.0]
    _auto_range_ulimit = 2.1e-2
    _auto_range_llimit = 2.1e-9
    _curr_limit = 0.0
    _integ_cycles = 0.0
    _line_freq = 60.0

    def __init__(self, inst):
        self.inst = inst
        self.inst.write("*RST; *CLS")
        self.auto_range_llimits = get_limits(inst, "RANG:AUTO:LLIM")
        self.auto_range_ulimits = get_limits(inst, "RANG:AUTO:ULIM")
        self.integ_cycles_limits = get_limits(inst, "NPLCycles")
        self._line_freq = inst.query_ascii_values("SYST:LFR?")[0]
        self.integration_time = None
        self.range_auto_llimit = None
        self.range_auto_ulimit = None

    def zero_check(self):
        self.inst.write("SYST:ZCH ON")
        self.inst.write("INIT")
        self.inst.write("SYST:ZCOR:ACQ")
        self.inst.write("SYST:ZCOR ON")
        self.inst.write("SYST:ZCH OFF")

    @property
    def integration_time(self):
        return self._integ_cycles/self._line_freq

    @integration_time.setter
    def integration_time(self, value):
        if value is None:
            tvalue = None
        else:
            tvalue = value*self._line_freq
        if (within_limits(tvalue, self.integ_cycles_limits)):
            self._integ_cycles = tvalue
        else:
            self._integ_cycles = self.inst.query_ascii_values("NPLC? DEF")[0]
        self.inst.write("NPLC %f" % self._integ_cycles)

    @property
    def range_auto_ulimit(self):
        return self._auto_range_ulimit

    @range_auto_ulimit.setter
    def range_auto_ulimit(self, value):
        if (within_limits(value, self.auto_range_ulimits)):
            self._auto_range_ulimit = value
        else:
            self._auto_range_ulimit = self.inst.query_ascii_values(
                "RANG:AUTO:ULIM? DEF")[0]
        self.inst.write("RANG:AUTO:ULIM %f" % self._auto_range_ulimit)

    @property
    def range_auto_llimit(self):
        return self._auto_range_llimit

    @range_auto_llimit.setter
    def range_auto_llimit(self, value):
        if (within_limits(value, self.auto_range_llimits)):
            self._auto_range_llimit = value
        else:
            self._auto_range_llimit = self.inst.query_ascii_values(
                "RANG:AUTO:LLIM? DEF")[0]
        self.inst.write("RANG:AUTO:LLIM %f" % self._auto_range_llimit)

    def trigger(self):
        self.inst.write("INIT")

    def read(self):
        return [float(x) for x in re.split("A?,", self.inst.query("DATA?"))]

    def measurement(self):
        return [float(x) for x in re.split("A?,", self.inst.query("READ?"))]


class K6430():
    """
    PyVISA wrapper for K6430 Sub-femptoamp SMU
    """

    def __init__(self, inst):
        self.inst = inst
        cfg = json_load(PKGPTH+"configs/keithley.json")
        self.config = cfg['K6430']

    @property
    def output(self):
        return (self.inst.query_ascii_values("OUTP?", converter=u'd')[0] == 1)

    @output.setter
    def output(self, value):
        if (value):
            self.inst.write("OUTP 1")
        else:
            self.inst.write("OUTP 0")

    @property
    def offmode(self):
        smode = self.inst.query("OUTP:SMOD?")
        k = np.where(smode.upper().startswith(tuple(self.config['smodes'])))[0]
        if (k.size > 0):
            return self.config['smodes'][k[0]]

    @offmode.setter
    def offmode(self, value):
        k = np.where(value.upper().startswith(tuple(self.config['smodes'])))[0]
        if (k.size > 0):
            self.inst.write("OUTP:SMOD %s" % self.config['smodes'][k[0]])

    @property
    def concurrent(self):
        return (self.inst.query_ascii_values("FUNC:CONC?",
                                             converter=u'd')[0] == 1)

    @concurrent.setter
    def concurrent(self, value):
        if (value):
            self.inst.write("FUNC:CONC 1")
        else:
            self.inst.write("FUNC:CONC 0")

    @property
    def sense(self):
        tmp = self.inst.query("FUNC?").split(",")
        funcs = []
        for v in tmp:
            v = v.translate({ord('"'): None, ord('\n'): None}).upper()
            k = np.where(list(map(v.startswith, self.config['functions'])))[0]
            if (k.size > 0 and self.config['functions'][k[0]] not in funcs):
                funcs.append(self.config['functions'][k[0]])
        return np.array(funcs)

    @sense.setter
    def sense(self, value):
        try:
            value = iter(value)
        except TypeError:
            value = [value]
        funcs = []
        for v in value:
            k = np.where(list(map(
                v.upper().startswith, self.config['functions'])))[0]
            if (k.size > 0 and self.config['functions'][k[0]] not in funcs):
                funcs.append(self.config['functions'][k[0]])
        if (len(funcs) > 0):
            self.inst.write("FUNC '%s'" % "','".join(funcs))

    @property
    def auto_voltage(self):
        return (
            self.inst.query_ascii_values("VOLT:RANG:AUTO?",
                                         converter=u'd')[0] == 1)

    @auto_voltage.setter
    def auto_voltage(self, value):
        if (value):
            self.inst.write("VOLT:RANG:AUTO 1")
        else:
            self.inst.write("VOLT:RANG:AUTO 0")

    @property
    def auto_current(self):
        return (
            self.inst.query_ascii_values("CURR:RANG:AUTO?",
                                         converter=u'd')[0] == 1)

    @auto_current.setter
    def auto_current(self, value):
        if (value):
            self.inst.write("CURR:RANG:AUTO 1")
        else:
            self.inst.write("CURR:RANG:AUTO 0")

    @property
    def auto_resistance(self):
        return (
            self.inst.query_ascii_values("RES:RANG:AUTO?",
                                         converter=u'd')[0] == 1)

    @auto_resistance.setter
    def auto_resistance(self, value):
        if (value):
            self.inst.write("RES:RANG:AUTO 1")
        else:
            self.inst.write("RES:RANG:AUTO 0")

    @property
    def voltage_limit_range(self):
        return get_limits(self.inst, "VOLT:PROT")

    @property
    def voltage_limit(self):
        return self.inst.query_ascii_values("VOLT:PROT?")[0]

    @voltage_limit.setter
    def voltage_limit(self, value):
        if (within_limits(value, self.voltage_limit_range)):
            self.inst.write("VOLT:PROT %f" % value)

    @property
    def current_limit_range(self):
        return get_limits(self.inst, "CURR:PROT")

    @property
    def current_limit(self):
        return self.inst.query_ascii_values("CURR:PROT?")[0]

    @current_limit.setter
    def current_limit(self, value):
        if (within_limits(value, self.voltage_limit_range)):
            self.inst.write("CURR:PROT %f" % value)

    @property
    def nplcycles_range(self):
        return get_limits(self.inst, "CURR:NPLC")

    @property
    def nplcycles(self):
        return (self.inst.query_ascii_values("CURR:NPLC?")[0])

    @nplcycles.setter
    def nplcycles(self, value):
        if (within_limits(value, self.nplcycles_range)):
            self.inst.write("CURR:NPLC %f" % value)

    @property
    def auto_average(self):
        return (
            self.inst.query_ascii_values("AVER:AUTO?", converter=u'd')[0] == 1)

    @auto_average.setter
    def auto_average(self, value):
        if (value):
            self.inst.write("AVER:AUTO 1")
        else:
            self.inst.write("AVER:AUTO 0")

    @property
    def average_repeat_count_range(self):
        return get_limits(self.inst, "AVER:REP:COUN")

    @property
    def average_repeat_count(self):
        return self.inst.query_ascii_values("AVER:REP:COUN?",
                                            converter=u'd')[0]

    @average_repeat_count.setter
    def average_repeat_count(self, value):
        if within_limits(value, self.average_repeat_count_range):
            self.inst.write("AVER:REP:COUN %d" % value)

    @property
    def average_repeat(self):
        return (self.inst.query_ascii_values("AVER:REP?",
                                             converter=u'd')[0] == 1)

    @average_repeat.setter
    def average_repeat(self, value):
        if (value):
            self.inst.write("AVER:REP 1")
        else:
            self.inst.write("AVER:REP 0")

    @property
    def median_rank(self):
        return self.inst.query_ascii_values("MED:RANK?", converter=u'd')[0]

    @median_rank.setter
    def median_rank(self, value):
        if within_limits(value, [0, 5]):
            self.inst.write("MED:RANK %d" % value)

    @property
    def median(self):
        return (self.inst.query_ascii_values("MED?", converter=u'd')[0] == 1)

    @median.setter
    def median(self, value):
        if (value):
            self.inst.write("MED 1")
        else:
            self.inst.write("MED 0")

    @property
    def average_count_range(self):
        return get_limits(self.inst, "AVER:COUN")

    @property
    def average_count(self):
        return self.inst.query_ascii_values("AVER:COUN?", converter=u'd')[0]

    @average_count.setter
    def average_count(self, value):
        if within_limits(value, self.average_count_range):
            self.inst.write("AVER:COUN %d" % value)

    @property
    def average(self):
        return (self.inst.query_ascii_values("AVER?", converter=u'd')[0] == 1)

    @average.setter
    def average(self, value):
        if (value):
            self.inst.write("AVER 1")
        else:
            self.inst.write("AVER 0")

    @property
    def source_voltage(self):
        return (self.inst.query("SOUR:FUNC?") == "VOLT\n")

    @source_voltage.setter
    def source_voltage(self, value):
        if (value):
            self.inst.write("SOUR:FUNC VOLT")
        else:
            self.inst.write("SOUR:FUNC CURR")

    @property
    def voltage_range_range(self):
        return get_limits(self.inst, "SOUR:VOLT:RANG")

    @property
    def voltage_range(self):
        return self.inst.query_ascii_values("SOUR:VOLT:RANG?")[0]

    @voltage_range.setter
    def voltage_range(self, value):
        if within_limits(value, self.voltage_range_range):
            self.inst.write("SOUR:VOLT:RANG %f" % value)

    @property
    def auto_voltage_range(self):
        return (
            self.inst.query_ascii_values("SOUR:VOLT:RANG:AUTO?",
                                         converter=u'd')[0] == 1)

    @auto_voltage_range.setter
    def auto_voltage_range(self, value):
        if (value):
            self.inst.write("SOUR:VOLT:RANG:AUTO 1")
        else:
            self.inst.write("SOUR:VOLT:RANG:AUTO 0")

    @property
    def current_range_range(self):
        return get_limits(self.inst, "SOUR:CURR:RANG")

    @property
    def current_range(self):
        return self.inst.query_ascii_values("SOUR:CURR:RANG?")[0]

    @current_range.setter
    def current_range(self, value):
        if within_limits(value, self.current_range_range):
            self.inst.write("SOUR:CURR:RANG %f" % value)

    @property
    def auto_current_range(self):
        return (
            self.inst.query_ascii_values("SOUR:CURR:RANG:AUTO?",
                                         converter=u'd')[0] == 1)

    @auto_current_range.setter
    def auto_current_range(self, value):
        if (value):
            self.inst.write("SOUR:CURR:RANG:AUTO 1")
        else:
            self.inst.write("SOUR:CURR:RANG:AUTO 0")

    @property
    def voltage_amp_range(self):
        return get_limits(self.inst, "SOUR:VOLT")

    @property
    def voltage(self):
        return self.inst.query_ascii_values("SOUR:VOLT?")[0]

    @voltage.setter
    def voltage(self, value):
        if within_limits(value, self.voltage_amp_range):
            self.inst.write("SOUR:VOLT %f" % value)

    @property
    def current_amp_range(self):
        return get_limits(self.inst, "SOUR:CURR")

    @property
    def current(self):
        return self.inst.query_ascii_values("SOUR:CURR?")[0]

    @current.setter
    def current(self, value):
        if within_limits(value, self.current_amp_range):
            self.inst.write("SOUR:CURR %f" % value)

    def beep(self, time=0.5, freq=500):
        if within_limits(freq, [65, 2e6]):
            if within_limits(time, [0, 512/freq]):
                self.inst.write("SYST:BEEP %f, %f" % (freq, time))

    def measurement(self, tmax=300):
        self.inst.write("INIT")
        self.inst.write("*OPC?")
        tm = time.time() + tmax
        cycles = 0
        opc = False
        while (not opc and time.time() < tm):
            cycles = cycles+1
            if (self.inst.stb > 0):
                opc = self.inst.read() == "1\n"
                break
        if (opc):
            return self.inst.query_ascii_values("FETCH?")
        else:
            return None


class K237():
    """
    PyVISA wrapper for K237 High Voltage SMU
    """

    def __init__(self, inst):
        self.inst = inst
        cfg = json_load(PKGPTH+"configs/keithley.json")
        self.config = cfg['K237']
        self.measure_parameters()
        self.machine_status()


    def machine_status(self):
        """
        Query Status Variables

        Returns
        -------
        bool
            success
        """
        tmp = self.inst.query("U3X")
        # 0000000000111111111122222222223333
        # 0123456789012345678901234567890123
        # MSTG05,0,0K0M000,0N0R1T4,0,0,0V1Y0
        if tmp[:3] != "MST":
            return False
        self._sqrMask = int(tmp[13:16])
        self._output_enable = tmp[19] == '1'
        self._trigger = tmp[21] == '1'
        self._trigger_source = int(tmp[23])
        self._trigger_in = int(tmp[25])
        self._trigger_out = int(tmp[27])
        self._trigger_out_sweep_end = tmp[29] == '1'
        self._high_voltage_enabled = tmp[31] == '1'
        return True


    def measure_parameters(self):
        tmp = self.inst.query("U4X")
        # 000000000011111111112
        # 012345678901234567890
        # IMPL,05F0,0O0P0S0W1Z0
        self._source_voltage = tmp[8] == '0'
        self._sweep_mode = tmp[10] == '1'
        self._remote_sense = tmp[12] == '1'
        if self._source_voltage:
            self._current_compliance_range = self.config['current_ranges'][int(tmp[5:7])]
        else:
            self._voltage_compliance_range = self.config['voltage_ranges'][int(tmp[5:7])]
        self._filter_samples = self.config['filter_samples'][int(tmp[14])]
        self._integration_time = self.config['integration_times'][int(tmp[16])]
        self._default_delay = tmp[18] == '1'
        self._suppression = tmp[20] == '1'

    @property
    def measure(self):
        if self._sweep_mode:
            return None, None
        tmp = self.inst.read()
        v = None
        i = None
        for val in tmp.split(","):
            if val[0] == 'N':
                if val[4] == 'V':
                    v = float(val[5:])
                elif val[4] == 'I':
                    i = float(val[5:])
        return np.array([v, i])

    @property
    def sweep_mode(self):
        if self.measure_parameters():
            return self._sweep_mode
        else:
            return None

    @sweep_mode.setter
    def sweep_mode(self, value):
        if value:
            self.inst.write("G15,3,2X")
            if self._source_voltage:
                self.inst.write("F0,1X")
            else:
                self.inst.write("F1,1X")
            self._sweep_mode = True
        else:
            self.inst.write("G5,0,0X")
            if self._source_voltage:
                self.inst.write("F0,0X")
            else:
                self.inst.write("F1,0X")
            self._sweep_mode = False

    @property
    def source_voltage(self):
        if self.measure_parameters():
            return self._sweep_mode
        else:
            return None

    @source_voltage.setter
    def source_voltage(self, value):
        if value:
            if self._sweep_mode:
                self.inst.write("F0,1X")
            else:
                self.inst.write("F0,0X")
            self._source_voltage = True
        else:
            if self._sweep_mode:
                self.inst.write("F1,1X")
            else:
                self.inst.write("F1,0X")
            self._source_voltage = False

    @property
    def high_voltage_enabled(self):
        if self.machine_status():
            return self._high_voltage_enabled
        else:
            return None

    @high_voltage_enabled.setter
    def high_voltage_enabled(self, value):
        if value:
            self.inst.write("V1X")
            self._high_voltage_enabled = True
        else:
            self.inst.write("V0X")
            self._high_voltage_enabled = False

    @property
    def bias(self):
        if self._sweep_mode:
            return None
        v, i = self.measure
        if self._source_voltage:
            return v
        else:
            return i

    @bias.setter
    def bias(self, value):
        if self._source_voltage and within_limits(value, [-1100., 1100.]):
            self.inst.write("B{:0.4E},0,0X".format(value))
        elif not self._source_voltage and within_limits(value, [-100e-3, 100e-3]):
            self.inst.write("B{:04E},0,0X")


    @property
    def compliance(self):
        tmp = self.inst.query("U5X")
        return float(tmp[3:])

    @compliance.setter
    def compliance(self, value):
        if self._source_voltage and within_limits(value, [1e-12, 100e-3]):
            self.inst.write("L{:0.4E},0".format(value))
        elif not self._source_voltage and within_limits(value, [1e-3, 1100.]):
            self.inst.write("L{:0.4E},0".format(value))

    @property
    def output_enable(self):
        if self.machine_status():
            return self._output_enable
        else:
            return None

    @output_enable.setter
    def output_enable(self, value):
        if value:
            self.inst.write("N1X")
            self._output_enable = True
        else:
            self.inst.write("N0X")
            self._output_enable = False
