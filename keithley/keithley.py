import visa


class K2000():
    """
    PyVISA wrapper for Keithley 2000 Multimeter
    """
    rm = visa.ResourceManager()
    inst = visa.Resource()
    _sample = None
    _delay = None

    def __init__(self, address):
        self.inst = self.rm.open_resource("GPIB::%s" % address)
        self.inst.write("*RST, STATUS:PRESET; *CLS")
        self.inst.write("STAT:MEAS:ENAB 512; *SRE 1")
        self.sample = 1
        self.inst.write("TRIG:SOUR BUS")
        self.delay = 0.5

    @property
    def sample(self):
        return self._sample

    @sample.setter
    def sample(self, value):
        if (self._sample is not value):
            if (value >= 2 and value <= 1024):
                self.inst.write("SAMP:COUN %d" % value)
                self.inst.write("TRAC:POIN %d" % value)
                self.inst.write("TRAC:FEED SENS")
                self.inst.write("TRAC:FEED:CONT NEXT")
                self._sample = value
            else:
                self.inst.write("SAMP:CON %d" % value)
                self.inst.write("TRAC:FEED:CONT NEV")
                self._sample = 1

    @property
    def delay(self):
        return self._delay

    @delay.setter
    def delay(self, value):
        if (self._delay is not value):
            self.inst.write("TRIG:DEL %f" % value)
            self._delay = value

    def values(self):
        if (self.sample > 1):
            self.init.write("INIT")
            self.init.assert_trigger()
            self.init.wait_for_srq()
            data = self.init.query_ascii_values("TRAC:DATA?")
            self.init.query("STAT:MEAS?")
            self.init.write("TRAC:CLE; TRAC:FEED:CONT NEXT")
            return data
        else:
            data = self.init.query_ascii_values("READ?")
            return data


class K2400():
    """
    PyVISA wrapper for Keithley 2400 SMU
    """
    rm = visa.ResourceManager()
    inst = visa.Resource()
    current_limits = [-1.05, 1.05]
    voltage_limits = [-21.0, 21.0]
    speed_limits = [0.01, 10.0]
    delay_limits = [0.0, 999.999]

    def __init__(self, address):
        self.inst = self.rm.open_resource("GPIB::%s" % address)
        self.inst.write("*RST; *CLS")
        self.inst.write("FUNC:CONC ON")
        self.inst.write("FUNC 'VOLT', 'CURR'")

    def outupt(self, value):
        if (value):
            self.inst.write("OUTP ON")
        else:
            self.inst.write("OUTP OFF")
