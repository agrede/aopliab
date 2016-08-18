import numpy as np
import matplotlib.pylab as plt
import aopliab_common as ac
import visa
from keysight import Keysight2900
import iv
import time

#Initialize resource manager and open the SMU
addr = "USB0::0x0957::0x8E18::MY51141103::0::INSTR"
rm = visa.ResourceManager()
instr = rm.open_resource(addr)
smu = Keysight2900(instr)

# Device identification

dc_bias_start = -2;   dc_bias_stop = 7;   dc_bias_step = .005;
current_limit = .01
integ_time = 3/60

pulse_bias_start = 2.5;   pulse_bias_stop = 8.5;   pulse_bias_step = .005;
voltages = np.arange(pulse_bias_start, pulse_bias_stop + pulse_bias_step, pulse_bias_step)
pulsed_current_limit = 1.515
pulse_integ_time = 8E-6

photocurrent_limit = 0.5
pulse_width = 95E-6
pulse_period = pulse_width*1E3
compliance_protection = True
timeout = 3000


fpath = 'C:/Users/jspri/Dropbox/Jared/Data/2016_8-17 - LED Retake w Pulse Generator/Perovskite/DC/'

count = 1  #LIV run number
dcreps = np.arange(0,30,1)
preps = np.arange(0,10,1)

#print("Pulsed")
#for k in preps:
#    print("Run %d" %k)
#    liv = iv.pulsed_livmeasure_2900(voltages, 
#         pulsed_current_limit, photocurrent_limit,
#         pulse_integ_time, pulse_width, pulse_period, 
#         timeout, addr); 
#    fname = ('385GaN_LIV%2d - Pulsed Sweep %2.2fV to %2.2fV - width %1.2E - period - %1.2E.txt' %(count, pulse_bias_start, pulse_bias_stop, pulse_width, pulse_period))
#    np.savetxt(''.join([fpath,fname]),liv)
#    count+=1
#    plt.semilogy(liv[:,0],liv[:,1])
#    time.sleep(5)   #dwell after the measurement
    

# internal sweeps
print("DC")
for k in dcreps:
    print("Run %d" %k)
    liv = smu.dc_internal_LIV(dc_bias_start, dc_bias_stop, dc_bias_step, current_limit, 
                               photocurrent_limit, compliance_protection, integ_time, timeout)
    fname = ('S01_D05_Run%2d - HiRes DC Sweep - pre pulse.txt' %count)
    np.savetxt(''.join([fpath,fname]),liv)
    plt.semilogy(liv[:,0],liv[:,1])
    count+=1
    time.sleep(5)   #dwell after the measurement


