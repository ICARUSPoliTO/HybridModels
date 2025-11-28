"""
Optimization Page - Parameter ranges and operating conditions

Contains fields for defining optimization parameter ranges and running simulations.
"""

import tkinter as tk
from tkinter import ttk
from config.constants import COLORS, FONTS
from gui.components.input_field import create_input_field


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
        
        # Parameter ranges section
        self.create_parameter_ranges_section(main_frame)
        
        # Operating conditions section
        self.create_operating_conditions_section(main_frame)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_parameter_ranges_section(self, parent):
        """Create parameter ranges input section"""
        section = tk.LabelFrame(
            parent, 
            text="Parameter Ranges", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, pady=10)
        
        # Number of points
        create_input_field(section, "Optimization_parameter_points", 
                          "Number of points:", self.inputs, default="10", row=0)
        
        # Dport-Dt range
        create_input_field(section, "Optimization_Dport_Dt_min", 
                          "Dport-Dt.min:", self.inputs, default="2.3", row=1)
        create_input_field(section, "Optimization_Dport_Dt_max", 
                          "Dport-Dt.max:", self.inputs, default="5.0", row=2)
        
        # Dinj-Dt range
        create_input_field(section, "Optimization_Dinj_Dt_min", 
                          "Dinj-Dt.min:", self.inputs, default="0.8", row=3)
        create_input_field(section, "Optimization_Dinj_Dt_max", 
                          "Dinj-Dt.max:", self.inputs, default="1.0", row=4)
        
        # Lc-Dt range
        create_input_field(section, "Optimization_Lc_Dt_min", 
                          "Lc-Dt.min:", self.inputs, default="8", row=5)
        create_input_field(section, "Optimization_Lc_Dt_max", 
                          "Lc-Dt.max:", self.inputs, default="10", row=6)
    
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
                          "Tank Pressure [Pa]:", self.inputs, default="5500000", row=0)
        create_input_field(section, "Optimization_Ttank", 
                          "Tank Temperature [K]:", self.inputs, default="288", row=1)
        create_input_field(section, "Optimization_pamb", 
                          "Ambient Pressure [Pa]:", self.inputs, default="100000", row=2)


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
