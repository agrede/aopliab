import numpy as np
import matplotlib.pylab as plt
import aopliab_common as ac
import visa
from keysight import InfiniiVision5000
from keysight import InfiniiVision5000Channel
import iv
import time

#Initialize resource manager and open the SMU
addr = "USB0::0x0957::0x1765::MY48200170::INSTR"
rm = visa.ResourceManager()
instr = rm.open_resource(addr)
osc = InfiniiVision5000(instr)

#Pull the number of points that the scope is recording; I throw away the first one
num_pts = int(osc.preamble[2])

osc.trig_single()
time.sleep(3)

#Read off chs 1-3
chs = np.arange(0,3)

#pull data for each channel; since time is independent, only do that once
# dat == [time, ch1, ch2, ch3]
dat = np.zeros([num_pts-1,np.size(chs)+1])
for ch in chs:

    dat[:,ch+1] = osc.voltages(ch+1)   
dat[:,0] = osc.times[1:num_pts]


# Convert voltage readings to current for I_device and I_pd
r_pd = 50   #50 ohm scope termination
r_s = 10.01 #10 ohm series resistance
dat[:,2] = dat[:,2] / r_s
dat[:,3] = dat[:,3] / r_pd

# Write out data
#fpath = 'H:/dat'
#fname = 'test.txt'
#np.savetxt(''.join([fpath,fname]),dat)

osc.inst.close()