"""
This script provides the function to dimensionalize the given geometry according to required port area and burn area.
"""
import numpy as np
import matplotlib.pyplot as plt
import Geometry.geometry_calculation as geom

def dimensionalize_geometry(x, y, Dp, Lc, p=0.0):
    Ap_wanted, Ab_wanted = 0.25 * np.pi * (Dp**2), np.pi * Dp * Lc
    Ap_0, Ab_0 = geom.calculate_surfaces_from_points(x, y, p, p)
    Deq_0 = np.sqrt(4 * Ap_0 / np.pi)

    x_1 = Dp * x / Deq_0
    y_1 = Dp * y / Deq_0
    p_1 = Dp * p / Deq_0

    Ap_mid, Ab_mid = geom.calculate_surfaces_from_points(x_1, y_1, p_1, p_1)

    L_1 = p_1 * Ab_wanted / Ab_mid

    Ap_1, Ab_1 = geom.calculate_surfaces_from_points(x_1, y_1, L_1, p_1)

    if np.isclose(Ap_1, Ap_wanted, rtol=0.001):
        print("Port area matches")
        print("Ap = ", Ap_1)
        print("Ap wanted = ", Ap_wanted)

    else:
        print("Port area did not match")
        print("Ap = ", Ap_1)
        print("Ap wanted = ", Ap_wanted)

    if np.isclose(Ab_1, Ab_wanted, rtol=0.001):
        print("Burn area matches")
        print("Ab = ", Ab_1)
        print("Ab wanted = ", Ab_wanted)
    else:
        print("Burn area did not match")
        print("Ab = ", Ab_1)
        print("Ab wanted = ", Ab_wanted)

    return x_1, y_1, L_1, p_1

if __name__ == "__main__":
    """
    x, y = geom.create_regular_poligon(6, 1)
    x, y = geom.fill_borders(x, y, 100)
    """
    
    theta = np.linspace(0, 2 * np.pi, 50, endpoint=False)
    r = 1.0 + 0.2 * np.cos(10 * theta)  # forma non convessa ma chiusa
    x_poly = (r * np.cos(theta))  # traslato per test translate
    y_poly = (r * np.sin(theta))
    x, y = geom.sort_input(x_poly, y_poly)

    p = 0.8
    Ap00, Ab00 = geom.calculate_surfaces_from_points(x, y, p, p)
    print(Ab00)

    Dp = 0.01
    Lc = 0.4

    x_1, y_1, L_1, p_1 = dimensionalize_geometry(x, y, Dp, Lc, p)

