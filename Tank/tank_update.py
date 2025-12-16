"""
This script provides the functions to update the tank properties.
"""

import numpy as np
import matplotlib.pyplot as plt
import CoolProp.CoolProp as cp
import Injection.PyInjection as injection
import Tank.tank_simulation as normal_tank
import Tank.tank_pressurant_simulation as pressurised_tank

def build_tank(m, Q, T, oxidizer, pressurant=None, ppress=1e5, p=1e5, plim=None):
    try:
        # If calculation performs, fluid isn't super-critic, liquid phase exists
        pV = cp.PropsSI('P', 'T', T, 'Q', 1, oxidizer["OxidizerCP"])
    except ValueError:
        # If calculation doesn't perform, sets Vapor pressure very high
        Q = 1
        pV = 100 * p

    if Q >= 1: # If full gas requested
        # If calculation performed and (p >= pV), (Q < 1), so we set (Q = 0.05)
        if p >= pV:
            p = pV

    if (Q < 1) & (p > pV):
        constant_pressure_tank = True
        if plim is None:
            plim = 1.5 * p
    else:
        constant_pressure_tank = False
        if plim is None:
            plim = 1.5 * p

    if not constant_pressure_tank:
        Vtank = normal_tank.create_tank(m, Q, T, oxidizer, p)

        masses = {"m": m}
        volumes = {"Vtank": Vtank}
        temperatures = {"Ttank": T}
        pressures = {"plim": plim}
    else:
        Vtank, Vliq = pressurised_tank.create_propellant_tank(m, p, T, Q, oxidizer["OxidizerCP"], pressurant)
        Vpress = pressurised_tank.create_pressurant_tank(T, ppress, Vliq, p, pressurant)

        masses = {"mL": m}
        volumes = {"Vtank": Vtank, "Vpress": Vpress}
        pressures = {"ppress": ppress, "ptank": p, "plim": plim}
        temperatures = {"Tpress": T, "Ttank": T}

    return masses, volumes, pressures, temperatures, constant_pressure_tank

def start_conditions(masses, volumes, pressures, temperatures,
                     oxidizer, pressurant=None, constant_pressure_tank = False):
    """
    Helper function for starting the conditions.
    :param masses: Masses dictionary (depends on type of tank)
    :param volumes: Volumes dictionary (depends on type of tank)
    :param pressures: Pressures dictionary (depends on type of tank)
    :param temperatures: Temperatures dictionary (depends on type of tank)
    :param oxidizer: oxidizer properties (Coolprop & CEA)
        {"OxidizerCP" : "", <--Name for CoolProp
        "OxidizerCEA" : "", <--Name for CEA
        "Weight fraction" : "100", # Multi-fluid Ox injector not available
        "Exploded Formula": "",
        "Temperature [K]" : "",
        "Specific Enthalpy [kj/mol]" : ""
        }
    :param pressurant: Pressurant CoolProp name
    :param constant_pressure_tank: Bool
    :return: ptank: Tank pressure [Pa],
             Ttank: Tank Temperature [K],
             mL: Liquid mass,
             entropies_out: Entropies dictionary (depends on type of tank),
             masses_out: Masses dictionary (depends on type of tank),
             pressures_out: Pressures dictionary (depends on type of tank),
             temperatures_out: Temperatures dictionary (depends on type of tank)
    """
    plim = pressures["plim"]

    if constant_pressure_tank:
        mL = masses["mL"]

        Vtank = volumes["Vtank"]
        Vpress = volumes["Vpress"]

        ppress = pressures["ppress"]
        ptank = pressures["ptank"]

        Tpress = temperatures["Tpress"]
        Ttank = temperatures["Ttank"]

        sL, sG, spress, mG, mpress = (
            pressurised_tank.starting_conditions(mL, Ttank, ptank, ppress, Vtank, Vpress,
                                                 oxidizer["OxidizerCP"], pressurant))

        entropies_out = {"sL": sL, "sG": sG, "spress": spress}
        masses_out = {"mL": mL, "mG": mG, "mpress": mpress}
        pressures_out = {"ppress": ppress, "ptank": ptank, "plim": plim}
        temperatures_out = {"Tpress": Tpress, "Ttank": Ttank}
    else:
        m = masses["m"]

        Vtank = volumes["Vtank"]

        Ttank = temperatures["Ttank"]

        ptank, sL, sG, mL, mG, Q, s, S = normal_tank.starting_conditions(m, Ttank, Vtank, oxidizer)

        entropies_out = {"sL": sL, "sG": sG, "S": S}
        masses_out = {"m": m, "Q": Q, "mL": mL, "mG": mG}
        pressures_out = {"ptank": ptank, "plim": plim}
        temperatures_out = {"Ttank": Ttank}

    return ptank, Ttank, mL, entropies_out, masses_out, pressures_out, temperatures_out

