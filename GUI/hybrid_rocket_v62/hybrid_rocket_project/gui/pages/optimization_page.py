"""
Optimization Page - Parameter ranges and operating conditions

Contains fields for defining optimization parameter ranges and running simulations.
"""

import tkinter as tk
from tkinter import ttk
from config.constants import COLORS, FONTS
from gui.components.input_field import create_input_field


# Reasonable default values based on typical hybrid rocket configurations
# Reference: optimization.py uses these ranges:
#   Dport_Dt_range = np.arange(1.25, 3.5, 0.25)  -> port diameter 1.25-3.5x throat
#   Dinj_Dt_range = np.arange(0.01, 0.8, 0.01)   -> injector diameter 0.01-0.8x throat  
#   Lc_Dt_range = np.arange(1.5, 5, 0.5)         -> chamber length 1.5-5x throat

DEFAULT_VALUES = {
    'Dport_Dt_min': '1.5',      # Port diameter / Throat diameter minimum
    'Dport_Dt_max': '3.0',      # Port diameter / Throat diameter maximum
    'Dinj_Dt_min': '0.1',       # Injector diameter / Throat diameter minimum
    'Dinj_Dt_max': '0.5',       # Injector diameter / Throat diameter maximum
    'Lc_Dt_min': '2.0',         # Chamber length / Throat diameter minimum
    'Lc_Dt_max': '4.0',         # Chamber length / Throat diameter maximum
    'ptank': '2700000',         # Tank pressure [Pa] = 27 bar (typical N2O)
    'Ttank': '288',             # Tank temperature [K] = 15°C
    'pamb': '101325',           # Ambient pressure [Pa] = 1 atm
}

# Preset configurations for number of points
ITERATION_PRESETS = {
    'Quick Test (3³=27)': 3,
    'Fast (5³=125)': 5,
    'Medium (8³=512)': 8,
    'Standard (10³=1000)': 10,
    'Detailed (15³=3375)': 15,
    'High Resolution (20³=8000)': 20,
}


