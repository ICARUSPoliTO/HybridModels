"""
This script provides the functions to simulate the emptying of a self-pressurizing oxidizer tank.
Procedure according to
Engineering Model for Self-Pressurizing Saturated-N2O-Propellant Feed Systems
Stephen A. Whitmore∗ and Spencer N. Chandler†
Utah State University, Logan, Utah 84322-4130
DOI: 10.2514/1.47131
"""

import numpy as np
import matplotlib.pyplot as plt
import CoolProp.CoolProp as cp
import Line_losses.linelosses as linelosses
import Injection.PyInjection as injection

def create_tank(m, Q, T, oxidizer):
    """
    This function creates a tank using the given oxidizer properties, mass, temperature and vapor quality (mV/mTOT)
    :param m: Total mass [kg]
    :param Q: Vapor quality
    :param T: Temperature [K]
    :param oxidizer: oxidizer properties (Coolprop & CEA)
        {"OxidizerCP" : "", <--Name for CoolProp
        "OxidizerCEA" : "", <--Name for CEA
        "Weight fraction" : "100", # Multi-fluid Ox injector not available
        "Exploded Formula": "",
        "Temperature [K]" : "",
        "Specific Enthalpy [kj/mol]" : ""
        }
    :return: Tank volume [m^3]
    """
    rhoL = cp.PropsSI('D', 'T', T, 'Q', 0, oxidizer["OxidizerCP"])  # [kg/m^3]
    rhoV = cp.PropsSI('D', 'T', T, 'Q', 1, oxidizer["OxidizerCP"])  # [kg/m^3]

    Vtank = (Q* (rhoL - rhoV) + rhoV) * m/(rhoV * rhoL)
    return Vtank

def starting_conditions(m0, T0, Vtank, oxidizer):
    """
    This function gets the starting pressure, vapor quality, specific entropies for liquid (L), vapor (V) and tank
    and entropy of the tank. The values are calculated using CoolProp.
    :param m0: Initial mass [kg]
    :param T0: Initial temperature [K]
    :param Vtank: Tank volume [m^3]
    :param oxidizer:  oxidizer properties (Coolprop & CEA)
        {"OxidizerCP" : "", <--Name for CoolProp
        "OxidizerCEA" : "", <--Name for CEA
        "Weight fraction" : "100", # Multi-fluid Ox injector not available
        "Exploded Formula": "",
        "Temperature [K]" : "",
        "Specific Enthalpy [kj/mol]" : ""
        }
    :return: ptank0 (starting pressure) [Pa],
             sL0 (starting liquid specific entropy) [J/kgK],
             sV0 (starting vapor specific entropy) [J/kgK],
             Q0 (starting vapor quality),
             s0 (starting specific entropy) [J/kgK],
             S0 (starting entropy) [J/K]
    """
    ptank0 = cp.PropsSI('P', 'T', T0, 'Q', 1, oxidizer["OxidizerCP"]) #[Pa]

    rhoL0 = cp.PropsSI('D', 'T', T0, 'Q', 0, oxidizer["OxidizerCP"]) #[kg/m^3]
    sL0 = cp.PropsSI('S', 'T', T0, 'Q', 0, oxidizer["OxidizerCP"]) #[J/kgK]

    rhoV0 = cp.PropsSI('D', 'T', T0, 'Q', 1, oxidizer["OxidizerCP"]) #[kg/m^3]
    sV0 = cp.PropsSI('S', 'T', T0, 'Q', 1, oxidizer["OxidizerCP"]) #[J/kgK]

    Q0 = (rhoV0*rhoL0*Vtank - rhoV0*m0)/(m0*(rhoL0 - rhoV0))

    mL0 = m0*(1-Q0) #[kg]
    mV0 = m0*Q0 #[kg]

    s0 = sL0*(1 - Q0) + sV0*Q0 #[J/kgK]
    S0 = sL0*m0 #[J/K]

    return ptank0, sL0, sV0, mL0, mV0, Q0, s0, S0


