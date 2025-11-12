# sections/nozzle_section.py

import tkinter as tk
from config import COLORS, FONTS


class NozzleSection:
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
        
        section_title = tk.Label(header_frame, text="Nozzle", font=self.fonts['section'],
                                 bg=self.colors['bg_light'], fg='black')
        section_title.pack(side=tk.LEFT)
        
        fields_frame = tk.Frame(section, bg=self.colors['bg_light'])
        fields_frame.pack(fill=tk.X, padx=40, pady=10)
        
        self.create_epsilon_field(fields_frame)
    
    def create_epsilon_field(self, parent):
        row = tk.Frame(parent, bg=self.colors['bg_light'])
        row.pack(fill=tk.X, pady=5)
        
        label = tk.Label(row, text="(ε) eps:", font=self.fonts['normal'],
                         bg=self.colors['bg_light'], fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        entry = tk.Entry(row, font=self.fonts['normal'], width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.colors['bg_light'],
                         highlightcolor=self.colors['bg_light'])
        entry.pack(side=tk.LEFT)
        entry.bind('<KeyRelease>', lambda e: self.validate_epsilon())
        
        self.app.inputs["Nozzle_epsilon"] = entry
    
    def validate_epsilon(self):
        entry = self.app.inputs["Nozzle_epsilon"]
        value = entry.get().strip()
        
        is_valid = False
        if value:
            if value.lower() == "adapt":
                is_valid = True
            else:
                try:
                    float_val = float(value)
                    if float_val > 1:
                        is_valid = True
                except ValueError:
                    pass
        
        if is_valid:
            entry.configure(highlightbackground='#00aa00', highlightcolor='#00aa00')
        else:
            entry.configure(highlightbackground='red', highlightcolor='red')
        
        self.app.validate_inputs()