import numpy as np
import matplotlib.pyplot as plt
import json
import pyvisa
import re
import serial as srl
import os
from datetime import datetime, timezone


PKGPTH = os.path.dirname(__file__)+"/"


def within_limits(value, limits):
    """
    checks if value contained by limits

    Parameters
    ----------
    value : comparable type
    values : list of value type
        min, max value
    Returns
    -------
    bool
    """
    return (value is not None and limits[0] <= value and limits[1] >= value)


def getInstr(rm, name, local_config=PKGPTH+'local.json'):
    """
    Get pyvisa object for instrument as specified in configuration file

    Parameters
    ----------
    rm : pyvisa.highlevel.ResourceManager
        pyvisa resource manager for session
    name : str
        Instrument name stored in `local_config`
    local_config : str
        Path to json configuration file

    Returns
    -------
    pyvisa.resources.Resource
       pyvisa resource object for the instrument
    """
    cfg_file = open(local_config)
    cfg = json.load(cfg_file)
    cfg_file.close()
    if ('non_visa' in cfg[name].keys() and cfg[name]['non_visa']):
        if (cfg[name]['manufacturer'] == 'ARC' and
                cfg[name]['model'] == 'SpecPro'):
            return (cfg[name]['com'], cfg[name]['dll_path'])
    if ('conn_params' in cfg[name]):
        conn_params = parseConnParams(cfg[name]['conn_params'])
    else:
        conn_params = {}
    return rm.open_resource(cfg[name]['addr'], **conn_params)


def getSer(name, local_config=PKGPTH+'local.json'):
    """Load a serial object"""
    cfg_file = open(local_config)
    cfg = json.load(cfg_file)
    cfg_file.close()
    return srl.Serial(cfg[name]['addr'], cfg[name]['conn_params']['baud_rate'],
                      timeout=cfg[name]['conn_params']['timeout'])


def parseConnParams(params):
    if ('stop_bits' in params):
        if (params['stop_bits'] == 1):
            params['stop_bits'] = pyvisa.constants.StopBits.one
        elif (params['stop_bits'] == 1.5):
            params['stop_bits'] = pyvisa.constants.StopBits.one_and_a_half
        elif (params['stop_bits'] == 2):
            params['stop_bits'] = pyvisa.constants.StopBits.two
        else:
            del(params['stop_bits'])
    if ('read_termination' in params):
        params['read_termination'] = "".join(
            [parseTermString(x) for x in params['read_termination']])
    if ('write_termination' in params):
        params['write_termination'] = "".join(
            [parseTermString(x) for x in params['write_termination']])
    return params


def parseTermString(strng):
    """
    look up table for terminal strings in local configuration file

    Example
    -------
    >>> parseTermString("CR")
    '\r'
    """
    strs = {'NULL': '\0', 'CR': '\r', 'LF': '\n'}
    m = re.match('<(\w+)>', strng)
    if (m and m.group(1) in strs):
        return strs[m.group(1)]
    else:
        return strng


def nearest_index(value, values, rndup):
    """
    get the closest index of value in values

    Parameters
    ----------
    value : numeric
        value to search
    values : array_like
        array of values to compare
    rndup : bool
        round up to nearest index
    Returns
    -------
    value
    """
    k = np.where(np.isfinite(values))[0]
    tvalues = values[k]
    if (value < tvalues[0]):
        value = tvalues[0]
    elif(value > tvalues[-1]):
        value = tvalues[-1]
    try:
        idx = np.where(value <= tvalues)[0][0]
    except IndexError:
        #print("nearest_index({value}, {values})".format(value=value, values=values))
        raise IndexError
    if (not rndup and value < tvalues[idx]):
        idx = idx-1
    return k[idx]


