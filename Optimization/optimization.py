"""
This file provides the functions needed to get the chamber pressure
at convergence for every parameter combination.
"""
import numpy as np
import time
import Performance.performance_singlepoint as perfs


def starting_pressure(Ainj, Aport, At, Ab, eps, ptank, Ttank, CD, a, n, rho_fuel, oxidizer, fuel,
                                  pamb=0.0, gamma0=1.3):
    """
    This function returns the best value to start the iteration.
    :param Ainj     : Injection Area                               [m^2]
    :param Aport    : Port Area                                    [m^2]
    :param Ab       : Burning Area                                 [m^2]
    :param eps      : Expantion Ratio input
    :param ptank    : Tank total pressure                          [Pa]
    :param Ttank    : Tank total temperature                       [K]
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
    :return: Chamber pressure to start
    """

    if pamb <= 0: # pamb should never be negative obviously but never trust the user
        pc_range_a = np.linspace(1, 0.8 * ptank, 100)
        pc_range_b = np.linspace(0.8 * ptank, ptank, 100)
        pc_range = np.concatenate((pc_range_a, pc_range_b[1:]))
    else:
        pc_range_a = np.linspace(pamb, 0.8 * ptank, 100)
        pc_range_b = np.linspace(0.8 * ptank, ptank, 100)
        pc_range = np.concatenate((pc_range_a, pc_range_b[1:]))

    Fpcs = np.ones(np.shape(pc_range))

    for i, pc_try in enumerate(pc_range):
        try:
            Fpcs[i] = perfs.pressure_fun(Ainj, Aport, At, Ab, eps, ptank, Ttank, pc_try,
                                         CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma0)
        except:
            Fpcs[i] = 1e8

    # remove bad solutions
    mask = Fpcs != 1e8
    Fpcs = Fpcs[mask]
    pc_range = pc_range[mask]

    i_min = np.argmin(np.abs(Fpcs)) # absolute value!!!!!!!
    pc_best = pc_range[i_min]

    if np.all(abs(Fpcs)==Fpcs) or np.all(-abs(Fpcs)==Fpcs):
        pc_best = 0 # No zero can be found, don't waste time

    return pc_best


def get_pressure(Ainj, Aport, At, Ab, eps, ptank, Ttank, CD, a, n, rho_fuel, oxidizer, fuel,
                                  pamb=0.0, gamma0=1.3):
    """
    This function iterates with a Newton-like method to find the zero of the chamber pressure function.
    F(pc_new) - F(pc_old) = (dF/dpc)/k_Newton * (pc_new - pc_old)
    with F(pc_new) = 0
    => pc_new = pc_old - k_Newton*F(pc_old)/(dF/dpc)
    We use a constant k_Newton <=1 to increase the slope of the line
    to avoid falling out of the possible range.
    k_Newton starts from 1, every time the pressure falls out of the range [pamb, pinj],
    k_Newton = k_Newton - 0.05
    :param Ainj: Injection Area                             [m^2]
    :param Aport: Port Area                                 [m^2]
    :param At: Throat Area                                  [m^2]
    :param Ab: Burning Area                                 [m^2]
    :param eps: Expantion Ratio
    :param ptank: Tank total pressure                       [Pa]
    :param Ttank: Tank total temperature                    [K]
    :param CD: Discharge coefficient
    :param a: fuel regression rate coefficient (r=a*Gox^n)
    :param n: fuel regression rate exponent (r=a*Gox^n)
    :param rho_fuel: fuel density                           [kg/m^3]
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
    :param pamb: Ambient pressure                            [Pa]
    :param gamma0   : Guess for specific heat ratio
    :return: pc (Chamber pressure)                           [Pa],
            Fpc (Chamber pressure function)                  [Pa],
            n_iter (number of iteration at stop),
            maxit (maximum number of iterations)
    """
    k_Newton = 1
    n_iter = 0
    maxit = 1000

    dpc = 10 #[Pa] Small value for our purposes.
    # Probably every purpose if you're not dealing with void chambers.

    pc = starting_pressure(Ainj, Aport, At, Ab, eps, ptank, Ttank, CD, a, n,
                                 rho_fuel, oxidizer, fuel, pamb, gamma0)
    if pc == 0:
        n_iter = maxit + 1
        Fpc = 0
    else:
        p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, eps_out, cs, CF_vac, CF, Ivac, Is, flag_performance\
            = perfs.calculate_performance(Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD,
                                          a, n, rho_fuel, oxidizer, fuel, pamb, gamma0)
        gamma0 = gamma

        Fpc = perfs.pressure_fun(Ainj, Aport, At, Ab, eps, ptank, Ttank, pc,
                                 CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma0)


    while (np.abs(Fpc) > 1e-1) & (n_iter < maxit):
        Fdpc = perfs.pressure_fun(Ainj, Aport, At, Ab, eps, ptank, Ttank, (pc+dpc),
                             CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma0)

        dFpc = (Fdpc - Fpc)/dpc

        if dFpc == 0:
            dFpc = 0.01

        pc = pc - k_Newton*Fpc/dFpc

        if pc <= pamb:
            pc = max(0.2 * ptank, 1.5 * pamb)
            k_Newton = k_Newton - 0.05
        elif pc >= ptank:
            pc = 0.75 * ptank
            k_Newton = k_Newton - 0.05

        p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, eps_out, cs, CF_vac, CF, Ivac, Is, flag_performance \
            = perfs.calculate_performance(Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD,
                                          a, n, rho_fuel, oxidizer, fuel, pamb, gamma0)
        gamma0 = gamma

        Fpc = perfs.pressure_fun(Ainj, Aport, At, Ab, eps, ptank, Ttank, pc,
                                 CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma0)
        n_iter += 1

    return pc, Fpc, n_iter, maxit, gamma0


