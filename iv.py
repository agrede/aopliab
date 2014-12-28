import visa
from keithley import K2400, K2485


def ivmeasure(voltages, current_limit, address):
    meas_volt = []
    meas_curr = []
    rm = visa.ResourceManager()
    inst = rm.open_resource(address)
    kthly = K2400(inst)
    kthly.current_limit = current_limit
    kthly.set_voltage(voltages[0])
    kthly.output = True
    for v in voltages:
        kthly.set_voltage(v)
        meas = kthly.measurement()
        meas_volt.append(meas[0])
        meas_curr.append(meas[1])
    kthly.output = False
    inst.close()
    return (meas_volt, meas_curr)


def phoivmeasure(voltages, current_limit, photo_current_limit,
                 address1, address2):
    meas_volt = []
    meas_curr = []
    meas_phot = []
    rm = visa.ResourceManager()
    inst1 = rm.open_resource(address1)
    inst2 = rm.open_resource(address2)
    smu = K2400(inst1)
    pam = K2485(inst2)
    smu.current_limit = current_limit
    pam.current_limit = photo_current_limit
    smu.set_voltage(voltages[0])
    smu.output = True
    for v in voltages:
        smu.set_voltage(v)
        smu.trigger()
        pam.trigger()
        meas1 = smu.read()
        meas2 = pam.read()
        meas_volt.append(meas1[0])
        meas_curr.append(meas1[1])
        meas_phot.append(meas2[1])
    smu.output = False
    inst1.close()
    inst2.close()
    return (meas_volt, meas_curr, meas_phot)
