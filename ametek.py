import numpy as np
import json
import collections
from aopliab_common import within_limits, nearest_index


class SR7230():
    """
    PyVISA wrapper for 7230 DSP Lock-in Amplifier
    """

    inst = None
    gains = np.array([])
    senss = np.array([])
    tcons = np.array([])
    slopes = np.array([])
    config = None
    separator = ","

    def __init__(self, inst):
        self.inst = inst
        cfg_file = open("configs/ametek.json")
        cfg = json.load(cfg_file)
        cfg_file.close()
        self.config = cfg['SR7230']
        self.gains = np.array(self.config['acgains'])
        self.tcons = np.array(self.config['time_constants'])
        self.senss = np.array(self.config['sensitivities'])
        self.slopes = np.array(self.config['slopes'])

    def query(self, str):
        tmp1 = self.inst.query_ascii_values(str, separator=self.separator)
        self.inst.read_raw()
        return tmp1

    def write(self, str):
        self.inst.write(str)
        self.inst.read_raw()
        self.inst.read_raw()

    def close(self):
        self.inst.close()

    @property
    def imode(self):
        return int(self.query("IMODE")[0])

    @imode.setter
    def imode(self, value):
        if (within_limits(int(value), [0, 2])):
            self.write("IMODE %d" % value)

    @property
    def vmode(self):
        return int(self.query("VMODE")[0])

    @vmode.setter
    def vmode(self, value):
        if (within_limits(int(value), [0, 3])):
            self.write("VMODE %d" % value)

    @property
    def demod2src(self):
        return int(self.query("DMOD2SRC")[0])

    @demod2src.setter
    def demod2src(self, value):
        if (within_limits(int(value), [0, 2])):
            self.write("DMOD2SRC %d" % value)

    @property
    def float_shield(self):
        return (int(self.query("FLOAT")[0]) == 1)

    @float_shield.setter
    def float_shield(self, value):
        if (value):
            self.write("FLOAT 1")
        else:
            self.write("FLOAT 0")

    @property
    def fet_input(self):
        return (int(self.query("FET")[0]) == 1)

    @fet_input.setter
    def fet_input(self, value):
        if (value):
            self.write("FET 1")
        else:
            self.write("FET 0")

    @property
    def dc_couple(self):
        return (int(self.query("DCCOUPLE")[0]) == 1)

    @dc_couple.setter
    def dc_couple(self, value):
        if (value):
            self.write("DCCOUPLE 1")
        else:
            self.write("DCCOUPLE 0")

    @property
    def sensitivity(self):
        return self.query("SEN.")[0]

    @sensitivity.setter
    def sensitivity(self, value):
        imde = self.imode()
        idx = nearest_index(value, self.senss[:, imde+1], True)
        self.write("SENS %d" % self.senss[idx, 0])

    def run_auto_sensitivity(self):
        self.write("AS")

    def run_auto_measure(self):
        self.write("ASM")

    @property
    def ac_gain(self):
        idx = int(self.query("ACGAIN")[0])
        return self.gains[idx]

    @ac_gain.setter
    def ac_gain(self, value):
        if (self.ac_auto_gain):
            self.ac_auto_gain = False
        idx = nearest_index(value, self.gains)
        self.write("ACGAIN %d" % idx)

    @property
    def ac_auto_gain(self):
        return (int(self.query("AUTOMATIC")) == 1)

    @ac_auto_gain.setter
    def ac_auto_gain(self, value):
        if (value):
            self.write("AUTOMATIC 1")
        else:
            self.write("AUTOMATIC 0")

    @property
    def line_filter(self):
        return [int(x) for x in self.query("LF")]

    @line_filter.setter
    def line_filter(self, value):
        cur = self.line_filter
        n1 = cur[0]
        n2 = cur[1]
        if (isinstance(value, (np.ndarray, collections.Sequence))):
            n1 = int(value[0])
            if (len(value) > 1):
                if (within_limits(int(value[1]), [0, 1])):
                    n2 = int(value[1])
        else:
            n1 = int(value)
        if (within_limits(n1, [0, 3])):
            self.write("LF %d %d" % (n1, n2))

    @property
    def ref_mode(self):
        return int(self.query("REFMODE")[0])

    @ref_mode.setter
    def ref_mode(self, value):
        if (within_limits(int(value), [0, 2])):
            self.write("REFMODE %d" % value)

    @property
    def ref_source(self):
        return int(self.query("IE"))

    @ref_source.setter
    def ref_source(self, value):
        limits = [0, 2]
        if (self.ref_mode > 0):
            limits[0] = 1
        if (within_limits(int(value), limits)):
            self.write("IE %d" % value)

    @property
    def ref_int_chan(self):
        if (self.ref_mode > 0):
            return int(self.query("INT")[0])
        else:
            return None

    @ref_int_chan.setter
    def ref_int_chan(self, value):
        if (self.ref_mode > 0 and within_limits(value, [1, 2])):
            self.write("INT %d" % value)

    @property
    def ref_harm(self):
        return int(self.query("REFN")[0])

    @ref_harm.setter
    def ref_harm(self, value):
        if (within_limits(int(value), [1, 127])):
            self.write("REFN %d" % value)

    @property
    def ref_trig_out_mode(self):
        return int(self.query("REFMON")[0])

    @ref_trig_out_mode.setter
    def ref_trig_out_mode(self, value):
        if (within_limits(int(value), [0, 1])):
            self.write("REFMON %d" % value)

    @property
    def ref_phase(self):
        return self.query_ascii_values("REFP.")[0]

    @ref_phase.setter
    def ref_phase(self, value):
        if (within_limits(value, [-360.0, 360.0])):
            self.write("REFP. %f" % value)

    def run_auto_phase(self):
        self.write("AQN")

    @property
    def freq(self):
        return self.query("FRQ.")[0]

    def run_lock(self):
        self.write("LOCK")

    @property
    def vrlock(self):
        return (int(self.query("VRLOCK")[0]) == 1)

    @vrlock.setter
    def vrlock(self, value):
        pass

    @property
    def noise_mode(self):
        return (int(self.query("NOISEMODE")[0]) == 1)

    @noise_mode.setter
    def noise_mode(self, value):
        if (value):
            self.write("NOISEMODE 1")
        else:
            self.write("NOISEMODE 0")

    @property
    def noise_buff_len(self):
        return int(self.query("NNBUF")[0])

    @noise_buff_len.setter
    def noise_buff_len(self, value):
        if (int(value) == 0):
            self.noise_mode = False
        elif (within_limits(int(value), [1, 4])):
            self.write("NNBUF %d" % value)

    @property
    def filter_time_constant(self):
        return self.query("TC.")[0]

    @filter_time_constant.setter
    def filter_time_constant(self, value):
        if (self.noise_mode):
            idx = 5+nearest_index(value, [5e-4, 1e-3, 2e-3, 5e-3, 1e-2], True)
        else:
            idx = nearest_index(value, self.tcons, True)
        self.write("TC %d" % idx)

    @property
    def filter_frequency(self):
        return 1.0/self.filter_time_constant

    @filter_frequency.setter
    def filter_frequency(self, value):
        self.filter_time_constant(1.0/value)

    @property
    def filter_sync(self):
        return (int(self.query("SYNC")[0]) == 1)

    @filter_sync.setter
    def filter_sync(self, value):
        if (value):
            self.write("SYNC 1")
        else:
            self.write("SYNC 0")

    @property
    def filter_slope(self):
        return self.slopes[int(self.query("SLOPE")[0])]

    @filter_slope.setter
    def filter_slope(self, value):
        if (self.noise_mode or self.filter_fast_mode):
            idx = nearest_index(value, self.slopes[0, 1], False)
        else:
            idx = nearest_index(value, self.slopes, False)
        self.write("SLOPE %d" % idx)

    @property
    def filter_fast_mode(self):
        return (int(self.query("FASTMODE")[0]) == 1)

    @filter_fast_mode.setter
    def filter_fast_mode(self, value):
        if (value):
            self.write("FASTMODE 1")
        else:
            self.write("FASTMODE 0")

    @property
    def x(self):
        return self.query("X.")[0]

    @property
    def y(self):
        return self.query("Y.")[0]

    @property
    def xy(self):
        return self.query("XY.")

    @property
    def mag(self):
        return self.query("MAG.")[0]

    @property
    def phase(self):
        return self.query("PHA.")[0]

    @property
    def magphase(self):
        return self.query("MP.")
