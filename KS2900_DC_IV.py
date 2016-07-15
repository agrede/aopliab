import numpy as np
import aopliab_common as ac
import visa
from keysight import Keysight2900


#Initialize resource manager and open the SMU
rm = visa.ResourceManager()
addr = "USB0::0x0957::0x8E18::MY51141103::0::INSTR"
instr = rm.open_resource(addr)
smu = Keysight2900(instr)



#Working Commands...

#DC_voltage_Sweep(Vmin,Vmax,Vstep)


smu.error_all()
smu.source_output_mode(ch1,"VOLT")
smu.source_output_shape(ch1,"DC")
smu.source_mode(ch1,V0_I1,"SWE")
smu.sweep_mode(ch1,"SING")
smu.set_sweep_direction(ch1, 0)
smu.source_start_and_stop_values(ch1,V0_I1,0,stop)
#smu.source_sweep_step(ch1,V0_I1,step)
smu.source_number_sweep_steps(ch1,V0_I1,steps)

smu.compliance(ch1,V0_I1,comp)
smu.output_auto_on(ch1,1)
smu.output_enable(ch1,1);
smu.sense_measurements(ch1,meas volt,meas curr,meas res)

#smu.trigger_time_interval(ch1,time_interval)
#smu.trigger_count(ch1,trigger_count)
#smu.arm(ch)
#smu.initiate_channel(ch1,ch2)

bitch = smu.measurement_all(ch1,ch2)
smu.error_all()




print('\n Stop Testing \n')

#maybe working?

#Not working...
#smu.integration_time_NPLC(2,1)  #undefined header?
#(smu.sense_range_auto_ulim(1,0,1))  #-113 undefined header error

#Untested...
#smu.get_data(1,0)
#smu.measure_single_data(0,1)