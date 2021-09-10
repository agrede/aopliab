from ctypes import *
import numpy as np
from aopliab.aopliab_common import within_limits


class SpecPro():
    """
    Uses ARC_SpectraPro.dll to interface with mono
    """
    _mono = c_int(32)
    wavelength_limits = [0, 20000]

    def __init__(self, com_port, dll_path="C:\\Program Files (x86)\\Princeton Instruments\\MonoControl\\ARC_SpectraPro.dll"):
        self._dll = windll.LoadLibrary(dll_path)
        self._dll.ARC_Open_Mono_Port(com_port, byref(self._mono))
        self.get_limits()

    def close(self):
        self._dll.ARC_Close_Mono(self._mono)

    @property
    def wavelength(self):
        tmp = c_double()
        self._dll.ARC_get_Mono_Wavelength_nm(self._mono, byref(tmp))
        return tmp.value

    @wavelength.setter
    def wavelength(self, value):
        if (within_limits(value, self.wavelength_limits)):
            self._dll.ARC_set_Mono_Wavelength_nm(self._mono, c_double(value))

    def get_limits(self):
        tmp = c_double()
        self._dll.ARC_get_Mono_Wavelength_Cutoff_nm(self._mono, byref(tmp))
        self.wavelength_limits[1] = tmp.value
        self._dll.ARC_get_Mono_Wavelength_Min_nm(self._mono, byref(tmp))
        self.wavelength_limits[0] = tmp.value

    @property
    def grating(self):
        tmp = c_int(32)
        self._dll.ARC_get_Mono_Grating(self._mono, byref(tmp))
        return tmp.value

    @grating.setter
    def grating(self, value):
        value = int(value)
        if self.grating_installed(value):
            self._dll.ARC_set_Mono_Grating(self._mono, c_int(value))

    @property
    def grating_range(self):
        tmp = c_int(32)
        self._dll.ARC_get_Mono_Grating_Max(self._mono, byref(tmp))
        return np.array([1, tmp.value])

    def grating_installed(self, value):
        value = int(value)
        if within_limits(value, self.grating_range):
            if self._dll.ARC_get_Mono_Grating_Installed(self._mono, c_int(value)) == -1:
                return True
        return False
