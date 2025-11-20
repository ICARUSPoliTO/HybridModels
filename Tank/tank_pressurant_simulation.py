"""
This file provides the functions to simulate a tank of fluid with an inert pressurant.
"""

import numpy as np
import matplotlib.pyplot as plt
import CoolProp.CoolProp as cp
import Line_losses.linelosses as linelosses
import Injection.PyInjection as injection

def create_pressurant_tank(T0, P0, V_propellant, p_reg, pressurant):
    """
    This function creates the tank (returns volume and starting mass) for a pressurant with adiabatic deployment.
    :param T0: Starting temperature [K]
    :param P0: Starting pressure [Pa]
    :param V_propellant: Propellant volume [m^3]
    :param p_reg: Regulation pressure [Pa]
    :param pressurant: Pressurant CoolProp name
    :return: V0: Starting volume [m^3],
             m0: Starting mass [kg],
    """

    Pfin = 1.2 * p_reg #Educate guess of the final pressure in the pressurant tank [Pa]

    gamma = (cp.PropsSI('CPMASS', 'T', T0, 'P', P0, pressurant)
             / cp.PropsSI('CVMASS', 'T', T0, 'P', P0, pressurant))

    R = 8314 / (cp.PropsSI('MOLARMASS', pressurant) / 1e-3)

    V0 = (gamma * p_reg * V_propellant)/(P0 - Pfin)
    m0 = (P0 * V0)/(R * T0)
    return V0

def create_propellant_tank(mp0, p0, T0, Q0, propellant, pressurant):
    """
    This function creates a tank with pressurant at a given pressure.
    !!!
    WE NEED A CHECK IN INPUT PRESSURE BECAUSE:
        if (Q0 < 1) & (p0 >= vapor pressure of propellant):
            correct
        elseif (Q0 < 1) & (p0 < vapor pressure of propellant):
            WE SHOULD HAVE A FULL GAS TANK -> WARN TO CHANGE FUNCTION (NO NEED OF PRESSURANT)
        elseif Q >= 1:
            WE SHOULD HAVE A FULL GAS TANK -> WARN TO CHANGE FUNCTION (NO NEED OF PRESSURANT)
    !!!

    :param mp0: Initial liquid mass (if Q<1), total mass (if Q==1) [kg]
    :param p0: Initial pressure [Pa]
    :param T0: Initial temperature [K]
    :param Q0: Initial vapor quality
    :param propellant: Propellant CoolProp name
    :param pressurant: Pressurant CoolProp name
    :return: V_tank: Propellant tank volume [m^3]
    """

    MM = cp.PropsSI('MOLARMASS', pressurant) / 1e-3 #[kg/kmol]
    R = 8314/MM #[J/kgK]

    V_ullage = (Q0/(1 - Q0)) * mp0 * R * T0 / p0 #[m^3]
    m_press = p0 * V_ullage / (R * T0) #[kg]

    rho_liq = cp.PropsSI('D', 'T', T0, 'Q', 0, propellant) #[kg/m^3]
    V_liq = mp0 / rho_liq #[m^3]

    V_tank = V_liq + V_ullage

    return V_tank

def starting_conditions(mL, T, ptank, ppress, Vtank, Vpress, propellant, pressurant):
    """
    This function provides the starting conditions for the step function.
    :param mL: Liquid mass [kg]
    :param T: Temperature [K]
    :param ptank: Tank pressure [Pa]
    :param ppress: Pressurant pressure [Pa]
    :param Vtank: Tank volume [m^3]
    :param Vpress: Pressurant volume [m^3]
    :param propellant: Propellant CoolProp name
    :param pressurant: Pressurant CoolProp name
    :return: sL: Liquid specific entropy [J/kgK],
             sG: Gas specific entropy [J/kgK],
             spress: Pressurant specific entropy [J/kgK],
             mG: Ullage gas mass [kg],
             mpress: Pressurant mass [kg]
    """
    sL = cp.PropsSI('S', 'T', T, 'Q', 0, propellant)
    sG = cp.PropsSI('S', 'T', T, 'P', ptank, pressurant)
    spress = cp.PropsSI('S', 'T', T, 'P', ppress, pressurant)

    rhoL = cp.PropsSI('D', 'T', T, 'Q', 0, propellant)
    VL = mL / rhoL
    VG = Vtank - VL
    R = 8314/(cp.PropsSI('MOLARMASS', pressurant) / 1e-3) #[J/kgK]
    mG = (ptank * VG) / (R * T)

    mpress = (ppress * Vpress) / (R * T)

    return sL, sG, spress, mG, mpress


