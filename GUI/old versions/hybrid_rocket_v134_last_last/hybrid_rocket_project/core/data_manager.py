"""
Data Manager - Handles all CSV file operations

Responsible for:
- Saving/loading configuration data
- Saving/loading optimization data
- Saving results data
- Data serialization/deserialization
"""

import csv
import json
from typing import Dict, Any, Optional, Tuple
from core.data_structures import ConfigurationData, OptimizationData


class DataManager:
    """Handles all CSV save/load operations"""
    
    @staticmethod
    def save_configuration_csv(data: ConfigurationData, filepath: str) -> Tuple[bool, str]:
        """
        Save configuration data to CSV
        
        Args:
            data: ConfigurationData object
            filepath: Path to save file
            
        Returns:
            (success: bool, message: str)
        """
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Parameter', 'Value'])
                
                # Save inputs
                for key, value in data.inputs.items():
                    writer.writerow([key, value])
                
                # Save dropdowns
                for key, value in data.dropdowns.items():
                    writer.writerow([key, value])
                
                # Save fuel data
                writer.writerow(['selected_fuels', json.dumps(data.selected_fuels)])
                writer.writerow(['fuel_weight_entries', json.dumps(data.fuel_weight_entries)])
                
            return True, "Configuration saved successfully"
        except Exception as e:
            return False, f"Error saving configuration: {str(e)}"
    
    @staticmethod
    def load_configuration_csv(filepath: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Load configuration data from CSV
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            (success: bool, data: dict or None, message: str)
        """
        try:
            inputs = {}
            dropdowns = {}
            selected_fuels = []
            fuel_weight_entries = {}
            
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                
                for row in reader:
                    if len(row) < 2:
                        continue
                    key, value = row[0], row[1]
                    
                    if key == 'selected_fuels':
                        selected_fuels = json.loads(value)
                    elif key == 'fuel_weight_entries':
                        fuel_weight_entries = json.loads(value)
                    elif key.startswith('Fuel') or key.startswith('Oxidiser') or key.startswith('Nozzle'):
                        dropdowns[key] = value
                    else:
                        inputs[key] = value
            
            data = {
                'inputs': inputs,
                'dropdowns': dropdowns,
                'selected_fuels': selected_fuels,
                'fuel_weight_entries': fuel_weight_entries
            }
            return True, data, "Configuration loaded successfully"
        except Exception as e:
            return False, None, f"Error loading configuration: {str(e)}"
    
    @staticmethod
    def save_optimization_csv(data: OptimizationData, filepath: str) -> Tuple[bool, str]:
        """
        Save optimization data to CSV
        
        Args:
            data: OptimizationData object
            filepath: Path to save file
            
        Returns:
            (success: bool, message: str)
        """
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Parameter', 'Value'])
                
                for key, value in data.to_dict().items():
                    writer.writerow([key, value])
                
            return True, "Optimization parameters saved successfully"
        except Exception as e:
            return False, f"Error saving optimization parameters: {str(e)}"
    
    @staticmethod
    def load_optimization_csv(filepath: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Load optimization data from CSV
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            (success: bool, data: dict or None, message: str)
        """
        try:
            data = {}
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                
                for row in reader:
                    if len(row) < 2:
                        continue
                    key, value = row[0], row[1]
                    
                    # Convert to appropriate type
                    if key == 'parameter_points':
                        data[key] = int(value)
                    else:
                        data[key] = float(value)
            
            return True, data, "Optimization parameters loaded successfully"
        except Exception as e:
            return False, None, f"Error loading optimization parameters: {str(e)}"
    
    @staticmethod
    def save_results_csv(results: Dict, config_data: ConfigurationData, 
                        opt_data: OptimizationData, filepath: str) -> Tuple[bool, str]:
        """
        Save optimization results to CSV
        
        Args:
            results: Dictionary of results
            config_data: Configuration data used
            opt_data: Optimization parameters used
            filepath: Path to save file
            
        Returns:
            (success: bool, message: str)
        """
        try:
            import numpy as np
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['Optimization Results'])
                writer.writerow([])
                
                # Write configuration summary
                writer.writerow(['Configuration Summary'])
                writer.writerow(['Parameter', 'Value'])
                for key, value in config_data.inputs.items():
                    writer.writerow([key, value])
                writer.writerow([])
                
                # Write optimization parameters
                writer.writerow(['Optimization Parameters'])
                writer.writerow(['Parameter', 'Value'])
                for key, value in opt_data.to_dict().items():
                    writer.writerow([key, value])
                writer.writerow([])
                
                # Write results
                writer.writerow(['Results'])
                writer.writerow(['Metric', 'Value'])
                for key, value in results.items():
                    if isinstance(value, np.ndarray):
                        writer.writerow([key, f'Array shape: {value.shape}'])
                        writer.writerow([f'{key}_min', np.min(value)])
                        writer.writerow([f'{key}_max', np.max(value)])
                        writer.writerow([f'{key}_mean', np.mean(value)])
                    else:
                        writer.writerow([key, value])
                
            return True, "Results saved successfully"
        except Exception as e:
            return False, f"Error saving results: {str(e)}"
