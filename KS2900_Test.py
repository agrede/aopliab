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
#Working Commands...
#smu.reset()
#smu.beep(0)
#smu.disp(0)
#smu.identity()
#smu.error_single()
#smu.integration_time(2,1E-3) 
#print(smu.at_compliance(1, 0))
#smu.sense_range_mode(1,0,"RES")
#smu.sense_range_threshold(1, 0, 90):
#smu.sense_range_ulim(1,0,2)
#smu.sense_range_auto(1,1,1)
#smu.sense_range_auto_llim(1,1,"MAX")
#print(smu.sense_measurements(1,1,1,0))
#(smu.compliance(1,0,1E-2)
#smu.output_filter(1,0,20E-6)
#smu.output_high_capacitance(1,1)
#smu.output_ground(1,1)
#smu.output_enable(1,1)
#smu.output_over_protection(1,0)
#smu.output_off_mode(1,0)

#sort of working...   


#maybe working?


smu.error_all()
smu.output_auto_on(1,0)
smu.error_all()




print('\n Stop Testing \n')

#Not working...
#smu.integration_time_NPLC(2,1)  #undefined header?
#(smu.sense_range_auto_ulim(1,0,1))  #-113 undefined header error

#Untested...
#smu.get_data(1,0)
#smu.measure_single_data(0,1)