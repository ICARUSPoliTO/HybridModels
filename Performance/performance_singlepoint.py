"""
This script provides the function to calculate the output performance of the Rocket Engine.

"""
import CoolProp.CoolProp as cp
import numpy as np
import matplotlib.pyplot as plt
import Line_losses.linelosses as linelosses
import Injection.PyInjection as injection
import CEA_py
import time


def calculate_performance(Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD, a, n, rho_fuel, oxidizer, fuel, pamb=0):
    """
    This function calculates the output performance of the Rocket Engine.
    :param Ainj     : Injection Area                               [m^2]
    :param Aport    : Port Area                                    [m^2]
    :param Ab       : Burning Area                                 [m^2]
    :param eps      : Expantion Ratio
    :param ptank    : Tank total pressure                          [Pa]
    :param Ttank    : Tank total temperature                       [K]
    :param pc       : Chamber total pressure                       [Pa]
    :param CD       : Discharge coefficient
    :param a        : regression rate coefficient (r=a*Gox^n)
    :param n        : regression rate exponent (r=a*Gox^n)
    :param rho_fuel : Fuel Density                                  [kg/m^3]
    :param oxidizer : oxidizer properties (Coolprop & CEA)
        {"OxidizerCP" : "", <--Name for CoolProp
        "OxidizerCEA" : "", <--Name for CEA
        "Weight fraction" : "100", # Multi-fluid Ox injector not available
        "Exploded Formula": "",
        "Temperature [K]" : "",
        "Specific Enthalpy [kj/mol]" : ""
        }
    :param fuel     : fuel properties
        {"Fuels" : [],  <--Names for CEA
        "Weight fraction" : [],
        "Exploded Formula": [],
        "Temperature [K]" : [],
        "Specific Enthalpy [kj/mol]" : []
        }
    :param pamb     : Ambient pressure                              [Pa]
    :return:    p_inj, <--Injected pressure
                mdot_ox, <--Oxidizer mass flow
                mdot_fuel, <--Fuel mass flow
                mdot, <--Total mass flow
                Gox, <--Oxidizer mass flux
                r, <--Regression rate [m/s]
                MR, <--Mixture ratio
                Tc, <--Chamber Temperature [K]
                MW, <--Molecular Weight [kg/kmol]
                gamma,
                cs, <--Characteristic velocity [m/s]
                CF_vac, <--Force coefficient in vacuum
                CF, <--Force coefficient
                Ivac, <--Specific impulse in vacuum [s]
                Is, <--Specific impulse [s]
                flag_performance <--0=converged, 1=diverged
    """
    # Calculate injection pressure after losses. May require iterations with Oxidizer injection
    p_inj = ptank - linelosses.linelosses() #add input for line losses here and in the inputs of the function

    # Calculate injection mass flow
    inj = injection.Injector(oxidizer["OxidizerCP"])
    inj.massflow(p_inj, pc, Ttank, CD)
    mdot_ox = inj.mdot * Ainj

    # Calculate injection mass flux
    Gox = mdot_ox/Aport

    # Calculate fuel regression rate
    r = a*Gox**n

    # Calculate fuel mass flow
    mdot_fuel = rho_fuel*Ab*r

    # Calculate total mass flow and Mixture ratio
    mdot = mdot_ox + mdot_fuel
    MR = mdot_ox/mdot_fuel

    # Calculate CEA Output and performances
    flag_performance = 0
    try:
        CEA_output = CEA_py.runCEA(pc, MR, eps, oxidizer, fuel)
        Tc = CEA_output[0]  # [K] ##[0, 0]
        MW = CEA_output[1]  # [kg/Mol] ##[0, 1]
        gamma = CEA_output[2]  ##[0, 2]
        cs = CEA_output[3]  # [m/s] ##[0, 3]
        CF_vac = CEA_output[4]  ##[0, 4]
    except IndexError:
        flag_performance = 1
        Tc=0
        MW=0
        gamma=0
        cs=0
        CF_vac=0

    CF = CF_vac - eps*(pamb/pc)

    Ivac = (cs*CF_vac)/9.81
    Is = (cs*CF)/9.81

    return p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, cs, CF_vac, CF, Ivac, Is, flag_performance


if __name__ == "__main__":
    Dinj = 1e-3 #[m]
    ninj = 10
    Ainj = ninj*0.25*np.pi*(Dinj**2)

    Dport = 1e-2 #[m]
    nport = 1
    Aport = nport*0.25*np.pi*(Dport**2)

    Lc = 20e-2 #[m]
    Ab = nport*np.pi*Dport*Lc

    eps = 6
    ptank = 55e5 #[Pa]
    Ttank = 288 #[K]
    pc = 43e5 #[Pa]
    pamb = 1e5 #[Pa]
    CD = 0.8
    a = 0.17e-3
    n = 0.5
    rho_fuel = 850 #[kg/m^3]
    oxidizer = {"OxidizerCP" : "NitrousOxide",
        "OxidizerCEA" : "N2O",
        "Weight fraction" : "100", # Multi-fluid Ox injector not available
        "Exploded Formula": "",
        "Temperature [K]" : "",
        "Specific Enthalpy [kj/mol]" : ""
        }
    fuel = {"Fuels" : ["paraffin"],
        "Weight fraction" : ["100"],
        "Exploded Formula": ["C 73 H 124"],
        "Temperature [K]" : [float(533)],
        "Specific Enthalpy [kj/mol]" : [-1860.6]
        }

    start = time.perf_counter()
    p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, cs, CF_vac, CF, Ivac, Is, flag_performance\
        =calculate_performance(Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD, a, n, rho_fuel, oxidizer, fuel, pamb)
    end = time.perf_counter()
    runtime = (end - start)*1e-3

    print("p_inj=               "+str(p_inj)+"    Pa"      )
    print("mdot_ox=             "+str(mdot_ox)+"    kg/s"  )
    print("mdot_fuel=           "+str(mdot_fuel)+"    kg/s")
    print("mdot=                "+str(mdot)+"    kg/s"     )
    print("Gox=                 "+str(Gox)+"    kg/s*m^2"  )
    print("r=                   "+str(r)+"    m/s"         )
    print("MR=                  "+str(MR)              )
    print("Tc=                  "+str(Tc)+"    K"          )
    print("MW=                  "+str(MW)+"    kg/kmol"    )
    print("gamma=               "+str(gamma)           )
    print("cs=                  "+str(cs)+"    m/s"        )
    print("CF_vac=              "+str(CF_vac)          )
    print("CF=                  "+str(CF)              )
    print("Ivac=                "+str(Ivac)+"   s"        )
    print("Is=                  "+str(Is)+"    s"          )
    print("flag_performance=    "+str(flag_performance))
    print("runtime=             "+str(runtime)+"    ms"    )

## end of file