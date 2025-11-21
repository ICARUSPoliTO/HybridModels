"""
This file provides the function to simulate a mission of an hybrid rocket engine.
"""
import numpy as np
import matplotlib.pyplot as plt
import Performance.performance_singlepoint as performance

def update_chamberpressure(pc_i, Tc_i, MW_i, r_i, Ab_i, mdot_ox_i, mdot_fuel_i, At, cs_i, dt, Ainj, Aport,
                           eps, ptank, Ttank, CD, a, n, rho_fuel, oxidizer, fuel, pamb=0.0, gamma0=1.3):
    """
    This function updates the chamber pressure with a finite difference of the mass conservation equation.
    dm/dt = mdot_ox + mdot_fuel - (pc * At / c*)
    with
    m = pc * V / (R * Tc) [Ideal gas state equation]
    dm/dt = d(pc/(R * Tc))/dt + pc/(R * Tc) * dV/dt
    and
    dV/dt = r * Ab

    :param pc_i: Chamber pressure previous step [Pa]
    :param Tc_i: Chamber temperature previous step [K]
    :param MW_i: Molecular weight previous step [kg/kmol]
    :param r_i: Regression rate previous step [m/s]
    :param Ab_i: Burning area previous step [m^2]
    :param mdot_ox_i: Oxidizer mass flow previous step [kg/s]
    :param mdot_fuel_i: Fuel mass flow previous step [kg/s]
    :param At: Throat Area [m^2]
    :param cs_i: Characteristic velocity previous step [m/s]
    :param dt: time step [s]
    :param Ainj: Injection area [m^2]
    :param Aport: Port area [m^2]
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
    :return:
    """
    R_i = 8314 / MW_i #[J/kgK]
    rho_c_i = pc_i / (R_i * Tc_i)
    Dmdot_i = mdot_ox_i + mdot_fuel_i - (pc_i * At / cs_i)

    rho_c = rho_c_i * (1 - r_i * Ab_i) + Dmdot_i * dt

    pc = rho_c * R_i * Tc_i
    err = 1
    num_it = 0
    maxit = 1000
    while (err > 1e-6) & (num_it < maxit):
        num_it += 1
        (p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, eps_out, cs,
         CF_vac, CF, Ivac, Is, flag_performance) = (
            performance.calculate_performance(Ainj, Aport, Ab_i, eps, ptank, Ttank, pc, CD,
                          a, n, rho_fuel, oxidizer, fuel, pamb, gamma0))
        # add flag response!!!!!!
        R = 8314 / MW
        err = abs(pc - rho_c * R * Tc) / abs(pc)
        pc = rho_c * R * Tc

# End of file