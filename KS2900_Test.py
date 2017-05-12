import numpy as np
import matplotlib.pylab as plt
import visa
from keysight import Keysight2900
import time

#Initialize resource manager and open the SMU
addr = "USB0::0x0957::0x8E18::MY51141103::0::INSTR"
rm = visa.ResourceManager()
instr = rm.open_resource(addr)
smu = Keysight2900(instr)

#initialize runs with: runs = np.zeros(shape=(10,3))
runs = runs
sNum = 1
dNum = 3
temp = 31

dc_bias_start = -0.5;   dc_bias_stop = 6;   dc_bias_step = .05; 
Jmax = 100 #mA/cm^2

# Get the device size
if (dNum == 3 or dNum == 8):
    l = 4
    w = 4
    A = l*w/100 #area in cm^2
else:
    l = 2
    w = 2
    A = l*w/100 #area in cm^2

#Get sample composition
if (sNum == 1 or sNum ==2):
    sName = '25pct Tef'
else:
    sName = '00pct Tef'

fpath_base = 'C:/Users/Jared/Dropbox/Jared/Data/2017_01-16 - PTFE-NPD OLEDs/'
fpath = ''.join([fpath_base, ('S%02dD%02d - %s/' %(sNum, dNum, sName))] )

#Set up the SMU
current_limit = Jmax * A / 1000
dcreps = np.arange(0,2,1)
integ_time = 3/60
photocurrent_limit = 0.5
compliance_protection = True
timeout = 3000
t_dwell = 5 #dell time between consecutive measurements [s]

# internal sweeps
print("DC")
for k in dcreps:
    
    #Increment the run counter
    runs[dNum-1][sNum-1] = runs[dNum-1][sNum-1] + 1
    print("S%02d D%02d Run %d" %(sNum, dNum, runs[dNum-1][sNum-1]))

    #Run the LIV
    liv = smu.dc_internal_LIV(dc_bias_start, dc_bias_stop, dc_bias_step, current_limit, 
                               photocurrent_limit, compliance_protection, integ_time, timeout)
    fname = ('S%02dD%02dR%02d - %s - %003dC.txt' %(sNum, dNum, runs[dNum-1][sNum-1], sName, temp ) )
    np.savetxt(''.join([fpath,fname]),liv)
    plt.semilogy(liv[:,0],liv[:,1])
    time.sleep(t_dwell)   #dwell after the measurement



#Pulsed Setup
#preps = np.arange(0,10,1)
#pulse_bias_start = 2.5;   pulse_bias_stop = 8.5;   pulse_bias_step = .005;
#voltages = np.arange(pulse_bias_start, pulse_bias_stop + pulse_bias_step, pulse_bias_step)
#pulsed_current_limit = 1.515
#pulse_integ_time = 8E-6
#pulse_width = 95E-6
#pulse_period = pulse_width*1E3

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
    