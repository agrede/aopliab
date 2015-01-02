import visa
from keithley import K2400, K6485


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
    pam = K6485(inst2)
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
