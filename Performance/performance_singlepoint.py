"""
This script provides the function to calculate the output performance of the Rocket Engine.
Author: Cristian Casalanguida 2025
"""
import CoolProp.CoolProp as cp
import numpy as np
import matplotlib.pyplot as plt
import Line_losses.linelosses as linelosses
import Injection.PyInjection as injection
import Performance.CEA_py as CEA_py
import time

def Gammone(g):
    G = np.sqrt(g * (2/(g + 1))**((g+1)/(g-1)))
    return G

def ER(g, pe, pc):
    pe_pc_crit = (2/(g+1))**(g/(g-1))
    if (pe/pc) < pe_pc_crit: # Is critical?
        eps = Gammone(g)/np.sqrt( (2*g)*( (pe/pc)**(2/g) - (pe/pc)**((g+1)/g) )/(g-1) )
    else:
        eps = 1
    return eps

def calculate_performance(Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD,
                          a, n, rho_fuel, oxidizer, fuel, pamb=0.0, gamma0=1.3):
    """
    This function calculates the output performance of the Rocket Engine.
    :param Ainj     : Injection Area                               [m^2]
    :param Aport    : Port Area                                    [m^2]
    :param Ab       : Burning Area                                 [m^2]
    :param eps      : Expansion Ratio user input
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
    :param gamma0   : Guess for specific heat ratio
    :return:    p_inj (Injected pressure) [Pa],
                mdot_ox (Oxidizer mass flow) [kg/(s*m**2)],
                mdot_fuel (Fuel mass flow) [kg/(s*m**2)],
                mdot (Total mass flow) [kg/(s*m**2)],
                Gox (Oxidizer mass flux) [kg/(s*m**2)],
                r (Regression rate) [m/s]
                MR (Mixture ratio)
                Tc (Chamber Temperature) [K]
                MW (Molecular Weight) [kg/kmol]
                gamma (Specific heats ratio)
                eps_out (Expansion ratio)
                cs (Characteristic velocity) [m/s]
                CF_vac (Force coefficient in vacuum)
                CF (Force coefficient)
                Ivac (Specific impulse in vacuum) [s]
                Is (Specific impulse) [s]
                flag_performance (0=converged, 1=diverged)
    """
    if eps == "adapt":
        eps_out = ER(gamma0, pamb, pc)
    else:
        eps_out = eps

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

    # Calculate total mass flow
    mdot = mdot_ox + mdot_fuel

    # Calculate CEA Output and performances
    flag_performance = 0
    try:
        MR = mdot_ox / mdot_fuel # if pinj==pc: mdot=0 -> MR=0/0
        CEA_output = CEA_py.runCEA(pc, MR, eps_out, oxidizer, fuel)
        Tc = CEA_output[0]  # [K] ##[0, 0]
        MW = CEA_output[1]  # [kg/Mol] ##[0, 1]
        gamma = CEA_output[2]  ##[0, 2]
        cs = CEA_output[3]  # [m/s] ##[0, 3]
        CF_vac = CEA_output[4]  ##[0, 4]
    except IndexError:
        flag_performance = 1
        MR = 0
        Tc=0
        MW=0
        gamma=0
        cs=0
        CF_vac=0
    except ZeroDivisionError:
        flag_performance = 1
        MR = 0
        Tc = 0
        MW = 0
        gamma = 0
        cs = 0
        CF_vac = 0

    CF = CF_vac - eps_out*(pamb/pc)

    Ivac = (cs*CF_vac)/9.81
    Is = (cs*CF)/9.81

    return (p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, eps_out, cs,
            CF_vac, CF, Ivac, Is, flag_performance)


