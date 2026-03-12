"""
Simple test to verify the backend optimization works correctly.
Run this from the hybrid_rocket_project directory.
"""
import numpy as np

# Add project root to path
import sys
sys.path.insert(0, '.')

from backend import optimization as opt

# Test parameters - same as in your working optimization.py __main__
Dport_Dt_range = np.array([1.5, 2.0, 2.5])  # Small range for quick test
Dinj_Dt_range = np.array([0.1, 0.2, 0.3])
Lc_Dt_range = np.array([2.0, 3.0])

eps = "adapt"
ptank = 27e5  # [Pa]
Ttank = 288  # [K]
pamb = 1e5  # [Pa]
gamma0 = 1.3
CD = 0.8
a = 0.17e-3
n = 0.5
rho_fuel = 850  # [kg/m^3]

# CORRECT oxidizer format
oxidizer = {
    "OxidizerCP": "NitrousOxide",
    "OxidizerCEA": "N2O",
    "Weight fraction": "100",
    "Exploded Formula": "",
    "Temperature [K]": "",
    "Specific Enthalpy [kj/mol]": ""
}

# CORRECT fuel format
fuel = {
    "Fuels": ["paraffin"],
    "Weight fraction": ["100"],
    "Exploded Formula": ["C 73 H 124"],
    "Temperature [K]": [float(533)],
    "Specific Enthalpy [kj/mol]": [-1860.6]
}

print("=" * 60)
print("BACKEND TEST")
print("=" * 60)
print(f"\nOxidizer: {oxidizer}")
print(f"\nFuel: {fuel}")
print(f"\nRunning optimization with {len(Dport_Dt_range)}x{len(Dinj_Dt_range)}x{len(Lc_Dt_range)} = {len(Dport_Dt_range)*len(Dinj_Dt_range)*len(Lc_Dt_range)} iterations...")

def progress(current, total, msg):
    print(f"  [{current}/{total}] {msg}")

results = opt.full_range_simulation(
    Dport_Dt_range, Dinj_Dt_range, Lc_Dt_range,
    eps, ptank, Ttank, CD, a, n, rho_fuel,
    oxidizer, fuel, pamb, gamma0,
    progress_callback=progress
)

pc_array = results[0]
Is_array = results[17]
flag_array = results[18]

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
print(f"\nChamber Pressure (pc) array:")
print(pc_array)
print(f"\nSpecific Impulse (Is) array:")
print(Is_array)
print(f"\nFlag array (0=good, 1=max iter, 10=no solution):")
print(flag_array)
print(f"\nMax Is: {np.max(Is_array):.1f} s")
print(f"Max pc: {np.max(pc_array)/1e5:.2f} bar")

# Check if all zeros
if np.all(pc_array == 0):
    print("\n*** WARNING: All values are ZERO! Something is wrong. ***")
else:
    print("\n*** SUCCESS: Got non-zero values! ***")
