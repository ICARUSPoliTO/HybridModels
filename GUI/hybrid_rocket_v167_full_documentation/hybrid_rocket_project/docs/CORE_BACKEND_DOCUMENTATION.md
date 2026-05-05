# Documentazione Moduli Core e Backend

---

## `core/data_structures.py`

### Scopo
Definisce le strutture dati immutabili (dataclass) per rappresentare lo stato dell'applicazione. Fornisce un contratto tipizzato per la comunicazione tra GUI, controller e persistenza, garantendo consistenza dei dati attraverso i vari moduli.

### Dipendenze chiave
| Import | Motivo |
|--------|--------|
| `dataclasses.dataclass, asdict` | Decoratore per creare classi dati con metodi automatici (`__init__`, `__repr__`, `__eq__`) e serializzazione a dizionario |
| `typing.Dict, Any, List` | Type hints per documentare la struttura attesa dei campi |

### Classi

#### `ConfigurationData`
- **Scopo**: Contenitore per tutti i parametri della pagina Configuration (ossidante, fuel, proprietà fisiche, coefficienti)

- **Costruttore `__init__`**:
  | Parametro | Tipo | Descrizione |
  |-----------|------|-------------|
  | `inputs` | `Dict[str, Any]` | Valori dei campi Entry (es. `Fuel_a`, `Fuel_n`, `Oxidizer_CoolProp`) |
  | `dropdowns` | `Dict[str, str]` | Selezioni dei menu dropdown (es. `Oxidizer_CEA`, `Fuel_Type`) |
  | `selected_fuels` | `List[str]` | Lista dei nomi fuel selezionati per miscele multi-fuel |
  | `fuel_weight_entries` | `Dict[str, float]` | Percentuali in peso per ogni fuel nella miscela |

- **Metodi principali**:
  | Metodo | Parametri | Cosa fa | Stato modificato |
  |--------|-----------|---------|------------------|
  | `to_dict()` | nessuno | Converte l'istanza in dizionario usando `asdict()` per serializzazione JSON/CSV | Nessuno (puro) |
  | `from_dict(cls, data)` | `data: dict` | Factory method che ricostruisce l'istanza da un dizionario | Nessuno (costruttore) |

---

#### `OptimizationData`
- **Scopo**: Contenitore per i parametri della pagina Optimization (range adimensionali, condizioni operative, limiti Gox)

- **Costruttore `__init__`**:
  | Parametro | Tipo | Default | Descrizione |
  |-----------|------|---------|-------------|
  | `parameter_points` | `int` | - | Numero di punti per ogni asse del parametric sweep |
  | `dport_dt_min/max` | `float` | - | Range del rapporto Dport/Dt |
  | `dinj_dt_min/max` | `float` | - | Range del rapporto Dinj/Dt |
  | `lc_dt_min/max` | `float` | - | Range del rapporto Lc/Dt |
  | `ptank` | `float` | - | Pressione tank [Pa] |
  | `ttank` | `float` | - | Temperatura tank [K] |
  | `pamb` | `float` | - | Pressione ambiente [Pa] |
  | `gox_min` | `float` | `100.0` | Limite inferiore Gox per filtraggio risultati [kg/(s·m²)] |
  | `gox_max` | `float` | `800.0` | Limite superiore Gox per filtraggio risultati [kg/(s·m²)] |

- **Metodi principali**:
  | Metodo | Parametri | Cosa fa | Stato modificato |
  |--------|-----------|---------|------------------|
  | `to_dict()` | nessuno | Serializza tutti i campi a dizionario | Nessuno |
  | `from_dict(cls, data)` | `data: dict` | Ricostruisce istanza; converte automaticamente tipi | Nessuno |

---

#### `MissionData`
- **Scopo**: Placeholder per futuri parametri missione (attualmente vuoto, `pass`)

- **Note**: Classe stub destinata a contenere `burn_time`, `target_altitude`, `payload_mass`, etc.

---

## `core/data_manager.py`

### Scopo
Gestisce tutte le operazioni di I/O su file CSV per persistenza dati. Centralizza la logica di serializzazione/deserializzazione, isolando il resto dell'applicazione dai dettagli di formato file.

### Dipendenze chiave
| Import | Motivo |
|--------|--------|
| `csv` | Lettura/scrittura file CSV |
| `json` | Serializzazione liste e dizionari nested (es. `selected_fuels`) dentro celle CSV |
| `core.data_structures` | Accesso ai tipi `ConfigurationData`, `OptimizationData` |