def full_range_simulation(Dport_Dt_range, Dinj_Dt_range, Lc_Dt_range, eps, ptank, Ttank,
                          CD, a, n, rho_fuel, oxidizer, fuel, pamb=0.0, gamma0=1.3):
    """
    This functions runs the performances and finds the pressure for every configuration of the parameters.
    :param Dport_Dt_range: First adimensional parameter
    :param Dinj_Dt_range: Second adimensional parameter
    :param Lc_Dt_range: Third adimensional parameter
    :param eps: Expantion ratio input
    :param ptank: Tank pressure [Pa]
    :param Ttank: Tank temperature [K]
    :param CD: Discharge coefficient
    :param a: Regression rate coefficient (r=a*Gox^n)
    :param n: Regression rate exponent (r=a*Gox^n)
    :param rho_fuel: Fuel density
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
    :param pamb: Ambient pressure [Pa]
    :return: pc_array (Chamber pressure array) [Pa],
            Fpc_array (Chamber pressure function array) [Pa],
            p_inj_array (Injection pressure array) [Pa],
            mdot_ox_array (Oxidizer mass flow corrected with squared throad diameter array) [kg/(s*m**2)],
            mdot_fuel_array (Fuel mass flow corrected with squared throad diameter array) [kg/(s*m**2)],
            mdot_array (Total mass flow corrected with squared throad diameter array) [kg/(s*m**2)],
            Gox_array (Oxidizer mass flux array [kg/s*m**2],
            r_array (Regression rate array) [m/s],
            MR_array (Mixture Ratio array),
            eps_array (Expansion ratio array),
            Tc_array (Chamber Temperature array) [K],
            MW_array (Molecular weight array) [kg/kmol],
            gamma_array (Gamma array),
            cs_array (Characteristic velocity array) [m/s],
            CF_vac_array (Thrust coefficient in vacuum array),
            CF_array (Thrust coefficient array),
            Ivac_array (Specific impulse in vacuum array), [s]
            Is_array (Specific impulse array), [s]
            flag_array (0=converged, 1=pressure diverged, -1=CEA diverged, 2=both diverged, 10=no pressure solution exists)
    """

    Dport_length = np.size(Dport_Dt_range)
    Dinj_length = np.size(Dinj_Dt_range)
    Lc_length = np.size(Lc_Dt_range)

    #Create a three-dimensional array for every output
    pc_array        = np.zeros((Dport_length, Dinj_length, Lc_length))
    Fpc_array       = np.zeros((Dport_length, Dinj_length, Lc_length))
    p_inj_array     = np.zeros((Dport_length, Dinj_length, Lc_length))

    mdot_ox_array   = np.zeros((Dport_length, Dinj_length, Lc_length))
    mdot_fuel_array = np.zeros((Dport_length, Dinj_length, Lc_length))
    mdot_array      = np.zeros((Dport_length, Dinj_length, Lc_length))
    Gox_array       = np.zeros((Dport_length, Dinj_length, Lc_length))
    r_array         = np.zeros((Dport_length, Dinj_length, Lc_length))

    MR_array        = np.zeros((Dport_length, Dinj_length, Lc_length))
    eps_array       = np.zeros((Dport_length, Dinj_length, Lc_length))

    Tc_array        = np.zeros((Dport_length, Dinj_length, Lc_length))
    MW_array        = np.zeros((Dport_length, Dinj_length, Lc_length))
    gamma_array     = np.zeros((Dport_length, Dinj_length, Lc_length))
    cs_array        = np.zeros((Dport_length, Dinj_length, Lc_length))
    CF_vac_array    = np.zeros((Dport_length, Dinj_length, Lc_length))
    CF_array        = np.zeros((Dport_length, Dinj_length, Lc_length))
    Ivac_array      = np.zeros((Dport_length, Dinj_length, Lc_length))
    Is_array        = np.zeros((Dport_length, Dinj_length, Lc_length))

    flag_array      = 100*np.ones((Dport_length, Dinj_length, Lc_length)) # ones to be sure


    Dt = 1
    for ind_Dport, Dport in enumerate(Dport_Dt_range):
        for ind_Dinj, Dinj in enumerate(Dinj_Dt_range):
            for ind_Lc, Lc in enumerate(Lc_Dt_range):
                # Calculate areas (A/Dt**2)
                Aport = 0.25*np.pi*(Dport**2)
                Ainj = 0.25*np.pi*(Dinj**2)
                At = 0.25*np.pi*(Dt**2)
                Ab = np.pi*Dport*Lc
                pc, Fpc, n_iter, maxit, gamma0 = get_pressure(Ainj, Aport, At, Ab, eps, ptank, Ttank,
                                                      CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma0)

                if pc != 0:
                    (p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, eps_out, cs,
                     CF_vac, CF, Ivac, Is, flag_performance) = \
                        (perfs.calculate_performance(Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD, a, n, rho_fuel,
                                                     oxidizer, fuel, pamb, gamma0))

                    # Write outputs
                    pc_array[ind_Dport, ind_Dinj, ind_Lc]           = pc # [Pa]
                    Fpc_array[ind_Dport, ind_Dinj, ind_Lc]          = Fpc # [Pa]
                    p_inj_array[ind_Dport, ind_Dinj, ind_Lc]        = p_inj #[Pa]

                    mdot_ox_array[ind_Dport, ind_Dinj, ind_Lc]      = mdot_ox #mdot_ox/Dt**2 [kg/(s*m**2)]
                    mdot_fuel_array[ind_Dport, ind_Dinj, ind_Lc]    = mdot_fuel #mdot_fuel/Dt**2 [kg/(s*m**2)]
                    mdot_array[ind_Dport, ind_Dinj, ind_Lc]         = mdot #mdot/Dt**2 [kg/(s*m**2)]
                    Gox_array[ind_Dport, ind_Dinj, ind_Lc]          = Gox # [kg/(s*m**2)]
                    r_array[ind_Dport, ind_Dinj, ind_Lc]            = r # [m/s]

                    MR_array[ind_Dport, ind_Dinj, ind_Lc]           = MR
                    eps_array[ind_Dport, ind_Dinj, ind_Lc]          = eps_out

                    Tc_array[ind_Dport, ind_Dinj, ind_Lc]           = Tc # [K]
                    MW_array[ind_Dport, ind_Dinj, ind_Lc]           = MW # [kg/kmol]
                    gamma_array[ind_Dport, ind_Dinj, ind_Lc]        = gamma
                    cs_array[ind_Dport, ind_Dinj, ind_Lc]           = cs # [m/s]
                    CF_vac_array[ind_Dport, ind_Dinj, ind_Lc]       = CF_vac
                    CF_array[ind_Dport, ind_Dinj, ind_Lc]           = CF
                    Ivac_array[ind_Dport, ind_Dinj, ind_Lc]         = Ivac #[s]
                    Is_array[ind_Dport, ind_Dinj, ind_Lc]           = Is #[s]
                else:
                    flag_performance = 0


                if (n_iter == maxit) and (flag_performance == 1):
                    flag_array[ind_Dport, ind_Dinj, ind_Lc]     = 2

                elif (n_iter == maxit):
                    flag_array[ind_Dport, ind_Dinj, ind_Lc] = 1

                elif (n_iter == maxit+1):
                    flag_array[ind_Dport, ind_Dinj, ind_Lc] = 10

                elif (flag_performance == 1):
                    flag_array[ind_Dport, ind_Dinj, ind_Lc] = -1

                else:
                    flag_array[ind_Dport, ind_Dinj, ind_Lc]     = 0

    return (pc_array, Fpc_array, p_inj_array, mdot_ox_array, mdot_fuel_array, mdot_array, Gox_array,
            r_array, MR_array, eps_array, Tc_array, MW_array, gamma_array, cs_array,
            CF_vac_array, CF_array, Ivac_array, Is_array, flag_array)


