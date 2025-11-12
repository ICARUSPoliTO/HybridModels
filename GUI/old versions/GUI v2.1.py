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

    def show_search_popup(self, title, reactant_list, callback):
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

        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                             font=('Arial', 10), height=20)
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
                selected_item = listbox.get(selection[0])
                self.search_popup_active = False
                callback(selected_item)
                popup.destroy()
            else:
                messagebox.showwarning("No Selection", "Please select an item.")        
        select_btn = ttk.Button(popup, text="Select", style="Rounded.TButton", command=on_select)
        select_btn.pack(pady=(0, 20))

        # Allow double-click to select
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
            x = self.menu_button.winfo_rootx() + self.menu_button.winfo_width()
            y = self.menu_button.winfo_rooty() + self.menu_button.winfo_height()  # Position below the button
            
            # Create dropdown frame
            self.dropdown_frame = tk.Toplevel(self.root)
            self.dropdown_frame.overrideredirect(True)
            
            # Configure the frame first
            self.dropdown_frame.configure(bg=self.bg_active)
            
            # Create and pack the buttons to get their required height
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
            
            # Update idletasks to make sure the frame has its true size
            self.dropdown_frame.update_idletasks()
            
            # Now position the frame above the button
            frame_height = self.dropdown_frame.winfo_height()
            frame_y = y - frame_height - self.menu_button.winfo_height()  # Position above the button
            
            self.dropdown_frame.geometry(f"150x{frame_height}+{x}+{frame_y}")

            tk.Button(self.dropdown_frame, text="Save", font=('Arial', 10),
                      bg=self.bg_light, command=self.save_config,
                      relief=tk.FLAT, anchor='w', highlightthickness=0, bd=0).pack(fill=tk.X, pady=2, padx=2)
            tk.Button(self.dropdown_frame, text="Save As", font=('Arial', 10),
                      bg=self.bg_light, command=self.save_config_as,
                      relief=tk.FLAT, anchor='w', highlightthickness=0, bd=0).pack(fill=tk.X, pady=2, padx=2)
            tk.Button(self.dropdown_frame, text="Open", font=('Arial', 10),
                      bg=self.bg_light, command=self.open_config,
                      relief=tk.FLAT, anchor='w', highlightthickness=0, bd=0).pack(fill=tk.X, pady=2, padx=2)

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

    def create_line_section(self, parent):
        section = tk.Frame(parent, bg=self.bg_light, relief=tk.RIDGE, bd=2)
        section.pack(fill=tk.X, pady=10, ipady=15)

        header_frame = tk.Frame(section, bg=self.bg_light)
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        section_title = tk.Label(header_frame, text="Line", font=('Arial', 16),
                                 bg=self.bg_light, fg='black')
        section_title.pack(side=tk.LEFT)

        import_btn = ttk.Button(header_frame, text="Import Line",
                                style="Rounded.TButton",
                                command=self.import_line_placeholder)
        import_btn.pack(side=tk.LEFT, padx=(20, 0))

    def create_fuel_oxidiser_section(self, parent):
        section = tk.Frame(parent, bg=self.bg_light, relief=tk.RIDGE, bd=2)
        section.pack(fill=tk.X, pady=10, ipady=15)

        header_frame = tk.Frame(section, bg=self.bg_light)
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        section_title = tk.Label(header_frame, text="Fuel & Oxidiser", font=('Arial', 16),
                                 bg=self.bg_light, fg='black')
        section_title.pack(side=tk.LEFT)

        fields_frame = tk.Frame(section, bg=self.bg_light)
        fields_frame.pack(fill=tk.X, padx=40, pady=10)

        # Oxidizer fields
        self.create_oxidizer_fields(fields_frame)

        # Fuel fields
        self.create_fuel_fields(fields_frame)

        # Regression rate parameters
        self.create_float_field(fields_frame, "Fuel & Oxidiser", "a", "a", min_value=0, exclusive=True)
        self.create_float_field(fields_frame, "Fuel & Oxidiser", "n", "n")
        self.create_float_field(fields_frame, "Fuel & Oxidiser", "rho.fuel", "ρF (kg/m³)",
                                min_value=0, exclusive=True)

    def create_oxidizer_fields(self, parent):
        # Main oxidizer dropdown
        row = tk.Frame(parent, bg=self.bg_light)
        row.pack(fill=tk.X, pady=5)

        label = tk.Label(row, text="(Ox) Oxidizer:", font=('Arial', 11),
                         bg=self.bg_light, fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))

        combo = ttk.Combobox(row, font=('Arial', 11), width=28,
                             values=self.easy_cea_ox_list, state='readonly')
        combo.pack(side=tk.LEFT)
        combo.bind('<<ComboboxSelected>>', lambda e: self.on_oxidizer_change())

        self.dropdowns["Fuel & Oxidiser_Oxidizer"] = combo

        # Weight fraction (unchangeable for single-fluid)
        row = tk.Frame(parent, bg=self.bg_light)
        row.pack(fill=tk.X, pady=5)

        label = tk.Label(row, text="Weight fraction:", font=('Arial', 11),
                         bg=self.bg_light, fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))

        entry = tk.Entry(row, font=('Arial', 11), width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.bg_light,
                         highlightcolor=self.bg_light, state='readonly')
        entry.insert(0, "100")
        entry.pack(side=tk.LEFT)

        self.inputs["Fuel & Oxidiser_Oxidizer_WeightFraction"] = entry

        # Container for dynamic fields
        self.oxidizer_dynamic_frame = tk.Frame(parent, bg=self.bg_light)
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
                # Store custom oxidizer data
                self.inputs["Fuel & Oxidiser_Oxidizer_CustomName"] = result['name']
                self.inputs["Fuel & Oxidiser_Oxidizer_ExpandedFormula"] = result['exploded_formula']

                # Update display
                self.dropdowns["Fuel & Oxidiser_Oxidizer"].set(f"Custom: {result['name']}")

                # Create dynamic fields with pre-filled values
                self.create_oxidizer_dynamic_fields(result['temperature'], result['enthalpy'])

            self.show_custom_formula_popup(callback)
            return

        # Standard selection - create dynamic fields
        self.create_oxidizer_dynamic_fields()

    def create_oxidizer_dynamic_fields(self, temp_default=None, enthalpy_default=None):
        """Create temperature and enthalpy fields for oxidizer"""
        # Temperature field
        row = tk.Frame(self.oxidizer_dynamic_frame, bg=self.bg_light)
        row.pack(fill=tk.X, pady=5)

        label = tk.Label(row, text="Temperature [K]:", font=('Arial', 11),
                         bg=self.bg_light, fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))

        entry = tk.Entry(row, font=('Arial', 11), width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.bg_light,
                         highlightcolor=self.bg_light)
        entry.pack(side=tk.LEFT)
        if temp_default:
            entry.insert(0, str(temp_default))
        entry.bind('<KeyRelease>', lambda e: self.validate_single_input(entry))

        self.inputs["Fuel & Oxidiser_Oxidizer_Temperature"] = entry

        # Specific Enthalpy field
        row = tk.Frame(self.oxidizer_dynamic_frame, bg=self.bg_light)
        row.pack(fill=tk.X, pady=5)

        label = tk.Label(row, text="Specific Enthalpy [kJ/mol]:", font=('Arial', 11),
                         bg=self.bg_light, fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))

        entry = tk.Entry(row, font=('Arial', 11), width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.bg_light,
                         highlightcolor=self.bg_light)
        entry.pack(side=tk.LEFT)
        if enthalpy_default:
            entry.insert(0, str(enthalpy_default))
        entry.bind('<KeyRelease>', lambda e: self.validate_single_input(entry))

        self.inputs["Fuel & Oxidiser_Oxidizer_SpecificEnthalpy"] = entry

        self.validate_inputs()

    def create_fuel_fields(self, parent):
        # Main fuel dropdown
        row = tk.Frame(parent, bg=self.bg_light)
        row.pack(fill=tk.X, pady=5)

        label = tk.Label(row, text="(F) Fuel:", font=('Arial', 11),
                         bg=self.bg_light, fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))

        combo = ttk.Combobox(row, font=('Arial', 11), width=28,
                             values=self.easy_cea_fuel_list, state='readonly')
        combo.pack(side=tk.LEFT)
        combo.bind('<<ComboboxSelected>>', lambda e: self.on_fuel_change())

        self.dropdowns["Fuel & Oxidiser_Fuel"] = combo

        # Weight fraction
        row = tk.Frame(parent, bg=self.bg_light)
        row.pack(fill=tk.X, pady=5)

        label = tk.Label(row, text="Fuel Weight fraction:", font=('Arial', 11),
                         bg=self.bg_light, fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))

        entry = tk.Entry(row, font=('Arial', 11), width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.bg_light,
                         highlightcolor=self.bg_light)
        entry.pack(side=tk.LEFT)
        entry.bind('<KeyRelease>', lambda e: self.validate_fuel_weight_fraction())

        self.inputs["Fuel & Oxidiser_Fuel_WeightFraction"] = entry

        # Container for dynamic fuel fields
        self.fuel_dynamic_frame = tk.Frame(parent, bg=self.bg_light)
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

        # Handle special case for paraffin
        if fuel == "paraffin":
            self.create_fuel_dynamic_fields(533.0, -1860.6)
        else:
            self.create_fuel_dynamic_fields()

    def create_fuel_dynamic_fields(self, temp_default=None, enthalpy_default=None):
        """Create temperature and enthalpy fields for fuel"""
        # Temperature field
        row = tk.Frame(self.fuel_dynamic_frame, bg=self.bg_light)
        row.pack(fill=tk.X, pady=5)

        label = tk.Label(row, text="Fuel Temperature [K]:", font=('Arial', 11),
                         bg=self.bg_light, fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))

        entry = tk.Entry(row, font=('Arial', 11), width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.bg_light,
                         highlightcolor=self.bg_light)
        entry.pack(side=tk.LEFT)
        if temp_default:
            entry.insert(0, str(temp_default))
        entry.bind('<KeyRelease>', lambda e: self.validate_single_input(entry))

        self.inputs["Fuel & Oxidiser_Fuel_Temperature"] = entry

        # Specific Enthalpy field
        row = tk.Frame(self.fuel_dynamic_frame, bg=self.bg_light)
        row.pack(fill=tk.X, pady=5)

        label = tk.Label(row, text="Fuel Specific Enthalpy [kJ/mol]:", font=('Arial', 11),
                         bg=self.bg_light, fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))

        entry = tk.Entry(row, font=('Arial', 11), width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.bg_light,
                         highlightcolor=self.bg_light)
        entry.pack(side=tk.LEFT)
        if enthalpy_default:
            entry.insert(0, str(enthalpy_default))
        entry.bind('<KeyRelease>', lambda e: self.validate_single_input(entry))

        self.inputs["Fuel & Oxidiser_Fuel_SpecificEnthalpy"] = entry

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
            entry.configure(highlightbackground='#00aa00', highlightcolor='#00aa00')
        else:
            entry.configure(highlightbackground='red', highlightcolor='red')

        self.validate_inputs()

    def create_injector_section(self, parent):
        section = tk.Frame(parent, bg=self.bg_light, relief=tk.RIDGE, bd=2)
        section.pack(fill=tk.X, pady=10, ipady=15)

        header_frame = tk.Frame(section, bg=self.bg_light)
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        section_title = tk.Label(header_frame, text="Injector", font=('Arial', 16),
                                 bg=self.bg_light, fg='black')
        section_title.pack(side=tk.LEFT)

        fields_frame = tk.Frame(section, bg=self.bg_light)
        fields_frame.pack(fill=tk.X, padx=40, pady=10)

        self.create_float_field(fields_frame, "Injector", "CD", "(CD) CD", min_value=0, exclusive=True)
        self.create_float_field(fields_frame, "Injector", "Gox.min", "(Gox_min) Gox.min [kg/s/m²]",
                                min_value=0, exclusive=True)
        self.create_float_field(fields_frame, "Injector", "Gox.max", "(Gox_max) Gox.max [kg/s/m²]",
                                min_value=0, exclusive=True)

    def create_nozzle_section(self, parent):
        section = tk.Frame(parent, bg=self.bg_light, relief=tk.RIDGE, bd=2)
        section.pack(fill=tk.X, pady=10, ipady=15)

        header_frame = tk.Frame(section, bg=self.bg_light)
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        section_title = tk.Label(header_frame, text="Nozzle", font=('Arial', 16),
                                 bg=self.bg_light, fg='black')
        section_title.pack(side=tk.LEFT)

        fields_frame = tk.Frame(section, bg=self.bg_light)
        fields_frame.pack(fill=tk.X, padx=40, pady=10)

        self.create_epsilon_field(fields_frame)

    def create_epsilon_field(self, parent):
        row = tk.Frame(parent, bg=self.bg_light)
        row.pack(fill=tk.X, pady=5)

        label = tk.Label(row, text="(ε) eps:", font=('Arial', 11),
                         bg=self.bg_light, fg='black', width=25, anchor='w')
        label.pack(side=tk.LEFT, padx=(0, 10))

        entry = tk.Entry(row, font=('Arial', 11), width=30, relief=tk.SUNKEN, bd=2,
                         highlightthickness=2, highlightbackground=self.bg_light,
                         highlightcolor=self.bg_light)
        entry.pack(side=tk.LEFT)
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
                    float_val = float(value)
                    if float_val > 1:
                        is_valid = True
                except ValueError:
                    pass

        if is_valid:
            entry.configure(highlightbackground='#00aa00', highlightcolor='#00aa00')
        else:
            entry.configure(highlightbackground='red', highlightcolor='red')

        self.validate_inputs()

    def create_float_field(self, parent, section, var_name, display_name, min_value=None,
                           max_value=None, exclusive=False):
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
            'exclusive': exclusive
        }

        entry.bind('<KeyRelease>', lambda e: self.validate_single_input(entry))

        self.inputs[f"{section}_{var_name}"] = entry

    def validate_single_input(self, entry):
        """Validate a single input field and change border color"""
        value = entry.get().strip()
        is_valid = False

        if value:
            # Check if it's a string field
            field_key = None
            for key, val in self.inputs.items():
                if val == entry:
                    field_key = key
                    break

            if field_key and ("CustomName" in field_key or "ExpandedFormula" in field_key):
                is_valid = len(value) > 0
            else:
                # Numeric validation
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
            entry.configure(highlightbackground='#00aa00', highlightcolor='#00aa00')
        elif value:
            entry.configure(highlightbackground='red', highlightcolor='red')
        else:
            entry.configure(highlightbackground=self.bg_light, highlightcolor=self.bg_light)

        self.validate_inputs()

    def validate_inputs(self):
        all_valid = True

        # Check all text entries
        for key, entry in self.inputs.items():
            if isinstance(entry, str):  # Skip string stored values like CustomName
                continue

            value = entry.get().strip()
            if not value:
                all_valid = False
                continue

            # String field validation
            if "CustomName" in key or "ExpandedFormula" in key:
                if not value:
                    all_valid = False
            # Numeric field validation
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

        # Check epsilon special case
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

        # Check fuel weight fraction
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

        # Check dropdowns
        for key, combo in self.dropdowns.items():
            if not combo.get():
                all_valid = False

        # Change button color
        if all_valid:
            self.style.configure("Rounded.TButton", background='#006400')
        else:
            self.style.configure("Rounded.TButton", background='#8b0000')

    def import_line_placeholder(self):
        messagebox.showinfo("Info", "Import line function in development")

    def validate_and_save(self):
        config = {}
        all_valid = True

        # Validate text entries
        for key, entry in self.inputs.items():
            if isinstance(entry, str):  # Handle stored string values
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

        # Validate dropdowns
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

        # Save text entries
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

        # Save dropdowns
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

                # Load text entries
                for key, value in config.items():
                    if key in self.inputs:
                        if isinstance(self.inputs[key], str):
                            self.inputs[key] = value
                        else:
                            self.inputs[key].delete(0, tk.END)
                            self.inputs[key].insert(0, str(value))
                    elif key in self.dropdowns:
                        self.dropdowns[key].set(value)

                # Trigger changes
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
    root = tk.Tk()
    app = HybridRocketGUI(root)
    root.mainloop()