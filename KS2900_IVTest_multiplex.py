## 
import os
os.chdir('C:/Dropbox/Jared/Python/aopliab')
import numpy as np
import matplotlib.pylab as plt
import visa
from keysight import Keysight2900
import time
import bluetooth as bt
import aopliab_common as aop

def set_mpx(bt_sock, device_num):
    #Generate device index/location 
#    devices = np.reshape(np.arange(1,21,1),[5,4])
#    devices[0,:] = [1,  11, 18, 10]
#    devices[1,:] = [2,  12, 17, 9]
#    devices[2,:] = [3,  0,  0,  8]
#    devices[3,:] = [4,  13, 16, 7]
#    devices[4,:] = [5,  14, 15, 6]

    devices = np.reshape(np.arange(1,21,1),[5,4])    
    devices[0,:] = [10, 18, 11, 1]
    devices[1,:] = [9,  17, 12, 2]
    devices[2,:] = [8,  0,  0,  3]
    devices[3,:] = [7,  16, 13, 4]
    devices[4,:] = [6,  15, 14, 5]

    #1-0 = D
    #1-1 = C
    #1-2 = A
    #1-3 = B
    
    #0-0 = 1 & 10
    #0-1 = 2 & 9
    #0-2 = 3 & 8
    #0-3 = 4 & 7
    #0-4 = 5 & 6
    
    shld = 0
    for k in np.arange(0,5,1):
        if device_num in devices[k,:]:
#            print('anode - set %d %d' %(shld, k))
            bt_sock.send('set %d %d' %(shld, k))
            
    #time to let the first board switch; the second command gets skipped otherwise
    time.sleep(2) 
            
    #set cathode
    shld = 1
    for k in np.arange(0,4,1):
        if device_num in devices[:,k]:
#            print('cathode - set %d %d' %(shld, k))
            bt_sock.send('set %d %d' %(shld, k))


# Get the device size from Gen 4 patterns
def size_gen4(deviceNum):
    small = np.arange(11,19,1)  #small devices in center
    if deviceNum in small:
        l = 1
        w = 1
        area = l*w/100 #area in cm^2
    else:
        l = 2
        w = 5
        area = l*w/100 #area in cm^2
    return area
     
###############################################################################
###############################################################################
###############################################################################
##############################   Begin program   ##############################
###############################################################################
###############################################################################
###############################################################################

       
#Initialize bluetooth shield
#Bluetooth address of BT shield - 00:6A:8E:16:CA:20
#write a method for this
#bt_addr = '00:6A:8E:16:CA:20'
#port = 1
#sock=bt.BluetoothSocket( bt.RFCOMM )
#sock.connect((bt_addr, port))
sock.send("rst")
sock.recv(1064)
time.sleep(2)

#Initialize resource manager and open the SMU
addr = "USB0::0x0957::0x8E18::MY51141103::0::INSTR"
rm = visa.ResourceManager()
instr = rm.open_resource(addr)
smu = Keysight2900(instr)

dcreps = np.arange(0,3,1)
integ_time = 1/60
photocurrent_limit = 0.5
compliance_protection = True
timeout = 3000
t_dwell = 0 #dell time between consecutive measurements [s]


#initialize runs with: runs = np.zeros(shape=(10,3))
#load with np.genfromtxt('fpath/fname')
try:
  runs
except NameError:
  runs = np.zeros(shape=(18,7))

isLIV = False

sNum = 1
temp = 20
dc_bias_start = -3;   dc_bias_stop = 5;   dc_bias_step = .05; 
Jmax = 200 #mA/cm^2


##################  File path, sample name, working devices, etc. #####################

#Get sample composition / file paths
if(sNum ==  1):
    sName = 'NPD'
elif(sNum == 2):
    sName = '25% Tef AF 1600'
elif(sNum == 3):
    sName = '25% Tef AF 2400'
elif(sNum == 4):
    sName = '50% Tef AF 1600'
elif(sNum == 5):
    sName = '50% Tef AF 2400'
elif(sNum == 6):
    sName = '80% Tef AF 1600'
elif(sNum == 7):
    sName = '80% Tef AF 2400'
else:
    sName = 'Test'

#Base directory for a sample   
root_path = 'C:/Dropbox/Jared/Data/2017/2017_05-12 - NPD-TAF in glovebox/'
fpath_base = ''.join([root_path,'S%02d - %s/' %(sNum, sName)])

#Import number of working runs
try:
  working_devices = np.genfromtxt(''.join([fpath_base,'working devices.txt']))
except OSError:
  working_devices = np.arange(1,19,1)    

t_elapsed = 0;
t_start = time.time()


#Run IVs on all working devices
for dNum in working_devices:
    set_mpx(sock,dNum) #set the device
    A = size_gen4(dNum) #Device area

    #Generate the file path
    fpath = ''.join([fpath_base, ('S%02dD%02d - %s/' %(sNum, dNum, sName))] )
    #Create the file path 
    if not os.path.exists(fpath):
      os.makedirs(fpath)
           
    #Set up the SMU
    current_limit = Jmax * A / 1000

    
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
            
        #Save runs    
        np.savetxt(''.join([root_path,'runs.npz']),runs)    
        time.sleep(t_dwell)   #dwell after the measurement

t_elapsed = time.time()-t_start
print('Elapsed time = %d min' %(t_elapsed/60))
plt.xlim(-10,10)
plt.ylim(1E-6,1E3)   
    
print('remember to update and export working devices')
np.savetxt(''.join([fpath_base,'working devices.txt']),working_devices)
#sock.close()