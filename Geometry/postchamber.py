"""
Script to make the postchamber based on code outputs.
"""
import numpy as np

def Gammone(g):
    G = np.sqrt(g * (2/(g + 1))**((g+1)/(g-1)))
    return G

def characteristic_length(gamma, cstar, tstar):
    G = Gammone(gamma)
    Lstar = tstar * cstar * (G ** 2)
    return Lstar

def postchamber_length(Lstar, At, D_chamber):
    L_postchamber = Lstar * At / (0.25 * np.pi * (D_chamber ** 2))
    return L_postchamber

def filter_value(burn_mask, val):
    val = val[burn_mask]
    return val

if __name__ == "__main__":

    Dt =
    At = 0.25 * np.pi * (Dt ** 2)
    D_chamber =
    tstar = 20e-3 # [s]

    burn_mask = []
    gamma = []
    cstar = []

    gamma = filter_value(burn_mask, gamma)
    cstar = filter_value(burn_mask, cstar)

    gamma_avg = np.mean(gamma)
    cstar_avg = np.mean(cstar)

    L = postchamber_length(characteristic_length(gamma_avg, cstar_avg, tstar), At, D_chamber)

    print(f"Post chamber length = {L} m")
    print(f"Bye! Love u <3")

# end of file