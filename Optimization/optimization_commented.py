"""
Chamber Pressure Convergence Module

This module provides functions to calculate chamber pressure at convergence
for hybrid rocket engine configurations across various parameter combinations.

The solver uses a Newton-like iterative method to find the chamber pressure
that satisfies mass flow and thermodynamic equilibrium constraints.
"""

import numpy as np
import time
import Performance.performance_singlepoint as perfs


# =============================================================================
# CONSTANTS AND TYPE DEFINITIONS
# =============================================================================

DEFAULT_AMBIENT_PRESSURE = 0.0  # Pa
DEFAULT_GAMMA_GUESS = 1.3
CONVERGENCE_TOLERANCE = 1e-1  # Pa
MAX_ITERATIONS = 100
PRESSURE_PERTURBATION = 10.0  # Pa for numerical derivative


# =============================================================================
# INITIAL GUESS CALCULATION
# =============================================================================

def starting_pressure(Ainj, Aport, At, Ab, eps, ptank, Ttank, CD, a, n, 
                      rho_fuel, oxidizer, fuel, pamb=DEFAULT_AMBIENT_PRESSURE, 
                      gamma0=DEFAULT_GAMMA_GUESS):
    """
    Calculate optimal starting pressure for iterative solver.
    
    Evaluates the pressure function across a range of possible chamber pressures
    to find the best initial guess for the Newton iteration.
    
    Parameters
    ----------
    Ainj : float
        Injection area [m²]
    Aport : float
        Port area [m²]
    At : float
        Throat area [m²]
    Ab : float
        Burning area [m²]
    eps : float or str
        Expansion ratio (or "adapt" for adaptive)
    ptank : float
        Tank total pressure [Pa]
    Ttank : float
        Tank total temperature [K]
    CD : float
        Discharge coefficient [-]
    a : float
        Regression rate coefficient in r = a * Gox^n [m/s / (kg/m²s)^n]
    n : float
        Regression rate exponent in r = a * Gox^n [-]
    rho_fuel : float
        Fuel density [kg/m³]
    oxidizer : dict
        Oxidizer properties dictionary with keys:
        - "OxidizerCP": CoolProp name
        - "OxidizerCEA": CEA name
        - "Weight fraction": "100" (multi-fluid not supported)
        - "Exploded Formula": Chemical formula
        - "Temperature [K]": Temperature
        - "Specific Enthalpy [kj/mol]": Enthalpy
    fuel : dict
        Fuel properties dictionary with keys:
        - "Fuels": List of fuel names for CEA
        - "Weight fraction": List of weight fractions
        - "Exploded Formula": List of chemical formulas
        - "Temperature [K]": List of temperatures
        - "Specific Enthalpy [kj/mol]": List of enthalpies
    pamb : float, optional
        Ambient pressure [Pa] (default: 0.0)
    gamma0 : float, optional
        Initial guess for specific heat ratio [-] (default: 1.3)
    
    Returns
    -------
    float
        Best chamber pressure to start iteration [Pa].
        Returns 0 if no valid solution can be found.
    """
    # Define pressure search range (0.9*ptank accounts for pressure losses)
    p_min = max(pamb, 1.0) if pamb > 0 else 1.0
    p_max = 0.9 * ptank
    pc_range = np.linspace(p_min, p_max, num=50)
    
    # Evaluate pressure function across range
    Fpcs = np.ones_like(pc_range)
    for i, pc_try in enumerate(pc_range):
        try:
            Fpcs[i] = perfs.pressure_fun(
                Ainj, Aport, At, Ab, eps, ptank, Ttank, pc_try,
                CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma0
            )
        except Exception:
            Fpcs[i] = 1e8  # Mark failed evaluations
    
    # Remove failed evaluations
    valid_mask = Fpcs != 1e8
    Fpcs = Fpcs[valid_mask]
    pc_range = pc_range[valid_mask]
    
    # Find pressure with minimum absolute function value
    i_min = np.argmin(np.abs(Fpcs))
    pc_best = pc_range[i_min]
    
    # Check if a zero crossing exists
    all_positive = np.all(Fpcs >= 0)
    all_negative = np.all(Fpcs <= 0)
    if all_positive or all_negative:
        return 0.0  # No zero crossing found
    
    return pc_best


# =============================================================================
# ITERATIVE PRESSURE SOLVER
# =============================================================================

