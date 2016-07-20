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

dc_bias_start = -2;   dc_bias_stop = 6;   dc_bias_step = .01;
current_limit = 10E-3
integ_time = 40E-3

pulse_bias_start = -2;   pulse_bias_stop = 15;   pulse_bias_step = .01;
voltages = np.arange(pulse_bias_start, pulse_bias_stop + pulse_bias_step, pulse_bias_step)
pulsed_current_limit = 1.515
pulse_integ_time = 8E-6

photocurrent_limit = 0.5
pulse_width = 110E-6
#pulse_period = 100E-3
pulse_period = pulse_width*1E3
compliance_protection = True
timeout = 3000

    
#need to remove values == 9.910e+37 - what's the simplest way?
#plt.plot(liv[:,0],liv[:,1])

# internal sweeps
liv = smu.dc_internal_LIV(dc_bias_start, dc_bias_stop, dc_bias_step, current_limit, 
                           photocurrent_limit, compliance_protection, integ_time, timeout)

# dual channel external sweep
#liv = iv.pulsed_livmeasure_2900(voltages, pulsed_current_limit, photocurrent_limit,
#       pulse_integ_time, pulse_width, pulse_period, 
#       timeout, addr); 
#liv = np.asarray(liv).T

fpath = 'C:/Users/jspri/Dropbox/Jared/Data/2016_7-20 - Perovskite LED First test/S01D02/'
fname = 'S01D02_LIV08 - DC Sweep - post 110us to 15V.txt'
np.savetxt(''.join([fpath,fname]),liv)