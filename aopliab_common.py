import numpy as np
import matplotlib.pyplot as plt
import json


def within_limits(value, limits):
    return (value is not None and limits[0] <= value and limits[1] >= value)


def nearest_index(value, values, rndup):
    k = np.where(np.isfinite(values))[0]
    tvalues = values[k]
    if (value < tvalues[0]):
        value = tvalues[0]
    elif(value > tvalues[-1]):
        value = tvalues[-1]
    idx = np.where(value <= tvalues)[0][0]
    if (not rndup and value < tvalues[idx]):
        idx = idx-1
    return k[idx]


class DynamicPlot():
    def __init__(self):
        #Set up plot
        self.figure, self.ax = plt.subplots()
        self.lines, = self.ax.plot([],[], 'o-')
        #Autoscale on unknown axis and known lims on the other
        self.ax.set_autoscale_on(True)

    def update(self, newx, newy):
        #Update data (with the new _and_ the old points)
        self.lines.set_xdata(np.append(self.lines.get_xdata(), newx))
        self.lines.set_ydata(np.append(self.lines.get_ydata(), newy))
        #Need both of these in order to rescale
        self.ax.relim()
        self.ax.autoscale_view()
        #We need to draw *and* flush
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def clear(self):
        self.lines.set_xdata([])
        self.lines.set_ydata([])
        self.ax.relim()
        self.ax.autoscale_view()
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()


class NumpyAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            if obj.ndim == 1:
                return obj.tolist()
            else:
                return [self.default(obj[i]) for i in range(obj.shape[0])]
        return json.JSONEncoder.default(self, obj)
        

def json_write(obj, fp):
    fo = open(fp, mode='w')
    json.dump(obj, fo, cls=NumpyAwareJSONEncoder)
    fo.close()