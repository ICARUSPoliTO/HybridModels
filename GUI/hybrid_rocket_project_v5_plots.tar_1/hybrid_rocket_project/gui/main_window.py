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
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.current_page_obj = None
    
    def show_configuration_page(self):
        """Display configuration page"""
        self.current_page = 'configuration'
        self.clear_content()
        
        # Create page-specific frame
        page_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        page_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create configuration page with managers
        self.current_page_obj = create_configuration_page(
            page_frame, 
            self.inputs, 
            self.dropdowns,
            self.reactant_manager,
            self.popup_manager
        )
        
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
    
    def show_mission_page(self):
        """Display mission page"""
        self.current_page = 'mission'
        self.clear_content()
        
        # Create page-specific frame
        page_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        page_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create mission page
        self.current_page_obj = create_mission_page(page_frame, self.inputs)
        
        # Add action buttons (for future save/load functionality)
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
        
        # If we have results stored, display them
        if self.controller.results is not None:
            self.current_page_obj.display_results(self.controller.results)
    
    def show_mission_output_page(self):
        """Display mission output page"""
        self.current_page = 'mission_output'
        self.clear_content()
        
        # Create page-specific frame
        page_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        page_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create mission output page
        self.current_page_obj = create_mission_output_page(page_frame)
        
        # No action buttons needed for now
    
    def create_configuration_buttons(self):
        """Create action buttons for configuration page"""
        button_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        button_frame.pack(side=tk.BOTTOM, pady=20)
        
        # Save button
        tk.Button(
            button_frame, 
            text="Save Configuration",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.save_configuration,
            cursor='hand2',
            padx=15,
            pady=8
        ).grid(row=0, column=0, padx=10)
        
        # Load button
        tk.Button(
            button_frame, 
            text="Load Configuration",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.load_configuration,
            cursor='hand2',
            padx=15,
            pady=8
        ).grid(row=0, column=1, padx=10)
        
        # Send to optimization button
        tk.Button(
            button_frame, 
            text="Send to Optimization",
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
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.run_optimization,
            cursor='hand2',
            padx=15,
            pady=8
        ).grid(row=0, column=2, padx=10)
    
    def create_mission_buttons(self):
        """Create action buttons for mission page"""
        button_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        button_frame.pack(side=tk.BOTTOM, pady=20)
        
        # Placeholder buttons for future functionality
        tk.Label(
            button_frame,
            text="Mission page controls coming soon...",
            font=FONTS['label'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_color']
        ).pack(pady=10)
    
    # ==================================================================
    # DATA COLLECTION METHODS
    # ==================================================================
    
    def collect_configuration_data(self):
        """Collect all configuration data from inputs"""
        inputs = {}
        for key, entry in self.inputs.items():
            if not key.startswith("Optimization_"):
                value = entry.get().strip()
                if value:
                    inputs[key] = value
        
        dropdowns = {}
        for key, combo in self.dropdowns.items():
            value = combo.get()
            if value:
                dropdowns[key] = value
        
        # Get fuel data if page object exists
        selected_fuels = []
        fuel_weights = {}
        if self.current_page_obj and hasattr(self.current_page_obj, 'get_fuel_data'):
            selected_fuels, fuel_weights = self.current_page_obj.get_fuel_data()
        
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
        
        return data
    
    # ==================================================================
    # ACTION METHODS
    # ==================================================================
    
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
        
        # Show running dialog
        self.show_running_dialog()
        
        # Create and start optimization runner
        runner = OptimizationRunner(
            callback_success=self.on_optimization_success,
            callback_error=self.on_optimization_error
        )
        
        success, msg = runner.start(inputs)
        if not success:
            self.close_running_dialog()
            messagebox.showerror("Error", msg)
    
    # ==================================================================
    # DIALOG AND RESULT HANDLING
    # ==================================================================
    
    def show_running_dialog(self):
        """Show 'Running...' dialog"""
        self.running_dialog = tk.Toplevel(self.root)
        self.running_dialog.title("Running Optimization")
        self.running_dialog.geometry("300x150")
        self.running_dialog.configure(bg=COLORS['bg_medium'])
        self.running_dialog.transient(self.root)
        self.running_dialog.grab_set()
        
        # Center on screen
        self.running_dialog.update_idletasks()
        x = (self.running_dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.running_dialog.winfo_screenheight() // 2) - (150 // 2)
        self.running_dialog.geometry(f'300x150+{x}+{y}')
        
        # Message
        tk.Label(
            self.running_dialog, 
            text="Optimization Running...", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        ).pack(pady=30)
        
        tk.Label(
            self.running_dialog, 
            text="Please wait. This may take several minutes.", 
            font=FONTS['small'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        ).pack(pady=10)
        
        # Prevent closing
        self.running_dialog.protocol("WM_DELETE_WINDOW", lambda: None)
    
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
