"""
This file provides the function to simulate a mission of a hybrid rocket engine.
"""

import numpy as np
import matplotlib.pyplot as plt
import CoolProp.CoolProp as cp
import Injection.PyInjection as inj
import Line_losses.linelosses as loss
import Geometry.geometry_update as geom
import Geometry.geometry_calculation as geomcalc
import Performance.performance_singlepoint as perf
import Tank.tank_update as tank
import Mission.chamber_update as chamber

def get_starting_conditions(pamb, Tamb, rho_fuel,
                            x, y, Lc,
                            D_chamber, Vol_prechamber, Vol_postchamber,
                            masses, volumes, pressures, temperatures,
                            oxidizer, pressurant=None,
                            pitch=0.0, circular=False, npointsperside=50, constant_pressure_tank=False):
    """
    Calculates the needed starting conditions.
    :param pamb: Ambient pressure [Pa]
    :param Tamb: Ambient temperature [K]
    :param rho_fuel: Fuel density [kg/m^3]
    :param x: x-coordinates [m]
    :param y: y-coordinates [m]
    :param Lc: Chamber length [m]
    :param D_chamber: Chamber diameter [m]
    :param Vol_prechamber: Prechamber volume [m^3]
    :param Vol_postchamber: Postchamber volume [m^3]
    :param masses: masses dictionary (depends on type of tank)
    :param volumes: volumes dictionary (depends on type of chamber)
    :param pressures: pressures dictionary (depends on type of pressure)
    :param temperatures: temperatures dictionary (depends on type of tank)
    :param oxidizer : oxidizer properties (Coolprop & CEA)
        {"OxidizerCP" : "", <--Name for CoolProp
        "OxidizerCEA" : "", <--Name for CEA
        "Weight fraction" : "100", # Multi-fluid Ox injector not available
        "Exploded Formula": "",
        "Temperature [K]" : "",
        "Specific Enthalpy [kj/mol]" : ""
        }
    :param pressurant: pressurant CoolProp name
    :param pitch: Grain pitch for helix [m]
    :param circular: Bool (False: connect grain points with segments, True: connect grain points with arcs)
    :param npointsperside: Points between every point to fill sides of grain geometry
    :param constant_pressure_tank: Bool (False: Self-pressurising/Full gas tank, True: Pressurised tank)
    :return: pc: Chamber pressure [Pa],
             mdot_throat: mass flow through the nozzle [kg/s],
             Tc: Chamber temperature [K],
             MW: Molecular weight [kg/kmol],
             gamma: specific heat ratio,
             ptank: tank pressure,
             Ttank: tank temperature [K],
             mL: Liquid mass in the tank (0.0 if full gas tank) [kg],
             m_fuel: Fuel mass [kg]
             entropies: entropies dictionary (depends on type of tank),
             masses: masses dictionary (depends on type of tank),
             pressures: pressures dictionary (depends on type of pressure),
             temperatures: temperatures dictionary (depends on type of tank),
             Ap: Port Area [m^2],
             Ab: Burning Area [m^2],
             Vol_chamber: Chamber volume [m^3]
    """
    pc = pamb
    mdot_throat = 0.0
    Tc = Tamb

    MW = cp.PropsSI('MOLARMASS','Air') * 1e3
    gamma = (cp.PropsSI('CPMASS', 'T', Tc, 'P', pc, 'Air')
             / cp.PropsSI('CVMASS', 'T', Tc, 'P', pc, 'Air'))

    ptank, Ttank, mL, entropies, masses, pressures, temperatures = (
        tank.start_conditions(masses, volumes, pressures, temperatures, oxidizer, pressurant, constant_pressure_tank))

    Ap, Ab, Vol_chamber = geomcalc.fill_and_calculate_surfaces_and_volume(x, y, Lc, npointsperside, circular, pitch,
                                                                          Vol_prechamber, Vol_postchamber)

    m_fuel = geomcalc.calculate_fuel_mass(Ap, Lc, D_chamber, rho_fuel)

    return (pc, mdot_throat, Tc, MW, gamma,
            ptank, Ttank, mL, m_fuel,
            entropies, masses, pressures, temperatures,
            Ap, Ab, Vol_chamber)

