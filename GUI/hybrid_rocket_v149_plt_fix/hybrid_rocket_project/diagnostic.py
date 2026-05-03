"""
Diagnostic script to test the optimization pipeline step by step.
Run this from the project root directory.
"""

import numpy as np
import sys

print("=" * 60)
print("HYBRID ROCKET OPTIMIZATION DIAGNOSTIC")
print("=" * 60)

# Step 1: Test imports
print("\n[1] Testing imports...")
try:
    import Performance.performance_singlepoint as perfs
    print("    ✓ Performance.performance_singlepoint imported")
except ImportError as e:
    print(f"    ✗ Failed to import performance_singlepoint: {e}")
    sys.exit(1)

try:
    import Injection.PyInjection as injection
    print("    ✓ Injection.PyInjection imported")
except ImportError as e:
    print(f"    ✗ Failed to import PyInjection: {e}")
    sys.exit(1)

try:
    import Performance.CEA_py as CEA_py
    print("    ✓ Performance.CEA_py imported")
except ImportError as e:
    print(f"    ✗ Failed to import CEA_py: {e}")
    sys.exit(1)

try:
    import Line_losses.linelosses as linelosses
    print("    ✓ Line_losses.linelosses imported")
except ImportError as e:
    print(f"    ✗ Failed to import linelosses: {e}")
    sys.exit(1)

try:
    import CoolProp.CoolProp as cp
    print("    ✓ CoolProp imported")
except ImportError as e:
    print(f"    ✗ Failed to import CoolProp: {e}")
    sys.exit(1)

try:
    from rocketcea.cea_obj import CEA_Obj
    print("    ✓ RocketCEA imported")
except ImportError as e:
    print(f"    ✗ Failed to import RocketCEA: {e}")
    sys.exit(1)

# Step 2: Set up test parameters (from optimization.py __main__)
print("\n[2] Setting up test parameters...")

# These are the WORKING parameters from the original optimization.py
ptank = 27e5  # [Pa] = 27 bar
Ttank = 288   # [K]
pamb = 1e5    # [Pa] = 1 bar
gamma0 = 1.3
CD = 0.8
a = 0.17e-3
n = 0.5
rho_fuel = 850  # [kg/m^3]

oxidizer = {
    "OxidizerCP": "NitrousOxide",
    "OxidizerCEA": "N2O",
    "Weight fraction": "100",
    "Exploded Formula": "",
    "Temperature [K]": "",
    "Specific Enthalpy [kj/mol]": ""
}

fuel = {
    "Fuels": ["paraffin"],
    "Weight fraction": ["100"],
    "Exploded Formula": ["C 73 H 124"],
    "Temperature [K]": [float(533)],
    "Specific Enthalpy [kj/mol]": [-1860.6]
}

eps = "adapt"

print(f"    ptank = {ptank} Pa ({ptank/1e5} bar)")
print(f"    Ttank = {Ttank} K")
print(f"    pamb = {pamb} Pa ({pamb/1e5} bar)")
print(f"    CD = {CD}")
print(f"    a = {a}, n = {n}")
print(f"    rho_fuel = {rho_fuel} kg/m³")
print(f"    oxidizer = {oxidizer['OxidizerCEA']} / {oxidizer['OxidizerCP']}")
print(f"    fuel = {fuel['Fuels']}")

# Step 3: Test line losses
print("\n[3] Testing line losses...")
linelosses.set_line_losses(0)
ll_value = linelosses.linelosses()
print(f"    Line losses = {ll_value} Pa")

# Step 4: Test CoolProp for N2O
print("\n[4] Testing CoolProp for NitrousOxide...")
try:
    # Get vapor pressure at tank temperature
    p_vapor = cp.PropsSI('P', 'T', Ttank, 'Q', 1, 'NitrousOxide')
    print(f"    N2O vapor pressure at {Ttank}K = {p_vapor/1e5:.2f} bar")
    
    # Get density
    rho = cp.PropsSI('D', 'P', ptank, 'T', Ttank, 'NitrousOxide')
    print(f"    N2O density at {ptank/1e5}bar, {Ttank}K = {rho:.2f} kg/m³")
except Exception as e:
    print(f"    ✗ CoolProp error: {e}")

# Step 5: Test injection mass flow
print("\n[5] Testing injection mass flow...")
# Single point test
Dport = 2.0  # Dport/Dt = 2.0
Dinj = 0.2   # Dinj/Dt = 0.2
Lc = 3.0     # Lc/Dt = 3.0
Dt = 1.0

Aport = 0.25 * np.pi * (Dport**2)
Ainj = 0.25 * np.pi * (Dinj**2)
At = 0.25 * np.pi * (Dt**2)
Ab = np.pi * Dport * Lc

print(f"    Dport/Dt = {Dport}, Dinj/Dt = {Dinj}, Lc/Dt = {Lc}")
print(f"    Aport = {Aport:.4f} m², Ainj = {Ainj:.6f} m², At = {At:.4f} m², Ab = {Ab:.4f} m²")

# Test injection at a reasonable chamber pressure
pc_test = 15e5  # 15 bar chamber pressure
p_inj = ptank  # No line losses

