# Mission Simulation Module

This document describes the Mission simulation system for the Hybrid Rocket Engine design tool.

## Overview

The Mission module simulates the complete flight of a hybrid rocket engine, integrating:
- Tank blowdown (self-pressurizing, pressurized gas, or constant pressure)
- Chamber pressure dynamics
- Fuel grain regression
- Nozzle flow and thrust calculation

## Components

### Mission Page (`gui/pages/mission_page.py`)
User interface for configuring mission parameters:

#### 1. Optimal Design Point
Enter the optimal dimensionless ratios from the Optimization results:
- **Dport/Dt optimal**: Port diameter to throat diameter ratio
- **Dinj/Dt optimal**: Injector diameter to throat diameter ratio  
- **Lc/Dt optimal**: Chamber length to throat diameter ratio

These ratios are used with the throat diameter (Dt) to calculate actual dimensions.

#### 2. Mission Timing
- **Burn Time [s]**: Target combustion duration
- **Ignition Delay [s]**: Delay before ignition (for pre-pressurization)

#### 3. Chamber & Nozzle Geometry
- **Chamber Diameter [m]**: Maximum internal diameter
- **Throat Diameter [m]**: Nozzle throat diameter (Dt)
- **Number of Injectors**: Number of oxidizer injection orifices
- **Pre-chamber Volume [m³]**: Volume before grain (for mixing)
- **Post-chamber Volume [m³]**: Volume after grain (post-combustion)

#### 4. Grain Geometry
Choose from preset grain shapes:
- **Cylindrical**: Simple circular port
- **Star (6/8 points)**: Star-shaped port for increased burning surface
- **Wagon Wheel**: Circular with radial notches
- **Custom Polygon**: Regular polygon with n sides

Parameters:
- **Number of Sides/Points**: For star/polygon geometries
- **Inner Radius [m]**: Inner radius for star points
- **Outer Radius [m]**: Outer radius for star peaks
- **Helix Pitch [m]**: For helical grains (0 = straight)
- **Circular**: Use arc interpolation (for round features)

#### 5. Tank Configuration
Choose tank type:
- **Self-pressurizing**: Uses vapor pressure (e.g., N2O)
- **Pressurized gas**: Blow-down from initial pressure
- **Constant pressure**: With pressurant gas regulation

Parameters:
- **Oxidizer Mass [kg]**: Initial oxidizer mass
- **Vapor Quality (0-1)**: Initial liquid/gas ratio
- **Pressurant Pressure [bar]**: For constant pressure tanks
- **Pressurant**: Gas type (Helium, Nitrogen, Argon)

#### 6. Performance Efficiencies
- **c* Efficiency (η_c*)**: Characteristic velocity efficiency
- **CF Efficiency (η_CF)**: Thrust coefficient efficiency

### Mission Simulation Functions

#### `run_full_mission()`
Simulates the complete mission from ignition to tank depletion or grain burnout.

**Flow:**
1. Get starting conditions (ambient pressure/temperature)
2. Build tank with specified configuration
3. Run simulation loop:
   - Calculate performance (CEA)
   - Update gas mixture properties
   - Burn grain geometry
   - Update surfaces and volume
   - Update chamber pressure
   - Calculate nozzle flow and thrust
   - Update tank state
4. Continue until:
   - Oxidizer depleted (mL < 0)
   - Fuel consumed (m_fuel < 0)
   - Grain contacts chamber wall
5. Empty remaining tank

**Outputs:**
- `time`: List of time points [s]
- `performances`: Dictionary of performance lists
- `log`: Termination reason

#### `match_mission()`
Iteratively finds tank mass and chamber diameter to match target burn time.

**Algorithm:**
1. Start with initial guesses for mtank and D_chamber
2. Run simulation iteration
3. Check convergence:
   - Final oxidizer mass < 5% of starting mass
   - Final fuel mass < 5% of starting fuel
   - Chamber diameter < 1.05 * max(grain diameter)
4. Adjust parameters using time proportionality:
   ```
   X_new = X_old * (t_target / t_actual)
   ```
5. Repeat until converged or max iterations

**Outputs:**
- `time`: List of time points [s]
- `inputs`: Final matched configuration
- `performances`: Dictionary of performance lists
- `log`: Convergence status

### Tank Models

#### Self-Pressurizing (`Tank/tank_simulation.py`)
For fluids with high vapor pressure (N2O, CO2):
- Isentropic blow-down model
- Uses CoolProp for fluid properties
- Tracks liquid/vapor phases
- Entropy conservation: `s_{i+1} = (s_i*m_i - s_L*dm_L - s_V*dm_V) / m_{i+1}`

#### Pressurized Gas
Simple blow-down from initial pressure:
- Ideal gas behavior
- Q = 1 (full vapor)
- Pressure drops as gas expands

#### Constant Pressure (`Tank/tank_pressurant_simulation.py`)
Regulated pressure with pressurant:
- Separate pressurant vessel
- Mass transfer maintains tank pressure
- Adiabatic pressurant expansion

### Chamber Update (`Mission/chamber_update.py`)

