# sections/optimization_section.py

import tkinter as tk
from config import COLORS, FONTS


class OptimizationSection:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.app = main_app
        self.colors = COLORS
        self.fonts = FONTS
    
    def create(self):
        section = tk.Frame(self.parent, bg=self.colors['bg_light'], relief=tk.RIDGE, bd=2)
        section.pack(fill=tk.X, pady=10, ipady=15)
        
        header_frame = tk.Frame(section, bg=self.colors['bg_light'])
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
        
        section_title = tk.Label(header_frame, text="Optimization", font=self.fonts['section'],
                                 bg=self.colors['bg_light'], fg='black')
        section_title.pack(side=tk.LEFT)
        
        fields_frame = tk.Frame(section, bg=self.colors['bg_light'])
        fields_frame.pack(fill=tk.X, padx=40, pady=10)
        
        # Create all fields
        self.create_int_field(fields_frame, "Optimization", "parameter_points",
                              "parameter_points", min_value=0, exclusive=True)
        self.create_float_field(fields_frame, "Optimization", "Dport-Dt.min",
                                "Dport-Dt.min", min_value=0, exclusive=True)
        self.create_float_field(fields_frame, "Optimization", "Dport-Dt.max",
                                "Dport-Dt.max", min_value=0, exclusive=True)
        self.create_float_field(fields_frame, "Optimization", "Dinj-Dt.min",
                                "Dinj-Dt.min", min_value=0, exclusive=True)
        self.create_float_field(fields_frame, "Optimization", "Dinj-Dt.max",
                                "Dinj-Dt.max", min_value=0, exclusive=True)
        self.create_float_field(fields_frame, "Optimization", "Lc-Dt.min",
                                "Lc-Dt.min", min_value=0, exclusive=True)
        self.create_float_field(fields_frame, "Optimization", "Lc-Dt.max",
                                "Lc-Dt.max", min_value=0, exclusive=True)
        self.create_float_field(fields_frame, "Optimization", "ptank",
                                "(Ptank) ptank [Pa]", min_value=0, exclusive=True)
        self.create_float_field(fields_frame, "Optimization", "Ttank",
                                "(Ttank) Ttank [K]", min_value=0, exclusive=True)
        self.create_float_field(fields_frame, "Optimization", "pamb",
                                "(Pamb) pamb [Pa]", min_value=0, exclusive=True)
    
    def create_float_field(self, parent, section, var_name, display_name, min_value=None,
                           max_value=None, exclusive=False):
        row = tk.Frame(parent, bg=self.colors['bg_light'])
        row.pack(fill=tk.X, pady=5)
        
        label = tk.Label(row, text=display_name + ":", font=self.fonts['normal'],
                         bg=self.colors['bg_light'], fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        entry = tk.Entry(row, font=self.fonts['normal'], width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.colors['bg_light'],
                         highlightcolor=self.colors['bg_light'])
        entry.pack(side=tk.LEFT)
        
        entry.validation_params = {
            'min_value': min_value,
            'max_value': max_value,
            'exclusive': exclusive
        }
        
        entry.bind('<KeyRelease>', lambda e: self.app.validate_single_input(entry))
        
        self.app.inputs[f"{section}_{var_name}"] = entry
    
    def create_int_field(self, parent, section, var_name, display_name, min_value=None,
                         max_value=None, exclusive=False):
        row = tk.Frame(parent, bg=self.colors['bg_light'])
        row.pack(fill=tk.X, pady=5)
        
        label = tk.Label(row, text=display_name + ":", font=self.fonts['normal'],
                         bg=self.colors['bg_light'], fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        entry = tk.Entry(row, font=self.fonts['normal'], width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.colors['bg_light'],
                         highlightcolor=self.colors['bg_light'])
        entry.pack(side=tk.LEFT)
        
        entry.validation_params = {
            'min_value': min_value,
            'max_value': max_value,
            'exclusive': exclusive,
            'is_int': True
        }
        
        entry.bind('<KeyRelease>', lambda e: self.app.validate_single_input(entry))
        
        self.app.inputs[f"{section}_{var_name}"] = entry