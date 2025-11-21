"""
This file provides the function to simulate a mission of an hybrid rocket engine.
"""
import numpy as np
import matplotlib.pyplot as plt
import Performance.performance_singlepoint as performance
import Injection.PyInjection as injection


def update_chamberpressure(pc_i, Tc_i, MW_i, Ab_i, mdot_ox_i, mdot_fuel_i, mdot_throat_i,
                           Vol_chamber_i, Ainj, Aport_i,
                           eps, ptank, Ttank, CD, a, n, rho_fuel, oxidizer, fuel, pamb=0.0, gamma0=1.3):
    """
    This function updates the chamber pressure with a finite difference of the mass conservation equation.
    dm/dt = mdot_ox + mdot_fuel - (pc * At / c*)
    with
    m = pc * V / (R * Tc) [Ideal gas state equation]
    dm/dt = d(pc/(R * Tc))/dt * V + pc/(R * Tc) * dV/dt
    and
    dV/dt = r * Ab

    :param pc_i: Chamber pressure previous step [Pa]
    :param Tc_i: Chamber temperature previous step [K]
    :param MW_i: Molecular weight previous step [kg/kmol]
    :param Ab_i: Burning area previous step [m^2]
    :param mdot_ox_i: Oxidizer mass flow previous step [kg/s]
    :param mdot_fuel_i: Fuel mass flow previous step [kg/s]
    :param mdot_throat_i: Mass flow through throat Area [kg/s]
    :param Vol_chamber_i: Volume of the chamber previous step [m^3]
    :param Ainj: Injection area [m^2]
    :param Aport_i: Port area previous step[m^2]
    :param eps: expansion ratio
    :param ptank: tank pressure [Pa]
    :param Ttank: Tank temperature [K]
    :param CD: Discharge coefficient
    :param a: regression rate coefficient r = a * Gox**n
    :param n: regression rate exponent r = a * Gox**n
    :param rho_fuel: fuel density [kg/m^3]
    :param oxidizer: oxidizer properties (Coolprop & CEA)
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
    :param pamb: ambient pressure [Pa]
    :param gamma0: specific heat ratio initial guess
    :return pc: Chamber pressure [Pa]
            flag: 0=converged, 1=diverged
    """
    R_i = 8314 / MW_i #[J/kgK]
    m_c_i = pc_i * Vol_chamber_i / (R_i * Tc_i)
    Dmdot_i = mdot_ox_i + mdot_fuel_i - mdot_throat_i
    dt = abs(m_c_i / Dmdot_i) / 2.5

    m_c = m_c_i + Dmdot_i * dt

    pc = m_c * R_i * Tc_i / Vol_chamber_i
    err = 1
    flag = 0
    num_it = 0
    maxit = 1000
    while (err > 1e-6) & (num_it < maxit):
        num_it += 1
        (p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, eps_out, cs,
         CF_vac, CF, Ivac, Is, flag_performance) = (
            performance.calculate_performance(Ainj, Aport_i, Ab_i, eps, ptank, Ttank, pc, CD,
                          a, n, rho_fuel, oxidizer, fuel, pamb, gamma0))
        if flag_performance==1:
            num_it = maxit
        else:
            Vol_chamber = Vol_chamber_i + r * Ab_i
            R = 8314 / MW
            err = abs(pc - m_c * R * Tc / Vol_chamber) / abs(pc)
            pc = m_c * R * Tc / Vol_chamber

    if num_it == maxit:
        flag = 1

    return pc, flag, dt

