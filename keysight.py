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
    ############################# SENSE COMMANDS #############################
    ##########################################################################        
    '''integration_time - sets the integration time/measurement window for the smu.  
        Setting VOLTage/CURRent/RESistance doesn't matter b/c the time window is common for all values.
    variables...
        channel = channel # (1 or 2)
        value = integration time; min = 8E-6s, max = 2s; if you go outside of these bounds, the SMU sets to these values'''
    def integration_time(self, ch, value):    
        if value == "AUTO":
            self.inst.write("SENS%d:VOLT:DC:APER:AUTO 1" % (ch))
        else:
            self.inst.write("SENS%d:VOLT:DC:APER %s" % (ch, value))
        ################return self.inst.query_ascii_values("SENS%d:VOLT:DC:APER",ch)
        
        '''integration_time_NPLC: sets number of power line cycles to measure over
    variables...
        channel = channel # (1 or 2)
        value = integration time; +4E-4 to +100 for 50 Hz or +4.8E-4 to +120 for 60 Hz'''
    def integration_time_NPLC(self, ch, value):    
        if value == "DEF" or "Default":
            self.inst.write("SENS%d:VOLT:NPLC:DEF" % (ch))
        elif value == "AUTO":
            self.inst.write("SENS%d:VOLT:NPLC:AUTO 1" % (ch))
        else:
            self.inst.write("SENS%d:VOLT:NPLC %s" % (ch, value))
            
        '''at_compliance: checks to see if the specified channel has hit compliance
    variables...
        channel = channel # (1 or 2)
        V0_or_I1 = 0 for voltage, 1 for current'''
    def at_compliance(self, ch, V0_or_I1):
        if V0_or_I1 == 0:
            return self.inst.query_ascii_values("SENS%d:VOLT:PROT:TRIP?" % ch)
        if V0_or_I1 == 1:
            return self.inst.query_ascii_values("SENS%d:CURR:PROT:TRIP?" % ch )

    '''sense_range_auto: toggles auto ranging for the a given channel/measurement
    variables...
        channel = channel # (1 or 2)
        V0_I1_R2 = 0 for voltage, 1 for current, 2 for resistance
        value = 0 for no auto ranging, 1 for auto ranging'''
    def sense_range_auto(self, ch, V0_I1_R2, value):   
        if V0_I1_R2 == 0:
            self.inst.write("SENS%d:VOLT:DC:RANG:AUTO %d" % (ch, value))
        if V0_I1_R2 == 1:
            self.inst.write("SENS%d:CURR:DC:RANG:AUTO %d" % (ch, value))
        if V0_I1_R2 == 2:
            self.inst.write("SENS%d:RES:RANG:AUTO %d" % (ch, value))
    
    '''sense_range_mode: toggles measurement speed type
    variables...
        channel = channel # (1 or 2)
        V0_I1 = 0 for voltage, 1 for current
        value: 0=NORMal, 1=RESolution, 2=SPEed; 0 is default'''
    def sense_range_mode(self, ch, V0_I1, value):   
        if V0_I1 == 0:
            self.inst.write("SENS%d:VOLT:DC:RANG:AUTO:MODE %s" % (ch, value))
        if V0_I1 == 1:
            self.inst.write("SENS%d:CURR:DC:RANG:AUTO:MODE %s" % (ch, value))
            
    '''sense_range_threshold: sets threshold rate for automatic measurement ranging...
        channel =channel # (1 or 2)
        V0_I1 = 0 for voltage, 1 for current
        value: threshold measurement - 11 to 100; default is 90'''
    def sense_range_threshold(self, ch, V0_I1, value):   
        if V0_I1 == 0:
            self.inst.write("SENS%d:VOLT:DC:RANG:AUTO:THR %s" % (ch, value))
        if V0_I1 == 1:
            self.inst.write("SENS%d:CURR:DC:RANG:AUTO:THR %s" % (ch, value))
            
    ######NOT WORKING######
    '''sense_range_auto_ulim: sets the threshold upper limit for automatic measurement ranging...
        channel =channel # (1 or 2)
        V0_I1 = 0 for voltage, 1 for current
        value = MIN, MAX, DEFault, or a number'''
    def sense_range_auto_ulim(self, ch, V0_I1_R2, value):
        if V0_I1_R2 == 0:
            self.inst.write("SENS%d:VOLT:DC:RANG:AUTO:ULIM %s" % (ch, value))
        if V0_I1_R2 == 1:
            self.inst.write("SENS%d:CURR:DC:RANG:AUTO:ULIM %s" % (ch, value))
        if V0_I1_R2 == 2:
            self.inst.write("SENS%d:RES:RANG:AUTO:ULIM %s" % (ch, value))
    
    '''sense_range_auto_llim: sets the threshold lower limit for automatic measurement ranging...
        channel =channel # (1 or 2)
        V0_I1 = 0 for voltage, 1 for current
        value = MIN, MAX, DEFault, or a number'''
    def sense_range_auto_llim(self, ch, V0_I1_R2, value):
        if V0_I1_R2 == 0:
            self.inst.write("SENS%d:VOLT:DC:RANG:AUTO:LLIM %s" % (ch, value))
        if V0_I1_R2 == 1:
            self.inst.write("SENS%d:CURR:DC:RANG:AUTO:LLIM %s" % (ch, value))
        if V0_I1_R2 == 2:
            self.inst.write("SENS%d:RES:RANG:AUTO:LLIM %s" % (ch, value))