def run_one_step_no_burn(pc, mdot_throat, Tc, MW, gamma, rho_fuel, pamb, ptank, Ttank, eps,
                 Ainj, At, Ap, Ab, Lc, Vol_chamber, D_chamber,
                 x, y,
                 entropies, masses, volumes, pressures, temperatures, utilities,
                 CD,
                 oxidizer, pressurant=None,
                 rend_CF = 1.0, constant_pressure_tank=False, tol=1e-3):
    """
        This function runs one step of oxidizer injection without burn,
        returning performances and input for the next step.
        :param pc: Chamber pressure [Pa]
        :param mdot_throat: Mass flow though nozzle [kg/s]
        :param Tc: Chamber Temperature [K]
        :param MW: Molecular Weight [kg/kmol]
        :param gamma: Specific heat ratio
        :param rho_fuel: Fuel density [kg/m^3]
        :param pamb: Ambient pressure [Pa]
        :param ptank: Tank pressure [Pa]
        :param Ttank: Tank temperature [K]
        :param eps: Expansion ratio
        :param Ainj: Injection Area [m^2]
        :param At: Throat Area [m^2]
        :param Ap: Port Area [m^2]
        :param Ab: Burning Area [m^2]
        :param Lc: Chamber Length [m]
        :param Vol_chamber: Chamber Volume [m^3]
        :param D_chamber: Chamber internal diameter [m]
        :param x: x-coordinates for the grain port [m]
        :param y: y-coordinates for the grain port [m]
        :param entropies: entropies dict (depends on type of tank)
        :param masses: masses dict (depends on type of tank)
        :param volumes: volumes dict (depends on type of tank)
        :param pressures: pressures dict (depends on type of tank)
        :param temperatures: temperatures dict (depends on type of tank)
        :param utilities: utilities dict (depends on type of tank)
        :param CD: Discharge coefficient for injector massflow
        :param oxidizer : oxidizer properties (Coolprop & CEA)
            {"OxidizerCP" : "", <--Name for CoolProp
            "OxidizerCEA" : "", <--Name for CEA
            "Weight fraction" : "100", # Multi-fluid Ox injector not available
            "Exploded Formula": "",
            "Temperature [K]" : "",
            "Specific Enthalpy [kj/mol]" : ""
            }
        :param pressurant: Pressurant CoolProp name
        :param rend_CF: Thrust coefficient efficiecy
        :param constant_pressure_tank: Bool (False: Self-pressurising/Full gas tank, True: Pressurised tank)
        :param tol: Time-step evaluation tolerance
        :return: pc: Chamber pressure [Pa],
                 mdot_throat: Mass flow through the nozzle [kg/s],
                 Thrust: thrust [N],
                 dt: timestep [s],
                 Tc: Chamber temperature [K],
                 MW: Molecular weight [kg/kmol],
                 gamma: specific heat ratio,
                 ptank: tank pressure [Pa],
                 Ttank: tank temperature [K],
                 eps: expansion ratio,
                 mL: Liquid mass in the tank (0.0 if full gas) [kg],
                 m_fuel: Fuel mass [kg],
                 Ap: Port Area [m^2],
                 Ab: Burning Area [m^2],
                 Vol_chamber: Chamber Volume [m^3],
                 x: x-coordinates [m],
                 y: y-coordinates [m],
                 entropies: entropies dict (depends on type of tank),
                 masses: masses dict (depends on type of tank),
                 pressures: pressures dict (depends on type of tank),
                 temperatures: temperatures dict (depends on type of tank),
                 performances: performances dict
                 """

    if eps == "adapt":
        eps = perf.ER(gamma, pamb, pc)
    else:
        eps = eps

    # Calculate injection pressure after losses. May require iterations with Oxidizer injection
    p_inj = ptank - loss.linelosses()  # add input for line losses here and in the inputs of the function

    # Calculate injection mass flow
    mdot_ox = inj.massflow(p_inj, pc, Ttank, CD, oxidizer['OxidizerCP'])
    mdot_ox = mdot_ox * Ainj
    mdot_fuel = 0.0
    mdot = mdot_ox + mdot_fuel
    Tc_CEA = Ttank
    MW_CEA = cp.PropsSI('MOLARMASS', oxidizer['OxidizerCP']) * 1e3
    gamma_CEA = (cp.PropsSI('CPMASS', 'T', Tc, 'P', pc, oxidizer['OxidizerCP'])
             / cp.PropsSI('CVMASS', 'T', Tc, 'P', pc, oxidizer['OxidizerCP']))

    Tc, MW, gamma, m_c, dt = chamber.update_Temperature_and_gasproperties(pc, Tc, MW, gamma, Tc_CEA, MW_CEA, gamma_CEA,
                                                                          mdot_ox, mdot_fuel, mdot_throat, Vol_chamber,
                                                                          tol)

    pc = chamber.update_chamberpressure(m_c, Tc, MW, Vol_chamber)
    mdot_throat = inj.gas_injection_custom(pc, pamb, Tc, 1, gamma, MW) * At

    ptank, Ttank, mL, entropies, masses, pressures, temperatures = tank.update_tank(mdot_ox, dt,
                                                                                    entropies, masses, volumes,
                                                                                    pressures, temperatures, utilities,
                                                                                    oxidizer, pressurant,
                                                                                    constant_pressure_tank)
    m_fuel = geomcalc.calculate_fuel_mass(Ap, Lc, D_chamber, rho_fuel)

    Me = 0
    feps = 1
    n_eps = 0
    maxit_eps = 100
    while (abs(feps) > 1e-12) & (n_eps < maxit_eps):
        gammone = np.sqrt(gamma * (2 / (gamma + 1)) ** ((gamma + 1) / (gamma - 1)))
        fMe = np.sqrt(gamma) * Me * (1 + 0.5 * (gamma - 1) * (Me ** 2)) ** (-0.5 * (gamma + 1) / (gamma - 1))

        feps = eps - (gammone / fMe)

        Me = gammone * Me / (fMe * eps)
        n_eps = n_eps + 1

    Te = Tc / (1 + 0.5 * (gamma - 1) * (Me ** 2))
    pe = pc / ((1 + 0.5 * (gamma - 1) * (Me ** 2)) ** (gamma / (gamma - 1)))
    R = 8314 / MW
    Ve = Me * np.sqrt(gamma * R * Te)

    Thrust = rend_CF * mdot_throat * Ve + (pe - pamb) * eps * At

    performances = {"pc": pc, "pinj": p_inj, "dt": dt, "Thrust": Thrust,
                    "mdot_ox": mdot_ox, "mdot_fuel": mdot_fuel, "mdot": mdot, "mdot_throat": mdot_throat,
                    "Tc": Tc, "MW": MW, "gamma": gamma,
                    "eps": eps,
                    "x": x, "y": y, "Ap": Ap, "Ab": Ab, "Vol_chamber": Vol_chamber,
                    "m_fuel": m_fuel, "mL": mL, "ptank": ptank, "Ttank": Ttank}

    return (pc, mdot_throat, Thrust, dt,
            Tc, MW, gamma, ptank, Ttank, eps,
            mL, m_fuel,
            Ap, Ab, Vol_chamber,
            x, y,
            entropies, masses, pressures, temperatures,
            performances)

