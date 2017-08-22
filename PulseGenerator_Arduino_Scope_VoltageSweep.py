# Import shit...
import numpy as np
import aopliab_common as ac
import visa
from keysight import InfiniiVision5000
from keysight import InfiniiVision5000Channel
from time import sleep

## Set up file name and outputs
fpath = "C:/Users/Maxwell/Desktop/Student Data/Grede/2017-06-09/"#test1.npz"

##Initialize resource manager and open the scope
rm = visa.ResourceManager()
osci = ac.getInstr(rm, "OScope")
osc = InfiniiVision5000(osci)
osc1 = InfiniiVision5000Channel(osc, 1)
osc2 = InfiniiVision5000Channel(osc, 2)
osc3 = InfiniiVision5000Channel(osc, 3)

## Initialize the arduino
ard = ac.getInstr(rm, 'PulsMotor')

# Set up local arduino variables
steps_per_trig = 2                               #number of steps per each call of "single" [# steps]
max_steps = 295                                  #number of stepper steps to take; 270 is ~ full range
trigs = np.arange(0, max_steps, steps_per_trig)
off_time = 1000                                  #time between pulses in [ms]
avgs = 8                                         #number of pulses to send per each call of "average"
ard.write("set_steps %d" % steps_per_trig)
ard.write("set_dwell %d" % off_time)
ard.write("set_avgs %d" % avgs)

pres_step = 0;
r_pd = 50   #50 ohm scope termination
r_s = 10.01 #10 ohm series resistance


def meas():
    return np.vstack((
            (osc.times),
            (osc1.voltages),
            (osc2.voltages)/r_s,
            (osc3.voltages)/r_pd
            )).T

## BEGIN THE MAGIC!!!
#repeats = np.arange(0,10)
#for count in repeats:
count = 3
print("Repeat %d" %count)
fname = 'S01-D04-Run%2d - Pulsed 5-15V' % count

osc.trig_run()
ard.write("first_single");
osc.digitize()

dat = []
dat.append(meas())

############ START LOOP
for k in trigs[41:]:
    sleep(off_time*1e-3)
    osc.trig_run()
    ard.write("single");
    osc.digitize()
    pres_step += 1
    print(''.join(["Step # %d out of %d" % (pres_step*int(steps_per_trig), int(max_steps))]) )
    
    dat.append(meas())
############ END LOOP
np.savez_compressed(fpath+fname+".npz", dat)

#bring the voltage knob back home, then restart loop
ard.write("reset")

#bring the voltage knob back home, then restart loop
ard.close()
osc.inst.close()