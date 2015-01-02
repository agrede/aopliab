import re


def get_limits(inst, query):
    return [
        inst.query_ascii_values(query+"? MIN")[0],
        inst.query_ascii_values(query+"? MAX")[0]]

def within_limits(value, limits):
    return (value is not None and limits[0] <= value and limits[1] >= value)
    

class K2400():
    """
    PyVISA wrapper for Keithley 2400 SMU
    """

    inst = None
    curr_limits = [-1.05, 1.05]
    volt_limits = [-21.0, 21.0]
    speed_limits = [0.01, 10.0]
    delay_limits = [0.0, 999.999]
    _output = False
    _curr_limit = 0
    _volt_limit = 0

    def __init__(self, inst):
        self.inst = inst
        self.inst.write("*RST; *CLS")
        self.curr_limits[0] = inst.query_ascii_values("CURR:PROT:LEV? MIN")[0]
        self.curr_limits[1] = inst.query_ascii_values("CURR:PROT:LEV? MAX")[0]
        self.volt_limits[0] = inst.query_ascii_values("VOLT:PROT:LEV? MIN")[0]
        self.volt_limits[1] = inst.query_ascii_values("VOLT:PROT:LEV? MAX")[0]
        self.current_limit = None
        self.voltage_limit = None
        self.inst.write("FUNC:CONC ON")
        self.inst.write("FUNC 'VOLT', 'CURR'")

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, value):
        if (value):
            self._output = True
            self.inst.write("OUTP ON")
        else:
            self._output = False
            self.inst.write("OUTP OFF")

    def trigger(self):
        if (self.output):
            self.inst.write("INIT")

    def read(self):
        return self.inst.query_ascii_values("DATA?")

    def set_voltage(self, value):
        if (
                value is not None and
                self.volt_limits[0] < value and
                self.volt_limits[1] > value
        ):
            self.inst.write("SOUR:VOLT %f" % value)

    def set_current(self, value):
        if (
                value is not None or
                self.curr_limits[0] < value or
                self.curr_limits[1] > value
        ):
            self.inst.write("SOUR:CURR %f" % value)

    def measurement(self):
        return self.inst.query_ascii_values("READ?")

    @property
    def current_limit(self):
        return self._curr_limit

    @current_limit.setter
    def current_limit(self, value):
        if (
                value is None or
                self.curr_limits[0] > value or
                self.curr_limits[1] < value
        ):
            self._curr_limit = self.inst.query_ascii_values(
                "CURR:PROT:LEV? DEF")[0]
        else:
            self._curr_limit = value
        self.inst.write("CURR:PROT %f" % self._curr_limit)

    @property
    def voltage_limit(self):
        return self._volt_limit

    @voltage_limit.setter
    def voltage_limit(self, value):
        if (
                value is None or
                self.volt_limits[0] > value or
                self.volt_limits[1] < value
        ):
            self._volt_limit = self.inst.query_ascii_values(
                "VOLT:PROT:LEV? DEF")[0]
        else:
            self._volt_limit = value
        self.inst.write("VOLT:PROT %f" % self._volt_limit)


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
