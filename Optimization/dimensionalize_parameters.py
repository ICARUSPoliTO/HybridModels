"""
This script provides the functions to dimensionalise the parameter of the optimization given an input.
"""

import numpy as np
import matplotlib.pyplot as plt

def Thrust2Rocket(F, Dinj_Dt, Dp_Dt, Lc_Dt, mdot_ox_Dtsq, mdot_fuel_Dtsq, mdot_Dtsq, pc, CF, rend_CF = 1.0):
    """
    This function dimensionalize the parameter of the optimization given the desired thrust and the CF efficiency.
    :param F: Desired thrust [N]
    :param Dinj_Dt: Injection equivalent diameter and throat diameter ratio
    :param Dp_Dt: Port equivalent diameter and throat diameter ratio
    :param Lc_Dt: Grain equivalent length and throat diameter ratio
    :param mdot_ox_Dtsq: Oxidizer mass flow and squared throat diameter ratio
    :param mdot_fuel_Dtsq: Fuel mass flow and squared throat diameter ratio
    :param mdot_Dtsq: Total mass flow and squared throat diameter ratio
    :param pc: Chamber pressure [Pa]
    :param CF: Thrust coefficient {F/(pc*At)}
    :param rend_CF: Thrust coefficient efficiency
    :return: Dinj: Injection equivalent diameter [m],
             Dp: Port equivalent diameter [m],
             Lc: Fuel grain equivalent length [m],
             Dt: Throat diameter [m],
             mdot_ox: Oxidizer mass flow [kg/s],
             mdot_fuel: Fuel mass flow [kg/s],
             mdot: Total mass flow [kg/s]
    """
    pcAt = F / (rend_CF * CF) # rend * CFideal = F / (pc * At)
    At = pcAt / pc

    Dt = np.sqrt(4 * At / np.pi)

    Dinj = Dinj_Dt * Dt
    Dp = Dp_Dt * Dt
    Lc = Lc_Dt * Dt
    mdot_ox = mdot_ox_Dtsq * Dt**2
    mdot_fuel = mdot_fuel_Dtsq * Dt**2
    mdot = mdot_Dtsq * Dt**2

    return Dinj, Dp, Lc, Dt, mdot_ox, mdot_fuel, mdot

def Dt2Rocket(Dt, Dinj_Dt, Dp_Dt, Lc_Dt, mdot_ox_Dtsq, mdot_fuel_Dtsq, mdot_Dtsq):
    """
    This functions dimensionalize the parameter of the optimization given the throat diameter.
    :param Dt: Throat diameter [m]
    :param Dinj_Dt: Injection equivalent diameter and throat diameter ratio
    :param Dp_Dt: Port equivalent diameter and throat diameter ratio
    :param Lc_Dt: Grain equivalent length and throat diameter ratio
    :param mdot_ox_Dtsq: Oxidizer mass flow and squared throat diameter ratio
    :param mdot_fuel_Dtsq: Fuel mass flow and squared throat diameter ratio
    :param mdot_Dtsq: Total mass flow and squared throat diameter ratio
    :return: Dinj: Injection equivalent diameter [m],
             Dp: Port equivalent diameter [m],
             Lc: Fuel grain equivalent length [m],
             mdot_ox: Oxidizer mass flow [kg/s],
             mdot_fuel: Fuel mass flow [kg/s],
             mdot: Total mass flow [kg/s]
    """
    Dinj = Dinj_Dt * Dt
    Dp = Dp_Dt * Dt
    Lc = Lc_Dt * Dt
    mdot_ox = mdot_ox_Dtsq * (Dt ** 2)
    mdot_fuel = mdot_fuel_Dtsq * (Dt ** 2)
    mdot = mdot_Dtsq * (Dt ** 2)

    return Dinj, Dp, Lc, mdot_ox, mdot_fuel, mdot

def Dinj2Rocket(Dinj, Dinj_Dt, Dp_Dt, Lc_Dt, mdot_ox_Dtsq, mdot_fuel_Dtsq, mdot_Dtsq):
    """
    This functions dimensionalize the parameter of the optimization given the injection diameter.
    :param Dinj: Injection diameter [m]
    :param Dinj_Dt: Injection equivalent diameter and throat diameter ratio
    :param Dp_Dt: Port equivalent diameter and throat diameter ratio
    :param Lc_Dt: Grain equivalent length and throat diameter ratio
    :param mdot_ox_Dtsq: Oxidizer mass flow and squared throat diameter ratio
    :param mdot_fuel_Dtsq: Fuel mass flow and squared throat diameter ratio
    :param mdot_Dtsq: Total mass flow and squared throat diameter ratio
    :return: Dt: Throat diameter [m],
             Dp: Port equivalent diameter [m],
             Lc: Fuel grain equivalent length [m],
             mdot_ox: Oxidizer mass flow [kg/s],
             mdot_fuel: Fuel mass flow [kg/s],
             mdot: Total mass flow [kg/s]
    """
    Dt = Dinj / Dinj_Dt
    Dp = Dp_Dt * Dt
    Lc = Lc_Dt * Dt
    mdot_ox = mdot_ox_Dtsq * (Dt ** 2)
    mdot_fuel = mdot_fuel_Dtsq * (Dt ** 2)
    mdot = mdot_Dtsq * (Dt ** 2)

    return Dt, Dp, Lc, mdot_ox, mdot_fuel, mdot

def Dp2Rocket(Dp, Dinj_Dt, Dp_Dt, Lc_Dt, mdot_ox_Dtsq, mdot_fuel_Dtsq, mdot_Dtsq):
    """
    This functions dimensionalize the parameter of the optimization given the port diameter.
    :param Dp: Port diameter [m]
    :param Dinj_Dt: Injection equivalent diameter and throat diameter ratio
    :param Dp_Dt: Port equivalent diameter and throat diameter ratio
    :param Lc_Dt: Grain equivalent length and throat diameter ratio
    :param mdot_ox_Dtsq: Oxidizer mass flow and squared throat diameter ratio
    :param mdot_fuel_Dtsq: Fuel mass flow and squared throat diameter ratio
    :param mdot_Dtsq: Total mass flow and squared throat diameter ratio
    :return: Dt: Throat diameter [m],
             Dinj: Injection equivalent diameter [m],
             Lc: Fuel grain equivalent length [m],
             mdot_ox: Oxidizer mass flow [kg/s],
             mdot_fuel: Fuel mass flow [kg/s],
             mdot: Total mass flow [kg/s]
    """
    Dt = Dp / Dp_Dt
    Dinj = Dinj_Dt * Dt
    Lc = Lc_Dt * Dt
    mdot_ox = mdot_ox_Dtsq * (Dt ** 2)
    mdot_fuel = mdot_fuel_Dtsq * (Dt ** 2)
    mdot = mdot_Dtsq * (Dt ** 2)

    return Dt, Dinj, Lc, mdot_ox, mdot_fuel, mdot