### Classi

#### `DataManager`
- **Scopo**: Classe con metodi statici per save/load di configuration, optimization e results

- **Costruttore `__init__`**: Nessuno (tutti i metodi sono `@staticmethod`)

- **Metodi principali**:

  | Metodo | Parametri | Cosa fa | Stato modificato |
  |--------|-----------|---------|------------------|
  | `save_configuration_csv(data, filepath)` | `data: ConfigurationData`, `filepath: str` | Scrive CSV con formato `[Parameter, Value]`. Usa `json.dumps()` per campi lista/dict (`selected_fuels`, `fuel_weight_entries`) | File system |
  | `load_configuration_csv(filepath)` | `filepath: str` | Legge CSV, ricostruisce dizionari separando inputs/dropdowns in base al prefisso chiave (`Fuel`, `Oxidiser`, `Nozzle`). Deserializza JSON per liste | Nessuno |
  | `save_optimization_csv(data, filepath)` | `data: OptimizationData`, `filepath: str` | Serializza `to_dict()` in CSV semplice key-value | File system |
  | `load_optimization_csv(filepath)` | `filepath: str` | Legge CSV, converte `parameter_points` a `int`, resto a `float` | Nessuno |
  | `save_results_csv(results, config_data, opt_data, filepath)` | `results: Dict`, `config_data`, `opt_data`, `filepath` | Scrive report CSV multi-sezione: config summary, optimization params, results con statistiche (min/max/mean) per ogni array numpy | File system |

- **Return type comune**: Tutti i metodi ritornano `Tuple[bool, str]` (save) o `Tuple[bool, Optional[Dict], str]` (load) per gestione errori uniforme

### Flusso di esecuzione
1. GUI chiama `controller.save_configuration(filepath)`
2. Controller delega a `DataManager.save_configuration_csv()`
3. DataManager itera sui campi, serializza, scrive CSV
4. Ritorna `(True, "success message")` o `(False, "error: ...")`

### Note critiche
- **Formato JSON embedded**: I campi `selected_fuels` e `fuel_weight_entries` sono serializzati come JSON dentro una cella CSV. Parsing fragile se il JSON contiene virgole non escapate.
- **Discriminazione prefisso**: La logica `key.startswith('Fuel')` per distinguere inputs da dropdowns è fragile; un campo `Fuel_custom_input` verrebbe erroneamente classificato come dropdown.
- **Encoding**: Hardcoded `utf-8`, potrebbe fallire su sistemi Windows con encoding locale diverso.

---

## `core/controller.py`

### Scopo
Controller centrale dell'applicazione secondo pattern MVC. Coordina il flusso dati tra GUI e backend, mantiene lo stato applicativo (configuration, optimization, results), valida la readiness per operazioni, e prepara gli input per le funzioni di simulazione.

### Dipendenze chiave
| Import | Motivo |
|--------|--------|
| `numpy` | Creazione range con `linspace`, operazioni su array geometria |
| `core.data_structures` | Tipi `ConfigurationData`, `OptimizationData` |
| `core.data_manager.DataManager` | Delegazione operazioni file |
| `Geometry.geometry_calculation` | Import lazy per generazione geometria grano (solo in `_generate_grain_geometry`) |

### Classi

#### `ApplicationController`
- **Scopo**: Singleton di fatto che mantiene lo stato globale e orchestra le operazioni

- **Costruttore `__init__`**:
  ```python
  self.configuration_data: Optional[ConfigurationData] = None
  self.optimization_data: Optional[OptimizationData] = None
  self.results = None  # Dict con array numpy post-ottimizzazione
  self.data_manager = DataManager()
  ```

