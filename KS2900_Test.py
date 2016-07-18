import numpy as np
import matplotlib.pylab as plt
import aopliab_common as ac
import visa
from keysight import Keysight2900
import iv

#Initialize resource manager and open the SMU
addr = "USB0::0x0957::0x8E18::MY51141103::0::INSTR"
rm = visa.ResourceManager()
instr = rm.open_resource(addr)
smu = Keysight2900(instr)

bias_start = 0.0;   bias_stop = 2.5;   bias_step = .01;
voltages = np.arange(bias_start, bias_stop + bias_step, bias_step)
current_limit = 1.515
photocurrent_limit = .1
integ_time = 8E-6
pulse_width = 50E-6
pulse_period = 10E-3
compliance_protection = True
timeout = 3000

# internal sweeps
#x = smu.dc_internal_IV(bias_start, bias_stop, bias_step, current_limit, integ_time, timeout)
#liv = smu.dc_internal_LIV(bias_start, bias_stop, bias_step, current_limit, 
#                           photocurrent_limit, compliance_protection, integ_time, timeout)


liv = smu.pulsed_internal_LIV(bias_start, bias_stop, bias_step, current_limit, 
                              photocurrent_limit, integ_time, pulse_width,
                              pulse_period, timeout)



    
#need to remove values == 9.910e+37 - what's the simplest way?
#plt.plot(liv[:,0],liv[:,1])

# dual channel external sweep
#[x,y,z] = iv.livmeasure_2900(voltages, current_limit, photocurrent_limit, integ_time, addr)
liv2 = iv.pulsed_livmeasure_2900(voltages, current_limit, photocurrent_limit,
       integ_time, pulse_width, pulse_period, 
       timeout, addr); 
liv2 = np.asarray(liv).T


#Not working...
#smu.integration_time_NPLC(2,1)  #undefined header?
#(smu.sense_range_auto_ulim(1,0,1))  #-113 undefined header error
