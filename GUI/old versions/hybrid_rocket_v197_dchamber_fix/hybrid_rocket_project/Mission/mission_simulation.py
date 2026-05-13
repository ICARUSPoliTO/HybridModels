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
import Mission.Plotting as plotting

from typing import List, Dict, Any, Optional

def normalize_performances(list_of_dicts: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
    """
    Trasforma una lista di dizionari (performances) in un dizionario di liste per ogni chiave.
    - Preserva l'ordine di apparizione delle chiavi (prima occorrenza).
    - Se una chiave manca in un elemento, inserisce il valore di default:
        * se defaults contiene la chiave -> usa defaults[key]
        * se la chiave è 'burn' -> usa False
        * altrimenti -> usa None
    :param list_of_dicts: lista di dizionari (es. performances_out)
    :param defaults: dizionario opzionale di valori di default per chiave
    :return: dict con chiavi -> lista di valori (stessa lunghezza di list_of_dicts)
    """

    # Costruisci ordine delle chiavi basato sulla prima apparizione
    seen = []
    for d in list_of_dicts:
        for k in d.keys():
            if k not in seen:
                seen.append(k)

    # Assicurati che 'burn' sia presente nell'ordine delle chiavi
    if 'burn' not in seen:
        seen.append('burn')

    # Per ogni chiave crea la lista dei valori, usando default se mancante
    result: Dict[str, List[Any]] = {}
    for key in seen:
        col = []
        for d in list_of_dicts:
            if key in d:
                col.append(d[key])
            else:
                if key == 'burn':
                    col.append(False)
                else:
                    col.append(None)
        result[key] = col

    return result

def find_nozzle_output(gamma, MW, Tc, pc, mdot_throat, pamb, At, eps):
    R = 8314 / MW

    pamb_pc = pamb / pc
    fpamb = np.sqrt(2 * gamma * (pamb_pc**(2/gamma) - pamb_pc**((gamma+1)/gamma)) / (gamma - 1))
    gammone = np.sqrt(gamma * (2 / (gamma + 1)) ** ((gamma + 1) / (gamma - 1)))

    pe_pc_crit = (2 / (gamma + 1)) ** (gamma / (gamma - 1))

    if ((pamb/pc) < pe_pc_crit) or (fpamb >= gammone/eps):
        Me = 1.5

        fMe_target = mdot_throat / (pc * At * eps / np.sqrt(R * Tc))

        fMe = np.sqrt(gamma) * Me / np.sqrt((1 + 0.5 * (gamma - 1) * (Me ** 2)) ** ((gamma + 1) / (gamma - 1)))
        dfMe = np.sqrt(gamma) * (1 / np.sqrt((1 + 0.5 * (gamma - 1) * (Me ** 2)) ** ((gamma + 1) / (gamma - 1)))
                - 0.5 * (gamma + 1) * (Me ** 2) * ((1 + 0.5 * (gamma - 1) * (Me ** 2)) ** (2 / (gamma - 1))) /
                                 ((1 + 0.5 * (gamma - 1) * (Me ** 2)) ** (1.5 * (gamma + 1) / (gamma - 1))))
        feps = fMe - fMe_target
        n_eps = 0
        maxit_eps = 100
        while (abs(feps) > 1e-12) & (n_eps < maxit_eps):
            Me = Me - feps / dfMe
            fMe = np.sqrt(gamma) * Me / np.sqrt((1 + 0.5 * (gamma - 1) * (Me ** 2)) ** ((gamma + 1) / (gamma - 1)))
            dfMe = np.sqrt(gamma) * (1 / np.sqrt((1 + 0.5 * (gamma - 1) * (Me ** 2)) ** ((gamma + 1) / (gamma - 1)))
                                     - 0.5 * (gamma + 1) * (Me ** 2) * (
                                                 (1 + 0.5 * (gamma - 1) * (Me ** 2)) ** (2 / (gamma - 1))) /
                                     ((1 + 0.5 * (gamma - 1) * (Me ** 2)) ** (1.5 * (gamma + 1) / (gamma - 1))))
            feps = fMe - fMe_target

            n_eps = n_eps + 1

        Te = Tc / (1 + 0.5 * (gamma - 1) * (Me ** 2))
        pe = pc / ((1 + 0.5 * (gamma - 1) * (Me ** 2)) ** (gamma / (gamma - 1)))
        Ve = Me * np.sqrt(gamma * R * Te)

    else:
        pe = pamb
        Te = Tc / (pc/pe)**(gamma / (gamma - 1))
        Me = np.sqrt(2 * (Tc/Te - 1) / (gamma - 1))
        Ve = Me * np.sqrt(gamma * R * Te)

    return Me, Te, pe, Ve

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
    mdot_throat = inj.gas_injection_custom(pc, pamb, Tc, 1, gamma, MW, eps) * At

    ptank, Ttank, mL, entropies, masses, pressures, temperatures = tank.update_tank(mdot_ox, dt,
                                                                                    entropies, masses, volumes,
                                                                                    pressures, temperatures, utilities,
                                                                                    oxidizer, pressurant,
                                                                                    constant_pressure_tank)
    m_fuel = geomcalc.calculate_fuel_mass(Ap, Lc, D_chamber, rho_fuel)

    Me, Te, pe, Ve = find_nozzle_output(gamma, MW, Tc, pc, mdot_throat, pamb, At, eps)

    Thrust = rend_CF * (mdot_throat * Ve + (pe - pamb) * eps * At)

    performances = {"pc": pc, "pinj": p_inj, "dt": dt, "Thrust": Thrust,
                    "mdot_ox": mdot_ox, "mdot_fuel": mdot_fuel, "mdot": mdot, "mdot_throat": mdot_throat,
                    "Tc": Tc, "MW": MW, "gamma": gamma,
                    "eps": eps,
                    "x": x, "y": y, "Ap": Ap, "Ab": Ab, "Vol_chamber": Vol_chamber,
                    "m_fuel": m_fuel, "mL": mL, "ptank": ptank, "Ttank": Ttank,
                    "Me": Me, "Te": Te, "pe": pe, "pamb": pamb,
                    "D_chamber": D_chamber, "Ainj": Ainj, "At": At, "Lc": Lc,
                    "entropies": entropies, "masses": masses, "pressures": pressures,"temperatures": temperatures,
                    "burn": False}

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

    x, y = geom.burn_grain(x, y, z, r, dt, circular)
    Ap, Ab, Vol_chamber = geomcalc.fill_and_calculate_surfaces_and_volume(x, y, Lc, npointsperside, circular, pitch,
                                                                          Vol_prechamber, Vol_postchamber)
    m_fuel = geomcalc.calculate_fuel_mass(Ap, Lc, D_chamber, rho_fuel)

    pc = chamber.update_chamberpressure(m_c, Tc, MW, Vol_chamber)
    mdot_throat = inj.gas_injection_custom(pc, pamb, Tc, 1, gamma, MW, eps) * At

    ptank, Ttank, mL, entropies, masses, pressures, temperatures = tank.update_tank(mdot_ox, dt,
                                                                                    entropies, masses, volumes,
                                                                                    pressures, temperatures, utilities,
                                                                                    oxidizer, pressurant,
                                                                                    constant_pressure_tank)

    Me, Te, pe, Ve = find_nozzle_output(gamma, MW, Tc, pc, mdot_throat, pamb, At, eps)

    Thrust = rend_cstar * rend_CF * (mdot_throat * Ve + (pe - pamb) * eps * At)
    """
    print("c* = ", cstar)
    print("CF = ", CF)
    print("mdot = ", mdot_throat)
    print("F1 = ", rend_cstar * rend_CF * cstar * CF * mdot_throat)
    print("F2 = ", rend_cstar * rend_CF * CF * pc * At)
    print("F3 = ", Thrust)
    #Thrust = rend_cstar * rend_CF * cstar * CF * mdot_throat
    """

    performances = {"pc": pc, "pinj": p_inj, "dt": dt, "Thrust": Thrust,
                    "mdot_ox": mdot_ox, "mdot_fuel": mdot_fuel, "mdot": mdot, "mdot_throat": mdot_throat, "Gox": Gox,
                    "r": r, "MR": MR, "Tc_CEA": Tc_CEA, "MW_CEA": MW_CEA, "gamma_CEA": gamma_CEA,
                    "Tc": Tc, "MW": MW, "gamma": gamma,
                    "eps": eps, "cstar": cstar, "CFvac": CFvac, "CF": CF, "Ivac": Ivac, "Is": Is,
                    "x": x, "y": y, "Ap": Ap, "Ab": Ab, "Vol_chamber": Vol_chamber,
                    "m_fuel": m_fuel, "mL": mL, "ptank": ptank, "Ttank": Ttank,
                    "Me": Me, "Te": Te, "pe": pe, "pamb": pamb,
                    "D_chamber": D_chamber, "Ainj": Ainj, "At": At, "Lc": Lc,
                    "entropies": entropies, "masses": masses, "pressures": pressures,"temperatures": temperatures,
                    "flag": flag, "burn": True}

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

    performances = {"pc": pc, "pinj": pc, "dt": 0.0, "Thrust": 0.0,
                    "mdot_ox": 0.0, "mdot_fuel": 0.0, "mdot": 0.0, "mdot_throat": mdot_throat,
                    "Tc": Tc, "MW": MW, "gamma": gamma,
                    "eps": eps,
                    "x": x, "y": y, "Ap": Ap, "Ab": Ab, "Vol_chamber": Vol_chamber,
                    "m_fuel": m_fuel, "mL": mL, "ptank": ptank, "Ttank": Ttank,
                    "Me": 0.0, "Te": Tc, "pe": pamb, "pamb": pamb,
                    "D_chamber": D_chamber, "Ainj": Ainj, "At": At, "Lc": Lc,
                    "entropies": entropies, "masses": masses, "pressures": pressures, "temperatures": temperatures,
                    "burn": False}

    time = [0]
    performances_out = [performances]
    out_log = []

    conditions_no_burn = (mL > 0 or full_gas_tank) & (ptank > pc)

    conditions_burn = ((mL > 0 or full_gas_tank) & (ptank > pc) &
                  (m_fuel > 0) & (np.max(np.hypot(x, y)) < 0.5 * D_chamber))

    if delay_time == 0.0:
        delay_time = -1

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
        performances_out.append(performances)

    out_str = "Delayied ignition ended:\n"
    if time[-1] >= delay_time:
        out_str += f"Delay time ended at {time[-1]}!"
    elif not (mL > 0 or full_gas_tank):
        out_str += "Tank empty!\n"
        out_str += f"Time: {time[-1]}"
    elif not (ptank > pc):
        out_str += "Tank pressure too low!\n"
        out_str += f"Time: {time[-1]}"
    else:
        out_str += f"Delay time ended at {time[-1]}!"
    out_log.append(out_str)

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
        performances_out.append(performances)

    out_str = "Combustion ended:\n"
    if time[-1] >= (burn_time + delay_time):
        out_str += f"Combustion time ended at {time[-1]}!"
    elif not (mL > 0 or full_gas_tank):
        out_str += "Tank empty!\n"
        out_str += f"Time: {time[-1]}"
    elif not (ptank > pc):
        out_str += "Tank pressure too low!\n"
        out_str += f"Time: {time[-1]}"
    elif not (m_fuel > 0):
        out_str += "Fuel finished\n"
        out_str += f"Time: {time[-1]}"
    elif not (np.max(np.hypot(x, y)) < 0.5 * D_chamber):
        out_str += "Chamber wall reached\n"
        out_str += f"Time: {time[-1]}"
    else:
        out_str += f"Combustion time ended at {time[-1]}!"

    out_log.append(out_str)

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
                     rend_CF, constant_pressure_tank, tol)

        conditions_no_burn = (mL > 0 or full_gas_tank) & (ptank > pc)
        time.append(time[-1] + dt)
        performances_out.append(performances)

    out_str = "Final emptying ended:\n"
    if not (mL > 0 or full_gas_tank):
        out_str += "Tank empty!\n"
        out_str += f"Time: {time[-1]}"
    elif not (ptank > pc):
        out_str += "Tank pressure too low!\n"
        out_str += f"Time: {time[-1]}"

    out_log.append(out_str)

    return time, performances_out, out_log

