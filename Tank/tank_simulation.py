"""
This script provides the functions to simulate the emptying of a self-pressurizing oxidizer tank.
Procedure according to
Engineering Model for Self-Pressurizing Saturated-N2O-Propellant Feed Systems
Stephen A. Whitmore∗ and Spencer N. Chandler†
Utah State University, Logan, Utah 84322-4130
DOI: 10.2514/1.47131
"""

import numpy as np
import matplotlib.pyplot as plt
import CoolProp.CoolProp as cp
import Line_losses.linelosses as linelosses
import Injection.PyInjection as injection

def create_tank(m, Q, T, oxidizer):
    """
    This function creates a tank using the given oxidizer properties, mass, temperature and vapor quality (mV/mTOT)
    :param m: Total mass [kg]
    :param Q: Vapor quality
    :param T: Temperature [K]
    :param oxidizer: oxidizer properties (Coolprop & CEA)
        {"OxidizerCP" : "", <--Name for CoolProp
        "OxidizerCEA" : "", <--Name for CEA
        "Weight fraction" : "100", # Multi-fluid Ox injector not available
        "Exploded Formula": "",
        "Temperature [K]" : "",
        "Specific Enthalpy [kj/mol]" : ""
        }
    :return: Tank volume [m^3]
    """
    rhoL = cp.PropsSI('D', 'T', T, 'Q', 0, oxidizer["OxidizerCP"])  # [kg/m^3]
    rhoV = cp.PropsSI('D', 'T', T, 'Q', 1, oxidizer["OxidizerCP"])  # [kg/m^3]

    Vtank = (Q* (rhoL - rhoV) + rhoV) * m/(rhoV * rhoL)
    return Vtank

def starting_conditions(m0, T0, Vtank, oxidizer):
    """
    This function gets the starting pressure, vapor quality, specific entropies for liquid (L), vapor (V) and tank
    and entropy of the tank. The values are calculated using CoolProp.
    :param m0: Initial mass [kg]
    :param T0: Initial temperature [K]
    :param Vtank: Tank volume [m^3]
    :param oxidizer:  oxidizer properties (Coolprop & CEA)
        {"OxidizerCP" : "", <--Name for CoolProp
        "OxidizerCEA" : "", <--Name for CEA
        "Weight fraction" : "100", # Multi-fluid Ox injector not available
        "Exploded Formula": "",
        "Temperature [K]" : "",
        "Specific Enthalpy [kj/mol]" : ""
        }
    :return: ptank0 (starting pressure) [Pa],
             sL0 (starting liquid specific entropy) [J/kgK],
             sV0 (starting vapor specific entropy) [J/kgK],
             Q0 (starting vapor quality),
             s0 (starting specific entropy) [J/kgK],
             S0 (starting entropy) [J/K]
    """
    ptank0 = cp.PropsSI('P', 'T', T0, 'Q', 1, oxidizer["OxidizerCP"]) #[Pa]

    rhoL0 = cp.PropsSI('D', 'T', T0, 'Q', 0, oxidizer["OxidizerCP"]) #[kg/m^3]
    sL0 = cp.PropsSI('S', 'T', T0, 'Q', 0, oxidizer["OxidizerCP"]) #[J/kgK]

    rhoV0 = cp.PropsSI('D', 'T', T0, 'Q', 1, oxidizer["OxidizerCP"]) #[kg/m^3]
    sV0 = cp.PropsSI('S', 'T', T0, 'Q', 1, oxidizer["OxidizerCP"]) #[J/kgK]

    Q0 = (rhoV0*rhoL0*Vtank - rhoV0*m0)/(m0*(rhoL0 - rhoV0))

    mL0 = m0*(1-Q0) #[kg]
    mV0 = m0*Q0 #[kg]

    s0 = sL0*(1 - Q0) + sV0*Q0 #[J/kgK]
    S0 = sL0*Q0 #[J/kgK]

    return ptank0, sL0, sV0, mL0, mV0, Q0, s0, S0


