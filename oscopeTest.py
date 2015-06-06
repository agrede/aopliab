# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 07:42:49 2015

@author: Maxwell-Faraday
"""

wav = np.zeros((t.size, 500))

for k in range(wav.shape[1]):
    oscpi.write("DIG 1")
    wav[:, k] = np.array(oscpi.query_binary_values("WAV:DATA?", datatype='B'))
