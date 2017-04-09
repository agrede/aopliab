import numpy as np
from aopliab_common import within_limits, nearest_index

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
        return (self.inst.query("SOUR:AM:SOUR?") == 'CWP')
    
    @source_power.setter
    def source_power(self, value):
        if value:
            self.inst.write("SOUR:AM:SOUR CWP")
        else:
            self.inst.write("SOUR:AM:SOUR CWC")
            
    @property
    