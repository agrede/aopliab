import re
from aopliab_common import within_limits, json_load, get_bool, set_bool
import numpy as np
import weakref
import time



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
            self.inst.write("SENS%d:VOLT:DC:NPLC:DEF" % ch)
        elif value == "AUTO":
            self.inst.write("SENS%d:VOLT:DC:NPLC:AUTO 1" % ch)
        else:
            self.inst.write("SENS%d:VOLT:DC:NPLC %s" % (ch, value))
            
        '''at_compliance: checks to see if the specified channel has hit compliance
    variables...
        ch = channel # (1 or 2)
        V0_or_I1 = 0 for voltage, 1 for current'''
    def at_compliance(self, ch, V0_or_I1):
        if V0_or_I1 == 0:
            return self.inst.query_ascii_values("SENS%d:VOLT:PROT:TRIP?" % ch)
        if V0_or_I1 == 1:
            return self.inst.query_ascii_values("SENS%d:CURR:PROT:TRIP?" % ch)

    '''sense_remote: enables or disables 4/four-wire sensing
    variables...
        ch = channel #
        value = 1 for 4 point, any other value is 2 point'''
    def sense_remote(self, ch, value):
        if value == 1:
            self.inst.write("SENS%d:REM 1" % ch)
        else:
            self.inst.write("SENS%d:REM 0" % ch)
            
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
    ############################ OUTPUT COMMANDS #############################
    ##########################################################################
    '''output_filter_auto: enables or disables automatic lowpass filter.  If automatic settings
        are disabled, the filter freq and time const must be set
    variables...
    ch - 1 or 2
    auto0_manual1_off2 - 0 for auto, 1 for manual w/ settings, other numbers for off
    time const - filter time constant; DEFault, MIN, MAX, or a number between 5 us to 5 ms'''
    def output_filter(self, ch, auto0_manual1_off2, time_const):
        if auto0_manual1_off2 == 0:
            self.inst.write("OUTP%d:FILT:AUTO %d" % (ch, auto0_manual1_off2))
        elif auto0_manual1_off2 == 1:
            self.inst.write("OUTP%d:FILT:AUTO %d" % (ch, auto0_manual1_off2))
            #self.inst.write("OUTP%d:FILT:LPAS:FREQ %e" % (ch, freq))
            self.inst.write("OUTP%d:FILT:LPAS:TCON %e" % (ch, time_const))
        else:
            self.inst.write("OUTP%d:FILT 0" % ch)
            
    '''output_high_capacitance: enables or disables high cap mode
    variables...
    ch - 1 or 2
    value - 0 for off, 1 for on'''
    def output_high_capacitance(self, ch, value):
        self.inst.write("OUTP%d:HCAP %d" % (ch, value))

    '''output_ground: turns off the source and changes ground state of low terminal
    variables...
    ch - 1 or 2
    value - 0 for float, 1 for ground'''
    def output_ground(self, ch, value):
        self.inst.write("OUTP%d:STATE 0" % ch)
        if value:
            self.inst.write("OUTP%d:LOW GRO" % ch)
        else:
            self.inst.write("OUTP%d:LOW FLO" % ch)

    '''output_off_mode: toggles auto-off for the output
    variables...
    ch - 1 or 2
    value - mode=1 or ON enables the automatic output off function. If this function is enabled,
        the source output is automatically turned off immediately when the grouped
        channels change status from busy to idle.'''            
    def output_auto_off(self, ch, value):
        self.inst.write("OUTP%d:OFF:AUTO %d" % (ch, value))
        
    '''output_off_mode: selects source condition after output off
    variables...
    ch - 1 or 2
    value - 1 for ZERO, 2 for HIZ/high impedance, any other number for NORMal'''
    def output_off_mode(self, ch, value):
        if value == 1:
            self.inst.write("OUTP%d:OFF:MODE HIZ" % ch)
        elif value == 2:
            self.inst.write("OUTP%d:OFF:MODE ZERO" % ch)
        else:
            self.inst.write("OUTP%d:OFF:MODE NORM" % ch)
          
            
    '''output_on_mode: toggles auto-off for the output
    variables...
    ch - 1 or 2
    value - mode=0 or OFF disables the automatic output on function.
        mode=1 or ON enables the automatic output on function. If this function is enabled,
        the source output is automatically turned on when the :INITiate or :READ command
        is sent.'''            
    def output_auto_on(self, ch, value):
        self.inst.write("OUTP%d:ON:AUTO %d" % (ch, value))
        
        
    '''output_over_protection: if the source hits compliance, the output shuts off
    variables...
    ch - 1 or 2
    value - 0 for off, 1 for on'''
    def output_over_protection(self, ch, value):
        if value == 1:
            self.inst.write("OUTP%d:PROT 1" % ch)
        else:
            self.inst.write("OUTP%d:PROT 0" % ch)

            
    '''output_enable: toggles output of a given channel
    variables...
    ch - 1 or 2
    value - 0 for off, 1 for on'''
    def output_enable(self, ch, value):
        if value == 1:
            self.inst.write("OUTP%d:STATE 1" % ch)
            self.inst.write("OUTP%d ON" % ch)
        else:
            self.inst.write("OUTP%d:STATE 0" % ch)
            self.inst.write("OUTP%d OFF" % ch)
     
            
    ##########################################################################
    ############################# FETCH COMMANDS #############################
    ##########################################################################
    
    '''Pull all voltage, current, and resistance measurements for channels 1-2
    Variables...
        ch1 - 1 = get data for channel 1; 0 = ignore channel 1
        ch2 - 1 = get data for channel 2; 0 = ignore channel 2'''
    def fetch_all_data(self,ch1,ch2):
        if(ch1 and (not ch2)):
            return self.inst.query_ascii_values("FETC:ARR? (@1)")
        elif( (not ch1) and ch2):
            return self.inst.query_ascii_values("FETC:ARR? (@2)")
        elif(ch1 and ch2):
            return self.inst.query_ascii_values("FETC:ARR? (@1,2)")
        else:
            print("Nothing happens with neither channel selected, dufus.")
            
    def fetch_last_data(self,ch1,ch2):
        if(ch1 and (not ch2)):
            return self.inst.query_ascii_values("FETC:SCAL? (@1)")
        elif( (not ch1) and ch2):
            return self.inst.query_ascii_values("FETC:SCAL? (@2)")
        elif(ch1 and ch2):
            return self.inst.query_ascii_values("FETC:SCAL? (@1,2)")
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
#    def measure_single_data(self,ch1,ch2):
#        if(ch1 and (not ch2)):
#            return self.inst.query_ascii_values("MEAS:ARR? (@1)")
#        elif( (not ch1) and ch2):
#            return self.inst.query_ascii_values("MEAS:ARR? (@2)")
#        elif(ch1 and ch2):
#            return self.inst.query_ascii_values("MEAS:ARR? (@1,2)")
#        else:
#            print("Nothing happens with neither channel selected, dufus.")
            
    ##########################################################################
    ############################ SOURCE COMMANDS #############################
    ##########################################################################    
    '''changes the immdiate value of the source output'''
    def source_value(self, ch, V0_I1, value):
        if V0_I1 == 0:
            self.inst.write("SOUR%d:VOLT:LEV:IMM:AMPL %e" % (ch, value))
        if V0_I1 == 1:
            self.inst.write("SOUR%d:CURR:LEV:IMM:AMPL %e" % (ch, value))
            
    def set_voltage(self, ch, value):
        self.inst.write("SOUR%d:VOLT:TRIG %e" % (ch, value))
        
    def set_current(self, ch, value):
        self.inst.write("SOUR%d:CURR:TRIG %e" % (ch, value))
        
        
    '''Sets the output range of the specified channel'''
    def source_range(self, ch, V0_I1, value):
        value = 200 if (value > 200) else value       
        if V0_I1 ==0:
            self.inst.write("SOUR%d:VOLT:RANG %d" % (ch, value))
        if V0_I1 ==1:
            self.inst.write("SOUR%d:CURR:RANG %d" % (ch, value))

    
    '''Sets whether auto ranging is on or off. value= 0 or 1'''       
    def source_auto_range(self, ch, V0_I1, value):
        if V0_I1 ==0:
            self.inst.write("SOUR%d:VOLT:RANG:AUTO %d" % (ch, value))
        if V0_I1 ==1:
            self.inst.write("SOUR%d:CURR:RANG:AUTO %d" % (ch, value))
         
    '''Specifies the lower limit for automatic output ranging'''  
    def source_auto_range_llim(self, ch, V0_I1, value):
        if V0_I1 ==0:
            self.inst.write("SOUR%d:VOLT:RANG:AUTO:LLIM %d" % (ch, value))
        if V0_I1 ==1:
            self.inst.write("SOUR%d:CURR:RANG:AUTO:LLIM %d" % (ch, value))  
     
            
    '''Sets source output mode. Value= VOLTage ot CURRent'''
    def source_mode(self, ch, value):
            self.inst.write("SOUR%s:FUNC:MODE %s" % (ch, value))
       
    '''Sets output shape. value= DC or PULSed'''       
    def source_pulse(self, ch, DC0_pulse1):
        if DC0_pulse1 == 1:
            self.inst.write("SOUR%s:FUNC:SHAP PULS" % ch)
        else:
            self.inst.write("SOUR%s:FUNC:SHAP DC" % ch)
            
            
    '''Turns on or off continuous triggering value= 0 or 1'''        
    def source_continuous_trigger(self, ch, value):
        self.inst.write("SOUR%d:FUNC:MODE %s" % (ch, value))
    
    '''Outputs data listed in a set spereated by commas. 
                value= list, Ex: 1.0,1.1,1.2...'''
    def source_output_listed_data(self, ch, V0_I1, value):
        if V0_I1 ==0:
            self.inst.write("SOUR%d:LIST:VOLT:APP %d" % (ch, value))
        if V0_I1 ==1:
            self.inst.write("SOUR%d:LIST:CURR:APP %d" % (ch, value))
       
    '''Lists values set for output.'''       
    def source_list_output_data(self, ch, V0_I1, value):
        if V0_I1 ==0:
            self.inst.write("SOUR%d:LIST:VOLT:POIN %d" % (ch, value))
        if V0_I1 ==1:
            self.inst.write("SOUR%d:LIST:CURR:POIN %d" % (ch, value))
       
    '''Sets pulse delay time'''       
    def pulse_delay(self, ch, value):
        value = 100E3 if (value > 100E3) else value
        self.inst.write("SOUR%d:PULS:DEL %e" % (ch, value))
    
    '''Sets pulse width time'''
    def pulse_width(self, ch, value):
        value = 50E-6 if (value < 50E-6) else value
        value = 100E3 if (value > 100E3) else value
        self.inst.write("SOUR%d:PULS:WIDT %e" % (ch, value))
    
 ########### Sweep #########           
            
    '''Sets the span value of the sweep'''
    def source_sweep_span(self, ch, V0_I1, value):
        if V0_I1 == 0:
            self.inst.write("SOUR%d:VOLT:SPAN %d" % (ch, value))
        if V0_I1 == 1:
            self.inst.write("SOUR%d:CURR:SPAN %d" % (ch, value))
            
    '''Sets the specified channel to fixed, sweep, 
    and listed sweep modes. value= FIX,LIST, SWEep'''        
    def source_sweep(self, ch, V0_I1, fix0_sweep1_list2):
        if V0_I1 == 1:
            if fix0_sweep1_list2 == 1:
                self.inst.write("SOUR%s:CURR:MODE SWE" % ch)
            elif fix0_sweep1_list2 == 2:
                self.inst.write("SOUR%s:CURR:MODE LIST" % ch)
            else:
                self.inst.write("SOUR%s:CURR:MODE FIX" % ch)
        else:
            if fix0_sweep1_list2 == 1:
                self.inst.write("SOUR%s:VOLT:MODE SWE" % ch)
            elif fix0_sweep1_list2 == 2:
                self.inst.write("SOUR%s:VOLT:MODE LIST" % ch)
            else:
                self.inst.write("SOUR%s:VOLT:MODE FIX" % ch)
            

    
    '''Sets the number of steps in sweep value= 1 to 2500'''        
    def source_number_sweep_steps(self, ch, V0_I1, value):
        if V0_I1 ==0:
            self.inst.write("SOUR%d:VOLT:POIN %d" % (ch, value))
        if V0_I1 ==1:
            self.inst.write("SOUR%d:CURR:POIN %d" % (ch, value))
            
    '''Sets sweep direction. Value: 0=UP or 1=DOWN'''
    def set_sweep_direction(self, ch, value):
        if value ==1:   
            self.inst.write("SOUR%d:SWE:DIR DOWN" % (ch))
        else:
            self.inst.write("SOUR%d:SWE:DIR UP" % (ch))
            
    '''Sets number of points in a sweep. value= 1-2500'''
    def set_number_sweep_points(self, ch, value):
            self.inst.write("SOUR%d:SWE:POIN %d" % (ch, value))
            
    '''Sets the ranging type for sweeped output.
    value= BEST, AUTO, FIX... BEST is determined by entire sweep
        AUTO is configured for each step'''
    def set_sweep_range_type(self, ch, value):
            if value ==0:
                self.inst.write("SOUR%s:SWE:RANG BEST" % (ch))
            if value ==1:
                self.inst.write("SOUR%s:SWE:RANG AUTO" % (ch))
            if value ==2:
                self.inst.write("SOUR%s:SWE:RANG FIX" % (ch))
            
    '''Sets sweep span with specified start and stop values'''    
    def source_sweep_range(self, ch, V0_I1, start, stop):
        if V0_I1 ==0: 
            self.inst.write("SOUR%d:VOLT:STAR %e" % (ch, start))
            self.inst.write("SOUR%d:VOLT:STOP %e" % (ch, stop))
        if V0_I1 ==1: 
            self.inst.write("SOUR%d:CURR:STAR %e" % (ch, start))
            self.inst.write("SOUR%d:CURR:STOP %e" % (ch, stop))
    
    '''Sets the intervals between sweep steps'''
    def source_sweep_step(self, ch, V0_I1, value):
        if V0_I1 ==0:
            self.inst.write("SOUR%d:VOLT:STEP %f" % (ch, value))
        if V0_I1 ==1:
            self.inst.write("SOUR%d:VOLT:STEP %f" % (ch, value))
            
    '''Sets sweep scale type. value= LINear or LOGarithmic'''
    def set_sweep_scaling(self, ch, value):
            self.inst.write("SOUR%s:SWE:SPAC %s" % (ch, value))
            
    '''Sets the sweep type. value: 0 = SINGle or 1 = DOUBle'''
    def sweep_bidirectional(self, ch, value):
        if value == 1:
            self.inst.write("SOUR%s:SWE:STA SING" % ch)       
        else:
            self.inst.write("SOUR%s:SWE:STA SING" % ch)       
        
    #wait commands?
    ##########################################################################
    ########################### Trigger Commands #############################
    ##########################################################################
    '''ch1 - 0 = get data for channel 1; 1 = ignore channel 1
        ch2 - 0 = get data for channel 2; 1 = ignore channel 2'''
    def arm_channel(self,ch):
        self.inst.write("ARM:IMM (@%d)" % ch)
            
    def arm_counts(self,ch,value):
        if value > 10000:
            self.inst.write("ARM%d:COUN INF" %ch )
        else:
            self.inst.write("ARM%d:COUN %d" % (ch, value))
            
    def arm_source_period(self, ch, value):
        self.inst.write("ARM%d:TRAN:TIM %e" % (ch, value))
    
    def arm_measure_period(self, ch, value):
        self.inst.write("ARM%d:ACQ:TIM %e" % (ch, value))
     
    def arm_period(self, ch, value):
        self.inst.write("ARM%d:TIM %e" % (ch, value))
     
    def arm_source_delay(self, ch, value):
        self.inst.write("ARM%d:TRAN:DEL %e" % (ch, value))
    
    def arm_measure_delay(self, ch, value):
        self.inst.write("ARM%d:ACQ:DEL %e" % (ch, value))
    
    def arm_delay(self, ch, value):
        self.inst.write("ARM%d:DEL %e" % (ch, value))  
            
            
            
            
            
            
            
            
            
       
        '''1 to 100000'''
    def trigger_counts(self, ch, value):
        self.inst.write("TRIG%d:COUN %e" % (ch, value))
       
    def trigger_source_period(self, ch, value):
        self.inst.write("TRIG%d:TRAN:TIM %e" % (ch, value))
    
    def trigger_measure_period(self, ch, value):
        self.inst.write("TRIG%d:ACQ:TIM %e" % (ch, value))
     
    def trigger_period(self, ch, value):
        self.inst.write("TRIG%d:TIM %e" % (ch, value))
     
    def trigger_source_delay(self, ch, value):
        self.inst.write("TRIG%d:TRAN:DEL %e" % (ch, value))
    
    def trigger_measure_delay(self, ch, value):
        self.inst.write("TRIG%d:ACQ:DEL %e" % (ch, value))
    
    def trigger_delay(self, ch, value):
        self.inst.write("TRIG%d:DEL %e" % (ch, value))    
            
        
        
        
        
    def initialize(self, ch1, ch2):
        if(ch1 and (not ch2)):
            self.inst.write("INIT:IMM:ALL (@1)")
        elif( (not ch1) and ch2):
            self.inst.write("INIT:IMM:ALL (@2)")
        elif(ch1 and ch2):
            self.inst.write("INIT:IMM:ALL (@1,2)")
        else:
            print("Nothing happens with neither channel selected, dufus.") 
            
        
        
    ##########################################################################
    ########################## High level commands ###########################
    ##########################################################################
    '''compliance - sets the source mode and compliance level
    variables...
        ch = channel
        src_v_or_i: source mode = 0 for voltage, 1 for current
        value = complaince level in A or V for sourcing voltage or current, respectively'''
    def compliance(self, ch, src_v_or_i, value):
        #source voltage / limit current
        if src_v_or_i == 0:
            self.inst.write("SOUR%d:FUNC:MODE VOLT" % (ch))
            self.inst.write("SENS%d:CURR:PROT %s" % (ch, value))
            #return " ".join(["Sourcing:",self.inst.query_ascii_values("SOUR%d:FUNC:MODE?" % ch,converter = "s")[0].rstrip("\n"),"Compliance Level:",self.inst.query_ascii_values("SENS%d:CURR:PROT?" % ch,converter = "s")[0].rstrip("\n")])
        #source current / limit voltage
        if src_v_or_i == 1:
            self.inst.write("SOUR%d:FUNC:MODE CURR" % (ch))
            self.inst.write("SENS%d:VOLT:PROT %s" % (ch, value))
            #return " ".join(["Sourcing:",self.inst.query_ascii_values("SOUR%d:FUNC:MODE?" % ch,converter = "s")[0].rstrip("\n"),"Compliance Level:",self.inst.query_ascii_values("SENS%d:VOLT:PROT?" % ch,converter = "s")[0].rstrip("\n")])
        
    def measurement_all(self, ch1, ch2, tmax=3000):
        #Initialized the selected channels
        if ch1 and (not ch2):
            self.inst.write("INIT (@1)")
        elif (not ch1) and ch2: 
            self.inst.write("INIT (@1)")
        elif ch1 and ch2:
            self.inst.write("INIT (@1,2)")
        else:
            print("Select a channel, jackass")
            return
          
        #Check to see if the instrument is busy
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
            return self.fetch_all_data(ch1, ch2)
        else:
            return None
        
    def measurement_single(self, ch1, ch2, tmax=300):
        #Initialized the selected channels
        if ch1 and (not ch2):
            self.inst.write("INIT (@1)")
        elif (not ch1) and ch2: 
            self.inst.write("INIT (@1)")
        elif ch1 and ch2:
            self.inst.write("INIT (@1,2)")
        else:
            print("Select a channel, jackass")
            return
          
        #Check to see if the instrument is busy
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
            return self.fetch_last_data(ch1, ch2)
        else:
            return None


    ''' trigger_setup_dc - sets triggering time and count for DC spot/sweep measurements'''
    def trigger_setup_dc(self, ch, npts):
        self.arm_channel(ch)
        self.arm_counts(ch,1)
        self.arm_period(ch, 10E-6)
        self.arm_delay(ch, 0)
        
        self.trigger_period(ch, 10E-6)
        self.trigger_delay(ch, 0)
        self.trigger_counts(ch,npts)
        
    ''' trigger_setup_pulse - sets trigger time, delay, and count  for pulsed spot/sweep measurements'''
    def trigger_setup_pulse(self, ch, npts, period):
        self.arm_channel(ch)
        self.arm_counts(ch,1)
        self.arm_period(ch, 10E-6)
        self.arm_delay(ch, 0)
        
        #Make sure that the measurement delay is > 0, and then set it to be towards the end of the pulse
        meas_delay = float(self.inst.query("SOUR%d:PULS:WIDT?" % ch)) - float(self.inst.query("SENS%d:VOLT:DC:APER?" % ch))*1.1
        meas_delay = 0 if (meas_delay < 0) else meas_delay
        
        
        self.trigger_period(ch, period)
        self.trigger_measure_delay(ch, meas_delay)
        self.trigger_counts(ch,npts)
        
    ''' dc_internal_IV - performs internal voltage sweep for a single channel'''    
    def dc_internal_IV(self, bias_start, bias_stop, bias_step, current_limit, compliance_protection,
                       int_time, timeout):
        
        #set ch 1 to source voltage, ch 2 to only read current w/ 100 mA compliance
        self.compliance(1, 0, current_limit)
        self.source_auto_range(1, 0, 1)
        
        #Set up sense subsystem for integration, sensitivity, etc.
        self.integration_time(1,int_time)
        self.sense_measurements(1, 1, 1, 1)
        self.sense_range_auto(1, 0, 1)
        self.sense_range_auto(1, 1, 1)
        self.sense_range_auto(1, 2, 1)

        
        self.source_pulse(1, 0)
        self.sweep_bidirectional(1, 0)
        self.set_sweep_direction(1, 0)   #sweeps from low to high
        self.source_sweep(1, 0, 1)
        self.source_sweep_range(1, 0, bias_start, bias_stop)
        self.source_sweep_step(1, 0, bias_step)

        #If the smu hits compliance stop the sweep
        self.output_over_protection(1, compliance_protection)        
        
        #Set arm both channels and set trigger delays to 0
        npts = abs((bias_stop - bias_start)/bias_step) + 1
        self.trigger_setup_dc(1, npts)

        #Initiate both channels and measure data
        self.output_enable(1,1);
        dat = self.measurement_all(1,0, timeout)
        dat = np.reshape(dat,[np.size(dat)/6,6])
        VIR = np.array( [dat[:,0], dat[:,1], dat[:,2]] ).T #return voltage | current | resistance
        
        #Disable the sources and collect any errors
        self.source_value(1,0,0)
        self.output_enable(1,0)    
        self.error_all()
        
        return VIR


    def dc_internal_LIV(self, bias_start, bias_stop, bias_step, current_limit, photocurrent_limit, 
                        compliance_protection, int_time, timeout):
        
        #set ch 1 to source voltage, ch 2 to only read current w/ 100 mA compliance
        self.compliance(1, 0, current_limit)
        self.source_auto_range(1, 0, 1)
        self.compliance(2, 0, photocurrent_limit)
        self.source_auto_range(2, 0, 1)
        
        #Set up sense subsystem for integration, sensitivity, etc.
        self.integration_time(1,int_time)
        self.sense_measurements(1, 1, 1, 0)
        self.sense_range_auto(1, 0, 1)
        self.sense_range_auto(1, 1, 1)
        
        self.integration_time(2,int_time)
        self.sense_measurements(1, 1, 1, 0)
        self.sense_range_auto(1, 0, 1)
        self.sense_range_auto(1, 1, 1)

        self.source_pulse(1, 0)
        self.sweep_bidirectional(1, 0)
        self.set_sweep_direction(1, 0)   #sweeps from low to high
        self.source_sweep(1, 0, 1)
        self.source_sweep_range(1, 0, bias_start, bias_stop)
        self.source_sweep_step(1, 0, bias_step)

        #If the smu hits compliance stop the sweep
        self.output_over_protection(1, compliance_protection)        
        self.output_over_protection(2, compliance_protection)   
        
        #Set arm both channels and set trigger delays to 0
        npts = abs((bias_stop - bias_start)/bias_step) + 1
        self.trigger_setup_dc(1, npts)
        self.trigger_setup_dc(2, npts)

        #Initiate both channels and measure data
        self.output_enable(1,1)
        self.output_enable(2,1)
        dat = self.measurement_all(1,1, timeout)
        dat = np.reshape(dat,[np.size(dat)/12,12])
        VIL = np.array( [dat[:,0], dat[:,1], dat[:,7]] ).T #return voltage | current | photocurrent
        
        #Disable the sources and collect any errors
        self.source_value(1,0,0)
        self.source_value(2,0,0)
        self.output_enable(1,0)    
        self.output_enable(2,0)    
        self.error_all()
        
        return VIL
        
    def pulsed_internal_LIV(self, bias_start, bias_stop, bias_step,
                            current_limit, photocurrent_limit,
                            int_time, pulse_width, pulse_period, timeout):
        
        #set ch 1 to source voltage, ch 2 to only read current w/ 100 mA compliance
        self.compliance(1, 0, current_limit)
        self.source_auto_range(1, 0, 0)
        self.source_range(1,0,10*bias_stop)
        self.compliance(2, 0, photocurrent_limit)
        self.source_auto_range(2, 0, 0)
        self.source_range(2, 0, 2)
        
        #Set up sense subsystem for integration, sensitivity, etc.
        self.integration_time(1,int_time)
        self.integration_time(2,int_time)
        self.sense_measurements(1, 1, 1, 0)  
        self.sense_measurements(2, 1, 1, 0)             

        self.sense_range_auto(1, 0, 1)
        self.sense_range_auto(1, 1, 1)
        self.sense_range_auto(2, 0, 1)
        self.sense_range_auto(2, 1, 1)




        # Set up pulsed sweep
        self.source_pulse(1, 1)         #turn on pulsed measurements
        self.pulse_delay(1,0)           #set delay to 0
        self.pulse_width(1,pulse_width)       #set pulse width
        self.sweep_bidirectional(1, 0)  #single direction sweep
        self.set_sweep_direction(1, 0)  #sweeps from low to high
        self.source_sweep(1, 0, 1)      
        self.source_sweep_range(1, 0, bias_start, bias_stop)
        self.source_sweep_step(1, 0, bias_step)

        #If the smu hits compliance stop the sweep
        self.output_over_protection(1, 0)        
        self.output_over_protection(2, 0)   
        
        #Set arm both channels and set trigger delays to (pulse_width - 1.1*int_time)
        npts = abs((bias_stop - bias_start)/bias_step) + 1
        self.trigger_setup_pulse(1, npts, pulse_period)
        self.trigger_setup_pulse(2, npts, pulse_period) 

        #Initiate both channels and measure data
        self.output_enable(1,1)
        self.output_enable(2,1)
        dat = self.measurement_all(1,1, timeout)
        dat = np.reshape(dat,[np.size(dat)/12,12])
        VIL = np.array( [dat[:,0], dat[:,1], dat[:,7]] ).T #return voltage | current | photocurrent
        
        #Disable the sources and collect any errors
        self.source_value(1,0,0)
        self.source_value(2,0,0)
        self.output_enable(1,0)    
        self.output_enable(2,0)    
        self.error_all()
        
        return VIL