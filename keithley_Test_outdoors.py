# -*- coding: utf-8 -*-
"""
Created on Tue Sep 13 16:32:47 2016

@author: jspri
"""

from iv import ivmeasure
import visa
import numpy as np

# Connect to instruments and initialize
rm = visa.ResourceManager()
smui = ac.getInstr(rm, "SMU")
smu = K2400(smui)

    
bias_start = -2
bias_stop = 3.5
bias_step = 0.01
v  = np.arange(bias_step, bias_stop + bias_step, bias_step)
    
current_limit = 40E-3
    
dat = ivmeasure(v,current_limit, smu)