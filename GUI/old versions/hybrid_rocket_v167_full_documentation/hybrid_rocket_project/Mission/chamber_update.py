"""
This file provides the function to update the chamber pressure of a hybrid rocket engine.
"""
from math import isclose

import numpy as np
import matplotlib.pyplot as plt
import Performance.performance_singlepoint as performance
import Injection.PyInjection as injection

def find_dt(Tc, MW, gamma, Tc_CEA, MW_CEA, gamma_CEA, m_c_i, Dmdot_in, Dmdot_out, tol=1e-3):

    R = 8314 / MW  # [J/kgK]
    cp = gamma * R / (gamma - 1)
    R_CEA = 8314 / MW_CEA
    cp_CEA = gamma_CEA * R_CEA / (gamma_CEA - 1)

    KC = abs((cp_CEA / cp) - 1)
    KT = abs((cp_CEA * Tc_CEA / (cp * Tc)) - 1)
    KM = abs((MW / MW_CEA) - 1)
    KG = (cp * MW -  8314)/ cp * MW

    tol_alpha = tol
    tol_beta = tol
    tol_delta = tol
    #tol_epsilon = tol
    tol_zita = tol

    dt_mass = tol_zita * m_c_i / (Dmdot_in - Dmdot_out)
    dt_alpha = m_c_i / ( (KC - tol_alpha) * Dmdot_in / tol_alpha + Dmdot_out)
    dt_beta = m_c_i / ( (KT - tol_beta) * Dmdot_in / tol_beta + Dmdot_out)
    dt_delta = m_c_i / ( (KM - tol_delta) * Dmdot_in / tol_delta + Dmdot_out)
    #dt_epsilon = m_c_i / ( ((KC - KM) / ( (KG / tol_epsilon) - 1 + 8314) + KM + 1) * Dmdot_in + Dmdot_out)

    dt = min(abs(dt_mass), abs(dt_alpha), abs(dt_beta), abs(dt_delta))

    return dt

def update_Temperature_and_gasproperties(pc, Tc, MW, gamma, Tc_CEA, MW_CEA, gamma_CEA,
                                         mdot_ox, mdot_fuel, mdot_throat, Vol_chamber, tol=1e-3):
    """
    This updates the properties of the gas in the chamber.
    The calculation is used to get the needed timestep for geometry and tank update.
    :param pc: Chamber pressure [Pa]
    :param Tc: Chamber temperature [K]
    :param MW: Molecular weight [kg/kmol]
    :param gamma: Specific heat ratio
    :param Tc_CEA: Chamber temperature from CEA [K]
    :param MW_CEA: Molecular weight from CEA [K]
    :param gamma_CEA: Specific heat ratio from CEA
    :param mdot_ox: Oxidizer mass flow [kg/s]
    :param mdot_fuel: Fuel mass flow [kg/s]
    :param mdot_throat: Throat mass flow [kg/s]
    :param Vol_chamber: Chamber volume [m^3]
    :return: Tc_actual, MW_actual, gamma_actual, m_c, dt
    """
    R = 8314 / MW #[J/kgK]
    cp = gamma * R / (gamma - 1)
    m_c_i = pc * Vol_chamber / (R * Tc)

    Dmdot_in = mdot_ox + mdot_fuel
    Dmdot_out = mdot_throat
    Dmdot = Dmdot_in - Dmdot_out

    #dt = abs(m_c_i / max(Dmdot_in, Dmdot_out))
    dt = find_dt(Tc, MW, gamma, Tc_CEA, MW_CEA, gamma_CEA, m_c_i, Dmdot_in, Dmdot_out, tol)

    dmc_in = Dmdot_in * dt
    dmc_out = Dmdot_out * dt
    dmc = Dmdot * dt
    m_c = m_c_i + dmc

    R_CEA = 8314 / MW_CEA
    cp_CEA = gamma_CEA * R_CEA / (gamma_CEA - 1)
    cp_actual = (cp * (m_c_i - dmc_out) + cp_CEA * dmc_in) / m_c
    #cp_actual = cp_CEA
    Tc_actual =  (cp* (m_c_i - dmc_out) * Tc + cp_CEA * dmc_in * Tc_CEA) / (cp_actual * m_c)
    MW_actual = m_c / (((m_c_i - dmc_out) / MW) + (dmc_in / MW_CEA))
    R_actual = 8314 / MW_actual
    gamma_actual = (cp_actual / R_actual) / ( (cp_actual / R_actual) - 1)
    #gamma_actual = gamma
    #pc_fake = m_c * R_actual * Tc_actual / Vol_chamber
    #print("pc_fake = ", pc_fake)

    return Tc_actual, MW_actual, gamma_actual, m_c, dt

