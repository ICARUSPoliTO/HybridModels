import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from typing import Dict, List, Any

# ---------------- Helper functions ----------------

def _get_series(results: Dict[str, List[Any]], key: str, n: int) -> np.ndarray:
    """
    Restituisce una serie numpy per la chiave richiesta.
    Se la chiave non esiste o è None, ritorna un array di NaN della lunghezza n.
    Se la serie ha lunghezza diversa da n:
      - se è uno scalare lo broadcasta,
      - altrimenti tronca o riempie con NaN.
    """
    if key in results and results[key] is not None:
        arr = np.array(results[key], dtype=float)
        if arr.shape[0] != n:
            if arr.size == 1:
                return np.full(n, float(arr))
            out = np.full(n, np.nan)
            out[:min(n, arr.size)] = arr[:min(n, arr.size)]
            return out
        return arr
    return np.full(n, np.nan)

def _collect_legend(axs: List[plt.Axes]):
    """
    Raccoglie handle/label unici da una lista di assi per costruire una legenda unificata.
    Restituisce (handles, labels) in ordine di prima apparizione.
    """
    handles = []
    labels = []
    for ax in axs:
        h, l = ax.get_legend_handles_labels()
        for hh, ll in zip(h, l):
            if ll not in labels:
                handles.append(hh)
                labels.append(ll)
    return handles, labels

def _make_right_axes(ax: plt.Axes, n_right: int, offset_step: float = 0.12) -> List[plt.Axes]:
    """
    Crea n_right assi twin a destra spostandoli progressivamente verso destra.
    Ritorna la lista degli assi creati.
    """
    axes = []
    for i in range(n_right):
        twin = ax.twinx()
        # sposta la spina destra in coordinate "axes" (1.0 = bordo destro)
        twin.spines["right"].set_position(("axes", 1.0 + offset_step * i))
        twin.set_frame_on(True)
        twin.patch.set_visible(False)  # rende trasparente il background dell'asse
        axes.append(twin)
    return axes

def _make_left_axes(ax: plt.Axes, n_left: int, offset_step: float = 0.12) -> List[plt.Axes]:
    """
    Crea n_left assi twin posizionati a sinistra (negativo rispetto all'asse principale).
    Ritorna la lista degli assi creati.
    """
    axes = []
    for i in range(n_left):
        twin = ax.twinx()
        twin.spines["right"].set_visible(False)  # nasconde la spina destra del twin
        pos = -offset_step * (i + 1)
        # posiziona la spina sinistra in coordinate "axes" (valori negativi spostano a sinistra)
        twin.spines["left"].set_position(("axes", pos))
        twin.yaxis.set_label_position("left")
        twin.yaxis.set_ticks_position("left")
        twin.set_frame_on(True)
        twin.patch.set_visible(False)
        axes.append(twin)
    return axes

def _adjust_margins_for_axes(fig: plt.Figure, n_left_extra: int = 0, n_right_extra: int = 0,
                             offset_step: float = 0.12, pad: float = 0.02):
    """
    Aggiusta i margini della figura per evitare che assi aggiuntivi vengano tagliati.
    n_left_extra: numero di assi aggiuntivi a sinistra (escluso l'asse principale)
    n_right_extra: numero di assi aggiuntivi a destra (escluso l'asse principale)
    offset_step: passo usato per posizionare le spine (deve corrispondere a _make_*_axes)
    pad: padding addizionale
    """
    total_right = offset_step * max(0, n_right_extra)
    total_left = offset_step * max(0, n_left_extra)
    # left_margin aumenta se ci sono molti assi a sinistra; clamp per non esagerare
    left_margin = min(0.70, 0.06 + total_left + pad)
    # right_margin diminuisce se ci sono molti assi a destra; clamp per non esagerare
    right_margin = max(0.50, 0.94 - (total_right + pad))
    fig.subplots_adjust(left=left_margin, right=right_margin)

