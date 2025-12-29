"""
Optimization Runner - Handles long-running optimization in background thread

Responsible for:
- Running simulations in background thread
- Preventing UI freezing
- Handling success/error callbacks
- Thread management
"""

import threading
from typing import Dict, Callable


class OptimizationRunner:
    """Handles optimization execution in background thread"""
    
    def __init__(self, callback_success: Callable, callback_error: Callable):
        """
        Initialize runner with callbacks
        
        Args:
            callback_success: Function to call on successful completion
            callback_error: Function to call on error
        """
        self.callback_success = callback_success
        self.callback_error = callback_error
        self.thread = None
        self.running = False
    
    def run_simulation(self, inputs: Dict):
        """
        Run the optimization simulation
        
        Args:
            inputs: Dictionary of inputs for backend function
        """
        try:
            # Import here to avoid dependency issues if module not available
            from backend import optimization as opt_module
            
            # Extract parameters and call backend function
            results = opt_module.full_range_simulation(
                Dport_Dt_range=inputs['Dport_Dt_range'],
                Dinj_Dt_range=inputs['Dinj_Dt_range'],
                Lc_Dt_range=inputs['Lc_Dt_range'],
                eps=inputs['eps'],
                ptank=inputs['ptank'],
                Ttank=inputs['Ttank'],
                CD=inputs['CD'],
                a=inputs['a'],
                n=inputs['n'],
                rho_fuel=inputs['rho_fuel'],
                oxidizer=inputs['oxidizer'],
                fuel=inputs['fuel'],
                pamb=inputs['pamb'],
                gamma0=inputs['gamma0']
            )
            
            # Package results into dictionary
            result_dict = {
                'pc_array': results[0],
                'Fpc_array': results[1],
                'p_inj_array': results[2],
                'mdot_ox_array': results[3],
                'mdot_fuel_array': results[4],
                'mdot_array': results[5],
                'Gox_array': results[6],
                'r_array': results[7],
                'MR_array': results[8],
                'eps_array': results[9],
                'Tc_array': results[10],
                'MW_array': results[11],
                'gamma_array': results[12],
                'cs_array': results[13],
                'CF_vac_array': results[14],
                'CF_array': results[15],
                'Ivac_array': results[16],
                'Is_array': results[17],
                'flag_array': results[18]
            }
            
            self.running = False
            self.callback_success(result_dict)
            
        except ImportError as e:
            self.running = False
            error_msg = (f"Failed to import optimization module: {str(e)}\n\n"
                        "Make sure optimization.py is in the backend/ directory.")
            self.callback_error(error_msg)
        
        except ValueError as e:
            self.running = False
            error_msg = (f"Invalid input values: {str(e)}\n\n"
                        "Check your configuration and optimization parameters.")
            self.callback_error(error_msg)
        
        except Exception as e:
            self.running = False
            error_msg = f"Simulation error: {str(e)}\n\nError type: {type(e).__name__}"
            self.callback_error(error_msg)
    
    def start(self, inputs: Dict) -> tuple[bool, str]:
        """
        Start simulation in background thread
        
        Args:
            inputs: Dictionary of inputs for backend function
            
        Returns:
            (success: bool, message: str)
        """
        if self.running:
            return False, "Simulation already running"
        
        self.running = True
        self.thread = threading.Thread(target=self.run_simulation, args=(inputs,))
        self.thread.daemon = True
        self.thread.start()
        return True, "Simulation started"
