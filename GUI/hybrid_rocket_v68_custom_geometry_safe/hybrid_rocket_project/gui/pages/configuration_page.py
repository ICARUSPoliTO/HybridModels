"""
Configuration Page - Rocket configuration inputs

Contains all fields for geometry, fuel properties, line losses, and nozzle parameters.
"""

import tkinter as tk
from tkinter import ttk
from config.constants import COLORS, FONTS
from gui.components.input_field import create_input_field


# Mapping CEA oxidizer names to CoolProp names
CEA_TO_COOLPROP_OXIDIZER = {
    "N2O": "NitrousOxide",
    "O2": "Oxygen",
    "O2(L)": "Oxygen",
    "Air": "Air",
    "H2O2(L)": "HydrogenPeroxide",
    "N2H4(L)": "Nitrogen",  # Approximation
    "F2": "Fluorine",
    "F2(L)": "Fluorine",
    "CL2": "Chlorine", 
    "CL2(L)": "Chlorine",
}

# Predefined fuel properties (exploded formula, temperature, enthalpy)
FUEL_PROPERTIES = {
    "paraffin": {
        "exploded_formula": "C 73 H 124",
        "temperature": 533.0,
        "enthalpy": -1860.6
    },
    "CH4": {
        "exploded_formula": "C 1 H 4",
        "temperature": 111.0,
        "enthalpy": -74.87
    },
    "CH4(L)": {
        "exploded_formula": "C 1 H 4",
        "temperature": 111.0,
        "enthalpy": -89.0
    },
    "H2": {
        "exploded_formula": "H 2",
        "temperature": 20.0,
        "enthalpy": 0.0
    },
    "H2(L)": {
        "exploded_formula": "H 2",
        "temperature": 20.0,
        "enthalpy": -9.01
    },
    "RP-1": {
        "exploded_formula": "C 1 H 1.95",
        "temperature": 298.0,
        "enthalpy": -24.7
    },
}

# Predefined oxidizer properties
OXIDIZER_PROPERTIES = {
    "N2O": {
        "exploded_formula": "N 2 O 1",
        "temperature": 298.0,
        "enthalpy": 82.05
    },
    "O2": {
        "exploded_formula": "O 2",
        "temperature": 90.0,
        "enthalpy": 0.0
    },
    "O2(L)": {
        "exploded_formula": "O 2",
        "temperature": 90.0,
        "enthalpy": -12.98
    },
    "H2O2(L)": {
        "exploded_formula": "H 2 O 2",
        "temperature": 298.0,
        "enthalpy": -187.8
    },
}


