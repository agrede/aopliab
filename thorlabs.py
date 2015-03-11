from aopliab_common import within_limits
import json
import numpy as np


class MC2000():
    _harmonic_limits = [1, 15]
    _display_limits = [1, 10]
    _phase_limits [0, 360]

    def __init__(self, inst):
        self.inst = inst
        cfg_file = open('configs/thorlabs.json')
        cfg = json.load(cfg_file)
        cfg_file.close()
        self.config = cfg['MC2000']
        self.blades = np.array(cfg['MC2000']['blades'])

    @property
    def blade(self):
        idx = int(self.inst.query_ascii_values('blade?')[0])
        return (idx, self.blades[idx, 0])

    @blade.setter
    def blade(self, value):
        if (type(value) is int):
            if (within_limits(value, [0, (self.blades.size-1)])):
                self.inst.write('blade=%d' % value)
        elif (value in self.blades[:, 0]):
            v = np.where(value == self.blades[:, 0])[0][0]
            self.inst.write('blade%d' % v)

    @property
    def freq_limits(self):
        return self.blades[self.blade, [1, 2]]

    @property
    def freq(self):
        if (self.ext_ref):
            return self.inst.query_ascii_values('input?')[0][0]
        else:
            return self.inst.query_ascii_values('freq?')[0][0]

    @freq.setter
    def freq(self, value):
        if (within_limits(value, self.freq_limits)):
            self.inst.write('freq=%f' % value)

    @property
    def phase(self):
        return self.inst.query_ascii_values('phase?')[0][0]

    @phase.setter
    def phase(self, value):
        if (within_limits(value, self._phase_limits)):
            self.inst.write('phase=%d' % value)

    @property
    def enable(self):
        return (self.inst.query_ascii_values('enable?')[0][0] == 1)

    @enable.setter
    def enable(self, value):
        if (value):
            self.inst.write('enable=1')
        else:
            self.inst.write('enable=0')

    @property
    def harmonic_mult(self):
        return int(self.inst.query_ascii_values('nharmonic?')[0][0])

    @harmonic_mult.setter
    def harmonic_mult(self, value):
        if (within_limits(value, self._harmonic_limits)):
            self.inst.write('nharmonic=%d' % value)

    @property
    def harmonic_div(self):
        return int(self.inst.query_ascii_values('dharmonic?')[0][0])

    @harmonic_div.setter
    def harmonic_div(self, value):
        if (within_limits(value, self._harmonic_limits)):
            self.inst.write('dharmonic=%d' % value)

    @property
    def ext_ref(self):
        return (self.inst.query_ascii_values('ref?')[0][0] == 1)

    @ext_ref.setter
    def ext_ref(self, value):
        if (value):
            self.inst.write('ref=1')
        else:
            self.inst.write('ref=0')

    @property
    def ref_out_actual(self):
        return (self.inst.query_ascii_values('output?')[0][0] == 1)

    @ref_out_actual.setter
    def ref_out_actual(self, value):
        if (value):
            self.inst.write('output=1')
        else:
            self.inst.write('output=0')

    @property
    def display(self):
        return int(self.inst.query_ascii_values('intensity?')[0][0])

    @display.setter
    def display(self, value):
        if (within_limits(value, self._display_limits)):
            self.inst.write('intensity=%d' % value)