def run_one_step(pc, mdot_throat, Tc, MW, gamma, a, n, rho_fuel, pamb, ptank, Ttank, eps,
                 Ainj, At, Ap, Ab, Lc, Vol_chamber, Vol_prechamber, Vol_postchamber, D_chamber,
                 x, y, z,
                 entropies, masses, volumes, pressures, temperatures, utilities,
                 CD,
                 oxidizer, fuel, pressurant=None,
                 rend_cstar = 1.0, rend_CF = 1.0,
                 pitch=0.0, circular=False, npointsperside=50, constant_pressure_tank=False, tol=1e-3):
    """
    This function runs one step of the mission, returning performances and input for the next step.
    :param pc: Chamber pressure [Pa]
    :param mdot_throat: Mass flow though nozzle [kg/s]
    :param Tc: Chamber Temperature [K]
    :param MW: Molecular Weight [kg/kmol]
    :param gamma: Specific heat ratio
    :param a: Regression rate coefficient r=a*Gox**n [m/s]
    :param n: Regression rate exponent r=a*Gox**n [m/s]
    :param rho_fuel: Fuel density [kg/m^3]
    :param pamb: Ambient pressure [Pa]
    :param ptank: Tank pressure [Pa]
    :param Ttank: Tank temperature [K]
    :param eps: Expansion ratio
    :param Ainj: Injection Area [m^2]
    :param At: Throat Area [m^2]
    :param Ap: Port Area [m^2]
    :param Ab: Burning Area [m^2]
    :param Lc: Chamber Length [m]
    :param Vol_chamber: Chamber Volume [m^3]
    :param Vol_prechamber: Prechamber Volume [m^3]
    :param Vol_postchamber: Postchamber Volume [m^3]
    :param D_chamber: Chamber internal diameter [m]
    :param x: x-coordinates for the grain port [m]
    :param y: y-coordinates for the grain port [m]
    :param z: axis direction for grain points (1: counterclockwise, 0: clockwise)
    :param entropies: entropies dict (depends on type of tank)
    :param masses: masses dict (depends on type of tank)
    :param volumes: volumes dict (depends on type of tank)
    :param pressures: pressures dict (depends on type of tank)
    :param temperatures: temperatures dict (depends on type of tank)
    :param utilities: utilities dict (depends on type of tank)
    :param CD: Discharge coefficient for injector massflow
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
    :param pressurant: Pressurant CoolProp name
    :param rend_cstar: c* efficiency
    :param rend_CF: CF efficiency
    :param pitch: Grain pitch for helix [m]
    :param circular: Bool (False: connect grain points with segments, True: connect grain points with arcs)
    :param npointsperside: Points between every point to fill sides of grain geometry
    :param constant_pressure_tank: Bool (False: Self-pressurising/Full gas tank, True: Pressurised tank)
    :param tol: Time-step evaluation tolerance
    :return: pc: Chamber pressure [Pa],
             mdot_throat: Mass flow through the nozzle [kg/s],
             Thrust: thrust [N],
             dt: timestep [s],
             Tc: Chamber temperature [K],
             MW: Molecular weight [kg/kmol],
             gamma: specific heat ratio,
             ptank: tank pressure [Pa],
             Ttank: tank temperature [K],
             eps: expansion ratio,
             mL: Liquid mass in the tank (0.0 if full gas) [kg],
             m_fuel: Fuel mass [kg],
             Ap: Port Area [m^2],
             Ab: Burning Area [m^2],
             Vol_chamber: Chamber Volume [m^3],
             x: x-coordinates [m],
             y: y-coordinates [m],
             entropies: entropies dict (depends on type of tank),
             masses: masses dict (depends on type of tank),
             pressures: pressures dict (depends on type of tank),
             temperatures: temperatures dict (depends on type of tank),
             performances: performances dict,
             flag: CEA flag
    """

    p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc_CEA, MW_CEA, gamma_CEA, eps, cstar, CFvac, CF, Ivac, Is, flag = (
        perf.calculate_performance(Ainj, Ap, Ab, eps, ptank, Ttank, pc, CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma))

    Tc, MW, gamma, m_c, dt = chamber.update_Temperature_and_gasproperties(pc, Tc, MW, gamma, Tc_CEA, MW_CEA, gamma_CEA,
                                                 mdot_ox, mdot_fuel, mdot_throat, Vol_chamber, tol)

    pc = chamber.update_chamberpressure(m_c, Tc, MW, Vol_chamber)
    mdot_throat = inj.gas_injection_custom(pc, pamb, Tc, 1, gamma, MW) * At

    x, y = geom.burn_grain(x, y, z, r, dt, circular)
    Ap, Ab, Vol_chamber = geomcalc.fill_and_calculate_surfaces_and_volume(x, y, Lc, npointsperside, circular, pitch,
                                                                          Vol_prechamber, Vol_postchamber)
    m_fuel = geomcalc.calculate_fuel_mass(Ap, Lc, D_chamber, rho_fuel)

    ptank, Ttank, mL, entropies, masses, pressures, temperatures = tank.update_tank(mdot_ox, dt,
                                                                                    entropies, masses, volumes,
                                                                                    pressures, temperatures, utilities,
                                                                                    oxidizer, pressurant,
                                                                                    constant_pressure_tank)

    Thrust = rend_cstar * rend_CF * cstar * CF * mdot_throat

    performances = {"pc": pc, "pinj": p_inj, "dt": dt, "Thrust": Thrust,
                    "mdot_ox": mdot_ox, "mdot_fuel": mdot_fuel, "mdot": mdot, "mdot_throat": mdot_throat, "Gox": Gox,
                    "r": r, "MR": MR, "Tc_CEA": Tc_CEA, "MW_CEA": MW_CEA, "gamma_CEA": gamma_CEA,
                    "Tc": Tc, "MW": MW, "gamma": gamma,
                    "eps": eps, "cstar": cstar, "CFvac": CFvac, "CF": CF, "Ivac": Ivac, "Is": Is,
                    "x": x, "y": y, "Ap": Ap, "Ab": Ab, "Vol_chamber": Vol_chamber,
                    "m_fuel": m_fuel, "mL": mL, "ptank": ptank, "Ttank": Ttank,
                    "flag": flag}

    return (pc, mdot_throat, Thrust, dt,
            Tc, MW, gamma, ptank, Ttank, eps,
            mL, m_fuel,
            Ap, Ab, Vol_chamber,
            x, y,
            entropies, masses, pressures, temperatures,
            performances, flag)