- **Metodi principali**:

  | Metodo | Parametri | Cosa fa | Stato modificato |
  |--------|-----------|---------|------------------|
  | `set_configuration_data(inputs, dropdowns, selected_fuels, fuel_weights)` | 4 dict/list dalla GUI | Crea `ConfigurationData` e la memorizza | `self.configuration_data` |
  | `get_configuration_data()` | - | Getter | Nessuno |
  | `set_optimization_data(data)` | `data: Dict` | Chiama `OptimizationData.from_dict()` | `self.optimization_data` |
  | `get_optimization_data()` | - | Getter | Nessuno |
  | `save_configuration(filepath)` | `filepath: str` | Delega a `data_manager`, ritorna `(bool, msg)` | File system |
  | `load_configuration(filepath)` | `filepath: str` | Delega a `data_manager`, ritorna `(bool, data, msg)` | Nessuno |
  | `save_optimization(filepath)` | `filepath: str` | Come sopra per optimization | File system |
  | `load_optimization(filepath)` | `filepath: str` | Come sopra | Nessuno |
  | `save_results(filepath)` | `filepath: str` | Salva results + config + opt in unico CSV | File system |
  | `is_ready_for_optimization()` | - | Verifica che `configuration_data` e `optimization_data` siano non-None | Nessuno |
  | `prepare_optimization_inputs()` | - | **Metodo critico**: costruisce il dizionario completo per `full_range_simulation()` | Nessuno |
  | `prepare_mission_inputs(mission_data)` | `mission_data: Dict` | **Metodo critico**: costruisce input per `run_full_mission()` / `match_mission()` | Nessuno |
  | `_generate_grain_geometry(mission_data, Dport)` | `mission_data: Dict`, `Dport: float` | Genera coordinate x,y,z del grano in base al preset | Nessuno |

- **Dettaglio `prepare_optimization_inputs()`**:
  1. Verifica readiness con `is_ready_for_optimization()`
  2. Crea range numpy con `linspace(min, max, points)` per Dport/Dt, Dinj/Dt, Lc/Dt
  3. Estrae epsilon (può essere `"adapt"` o float)
  4. Gestisce custom oxidizer (prefisso `"Custom:"`)
  5. Costruisce dizionari `oxidizer` e `fuel` nel formato atteso da CEA/CoolProp
  6. Ritorna dizionario con 15+ chiavi pronte per backend

- **Dettaglio `prepare_mission_inputs()`** (~200 righe):
  1. Estrae Dport/Dt, Dinj/Dt, Lc/Dt ottimali
  2. Calcola dimensioni assolute: `Dport = Dt * ratio`, `Ainj = n_inj * π/4 * Dinj²`
  3. Determina tipo tank (self-pressurizing vs regulated)
  4. Chiama `_generate_grain_geometry()` per ottenere x, y, z
  5. Costruisce dizionario con ~35 chiavi per simulazione missione

- **Dettaglio `_generate_grain_geometry()`** (~180 righe):
  
  | Preset | Logica |
  |--------|--------|
  | `Custom (from CSV)` | Usa solo `custom_geometry_x/y`, ignora n_sides/inner_r/outer_r |
  | `Cylindrical` | Cerchio con 36 punti, raggio = Dport/2 |
  | `Regular Polygon` | N vertici a distanza outer_r, poi scalato a Dport |
  | `Star` | 2*n_sides punti alternando inner_r e outer_r |
  | `Wagon Wheel` | Cerchio con notch verso inner_r |
  | `Custom Polygon` | Usa `geom.create_regular_poligon()` |

  Tutte le geometrie vengono:
  1. Ordinate counter-clockwise (`geom.sort_input`)
  2. Centrate all'origine (`geom.translate_figure`)
  3. Scalate per matchare Dport target

### Flusso di esecuzione
1. **Startup**: `main_window` crea `ApplicationController()`
2. **Configuration**: utente compila form → `set_configuration_data()` → dati memorizzati
3. **Optimization params**: utente compila → `set_optimization_data()`
4. **Run Optimization**: `main_window` chiama `is_ready_for_optimization()` → se OK, `prepare_optimization_inputs()` → passa a `OptimizationRunner`
5. **Run Mission**: `prepare_mission_inputs(mission_data)` → passa a `MissionRunner`

### Note critiche
- **Fallback silenziosi**: Se `Oxidizer_CoolProp` è vuoto, usa `"NitrousOxide"` con solo un `print()` di warning. Nessun feedback utente.
- **Dipendenza implicita da `Geometry`**: Import lazy di `geometry_calculation` dentro `_generate_grain_geometry()`. Se il modulo manca, errore solo a runtime.
- **Validazione parziale**: `is_ready_for_optimization()` verifica solo che i dati esistano, non che siano validi (range negativi, temperature assurde, etc.).
- **Side effect print**: Molti `print()` di debug che finiscono in console, non visibili all'utente GUI.

---

## `core/optimization_runner.py`

### Scopo
Esegue la simulazione di ottimizzazione in un thread separato per evitare il freeze della GUI Tkinter. Gestisce progress callback, cancellazione, e routing di success/error verso la GUI tramite callback.