def _place_offset_text_above_axis(fig: plt.Figure, ax: plt.Axes, side: str, x_shift: float = 0.0, y_shift: float = 0.01):
    """
    Posiziona il testo di offset (esponente della notazione scientifica) sopra l'asse corrispondente.
    - fig: oggetto figura (usato per trasformazioni in coordinate figura)
    - ax: asse di cui spostare l'offset text
    - side: 'left' o 'right' indica su quale lato dell'asse si trova la spine
    - x_shift: spostamento orizzontale in coordinate figura (utile per separare esponenti vicini)
    - y_shift: spostamento verticale in coordinate figura (quanto sopra l'asse)
    NOTE: la funzione forza un draw della figura per assicurarsi che l'offset text sia stato creato.
    """
    # Forza il rendering per creare/posizionare l'offset text interno di Matplotlib
    fig.canvas.draw()
    offset_text = ax.yaxis.get_offset_text()  # oggetto Text che contiene l'esponente (se presente)
    if offset_text is None:
        return
    # bbox dell'asse in coordinate figura (x0,y0,x1,y1)
    bbox = ax.get_position()
    # scegli x in coordinate figura: per assi a sinistra usa bbox.x0, per destra bbox.x1
    if side == "left":
        x_fig = bbox.x0 + x_shift
        ha = "left"
    else:
        x_fig = bbox.x1 + x_shift
        ha = "right"
    # y leggermente sopra il bordo superiore dell'asse
    y_fig = bbox.y1 + y_shift
    # imposta trasformazione in coordinate figura e posiziona il testo
    offset_text.set_transform(fig.transFigure)
    offset_text.set_x(x_fig)
    offset_text.set_y(y_fig)
    offset_text.set_ha(ha)
    offset_text.set_va("bottom")

# ---------------- Main plotting function ----------------