def do_one_step(ptank, pc, pamb, Ttank, sL, sV, S, m, oxidizer, CD, Ainj, plim, Avent, CD_vent, Vtank, dt):
    # Calculate injection pressure after losses. May require iterations with Oxidizer injection
    p_inj = ptank - linelosses.linelosses()  # add input for line losses here and in the inputs of the function

    # Calculate injection mass flow
    inj = injection.Injector(oxidizer["OxidizerCP"])
    inj.massflow(p_inj, pc, Ttank, CD)
    mdotL = inj.mdot * Ainj  #[kg/s]

    if ptank > plim:
        gamma = (cp.PropsSI('CPMASS', 'T', Ttank, 'Q', 1, oxidizer["OxidizerCP"])
                 / cp.PropsSI('CVMASS','T', Ttank, 'Q', 1, oxidizer["OxidizerCP"]))
        R = 8314 / (cp.PropsSI('MOLARMASS', 'T', Ttank, 'Q', 1, oxidizer["OxidizerCP"]) / 1e-3) #[J/kgK]

        mdotV = CD_vent * Avent * ptank / np.sqrt(R * Ttank) #[kg/s]
        gammone = np.sqrt(gamma * (2 / (gamma + 1)) ** ((gamma + 1) / (gamma - 1)))
        ptank_pamb_crit = (2 / (gamma + 1)) ** (gamma / (gamma - 1))
        if (pamb / ptank) < ptank_pamb_crit:  # Is critical?
            mdotV = mdotV * gammone
        else:
            mdotV = mdotV * np.sqrt(
                (2 * gamma) * ((pamb / ptank) ** (2 / gamma) - (pamb / ptank) ** ((gamma + 1) / gamma)) / (gamma - 1))

    else:
        mdotV = 0

    m_new = m - (mdotL + mdotV)*dt #[kg]
    S_new = S - (sL*mdotL + sV*mdotV)*dt #[J/K]
    s_new = S_new/m_new #[J/kgK]
    rho_new = m_new/Vtank #[kg/m^3]

    ptank_new = cp.PropsSI('P', 'D', rho_new, 'S', s_new, oxidizer["OxidizerCP"]) #[Pa]
    Ttank_new = cp.PropsSI('T', 'D', rho_new, 'S', s_new, oxidizer["OxidizerCP"]) #[K]
    Q_new = cp.PropsSI('Q', 'D', rho_new, 'S', s_new, oxidizer["OxidizerCP"])


    sL_new = cp.PropsSI('S', 'T', Ttank_new, 'Q', 0, oxidizer["OxidizerCP"]) #[J/kgK]
    sV_new = cp.PropsSI('S', 'T', Ttank_new, 'Q', 1, oxidizer["OxidizerCP"]) #[J/kgK]

    if Q_new < 0.99:
        mL_new = m_new*(1-Q_new) #[kg]
        mV_new = m_new*Q_new #[kg]
    else:
        Q_new = 1
        mL_new = 0
        mV_new = m_new

    return m_new, mL_new, mV_new, Q_new, sL_new, sV_new, S_new, ptank_new, Ttank_new, mdotV


def full_tank_simulation(m, Q, T, oxidizer, pamb, pc, Ainj, CD, plim, Avent, CD_vent, dt, endtime):
    Vtank = create_tank(m, Q, T, oxidizer)
    ptank, sL, sV, mL, mV, Q, s, S = starting_conditions(m, T, Vtank, oxidizer)

    inj = injection.Injector('NitrousOxide')
    inj.massflow(ptank, pc, T, CD)
    mdotL = inj.mdot * Ainj

    print("Tank volume= " + str(Vtank * 1e3) + " L")
    print("Starting tank pressure= " + str(ptank) + " Pa")
    print("Starting temperature= " + str(T) + " K")
    print("Starting mass= " + str(m) + " kg")
    print("Starting liquid mass= " + str(mL) + " kg")
    print("Starting vapor mass= " + str(mV) + " kg")
    print("Starting liquid mass flow= "+str(mdotL)+" kg/s")
    print("Starting quality= " + str(Q))
    print("########### after " + str(dt) + " seconds ###########")

    time = np.arange(0, endtime, dt)
    output_size = np.size(time)
    mdotL_vec   = np.zeros(output_size)
    mdotV_vec = np.zeros(output_size)
    ptank_vec   = np.zeros(output_size)
    Ttank_vec   = np.zeros(output_size)
    m_vec       = np.zeros(output_size)
    mL_vec      = np.zeros(output_size)
    mV_vec      = np.zeros(output_size)
    Q_vec       = np.zeros(output_size)
    sL_vec      = np.zeros(output_size)
    sV_vec      = np.zeros(output_size)
    S_vec       = np.zeros(output_size)

    mdotL_vec[0] = mdotL
    ptank_vec[0] = ptank
    Ttank_vec[0] = T
    m_vec[0] = m
    mL_vec[0] = mL
    mV_vec[0] = mV
    Q_vec[0] = Q
    sL_vec[0] = sL
    sV_vec[0] = sV
    S_vec[0] = S

    for idx_t in np.arange(1, np.size(time), 1):
        m, mL, mV, Q, sL, sV, S, ptank, T, mdotV = (
            do_one_step(mdotL, ptank, pamb, T, sL, sV, S, m, oxidizer, plim, Avent, CD_vent, Vtank, dt))

        inj.massflow(ptank, pc, T, CD)
        mdotL = inj.mdot * Ainj

        print("Time= "+str(time[idx_t]) + " s")
        print("Tank pressure= " + str(ptank) + " Pa")
        print("Temperature= " + str(T) + " K")
        print("Total mass= " + str(m) + " kg")
        print("Liquid mass= " + str(mL) + " kg")
        print("Vapor mass= " + str(mV) + " kg")
        print("Liquid mass flow= " + str(mdotL) + " kg/s")
        print("Vapor mass flow= " + str(mdotV) + " kg/s")
        print("Quality= " + str(Q))
        print("########### after " + str(dt) + " seconds ###########")

        mdotL_vec[idx_t] = mdotL
        mdotV_vec[idx_t] = mdotV
        ptank_vec[idx_t] = ptank
        Ttank_vec[idx_t] = T
        m_vec[idx_t]     = m
        mL_vec[idx_t]    = mL
        mV_vec[idx_t]    = mV
        Q_vec[idx_t]     = Q
        sL_vec[idx_t]    = sL
        sV_vec[idx_t]    = sV
        S_vec[idx_t]     = S

        if Q == 1:
            time = time[0:idx_t+1]
            mdotL_vec = mdotL_vec[0:idx_t+1]
            mdotV_vec = mdotV_vec[0:idx_t+1]
            ptank_vec = ptank_vec[0:idx_t+1]
            Ttank_vec = Ttank_vec[0:idx_t+1]
            m_vec = m_vec[0:idx_t+1]
            mL_vec = mL_vec[0:idx_t+1]
            mV_vec = mV_vec[0:idx_t+1]
            Q_vec = Q_vec[0:idx_t+1]
            sL_vec = sL_vec[0:idx_t+1]
            sV_vec = sV_vec[0:idx_t+1]
            S_vec = S_vec[0:idx_t+1]
            break

    return time, mdotL_vec, mdotV_vec, ptank_vec, Ttank_vec, m_vec, mL_vec, mV_vec, Q_vec, sL_vec, sV_vec, S_vec

