"""
Application Controller - Manages application state and coordinates components

Responsible for:
- Managing configuration and optimization data
- Coordinating between GUI and backend
- Validating readiness for operations
- Preparing data for backend functions
"""

from typing import Dict, Any, Optional, Tuple, List
import numpy as np

from core.data_structures import ConfigurationData, OptimizationData
from core.data_manager import DataManager


class ApplicationController:
    """Manages application state and coordinates between components"""
    
    def __init__(self):
        self.configuration_data: Optional[ConfigurationData] = None
        self.optimization_data: Optional[OptimizationData] = None
        self.results = None
        self.data_manager = DataManager()
    
    def set_configuration_data(self, inputs: Dict, dropdowns: Dict, 
                              selected_fuels: List, fuel_weights: Dict):
        """
        Store configuration data
        
        Args:
            inputs: Dictionary of input field values
            dropdowns: Dictionary of dropdown values
            selected_fuels: List of selected fuel names
            fuel_weights: Dictionary of fuel weight percentages
        """
        self.configuration_data = ConfigurationData(
            inputs=inputs.copy(),
            dropdowns=dropdowns.copy(),
            selected_fuels=selected_fuels.copy(),
            fuel_weight_entries=fuel_weights.copy()
        )
    
    def get_configuration_data(self) -> Optional[ConfigurationData]:
        """Retrieve configuration data"""
        return self.configuration_data
    
    def set_optimization_data(self, data: Dict):
        """
        Store optimization data
        
        Args:
            data: Dictionary with optimization parameters
        """
        self.optimization_data = OptimizationData.from_dict(data)
    
    def get_optimization_data(self) -> Optional[OptimizationData]:
        """Retrieve optimization data"""
        return self.optimization_data
    
    def save_configuration(self, filepath: str) -> Tuple[bool, str]:
        """
        Save configuration to CSV
        
        Args:
            filepath: Path to save file
            
        Returns:
            (success: bool, message: str)
        """
        if self.configuration_data is None:
            return False, "No configuration data to save"
        return self.data_manager.save_configuration_csv(self.configuration_data, filepath)
    
    def load_configuration(self, filepath: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Load configuration from CSV
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            (success: bool, data: dict or None, message: str)
        """
        return self.data_manager.load_configuration_csv(filepath)
    
    def save_optimization(self, filepath: str) -> Tuple[bool, str]:
        """
        Save optimization parameters to CSV
        
        Args:
            filepath: Path to save file
            
        Returns:
            (success: bool, message: str)
        """
        if self.optimization_data is None:
            return False, "No optimization data to save"
        return self.data_manager.save_optimization_csv(self.optimization_data, filepath)
    
    def load_optimization(self, filepath: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Load optimization parameters from CSV
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            (success: bool, data: dict or None, message: str)
        """
        return self.data_manager.load_optimization_csv(filepath)
    
    def save_results(self, filepath: str) -> Tuple[bool, str]:
        """
        Save optimization results to CSV
        
        Args:
            filepath: Path to save file
            
        Returns:
            (success: bool, message: str)
        """
        if self.results is None:
            return False, "No results to save"
        if self.configuration_data is None or self.optimization_data is None:
            return False, "Missing configuration or optimization data"
        
        return self.data_manager.save_results_csv(
            self.results, 
            self.configuration_data, 
            self.optimization_data, 
            filepath
        )
    
    def is_ready_for_optimization(self) -> Tuple[bool, str]:
        """
        Check if both configuration and optimization data are ready
        
        Returns:
            (ready: bool, message: str)
        """
        if self.configuration_data is None:
            return False, "Configuration data not set. Please fill and save the Configuration page first."
        if self.optimization_data is None:
            return False, "Optimization parameters not set. Please fill and save the Optimization page first."
        return True, "Ready for optimization"
    
    def prepare_optimization_inputs(self) -> Optional[Dict]:
        """
        Prepare inputs for full_range_simulation function
        
        Returns:
            Dictionary of inputs for backend function, or None if not ready
        """
        if not self.is_ready_for_optimization()[0]:
            return None
        
        config = self.configuration_data
        opt = self.optimization_data
        
        # Create ranges using linspace
        dport_range = np.linspace(opt.dport_dt_min, opt.dport_dt_max, opt.parameter_points)
        dinj_range = np.linspace(opt.dinj_dt_min, opt.dinj_dt_max, opt.parameter_points)
        lc_range = np.linspace(opt.lc_dt_min, opt.lc_dt_max, opt.parameter_points)
        
        # Extract epsilon (can be "adapt" or a number)
        eps = config.inputs.get('Nozzle_epsilon', 'adapt')
        if isinstance(eps, str) and eps.lower() != 'adapt':
            try:
                eps = float(eps)
            except ValueError:
                eps = 'adapt'
        
        # Get line losses (default 0)
        line_losses = float(config.inputs.get('LineLosses_DeltaP', 0) or 0)
        
        # Get oxidizer CoolProp name - with fallback
        oxidizer_coolprop = config.inputs.get('Oxidizer_CoolProp', '')
        oxidizer_cea = config.dropdowns.get('Oxidizer_CEA', '')
        
        # Check if this is a custom oxidizer
        is_custom_oxidizer = oxidizer_cea.startswith("Custom:")
        
        # Handle "Custom: name" format
        if is_custom_oxidizer:
            oxidizer_cea = oxidizer_cea.replace("Custom:", "").strip()
        
        # FALLBACK: If oxidizer is empty, use N2O as default
        if not oxidizer_coolprop:
            print("WARNING: Oxidizer CoolProp name is empty! Using default 'NitrousOxide'")
            oxidizer_coolprop = 'NitrousOxide'
        if not oxidizer_cea:
            print("WARNING: Oxidizer CEA name is empty! Using default 'N2O'")
            oxidizer_cea = 'N2O'
        
        # For STANDARD CEA oxidizers (not custom), we MUST NOT pass formula/temp/enthalpy
        # These are only for custom oxidizers defined by the user
        if is_custom_oxidizer:
            # Custom oxidizer - use user-provided values
            ox_temp = config.inputs.get('Oxidizer_Temperature', '')
            ox_enthalpy = config.inputs.get('Oxidizer_Enthalpy', '')
            ox_formula = config.inputs.get('Oxidizer_ExplodedFormula', '')
        else:
            # Standard CEA oxidizer - leave these EMPTY so CEA uses its database
            ox_temp = ''
            ox_enthalpy = ''
            ox_formula = ''
        
        # Prepare oxidizer dict
        oxidizer = {
            "OxidizerCP": oxidizer_coolprop,
            "OxidizerCEA": oxidizer_cea,
            "Weight fraction": "100",
            "Exploded Formula": ox_formula,
            "Temperature [K]": ox_temp,
            "Specific Enthalpy [kj/mol]": ox_enthalpy
        }
        
        # Prepare fuel dict
        # Check if single fuel or multiple fuels
        fuel_name_clean = 'paraffin'  # Default
        fuel_formula = ''
        fuel_temp = 298.0
        fuel_enthalpy = 0.0
        
        if config.selected_fuels and len(config.selected_fuels) >= 1:
            fuel_name = config.selected_fuels[0]
            # Handle "Custom: name" format
            if fuel_name.startswith("Custom:"):
                fuel_name_clean = fuel_name.replace("Custom:", "").strip()
            else:
                fuel_name_clean = fuel_name
            
            # Get from single fuel fields
            fuel_formula = config.inputs.get('Fuel_ExplodedFormula', '')
            fuel_temp_str = config.inputs.get('Fuel_Temperature', '')
            fuel_enthalpy_str = config.inputs.get('Fuel_Enthalpy', '')
            
            # Convert to proper types
            try:
                fuel_temp = float(fuel_temp_str) if fuel_temp_str else 298.0
            except ValueError:
                fuel_temp = 298.0
            
            try:
                fuel_enthalpy = float(fuel_enthalpy_str) if fuel_enthalpy_str else 0.0
            except ValueError:
                fuel_enthalpy = 0.0
        
        # FALLBACK: If fuel data is empty, use paraffin defaults
        if not fuel_formula:
            print("WARNING: Fuel formula is empty! Using default paraffin 'C 73 H 124'")
            fuel_formula = 'C 73 H 124'
            fuel_temp = 533.0
            fuel_enthalpy = -1860.6
        
        fuel = {
            "Fuels": [fuel_name_clean],
            "Weight fraction": ["100"],
            "Exploded Formula": [fuel_formula],
            "Temperature [K]": [fuel_temp],
            "Specific Enthalpy [kj/mol]": [fuel_enthalpy]
        }
        
        # Get other parameters with defaults
        try:
            cd_value = float(config.inputs.get('Geometry_CD', 0.8) or 0.8)
        except:
            cd_value = 0.8
        
        try:
            a_value = float(config.inputs.get('Fuel_a', 0.17e-3) or 0.17e-3)
        except:
            a_value = 0.17e-3
        
        try:
            n_value = float(config.inputs.get('Fuel_n', 0.5) or 0.5)
        except:
            n_value = 0.5
        
        try:
            rho_value = float(config.inputs.get('Fuel_rho', 850) or 850)
        except:
            rho_value = 850
        
        # Compile all inputs
        inputs = {
            'Dport_Dt_range': dport_range,
            'Dinj_Dt_range': dinj_range,
            'Lc_Dt_range': lc_range,
            'eps': eps,
            'ptank': opt.ptank,
            'Ttank': opt.ttank,
            'CD': cd_value,
            'a': a_value,
            'n': n_value,
            'rho_fuel': rho_value,
            'oxidizer': oxidizer,
            'fuel': fuel,
            'pamb': opt.pamb,
            'gamma0': 1.3,
            'line_losses': line_losses
        }
        
        return inputs
    
    # ==================================================================
    # MISSION METHODS
    # ==================================================================
    
    def set_mission_data(self, mission_data: Dict):
        """Store mission page data"""
        self.mission_data = mission_data
    
    def set_mission_results(self, time_data, performances, log_data):
        """Store mission simulation results"""
        self.mission_results = {
            'time': time_data,
            'performances': performances,
            'log': log_data
        }
    
    def prepare_mission_inputs(self, mission_data: Dict) -> Dict:
        """
        Prepare inputs for mission simulation
        
        Args:
            mission_data: Data from mission page
            
        Returns:
            Dictionary with all inputs for mission simulation
        """
        config = self.configuration_data
        if not config:
            raise ValueError("Configuration data not set")
        
        # Get oxidizer and fuel from configuration (same as optimization)
        oxidizer_coolprop = config.inputs.get('Oxidizer_CoolProp', '')
        oxidizer_cea = config.dropdowns.get('Oxidizer_CEA', '')
        
        is_custom_oxidizer = oxidizer_cea.startswith("Custom:")
        if is_custom_oxidizer:
            oxidizer_cea = oxidizer_cea.replace("Custom:", "").strip()
        
        if not oxidizer_coolprop:
            oxidizer_coolprop = 'NitrousOxide'
        if not oxidizer_cea:
            oxidizer_cea = 'N2O'
        
        if is_custom_oxidizer:
            ox_temp = config.inputs.get('Oxidizer_Temperature', '')
            ox_enthalpy = config.inputs.get('Oxidizer_Enthalpy', '')
            ox_formula = config.inputs.get('Oxidizer_ExplodedFormula', '')
        else:
            ox_temp = ''
            ox_enthalpy = ''
            ox_formula = ''
        
        oxidizer = {
            "OxidizerCP": oxidizer_coolprop,
            "OxidizerCEA": oxidizer_cea,
            "Weight fraction": "100",
            "Exploded Formula": ox_formula,
            "Temperature [K]": ox_temp,
            "Specific Enthalpy [kj/mol]": ox_enthalpy
        }
        
        # Fuel data
        fuel_names = config.selected_fuels if config.selected_fuels else ['paraffin']
        fuel_formulas = []
        fuel_temps = []
        fuel_enthalpies = []
        fuel_weights = []
        
        for fuel_name in fuel_names:
            formula = config.inputs.get(f'Fuel_{fuel_name}_formula', 'C 73 H 124')
            temp = config.inputs.get(f'Fuel_{fuel_name}_temp', 533.0)
            enthalpy = config.inputs.get(f'Fuel_{fuel_name}_enthalpy', -1860.6)
            weight = config.fuel_weight_entries.get(fuel_name, '100')
            
            fuel_formulas.append(formula if formula else 'C 73 H 124')
            try:
                fuel_temps.append(float(temp) if temp else 533.0)
            except:
                fuel_temps.append(533.0)
            try:
                fuel_enthalpies.append(float(enthalpy) if enthalpy else -1860.6)
            except:
                fuel_enthalpies.append(-1860.6)
            fuel_weights.append(weight if weight else '100')
        
        fuel = {
            "Fuels": fuel_names,
            "Weight fraction": fuel_weights,
            "Exploded Formula": fuel_formulas,
            "Temperature [K]": fuel_temps,
            "Specific Enthalpy [kj/mol]": fuel_enthalpies
        }
        
        # Get other configuration values
        try:
            cd_value = float(config.inputs.get('Injector_CD', 0.8) or 0.8)
        except:
            cd_value = 0.8
        
        try:
            a_value = float(config.inputs.get('Fuel_a', 0.17e-3) or 0.17e-3)
        except:
            a_value = 0.17e-3
        
        try:
            n_value = float(config.inputs.get('Fuel_n', 0.5) or 0.5)
        except:
            n_value = 0.5
        
        try:
            rho_fuel = float(config.inputs.get('Fuel_rho', 850) or 850)
        except:
            rho_fuel = 850
        
        # Get expansion ratio
        eps_str = config.inputs.get('Nozzle_ExpansionRatio', 'adapt')
        if eps_str and eps_str.lower() != 'adapt':
            try:
                eps = float(eps_str)
            except:
                eps = 'adapt'
        else:
            eps = 'adapt'
        
        # Get tank and ambient conditions from optimization data or defaults
        opt = self.optimization_data
        if opt:
            ptank = opt.ptank
            Ttank = opt.ttank
            pamb = opt.pamb
        else:
            ptank = 27e5
            Ttank = 288.0
            pamb = 101325.0
        
        # Calculate derived dimensions from optimal ratios and Dt
        Dt = mission_data['Dt']
        At = 0.25 * np.pi * Dt**2
        
        Dport_Dt = mission_data['Dport_Dt_optimal']
        Dinj_Dt = mission_data['Dinj_Dt_optimal']
        Lc_Dt = mission_data['Lc_Dt_optimal']
        
        Dport = Dport_Dt * Dt
        Dinj = Dinj_Dt * Dt
        Lc = Lc_Dt * Dt
        
        # Injection area (per injector * number of injectors)
        n_inj = mission_data['n_injectors']
        Ainj = n_inj * 0.25 * np.pi * Dinj**2
        
        # Generate grain geometry
        x, y, z = self._generate_grain_geometry(mission_data, Dport)
        
        # Determine tank type flags
        tank_type = mission_data['tank_type']
        Q_vapor = mission_data['Q_vapor']
        
        if tank_type == 'Pressurized gas':
            Q_vapor = 1.0  # Full gas
            constant_pressure_tank = False
            pressurant = None
        elif tank_type == 'Constant pressure':
            constant_pressure_tank = True
            pressurant = mission_data['pressurant']
        else:  # Self-pressurizing
            constant_pressure_tank = False
            pressurant = None
        
        inputs = {
            'burn_time': mission_data['burn_time'],
            'delay_time': mission_data['delay_time'],
            'pamb': pamb,
            'Tamb': Ttank,
            'a': a_value,
            'n': n_value,
            'rho_fuel': rho_fuel,
            'eps': eps,
            'Ainj': Ainj,
            'At': At,
            'Lc': Lc,
            'D_chamber': mission_data['D_chamber'],
            'x': x,
            'y': y,
            'z': z,
            'Vol_prechamber': mission_data['Vol_prechamber'],
            'Vol_postchamber': mission_data['Vol_postchamber'],
            'CD': cd_value,
            'mtank': mission_data['mtank'],
            'Q': Q_vapor,
            'oxidizer': oxidizer,
            'fuel': fuel,
            'pressurant': pressurant,
            'rend_cstar': mission_data['rend_cstar'],
            'rend_CF': mission_data['rend_CF'],
            'pitch': mission_data['grain_pitch'],
            'circular': mission_data['circular'],
            'constant_pressure_tank': constant_pressure_tank,
            'ptank': ptank,
            'Ttank': Ttank,
            'ppress': mission_data.get('ppress', 200e5),
        }
        
        return inputs
    
    def _generate_grain_geometry(self, mission_data: Dict, Dport: float):
        """
        Generate grain geometry based on preset and parameters
        
        The geometry is first created in normalized form using the user's inner/outer radii,
        then scaled to match the required Dport from optimization.
        
        IMPORTANT: When preset is 'Custom (from CSV)', ONLY the custom_geometry_x/y arrays
        are used. The n_sides, inner_radius, outer_radius parameters are IGNORED.
        """
        import numpy as np
        from Geometry import geometry_calculation as geom
        
        preset = mission_data['grain_preset']
        
        # ============================================================
        # CUSTOM GEOMETRY FROM CSV - Uses ONLY custom data, ignores all preset parameters
        # ============================================================
        if preset == 'Custom (from CSV)':
            custom_x = mission_data.get('custom_geometry_x')
            custom_y = mission_data.get('custom_geometry_y')
            
            # Validate custom geometry data
            if custom_x is None or custom_y is None:
                raise ValueError("Custom geometry selected but no CSV data loaded. Please load a CSV file first.")
            
            if not hasattr(custom_x, '__len__') or not hasattr(custom_y, '__len__'):
                raise ValueError("Custom geometry data is invalid. Expected arrays of x and y coordinates.")
            
            if len(custom_x) < 3 or len(custom_y) < 3:
                raise ValueError(f"Custom geometry must have at least 3 points. Got {len(custom_x)} points.")
            
            if len(custom_x) != len(custom_y):
                raise ValueError(f"Custom geometry x and y arrays must have same length. Got x={len(custom_x)}, y={len(custom_y)}.")
            
            # Use ONLY the custom geometry data - no preset parameters used here
            x_norm = np.array(custom_x, dtype=float)
            y_norm = np.array(custom_y, dtype=float)
            
            # Check for invalid values
            if np.any(np.isnan(x_norm)) or np.any(np.isnan(y_norm)):
                raise ValueError("Custom geometry contains NaN values.")
            if np.any(np.isinf(x_norm)) or np.any(np.isinf(y_norm)):
                raise ValueError("Custom geometry contains infinite values.")
            
            # Sort points counter-clockwise
            x_norm, y_norm = geom.sort_input(x_norm, y_norm, z=1)
            
            # Translate to center at origin
            x_norm, y_norm = geom.translate_figure(x_norm, y_norm)
            
            # Calculate current equivalent diameter
            Ap_norm, _ = geom.calculate_surfaces_from_points(x_norm, y_norm, lc=1.0, step=0.0)
            Deq_norm = np.sqrt(4 * Ap_norm / np.pi)
            
            if Deq_norm < 1e-12:
                raise ValueError("Custom geometry has zero or negative area. Check your CSV data.")
            
            # Scale to match desired Dport
            scale_factor = Dport / Deq_norm
            x = x_norm * scale_factor
            y = y_norm * scale_factor
            z = 1  # Counter-clockwise orientation
            
            print(f"Custom CSV geometry loaded (preset parameters IGNORED):")
            print(f"  Points: {len(x)}")
            print(f"  Deq_original: {Deq_norm*1000:.2f} mm")
            print(f"  Dport_target: {Dport*1000:.2f} mm")
            print(f"  Scale_factor: {scale_factor:.4f}")
            
            return x, y, z
        
        # ============================================================
        # PRESET GEOMETRIES - Uses n_sides, inner_radius, outer_radius
        # ============================================================
        n_sides = mission_data['grain_n_sides']
        inner_r = mission_data['grain_inner_radius']
        outer_r = mission_data['grain_outer_radius']
        
        # Simple cylindrical grain - discretize as circle with many points
        if preset == 'Cylindrical' or n_sides <= 1:
            # Create circle with 36 points (10° intervals)
            n_points = 36
            theta = np.linspace(0, 2*np.pi, n_points, endpoint=False)
            radius = Dport / 2
            x = radius * np.cos(theta)
            y = radius * np.sin(theta)
            z = 1  # Counter-clockwise
            print(f"Cylindrical grain: {n_points} points, radius={radius*1000:.2f} mm")
            return x, y, z
        
        # Create geometry in normalized form first
        theta = np.linspace(0, 2*np.pi, n_sides, endpoint=False)
        
        if 'Star' in preset:
            # Star geometry: alternating inner/outer radii
            x_norm = []
            y_norm = []
            # For star, we need 2*n_sides points (alternating)
            theta_double = np.linspace(0, 2*np.pi, 2*n_sides, endpoint=False)
            for i, t in enumerate(theta_double):
                if i % 2 == 0:
                    r = outer_r
                else:
                    r = inner_r
                x_norm.append(r * np.cos(t))
                y_norm.append(r * np.sin(t))
            x_norm = np.array(x_norm)
            y_norm = np.array(y_norm)
            
        elif preset == 'Wagon Wheel':
            # Wagon wheel: circular with notches
            x_norm = []
            y_norm = []
            for i, t in enumerate(theta):
                # Main circle point
                x_norm.append(outer_r * np.cos(t))
                y_norm.append(outer_r * np.sin(t))
                # Add notch point
                t_notch = t + np.pi/n_sides
                x_norm.append(inner_r * np.cos(t_notch))
                y_norm.append(inner_r * np.sin(t_notch))
            x_norm = np.array(x_norm)
            y_norm = np.array(y_norm)
            
        else:  # Custom Polygon
            # Regular polygon using Geometry module
            x_norm, y_norm = geom.create_regular_poligon(n_sides, outer_r)
        
        # Sort points counter-clockwise
        x_norm, y_norm = geom.sort_input(x_norm, y_norm, z=1)
        
        # Translate to center at origin
        x_norm, y_norm = geom.translate_figure(x_norm, y_norm)
        
        # Calculate current equivalent diameter
        Ap_norm, _ = geom.calculate_surfaces_from_points(x_norm, y_norm, lc=1.0, step=0.0)
        Deq_norm = np.sqrt(4 * Ap_norm / np.pi)
        
        # Scale to match desired Dport
        scale_factor = Dport / Deq_norm if Deq_norm > 1e-12 else 1.0
        x = x_norm * scale_factor
        y = y_norm * scale_factor
        z = 1  # Counter-clockwise orientation
        
        print(f"Grain geometry generated:")
        print(f"  Preset: {preset}")
        print(f"  N_sides: {n_sides}")
        print(f"  Points: {len(x)}")
        print(f"  Deq_normalized: {Deq_norm:.6f} m")
        print(f"  Dport_target: {Dport:.6f} m")
        print(f"  Scale_factor: {scale_factor:.4f}")
        
        return x, y, z