try:
    mdot_ox = injection.massflow(p_inj, pc_test, Ttank, CD, oxidizer['OxidizerCP'])
    print(f"    mdot_ox (per unit area) at pc={pc_test/1e5}bar = {mdot_ox:.2f} kg/(s·m²)")
    mdot_ox_total = mdot_ox * Ainj
    print(f"    mdot_ox (total) = {mdot_ox_total:.4f} kg/s")
except Exception as e:
    print(f"    ✗ Injection error: {e}")
    import traceback
    traceback.print_exc()

# Step 6: Test CEA
print("\n[6] Testing CEA...")
try:
    MR_test = 5.0  # Typical O/F ratio for N2O/paraffin
    CEA_output = CEA_py.runCEA(pc_test, MR_test, 10.0, oxidizer, fuel)
    if CEA_output and len(CEA_output) > 0:
        print(f"    CEA output at pc={pc_test/1e5}bar, MR={MR_test}:")
        print(f"      Tc = {CEA_output[0]:.1f} K")
        print(f"      MW = {CEA_output[1]:.2f} kg/kmol")
        print(f"      gamma = {CEA_output[2]:.3f}")
        print(f"      c* = {CEA_output[3]:.1f} m/s")
        print(f"      CF_vac = {CEA_output[4]:.3f}")
    else:
        print(f"    ✗ CEA returned empty output: {CEA_output}")
except Exception as e:
    print(f"    ✗ CEA error: {e}")
    import traceback
    traceback.print_exc()

# Step 7: Test calculate_performance
print("\n[7] Testing calculate_performance...")
try:
    result = perfs.calculate_performance(
        Ainj, Aport, Ab, eps, ptank, Ttank, pc_test, CD,
        a, n, rho_fuel, oxidizer, fuel, pamb, gamma0
    )
    p_inj, mdot_ox, mdot_fuel, mdot, Gox, r, MR, Tc, MW, gamma, eps_out, cs, CF_vac, CF, Ivac, Is, flag = result
    
    print(f"    Results:")
    print(f"      p_inj = {p_inj/1e5:.2f} bar")
    print(f"      mdot_ox = {mdot_ox:.4f} kg/s")
    print(f"      mdot_fuel = {mdot_fuel:.6f} kg/s")
    print(f"      mdot = {mdot:.4f} kg/s")
    print(f"      Gox = {Gox:.2f} kg/(s·m²)")
    print(f"      r = {r:.6f} m/s")
    print(f"      MR = {MR:.2f}")
    print(f"      Tc = {Tc:.1f} K")
    print(f"      c* = {cs:.1f} m/s")
    print(f"      Ivac = {Ivac:.1f} s")
    print(f"      Is = {Is:.1f} s")
    print(f"      flag = {flag}")
except Exception as e:
    print(f"    ✗ calculate_performance error: {e}")
    import traceback
    traceback.print_exc()

# Step 8: Test pressure_fun (should be near zero at correct pc)
print("\n[8] Testing pressure_fun to find equilibrium...")
try:
    # Scan pc to find where Fpc crosses zero
    pc_range = np.linspace(5e5, 25e5, 20)
    print(f"    Scanning pc from {pc_range[0]/1e5:.1f} to {pc_range[-1]/1e5:.1f} bar...")
    
    for pc in pc_range:
        try:
            Fpc = perfs.pressure_fun(Ainj, Aport, At, Ab, eps, ptank, Ttank, pc,
                                     CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma0)
            sign = "+" if Fpc > 0 else "-"
            print(f"      pc={pc/1e5:5.1f} bar -> Fpc={Fpc:12.1f} Pa ({sign})")
        except Exception as e:
            print(f"      pc={pc/1e5:5.1f} bar -> ERROR: {e}")
except Exception as e:
    print(f"    ✗ pressure_fun scan error: {e}")
    import traceback
    traceback.print_exc()

# Step 9: Test starting_pressure
print("\n[9] Testing starting_pressure...")
try:
    from backend.optimization import starting_pressure
    pc_start = starting_pressure(Ainj, Aport, At, Ab, eps, ptank, Ttank, CD, a, n,
                                  rho_fuel, oxidizer, fuel, pamb, gamma0)
    print(f"    Starting pressure = {pc_start/1e5:.2f} bar")
    
    if pc_start == 0:
        print("    ✗ starting_pressure returned 0 - no valid solution found!")
    else:
        print("    ✓ Found valid starting pressure")
except Exception as e:
    print(f"    ✗ starting_pressure error: {e}")
    import traceback
    traceback.print_exc()

# Step 10: Test get_pressure (Newton iteration)
print("\n[10] Testing get_pressure (Newton iteration)...")
try:
    from backend.optimization import get_pressure
    pc, Fpc, n_iter, maxit, gamma_out = get_pressure(Ainj, Aport, At, Ab, eps, ptank, Ttank,
                                                      CD, a, n, rho_fuel, oxidizer, fuel, pamb, gamma0)
    print(f"    Converged pc = {pc/1e5:.2f} bar")
    print(f"    Final Fpc = {Fpc:.2f} Pa")
    print(f"    Iterations = {n_iter}/{maxit}")
    print(f"    Final gamma = {gamma_out:.3f}")
    
    if pc == 0:
        print("    ✗ get_pressure returned 0 - convergence failed!")
    elif n_iter >= maxit:
        print("    ⚠ Warning: reached max iterations")
    else:
        print("    ✓ Converged successfully")
except Exception as e:
    print(f"    ✗ get_pressure error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
