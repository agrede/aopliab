# Import shit...
import numpy as np
import matplotlib.pylab as plt
import aopliab_common as ac
import visa
from keysight import InfiniiVision5000
from keysight import InfiniiVision5000Channel
import time




## Set up file name and outputs
fpath = 'C:/Users/jspri/Dropbox/Jared/Data/2016_8-17 - LED Retake w Pulse Generator/New LED385L/Raw Scope Data/'

##Initialize resource manager and open the scope
#rm = visa.ResourceManager()
#osc = ac.getInstr(rm,'InfiniiVision5000','./configs/keysight.json')
addr = "USB0::0x0957::0x1765::MY48200170::INSTR"
rm = visa.ResourceManager()
instr = rm.open_resource(addr)
osc = InfiniiVision5000(instr)

# Pull the number of points that the scope is recording; I throw away the first one
num_pts = int(osc.preamble[2])
chs = np.arange(0,3)    #Set chs 1-3 to be read

## Initialize the arduino
ard = ac.getSer('JeffARD'); time.sleep(2)
msg = b'single'

# Set up local arduino variables
steps_per_trig = b'1'                               #number of steps per each call of "single" [# steps]
max_steps = 270                                     #number of stepper steps to take; 270 is ~ full range
trigs = np.arange(0,max_steps,int(steps_per_trig))
off_time = b'10'                                    #time between pulses in [ms]
avgs = b'8'                                         #number of pulses to send per each call of "average"
ard.write(b'set_steps');    time.sleep(2);  ard.write(steps_per_trig);  print(''.join(["Steps per trigger: ", ard.readline().decode('utf-8') ]));
ard.write(b'set_dwell');    time.sleep(2);  ard.write(off_time);        print(''.join(["Delay between pulses (ms): ", ard.readline().decode('utf-8') ]));
ard.write(b'set_avgs');     time.sleep(2);  ard.write(b'8');            print(''.join(["Number of pulses to average : ", ard.readline().decode('utf-8') ]));

pres_step = 0;
r_pd = 50   #50 ohm scope termination
r_s = 10.01 #10 ohm series resistance


## BEGIN THE MAGIC!!!
#repeats = np.arange(0,10)
#for count in repeats:
count = 8
print("Repeat %d" %count)
fname = 'LED385L_Run%2d - Voltage Range 15-50V - Pulse ' % count

osc.trig_single()
ard.write(b'first_single'); ard.readline()

### pull data for each channel; since time is independent, only do that once
### dat == [time, ch1, ch2, ch3]
dat = np.zeros([num_pts-1,np.size(chs)+1])
for ch in chs:
    dat[:,ch+1] = osc.voltages(ch+1)   
dat[:,0] = osc.times[1:num_pts]

# Convert voltage readings to current for I_device and I_pd
dat[:,2] = dat[:,2] / r_s
dat[:,3] = dat[:,3] / r_pd

# Write out data
np.savetxt(''.join([fpath,fname,str(pres_step*int(steps_per_trig)),'.txt']),dat)

############ START LOOP
for k in trigs:
    osc.trig_single()
    ard.write(msg)
    pres_step = int(ard.readline())
    print(''.join(["Step # %d out of %d" % (pres_step*int(steps_per_trig), int(max_steps))]) )
    

    ### pull data for each channel; since time is independent, only do that once
    ### dat == [time, ch1, ch2, ch3]
    dat = np.zeros([num_pts-1,np.size(chs)+1])
    for ch in chs:
        dat[:,ch+1] = osc.voltages(ch+1)   
    dat[:,0] = osc.times[1:num_pts]
    
    # Convert voltage readings to current for I_device and I_pd
    dat[:,2] = dat[:,2] / r_s
    dat[:,3] = dat[:,3] / r_pd
    
    # Write out data
    np.savetxt(''.join([fpath,fname,str(pres_step*int(steps_per_trig)),'.txt']),dat)
############ END LOOP

#bring the voltage knob back home, then restart loop
ard.write(b'reset');    print(ard.readline().decode('utf-8')) 

#bring the voltage knob back home, then restart loop
ard.close()
osc.inst.close()