class ConfigurationPage:
    """Configuration page for rocket parameters"""
    
    def __init__(self, parent, inputs_dict: dict, dropdowns_dict: dict, 
                 reactant_manager, popup_manager):
        """
        Initialize configuration page
        
        Args:
            parent: Parent frame to contain this page
            inputs_dict: Shared dictionary for input fields
            dropdowns_dict: Shared dictionary for dropdown fields
            reactant_manager: ReactantManager instance
            popup_manager: PopupManager instance
        """
        self.parent = parent
        self.inputs = inputs_dict
        self.dropdowns = dropdowns_dict
        self.reactant_manager = reactant_manager
        self.popup_manager = popup_manager
        
        # Fuel selection variables
        self.selected_fuels = []
        self.fuel_weight_entries = {}
        
        # Dynamic frame references
        self.oxidizer_dynamic_frame = None
        self.fuel_display_frame = None
        self.fuel_dynamic_frame = None
        
        self.create_page()
    
    def create_page(self):
        """Create the configuration page content"""
        # Title
        title = tk.Label(
            self.parent, 
            text="Configuration", 
            font=FONTS['title'],
            bg=COLORS['bg_dark'], 
            fg=COLORS['text_color']
        )
        title.pack(pady=20)
        
        # Scrollable frame
        canvas = tk.Canvas(self.parent, bg=COLORS['bg_dark'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['bg_dark'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
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
        
        # Add sections
        self.create_geometry_section(scrollable_frame)
        self.create_fuel_oxidizer_section(scrollable_frame)
        self.create_line_losses_section(scrollable_frame)
        self.create_nozzle_section(scrollable_frame)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_geometry_section(self, parent):
        """Create geometry input section"""
        section = tk.LabelFrame(
            parent, 
            text="Geometry", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, padx=20, pady=10)
        
        create_input_field(section, "Geometry_CD", "Discharge Coefficient CD:", 
                          self.inputs, default="0.8", row=0)
    
    def create_line_losses_section(self, parent):
        """Create line losses input section"""
        section = tk.LabelFrame(
            parent, 
            text="Line Losses", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, padx=20, pady=10)
        
        # Info label
        info_label = tk.Label(
            section,
            text="Pressure drop in feed line. Leave at 0 if no line losses model.",
            font=FONTS['small'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            wraplength=500,
            anchor='w'
        )
        info_label.grid(row=0, column=0, columnspan=2, sticky='w', padx=10, pady=(5, 10))
        
        create_input_field(section, "LineLosses_DeltaP", "Line Pressure Drop [Pa]:", 
                          self.inputs, default="0", row=1)
    
    def create_fuel_oxidizer_section(self, parent):
        """Create fuel and oxidizer properties section"""
        section = tk.LabelFrame(
            parent, 
            text="Fuel & Oxidizer", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, padx=20, pady=10)
        
        # Oxidizer dropdown
        self.create_oxidizer_dropdown(section)
        
        # Fuel selection
        self.create_fuel_selection(section)
        
        # Common fuel properties
        create_input_field(section, "Fuel_a", "Regression rate coefficient a:", 
                          self.inputs, default="0.00017", row=20)
        create_input_field(section, "Fuel_n", "Regression rate exponent n:", 
                          self.inputs, default="0.5", row=21)
        create_input_field(section, "Fuel_rho", "Fuel density [kg/m³]:", 
                          self.inputs, default="850", row=22)
    
    def create_oxidizer_dropdown(self, parent):
        """Create oxidizer selection dropdown and dynamic fields"""
        # Oxidizer CEA dropdown
        row = tk.Frame(parent, bg=COLORS['bg_medium'])
        row.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        parent.grid_columnconfigure(0, weight=1)
        
        tk.Label(
            row, 
            text="Oxidizer (CEA name):", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=25,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        combo = ttk.Combobox(
            row, 
            font=FONTS['label'], 
            width=28,
            values=self.reactant_manager.get_oxidizer_list(), 
            state='readonly'
        )
        combo.pack(side=tk.LEFT)
        combo.bind('<<ComboboxSelected>>', lambda e: self.on_oxidizer_change())
        
        self.dropdowns["Oxidizer_CEA"] = combo
        
        # CoolProp name (auto-filled or manual)
        row2 = tk.Frame(parent, bg=COLORS['bg_medium'])
        row2.grid(row=1, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        tk.Label(
            row2, 
            text="Oxidizer (CoolProp name):", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=25,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        coolprop_entry = tk.Entry(row2, font=FONTS['label'], width=30)
        coolprop_entry.pack(side=tk.LEFT)
        self.inputs["Oxidizer_CoolProp"] = coolprop_entry
        
        # Oxidizer exploded formula
        row3 = tk.Frame(parent, bg=COLORS['bg_medium'])
        row3.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        tk.Label(
            row3, 
            text="Oxidizer Exploded Formula:", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=25,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        formula_entry = tk.Entry(row3, font=FONTS['label'], width=30)
        formula_entry.pack(side=tk.LEFT)
        self.inputs["Oxidizer_ExplodedFormula"] = formula_entry
        
        # Oxidizer temperature (optional)
        row4 = tk.Frame(parent, bg=COLORS['bg_medium'])
        row4.grid(row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        tk.Label(
            row4, 
            text="Oxidizer Temperature [K] (opt):", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=25,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        temp_entry = tk.Entry(row4, font=FONTS['label'], width=30)
        temp_entry.pack(side=tk.LEFT)
        self.inputs["Oxidizer_Temperature"] = temp_entry
        
        # Oxidizer enthalpy (optional)
        row5 = tk.Frame(parent, bg=COLORS['bg_medium'])
        row5.grid(row=4, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        tk.Label(
            row5, 
            text="Oxidizer Enthalpy [kJ/mol] (opt):", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=25,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        enthalpy_entry = tk.Entry(row5, font=FONTS['label'], width=30)
        enthalpy_entry.pack(side=tk.LEFT)
        self.inputs["Oxidizer_Enthalpy"] = enthalpy_entry
        
        # Separator
        separator = ttk.Separator(parent, orient='horizontal')
        separator.grid(row=5, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
    
    def on_oxidizer_change(self):
        """Handle oxidizer selection change"""
        oxidizer_cea = self.dropdowns["Oxidizer_CEA"].get()
        
        if oxidizer_cea == "Select other options":
            def callback(selected):
                self.dropdowns["Oxidizer_CEA"].set(selected)
                self.on_oxidizer_change()
            
            self.popup_manager.show_search_popup(
                "Select Oxidizer", 
                self.reactant_manager.get_cea_reactants(), 
                callback
            )
            return
        
        elif oxidizer_cea == "Custom with exploded formula":
            def callback(result):
                self.dropdowns["Oxidizer_CEA"].set(f"Custom: {result['name']}")
                self.inputs["Oxidizer_CoolProp"].delete(0, tk.END)
                self.inputs["Oxidizer_CoolProp"].insert(0, result.get('coolprop_name', ''))
                self.inputs["Oxidizer_ExplodedFormula"].delete(0, tk.END)
                self.inputs["Oxidizer_ExplodedFormula"].insert(0, result['exploded_formula'])
            
            self.popup_manager.show_custom_formula_popup(callback)
            return
        
        # Auto-fill CoolProp name if known
        coolprop_name = CEA_TO_COOLPROP_OXIDIZER.get(oxidizer_cea, "")
        self.inputs["Oxidizer_CoolProp"].delete(0, tk.END)
        self.inputs["Oxidizer_CoolProp"].insert(0, coolprop_name)
        
        # Auto-fill properties if known
        if oxidizer_cea in OXIDIZER_PROPERTIES:
            props = OXIDIZER_PROPERTIES[oxidizer_cea]
            self.inputs["Oxidizer_ExplodedFormula"].delete(0, tk.END)
            self.inputs["Oxidizer_ExplodedFormula"].insert(0, props["exploded_formula"])
            self.inputs["Oxidizer_Temperature"].delete(0, tk.END)
            self.inputs["Oxidizer_Temperature"].insert(0, str(props["temperature"]))
            self.inputs["Oxidizer_Enthalpy"].delete(0, tk.END)
            self.inputs["Oxidizer_Enthalpy"].insert(0, str(props["enthalpy"]))
        else:
            # Clear fields for manual input
            self.inputs["Oxidizer_ExplodedFormula"].delete(0, tk.END)
            self.inputs["Oxidizer_Temperature"].delete(0, tk.END)
            self.inputs["Oxidizer_Enthalpy"].delete(0, tk.END)
    
    def create_fuel_selection(self, parent):
        """Create fuel selection button and display"""
        # Fuel select button
        row = tk.Frame(parent, bg=COLORS['bg_medium'])
        row.grid(row=6, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        tk.Label(
            row, 
            text="Fuel:", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=25,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        select_btn = tk.Button(
            row, 
            text="Select Fuels",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.on_fuel_select_click,
            cursor='hand2',
            padx=10,
            pady=5
        )
        select_btn.pack(side=tk.LEFT)
        
        # Fuel display frame
        self.fuel_display_frame = tk.Frame(parent, bg=COLORS['bg_medium'])
        self.fuel_display_frame.grid(row=7, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        # Fuel properties frame (exploded formula, temp, enthalpy)
        self.fuel_dynamic_frame = tk.Frame(parent, bg=COLORS['bg_medium'])
        self.fuel_dynamic_frame.grid(row=8, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        # Separator before common properties
        separator = ttk.Separator(parent, orient='horizontal')
        separator.grid(row=19, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
    
    def on_fuel_select_click(self):
        """Handle fuel selection button click"""
        def callback(selected_fuels):
            if not selected_fuels:
                return
                
            if "Select other options" in selected_fuels:
                def full_list_callback(full_selected):
                    self.handle_fuel_selection(full_selected)
                
                self.popup_manager.show_search_popup(
                    "Select Fuels", 
                    self.reactant_manager.get_cea_reactants(),
                    full_list_callback, 
                    multi_select=True
                )
                return
            
            if "Custom with exploded formula" in selected_fuels:
                def custom_callback(result):
                    custom_name = f"Custom: {result['name']}"
                    self.selected_fuels = [custom_name]
                    self.fuel_weight_entries = {custom_name: 100.0}
                    self.update_fuel_display()
                    self.create_fuel_dynamic_fields(
                        custom_name,
                        result['exploded_formula'],
                        result.get('temperature', ''),
                        result.get('enthalpy', '')
                    )
                
                self.popup_manager.show_custom_formula_popup(custom_callback)
                return
            
            self.handle_fuel_selection(selected_fuels)
        
        self.popup_manager.show_search_popup(
            "Select Fuels", 
            self.reactant_manager.get_fuel_list(),
            callback, 
            multi_select=True
        )
    
    def handle_fuel_selection(self, selected_fuels):
        """Process selected fuels"""
        if not selected_fuels:
            return
        
        # Single fuel
        if len(selected_fuels) == 1:
            fuel = selected_fuels[0]
            self.selected_fuels = selected_fuels
            self.fuel_weight_entries = {fuel: 100.0}
            self.update_fuel_display()
            
            # Get properties if known
            if fuel in FUEL_PROPERTIES:
                props = FUEL_PROPERTIES[fuel]
                self.create_fuel_dynamic_fields(
                    fuel,
                    props["exploded_formula"],
                    props["temperature"],
                    props["enthalpy"]
                )
            else:
                self.create_fuel_dynamic_fields(fuel)
            return
        
        # Multiple fuels - need weights
        self.selected_fuels = selected_fuels
        
        def weight_callback(weights):
            self.fuel_weight_entries = weights
            self.update_fuel_display()
            self.create_multi_fuel_dynamic_fields()
        
        self.popup_manager.show_fuel_weight_popup(selected_fuels, weight_callback)
    
    def update_fuel_display(self):
        """Update fuel display showing selected fuels and weights"""
        for widget in self.fuel_display_frame.winfo_children():
            widget.destroy()
        
        if not self.selected_fuels:
            return
        
        for fuel in self.selected_fuels:
            row = tk.Frame(self.fuel_display_frame, bg=COLORS['bg_medium'])
            row.pack(fill=tk.X, pady=2)
            
            weight = self.fuel_weight_entries.get(fuel, 0)
            text = f"  • {fuel}: {weight}%"
            
            label = tk.Label(
                row, 
                text=text, 
                font=FONTS['small'],
                bg=COLORS['bg_medium'], 
                fg=COLORS['text_color'], 
                anchor='w'
            )
            label.pack(side=tk.LEFT, padx=(20, 0))
    
    def create_fuel_dynamic_fields(self, fuel_name, formula_default="", 
                                    temp_default=None, enthalpy_default=None):
        """Create dynamic fields for a single fuel"""
        for widget in self.fuel_dynamic_frame.winfo_children():
            widget.destroy()
        
        # Exploded formula
        row1 = tk.Frame(self.fuel_dynamic_frame, bg=COLORS['bg_medium'])
        row1.pack(fill=tk.X, pady=5)
        
        tk.Label(
            row1, 
            text="Fuel Exploded Formula:", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=25,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        formula_entry = tk.Entry(row1, font=FONTS['label'], width=30)
        formula_entry.pack(side=tk.LEFT)
        if formula_default:
            formula_entry.insert(0, formula_default)
        self.inputs["Fuel_ExplodedFormula"] = formula_entry
        
        # Temperature field
        row2 = tk.Frame(self.fuel_dynamic_frame, bg=COLORS['bg_medium'])
        row2.pack(fill=tk.X, pady=5)
        
        tk.Label(
            row2, 
            text="Fuel Temperature [K]:", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=25,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        temp_entry = tk.Entry(row2, font=FONTS['label'], width=30)
        temp_entry.pack(side=tk.LEFT)
        if temp_default:
            temp_entry.insert(0, str(temp_default))
        self.inputs["Fuel_Temperature"] = temp_entry
        
        # Enthalpy field
        row3 = tk.Frame(self.fuel_dynamic_frame, bg=COLORS['bg_medium'])
        row3.pack(fill=tk.X, pady=5)
        
        tk.Label(
            row3, 
            text="Fuel Enthalpy [kJ/mol]:", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=25,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        enthalpy_entry = tk.Entry(row3, font=FONTS['label'], width=30)
        enthalpy_entry.pack(side=tk.LEFT)
        if enthalpy_default:
            enthalpy_entry.insert(0, str(enthalpy_default))
        self.inputs["Fuel_Enthalpy"] = enthalpy_entry
    
    def create_multi_fuel_dynamic_fields(self):
        """Create dynamic fields for multiple fuels"""
        for widget in self.fuel_dynamic_frame.winfo_children():
            widget.destroy()
        
        info_label = tk.Label(
            self.fuel_dynamic_frame,
            text="Multiple fuels selected. Properties will use CEA database defaults.",
            font=FONTS['small'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color']
        )
        info_label.pack(pady=5)
        
        # Create fields for each fuel
        for i, fuel in enumerate(self.selected_fuels):
            frame = tk.LabelFrame(
                self.fuel_dynamic_frame,
                text=fuel,
                font=FONTS['small'],
                bg=COLORS['bg_medium'],
                fg=COLORS['text_color']
            )
            frame.pack(fill=tk.X, pady=5, padx=10)
            
            # Get defaults if known
            props = FUEL_PROPERTIES.get(fuel, {})
            
            # Formula
            row1 = tk.Frame(frame, bg=COLORS['bg_medium'])
            row1.pack(fill=tk.X, pady=2)
            tk.Label(row1, text="Formula:", font=FONTS['small'], 
                    bg=COLORS['bg_medium'], fg=COLORS['text_color'],
                    width=15, anchor='w').pack(side=tk.LEFT)
            entry1 = tk.Entry(row1, font=FONTS['small'], width=25)
            entry1.pack(side=tk.LEFT)
            entry1.insert(0, props.get("exploded_formula", ""))
            self.inputs[f"Fuel_{fuel}_ExplodedFormula"] = entry1
            
            # Temperature
            row2 = tk.Frame(frame, bg=COLORS['bg_medium'])
            row2.pack(fill=tk.X, pady=2)
            tk.Label(row2, text="Temp [K]:", font=FONTS['small'],
                    bg=COLORS['bg_medium'], fg=COLORS['text_color'],
                    width=15, anchor='w').pack(side=tk.LEFT)
            entry2 = tk.Entry(row2, font=FONTS['small'], width=25)
            entry2.pack(side=tk.LEFT)
            entry2.insert(0, str(props.get("temperature", "")))
            self.inputs[f"Fuel_{fuel}_Temperature"] = entry2
            
            # Enthalpy
            row3 = tk.Frame(frame, bg=COLORS['bg_medium'])
            row3.pack(fill=tk.X, pady=2)
            tk.Label(row3, text="Enthalpy [kJ/mol]:", font=FONTS['small'],
                    bg=COLORS['bg_medium'], fg=COLORS['text_color'],
                    width=15, anchor='w').pack(side=tk.LEFT)
            entry3 = tk.Entry(row3, font=FONTS['small'], width=25)
            entry3.pack(side=tk.LEFT)
            entry3.insert(0, str(props.get("enthalpy", "")))
            self.inputs[f"Fuel_{fuel}_Enthalpy"] = entry3
    
    def create_nozzle_section(self, parent):
        """Create nozzle parameters section"""
        section = tk.LabelFrame(
            parent, 
            text="Nozzle", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, padx=20, pady=10)
        
        create_input_field(section, "Nozzle_epsilon", "Expansion ratio (or 'adapt'):", 
                          self.inputs, default="adapt", row=0)
    
    def get_fuel_data(self):
        """
        Get fuel selection data
        
        Returns:
            (selected_fuels: list, fuel_weights: dict)
        """
        return self.selected_fuels.copy(), self.fuel_weight_entries.copy()
    
    def set_fuel_data(self, selected_fuels: list, fuel_weights: dict):
        """
        Set fuel selection data (for loading)
        
        Args:
            selected_fuels: List of selected fuel names
            fuel_weights: Dictionary of fuel weights
        """
        self.selected_fuels = selected_fuels.copy()
        self.fuel_weight_entries = fuel_weights.copy()


# Helper function to create the configuration page
def create_configuration_page(parent, inputs_dict, dropdowns_dict, reactant_manager, popup_manager):
    """
    Factory function to create configuration page
    
    Args:
        parent: Parent frame
        inputs_dict: Shared inputs dictionary
        dropdowns_dict: Shared dropdowns dictionary
        reactant_manager: ReactantManager instance
        popup_manager: PopupManager instance
        
    Returns:
        ConfigurationPage instance
    """
    return ConfigurationPage(parent, inputs_dict, dropdowns_dict, reactant_manager, popup_manager)
