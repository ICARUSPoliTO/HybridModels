# pages/configuration.py

import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from sections.line_section import LineSection
from sections.fuel_oxidiser import FuelOxidiserSection
from sections.injector_section import InjectorSection
from sections.nozzle_section import NozzleSection


class ConfigurationPage:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.app = main_app
        self.colors = COLORS
        self.fonts = FONTS
    
    def show(self):
        # Create scrollable canvas
        canvas = tk.Canvas(self.parent, bg=self.colors['bg_dark'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_dark'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title = tk.Label(scrollable_frame, text="configuration",
                         font=self.fonts['title'], bg=self.colors['bg_dark'], 
                         fg=self.colors['text_color'])
        title.pack(pady=(0, 20))
        
        # Sections
        line_section = LineSection(scrollable_frame, self.app)
        line_section.create()
        
        fuel_ox_section = FuelOxidiserSection(scrollable_frame, self.app)
        fuel_ox_section.create()
        
        injector_section = InjectorSection(scrollable_frame, self.app)
        injector_section.create()
        
        nozzle_section = NozzleSection(scrollable_frame, self.app)
        nozzle_section.create()
        
        # Save button
        save_button_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_dark'])
        save_button_frame.pack(fill=tk.X, pady=(20, 0))
        
        save_btn = ttk.Button(save_button_frame, text="Save Configuration",
                              style="Rounded.TButton",
                              command=self.validate_and_save)
        save_btn.pack(pady=10)
        
        # Validate on load
        from ui.validators import validate_all_inputs
        validate_all_inputs(self.app)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            if hasattr(self.app.popup_manager, 'search_popup_active') and self.app.popup_manager.search_popup_active:
                return
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def validate_and_save(self):
        config = {}
        all_valid = True
        
        for key, entry in self.app.inputs.items():
            if isinstance(entry, str):
                config[key] = entry
                continue
            
            value = entry.get().strip()
            if not value:
                all_valid = False
                break
            
            if "CustomName" in key or "ExpandedFormula" in key:
                config[key] = value
            else:
                try:
                    config[key] = float(value)
                except ValueError:
                    if key == "Nozzle_epsilon" and value.lower() == "adapt":
                        config[key] = value
                    else:
                        all_valid = False
                        break
        
        for key, combo in self.app.dropdowns.items():
            value = combo.get()
            if not value:
                all_valid = False
                break
            config[key] = value
        
        if all_valid:
            messagebox.showinfo("Success", "Configuration validated! All fields are valid.")
        else:
            messagebox.showerror("Error", "Some fields are empty or invalid.")