def do_one_step(mdotL, mdotG, sL, sG, spress, mL, mG, mpress, T_tank, propellant, pressurant, Vtank, Vpress, dt):
    """
    This function performs the one step of the simulation with entropy conservation but it returns wrong outputs
    (the temperature drops too low).
    Do not use it, instead use the previous functions to generate the tank and then iterate with
    costant pressure of the tank until the liquid is over.
    :param mdotL: Liquid mass flow [kg/s]
    :param mdotG: Pressurant mass flow [kg/s]
    :param sL: Liquid specific entropy [J/kgK]
    :param sG: Gas specific entropy [J/kgK]
    :param spress: Pressurant specific entropy [J/kgK]
    :param mL: Liquid mass [kg]
    :param mG: Gas mass [kg]
    :param mpress: Pressurant mass [kg]
    :param T_tank: Tank temperature [K]
    :param propellant: Propellant CoolProp name
    :param pressurant: Pressurant CoolProp name
    :param Vtank: Tank volume [m^3]
    :param Vpress: Pressurant volume [m^3]
    :param dt: Time step [s]
    :return: mL_new: New liquid mass [kg],
             mG_new: New gas mass [kg],
             mpress_new: New pressurant mass [kg],
             sL_new: New liquid specific entropy [J/kg],
             sG_new: New gas specific entropy [J/kg],
             spress_new: New pressurant specific entropy [J/kg],
             ptank_new: New tank pressure [Pa],
             Ttank_new: New tank temperature [K],
             p_press_new: New pressurant pressure [Pa]
    """

    mL_new = mL - mdotL*dt #[kg]
    mG_new = mG + mdotG*dt #[kg]
    mpress_new = mpress - mdotG*dt #[kg]

    SL = sL * mL #[J/K]
    SG = sG * mG #[J/K]
    Spress = spress * mpress #[J/K]
    S = SL + SG + Spress #[J/K]

    S_new = S - mdotL * sL #[J/K]

    rhopress_new = mpress_new / Vpress #[kg/m^3]
    #spress_new = cp.PropsSI('S', 'D', rhopress_new, 'Q', 1, pressurant)  # [J/kgK]
    spress_new = spress
    Spress_new = spress_new * mpress_new #[J/K]
    p_press_new = cp.PropsSI('P', 'D', rhopress_new, 'S', spress_new, pressurant)  # [Pa]

    rhoL = cp.PropsSI('D', 'T', T_tank, 'Q', 0, propellant) #[kg/m^3]
    VL_new = mL_new / rhoL #[m^3]

    VG_new = Vtank - VL_new #[m^3]
    rhoG_new = mG_new / VG_new #[kg/m^3]
    #sG_new = cp.PropsSI('S', 'D', rhoG_new, 'Q', 1, pressurant)  # [J/kgK]
    sG_new = sG
    SG_new = sG_new * mG_new #[J/K]
    ptank_new = cp.PropsSI('P', 'D', rhoG_new, 'S', sG_new, pressurant)  # [Pa]

    SL_new = S_new - Spress_new - SG_new #[J/K]
    sL_new = SL_new / mL_new #[J/kgK]
    Ttank_new = cp.PropsSI('T','S', sL_new, 'P', ptank_new, propellant)  # [K]

    return mL_new, mG_new, mpress_new, sL_new, sG_new, spress_new, ptank_new, Ttank_new, p_press_new

if __name__ == '__main__':
    T = 288
    ppress = 200e5
    ptank = 70e5
    preg = ptank
    pressurant = "Helium"

    mL = 5
    Q0 = 0.01
    propellant = "NitrousOxide"

    pc = 1e5
    CD = 0.8
    Ainj = np.pi * 0.25 * (5e-3)**2
    Avent = np.pi * 0.25 * (12e-3)**2
    inj = injection.Injector(propellant)

    Vtank = create_propellant_tank(mL, ptank, T, Q0, propellant, pressurant)
    Vpress = create_pressurant_tank(T, ppress, Vtank, ptank, pressurant)

    sL, sG, spress, mG, mpress = starting_conditions(mL, T, ptank, ppress, Vtank, Vpress, propellant, pressurant)

    dt = 1e-2
    I = np.arange(100)
    mL_out = np.zeros(len(I))
    mG_out = np.zeros(len(I))
    mpress_out = np.zeros(len(I))
    ptank_out = np.zeros(len(I))
    ppress_out = np.zeros(len(I))
    T_out = np.zeros(len(I))

    mL_out[0] = mL
    mG_out[0] = mG
    mpress_out[0] = mpress
    T_out[0] = T
    ptank_out[0] = ptank
    ppress_out[0] = ppress
    for i in I:
        inj.massflow(ptank, pc, T, CD)
        mdotL = inj.mdot * Ainj
        mdotG = Avent * injection.gas_injection(preg, ptank, T, CD, pressurant)

        mL, mG, mpress, sL, sG, spress, ptank, T, ppress = (
            do_one_step(mdotL, mdotG, sL, sG, spress, mL, mG, mpress, T, propellant, pressurant, Vtank, Vpress, dt))

        mL_out[i] = mL
        mG_out[i] = mG
        mpress_out[i] = mpress
        T_out[i] = T
        ptank_out[i] = ptank
        ppress_out[i] = ppress

    print("Oxidizer volume [m^3] = ", Vtank)
    print("Pressurant volume [m^3] = ", Vpress)
    print("Pressurant mass [kg] = ", mpress)

    plt.figure()
    plt.plot(I, mL_out, 'b-', label='mL')
    plt.plot(I, mG_out, 'g-', label='mG')
    plt.plot(I, mpress_out, 'r-', label='mpress')
    plt.legend()

    plt.figure()
    plt.plot(I, T_out, 'b-', label='T')
    plt.legend()

    plt.figure()
    plt.plot(I, ptank_out, 'b-', label='Tank')
    plt.plot(I, ppress_out, 'r-', label='Pressurant')
    plt.legend()

    plt.show()

# End of file