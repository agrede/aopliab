import re
from aopliab_common import within_limits

def get_limits(inst, query):
    return [
        inst.query_ascii_values(query+"? MIN")[0],
        inst.query_ascii_values(query+"? MAX")[0]]


class K2400():
    """
    PyVISA wrapper for Keithley 2400 SMU
    """

    inst = None
    curr_limits = [-1.05, 1.05]
    volt_limits = [-21.0, 21.0]
    speed_limits = [0.01, 10.0]
    delay_limits = [0.0, 999.999]
    count_limits = [0, 2500]
    integ_cycles_limits = [0.01, 10.0]
    _output = False
    _curr_limit = 0.0
    _volt_limit = 0.0
    _delay = 0.0
    _integ_cycles = 1.0
    _line_freq = 60.0
    _count = 1
    _triggered = False
    _source_volt = True

    def __init__(self, inst):
        self.inst = inst
        self.inst.write("*RST; *CLS")
        self.inst.write("STAT:MEAS:ENAB 512; *SRE 1")
        self.inst.write("TRAC:FEED SENS; TRAC:FEED:CONT NEXT")
        self.inst.write("SOUR:FUNC VOLT")
        self.inst.write("FUNC:CONC ON")
        self.inst.write("FUNC 'VOLT', 'CURR'")
        self.curr_limits = get_limits(inst, "CURR:PROT:LEV")
        self.volt_limits = get_limits(inst, "VOLT:PROT:LEV")
        self.delay_limits = get_limits(inst, "TRIG:DEL")
        self.count_limits = [int(x) for x in get_limits(inst, "TRIG:COUN")]
        # Integration time is a global setting, CURR will be used as default
        self.integ_cycles_limits = get_limits(inst, "CURR:NPLC")
        self.current_limit = None
        self.voltage_limit = None
        self.delay = None
        self.trigger_count = None

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
            self._triggered = True

    def read(self):
        if (self._triggered):
            self.inst.wait_for_srq()
            self._triggered = False
        data = self.inst.query_ascii_values("TRAC:DATA?")
        self.inst.query("STAT:MEAS?")
        self.inst.write("TRAC:CLE; TRAC:FEED:CONT:NEXT")
        return data

    def set_voltage(self, value):
        if (not self._source_volt):
            self.inst.write("SOUR:FUNC VOLT")
            self._source_volt = True
        if (within_limits(value, self.volt_limits)):
            self.inst.write("SOUR:VOLT %f" % value)

    def set_current(self, value):
        if (self._source_volt):
            self.inst.write("SOUR:FUNC CURR")
            self._source_volt = False
        if (within_limits(value, self.curr_limits)):
            self.inst.write("SOUR:CURR %f" % value)

    def measurement(self):
        self.trigger()
        return self.read()

    @property
    def current_limit(self):
        return self._curr_limit

    @current_limit.setter
    def current_limit(self, value):
        if (within_limits(value, self.curr_limits)):
            self._curr_limit = value
        else:
            self._curr_limit = self.inst.query_ascii_values(
                "CURR:PROT:LEV? DEF")[0]
        self.inst.write("CURR:PROT %f" % self._curr_limit)

    @property
    def voltage_limit(self):
        return self._volt_limit

    @voltage_limit.setter
    def voltage_limit(self, value):
        if (within_limits(value, self.volt_limits)):
            self._volt_limit = value
        else:
            self._volt_limit = self.inst.query_ascii_values(
                "VOLT:PROT:LEV? DEF")[0]
        self.inst.write("VOLT:PROT %f" % self._volt_limit)

    @property
    def delay(self):
        return self._delay

    @delay.setter
    def delay(self, value):
        if (within_limits(value, self.delay_limits)):
            self._delay = value
        else:
            self._delay = self.inst.query_ascii_values("TRIG:DEL? DEF")
        self.inst.write("TRIG:DEL %f" % self._delay)

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
            self._integ_cycles = self.inst.query_ascii_values(
                "CURR:NPLC? DEF")[0]
        self.inst.write("CURR:NPLC %f" % self._integ_cycles)

    @property
    def trigger_count(self):
        return self._count

    @trigger_count.setter
    def trigger_count(self, value):
        if (within_limits(value, self.count_limits)):
            self._count = int(value)
        else:
            self._count = 1
        self.inst.write("TRIG:COUN %d" % self._count)
        self.inst.write("TRAC:POIN %d" % self._count)


class K6485:
    inst = None
    auto_range_ulimits = [0.0, 2.1e-2]
    auto_range_llimits = [0.0, 2.1e-2]
    integ_cycles_limits = [0.01, 60.0]
    delay_limits = [0.0, 999.999]
    count_limits = [0, 2500]
    _auto_range_ulimit = 2.1e-2
    _auto_range_llimit = 2.1e-9
    _curr_limit = 0.0
    _integ_cycles = 0.0
    _line_freq = 60.0
    _delay = 0.0
    _count = 1
    _triggered = False

    def __init__(self, inst):
        self.inst = inst
        self.inst.write("*RST; *CLS")
        self.inst.write("STAT:MEAS:ENAB 512; *SRE 1")
        self.inst.write("TRAC:FEED:SENS; TRAC:FEED:CONT NEXT")
        self.auto_range_llimits = get_limits(inst, "RANG:AUTO:LLIM")
        self.auto_range_ulimits = get_limits(inst, "RANG:AUTO:ULIM")
        self.integ_cycles_limits = get_limits(inst, "NPLCycles")
        self._line_freq = inst.query_ascii_values("SYST:LFR?")[0]
        self.count_limits = get_limits("TRIG:COUN")
        self.delay_limits = get_limits("TRIG:DEL")
        self.integration_time = None
        self.range_auto_llimit = None
        self.range_auto_ulimit = None
        self.trigger_count = None
        self.delay = None

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
        self._triggered = True

    def read(self):
        if (self._triggered):
            self.inst.wait_for_srq()
            self._triggered = False
        data = [
            float(x) for x in re.split("A?,", self.inst.query("TRAC:DATA?"))]
        self.inst.query("STAT:MEAS?")
        self.inst.write("TRAC:CLE; TRAC:FEED:CONT:NEXT")
        return data

    def measurement(self):
        self.trigger()
        return self.read()

    @property
    def trigger_count(self):
        return self._count

    @trigger_count.setter
    def trigger_count(self, value):
        if (within_limits(value, self.count_limits)):
            self._count = int(value)
        else:
            self._count = 1
        self.inst.write("TRIG:COUN %d" % self._count)
        self.inst.write("TRAC:POIN %d" % self._count)

    @property
    def delay(self):
        return self._delay

    @delay.setter
    def delay(self, value):
        if (within_limits(value, self.delay_limits)):
            self._delay = value
        else:
            self._delay = self.inst.query_ascii_values("TRIG:DEL? DEF")
        self.inst.write("TRIG:DEL %f" % self._delay)