def update_chamberpressure_nocombustion(pc_i, Tc_i, MW_i, mdot_ox_i, mdot_fuel_i, mdot_throat_i,
                           Vol_chamber_i):
    """
    This function updates the chamber pressure with a finite difference of the mass conservation equation.
    dm/dt = mdot_ox + mdot_fuel - (pc * At / c*)
    with
    m = pc * V / (R * Tc) [Ideal gas state equation]
    dm/dt = d(pc/(R * Tc))/dt * V + pc/(R * Tc) * dV/dt
    and
    dV/dt = r * Ab

    :param pc_i: Chamber pressure previous step [Pa]
    :param Tc_i: Chamber temperature previous step [K]
    :param MW_i: Molecular weight previous step [kg/kmol]
    :param Ab_i: Burning area previous step [m^2]
    :param mdot_ox_i: Oxidizer mass flow previous step [kg/s]
    :param mdot_fuel_i: Fuel mass flow previous step [kg/s]
    :param mdot_throat_i: Mass flow through throat Area [kg/s]
    :param Vol_chamber_i: Volume of the chamber previous step [m^3]
    :param dt: time step [s]
    :param Ainj: Injection area [m^2]
    :param Aport_i: Port area previous step[m^2]
    :param eps: expansion ratio
    :param ptank: tank pressure [Pa]
    :param Ttank: Tank temperature [K]
    :param CD: Discharge coefficient
    :param a: regression rate coefficient r = a * Gox**n
    :param n: regression rate exponent r = a * Gox**n
    :param rho_fuel: fuel density [kg/m^3]
    :param oxidizer: oxidizer properties (Coolprop & CEA)
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
    :param pamb: ambient pressure [Pa]
    :param gamma0: specific heat ratio initial guess
    :return pc: Chamber pressure [Pa]
            flag: 0=converged, 1=diverged
    """
    R_i = 8314 / MW_i #[J/kgK]
    m_c_i = pc_i * Vol_chamber_i / (R_i * Tc_i)
    Dmdot_i = mdot_ox_i + mdot_fuel_i - mdot_throat_i

    dt = abs(m_c_i / Dmdot_i) / 2.5
    m_c = m_c_i + Dmdot_i * dt

    pc = m_c * R_i * Tc_i / Vol_chamber_i

    return pc, dt

if __name__ == '__main__':
    pc_i = 1e5
    pamb = 1e5
    Tamb = 300

    ptank = 50e5
    Ttank = 300

    Dinj = 0.001
    Ainj = 0.25 * np.pi * Dinj**2
    CD = 0.8

    Dp = 0.01
    Lc = 0.1
    Ab_i = np.pi * Dp * Lc
    Aport = 0.25 * np.pi * Dp**2
    Vol_chamber_i = Aport * Lc

    Dt = Dp / 1.5
    At = 0.25 * np.pi * Dt**2

    a = 0.17e-3
    n = 0.5
    rho_fuel = 850  # [kg/m^3]
    oxidizer = {"OxidizerCP": "NitrousOxide",
                "OxidizerCEA": "N2O",
                "Weight fraction": "100",  # Multi-fluid Ox injector not available
                "Exploded Formula": "",
                "Temperature [K]": "",
                "Specific Enthalpy [kj/mol]": ""
                }
    fuel = {"Fuels": ["paraffin"],
            "Weight fraction": ["100"],
            "Exploded Formula": ["C 73 H 124"],
            "Temperature [K]": [float(533)],
            "Specific Enthalpy [kj/mol]": [-1860.6]
            }

    eps = 3

    (p_inj, mdot_ox_i, mdot_fuel_i, mdot, Gox, r_i, MR, Tc_i, MW_i, gamma, eps, cs,
     CF_vac, CF, Ivac, Is, flag_performance) = (
        performance.calculate_performance(Ainj, Aport, Ab_i, eps, ptank, Ttank, pc_i, CD,
                                          a, n, rho_fuel, oxidizer, fuel, pamb))
    mdot_throat_i = injection.gas_injection_custom(pc_i, pamb, Tc_i, CD, gamma, MW_i) * At

    pc, flag, dt = update_chamberpressure(pc_i, Tc_i, MW_i, Ab_i, mdot_ox_i, mdot_fuel_i,
                                      mdot_throat_i, Vol_chamber_i, Ainj, Aport,
                           eps, ptank, Ttank, CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma)

    print("mdot ox [kg/s]= ",mdot_ox_i)
    print("mdot fuel [kg/s]= ", mdot_fuel_i)
    print("mdot throat [kg/s]= ", mdot_throat_i)
    print("dt = ", dt)
    print("pc [Pa]= ", pc)
    print("flag = ", flag)
# End of file