### Dipendenze chiave
| Import | Motivo |
|--------|--------|
| `threading` | Esecuzione background con `Thread` |
| `time` | Misurazione durata simulazione |
| `backend.optimization` | Import lazy del modulo che contiene `full_range_simulation()` |
| `Line_losses.linelosses` | Import lazy per settare perdite di linea (opzionale) |

### Classi

#### `OptimizationRunner`
- **Scopo**: Wrapper thread-safe per esecuzione ottimizzazione con pattern callback

- **Costruttore `__init__`**:
  | Parametro | Tipo | Descrizione |
  |-----------|------|-------------|
  | `callback_success` | `Callable` | Funzione chiamata con `result_dict` al completamento |
  | `callback_error` | `Callable` | Funzione chiamata con `error_message: str` su errore |
  | `callback_progress` | `Optional[Callable]` | Funzione chiamata con `(current, total, message)` per aggiornare progress bar |

  **Stato inizializzato**:
  ```python
  self.thread = None
  self.running = False
  self.cancel_requested = False
  ```

- **Metodi principali**:

  | Metodo | Parametri | Cosa fa | Stato modificato |
  |--------|-----------|---------|------------------|
  | `set_progress_callback(callback)` | `callback: Callable` | Setter per callback progress post-init | `self.callback_progress` |
  | `request_cancel()` | - | Setta flag `cancel_requested = True` | `self.cancel_requested` |
  | `_progress_wrapper(current, total, message)` | int, int, str | **Checkpoint cancellazione**: se `cancel_requested`, solleva `InterruptedError`. Altrimenti chiama `callback_progress` e stampa a console | Nessuno |
  | `run_simulation(inputs)` | `inputs: Dict` | **Entry point thread**: importa backend, chiama `full_range_simulation()`, impacchetta risultati, chiama callback appropriato | `self.running` |
  | `start(inputs)` | `inputs: Dict` | Crea e avvia `Thread(target=run_simulation)` con `daemon=True` | `self.thread`, `self.running` |

- **Dettaglio `run_simulation()`**:
  1. Reset `cancel_requested = False`
  2. Print debug di tutti gli input
  3. Import `backend.optimization` (può sollevare `ImportError`)
  4. Opzionale: setta `line_losses` via modulo dedicato
  5. Chiama `full_range_simulation()` passando `progress_callback=self._progress_wrapper`
  6. Impacchetta i 19 array risultato in `result_dict` con chiavi nominate
  7. `callback_success(result_dict)`
  
  **Gestione errori**:
  | Eccezione | Handling |
  |-----------|----------|
  | `InterruptedError` | `callback_error("CANCELLED: ...")` |
  | `ImportError` | Messaggio specifico su modulo mancante |
  | `ValueError` | Suggerimenti su cause comuni (CoolProp name, formula) |
  | `Exception` | Traceback completo |

- **Callback / event handler**: Nessun binding Tkinter diretto. Comunicazione via callback passati dal `main_window`.

- **Comunicazione esterna**: 
  - Riceve `inputs` dict preparato da `ApplicationController.prepare_optimization_inputs()`
  - Chiama `callback_success/error/progress` che sono metodi di `main_window` wrappati per `root.after()` thread-safety

### Flusso di esecuzione
1. `main_window.run_optimization()` crea `OptimizationRunner` con callback
2. Chiama `runner.start(inputs)` → crea thread daemon
3. Thread esegue `run_simulation()`
4. Periodicamente, backend chiama `progress_callback` → `_progress_wrapper` controlla cancellazione
5. Al termine: `callback_success(results)` → eseguito nel thread, deve usare `root.after()` per update GUI

### Note critiche
- **Thread safety**: I callback vengono chiamati dal thread worker, NON dal main thread Tkinter. Il chiamante DEVE wrappare con `root.after()` per evitare race condition sulla GUI.
- **Daemon thread**: `thread.daemon = True` significa che il thread viene killato bruscamente se il processo principale termina. Nessun cleanup garantito.
- **Cancellazione cooperativa**: Funziona solo se il backend chiama `progress_callback` regolarmente. Loop interni lunghi senza callback non sono interrompibili.
- **Memory**: I 19 array numpy vengono tenuti in memoria tutti insieme. Per grid molto grandi (es. 50³ = 125000 punti × 19 array) può causare memory pressure.

---

## `core/mission_runner.py`

