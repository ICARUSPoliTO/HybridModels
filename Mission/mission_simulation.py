"""
This file provides the function to simulate a mission of a hybrid rocket engine.
"""
from math import isclose

import numpy as np
import matplotlib.pyplot as plt
import Performance.performance_singlepoint as performance
import Injection.PyInjection as injection


def update_Temperature_and_gasproperties(pc, Tc, MW, gamma, Tc_CEA, MW_CEA, gamma_CEA,
                                         mdot_ox, mdot_fuel, mdot_throat, Vol_chamber):
    """
    This updates the properties of the gas in the chamber.
    The calculation is used to get the needed timestep for geometry and tank update.
    :param pc_i: Chamber pressure [Pa]
    :param Tc_i: Chamber temperature [K]
    :param MW_i: Molecular weight [kg/kmol]
    :param gamma_i: Specific heat ratio
    :param Tc_CEA: Chamber temperature from CEA [K]
    :param MW_CEA: Molecular weight from CEA [K]
    :param gamma_CEA: Specific heat ratio from CEA
    :param mdot_ox_i: Oxidizer mass flow [kg/s]
    :param mdot_fuel_i: Fuel mass flow [kg/s]
    :param mdot_throat_i: Throat mass flow [kg/s]
    :param Vol_chamber_i: Chamber volume [m^3]
    :return: Tc_actual, MW_actual, dt
    """
    R = 8314 / MW #[J/kgK]
    cp = gamma * R / (gamma - 1)
    m_c_i = pc * Vol_chamber / (R * Tc)

    Dmdot_in = mdot_ox + mdot_fuel
    Dmdot_out = mdot_throat
    Dmdot = Dmdot_in - Dmdot_out

    dt = abs(m_c_i / max(Dmdot_in, Dmdot_out)) / 2.5

    dmc_in = Dmdot_in * dt
    dmc_out = Dmdot_out * dt
    dmc = Dmdot * dt
    m_c = m_c_i + dmc

    R_CEA = 8314 / MW_CEA
    cp_CEA = gamma_CEA * R_CEA / (gamma_CEA - 1)
    Tc_actual =  ((cp / cp_CEA) * (m_c_i - dmc_out) * Tc + dmc_in * Tc_CEA) / m_c
    MW_actual = m_c / (((m_c_i - dmc_out) / MW) + (dmc_in / MW_CEA))
    #gamma_actual = ADD!!!

    return Tc_actual, MW_actual, 'gamma_actual', dt


def update_chamberpressure(pc_i, Tc_i, MW_i, mdot_ox_i, mdot_fuel_i, At, pamb=0.0, gamma0=1.3):
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
    :param mdot_ox_i: Oxidizer mass flow previous step [kg/s]
    :param mdot_fuel_i: Fuel mass flow previous step [kg/s]
    :param pamb: ambient pressure [Pa]
    :param gamma0: specific heat ratio initial guess or previous step
    :return pc: Chamber pressure [Pa]
            flag: 0=converged, 1=diverged,
            dt: time step [s]
    """

    mdot_in = mdot_ox_i + mdot_fuel_i #[kg/s]
    dpc = 0 # [Pa]

    pc = pc_i # [Pa]
    fmpc = 1
    maxit = 100
    n_it = 0
    flag = 0
    while (abs(fmpc) > 1e-6) & (n_it < maxit):
        n_it += 1
        mdot_out = injection.gas_injection_custom(pc, pamb, Tc_i, 1, gamma0, MW_i) * At
        fmpc = mdot_out - mdot_in

        dfmpc = fmpc
        while np.isclose(dfmpc, fmpc, rtol=1e-12) & (dpc < 10):
            dpc += 1
            dmdot_out = injection.gas_injection_custom((pc+dpc), pamb, Tc_i, 1, gamma0, MW_i) * At
            dfmpc = dmdot_out - mdot_in

        dF = (dfmpc - fmpc) / dpc

        if abs(dF) < 1e-12:
            print('dfmpc = ', dfmpc)
            print('fmpc = ', fmpc)
            break

        pc = pc - (fmpc / dF)

        dpc = 0


    if n_it == maxit:
        flag = 1

    return pc, flag


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
    dt = 1e-1

    pc_out = [pc]
    Tc_out = [Tc]
    MW_out = [MW]
    dt_out = [dt]
    mdot_ox_out = [mdot_ox]
    mdot_throat_out = [mdot_throat]
    mdot_fuel_out = [mdot_fuel]

    print('n_it = ', n_it)
    print('flag = ',flag)
    print('Pressure variation = ',dpc)

    while (flag == 0) & (dpc > 1e-6) & (dt_out[-1] < 10):
        n_it += 1
        pc_old = pc

        pc, flag = update_chamberpressure(pc, Tc, MW, mdot_ox, mdot_fuel, At, pamb, gamma)

        dpc = abs(pc - pc_old) / abs(pc_old)

        mdot_throat = injection.gas_injection_custom(pc, pamb, Tc, CD, gamma, MW) * At

        (p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc_CEA, MW_CEA, gamma_CEA, eps, cs,
         CF_vac, CF, Ivac, Is, flag_performance) = (
            performance.calculate_performance(Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD,
                                              a, n, rho_fuel, oxidizer, fuel, pamb))

        Tc, MW, gamma, dt = update_Temperature_and_gasproperties(pc, Tc, MW, gamma, Tc_CEA, MW_CEA, gamma_CEA,
                                             mdot_ox, mdot_fuel, mdot_throat, Vol_chamber)

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

    pc_mask = np.where(np.asarray(pc_out) > 35e5)
    pc_check = np.asarray(pc_out)[pc_mask]
    print('Average pc = ', np.average(pc_check))
    print('Maximum pc = ', np.max(pc_check))
    print('Minimum pc = ', np.min(pc_check))

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