import numpy as np


def within_limits(value, limits):
    return (value is not None and limits[0] <= value and limits[1] >= value)


def nearest_index(value, values, rndup):
    if (value < values[0]):
        value = values[0]
    elif(value > values[-1]):
        value = values[-1]
    idx = np.where(value <= values)[0][0]
    if (not rndup and value < values[idx]):
        idx = idx-1
    return idx
