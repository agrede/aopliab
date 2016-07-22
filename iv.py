import visa
from keithley import K2400, K2485
from keysight import Keysight2900
import numpy as np


def ivmeasure(voltages, current_limit, address):
    meas_volt = []  # List of measured voltages from 2401
    meas_curr = []  # List of measured currents from 2401
    # Connect to instruments and initialize
    rm = visa.ResourceManager()
    inst = rm.open_resource(address)
    kthly = K2400(inst)
    # Set current compliance
    kthly.current_limit = current_limit
    # Set initial voltage and turn on output
    kthly.set_voltage(voltages[0])
    kthly.output = True
    # Sweep voltages
    for v in voltages:
        kthly.set_voltage(v)
        meas = kthly.measurement()  # Measure and read
        meas_volt.append(meas[0])
        meas_curr.append(meas[1])
    # Turn off output and close connections
    kthly.output = False
    inst.close()
    return (meas_volt, meas_curr)


def phoivmeasure(voltages, current_limit, photo_current_limit,
                 address1, address2):
    meas_volt = []  # List of measured voltages from 2401
    meas_curr = []  # List of measured currents from 2401
    meas_phot = []  # List of measured currents from 6485
    # Connect to instruments and initialize
    rm = visa.ResourceManager()
    inst1 = rm.open_resource(address1)
    inst2 = rm.open_resource(address2)
    smu = K2400(inst1)
    pam = K2485(inst2)
    # Set compliance levels
    smu.current_limit = current_limit
    pam.auto_range_ulimit = photo_current_limit
    # Zero-check pam
    pam.zero_check()
    # Set Initial voltage and turn on output
    smu.set_voltage(voltages[0])
    smu.output = True
    # Sweep voltages
    for v in voltages:
        smu.set_voltage(v)
        # Trigger measurements, read later (after they are done)
        smu.trigger()
        pam.trigger()
        # Read measurements
        meas1 = smu.read()
        meas2 = pam.read()
        # Save measurments
        meas_volt.append(meas1[0])
        meas_curr.append(meas1[1])
        meas_phot.append(meas2[0])
    # Turn off output and close connections
    smu.output = False
    inst1.close()
    inst2.close()
    return (meas_volt, meas_curr, meas_phot)

def livmeasure_2900(voltages, current_limit, photo_current_limit, int_time,
                 address):
    meas_volt = []  # List of measured voltages from source 1/device
    meas_curr = []  # List of measured currents from source 1/device
    meas_phot = []  # List of measured currents from source 2/photodiode
    
    # Connect to instruments and initialize
    rm = visa.ResourceManager()
    inst = rm.open_resource(address)
    smu = Keysight2900(inst)
    
    # set ch 1 to source voltage, ch 2 to only read current w/ 100 mA compliance
    smu.compliance(1, 0, current_limit)
    smu.source_auto_range(1, 0, 1); smu.source_auto_range(1, 1, 1)
    smu.compliance(2, 0, photo_current_limit)
    smu.source_auto_range(2, 0, 1); smu.source_auto_range(2, 1, 1);
    
    # Set up sense subsystem for integration, measure I/V/L, autosensitivity
    smu.integration_time(1,int_time)
    smu.sense_measurements(1, 1, 1, 0)
    smu.sense_range_auto(1, 0, 1);  smu.sense_range_auto(1, 1, 1);
    smu.sense_range_auto_llim(1, 1, "MIN")
    smu.integration_time(2,int_time)
    smu.sense_measurements(2, 1, 1, 0)
    smu.sense_range_auto(2, 0, 1);  smu.sense_range_auto(2, 1, 1);
    smu.sense_range_auto_llim(2, 1, "MIN")

    # Disable pulsing and any sweeps
    smu.source_pulse(1, 0)
    smu.source_sweep(1, 0, 0)
    smu.source_pulse(2, 0)
    smu.source_sweep(2, 0, 0)

    # Enable protection such that if the smu hits compliance, the source will turn off
    smu.output_over_protection(1, 1)        
    smu.output_over_protection(1, 1)    
    
    # Arm both channels and set trigger delays to 0; one trigger per measurement
    smu.trigger_setup_dc(1, 1)
    smu.trigger_setup_dc(2, 1)

    # Set initial voltage and turn on output
    smu.set_voltage(1,voltages[0])
    smu.output_enable(1,1)
    smu.set_voltage(2,0)
    smu.output_enable(2,1)
    
    # Sweep voltages
    for v in voltages:
        smu.set_voltage(1,v)
        
        # Trigger and read measurements
        meas = smu.measurement_single(1,1)

        # Save measurments
        meas_volt.append(meas[0])
        meas_curr.append(meas[1])
        meas_phot.append(meas[7])
        
        #If the SMU hits compliance, exit the loop
        ######WHY THE FUCK DON'T EITHER OF THESE KILL THE LOOP???###########
