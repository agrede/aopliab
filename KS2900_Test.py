import numpy as np
import aopliab_common as ac
import visa
from keysight import Keysight2900
from iv import livmeasure_2900

#Initialize resource manager and open the SMU
addr = "USB0::0x0957::0x8E18::MY51141103::0::INSTR"
rm = visa.ResourceManager()
instr = rm.open_resource(addr)
smu = Keysight2900(instr)

bias_start = 0.0;   bias_stop = 10.0;   bias_step = 1;
voltages = np.arange(bias_start, bias_stop + bias_step, bias_step)
current_limit = 1E-2
photo_current_limit = 0.1
integ_time = "AUTO"

# single channel internal sweep
#x = smu.dc_internal_IV(bias_start, bias_stop, bias_step, current_limit, integ_time)

# dual channel external sweep
[x,y,z] = livmeasure_2900(voltages, current_limit, photo_current_limit, integ_time, addr)

#Not working...
#smu.integration_time_NPLC(2,1)  #undefined header?
#(smu.sense_range_auto_ulim(1,0,1))  #-113 undefined header error

#Untested...
#smu.get_data(1,0)
#smu.measure_single_data(0,1)