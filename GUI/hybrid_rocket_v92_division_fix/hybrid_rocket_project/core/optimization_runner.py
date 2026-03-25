"""
Optimization Runner - Handles long-running optimization in background thread

Responsible for:
- Running simulations in background thread
- Preventing UI freezing
- Handling success/error callbacks
- Thread management
- Progress tracking
"""

import threading
import time
from typing import Dict, Callable, Optional


class OptimizationRunner:
    """Handles optimization execution in background thread"""
    
    def __init__(self, callback_success: Callable, callback_error: Callable,
                 callback_progress: Optional[Callable] = None):
        """
        Initialize runner with callbacks
        
        Args:
            callback_success: Function to call on successful completion
            callback_error: Function to call on error
            callback_progress: Function to call with progress updates (current, total, message)
        """
        self.callback_success = callback_success
        self.callback_error = callback_error
        self.callback_progress = callback_progress
        self.thread = None
        self.running = False
        self.cancel_requested = False
    
    def set_progress_callback(self, callback: Callable):
        """Set the progress callback after initialization"""
        self.callback_progress = callback
    
    def request_cancel(self):
        """Request cancellation of the running simulation"""
        self.cancel_requested = True
    
    def _progress_wrapper(self, current: int, total: int, message: str):
        """Wrapper to handle progress updates safely"""
        if self.callback_progress:
            try:
                self.callback_progress(current, total, message)
            except Exception as e:
                print(f"Progress callback error: {e}")
        
        # Print to console as well
        percent = (current / total) * 100 if total > 0 else 0
        print(f"Progress: {current}/{total} ({percent:.1f}%) - {message}")
    
    def run_simulation(self, inputs: Dict):
        """
        Run the optimization simulation
        
        Args:
            inputs: Dictionary of inputs for backend function
        """
        try:
            self.cancel_requested = False
            
            # Debug: print inputs to console
            print("\n=== OPTIMIZATION INPUTS ===")
            print(f"Dport_Dt_range: {inputs['Dport_Dt_range']}")
            print(f"Dinj_Dt_range: {inputs['Dinj_Dt_range']}")
            print(f"Lc_Dt_range: {inputs['Lc_Dt_range']}")
            print(f"eps: {inputs['eps']}")
            print(f"ptank: {inputs['ptank']}")
            print(f"Ttank: {inputs['Ttank']}")
            print(f"CD: {inputs['CD']}")
            print(f"a: {inputs['a']}")
            print(f"n: {inputs['n']}")
            print(f"rho_fuel: {inputs['rho_fuel']}")
            print(f"pamb: {inputs['pamb']}")
            print(f"line_losses: {inputs.get('line_losses', 0)}")
            print("\n--- OXIDIZER ---")
            for k, v in inputs['oxidizer'].items():
                print(f"  {k}: '{v}'")
            print("\n--- FUEL ---")
            for k, v in inputs['fuel'].items():
                print(f"  {k}: {v}")
            
            # Calculate total iterations
            n_dport = len(inputs['Dport_Dt_range'])
            n_dinj = len(inputs['Dinj_Dt_range'])
            n_lc = len(inputs['Lc_Dt_range'])
            total = n_dport * n_dinj * n_lc
            print(f"Total iterations: {total} ({n_dport} x {n_dinj} x {n_lc})")
            print("===========================\n")
            
            # Import here to avoid dependency issues if module not available
            from backend import optimization as opt_module
            
            # Set line losses before running simulation
            try:
                from Line_losses import linelosses as ll
                line_losses_value = inputs.get('line_losses', 0)
                ll.set_line_losses(line_losses_value)
            except ImportError:
                pass  # Line losses module not available, will use default 0
            
            # Start time tracking
            start_time = time.time()
            
            # Extract parameters and call backend function with progress callback
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
                gamma0=inputs['gamma0'],
                progress_callback=self._progress_wrapper
            )
            
            elapsed_time = time.time() - start_time
            print(f"\n=== OPTIMIZATION COMPLETE ===")
            print(f"Total time: {elapsed_time:.2f} seconds")
            print("=============================\n")
            
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
                        "Check your configuration and optimization parameters.\n\n"
                        "Common issues:\n"
                        "- Oxidizer CoolProp name not set (e.g., 'NitrousOxide')\n"
                        "- Fuel exploded formula not set (e.g., 'C 73 H 124')\n"
                        "- Invalid temperature or enthalpy values")
            self.callback_error(error_msg)
        
        except Exception as e:
            self.running = False
            import traceback
            tb = traceback.format_exc()
            error_msg = f"Simulation error: {str(e)}\n\nError type: {type(e).__name__}\n\nTraceback:\n{tb}"
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