if __name__=="__main__":
    #"""
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
    """

    Dport_Dt_range = np.arange(3.5,5,0.5)
    Dinj_Dt_range = np.arange(0.8,1,0.05)
    Lc_Dt_range = np.arange(8,10,1)
    #"""

    eps = "adapt"
    ptank = 55e5  # [Pa]
    Ttank = 288  # [K]
    pamb = 1e5  # [Pa]
    gamma0 = 1.3
    CD = 0.8
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

    start = time.process_time()

    #"""
    pc_start = starting_pressure(Ainj, Aport, At, Ab, eps, ptank, Ttank, CD, a, n,
                                 rho_fuel, oxidizer, fuel, pamb, gamma0)

    if pc_start != 0:
        Fpc_start = perfs.pressure_fun(Ainj, Aport, At, Ab, eps, ptank, Ttank, pc_start,
                                             CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma0)
        pc, Fpc, n_end, maxit, gamma_out = get_pressure(Ainj, Aport, At, Ab, eps, ptank, Ttank, CD, a, n,
                                     rho_fuel, oxidizer, fuel, pamb, gamma0)
        (p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, eps_out, cs,
         CF_vac, CF, Ivac, Is, flag_performance) = \
            (perfs.calculate_performance(Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD, a, n, rho_fuel,
                                         oxidizer, fuel, pamb, gamma0))

    else:
        Fpc_start = 0
        pc = 0
        Fpc = 0
        n_end = 0
        maxit = 0
        gamma_out = 100

    """
    (pc_array, Fpc_array, p_inj_array, mdot_ox_array, mdot_fuel_array, mdot_array, Gox_array,
     r_array, MR_array, eps_array, Tc_array, MW_array, gamma_array, cs_array,
     CF_vac_array, CF_array, Ivac_array, Is_array, flag_array) = (
        full_range_simulation(Dport_Dt_range, Dinj_Dt_range, Lc_Dt_range, eps, ptank, Ttank,
                          CD, a, n, rho_fuel, oxidizer, fuel, pamb))
    #"""
    end = time.process_time()
    runtime = (end - start)

    #"""
    print("pc_start=    "+str(pc_start)+"Pa")
    print("Fpc_start=   "+str(Fpc_start)+"Pa")
    print("pc=          "+str(pc)+"Pa")
    print("Fpc=         "+str(Fpc)+"Pa")
    print("gamma=       "+str(gamma_out))
    print("n_end=       "+str(n_end)+"/"+str(maxit))
    print("mdot_ox=     "+str(mdot_ox)+"kg/s")
    print("mdot_fuel=   "+str(mdot_fuel)+"kg/s")
    print("mdot=        "+str(mdot)+"kg/s")
    """
    print("eps=")
    print(eps_array)
    print("flag=")
    print(flag_array)
    #"""
    print("runtime=     "+str(runtime)+"s")


## end of file