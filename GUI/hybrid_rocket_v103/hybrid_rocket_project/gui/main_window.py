"""
Main Window - Primary GUI container and coordinator

Manages:
- Window layout (header, sidebar, content area)
- Page navigation
- User actions (save, load, run)
- Coordination with controller
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config.constants import COLORS, FONTS, WINDOW_CONFIG, BUTTON_STYLE, FILE_TYPES
from core.controller import ApplicationController
from core.optimization_runner import OptimizationRunner
from core.mission_runner import MissionRunner
from gui.pages.configuration_page import create_configuration_page
from gui.pages.optimization_page import create_optimization_page
from gui.pages.mission_page import create_mission_page
from gui.pages.optimization_output_page import create_optimization_output_page
from gui.pages.mission_output_page import create_mission_output_page
from gui.components.popup_manager import PopupManager
from utils.reactants import ReactantManager


class HybridRocketGUI:
    """Main GUI window and coordinator"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_CONFIG['title'])
        self.root.geometry(WINDOW_CONFIG['geometry'])
        self.root.configure(bg=COLORS['bg_dark'])
        
        # Initialize controller
        self.controller = ApplicationController()
        
        # Initialize managers
        self.reactant_manager = ReactantManager()
        self.popup_manager = PopupManager(root)
        
        # Maximize window
        try:
            self.root.state('zoomed')
        except:
            pass
        
        # Shared input storage
        self.inputs = {}
        self.dropdowns = {}
        self.current_page = 'configuration'
        
        # Current page object reference
        self.current_page_obj = None
        
        # Create UI
        self.create_header()
        self.create_sidebar()
        
        # Content area
        self.content_frame = tk.Frame(self.root, bg=COLORS['bg_dark'])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Show configuration page by default
        self.show_configuration_page()
    
    def create_header(self):
        """Create header bar"""
        header = tk.Frame(self.root, bg=COLORS['bg_medium'], height=60)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header, 
            text="Hybrid Rocket Simulator", 
            font=FONTS['header'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        ).pack(side=tk.LEFT, padx=20)
    
    def create_sidebar(self):
        """Create navigation sidebar"""
        sidebar = tk.Frame(self.root, bg=COLORS['bg_medium'], width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        tk.Label(
            sidebar, 
            text="Navigation", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        ).pack(pady=20)
        
        # Navigation buttons
        btn_config = tk.Button(
            sidebar, 
            text="Configuration", 
            font=FONTS['button'],
            bg=COLORS['bg_active'], 
            fg=COLORS['text_color'], 
            relief=tk.FLAT,
            command=self.show_configuration_page, 
            cursor='hand2'
        )
        btn_config.pack(fill=tk.X, padx=10, pady=5)
        
        btn_optimization = tk.Button(
            sidebar, 
            text="Optimization", 
            font=FONTS['button'],
            bg=COLORS['bg_light'], 
            fg=COLORS['text_color'], 
            relief=tk.FLAT,
            command=self.show_optimization_page, 
            cursor='hand2'
        )
        btn_optimization.pack(fill=tk.X, padx=10, pady=5)
        
        btn_opt_output = tk.Button(
            sidebar, 
            text="Optimization Output", 
            font=FONTS['button'],
            bg=COLORS['bg_light'], 
            fg=COLORS['text_color'], 
            relief=tk.FLAT,
            command=self.show_optimization_output_page, 
            cursor='hand2'
        )
        btn_opt_output.pack(fill=tk.X, padx=10, pady=5)
        
        btn_mission = tk.Button(
            sidebar, 
            text="Mission", 
            font=FONTS['button'],
            bg=COLORS['bg_light'], 
            fg=COLORS['text_color'], 
            relief=tk.FLAT,
            command=self.show_mission_page, 
            cursor='hand2'
        )
        btn_mission.pack(fill=tk.X, padx=10, pady=5)
        
        btn_mission_output = tk.Button(
            sidebar, 
            text="Mission Output", 
            font=FONTS['button'],
            bg=COLORS['bg_light'], 
            fg=COLORS['text_color'], 
            relief=tk.FLAT,
            command=self.show_mission_output_page, 
            cursor='hand2'
        )
        btn_mission_output.pack(fill=tk.X, padx=10, pady=5)
    
    def clear_content(self):
        """Clear current page content"""
        # Save configuration data BEFORE destroying widgets
        if self.current_page == 'configuration' and hasattr(self, 'configuration_page_obj') and self.configuration_page_obj:
            self._save_current_configuration()
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.current_page_obj = None
    
    def show_configuration_page(self):
        """Display configuration page"""
        self.current_page = 'configuration'
        
        # Clear but don't save (we're going TO configuration, not FROM it)
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.current_page_obj = None
        
        # Create page-specific frame
        page_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        page_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create configuration page with managers
        self.configuration_page_obj = create_configuration_page(
            page_frame, 
            self.inputs, 
            self.dropdowns,
            self.reactant_manager,
            self.popup_manager
        )
        self.current_page_obj = self.configuration_page_obj
        
        # Add action buttons
        self.create_configuration_buttons()
    
    def show_optimization_page(self):
        """Display optimization page"""
        self.current_page = 'optimization'
        self.clear_content()
        
        # Create page-specific frame
        page_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        page_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create optimization page
        self.current_page_obj = create_optimization_page(page_frame, self.inputs)
        
        # Add action buttons
        self.create_optimization_buttons()
    
    def _save_current_configuration(self):
        """Save configuration data from the configuration page - MUST be called BEFORE widgets are destroyed"""
        if not hasattr(self, 'configuration_page_obj') or not self.configuration_page_obj:
            return
            
        try:
            selected_fuels, fuel_weights = self.configuration_page_obj.get_fuel_data()
            # Store fuel data for later use
            self._stored_selected_fuels = selected_fuels
            self._stored_fuel_weights = fuel_weights
        except Exception as e:
            print(f"Warning: Could not get fuel data: {e}")
            selected_fuels = getattr(self, '_stored_selected_fuels', [])
            fuel_weights = getattr(self, '_stored_fuel_weights', {})
        
        # Collect all inputs - store the VALUES, not the widgets
        inputs = {}
        for key, entry in list(self.inputs.items()):
            if not key.startswith("Optimization_"):
                try:
                    if entry.winfo_exists():
                        value = entry.get().strip()
                        if value:
                            inputs[key] = value
                except Exception as e:
                    pass
        
        # Collect dropdown values
        dropdowns = {}
        for key, combo in list(self.dropdowns.items()):
            try:
                if combo.winfo_exists():
                    value = combo.get()
                    if value:
                        dropdowns[key] = value
            except Exception as e:
                pass
        
        # Debug print
        print("\n=== SAVING CONFIGURATION ===")
        print(f"Selected fuels: {selected_fuels}")
        print(f"Inputs keys: {list(inputs.keys())}")
        print(f"Dropdowns: {dropdowns}")
        print(f"Oxidizer_CoolProp: {inputs.get('Oxidizer_CoolProp', 'NOT FOUND')}")
        print(f"Oxidizer_CEA: {dropdowns.get('Oxidizer_CEA', 'NOT FOUND')}")
        print(f"Fuel_ExplodedFormula: {inputs.get('Fuel_ExplodedFormula', 'NOT FOUND')}")
        print("============================\n")
        
        # Only save if we have meaningful data
        if inputs or dropdowns or selected_fuels:
            self.controller.set_configuration_data(
                inputs, dropdowns, selected_fuels, fuel_weights
            )
    
    def show_mission_page(self):
        """Display mission page"""
        self.current_page = 'mission'
        self.clear_content()
        
        # Create page-specific frame
        page_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        page_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create mission page with dropdowns
        self.current_page_obj = create_mission_page(page_frame, self.inputs, self.dropdowns)
        self.mission_page_obj = self.current_page_obj  # Keep reference
        
        # Add action buttons
        self.create_mission_buttons()
    
    def show_optimization_output_page(self):
        """Display optimization output page"""
        self.current_page = 'optimization_output'
        self.clear_content()
        
        # Create page-specific frame
        page_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        page_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create optimization output page with controller
        self.current_page_obj = create_optimization_output_page(page_frame, self.controller)
        
        # If we have results stored, display them with Gox limits
        if self.controller.results is not None:
            # Get Gox limits from optimization data
            gox_min = 100.0
            gox_max = 800.0
            if self.controller.optimization_data is not None:
                gox_min = getattr(self.controller.optimization_data, 'gox_min', 100.0)
                gox_max = getattr(self.controller.optimization_data, 'gox_max', 800.0)
            
            self.current_page_obj.display_results(
                self.controller.results,
                gox_min=gox_min,
                gox_max=gox_max
            )
    
    def show_mission_output_page(self):
        """Display mission output page"""
        self.current_page = 'mission_output'
        self.clear_content()
        
        # Create page-specific frame
        page_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        page_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create mission output page with controller
        self.current_page_obj = create_mission_output_page(page_frame, self.controller)
        self.mission_output_page_obj = self.current_page_obj  # Keep reference
        
        # If we have mission results, display them
        if hasattr(self.controller, 'mission_results') and self.controller.mission_results:
            mr = self.controller.mission_results
            self.current_page_obj.display_results(
                mr.get('time', []),
                mr.get('performances', {}),
                mr.get('log', '')
            )
    
    def create_configuration_buttons(self):
        """Create action buttons for configuration page"""
        button_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        button_frame.pack(side=tk.BOTTOM, pady=20)
        
        # Apply button (save without file dialog)
        tk.Button(
            button_frame, 
            text="Apply Configuration",
            font=FONTS['button'],
            bg='#4CAF50',  # Green
            fg='white',
            command=self.apply_configuration,
            cursor='hand2',
            padx=15,
            pady=8
        ).grid(row=0, column=0, padx=10)
        
        # Save to file button
        tk.Button(
            button_frame, 
            text="Save to File",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.save_configuration,
            cursor='hand2',
            padx=15,
            pady=8
        ).grid(row=0, column=1, padx=10)
        
        # Load button
        tk.Button(
            button_frame, 
            text="Load from File",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.load_configuration,
            cursor='hand2',
            padx=15,
            pady=8
        ).grid(row=0, column=2, padx=10)
        
        # Send to optimization button
        tk.Button(
            button_frame, 
            text="Go to Optimization →",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.send_to_optimization,
            cursor='hand2',
            padx=15,
            pady=8
        ).grid(row=0, column=2, padx=10)
    
    def create_optimization_buttons(self):
        """Create action buttons for optimization page"""
        button_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        button_frame.pack(side=tk.BOTTOM, pady=20)
        
        # Save button
        tk.Button(
            button_frame, 
            text="Save Optimization Parameters",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.save_optimization,
            cursor='hand2',
            padx=15,
            pady=8
        ).grid(row=0, column=0, padx=10)
        
        # Load button
        tk.Button(
            button_frame, 
            text="Load Optimization Parameters",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.load_optimization,
            cursor='hand2',
            padx=15,
            pady=8
        ).grid(row=0, column=1, padx=10)
        
        # Run simulation button
        tk.Button(
            button_frame, 
            text="Run Optimization",
            font=FONTS['button'],
            bg='#4CAF50',  # Green for action
            fg='white',
            command=self.run_optimization,
            cursor='hand2',
            padx=15,
            pady=8
        ).grid(row=0, column=2, padx=10)
        
        # View Output button
        tk.Button(
            button_frame,
            text="View Output →",
            font=FONTS['button'],
            bg='#2196F3',  # Blue for navigation
            fg='white',
            command=self.show_optimization_output_page,
            cursor='hand2',
            padx=15,
            pady=8
        ).grid(row=0, column=3, padx=10)
    
    def create_mission_buttons(self):
        """Create action buttons for mission page"""
        button_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        button_frame.pack(side=tk.BOTTOM, pady=20)
        
        # Run Mission button
        tk.Button(
            button_frame,
            text="Run Mission",
            font=FONTS['button'],
            bg='#4CAF50',
            fg='white',
            command=self.run_mission,
            cursor='hand2',
            padx=20, pady=10
        ).grid(row=0, column=0, padx=10)
        
        # Match Mission button
        tk.Button(
            button_frame,
            text="Match Mission",
            font=FONTS['button'],
            bg='#2196F3',
            fg='white',
            command=self.match_mission,
            cursor='hand2',
            padx=20, pady=10
        ).grid(row=0, column=1, padx=10)
        
        # View Results button
        tk.Button(
            button_frame,
            text="View Results →",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.show_mission_output_page,
            cursor='hand2',
            padx=15, pady=8
        ).grid(row=0, column=2, padx=10)
    
    def run_mission(self):
        """Run mission simulation with current parameters"""
        try:
            # Make sure we have configuration data
            if not self.controller.configuration_data:
                # Try to collect it
                self.collect_and_store_configuration()
            
            if not self.controller.configuration_data:
                messagebox.showerror("Error", "Please configure fuel and oxidizer first.")
                return
            
            # Get mission data from the page
            if not hasattr(self, 'mission_page_obj') or self.mission_page_obj is None:
                messagebox.showerror("Error", "Mission page not initialized.")
                return
            
            mission_data = self.mission_page_obj.get_mission_data()
            
            # Prepare inputs
            try:
                inputs = self.controller.prepare_mission_inputs(mission_data)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to prepare mission inputs:\n{str(e)}")
                return
            
            # Create mission runner
            self.mission_runner = MissionRunner(
                callback_success=self._on_mission_success,
                callback_error=self._on_mission_error,
                callback_progress=self._on_mission_progress
            )
            
            # Show progress dialog
            self._show_mission_progress_dialog("Running Mission Simulation...")
            
            # Start simulation
            success, message = self.mission_runner.start(inputs, match_mode=False)
            
            if not success:
                self._close_mission_progress_dialog()
                messagebox.showerror("Error", message)
                
        except Exception as e:
            import traceback
            messagebox.showerror("Error", f"Mission simulation failed:\n{str(e)}\n\n{traceback.format_exc()}")
    
    def match_mission(self):
        """Run mission matching to find optimal configuration"""
        try:
            # Make sure we have configuration data
            if not self.controller.configuration_data:
                self.collect_and_store_configuration()
            
            if not self.controller.configuration_data:
                messagebox.showerror("Error", "Please configure fuel and oxidizer first.")
                return
            
            # Get mission data from the page
            if not hasattr(self, 'mission_page_obj') or self.mission_page_obj is None:
                messagebox.showerror("Error", "Mission page not initialized.")
                return
            
            mission_data = self.mission_page_obj.get_mission_data()
            
            # Prepare inputs
            try:
                inputs = self.controller.prepare_mission_inputs(mission_data)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to prepare mission inputs:\n{str(e)}")
                return
            
            # Create mission runner
            self.mission_runner = MissionRunner(
                callback_success=self._on_mission_success,
                callback_error=self._on_mission_error,
                callback_progress=self._on_mission_progress
            )
            
            # Show progress dialog
            self._show_mission_progress_dialog("Matching Mission Requirements...")
            
            # Start simulation in match mode
            success, message = self.mission_runner.start(inputs, match_mode=True)
            
            if not success:
                self._close_mission_progress_dialog()
                messagebox.showerror("Error", message)
                
        except Exception as e:
            import traceback
            messagebox.showerror("Error", f"Mission matching failed:\n{str(e)}\n\n{traceback.format_exc()}")
    
    def _show_mission_progress_dialog(self, title: str):
        """Show a progress dialog for mission simulation"""
        self.mission_progress_window = tk.Toplevel(self.root)
        self.mission_progress_window.title(title)
        self.mission_progress_window.geometry("400x180")
        self.mission_progress_window.transient(self.root)
        self.mission_progress_window.grab_set()
        
        # Center the window
        self.mission_progress_window.update_idletasks()
        x = (self.root.winfo_screenwidth() - 400) // 2
        y = (self.root.winfo_screenheight() - 180) // 2
        self.mission_progress_window.geometry(f"+{x}+{y}")
        
        tk.Label(
            self.mission_progress_window,
            text=title,
            font=FONTS['section']
        ).pack(pady=20)
        
        self.mission_progress_label = tk.Label(
            self.mission_progress_window,
            text="Initializing...",
            font=FONTS['label']
        )
        self.mission_progress_label.pack(pady=10)
        
        self.mission_progress_bar = ttk.Progressbar(
            self.mission_progress_window,
            mode='indeterminate',
            length=300
        )
        self.mission_progress_bar.pack(pady=10)
        self.mission_progress_bar.start(10)
        
        # Stop button
        self.mission_stop_button = tk.Button(
            self.mission_progress_window,
            text="⏹ Stop Mission",
            font=FONTS['button'],
            bg='#f44336',  # Red
            fg='white',
            command=self._stop_mission,
            cursor='hand2',
            padx=20,
            pady=5
        )
        self.mission_stop_button.pack(pady=10)
        
        # Prevent closing via X button
        self.mission_progress_window.protocol("WM_DELETE_WINDOW", self._stop_mission)
    
    def _stop_mission(self):
        """Stop the running mission simulation"""
        if hasattr(self, 'mission_runner') and self.mission_runner:
            self.mission_runner.request_cancel()
            
            # Update UI to show stopping
            if hasattr(self, 'mission_stop_button'):
                self.mission_stop_button.config(text="Stopping...", state=tk.DISABLED)
            if hasattr(self, 'mission_progress_label'):
                self.mission_progress_label.config(text="Cancelling mission...")
    
    def _close_mission_progress_dialog(self):
        """Close the mission progress dialog"""
        if hasattr(self, 'mission_progress_window') and self.mission_progress_window:
            try:
                self.mission_progress_bar.stop()
                self.mission_progress_window.destroy()
            except:
                pass
            self.mission_progress_window = None
    
    def _on_mission_progress(self, message: str, progress: float = None):
        """Handle mission progress updates"""
        if hasattr(self, 'mission_progress_label') and self.mission_progress_label:
            try:
                self.mission_progress_label.config(text=message)
                self.root.update_idletasks()
            except:
                pass
    
    def _on_mission_success(self, time_data, performances, log):
        """Handle successful mission completion"""
        self._close_mission_progress_dialog()
        
        # Store results
        self.controller.set_mission_results(time_data, performances, log)
        
        # Show success message
        total_time = time_data[-1] if time_data else 0
        n_points = len(time_data)
        
        messagebox.showinfo(
            "Mission Complete",
            f"Mission simulation completed successfully!\n\n"
            f"Simulation time: {total_time:.3f} s\n"
            f"Data points: {n_points}\n\n"
            f"Click 'View Results' to see detailed output."
        )
        
        # Navigate to results page
        self.show_mission_output_page()
    
    def _on_mission_error(self, error_msg: str):
        """Handle mission error"""
        self._close_mission_progress_dialog()
        
        # Check if it was a cancellation
        if "CANCELLED" in error_msg:
            messagebox.showinfo("Mission Stopped", "Mission was stopped by user.")
        else:
            messagebox.showerror("Mission Error", error_msg)
    
    # ==================================================================
    # DATA COLLECTION METHODS
    # ==================================================================
    
    def collect_configuration_data(self):
        """Collect all configuration data from inputs"""
        inputs = {}
        for key, entry in self.inputs.items():
            if not key.startswith("Optimization_"):
                try:
                    if entry.winfo_exists():
                        value = entry.get().strip()
                        if value:
                            inputs[key] = value
                except:
                    pass
        
        dropdowns = {}
        for key, combo in self.dropdowns.items():
            try:
                if combo.winfo_exists():
                    value = combo.get()
                    if value:
                        dropdowns[key] = value
            except:
                pass
        
        # Get fuel data - try configuration_page_obj first, then current_page_obj
        selected_fuels = []
        fuel_weights = {}
        
        # Try to get from configuration page object
        if hasattr(self, 'configuration_page_obj') and self.configuration_page_obj:
            try:
                selected_fuels, fuel_weights = self.configuration_page_obj.get_fuel_data()
            except:
                pass
        
        # Fallback to current page if it's a configuration page
        if not selected_fuels and self.current_page_obj and hasattr(self.current_page_obj, 'get_fuel_data'):
            try:
                selected_fuels, fuel_weights = self.current_page_obj.get_fuel_data()
            except:
                pass
        
        # Fallback to stored fuel data
        if not selected_fuels and hasattr(self, '_stored_selected_fuels'):
            selected_fuels = self._stored_selected_fuels
            fuel_weights = getattr(self, '_stored_fuel_weights', {})
        
        return {
            'inputs': inputs,
            'dropdowns': dropdowns,
            'selected_fuels': selected_fuels,
            'fuel_weight_entries': fuel_weights
        }
    
    def collect_optimization_data(self):
        """Collect all optimization data from inputs"""
        data = {}
        for key, entry in self.inputs.items():
            if key.startswith("Optimization_"):
                value = entry.get().strip()
                if value:
                    # Remove prefix and convert to lowercase
                    param_name = key.replace("Optimization_", "").lower()
                    try:
                        if param_name == "parameter_points":
                            data[param_name] = int(value)
                        else:
                            data[param_name] = float(value)
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid value for {param_name}: {value}")
                        return None
        
        # Validate required fields
        required = ['parameter_points', 'dport_dt_min', 'dport_dt_max', 
                   'dinj_dt_min', 'dinj_dt_max', 'lc_dt_min', 'lc_dt_max',
                   'ptank', 'ttank', 'pamb']
        
        for field in required:
            if field not in data:
                messagebox.showerror("Error", f"Missing required field: {field}")
                return None
        
        # Add default values for Gox limits if not specified
        if 'gox_min' not in data:
            data['gox_min'] = 100.0
        if 'gox_max' not in data:
            data['gox_max'] = 800.0
        
        return data
    
    # ==================================================================
    # ACTION METHODS
    # ==================================================================
    
    def apply_configuration(self):
        """Apply configuration data without saving to file"""
        data = self.collect_configuration_data()
        
        # Store fuel data
        self._stored_selected_fuels = data['selected_fuels']
        self._stored_fuel_weights = data['fuel_weight_entries']
        
        self.controller.set_configuration_data(
            data['inputs'], 
            data['dropdowns'], 
            data['selected_fuels'],
            data['fuel_weight_entries']
        )
        
        # Debug print
        print("\n=== CONFIGURATION APPLIED ===")
        print(f"Selected fuels: {data['selected_fuels']}")
        print(f"Oxidizer_CoolProp: {data['inputs'].get('Oxidizer_CoolProp', 'NOT SET')}")
        print(f"Oxidizer_CEA: {data['dropdowns'].get('Oxidizer_CEA', 'NOT SET')}")
        print(f"Fuel_ExplodedFormula: {data['inputs'].get('Fuel_ExplodedFormula', 'NOT SET')}")
        print("==============================\n")
        
        messagebox.showinfo("Success", "Configuration applied! You can now go to Optimization page.")
    
    def save_configuration(self):
        """Save configuration data to CSV"""
        data = self.collect_configuration_data()
        self.controller.set_configuration_data(
            data['inputs'], 
            data['dropdowns'], 
            data['selected_fuels'],
            data['fuel_weight_entries']
        )
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=FILE_TYPES['config'],
            title="Save Configuration"
        )
        
        if filepath:
            success, message = self.controller.save_configuration(filepath)
            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
    
    def load_configuration(self):
        """Load configuration data from CSV"""
        filepath = filedialog.askopenfilename(
            filetypes=FILE_TYPES['config'],
            title="Load Configuration"
        )
        
        if filepath:
            success, data, message = self.controller.load_configuration(filepath)
            if success:
                # Populate input fields
                for key, value in data['inputs'].items():
                    if key in self.inputs:
                        self.inputs[key].delete(0, tk.END)
                        self.inputs[key].insert(0, str(value))
                
                # Populate dropdowns
                for key, value in data['dropdowns'].items():
                    if key in self.dropdowns:
                        self.dropdowns[key].set(value)
                
                # Set fuel data if page object exists
                if self.current_page_obj and hasattr(self.current_page_obj, 'set_fuel_data'):
                    self.current_page_obj.set_fuel_data(
                        data['selected_fuels'],
                        data['fuel_weight_entries']
                    )
                
                # Store in controller
                self.controller.set_configuration_data(
                    data['inputs'],
                    data['dropdowns'],
                    data['selected_fuels'],
                    data['fuel_weight_entries']
                )
                
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
    
    def send_to_optimization(self):
        """Send configuration data to optimization page"""
        data = self.collect_configuration_data()
        self.controller.set_configuration_data(
            data['inputs'], 
            data['dropdowns'], 
            data['selected_fuels'],
            data['fuel_weight_entries']
        )
        messagebox.showinfo(
            "Success", 
            "Configuration data sent to Optimization page!\n\n" + 
            "You can now go to the Optimization page and run the simulation."
        )
    
    def save_optimization(self):
        """Save optimization parameters to CSV"""
        data = self.collect_optimization_data()
        if data is None:
            return
        
        self.controller.set_optimization_data(data)
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=FILE_TYPES['optimization'],
            title="Save Optimization Parameters"
        )
        
        if filepath:
            success, message = self.controller.save_optimization(filepath)
            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
    
    def load_optimization(self):
        """Load optimization parameters from CSV"""
        filepath = filedialog.askopenfilename(
            filetypes=FILE_TYPES['optimization'],
            title="Load Optimization Parameters"
        )
        
        if filepath:
            success, data, message = self.controller.load_optimization(filepath)
            if success:
                # Populate fields - data keys are lowercase, field keys have capitals
                for key, value in data.items():
                    # Find matching field
                    for input_key in self.inputs.keys():
                        if input_key.startswith("Optimization_") and \
                           input_key.lower() == f"optimization_{key}":
                            self.inputs[input_key].delete(0, tk.END)
                            self.inputs[input_key].insert(0, str(value))
                            break
                
                # Store in controller
                self.controller.set_optimization_data(data)
                
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
    
    def run_optimization(self):
        """Run the optimization simulation"""
        # Make sure we have configuration data
        if self.controller.configuration_data is None:
            messagebox.showerror("Error", 
                "No configuration data found!\n\n"
                "Please go to the Configuration page, fill in the data, "
                "and click 'Save Configuration' before running optimization.")
            return
        
        # Check for essential configuration fields
        config = self.controller.configuration_data
        oxidizer_cp = config.inputs.get('Oxidizer_CoolProp', '')
        oxidizer_cea = config.dropdowns.get('Oxidizer_CEA', '')
        
        if not oxidizer_cp or not oxidizer_cea:
            messagebox.showerror("Error", 
                "Oxidizer not configured!\n\n"
                "Please go to Configuration page and select an oxidizer.")
            return
        
        if not config.selected_fuels:
            messagebox.showerror("Error", 
                "Fuel not configured!\n\n"
                "Please go to Configuration page and select a fuel.")
            return
        
        # Collect current optimization data
        opt_data = self.collect_optimization_data()
        if opt_data is None:
            return
        
        self.controller.set_optimization_data(opt_data)
        
        # Check if ready
        ready, message = self.controller.is_ready_for_optimization()
        if not ready:
            messagebox.showerror("Error", message)
            return
        
        # Prepare inputs
        inputs = self.controller.prepare_optimization_inputs()
        if inputs is None:
            messagebox.showerror("Error", "Failed to prepare optimization inputs")
            return
        
        # Show running dialog with progress bar
        self.show_running_dialog(inputs)
        
        # Create and start optimization runner with progress callback
        self.optimization_runner = OptimizationRunner(
            callback_success=self.on_optimization_success,
            callback_error=self.on_optimization_error,
            callback_progress=self.on_optimization_progress
        )
        
        success, msg = self.optimization_runner.start(inputs)
        if not success:
            self.close_running_dialog()
            messagebox.showerror("Error", msg)
    
    # ==================================================================
    # DIALOG AND RESULT HANDLING
    # ==================================================================
    
    def show_running_dialog(self, inputs=None):
        """Show 'Running...' dialog with progress bar"""
        self.running_dialog = tk.Toplevel(self.root)
        self.running_dialog.title("Running Optimization")
        self.running_dialog.geometry("500x250")
        self.running_dialog.configure(bg=COLORS['bg_medium'])
        self.running_dialog.transient(self.root)
        self.running_dialog.grab_set()
        
        # Center on screen
        self.running_dialog.update_idletasks()
        x = (self.running_dialog.winfo_screenwidth() // 2) - (250)
        y = (self.running_dialog.winfo_screenheight() // 2) - (125)
        self.running_dialog.geometry(f'500x250+{x}+{y}')
        
        # Title
        tk.Label(
            self.running_dialog, 
            text="Optimization Running...", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        ).pack(pady=(20, 10))
        
        # Calculate total iterations
        if inputs:
            n_dport = len(inputs['Dport_Dt_range'])
            n_dinj = len(inputs['Dinj_Dt_range'])
            n_lc = len(inputs['Lc_Dt_range'])
            total = n_dport * n_dinj * n_lc
            total_text = f"Total iterations: {total} ({n_dport} x {n_dinj} x {n_lc})"
        else:
            total_text = "Calculating..."
        
        tk.Label(
            self.running_dialog, 
            text=total_text, 
            font=FONTS['small'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        ).pack(pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.running_dialog,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode='determinate'
        )
        self.progress_bar.pack(pady=15)
        
        # Progress label
        self.progress_label = tk.Label(
            self.running_dialog, 
            text="0 / 0 (0.0%)", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        self.progress_label.pack(pady=5)
        
        # Current calculation label
        self.current_calc_label = tk.Label(
            self.running_dialog, 
            text="Initializing...", 
            font=FONTS['small'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        self.current_calc_label.pack(pady=5)
        
        # Estimated time label
        self.time_label = tk.Label(
            self.running_dialog, 
            text="", 
            font=FONTS['small'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        self.time_label.pack(pady=5)
        
        # Stop button
        self.stop_button = tk.Button(
            self.running_dialog,
            text="⏹ Stop Optimization",
            font=FONTS['button'],
            bg='#f44336',  # Red
            fg='white',
            command=self._stop_optimization,
            cursor='hand2',
            padx=20,
            pady=8
        )
        self.stop_button.pack(pady=10)
        
        # Store start time for ETA calculation
        import time
        self.optimization_start_time = time.time()
        
        # Prevent closing via X button (use Stop button instead)
        self.running_dialog.protocol("WM_DELETE_WINDOW", self._stop_optimization)
    
    def on_optimization_progress(self, current: int, total: int, message: str):
        """Handle progress updates from optimization - called from worker thread"""
        # Schedule UI update on main thread
        self.root.after(0, self._update_progress_ui, current, total, message)
    
    def _update_progress_ui(self, current: int, total: int, message: str):
        """Update progress UI on main thread"""
        if not hasattr(self, 'running_dialog') or not self.running_dialog.winfo_exists():
            return
        
        import time
        
        # Update progress bar
        percent = (current / total) * 100 if total > 0 else 0
        self.progress_var.set(percent)
        
        # Update progress text
        self.progress_label.config(text=f"{current} / {total} ({percent:.1f}%)")
        
        # Update current calculation
        self.current_calc_label.config(text=message)
        
        # Calculate ETA
        if current > 0:
            elapsed = time.time() - self.optimization_start_time
            rate = current / elapsed  # iterations per second
            remaining = total - current
            eta_seconds = remaining / rate if rate > 0 else 0
            
            if eta_seconds > 60:
                eta_text = f"ETA: {eta_seconds/60:.1f} minutes"
            else:
                eta_text = f"ETA: {eta_seconds:.0f} seconds"
            
            self.time_label.config(text=f"Elapsed: {elapsed:.1f}s | {eta_text}")
        
        # Force UI update
        self.running_dialog.update_idletasks()
    
    def _stop_optimization(self):
        """Stop the running optimization"""
        if hasattr(self, 'optimization_runner') and self.optimization_runner:
            self.optimization_runner.request_cancel()
            
            # Update UI to show stopping
            if hasattr(self, 'stop_button'):
                self.stop_button.config(text="Stopping...", state=tk.DISABLED)
            if hasattr(self, 'current_calc_label'):
                self.current_calc_label.config(text="Cancelling optimization...")
    
    def close_running_dialog(self):
        """Close the running dialog"""
        if hasattr(self, 'running_dialog'):
            self.running_dialog.destroy()
    
    def on_optimization_success(self, results):
        """Handle successful optimization completion"""
        self.root.after(0, self._on_optimization_success_ui, results)
    
    def _on_optimization_success_ui(self, results):
        """UI thread handler for optimization success"""
        self.close_running_dialog()
        
        # Store results in controller
        self.controller.results = results
        
        # Navigate to Optimization Output page and display results
        self.show_optimization_output_page()
        
        # Show success message
        messagebox.showinfo(
            "Optimization Complete", 
            "Optimization completed successfully!\n\n"
            "Results are now displayed in the Optimization Output page."
        )
    
    def on_optimization_error(self, error_message):
        """Handle optimization error"""
        self.root.after(0, self._on_optimization_error_ui, error_message)
    
    def _on_optimization_error_ui(self, error_message):
        """UI thread handler for optimization error"""
        self.close_running_dialog()
        
        # Check if it was a cancellation
        if "CANCELLED" in error_message:
            messagebox.showinfo(
                "Optimization Stopped", 
                "Optimization was stopped by user."
            )
        else:
            messagebox.showerror(
                "Optimization Error", 
                f"An error occurred during optimization:\n\n{error_message}"
            )
    
    def show_results_popup(self, results):
        """Show results in a popup window"""
        import numpy as np
        
        popup = tk.Toplevel(self.root)
        popup.title("Optimization Results")
        popup.geometry("800x600")
        popup.configure(bg=COLORS['bg_medium'])
        popup.transient(self.root)
        
        # Title
        tk.Label(
            popup, 
            text="Optimization Results", 
            font=FONTS['header'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        ).pack(pady=20)
        
        # Create scrollable text area
        frame = tk.Frame(popup, bg=COLORS['bg_medium'])
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_area = tk.Text(
            frame, 
            yscrollcommand=scrollbar.set, 
            font=('Courier', 10), 
            bg='white', 
            fg='black'
        )
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_area.yview)
        
        # Format and display results
        text_area.insert(tk.END, "=" * 80 + "\n")
        text_area.insert(tk.END, "OPTIMIZATION RESULTS\n")
        text_area.insert(tk.END, "=" * 80 + "\n\n")
        
        for key, value in results.items():
            if isinstance(value, np.ndarray):
                text_area.insert(tk.END, f"{key}:\n")
                text_area.insert(tk.END, f"  Shape: {value.shape}\n")
                text_area.insert(tk.END, f"  Min: {np.min(value):.6e}\n")
                text_area.insert(tk.END, f"  Max: {np.max(value):.6e}\n")
                text_area.insert(tk.END, f"  Mean: {np.mean(value):.6e}\n")
                text_area.insert(tk.END, "\n")
            else:
                text_area.insert(tk.END, f"{key}: {value}\n\n")
        
        text_area.config(state=tk.DISABLED)
        
        # Close button
        tk.Button(
            popup, 
            text="Close",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=popup.destroy,
            cursor='hand2',
            padx=15,
            pady=8
        ).pack(pady=20)
