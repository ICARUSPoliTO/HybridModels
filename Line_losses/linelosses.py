"""
This file provides the builder for the feeding line losses model
"""
import CoolProp.CoolProp as cp
import inspect
import numpy as np
import matplotlib.pyplot as plt



def linelosses():
    frame = inspect.currentframe().f_back
    while frame is not None:
        if 'lossInput' in frame.f_locals:
            delta_p = frame.f_locals['lossInput']
            return delta_p
        if 'lossInput' in frame.f_globals:
            delta_p = frame.f_globals['lossInput']
            return delta_p
        frame = frame.f_back
    delta_p = 0
    if delta_p == 0:
        print("PCheck if you really wanted no pressure losses")
    return delta_p