if __name__ == '__main__':
    m0 = 10 #[kg]
    T0 = 298 #[K]
    oxidizer = {"OxidizerCP": "NitrousOxide"}
    #Vtank = 18e-3 #[m^3]

    Q0 = 0.03

    Dinj = 3.175e-3 #[m]
    ninj = 5
    Ainj = ninj*0.25*np.pi*Dinj**2 #[m^2]
    CD = 0.8
    mdotL = 0.5 #[kg/s]

    pamb = 1e5 #[Pa]
    pc = 1e5 #[Pa]
    plim = 70e5 #[Pa]

    Dvent = 3.175e-3 #[m]
    Avent = 0.25*np.pi*Dvent**2 #[m^2]
    CD_vent = 0.8

    dt = 1e-2 #[s]
    endtime = 1000

    """
    Vtank = create_tank(m0, Q0, T0, oxidizer)
    ptank0, sL0, sV0, mL0, mV0, Q0, s0, S0 = starting_conditions(m0, T0, Vtank, oxidizer)

    m_new, mL_new, mV_new, Q_new, sL_new, sV_new, S_new, ptank_new, Ttank_new, mdotV = (
        do_one_step(mdotL, ptank0, 1e5, T0, sL0, sV0, S0, m0, oxidizer, plim, Avent, 0.8, Vtank, dt))

    print("Tank volume= "+str(Vtank*1e3)+" L")
    print("Starting tank pressure= "+str(ptank0)+" Pa")
    print("Starting temperature= "+str(T0)+" K")
    print("Starting mass= "+str(m0)+" kg")
    print("Starting liquid mass= "+str(mL0)+" kg")
    print("Starting vapor mass= "+str(mV0)+" kg")
    print("Starting quality= "+str(Q0))
    print("Starting liquid specific entropy= "+str(sL0)+" J/kgK")
    print("Starting vapor specific entropy= "+str(sV0)+" J/kgK")
    print("Starting total entropy= "+str(S0)+" J/K")
    print("########### after "+str(dt)+" seconds ###########")
    print("New tank pressure= "+str(ptank_new)+" Pa")
    print("New temperature= "+str(Ttank_new)+" K")
    print("New mass= "+str(m_new)+" kg")
    print("New liquid mass= "+str(mL_new)+" kg")
    print("New vapor mass= "+str(mV_new)+" kg")
    print("New quality= "+str(Q_new)+" kg")
    print("New liquid specific entropy= " + str(sL_new) + " J/kgK")
    print("New vapor specific entropy= " + str(sV_new) + " J/kgK")
    print("New total entropy= " + str(S_new) + " J/K")
    """

    time, mdotL_vec, mdotV_vec, ptank_vec, Ttank_vec, m_vec, mL_vec, mV_vec, Q_vec, sL_vec, sV_vec, S_vec = (
        full_tank_simulation(m0, Q0, T0, oxidizer, pamb, pc, Ainj, CD, plim, Avent, CD_vent, dt, endtime))


    # Funzione helper per forzare spine, ticks e label in nero
    def make_axes_black(ax):
        for spine in ax.spines.values():
            spine.set_color('black')
        ax.xaxis.label.set_color('black')
        ax.yaxis.label.set_color('black')
        ax.tick_params(axis='x', colors='black')
        ax.tick_params(axis='y', colors='black')

    # Stile globale per chiarezza
    plt.rcParams.update({'axes.grid': True})

    # ---------- 1) mdotL_vec e mdotV_vec ----------
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ln_mL, = ax1.plot(time, mdotL_vec, color='tab:blue', label='mdot liquid')
    ln_mV, = ax1.plot(time, mdotV_vec, color='tab:red', label='mdot vapor')
    ax1.set_xlabel('time [s]')
    ax1.set_ylabel('mdot [kg/s]', color='black')
    make_axes_black(ax1)

    ax1_right = ax1.twinx()
    ln_Q, = ax1_right.plot(time, Q_vec, color='tab:red', linestyle='--', label='Vapor quality')
    ax1_right.set_ylabel('Vapor quality', color='black')
    make_axes_black(ax1_right)

    ax1.legend([ln_mL, ln_mV], ['mdot liquid', 'mdot vapor'], loc='center left')
    ax1_right.legend([ln_Q], ['Vapor quality'], loc='upper right')
    ax1.set_title('Mass flow rates')
    fig1.tight_layout()

    # ---------- 2) m_vec, mL_vec, mV_vec (left) ; Q_vec (right) ----------
    fig2, ax2_left = plt.subplots(figsize=(8, 4))
    ln_mtot, = ax2_left.plot(time, m_vec, color='tab:blue', label='Total mass')
    ln_mL, = ax2_left.plot(time, mL_vec, color='tab:green', label='Liquid mass')
    ln_mV2, = ax2_left.plot(time, mV_vec, color='tab:orange', label='Vapor mass')
    ax2_left.set_xlabel('time [s]')
    ax2_left.set_ylabel('Mass [kg]', color='black')
    make_axes_black(ax2_left)

    ax2_right = ax2_left.twinx()
    ln_Q, = ax2_right.plot(time, Q_vec, color='tab:red', linestyle='--', label='Vapor quality')
    ax2_right.set_ylabel('Vapor quality', color='black')
    make_axes_black(ax2_right)

    ax2_left.legend([ln_mtot, ln_mL, ln_mV2], ['Total mass', 'Liquid mass', 'Vapor mass'], loc='upper left')
    ax2_right.legend([ln_Q], ['Vapor quality'], loc='upper right')
    ax2_left.set_title('Masses (left) and vapor quality (right)')
    fig2.tight_layout()

    # ---------- 3) ptank_vec (left y P [Pa]) ; Ttank_vec (right y T [K]) ----------
    fig3, ax3_left = plt.subplots(figsize=(8, 4))
    ln_P, = ax3_left.plot(time, ptank_vec, color='tab:blue', label='Pressure')
    ax3_left.set_xlabel('time [s]')
    ax3_left.set_ylabel('P [Pa]', color='black')
    make_axes_black(ax3_left)

    ax3_right = ax3_left.twinx()
    ln_T, = ax3_right.plot(time, Ttank_vec, color='tab:red', label='Temperature')
    ax3_right.set_ylabel('T [K]', color='black')
    make_axes_black(ax3_right)

    ax3_left.legend([ln_P], ['Pressure'], loc='upper left')
    ax3_right.legend([ln_T], ['Temperature'], loc='upper right')
    ax3_left.set_title('Tank pressure and temperature vs time')
    fig3.tight_layout()

    # ---------- 4) sL_vec e sV_vec (left) ; S_vec (right) ----------
    fig4, ax4_left = plt.subplots(figsize=(8, 4))
    ln_sL, = ax4_left.plot(time, sL_vec, color='tab:blue', label='Liquid specific entropy')
    ln_sV, = ax4_left.plot(time, sV_vec, color='tab:green', label='Vapor specific entropy')
    ax4_left.set_xlabel('time [s]')
    ax4_left.set_ylabel('s [J/kgK]', color='black')
    make_axes_black(ax4_left)

    ax4_right = ax4_left.twinx()
    ln_S, = ax4_right.plot(time, S_vec, color='tab:red', linestyle='--', label='Total entropy')
    ax4_right.set_ylabel('S [J/kg]', color='black')
    make_axes_black(ax4_right)

    ax4_left.legend([ln_sL, ln_sV], ['Liquid specific entropy', 'Vapor specific entropy'], loc='upper left')
    ax4_right.legend([ln_S], ['Total entropy'], loc='upper right')
    ax4_left.set_title('Specific and total entropy')
    fig4.tight_layout()

    plt.show()
    
    #"""


