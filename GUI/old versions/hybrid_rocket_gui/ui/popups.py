
# ui/popups.py

import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from utils.chemistry import explode_formula


class PopupManager:
    def __init__(self, root, style_manager):
        self.root = root
        self.style_manager = style_manager
        self.colors = COLORS
        self.fonts = FONTS
        self.search_popup_active = False
    
    def show_search_popup(self, title, reactant_list, callback, multi_select=False):
        '''Show popup window with search functionality'''
        self.search_popup_active = True
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("500x600")
        popup.configure(bg=self.colors['bg_medium'])
        popup.transient(self.root)
        popup.grab_set()

        def on_popup_close():
            self.search_popup_active = False
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", on_popup_close)

        # Search frame
        search_frame = tk.Frame(popup, bg=self.colors['bg_medium'])
        search_frame.pack(fill=tk.X, padx=20, pady=20)

        tk.Label(search_frame, text="Search:", font=self.fonts['normal'],
                 bg=self.colors['bg_medium'], fg=self.colors['text_color']).pack(side=tk.LEFT, padx=(0, 10))

        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var,
                                font=self.fonts['normal'], width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # List frame
        list_frame = tk.Frame(popup, bg=self.colors['bg_medium'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        selectmode = tk.MULTIPLE if multi_select else tk.SINGLE
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                             font=self.fonts['small'], height=20, selectmode=selectmode)
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

        if not multi_select:
            listbox.bind('<Double-Button-1>', lambda e: on_select())
    
    def show_custom_formula_popup(self, callback):
        '''Show popup for custom chemical formula input'''
        popup = tk.Toplevel(self.root)
        popup.title("Custom Chemical Formula")
        popup.geometry("500x400")
        popup.configure(bg=self.colors['bg_medium'])
        popup.transient(self.root)
        popup.grab_set()

        entries = {}

        # Chemical Name
        row = tk.Frame(popup, bg=self.colors['bg_medium'])
        row.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(row, text="Chemical Name:", font=self.fonts['normal'],
                 bg=self.colors['bg_medium'], fg=self.colors['text_color'], width=20, anchor='w').pack(side=tk.LEFT)
        entries['name'] = tk.Entry(row, font=self.fonts['normal'], width=25)
        entries['name'].pack(side=tk.LEFT, padx=10)

        # Formula
        row = tk.Frame(popup, bg=self.colors['bg_medium'])
        row.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(row, text="Formula (e.g., H2O2):", font=self.fonts['normal'],
                 bg=self.colors['bg_medium'], fg=self.colors['text_color'], width=20, anchor='w').pack(side=tk.LEFT)
        entries['formula'] = tk.Entry(row, font=self.fonts['normal'], width=25)
        entries['formula'].pack(side=tk.LEFT, padx=10)

        # Temperature
        row = tk.Frame(popup, bg=self.colors['bg_medium'])
        row.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(row, text="Temperature [K]:", font=self.fonts['normal'],
                 bg=self.colors['bg_medium'], fg=self.colors['text_color'], width=20, anchor='w').pack(side=tk.LEFT)
        entries['temp'] = tk.Entry(row, font=self.fonts['normal'], width=25)
        entries['temp'].pack(side=tk.LEFT, padx=10)

        # Enthalpy
        row = tk.Frame(popup, bg=self.colors['bg_medium'])
        row.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(row, text="Specific Enthalpy [kJ/mol]:", font=self.fonts['normal'],
                 bg=self.colors['bg_medium'], fg=self.colors['text_color'], width=20, anchor='w').pack(side=tk.LEFT)
        entries['enthalpy'] = tk.Entry(row, font=self.fonts['normal'], width=25)
        entries['enthalpy'].pack(side=tk.LEFT, padx=10)

        error_label = tk.Label(popup, text="", font=self.fonts['small'],
                               bg=self.colors['bg_medium'], fg='red')
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
                exploded = explode_formula(formula)
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
    
    def show_fuel_weight_popup(self, fuels, callback):
        '''Show popup for entering weight percentages'''
        popup = tk.Toplevel(self.root)
        popup.title("Enter Fuel Weight Percentages")
        popup.geometry("500x400")
        popup.configure(bg=self.colors['bg_medium'])
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text="Enter weight percentage for each fuel:",
                 font=self.fonts['subtitle'], bg=self.colors['bg_medium'],
                 fg=self.colors['text_color']).pack(pady=20)

        entries = {}
        for fuel in fuels:
            row = tk.Frame(popup, bg=self.colors['bg_medium'])
            row.pack(fill=tk.X, padx=40, pady=5)

            tk.Label(row, text=f"{fuel}:", font=self.fonts['normal'],
                     bg=self.colors['bg_medium'], fg=self.colors['text_color'], width=20, anchor='w').pack(side=tk.LEFT)
            entry = tk.Entry(row, font=self.fonts['normal'], width=15)
            entry.pack(side=tk.LEFT, padx=10)
            tk.Label(row, text="%", font=self.fonts['normal'],
                     bg=self.colors['bg_medium'], fg=self.colors['text_color']).pack(side=tk.LEFT)
            entries[fuel] = entry

        error_label = tk.Label(popup, text="", font=self.fonts['small'],
                               bg=self.colors['bg_medium'], fg='red')
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

            if abs(total - 100) > 0.01:
                messagebox.showwarning("Invalid Total",
                                       f"Total weight percentage must equal 100%\nCurrent total: {total:.2f}%\n\nPlease adjust the values.")
                return

            callback(weights)
            popup.destroy()

        confirm_btn = ttk.Button(popup, text="Confirm", style="Rounded.TButton",
                                 command=on_confirm)
        confirm_btn.pack(pady=20)