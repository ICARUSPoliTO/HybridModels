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
    :param gamma0: specific heat ratio initial guess or previous step
    :return pc: Chamber pressure [Pa]
            flag: 0=converged, 1=diverged,
            dt: time step [s]
    """
    R_i = 8314 / MW_i #[J/kgK]
    cp_i = gamma0 * R_i / (gamma0 - 1)
    m_c_i = pc_i * Vol_chamber_i / (R_i * Tc_i)

    Dmdot_in_i = mdot_ox_i + mdot_fuel_i
    Dmdot_out_i = mdot_throat_i
    Dmdot_i = Dmdot_in_i - Dmdot_out_i

    dt = abs(m_c_i / max(Dmdot_in_i, Dmdot_out_i)) / 2.5


    dmc_in = Dmdot_in_i * dt
    dmc_out = Dmdot_out_i * dt
    dmc = Dmdot_i * dt
    m_c = m_c_i + dmc

    pc = m_c * R_i * Tc_i / Vol_chamber_i

    Tc_actual = Tc_i
    MW_actual = MW_i
    err = 1
    flag = 0
    num_it = 0
    maxit = 1000

    if abs(Dmdot_i) < 1e-12:
        num_it = maxit

    while (err > 1e-6) & (num_it < maxit):
        num_it += 1
        (p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, eps_out, cs,
         CF_vac, CF, Ivac, Is, flag_performance) = (
            performance.calculate_performance(Ainj, Aport_i, Ab_i, eps, ptank, Ttank, pc, CD,
                          a, n, rho_fuel, oxidizer, fuel, pamb, gamma0))
        if flag_performance==1:
            num_it = maxit
        else:
            R = 8314 / MW
            cp = gamma * R / (gamma - 1)
            Tc_actual =  ((cp_i / cp) * (m_c_i - dmc_out) * Tc_i + dmc_in * Tc) / m_c
            MW_actual = m_c / (((m_c_i - dmc_out) / MW_i) + (dmc_in / MW))
            R_actual = 8314 / MW_actual

            Vol_chamber = Vol_chamber_i + r * Ab_i

            pc_old = pc

            # pc = m_c * R_actual * Tc_actual / Vol_chamber
            # pc = m_c * R * Tc_actual / Vol_chamber
            pc = m_c * R_actual * Tc / Vol_chamber
            # pc = m_c * R * Tc / Vol_chamber

            err = abs(pc_old - pc) / abs(pc_old)

    if num_it == maxit:
        flag = 1

    return pc, flag, dt, Tc_actual, MW_actual



def update_chamberpressure_nocombustion(pc_i, Tc_i, MW_i, mdot_ox_i, mdot_throat_i,
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
    :param mdot_ox_i: Oxidizer mass flow previous step [kg/s]
    :param mdot_throat_i: Mass flow through throat Area [kg/s]
    :param Vol_chamber_i: Volume of the chamber previous step [m^3]
    :return pc: Chamber pressure [Pa]
            flag: 0=converged, 1=diverged,
            dt: time step [s]
    """
    R_i = 8314 / MW_i #[J/kgK]
    m_c_i = pc_i * Vol_chamber_i / (R_i * Tc_i)
    Dmdot_i = mdot_ox_i - mdot_throat_i

    dt = abs(m_c_i / Dmdot_i) / 2.5
    m_c = m_c_i + Dmdot_i * dt

    pc = m_c * R_i * Tc_i / Vol_chamber_i

    return pc, dt

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
    print('dpc = ',dpc)

    while (flag == 0) & (dpc > 1e-6):
        n_it += 1
        pc_old = pc
        pc, flag, dt, Tc, MW = update_chamberpressure(pc, Tc, MW, Ab, mdot_ox, mdot_fuel,
                                          mdot_throat, Vol_chamber_i, Ainj, Aport,
                               eps, ptank, Ttank, CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma)

        dpc = abs(pc - pc_old) / abs(pc_old)

        mdot_throat = injection.gas_injection_custom(pc, pamb, Tc, CD, gamma, MW) * At
        mdot_ox = injection.massflow(ptank, pc, Ttank, CD, oxidizer["OxidizerCP"]) * Ainj
        mdot_fuel = rho_fuel * Ab * a * (mdot_ox / Aport) ** n

        pc_out.append(pc)
        Tc_out.append(Tc)
        MW_out.append(MW)
        dt_out.append(dt_out[-1] + dt)
        mdot_ox_out.append(mdot_ox)
        mdot_throat_out.append(mdot_throat)
        mdot_fuel_out.append(mdot_fuel)

    print('n_it = ', n_it)
    print('flag = ', flag)
    print('dpc = ', dpc)

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