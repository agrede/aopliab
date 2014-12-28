import visa


class Keithley2400():
    """
    PyVISA wrapper for Keithley 2400 SMU
    """
    rm = visa.ResourceManager()
    inst = None

    def __init__(self, address):
        self.inst = self.rm.open_resource("GPIB::%s" % address)
        self.inst.write("*RST; status:preset; *CLS")

    def close(self):
        self.rm.close()

    def measure_current(self, voltage):
        pass

    def measure_voltage(self, current):
        pass

    def output(self, value):
        if (value):
            self.inst.write.output("OUTP:STAT")
