import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import re

# Try to import ttkbootstrap for modern theming
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *

    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    TTKBOOTSTRAP_AVAILABLE = False
    print("Warning: ttkbootstrap not available. Using standard ttk.")

# Try to import CoolProp, handle gracefully if missing
try:
    import CoolProp.CoolProp as cp

    COOLPROP_AVAILABLE = True
except ImportError:
    COOLPROP_AVAILABLE = False
    print("Warning: CoolProp not available. Using fallback oxidizer list.")


class HybridRocketGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hybrid Rocket Model")
        self.root.geometry("1400x900")
        self.search_popup_active = False

        # Maximize the window
        self.root.state('zoomed')

        # Modern color scheme
        self.colors = {
            'bg_primary': '#f8f9fa',
            'bg_secondary': '#ffffff',
            'bg_sidebar': '#2c3e50',
            'bg_header': '#34495e',
            'accent': '#3498db',
            'accent_hover': '#2980b9',
            'text_primary': '#2c3e50',
            'text_secondary': '#7f8c8d',
            'text_light': '#ffffff',
            'success': '#27ae60',
            'error': '#e74c3c',
            'border': '#ecf0f1',
            'input_bg': '#ffffff',
        }

        # Variables for inputs
        self.inputs = {}
        self.dropdowns = {}
        self.current_page = 'configuration'

        # Load reactant lists
        self.load_reactant_lists()

        # Configure root
        self.root.configure(bg=self.colors['bg_primary'])

        # Define custom styles
        self.setup_styles()

        # Create main layout
        self.create_header()
        self.create_sidebar()

        # Content area
        self.content_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Show configuration page
        self.show_configuration_page()

    def setup_styles(self):
        """Configure modern styles for widgets"""
        if TTKBOOTSTRAP_AVAILABLE:
            # ttkbootstrap handles most styling automatically
            pass
        else:
            self.style = ttk.Style()
            self.style.theme_use('clam')

            # Button style
            self.style.configure("Modern.TButton",
                                 font=('Segoe UI', 10),
                                 padding=10,
                                 relief="flat",
                                 borderwidth=0,
                                 background=self.colors['accent'],
                                 foreground='white')
            self.style.map("Modern.TButton",
                           background=[('active', self.colors['accent_hover'])],
                           foreground=[('active', 'white')])

            # Sidebar button
            self.style.configure("Sidebar.TButton",
                                 font=('Segoe UI', 11),
                                 padding=12,
                                 relief="flat",
                                 borderwidth=0,
                                 background=self.colors['bg_sidebar'],
                                 foreground=self.colors['text_light'])

            # Combobox
            self.style.configure("Modern.TCombobox",
                                 font=('Segoe UI', 10),
                                 padding=5)

    def load_reactant_lists(self):
        """Load reactant lists from CEA_reactants.txt and CoolProp"""
        self.cea_reactants = []
        try:
            with open("CEA_reactants.txt", "r", encoding="utf-8") as f:
                self.cea_reactants = [line.strip() for line in f.readlines() if line.strip()]
            self.cea_reactants.sort()
        except FileNotFoundError:
            messagebox.showwarning("Warning", "CEA_reactants.txt not found. Using empty reactant list.")
            self.cea_reactants = []

        self.easy_cea_ox_list = ["Air", "CL2", "CL2(L)", "F2", "F2(L)", "H2O2(L)",
                                 "N2H4(L)", "N2O", "NH4NO3(I)", "O2", "O2(L)",
                                 "Select other options", "Custom with exploded formula"]

        self.easy_cea_fuel_list = ["CH4", "CH4(L)", "H2", "H2(L)", "RP-1", "paraffin",
                                   "Select other options", "Custom with exploded formula"]

        if COOLPROP_AVAILABLE:
            self.coolprop_fluids = cp.FluidsList()
        else:
            self.coolprop_fluids = ["NitrousOxide", "Oxygen", "Nitrogen", "Water",
                                    "CarbonDioxide", "Methane", "Hydrogen"]

    def explode_formula(self, formula):
        """Convert chemical formula to expanded format"""
        formula = formula.replace(" ", "")
        exploded_formula = ""
        prec = "1"

        for i, char in enumerate(formula):
            if char.isupper() and char.isalpha():
                if prec.isdigit():
                    exploded_formula = exploded_formula + " " + char
                else:
                    exploded_formula = exploded_formula + " " + "1" + " " + char
                prec = char
            elif char.islower() and char.isalpha():
                if prec.isupper() and prec.isalpha():
                    exploded_formula = exploded_formula + char
                prec = char
            elif char.isdigit():
                if prec.isalpha():
                    exploded_formula = exploded_formula + " " + char
                elif prec.isdigit():
                    exploded_formula = exploded_formula + char
                prec = char
            if i == (len(formula) - 1) and char.isalpha():
                exploded_formula = exploded_formula + " " + "1"

        return exploded_formula.strip()

    def show_search_popup(self, title, reactant_list, callback):
        """Show modern popup window with search functionality"""
        self.search_popup_active = True
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("550x650")
        popup.configure(bg=self.colors['bg_secondary'])
        popup.transient(self.root)
        popup.grab_set()

        def on_popup_close():
            self.search_popup_active = False
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", on_popup_close)

        # Header
        header = tk.Frame(popup, bg=self.colors['accent'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text=title, font=('Segoe UI', 16, 'bold'),
                 bg=self.colors['accent'], fg='white').pack(pady=15)

        # Search frame
        search_frame = tk.Frame(popup, bg=self.colors['bg_secondary'])
        search_frame.pack(fill=tk.X, padx=30, pady=20)

        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var,
                                font=('Segoe UI', 11), relief=tk.FLAT,
                                bg=self.colors['input_bg'], bd=2)
        search_entry.pack(fill=tk.X, ipady=8)
        search_entry.focus()

        # Listbox with modern styling
        list_frame = tk.Frame(popup, bg=self.colors['bg_secondary'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                             font=('Segoe UI', 10), height=20, relief=tk.FLAT,
                             bg=self.colors['input_bg'], bd=0,
                             highlightthickness=1, highlightcolor=self.colors['accent'],
                             selectbackground=self.colors['accent'],
                             selectforeground='white')
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        def update_listbox(*args):
            search_term = search_var.get().lower()
            listbox.delete(0, tk.END)
            filtered = [item for item in reactant_list if search_term in item.lower()]
            for item in filtered:
                listbox.insert(tk.END, item)

        search_var.trace('w', update_listbox)
        update_listbox()

        def on_select():
            selection = listbox.curselection()
            if selection:
                selected_item = listbox.get(selection[0])
                self.search_popup_active = False
                callback(selected_item)
                popup.destroy()
            else:
                messagebox.showwarning("No Selection", "Please select an item.")

        # Modern button
        btn_frame = tk.Frame(popup, bg=self.colors['bg_secondary'])
        btn_frame.pack(pady=(0, 20))

        if TTKBOOTSTRAP_AVAILABLE:
            select_btn = ttk.Button(btn_frame, text="Select", bootstyle="primary", command=on_select)
        else:
            select_btn = tk.Button(btn_frame, text="Select", font=('Segoe UI', 11),
                                   bg=self.colors['accent'], fg='white',
                                   relief=tk.FLAT, padx=30, pady=10,
                                   cursor='hand2', command=on_select)
        select_btn.pack()

        listbox.bind('<Double-Button-1>', lambda e: on_select())
        popup.bind('<Return>', lambda e: on_select())

    def show_custom_formula_popup(self, callback):
        """Show modern popup for custom chemical formula input"""
        popup = tk.Toplevel(self.root)
        popup.title("Custom Chemical Formula")
        popup.geometry("600x500")
        popup.configure(bg=self.colors['bg_secondary'])
        popup.transient(self.root)
        popup.grab_set()

        # Header
        header = tk.Frame(popup, bg=self.colors['accent'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="Custom Chemical Formula", font=('Segoe UI', 16, 'bold'),
                 bg=self.colors['accent'], fg='white').pack(pady=15)

        entries = {}
        content = tk.Frame(popup, bg=self.colors['bg_secondary'])
        content.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)

        fields = [
            ("Chemical Name:", "name", None),
            ("Formula (e.g., H2O2):", "formula", None),
            ("Temperature [K]:", "temp", "optional"),
            ("Specific Enthalpy [kJ/mol]:", "enthalpy", "optional")
        ]

        for label_text, key, note in fields:
            row = tk.Frame(content, bg=self.colors['bg_secondary'])
            row.pack(fill=tk.X, pady=10)

            label = tk.Label(row, text=label_text, font=('Segoe UI', 10),
                             bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                             anchor='w')
            label.pack(anchor='w')

            entries[key] = tk.Entry(row, font=('Segoe UI', 11), relief=tk.FLAT,
                                    bg=self.colors['input_bg'], bd=1)
            entries[key].pack(fill=tk.X, ipady=6, pady=(5, 0))

        error_label = tk.Label(content, text="", font=('Segoe UI', 9),
                               bg=self.colors['bg_secondary'], fg=self.colors['error'])
        error_label.pack(pady=10)

        def on_confirm():
            name = entries['name'].get().strip()
            formula = entries['formula'].get().strip()
            temp = entries['temp'].get().strip()
            enthalpy = entries['enthalpy'].get().strip()

            if not name:
                error_label.config(text="Please enter a chemical name")
                return
            if not formula:
                error_label.config(text="Please enter a formula")
                return

            try:
                temp_val = float(temp) if temp else None
                if temp_val is not None and temp_val <= 0:
                    error_label.config(text="Temperature must be > 0")
                    return
            except ValueError:
                error_label.config(text="Invalid temperature value")
                return

            try:
                enthalpy_val = float(enthalpy) if enthalpy else None
            except ValueError:
                error_label.config(text="Invalid enthalpy value")
                return

            try:
                exploded = self.explode_formula(formula)
            except Exception as e:
                error_label.config(text=f"Invalid formula format: {str(e)}")
                return

            result = {
                'name': name,
                'formula': formula,
                'exploded_formula': exploded,
                'temperature': temp_val,
                'enthalpy': enthalpy_val
            }
            callback(result)
            popup.destroy()

        btn_frame = tk.Frame(content, bg=self.colors['bg_secondary'])
        btn_frame.pack(pady=20)

        if TTKBOOTSTRAP_AVAILABLE:
            confirm_btn = ttk.Button(btn_frame, text="Confirm", bootstyle="success", command=on_confirm)
        else:
            confirm_btn = tk.Button(btn_frame, text="Confirm", font=('Segoe UI', 11),
                                    bg=self.colors['success'], fg='white',
                                    relief=tk.FLAT, padx=30, pady=10,
                                    cursor='hand2', command=on_confirm)
        confirm_btn.pack()

    def create_header(self):
        """Create modern header"""
        header = tk.Frame(self.root, bg=self.colors['bg_header'], height=70)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        title = tk.Label(header, text="HYBRID ROCKET MODEL",
                         font=('Segoe UI', 20, 'bold'),
                         bg=self.colors['bg_header'], fg='white')
        title.pack(side=tk.LEFT, padx=30, pady=20)

        # Menu button on the right
        menu_frame = tk.Frame(header, bg=self.colors['bg_header'])
        menu_frame.pack(side=tk.RIGHT, padx=30)

        if TTKBOOTSTRAP_AVAILABLE:
            self.menu_button = ttk.Button(menu_frame, text="⋮ Menu",
                                          bootstyle="secondary-outline",
                                          command=self.toggle_menu)
        else:
            self.menu_button = tk.Button(menu_frame, text="⋮ Menu",
                                         font=('Segoe UI', 10),
                                         bg=self.colors['bg_header'],
                                         fg='white', relief=tk.FLAT,
                                         cursor='hand2',
                                         command=self.toggle_menu)
        self.menu_button.pack()

    def create_sidebar(self):
        """Create modern sidebar"""
        sidebar = tk.Frame(self.root, bg=self.colors['bg_sidebar'], width=250)  # Increased width
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Add some padding at top
        tk.Frame(sidebar, bg=self.colors['bg_sidebar'], height=20).pack()

        self.page_buttons = {}
        pages = [
            ('configuration', '⚙ Configuration'),
            ('optimization', '📊 Optimization'),
            ('mission', '🚀 Mission'),
            ('output', '📈 Output')
        ]

        for page, label in pages:
            btn_frame = tk.Frame(sidebar, bg=self.colors['bg_sidebar'])
            btn_frame.pack(fill=tk.X, padx=10, pady=5)

            btn = tk.Button(btn_frame, text=label,
                            font=('Segoe UI', 11),
                            bg=self.colors['bg_sidebar'],
                            fg=self.colors['text_light'],
                            activebackground=self.colors['accent'],
                            activeforeground='white',
                            relief=tk.FLAT,
                            anchor='w',
                            padx=20, pady=12,
                            cursor='hand2',
                            command=lambda p=page: self.change_page(p))
            btn.pack(fill=tk.X)

            # Hover effect
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=self.colors['accent']))
            btn.bind('<Leave>', lambda e, b=btn, p=page: b.config(
                bg=self.colors['accent'] if self.current_page == p else self.colors['bg_sidebar']))

            self.page_buttons[page] = btn

        # Update initial button state
        self.page_buttons['configuration'].config(bg=self.colors['accent'])

    def toggle_menu(self):
        """Toggle dropdown menu"""
        if hasattr(self, 'dropdown_frame') and self.dropdown_frame:
            self.dropdown_frame.destroy()
            self.dropdown_frame = None
        else:
            x = self.menu_button.winfo_rootx()
            y = self.menu_button.winfo_rooty() + self.menu_button.winfo_height()

            self.dropdown_frame = tk.Toplevel(self.root)
            self.dropdown_frame.overrideredirect(True)
            self.dropdown_frame.geometry(f"160x120+{x}+{y}")
            self.dropdown_frame.configure(bg=self.colors['bg_secondary'])

            # Add shadow effect (simple border)
            self.dropdown_frame.configure(highlightthickness=1,
                                          highlightbackground=self.colors['border'])

            menu_items = [
                ("💾 Save", self.save_config),
                ("💾 Save As", self.save_config_as),
                ("📂 Open", self.open_config)
            ]

            for text, cmd in menu_items:
                btn = tk.Button(self.dropdown_frame, text=text,
                                font=('Segoe UI', 10),
                                bg=self.colors['bg_secondary'],
                                fg=self.colors['text_primary'],
                                activebackground=self.colors['border'],
                                relief=tk.FLAT, anchor='w',
                                padx=15, pady=8,
                                cursor='hand2',
                                command=lambda c=cmd: (c(), self.toggle_menu()))
                btn.pack(fill=tk.X)

                # Hover effect
                btn.bind('<Enter>', lambda e, b=btn: b.config(bg=self.colors['border']))
                btn.bind('<Leave>', lambda e, b=btn: b.config(bg=self.colors['bg_secondary']))

            self.dropdown_frame.bind("<FocusOut>", lambda e: self.toggle_menu())

    def change_page(self, page):
        """Change active page"""
        # Update button colors
        for p, btn in self.page_buttons.items():
            if p == page:
                btn.config(bg=self.colors['accent'])
            else:
                btn.config(bg=self.colors['bg_sidebar'])

        self.current_page = page

        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if page == 'configuration':
            self.show_configuration_page()
        else:
            placeholder = tk.Frame(self.content_frame, bg=self.colors['bg_primary'])
            placeholder.pack(expand=True, fill=tk.BOTH)

            label = tk.Label(placeholder, text=f"{page.upper()}\nComing soon",
                             font=('Segoe UI', 24), bg=self.colors['bg_primary'],
                             fg=self.colors['text_secondary'])
            label.pack(expand=True)

    def show_configuration_page(self):
        """Show modern configuration page"""
        # Main container with padding
        # Create a frame to center the content
        center_container = tk.Frame(self.content_frame, bg=self.colors['bg_primary'])
        center_container.pack(fill=tk.BOTH, expand=True)
        
        # Main container with max width constraint
        main_container = tk.Frame(center_container, bg=self.colors['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=50, pady=30, anchor='center')
        
        # Set a minimum width for the main container
        main_container.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        min_width = int(screen_width * 0.7)  # 70% of screen width
        main_container.configure(width=min_width)

        # Title
        title = tk.Label(main_container, text="Configuration",
                         font=('Segoe UI', 24, 'bold'),
                         bg=self.colors['bg_primary'],
                         fg=self.colors['text_primary'])
        title.pack(anchor='w', pady=(0, 20))

        # Scrollable canvas
        canvas = tk.Canvas(main_container, bg=self.colors['bg_primary'],
                           highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient="vertical",
                                 command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_primary'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Create sections
        self.create_line_section(scrollable_frame)
        self.create_fuel_oxidiser_section(scrollable_frame)
        self.create_injector_section(scrollable_frame)
        self.create_nozzle_section(scrollable_frame)

        # Save button
        save_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_primary'])
        save_frame.pack(fill=tk.X, pady=30)

        if TTKBOOTSTRAP_AVAILABLE:
            self.save_btn = ttk.Button(save_frame, text="Save Configuration",
                                       bootstyle="success",
                                       command=self.validate_and_save)
        else:
            self.save_btn = tk.Button(save_frame, text="Save Configuration",
                                      font=('Segoe UI', 12, 'bold'),
                                      bg=self.colors['success'], fg='white',
                                      relief=tk.FLAT, padx=30, pady=12,
                                      cursor='hand2',
                                      command=self.validate_and_save)
        self.save_btn.pack()

        self.validate_inputs()

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            if self.search_popup_active:
                return
            widget = event.widget
            while widget is not None:
                if isinstance(widget, tk.Listbox):
                    parent = widget.master
                    if parent and parent.master and parent.master.winfo_class() == 'TCombobox':
                        return
                widget = widget.master
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def create_card(self, parent, title, show_import=False):
        """Create a modern card-style section"""
        # Create a container to center the card
        container = tk.Frame(parent, bg=self.colors['bg_primary'])
        container.pack(fill=tk.X, pady=20)
        
        # Create the card with a maximum width
        card = tk.Frame(container, bg=self.colors['bg_secondary'],
                       relief=tk.FLAT, bd=0)
        card.pack(fill=tk.X, padx=100)  # Add horizontal padding to limit width

        # Add subtle border
        card.configure(highlightthickness=1, highlightbackground=self.colors['border'])

        header = tk.Frame(card, bg=self.colors['bg_secondary'])
        header.pack(fill=tk.X, padx=25, pady=(20, 15))

        title_label = tk.Label(header, text=title, font=('Segoe UI', 14, 'bold'),
                               bg=self.colors['bg_secondary'],
                               fg=self.colors['text_primary'])
        title_label.pack(side=tk.LEFT)

        if show_import:
            if TTKBOOTSTRAP_AVAILABLE:
                import_btn = ttk.Button(header, text="Import Line",
                                        bootstyle="secondary-outline",
                                        command=self.import_line_placeholder)
            else:
                import_btn = tk.Button(header, text="Import Line",
                                       font=('Segoe UI', 9),
                                       bg=self.colors['bg_secondary'],
                                       fg=self.colors['accent'],
                                       relief=tk.FLAT, cursor='hand2',
                                       command=self.import_line_placeholder)
            import_btn.pack(side=tk.RIGHT)

        fields_frame = tk.Frame(card, bg=self.colors['bg_secondary'])
        fields_frame.pack(fill=tk.X, padx=40, pady=(0, 30))  # Increased padding

        return fields_frame

    def create_line_section(self, parent):
        self.create_card(parent, "Line", show_import=True)

    def create_fuel_oxidiser_section(self, parent):
        fields_frame = self.create_card(parent, "Fuel & Oxidiser")

        self.create_oxidizer_fields(fields_frame)
        self.create_fuel_fields(fields_frame)
        self.create_modern_float_field(fields_frame, "Fuel & Oxidiser", "a", "a",
                                       min_value=0, exclusive=True)
        self.create_modern_float_field(fields_frame, "Fuel & Oxidiser", "n", "n")
        self.create_modern_float_field(fields_frame, "Fuel & Oxidiser", "rho.fuel",
                                       "ρF (kg/m³)", min_value=0, exclusive=True)

    def create_oxidizer_fields(self, parent):
        # Main oxidizer dropdown
        self.create_modern_dropdown(parent, "Oxidizer:", "Fuel & Oxidiser_Oxidizer",
                                    self.easy_cea_ox_list,
                                    lambda: self.on_oxidizer_change())

        # Weight fraction (readonly)
        row = tk.Frame(parent, bg=self.colors['bg_secondary'])
        row.pack(fill=tk.X, pady=8)

        label = tk.Label(row, text="Weight fraction:", font=('Segoe UI', 10),
                         bg=self.colors['bg_secondary'],
                         fg=self.colors['text_secondary'])
        label.pack(anchor='w', pady=(0, 5))

        entry = tk.Entry(row, font=('Segoe UI', 11), relief=tk.FLAT,
                         bg='#f0f0f0', bd=0, state='readonly')
        entry.insert(0, "100")
        entry.pack(fill=tk.X, ipady=8)

        self.inputs["Fuel & Oxidiser_Oxidizer_WeightFraction"] = entry

        # Container for dynamic fields
        self.oxidizer_dynamic_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        self.oxidizer_dynamic_frame.pack(fill=tk.X)

    def on_oxidizer_change(self):
        for widget in self.oxidizer_dynamic_frame.winfo_children():
            widget.destroy()

        oxidizer = self.dropdowns["Fuel & Oxidiser_Oxidizer"].get()

        if oxidizer == "Select other options":
            def callback(selected):
                self.dropdowns["Fuel & Oxidiser_Oxidizer"].set(selected)
                self.on_oxidizer_change()

            self.show_search_popup("Select Oxidizer", self.cea_reactants, callback)
            return

        elif oxidizer == "Custom with exploded formula":
            def callback(result):
                self.inputs["Fuel & Oxidiser_Oxidizer_CustomName"] = result['name']
                self.inputs["Fuel & Oxidiser_Oxidizer_ExpandedFormula"] = result['exploded_formula']
                self.dropdowns["Fuel & Oxidiser_Oxidizer"].set(f"Custom: {result['name']}")
                self.create_oxidizer_dynamic_fields(result['temperature'], result['enthalpy'])

            self.show_custom_formula_popup(callback)
            return

        self.create_oxidizer_dynamic_fields()

    def create_oxidizer_dynamic_fields(self, temp_default=None, enthalpy_default=None):
        self.create_modern_float_field(self.oxidizer_dynamic_frame, "Fuel & Oxidiser",
                                       "Oxidizer_Temperature", "Temperature [K]",
                                       default=temp_default)
        self.create_modern_float_field(self.oxidizer_dynamic_frame, "Fuel & Oxidiser",
                                       "Oxidizer_SpecificEnthalpy",
                                       "Specific Enthalpy [kJ/mol]",
                                       default=enthalpy_default)
        self.validate_inputs()

    def create_fuel_fields(self, parent):
        self.create_modern_dropdown(parent, "Fuel:", "Fuel & Oxidiser_Fuel",
                                    self.easy_cea_fuel_list,
                                    lambda: self.on_fuel_change())

        # Fuel weight fraction
        self.create_modern_float_field(parent, "Fuel & Oxidiser",
                                       "Fuel_WeightFraction",
                                       "Fuel Weight fraction",
                                       validation_func=self.validate_fuel_weight_fraction)

        self.fuel_dynamic_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        self.fuel_dynamic_frame.pack(fill=tk.X)

    def on_fuel_change(self):
        for widget in self.fuel_dynamic_frame.winfo_children():
            widget.destroy()

        fuel = self.dropdowns["Fuel & Oxidiser_Fuel"].get()

        if fuel == "Select other options":
            def callback(selected):
                self.dropdowns["Fuel & Oxidiser_Fuel"].set(selected)
                self.on_fuel_change()

            self.show_search_popup("Select Fuel", self.cea_reactants, callback)
            return

        elif fuel == "Custom with exploded formula":
            def callback(result):
                self.inputs["Fuel & Oxidiser_Fuel_CustomName"] = result['name']
                self.inputs["Fuel & Oxidiser_Fuel_ExpandedFormula"] = result['exploded_formula']
                self.dropdowns["Fuel & Oxidiser_Fuel"].set(f"Custom: {result['name']}")
                self.create_fuel_dynamic_fields(result['temperature'], result['enthalpy'])

            self.show_custom_formula_popup(callback)
            return

        if fuel == "paraffin":
            self.create_fuel_dynamic_fields(533.0, -1860.6)
        else:
            self.create_fuel_dynamic_fields()

    def create_fuel_dynamic_fields(self, temp_default=None, enthalpy_default=None):
        self.create_modern_float_field(self.fuel_dynamic_frame, "Fuel & Oxidiser",
                                       "Fuel_Temperature", "Fuel Temperature [K]",
                                       default=temp_default)
        self.create_modern_float_field(self.fuel_dynamic_frame, "Fuel & Oxidiser",
                                       "Fuel_SpecificEnthalpy",
                                       "Fuel Specific Enthalpy [kJ/mol]",
                                       default=enthalpy_default)
        self.validate_inputs()

    def validate_fuel_weight_fraction(self):
        entry = self.inputs["Fuel & Oxidiser_Fuel_WeightFraction"]
        value = entry.get().strip()

        is_valid = False
        if value:
            try:
                fractions = [float(x.strip()) for x in value.split(',')]
                if all(f > 0 for f in fractions) and abs(sum(fractions) - 100) < 0.01:
                    is_valid = True
            except ValueError:
                pass

        if is_valid:
            entry.configure(bg='#e8f5e9', highlightthickness=2,
                            highlightbackground=self.colors['success'],
                            highlightcolor=self.colors['success'])
        elif value:
            entry.configure(bg='#ffebee', highlightthickness=2,
                            highlightbackground=self.colors['error'],
                            highlightcolor=self.colors['error'])
        else:
            entry.configure(bg=self.colors['input_bg'], highlightthickness=1,
                            highlightbackground=self.colors['border'],
                            highlightcolor=self.colors['accent'])

        self.validate_inputs()

    def create_injector_section(self, parent):
        fields_frame = self.create_card(parent, "Injector")

        self.create_modern_float_field(fields_frame, "Injector", "CD", "CD",
                                       min_value=0, exclusive=True)
        self.create_modern_float_field(fields_frame, "Injector", "Gox.min",
                                       "Gox.min [kg/s/m²]",
                                       min_value=0, exclusive=True)
        self.create_modern_float_field(fields_frame, "Injector", "Gox.max",
                                       "Gox.max [kg/s/m²]",
                                       min_value=0, exclusive=True)

    def create_nozzle_section(self, parent):
        fields_frame = self.create_card(parent, "Nozzle")
        self.create_epsilon_field(fields_frame)

    def create_epsilon_field(self, parent):
        row = tk.Frame(parent, bg=self.colors['bg_secondary'])
        row.pack(fill=tk.X, pady=8)

        label = tk.Label(row, text="ε (eps):", font=('Segoe UI', 10),
                         bg=self.colors['bg_secondary'],
                         fg=self.colors['text_secondary'])
        label.pack(anchor='w', pady=(0, 5))

        entry = tk.Entry(row, font=('Segoe UI', 11), relief=tk.FLAT,
                         bg=self.colors['input_bg'], bd=0,
                         highlightthickness=1,
                         highlightbackground=self.colors['border'],
                         highlightcolor=self.colors['accent'])
        entry.pack(fill=tk.X, ipady=8)
        entry.bind('<KeyRelease>', lambda e: self.validate_epsilon())

        self.inputs["Nozzle_epsilon"] = entry

    def validate_epsilon(self):
        entry = self.inputs["Nozzle_epsilon"]
        value = entry.get().strip()

        is_valid = False
        if value:
            if value.lower() == "adapt":
                is_valid = True
            else:
                try:
                    if float(value) > 1:
                        is_valid = True
                except ValueError:
                    pass

        if is_valid:
            entry.configure(bg='#e8f5e9', highlightthickness=2,
                            highlightbackground=self.colors['success'],
                            highlightcolor=self.colors['success'])
        elif value:
            entry.configure(bg='#ffebee', highlightthickness=2,
                            highlightbackground=self.colors['error'],
                            highlightcolor=self.colors['error'])
        else:
            entry.configure(bg=self.colors['input_bg'], highlightthickness=1,
                            highlightbackground=self.colors['border'],
                            highlightcolor=self.colors['accent'])

        self.validate_inputs()

    def create_modern_dropdown(self, parent, label_text, key, values, callback):
        row = tk.Frame(parent, bg=self.colors['bg_secondary'])
        row.pack(fill=tk.X, pady=12)  # Increased vertical spacing

        # Create a container for the label and dropdown
        field_container = tk.Frame(row, bg=self.colors['bg_secondary'])
        field_container.pack(fill=tk.X, padx=20)  # Add padding to create margins
        
        label = tk.Label(field_container, text=label_text, font=('Segoe UI', 10),
                         bg=self.colors['bg_secondary'],
                         fg=self.colors['text_secondary'])
        label.pack(anchor='w', pady=(0, 5))

        if TTKBOOTSTRAP_AVAILABLE:
            combo = ttk.Combobox(row, font=('Segoe UI', 11),
                                 values=values, state='readonly')
        else:
            combo = ttk.Combobox(row, font=('Segoe UI', 11),
                                 values=values, state='readonly')
        combo.pack(fill=tk.X, ipady=6)
        combo.bind('<<ComboboxSelected>>', lambda e: callback())

        self.dropdowns[key] = combo

    def create_modern_float_field(self, parent, section, var_name, display_name,
                                  min_value=None, max_value=None, exclusive=False,
                                  default=None, validation_func=None):
        row = tk.Frame(parent, bg=self.colors['bg_secondary'])
        row.pack(fill=tk.X, pady=8)
        
        # Create a container for the input field with margins
        field_container = tk.Frame(row, bg=self.colors['bg_secondary'])
        field_container.pack(fill=tk.X, padx=20)

        label = tk.Label(row, text=display_name + ":", font=('Segoe UI', 10),
                         bg=self.colors['bg_secondary'],
                         fg=self.colors['text_secondary'])
        label.pack(anchor='w', pady=(0, 5))

        entry = tk.Entry(row, font=('Segoe UI', 11), relief=tk.FLAT,
                         bg=self.colors['input_bg'], bd=0,
                         highlightthickness=1,
                         highlightbackground=self.colors['border'],
                         highlightcolor=self.colors['accent'])
        entry.pack(fill=tk.X, ipady=8)

        if default:
            entry.insert(0, str(default))

        entry.validation_params = {
            'min_value': min_value,
            'max_value': max_value,
            'exclusive': exclusive
        }

        if validation_func:
            entry.bind('<KeyRelease>', lambda e: validation_func())
        else:
            entry.bind('<KeyRelease>', lambda e: self.validate_single_input(entry))

        self.inputs[f"{section}_{var_name}"] = entry

    def validate_single_input(self, entry):
        value = entry.get().strip()
        is_valid = False

        if value:
            field_key = None
            for key, val in self.inputs.items():
                if val == entry:
                    field_key = key
                    break

            if field_key and ("CustomName" in field_key or "ExpandedFormula" in field_key):
                is_valid = len(value) > 0
            else:
                try:
                    float_val = float(value)
                    is_valid = True

                    if hasattr(entry, 'validation_params'):
                        params = entry.validation_params

                        if params.get('min_value') is not None:
                            if params.get('exclusive'):
                                is_valid = is_valid and float_val > params['min_value']
                            else:
                                is_valid = is_valid and float_val >= params['min_value']

                        if params.get('max_value') is not None:
                            if params.get('exclusive'):
                                is_valid = is_valid and float_val < params['max_value']
                            else:
                                is_valid = is_valid and float_val <= params['max_value']
                except ValueError:
                    is_valid = False

        if is_valid:
            entry.configure(bg='#e8f5e9', highlightthickness=2,
                            highlightbackground=self.colors['success'],
                            highlightcolor=self.colors['success'])
        elif value:
            entry.configure(bg='#ffebee', highlightthickness=2,
                            highlightbackground=self.colors['error'],
                            highlightcolor=self.colors['error'])
        else:
            entry.configure(bg=self.colors['input_bg'], highlightthickness=1,
                            highlightbackground=self.colors['border'],
                            highlightcolor=self.colors['accent'])

        self.validate_inputs()

    def validate_inputs(self):
        all_valid = True

        for key, entry in self.inputs.items():
            if isinstance(entry, str):
                continue

            value = entry.get().strip()
            if not value:
                all_valid = False
                continue

            if "CustomName" in key or "ExpandedFormula" in key:
                if not value:
                    all_valid = False
            else:
                try:
                    float_val = float(value)

                    if hasattr(entry, 'validation_params'):
                        params = entry.validation_params

                        if params.get('min_value') is not None:
                            if params.get('exclusive'):
                                if not (float_val > params['min_value']):
                                    all_valid = False
                            else:
                                if not (float_val >= params['min_value']):
                                    all_valid = False

                        if params.get('max_value') is not None:
                            if params.get('exclusive'):
                                if not (float_val < params['max_value']):
                                    all_valid = False
                            else:
                                if not (float_val <= params['max_value']):
                                    all_valid = False
                except ValueError:
                    all_valid = False

        if "Nozzle_epsilon" in self.inputs:
            eps_value = self.inputs["Nozzle_epsilon"].get().strip()
            if eps_value:
                if eps_value.lower() != "adapt":
                    try:
                        if float(eps_value) <= 1:
                            all_valid = False
                    except ValueError:
                        all_valid = False
            else:
                all_valid = False

        if "Fuel & Oxidiser_Fuel_WeightFraction" in self.inputs:
            value = self.inputs["Fuel & Oxidiser_Fuel_WeightFraction"].get().strip()
            if value:
                try:
                    fractions = [float(x.strip()) for x in value.split(',')]
                    if not (all(f > 0 for f in fractions) and abs(sum(fractions) - 100) < 0.01):
                        all_valid = False
                except ValueError:
                    all_valid = False
            else:
                all_valid = False

        for key, combo in self.dropdowns.items():
            if not combo.get():
                all_valid = False

        # Update save button
        if hasattr(self, 'save_btn'):
            if TTKBOOTSTRAP_AVAILABLE:
                if all_valid:
                    self.save_btn.configure(bootstyle="success")
                else:
                    self.save_btn.configure(bootstyle="danger")
            else:
                if all_valid:
                    self.save_btn.configure(bg=self.colors['success'])
                else:
                    self.save_btn.configure(bg=self.colors['error'])

    def import_line_placeholder(self):
        messagebox.showinfo("Info", "Import line function in development")

    def validate_and_save(self):
        config = {}
        all_valid = True

        for key, entry in self.inputs.items():
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

        for key, combo in self.dropdowns.items():
            value = combo.get()
            if not value:
                all_valid = False
                break
            config[key] = value

        if all_valid:
            messagebox.showinfo("Success", "Configuration validated! All fields are valid.")
        else:
            messagebox.showerror("Error", "Some fields are empty or invalid.")

    def save_config(self):
        if not hasattr(self, 'current_file'):
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
                        config[key] = float(value)
                    except ValueError:
                        config[key] = value

        for key, combo in self.dropdowns.items():
            value = combo.get()
            if value:
                config[key] = value

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
                    if key in self.inputs:
                        if isinstance(self.inputs[key], str):
                            self.inputs[key] = value
                        else:
                            self.inputs[key].delete(0, tk.END)
                            self.inputs[key].insert(0, str(value))
                    elif key in self.dropdowns:
                        self.dropdowns[key].set(value)

                if "Fuel & Oxidiser_Oxidizer" in self.dropdowns:
                    self.on_oxidizer_change()
                if "Fuel & Oxidiser_Fuel" in self.dropdowns:
                    self.on_fuel_change()

                self.current_file = filename
                self.validate_inputs()
                messagebox.showinfo("Loaded", f"Configuration loaded from:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading configuration:\n{str(e)}")


if __name__ == "__main__":
    if TTKBOOTSTRAP_AVAILABLE:
        root = ttk.Window(themename="cosmo")  # Modern light theme
    else:
        root = tk.Tk()

    app = HybridRocketGUI(root)
    root.mainloop()