class OptimizationPage:
    """Optimization page for parameter ranges and simulation"""
    
    def __init__(self, parent, inputs_dict: dict):
        """
        Initialize optimization page
        
        Args:
            parent: Parent frame to contain this page
            inputs_dict: Shared dictionary for input fields
        """
        self.parent = parent
        self.inputs = inputs_dict
        
        self.create_page()
    
    def create_page(self):
        """Create the optimization page content"""
        # Title
        title = tk.Label(
            self.parent, 
            text="Optimization Parameters", 
            font=FONTS['title'],
            bg=COLORS['bg_dark'], 
            fg=COLORS['text_color']
        )
        title.pack(pady=20)
        
        # Scrollable frame
        canvas = tk.Canvas(self.parent, bg=COLORS['bg_dark'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        main_frame = tk.Frame(canvas, bg=COLORS['bg_dark'])
        
        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_mousewheel)
        canvas.bind('<Leave>', _unbind_mousewheel)
        
        # Resolution section (number of points)
        self.create_resolution_section(main_frame)
        
        # Parameter ranges section
        self.create_parameter_ranges_section(main_frame)
        
        # Operating conditions section
        self.create_operating_conditions_section(main_frame)
        
        # Info section
        self.create_info_section(main_frame)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_resolution_section(self, parent):
        """Create resolution/iteration selector section"""
        section = tk.LabelFrame(
            parent, 
            text="Simulation Resolution", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, pady=10)
        
        # Preset selector row
        row = tk.Frame(section, bg=COLORS['bg_medium'])
        row.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
        section.grid_columnconfigure(0, weight=1)
        
        tk.Label(
            row, 
            text="Resolution Preset:", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=20,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.preset_var = tk.StringVar(value='Fast (5³=125)')
        preset_combo = ttk.Combobox(
            row,
            textvariable=self.preset_var,
            values=list(ITERATION_PRESETS.keys()),
            state='readonly',
            font=FONTS['label'],
            width=25
        )
        preset_combo.pack(side=tk.LEFT)
        preset_combo.bind('<<ComboboxSelected>>', self.on_preset_change)
        
        # Manual entry row
        row2 = tk.Frame(section, bg=COLORS['bg_medium'])
        row2.grid(row=1, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        tk.Label(
            row2, 
            text="Points per parameter:", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=20,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.points_entry = tk.Entry(row2, font=FONTS['label'], width=10)
        self.points_entry.pack(side=tk.LEFT)
        self.points_entry.insert(0, "5")
        self.inputs["Optimization_parameter_points"] = self.points_entry
        
        # Total iterations label
        self.total_label = tk.Label(
            row2, 
            text="= 125 total iterations", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg='#00ff00'
        )
        self.total_label.pack(side=tk.LEFT, padx=10)
        
        # Bind entry change to update total
        self.points_entry.bind('<KeyRelease>', self.update_total_label)
        
        # Estimated time row
        row3 = tk.Frame(section, bg=COLORS['bg_medium'])
        row3.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=(5, 10))
        
        self.time_estimate_label = tk.Label(
            row3, 
            text="Estimated time: ~1-3 minutes (depends on system)", 
            font=FONTS['small'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        self.time_estimate_label.pack(side=tk.LEFT)
    
    def on_preset_change(self, event=None):
        """Handle preset selection change"""
        preset_name = self.preset_var.get()
        if preset_name in ITERATION_PRESETS:
            points = ITERATION_PRESETS[preset_name]
            self.points_entry.delete(0, tk.END)
            self.points_entry.insert(0, str(points))
            self.update_total_label()
    
    def update_total_label(self, event=None):
        """Update the total iterations label"""
        try:
            points = int(self.points_entry.get())
            total = points ** 3
            self.total_label.config(text=f"= {total:,} total iterations")
            
            # Update color based on total
            if total <= 125:
                self.total_label.config(fg='#00ff00')  # Green
                time_est = "~30 seconds - 2 minutes"
            elif total <= 1000:
                self.total_label.config(fg='#ffff00')  # Yellow
                time_est = "~2-10 minutes"
            elif total <= 5000:
                self.total_label.config(fg='#ff9900')  # Orange
                time_est = "~10-30 minutes"
            else:
                self.total_label.config(fg='#ff0000')  # Red
                time_est = "~30+ minutes (consider reducing)"
            
            self.time_estimate_label.config(text=f"Estimated time: {time_est}")
        except ValueError:
            self.total_label.config(text="= ? (invalid input)", fg='#ff0000')
    
    def create_parameter_ranges_section(self, parent):
        """Create parameter ranges input section"""
        section = tk.LabelFrame(
            parent, 
            text="Parameter Ranges (dimensionless ratios)", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, pady=10)
        
        # Info about parameters
        info_text = ("Dport/Dt = Port diameter / Throat diameter\n"
                    "Dinj/Dt = Injector diameter / Throat diameter (typically small: 0.01-0.5)\n"
                    "Lc/Dt = Chamber length / Throat diameter")
        
        info_label = tk.Label(
            section,
            text=info_text,
            font=FONTS['small'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            justify='left'
        )
        info_label.grid(row=0, column=0, columnspan=2, sticky='w', padx=10, pady=(5, 10))
        
        # Dport-Dt range
        create_input_field(section, "Optimization_Dport_Dt_min", 
                          "Dport/Dt min:", self.inputs, 
                          default=DEFAULT_VALUES['Dport_Dt_min'], row=1)
        create_input_field(section, "Optimization_Dport_Dt_max", 
                          "Dport/Dt max:", self.inputs, 
                          default=DEFAULT_VALUES['Dport_Dt_max'], row=2)
        
        # Dinj-Dt range
        create_input_field(section, "Optimization_Dinj_Dt_min", 
                          "Dinj/Dt min:", self.inputs, 
                          default=DEFAULT_VALUES['Dinj_Dt_min'], row=3)
        create_input_field(section, "Optimization_Dinj_Dt_max", 
                          "Dinj/Dt max:", self.inputs, 
                          default=DEFAULT_VALUES['Dinj_Dt_max'], row=4)
        
        # Lc-Dt range
        create_input_field(section, "Optimization_Lc_Dt_min", 
                          "Lc/Dt min:", self.inputs, 
                          default=DEFAULT_VALUES['Lc_Dt_min'], row=5)
        create_input_field(section, "Optimization_Lc_Dt_max", 
                          "Lc/Dt max:", self.inputs, 
                          default=DEFAULT_VALUES['Lc_Dt_max'], row=6)
    
    def create_operating_conditions_section(self, parent):
        """Create operating conditions input section"""
        section = tk.LabelFrame(
            parent, 
            text="Operating Conditions", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, pady=10)
        
        create_input_field(section, "Optimization_ptank", 
                          "Tank Pressure [Pa]:", self.inputs, 
                          default=DEFAULT_VALUES['ptank'], row=0)
        create_input_field(section, "Optimization_Ttank", 
                          "Tank Temperature [K]:", self.inputs, 
                          default=DEFAULT_VALUES['Ttank'], row=1)
        create_input_field(section, "Optimization_pamb", 
                          "Ambient Pressure [Pa]:", self.inputs, 
                          default=DEFAULT_VALUES['pamb'], row=2)
        
        # Helpful info
        info_frame = tk.Frame(section, bg=COLORS['bg_medium'])
        info_frame.grid(row=3, column=0, columnspan=2, sticky='w', padx=10, pady=10)
        
        info_text = ("Typical values:\n"
                    "  • N2O at 15°C: ptank ≈ 27-50 bar (2.7-5.0 MPa)\n"
                    "  • Sea level: pamb = 101325 Pa\n"
                    "  • Vacuum: pamb = 0 Pa")
        
        tk.Label(
            info_frame,
            text=info_text,
            font=FONTS['small'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            justify='left'
        ).pack(anchor='w')
    
    def create_info_section(self, parent):
        """Create information section with tips"""
        section = tk.LabelFrame(
            parent, 
            text="Tips", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, pady=10)
        
        tips_text = (
            "• Start with 'Fast' resolution (5³=125) to verify your configuration works\n"
            "• If all results are zero, check your Configuration page settings\n"
            "• Common issues: wrong oxidizer CoolProp name, missing fuel formula\n"
            "• Dinj/Dt should be small (0.01-0.5) - the injector is smaller than the throat\n"
            "• Dport/Dt should be larger (1.5-4.0) - the port is larger than the throat"
        )
        
        tk.Label(
            section,
            text=tips_text,
            font=FONTS['small'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            justify='left'
        ).pack(anchor='w', padx=10, pady=10)


# Helper function to create the optimization page
def create_optimization_page(parent, inputs_dict):
    """
    Factory function to create optimization page
    
    Args:
        parent: Parent frame
        inputs_dict: Shared inputs dictionary
        
    Returns:
        OptimizationPage instance
    """
    return OptimizationPage(parent, inputs_dict)
