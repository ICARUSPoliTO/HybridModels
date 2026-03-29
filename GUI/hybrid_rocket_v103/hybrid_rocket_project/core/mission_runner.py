"""
Mission Runner - Handles mission simulation in background thread

Responsible for:
- Running mission simulations in background thread
- Preventing UI freezing during long simulations
- Handling success/error callbacks
- Progress tracking
"""

import threading
import time
from typing import Dict, Callable, Optional


class MissionRunner:
    """Handles mission execution in background thread"""
    
    def __init__(self, callback_success: Callable, callback_error: Callable,
                 callback_progress: Optional[Callable] = None):
        """
        Initialize runner with callbacks
        
        Args:
            callback_success: Function to call on successful completion
            callback_error: Function to call on error
            callback_progress: Function to call with progress updates
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
    
    def _progress_wrapper(self, message: str, progress: float = None):
        """Wrapper to handle progress updates safely"""
        # Check for cancellation
        if self.cancel_requested:
            raise InterruptedError("Mission cancelled by user")
        
        if self.callback_progress:
            try:
                self.callback_progress(message, progress)
            except Exception as e:
                print(f"Progress callback error: {e}")
        print(f"Mission: {message}")
    
    def run_mission(self, inputs: Dict, match_mode: bool = False):
        """
        Run the mission simulation
        
        Args:
            inputs: Dictionary of inputs for mission simulation
            match_mode: If True, use match_mission; else use run_full_mission
        """
        try:
            self.cancel_requested = False
            
            print("\n=== MISSION SIMULATION STARTED ===")
            print(f"Mode: {'Match Mission' if match_mode else 'Run Mission'}")
            print(f"Burn time: {inputs['burn_time']} s")
            print(f"Delay time: {inputs['delay_time']} s")
            print(f"Chamber diameter: {inputs['D_chamber']} m")
            print(f"Throat area: {inputs['At']} m²")
            print(f"Injection area: {inputs['Ainj']} m²")
            print(f"Grain length: {inputs['Lc']} m")
            print(f"Tank mass: {inputs['mtank']} kg")
            print(f"Vapor quality: {inputs['Q']}")
            print("===================================\n")
            
            start_time = time.time()
            
            # Import mission simulation module
            from Mission import mission_simulation as mission
            from Tank import tank_update as tank
            
            # Utilities for tank update
            utilities = {
                "CDvent": inputs['CD'],
                "Avent": 0.0,  # No venting by default
            }
            
            if inputs.get('constant_pressure_tank', False):
                utilities["CDpress"] = inputs['CD']
                utilities["Apress"] = 0.25 * 3.14159 * (0.005)**2  # Small pressurant line
            
            if match_mode:
                self._progress_wrapper("Running match_mission...", 0.2)
                
                # Match mission mode - builds tank internally
                time_data, sim_inputs, performances_list, log = mission.match_mission(
                    burn_time=inputs['burn_time'],
                    pamb=inputs['pamb'],
                    Tamb=inputs['Tamb'],
                    a=inputs['a'],
                    n=inputs['n'],
                    rho_fuel=inputs['rho_fuel'],
                    eps=inputs['eps'],
                    Ainj=inputs['Ainj'],
                    At=inputs['At'],
                    Lc=inputs['Lc'],
                    D_chamber=inputs['D_chamber'],
                    x=inputs['x'],
                    y=inputs['y'],
                    z=inputs['z'],
                    Vol_prechamber=inputs['Vol_prechamber'],
                    Vol_postchamber=inputs['Vol_postchamber'],
                    utilities=utilities,
                    CD=inputs['CD'],
                    mtank=inputs['mtank'],
                    Q=inputs['Q'],
                    oxidizer=inputs['oxidizer'],
                    fuel=inputs['fuel'],
                    pressurant=inputs['pressurant'],
                    rend_cstar=inputs['rend_cstar'],
                    rend_CF=inputs['rend_CF'],
                    pitch=inputs['pitch'],
                    circular=inputs['circular'],
                    delay_time=inputs['delay_time'],
                    npointsperside=50,
                    tol=1e-3,
                    ppress=inputs.get('ppress', 1e5),
                    ptank0=inputs['ptank'],
                    plim=None
                )
            else:
                self._progress_wrapper("Building tank...", 0.1)
                
                # Build tank first for run_full_mission
                masses, volumes, pressures, temperatures, constant_pressure_tank = tank.build_tank(
                    m=inputs['mtank'],
                    Q=inputs['Q'],
                    T=inputs['Ttank'],
                    oxidizer=inputs['oxidizer'],
                    pressurant=inputs['pressurant'],
                    ppress=inputs.get('ppress', 1e5),
                    p=inputs['ptank'],
                    plim=None
                )
                
                self._progress_wrapper("Running simulation...", 0.2)
                
                # Run full mission mode
                time_data, performances_list, log = mission.run_full_mission(
                    burn_time=inputs['burn_time'],
                    pamb=inputs['pamb'],
                    Tamb=inputs['Tamb'],
                    a=inputs['a'],
                    n=inputs['n'],
                    rho_fuel=inputs['rho_fuel'],
                    eps=inputs['eps'],
                    Ainj=inputs['Ainj'],
                    At=inputs['At'],
                    Lc=inputs['Lc'],
                    D_chamber=inputs['D_chamber'],
                    x=inputs['x'],
                    y=inputs['y'],
                    z=inputs['z'],
                    Vol_prechamber=inputs['Vol_prechamber'],
                    Vol_postchamber=inputs['Vol_postchamber'],
                    masses=masses,
                    volumes=volumes,
                    pressures=pressures,
                    temperatures=temperatures,
                    utilities=utilities,
                    CD=inputs['CD'],
                    oxidizer=inputs['oxidizer'],
                    fuel=inputs['fuel'],
                    pressurant=inputs['pressurant'],
                    rend_cstar=inputs['rend_cstar'],
                    rend_CF=inputs['rend_CF'],
                    pitch=inputs['pitch'],
                    circular=inputs['circular'],
                    delay_time=inputs['delay_time'],
                    npointsperside=50,
                    constant_pressure_tank=constant_pressure_tank,
                    tol=1e-3
                )
            
            self._progress_wrapper("Normalizing results...", 0.9)
            
            # Normalize performances to dictionary of lists
            performances = mission.normalize_performances(performances_list)
            
            elapsed_time = time.time() - start_time
            
            print(f"\n=== MISSION COMPLETE ===")
            print(f"Total time: {elapsed_time:.2f} seconds")
            print(f"Simulation points: {len(time_data)}")
            print(f"Final time: {time_data[-1] if time_data else 0:.3f} s")
            print("========================\n")
            
            self.running = False
            self.callback_success(time_data, performances, log)
        
        except InterruptedError as e:
            self.running = False
            self.cancel_requested = False
            self.callback_error("CANCELLED: Mission stopped by user.")
            
        except ImportError as e:
            self.running = False
            error_msg = (f"Failed to import mission module: {str(e)}\n\n"
                        "Make sure all Mission/ files are in place.")
            self.callback_error(error_msg)
        
        except Exception as e:
            self.running = False
            import traceback
            tb = traceback.format_exc()
            error_msg = f"Mission simulation error: {str(e)}\n\nTraceback:\n{tb}"
            self.callback_error(error_msg)
    
    def start(self, inputs: Dict, match_mode: bool = False) -> tuple:
        """
        Start simulation in background thread
        
        Args:
            inputs: Dictionary of inputs for mission simulation
            match_mode: If True, use match_mission
            
        Returns:
            (success: bool, message: str)
        """
        if self.running:
            return False, "Simulation already running"
        
        self.running = True
        self.thread = threading.Thread(
            target=self.run_mission, 
            args=(inputs, match_mode)
        )
        self.thread.daemon = True
        self.thread.start()
        return True, "Mission simulation started"
