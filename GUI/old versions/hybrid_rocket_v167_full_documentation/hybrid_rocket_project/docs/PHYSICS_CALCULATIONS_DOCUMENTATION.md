# Documentazione Moduli di Calcolo

Questa documentazione copre tutti i moduli che eseguono calcoli fisici e termodinamici per la simulazione del motore a razzo ibrido.

---

## Indice

1. [Performance/performance_singlepoint.py](#performanceperformance_singlepointpy)
2. [Performance/CEA_py.py](#performancecea_pypy)
3. [Injection/PyInjection.py](#injectionpyinjectionpy)
4. [Geometry/geometry_calculation.py](#geometrygeometry_calculationpy)
5. [Geometry/geometry_update.py](#geometrygeometry_updatepy)
6. [Tank/tank_update.py](#tanktank_updatepy)
7. [Mission/mission_simulation.py](#missionmission_simulationpy)
8. [Equazioni Fondamentali](#equazioni-fondamentali)
9. [Validazione e Verifica](#validazione-e-verifica)

---

## `Performance/performance_singlepoint.py`

### Scopo
Calcola le performance steady-state del motore a razzo per un singolo punto operativo: pressione camera, flussi di massa, mixture ratio, temperature di combustione, impulso specifico. È il nucleo dei calcoli termodinamici usato sia nell'ottimizzazione che nella simulazione missione.

### Dipendenze chiave
| Import | Motivo |
|--------|--------|
| `CoolProp.CoolProp` | Proprietà termodinamiche dell'ossidante (N2O, LOX, etc.) |
| `Line_losses.linelosses` | Perdite di carico nella linea di alimentazione |
| `Injection.PyInjection` | Calcolo flusso massa attraverso iniettore |
| `Performance.CEA_py` | Calcoli termochimica combustione (NASA CEA) |

### Funzioni

#### `Gammone(g)`
```python
def Gammone(g):
    G = np.sqrt(g * (2/(g + 1))**((g+1)/(g-1)))
    return G
```
- **Scopo**: Calcola la funzione Γ (Gamma-one) per gas ideale
- **Formula**: $\Gamma = \sqrt{\gamma \left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{\gamma-1}}}$
- **Utilizzo**: Flusso critico (sonico) attraverso la gola

---

#### `ER(g, pe, pc)`
```python
def ER(g, pe, pc):
    pe_pc_crit = (2/(g+1))**(g/(g-1))
    if (pe/pc) < pe_pc_crit:
        eps = Gammone(g)/np.sqrt((2*g)*((pe/pc)**(2/g) - (pe/pc)**((g+1)/g))/(g-1))
    else:
        eps = 1
    return eps
```
- **Scopo**: Calcola il rapporto di espansione ε dato il rapporto di pressione pe/pc
- **Formula** (flusso supersonico):
  $$\varepsilon = \frac{\Gamma}{\sqrt{\frac{2\gamma}{\gamma-1}\left[\left(\frac{p_e}{p_c}\right)^{2/\gamma} - \left(\frac{p_e}{p_c}\right)^{(\gamma+1)/\gamma}\right]}}$$
- **Return**: `eps = 1` se flusso subsonico (pe/pc ≥ critico)

---

#### `calculate_performance(...)`

**Parametri principali**:
| Parametro | Tipo | Unità | Descrizione |
|-----------|------|-------|-------------|
| `Ainj` | float | m² | Area totale iniettori |
| `Aport` | float | m² | Area porta grano |
| `Ab` | float | m² | Area burning |
| `eps` | float/"adapt" | - | Rapporto espansione (o "adapt" per calcolo automatico) |
| `ptank` | float | Pa | Pressione tank |
| `Ttank` | float | K | Temperatura tank |
| `pc` | float | Pa | Pressione camera (input per iterazione) |
| `CD` | float | - | Coefficiente di scarico iniettore |
| `a`, `n` | float | - | Coefficienti regression rate: r = a·Gox^n |
| `rho_fuel` | float | kg/m³ | Densità fuel solido |
| `oxidizer` | dict | - | Proprietà ossidante per CoolProp/CEA |
| `fuel` | dict | - | Proprietà fuel per CEA |
| `pamb` | float | Pa | Pressione ambiente |
| `gamma0` | float | - | Guess iniziale γ |

**Algoritmo**:
```
1. Se eps == "adapt":
   eps_out = ER(gamma0, pamb, pc)  # Calcola eps ottimale
   
2. p_inj = ptank - linelosses()  # Pressione dopo perdite

3. mdot_ox = massflow(p_inj, pc, Ttank, CD, oxidizer) * Ainj
   # Flusso ossidante attraverso iniettore

4. Gox = mdot_ox / Aport  # Mass flux ossidante

5. r = a * Gox^n  # Regression rate empirico

6. mdot_fuel = rho_fuel * Ab * r  # Flusso fuel

7. mdot = mdot_ox + mdot_fuel  # Flusso totale

8. MR = mdot_ox / mdot_fuel  # Mixture ratio O/F

9. CEA_output = runCEA(pc, MR, eps_out, oxidizer, fuel)
   Tc, MW, gamma, cs, CF_vac = CEA_output

10. CF = CF_vac - eps_out * (pamb/pc)  # Thrust coefficient con backpressure

11. Ivac = (cs * CF_vac) / g0  # Isp vacuum
12. Is = (cs * CF) / g0  # Isp sea-level
```

**Return**: Tupla di 17 valori:
| Indice | Nome | Unità | Descrizione |
|--------|------|-------|-------------|
| 0 | p_inj | Pa | Pressione iniezione |
| 1 | mdot_ox | kg/s | Flusso ossidante |
| 2 | mdot_fuel | kg/s | Flusso fuel |
| 3 | mdot | kg/s | Flusso totale |
| 4 | Gox | kg/(s·m²) | Mass flux ossidante |
| 5 | r | m/s | Regression rate |
| 6 | MR | - | Mixture ratio |
| 7 | Tc | K | Temperatura camera |
| 8 | MW | kg/kmol | Peso molecolare |
| 9 | gamma | - | Rapporto calori specifici |
| 10 | eps_out | - | Expansion ratio effettivo |
| 11 | cs | m/s | Velocità caratteristica c* |
| 12 | CF_vac | - | Thrust coefficient vacuum |
| 13 | CF | - | Thrust coefficient |
| 14 | Ivac | s | Isp vacuum |
| 15 | Is | s | Isp |
| 16 | flag | int | 0=OK, 1=CEA failed |

---

#### `pressure_fun(...)`
- **Scopo**: Funzione obiettivo per Newton solver. Trova la pc dove il bilancio di massa è soddisfatto.
- **Formula**: $F_{pc} = \frac{\dot{m} \cdot c^*}{A_t} - p_c$
- **Derivazione**: Dal bilancio di massa alla gola: $\dot{m} = \frac{p_c \cdot A_t}{c^*}$
- **Return**: `Fpc` in Pa (deve essere ≈ 0 a convergenza)

### Note critiche
- **Fallback CEA**: Se CEA fallisce (IndexError, ZeroDivisionError), ritorna `flag=1` e tutti i valori a 0. Nessun messaggio di errore esplicito.
- **Unità**: Tutti i flussi sono già moltiplicati per area (kg/s, non kg/(s·m²))
- **eps="adapt"**: Usa `gamma0` per il primo calcolo, poi aggiorna con gamma da CEA

---

## `Performance/CEA_py.py`

### Scopo
Wrapper per RocketCEA (NASA Chemical Equilibrium with Applications). Calcola le proprietà dei gas di combustione per una data combinazione ossidante/fuel a specifiche condizioni.

### Dipendenze chiave
| Import | Motivo |
|--------|--------|
| `rocketcea.cea_obj` | Libreria Python per NASA CEA |

### Funzioni

#### `runCEA(pc, MR, eps, oxCEA, fuelCEA)`

**Input**:
| Parametro | Tipo | Unità | Descrizione |
|-----------|------|-------|-------------|
| `pc` | float | Pa | Pressione camera |
| `MR` | float | - | Mixture ratio O/F |
| `eps` | float | - | Expansion ratio |
| `oxCEA` | dict | - | Definizione ossidante |
| `fuelCEA` | dict | - | Definizione fuel (può essere multiplo) |

**Formato oxidizer dict**:
```python
{
    "OxidizerCEA": "N2O",           # Nome CEA
    "Exploded Formula": "N 2 O 1",  # Formula atomica (opzionale)
    "Weight fraction": "100",       # Percentuale peso
    "Temperature [K]": 298,         # Temperatura (opzionale)
    "Specific Enthalpy [kj/mol]": -82.05  # Entalpia (opzionale)
}
```

**Formato fuel dict** (multi-componente):
```python
{
    "Fuels": ["paraffin", "HTPB"],
    "Weight fraction": ["70", "30"],
    "Exploded Formula": ["C 73 H 124", "C 4 H 6"],
    "Temperature [K]": [533, 298],
    "Specific Enthalpy [kj/mol]": [-1860.6, 45.0]
}
```

**Algoritmo**:
```
1. Costruisce stringa fuel per CEA:
   "fuel paraffin C 73 H 124 wt%= 100 t,k= 533 h,cal= -444586.42"
   (nota: h in cal/mol = kj/mol * 239.0057)

2. Costruisce stringa oxidizer per CEA

3. add_new_oxidizer('NEWOX', newoxid)
   add_new_fuel('NEWFUEL', newfuel)

4. C = CEA_Obj(oxName="NEWOX", fuelName="NEWFUEL")

5. Ivac, cs, Tc, M, g = C.get_IvacCstrTc_ThtMwGam(pc_psia, MR, eps)
   # pc in psia = pc[Pa] * 14.503773800722e-5

6. Conversioni unità:
   cs = cs * 0.3048  # ft/s → m/s
   Tc = Tc * 5/9     # °R → K

7. cfvac = (Ivac * 9.81) / cs  # Back-calculate CF_vac
```

**Return**: `[Tc, MW, gamma, cs, CF_vac]` o `[]` se fallisce

### Note critiche
- **Unità imperiali interne**: CEA usa psia, ft/s, °R. Conversioni necessarie.
- **add_new_***: Ogni chiamata aggiunge reagenti al database CEA. Non c'è cleanup → memory leak potenziale in loop lunghi.
- **Fallback vuoto**: Se Ivac=0 o cs=0, ritorna lista vuota → causa IndexError nel chiamante.

---

## `Injection/PyInjection.py`

### Scopo
Modelli di iniezione per fluidi bifase e gas. Implementa il modello NHNE (Non-Homogeneous Non-Equilibrium) di Waxman et al. per N2O auto-pressurizzante.

### Dipendenze chiave
| Import | Motivo |
|--------|--------|
| `CoolProp.CoolProp` | Proprietà termodinamiche fluidi |

### Funzioni

#### `NHNE_injection(p1, p2, T, cD, fluid)`
- **Scopo**: Modello iniezione per fluido bifase (liquido-vapore)
- **Riferimento**: Waxman, Zimmerman, Cantwell - Stanford University

**Algoritmo**:
```
1. h1 = entalpia a (p1, T)  # Stato upstream
2. h2 = entalpia a (p2, T)  # Stato downstream
3. d2 = densità a (p2, T)
4. dSPI = densità liquido saturo a T
5. pV = pressione vapore a T

6. mdot_SPI = CD * sqrt(2 * dSPI * (p1 - p2))  # Single Phase Incompressible

7. mdot_HEM = CD * d2 * sqrt(2 * |h1 - h2|)    # Homogeneous Equilibrium Model

8. Se pV > p2:  # Uscita bifase
   k = sqrt((p1 - p2) / (pV - p2))
   mdot = (k * mdot_SPI + mdot_HEM) / (k + 1)  # Media pesata
   
9. Altrimenti:  # Sempre liquido
   mdot = mdot_SPI
```

**Return**: `mdot` in kg/(s·m²) - flusso per unità di area

---

#### `gas_injection(p1, p2, T, CD, fluid)`
- **Scopo**: Iniezione gas ideale (compressibile)

**Formula flusso sonico**:
$$\dot{m} = C_D \cdot \frac{p_1}{\sqrt{R T}} \cdot \Gamma$$

**Formula flusso subsonico**:
$$\dot{m} = C_D \cdot \frac{p_1}{\sqrt{R T}} \cdot \sqrt{\frac{2\gamma}{\gamma-1}\left[\left(\frac{p_2}{p_1}\right)^{2/\gamma} - \left(\frac{p_2}{p_1}\right)^{(\gamma+1)/\gamma}\right]}$$

---

#### `gas_injection_custom(p1, p2, T, CD, gamma, M, eps=1.0)`
- **Scopo**: Come `gas_injection` ma con γ e M forniti (non da CoolProp)
- **Utilizzo**: Per gas di combustione nella camera

---

#### `massflow(p1, p2, T, CD, fluid)`
- **Scopo**: Funzione wrapper che sceglie automaticamente NHNE o gas_injection
- **Logica**: Prova NHNE; se ValueError (fluido supercritico) → usa gas_injection

### Note critiche
- **ValueError handling**: CoolProp solleva ValueError per stati fuori range (es. T > T_critica). Ogni chiamata è wrappata in try/except.
- **Backflow**: Se p1 ≤ p2, ritorna mdot=0 (nessun flusso inverso)

---

## `Geometry/geometry_calculation.py`

### Scopo
Calcola le proprietà geometriche del grano: area porta, area burning, volume camera. Gestisce varie forme (poligoni, stelle, elica).

### Funzioni

#### `create_regular_poligon(n_sides, circum_radius)`
```python
theta = 2π / n_sides
x = circum_radius * cos(theta * [0, 1, ..., n-1])
y = circum_radius * sin(theta * [0, 1, ..., n-1])
```

---

#### `sort_input(x, y, z=1)`
- **Scopo**: Ordina punti in senso antiorario (z=1) o orario (z=-1)
- **Algoritmo**: Calcola angoli `atan2(y, x)`, ordina per angolo crescente

---

#### `fill_borders(x, y, n_points_per_side)`
- **Scopo**: Interpola linearmente tra vertici per creare mesh più fitta
- **Output**: Array di n_points_per_side * n_vertices punti

---

#### `fill_borders_circumference(x, y, n_points_per_side)`
- **Scopo**: Come fill_borders, ma usa archi di cerchio se due punti hanno stesso raggio
- **Utilizzo**: Per forme con porzioni circolari (wagon wheel, etc.)

---

#### `calculate_surfaces_from_points(x, y, lc, step=0.0)`

**Algoritmo Area Porta (Erone)**:
```
Per ogni coppia di punti consecutivi (i, i+1):
  a = r[i]       # distanza punto i dall'origine
  b = r[i+1]     # distanza punto i+1 dall'origine  
  c = hypot(dx, dy)  # distanza tra i punti
  
  p = (a + b + c) / 2  # semiperimetro
  area_triangolo = sqrt(p(p-a)(p-b)(p-c))  # Formula di Erone

PortArea = sum(area_triangolo per tutti i triangoli)
```

**Burning Area**:
- `step=0`: `BurningArea = perimetro * lc`
- `step>0`: Calcolo elicoidale più complesso

---

#### `calculate_fuel_mass(Ap, lc, D_chamber, rho_fuel)`
```python
empty_volume = Ap * lc
full_volume = π/4 * D_chamber² * lc
remaining_volume = full_volume - empty_volume
mfuel = remaining_volume * rho_fuel
```

### Note critiche
- **Origine al centro**: Le funzioni assumono che l'origine (0,0) sia all'interno del poligono. Se non lo è, l'area calcolata sarà errata.
- **Orientazione**: I punti DEVONO essere ordinati (CCW o CW). Punti disordinati → area sbagliata.

---

## `Geometry/geometry_update.py`

### Scopo
Aggiorna la geometria del grano simulando la regressione del fuel nel tempo. Implementa algoritmi robusti per evitare auto-intersezioni e geometrie degeneri.

### Funzioni principali

#### `burn_surface(x, y, z, regression_rate, dt, ...)`

**Algoritmo**:
```
1. Rimuovi vertici duplicati e collineari

2. Per ogni lato i:
   - Calcola midpoint: M[i] = (P[i] + P[i+1]) / 2
   - Calcola tangente: t[i] = (P[i+1] - P[i]) / |P[i+1] - P[i]|
   - Calcola normale: n[i] = rotate(t[i], 90° * z)

3. Trasla midpoint: M'[i] = M[i] + d * n[i]
   dove d = regression_rate * dt

4. Per ogni coppia di lati adiacenti (i, i+1):
   - Trova intersezione delle linee passanti per M'[i] e M'[i+1]
     con direzioni t[i] e t[i+1]
   - Questo dà il nuovo vertice P'[i]

5. Gestisci casi speciali:
   - Lati quasi paralleli → fallback a media midpoint
   - Vertici troppo vicini → merge
   - Auto-intersezioni → shrink verso centroide

6. Cleanup: rimuovi duplicati e collineari
```

**Parametri di tuning**:
| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `min_param` | 1e-9 | Tolleranza per valori quasi-zero |
| `parallel_dot_thresh` | 0.9999 | Soglia per lati paralleli |
| `close_tol` | 1e-12 | Tolleranza per punti coincidenti |
| `merge_tol` | 1e-9 | Tolleranza per merge vertici |

---

#### `burn_surface_circular(x, y, z, regression_rate, dt, ...)`
- **Scopo**: Versione che preserva porzioni circolari (per wagon wheel)
- **Differenza**: Interpola su archi invece che linee dove appropriato

---

#### `burn_grain(x, y, z, regression_rate, dt, circular=False, ...)`
- **Scopo**: Wrapper che sceglie tra `burn_surface` e `burn_surface_circular`

### Note critiche
- **Stabilità numerica**: Molti check per evitare divisioni per zero e matrici singolari
- **Self-intersection**: Viene rilevata e corretta con shrink verso centroide
- **Performance**: ~800 righe di codice per gestire tutti i casi edge

---

## `Tank/tank_update.py`

### Scopo
Gestisce l'evoluzione del tank: self-pressurizing (N2O), pressurizzato con gas esterno (He), o solo gas.

### Funzioni

#### `build_tank(m, Q, T, oxidizer, pressurant, ppress, p, plim)`

**Logica selezione tipo tank**:
```
Se Q >= 1:  # Full gas
   constant_pressure_tank = False
   
Altrimenti se p > pV:  # Liquido ma pressione > saturazione
   constant_pressure_tank = True  # Serve pressurizzante
   
Altrimenti:  # Self-pressurizing (N2O tipico)
   constant_pressure_tank = False
```

**Return**: `(masses, volumes, pressures, temperatures, constant_pressure_tank)`

---

#### `start_conditions(...)`
- **Scopo**: Calcola condizioni iniziali per la simulazione
- **Output**: `(ptank, Ttank, mL, entropies, masses, pressures, temperatures)`

---

#### `update_tank(mdotL, dt, ...)`
- **Scopo**: Avanza lo stato del tank di un timestep

**Per tank self-pressurizing**:
1. Calcola evaporazione/condensazione
2. Aggiorna masse liquido/vapore
3. Ricalcola pressione da equilibrio vapore

**Per tank pressurizzato**:
1. Calcola flusso pressurizzante in entrata
2. Calcola eventuale venting
3. Aggiorna pressioni e temperature

---

## `Mission/mission_simulation.py`

### Scopo
Simulazione time-accurate della missione completa: dal pre-burn, attraverso l'accensione e combustione, fino allo spegnimento.

### Funzioni principali

#### `normalize_performances(list_of_dicts)`
- **Scopo**: Converte lista di dizionari (un dict per timestep) in dizionario di liste
- **Utilizzo**: Per plotting facile con `time` vs `performances['Thrust']`

---

#### `find_nozzle_output(gamma, MW, Tc, pc, mdot_throat, pamb, At, eps)`

**Algoritmo** (flusso supersonico):
```
1. Target: fMe = mdot_throat / (pc * At * eps / sqrt(R * Tc))

2. Newton iteration per trovare Me:
   fMe = sqrt(γ) * Me / sqrt((1 + 0.5*(γ-1)*Me²)^((γ+1)/(γ-1)))
   
3. Una volta trovato Me:
   Te = Tc / (1 + 0.5*(γ-1)*Me²)
   pe = pc / (1 + 0.5*(γ-1)*Me²)^(γ/(γ-1))
   Ve = Me * sqrt(γ * R * Te)
```

**Return**: `(Me, Te, pe, Ve)`

---

#### `run_one_step(...)`

**Ciclo principale**:
```python
# 1. Performance combustione
p_inj, mdot_ox, mdot_fuel, ..., flag = calculate_performance(...)

# 2. Update temperatura e proprietà gas
Tc, MW, gamma, m_c, dt = update_Temperature_and_gasproperties(...)

# 3. Burn grain (update geometria)
x, y = burn_grain(x, y, z, r, dt, circular)
Ap, Ab, Vol = fill_and_calculate_surfaces_and_volume(...)
m_fuel = calculate_fuel_mass(...)

# 4. Update pressione camera
pc = update_chamberpressure(m_c, Tc, MW, Vol)

# 5. Flusso gola
mdot_throat = gas_injection_custom(...) * At

# 6. Update tank
ptank, Ttank, mL, ... = update_tank(mdot_ox, dt, ...)

# 7. Output nozzle
Me, Te, pe, Ve = find_nozzle_output(...)

# 8. Thrust
Thrust = η_c* * η_CF * (mdot_throat * Ve + (pe - pamb) * eps * At)
```

---

#### `run_full_mission(...)`

**Struttura**:
```
1. Condizioni iniziali (delay_time secondi a pc=pamb)

2. Loop principale while (t < burn_time) AND (mL > 0) AND (m_fuel > 0):
   - run_one_step()
   - Accumula risultati
   - t += dt
   
3. Spegnimento (flusso residuo, pressione cala)

4. Return (time_array, performances_list, log_string)
```

---

#### `match_mission(...)`
- **Scopo**: Trova iterativamente i parametri per matchare un target burn_time
- **Algoritmo**: Varia la massa tank e/o geometria, ri-esegue run_full_mission

---

## Equazioni Fondamentali

### Bilancio di massa alla gola
$$\dot{m}_{throat} = \frac{p_c \cdot A_t}{c^*}$$

dove c* è la velocità caratteristica:
$$c^* = \frac{\sqrt{\gamma R T_c}}{\Gamma}$$

### Spinta
$$F = \dot{m} \cdot V_e + (p_e - p_{amb}) \cdot A_e$$

oppure:
$$F = C_F \cdot p_c \cdot A_t$$

dove:
$$C_F = C_{F,vac} - \varepsilon \cdot \frac{p_{amb}}{p_c}$$

### Regression rate (empirico)
$$r = a \cdot G_{ox}^n$$

dove $G_{ox} = \dot{m}_{ox} / A_{port}$ [kg/(s·m²)]

### Mixture ratio
$$MR = \frac{\dot{m}_{ox}}{\dot{m}_{fuel}} = \frac{\dot{m}_{ox}}{\rho_{fuel} \cdot A_b \cdot r}$$

### Impulso specifico
$$I_{sp} = \frac{F}{\dot{m} \cdot g_0} = \frac{c^* \cdot C_F}{g_0}$$

### Rapporto di espansione critico
$$\left(\frac{p_e}{p_c}\right)_{crit} = \left(\frac{2}{\gamma+1}\right)^{\gamma/(\gamma-1)}$$

### Funzione Γ (Gammone)
$$\Gamma = \sqrt{\gamma \left(\frac{2}{\gamma+1}\right)^{(\gamma+1)/(\gamma-1)}}$$

### Temperatura di uscita ugello (isoentropico)
$$\frac{T_e}{T_c} = \frac{1}{1 + \frac{\gamma-1}{2}M_e^2}$$

### Pressione di uscita ugello
$$\frac{p_e}{p_c} = \left(\frac{T_e}{T_c}\right)^{\gamma/(\gamma-1)}$$

---

## Validazione e Verifica

### Test consigliati

#### 1. Verifica conservation of mass
```python
# A ogni timestep:
assert abs(mdot_ox + mdot_fuel - mdot_throat) < tolerance * mdot_throat
```

#### 2. Verifica pressure_fun convergenza
```python
# Dopo Newton iteration:
assert abs(Fpc) < 0.1  # Pa
```

#### 3. Verifica geometria
```python
# Area porta deve crescere con regression
assert Ap[t+1] > Ap[t]

# Massa fuel deve calare
assert m_fuel[t+1] < m_fuel[t]

# Area burning può crescere o calare (forma-dipendente)
```

#### 4. Verifica termodinamica
```python
# Tc deve essere ragionevole
assert 1000 < Tc < 4000  # K per N2O/paraffin

# Gamma deve essere in range
assert 1.1 < gamma < 1.4

# MR tipico per N2O/paraffin
assert 3 < MR < 10
```

#### 5. Verifica nozzle
```python
# Per flusso sonico alla gola
assert Me_throat ≈ 1.0

# Pressione uscita deve essere < pressione camera
assert pe < pc

# Per flusso supersonico in divergente
assert Me_exit > 1.0
```

### Valori tipici di riferimento

| Parametro | N2O/Paraffin | N2O/HTPB |
|-----------|--------------|----------|
| Tc | 3200-3500 K | 3000-3300 K |
| c* | 1500-1700 m/s | 1450-1600 m/s |
| Isp (vac) | 280-310 s | 260-290 s |
| MR ottimale | 6-8 | 5-7 |
| γ | 1.15-1.25 | 1.18-1.28 |
| a (paraffin) | 0.1-0.2 mm/s | - |
| n (paraffin) | 0.5-0.7 | - |

---

## Diagramma flusso calcoli

```
┌─────────────────────────────────────────────────────────────────────┐
│                         OTTIMIZZAZIONE                               │
└─────────────────────────────────────────────────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
   ┌─────────┐              ┌─────────┐              ┌─────────┐
   │Dport/Dt │              │Dinj/Dt  │              │Lc/Dt    │
   │ range   │              │ range   │              │ range   │
   └────┬────┘              └────┬────┘              └────┬────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  for each combination  │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │   get_pressure()       │
                    │   Newton iteration     │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │ calculate_performance()│
                    └───────────┬────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
   ┌─────────┐            ┌─────────┐            ┌─────────┐
   │Injection│            │   CEA   │            │ Nozzle  │
   │ model   │            │(runCEA) │            │ output  │
   └─────────┘            └─────────┘            └─────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │   Store in arrays      │
                    │   pc, Isp, Gox, etc.   │
                    └────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                        MISSION SIMULATION                            │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌────────────────────────┐
                    │  get_starting_         │
                    │  conditions()          │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │  while t < burn_time   │◄────────────────────┐
                    │  AND mL > 0            │                     │
                    │  AND m_fuel > 0        │                     │
                    └───────────┬────────────┘                     │
                                │                                  │
                                ▼                                  │
                    ┌────────────────────────┐                     │
                    │   run_one_step()       │                     │
                    └───────────┬────────────┘                     │
                                │                                  │
        ┌───────────┬───────────┼───────────┬───────────┐          │
        │           │           │           │           │          │
        ▼           ▼           ▼           ▼           ▼          │
   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐      │
   │Inject. │  │  CEA   │  │ Burn   │  │Chamber │  │  Tank  │      │
   │massflow│  │(perf)  │  │ grain  │  │pressure│  │ update │      │
   └────────┘  └────────┘  └────────┘  └────────┘  └────────┘      │
        │           │           │           │           │          │
        └───────────┴───────────┼───────────┴───────────┘          │
                                │                                  │
                                ▼                                  │
                    ┌────────────────────────┐                     │
                    │  find_nozzle_output()  │                     │
                    │  Thrust calculation    │                     │
                    └───────────┬────────────┘                     │
                                │                                  │
                                ▼                                  │
                    ┌────────────────────────┐                     │
                    │  Store performances    │                     │
                    │  t += dt               │─────────────────────┘
                    └────────────────────────┘
```
