# Import shit...
import os
os.chdir('C:/Users/Maxwell/Desktop/aopliab_JSP Branch 9-20-2016')

import numpy as np
import aopliab_common as ac
import visa
from ametek import SR7230
import time

##Initialize resource manager and open the scope
rm = visa.ResourceManager()
lockin_h = ac.getInstr(rm, "LockInAmp")
lockin = SR7230(lockin_h)

# Set up variables for lockin
dwell = 5   #time to dwell in [s]

avgs = 4
tmp_mag = np.zeros(avgs-1)
tmp_phase = np.zeros(avgs-1)


## Initialize the arduino
ard = ac.getSer('JeffARD'); time.sleep(2)
msg = b'single'

# Set up local arduino variables
steps_per_trig = b'10'                             #number of steps per each call of "single" [# steps]
max_steps = 5                                     #number of stepper steps to take; 270 is ~ full range
trigs = np.arange(0,max_steps,int(steps_per_trig))
off_time = b'1000'                                    #time between pulses in [ms]
ard.write(b'set_steps');    time.sleep(2);  ard.write(steps_per_trig);  print(''.join(["Steps per trigger: ", ard.readline().decode('utf-8') ]));
ard.write(b'set_dwell');    time.sleep(2);  ard.write(off_time);        print(''.join(["Delay between pulses (ms): ", ard.readline().decode('utf-8') ]));

pres_step = 0;


## BEGIN THE MAGIC!!!
dat = np.zeros([np.size(trigs),2])
## Set up file name and outputs
fpath = 'C:/Users/Maxwell/Desktop/Student Data/Rijul/Data'
fname = 'S01-D07-Run%2d - Pulsed 15-50V'
ard.write(b'first_single'); ard.readline()

### pull data 5 times, average last 4, append to data array
for m in np.arange(0,avgs,1):
    time.sleep(dwell)
    if m>0:
        tmp_mag[m-1] = lockin.mag
        tmp_phase[m-1] = lockin.phase
    
dat[0,0] = np.average(tmp_mag)
dat[0,1] = np.average(tmp_phase)

# Write out data
np.savetxt(''.join([fpath,fname,str(pres_step*int(steps_per_trig)),'.txt']),dat)

############ START LOOP
for k in trigs:
    ard.write(msg)
    pres_step = int(ard.readline())
    print(''.join(["Step # %d out of %d" % (pres_step*int(steps_per_trig), int(max_steps))]) )

    ### pull data 5 times, average last 4, append to data array
    for m in avgs:
        time.sleep(dwell)
        if m>0:
            tmp_mag[m-1] = lockin.mag
            tmp_phase[m-1] = lockin.phase
        
    dat[k+1,0] = np.average(tmp_mag)
    dat[k+1,1] = np.average(tmp_phase)
    
############ END LOOP

# Write out data
np.savetxt(''.join([fpath,fname,'.txt']),dat)
    
#bring the voltage knob back home
ard.write(b'reset');    print(ard.readline().decode('utf-8')) 
ard.close()
