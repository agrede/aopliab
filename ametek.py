import json
import numpy as np
import collections
from aopliab_common import within_limits, nearest_index
from time import sleep
from geninst import LockInAmplifier
import numpy.ma as ma
from pyvisa.util import from_ascii_block
from pyvisa.constants import VI_SUCCESS_MAX_CNT


class SR7230(LockInAmplifier):
    """
    PyVISA wrapper for 7230 DSP Lock-in Amplifier
    """

    inst = None
    gains = np.array([])
    config = None
    separator = ","

    def __init__(self, inst):
        self.inst = inst
        cfg_file = open("configs/ametek.json")
        cfg = json.load(cfg_file)
        cfg_file.close()
        self.config = cfg['SR7230']
        self.gains = np.array(self.config['acgains'])
        tmp = np.array(self.config['time_constants'])
        self.tcons = ma.masked_where(tmp < 0., tmp)
        tmp = np.array(self.config['sensitivities'])
        self.senssall = ma.masked_where(tmp < 0., tmp)
        tmp = np.array(self.config['slopes'])
        self.slopes = ma.masked_where(tmp < 0., tmp)
        bwm = np.atleast_2d(self.config['slope_enbw'])
        sw = np.atleast_2d(self.config['slope_wait'])
        tc = np.atleast_2d(self.tcons).T
        self.enbws = bwm/tc
        self.waittimes = sw*tc

    def read_term(self, size):
        rt = self.inst.read_termination
        self.inst.read_termination = ''
        with self.inst.ignore_warning(VI_SUCCESS_MAX_CNT):
            ret = bytes()
            while len(ret) < size:
                chunk, status = self.inst.visalib.read(
                        self.inst.session, size-len(ret))
                ret += chunk
        self.inst.read_termination = rt
        return ret

    def query(self, str):
        tmp1 = self.inst.query_ascii_values(str, separator=self.separator)
        self.read_term(2)
        return tmp1

    def write(self, str):
        self.inst.write(str)
        self.read_term(3)

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
    def senss(self):
        idx = self.imode
        if self.ref_mode == 0:
            return self.senssall[:, [idx]]
        elif self.ref_mode == 1:
            return self.senssall[:, [idx, idx]]
        else:
            return self.senssall[:, [idx, 0]]

    @property
    def sensitivity_index(self):
        if self.ref_mode > 0:
            sns = np.array([0, 0])
            sns[0] = int(self.query("SEN1")[0])-3
            sns[1] = int(self.query("SEN2")[0])-3
            return sns
        else:
            return (np.array([int(x) for x in self.query("SEN")])-3)

    @property
    def sensitivity(self):
        if self.ref_mode > 0:
            sns = np.zeros(2)
            sns[0] = self.query("SEN1.")[0]
            sns[1] = self.query("SEN2.")[0]
            return sns
        else:
            return np.array(self.query("SEN."))

    @sensitivity.setter
    def sensitivity(self, value):
        if type(value) is np.ndarray:
            for k, v in enumerate(value):
                idx = nearest_index(v, self.senss[:, k], True)+3
                if self.ref_mode > 0:
                    self.write("SEN%d %d" % (k+1, idx))
                elif k == 0:
                    self.write("SEN %d" % idx)
        elif type(value) is tuple:
            k, v = value
            idx = nearest_index(v, self.senss[:, k], True)+3
            if self.ref_mode > 0:
                self.write("SEN%d %d" % (k+1, idx))
            elif k == 0:
                self.write("SEN %d" % idx)
        else:
            idx = nearest_index(value, self.senss[:, 0], True)+3
            self.write("SEN %d" % idx)

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
        idx = nearest_index(value, self.gains, True)
        self.write("ACGAIN %d" % idx)

    @property
    def ac_auto_gain(self):
        return (int(self.query("AUTOMATIC")[0]) == 1)

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
        return int(self.query("IE")[0])

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
    def phaseoff(self):
        if self.ref_mode > 0:
            phs = np.zeros(2)
            phs[0] = self.query("REFP1.")[0]
            phs[1] = self.query("REFP2.")[0]
            return phs
        else:
            return np.array(self.query("REFP."))

    @phaseoff.setter
    def phaseoff(self, value):
        if type(value) is np.ndarray:
            for k, v in value:
                if within_limits(v, [-360.0, 360.0]):
                    if self.ref_mode > 0:
                        self.write("REFP%d. %f" % (k+1, v))
                    elif k == 0:
                        self.write("REFP. %f" % v)
        elif type(value) is tuple:
            k, v = value
            if within_limits(v, [-360.0, 360.0]):
                if self.ref_mode > 0:
                    self.write("REFP%d. %f" % (k+1, v))
                elif k == 0:
                    self.write("REFP. %f" % v)
        elif within_limits(value, [-360.0, 360.0]):
            self.write("REFP. %f" % value)

    def system_auto_phase(self, idx):
        if self.ref_mode > 0:
            self.write("AQN%d" % (idx+1))
        else:
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
    def time_constant_index(self):
        if self.ref_mode > 0:
            return (int(self.query("TC1")[0]))
        else:
            return (int(self.query("TC")[0]))

    @property
    def time_constant(self):
        if self.ref_mode > 0:
            return self.query("TC1.")[0]
        else:
            return self.query("TC.")[0]

    @time_constant.setter
    def time_constant(self, value):
        if (self.noise_mode):
            idx = 5+nearest_index(value, np.array([5e-4, 1e-3, 2e-3, 5e-3, 1e-2]), True)
        else:
            idx = nearest_index(value, self.tcons, True)
        if self.ref_mode > 0:
            self.write("TC1 %d" % idx)
            self.write("TC2 %d" % idx)
        else:
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
    def slope_index(self):
        if self.ref_mode > 0:
            return int(self.query("SLOPE1")[0])
        else:
            return int(self.query("SLOPE")[0])

    @property
    def slope(self):
        return self.slopes[self.slope_index]

    @slope.setter
    def slope(self, value):
        if (self.noise_mode or self.filter_fast_mode):
            idx = nearest_index(value, self.slopes[[0, 1]], False)
        else:
            idx = nearest_index(value, self.slopes, False)
        if self.ref_mode > 0:
            self.write("SLOPE1 %d" % idx)
            self.write("SLOPE2 %d" % idx)
        else:
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
    def wait_time(self):
        return self.waittimes.data[self.time_constant_index, self.slope_index]

    @property
    def enbw(self):
        if self.noise_mode:
            return self.query("ENBW.")[0]
        else:
            return self.enbws.data[self.time_constant_index, self.slope_index]

    @property
    def cmeas(self):
        cbd = 0b111100000011
        idxs = np.array([[0, 1]])
        if self.ref_mode > 0:
            cbd = 0b1100000111100000011
            idxs = np.array([[0, 1], [6, 7]])
        self.write("CBD %d" % cbd)
        rtn = np.array(self.query("?"))
        for k, ks in enumerate(idxs):
            if self.preamps[k] is not None:
                rtn[ks] = rtn[ks]*self.preamps[k].sensitivity
        return rtn

    @property
    def cmags(self):
        if self.ref_mode > 0:
            mags = np.zeros(2)
            mags[0] = self.query("MAG1.")[0]
            mags[1] = self.query("MAG2.")[0]
        else:
            mags = np.array(self.query("MAG."))
        for k, m in enumerate(mags):
            if self.preamps[k] is not None:
                mags[k] = mags[k]*self.preamps[k].sensitivity
        return mags

    def adc(self, index, periods=2, min_number=500, fast=True, peak=True):
        index = int(index)
        if not within_limits(index, [0, 3]):
            return np.nan
        ctc = self.time_constant
        cfm = self.filter_fast_mode
        cnm = self.noise_mode
        if fast and index < 2:
            self.filter_fast_mode = True
            self.write("TADC 3")
            self.write("CMODE 1")
            self.write("STR 2")
            points = int(np.ceil(periods*5e5/self.freq))
        else:
            self.noise_mode = False
            self.filter_fast_mode = False
            self.write("TADC 0")
            self.write("CMODE 0")
            self.write("STR 1000")
            points = int(np.ceil(periods*1e3/self.freq))
        if points < min_number:
            points = min_number
        if points > 100000:
            points = 100000
        self.write("LEN %d" % points)
        self.write("CBD %d" % (2**(8+index)))
        self.write("NC")
        self.write("TD")
        wait = True
        m = [0, 0, 0, 0]
        while wait:
            m = [int(x) for x in self.query("M")]
            wait = m[1] < 1 or m[0] > 0
        if m[1] < 1:
            return np.nan
        values = np.zeros(points)
        if fast and index < 2:
            self.inst.write("DC %d" % (index+3))
            tmp = self.inst.read()
            self.inst.read_raw()
            values = 0.001*np.array([from_ascii_block(tmp[:-1], separator='\n')])
        else:
            self.inst.write("DC. %d" % (8+index))
            tmp = self.inst.read()
            self.inst.read_raw()
            values = np.array([from_ascii_block(tmp[:-1], separator='\n')])
        self.filter_fast_mode = cfm
        self.noise_mode = cnm
        self.time_constant = ctc
        if peak:
            return np.abs(values).max()
        else:
            return values

    def noise_measure(self, tc_noise, tc_mag, slope_noise,
                      slope_mag):
        cs = self.slope
        ctc = self.time_constant
        self.noise_mode = True
        self.noise_buff_len = 4
        self.time_constant = tc_noise
        self.slope = slope_noise
        if self.ref_mode > 0:
            y2n = np.zeros(int(10./self.wait_time))
            rtn = np.zeros((2, 2))
            for k in range(y2n.size):
                sleep(self.wait_time)
                y2n[k] = self.query("Y2.")[0]
            rtn[0, 1] = self.query("NHZ.")[0]
            rtn[1, 1] = y2n.std()/np.sqrt(self.enbw)
        else:
            rtn = np.zeros((1, 2))
            sleep(10.)
            rtn[0, 1] = self.query("NHZ.")[0]
        self.noise_mode = False
        self.filter_fast_mode = False
        self.slope = slope_mag
        self.time_constant = tc_mag
        sleep(self.wait_time)
        rtn[:, 0] = self.cmags
        for k in range(rtn.shape[0]):
            if self.preamps[k] is not None:
                rtn[k, 1] = rtn[k, 1]*self.preamps[k].sensitivity
        self.slope = cs
        self.time_constant = ctc
        return rtn

    def ioread(self, bit):
        if within_limits(bit, [0, 7]):
            tmp = int(self.query("READBYTE")[0])
            return ((tmp&(1<<bit)) != 0)
        else:
            return None

    def iowrite(self, bit, value):
        if within_limits(bit, [0, 7]):
            if not self.iodirin(bit):
                cur = int(self.query("READBYTE")[0])
                n = bool(value)
                rtn = ((~(1<<bit)&cur)|((1<<bit)*n))
                self.write("BYTE %d" % rtn)

    def iodirin(self, bit):
        if within_limits(bit, [0, 7]):
            tmp = int(self.query("PORTDIR")[0])
            return ((tmp&(1<<bit)) != 0)
        else:
            return None

    @property
    def osc_freq(self):
        return (self.query("OF.")[0])

    @osc_freq.setter
    def osc_freq(self, value):
        if within_limits(value, [0, 2.5e5]):
            self.write("OF. %0.5e" % value)

    @property
    def osc_amp(self):
        return (self.query("OA.")[0])

    @osc_amp.setter
    def osc_amp(self, value):
        if within_limits(value, [0., 5.]):
            self.write("OA. %0.6f" % value)
