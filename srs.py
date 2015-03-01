import numpy as np
import json


def within_limits(value, limits):
    return (value is not None and limits[0] <= value and limits[1] >= value)


def nearest_index(value, values, rndup):
    if (value < values[0]):
        value = values[0]
    elif(value > values[-1]):
        value = values[-1]
    idx = np.where(value <= values)[0][0]
    if (not rndup and value < values[idx]):
        idx = idx-1
    return idx


class SR570():
    """
    PyVISA wrapper for SRS SR570 Transimpedance amplifier
    """

    inst = None
    _volt_bias_enabled = False
    _curr_bias_enabled = False
    _curr_bias_sign = 1
    _curr_bias_index = 0
    _volt_bias_index = 0
    _sens_index = 27
    _gain_mode_index = 0
    _invert_output = 0
    _front_lights = True
    _lp_freq_index = 15
    _hp_freq_index = 0
    _filter_index = 5
    freqs = np.array([])
    currs = np.array([])
    senss = np.array([])
    config = None

    def __init__(self, inst):
        self.inst = inst
        self.inst.write("*RST")
        cfg_file = open("configs/srs.json")
        cfg = json.load(cfg_file)
        cfg_file.close()
        self.freqs = np.array(cfg['frequencies'])
        self.currs = np.array(cfg['currents'])
        self.senss = np.array(cfg['sensitivities'])
        self.config = cfg

    def nearest_volt_index(self, v):
        if (abs(int(v*1e3)) > 5000):
            return int(np.sign(v)*5000)
        return int(v*1e3)

    def nearest_freq_index(self, freq, rndup):
        return nearest_index(freq, self.freqs, rndup)

    @property
    def filter_type(self):
        return self._filter_index

    @filter_type.setter
    def filter_type(self, value):
        if (within_limits(int(value), [0, 5])):
            self._filter_index = int(value)
            self.inst.write("FLTT%d" % value)

    @property
    def lp_freq(self):
        return self.freqs[self._lp_freq_index]

    @lp_freq.setter
    def lp_freq(self, value):
        self._lp.freq_index = self.nearest_freq_index(value, False)
        if (within_limits(self._filter_index, [2, 4])):
            self.inst.write("LFRQ%d" % self._lp_freq_index)

    @property
    def hp_freq(self):
        return self.freqs[self._hp_freq_index]

    @hp_freq.setter
    def hp_freq(self, value):
        self._hp_freq_index = self.nearest_freq_index(value, True)
        if (within_limits(self._filter_index, [0, 2])):
            self.inst.write("HFRQ%d" % self._hp_freq_index)

    @property
    def bias_volt(self):
        return float(self.volt_bias_index)*1e-3

    @bias_volt.setter
    def bias_volt(self, value):
        self._volt_bias_index = self.nearest_volt_index(value)
        if (self._volt_bias_enabled):
            self.inst.write("BSLV%d" % self._volt_bias_index)

    @property
    def volt_output(self):
        return self._volt_bias_enabled

    @volt_output.setter
    def volt_output(self, value):
        if (value):
            self._volt_bias_enabled = True
            self.inst.write("BSON1;BSLV%d" % self._volt_bias_index)
        else:
            self._volt_bias_enabled = False
            self.inst.write("BSON0")

    def nearest_curr_index(self, curr, rndup=False):
        return nearest_index(abs(curr), self.currs, rndup)

    @property
    def bias_curr(self):
        return self.currs[self._curr_bias_index]

    @bias_curr.setter
    def bias_curr(self, value):
        self._curr_bias_index = self.nearest_curr_index(value)
        if (np.signbit(value)):
            self._curr_bias_sign = 0
        else:
            self._curr_bias_sign = 1
        if (self._curr_bias_enabled):
            self.inst.write("IOSN%d;IOLV%d" % (
                self._curr_bias_sign, self._curr_bias_index))

    @property
    def curr_output(self):
        return self._curr_bias_enabled

    @curr_output.setter
    def curr_output(self, value):
        if (value):
            self._curr_bias_enabled = True
            self.inst.write("IOON1;IOSN%d;IOLV%d" % (
                self._curr_bias_sign, self._curr_bias_index))
        else:
            self._curr_bias_enabled = False
            self.inst.write("IOON0")

    def nearest_sens_index(self, sens, rndup=True):
        return nearest_index(sens, self.senss, rndup)

    @property
    def sensitivity(self):
        return self.senss[self._sens_index]

    @sensitivity.setter
    def sensitivity(self, value):
        self._sens_index = self.nearest_sens_index(value)
        self.inst.write("SENS%d" % self._sens_index)

    @property
    def gain_mode(self):
        return self._gain_mode_index

    @gain_mode.setter
    def gain_mode(self, value):
        if (within_limits(int(value), [0, 2])):
            self._gain_mode_index = int(value)
            self.inst.write("GNMD%d" % self._gain_mode_index)

    @property
    def front_lights(self):
        return self._front_lights

    @front_lights.setter
    def front_lights(self, value):
        if (value):
            self._front_lights = True
            self.inst.write("BLNK0")
        else:
            self._front_lights = False
            self.inst.write("BLNK1")

    @property
    def invert_output(self):
        return self._invert_output

    @invert_output.setter
    def invert_output(self, value):
        if (value):
            self._invert_output = True
            self.inst.write("INVT1")
        else:
            self._invert_output = False
            self.inst.write("INVT0")

    def reset_overload(self):
        self.inst.write("ROLD")
