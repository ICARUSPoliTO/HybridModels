"""
Configuration Page - Rocket configuration inputs

Contains all fields for geometry, fuel properties, and nozzle parameters.
"""

import tkinter as tk
from tkinter import ttk
from config.constants import COLORS, FONTS
from gui.components.input_field import create_input_field


# Paraffin default values
PARAFFIN_DEFAULTS = {
    'temperature': 533.0,
    'enthalpy': -1860.6
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
                          self.inputs, default="0.00017", row=10)
        create_input_field(section, "Fuel_n", "Regression rate exponent n:", 
                          self.inputs, default="0.5", row=11)
        create_input_field(section, "Fuel_rho", "Fuel density [kg/m³]:", 
                          self.inputs, default="850", row=12)
    
    def create_oxidizer_dropdown(self, parent):
        """Create oxidizer selection dropdown and dynamic fields"""
        # Oxidizer dropdown
        row = tk.Frame(parent, bg=COLORS['bg_medium'])
        row.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        parent.grid_columnconfigure(0, weight=1)
        
        tk.Label(
            row, 
            text="(Ox) Oxidizer:", 
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
        
        self.dropdowns["Fuel & Oxidiser_Oxidizer"] = combo
        
        # Weight fraction (readonly, always 100 for single oxidizer)
        row = tk.Frame(parent, bg=COLORS['bg_medium'])
        row.grid(row=1, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        tk.Label(
            row, 
            text="Weight fraction:", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=25,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        entry = tk.Entry(
            row, 
            font=FONTS['label'], 
            width=30,
            state='readonly'
        )
        entry.pack(side=tk.LEFT)
        entry.config(state='normal')
        entry.insert(0, "100")
        entry.config(state='readonly')
        
        self.inputs["Fuel & Oxidiser_Oxidizer_WeightFraction"] = entry
        
        # Dynamic fields frame
        self.oxidizer_dynamic_frame = tk.Frame(parent, bg=COLORS['bg_medium'])
        self.oxidizer_dynamic_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10)
    
    def on_oxidizer_change(self):
        """Handle oxidizer selection change"""
        # Clear dynamic fields
        for widget in self.oxidizer_dynamic_frame.winfo_children():
            widget.destroy()
        
        oxidizer = self.dropdowns["Fuel & Oxidiser_Oxidizer"].get()
        
        if oxidizer == "Select other options":
            def callback(selected):
                self.dropdowns["Fuel & Oxidiser_Oxidizer"].set(selected)
                self.on_oxidizer_change()
            
            self.popup_manager.show_search_popup(
                "Select Oxidizer", 
                self.reactant_manager.get_cea_reactants(), 
                callback
            )
            return
        
        elif oxidizer == "Custom with exploded formula":
            def callback(result):
                self.inputs["Fuel & Oxidiser_Oxidizer_CustomName"] = result['name']
                self.inputs["Fuel & Oxidiser_Oxidizer_ExpandedFormula"] = result['exploded_formula']
                self.dropdowns["Fuel & Oxidiser_Oxidizer"].set(f"Custom: {result['name']}")
                # Don't create dynamic fields for oxidizer
            
            self.popup_manager.show_custom_formula_popup(callback)
            return
        
        # No dynamic fields for oxidizer - temperature/enthalpy not needed
    
    def create_oxidizer_dynamic_fields(self, temp_default=None, enthalpy_default=None):
        """Create dynamic temperature and enthalpy fields for oxidizer"""
        # This method is now deprecated - oxidizer doesn't need these fields
        # Kept for backwards compatibility but does nothing
        pass
    
    def create_fuel_selection(self, parent):
        """Create fuel selection button and display"""
        # Fuel select button
        row = tk.Frame(parent, bg=COLORS['bg_medium'])
        row.grid(row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        tk.Label(
            row, 
            text="(F) Fuel:", 
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
        self.fuel_display_frame.grid(row=4, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        # Dynamic fields frame
        self.fuel_dynamic_frame = tk.Frame(parent, bg=COLORS['bg_medium'])
        self.fuel_dynamic_frame.grid(row=5, column=0, columnspan=2, sticky='ew', padx=10)
    
    def on_fuel_select_click(self):
        """Handle fuel selection button click"""
        def callback(selected_fuels):
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
                    self.selected_fuels = [f"Custom: {result['name']}"]
                    self.inputs["Fuel & Oxidiser_Fuel_CustomName"] = result['name']
                    self.inputs["Fuel & Oxidiser_Fuel_ExpandedFormula"] = result['exploded_formula']
                    
                    self.fuel_weight_entries = {f"Custom: {result['name']}": 100.0}
                    self.update_fuel_display()
                    self.create_fuel_dynamic_fields(result['temperature'], result['enthalpy'])
                
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
        
        # Special case for paraffin
        if len(selected_fuels) == 1 and selected_fuels[0] == "paraffin":
            self.selected_fuels = selected_fuels
            self.fuel_weight_entries = {"paraffin": 100.0}
            self.update_fuel_display()
            self.create_fuel_dynamic_fields(
                PARAFFIN_DEFAULTS['temperature'], 
                PARAFFIN_DEFAULTS['enthalpy']
            )
            return
        
        # Single fuel
        if len(selected_fuels) == 1:
            self.selected_fuels = selected_fuels
            self.fuel_weight_entries = {selected_fuels[0]: 100.0}
            self.update_fuel_display()
            self.create_fuel_dynamic_fields()
            return
        
        # Multiple fuels - need weights
        self.selected_fuels = selected_fuels
        
        def weight_callback(weights):
            self.fuel_weight_entries = weights
            self.update_fuel_display()
            self.create_fuel_dynamic_fields()
        
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
    
    def create_fuel_dynamic_fields(self, temp_default=None, enthalpy_default=None):
        """Create dynamic temperature and enthalpy fields for fuel"""
        for widget in self.fuel_dynamic_frame.winfo_children():
            widget.destroy()
        
        # Temperature field
        row = tk.Frame(self.fuel_dynamic_frame, bg=COLORS['bg_medium'])
        row.pack(fill=tk.X, pady=5)
        
        tk.Label(
            row, 
            text="Fuel Temperature [K]:", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=25,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        entry = tk.Entry(row, font=FONTS['label'], width=30)
        entry.pack(side=tk.LEFT)
        if temp_default:
            entry.insert(0, str(temp_default))
        
        self.inputs["Fuel & Oxidiser_Fuel_Temperature"] = entry
        
        # Enthalpy field
        row = tk.Frame(self.fuel_dynamic_frame, bg=COLORS['bg_medium'])
        row.pack(fill=tk.X, pady=5)
        
        tk.Label(
            row, 
            text="Fuel Specific Enthalpy [kJ/mol]:", 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color'],
            width=25,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        entry = tk.Entry(row, font=FONTS['label'], width=30)
        entry.pack(side=tk.LEFT)
        if enthalpy_default:
            entry.insert(0, str(enthalpy_default))
        
        self.inputs["Fuel & Oxidiser_Fuel_SpecificEnthalpy"] = entry
    
    def create_fuel_section(self, parent):
        """Create fuel properties section"""
        section = tk.LabelFrame(
            parent, 
            text="Fuel Properties", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, padx=20, pady=10)
        
        create_input_field(section, "Fuel_a", "Regression rate coefficient a:", 
                          self.inputs, default="0.00017", row=0)
        create_input_field(section, "Fuel_n", "Regression rate exponent n:", 
                          self.inputs, default="0.5", row=1)
        create_input_field(section, "Fuel_rho", "Fuel density [kg/m³]:", 
                          self.inputs, default="850", row=2)
        
        # Note about fuel selection
        note = tk.Label(
            section,
            text="Note: Full fuel and oxidizer selection will be added from your original code",
            font=FONTS['small'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            wraplength=500
        )
        note.grid(row=3, column=0, columnspan=2, pady=10)
    
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
        # Update UI if needed


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