def get_pressure(Ainj, Aport, At, Ab, eps, ptank, Ttank, CD, a, n, 
                 rho_fuel, oxidizer, fuel, pamb=DEFAULT_AMBIENT_PRESSURE, 
                 gamma0=DEFAULT_GAMMA_GUESS):
    """
    Solve for chamber pressure using modified Newton iteration.
    
    Uses Newton's method with adaptive damping to find the chamber pressure
    that satisfies equilibrium constraints:
    
        pc_new = pc_old - k_Newton * F(pc_old) / (dF/dpc)
    
    where k_Newton ≤ 1 is adaptively reduced when the solution leaves the
    valid pressure range [pamb, 0.9*ptank].
    
    Parameters
    ----------
    Ainj, Aport, At, Ab : float
        Injection, port, throat, and burning areas [m²]
    eps : float or str
        Expansion ratio
    ptank : float
        Tank total pressure [Pa]
    Ttank : float
        Tank total temperature [K]
    CD : float
        Discharge coefficient [-]
    a, n : float
        Regression rate parameters (r = a * Gox^n)
    rho_fuel : float
        Fuel density [kg/m³]
    oxidizer, fuel : dict
        Propellant property dictionaries (see starting_pressure docstring)
    pamb : float, optional
        Ambient pressure [Pa]
    gamma0 : float, optional
        Initial specific heat ratio guess [-]
    
    Returns
    -------
    pc : float
        Converged chamber pressure [Pa]
    Fpc : float
        Final pressure function residual [Pa]
    n_iter : int
        Number of iterations performed
    maxit : int
        Maximum iterations allowed
    gamma0 : float
        Final specific heat ratio [-]
    """
    # Initialize iteration parameters
    k_Newton = 1.0  # Damping factor
    n_iter = 0
    maxit = MAX_ITERATIONS
    
    # Get initial pressure guess
    pc = starting_pressure(
        Ainj, Aport, At, Ab, eps, ptank, Ttank, CD, a, n,
        rho_fuel, oxidizer, fuel, pamb, gamma0
    )
    
    # Check if initial solution exists
    if pc == 0:
        return 0.0, 0.0, maxit + 1, maxit, gamma0
    
    # Calculate initial performance and residual
    p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, eps_out, cs, \
    CF_vac, CF, Ivac, Is, flag_performance = perfs.calculate_performance(
        Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD, a, n, 
        rho_fuel, oxidizer, fuel, pamb, gamma0
    )
    gamma0 = gamma
    
    Fpc = perfs.pressure_fun(
        Ainj, Aport, At, Ab, eps, ptank, Ttank, pc,
        CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma0
    )
    
    # Newton iteration loop
    while np.abs(Fpc) > CONVERGENCE_TOLERANCE and n_iter < maxit:
        # Calculate numerical derivative
        Fdpc = perfs.pressure_fun(
            Ainj, Aport, At, Ab, eps, ptank, Ttank, pc + PRESSURE_PERTURBATION,
            CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma0
        )
        dFpc = (Fdpc - Fpc) / PRESSURE_PERTURBATION
        
        # Avoid division by zero
        if dFpc == 0:
            dFpc = 0.01
        
        # Newton step
        pc_new = pc - k_Newton * Fpc / dFpc
        
        # Enforce pressure bounds and reduce damping if needed
        if pc_new < pamb:
            pc_new = max(0.2 * ptank, 1.5 * pamb)
            k_Newton -= 0.05
        elif pc_new >= 0.9 * ptank:
            pc_new = 0.75 * ptank
            k_Newton -= 0.05
        
        pc = pc_new
        
        # Update performance and gamma
        p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, eps_out, cs, \
        CF_vac, CF, Ivac, Is, flag_performance = perfs.calculate_performance(
            Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD, a, n,
            rho_fuel, oxidizer, fuel, pamb, gamma0
        )
        gamma0 = gamma
        
        # Recalculate residual
        Fpc = perfs.pressure_fun(
            Ainj, Aport, At, Ab, eps, ptank, Ttank, pc,
            CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma0
        )
        n_iter += 1
    
    return pc, Fpc, n_iter, maxit, gamma0


# =============================================================================
# PARAMETRIC SWEEP SIMULATION
# =============================================================================