class DynamicPlot():
    """
    Plot/subplots which can points can be dynamically added
    """
    ptype = "plot"
    dlstyle = "o-"

    def __init__(self, ptype="plot", lstyle="o-", fig=None, label=None,
                 title="title", xAxis="x Axis", yAxis="y Axis",
                 figsize=(6.4, 4.8)):
        """
        Parameters
        ----------
        ptype : {'plot', 'loglog', 'semilogy', 'semilogx', 'errorbar'}, optional
            plot type to use
        lstyle : str, optional
            default line style to use
        fig : int, optional
            subplot number
        title : str, optional
        xAxis : str, optional
            x axis label
        yAxis : str, optional
            y axis label
        figsize : (float, float), optional
            figure size in inches (100 dpi default)
        """
        self.ptype = ptype
        self.dlstyle = lstyle
        self.lines = []
        # Set up plot
        self.figure, self.ax = plt.subplots(figsize=figsize, num=fig)
        self.ax.set_title(title)
        self.xAxis = plt.xlabel(xAxis)
        self.yAxis = plt.ylabel(yAxis)
        self.addnew(label=label)
        if label:
            self.ax.legend()
        # Autoscale on unknown axis and known lims on the other
        self.ax.set_autoscale_on(True)

    def addnew(self, ptype=None, lstyle=None, label=None):
        """
        add new line

        Parameters
        ----------
        ptype : str, optional
        lstyle : str, optional
        label : str, optional
        """
        if ptype is None:
            ptype = self.ptype
        if lstyle is None:
            lstyle = self.dlstyle
        if (ptype == "loglog"):
            tline, = self.ax.loglog([], [], lstyle)
        elif (ptype == "semilogy"):
            tline, = self.ax.semilogy([], [], lstyle)
        elif (ptype == "semilogx"):
            tline, = self.ax.semilogx([], [], lstyle)
        elif (ptype == "errorbar"):
            if lstyle is None:
                self.errorlstyle = self.dlstyle
            else:
                self.errorlstyle = lstyle
        else:
            tline, = self.ax.plot([], [], lstyle)
        if label:
            tline.set_label(label)
            self.ax.legend()
        self.lines.append(tline)

    def update(self, newx, newy, error_up=None, error_down=None):
        """
        Update plot with new values

        Parameters
        ----------
        newx : float
            x-value to add
        newy : float
            y-value to added
        error_up : float, optional
            positive valued upper error bar
        error_down : float, optional
            positive valued lower error bar
        """
        k = len(self.lines) - 1
        if (error_up and len(self.lines) == 0): # trying to determine when we have new errorbar first case
            if not error_down:
                error_down = error_up
            tline, error_l, error_bar = self.ax.errorbar(
                [newx], [newy], [[error_up], [error_down]],
                fmt=self.errorlstyle)
            self.lines.append(tline)
            self.error_L.append(error_l)
            self.error_Bar.append(error_bar)
        elif (error_up and len(self.error_Bar[-1]) == 0): # trying to determine when we have new errorbar second case
            if not error_down:
                error_down = error_up
            tline, error_l, error_bar = self.ax.errorbar(
                [newx], [newy], [[error_up], [error_down]],
                fmt=self.errorlstyle)
            self.lines.append(tline)
            self.error_L.append(error_l)
            self.error_Bar.append(error_bar)
        elif error_up:
            if not error_down:
                error_down = error_up
            self.lines[k].set_xdata(np.append(self.lines[k].get_xdata(), newx))
            self.lines[k].set_ydata(np.append(self.lines[k].get_ydata(), newy))
            self.error_Bar[k][0].set_segments(
                np.append(self.error_Bar[k][0].get_segments(),
                          [np.array([[newx, newy + error_up],
                                     [newx, newy - error_down]])],
                          axis=0))
            self.error_L[k][0].set_ydata(
                np.append(self.error_L[k][0].get_ydata(), newy - error_down))
            self.error_L[k][1].set_ydata(
                np.append(self.error_L[k][1].get_ydata(), error_up + newy))
            self.error_L[k][0].set_xdata(
                np.append(self.error_L[k][0].get_xdata(), newx))
            self.error_L[k][1].set_xdata(
                np.append(self.error_L[k][1].get_xdata(), newx))
        else:        # Update data (with the new *and* the old points)
            self.lines[k].set_xdata(np.append(self.lines[k].get_xdata(), newx))
            self.lines[k].set_ydata(np.append(self.lines[k].get_ydata(), newy))
        # Need both of these in order to rescale
        self.ax.relim()
        self.ax.autoscale_view()
        # We need to draw *and* flush
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def clear(self):
        for k in range(len(self.lines)):
            self.lines[k].set_xdata([])
            self.lines[k].set_ydata([])
        self.lines = []
        self.addnew()
        self.ax.relim()
        self.ax.autoscale_view()
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()


def get_limits(inst, query):
    """
    Queries minimum and maximum values from instrument

    Parameters
    ----------
    instr : pyvisa.resource.Resource
        instrument interface to query from
    query : str
        SCPI value to query

    Returns
    -------
    [float, float]
        minimum, maximum value
    """
    return [
        inst.query_ascii_values(query+"? MIN")[0],
        inst.query_ascii_values(query+"? MAX")[0]]


def get_bool(inst, query):
    """
    Queries boolean values from instrument

    Parameters
    ----------
    instr : pyvisa.resource.Resource
        instrument interface to query from
    query : str
        SCPI value to query

    Returns
    -------
    bool
    """
    return (inst.query_ascii_values(query+"?", converter=u'd')[0] == 1)


def set_bool(inst, query, value):
    """
    Sets boolean values from instrument

    Parameters
    ----------
    instr : pyvisa.resource.Resource
        instrument interface to query from
    query : str
        SCPI value to use
    value : bool
        value to write
    """
    if (value):
        inst.write(query+" 1")
    else:
        inst.write(query+" 0")


class NumpyAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            if obj.ndim == 1:
                return obj.tolist()
            else:
                return [self.default(obj[i]) for i in range(obj.shape[0])]
        return json.JSONEncoder.default(self, obj)


def json_write(obj, path):
    fp = open(path, mode='w')
    json.dump(obj, fp, cls=NumpyAwareJSONEncoder)
    fp.close()


def json_load(path):
    fp = open(path)
    tmp = json.load(fp)
    fp.close()
    return tmp


def twos_complement(n, nbits=32):
    """
    2's complement and its inverse
    """
    if n < 0:
        n += (1 << nbits)
    elif n & (1 << (nbits - 1)) != 0:
        n -= (1 << nbits)
    return n


def save_path(user, subfolder=None, utc=False, local_config=PKGPTH+'local.json'):
    """
    Create current date directory in user's sub-folder

    Parameters
    ----------
    user : str
        user sub-folder
    subfolder : str, optional
        sub-folder within directory
    utc : bool, optional
        use utc instead of local-time
    local_config : str, optional
        path to configuration file

    Returns
    -------
    svepth : str
        string for directory created
    """
    config = json_load(local_config)
    svepth = config['data_path']
    if len(str(user)):
        svepth += str(user)
    else:
        svepth += "None"
    svepth += "/"
    if utc:
        dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now()
    svepth += dt.isoformat()[:10] + "/"
    if subfolder is not None and len(str(subfolder)) > 0:
        svepth += str(subfolder) + "/"
    if not os.path.exists(svepth):
        os.makedirs(svepth)
    return svepth
