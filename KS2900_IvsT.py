import numpy as np
import aopliab_common as ac
import matplotlib.pylab as plt
import visa
from keysight import Keysight2900
import time
import os
 

  
# Stuff that you change
integ_time = 3/60           #Integration time for measurements - 3 power line cycles is usually sufficient
t_max = 240             # total length of measurement [s]

#Set file path and create directory if it doesn't exist yet    
fpath = 'C:/Users/ho4jc/Desktop/Box Sync/Experiments_PSU/IV/170504/'
fname = '5s_45mW_5_temp_3.txt'
if not os.path.exists(fpath):
  os.makedirs(fpath)


  

####################################################
##### Prepare the sourcemeter for measurements #####
####################################################

# Initialize resource manager and open the SMU
addr = "USB0::0x0957::0x8E18::MY51141103::0::INSTR"
rm = visa.ResourceManager()
instr = rm.open_resource(addr)
smu = Keysight2900(instr)
timeout = 3000

# set ch 1 to source voltage, ch 2 to only read current 
photocurrent_limit = 0.5    #Arbitrary upper limit for photocurrent
smu.compliance(1, 0, photocurrent_limit)
smu.source_auto_range(1, 0, 1)  #set sourcing range (src1, voltage, auto-ranging on)
smu.source_auto_range(1, 1, 1)  #set sourcing range (src1, current, auto-ranging on)
smu.compliance(2, 0, photocurrent_limit)
smu.source_auto_range(2, 0, 1)  #set sourcing range (src2, voltage, auto-ranging on)
smu.source_auto_range(2, 1, 1)  #set sourcing range (src2, current, auto-ranging on)

# Set up sense subsystem for integration, measure I/V/L, autosensitivity first for source 1, then source 2
smu.integration_time(1,integ_time)  # set integration time (src1, time)
smu.sense_measurements(1, 1, 1, 0)  # set to record the following data (src1, voltage - on, current - on, resistance - off)
smu.sense_range_auto(1, 0, 1)   # set measurement/sense to auto-range (src1, voltage, auto-ranging on)
smu.sense_range_auto(1, 1, 1)   # set measurement/sense to auto-range (src1, current, auto-ranging on)
smu.sense_range_auto_llim(1, 1, "MIN") #set lower current measurement range to the instrument's minimum (src1, current, minimum hardware value)

smu.integration_time(2,integ_time)  # set integration time (src2, integration time)
smu.sense_measurements(2, 1, 1, 0)  # set to record the following data (src2, voltage - on, current - on, resistance - off)
smu.sense_range_auto(2, 0, 1)   # set measurement/sense to auto-range (src2, voltage, auto-ranging on)
smu.sense_range_auto(2, 1, 1)   # set measurement/sense to auto-range (src2, current, auto-ranging on)
smu.sense_range_auto_llim(2, 1, "MIN")  #set lower current measurement range to the instrument's minimum (src2, current, minimum hardware value)

# Disable pulsing and any sweeps
smu.source_pulse(1, 0)
smu.source_sweep(1, 0, 0)
smu.source_pulse(2, 0)
smu.source_sweep(2, 0, 0)

# Enable protection such that if the smu hits compliance, the source will turn off
# this is probably unimporant for this measurement
#smu.output_over_protection(1, 1)        
#smu.output_over_protection(2, 1)    

# Arm both channels and set trigger delays to 0; one trigger per measurement
smu.trigger_setup_dc(1, 1)  # arm source 1 (src1, arm - on)
smu.trigger_setup_dc(2, 1)  # arm source 2 (src1, arm - on)

# Set initial voltage and turn on output
# Since we are only measuring Isc, set both voltages to 0
smu.set_voltage(1,0)    #set voltage (src1, value)
smu.output_enable(1,1)  #enable output (src1, output = on)
smu.set_voltage(2,0)    #set voltage (src2, value)
smu.output_enable(2,1)  #enable output (src2, output = on)

#Turn off display
smu.disp(0)





##############################
##### Begin measurements #####
##############################
meas_curr1 = []  # List of measured currents from source 1/device
meas_curr2 = []  # List of measured currents from source 2/photodiode
t_pres = []     # present time

#p1 = ac.DynamicPlot("semilogy","-x")
#p2 = ac.DynamicPlot("semilogy","-o")

time.sleep(5)

#Initialize timer
t_elapsed = 0;
t_start = time.time()

while t_elapsed < t_max:    
    
    # Trigger and read measurements
    meas = smu.measurement_single(1,1)
    
    # Pull elapsed time
    t_elapsed = time.time()-t_start
    print("Present time %3d", t_elapsed)
    
    # Append measurements arrays
    t_pres.append(t_elapsed)  
    meas_curr1.append(meas[1])
    meas_curr2.append(meas[7])
    dat = np.array([t_pres, meas_curr1, meas_curr2]).T

    # Save the data and update the plot
    np.savetxt(''.join([fpath,fname]),dat)

    ## end for t in times

print("Measurement Complete")

#plt.plot(dat[:,0],abs(dat[:,1]))
#plt.plot(dat[:,0],abs(dat[:,2]))
#plt.plot(dat[:,0],abs(dat[:,2]/dat[1,2]))
#plt.plot(dat[:,0],abs(dat[:,1]/dat[1,1]))

#plt.plot(dat[:,0],abs(dat[:,1]/dat[:,2]))
#plt.plot(dat[:,0],(dat[:,2]/dat[1,2])/(dat[:,1]/dat[1,1]) )

#Shut down the sourcemeter - disable the sources, get errors, and close connection
smu.disp(1)
smu.source_value(1,0,0)
smu.output_enable(1,0)  
smu.source_value(2,0,0)
smu.output_enable(2,0)   
smu.error_all()     
 