def do_one_step(mdotL, ptank, pamb, Ttank, sL, sV, S, m, oxidizer, plim, Avent, CD_vent, Vtank, dt):
    """
    This function does a time-step for the blow-down of the tank. If the pressure is over the imposed limit,
    it vents out the gas (ideal).
    :param mdotL: Liquid mass flow [kg/s]
    :param ptank: Tank pressure [Pa]
    :param pamb: Ambient pressure [Pa]
    :param Ttank: Tank temperature [K]
    :param sL: Liquid specific entropy [J/kgK]
    :param sV: Vapor specific entropy [J/kgK]
    :param S: Total entropy [J/K]
    :param m: Total mass [kg]
    :param oxidizer: oxidizer properties (Coolprop & CEA)
        {"OxidizerCP" : "", <--Name for CoolProp
        "OxidizerCEA" : "", <--Name for CEA
        "Weight fraction" : "100", # Multi-fluid Ox injector not available
        "Exploded Formula": "",
        "Temperature [K]" : "",
        "Specific Enthalpy [kj/mol]" : ""
        }
    :param plim: Limit pressure of the tank [Pa]
    :param Avent: Vent area [m^2]
    :param CD_vent: Vent port CD
    :param Vtank: Tank volume [m^3]
    :param dt: Time step [s]
    :return: m_new (total mass after time-step) [kg],
             mL_new (liquid mass after time-step) [kg],
             mV_new (vapor mass after time-step) [kg],
             Q_new (vapor quality after time-step),
             sL_new (liquid specific entropy after time-step) [J/kgK],
             sV_new (vapor specific entropy after time-step) [J/kgK],
             S_new (total entropy after time-step) [J/K],
             ptank_new (tank pressure after time-step) [Pa],
             Ttank_new (tank temperature after time-step) [K]
    """
    if ptank > plim:
        gamma = (cp.PropsSI('CPMASS', 'P', ptank, 'T', Ttank, oxidizer["OxidizerCP"])
                 / cp.PropsSI('CVMASS', 'P', ptank, 'T', Ttank, oxidizer["OxidizerCP"]))
        R = 8314 / (cp.PropsSI('MOLARMASS', 'P', ptank, 'T', Ttank, oxidizer["OxidizerCP"]) / 1e-3) #[J/kgK]

        mdotV = CD_vent * Avent * ptank / np.sqrt(R * Ttank) #[kg/s]
        gammone = np.sqrt(gamma * (2 / (gamma + 1)) ** ((gamma + 1) / (gamma - 1)))
        ptank_pamb_crit = (2 / (gamma + 1)) ** (gamma / (gamma - 1))
        if (pamb / ptank) < ptank_pamb_crit:  # Is critical?
            mdotV = mdotV * gammone
        else:
            mdotV = mdotV * np.sqrt(
                (2 * gamma) * ((pamb / ptank) ** (2 / gamma) - (pamb / ptank) ** ((gamma + 1) / gamma)) / (gamma - 1))

    else:
        mdotV = 0

    m_new = m - (mdotL + mdotV)*dt #[kg]
    S_new = S - (sL*mdotL + sV*mdotV)*dt #[J/K]
    s_new = S_new/m_new #[J/kgK]
    rho_new = m_new/Vtank #[kg/m^3]

    ptank_new = cp.PropsSI('P', 'D', rho_new, 'S', s_new, oxidizer["OxidizerCP"]) #[Pa]
    Ttank_new = cp.PropsSI('T', 'D', rho_new, 'S', s_new, oxidizer["OxidizerCP"]) #[K]
    Q_new = cp.PropsSI('Q', 'D', rho_new, 'S', s_new, oxidizer["OxidizerCP"])

    sL_new = cp.PropsSI('S', 'T', Ttank_new, 'Q', 0, oxidizer["OxidizerCP"]) #[J/kgK]
    sV_new = cp.PropsSI('S', 'T', Ttank_new, 'Q', 1, oxidizer["OxidizerCP"]) #[J/kgK]

    mL_new = m_new*(1-Q_new) #[kg]
    mV_new = m_new*Q_new #[kg]

    return m_new, mL_new, mV_new, Q_new, sL_new, sV_new, S_new, ptank_new, Ttank_new


if __name__ == '__main__':
    m0 = 14 #[kg]
    T0 = 288 #[K]
    oxidizer = {"OxidizerCP": "NitrousOxide"}
    #Vtank = 18e-3 #[m^3]

    Q00 = 0.05
    Vtank = create_tank(m0, Q00, T0, oxidizer)

    Dinj = 0.1e-3 #[m]
    Ainj = 0.25*np.pi*Dinj**2 #[m^2]

    plim = 70e5 #[Pa]

    Avent = Ainj

    dt = 1e-2 #[s]

    ptank0, sL0, sV0, mL0, mV0, Q0, s0, S0 = starting_conditions(m0, T0, Vtank, oxidizer)

    m_new, mL_new, mV_new, Q_new, sL_new, sV_new, S_new, ptank_new, Ttank_new = (
        do_one_step(ptank0, 1e5, 1e5, T0, sL0, sV0, S0, m0, oxidizer, 0.8, Ainj, plim, Avent, 0.8, Vtank, dt))

    print("Tank volume= "+str(Vtank*1e3)+" L")
    print("Starting tank pressure= "+str(ptank0)+" Pa")
    print("Starting temperature= "+str(T0)+" K")
    print("Starting mass= "+str(m0)+" kg")
    print("Starting liquid mass= "+str(mL0)+" kg")
    print("Starting vapor mass= "+str(mV0)+" kg")
    print("Starting quality= "+str(Q0))
    print("########### after "+str(dt)+" seconds ###########")
    print("New tank pressure= "+str(ptank_new)+" Pa")
    print("New temperature= "+str(Ttank_new)+" K")
    print("New mass= "+str(m_new)+" kg")
    print("New liquid mass= "+str(mL_new)+" kg")
    print("New vapor mass= "+str(mV_new)+" kg")
    print("New quality= "+str(Q_new)+" kg")




