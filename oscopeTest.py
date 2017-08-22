import numpy as np
import aopliab_common as ac
import visa
import eqe
from time import sleep, time
import matplotlib.pyplot as plt
from keysight import InfiniiVision5000, InfiniiVision5000Channel


rm = visa.ResourceManager()

osci = ac.getInstr(rm, "OScope")
osc = InfiniiVision5000(osci)
osc1 = InfiniiVision5000Channel(osc, 1)
osc4 = InfiniiVision5000Channel(osc, 4)