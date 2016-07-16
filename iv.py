import visa
from keithley import K2400, K2485
from keysight import Keysight2900


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
    meas_volt = []  # List of measured voltages from 2401
    meas_curr = []  # List of measured currents from 2401
    meas_phot = []  # List of measured currents from 6485
    
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
    smu.integration_time(2,int_time)
    smu.sense_measurements(2, 1, 1, 0)
    smu.sense_range_auto(2, 0, 1);  smu.sense_range_auto(2, 1, 1);

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
        smu.set_voltage(2,0)
        
        # Trigger and read measurements
        meas = smu.measurement_single(1,1)

        # Save measurments
        meas_volt.append(meas[0])
        meas_curr.append(meas[1])
        meas_phot.append(meas[7])
        
        # If the SMU hits compliance, exit the loop
        v=max(voltages) if (smu.at_compliance(1,1) or smu.at_compliance(2,1)) else v

    #Disable the sources, get errors, and close connection
    smu.source_value(1,0,0)
    smu.output_enable(1,0)  
    smu.source_value(2,0,0)
    smu.output_enable(2,0)   
    smu.error_all()     
    inst.close()

    return (meas_volt, meas_curr, meas_phot)