def update_tank(mdotL, dt, entropies, masses, volumes, pressures, temperatures,
                utilities, oxidizer, pressurant=None, constant_pressure_tank = False):
    """
    Helper function that updates the tank properties.
    :param mdotL: Mass flow through the injector [kg/s]
    :param dt: Time step [s]
    :param entropies: Entropies dictionary (depends on type of tank)
    :param masses: Masses dictionary (depends on type of tank)
    :param volumes: Volumes dictionary (depends on type of tank)
    :param pressures: Pressures dictionary (depends on type of tank)
    :param temperatures: Temperatures dictionary (depends on type of tank)
    :param utilities: Utilities dictionary (depends on type of tank)
    :param oxidizer: oxidizer properties (Coolprop & CEA)
        {"OxidizerCP" : "", <--Name for CoolProp
        "OxidizerCEA" : "", <--Name for CEA
        "Weight fraction" : "100", # Multi-fluid Ox injector not available
        "Exploded Formula": "",
        "Temperature [K]" : "",
        "Specific Enthalpy [kj/mol]" : ""
        }
    :param pressurant: Pressurant CoolProp name
    :param constant_pressure_tank: Bool
    :return: ptank_new: Tank pressure [Pa],
             Ttank_new: Tank Temperature [K],
             mL_new: Liquid mass,
             entropies_out: Entropies dictionary (depends on type of tank),
             masses_out: Masses dictionary (depends on type of tank),
             pressures_out: Pressures dictionary (depends on type of tank),
             temperatures_out: Temperatures dictionary (depends on type of tank)
    """

    if constant_pressure_tank:
        sL = entropies["sL"]
        sG = entropies["sG"]
        spress = entropies["spress"]

        mL = masses["mL"]
        mG = masses["mG"]
        mpress = masses["mpress"]

        Vtank = volumes["Vtank"]
        Vpress = volumes["Vpress"]

        ppress = pressures["ppress"]
        ptank = pressures["ptank"]
        plim = pressures["plim"]

        Tpress = temperatures["Tpress"]
        Ttank = temperatures["Ttank"]

        CDpress = utilities["CDpress"]
        Apress = utilities["Apress"]
        CDvent = utilities["CDvent"]
        Avent = utilities["Avent"]

        mdotpress = injection.gas_injection(ppress, ptank, Tpress, CDpress, pressurant) * Apress
        mdotG2 = injection.gas_injection(ptank, plim, Ttank, CDvent, pressurant) * Avent
        mdotG = mdotpress - mdotG2
        mL_new, mG_new, mpress_new, sL_new, sG_new, spress_new, ptank_new, Ttank_new, ppress_new, Tpress_new = (
            pressurised_tank.do_one_step(mdotL, mdotG, mdotpress, sL, sG, spress, mL, mG, mpress,
                                         Ttank, oxidizer["OxidizerCP"], pressurant, Vtank, Vpress, dt))

        entropies_out = {"sL": sL_new, "sG": sG_new, "spress": spress_new}
        masses_out = {"mL": mL_new, "mG": mG_new, "mpress": mpress_new, "mdot_vent": mdotG2}
        pressures_out = {"ppress": ppress_new, "ptank": ptank_new, "plim": plim}
        temperatures_out = {"Tpress": Tpress_new, "Ttank": Ttank_new}

    else:
        sL = entropies["sL"]
        sG = entropies["sG"]
        S = entropies["S"]

        m = masses["m"]
        Q = masses["Q"]

        Vtank = volumes["Vtank"]

        ptank = pressures["ptank"]
        plim = pressures["plim"]

        Ttank = temperatures["Ttank"]

        CDvent = utilities["CDvent"]
        Avent = utilities["Avent"]

        mdotG = injection.gas_injection(ptank, plim, Ttank, CDvent, oxidizer["OxidizerCP"]) * Avent
        m_new, mL_new, mG_new, Q_new, sL_new, sG_new, S_new, ptank_new, Ttank_new = (
            normal_tank.do_one_step(mdotL, mdotG, sL, sG, S, m, Q, oxidizer, Vtank, dt))

        entropies_out = {"sL": sL_new, "sG": sG_new, "S": S_new}
        masses_out = {"m": m_new, "Q": Q_new, "mL": mL_new, "mG": mG_new, "mdot_vent": mdotG}
        pressures_out = {"ptank": ptank_new, "plim": plim}
        temperatures_out = {"Ttank": Ttank_new}

    return ptank_new, Ttank_new, mL_new, entropies_out, masses_out, pressures_out, temperatures_out