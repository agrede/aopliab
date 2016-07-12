import re
from aopliab_common import within_limits, json_load, get_bool, set_bool
import numpy as np
import weakref


class InfiniiVision5000():
    """
    PyVISA wrapper for InfiniiVision 5000 Oscilloscope
    """

    config = {}

    def __init__(self, inst):
        self.inst = inst
        self.inst.write("*RST; *CLS")
        cfg = json_load('configs/keysight.json')
        self.config = cfg['InfiniiVision5000']

    @property
    def acq_type(self):
        tmp = self.inst.query("ACQ:TYPE?")
        for idx, x in enumerate(self.config['acqtypes']):
            if (re.match(x+".*", tmp)):
                return idx

    @acq_type.setter
    def acq_type(self, value):
        if within_limits(value, [0, 3]):
            self.inst.write("ACQ:TYPE " + self.config['acqtypes'][int(value)])

    @property
    def acq_count(self):
        return self.inst.query_ascii_values("ACQ:COUN?")[0]

    @acq_count.setter
    def acq_count(self, value):
        if within_limits(value, [2, 65536]):
            self.inst.write("ACQ:COUN %d" % value)

    @property
    def format(self):
        tmp = self.inst.query("WAV:FORM?")
        for idx, x in enumerate(self.config['formats']):
            if (re.match(x+".*", tmp)):
                return idx

    @format.setter
    def format(self, value):
        if within_limits(value, [0, 2]):
            self.inst.write("WAV:FORM " + self.config['formats'][int(value)])

    @property
    def points_mode(self):
        tmp = self.inst.query("WAV:POIN:MODE?")
        for idx, x in enumerate(self.config['points_modes']):
            if (re.match(x+".*", tmp)):
                return idx

    @points_mode.setter
    def points_mode(self, value):
        if within_limits(value, [0, 2]):
            self.inst.write("WAV:POIN:MODE " +
                            self.config['points_modes'][int(value)])

    @property
    def points(self):
        return int(self.query_ascii_values("WAV:POIN?")[0])

    @points.setter
    def points(self, value):
        M = np.floor(np.log10(value))
        m = value/10**M
        v = self.points
        if (M == 2 and m < 5 and m >= 2.5):
            v = 250
        elif ((M == 6 and m >= 8) or M > 6):
            v = 8e6
        elif (m >= 5):
            v = m*10**M
        elif (m >= 2):
            v = m*10**M
        else:
            v = 10**M
        self.inst.write("WAV:POIN %d" % v)

    @property
    def voltages(self):
        pre = self.preamble
        self.inst.write("DIG 1")
        typ = 'b'
        if (pre[0] == 4):
            return self.inst.query_ascii_values("WAV:DATA?")
        elif (pre[0] == 1):
            typ = 'h'
        wav = self.inst.query_binary_values("WAV:DATA?", datatype=typ)
        return (np.array(wav)-pre[9])*pre[7]+pre[8]

    @property
    def times(self):
        pre = self.preamble
        return (np.arange(pre[2])-pre[6])*pre[4]+pre[5]

    @property
    def preamble(self):
        return self.inst.query_ascii_values("WAV:PRE?")


class InfiniiVision5000Channel:
    """
    Channel related commands
    """

    number = None

    def __init__(self, parent, number):
        self.parent = weakref.proxy(parent)
        self.number = number

    @property
    def bwlimit(self):
        return get_bool(self.parent.inst, "CHAN%d:BWL" % self.number)

    @bwlimit.setter
    def bwlimit(self, value):
        set_bool(self.parent.inst, "CHAN%d:BWL" % self.number, value)

    @property
    def dccoupling(self):
        return (self.parent.inst.query(
            "CHAN%d:COUP?" % self.number)[:2] == "DC")

    @dccoupling.setter
    def dccoupling(self, value):
        if (value):
            self.parent.inst.write("CHAN%d:COUP DC" % self.number)
        else:
            self.parent.inst.write("CHAN%d:COUP AC" % self.number)

    @property
    def display(self):
        return get_bool(self.parent.inst, "CHAN%d:DISP" % self.number)

    @display.setter
    def display(self, value):
        set_bool(self.parent.inst, "CHAN%d:DISP" % self.number, value)

    @property
    def lowimped(self):
        return (
            self.parent.inst.query(
                "CHAN%d:IMP?" % self.number)[:4] == "FIFT")

    @lowimped.setter
    def lowimp(self, value):
        if (value):
            self.parent.inst.write("CHAN%d:IMP FIFT" % self.number)
        else:
            self.parent.inst.write("CHAN%d:IMP ONEM" % self.number)

    @property
    def invert(self):
        return get_bool(self.parent.inst, "CHAN%d:INV" % self.number)

    @invert.setter
    def invert(self, value):
        set_bool(self.parent.inst, "CHAN%d:INV" % self.number, value)

    @property
    def label(self):
        return self.parent.inst.query("CHAN%d:LAB?" % self.number)[:-1]

    @label.setter
    def label(self, value):
        try:
            s = str(value)
        except TypeError:
            s = "CHAN 1"
        if (len(s) > 10):
            s = s[:10]
        self.parent.write("CHAN%d:LAB \"%s\"" % (self.number, s))

    @property
    def offset(self):
        return self.parent.query_ascii_values("CHAN%d:OFFS?" % self.number)[0]

    @offset.setter
    def offset(self, value):
        pass

    
