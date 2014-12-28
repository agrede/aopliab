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
        self.curr_limits[0] = inst.query_ascii_values("CURR:PROT:LEV? MIN")
        self.curr_limits[1] = inst.query_ascii_values("CURR:PROT:LEV? MAX")
        self.volt_limits[0] = inst.query_ascii_values("VOLT:PROT:LEV? MIN")
        self.volt_limits[1] = inst.query_ascii_values("VOLT:PROT:LEV? MAX")
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
                value is None or
                self.volt_limits[0] > value or
                self.volt_limits[1] < value
        ):
            self.inst.write("SOUR:VOLT %f" % value)

    def set_current(self, value):
        if (
                value is None or
                self.curr_limits[0] > value or
                self.curr_limits[1] < value
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
                "CURR:PROT:LEV? DEF")
        else:
            self._curr_limit = value

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
                "VOLT:PROT:LEV? DEF")
        else:
            self._volt_limit = value


class K2485:
    inst = None
    _curr_limit = 0
    _integ_time = 0

    def __init__(self, inst):
        self.inst = inst

    @property
    def current_limit(self):
        return self._curr_limit

    @current_limit.setter
    def current_limit(self, value):
        pass

    @property
    def integration_time(self):
        return self._integ_time

    @integration_time.setter
    def integration_time(self, value):
        pass

    def trigger(self):
        self.inst.write("INIT")

    def read(self):
        return self.inst.query_ascii_values("DATA?")