#### `update_Temperature_and_gasproperties()`
Updates gas properties using mixture theory:
```
m_{i+1} = m_i + (mdot_in - mdot_out) * dt
cp_{i+1} = (m_i * cp_i + mdot_in * cp_CEA * dt) / m_{i+1}
T_{i+1} = (m_i * T_i * cp_i + mdot_in * T_CEA * cp_CEA * dt) / (m_{i+1} * cp_{i+1})
MW_{i+1} = m_{i+1} / (m_i/MW_i + mdot_in*dt/MW_CEA)
```

Time step controlled to keep property changes below tolerance (default 0.1%):
```
dt = min(dt_mass, dt_cp, dt_T, dt_MW)
```

#### `update_chamberpressure()`
Ideal gas equation:
```
pc = (m_c * R * Tc) / V_chamber
```

### Geometry Update (`Geometry/geometry_update.py`)

#### `burn_grain()`
Updates grain geometry due to regression:
1. Remove collinear points (keep only vertices)
2. Find normal directions for each side
3. Move midpoints outward by `r * dt`
4. Calculate intersections of moved normals
5. Handle cusps (acute angles) and smooth transitions
6. Remove self-intersections and too-close points

Special handling:
- **Cusps**: Check for degeneration when sides become too small
- **Circular**: Maintain arc radii during regression
- **Fallback**: Use midpoint if intersection fails

### Performance Calculation

Each time step:
1. **Injection**: Calculate oxidizer mass flow
   ```
   mdot_ox = CD * A_inj * sqrt(2 * rho * (p_tank - p_chamber))
   ```

2. **Regression**: Calculate fuel mass flow
   ```
   r = a * G_ox^n
   mdot_fuel = rho_fuel * A_burn * r
   ```

3. **CEA Analysis**: Get combustion products
   - Chamber temperature, molecular weight, gamma
   - Characteristic velocity c*
   - Thrust coefficient CF

4. **Nozzle Flow**: Calculate exit conditions
   - Find exit Mach number (choked or adapted)
   - Exit pressure, temperature, velocity

5. **Thrust**:
   ```
   F = eta_cstar * eta_CF * mdot * c* * CF
   ```

## Usage Example

### 1. Configure System (Configuration Page)
```python
oxidizer = {
    "OxidizerCP": "NitrousOxide",
    "OxidizerCEA": "N2O",
    "Weight fraction": "100",
    "Exploded Formula": "",
    "Temperature [K]": "",
    "Specific Enthalpy [kj/mol]": ""
}

fuel = {
    "Fuels": ["paraffin"],
    "Weight fraction": ["100"],
    "Exploded Formula": ["C 73 H 124"],
    "Temperature [K]": [533],
    "Specific Enthalpy [kj/mol]": [-1860.6]
}
```

### 2. Optimize (Optimization Page)
Find optimal ratios: Dport/Dt, Dinj/Dt, Lc/Dt

### 3. Configure Mission (Mission Page)
```python
mission_params = {
    'Dport_Dt_optimal': 2.5,
    'Dinj_Dt_optimal': 0.2,
    'Lc_Dt_optimal': 3.0,
    'burn_time': 10.0,
    'Dt': 0.03,  # 30mm throat
    'mtank': 5.0,  # 5kg N2O
    'grain_preset': 'Star (6 points)'
}
```

### 4. Run Simulation
Click **"Run Mission"** to simulate with fixed parameters, or
Click **"Match Mission"** to find configuration matching burn time

### 5. View Results (Mission Output Page)
- Summary statistics
- Time-series data table
- Export to CSV

## Performance Considerations

### Simulation Speed
- Typical mission: 100-1000 time steps
- Simulation time: 1-30 seconds (depends on burn time)
- Progress updates shown in real-time

### Accuracy
- Time step adaptive (tolerance-controlled)
- CEA chemical equilibrium (assumes infinite residence time)
- Geometry update robust to high regression rates
- Tank model validated against experiments

### Validation
Compare with:
- Static fire test data
- Known flight performances
- Analytical solutions for simple cases

## Troubleshooting

### Simulation fails immediately
- Check fuel/oxidizer configuration
- Verify all parameters are positive
- Check grain doesn't contact chamber wall initially

### All zeros in results
- Verify oxidizer formula is empty for standard oxidizers
- Check tank pressure > chamber pressure
- Ensure grain geometry is valid

### Simulation doesn't reach target burn time
- Increase oxidizer mass (mtank)
- Decrease throat diameter (Dt)
- Check grain doesn't burn through too quickly
- Use Match Mission to find correct configuration

### Oscillations or instability
- Reduce time step tolerance (smaller dt)
- Check for numerical issues in geometry update
- Verify chamber volume > 0 at all times

## Future Enhancements

Potential additions:
- [ ] Real-time plotting during simulation
- [ ] Trajectory calculation (vertical flight)
- [ ] 2D axisymmetric CFD coupling
- [ ] Thermal analysis (grain/chamber heating)
- [ ] Structural loads calculation
- [ ] Cost estimation
- [ ] Multi-stage support

## References

1. Sutton & Biblarz, "Rocket Propulsion Elements"
2. Gordon & McBride, "Computer Program for Calculation of Complex Chemical Equilibrium Compositions"
3. Whitmore & Chandler, "Engineering Model for Self-Pressurizing Saturated-N2O-Propellant Feed Systems"
4. Zilliac & Karabeyoglu, "Hybrid Rocket Fuel Regression Rate Data and Analysis"