class Keysight2900:
    """
    PyVISA wrapper for Keysight 2900 Pulsed SMU
    """
    def __init__(self, inst):
        self.inst = inst
        #cfg = json_load("configs/keysight.json")
        #self.config = cfg['Keysight2900']

    '''reset - reset all parameters to default'''
    def reset(self):
        self.inst.write("*RST")
        
    def identity(self):
        msg = self.inst.query("*IDN?")
        print(msg)
        
    '''beep - turn the beeper on or off
    Variables...
        value - 0 = beeper off, 1 = beeper on'''
    def beep(self, value):
        if (value):
            self.inst.write("SYST:BEEP:STAT ON")
        else:
            self.inst.write("SYST:BEEP:STAT OFF")
            
    '''disp - set display on or off
    Variables...
        value - 0 = display off, 1 = display on'''
    def disp(self, value):
        if (value):
            self.inst.write("DISP:ENAB ON")
        else:
            self.inst.write("DISP:ENAB OFF")
            
    '''Error message is read one by one by using the :SYST:ERR? command. This
    command reads and removes the top item in the error buffer, and returns the code
    and message.'''
    def error_single(self):
        msg = self.inst.query("SYST:ERR?")
        print(msg)
         
    '''All error messages are read and then cleared'''
    def error_all(self):
        msg = self.inst.query("SYST:ERR:ALL?")
        print(msg)
    
    ##########################################################################
    ############################# FETCH COMMANDS #############################
    ##########################################################################
    
    '''Pull all voltage, current, and resistance measurements for channels 1-2
    Variables...
        ch1 - 0 = get data for channel 1; 1 = ignore channel 1
        ch2 - 0 = get data for channel 2; 1 = ignore channel 2'''
    def fetch_all_data(self,ch1,ch2):
        if(ch1 and (not ch2)):
            return self.inst.query_ascii_values("FETC:ARR? [@1]")
        elif( (not ch1) and ch2):
            return self.inst.query_ascii_values("FETC:ARR? [@2]")
        elif(ch1 and ch2):
            return self.inst.query_ascii_values("FETC:ARR? [@1,2]")
        else:
            print("Nothing happens with neither channel selected, dufus.")
            
        
    ##########################################################################
    ############################ MEASURE COMMANDS ############################
    ##########################################################################
    '''Executes a spot (one-shot) measurement for the parameters specified by
    ***:SENSe:FUNCtion[:ON]*** command, and returns the measurement result data
    specified by the :FORMat:ELEMents:SENSe command. Measurement conditions
    must be set by SCPI commands or front panel operation before executing this
    command.
    Variables...
        ch1 - 0 = get data for channel 1; 1 = ignore channel 1
        ch2 - 0 = get data for channel 2; 1 = ignore channel 2'''
    def measure_single_data(self,ch1,ch2):
        if(ch1 and (not ch2)):
            return self.inst.query_ascii_values("MEAS? [@1]")
        elif( (not ch1) and ch2):
            return self.inst.query_ascii_values("MEAS? [@2]")
        elif(ch1 and ch2):
            return self.inst.query_ascii_values("MEAS? [@1,2]")
        else:
            print("Nothing happens with neither channel selected, dufus.")
            
    
    ##########################################################################
    ############################ MEASURE COMMANDS ############################
    ##########################################################################        
    #integration_time - sets the integration time/measurement window for the smu.  
    #        Setting VOLTage/CURRent/RESistance doesn't matter b/c the time window is common for all values
    #channel = channel
    #value = integration time; min = 8E-6s, max = 2s; if you go outside of these bounds, the SMU sets to these values
    def integration_time(self, ch, value):    
        self.inst.write("SENS%d:VOLT:DC:APER %s" %(ch, value))
        ################return self.inst.query_ascii_values("SENS%d:VOLT:DC:APER",ch)