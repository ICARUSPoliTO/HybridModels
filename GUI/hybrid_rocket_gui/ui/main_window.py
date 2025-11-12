# ui/main_window.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json

from config import COLORS, FONTS
from ui.styles import StyleManager
from ui.popups import PopupManager
from ui.validators import InputValidator
from utils.reactants import ReactantManager
from pages.configuration import ConfigurationPage
from pages.optimization import OptimizationPage


class HybridRocketGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("hybrid model")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLORS['bg_dark'])
        
        # Maximize window
        try:
            self.root.state('zoomed')
        except:
            pass
        
        # Initialize managers
        self.colors = COLORS
        self.fonts = FONTS
        self.style_manager = StyleManager(root)
        self.reactant_manager = ReactantManager()
        self.popup_manager = PopupManager(root, self.style_manager)
        self.validator = InputValidator()
        
        # Data storage
        self.inputs = {}
        self.dropdowns = {}
        self.current_page = 'configuration'
        self.selected_fuels = []
        self.fuel_weight_entries = {}
        self.current_file = None
        
        # UI Components
        self.create_header()
        self.create_sidebar()
        
        # Content area
        self.content_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Show initial page
        self.change_page('configuration')
    
    def create_header(self):
        header = tk.Frame(self.root, bg=self.colors['bg_dark'], height=60)
        header.pack(side=tk.TOP, fill=tk.X)
        
        title = tk.Label(header, text="HYBRID MODEL", font=self.fonts['header'],
                         bg=self.colors['bg_dark'], fg=self.colors['text_color'])
        title.pack(side=tk.LEFT, padx=20)


    def create_sidebar(self):
        sidebar = tk.Frame(self.root, bg=self.colors['bg_medium'], width=150)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Menu button
        self.menu_button = ttk.Button(sidebar, text="Menu", style="Rounded.TButton",
                                      command=self.toggle_menu)
        self.menu_button.pack(fill=tk.X, padx=10, pady=10)
        
        # Page buttons
        self.page_buttons = {}
        pages = ['configuration', 'optimization', 'mission', 'output']
        
        for page in pages:
            btn = ttk.Button(sidebar, text=page.capitalize(),
                             style="Rounded.TButton",
                             command=lambda p=page: self.change_page(p))
            btn.pack(fill=tk.X, padx=10, pady=5)
            self.page_buttons[page] = btn
    
    def toggle_menu(self):
        if hasattr(self, 'dropdown_frame') and self.dropdown_frame and self.dropdown_frame.winfo_exists():
            self.dropdown_frame.destroy()
            self.dropdown_frame = None
        else:
            self._create_dropdown_menu()
    
    def _create_dropdown_menu(self):
        x = self.menu_button.winfo_rootx()
        y = self.menu_button.winfo_rooty() + self.menu_button.winfo_height()
        button_width = self.menu_button.winfo_width()
        
        self.dropdown_frame = tk.Toplevel(self.root)
        self.dropdown_frame.overrideredirect(True)
        self.dropdown_frame.configure(bg=self.colors['bg_active'])
        
        # Menu items
        save_btn = tk.Button(self.dropdown_frame, text="Save", font=self.fonts['small'],
                             bg=self.colors['bg_light'], command=self.save_config,
                             relief=tk.FLAT, anchor='w', highlightthickness=0, bd=0)
        save_btn.pack(fill=tk.X, pady=2, padx=2)
        
        save_as_btn = tk.Button(self.dropdown_frame, text="Save As", font=self.fonts['small'],
                                bg=self.colors['bg_light'], command=self.save_config_as,
                                relief=tk.FLAT, anchor='w', highlightthickness=0, bd=0)
        save_as_btn.pack(fill=tk.X, pady=2, padx=2)
        
        open_btn = tk.Button(self.dropdown_frame, text="Open", font=self.fonts['small'],
                             bg=self.colors['bg_light'], command=self.open_config,
                             relief=tk.FLAT, anchor='w', highlightthickness=0, bd=0)
        open_btn.pack(fill=tk.X, pady=2, padx=2)
        
        self.dropdown_frame.update_idletasks()
        frame_width = self.dropdown_frame.winfo_width()
        centered_x = x + (button_width - frame_width) // 2
        self.dropdown_frame.geometry(f"+{centered_x}+{y}")
        
        self.dropdown_frame.bind("<FocusOut>", lambda e: self.toggle_menu())
        self.root.bind("<Button-1>", self._close_dropdown_on_click)
    
    def _close_dropdown_on_click(self, event):
        if hasattr(self, 'dropdown_frame') and self.dropdown_frame:
            if event.widget != self.dropdown_frame and event.widget.master != self.dropdown_frame:
                self.toggle_menu()
    
    def change_page(self, page):
        self.current_page = page
        
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Show selected page
        if page == 'configuration':
            config_page = ConfigurationPage(self.content_frame, self)
            config_page.show()
        elif page == 'optimization':
            opt_page = OptimizationPage(self.content_frame, self)
            opt_page.show()
        elif page == 'mission':
            self._show_coming_soon("MISSION")
        elif page == 'output':
            self._show_coming_soon("OUTPUT")
    
    def _show_coming_soon(self, page_name):
        label = tk.Label(self.content_frame, text=f"{page_name} - Coming soon",
                         font=('Arial', 20), bg=self.colors['bg_dark'], 
                         fg=self.colors['text_color'])
        label.pack(expand=True)
    
    def save_config(self):
        if not hasattr(self, 'current_file') or not self.current_file:
            self.save_config_as()
        else:
            self._save_to_file(self.current_file)
    
    def save_config_as(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.current_file = filename
            self._save_to_file(filename)
    
    def _save_to_file(self, filename):
        config = {}
        
        for key, entry in self.inputs.items():
            if isinstance(entry, str):
                config[key] = entry
                continue
            
            value = entry.get().strip()
            if value:
                if "CustomName" in key or "ExpandedFormula" in key:
                    config[key] = value
                else:
                    try:
                        if hasattr(entry, 'validation_params') and entry.validation_params.get('is_int'):
                            config[key] = int(value)
                        else:
                            config[key] = float(value)
                    except ValueError:
                        config[key] = value
        
        for key, combo in self.dropdowns.items():
            value = combo.get()
            if value:
                config[key] = value
        
        config['selected_fuels'] = self.selected_fuels
        config['fuel_weight_entries'] = self.fuel_weight_entries
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=4)
        
        messagebox.showinfo("Saved", f"Configuration saved to:\n{filename}")
    
    def open_config(self):
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    config = json.load(f)
                
                for key, value in config.items():
                    if key == 'selected_fuels':
                        self.selected_fuels = value
                        continue
                    if key == 'fuel_weight_entries':
                        self.fuel_weight_entries = value
                        continue
                    
                    if key in self.inputs:
                        if isinstance(self.inputs[key], str):
                            self.inputs[key] = value
                        else:
                            self.inputs[key].delete(0, tk.END)
                            self.inputs[key].insert(0, str(value))
                    elif key in self.dropdowns:
                        self.dropdowns[key].set(value)
                
                self.current_file = filename
                self.change_page(self.current_page)  # Refresh current page
                messagebox.showinfo("Loaded", f"Configuration loaded from:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading configuration:\n{str(e)}")