def plot_results(time: List[float], results: Dict[str, List[Any]]):
    """
    time: lista o array 1D dei tempi
    results: dizionario già normalizzato (ogni chiave -> lista della stessa lunghezza di time)
    Questa funzione disegna i grafici richiesti e posiziona correttamente gli esponenti della notazione scientifica
    sopra il rispettivo asse, evitando sovrapposizioni e clipping.
    """
    time = np.array(time, dtype=float)
    n = time.size

    # helper locale per estrarre serie
    def s(k: str) -> np.ndarray:
        return _get_series(results, k, n)

    # stile generale
    lw = 2.2
    marker_size = 5
    markevery = max(1, n // 20)

    # ----------------- PRESSURES -----------------
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_title("PRESSURES")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Pressure [Pa]")
    ax.plot(time, s("pc"), label="p_c", linewidth=lw)
    ax.plot(time, s("pinj"), label="p_inj", linewidth=lw)
    ax.plot(time, s("ptank"), label="p_tank", linewidth=lw)
    #ax.set_xlim(time[0], 30)
    ax.legend()
    #ax.grid(True)
    fig.tight_layout()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_title("PRESSURES")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Pressure [Pa]")
    ax.plot(time, s("pc"), label="p_c", linewidth=lw)
    # ax.set_xlim(time[0], 30)
    ax.legend()
    # ax.grid(True)
    fig.tight_layout()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_title("PRESSURES")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Pressure [Pa]")
    ax.plot(time, s("pe"), label="p_e", linewidth=lw)
    ax.plot(time, s("pamb"), label="p_amb", linewidth=lw)
    #ax.set_xlim(time[0], 30)
    ax.legend()
    #ax.grid(True)
    fig.tight_layout()

    # ----------------- TEMPERATURES (Tc_CEA plotted first) -----------------
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_title("TEMPERATURES")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Temperature [K]")
    # Tc_CEA disegnato prima così Tc risulta sopra in caso di sovrapposizione
    ax.plot(time, s("Tc_CEA"), label="T_c(CEA)", linewidth=lw, marker='o',
            markersize=marker_size, markevery=markevery, zorder=1)
    ax.plot(time, s("Tc"), label="T_c", linewidth=lw, zorder=2)
    ax.plot(time, s("Ttank"), label="T_tank", linewidth=lw, zorder=2)
    ax.plot(time, s("Te"), label="T_e", linewidth=lw, zorder=2)
    #ax.set_xlim(time[0], 30)
    ax.legend()
    #ax.grid(True)
    fig.tight_layout()

    # ----------------- MASS FLOWS -----------------
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_title("MASS FLOWS")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Mass Flows [kg/s]")
    # mdot (Total inflow) plottata prima con marker per rimanere "sotto" in caso di sovrapposizione
    ax.plot(time, s("mdot"), label="Total inflow", linewidth=lw, marker='o',
            markersize=marker_size, markevery=markevery, zorder=1)
    ax.plot(time, s("mdot_ox"), label="Oxidizer", linewidth=lw, zorder=2)
    ax.plot(time, s("mdot_fuel"), label="Fuel", linewidth=lw, zorder=2)
    ax.plot(time, s("mdot_throat"), label="Total outflow", linewidth=lw, zorder=2)
    #ax.set_xlim(time[0], 30)
    ax.legend()
    #ax.grid(True)
    fig.tight_layout()

    # ----------------- COMBUSTION PROPERTIES (3 left axes) -----------------
    fig, ax0 = plt.subplots(figsize=(8, 4))
    ax0.set_title("COMBUSTION PROPERTIES")
    ax0.set_xlabel("Time [s]")

    # crea 2 assi aggiuntivi a sinistra (oltre all'asse principale)
    left_axes = [ax0] + _make_left_axes(ax0, 2)
    # aumenta i margini per evitare clipping delle spine/label
    _adjust_margins_for_axes(fig, n_left_extra=2, n_right_extra=0)

    # Asse 0: Oxidizer mass flux
    left_axes[0].plot(time, s("Gox"), color="C0", label="G_ox", linewidth=lw)
    left_axes[0].set_ylabel("Oxidizer mass flux [kg/(m^2 s)]")

    # Asse 1: Regression rate (mostriamo r*1e3 e aggiungiamo ×10^-3 sopra l'asse)
    r_raw = s("r")
    r_scaled = r_raw * 1e3  # scala per mostrare valori in "n" (es. 0.002 -> 2.0)
    left_axes[1].plot(time, r_scaled, color="C1", label="regression rate", linewidth=lw)
    left_axes[1].set_ylabel("Regression rate [m/s]")
        # posiziona l'esponente sopra l'asse e aggiungi il testo esplicito ×10^-3 in coordinate asse
    left_axes[1].text(-0.14, 1.02, r'$10^{-3}$', transform=left_axes[1].transAxes,
                      va='bottom', ha='left', fontsize=10)
    # Asse 2: Mixture Ratio (MR)
    left_axes[2].plot(time, s("MR"), color="C2", label="MR=O/F", linewidth=lw)
    left_axes[2].set_ylabel("Mixture Ratio")
    # sposta le label degli assi verso l'esterno per evitare sovrapposizioni con le spine
    left_axes[0].yaxis.set_label_coords(-0.08, 0.5)
    left_axes[1].yaxis.set_label_coords(-0.20, 0.5)
    left_axes[2].yaxis.set_label_coords(-0.32, 0.5)

    # costruisci legenda unificata
    handles, labels = _collect_legend(left_axes)
    ax0.legend(handles, labels, loc="best")
    #ax0.grid(True)

    # dopo aver disegnato, forziamo il draw e assicuriamo margini adeguati (evita tight_layout fallito)
    #fig.canvas.draw()
    # se l'asse MR o CF risultano ancora tagliati, aumentiamo il margine sinistro
    #fig.subplots_adjust(left=max(fig.subplotpars.left, 0.62))

    # ----------------- GAS PROPERTIES -----------------
    fig, ax_left = plt.subplots(figsize=(8, 4))
    ax_left.set_title("GAS PROPERTIES")
    ax_left.set_xlabel("Time [s]")
    ax_left.set_ylabel("Molecular Weight [kg/kmol]")
    h1, = ax_left.plot(time, s("MW"), label="Molecular Weight", linewidth=lw)
    h2, = ax_left.plot(time, s("MW_CEA"), label="Molecular Weight (CEA)", linewidth=lw,
                       marker='o', markersize=marker_size, markevery=markevery, zorder=1)
    ax_right = ax_left.twinx()
    ax_right.set_ylabel("Specific heat ratio")
    h3, = ax_right.plot(time, s("gamma"), "--", label=r"$\gamma$", linewidth=lw)
    h4, = ax_right.plot(time, s("gamma_CEA"), ":", label=r"$\gamma$ (CEA)", linewidth=lw,
                        marker='o', markersize=marker_size, markevery=markevery, zorder=1)
    handles = [h1, h2, h3, h4]
    labels = ["Molecular Weight", "Molecular Weight (CEA)", r"$\gamma$", r"$\gamma$ (CEA)"]
    ax_left.legend(handles, labels, loc="best")
    #ax_left.grid(True)
    fig.tight_layout()

    # ----------------- GEOMETRIES (Area e Volume in notazione scientifica) -----------------
    fig, ax0 = plt.subplots(figsize=(8, 4))
    ax0.set_title("GEOMETRIES")
    ax0.set_xlabel("Time [s]")
    left_axes = [ax0] + _make_left_axes(ax0, 2)
    _adjust_margins_for_axes(fig, n_left_extra=2, n_right_extra=0)

    # Expansion ratio
    left_axes[0].plot(time, s("eps"), color="C0", label=r"$\epsilon$", linewidth=lw)
    left_axes[0].set_ylabel("Expansion Ratio A_e/A_t")
    # Area (Port Area e Burning Area) in notazione scientifica
    left_axes[1].plot(time, s("Ap"), color="C1", label="Port Area", linewidth=lw)
    left_axes[1].plot(time, s("Ab"), color="C2", label="Burning Area", linewidth=lw)
    left_axes[1].set_ylabel("Area [m^2]")
    # Volume in notazione scientifica
    left_axes[2].plot(time, s("Vol_chamber"), color="C3", label="Internal volume", linewidth=lw)
    left_axes[2].set_ylabel("Volume [m^3]")
    # sposta le label verso l'esterno per evitare sovrapposizioni
    left_axes[0].yaxis.set_label_coords(-0.08, 0.5)
    left_axes[1].yaxis.set_label_coords(-0.20, 0.5)
    left_axes[2].yaxis.set_label_coords(-0.32, 0.5)

    handles, labels = _collect_legend(left_axes)
    ax0.legend(handles, labels, loc="best")
    #ax0.grid(True)

    # forza il draw e aumenta il margine sinistro se necessario per evitare clipping
    #fig.canvas.draw()
    #fig.subplots_adjust(left=max(fig.subplotpars.left, 0.62))

    # ----------------- MASSES -----------------
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_title("MASSES")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Mass [kg]")
    ax.plot(time, s("m_fuel"), label="Fuel mass", linewidth=lw)
    ax.plot(time, s("mL"), label="Liquid mass", linewidth=lw)
    ax.legend()
    #ax.grid(True)
    fig.tight_layout()

    # ----------------- PERFORMANCES 1: Thrust (left), Is & Ivac (right) -----------------
    fig, ax_left = plt.subplots(figsize=(9, 5))
    ax_left.set_title("PERFORMANCES 1")
    ax_left.set_xlabel("Time [s]")
    ax_left.set_ylabel("Thrust [N]")
    ax_left.plot(time, s("Thrust"), color="C0", label="Thrust", linewidth=lw)
    ax_right = ax_left.twinx()
    ax_right.set_ylabel("I_s [s]")
    ax_right.plot(time, s("Is"), color="C1", label="I_s", linewidth=lw, marker='o',
                  markersize=marker_size, markevery=markevery, zorder=1)
    ax_right.plot(time, s("Ivac"), color="C2", label="I_s,vacuum", linewidth=lw, zorder=2)
    handles, labels = _collect_legend([ax_left, ax_right])
    ax_left.legend(handles, labels, loc="best")
    #ax_left.grid(True)
    fig.tight_layout()

    # ----------------- PERFORMANCES 2: c*, CF (two left axes) and Me (right) -----------------
    fig, ax_main = plt.subplots(figsize=(9, 5))
    ax_main.set_title("PERFORMANCES 2")
    ax_main.set_xlabel("Time [s]")
    left_axes = [ax_main] + _make_left_axes(ax_main, 1)
    right_axes = _make_right_axes(ax_main, 1)
    _adjust_margins_for_axes(fig, n_left_extra=1, n_right_extra=1)

    left_axes[0].set_ylabel("c* [m/s]")
    left_axes[0].plot(time, s("cstar"), color="C1", label="c*", linewidth=lw)
    left_axes[1].set_ylabel("C_F")
    left_axes[1].plot(time, s("CFvac"), color="C2", label="C_F,vacuum", linewidth=lw)
    left_axes[1].plot(time, s("CF"), color="C3", label="C_F", linewidth=lw, marker='o',
                      markersize=marker_size, markevery=markevery, zorder=1)
    right_axes[0].set_ylabel("Mach number")
    right_axes[0].plot(time, s("Me"), color="C6", label="Exit Mach", linewidth=lw)

    left_axes[0].yaxis.set_label_coords(-0.08, 0.5)
    left_axes[1].yaxis.set_label_coords(-0.20, 0.5)

    handles, labels = _collect_legend([ax_main] + left_axes + right_axes)
    ax_main.legend(handles, labels, loc="best")
    #ax_main.grid(True)
    #fig.tight_layout()

    # ----------------- PARAMETERS -----------------
    fig, ax_left = plt.subplots(figsize=(8, 4))
    ax_left.set_title("PARAMETERS")
    ax_left.set_xlabel("Time [s]")
    ax_left.set_ylabel("Time step [s]")
    ax_left.plot(time, s("dt"), label="Time step", linewidth=lw)
    ax_right = ax_left.twinx()
    ax_right.set_ylabel("CEA flag")
    ax_right.plot(time, s("flag"), label="CEA Output flag", color="C1", linewidth=lw,
                  marker='o', markersize=marker_size, markevery=markevery)
    _place_offset_text_above_axis(fig, ax_left, side="left", x_shift=0.0, y_shift=0.012)
    _place_offset_text_above_axis(fig, ax_right, side="right", x_shift=0.0, y_shift=0.012)
    handles = [ax_left.lines[0], ax_right.lines[0]]
    labels = ["Time step", "CEA Output flag"]
    ax_left.legend(handles, labels, loc="best")
    #ax_left.grid(True)
    fig.tight_layout()



    plt.show()

if __name__ == "__main__":
    # Source - https://stackoverflow.com/a
    # Posted by Eric O. Lebigot, modified by community. See post 'Timeline' for change history
    # Retrieved 2025-12-08, License - CC BY-SA 3.0

    import pickle
    # Getting back the objects:
    SAVE_PATH = "D:\DesktopMirror\PoliTo\Team Icarus\FRANCO_mk14\FRANCO_mk14_N2_"  # <-- modifica qui
    with open(SAVE_PATH+'results.pkl', 'rb') as f:  # Python 3: open(..., 'rb')
        time, results, out_log = pickle.load(f)

    with open(SAVE_PATH+"mis_param.pkl", "rb") as f:
        sim_params = pickle.load(f)

    for elmnt in out_log:
        print(elmnt)
    from Geometry.geometry_calculation import fill_borders_circumference
    from Geometry.geometry_calculation import fill_borders

    plt.figure()
    for i in range(len(results["x"])):
        if i == 0:
            c = "ro-"
        elif i == len(results["x"]) - 1:
            c = "ro-"
        elif i == len(results["x"]) - 2:
            c = "g*-"
        else:
            c = '-'
        x, y = fill_borders(results["x"][i], results["y"][i], 50)
        if i%100==0:
            plt.plot(x,y, c)

    x,y = fill_borders_circumference(np.array([0.5*sim_params["D_chamber"]]), np.array([0]), 50)
    plt.plot(x,y, 'ko-')
    plt.show()

    """
    print("Starting fuel mass = ", results["m_fuel"][0], " kg")
    print("Starting oxidizer mass = ", results["mL"][0], " kg")

    burn_mask = results["burn"]
    burn_mask = np.array(burn_mask, dtype=bool)
    bf_fuel = np.array(results["m_fuel"])[burn_mask]
    bf_ox = np.array(results["mL"])[burn_mask]
    print(f'Average pc = {np.average(np.array(results["pc"])[burn_mask])/1e5} bar')
    print(f'Average Gox = {np.average(  np.array(results["Gox"])[burn_mask])} bar')
    print(f'Average r = {np.average(    np.array(results["r"])[burn_mask])*1e3} mm/s')
    print(f'Average MR = {np.average(   np.array(results["MR"])[burn_mask])}')
    print(f'Fuel burned = {bf_fuel[0] - bf_fuel[-1]} kg')
    print(f'Oxidizer burned = {bf_ox[0] - bf_ox[-1]} kg')

    print("********ROCKET DESIGN********")
    print(f"Injector diameter (equivalent) = {sim_params['Dt']} m")
    print(f"Initial port diameter (equivalent) = {sim_params['Dp']} m")
    print(f"Initial port diameter (real) = {2 * np.max(np.sqrt(sim_params['x']**2 + sim_params['y']**2))} m")
    print(f"Grain pitch = {sim_params['pitch']} m")
    print(f"Grain Lenght = {sim_params['Lc']} m")
    print(f"Chamber diameter = {sim_params['D_chamber']} m")
    print(f"Throat diameter = {sim_params['Dt']} m")
    """

    #print(results.keys())
    plot_results(time, results)