def full_range_simulation(Dport_Dt_range, Dinj_Dt_range, Lc_Dt_range, eps, 
                          ptank, Ttank, CD, a, n, rho_fuel, oxidizer, fuel, 
                          pamb=DEFAULT_AMBIENT_PRESSURE, gamma0=DEFAULT_GAMMA_GUESS):
    """
    Run performance analysis across full parameter space.
    
    Computes converged chamber pressure and performance metrics for all
    combinations of dimensionless parameters:
    - Dport/Dt: Port-to-throat diameter ratio
    - Dinj/Dt: Injector-to-throat diameter ratio  
    - Lc/Dt: Chamber length-to-throat diameter ratio
    
    Parameters
    ----------
    Dport_Dt_range : array_like
        Port diameter / throat diameter ratios [-]
    Dinj_Dt_range : array_like
        Injector diameter / throat diameter ratios [-]
    Lc_Dt_range : array_like
        Chamber length / throat diameter ratios [-]
    eps : float or str
        Expansion ratio
    ptank : float
        Tank pressure [Pa]
    Ttank : float
        Tank temperature [K]
    CD : float
        Discharge coefficient [-]
    a, n : float
        Regression rate parameters
    rho_fuel : float
        Fuel density [kg/m³]
    oxidizer, fuel : dict
        Propellant property dictionaries
    pamb : float, optional
        Ambient pressure [Pa]
    gamma0 : float, optional
        Initial gamma guess [-]
    
    Returns
    -------
    tuple of ndarray
        19 3D arrays (Dport, Dinj, Lc) containing:
        
        Pressures and residuals:
        - pc_array: Chamber pressure [Pa]
        - Fpc_array: Pressure function residual [Pa]
        - p_inj_array: Injection pressure [Pa]
        
        Mass flows (normalized by Dt²):
        - mdot_ox_array: Oxidizer mass flow [kg/(s·m²)]
        - mdot_fuel_array: Fuel mass flow [kg/(s·m²)]
        - mdot_array: Total mass flow [kg/(s·m²)]
        - Gox_array: Oxidizer mass flux [kg/(s·m²)]
        - r_array: Regression rate [m/s]
        
        Mixture and geometry:
        - MR_array: Mixture ratio (O/F) [-]
        - eps_array: Expansion ratio [-]
        
        Thermochemistry:
        - Tc_array: Chamber temperature [K]
        - MW_array: Molecular weight [kg/kmol]
        - gamma_array: Specific heat ratio [-]
        - cs_array: Characteristic velocity [m/s]
        
        Performance:
        - CF_vac_array: Vacuum thrust coefficient [-]
        - CF_array: Thrust coefficient [-]
        - Ivac_array: Vacuum specific impulse [s]
        - Is_array: Specific impulse [s]
        
        Convergence flags:
        - flag_array: Convergence status
          * 0: Converged successfully
          * 1: Pressure iteration diverged
          * -1: CEA (chemistry) diverged
          * 2: Both pressure and CEA diverged
          * 10: No pressure solution exists
    """
    # Get array dimensions
    n_Dport = len(Dport_Dt_range)
    n_Dinj = len(Dinj_Dt_range)
    n_Lc = len(Lc_Dt_range)
    shape = (n_Dport, n_Dinj, n_Lc)
    
    # Initialize output arrays
    # Pressures
    pc_array = np.zeros(shape)
    Fpc_array = np.zeros(shape)
    p_inj_array = np.zeros(shape)
    
    # Mass flows
    mdot_ox_array = np.zeros(shape)
    mdot_fuel_array = np.zeros(shape)
    mdot_array = np.zeros(shape)
    Gox_array = np.zeros(shape)
    r_array = np.zeros(shape)
    
    # Mixture and geometry
    MR_array = np.zeros(shape)
    eps_array = np.zeros(shape)
    
    # Thermochemistry
    Tc_array = np.zeros(shape)
    MW_array = np.zeros(shape)
    gamma_array = np.zeros(shape)
    cs_array = np.zeros(shape)
    
    # Performance
    CF_vac_array = np.zeros(shape)
    CF_array = np.zeros(shape)
    Ivac_array = np.zeros(shape)
    Is_array = np.zeros(shape)
    
    # Convergence flags (initialize to 100 for safety)
    flag_array = 100 * np.ones(shape)
    
    # Reference throat diameter (normalized to 1)
    Dt = 1.0
    At = 0.25 * np.pi * Dt**2
    
    # Loop over parameter space
    for i_Dport, Dport in enumerate(Dport_Dt_range):
        for i_Dinj, Dinj in enumerate(Dinj_Dt_range):
            for i_Lc, Lc in enumerate(Lc_Dt_range):
                
                # Calculate geometric areas
                Aport = 0.25 * np.pi * Dport**2
                Ainj = 0.25 * np.pi * Dinj**2
                Ab = np.pi * Dport * Lc
                
                # Solve for chamber pressure
                pc, Fpc, n_iter, maxit, gamma_updated = get_pressure(
                    Ainj, Aport, At, Ab, eps, ptank, Ttank, CD, a, n,
                    rho_fuel, oxidizer, fuel, pamb, gamma0
                )
                
                # Calculate performance if solution found
                if pc != 0:
                    (p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, 
                     gamma, eps_out, cs, CF_vac, CF, Ivac, Is, 
                     flag_performance) = perfs.calculate_performance(
                        Ainj, Aport, Ab, eps, ptank, Ttank, pc, CD, a, n,
                        rho_fuel, oxidizer, fuel, pamb, gamma_updated
                    )
                    
                    # Store results
                    pc_array[i_Dport, i_Dinj, i_Lc] = pc
                    Fpc_array[i_Dport, i_Dinj, i_Lc] = Fpc
                    p_inj_array[i_Dport, i_Dinj, i_Lc] = p_inj
                    
                    mdot_ox_array[i_Dport, i_Dinj, i_Lc] = mdot_ox
                    mdot_fuel_array[i_Dport, i_Dinj, i_Lc] = mdot_fuel
                    mdot_array[i_Dport, i_Dinj, i_Lc] = mdot
                    Gox_array[i_Dport, i_Dinj, i_Lc] = Gox
                    r_array[i_Dport, i_Dinj, i_Lc] = r
                    
                    MR_array[i_Dport, i_Dinj, i_Lc] = MR
                    eps_array[i_Dport, i_Dinj, i_Lc] = eps_out
                    
                    Tc_array[i_Dport, i_Dinj, i_Lc] = Tc
                    MW_array[i_Dport, i_Dinj, i_Lc] = MW
                    gamma_array[i_Dport, i_Dinj, i_Lc] = gamma
                    cs_array[i_Dport, i_Dinj, i_Lc] = cs
                    
                    CF_vac_array[i_Dport, i_Dinj, i_Lc] = CF_vac
                    CF_array[i_Dport, i_Dinj, i_Lc] = CF
                    Ivac_array[i_Dport, i_Dinj, i_Lc] = Ivac
                    Is_array[i_Dport, i_Dinj, i_Lc] = Is
                else:
                    flag_performance = 0
                
                # Set convergence flag
                if n_iter == maxit and flag_performance == 1:
                    flag_array[i_Dport, i_Dinj, i_Lc] = 2  # Both diverged
                elif n_iter == maxit:
                    flag_array[i_Dport, i_Dinj, i_Lc] = 1  # Pressure diverged
                elif n_iter == maxit + 1:
                    flag_array[i_Dport, i_Dinj, i_Lc] = 10  # No solution
                elif flag_performance == 1:
                    flag_array[i_Dport, i_Dinj, i_Lc] = -1  # CEA diverged
                else:
                    flag_array[i_Dport, i_Dinj, i_Lc] = 0  # Converged
    
    return (pc_array, Fpc_array, p_inj_array, mdot_ox_array, mdot_fuel_array, 
            mdot_array, Gox_array, r_array, MR_array, eps_array, Tc_array, 
            MW_array, gamma_array, cs_array, CF_vac_array, CF_array, 
            Ivac_array, Is_array, flag_array)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Define parameter ranges
    Dport_Dt_range = np.arange(3.5, 5.0, 0.5)
    Dinj_Dt_range = np.arange(0.8, 1.0, 0.05)
    Lc_Dt_range = np.arange(8, 10, 1)
    
    # Operating conditions
    eps = "adapt"
    ptank = 55e5  # Pa
    Ttank = 288  # K
    pamb = 1e5  # Pa
    CD = 0.8
    
    # Fuel properties (paraffin)
    a = 0.17e-3  # Regression rate coefficient
    n = 0.5  # Regression rate exponent
    rho_fuel = 850  # kg/m³
    
    # Oxidizer properties (N2O)
    oxidizer = {
        "OxidizerCP": "NitrousOxide",
        "OxidizerCEA": "N2O",
        "Weight fraction": "100",
        "Exploded Formula": "",
        "Temperature [K]": "",
        "Specific Enthalpy [kj/mol]": ""
    }
    
    # Fuel properties (paraffin wax)
    fuel = {
        "Fuels": ["paraffin"],
        "Weight fraction": ["100"],
        "Exploded Formula": ["C 73 H 124"],
        "Temperature [K]": [533.0],
        "Specific Enthalpy [kj/mol]": [-1860.6]
    }
    
    # Run simulation
    print("Starting parametric simulation...")
    start = time.process_time()
    
    results = full_range_simulation(
        Dport_Dt_range, Dinj_Dt_range, Lc_Dt_range, eps, ptank, Ttank,
        CD, a, n, rho_fuel, oxidizer, fuel, pamb
    )
    
    end = time.process_time()
    runtime = end - start
    
    # Unpack results
    (pc_array, Fpc_array, p_inj_array, mdot_ox_array, mdot_fuel_array,
     mdot_array, Gox_array, r_array, MR_array, eps_array, Tc_array,
     MW_array, gamma_array, cs_array, CF_vac_array, CF_array,
     Ivac_array, Is_array, flag_array) = results
    
    # Display results
    print("\nExpansion Ratios:")
    print(eps_array)
    print("\nConvergence Flags:")
    print(flag_array)
    print(f"\nRuntime: {runtime:.3f} s")
