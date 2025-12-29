"""
Test grain geometry generation
"""
import numpy as np
import sys
sys.path.insert(0, '/home/claude/hybrid_rocket_project')

from Geometry import geometry_calculation as geom

# Test cylindrical
print("=== Testing Cylindrical Grain ===")
Dport = 0.05  # 50mm port
x_cyl = np.array([Dport / 2])
y_cyl = np.array([0.0])
Ap, Ab = geom.calculate_surfaces_from_points(x_cyl, y_cyl, lc=0.3, step=0.0)
Deq = np.sqrt(4 * Ap / np.pi)
print(f"Port diameter: {Deq*1000:.2f} mm (target: {Dport*1000:.2f} mm)")
print(f"Port area: {Ap*1e6:.2f} mm²")
print(f"Burning area: {Ab*1e6:.2f} mm²")
print()

# Test 6-point star
print("=== Testing Star (6 points) ===")
n_sides = 6
inner_r = 0.02
outer_r = 0.04

# Create star
x_star = []
y_star = []
theta_double = np.linspace(0, 2*np.pi, 2*n_sides, endpoint=False)
for i, t in enumerate(theta_double):
    if i % 2 == 0:
        r = outer_r
    else:
        r = inner_r
    x_star.append(r * np.cos(t))
    y_star.append(r * np.sin(t))
x_star = np.array(x_star)
y_star = np.array(y_star)

# Sort and translate
x_star, y_star = geom.sort_input(x_star, y_star, z=1)
x_star, y_star = geom.translate_figure(x_star, y_star)

# Calculate
Ap_star, Ab_star = geom.calculate_surfaces_from_points(x_star, y_star, lc=0.3, step=0.0)
Deq_star = np.sqrt(4 * Ap_star / np.pi)

print(f"Number of points: {len(x_star)}")
print(f"Equivalent diameter: {Deq_star*1000:.2f} mm")
print(f"Port area: {Ap_star*1e6:.2f} mm²")
print(f"Burning area: {Ab_star*1e6:.2f} mm²")
print()

# Now scale to target Dport
print("=== Scaling Star to Target Dport ===")
scale_factor = Dport / Deq_star
x_scaled = x_star * scale_factor
y_scaled = y_star * scale_factor

Ap_scaled, Ab_scaled = geom.calculate_surfaces_from_points(x_scaled, y_scaled, lc=0.3, step=0.0)
Deq_scaled = np.sqrt(4 * Ap_scaled / np.pi)

print(f"Scale factor: {scale_factor:.4f}")
print(f"Equivalent diameter: {Deq_scaled*1000:.2f} mm (target: {Dport*1000:.2f} mm)")
print(f"Port area: {Ap_scaled*1e6:.2f} mm²")
print(f"Burning area: {Ab_scaled*1e6:.2f} mm²")
print()

# Test wagon wheel
print("=== Testing Wagon Wheel ===")
n_sides = 8
x_wagon = []
y_wagon = []
theta = np.linspace(0, 2*np.pi, n_sides, endpoint=False)
for i, t in enumerate(theta):
    # Main circle point
    x_wagon.append(outer_r * np.cos(t))
    y_wagon.append(outer_r * np.sin(t))
    # Add notch point
    t_notch = t + np.pi/n_sides
    x_wagon.append(inner_r * np.cos(t_notch))
    y_wagon.append(inner_r * np.sin(t_notch))

x_wagon = np.array(x_wagon)
y_wagon = np.array(y_wagon)

x_wagon, y_wagon = geom.sort_input(x_wagon, y_wagon, z=1)
x_wagon, y_wagon = geom.translate_figure(x_wagon, y_wagon)

Ap_wagon, Ab_wagon = geom.calculate_surfaces_from_points(x_wagon, y_wagon, lc=0.3, step=0.0)
Deq_wagon = np.sqrt(4 * Ap_wagon / np.pi)

print(f"Number of points: {len(x_wagon)}")
print(f"Equivalent diameter: {Deq_wagon*1000:.2f} mm")
print(f"Port area: {Ap_wagon*1e6:.2f} mm²")
print(f"Burning area: {Ab_wagon*1e6:.2f} mm²")

print("\n=== All Tests Complete ===")
