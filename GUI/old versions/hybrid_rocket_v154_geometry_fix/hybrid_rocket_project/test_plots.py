#!/usr/bin/env python3
"""
Test script for optimization output visualization.
Creates mock data and tests the plotting functionality.
"""

import sys
import os

# Add project to path
sys.path.insert(0, '/home/claude/hybrid_rocket_project')

import tkinter as tk
import numpy as np
from config.constants import COLORS
from gui.pages.optimization_output_page import OptimizationOutputPage

def create_mock_results(n_dport=10, n_dinj=10, n_lc=10):
    """Create mock optimization results for testing"""
    
    # Create coordinate grids
    dport_range = np.linspace(2.3, 5.0, n_dport)
    dinj_range = np.linspace(0.8, 1.0, n_dinj)
    lc_range = np.linspace(8, 15, n_lc)
    
    # Create 3D meshgrid for generating realistic-looking data
    Dport, Dinj, Lc = np.meshgrid(dport_range, dinj_range, lc_range, indexing='ij')
    
    # Generate mock data with some physical-like relationships
    results = {
        # Performance arrays
        'pc_array': 3e6 + 1e6 * np.sin(Dport) * np.cos(Dinj) * (Lc/10),  # Pa
        'Fpc_array': np.random.randn(n_dport, n_dinj, n_lc) * 100,
        'p_inj_array': 4e6 + 0.5e6 * Dport * Dinj,  # Pa
        
        'mdot_ox_array': 20000 + 10000 * (Dinj ** 2) / (Dport ** 0.5),
        'mdot_fuel_array': 2000 + 1000 * (Dport / Lc),
        'mdot_array': 22000 + 11000 * (Dinj ** 2) / (Dport ** 0.5),
        'Gox_array': 100 + 50 * (1/Dport) * (Dinj ** 2),
        
        'r_array': 1e-4 + 5e-5 * np.sqrt(Dinj / Dport),
        'MR_array': 5 + 3 * (Dinj / Dport) * (Lc / 10),
        'eps_array': 10 + 5 * np.ones_like(Dport),
        
        'Tc_array': 2800 + 400 * np.sin(Dport * Dinj),
        'MW_array': 25 + 3 * np.cos(Dport),
        'gamma_array': 1.2 + 0.1 * np.random.rand(n_dport, n_dinj, n_lc),
        'cs_array': 1400 + 200 * np.sin(Dport) * np.cos(Lc/10),
        
        'CF_vac_array': 1.5 + 0.2 * np.sin(Dport * Dinj),
        'CF_array': 1.3 + 0.2 * np.sin(Dport * Dinj) * 0.9,
        'Ivac_array': 220 + 40 * np.sin(Dport) * (Lc/10),
        'Is_array': 200 + 35 * np.sin(Dport) * (Lc/10),
        
        'flag_array': np.zeros((n_dport, n_dinj, n_lc))
    }
    
    ranges = {
        'Dport_Dt_range': dport_range,
        'Dinj_Dt_range': dinj_range,
        'Lc_Dt_range': lc_range
    }
    
    return results, ranges


def test_optimization_output():
    """Test the optimization output page with mock data"""
    
    print("Creating test window...")
    root = tk.Tk()
    root.title("Test - Optimization Output")
    root.geometry("1400x900")
    root.configure(bg=COLORS['bg_dark'])
    
    # Create main frame
    main_frame = tk.Frame(root, bg=COLORS['bg_dark'])
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Create the optimization output page
    print("Creating OptimizationOutputPage...")
    page = OptimizationOutputPage(main_frame, controller=None)
    
    # Generate mock data
    print("Generating mock data...")
    results, ranges = create_mock_results(n_dport=15, n_dinj=15, n_lc=10)
    
    # Display results
    print("Displaying results...")
    page.display_results(results, ranges)
    
    print("Test window ready. Close window to exit.")
    root.mainloop()


if __name__ == "__main__":
    test_optimization_output()
