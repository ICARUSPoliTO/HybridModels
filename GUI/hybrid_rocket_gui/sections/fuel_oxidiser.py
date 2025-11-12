# sections/fuel_oxidiser.py

import tkinter as tk
from tkinter import ttk
from config import COLORS, FONTS, PARAFFIN_DEFAULTS


class FuelOxidiserSection:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.app = main_app
        self.colors = COLORS
        self.fonts = FONTS
        self.oxidizer_dynamic_frame = None
        self.fuel_dynamic_frame = None
        self.fuel_display_frame = None
    
    def create(self):
        section = tk.Frame(self.parent, bg=self.colors['bg_light'], relief=tk.RIDGE, bd=2)
        section.pack(fill=tk.X, pady=10, ipady=15)
        
        header_frame = tk.Frame(section, bg=self.colors['bg_light'])
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
        
        section_title = tk.Label(header_frame, text="Fuel & Oxidiser", font=self.fonts['section'],
                                 bg=self.colors['bg_light'], fg='black')
        section_title.pack(side=tk.LEFT)
        
        fields_frame = tk.Frame(section, bg=self.colors['bg_light'])
        fields_frame.pack(fill=tk.X, padx=40, pady=10)
        
        # Create sections
        self.create_oxidizer_fields(fields_frame)
        self.create_fuel_fields(fields_frame)
        
        # Common fields
        self.create_float_field(fields_frame, "Fuel & Oxidiser", "a", "a", min_value=0, exclusive=True)
        self.create_float_field(fields_frame, "Fuel & Oxidiser", "n", "n")
        self.create_float_field(fields_frame, "Fuel & Oxidiser", "rho.fuel", "ρF (kg/m³)",
                                min_value=0, exclusive=True)
    
    def create_oxidizer_fields(self, parent):
        # Oxidizer dropdown
        row = tk.Frame(parent, bg=self.colors['bg_light'])
        row.pack(fill=tk.X, pady=5)
        
        label = tk.Label(row, text="(Ox) Oxidizer:", font=self.fonts['normal'],
                         bg=self.colors['bg_light'], fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        combo = ttk.Combobox(row, font=self.fonts['normal'], width=28,
                             values=self.app.reactant_manager.get_oxidizer_list(), state='readonly')
        combo.pack(side=tk.LEFT)
        combo.bind('<<ComboboxSelected>>', lambda e: self.on_oxidizer_change())
        
        self.app.dropdowns["Fuel & Oxidiser_Oxidizer"] = combo
        
        # Weight fraction (readonly, always 100)
        row = tk.Frame(parent, bg=self.colors['bg_light'])
        row.pack(fill=tk.X, pady=5)
        
        label = tk.Label(row, text="Weight fraction:", font=self.fonts['normal'],
                         bg=self.colors['bg_light'], fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        entry = tk.Entry(row, font=self.fonts['normal'], width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.colors['bg_light'],
                         highlightcolor=self.colors['bg_light'], state='readonly')
        entry.insert(0, "100")
        entry.pack(side=tk.LEFT)
        
        self.app.inputs["Fuel & Oxidiser_Oxidizer_WeightFraction"] = entry
        
        # Dynamic fields frame
        self.oxidizer_dynamic_frame = tk.Frame(parent, bg=self.colors['bg_light'])
        self.oxidizer_dynamic_frame.pack(fill=tk.X)
    
    def on_oxidizer_change(self):
        # Clear dynamic fields
        for widget in self.oxidizer_dynamic_frame.winfo_children():
            widget.destroy()
        
        oxidizer = self.app.dropdowns["Fuel & Oxidiser_Oxidizer"].get()
        
        if oxidizer == "Select other options":
            def callback(selected):
                self.app.dropdowns["Fuel & Oxidiser_Oxidizer"].set(selected)
                self.on_oxidizer_change()
            
            self.app.popup_manager.show_search_popup("Select Oxidizer", 
                                                     self.app.reactant_manager.get_cea_reactants(), 
                                                     callback)
            return
        
        elif oxidizer == "Custom with exploded formula":
            def callback(result):
                self.app.inputs["Fuel & Oxidiser_Oxidizer_CustomName"] = result['name']
                self.app.inputs["Fuel & Oxidiser_Oxidizer_ExpandedFormula"] = result['exploded_formula']
                self.app.dropdowns["Fuel & Oxidiser_Oxidizer"].set(f"Custom: {result['name']}")
                self.create_oxidizer_dynamic_fields(result['temperature'], result['enthalpy'])
            
            self.app.popup_manager.show_custom_formula_popup(callback)
            return
        
        self.create_oxidizer_dynamic_fields()
    
    def create_oxidizer_dynamic_fields(self, temp_default=None, enthalpy_default=None):
        # Temperature field
        row = tk.Frame(self.oxidizer_dynamic_frame, bg=self.colors['bg_light'])
        row.pack(fill=tk.X, pady=5)
        
        label = tk.Label(row, text="Temperature [K]:", font=self.fonts['normal'],
                         bg=self.colors['bg_light'], fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        entry = tk.Entry(row, font=self.fonts['normal'], width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.colors['bg_light'],
                         highlightcolor=self.colors['bg_light'])
        entry.pack(side=tk.LEFT)
        if temp_default:
            entry.insert(0, str(temp_default))
        entry.bind('<KeyRelease>', lambda e: self.app.validate_single_input(entry))
        
        self.app.inputs["Fuel & Oxidiser_Oxidizer_Temperature"] = entry
        
        # Enthalpy field
        row = tk.Frame(self.oxidizer_dynamic_frame, bg=self.colors['bg_light'])
        row.pack(fill=tk.X, pady=5)
        
        label = tk.Label(row, text="Specific Enthalpy [kJ/mol]:", font=self.fonts['normal'],
                         bg=self.colors['bg_light'], fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        entry = tk.Entry(row, font=self.fonts['normal'], width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.colors['bg_light'],
                         highlightcolor=self.colors['bg_light'])
        entry.pack(side=tk.LEFT)
        if enthalpy_default:
            entry.insert(0, str(enthalpy_default))
        entry.bind('<KeyRelease>', lambda e: self.app.validate_single_input(entry))
        
        self.app.inputs["Fuel & Oxidiser_Oxidizer_SpecificEnthalpy"] = entry
        
        self.app.validate_inputs()
    
    def create_fuel_fields(self, parent):
        # Fuel select button
        row = tk.Frame(parent, bg=self.colors['bg_light'])
        row.pack(fill=tk.X, pady=5)
        
        label = tk.Label(row, text="(F) Fuel:", font=self.fonts['normal'],
                         bg=self.colors['bg_light'], fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        select_btn = ttk.Button(row, text="Select Fuels", style="Rounded.TButton",
                                command=self.on_fuel_select_click)
        select_btn.pack(side=tk.LEFT)
        
        # Fuel display frame
        self.fuel_display_frame = tk.Frame(parent, bg=self.colors['bg_light'])
        self.fuel_display_frame.pack(fill=tk.X, pady=5)
        
        # Dynamic fields frame
        self.fuel_dynamic_frame = tk.Frame(parent, bg=self.colors['bg_light'])
        self.fuel_dynamic_frame.pack(fill=tk.X)
    
    def on_fuel_select_click(self):
        def callback(selected_fuels):
            if "Select other options" in selected_fuels:
                def full_list_callback(full_selected):
                    self.handle_fuel_selection(full_selected)
                
                self.app.popup_manager.show_search_popup("Select Fuels", 
                                                         self.app.reactant_manager.get_cea_reactants(),
                                                         full_list_callback, multi_select=True)
                return
            
            if "Custom with exploded formula" in selected_fuels:
                def custom_callback(result):
                    self.app.selected_fuels = [f"Custom: {result['name']}"]
                    self.app.inputs["Fuel & Oxidiser_Fuel_CustomName"] = result['name']
                    self.app.inputs["Fuel & Oxidiser_Fuel_ExpandedFormula"] = result['exploded_formula']
                    
                    self.app.fuel_weight_entries = {f"Custom: {result['name']}": 100.0}
                    self.update_fuel_display()
                    self.create_fuel_dynamic_fields(result['temperature'], result['enthalpy'])
                
                self.app.popup_manager.show_custom_formula_popup(custom_callback)
                return
            
            self.handle_fuel_selection(selected_fuels)
        
        self.app.popup_manager.show_search_popup("Select Fuels", 
                                                 self.app.reactant_manager.get_fuel_list(),
                                                 callback, multi_select=True)
    
    def handle_fuel_selection(self, selected_fuels):
        if not selected_fuels:
            return
        
        # Special case for paraffin
        if len(selected_fuels) == 1 and selected_fuels[0] == "paraffin":
            self.app.selected_fuels = selected_fuels
            self.app.fuel_weight_entries = {"paraffin": 100.0}
            self.update_fuel_display()
            self.create_fuel_dynamic_fields(PARAFFIN_DEFAULTS['temperature'], 
                                           PARAFFIN_DEFAULTS['enthalpy'])
            return
        
        # Single fuel
        if len(selected_fuels) == 1:
            self.app.selected_fuels = selected_fuels
            self.app.fuel_weight_entries = {selected_fuels[0]: 100.0}
            self.update_fuel_display()
            self.create_fuel_dynamic_fields()
            return
        
        # Multiple fuels - need weights
        self.app.selected_fuels = selected_fuels
        
        def weight_callback(weights):
            self.app.fuel_weight_entries = weights
            self.update_fuel_display()
            self.create_fuel_dynamic_fields()
        
        self.app.popup_manager.show_fuel_weight_popup(selected_fuels, weight_callback)
    
    def update_fuel_display(self):
        for widget in self.fuel_display_frame.winfo_children():
            widget.destroy()
        
        if not self.app.selected_fuels:
            return
        
        for fuel in self.app.selected_fuels:
            row = tk.Frame(self.fuel_display_frame, bg=self.colors['bg_light'])
            row.pack(fill=tk.X, pady=2)
            
            weight = self.app.fuel_weight_entries.get(fuel, 0)
            text = f"  • {fuel}: {weight}%"
            
            label = tk.Label(row, text=text, font=self.fonts['small'],
                             bg=self.colors['bg_light'], fg='black', anchor='w')
            label.pack(side=tk.LEFT, padx=(20, 0))
        
        self.app.validate_inputs()
    
    def create_fuel_dynamic_fields(self, temp_default=None, enthalpy_default=None):
        for widget in self.fuel_dynamic_frame.winfo_children():
            widget.destroy()
        
        # Temperature field
        row = tk.Frame(self.fuel_dynamic_frame, bg=self.colors['bg_light'])
        row.pack(fill=tk.X, pady=5)
        
        label = tk.Label(row, text="Fuel Temperature [K]:", font=self.fonts['normal'],
                         bg=self.colors['bg_light'], fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        entry = tk.Entry(row, font=self.fonts['normal'], width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.colors['bg_light'],
                         highlightcolor=self.colors['bg_light'])
        entry.pack(side=tk.LEFT)
        if temp_default:
            entry.insert(0, str(temp_default))
        entry.bind('<KeyRelease>', lambda e: self.app.validate_single_input(entry))
        
        self.app.inputs["Fuel & Oxidiser_Fuel_Temperature"] = entry
        
        # Enthalpy field
        row = tk.Frame(self.fuel_dynamic_frame, bg=self.colors['bg_light'])
        row.pack(fill=tk.X, pady=5)
        
        label = tk.Label(row, text="Fuel Specific Enthalpy [kJ/mol]:", font=self.fonts['normal'],
                         bg=self.colors['bg_light'], fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        entry = tk.Entry(row, font=self.fonts['normal'], width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.colors['bg_light'],
                         highlightcolor=self.colors['bg_light'])
        entry.pack(side=tk.LEFT)
        if enthalpy_default:
            entry.insert(0, str(enthalpy_default))
        entry.bind('<KeyRelease>', lambda e: self.app.validate_single_input(entry))
        
        self.app.inputs["Fuel & Oxidiser_Fuel_SpecificEnthalpy"] = entry
        
        self.app.validate_inputs()
    
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