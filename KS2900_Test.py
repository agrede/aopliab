import numpy as np
import aopliab_common as ac
import visa
from keysight import Keysight2900


#Initialize resource manager and open the SMU
rm = visa.ResourceManager()
addr = "USB0::0x0957::0x8E18::MY51141103::0::INSTR"
instr = rm.open_resource(addr)
smu = Keysight2900(instr)


#print(instr.query("*IDN?"))

#Test commands
print('\n Start Testing \n')
#smu.reset()
#smu.beep(0)
#smu.disp(1)
#smu.identity()
#smu.error_single()
smu.error_all()

smu.integration_time(2,1E5)


print('\n Stop Testing \n')
#Untested...
#smu.get_data(1,0)
#smu.measure_single_data(0,1)