### Scopo
Analogo a `OptimizationRunner` ma per simulazioni missione. Supporta due modalità: `run_full_mission` (parametri fissi) e `match_mission` (iterativo per raggiungere target burn time).

### Dipendenze chiave
| Import | Motivo |
|--------|--------|
| `threading` | Esecuzione background |
| `time` | Timing |
| `Mission.mission_simulation` | Import lazy del modulo simulazione |
| `Tank.tank_update` | Import lazy per costruzione stato tank |

### Classi

#### `MissionRunner`
- **Scopo**: Wrapper thread-safe per simulazione missione con supporto run/match mode

- **Costruttore `__init__`**: Identico a `OptimizationRunner`

- **Metodi principali**:

  | Metodo | Parametri | Cosa fa | Stato modificato |
  |--------|-----------|---------|------------------|
  | `set_progress_callback(callback)` | `Callable` | Setter post-init | `self.callback_progress` |
  | `request_cancel()` | - | Setta flag cancellazione | `self.cancel_requested` |
  | `_progress_wrapper(message, progress)` | `str`, `Optional[float]` | Checkpoint cancellazione, chiama callback | Nessuno |
  | `run_mission(inputs, match_mode)` | `Dict`, `bool` | Entry point thread: esegue simulazione | `self.running` |
  | `start(inputs, match_mode)` | `Dict`, `bool` | Avvia thread | `self.thread`, `self.running` |

- **Dettaglio `run_mission()`**:
  
  **Setup comune**:
  1. Reset cancellazione
  2. Print debug parametri principali
  3. Import `Mission.mission_simulation` e `Tank.tank_update`
  4. Costruisce `utilities` dict per tank (CDvent, Avent, opzionale CDpress/Apress)

  **Match mode** (`match_mode=True`):
  ```python
  time_data, sim_inputs, performances_list, log = mission.match_mission(
      burn_time=..., pamb=..., Tamb=..., # ~25 parametri
      ...
  )
  ```
  Il tank viene costruito internamente da `match_mission`.

  **Run mode** (`match_mode=False`):
  ```python
  # 1. Costruisce tank esplicitamente
  masses, volumes, pressures, temperatures, constant_pressure_tank = tank.build_tank(...)
  
  # 2. Esegue simulazione
  time_data, performances_list, log = mission.run_full_mission(
      ..., masses=masses, volumes=volumes, ...
  )
  ```

  **Post-processing**:
  ```python
  performances = mission.normalize_performances(performances_list)
  # Converte List[Dict] → Dict[str, List] per plotting
  callback_success(time_data, performances, log)
  ```

- **Comunicazione esterna**: 
  - Riceve `inputs` da `ApplicationController.prepare_mission_inputs()`
  - `callback_success(time_data, performances, log)` con 3 argomenti (diverso da optimization che ne ha 1)

### Flusso di esecuzione
1. `main_window._run_mission(match_mode)` prepara input via controller
2. Crea `MissionRunner` con callback
3. `runner.start(inputs, match_mode=True/False)`
4. Thread esegue, chiama `_progress_wrapper` periodicamente
5. `callback_success(time_data, performances, log)` al termine

### Note critiche
- **Signature callback diversa**: `callback_success` riceve 3 argomenti vs 1 di optimization. Il chiamante deve gestire entrambi i casi.
- **Build tank separato**: In run mode, il tank viene costruito prima della simulazione. Errori in `tank.build_tank()` vengono catturati dal try/except generico.
- **Normalize performances**: La funzione `normalize_performances()` assume che tutte le chiavi siano presenti in ogni step. Se la simulazione fallisce a metà, potrebbe ritornare liste di lunghezze diverse.

---

## `backend/optimization.py`

### Scopo
Modulo core per l'ottimizzazione parametrica steady-state. Implementa il solver Newton-like per trovare la pressione di camera di equilibrio, e il loop a 3 parametri per esplorare lo spazio di design Dport/Dt × Dinj/Dt × Lc/Dt.

### Dipendenze chiave
| Import | Motivo |
|--------|--------|
| `numpy` | Array operations, linspace, argmin |
| `time` | Timing (solo in `__main__`) |
| `Performance.performance_singlepoint` | Funzioni `pressure_fun()` e `calculate_performance()` per calcoli termodinamici |

### Funzioni

#### `starting_pressure(...)`
- **Scopo**: Trova un buon punto iniziale per l'iterazione Newton cercando dove `pressure_fun ≈ 0`

