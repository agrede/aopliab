import numpy as np
import aopliab_common as ac
import visa
from keysight import Keysight2900


#Initialize resource manager and open the SMU
rm = visa.ResourceManager()
addr = "USB0::0x0957::0x8E18::MY51141103::0::INSTR"
instr = rm.open_resource(addr)
smu = Keysight2900(instr)

#current_limit = 1E-2
#bias_start = 0
#bias_stop = 10
#bias_step = 0.1


dat = smu.dc_internal_LIV(0, 10, 1, 1E-2, 8E-6)
dat2 = np.reshape(dat,[np.size(dat)/12,12])

dat3 = smu.fetch_last_data(1,1)
dat4 = np.reshape(dat3,[np.size(dat3)/12,12])
#Not working...
#smu.integration_time_NPLC(2,1)  #undefined header?
#(smu.sense_range_auto_ulim(1,0,1))  #-113 undefined header error

#Untested...
#smu.get_data(1,0)
#smu.measure_single_data(0,1)