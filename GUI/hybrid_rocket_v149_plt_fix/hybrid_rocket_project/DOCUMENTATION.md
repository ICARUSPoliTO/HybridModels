# Hybrid Rocket Simulator - Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Detailed Code Structure](#detailed-code-structure)
4. [Optimization Module](#optimization-module)
5. [Mission Module](#mission-module)
6. [Plots Explanation](#plots-explanation)
7. [Key Equations](#key-equations)
8. [File Structure](#file-structure)

---

## Overview

The Hybrid Rocket Simulator is a professional desktop application for designing and optimizing hybrid rocket motors. It combines:

- **Optimization**: Find optimal geometric ratios (Dport/Dt, Dinj/Dt, Lc/Dt) for maximum performance
- **Mission Simulation**: Time-resolved simulation of rocket motor operation
- **Visualization**: Interactive plots for both optimization results and mission data

### Main Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Configuration  │────▶│  Optimization   │────▶│ Optimization    │
│  (Fuel, Ox,     │     │  (Parameter     │     │ Output          │
│   Properties)   │     │   Ranges)       │     │ (Contour Plots) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │ Select Optimal  │
                                               │ Design Point    │
                                               └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Mission      │────▶│ Run/Match       │────▶│ Mission Output  │
│  (Geometry,     │     │ Mission         │     │ (Time Plots)    │
│   Tank, etc.)   │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Architecture

### Module Structure

```
hybrid_rocket_project/
├── gui/                    # User Interface
│   ├── main_window.py      # Main application window
│   └── pages/
│       ├── configuration_page.py    # Fuel/Oxidizer setup
│       ├── optimization_page.py     # Optimization inputs
│       ├── optimization_output_page.py  # Optimization results + plots
│       ├── mission_page.py          # Mission parameters
│       └── mission_output_page.py   # Mission results + plots
│
├── core/                   # Business Logic
│   ├── controller.py       # Application controller
│   ├── data_structures.py  # Data classes
│   ├── optimization_runner.py  # Background optimization
│   └── mission_runner.py   # Background mission simulation
│
├── Mission/                # Simulation Backend
│   └── mission_simulation.py   # Core physics simulation
│
├── Performance/            # Performance calculations
├── Injection/              # Injector modeling
├── Tank/                   # Tank thermodynamics
└── Geometry/               # Grain geometry
```

### Data Flow

```
┌──────────────┐
│   GUI Page   │
│  (inputs)    │
└──────┬───────┘
       │ collect data
       ▼
┌──────────────┐
│  Controller  │
│  (prepare)   │
└──────┬───────┘
       │ prepare inputs
       ▼
┌──────────────┐
│   Runner     │
│ (background) │
└──────┬───────┘
       │ call backend
       ▼
┌──────────────┐
│   Backend    │
│  (physics)   │
└──────┬───────┘
       │ results
       ▼
┌──────────────┐
│ Output Page  │
│   (plots)    │
└──────────────┘
```

---

## Detailed Code Structure

Questa sezione spiega in dettaglio come è organizzato il codice e cosa fa ogni file.

### Directory Principal: `gui/`

La cartella `gui/` contiene tutto il codice dell'interfaccia utente.

#### `gui/main_window.py` (~1300 righe)

**Ruolo**: Finestra principale dell'applicazione. Gestisce navigazione, pulsanti, e coordinamento tra le pagine.

```python
class MainWindow:
    def __init__(self):
        self.root = tk.Tk()           # Finestra principale Tkinter
        self.controller = ApplicationController()  # Logica business
        self.inputs = {}              # Dizionario di tutti i campi input
        self.pages = {}               # Dizionario delle pagine
```

**Metodi principali**:

| Metodo | Descrizione |
|--------|-------------|
| `create_navigation()` | Crea il menu laterale con i pulsanti di navigazione |
| `show_page(page_name)` | Mostra una pagina specifica, nasconde le altre |
| `run_optimization()` | Raccoglie dati, avvia OptimizationRunner in background |
| `run_mission()` | Raccoglie dati missione, avvia MissionRunner |
| `on_optimization_progress()` | Callback per aggiornare barra progresso |
| `on_optimization_success()` | Callback quando ottimizzazione finisce, mostra risultati |
| `save_mission_parameters()` | Salva parametri missione in CSV |
| `load_mission_parameters()` | Carica parametri missione da CSV |

**Flusso di un'ottimizzazione**:
```
1. Utente clicca "Run Optimization"
2. run_optimization() raccoglie dati da self.inputs
3. Crea OptimizationRunner con callbacks
4. Runner.start() → thread separato
5. on_optimization_progress() aggiorna UI ogni iterazione
6. on_optimization_success() → display_results() sulla output page
```

---

#### `gui/pages/configuration_page.py` (~400 righe)

**Ruolo**: Prima pagina - configurazione di fuel, ossidante, proprietà base.

**Sezioni**:
- **Oxidizer Selection**: Dropdown per scegliere N2O, LOX, etc.
- **Fuel Selection**: Dropdown per HTPB, Paraffin, etc.
- **Fuel Properties**: Coefficienti a, n per regression rate
- **Injector**: Coefficiente di scarico CD

**Campi input** (prefisso `Config_` o nome specifico):
```
Fuel_a, Fuel_n, Fuel_rho    → Proprietà fuel
Injector_CD                  → Coefficiente scarico
Nozzle_ExpansionRatio        → Rapporto espansione
```

---

#### `gui/pages/optimization_page.py` (~350 righe)

**Ruolo**: Input per l'ottimizzazione - range parametri, condizioni operative.

**Sezioni**:
- **Simulation Resolution**: Preset (Quick/Standard/Fine) e punti per parametro
- **Parameter Ranges**: Min/max per Dport/Dt, Dinj/Dt, Lc/Dt
- **Operating Conditions**: Pressione tank, temperatura, pressione ambiente
- **Gox Limits**: Filtro per massa flux ossidante

**Campi input** (prefisso `Optimization_`):
```
Optimization_Dport_Dt_min/max
Optimization_Dinj_Dt_min/max
Optimization_Lc_Dt_min/max
Optimization_ptank, Optimization_Ttank
Optimization_Gox_min, Optimization_Gox_max
```

---

#### `gui/pages/optimization_output_page.py` (~800 righe)

**Ruolo**: Visualizzazione risultati ottimizzazione con grafici contour interattivi.

**Struttura**:
```python
class OptimizationOutputPage:
    TAB_DEFINITIONS = {
        'Gox Analysis': {'params': ['Gox_array'], 'single_plot': True},
        'Performance': {'params': ['Ivac_array', 'Is_array', 'pc_array']},
        'Pressures & Flows': {...},
        ...
    }
```

**Metodi principali**:

| Metodo | Descrizione |
|--------|-------------|
| `display_results(results, gox_min, gox_max)` | Entry point, riceve dati e li visualizza |
| `_update_text_results()` | Genera TOP 10 soluzioni filtrate per Gox |
| `_create_plot_tabs()` | Crea notebook con tab per ogni gruppo di plot |
| `_create_contour_figure()` | Genera figura matplotlib con contour plots |
| `_create_parametric_tab()` | Crea tab con slider interattivo per Lc/Dt |
| `export_to_excel()` | Esporta tutti i dati in Excel multi-sheet |

**Come funziona il filtro Gox**:
```python
def _update_text_results(self):
    # Per ogni combinazione (i, j, k) di indici
    for i in range(n_dport):
        for j in range(n_dinj):
            for k in range(n_lc):
                gox = self.results['Gox_array'][i, j, k]
                # Filtra solo se Gox è nel range valido
                if self.gox_min <= gox <= self.gox_max:
                    ivac = self.results['Ivac_array'][i, j, k]
                    solutions.append((ivac, i, j, k, gox, ...))
    
    # Ordina per Ivac decrescente, prendi TOP 10
    solutions.sort(reverse=True)
    top_10 = solutions[:10]
```

---

#### `gui/pages/mission_page.py` (~1150 righe)

**Ruolo**: Parametri per simulazione missione - geometria grano, tank, timing.

**Sezioni**:
- **Optimal Design Point**: Rapporti ottimali da usare (Dport/Dt, Dinj/Dt, Lc/Dt)
- **Mission Timing**: Tempo di burn target, delay
- **Chamber & Nozzle**: Diametri, volumi, expansion ratio ε
- **Grain Geometry**: Preset forma grano, parametri geometrici
- **Tank Configuration**: Tipo tank, massa, pressurizzazione
- **Efficiencies**: Rendimenti c* e CF

**Sistema Auto-Calculation**:
```python
def _auto_calculate_dt(self):
    """Calcola Dt automaticamente dalla geometria"""
    # 1. Calcola Dport dalla geometria del grano
    dport = self._calculate_dport_from_geometry()
    
    # 2. Usa il rapporto ottimale per trovare Dt
    dport_dt_ratio = float(self.inputs['Mission_Dport_Dt_optimal'].get())
    dt = dport / dport_dt_ratio
    
    # 3. Aggiorna il campo Dt
    self.inputs['Mission_Dt'].delete(0, tk.END)
    self.inputs['Mission_Dt'].insert(0, f"{dt:.5f}")

def _calculate_dport_from_geometry(self):
    """Calcola diametro porta equivalente dalla geometria"""
    preset = self.grain_preset_var.get()
    outer_r = float(self.inputs['Mission_grain_outer_radius'].get())
    
    if preset == 'Cylindrical':
        ap = np.pi * outer_r**2  # Area circolare
    elif preset in ['Regular Polygon', 'Custom Polygon']:
        n = int(self.inputs['Mission_grain_n_sides'].get())
        ap = 0.5 * n * outer_r**2 * np.sin(2*np.pi/n)  # Area poligono
    ...
    
    return np.sqrt(4 * ap / np.pi)  # Diametro equivalente
```

**Grain Presets e visibilità campi**:
```python
def _on_grain_preset_change(self):
    preset = self.grain_preset_var.get()
    
    if preset == 'Cylindrical':
        # Mostra solo outer_radius
        hide_frame(self.n_sides_frame)
        hide_frame(self.pitch_frame)
        show_frame(self.outer_radius_frame)
        
    elif preset in ['Regular Polygon', 'Custom Polygon']:
        # Mostra n_sides, outer_radius, pitch
        show_frame(self.n_sides_frame)
        show_frame(self.outer_radius_frame)
        show_frame(self.pitch_frame)
        
    elif 'Star' in preset or preset == 'Wagon Wheel':
        # Mostra tutti i campi
        show_frame(self.n_sides_frame)
        show_frame(self.inner_radius_frame)
        show_frame(self.outer_radius_frame)
        show_frame(self.pitch_frame)
        show_frame(self.circular_frame)
```

---

#### `gui/pages/mission_output_page.py` (~450 righe)

**Ruolo**: Visualizzazione risultati missione con grafici time-series.

**Struttura**:
```python
class MissionOutputPage:
    PLOT_TABS = {
        'Thrust & Performance': ['Thrust', 'Is', 'Ivac'],
        'Pressures': ['pc', 'pinj', 'pT'],
        'Mass Flow': ['mdot', 'mdot_ox', 'mdot_fuel'],
        'Combustion': ['MR', 'Gox', 'r'],
        'Temperatures': ['Tc', 'Tc_CEA', 'TL'],
        'Masses': ['mL', 'm_fuel', 'mV'],
    }
    
    PARAM_INFO = {
        'Thrust': ('Thrust', 'N'),
        'pc': ('Chamber Pressure', 'bar', 1e-5),  # con fattore scala
        'r': ('Regression Rate', 'mm/s', 1000),
        ...
    }
```

**Metodi principali**:

| Metodo | Descrizione |
|--------|-------------|
| `display_results(time_data, performances, log)` | Riceve dati e crea layout |
| `create_summary_section()` | Pannello sinistro con statistiche |
| `create_plots_section()` | Pannello destro con tab di grafici |
| `_create_plot_tab()` | Crea singolo tab con subplot per ogni parametro |
| `export_to_excel()` | Esporta dati + summary in Excel |

---

### Directory: `core/`

La cartella `core/` contiene la logica business separata dalla GUI.

#### `core/controller.py` (~700 righe)

**Ruolo**: Ponte tra GUI e backend. Prepara i dati, gestisce lo stato dell'applicazione.

```python
class ApplicationController:
    def __init__(self):
        self.configuration_data = None   # Dati configurazione
        self.optimization_data = None    # Dati ottimizzazione
        self.mission_data = None         # Dati missione
```

**Metodi principali**:

| Metodo | Descrizione |
|--------|-------------|
| `prepare_optimization_inputs(data)` | Converte dati GUI → formato backend |
| `prepare_mission_inputs(mission_data)` | Prepara input per simulazione missione |
| `_generate_grain_geometry(mission_data, Dport)` | Genera coordinate x,y,z del grano |

**Esempio prepare_mission_inputs**:
```python
def prepare_mission_inputs(self, mission_data):
    # Prende dati dalla GUI
    Dt = mission_data['Dt']
    Dport_Dt = mission_data['Dport_Dt_optimal']
    
    # Calcola dimensioni derivate
    At = 0.25 * np.pi * Dt**2
    Dport = Dport_Dt * Dt
    Dinj = Dinj_Dt * Dt
    Lc = Lc_Dt * Dt
    Ainj = n_inj * 0.25 * np.pi * Dinj**2
    
    # Genera geometria grano
    x, y, z = self._generate_grain_geometry(mission_data, Dport)
    
    # Ritorna dizionario pronto per il backend
    return {
        'burn_time': mission_data['burn_time'],
        'eps': mission_data['expansion_ratio'],
        'Ainj': Ainj,
        'At': At,
        'x': x, 'y': y, 'z': z,
        ...
    }
```

---

#### `core/optimization_runner.py` (~200 righe)

**Ruolo**: Esegue ottimizzazione in thread separato per non bloccare la GUI.

```python
class OptimizationRunner(threading.Thread):
    def __init__(self, inputs, callback_progress, callback_success, callback_error):
        self.inputs = inputs
        self.callback_progress = callback_progress
        self.callback_success = callback_success
        self.callback_error = callback_error
        self.cancel_requested = False  # Flag per stop
    
    def run(self):
        """Eseguito nel thread separato"""
        try:
            results = full_range_simulation(
                ...,
                progress_callback=self._progress_wrapper
            )
            self.callback_success(results)
        except InterruptedError:
            self.callback_error("CANCELLED: Stopped by user")
        except Exception as e:
            self.callback_error(str(e))
    
    def _progress_wrapper(self, current, total, message):
        """Wrapper che controlla cancellazione"""
        if self.cancel_requested:
            raise InterruptedError("Cancelled")
        self.callback_progress(current, total, message)
    
    def request_cancel(self):
        """Chiamato quando utente preme Stop"""
        self.cancel_requested = True
```

---

#### `core/mission_runner.py` (~250 righe)

**Ruolo**: Esegue simulazione missione in thread separato.

Struttura identica a OptimizationRunner ma chiama `run_full_mission()` o `match_mission()`.

---

#### `core/data_structures.py` (~100 righe)

**Ruolo**: Dataclass per tipizzazione e validazione dati.

```python
@dataclass
class ConfigurationData:
    oxidizer: str = 'N2O'
    fuel: str = 'HTPB'
    inputs: dict = field(default_factory=dict)

@dataclass
class OptimizationData:
    dport_dt_range: np.ndarray = None
    dinj_dt_range: np.ndarray = None
    lc_dt_range: np.ndarray = None
    ptank: float = 27e5
    ttank: float = 288.0
    pamb: float = 101325.0
    gox_min: float = 100.0
    gox_max: float = 800.0
```

---

### Directory: `Mission/`

#### `Mission/mission_simulation.py` (~1150 righe)

**Ruolo**: Cuore della simulazione fisica. Contiene tutta la fisica del motore.

**Funzioni principali**:

| Funzione | Descrizione |
|----------|-------------|
| `run_full_mission()` | Simulazione completa con parametri fissi |
| `match_mission()` | Trova parametri per raggiungere target burn time |
| `step_iteration()` | Singolo step temporale della simulazione |
| `find_combustion_performance()` | Calcola performance CEA per dato O/F |
| `find_nozzle_output()` | Calcola thrust, Isp dal nozzle |
| `normalize_performances()` | Converte lista di dict → dict di liste |

**Ciclo principale simulazione**:
```python
def run_full_mission(...):
    t = 0
    performances_out = []
    
    while t < burn_time and mL > 0 and m_fuel > 0:
        # 1. Calcola stato tank (p, T, densità)
        tank_state = calculate_tank_state(...)
        
        # 2. Calcola flusso attraverso iniettore
        mdot_ox = injector_flow(p_tank, p_chamber, Ainj, CD)
        
        # 3. Calcola combustione
        Gox = mdot_ox / Ap
        r = a * Gox**n  # Regression rate
        mdot_fuel = rho_fuel * Ab * r
        MR = mdot_ox / mdot_fuel
        
        # 4. Calcola performance CEA
        Tc, MW, gamma, cstar = CEA_lookup(MR, pc)
        
        # 5. Calcola nozzle output
        CF, Isp, Thrust = nozzle_output(pc, At, eps, pamb)
        
        # 6. Aggiorna geometria grano (regressione)
        x, y = regress_grain(x, y, r, dt)
        
        # 7. Aggiorna masse
        mL -= mdot_ox * dt
        m_fuel -= mdot_fuel * dt
        
        # 8. Salva stato
        performances_out.append({
            'pc': pc, 'Thrust': Thrust, 'MR': MR, ...
        })
        
        t += dt
    
    return time_data, normalize_performances(performances_out), log
```

---

### Directory: `Performance/`

Contiene funzioni per calcolo performance steady-state usate nell'ottimizzazione.

#### `Performance/full_range_simulation.py`

```python
def full_range_simulation(Dport_Dt_range, Dinj_Dt_range, Lc_Dt_range, ...):
    """
    Itera su tutte le combinazioni di parametri.
    Per ogni combinazione calcola steady-state performance.
    """
    results = np.zeros((n_dport, n_dinj, n_lc, n_outputs))
    
    for i, dport_dt in enumerate(Dport_Dt_range):
        for j, dinj_dt in enumerate(Dinj_Dt_range):
            for k, lc_dt in enumerate(Lc_Dt_range):
                # Calcola performance a questo punto
                pc, mdot, Gox, MR, Tc, Isp, ... = steady_state_calc(
                    dport_dt, dinj_dt, lc_dt, ...
                )
                
                # Salva risultati
                results[i, j, k, :] = [pc, mdot, Gox, ...]
                
                # Aggiorna progress
                progress_callback(iteration, total, f"Dport/Dt={dport_dt}")
    
    return results
```

---

### Directory: `config/`

#### `config/constants.py`

**Ruolo**: Costanti UI centralizzate.

```python
COLORS = {
    'bg_dark': '#1e1e1e',      # Sfondo scuro
    'bg_medium': '#2d2d2d',    # Sfondo sezioni
    'text_color': '#ffffff',   # Testo bianco
    'accent': '#4fc3f7',       # Colore accent (azzurro)
    'button_inactive': '#9e9e9e',
}

FONTS = {
    'title': ('Arial', 18, 'bold'),
    'section': ('Arial', 12, 'bold'),
    'label': ('Arial', 10),
    'button': ('Arial', 10, 'bold'),
    'small': ('Arial', 9),
}
```

---

### Directory: `gui/components/`

#### `gui/components/input_field.py`

**Ruolo**: Factory function per creare campi input standardizzati.

```python
def create_input_field(parent, key, label, inputs_dict, default='', row=0, col=0):
    """
    Crea Label + Entry e registra nel dizionario inputs.
    
    Args:
        parent: Frame contenitore
        key: Chiave per dizionario inputs (es. 'Mission_Dt')
        label: Testo da mostrare
        inputs_dict: Dizionario dove salvare riferimento al widget
        default: Valore iniziale
        row, col: Posizione nella griglia
    
    Returns:
        Entry widget creato
    """
    tk.Label(parent, text=label, ...).grid(row=row, column=col)
    entry = tk.Entry(parent, ...)
    entry.grid(row=row, column=col+1)
    entry.insert(0, default)
    inputs_dict[key] = entry
    return entry
```

---

### Comunicazione tra Moduli

```
┌─────────────────────────────────────────────────────────────────┐
│                         main_window.py                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   inputs    │  │   pages     │  │ controller  │              │
│  │ (dict)      │  │ (dict)      │  │             │              │
│  └─────────────┘  └─────────────┘  └──────┬──────┘              │
└───────────────────────────────────────────┼─────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                    ▼                       ▼                       ▼
         ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
         │ optimization_    │    │ mission_         │    │ data_            │
         │ runner.py        │    │ runner.py        │    │ structures.py    │
         │                  │    │                  │    │                  │
         │ Thread separato  │    │ Thread separato  │    │ Dataclass        │
         └────────┬─────────┘    └────────┬─────────┘    └──────────────────┘
                  │                       │
                  ▼                       ▼
         ┌──────────────────┐    ┌──────────────────┐
         │ Performance/     │    │ Mission/         │
         │ full_range_sim.  │    │ mission_sim.py   │
         │                  │    │                  │
         │ Backend physics  │    │ Backend physics  │
         └──────────────────┘    └──────────────────┘
```

---

## Optimization Module

### Purpose

Find the optimal dimensionless ratios for rocket motor geometry:

| Ratio | Definition | Typical Range |
|-------|------------|---------------|
| **Dport/Dt** | Port diameter / Throat diameter | 1.5 - 4.0 |
| **Dinj/Dt** | Injector diameter / Throat diameter | 0.1 - 0.5 |
| **Lc/Dt** | Chamber length / Throat diameter | 2.0 - 6.0 |

### How It Works

1. **Define parameter ranges** (min, max, number of points)
2. **Run full_range_simulation()** which iterates over all combinations
3. **For each combination**, calculate steady-state performance:
   - Chamber pressure (pc)
   - Mass flow rates (mdot_ox, mdot_fuel)
   - Combustion temperature (Tc)
   - Specific impulse (Isp)
   - Oxidizer mass flux (Gox)

### Gox Filtering

The oxidizer mass flux (Gox) is critical for hybrid rockets:

- **Too low Gox** → Poor combustion, low regression rate
- **Too high Gox** → Erosive burning, structural issues
- **Typical range**: 100-800 kg/m²s

The optimizer filters results to show only configurations within valid Gox limits.

---

## Mission Module

### Purpose

Simulate the time-evolution of a rocket motor burn, including:

- Grain regression (shape change over time)
- Tank blowdown (pressure/temperature evolution)
- Combustion dynamics
- Thrust profile

### Operating Modes

| Mode | Description |
|------|-------------|
| **Run Mission** | Simulate with fixed parameters until fuel/oxidizer depletes |
| **Match Mission** | Iteratively adjust parameters to match target burn time |

### Key Inputs

- **Geometry**: Grain shape, chamber dimensions, nozzle expansion ratio
- **Tank**: Initial mass, vapor quality, pressurization type
- **Timing**: Target burn time, delay time

---

## Plots Explanation

### Optimization Output Plots

#### Tab 1: Gox Analysis
```
┌─────────────────────────────────────────┐
│           Gox [kg/m²s]                  │
│                                         │
│    ┌───────────────────────────────┐    │
│    │ Dinj/Dt ▲                     │    │
│    │         │    ████████         │    │
│    │         │  ████████████       │    │
│    │         │████████████████     │    │
│    │         └────────────────▶    │    │
│    │              Dport/Dt         │    │
│    └───────────────────────────────┘    │
│                                         │
│  ---- Gox_min (red dashed)              │
│  ---- Gox_max (red dashed)              │
│  ★ Optimal point (green star)           │
└─────────────────────────────────────────┘
```

**What it shows**: Oxidizer mass flux across the design space
**Why it matters**: Identifies valid operating regions (between red lines)
**Optimal point**: Best performance within Gox limits

#### Tab 2: Performance
Contains contour plots for:

| Plot | Unit | Description |
|------|------|-------------|
| **Ivac** | s | Vacuum specific impulse - overall efficiency metric |
| **Is** | s | Sea-level specific impulse |
| **pc** | bar | Chamber pressure |

#### Tab 3: Pressures & Flows
| Plot | Unit | Description |
|------|------|-------------|
| **pc** | bar | Chamber pressure |
| **p_inj** | bar | Pressure at injector |
| **mdot** | kg/s | Total mass flow rate |

#### Tab 4: Combustion
| Plot | Unit | Description |
|------|------|-------------|
| **MR** | - | Mixture ratio (O/F) |
| **Tc** | K | Combustion temperature |
| **r** | mm/s | Fuel regression rate |

#### Tab 5: Thermodynamics
| Plot | Unit | Description |
|------|------|-------------|
| **c*** | m/s | Characteristic velocity |
| **CF** | - | Thrust coefficient |
| **gamma** | - | Specific heat ratio |

#### Tab 6: Parametric
```
┌─────────────────────────────────────────┐
│  Ivac vs Dport/Dt at different Dinj/Dt │
│                                         │
│    Ivac ▲                               │
│    [s]  │    ___----___                 │
│         │  _/          \_               │
│         │_/              \_             │
│         └──────────────────▶            │
│              Dport/Dt                   │
│                                         │
│  [Lc/Dt Slider: ═══════●═══]            │
│              3.5                        │
└─────────────────────────────────────────┘
```

**Interactive slider**: Change Lc/Dt to see how curves shift
**Multiple lines**: Each line is a different Dinj/Dt value

### Mission Output Plots

Time-series plots showing motor behavior during the burn:

#### Tab 1: Thrust & Performance
```
┌─────────────────────────────────────────┐
│  Thrust [N]                             │
│    ▲                                    │
│    │ ████████████████████               │
│    │█                   ██              │
│    │                      █             │
│    └──────────────────────▶ Time [s]    │
├─────────────────────────────────────────┤
│  Is [s]                                 │
│    ▲                                    │
│    │════════════════════════            │
│    └──────────────────────▶ Time [s]    │
└─────────────────────────────────────────┘
```

| Plot | Description |
|------|-------------|
| **Thrust** | Force produced over time |
| **Is** | Specific impulse (efficiency) |
| **Ivac** | Vacuum specific impulse |

#### Tab 2: Pressures
| Plot | Description |
|------|-------------|
| **pc** | Chamber pressure [bar] |
| **pinj** | Injector pressure [bar] |
| **pT** | Tank pressure [bar] |

#### Tab 3: Mass Flow
| Plot | Description |
|------|-------------|
| **mdot** | Total mass flow [kg/s] |
| **mdot_ox** | Oxidizer flow [kg/s] |
| **mdot_fuel** | Fuel flow [kg/s] |

#### Tab 4: Combustion
| Plot | Description |
|------|-------------|
| **MR** | Mixture ratio [-] |
| **Gox** | Oxidizer mass flux [kg/m²s] |
| **r** | Regression rate [mm/s] |

#### Tab 5: Temperatures
| Plot | Description |
|------|-------------|
| **Tc** | Chamber temperature [K] |
| **Tc_CEA** | CEA-calculated temperature [K] |
| **TL** | Tank liquid temperature [K] |

#### Tab 6: Masses
| Plot | Description |
|------|-------------|
| **mL** | Oxidizer liquid mass [kg] |
| **m_fuel** | Remaining fuel mass [kg] |
| **mV** | Vapor mass in tank [kg] |

---

## Key Equations

### Combustion Chamber

**Chamber Pressure** (steady-state balance):
```
ṁ_throat = ṁ_ox + ṁ_fuel

pc = ṁ_throat * c* / At

where:
  ṁ_throat = mass flow through nozzle throat
  c* = characteristic velocity (from CEA)
  At = throat area = π/4 * Dt²
```

**Oxidizer Mass Flux**:
```
Gox = ṁ_ox / Ap

where:
  Ap = port area = π/4 * Dport²
```

**Fuel Regression Rate** (empirical):
```
r = a * Gox^n

where:
  a = regression rate coefficient [m/s / (kg/m²s)^n]
  n = regression rate exponent (typically 0.5-0.8)
```

**Fuel Mass Flow**:
```
ṁ_fuel = ρ_fuel * Ab * r

where:
  ρ_fuel = fuel density
  Ab = burning surface area
```

### Nozzle

**Thrust Coefficient**:
```
CF = √(2γ²/(γ-1) * (2/(γ+1))^((γ+1)/(γ-1)) * [1-(pe/pc)^((γ-1)/γ)]) + (pe-pa)/pc * ε

where:
  γ = specific heat ratio
  pe = nozzle exit pressure
  pa = ambient pressure
  ε = expansion ratio = Ae/At
```

**Thrust**:
```
F = CF * pc * At
```

**Specific Impulse**:
```
Isp = F / (ṁ * g0) = c* * CF / g0
```

### Tank (Self-Pressurizing N2O)

**Vapor-Liquid Equilibrium**:
```
pT = psat(TL)  for self-pressurizing tank
```

**Mass Balance**:
```
d(mL)/dt = -ṁ_ox
d(mV)/dt = ṁ_evap - ṁ_ox * (1-Q)
```

---

## File Structure

### Configuration Files

| File | Purpose |
|------|---------|
| `config/constants.py` | Colors, fonts, UI constants |
| `requirements.txt` | Python dependencies |

### Key Source Files

| File | Lines | Purpose |
|------|-------|---------|
| `gui/main_window.py` | ~1300 | Main application window, navigation, buttons |
| `gui/pages/mission_page.py` | ~1150 | Mission parameter inputs |
| `gui/pages/optimization_output_page.py` | ~800 | Optimization plots (contours, parametric) |
| `gui/pages/mission_output_page.py` | ~450 | Mission plots (time series) |
| `core/controller.py` | ~700 | Business logic, data preparation |
| `Mission/mission_simulation.py` | ~1150 | Core physics simulation |

### Data Flow Example: Running Optimization

```python
# 1. User clicks "Run Optimization" in main_window.py
def run_optimization(self):
    inputs = self.collect_optimization_data()  # From GUI
    
# 2. Controller prepares data (controller.py)
    prepared = self.controller.prepare_optimization_inputs(inputs)
    
# 3. Runner executes in background thread (optimization_runner.py)
    self.runner = OptimizationRunner(
        inputs=prepared,
        callback_progress=self.on_progress,
        callback_success=self.on_success,
        callback_error=self.on_error
    )
    self.runner.start()
    
# 4. Backend calculates (Performance/full_range_simulation)
    results = full_range_simulation(
        Dport_Dt_range, Dinj_Dt_range, Lc_Dt_range,
        eps, ptank, Ttank, CD, a, n, rho_fuel,
        oxidizer, fuel, pamb, gamma0, progress_callback
    )
    
# 5. Results displayed (optimization_output_page.py)
    self.output_page.display_results(results, gox_min, gox_max)
```

---

## GUI Components

### Input Fields

All input fields follow the naming convention:
```
{Page}_{Parameter}

Examples:
  Mission_Dt          → Throat diameter on Mission page
  Mission_mtank       → Tank mass on Mission page
  Optimization_Gox_min → Minimum Gox on Optimization page
```

### Auto-Calculation System

The Mission page has auto-calculation for derived parameters:

```
User inputs:
  - Grain geometry (outer_radius, n_sides, etc.)
  - Optimal ratios (Dport/Dt, Dinj/Dt, Lc/Dt)

Auto-calculated (when "Auto" checkbox is enabled):
  - Dport = calculated from grain geometry
  - Dt = Dport / (Dport/Dt)_optimal
  - Dinj = Dt * (Dinj/Dt)_optimal
  - Lc = Dt * (Lc/Dt)_optimal
```

### Grain Presets

| Preset | Fields Shown | Description |
|--------|--------------|-------------|
| Cylindrical | outer_radius | Simple circular port |
| Regular Polygon | n_sides, outer_radius, pitch | N-sided polygon (hex, etc.) |
| Custom Polygon | n_sides, outer_radius, pitch | User-defined polygon |
| Star (6/8 points) | all fields | Star-shaped grain |
| Wagon Wheel | all fields | Star with circular arcs |
| Custom (from CSV) | CSV button only | Import from file |

---

## Export Formats

### CSV Export

Simple comma-separated format:
```csv
time,Thrust,pc,Is,MR,Gox,...
0.0,0.0,101325,0.0,0.0,0.0,...
0.01,1523.5,2500000,215.3,5.2,450.2,...
...
```

### Excel Export

Multi-sheet workbook:
- **Sheet 1 (Data)**: Full time-series data
- **Sheet 2 (Summary)**: Statistics (max, mean, min for key parameters)

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "No module named tkinter" | Missing system package | `apt install python3-tk` |
| RocketCEA fails | Missing compiler | Install Visual Studio Build Tools |
| Plots don't appear | Backend issue | Check matplotlib backend is TkAgg |
| Simulation diverges | Bad parameters | Check Gox is in valid range |

### Performance Tips

1. **Start with coarse optimization** (3-5 points per parameter)
2. **Refine around optimal region** with finer resolution
3. **Use Gox limits** to filter unrealistic solutions
4. **Check expansion ratio** matches your nozzle design

---

## Version History

| Version | Changes |
|---------|---------|
| v46 | Fixed grain presets, added eps to mission, save/load mission params |
| v45 | Mission output plots (6 tabs with time-series) |
| v44 | Stop button for optimization/mission |
| v43 | Auto-calculation system for Dt |
| v42 | Requirements.txt and setup scripts |

---

*Document generated for Hybrid Rocket Simulator v46*
