import os
os.chdir('C:/Dropbox/Jared/Python/aopliab')
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
#load with np.genfromtxt('fpath/fname')
try:
  runs
except NameError:
  runs = np.zeros(shape=(10,5))

sNum = 3
dNum = 8
temp = 20

isLIV = True

dc_bias_start = 0;   dc_bias_stop = 10;   dc_bias_step = .05; 
Jmax = 20 #mA/cm^2
#Jmax_low = 3000 #mA/cm^2
#Jmax_high = 3000 #mA/cm^2

# Get the device size
if (dNum == 3 or dNum == 8):
    l = 4
    w = 4
    A = l*w/100 #area in cm^2
else:
    l = 2
    w = 2
    A = l*w/100 #area in cm^2

#Get Princeton device sizes
#if(dNum == 1 or dNum == 2 or dNum == 3):
#    r = 10E-3
#    A = np.pi*r**2/100 #area in cm^2
#elif(dNum == 4 or dNum == 5 or dNum == 6):
#    r = 100E-3
#    A = np.pi*r**2/100 #area in cm^2
#elif(dNum == 7 or dNum == 8 or dNum == 9):
#    r = 25E-3
#    A = np.pi*r**2/100 #area in cm^2
#else: #(dNum == 10 or dNum == 11 or dNum == 12):
#    r = 5E-3
#    A = np.pi*r**2/100 #area in cm^2
    

#Get sample composition / file paths
if(sNum ==  2):
    sName = '13 nm Ag-Al'
elif(sNum == 3):
    sName = '6 nm Al'
elif(sNum == 4):
    sName = '100 nm Al'
else:
    sName = 'Test'

 
#Set file path and create directory if it doesn't exist yet    
fpath_base = 'C:/Dropbox/Jared/Data/2017/2017_05-04 - Taehwan Semitransparent Contacts on Glass/'
fpath = ''.join([fpath_base, ('S%02dD%02d - %s/' %(sNum, dNum, sName))] )
#fpath = ''.join([fpath_base, ('S%02dD%02d/' %(sNum, dNum))] )
if not os.path.exists(fpath):
  os.makedirs(fpath)
    
#Set up the SMU
current_limit = Jmax * A / 1000
dcreps = np.arange(0,1,1)
integ_time = 3/60
photocurrent_limit = 0.5
compliance_protection = True
timeout = 3000
t_dwell = 0 #dell time between consecutive measurements [s]

# internal sweeps
print("DC")
for k in dcreps:
    
    #Increment the run counter
    runs[dNum-1][sNum-1] = runs[dNum-1][sNum-1] + 1
    print("S%02d D%02d Run %d" %(sNum, dNum, runs[dNum-1][sNum-1]))

    if isLIV:
        #Run the LIV
        fname = ('S%02dD%02dR%02d_LIV - %s - %003dC.txt' %(sNum, dNum, runs[dNum-1][sNum-1], sName, temp ) )
        liv = smu.dc_internal_LIV(dc_bias_start, dc_bias_stop, dc_bias_step, current_limit, 
                                   photocurrent_limit, compliance_protection, integ_time, timeout)
        np.savetxt(''.join([fpath,fname]),liv)
        plt.semilogy(liv[:,0],abs(liv[:,1])/A*1000)
        plt.semilogy(liv[:,0],abs(liv[:,2])/A*1000)
    else:
        #Run the IV  
        fname = ('S%02dD%02dR%02d - %s - %003dC.txt' %(sNum, dNum, runs[dNum-1][sNum-1], sName, temp ) )
        iv = smu.dc_internal_IV(dc_bias_start, dc_bias_stop, dc_bias_step, current_limit, 
                                   compliance_protection, integ_time, timeout)
        np.savetxt(''.join([fpath,fname]),iv)
        plt.semilogy(iv[:,0],abs(iv[:,1])/A*1000)
        
    np.savetxt(''.join([fpath_base,'runs.npz']),runs)    
    time.sleep(t_dwell)   #dwell after the measurement

