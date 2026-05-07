# Documentazione Sistema di Dimensionalizzazione

## Panoramica

Il sistema di simulazione utilizza un approccio di **adimensionalizzazione basato sul diametro gola** ($D_t$) per l'ottimizzazione, seguito da una **ri-dimensionalizzazione** per la simulazione missione. Questo documento traccia il flusso completo dei calcoli geometrici attraverso tutti i file del progetto.

---

## Indice

1. [Concetto Fondamentale](#1-concetto-fondamentale)
2. [Fase 1: Ottimizzazione Adimensionale](#2-fase-1-ottimizzazione-adimensionale)
3. [Fase 2: Ri-dimensionalizzazione per Missione](#3-fase-2-ri-dimensionalizzazione-per-missione)
4. [Calcolo Area Porta e Diametro Equivalente](#4-calcolo-area-porta-e-diametro-equivalente)
5. [Scaling della Geometria del Grano](#5-scaling-della-geometria-del-grano)
6. [Flusso Dati Completo](#6-flusso-dati-completo)
7. [Formule di Conversione](#7-formule-di-conversione)
8. [Verifica e Validazione](#8-verifica-e-validazione)

---

## 1. Concetto Fondamentale

### 1.1 Perché Adimensionalizzare?

L'ottimizzazione esplora lo spazio di design usando **rapporti adimensionali**:

| Rapporto | Simbolo | Descrizione |
|----------|---------|-------------|
| $D_{port}/D_t$ | `Dport_Dt` | Rapporto diametro porta / diametro gola |
| $D_{inj}/D_t$ | `Dinj_Dt` | Rapporto diametro iniettore / diametro gola |
| $L_c/D_t$ | `Lc_Dt` | Rapporto lunghezza camera / diametro gola |

**Vantaggi**:
1. Risultati scalabili a qualsiasi dimensione di motore
2. Riduzione dello spazio parametrico (3D invece di 6D)
3. Le proprietà termodinamiche (Isp, MR, Tc) sono **invarianti** rispetto alla scala

### 1.2 Il Diametro Gola come Riferimento

Il diametro gola $D_t$ è scelto come riferimento perché:
- Determina la spinta massima ($F \propto p_c \cdot A_t$)
- È il collo di bottiglia del flusso
- È facilmente misurabile e controllabile

---

## 2. Fase 1: Ottimizzazione Adimensionale

### 2.1 File: `core/controller.py` (linee 149-305)

**Metodo**: `prepare_optimization_inputs()`

```python
# Linee 162-165
dport_range = np.linspace(opt.dport_dt_min, opt.dport_dt_max, opt.parameter_points)
dinj_range = np.linspace(opt.dinj_dt_min, opt.dinj_dt_max, opt.parameter_points)
lc_range = np.linspace(opt.lc_dt_min, opt.lc_dt_max, opt.parameter_points)
```

**Input utente** (da `gui/pages/optimization_page.py`):
- `dport_dt_min`, `dport_dt_max`: Range del rapporto Dport/Dt (tipico: 1.5 - 4.0)
- `dinj_dt_min`, `dinj_dt_max`: Range del rapporto Dinj/Dt (tipico: 0.1 - 0.8)
- `lc_dt_min`, `lc_dt_max`: Range del rapporto Lc/Dt (tipico: 2.0 - 8.0)
- `parameter_points`: Numero di punti per asse (tipico: 10-20)

**Output**: Dizionario con chiavi `Dport_Dt_range`, `Dinj_Dt_range`, `Lc_Dt_range`

---

### 2.2 File: `backend/optimization.py` (linee 176-328)

**Funzione**: `full_range_simulation()`

```python
# Linea 261 - NORMALIZZAZIONE FONDAMENTALE
Dt = 1  # Il diametro gola è fissato a 1 (unità normalizzata)

# Linee 262-275 - Loop principale
for ind_Dport, Dport in enumerate(Dport_Dt_range):
    for ind_Dinj, Dinj in enumerate(Dinj_Dt_range):
        for ind_Lc, Lc in enumerate(Lc_Dt_range):
            
            # Calcolo aree NORMALIZZATE (tutte divise per Dt²)
            Aport = 0.25 * np.pi * (Dport**2)   # Area porta / Dt²
            Ainj = 0.25 * np.pi * (Dinj**2)     # Area iniezione / Dt²
            At = 0.25 * np.pi * (Dt**2)         # = π/4 (costante)
            Ab = np.pi * Dport * Lc              # Area burning / Dt²
```

**Relazioni geometriche** (con $D_t = 1$):

$$A_{port}^* = \frac{\pi}{4} \left(\frac{D_{port}}{D_t}\right)^2 = \frac{\pi}{4} \cdot D_{port}^{*2}$$

$$A_t^* = \frac{\pi}{4} \cdot 1^2 = \frac{\pi}{4}$$

$$A_b^* = \pi \cdot D_{port}^* \cdot L_c^*$$

dove l'asterisco * indica grandezze normalizzate.

---

### 2.3 Invarianza delle Performance

**File**: `Performance/performance_singlepoint.py` (linee 25-132)

Le seguenti quantità sono **indipendenti dalla scala**:
- Pressione camera $p_c$ [Pa]
- Mixture ratio $MR = \dot{m}_{ox}/\dot{m}_{fuel}$
- Temperatura camera $T_c$ [K]
- Impulso specifico $I_{sp}$ [s]
- Mass flux ossidante $G_{ox}$ [kg/(s·m²)]

Le seguenti quantità **scalano con $D_t^2$**:
- Flussi di massa: $\dot{m} \propto D_t^2$
- Spinta: $F \propto D_t^2$
- Area gola: $A_t \propto D_t^2$

---

## 3. Fase 2: Ri-dimensionalizzazione per Missione

### 3.1 File: `core/controller.py` (linee 446-514)

**Metodo**: `prepare_mission_inputs()`

```python
# Linee 446-456 - CONVERSIONE DA ADIMENSIONALE A DIMENSIONALE
Dt = mission_data['Dt']                    # Diametro gola REALE [m]
At = 0.25 * np.pi * Dt**2                  # Area gola REALE [m²]

Dport_Dt = mission_data['Dport_Dt_optimal']  # Rapporto ottimale dall'ottimizzazione
Dinj_Dt = mission_data['Dinj_Dt_optimal']
Lc_Dt = mission_data['Lc_Dt_optimal']

Dport = Dport_Dt * Dt   # Diametro porta REALE [m]
Dinj = Dinj_Dt * Dt     # Diametro iniettore REALE [m]
Lc = Lc_Dt * Dt         # Lunghezza camera REALE [m]

# Linee 459-460 - Area iniezione con numero iniettori
n_inj = mission_data['n_injectors']
Ainj = n_inj * 0.25 * np.pi * Dinj**2   # Area TOTALE iniezione [m²]
```

**Esempio numerico**:
```
Input utente:
  Dt = 0.030 m (30 mm)
  Dport_Dt_optimal = 2.5 (dall'ottimizzazione)
  Dinj_Dt_optimal = 0.3
  Lc_Dt_optimal = 4.0
  n_injectors = 6

Output:
  Dport = 2.5 × 0.030 = 0.075 m (75 mm)
  Dinj = 0.3 × 0.030 = 0.009 m (9 mm per iniettore)
  Lc = 4.0 × 0.030 = 0.120 m (120 mm)
  Ainj = 6 × π/4 × 0.009² = 3.82e-4 m²
  At = π/4 × 0.030² = 7.07e-4 m²
```

---

## 4. Calcolo Area Porta e Diametro Equivalente

### 4.1 File: `Geometry/geometry_calculation.py` (linee 205-261)

**Funzione**: `calculate_surfaces_from_points(x, y, lc, step=0.0)`

Calcola l'area porta usando la **formula di Erone** per triangoli con vertice all'origine:

```python
# Linee 217-235
r = np.hypot(x, y)  # Distanza di ogni punto dall'origine

x2 = np.r_[x, x[0]]  # Chiude il poligono
y2 = np.r_[y, y[0]]
r2 = np.r_[r, r[0]]

dx = np.diff(x2)
dy = np.diff(y2)

# Per ogni coppia di punti consecutivi (i, i+1):
a = r2[:-1]           # Distanza punto i dall'origine
b = r2[1:]            # Distanza punto i+1 dall'origine
c = np.hypot(dx, dy)  # Distanza tra i due punti

# Formula di Erone: Area = sqrt(s(s-a)(s-b)(s-c)) dove s = (a+b+c)/2
p = (a + b + c) / 2
area_term = p * (p - a) * (p - b) * (p - c)
area_term[area_term < 0] = 0.0  # Protezione numerica
areas = np.sqrt(area_term)

PortArea = np.sum(areas)  # Somma di tutti i triangoli
```

**Diagramma del calcolo**:
```
                    P[i+1]
                   /|
                  / |
               b /  | 
                /   |
               /    |
              /  T  | c (lato del poligono)
             /      |
            /       |
           /________|
     Origin    a    P[i]
     (0,0)
     
Ogni triangolo T ha:
- vertice all'origine
- base = segmento P[i] → P[i+1]
- Area calcolata con Erone
```

### 4.2 Diametro Equivalente

Il **diametro equivalente** $D_{eq}$ è il diametro del cerchio con stessa area:

$$D_{eq} = \sqrt{\frac{4 \cdot A_{port}}{\pi}}$$

**File**: `core/controller.py` (linee 567-569, 614-615, 677-678)

```python
# Calcolo diametro equivalente dalla geometria normalizzata
Ap_norm, _ = geom.calculate_surfaces_from_points(x_norm, y_norm, lc=1.0, step=0.0)
Deq_norm = np.sqrt(4 * Ap_norm / np.pi)
```

**File**: `gui/pages/mission_page.py` (linee 888-890, 940-941)

```python
# Preview nella GUI
from Geometry.geometry_calculation import calculate_surfaces_from_points
Ap, _ = calculate_surfaces_from_points(x, y, 1.0, 0.0)
Deq = np.sqrt(4 * Ap / np.pi)
```

---

## 5. Scaling della Geometria del Grano

### 5.1 File: `core/controller.py` (linee 516-694)

**Metodo**: `_generate_grain_geometry(mission_data, Dport)`

L'algoritmo di scaling preserva la **forma** del grano mentre scala le dimensioni:

```python
# STEP 1: Crea geometria normalizzata (forma desiderata)
# Per Regular Polygon (linee 608-620):
theta = np.linspace(0, 2*np.pi, n_sides, endpoint=False)
x_norm = outer_r * np.cos(theta)
y_norm = outer_r * np.sin(theta)

# STEP 2: Calcola diametro equivalente della forma normalizzata
Ap_norm, _ = geom.calculate_surfaces_from_points(x_norm, y_norm, lc=1.0, step=0.0)
Deq_norm = np.sqrt(4 * Ap_norm / np.pi)

# STEP 3: Calcola fattore di scala per matchare Dport target
scale_factor = Dport / Deq_norm

# STEP 4: Applica scaling uniforme
x = x_norm * scale_factor
y = y_norm * scale_factor
```

**Proprietà preservate dallo scaling**:
- Forma geometrica (angoli, proporzioni)
- Numero di lati/vertici
- Orientazione (counter-clockwise)

**Proprietà che scalano**:
- Area porta: $A_{port} \propto scale\_factor^2$
- Perimetro: $P \propto scale\_factor$
- Diametro equivalente: $D_{eq} \propto scale\_factor$

### 5.2 Tipi di Geometria Supportati

| Preset | File | Linee | Descrizione |
|--------|------|-------|-------------|
| Cylindrical | `controller.py` | 596-605 | Cerchio con 36 punti |
| Regular Polygon | `controller.py` | 608-630 | N-gono regolare |
| Star | `controller.py` | 635-649 | 2N punti alternati inner/outer |
| Wagon Wheel | `controller.py` | 651-664 | Cerchio con notch |
| Custom (from CSV) | `controller.py` | 534-586 | Punti da file esterno |

### 5.3 Esempio: Star Grain

```python
# File: core/controller.py, linee 635-649
# Star geometry: alternating inner/outer radii
theta_double = np.linspace(0, 2*np.pi, 2*n_sides, endpoint=False)
for i, t in enumerate(theta_double):
    if i % 2 == 0:
        r = outer_r   # Punta della stella
    else:
        r = inner_r   # Valle della stella
    x_norm.append(r * np.cos(t))
    y_norm.append(r * np.sin(t))
```

**Diagramma** (n_sides=4, inner_r=0.5, outer_r=1.0):
```
              * (outer_r)
             /|\
            / | \
           /  |  \
          *---+---* (inner_r)
           \  |  /
            \ | /
             \|/
              * (outer_r)
```

---

## 6. Flusso Dati Completo

### 6.1 Ottimizzazione → Missione

```
┌─────────────────────────────────────────────────────────────────────┐
│                        OTTIMIZZAZIONE                                │
│ File: gui/pages/optimization_page.py                                 │
│ Input: Dport/Dt range, Dinj/Dt range, Lc/Dt range                   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ File: core/controller.py - prepare_optimization_inputs()            │
│ Linee 149-305                                                        │
│ Crea: dport_range, dinj_range, lc_range con np.linspace            │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ File: backend/optimization.py - full_range_simulation()             │
│ Linee 176-328                                                        │
│                                                                      │
│ Dt = 1 (NORMALIZZATO)                                               │
│                                                                      │
│ Per ogni combinazione (Dport/Dt, Dinj/Dt, Lc/Dt):                   │
│   Aport = π/4 × (Dport/Dt)²                                         │
│   Ainj = π/4 × (Dinj/Dt)²                                           │
│   At = π/4                                                          │
│   Ab = π × (Dport/Dt) × (Lc/Dt)                                     │
│                                                                      │
│ Output: Array 3D di Isp, pc, Gox, MR, etc.                          │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ File: gui/pages/optimization_output_page.py                          │
│ Visualizza contour plots, trova ottimo                               │
│ Output: Dport_Dt_optimal, Dinj_Dt_optimal, Lc_Dt_optimal            │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           MISSIONE                                   │
│ File: gui/pages/mission_page.py                                      │
│ Input utente: Dt [m], n_injectors, grain preset                     │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ File: core/controller.py - prepare_mission_inputs()                  │
│ Linee 400-514                                                        │
│                                                                      │
│ RIDIMENSIONALIZZAZIONE:                                             │
│   Dport = Dport_Dt_optimal × Dt                                     │
│   Dinj = Dinj_Dt_optimal × Dt                                       │
│   Lc = Lc_Dt_optimal × Dt                                           │
│   At = π/4 × Dt²                                                    │
│   Ainj = n_inj × π/4 × Dinj²                                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ File: core/controller.py - _generate_grain_geometry()                │
│ Linee 516-694                                                        │
│                                                                      │
│ 1. Genera forma normalizzata (inner_r, outer_r, n_sides)            │
│ 2. Calcola Deq_norm = sqrt(4 × Ap_norm / π)                         │
│ 3. scale_factor = Dport / Deq_norm                                  │
│ 4. x_scaled = x_norm × scale_factor                                 │
│    y_scaled = y_norm × scale_factor                                 │
│                                                                      │
│ Output: x, y, z (geometria scalata in metri)                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ File: Mission/mission_simulation.py - run_full_mission()            │
│ Linee 443-600                                                        │
│                                                                      │
│ Usa geometria scalata per simulazione time-accurate                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Formule di Conversione

### 7.1 Tabella di Conversione Adimensionale ↔ Dimensionale

| Grandezza | Adimensionale | Dimensionale | Conversione |
|-----------|---------------|--------------|-------------|
| Diametro porta | $D_{port}^* = D_{port}/D_t$ | $D_{port}$ [m] | $D_{port} = D_{port}^* \times D_t$ |
| Area porta | $A_{port}^* = A_{port}/D_t^2$ | $A_{port}$ [m²] | $A_{port} = A_{port}^* \times D_t^2$ |
| Area gola | $A_t^* = \pi/4$ | $A_t$ [m²] | $A_t = \frac{\pi}{4} D_t^2$ |
| Lunghezza camera | $L_c^* = L_c/D_t$ | $L_c$ [m] | $L_c = L_c^* \times D_t$ |
| Area burning | $A_b^* = A_b/D_t^2$ | $A_b$ [m²] | $A_b = A_b^* \times D_t^2$ |
| Volume camera | $V^* = V/D_t^3$ | $V$ [m³] | $V = V^* \times D_t^3$ |
| Flusso massa | $\dot{m}^* = \dot{m}/D_t^2$ | $\dot{m}$ [kg/s] | $\dot{m} = \dot{m}^* \times D_t^2$ |
| Spinta | $F^* = F/D_t^2$ | $F$ [N] | $F = F^* \times D_t^2$ |

### 7.2 Grandezze Invarianti (non dipendono da $D_t$)

| Grandezza | Unità | Note |
|-----------|-------|------|
| Pressione camera $p_c$ | Pa | Dipende solo dai rapporti |
| Mixture ratio $MR$ | - | $MR = \dot{m}_{ox}/\dot{m}_{fuel}$ |
| Temperature $T_c$, $T_e$ | K | Proprietà termodinamiche |
| Impulso specifico $I_{sp}$ | s | $I_{sp} = F/(\dot{m} \cdot g_0)$ |
| Mass flux $G_{ox}$ | kg/(s·m²) | $G_{ox} = \dot{m}_{ox}/A_{port}$ |
| Regression rate $r$ | m/s | $r = a \cdot G_{ox}^n$ |
| Rapporto espansione $\varepsilon$ | - | $\varepsilon = A_e/A_t$ |

---

## 8. Verifica e Validazione

### 8.1 Test di Consistenza Geometrica

**File consigliato per test**: `test_grain_geometry.py`

```python
import numpy as np
from Geometry import geometry_calculation as geom
from core.controller import ApplicationController

# Test 1: Verifica che lo scaling preservi il rapporto area/diametro
def test_scaling_preserves_shape():
    # Crea stella normalizzata
    n_sides = 5
    inner_r = 0.5
    outer_r = 1.0
    
    theta = np.linspace(0, 2*np.pi, 2*n_sides, endpoint=False)
    x_norm = [outer_r if i%2==0 else inner_r for i in range(2*n_sides)]
    x_norm = np.array([r * np.cos(t) for r, t in zip(x_norm, theta)])
    y_norm = np.array([r * np.sin(t) for r, t in zip(
        [outer_r if i%2==0 else inner_r for i in range(2*n_sides)], 
        theta
    )])
    
    # Calcola proprietà normalizzate
    Ap_norm, Ab_norm = geom.calculate_surfaces_from_points(x_norm, y_norm, 1.0, 0.0)
    Deq_norm = np.sqrt(4 * Ap_norm / np.pi)
    
    # Scala a Dport target
    Dport_target = 0.075  # 75 mm
    scale = Dport_target / Deq_norm
    x_scaled = x_norm * scale
    y_scaled = y_norm * scale
    
    # Verifica
    Ap_scaled, _ = geom.calculate_surfaces_from_points(x_scaled, y_scaled, 1.0, 0.0)
    Deq_scaled = np.sqrt(4 * Ap_scaled / np.pi)
    
    assert np.isclose(Deq_scaled, Dport_target, rtol=1e-6), \
        f"Deq mismatch: {Deq_scaled} != {Dport_target}"
    
    print(f"✓ Scaling test passed: Deq = {Deq_scaled*1000:.3f} mm")

# Test 2: Verifica invarianza Isp con diversi Dt
def test_isp_invariance():
    # Simula con Dt = 0.020 m
    Dt_1 = 0.020
    # ... (chiamata ottimizzazione con Dport/Dt = 2.5)
    Isp_1 = ...  # Risultato
    
    # Simula con Dt = 0.040 m
    Dt_2 = 0.040
    # ... (stessa chiamata con Dport/Dt = 2.5)
    Isp_2 = ...  # Risultato
    
    assert np.isclose(Isp_1, Isp_2, rtol=1e-3), \
        f"Isp should be invariant: {Isp_1} != {Isp_2}"
```

### 8.2 Checklist di Validazione

| Check | File di riferimento | Criterio |
|-------|---------------------|----------|
| Area porta = π/4 × Dport² per cilindro | `geometry_calculation.py:205` | Errore < 0.1% |
| Deq_scaled = Dport_target | `controller.py:575` | Errore < 0.01% |
| Isp invariante con scala | `optimization.py` | Errore < 1% |
| Ab = π × Dport × Lc per cilindro | `optimization.py:275` | Esatto |
| Somma aree triangoli = Area totale | `geometry_calculation.py:235` | Teorema Erone |

### 8.3 Errori Comuni e Debug

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| `Deq_norm = 0` | Geometria con area nulla | Verificare punti non collineari |
| `scale_factor = inf` | Dport > 0 ma Deq_norm ≈ 0 | Check `Deq_norm > 1e-12` |
| Area negativa | Punti in senso orario | Usare `sort_input(x, y, z=1)` |
| Isp varia con Dt | Bug nel flusso dati | Verificare che `Dt=1` in ottimizzazione |

---

## Appendice: Riferimenti Codice per File

### `backend/optimization.py`
- **Linea 261**: `Dt = 1` - Normalizzazione fondamentale
- **Linee 272-275**: Calcolo aree normalizzate
- **Linee 290-293**: Commenti su unità normalizzate

### `core/controller.py`
- **Linee 162-165**: Creazione range adimensionali
- **Linee 446-460**: Ri-dimensionalizzazione Dport, Dinj, Lc
- **Linee 567-575**: Calcolo Deq e scale_factor
- **Linee 680-683**: Scaling finale della geometria

### `Geometry/geometry_calculation.py`
- **Linee 205-261**: `calculate_surfaces_from_points()` - Formula di Erone
- **Linee 263-288**: `fill_and_calculate_surfaces_and_volume()`
- **Linee 290-304**: `calculate_fuel_mass()`

### `Geometry/dimensionalize.py`
- **Linee 8-61**: `dimensionalize_geometry()` - Scaling alternativo
- **Linea 23**: Calcolo `Deq_0`
- **Linee 25-27**: Scaling coordinate e step

### `gui/pages/mission_page.py`
- **Linee 888-901**: Preview Deq da CSV
- **Linee 932-956**: Preview geometria in GUI
