"""
Popup Manager

Handles popup dialogs for searching reactants, entering custom formulas,
and managing fuel weight percentages.
"""

import tkinter as tk
from tkinter import messagebox
from config.constants import COLORS, FONTS
from utils.chemistry import explode_formula


class PopupManager:
    """Manages popup dialogs for user interactions"""
    
    def __init__(self, root):
        self.root = root
        self.colors = COLORS
        self.fonts = FONTS
        self.popup_active = False
    
    def show_search_popup(self, title: str, items: list, callback, multi_select: bool = False):
        """
        Show searchable list popup
        
        Args:
            title: Popup title
            items: List of items to display
            callback: Function to call with selected item(s)
            multi_select: Allow multiple selection
        """
        if self.popup_active:
            return
        
        self.popup_active = True
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("500x600")
        popup.configure(bg=self.colors['bg_medium'])
        popup.transient(self.root)
        popup.grab_set()
        
        def on_close():
            self.popup_active = False
            popup.destroy()
        
        popup.protocol("WM_DELETE_WINDOW", on_close)
        
        # Search frame
        search_frame = tk.Frame(popup, bg=self.colors['bg_medium'])
        search_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(
            search_frame, 
            text="Search:", 
            font=self.fonts['label'],
            bg=self.colors['bg_medium'], 
            fg=self.colors['text_color']
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame, 
            textvariable=search_var,
            font=self.fonts['label'], 
            width=30
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # List frame
        list_frame = tk.Frame(popup, bg=self.colors['bg_medium'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        selectmode = tk.MULTIPLE if multi_select else tk.SINGLE
        listbox = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set,
            font=self.fonts['small'], 
            height=20, 
            selectmode=selectmode
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Update listbox on search
        def update_listbox(*args):
            search_term = search_var.get().lower()
            listbox.delete(0, tk.END)
            filtered = [item for item in items if search_term in item.lower()]
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
                    self.popup_active = False
                    callback(selected_items)
                    popup.destroy()
                else:
                    selected_item = listbox.get(selection[0])
                    self.popup_active = False
                    callback(selected_item)
                    popup.destroy()
            else:
                messagebox.showwarning("No Selection", "Please select an item.")
        
        select_btn = tk.Button(
            popup, 
            text="Select",
            font=self.fonts['button'],
            bg=self.colors['button_inactive'],
            fg='black',
            command=on_select,
            cursor='hand2',
            padx=15,
            pady=8
        )
        select_btn.pack(pady=(0, 20))
        
        # Double-click to select (single select only)
        if not multi_select:
            listbox.bind('<Double-Button-1>', lambda e: on_select())
    
    def show_custom_formula_popup(self, callback):
        """
        Show custom chemical formula input popup
        
        Args:
            callback: Function to call with formula data dict
        """
        if self.popup_active:
            return
        
        self.popup_active = True
        popup = tk.Toplevel(self.root)
        popup.title("Custom Chemical Formula")
        popup.geometry("500x400")
        popup.configure(bg=self.colors['bg_medium'])
        popup.transient(self.root)
        popup.grab_set()
        
        def on_close():
            self.popup_active = False
            popup.destroy()
        
        popup.protocol("WM_DELETE_WINDOW", on_close)
        
        entries = {}
        
        # Chemical Name
        row = tk.Frame(popup, bg=self.colors['bg_medium'])
        row.pack(fill=tk.X, padx=40, pady=15)
        
        tk.Label(
            row, 
            text="Chemical Name:", 
            font=self.fonts['label'],
            bg=self.colors['bg_medium'], 
            fg=self.colors['text_color'],
            width=20,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        entries['name'] = tk.Entry(row, font=self.fonts['label'], width=30)
        entries['name'].pack(side=tk.LEFT)
        
        # Formula
        row = tk.Frame(popup, bg=self.colors['bg_medium'])
        row.pack(fill=tk.X, padx=40, pady=15)
        
        tk.Label(
            row, 
            text="Formula (e.g., H2O2):", 
            font=self.fonts['label'],
            bg=self.colors['bg_medium'], 
            fg=self.colors['text_color'],
            width=20,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        entries['formula'] = tk.Entry(row, font=self.fonts['label'], width=30)
        entries['formula'].pack(side=tk.LEFT)
        
        # Temperature
        row = tk.Frame(popup, bg=self.colors['bg_medium'])
        row.pack(fill=tk.X, padx=40, pady=15)
        
        tk.Label(
            row, 
            text="Temperature [K]:", 
            font=self.fonts['label'],
            bg=self.colors['bg_medium'], 
            fg=self.colors['text_color'],
            width=20,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        entries['temperature'] = tk.Entry(row, font=self.fonts['label'], width=30)
        entries['temperature'].pack(side=tk.LEFT)
        
        # Enthalpy
        row = tk.Frame(popup, bg=self.colors['bg_medium'])
        row.pack(fill=tk.X, padx=40, pady=15)
        
        tk.Label(
            row, 
            text="Specific Enthalpy [kJ/mol]:", 
            font=self.fonts['label'],
            bg=self.colors['bg_medium'], 
            fg=self.colors['text_color'],
            width=20,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        entries['enthalpy'] = tk.Entry(row, font=self.fonts['label'], width=30)
        entries['enthalpy'].pack(side=tk.LEFT)
        
        # Confirm button
        def on_confirm():
            name = entries['name'].get().strip()
            formula = entries['formula'].get().strip()
            temp = entries['temperature'].get().strip()
            enthalpy = entries['enthalpy'].get().strip()
            
            if not name or not formula:
                messagebox.showerror("Error", "Please enter chemical name and formula")
                return
            
            try:
                temp_val = float(temp) if temp else None
                enthalpy_val = float(enthalpy) if enthalpy else None
            except ValueError:
                messagebox.showerror("Error", "Temperature and enthalpy must be numbers")
                return
            
            # Explode the formula
            try:
                exploded = explode_formula(formula)
            except Exception as e:
                messagebox.showerror("Error", f"Invalid formula: {str(e)}")
                return
            
            result = {
                'name': name,
                'formula': formula,
                'exploded_formula': exploded,
                'temperature': temp_val,
                'enthalpy': enthalpy_val
            }
            
            self.popup_active = False
            callback(result)
            popup.destroy()
        
        confirm_btn = tk.Button(
            popup, 
            text="Confirm",
            font=self.fonts['button'],
            bg=self.colors['button_inactive'],
            fg='black',
            command=on_confirm,
            cursor='hand2',
            padx=20,
            pady=10
        )
        confirm_btn.pack(pady=30)
    
    def show_fuel_weight_popup(self, fuels: list, callback):
        """
        Show fuel weight percentage input popup
        
        Args:
            fuels: List of fuel names
            callback: Function to call with weight dictionary
        """
        if self.popup_active:
            return
        
        self.popup_active = True
        popup = tk.Toplevel(self.root)
        popup.title("Fuel Weight Percentages")
        popup.geometry("450x400")
        popup.configure(bg=self.colors['bg_medium'])
        popup.transient(self.root)
        popup.grab_set()
        
        def on_close():
            self.popup_active = False
            popup.destroy()
        
        popup.protocol("WM_DELETE_WINDOW", on_close)
        
        # Instructions
        tk.Label(
            popup,
            text="Enter weight percentage for each fuel\n(Total must equal 100%)",
            font=self.fonts['label'],
            bg=self.colors['bg_medium'],
            fg=self.colors['text_color']
        ).pack(pady=20)
        
        # Create entries for each fuel
        entries = {}
        for fuel in fuels:
            row = tk.Frame(popup, bg=self.colors['bg_medium'])
            row.pack(fill=tk.X, padx=40, pady=10)
            
            tk.Label(
                row,
                text=f"{fuel}:",
                font=self.fonts['label'],
                bg=self.colors['bg_medium'],
                fg=self.colors['text_color'],
                width=20,
                anchor='w'
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            entry = tk.Entry(row, font=self.fonts['label'], width=15)
            entry.pack(side=tk.LEFT)
            entry.insert(0, "0")
            entries[fuel] = entry
        
        # Confirm button
        def on_confirm():
            weights = {}
            total = 0
            
            try:
                for fuel, entry in entries.items():
                    value = float(entry.get())
                    if value < 0 or value > 100:
                        messagebox.showerror("Error", "Percentages must be between 0 and 100")
                        return
                    weights[fuel] = value
                    total += value
                
                if abs(total - 100) > 0.01:
                    messagebox.showerror("Error", f"Total must equal 100% (currently {total}%)")
                    return
                
                self.popup_active = False
                callback(weights)
                popup.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers")
        
        confirm_btn = tk.Button(
            popup,
            text="Confirm",
            font=self.fonts['button'],
            bg=self.colors['button_inactive'],
            fg='black',
            command=on_confirm,
            cursor='hand2',
            padx=20,
            pady=10
        )
        confirm_btn.pack(pady=20)
