import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from sections.optimization_section import OptimizationSection


class OptimizationPage:
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
        title = tk.Label(scrollable_frame, text="optimization",
                         font=self.fonts['title'], bg=self.colors['bg_dark'], 
                         fg=self.colors['text_color'])
        title.pack(pady=(0, 20))
        
        # Optimization section
        opt_section = OptimizationSection(scrollable_frame, self.app)
        opt_section.create()
        
        # Save button
        save_button_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_dark'])
        save_button_frame.pack(fill=tk.X, pady=(20, 0))
        
        save_btn = ttk.Button(save_button_frame, text="Save Optimization",
                              style="Rounded.TButton",
                              command=self.validate_and_save)
        save_btn.pack(pady=10)
        
        # Validate on load
        self.app.validate_inputs()
        
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
            if not key.startswith("Optimization_"):
                continue
            
            if isinstance(entry, str):
                config[key] = entry
                continue
            
            value = entry.get().strip()
            if not value:
                all_valid = False
                break
            
            try:
                if hasattr(entry, 'validation_params') and entry.validation_params.get('is_int'):
                    config[key] = int(value)
                else:
                    config[key] = float(value)
            except ValueError:
                all_valid = False
                break
        
        if all_valid:
            messagebox.showinfo("Success", "Optimization configuration validated! All fields are valid.")
        else:
            messagebox.showerror("Error", "Some fields are empty or invalid.")