from ctypes import *
import numpy as np


class SpecPro():
    """
    Uses ARC_SpectraPro.dll to interface with mono
    """

    def __init__(self, com_port, dll_path="ARC_SpectraPro.dll"):
        self._dll = wdll(dll_path)
        self._dll.ARC_Open_Mono_Port(com_port, byref(self._mono))

    def close(self):
        self._dll.ARC_Close_Mono(self._mono)

    @property
    def wavelength(self):
        self._dll.ARC_get_Mono_Wavelength_nm(self._mono, byref(tmp))
        return tmp.value

    @wavelength.setter
    def wavelength(self, value):
        self._dll.ARC_set_Mono_Wavelength_nm(self, c_double(value))
