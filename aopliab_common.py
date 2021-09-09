import numpy as np
import matplotlib.pyplot as plt
import json
import pyvisa
import re
import serial as srl


def within_limits(value, limits):
    return (value is not None and limits[0] <= value and limits[1] >= value)


def getInstr(rm, name, local_config='local.json'):
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


def getSer(name, local_config='local.json'):
    """Load a serial object"""
    cfg_file = open(local_config)
    cfg = json.load(cfg_file)
    cfg_file.close()
    return srl.Serial(cfg[name]['addr'], cfg[name]['conn_params']['baud_rate'], timeout=cfg[name]['conn_params']['timeout'])


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


def parseTermString(str):
    strs = {'NULL': '\0', 'CR': '\r', 'LF': '\n'}
    m = re.match('<(\w+)>', str)
    if (m and m.group(1) in strs):
        return strs[m.group(1)]
    else:
        return str


def nearest_index(value, values, rndup):
    k = np.where(np.isfinite(values))[0]
    tvalues = values[k]
    if (value < tvalues[0]):
        value = tvalues[0]
    elif(value > tvalues[-1]):
        value = tvalues[-1]
    try:
        idx = np.where(value <= tvalues)[0][0]
    except IndexError:
        print(f"nearest_index({value}, {values})")
        raise IndexError
    if (not rndup and value < tvalues[idx]):
        idx = idx-1
    return k[idx]

class DynamicPlot():
    lines = []
    error_L = []
    error_Bar = []
    ptype = "plot"
    dlstyle = "o-"

    def __init__(self, ptype="plot", lstyle="o-", fig=None, label=None):
        self.ptype = ptype
        self.dlstyle = lstyle
        self.lines = []
        # Set up plot
        self.figure, self.ax = plt.subplots(num=fig)
        #self.addnew(label = label)
        if label:
            self.ax.legend()
        #Autoscale on unknown axis and known lims on the other
        self.ax.set_autoscale_on(True)

    def addnew(self, ptype=None, lstyle=None, label=None):
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
        elif (ptype is "errorbar"):
            if lstyle is None:
                self.errorlstyle  = self.dlstyle
            else : self.errorlstyle = lstyle
            return
        else:
            tline, = self.ax.plot([], [], lstyle)
        if label:
            tline.set_label(label)
            self.ax.legend()
        self.lines.append(tline)

    def update(self, newx, newy, error_up = None, error_down= None): # error_up an error_down are positive values
        k = len(self.lines) - 1
        if (error_up and len(self.lines)==0): # trying to determine when we have new errorbar first case
            if not error_down: error_down = error_up
            tline, error_l, error_bar = self.ax.errorbar([newx], [newy], [[error_up], [error_down]], fmt=self.errorlstyle)
            self.lines.append(tline)
            self.error_L.append(error_l)
            self.error_Bar.append(error_bar)
        elif (error_up and len(self.error_Bar[-1])==0): # trying to determine when we have new errorbar second case
            if not error_down: error_down = error_up
            tline, error_l, error_bar = self.ax.errorbar([newx], [newy], [[error_up], [error_down]], fmt=self.errorlstyle)
            self.lines.append(tline)
            self.error_L.append(error_l)
            self.error_Bar.append(error_bar)
        elif error_up:
            if not error_down: error_down = error_up
            self.lines[k].set_xdata(np.append(self.lines[k].get_xdata(), newx))
            self.lines[k].set_ydata(np.append(self.lines[k].get_ydata(), newy))
            self.error_Bar[k][0].set_segments(np.append(self.error_Bar[k][0].get_segments(), [np.array([[newx, newy + error_up], [newx, newy - error_down]])] ,axis=0))
            self.error_L[k][0].set_ydata(np.append(self.error_L[k][0].get_ydata(), newy - error_down))
            self.error_L[k][1].set_ydata(np.append(self.error_L[k][1].get_ydata(), error_up + newy))
            self.error_L[k][0].set_xdata(np.append(self.error_L[k][0].get_xdata(), newx))
            self.error_L[k][1].set_xdata(np.append(self.error_L[k][1].get_xdata(), newx))
        else:
	 #Update data (with the new _and_ the old points)
        self.lines[k].set_xdata(np.append(self.lines[k].get_xdata(), newx))
        self.lines[k].set_ydata(np.append(self.lines[k].get_ydata(), newy))
        #Need both of these in order to rescale

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
    return [
        inst.query_ascii_values(query+"? MIN")[0],
        inst.query_ascii_values(query+"? MAX")[0]]


def get_bool(inst, query):
    return (inst.query_ascii_values(query+"?", converter=u'd')[0] == 1)


def set_bool(inst, query, value):
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