def run_full_mission(burn_time, pamb, Tamb, a, n, rho_fuel,
                     eps, Ainj, At, Lc, D_chamber,
                     x, y, z,
                     Vol_prechamber, Vol_postchamber,
                     masses, volumes, pressures, temperatures, utilities,
                     CD,
                     oxidizer, fuel, pressurant=None,
                     rend_cstar = 1.1, rend_CF = 1.1,
                     pitch=0.0, circular=False, delay_time = 0.0, npointsperside=50, constant_pressure_tank=False,
                     tol=1e-3):
    """
    This functions runs the whole mission, until tank emptying.
    :param burn_time: Time for burning phase [s]
    :param pamb: Ambient pressure [Pa]
    :param Tamb: Ambient temperature [K]
    :param a: regression rate coefficient r=a*Gox**n
    :param n: regression rate coefficient r=a*Gox**n
    :param rho_fuel: Fuel density [kg/m^3]
    :param eps: Expansion ratio
    :param Ainj: Injection Area [m^2]
    :param At: Throat Area [m^2]
    :param Lc: Chamber Length [m]
    :param D_chamber: Chamber Diameter [m]
    :param x: x-coordinates for grain geometry [m]
    :param y: y-coordinates for grain geometry [m]
    :param z: axis for grain geometry (1: counter-clockwise, 0: clockwise)
    :param Vol_prechamber: Prechamber volume [m]
    :param Vol_postchamber: Postchamber volume [m]
    :param masses: Masses dictionaty (depends on type of tank)
    :param volumes: Volumes dictionaty (depends on type of tank)
    :param pressures: Pressures dictionaty (depends on type of tank)
    :param temperatures: Temperatures dictionaty (depends on type of tank)
    :param utilities: Utilities dictionaty (depends on type of tank)
    :param CD: Injector discharge coefficient
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
    :param pressurant: Pressurant CoolProp name
    :param rend_cstar: c* efficiency
    :param rend_CF: CF efficiency
    :param pitch: Grain geometry pitch [m]
    :param circular: Bool (False: connect grain points with segments, True: connect grain points with arcs)
    :param delay_time: Time to delay before ignition [s]
    :param npointsperside: Points between every point to fill sides of grain geometry
    :param constant_pressure_tank: Bool (False: Self-pressurising/Full gas tank, True: Pressurised tank)
    :param tol: Time-step evaluation tolerance
    :return:
    """
    (pc, mdot_throat, Tc, MW, gamma,
     ptank, Ttank, mL, m_fuel,
     entropies, masses, pressures, temperatures,
     Ap, Ab, Vol_chamber) = get_starting_conditions(pamb, Tamb, rho_fuel,
                            x, y, Lc,
                            D_chamber, Vol_prechamber, Vol_postchamber,
                            masses, volumes, pressures, temperatures,
                            oxidizer, pressurant,
                            pitch, circular, npointsperside, constant_pressure_tank)

    if mL == 0:
        full_gas_tank = True
    else:
        full_gas_tank = False

    time = [0]
    pc_out = [pc]

    conditions_no_burn = (mL > 0 or full_gas_tank) & (ptank > pc)

    conditions_burn = ((mL > 0 or full_gas_tank) & (ptank > pc) &
                  (m_fuel > 0) & (np.max(np.hypot(x, y)) < 0.5 * D_chamber))

    while conditions_no_burn & (time[-1] < delay_time):
        (pc, mdot_throat, Thrust, dt,
         Tc, MW, gamma, ptank, Ttank, eps,
         mL, m_fuel,
         Ap, Ab, Vol_chamber,
         x, y,
         entropies, masses, pressures, temperatures,
         performances) = run_one_step_no_burn(pc, mdot_throat, Tc, MW, gamma, rho_fuel, pamb, ptank, Ttank, eps,
                     Ainj, At, Ap, Ab, Lc, Vol_chamber, D_chamber,
                     x, y,
                     entropies, masses, volumes, pressures, temperatures, utilities,
                     CD,
                     oxidizer, pressurant,
                     rend_CF, constant_pressure_tank, tol)

        conditions_no_burn = (mL > 0 or full_gas_tank) & (ptank > pc)
        time.append(time[-1] + dt)
        pc_out.append(pc)

    while conditions_burn & (time[-1] < (burn_time + delay_time)):
        (pc, mdot_throat, Thrust, dt,
         Tc, MW, gamma, ptank, Ttank, eps,
         mL, m_fuel,
         Ap, Ab, Vol_chamber,
         x, y,
         entropies, masses, pressures, temperatures,
         performances, flag) = run_one_step(pc, mdot_throat, Tc, MW, gamma, a, n, rho_fuel, pamb, ptank, Ttank, eps,
                     Ainj, At, Ap, Ab, Lc, Vol_chamber, Vol_prechamber, Vol_postchamber, D_chamber,
                     x, y, z,
                     entropies, masses, volumes, pressures, temperatures, utilities,
                     CD,
                     oxidizer, fuel, pressurant,
                     rend_cstar, rend_CF,
                     pitch, circular, npointsperside, constant_pressure_tank, tol)

        conditions_burn = ((mL > 0 or full_gas_tank) & (ptank > pc) &
                           (m_fuel > 0) & (np.max(np.hypot(x, y)) < 0.5 * D_chamber))
        time.append(time[-1] + dt)
        pc_out.append(pc)

    while conditions_no_burn:
        (pc, mdot_throat, Thrust, dt,
         Tc, MW, gamma, ptank, Ttank, eps,
         mL, m_fuel,
         Ap, Ab, Vol_chamber,
         x, y,
         entropies, masses, pressures, temperatures,
         performances) = run_one_step_no_burn(pc, mdot_throat, Tc, MW, gamma, rho_fuel, pamb, ptank, Ttank, eps,
                     Ainj, At, Ap, Ab, Lc, Vol_chamber, D_chamber,
                     x, y,
                     entropies, masses, volumes, pressures, temperatures, utilities,
                     CD,
                     oxidizer, pressurant,
                     constant_pressure_tank, tol)

        conditions_no_burn = (mL > 0 or full_gas_tank) & (ptank > pc)
        time.append(time[-1] + dt)
        pc_out.append(pc)

    return time, pc_out

if __name__ == '__main__':

    burn_time = 5 #[s]
    pamb = 1.01325e5
    Tamb = 288
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
    Ainj = # [m^2]
    At = # [m^2]
    Lc = # [m]
    D_chamber = 0.1 # [m]

    x = np.array([]) # [m]
    y = np.array([0]) # [m]
    z = 1
    Vol_prechamber = 0
    Vol_postchamber = 0

    CD = 0.8
    pressurant = None
    rend_cstar = 0.85
    rend_CF = 0.8
    pitch = 0.0 # [m]
    circular = True
    delay_time = 0.5 # [s]
    npointsperside = 50
    constant_pressure_tank = False
    tol = 1e-3

    time, pc_out = run_full_mission(burn_time, pamb, Tamb, a, n, rho_fuel,
                     eps, Ainj, At, Lc, D_chamber,
                     x, y, z,
                     Vol_prechamber, Vol_postchamber,
                     masses, volumes, pressures, temperatures, utilities,
                     CD,
                     oxidizer, fuel, pressurant,
                     rend_cstar, rend_CF,
                     pitch, circular, delay_time, npointsperside, constant_pressure_tank,
                     tol)


