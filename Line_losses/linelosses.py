"""
This file provides the builder for the feeding line losses model
"""
import CoolProp.CoolProp as cp
import inspect
import numpy as np
import matplotlib.pyplot as plt


def linelosses(ptank):
    frame = inspect.currentframe().f_back
    while frame is not None:
        if 'lossInput' in frame.f_locals:
            delta_p = frame.f_locals['lossInput']
            break
        if 'lossInput' in frame.f_globals:
            delta_p = frame.f_globals['lossInput']
            break
        frame = frame.f_back
    else:
        delta_p = 0
        print("Check if you really wanted no pressure losses")

    if isinstance(delta_p, list):
        if ptank > delta_p[1]:
            return ptank - (delta_p[1] - delta_p[0])
        else:
            return delta_p[0]
    else:
        return delta_p