plt.xlim(-1,10)
plt.ylim(1E-11,1E3)   
################  Baomin sweeps

#Run the LIV at low current density twice
#runs[dNum-1][sNum-1] = runs[dNum-1][sNum-1] + 1
#print("S%02d D%02d Run %d" %(sNum, dNum, runs[dNum-1][sNum-1]))
#current_limit = Jmax_low * A / 1000
#fname = ('S%02dD%02dR%02d_LIV - %s - Jmax = %003d mA-cm2.txt' %(sNum, dNum, runs[dNum-1][sNum-1], sName, Jmax_low) )
#liv = smu.dc_internal_LIV(dc_bias_start, dc_bias_stop, dc_bias_step, current_limit, 
#                           photocurrent_limit, compliance_protection, integ_time, timeout)
#np.savetxt(''.join([fpath,fname]),liv)
#plt.semilogy(liv[:,0],abs(liv[:,1])/A*1000)
#plt.semilogy(liv[:,0],abs(liv[:,2])/A*1000)
#time.sleep(t_dwell)   #dwell after the measurement
#
#runs[dNum-1][sNum-1] = runs[dNum-1][sNum-1] + 1
#print("S%02d D%02d Run %d" %(sNum, dNum, runs[dNum-1][sNum-1]))
#current_limit = Jmax_low * A / 1000
#fname = ('S%02dD%02dR%02d_LIV - %s - Jmax = %003d mA-cm2.txt' %(sNum, dNum, runs[dNum-1][sNum-1], sName, Jmax_low) )
#liv = smu.dc_internal_LIV(dc_bias_start, dc_bias_stop, dc_bias_step, current_limit, 
#                           photocurrent_limit, compliance_protection, integ_time, timeout)
#np.savetxt(''.join([fpath,fname]),liv)
#plt.semilogy(liv[:,0],abs(liv[:,1])/A*1000)
#plt.semilogy(liv[:,0],abs(liv[:,2])/A*1000)
#time.sleep(t_dwell)   #dwell after the measurement
#
##run at high current density
#runs[dNum-1][sNum-1] = runs[dNum-1][sNum-1] + 1
#print("S%02d D%02d Run %d" %(sNum, dNum, runs[dNum-1][sNum-1]))
#current_limit = Jmax_high * A / 1000
#fname = ('S%02dD%02dR%02d_LIV - %s - Jmax = %003d mA-cm2.txt' %(sNum, dNum, runs[dNum-1][sNum-1], sName, Jmax_high) )
#liv = smu.dc_internal_LIV(dc_bias_start, dc_bias_stop, dc_bias_step, current_limit, 
#                           photocurrent_limit, compliance_protection, integ_time, timeout)
#np.savetxt(''.join([fpath,fname]),liv)
#plt.semilogy(liv[:,0],abs(liv[:,1])/A*1000)
#plt.semilogy(liv[:,0],abs(liv[:,2])/A*1000)
#time.sleep(t_dwell)   #dwell after the measurement
#
#
##Run at low current density one last time
#runs[dNum-1][sNum-1] = runs[dNum-1][sNum-1] + 1
#print("S%02d D%02d Run %d" %(sNum, dNum, runs[dNum-1][sNum-1]))
#current_limit = Jmax_low * A / 1000
#fname = ('S%02dD%02dR%02d_LIV - %s - Jmax = %003d mA-cm2.txt' %(sNum, dNum, runs[dNum-1][sNum-1], sName, Jmax_low) )
#liv = smu.dc_internal_LIV(dc_bias_start, dc_bias_stop, dc_bias_step, current_limit, 
#                           photocurrent_limit, compliance_protection, integ_time, timeout)
#np.savetxt(''.join([fpath,fname]),liv)
#plt.semilogy(liv[:,0],abs(liv[:,1])/A*1000)
#plt.semilogy(liv[:,0],abs(liv[:,2])/A*1000)
#time.sleep(t_dwell)   #dwell after the measurement
    


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
    