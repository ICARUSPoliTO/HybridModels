"""
Mission Page - Mission parameters and simulation settings

Contains fields for:
- Grain geometry (preset shapes)
- Tank configuration
- Chamber and nozzle parameters
- Mission timing
- Optimal design point from optimization
"""

import tkinter as tk
from tkinter import ttk
from config.constants import COLORS, FONTS
from gui.components.input_field import create_input_field


# Default values for mission parameters
MISSION_DEFAULTS = {
    # Timing
    'burn_time': '10.0',
    'delay_time': '0.0',
    
    # Chamber geometry
    'D_chamber': '0.1',
    'Dt': '0.03',
    'n_injectors': '4',
    'Vol_prechamber': '0.0',
    'Vol_postchamber': '0.0',
    
    # Tank
    'mtank': '5.0',
    'Q_vapor': '0.05',
    'ppress': '200',
    
    # Efficiencies
    'rend_cstar': '0.95',
    'rend_CF': '0.95',
    
    # Grain geometry parameters
    'grain_n_sides': '6',
    'grain_inner_radius': '0.02',
    'grain_outer_radius': '0.04',
    'grain_pitch': '0.0',
    
    # Optimal design point
    'Dport_Dt_optimal': '2.0',
    'Dinj_Dt_optimal': '0.2',
    'Lc_Dt_optimal': '3.0',
}

GRAIN_PRESETS = [
    'Cylindrical',
    'Star (6 points)',
    'Star (8 points)', 
    'Wagon Wheel',
    'Custom Polygon',
]

TANK_TYPES = [
    'Self-pressurizing',
    'Pressurized gas',
    'Constant pressure',
]


