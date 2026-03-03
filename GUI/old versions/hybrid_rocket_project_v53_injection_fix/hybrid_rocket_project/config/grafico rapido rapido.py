import numpy as np
import matplotlib.pyplot as plt

# Parametri del profilo
F_peak = 180.0      # spinta di picco [N]
t_total = 1.8       # durata combustione [s]
dt = 0.001

# Asse dei tempi
t = np.arange(0.0, t_total, dt)

# Definizione delle fasi
t_rise = 0.6 * t_total     # salita
t_plateau = 0.3 * t_total  # parte alta estesa
t_fall = t_total - t_rise - t_plateau

F = np.zeros_like(t)

for i, ti in enumerate(t):
    if ti <= t_rise:
        x = ti / t_rise
        F[i] = F_peak * (np.sin(x * np.pi / 2))**3
    elif ti <= t_rise + t_plateau:
        F[i] = F_peak
    else:
        x = (ti - t_rise - t_plateau) / t_fall
        F[i] = F_peak * (np.cos(x * np.pi / 2))**2

# Plot
plt.figure(figsize=(10, 6))
plt.plot(t, F, 'r', lw=2)
plt.xlabel("Tempo [s]")
plt.ylabel("Spinta [N]")
plt.title("ED Special – Profilo Progressivo")
plt.grid(True)
plt.tight_layout()
plt.savefig("ED_special_progressivo.png", dpi=300)
plt.close()

print("Grafico salvato come 'ED_special_progressivo.png'")
print(f"Durata combustione ≈ {t_total:.2f} s, spinta di picco ≈ {F_peak:.1f} N")