- **Parametri**: 
  | Nome | Tipo | Descrizione |
  |------|------|-------------|
  | `Ainj` | float | Area iniettore [m²] |
  | `Aport` | float | Area porta [m²] |
  | `At` | float | Area gola [m²] |
  | `Ab` | float | Area burning [m²] |
  | `eps` | float/str | Expansion ratio o `"adapt"` |
  | `ptank` | float | Pressione tank [Pa] |
  | `Ttank` | float | Temperatura tank [K] |
  | `CD` | float | Coefficiente scarico |
  | `a`, `n` | float | Coefficienti regression rate r=a·Gox^n |
  | `rho_fuel` | float | Densità fuel [kg/m³] |
  | `oxidizer` | Dict | Proprietà ossidante per CoolProp/CEA |
  | `fuel` | Dict | Proprietà fuel per CEA |
  | `pamb` | float | Pressione ambiente [Pa] |
  | `gamma0` | float | Guess iniziale per γ |

- **Algoritmo**:
  1. Crea range `pc_range` da `pamb` (o 1 Pa) a `ptank` con 399 punti, più denso vicino a `ptank`
  2. Valuta `pressure_fun()` per ogni pc
  3. Trova indice dove `|Fpc|` è minimo
  4. Se tutti i valori hanno stesso segno → ritorna 0 (nessuna soluzione)

- **Return**: `pc_best: float` (può essere 0 se no soluzione)

---

#### `get_pressure(...)`
- **Scopo**: Solver Newton modificato per trovare pc dove `pressure_fun(pc) = 0`

- **Parametri**: Stessi di `starting_pressure`

- **Algoritmo**:
  ```
  1. pc = starting_pressure(...)
  2. if pc == 0: return (0, 0, maxit+1, maxit, gamma0)
  3. while |Fpc| > 0.1 Pa AND n_iter < 100:
     a. Fpc = pressure_fun(pc)
     b. Fdpc = pressure_fun(pc + 10 Pa)
     c. dFpc = (Fdpc - Fpc) / 10
     d. pc_new = pc - k_Newton * Fpc / dFpc
     e. if pc_new fuori range [pamb, ptank]:
        - clamp pc
        - k_Newton -= 0.05  (rallenta convergenza)
     f. Aggiorna gamma0 dal calcolo performance
  4. return (pc, Fpc, n_iter, maxit, gamma0)
  ```

- **Return**: `Tuple[pc, Fpc, n_iter, maxit, gamma_final]`

- **Note**: 
  - `k_Newton` parte da 1.0 e decresce se la soluzione esce dal range → convergenza più lenta ma stabile
  - `dpc = 10 Pa` è fisso → può essere troppo grande per pressioni molto basse
  - Convergenza: `|Fpc| < 0.1 Pa` → ~1e-6 bar di accuratezza

---

#### `full_range_simulation(...)`
- **Scopo**: Loop principale che esplora tutto lo spazio parametrico 3D

- **Parametri aggiuntivi rispetto a `get_pressure`**:
  | Nome | Tipo | Descrizione |
  |------|------|-------------|
  | `Dport_Dt_range` | ndarray | Array dei valori Dport/Dt da testare |
  | `Dinj_Dt_range` | ndarray | Array dei valori Dinj/Dt da testare |
  | `Lc_Dt_range` | ndarray | Array dei valori Lc/Dt da testare |
  | `progress_callback` | Callable | `(current, total, message)` per progress bar |

- **Algoritmo**:
  ```python
  # Pre-alloca 19 array 3D di zeri
  pc_array = np.zeros((n_dport, n_dinj, n_lc))
  # ... altri 18 array ...
  
  Dt = 1  # Normalizzazione: tutte le aree sono /Dt²
  
  for i, Dport in enumerate(Dport_Dt_range):
      for j, Dinj in enumerate(Dinj_Dt_range):
          for k, Lc in enumerate(Lc_Dt_range):
              # Callback progress
              progress_callback(iteration, total, f"Dport/Dt={Dport:.2f}, ...")
              
              # Calcola aree normalizzate
              Aport = π/4 * Dport²
              Ainj = π/4 * Dinj²
              At = π/4 * 1²  # Dt=1
              Ab = π * Dport * Lc
              
              # Trova pressione equilibrio
              pc, Fpc, n_iter, maxit, gamma0 = get_pressure(...)
              
              if pc != 0:
                  # Calcola performance complete
                  (p_inj, mdot_ox, ..., flag) = calculate_performance(...)
                  
                  # Salva in array
                  pc_array[i,j,k] = pc
                  # ... altri 17 valori ...
              
              # Setta flag convergenza
              flag_array[i,j,k] = ...
  
  return (pc_array, ..., flag_array)  # 19 array
  ```

