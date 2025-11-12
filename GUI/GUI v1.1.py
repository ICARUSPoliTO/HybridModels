import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import re

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
        self.root.title("hybrid model")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')
        self.search_popup_active = False  # Track if search popup is open

        # Maximize the window
        self.root.state('zoomed')

        # Colors
        self.bg_dark = '#2b2b2b'
        self.bg_medium = '#3c3c3c'
        self.bg_light = '#8c8c8c'
        self.bg_active = '#5c5c5c'
        self.text_color = 'white'
        self.button_inactive = '#a0a0a0'
        self.button_active = '#6c6c6c'

        # Variables for inputs
        self.inputs = {}
        self.dropdowns = {}
        self.current_page = 'configuration'
        
        # Variables for multi-fuel selection
        self.selected_fuels = []  # List of selected fuel names
        self.fuel_weight_entries = {}  # Dict to store weight entries for each fuel

        # Load reactant lists
        self.load_reactant_lists()

        # Define custom styles
        self.style = ttk.Style()
        self.style.configure("Rounded.TButton",
                             font=('Arial', 11),
                             padding=6,
                             relief="flat",
                             borderwidth=0,
                             background=self.button_inactive,
                             foreground='black')
        self.style.map("Rounded.TButton",
                       background=[('active', self.button_active), ('!active', self.button_inactive)],
                       foreground=[('active', 'white'), ('!active', 'black')])

        # Menu and navigation
        self.create_header()
        self.create_sidebar()

        # Content area
        self.content_frame = tk.Frame(self.root, bg=self.bg_dark)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Show configuration page
        self.show_configuration_page()

    def load_reactant_lists(self):
        """Load reactant lists from CEA_reactants.txt and CoolProp"""
        # Load CEA reactants from file
        self.cea_reactants = []
        try:
            with open("CEA_reactants.txt", "r", encoding="utf-8") as f:
                self.cea_reactants = [line.strip() for line in f.readlines() if line.strip()]
            self.cea_reactants.sort()
        except FileNotFoundError:
            messagebox.showwarning("Warning", "CEA_reactants.txt not found. Using empty reactant list.")
            self.cea_reactants = []

        # Easy access lists for common oxidizers and fuels
        self.easy_cea_ox_list = ["Air", "CL2", "CL2(L)", "F2", "F2(L)", "H2O2(L)",
                                 "N2H4(L)", "N2O", "NH4NO3(I)", "O2", "O2(L)",
                                 "Select other options", "Custom with exploded formula"]

        self.easy_cea_fuel_list = ["CH4", "CH4(L)", "H2", "H2(L)", "RP-1", "paraffin",
                                   "Select other options", "Custom with exploded formula"]

        # CoolProp fluids list
        if COOLPROP_AVAILABLE:
            self.coolprop_fluids = cp.FluidsList()
        else:
            # Fallback list of common fluids
            self.coolprop_fluids = ["NitrousOxide", "Oxygen", "Nitrogen", "Water",
                                    "CarbonDioxide", "Methane", "Hydrogen"]

    def explode_formula(self, formula):
        """Convert chemical formula to expanded format (e.g., H2O2 -> H 2 O 2)"""
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

        exploded_formula = exploded_formula.strip()
        return exploded_formula

    def show_search_popup(self, title, reactant_list, callback, multi_select=False):
        """Show popup window with search functionality for reactant selection"""
        self.search_popup_active = True  # Track popup state
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("500x600")
        popup.configure(bg=self.bg_medium)
        popup.transient(self.root)
        popup.grab_set()
        
        # Bind the popup destruction to update the tracking state
        def on_popup_close():
            self.search_popup_active = False
            popup.destroy()
        popup.protocol("WM_DELETE_WINDOW", on_popup_close)

        # Search frame
        search_frame = tk.Frame(popup, bg=self.bg_medium)
        search_frame.pack(fill=tk.X, padx=20, pady=20)

        tk.Label(search_frame, text="Search:", font=('Arial', 11),
                 bg=self.bg_medium, fg=self.text_color).pack(side=tk.LEFT, padx=(0, 10))

        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var,
                                font=('Arial', 11), width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Listbox with scrollbar
        list_frame = tk.Frame(popup, bg=self.bg_medium)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Set selectmode based on multi_select parameter
        selectmode = tk.MULTIPLE if multi_select else tk.SINGLE
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                             font=('Arial', 10), height=20, selectmode=selectmode)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # Populate listbox
        def update_listbox(*args):
            search_term = search_var.get().lower()
            listbox.delete(0, tk.END)

            filtered = [item for item in reactant_list if search_term in item.lower()]
            for item in filtered:
                listbox.insert(tk.END, item)

        search_var.trace('w', update_listbox)
        update_listbox()

        # Select button
        def on_select():
            selection = listbox.curselection()
            if selection:
                if multi_select:
                    selected_items = [listbox.get(i) for i in selection]
                    self.search_popup_active = False
                    callback(selected_items)
                    popup.destroy()
                else:
                    selected_item = listbox.get(selection[0])
                    self.search_popup_active = False
                    callback(selected_item)
                    popup.destroy()
            else:
                messagebox.showwarning("No Selection", "Please select an item.")        
        select_btn = ttk.Button(popup, text="Select", style="Rounded.TButton", command=on_select)
        select_btn.pack(pady=(0, 20))

        # Allow double-click to select (only for single selection)
        if not multi_select:
            listbox.bind('<Double-Button-1>', lambda e: on_select())

    def show_custom_formula_popup(self, callback):
        """Show popup for custom chemical formula input"""
        popup = tk.Toplevel(self.root)
        popup.title("Custom Chemical Formula")
        popup.geometry("500x400")
        popup.configure(bg=self.bg_medium)
        popup.transient(self.root)
        popup.grab_set()

        entries = {}

        # Chemical name
        row = tk.Frame(popup, bg=self.bg_medium)
        row.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(row, text="Chemical Name:", font=('Arial', 11),
                 bg=self.bg_medium, fg=self.text_color, width=20, anchor='w').pack(side=tk.LEFT)
        entries['name'] = tk.Entry(row, font=('Arial', 11), width=25)
        entries['name'].pack(side=tk.LEFT, padx=10)

        # Formula
        row = tk.Frame(popup, bg=self.bg_medium)
        row.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(row, text="Formula (e.g., H2O2):", font=('Arial', 11),
                 bg=self.bg_medium, fg=self.text_color, width=20, anchor='w').pack(side=tk.LEFT)
        entries['formula'] = tk.Entry(row, font=('Arial', 11), width=25)
        entries['formula'].pack(side=tk.LEFT, padx=10)

        # Temperature
        row = tk.Frame(popup, bg=self.bg_medium)
        row.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(row, text="Temperature [K]:", font=('Arial', 11),
                 bg=self.bg_medium, fg=self.text_color, width=20, anchor='w').pack(side=tk.LEFT)
        entries['temp'] = tk.Entry(row, font=('Arial', 11), width=25)
        entries['temp'].pack(side=tk.LEFT, padx=10)

        # Enthalpy
        row = tk.Frame(popup, bg=self.bg_medium)
        row.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(row, text="Specific Enthalpy [kJ/mol]:", font=('Arial', 11),
                 bg=self.bg_medium, fg=self.text_color, width=20, anchor='w').pack(side=tk.LEFT)
        entries['enthalpy'] = tk.Entry(row, font=('Arial', 11), width=25)
        entries['enthalpy'].pack(side=tk.LEFT, padx=10)

        error_label = tk.Label(popup, text="", font=('Arial', 10),
                               bg=self.bg_medium, fg='red')
        error_label.pack(pady=10)

        def on_confirm():
            name = entries['name'].get().strip()
            formula = entries['formula'].get().strip()
            temp = entries['temp'].get().strip()
            enthalpy = entries['enthalpy'].get().strip()

            # Validation
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

            # Explode formula
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

        confirm_btn = ttk.Button(popup, text="Confirm", style="Rounded.TButton",
                                 command=on_confirm)
        confirm_btn.pack(pady=20)

    def show_fuel_weight_popup(self, fuels):
        """Show popup for entering weight percentages for multiple fuels"""
        popup = tk.Toplevel(self.root)
        popup.title("Enter Fuel Weight Percentages")
        popup.geometry("500x400")
        popup.configure(bg=self.bg_medium)
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text="Enter weight percentage for each fuel:", 
                 font=('Arial', 12, 'bold'), bg=self.bg_medium, 
                 fg=self.text_color).pack(pady=20)

        entries = {}
        for fuel in fuels:
            row = tk.Frame(popup, bg=self.bg_medium)
            row.pack(fill=tk.X, padx=40, pady=5)

            tk.Label(row, text=f"{fuel}:", font=('Arial', 11),
                     bg=self.bg_medium, fg=self.text_color, width=20, anchor='w').pack(side=tk.LEFT)
            entry = tk.Entry(row, font=('Arial', 11), width=15)
            entry.pack(side=tk.LEFT, padx=10)
            tk.Label(row, text="%", font=('Arial', 11),
                     bg=self.bg_medium, fg=self.text_color).pack(side=tk.LEFT)
            entries[fuel] = entry

        error_label = tk.Label(popup, text="", font=('Arial', 10),
                               bg=self.bg_medium, fg='red')
        error_label.pack(pady=10)

        def on_confirm():
            weights = {}
            total = 0
            
            for fuel, entry in entries.items():
                value = entry.get().strip()
                if not value:
                    error_label.config(text=f"Please enter weight for {fuel}")
                    return
                try:
                    weight = float(value)
                    if weight <= 0:
                        error_label.config(text=f"Weight for {fuel} must be > 0")
                        return
                    weights[fuel] = weight
                    total += weight
                except ValueError:
                    error_label.config(text=f"Invalid weight for {fuel}")
                    return

            # Check if total equals 100
            if abs(total - 100) > 0.01:
                messagebox.showwarning("Invalid Total", 
                                       f"Total weight percentage must equal 100%\nCurrent total: {total:.2f}%\n\nPlease adjust the values.")
                return

            # Store the weights and update display
            self.fuel_weight_entries = weights
            self.update_fuel_display()
            popup.destroy()

        confirm_btn = ttk.Button(popup, text="Confirm", style="Rounded.TButton",
                                 command=on_confirm)
        confirm_btn.pack(pady=20)

    def close_dropdown_on_click(self, event):
        if hasattr(self, 'dropdown_frame') and self.dropdown_frame:
            if event.widget != self.dropdown_frame and event.widget.master != self.dropdown_frame:
                self.toggle_menu()

    def create_header(self):
        header = tk.Frame(self.root, bg=self.bg_dark, height=60)
        header.pack(side=tk.TOP, fill=tk.X)

        title = tk.Label(header, text="HYBRID MODEL", font=('Arial', 24, 'bold'),
                         bg=self.bg_dark, fg=self.text_color)
        title.pack(side=tk.LEFT, padx=20)

    def create_sidebar(self):
        sidebar = tk.Frame(self.root, bg=self.bg_medium, width=150)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        self.menu_button = ttk.Button(sidebar, text="Menu", style="Rounded.TButton",
                                      command=self.toggle_menu)
        self.menu_button.pack(fill=tk.X, padx=10, pady=10)

        self.page_buttons = {}
        pages = ['configuration', 'optimization', 'mission', 'output']

        for page in pages:
            btn = ttk.Button(sidebar, text=page.capitalize(),
                             style="Rounded.TButton",
                             command=lambda p=page: self.change_page(p))
            btn.pack(fill=tk.X, padx=10, pady=5)
            self.page_buttons[page] = btn

    def toggle_menu(self):
        if hasattr(self, 'dropdown_frame') and self.dropdown_frame:
            self.dropdown_frame.destroy()
            self.dropdown_frame = None
        else:
            # Get button position
            x = self.menu_button.winfo_rootx()
            y = self.menu_button.winfo_rooty() + self.menu_button.winfo_height()
            button_width = self.menu_button.winfo_width()
            
            # Create dropdown frame
            self.dropdown_frame = tk.Toplevel(self.root)
            self.dropdown_frame.overrideredirect(True)
            self.dropdown_frame.configure(bg=self.bg_active)
            
            # Create buttons
            save_btn = tk.Button(self.dropdown_frame, text="Save", font=('Arial', 10),
                      bg=self.bg_light, command=self.save_config,
                      relief=tk.FLAT, anchor='w', highlightthickness=0, bd=0)
            save_btn.pack(fill=tk.X, pady=2, padx=2)
            
            save_as_btn = tk.Button(self.dropdown_frame, text="Save As", font=('Arial', 10),
                      bg=self.bg_light, command=self.save_config_as,
                      relief=tk.FLAT, anchor='w', highlightthickness=0, bd=0)
            save_as_btn.pack(fill=tk.X, pady=2, padx=2)
            
            open_btn = tk.Button(self.dropdown_frame, text="Open", font=('Arial', 10),
                      bg=self.bg_light, command=self.open_config,
                      relief=tk.FLAT, anchor='w', highlightthickness=0, bd=0)
            open_btn.pack(fill=tk.X, pady=2, padx=2)
            
            # Update to get actual size
            self.dropdown_frame.update_idletasks()
            
            # Center horizontally relative to button
            frame_width = self.dropdown_frame.winfo_width()
            centered_x = x + (button_width - frame_width) // 2
            
            # Position dropdown
            self.dropdown_frame.geometry(f"+{centered_x}+{y}")

            self.dropdown_frame.bind("<FocusOut>", lambda e: self.toggle_menu())
            self.root.bind("<Button-1>", self.close_dropdown_on_click)

    def change_page(self, page):
        for p, btn in self.page_buttons.items():
            if p == page:
                self.style.configure("Rounded.TButton", background=self.button_active)
            else:
                self.style.configure("Rounded.TButton", background=self.button_inactive)

        self.current_page = page

        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if page == 'configuration':
            self.show_configuration_page()
        elif page == 'optimization':
            self.show_optimization_page()
        else:
            label = tk.Label(self.content_frame, text=f"{page.upper()} - Coming soon",
                             font=('Arial', 20), bg=self.bg_dark, fg=self.text_color)
            label.pack(expand=True)

    def show_configuration_page(self):
        canvas = tk.Canvas(self.content_frame, bg=self.bg_dark, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_dark)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        title = tk.Label(scrollable_frame, text="configuration",
                         font=('Arial', 28, 'bold'), bg=self.bg_dark, fg=self.text_color)
        title.pack(pady=(0, 20))

        self.create_line_section(scrollable_frame)
        self.create_fuel_oxidiser_section(scrollable_frame)
        self.create_injector_section(scrollable_frame)
        self.create_nozzle_section(scrollable_frame)

        save_button_frame = tk.Frame(scrollable_frame, bg=self.bg_dark)
        save_button_frame.pack(fill=tk.X, pady=(20, 0))

        save_btn = ttk.Button(save_button_frame, text="Save Configuration",
                              style="Rounded.TButton",
                              command=self.validate_and_save)
        save_btn.pack(pady=10)

        self.validate_inputs()

        def _on_mousewheel(event):
            # Check if a combobox dropdown or search popup is active
            if hasattr(self, 'search_popup_active') and self.search_popup_active:
                # Don't scroll the main canvas when search popup is open
                return

            # Get the widget that triggered the event
            widget = event.widget
            while widget is not None:
                # Check if we're in a Combobox dropdown
                if isinstance(widget, tk.Listbox):
                    parent = widget.master
                    if parent and parent.master and parent.master.winfo_class() == 'TCombobox':
                        # We're in a Combobox listbox, let it handle its own scrolling
                        return
                # Move up the widget hierarchy
                widget = widget.master

            # If we're not in a Combobox dropdown or search popup, scroll the main canvas
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def show_optimization_page(self):
        """Display the Optimization page with the same style as Configuration"""
        canvas = tk.Canvas(self.content_frame, bg=self.bg_dark, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_dark)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        title = tk.Label(scrollable_frame, text="optimization",
                         font=('Arial', 28, 'bold'), bg=self.bg_dark, fg=self.text_color)
        title.pack(pady=(0, 20))

        # Create optimization section
        self.create_optimization_section(scrollable_frame)

        save_button_frame = tk.Frame(scrollable_frame, bg=self.bg_dark)
        save_button_frame.pack(fill=tk.X, pady=(20, 0))

        save_btn = ttk.Button(save_button_frame, text="Save Optimization",
                              style="Rounded.TButton",
                              command=self.validate_and_save_optimization)
        save_btn.pack(pady=10)

        self.validate_inputs()

        def _on_mousewheel(event):
            if hasattr(self, 'search_popup_active') and self.search_popup_active:
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

    def create_optimization_section(self, parent):
        """Create the Optimization section with all required fields"""
        section = tk.Frame(parent, bg=self.bg_light, relief=tk.RIDGE, bd=2)
        section.pack(fill=tk.X, pady=10, ipady=15)

        header_frame = tk.Frame(section, bg=self.bg_light)
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        section_title = tk.Label(header_frame, text="Optimization", font=('Arial', 16),
                                 bg=self.bg_light, fg='black')
        section_title.pack(side=tk.LEFT)

        fields_frame = tk.Frame(section, bg=self.bg_light)
        fields_frame.pack(fill=tk.X, padx=40, pady=10)

        # parameter_points (integer > 0)
        self.create_int_field(fields_frame, "Optimization", "parameter_points", 
                             "parameter_points", min_value=0, exclusive=True)

        # Dport-Dt.min (float > 0)
        self.create_float_field(fields_frame, "Optimization", "Dport-Dt.min", 
                               "Dport-Dt.min", min_value=0, exclusive=True)

        # Dport-Dt.max (float > 0)
        self.create_float_field(fields_frame, "Optimization", "Dport-Dt.max", 
                               "Dport-Dt.max", min_value=0, exclusive=True)

        # Dinj-Dt.min (float > 0)
        self.create_float_field(fields_frame, "Optimization", "Dinj-Dt.min", 
                               "Dinj-Dt.min", min_value=0, exclusive=True)

        # Dinj-Dt.max (float > 0)
        self.create_float_field(fields_frame, "Optimization", "Dinj-Dt.max", 
                               "Dinj-Dt.max", min_value=0, exclusive=True)

        # Lc-Dt.min (float > 0)
        self.create_float_field(fields_frame, "Optimization", "Lc-Dt.min", 
                               "Lc-Dt.min", min_value=0, exclusive=True)

        # Lc-Dt.max (float > 0)
        self.create_float_field(fields_frame, "Optimization", "Lc-Dt.max", 
                               "Lc-Dt.max", min_value=0, exclusive=True)

        # ptank (float > 0) [Pa]
        self.create_float_field(fields_frame, "Optimization", "ptank", 
                               "(Ptank) ptank [Pa]", min_value=0, exclusive=True)

        # Ttank (float > 0) [K]
        self.create_float_field(fields_frame, "Optimization", "Ttank", 
                               "(Ttank) Ttank [K]", min_value=0, exclusive=True)

        # pamb (float > 0) [Pa]
        self.create_float_field(fields_frame, "Optimization", "pamb", 
                               "(Pamb) pamb [Pa]", min_value=0, exclusive=True)

    def create_int_field(self, parent, section, var_name, display_name, min_value=None,
                        max_value=None, exclusive=False):
        """Create an integer input field with validation"""
        row = tk.Frame(parent, bg=self.bg_light)
        row.pack(fill=tk.X, pady=5)

        label = tk.Label(row, text=display_name + ":", font=('Arial', 11),
                         bg=self.bg_light, fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))

        entry = tk.Entry(row, font=('Arial', 11), width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.bg_light,
                         highlightcolor=self.bg_light)
        entry.pack(side=tk.LEFT)

        entry.validation_params = {
            'min_value': min_value,
            'max_value': max_value,
            'exclusive': exclusive,
            'is_int': True
        }

        entry.bind('<KeyRelease>', lambda e: self.validate_single_input(entry))

        self.inputs[f"{section}_{var_name}"] = entry

    def validate_and_save_optimization(self):
        """Validate and save optimization configuration"""
        config = {}
        all_valid = True

        # Validate optimization inputs
        for key, entry in self.inputs.items():
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

if __name__ == "__main__":
    root = tk.Tk()
    app = HybridRocketGUI(root)
    root.mainloop()