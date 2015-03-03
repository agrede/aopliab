import numpy as np


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
