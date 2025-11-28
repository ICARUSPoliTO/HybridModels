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
        
        # Prepare oxidizer dict
        oxidizer = {
            "OxidizerCP": config.dropdowns.get('Fuel & Oxidiser_OxidizerCoolProp', ''),
            "OxidizerCEA": config.dropdowns.get('Fuel & Oxidiser_Oxidizer', ''),
            "Weight fraction": "100",
            "Exploded Formula": config.inputs.get('Fuel & Oxidiser_OxidizerExpandedFormula', ''),
            "Temperature [K]": config.inputs.get('Fuel & Oxidiser_OxidizerTemperature', ''),
            "Specific Enthalpy [kj/mol]": config.inputs.get('Fuel & Oxidiser_OxidizerEnthalpy', '')
        }
        
        # Prepare fuel dict
        fuel = {
            "Fuels": config.selected_fuels,
            "Weight fraction": [str(config.fuel_weight_entries.get(f, 0)) for f in config.selected_fuels],
            "Exploded Formula": [config.inputs.get(f'Fuel & Oxidiser_{f}_ExpandedFormula', '') for f in config.selected_fuels],
            "Temperature [K]": [float(config.inputs.get(f'Fuel & Oxidiser_{f}_Temperature', 298)) for f in config.selected_fuels],
            "Specific Enthalpy [kj/mol]": [float(config.inputs.get(f'Fuel & Oxidiser_{f}_Enthalpy', 0)) for f in config.selected_fuels]
        }
        
        # Compile all inputs
        inputs = {
            'Dport_Dt_range': dport_range,
            'Dinj_Dt_range': dinj_range,
            'Lc_Dt_range': lc_range,
            'eps': eps,
            'ptank': opt.ptank,
            'Ttank': opt.ttank,
            'CD': float(config.inputs.get('Geometry_CD', 0.8)),
            'a': float(config.inputs.get('Fuel_a', 0.17e-3)),
            'n': float(config.inputs.get('Fuel_n', 0.5)),
            'rho_fuel': float(config.inputs.get('Fuel_rho', 850)),
            'oxidizer': oxidizer,
            'fuel': fuel,
            'pamb': opt.pamb,
            'gamma0': 1.3
        }
        
        return inputs
