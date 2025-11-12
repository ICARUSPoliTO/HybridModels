import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json


class HybridRocketGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("hybrid model")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')

        # Colori
        self.bg_dark = '#2b2b2b'
        self.bg_medium = '#3c3c3c'
        self.bg_light = '#8c8c8c'
        self.bg_active = '#5c5c5c'
        self.text_color = 'white'
        self.button_inactive = '#a0a0a0'
        self.button_active = '#6c6c6c'

        # Variabili per gli input
        self.inputs = {}
        self.current_page = 'configuration'

        # Menu principale e navigazione
        self.create_header()
        self.create_sidebar()

        # Area contenuto
        self.content_frame = tk.Frame(self.root, bg=self.bg_dark)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Mostra la pagina di configurazione
        self.show_configuration_page()

    def create_header(self):
        header = tk.Frame(self.root, bg=self.bg_dark, height=60)
        header.pack(side=tk.TOP, fill=tk.X)

        title = tk.Label(header, text="hybrid model", font=('Arial', 24, 'bold'),
                         bg=self.bg_dark, fg=self.text_color)
        title.pack(side=tk.LEFT, padx=20, pady=10)

    def create_sidebar(self):
        sidebar = tk.Frame(self.root, bg=self.bg_medium, width=150)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Menu button con dropdown
        menu_frame = tk.Frame(sidebar, bg=self.bg_medium)
        menu_frame.pack(pady=10, padx=10, fill=tk.X)

        self.menu_button = tk.Button(menu_frame, text="Main Menu ☰",
                                     font=('Arial', 10), bg=self.bg_light, fg='black',
                                     relief=tk.RAISED, command=self.toggle_menu)
        self.menu_button.pack(fill=tk.X)

        # Dropdown menu (inizialmente nascosto)
        self.dropdown_frame = tk.Frame(sidebar, bg=self.bg_active)
        self.dropdown_visible = False

        tk.Button(self.dropdown_frame, text="Save", font=('Arial', 9),
                  bg=self.bg_light, command=self.save_config,
                  relief=tk.FLAT).pack(fill=tk.X, pady=2)
        tk.Button(self.dropdown_frame, text="Save as", font=('Arial', 9),
                  bg=self.bg_light, command=self.save_config_as,
                  relief=tk.FLAT).pack(fill=tk.X, pady=2)
        tk.Button(self.dropdown_frame, text="Open", font=('Arial', 9),
                  bg=self.bg_light, command=self.open_config,
                  relief=tk.FLAT).pack(fill=tk.X, pady=2)

        # Pulsanti pagine
        self.page_buttons = {}
        pages = ['configuration', 'optimization', 'mission', 'output']

        for page in pages:
            btn = tk.Button(sidebar, text=page, font=('Arial', 11),
                            bg=self.button_active if page == 'configuration' else self.button_inactive,
                            fg='black', relief=tk.FLAT, height=2,
                            command=lambda p=page: self.change_page(p))
            btn.pack(fill=tk.X, padx=10, pady=5)
            self.page_buttons[page] = btn

    def toggle_menu(self):
        if self.dropdown_visible:
            self.dropdown_frame.pack_forget()
            self.dropdown_visible = False
        else:
            self.dropdown_frame.pack(padx=10, pady=5, fill=tk.X)
            self.dropdown_visible = True

    def change_page(self, page):
        # Aggiorna colori pulsanti
        for p, btn in self.page_buttons.items():
            if p == page:
                btn.configure(bg=self.button_active)
            else:
                btn.configure(bg=self.button_inactive)

        self.current_page = page

        # Pulisci contenuto
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Mostra pagina appropriata
        if page == 'configuration':
            self.show_configuration_page()
        else:
            # Pagine vuote per ora
            label = tk.Label(self.content_frame, text=f"{page.upper()} - Coming soon",
                             font=('Arial', 20), bg=self.bg_dark, fg=self.text_color)
            label.pack(expand=True)

    def show_configuration_page(self):
        # Titolo
        title = tk.Label(self.content_frame, text="configuration",
                         font=('Arial', 28, 'bold'), bg=self.bg_dark, fg=self.text_color)
        title.pack(pady=(0, 20))

        # Sezione Line
        self.create_section("Line", ["Parameter 1", "Parameter 2"], has_import=True)

        # Sezione Fuel & Oxidiser
        self.create_section("Fuel & Oxidiser", ["Fuel Density (kg/m³)", "Regression Coeff. a"])

        # Sezione Injector
        self.create_section("Injector", ["Discharge Coeff. CD", "Orifice Diameter (m)"])

        # Sezione Nozzle
        self.create_section("Nozzle", ["Expansion Ratio", "Throat Diameter (m)"])

        # Bottone Save Configuration
        button_frame = tk.Frame(self.content_frame, bg=self.bg_dark)
        button_frame.pack(side=tk.BOTTOM, anchor='se', pady=20, padx=20)

        self.save_btn = tk.Button(button_frame, text="Save configuration",
                                  font=('Arial', 12, 'bold'),
                                  bg='#8b0000', fg='white', relief=tk.RAISED,
                                  padx=20, pady=10, command=self.validate_and_save)
        self.save_btn.pack()

        # Valida input inizialmente
        self.validate_inputs()

    def create_section(self, title, fields, has_import=False):
        section = tk.Frame(self.content_frame, bg=self.bg_light, relief=tk.RIDGE, bd=2)
        section.pack(fill=tk.X, pady=10, ipady=15)

        # Header sezione
        header_frame = tk.Frame(section, bg=self.bg_light)
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        section_title = tk.Label(header_frame, text=title, font=('Arial', 16),
                                 bg=self.bg_light, fg='black')
        section_title.pack(side=tk.LEFT)

        # Pulsante import (solo per Line)
        if has_import:
            import_btn = tk.Button(header_frame, text="import line",
                                   font=('Arial', 10), bg='#3c3c3c', fg='white',
                                   relief=tk.RAISED, padx=15, pady=5,
                                   command=self.import_line_placeholder)
            import_btn.pack(side=tk.RIGHT)

        # Campi input
        fields_frame = tk.Frame(section, bg=self.bg_light)
        fields_frame.pack(fill=tk.X, padx=40, pady=10)

        for i, field in enumerate(fields):
            row = tk.Frame(fields_frame, bg=self.bg_light)
            row.pack(fill=tk.X, pady=5)

            label = tk.Label(row, text=field + ":", font=('Arial', 11),
                             bg=self.bg_light, fg='black', width=25, anchor='w')
            label.pack(side=tk.LEFT, padx=(0, 10))

            entry = tk.Entry(row, font=('Arial', 11), width=30, relief=tk.SUNKEN, bd=2)
            entry.pack(side=tk.LEFT)
            entry.bind('<KeyRelease>', lambda e: self.validate_inputs())

            # Salva riferimento all'entry
            self.inputs[f"{title}_{field}"] = entry

    def validate_inputs(self):
        all_valid = True

        for key, entry in self.inputs.items():
            value = entry.get().strip()
            if not value:
                all_valid = False
            else:
                try:
                    float(value)
                except ValueError:
                    all_valid = False

        # Cambia colore del bottone
        if all_valid and len(self.inputs) > 0:
            self.save_btn.configure(bg='#006400')  # Verde scuro
        else:
            self.save_btn.configure(bg='#8b0000')  # Rosso scuro

    def import_line_placeholder(self):
        messagebox.showinfo("Info", "Funzione 'import line' in sviluppo")

    def validate_and_save(self):
        config = {}
        all_valid = True

        for key, entry in self.inputs.items():
            value = entry.get().strip()
            if not value:
                all_valid = False
                break
            try:
                config[key] = float(value)
            except ValueError:
                all_valid = False
                break

        if all_valid:
            messagebox.showinfo("Success", "Configurazione validata! Tutti i campi sono float validi.")
        else:
            messagebox.showerror("Error", "Alcuni campi sono vuoti o non sono numeri validi.")

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
            value = entry.get().strip()
            if value:
                try:
                    config[key] = float(value)
                except ValueError:
                    config[key] = value

        with open(filename, 'w') as f:
            json.dump(config, f, indent=4)

        messagebox.showinfo("Saved", f"Configurazione salvata in:\n{filename}")

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
                        self.inputs[key].delete(0, tk.END)
                        self.inputs[key].insert(0, str(value))

                self.current_file = filename
                self.validate_inputs()
                messagebox.showinfo("Loaded", f"Configurazione caricata da:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Errore nel caricamento:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = HybridRocketGUI(root)
    root.mainloop()