def run_full_mission_iteration(burn_time, pamb, Tamb, a, n, rho_fuel,
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
    This functions runs the whole mission, until combustion time ends. Special flags for iteration matching.
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

    performances = {"pc": pc, "pinj": pc, "dt": 0.0, "Thrust": 0.0,
                    "mdot_ox": 0.0, "mdot_fuel": 0.0, "mdot": 0.0, "mdot_throat": mdot_throat,
                    "Tc": Tc, "MW": MW, "gamma": gamma,
                    "eps": eps,
                    "x": x, "y": y, "Ap": Ap, "Ab": Ab, "Vol_chamber": Vol_chamber,
                    "m_fuel": m_fuel, "mL": mL, "ptank": ptank, "Ttank": Ttank,
                    "Me": 0.0, "Te": Tc, "pe": pamb, "pamb": pamb,
                    "D_chamber": D_chamber, "Ainj": Ainj, "At": At, "Lc": Lc,
                    "entropies": entropies, "masses": masses, "pressures": pressures, "temperatures": temperatures,
                    "burn": False}

    time = [0]
    performances_out = [performances]
    out_log = []

    conditions_no_burn = (mL > 0 or full_gas_tank) & (ptank > pc)

    conditions_burn = ((mL > 0 or full_gas_tank) & (ptank > pc) &
                  (m_fuel > 0) & (np.max(np.hypot(x, y)) < 0.5 * D_chamber))

    if delay_time == 0.0:
        delay_time = -1

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
        performances_out.append(performances)

    if time[-1] >= delay_time:
        out_opt = {"ptank": True, "mL": True, "t": time[-1]}
    elif not (mL > 0 or full_gas_tank):
        out_opt = {"ptank": True, "mL": False, "t": time[-1]}
    elif not (ptank > pc):
        out_opt = {"ptank": False, "mL": True, "t": time[-1]}
    else:
        out_opt = {"ptank": True, "mL": True, "t": time[-1]}
    out_log.append(out_opt)

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
        performances_out.append(performances)

    if time[-1] >= (burn_time + delay_time):
        out_opt = {"ptank": True, "mL": True, "m_fuel": True, "max_r": True, "t": time[-1]}
    elif not (mL > 0 or full_gas_tank):
        out_opt = {"ptank": True, "mL": False, "m_fuel": True, "max_r": True, "t": time[-1]}
    elif not (ptank > pc):
        out_opt = {"ptank": False, "mL": True, "m_fuel": True, "max_r": True, "t": time[-1]}
    elif not (m_fuel > 0):
        out_opt = {"ptank": True, "mL": True, "m_fuel": False, "max_r": True, "t": time[-1]}
    elif not (np.max(np.hypot(x, y)) < 0.5 * D_chamber):
        out_opt = {"ptank": True, "mL": True, "m_fuel": True, "max_r": False, "t": time[-1]}
    else:
        out_opt = {"ptank": True, "mL": True, "m_fuel": True, "max_r": True, "t": time[-1]}

    out_log.append(out_opt)

    return time, performances_out, out_log

def match_mission(burn_time, pamb, Tamb, a, n, rho_fuel,
                     eps, Ainj, At, Lc, D_chamber,
                     x, y, z,
                     Vol_prechamber, Vol_postchamber, utilities,
                     CD,
                     mtank, Q,
                     oxidizer, fuel, pressurant=None,
                     rend_cstar = 1.1, rend_CF = 1.1,
                     pitch=0.0, circular=False, delay_time = 0.0, npointsperside=50,
                     tol=1e-3, ppress=1e5, ptank0=1e5, plim=None):
    """
    This functions iterates the mission until oxidizer and fuel mass aren't in a range of 5% of starting
    values at the end of combustion time.
    :param burn_time: Burn time [s]
    :param pamb: Ambient pressure [Pa]
    :param Tamb: Ambient temperature [K]
    :param a: regression rate coefficient r=aGox^n [m/s]
    :param n: regression rate exponent r=aGox^n [m/s]
    :param rho_fuel: Fuel density [kg/m^3]
    :param eps: Expansion ratio
    :param Ainj: Injection Area [m^2]
    :param At: Throat Area [m^2]
    :param Lc: Chamber Length [m]
    :param D_chamber: Chamber inner diameter [m]
    :param x: x-axis values [m]
    :param y: y-axis values [m]
    :param z: axis direction for grain geometry (1=counter-clockwise, -1=clockwise)
    :param Vol_prechamber: Prechamber volume [m^3]
    :param Vol_postchamber: Postchamber volume [m^3]
    :param utilities: Dict for tank utilities
           {"CDvent": float,"Avent": float, "CDpress": float, "Apress": float}
    :param CD: Injector Discharge coefficient [m/s]
    :param mtank: Tank mass (total if self press, liquid if pressurized)[kg]
    :param Q: Tank vapor quality
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
    :param pitch: Fuel grain helix pitch [m]
    :param circular: Bool (True: arc fill, False: linear fill)
    :param delay_time: Delay time before ignition [s]
    :param npointsperside: Point between every consecutive point to fill geometry
    :param tol: Tolerance for time step calculation
    :param ppress: Pressurant pressure [Pa]
    :param ptank0: Tank initial pressure (needed only for full gas or pressurised)[Pa]
    :param plim: Limit pressure of the tank for venting (optional) [Pa]
    :return: time, inputs, performances_out, out_log
    """
    matched = False
    n_it = 0
    maxit = 20
    while not matched:

        masses, volumes, pressures, temperatures, constant_pressure_tank = (
            tank.build_tank(mtank, Q, Tamb, oxidizer, pressurant, ppress, ptank0, plim))

        time, performances_out, out_log = run_full_mission_iteration(burn_time, pamb, Tamb, a, n, rho_fuel,
                         eps, Ainj, At, Lc, D_chamber,
                         x, y, z,
                         Vol_prechamber, Vol_postchamber,
                         masses, volumes, pressures, temperatures, utilities,
                         CD,
                         oxidizer, fuel, pressurant,
                         rend_cstar, rend_CF,
                         pitch, circular, delay_time, npointsperside, constant_pressure_tank,
                         tol)

        # Safety check: ensure out_log has at least 2 elements
        if len(out_log) < 2:
            # Simulation failed early, double parameters and retry
            mtank = 2 * mtank
            ptank0 = 1.5 * ptank0
            n_it += 1
            continue
        
        # Get elapsed time with protection against zero
        t_elapsed = out_log[1].get("t", 0) if out_log[1] else 0
        if t_elapsed is None or t_elapsed <= 0:
            t_elapsed = 1e-6  # Small positive value to avoid division by zero
        
        # Calculate time ratio for adjustments
        target_time = burn_time + delay_time
        time_ratio = target_time / t_elapsed if t_elapsed > 0 else 2.0  # Default to doubling if no time

        # Gross adjustements for delay injection
        if not out_log[0]["mL"]:
            mtank = 2 * mtank
        elif not out_log[0]["ptank"]:
            if (Q == 1) or (constant_pressure_tank):
                ptank0 = 1.5 * ptank0
            else:
                Q = 2 * Q

        if not out_log[1]["mL"]: # Tank empty before required time
            mtank = mtank * time_ratio  # Increment tank mass

            if performances_out[-1]["m_fuel"] > 0.05 * performances_out[0]["m_fuel"]: # Cut excess fuel
                D_chamber = 1.05 * 2 * np.max(np.hypot(performances_out[-1]["x"], performances_out[-1]["y"]))

        elif not out_log[1]["ptank"]: # Increment tank ullage or pressure
            if (Q == 1) or (constant_pressure_tank):
                ptank0 = ptank0 * time_ratio
            else:
                Q = Q * time_ratio

            if performances_out[-1]["m_fuel"] > 0.05 * performances_out[0]["m_fuel"]: # Cut excess fuel
                D_chamber = 1.05 * 2 * np.max(np.hypot(performances_out[-1]["x"], performances_out[-1]["y"]))

        elif not ((out_log[1]["m_fuel"]) and (out_log[1]["max_r"])): # Increment fuel
            D_chamber = D_chamber * time_ratio

            if performances_out[-1]["mL"] > 0.05 * performances_out[0]["mL"]:  # Cut excess oxidizer
                mtank = 1.05 * abs(performances_out[-1]["mL"] - performances_out[0]["mL"])

        else:
            if performances_out[-1]["mL"] > 0.05 * performances_out[0]["mL"]:  # Cut excess oxidizer
                mtank = 1.05 * abs(performances_out[-1]["mL"] - performances_out[0]["mL"])

                if performances_out[-1]["m_fuel"] > 0.05 * performances_out[0]["m_fuel"]: # Cut excess fuel
                    D_chamber = 1.05 * 2 * np.max(np.hypot(performances_out[-1]["x"], performances_out[-1]["y"]))
            else:

                if performances_out[-1]["m_fuel"] > 0.05 * performances_out[0]["m_fuel"]:  # Cut excess fuel
                    D_chamber = 1.05 * 2 * np.max(np.hypot(performances_out[-1]["x"], performances_out[-1]["y"]))
                else:
                    matched = True

        n_it += 1
        if n_it > maxit:
            matched = True

    if n_it > maxit:
        converged = False
        print( "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"Mission not matched! {n_it} / {maxit}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        converged = True
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"Mission matched! {n_it} / {maxit}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    masses, volumes, pressures, temperatures, constant_pressure_tank = (
        tank.build_tank(mtank, Q, Tamb, oxidizer, pressurant, ppress, ptank0, plim))

    time, performances_out, out_log = run_full_mission(burn_time, pamb, Tamb, a, n, rho_fuel,
                                                       eps, Ainj, At, Lc, D_chamber,
                                                       x, y, z,
                                                       Vol_prechamber, Vol_postchamber,
                                                       masses, volumes, pressures, temperatures, utilities,
                                                       CD,
                                                       oxidizer, fuel, pressurant,
                                                       rend_cstar, rend_CF,
                                                       pitch, circular, delay_time, npointsperside,
                                                       constant_pressure_tank,
                                                       tol)

    inputs = {"burn_time": burn_time, "Tamb": Tamb, "a": a, "n": n, "rho_fuel": rho_fuel,
              "Ainj": Ainj, "At": At, "Lc": Lc, "D_chamber": D_chamber,
              "z": z,
              "Vol_prechamber": Vol_prechamber, "Vol_postchamber": Vol_postchamber,
              "utilities": utilities,
              "CD": CD,
              "oxidizer": oxidizer, "fuel": fuel, "pressurant": pressurant,
              "rend_cstar": rend_cstar, "rend_CF": rend_CF,
              "pitch": pitch, "circular": circular, "delay_time": delay_time,
              "npointsperside": npointsperside, "constant_pressure_tank": constant_pressure_tank,
              "tol": tol, "converged": converged, "n_it": n_it, "maxit": maxit}
    """
    out_log[0] = {"ptank": True, "mL": False, "t": time[-1]}
    out_log[1] = {"ptank": True, "mL": False, "m_fuel": True, "max_r": True, "t": time[-1]}
    """

    return time, inputs, performances_out, out_log

if __name__ == '__main__':

    burn_time = 30 #[s]
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

    eps = 4.5
    Dt = 0.04
    Dp = 0.06
    Dinj = 0.0101

    Ainj = 0.25 * np.pi * (Dinj ** 2) # [m^2]
    At = 0.25 * np.pi * (Dt ** 2) # [m^2]
    Lc = 0.16 # [m]
    D_chamber = 0.1 # [m]
    Avent = 0 # [m^2]

    x = np.array([0.5 * Dp]) # [m]
    y = np.array([0]) # [m]
    z = 1
    Vol_prechamber = 0.1
    Vol_postchamber = 0.1

    mtank = 25 # [kg]
    Q = 0.03
    pressurant = None
    ppress = 1e5
    p0 = pamb
    plim = None
    masses, volumes, pressures, temperatures, constant_pressure_tank = (
        tank.build_tank(mtank, Q, Tamb, oxidizer, pressurant, ppress, p0, plim))

    utilities = {"CDvent": 0.75,"Avent": Avent, "CDpress": 0.9, "Apress": 0.0}

    CD = 0.8
    pressurant = None
    rend_cstar = 0.85
    rend_CF = 0.8
    pitch = 0.0 # [m]
    circular = True
    delay_time = 0.5 # [s]
    npointsperside = 50
    tol = 1e-3

    """
    time, performances_out, out_log = run_full_mission(burn_time, pamb, Tamb, a, n, rho_fuel,
                     eps, Ainj, At, Lc, D_chamber,
                     x, y, z,
                     Vol_prechamber, Vol_postchamber,
                     masses, volumes, pressures, temperatures, utilities,
                     CD,
                     oxidizer, fuel, pressurant,
                     rend_cstar, rend_CF,
                     pitch, circular, delay_time, npointsperside, constant_pressure_tank,
                     tol)
    """
    time, inputs, performances_out, out_log = match_mission(burn_time, pamb, Tamb, a, n, rho_fuel,
                  eps, Ainj, At, Lc, D_chamber,
                  x, y, z,
                  Vol_prechamber, Vol_postchamber, utilities,
                  CD,
                  mtank, Q,
                  oxidizer, fuel, pressurant,
                  rend_cstar, rend_CF,
                  pitch, circular, delay_time, npointsperside,
                  tol, ppress, p0, plim)
    #"""

    results = normalize_performances(performances_out)

    #Plot to match output file
    plt.figure()
    plt.plot(time, results["Thrust"])
    plt.show()

    plt.figure()
    plt.plot(time, results["m_fuel"], label="Fuel")
    plt.plot(time, results["mL"], label="Tank")
    plt.legend()
    plt.show()
    for elmnt in out_log:
        print(elmnt)

    import pickle
    # Saving the objects:
    open('results.pkl', 'w').close()
    with open('results.pkl', 'wb') as f:  # Python 3: open(..., 'wb')
        pickle.dump((time, inputs, results, out_log), f)



    """
    burn = [p["burn"] for p in performances_out]
    Tc_CEA = [performances_out[i]["Tc_CEA"] for i, b in enumerate(burn) if b]
    time_burn = [time[i] for i, b in enumerate(burn) if b]
    """
    #plotting.plot_results(time, results)
    """
    plt.figure()
    plt.plot(time, results["pc"], label="Pc")
    plt.plot(time, results["pe"], label="Pe")
    plt.plot(time, results["pamb"], label="P0")
    plt.xlabel("Time [s]")
    plt.ylabel("Pressure [Pa]")
    plt.legend()

    plt.figure()
    plt.plot(time, results["Tc"], label="Tc")
    plt.plot(time, results["Tc_CEA"], label="Tc_CEA")
    plt.plot(time, results["Te"], label="Te")
    plt.xlabel("Time [s]")
    plt.ylabel("Temperature [K]")
    plt.legend()

    plt.figure()
    plt.plot(time, results["Me"], label="Me")
    plt.xlabel("Time [s]")
    plt.ylabel("Mach Number")

    plt.figure()
    plt.plot(time, results["Thrust"])
    plt.xlabel("Time [s]")
    plt.ylabel("Thrust [N]")

    plt.figure()
    plt.plot(time, results["m_fuel"])
    plt.xlabel("Time [s]")
    plt.ylabel("Thrust [N]")

    plt.show()
    """
# end of file