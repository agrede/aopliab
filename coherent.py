import numpy as np
from aopliab.aopliab_common import within_limits, nearest_index


class OBISMC():
    """
    PyVISA wrapper for OBIS Mini-controller
    """

    inst = None

    def __init__(self, inst):
        self.inst = inst

    def query(self, value):
        msg = self.inst.query_ascii_values(value)
        self.inst.read_raw()
        return msg

    def write(self, value):
        self.inst.write(value)
        self.inst.read_raw()

    @property
    def source_power(self):
        rtn = self.inst.query("SOUR:AM:SOUR?")
        self.inst.read_raw()
        return (rtn == "CWP")

    @source_power.setter
    def source_power(self, value):
        if value:
            self.write("SOUR:AM:SOUR CWP")
        else:
            self.write("SOUR:AM:SOUR CWC")

    @property
    def power_limits(self):
        low = self.query("SOUR:POW:LIM:LOW?")
        high = self.query("SOUR:POW:NOM?")
        return np.array([low[0], high[0]])

    @property
    def power(self):
        return (self.query("SOUR:POW:LEV:IMM:AMPL?")[0])

    @power.setter
    def power(self, value):
        if (within_limits(value, self.power_limits)):
            self.write("SOUR:POW:LEV:IMM:AMPL %f" % value)

    @property
    def output(self):
        rtn = self.inst.query("SOUR:AM:STAT?")
        self.inst.read_raw()
        return (rtn == "ON")

    @output.setter
    def output(self, value):
        if value:
            self.write("SOUR:AM:STAT ON")
        else:
            self.write("SOUR:AM:STAT OFF")
