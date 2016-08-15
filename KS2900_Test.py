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

# Device identification
fpath = 'C:/Users/jspri/Dropbox/Jared/Data/2016_7-25 - More pulsed SMU/'
#sample = 1
#device = 2
#count = count + 1  #LIV run number

dc_bias_start = -2;   dc_bias_stop = 6;   dc_bias_step = .01;
current_limit = 1E-3
integ_time = 3/60

pulse_bias_start = -2;   pulse_bias_stop = 3;   pulse_bias_step = .1;
voltages = np.arange(pulse_bias_start, pulse_bias_stop + pulse_bias_step, pulse_bias_step)
pulsed_current_limit = 1.515
pulse_integ_time = 8E-6

photocurrent_limit = 0.5
transamp_gain = 1E-6    #gain in A/V
pulse_width = 75E-6
pulse_period = pulse_width*1E3
compliance_protection = True
timeout = 3000

    
#need to remove values == 9.910e+37 - what's the simplest way?
#plt.plot(liv[:,0],liv[:,1])

# internal sweeps
#liv = smu.dc_internal_LIV(dc_bias_start, dc_bias_stop, dc_bias_step, current_limit, 
#                           photocurrent_limit, compliance_protection, integ_time, timeout)
#fname = ('S%2dD%2d_LIV%2d - DC Sweep.txt' %(sample, device, count))

# dual channel external sweep
liv = iv.pulsed_livmeasure_2900(voltages, 
     pulsed_current_limit, photocurrent_limit,
     pulse_integ_time, pulse_width, pulse_period, 
     timeout, addr); 


#liv = iv.pulsed_livmeasure_2900_transamp(voltages, 
#     pulsed_current_limit, transamp_gain,
#     pulse_integ_time, pulse_width, pulse_period, 
#     timeout, addr); 
#fname = ('S%2dD%2d_LIV%2d - Pulsed Sweep %2.2fV to %2.2fV - %1.2E Pulse Width - %1.2E Pulse Period.txt' %(sample, device, count, pulse_bias_start, pulse_bias_stop, pulse_width, pulse_period))
#fname = ('LED851L %2d - Pulsed Sweep %2.2fV to %2.2fV - %1.2E Pulse Width - %1.2E Pulse Period.txt' %(count, pulse_bias_start, pulse_bias_stop, pulse_width, pulse_period))
fname = ('10M Resistor %2d - Pulsed Sweep %2.2fV to %2.2fV - %1.2E Pulse Width - %1.2E Pulse Period.txt' %(count, pulse_bias_start, pulse_bias_stop, pulse_width, pulse_period))



np.savetxt(''.join([fpath,fname]),liv)
plt.semilogy(liv[:,0], abs(liv[:,1]))

