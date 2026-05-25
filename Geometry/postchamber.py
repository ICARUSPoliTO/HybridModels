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
    import pickle

    # Getting back the objects:
    SAVE_PATH = "D:\DesktopMirror\PoliTo\Team Icarus\FRANCO_mk14\FRANCO_mk14_"  # <-- modifica qui
    with open(SAVE_PATH + 'results.pkl', 'rb') as f:  # Python 3: open(..., 'rb')
        time, results, out_log = pickle.load(f)

    with open(SAVE_PATH + "mis_param.pkl", "rb") as f:
        sim_params = pickle.load(f)

    Dt = sim_params['Dt']
    At = 0.25 * np.pi * (Dt ** 2)
    D_chamber = sim_params['D_chamber']
    tstar = 20e-3 # [s]

    burn_mask = results["burn"]
    burn_mask = np.array(burn_mask, dtype=bool)
    gamma = np.array(results['gamma'])
    cstar = np.array(results['cstar'])

    gamma = filter_value(burn_mask, gamma)
    cstar = filter_value(burn_mask, cstar)

    gamma_avg = np.mean(gamma)
    cstar_avg = np.mean(cstar)

    L = postchamber_length(characteristic_length(gamma_avg, cstar_avg, tstar), At, D_chamber)

    print(f"Post chamber length = {L} m")
    print(f"Post chamber Volume = {0.25*np.pi*L*D_chamber**2} m^3")
    print(f"Bye! Love u <3")

# end of file