- **Return**: Tupla di 19 `ndarray` shape `(n_dport, n_dinj, n_lc)`:
  
  | Indice | Nome | Unità |
  |--------|------|-------|
  | 0 | `pc_array` | Pa |
  | 1 | `Fpc_array` | Pa |
  | 2 | `p_inj_array` | Pa |
  | 3 | `mdot_ox_array` | kg/(s·m²) normalizzato |
  | 4 | `mdot_fuel_array` | kg/(s·m²) |
  | 5 | `mdot_array` | kg/(s·m²) |
  | 6 | `Gox_array` | kg/(s·m²) |
  | 7 | `r_array` | m/s |
  | 8 | `MR_array` | - |
  | 9 | `eps_array` | - |
  | 10 | `Tc_array` | K |
  | 11 | `MW_array` | kg/kmol |
  | 12 | `gamma_array` | - |
  | 13 | `cs_array` | m/s |
  | 14 | `CF_vac_array` | - |
  | 15 | `CF_array` | - |
  | 16 | `Ivac_array` | s |
  | 17 | `Is_array` | s |
  | 18 | `flag_array` | codice |

- **Flag codes**:
  | Valore | Significato |
  |--------|-------------|
  | 0 | Convergenza OK |
  | 1 | Max iterazioni pressione |
  | 2 | Max iter pressione + CEA diverged |
  | -1 | CEA diverged |
  | 10 | Nessuna soluzione pressione |
  | 100 | Non calcolato (init) |

### Note critiche
- **Normalizzazione Dt=1**: Tutte le aree e flussi sono normalizzati per Dt². Per ottenere valori assoluti, moltiplicare per Dt² effettivo.
- **Ordine loop**: Dport esterno → Dinj → Lc interno. Il caching di `gamma0` tra iterazioni consecutive (stesso Dport/Dinj) accelera la convergenza.
- **Memory footprint**: 19 array × 4 bytes (float32 di default numpy) × n³ punti. Per n=20: ~600 KB. Per n=50: ~23 MB.
- **No parallelismo**: Loop sequenziale. Potenziale speedup 4-8x con `multiprocessing` o `numba`.
- **Exception swallowing**: In `starting_pressure`, le eccezioni vengono silenziate con `Fpcs[i] = 1e8`. Debugging difficile se CEA fallisce silenziosamente.

---

## Diagramma delle dipendenze

```
┌─────────────────────────────────────────────────────────────────────┐
│                            main_window.py                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
           ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
           │ controller.py│ │optimization_ │ │mission_      │
           │              │ │runner.py     │ │runner.py     │
           └──────────────┘ └──────────────┘ └──────────────┘
                    │               │               │
                    ▼               │               │
           ┌──────────────┐         │               │
           │data_manager  │         │               │
           └──────────────┘         │               │
                    │               │               │
                    ▼               │               │
           ┌──────────────┐         │               │
           │data_structures│        │               │
           └──────────────┘         │               │
                                    │               │
                    ┌───────────────┘               │
                    │                               │
                    ▼                               ▼
           ┌──────────────┐                ┌──────────────┐
           │optimization  │                │mission_      │
           │.py (backend) │                │simulation.py │
           └──────────────┘                └──────────────┘
                    │                               │
                    ▼                               ▼
           ┌──────────────┐                ┌──────────────┐
           │performance_  │                │tank_update   │
           │singlepoint   │                │geometry_calc │
           └──────────────┘                └──────────────┘
                    │
                    ▼
           ┌──────────────┐
           │CEA / CoolProp│
           └──────────────┘
```

---

## Riepilogo pattern architetturali

| Pattern | Implementazione |
|---------|-----------------|
| **MVC** | `controller.py` = Controller, `pages/*.py` = View, `data_structures.py` = Model |
| **Observer** | Callback functions per progress/success/error |
| **Factory** | `from_dict()` class methods per deserializzazione |
| **Repository** | `DataManager` centralizza accesso a file |
| **Thread pool (semplificato)** | Un thread alla volta per simulazione |