def update_chamberpressure(m_c, Tc, MW, Vol_chamber):
    """
    Function to update chamber pressure after every step.
    :param m_c: Chamber mass [kg]
    :param Tc: Chamber temperature [K]
    :param MW: Gas molecular weight [kg/kmol]
    :param Vol_chamber: Chamber volume [m^3]
    :return: pc: Chamber pressure [Pa]
    """
    R = 8314 / MW
    pc = m_c * R * Tc / Vol_chamber
    return pc

if __name__ == '__main__':
    pc = 1e5
    Tc = 288
    pamb = 1e5
    Tamb = 288
    MW = 29
    gamma = 1.4

    ptank = 50e5
    Ttank = 288

    Dinj = 0.001
    Ainj = 4 * 0.25 * np.pi * Dinj**2
    CD = 0.8

    Dp = 0.01
    Lc = 0.3
    Ab = np.pi * Dp * Lc
    Aport = 0.25 * np.pi * Dp**2
    Vol_chamber = Aport * Lc

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

    eps = 6

    """
    (p_inj, mdot_ox_i, mdot_fuel_i, mdot, Gox, r_i, MR, Tc_i, MW_i, gamma, eps, cs,
     CF_vac, CF, Ivac, Is, flag_performance) = (
        performance.calculate_performance(Ainj, Aport, Ab_i, eps, ptank, Ttank, pc_i, CD,
                                          a, n, rho_fuel, oxidizer, fuel, pamb))
    """
    mdot_throat = 0
    mdot_ox = injection.massflow(ptank, pc, Ttank, CD, oxidizer["OxidizerCP"]) * Ainj
    mdot_fuel = rho_fuel * Ab * a * (mdot_ox / Aport)**n
    flag = 0
    dpc = 100
    n_it = 0

    pc_out = [pc]
    Tc_out = [Tc]
    MW_out = [MW]
    dt_out = [0]
    mdot_ox_out = [mdot_ox]
    mdot_throat_out = [mdot_throat]
    mdot_fuel_out = [mdot_fuel]

    print('n_it = ', n_it)
    print('flag = ',flag)
    print('Pressure variation = ',dpc)
    while (flag == 0) & (dpc > 1e-12) & (dt_out[-1] < 10):
        n_it += 1
        pc_old = pc

        (p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc_CEA, MW_CEA, gamma_CEA, eps, cs,
         CF_vac, CF, Ivac, Is, flag_performance) = (
            performance.calculate_performance(Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD,
                                              a, n, rho_fuel, oxidizer, fuel, pamb, gamma))
        if flag_performance == 1:
            flag = 1
            continue

        done = False
        tol = 1e-3

        Tc, MW, gamma, m_c, dt = update_Temperature_and_gasproperties(pc, Tc, MW, gamma, Tc_CEA, MW_CEA, gamma_CEA,
                                             mdot_ox, mdot_fuel, mdot_throat, Vol_chamber, tol)
        #print("dt = ", dt)
        #pc, flag = update_chamberpressure(pc, Tc, MW, mdot_ox, mdot_fuel, At, pamb, gamma)
        pc = update_chamberpressure_v2(m_c, Tc, MW, Vol_chamber)
        #print("pc = ", pc)

        dpc = abs(pc - pc_old) / abs(pc_old)
        mdot_throat = injection.gas_injection_custom(pc, pamb, Tc, CD, gamma, MW) * At

        pc_out.append(pc)
        Tc_out.append(Tc)
        MW_out.append(MW)
        dt_out.append(dt_out[-1] + dt)
        mdot_ox_out.append(mdot_ox)
        mdot_throat_out.append(mdot_throat)
        mdot_fuel_out.append(mdot_fuel)

    print('n_it = ', n_it)
    print('flag = ', flag)
    print('Pressure variation = ',dpc)
    print(dt_out[-1])
    """
    pc_mask = np.where(np.asarray(pc_out) > 35e5)
    pc_check = np.asarray(pc_out)[pc_mask]
    print('Average pc = ', np.average(pc_check))
    print('Maximum pc = ', np.max(pc_check))
    print('Minimum pc = ', np.min(pc_check))
    """

    if flag == 1:
        print(pc)
        print(Tc)

    plt.figure()
    plt.plot(dt_out, mdot_ox_out, label="Oxidizer")
    plt.plot(dt_out, mdot_throat_out, label="Throat")
    plt.plot(dt_out, mdot_fuel_out, label="Fuel")
    plt.legend()
    plt.xlabel("Time [s]")

    plt.figure()
    plt.plot(dt_out, pc_out, label="Chamber pressure")
    plt.legend()
    plt.xlabel("Time [s]")

    plt.figure()
    plt.plot(dt_out, Tc_out, label="Chamber temperature")
    plt.legend()
    plt.xlabel("Time [s]")

    plt.show()
# End of file