def pressure_fun(Ainj, Aport, At, Ab, eps, ptank, Ttank, pc, CD, a, n, rho_fuel, oxidizer, fuel, pamb=0.0, gamma0=1.3):
    """
    This function calculates the pressure function used for Finite Difference Newton-like method
    to bring chamber pressure to convergence.
    The function comes from mass conservation equation between the injector and the nozzle's throat:
    mdot = m_ox + m_fuel = (pc*At)*f(M=1)/sqrt(R*Tc) = pc*At/cs
    We will search for the zero of the function:
    Fpc = mdot*cs/At - pc
    :param Ainj     : Injection Area                               [m^2]
    :param Aport    : Port Area                                    [m^2]
    :param At       : Throat Area                                  [m^2]
    :param Ab       : Burning Area                                 [m^2]
    :param eps      : Expantion Ratio
    :param ptank    : Tank total pressure                          [Pa]
    :param Ttank    : Tank total temperature                       [K]
    :param pc       : Chamber total pressure                       [Pa]
    :param CD       : Discharge coefficient
    :param a        : regression rate coefficient (r=a*Gox^n)
    :param n        : regression rate exponent (r=a*Gox^n)
    :param rho_fuel : Fuel Density                                 [kg/m^3]
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
    :param gamma0   : Guess for specific heat ratio (1.3 standard)
    :return: Fpc (pressure function) [Pa]
    """
    p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, eps_out, cs, CF_vac, CF, Ivac, Is, flag_performance =(
        calculate_performance(Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma0))

    if flag_performance == 0:
        Fpc = (mdot*cs)/At - pc
    else:
        Fpc = 1e8
    return Fpc


if __name__ == "__main__":
    Dinj = 0.8  # [m]
    ninj = 1
    Ainj = ninj * 0.25 * np.pi * (Dinj ** 2)

    Dport = 7  # [m]
    nport = 1
    Aport = nport * 0.25 * np.pi * (Dport ** 2)

    Dt = 1
    At = 0.25 * np.pi * (Dt ** 2)

    Lc = 15  # [m]
    Ab = nport * np.pi * Dport * Lc

    #pc = 43e5
    eps = "adapt"
    ptank = 55e5  # [Pa]
    Ttank = 288  # [K]
    pamb = 1  # [Pa]

    pc_range_a = np.linspace(pamb, 0.8*ptank, 50)
    pc_range_b = np.linspace(0.8 * ptank, ptank, 100)
    pc_range = np.concatenate((pc_range_a, pc_range_b[1:]))
    Fpc_range = 1e8*np.ones(len(pc_range))
    gamma0 = 1.3
    CD = 0.8
    a = 0.17e-3
    n = 0.5
    rho_fuel = 850  # [kg/m^3]
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
    for ind_pc, pc in enumerate(pc_range):
        p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, eps_out, cs, CF_vac, CF, Ivac, Is, flag_performance\
            =calculate_performance(Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD, a, n, rho_fuel, oxidizer, fuel, pamb)

        Fpc = pressure_fun(Ainj, Aport, At, Ab, eps, ptank, Ttank, pc, CD, a, n, rho_fuel, oxidizer, fuel, pamb)

        Fpc_range[ind_pc] = Fpc

    end = time.perf_counter()
    runtime = (end - start)*1e3

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
    print("eps_out=             "+str(eps_out))
    print("cs=                  "+str(cs)+"    m/s"        )
    print("CF_vac=              "+str(CF_vac)          )
    print("CF=                  "+str(CF)              )
    print("Ivac=                "+str(Ivac)+"   s"        )
    print("Is=                  "+str(Is)+"    s"          )
    print("flag_performance=    "+str(flag_performance))
    print("Fpc=                 "+str(Fpc))
    print("runtime=             "+str(runtime)+"    ms"    )

    # remove bad solutions
    mask = Fpc_range != 1e8
    Fpc_range = Fpc_range[mask]
    pc_range = pc_range[mask]

    if (np.all(abs(Fpc_range)==Fpc_range)
            or np.all(-abs(Fpc_range)==Fpc_range)):
        acceptable = "CONFIGURATION UNACCEPTABLE" # No zero can be found, don't waste time
    else:
        acceptable = "CONFIGURATION ACCEPTABLE"

    plt.plot(pc_range, Fpc_range)
    plt.xlabel("pc [Pa]")
    plt.ylabel("Fpc [Pa]")
    plt.axhline(y=0, color='k')
    plt.axvline(x=0, color='k')
    plt.title("Dp="+str(Dport)+"; Dinj="+str(Dinj)+"; L="+str(Lc))
    plt.text(0, 2e6, acceptable)
    plt.show()
## end of file