"""
This file provides the builder for the feeding line losses model
"""
import CoolProp.CoolProp as cp
import numpy as np
import matplotlib.pyplot as plt


def linelosses(lossInput):
    delta_p = lossInput
    return delta_p