class MissionPage:
    """Mission page for mission parameters and simulation settings"""
    
    def __init__(self, parent, inputs_dict: dict, dropdowns_dict: dict = None):
        self.parent = parent
        self.inputs = inputs_dict
        self.dropdowns = dropdowns_dict if dropdowns_dict else {}
        
        # Initialize variables
        self.grain_preset_var = None
        self.tank_type_var = None
        self.circular_var = None
        self.pressurant_var = None
        self.pressurant_frame = None
        
        self.create_page()
    
    def create_page(self):
        """Create the mission page content"""
        # Title
        title = tk.Label(
            self.parent, 
            text="Mission Parameters", 
            font=FONTS['title'],
            bg=COLORS['bg_dark'], 
            fg=COLORS['text_color']
        )
        title.pack(pady=20)
        
        # Create canvas with scrollbar
        container = tk.Frame(self.parent, bg=COLORS['bg_dark'])
        container.pack(fill=tk.BOTH, expand=True, padx=20)
        
        canvas = tk.Canvas(container, bg=COLORS['bg_dark'], highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # Create scrollable frame
        self.scrollable_frame = tk.Frame(canvas, bg=COLORS['bg_dark'])
        
        # Configure canvas window
        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure scroll region when frame changes
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Also update canvas window width
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        
        self.scrollable_frame.bind("<Configure>", configure_scroll)
        
        # Update canvas window width when canvas resizes
        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", configure_canvas)
        
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
        
        # Pack canvas and scrollbar
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Now create all sections in the scrollable frame
        self.create_optimal_design_section(self.scrollable_frame)
        self.create_timing_section(self.scrollable_frame)
        self.create_chamber_section(self.scrollable_frame)
        self.create_grain_section(self.scrollable_frame)
        self.create_tank_section(self.scrollable_frame)
        self.create_efficiency_section(self.scrollable_frame)
        
        # Force update to ensure everything is visible
        self.scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Debug: Print what was created
        print(f"Mission page created: {len(self.inputs)} input fields, {len(self.dropdowns)} dropdowns")
    
    def create_optimal_design_section(self, parent):
        """Create section for optimal design point from optimization"""
        section = tk.LabelFrame(
            parent, 
            text="Optimal Design Point (from Optimization)", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, padx=10, pady=10)
        
        # Info label
        info = tk.Label(
            section,
            text="Enter the optimal dimensionless ratios from the optimization results:",
            font=FONTS['label'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_muted']
        )
        info.grid(row=0, column=0, columnspan=4, pady=(10, 10), sticky='w', padx=10)
        
        # Optimal ratios
        create_input_field(section, "Mission_Dport_Dt_optimal", "Dport/Dt optimal:",
                          self.inputs, default=MISSION_DEFAULTS['Dport_Dt_optimal'], row=1, col=0)
        create_input_field(section, "Mission_Dinj_Dt_optimal", "Dinj/Dt optimal:",
                          self.inputs, default=MISSION_DEFAULTS['Dinj_Dt_optimal'], row=1, col=2)
        create_input_field(section, "Mission_Lc_Dt_optimal", "Lc/Dt optimal:",
                          self.inputs, default=MISSION_DEFAULTS['Lc_Dt_optimal'], row=2, col=0)
        
        # Add padding at bottom
        tk.Frame(section, height=10, bg=COLORS['bg_medium']).grid(row=3, column=0, columnspan=4)
    
    def create_timing_section(self, parent):
        """Create timing parameters section"""
        section = tk.LabelFrame(
            parent, 
            text="Mission Timing", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, padx=10, pady=10)
        
        create_input_field(section, "Mission_burn_time", "Burn Time [s]:",
                          self.inputs, default=MISSION_DEFAULTS['burn_time'], row=0, col=0)
        create_input_field(section, "Mission_delay_time", "Ignition Delay [s]:",
                          self.inputs, default=MISSION_DEFAULTS['delay_time'], row=0, col=2)
        
        tk.Frame(section, height=10, bg=COLORS['bg_medium']).grid(row=1, column=0, columnspan=4)
    
    def create_chamber_section(self, parent):
        """Create chamber and nozzle geometry section"""
        section = tk.LabelFrame(
            parent, 
            text="Chamber & Nozzle Geometry", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, padx=10, pady=10)
        
        create_input_field(section, "Mission_D_chamber", "Chamber Diameter [m]:",
                          self.inputs, default=MISSION_DEFAULTS['D_chamber'], row=0, col=0)
        create_input_field(section, "Mission_Dt", "Throat Diameter [m]:",
                          self.inputs, default=MISSION_DEFAULTS['Dt'], row=0, col=2)
        create_input_field(section, "Mission_n_injectors", "Number of Injectors:",
                          self.inputs, default=MISSION_DEFAULTS['n_injectors'], row=1, col=0)
        create_input_field(section, "Mission_Vol_prechamber", "Pre-chamber Vol [m³]:",
                          self.inputs, default=MISSION_DEFAULTS['Vol_prechamber'], row=1, col=2)
        create_input_field(section, "Mission_Vol_postchamber", "Post-chamber Vol [m³]:",
                          self.inputs, default=MISSION_DEFAULTS['Vol_postchamber'], row=2, col=0)
        
        tk.Frame(section, height=10, bg=COLORS['bg_medium']).grid(row=3, column=0, columnspan=4)
    
    def create_grain_section(self, parent):
        """Create grain geometry section"""
        section = tk.LabelFrame(
            parent, 
            text="Grain Geometry", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, padx=10, pady=10)
        
        # Grain preset dropdown
        row0 = tk.Frame(section, bg=COLORS['bg_medium'])
        row0.grid(row=0, column=0, columnspan=4, pady=10, padx=10, sticky='w')
        
        tk.Label(
            row0,
            text="Grain Shape:",
            font=FONTS['label'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color']
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.grain_preset_var = tk.StringVar(value=GRAIN_PRESETS[0])
        grain_combo = ttk.Combobox(
            row0,
            textvariable=self.grain_preset_var,
            values=GRAIN_PRESETS,
            state='readonly',
            width=20
        )
        grain_combo.pack(side=tk.LEFT)
        grain_combo.bind('<<ComboboxSelected>>', self._on_grain_preset_change)
        self.dropdowns['Mission_grain_preset'] = grain_combo
        
        # Grain parameters
        create_input_field(section, "Mission_grain_n_sides", "Number of Sides/Points:",
                          self.inputs, default=MISSION_DEFAULTS['grain_n_sides'], row=1, col=0)
        create_input_field(section, "Mission_grain_inner_radius", "Inner Radius [m]:",
                          self.inputs, default=MISSION_DEFAULTS['grain_inner_radius'], row=1, col=2)
        create_input_field(section, "Mission_grain_outer_radius", "Outer Radius [m]:",
                          self.inputs, default=MISSION_DEFAULTS['grain_outer_radius'], row=2, col=0)
        create_input_field(section, "Mission_grain_pitch", "Helix Pitch [m] (0=none):",
                          self.inputs, default=MISSION_DEFAULTS['grain_pitch'], row=2, col=2)
        
        # Circular checkbox
        self.circular_var = tk.BooleanVar(value=False)
        circular_check = tk.Checkbutton(
            section,
            text="Circular grain (use arc interpolation)",
            variable=self.circular_var,
            font=FONTS['label'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            selectcolor=COLORS['bg_dark'],
            activebackground=COLORS['bg_medium'],
            activeforeground=COLORS['text_color']
        )
        circular_check.grid(row=3, column=0, columnspan=2, pady=10, padx=10, sticky='w')
        
        tk.Frame(section, height=10, bg=COLORS['bg_medium']).grid(row=4, column=0, columnspan=4)
    
    def create_tank_section(self, parent):
        """Create tank configuration section"""
        section = tk.LabelFrame(
            parent, 
            text="Tank Configuration", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, padx=10, pady=10)
        
        # Tank type dropdown
        row0 = tk.Frame(section, bg=COLORS['bg_medium'])
        row0.grid(row=0, column=0, columnspan=4, pady=10, padx=10, sticky='w')
        
        tk.Label(
            row0,
            text="Tank Type:",
            font=FONTS['label'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color']
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.tank_type_var = tk.StringVar(value=TANK_TYPES[0])
        tank_combo = ttk.Combobox(
            row0,
            textvariable=self.tank_type_var,
            values=TANK_TYPES,
            state='readonly',
            width=20
        )
        tank_combo.pack(side=tk.LEFT)
        tank_combo.bind('<<ComboboxSelected>>', self._on_tank_type_change)
        self.dropdowns['Mission_tank_type'] = tank_combo
        
        # Tank parameters
        create_input_field(section, "Mission_mtank", "Oxidizer Mass [kg]:",
                          self.inputs, default=MISSION_DEFAULTS['mtank'], row=1, col=0)
        create_input_field(section, "Mission_Q_vapor", "Vapor Quality (0-1):",
                          self.inputs, default=MISSION_DEFAULTS['Q_vapor'], row=1, col=2)
        
        # Pressurant frame (shown only for constant pressure tank)
        self.pressurant_frame = tk.Frame(section, bg=COLORS['bg_medium'])
        self.pressurant_frame.grid(row=2, column=0, columnspan=4, pady=5, padx=5, sticky='w')
        
        create_input_field(self.pressurant_frame, "Mission_ppress", "Pressurant Pressure [bar]:",
                          self.inputs, default=MISSION_DEFAULTS['ppress'], row=0, col=0)
        
        # Pressurant dropdown
        tk.Label(
            self.pressurant_frame,
            text="Pressurant:",
            font=FONTS['label'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color']
        ).grid(row=0, column=2, padx=10, sticky='e')
        
        self.pressurant_var = tk.StringVar(value="Helium")
        pressurant_combo = ttk.Combobox(
            self.pressurant_frame,
            textvariable=self.pressurant_var,
            values=["Helium", "Nitrogen", "Argon"],
            state='readonly',
            width=15
        )
        pressurant_combo.grid(row=0, column=3, padx=5)
        self.dropdowns['Mission_pressurant'] = pressurant_combo
        
        # Hide pressurant frame initially
        self.pressurant_frame.grid_remove()
        
        tk.Frame(section, height=10, bg=COLORS['bg_medium']).grid(row=3, column=0, columnspan=4)
    
    def create_efficiency_section(self, parent):
        """Create efficiency parameters section"""
        section = tk.LabelFrame(
            parent, 
            text="Performance Efficiencies", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, padx=10, pady=10)
        
        create_input_field(section, "Mission_rend_cstar", "c* Efficiency (η_c*):",
                          self.inputs, default=MISSION_DEFAULTS['rend_cstar'], row=0, col=0)
        create_input_field(section, "Mission_rend_CF", "CF Efficiency (η_CF):",
                          self.inputs, default=MISSION_DEFAULTS['rend_CF'], row=0, col=2)
        
        tk.Frame(section, height=10, bg=COLORS['bg_medium']).grid(row=1, column=0, columnspan=4)
    
    def _on_grain_preset_change(self, event=None):
        """Handle grain preset change"""
        preset = self.grain_preset_var.get()
        
        if preset == 'Cylindrical':
            if 'Mission_grain_n_sides' in self.inputs:
                self.inputs['Mission_grain_n_sides'].delete(0, tk.END)
                self.inputs['Mission_grain_n_sides'].insert(0, '1')
            self.circular_var.set(True)
        elif 'Star (6' in preset:
            if 'Mission_grain_n_sides' in self.inputs:
                self.inputs['Mission_grain_n_sides'].delete(0, tk.END)
                self.inputs['Mission_grain_n_sides'].insert(0, '6')
            self.circular_var.set(False)
        elif 'Star (8' in preset:
            if 'Mission_grain_n_sides' in self.inputs:
                self.inputs['Mission_grain_n_sides'].delete(0, tk.END)
                self.inputs['Mission_grain_n_sides'].insert(0, '8')
            self.circular_var.set(False)
        elif preset == 'Wagon Wheel':
            if 'Mission_grain_n_sides' in self.inputs:
                self.inputs['Mission_grain_n_sides'].delete(0, tk.END)
                self.inputs['Mission_grain_n_sides'].insert(0, '8')
            self.circular_var.set(True)
    
    def _on_tank_type_change(self, event=None):
        """Handle tank type change"""
        tank_type = self.tank_type_var.get()
        
        if tank_type == 'Constant pressure':
            self.pressurant_frame.grid()
        else:
            self.pressurant_frame.grid_remove()
    
    def get_mission_data(self):
        """Collect all mission page data"""
        def safe_get(key, default):
            try:
                entry = self.inputs.get(key)
                if entry and hasattr(entry, 'get'):
                    val = entry.get().strip()
                    return val if val else default
            except:
                pass
            return default
        
        data = {
            # Optimal design point
            'Dport_Dt_optimal': float(safe_get('Mission_Dport_Dt_optimal', MISSION_DEFAULTS['Dport_Dt_optimal'])),
            'Dinj_Dt_optimal': float(safe_get('Mission_Dinj_Dt_optimal', MISSION_DEFAULTS['Dinj_Dt_optimal'])),
            'Lc_Dt_optimal': float(safe_get('Mission_Lc_Dt_optimal', MISSION_DEFAULTS['Lc_Dt_optimal'])),
            
            # Timing
            'burn_time': float(safe_get('Mission_burn_time', MISSION_DEFAULTS['burn_time'])),
            'delay_time': float(safe_get('Mission_delay_time', MISSION_DEFAULTS['delay_time'])),
            
            # Chamber
            'D_chamber': float(safe_get('Mission_D_chamber', MISSION_DEFAULTS['D_chamber'])),
            'Dt': float(safe_get('Mission_Dt', MISSION_DEFAULTS['Dt'])),
            'n_injectors': int(float(safe_get('Mission_n_injectors', MISSION_DEFAULTS['n_injectors']))),
            'Vol_prechamber': float(safe_get('Mission_Vol_prechamber', MISSION_DEFAULTS['Vol_prechamber'])),
            'Vol_postchamber': float(safe_get('Mission_Vol_postchamber', MISSION_DEFAULTS['Vol_postchamber'])),
            
            # Grain
            'grain_preset': self.grain_preset_var.get() if self.grain_preset_var else GRAIN_PRESETS[0],
            'grain_n_sides': int(float(safe_get('Mission_grain_n_sides', MISSION_DEFAULTS['grain_n_sides']))),
            'grain_inner_radius': float(safe_get('Mission_grain_inner_radius', MISSION_DEFAULTS['grain_inner_radius'])),
            'grain_outer_radius': float(safe_get('Mission_grain_outer_radius', MISSION_DEFAULTS['grain_outer_radius'])),
            'grain_pitch': float(safe_get('Mission_grain_pitch', MISSION_DEFAULTS['grain_pitch'])),
            'circular': self.circular_var.get() if self.circular_var else False,
            
            # Tank
            'tank_type': self.tank_type_var.get() if self.tank_type_var else TANK_TYPES[0],
            'mtank': float(safe_get('Mission_mtank', MISSION_DEFAULTS['mtank'])),
            'Q_vapor': float(safe_get('Mission_Q_vapor', MISSION_DEFAULTS['Q_vapor'])),
            'ppress': float(safe_get('Mission_ppress', MISSION_DEFAULTS['ppress'])) * 1e5,
            'pressurant': self.pressurant_var.get() if self.pressurant_var else "Helium",
            
            # Efficiencies
            'rend_cstar': float(safe_get('Mission_rend_cstar', MISSION_DEFAULTS['rend_cstar'])),
            'rend_CF': float(safe_get('Mission_rend_CF', MISSION_DEFAULTS['rend_CF'])),
        }
        return data


def create_mission_page(parent, inputs_dict, dropdowns_dict=None):
    """Factory function to create mission page"""
    return MissionPage(parent, inputs_dict, dropdowns_dict)