#    def sense_range_ulim:

    '''sense_range_ulim: sets the measurement range upper limit to best meet measurement resolution...
        channel =channel # (1 or 2)
        V0_I1 = 0 for voltage, 1 for current
        value = UP, DOWN, MIN, MAX, DEFault, or a number'''
    def sense_range_ulim(self, ch, V0_I1_R2, value):
        if V0_I1_R2 == 0:
            self.inst.write("SENS%d:VOLT:DC:RANG:UPP %s" % (ch, value))
        if V0_I1_R2 == 1:
            self.inst.write("SENS%d:CURR:DC:RANG:UPP %s" % (ch, value))
        if V0_I1_R2 == 2:
            self.inst.write("SENS%d:RES:RANG:UPP %s" % (ch, value))

    '''sense_measurements: sets the measurements to be taken
        channel =channel # (1 or 2)
        meas_volt/curr/res = 0 for off/ 1 for on; resistance measurements turn both voltage/current on'''
    def sense_measurements(self, ch, meas_volt, meas_curr, meas_res):
        #turn all channels off
        self.inst.write("SENS%d:FUNC:OFF:ALL" % ch)
 
        #concatenate string with selected values    
        sv = '"VOLT"' if meas_volt else ""
        sc = '"CURR"' if meas_curr else ""
        sr = '"RES"' if meas_res else ""
        
        #remove any empty values before concatenation, then send values to be turned on
        msg = ",".join(filter(None,[sv, sc, sr]))
        self.inst.write('SENS%d:FUNC:ON %s' % (ch, msg))

        #return the channels that are on
        return self.inst.query_ascii_values("SENS%d:FUNC:ON?"  % ch, converter = 's')


    
    ##########################################################################
    ############################ HYBRID COMMANDS #############################
    ##########################################################################
            
    def compliance(self, ch, V0_or_I1, value):
        if V0_or_I1 == 0:
            self.inst.write("SOUR%d:FUNC:MODE VOLT" % (ch))
            self.inst.write("SENS%d:VOLT:PROT %f" % (ch, value))
        if V0_or_I1 == 1:
            self.inst.write("SOUR%d:FUNC:MODE CURR" % (ch))
            self.inst.write("SENS%d:CURR:PROT %f" % (ch, value))
#        else:
#            self.inst.query_ascii_values("")
            