#        if meas[7] >= current_limit:
#            break
        
#        tbool = (smu.at_compliance(1,1) or smu.at_compliance(2,1))
#        if tbool:
#            print(tbool)
#            print(smu.at_compliance(1,1))
#            print(smu.at_compliance(2,1))
#            break
#        else:
#            continue

    #Disable the sources, get errors, and close connection
    smu.source_value(1,0,0)
    smu.output_enable(1,0)  
    smu.source_value(2,0,0)
    smu.output_enable(2,0)   
    smu.error_all()     
    inst.close()

    return (meas_volt, meas_curr, meas_phot)
    
def pulsed_livmeasure_2900(voltages,
                            current_limit, photocurrent_limit,
                            int_time, pulse_width, pulse_period, 
                            timeout, address):
    
    # Initialized measurement arrays
    meas_volt = []  # List of measured voltages from source 1/device
    meas_curr = []  # List of measured currents from source 1/device
    meas_phot = []  # List of measured currents from source 2/photodiode
     
    # Connect to instruments and initialize
    rm = visa.ResourceManager()
    inst = rm.open_resource(address)
    smu = Keysight2900(inst)
    
    #set ch 1 to source voltage, ch 2 to only read current w/ 100 mA compliance
    smu.compliance(1, 0, current_limit)
    smu.source_auto_range(1, 0, 0)
    smu.source_range(1,0,10*max(voltages))
    smu.compliance(2, 0, photocurrent_limit)
    smu.source_auto_range(2, 0, 0)
    smu.source_range(2, 0, 2)
    
    # Set up sense subsystem for integration, measure I/V/L, autosensitivity
    smu.integration_time(1,int_time)
    smu.sense_measurements(1, 1, 1, 0)
    smu.sense_range_auto(1, 0, 1)
    smu.sense_range_auto(1, 1, 1)
    smu.sense_range_auto_llim(1, 1, "MIN")
    
    smu.integration_time(2,int_time)
    smu.sense_measurements(2, 1, 1, 0)
    smu.sense_range_auto(2, 0, 1)
    smu.sense_range_auto(2, 1, 1)
    smu.sense_range_auto_llim(2, 1, "MIN")

    # Set up pulsed sweep
    smu.source_pulse(1, 1)          #turn on pulsed measurements
    smu.pulse_delay(1,0)            #set delay to 0
    smu.pulse_width(1,pulse_width)  #set pulse width
    smu.source_sweep(1, 0, 0)       #disable sweeping 

    #Disable overprotection for pulsed measurements to avoid the SMU shutting off when charging cables
    smu.output_over_protection(1, 0)        
    smu.output_over_protection(2, 0)   
    
    # Arm both channels, trigger 1 measurement, and set trigger delays to (pulse_width - 1.1*int_time)
    smu.trigger_setup_pulse(1, 1, pulse_period)
    smu.trigger_setup_pulse(2, 1, pulse_period) 

    #Initiate both channels and measure data
    smu.set_voltage(1,voltages[0])
    smu.output_enable(1,1)
    smu.set_voltage(2,0)
    smu.output_enable(2,1)
    
    # Sweep voltages
    for v in voltages:
        smu.set_voltage(1,v)
        
        # Trigger and read measurements
        meas = smu.measurement_single(1,1)

        # Save measurments
        meas_volt.append(meas[0])
        meas_curr.append(meas[1])
        meas_phot.append(meas[7])
    
    #Disable the sources, get errors, and close connection
    smu.source_value(1,0,0)
    smu.output_enable(1,0)  
    smu.source_value(2,0,0)
    smu.output_enable(2,0)   
    smu.error_all()     
    inst.close()
    
    # Format data for output
    liv = (meas_volt, meas_curr, meas_phot)
    liv = np.asarray(liv).T
    
    return liv   
    
    #LIV where the light channel is passed through a transamp; might be switched at a later point
