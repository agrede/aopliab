import numpy as np
from time import time
import re
from aopliab.aopliab_common import within_limits


class SP2150():
    """
    Wrapper for SP-2150 monochrometer
    """
    
    _wavelength_max_limit = 20000.0
    _dispersion_factor = 5.0e-9*1200e3*1e3
    _grating_limits = [1, 8]
    gratings = [None]*8
    wavelength_multiple = 1e-9
    slit_multiple = 1e-6
    _max_factor = 1200e3*1400e-9
    _speed_factor = 1e-9/60.0
    _scan_speed_limits = np.array([0.01, 2000])*600e3*1e-9/60.0
    
    def __init__(self, inst):
        """
        Parameters
        ----------
        inst : pyvisa.resources.Resource
            pyvisa resource object for the instrument

        Returns
        -------
        None
        """
        self.inst = inst
        self.inst.write("ECHO-OFF")
        self.init_gratings()
        
    def query_value(self, command):
        """
        query values from instrument

        Parameters
        ----------
        command : str
            command string to query

        Returns
        -------
        dta : [str]
            list of returned values.
        """
        while self.inst.bytes_in_buffer > 1:
            self.inst.read()
        self.inst.write(command)
        dta = []
        while True:
            val = self.inst.read()
            if len(val) > 1:
                if val[-2:] == 'ok' or val[-2:] == '? ':
                    dta.append(val[:-2])
                    break
                dta.append(val)
        return dta
    
    def set_value(self, command):
        """
        write value to instrument

        Parameters
        ----------
        command : str
            command to set value.

        Returns
        -------
        bool
            if setting was somewhat successful.

        """
        while self.inst.bytes_in_buffer > 1:
            self.inst.read()
        return self.inst.query(command) == ' ok'
    
    def move_value(self, command, timeout=20.0):
        """
        same as set value but for actions that will move motors

        Parameters
        ----------
        command : str
            command to set value.
        timeout : float, optional
            additional timeout to wait for response. The default is 20.0.

        Returns
        -------
        bool
            if setting was somewhat successful.

        """
        while self.inst.bytes_in_buffer > 1:
            self.inst.read()
        self.inst.write(command)
        t0 = time()
        while time()-timeout < t0:
            if self.inst.bytes_in_buffer > 2:
                val = self.inst.read()
                return len(val) > 1 and val[-2:] == 'ok'
        return False
    
    def init_gratings(self):
        """
        Initialize gratings parameter

        Returns
        -------
        None.

        """
        rgxGrating = re.compile("\A.(\d)\s+(\d+\.?\d*) g/mm\s+BLZ=\s+(\d+\.?\d*)(\w+).*")
        for m in map(rgxGrating.match, self.query_value("?GRATINGS")):
            if m is not None:
                self.gratings[int(m.group(1))-1] = {
                    'pitch': float(m.group(2))*1e3,
                    'blaze': float(m.group(3))*(
                        1e-9 if m.group(4) == 'NM' else 1e-6)}

    @property
    def grating(self):
        """
        grating number or None if invalid.
        """
        if m := re.search("\d+", self.query_value("?GRATING")[0]):
            return int(m.group(0))
        else:
            return None

    @grating.setter
    def grating(self, value):
        value = int(value)
        if (within_limits(value, self._grating_limits) and 
            self.gratings[value-1] is not None):
            self.move_value("{:d} GRATING".format(int(value)))
           
    @property
    def pitch(self):
        """
        pitch of current grating in 1/m, cannot be set
        """
        grt = self.grating
        if grt is not None and self.gratings[grt-1] is not None:
            return self.gratings[grt-1]['pitch']
        else:
            return np.nan
    
    @property
    def wavelength_limits(self):
        """
        the wavelength limits in nm by default, cannot be set directly

        """
        return [0.0, np.nanmin([
            self._max_factor/self.pitch, 20e-6])/self.wavelength_multiple]
        

    @property
    def wavelength(self):
        """
        the current wavelength in nm by default
        """
        if m := re.search("\d+\.?\d*", self.query_value("?NM")[0]):
            return float(m.group(0))*1e-9/self.wavelength_multiple
        else:
            return np.nan
    
    @wavelength.setter
    def wavelength(self, value):
        if within_limits(value, self.wavelength_limits):
            self.move_value("{:0.1f} GOTO".format(
                value*self.wavelength_multiple*1e9))
           
    @property
    def scan_speed_limits(self):
        """
        the scan speed limits for the current grating in nm/s by default, 
        cannot be set directly

        """
        return self._scan_speed_limits/(
            self.pitch*self.wavelength_multiple)

    @property
    def scan_speed(self):
        """
        the scan speed in nm/s by default
        """
        if m := re.search("\d+\.?\d*", self.query_value("?NM/MIN")[0]):
            return float(m.group(0))*self._speed_factor/(
                self.wavelength_multiple)
        else:
            return np.nan
    
    @scan_speed.setter
    def scan_speed(self, value):
        if within_limits(value, self.scan_speed_limits):
            self.set_value("{:0.3f} NM/MIN".format(
                value*self.wavelength_multiple/self._speed_factor))
    
    def scan_to_wavelength(self, final_wavelength):
        """
        scan grating to wavelength at scan_speed

        Parameters
        ----------
        final_wavelength : float
            wavelength to end at in nm by default.

        Returns
        -------
        None.

        """
        if within_limits(final_wavelength, self.wavelength_limits):
            tscan = np.abs(self.wavelength-final_wavelength)/self.scan_speed
            if np.isfinite(tscan):
                self.move_value("{:0.1f} NM".format(
                    final_wavelength*self.wavelength_multiple*1e9),
                    20.0+tscan)
    
    @property
    def dispersion(self):
        """
        grating dispersion in nm/m with current grating
        """
        return self._dispersion_factor/(self.wavelength_multiple*self.pitch)

    def bandwidth(self, slit):
        """
        calculates the bandwidth for a givin slit width

        Parameters
        ----------
        slit : flot
            slit width in um by default.

        Returns
        -------
        float
            bandwidth in nm by default.
        """
        return (slit*self.slit_multiple*self.dispersion)