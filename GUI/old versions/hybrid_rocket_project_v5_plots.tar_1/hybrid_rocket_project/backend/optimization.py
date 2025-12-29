"""
Mock optimization module for testing the GUI
Replace this with your actual optimization.py when integrating
"""

import numpy as np
import time


def full_range_simulation(Dport_Dt_range, Dinj_Dt_range, Lc_Dt_range, eps, ptank, Ttank,
                          CD, a, n, rho_fuel, oxidizer, fuel, pamb=0.0, gamma0=1.3):
    """
    Mock simulation function that returns dummy data with correct structure
    Replace this with your actual function from optimization.py
    """
    
    # Simulate some processing time
    time.sleep(2)
    
    # Get dimensions
    Dport_length = len(Dport_Dt_range)
    Dinj_length = len(Dinj_Dt_range)
    Lc_length = len(Lc_Dt_range)
    
    # Create dummy result arrays with realistic values
    pc_array = np.random.uniform(1e5, 5e6, (Dport_length, Dinj_length, Lc_length))
    Fpc_array = np.random.uniform(-1000, 1000, (Dport_length, Dinj_length, Lc_length))
    p_inj_array = np.random.uniform(1e5, 6e6, (Dport_length, Dinj_length, Lc_length))
    
    mdot_ox_array = np.random.uniform(0.1, 10, (Dport_length, Dinj_length, Lc_length))
    mdot_fuel_array = np.random.uniform(0.05, 5, (Dport_length, Dinj_length, Lc_length))
    mdot_array = mdot_ox_array + mdot_fuel_array
    
    Gox_array = np.random.uniform(10, 500, (Dport_length, Dinj_length, Lc_length))
    r_array = np.random.uniform(1e-5, 1e-3, (Dport_length, Dinj_length, Lc_length))
    
    MR_array = mdot_ox_array / (mdot_fuel_array + 1e-10)
    eps_array = np.random.uniform(5, 20, (Dport_length, Dinj_length, Lc_length))
    
    Tc_array = np.random.uniform(2000, 3500, (Dport_length, Dinj_length, Lc_length))
    MW_array = np.random.uniform(20, 30, (Dport_length, Dinj_length, Lc_length))
    gamma_array = np.random.uniform(1.1, 1.4, (Dport_length, Dinj_length, Lc_length))
    cs_array = np.random.uniform(800, 1200, (Dport_length, Dinj_length, Lc_length))
    
    CF_vac_array = np.random.uniform(1.5, 2.0, (Dport_length, Dinj_length, Lc_length))
    CF_array = np.random.uniform(1.2, 1.8, (Dport_length, Dinj_length, Lc_length))
    
    Ivac_array = np.random.uniform(200, 350, (Dport_length, Dinj_length, Lc_length))
    Is_array = np.random.uniform(150, 300, (Dport_length, Dinj_length, Lc_length))
    
    flag_array = np.zeros((Dport_length, Dinj_length, Lc_length))
    
    return (pc_array, Fpc_array, p_inj_array, mdot_ox_array, mdot_fuel_array, mdot_array, Gox_array,
            r_array, MR_array, eps_array, Tc_array, MW_array, gamma_array, cs_array,
            CF_vac_array, CF_array, Ivac_array, Is_array, flag_array)


if __name__ == "__main__":
    print("This is a mock optimization module for testing")
    print("Replace with your actual optimization.py when ready")