#to dynamically adjust the transamp gain
def pulsed_livmeasure_2900_transamp(voltages,
                            current_limit, transamp_gain,
                            int_time, pulse_width, pulse_period, 
                            timeout, address):
    
    # Initialized measurement arrays
    meas_volt = []  # List of measured voltages from source 1/device
    meas_curr = []  # List of measured currents from source 1/device
    meas_phot = []  # List of measured currents from source 2/photodiode
     
    # Connect to instruments and initialize
    rm = visa.ResourceManager()
    inst = rm.open_resource(address)
    smu = Keysight2900(inst)
    
    #set ch 1 to source voltage, ch 2 to only read current w/ 100 mA compliance
    smu.compliance(1, 0, current_limit)
    smu.source_auto_range(1, 0, 0)
    smu.source_range(1,0,10*max(voltages))
    smu.compliance(2, 1, 10)                 # Set voltage compliance to 1V to save the transamp
    smu.source_auto_range(2, 0, 0)
    smu.source_range(2, 0, 2)
    
    # Set up sense subsystem for integration, measure I/V/L, autosensitivity
    smu.integration_time(1,int_time)
    smu.sense_measurements(1, 1, 1, 0)
    smu.sense_range_auto(1, 0, 1)
    smu.sense_range_auto(1, 1, 1)
    smu.sense_range_auto_llim(1, 1, "MIN")
    
    smu.integration_time(2,int_time)
    smu.sense_measurements(2, 1, 1, 0)
    smu.sense_range_auto(2, 0, 1)
    smu.sense_range_auto(2, 1, 1)
    smu.sense_range_auto_llim(2, 1, "MIN")

    # Set up pulsed sweep
    smu.source_pulse(1, 1)          #turn on pulsed measurements
    smu.pulse_delay(1,0)            #set delay to 0
    smu.pulse_width(1,pulse_width)  #set pulse width
    smu.source_sweep(1, 0, 0)       #disable sweeping 

    #Disable overprotection for pulsed measurements to avoid the SMU shutting off when charging cables
    smu.output_over_protection(1, 0)        
    smu.output_over_protection(2, 0)   
    
    # Arm both channels, trigger 1 measurement, and set trigger delays to (pulse_width - 1.1*int_time)
    smu.trigger_setup_pulse(1, 1, pulse_period)
    smu.trigger_setup_pulse(2, 1, pulse_period) 

    #Initiate both channels and measure data
    smu.set_voltage(1,voltages[0])
    smu.output_enable(1,1)
    smu.set_voltage(2,0)
    smu.output_enable(2,1)
    
    # Sweep voltages
    for v in voltages:
        smu.set_voltage(1,v)
        
        # Trigger and read measurements
        meas = smu.measurement_single(1,1)

        # Save measurments
        meas_volt.append(meas[0])
        meas_curr.append(meas[1])
        meas_phot.append(meas[6])
    
    #Disable the sources, get errors, and close connection
    smu.source_value(1,0,0)
    smu.output_enable(1,0)  
    smu.source_value(2,0,0)
    smu.output_enable(2,0)   
    smu.error_all()     
    inst.close()
    
    # Format data into [Voltage, Device Current, Photocurrent]
    liv = (meas_volt, meas_curr, meas_phot)
    liv = np.asarray(liv).T
    l = liv[:,2]*transamp_gain
    liv[:,2] = l
    
    return liv
    