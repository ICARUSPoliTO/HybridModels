import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import numpy as np
import threading
import sys
import os

# Import your optimization module
try:
    import Performance.optimization as optimization
except ImportError:
    print("Warning: Could not import optimization module")
    optimization = None


class HybridRocketGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hybrid Rocket Model")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')

        # Colors
        self.bg_dark = '#2b2b2b'
        self.bg_medium = '#3c3c3c'
        self.bg_light = '#8c8c8c'
        self.bg_active = '#5c5c5c'
        self.text_color = 'white'
        self.button_inactive = '#a0a0a0'
        self.button_active = '#6c6c6c'

        # Variables
        self.inputs = {}
        self.current_page = 'configuration'
        self.optimization_results = None
        self.is_optimizing = False

        # Create UI
        self.create_header()
        self.create_sidebar()

        # Content area
        self.content_frame = tk.Frame(self.root, bg=self.bg_dark)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Show configuration page
        self.show_configuration_page()

    def create_header(self):
        header = tk.Frame(self.root, bg=self.bg_dark, height=60)
        header.pack(side=tk.TOP, fill=tk.X)

        title = tk.Label(header, text="Hybrid Rocket Model", font=('Arial', 24, 'bold'),
                         bg=self.bg_dark, fg=self.text_color)
        title.pack(side=tk.LEFT, padx=20, pady=10)

    def create_sidebar(self):
        sidebar = tk.Frame(self.root, bg=self.bg_medium, width=150)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Menu button with dropdown
        menu_frame = tk.Frame(sidebar, bg=self.bg_medium)
        menu_frame.pack(pady=10, padx=10, fill=tk.X)

        self.menu_button = tk.Button(menu_frame, text="Main Menu ☰",
                                     font=('Arial', 10), bg=self.bg_light, fg='black',
                                     relief=tk.RAISED, command=self.toggle_menu)
        self.menu_button.pack(fill=tk.X)

        # Dropdown menu
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

        # Page buttons
        self.page_buttons = {}
        pages = ['configuration', 'optimization', 'output']

        for page in pages:
            btn = tk.Button(sidebar, text=page.capitalize(), font=('Arial', 11),
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
        # Update button colors
        for p, btn in self.page_buttons.items():
            if p == page:
                btn.configure(bg=self.button_active)
            else:
                btn.configure(bg=self.button_inactive)

        self.current_page = page

        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Show appropriate page
        if page == 'configuration':
            self.show_configuration_page()
        elif page == 'optimization':
            self.show_optimization_page()
        elif page == 'output':
            self.show_output_page()

    def show_configuration_page(self):
        # Title
        title = tk.Label(self.content_frame, text="Configuration",
                         font=('Arial', 28, 'bold'), bg=self.bg_dark, fg=self.text_color)
        title.pack(pady=(0, 20))

        # Create scrollable frame
        canvas = tk.Canvas(self.content_frame, bg=self.bg_dark)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_dark)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Fuel & Oxidizer Section
        self.create_section(scrollable_frame, "Fuel & Oxidizer", [
            ("Fuel Density (kg/m³)", "rho_fuel", "850"),
            ("Regression Coeff. a", "a", "0.00017"),
            ("Regression Exp. n", "n", "0.5"),
            ("Oxidizer (CP)", "oxidizer_cp", "NitrousOxide"),
            ("Oxidizer (CEA)", "oxidizer_cea", "N2O"),
            ("Fuel Name", "fuel_name", "paraffin"),
            ("Fuel Formula", "fuel_formula", "C 73 H 124"),
            ("Fuel Temp (K)", "fuel_temp", "533"),
            ("Fuel Enthalpy (kJ/mol)", "fuel_enthalpy", "-1860.6")
        ])

        # Injector Section
        self.create_section(scrollable_frame, "Injector", [
            ("Discharge Coeff. CD", "CD", "0.8"),
            ("Dinj/Dt Min", "dinj_dt_min", "0.8"),
            ("Dinj/Dt Max", "dinj_dt_max", "1.0"),
            ("Dinj/Dt Step", "dinj_dt_step", "0.05")
        ])

        # Chamber Section
        self.create_section(scrollable_frame, "Chamber", [
            ("Dport/Dt Min", "dport_dt_min", "3.5"),
            ("Dport/Dt Max", "dport_dt_max", "5.0"),
            ("Dport/Dt Step", "dport_dt_step", "0.5"),
            ("Lc/Dt Min", "lc_dt_min", "8"),
            ("Lc/Dt Max", "lc_dt_max", "10"),
            ("Lc/Dt Step", "lc_dt_step", "1")
        ])

        # Nozzle & Conditions Section
        self.create_section(scrollable_frame, "Nozzle & Conditions", [
            ("Expansion Ratio", "eps", "adapt"),
            ("Tank Pressure (Pa)", "ptank", "5500000"),
            ("Tank Temperature (K)", "Ttank", "288"),
            ("Ambient Pressure (Pa)", "pamb", "100000"),
            ("Initial Gamma", "gamma0", "1.3")
        ])

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Save button
        button_frame = tk.Frame(self.content_frame, bg=self.bg_dark)
        button_frame.pack(side=tk.BOTTOM, anchor='se', pady=20, padx=20)

        self.save_btn = tk.Button(button_frame, text="Validate Configuration",
                                  font=('Arial', 12, 'bold'),
                                  bg='#8b0000', fg='white', relief=tk.RAISED,
                                  padx=20, pady=10, command=self.validate_and_save)
        self.save_btn.pack()

        self.validate_inputs()

    def create_section(self, parent, title, fields):
        section = tk.Frame(parent, bg=self.bg_light, relief=tk.RIDGE, bd=2)
        section.pack(fill=tk.X, pady=10, ipady=15)

        # Header
        header_frame = tk.Frame(section, bg=self.bg_light)
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        section_title = tk.Label(header_frame, text=title, font=('Arial', 16, 'bold'),
                                 bg=self.bg_light, fg='black')
        section_title.pack(side=tk.LEFT)

        # Input fields
        fields_frame = tk.Frame(section, bg=self.bg_light)
        fields_frame.pack(fill=tk.X, padx=40, pady=10)

        for label_text, key, default_value in fields:
            row = tk.Frame(fields_frame, bg=self.bg_light)
            row.pack(fill=tk.X, pady=5)

            label = tk.Label(row, text=label_text + ":", font=('Arial', 11),
                             bg=self.bg_light, fg='black', width=30, anchor='w')
            label.pack(side=tk.LEFT, padx=(0, 10))

            entry = tk.Entry(row, font=('Arial', 11), width=30, relief=tk.SUNKEN, bd=2)
            entry.insert(0, default_value)
            entry.pack(side=tk.LEFT)
            entry.bind('<KeyRelease>', lambda e: self.validate_inputs())

            self.inputs[key] = entry

    def validate_inputs(self):
        all_valid = True

        for key, entry in self.inputs.items():
            value = entry.get().strip()
            if not value:
                all_valid = False
                continue

            # Skip validation for string fields
            if key in ['oxidizer_cp', 'oxidizer_cea', 'fuel_name', 'fuel_formula', 'eps']:
                continue

            try:
                float(value)
            except ValueError:
                all_valid = False

        if hasattr(self, 'save_btn'):
            if all_valid and len(self.inputs) > 0:
                self.save_btn.configure(bg='#006400')
            else:
                self.save_btn.configure(bg='#8b0000')

    def validate_and_save(self):
        config = self.get_config_dict()
        if config:
            messagebox.showinfo("Success", "Configuration validated successfully!")
        else:
            messagebox.showerror("Error", "Some fields are invalid.")

    def get_config_dict(self):
        """Extract configuration from inputs"""
        try:
            config = {}
            for key, entry in self.inputs.items():
                value = entry.get().strip()
                if not value:
                    return None

                # String fields
                if key in ['oxidizer_cp', 'oxidizer_cea', 'fuel_name', 'fuel_formula', 'eps']:
                    config[key] = value
                else:
                    config[key] = float(value)

            return config
        except ValueError:
            return None

    def show_optimization_page(self):
        title = tk.Label(self.content_frame, text="Optimization",
                         font=('Arial', 28, 'bold'), bg=self.bg_dark, fg=self.text_color)
        title.pack(pady=(0, 20))

        # Instructions
        info = tk.Label(self.content_frame,
                        text="Configure parameters in the Configuration page, then run optimization.",
                        font=('Arial', 12), bg=self.bg_dark, fg=self.text_color, wraplength=800)
        info.pack(pady=20)

        # Progress frame
        progress_frame = tk.Frame(self.content_frame, bg=self.bg_medium, relief=tk.RIDGE, bd=2)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Progress label
        self.progress_label = tk.Label(progress_frame, text="Ready to optimize",
                                       font=('Arial', 14), bg=self.bg_medium, fg=self.text_color)
        self.progress_label.pack(pady=20)

        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate', length=400)
        self.progress_bar.pack(pady=10)

        # Console output
        console_label = tk.Label(progress_frame, text="Console Output:",
                                 font=('Arial', 12, 'bold'), bg=self.bg_medium, fg=self.text_color)
        console_label.pack(pady=(20, 5))

        self.console_output = scrolledtext.ScrolledText(progress_frame, height=15,
                                                        bg='black', fg='#00ff00',
                                                        font=('Courier', 10))
        self.console_output.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Run button
        button_frame = tk.Frame(self.content_frame, bg=self.bg_dark)
        button_frame.pack(side=tk.BOTTOM, pady=20)

        self.run_btn = tk.Button(button_frame, text="Run Optimization",
                                 font=('Arial', 14, 'bold'),
                                 bg='#006400', fg='white', relief=tk.RAISED,
                                 padx=30, pady=15, command=self.run_optimization)
        self.run_btn.pack()

    def log_to_console(self, message):
        """Add message to console output"""
        if hasattr(self, 'console_output'):
            self.console_output.insert(tk.END, message + "\n")
            self.console_output.see(tk.END)
            self.console_output.update()

    def run_optimization(self):
        """Run the optimization in a separate thread"""
        if self.is_optimizing:
            messagebox.showwarning("Warning", "Optimization already running!")
            return

        config = self.get_config_dict()
        if not config:
            messagebox.showerror("Error", "Invalid configuration. Please check inputs.")
            return

        if optimization is None:
            messagebox.showerror("Error", "Optimization module not found!")
            return

        # Disable button and start progress
        self.run_btn.configure(state='disabled', bg='#8b0000')
        self.progress_bar.start(10)
        self.is_optimizing = True
        self.progress_label.configure(text="Optimization running...")
        self.log_to_console("=" * 60)
        self.log_to_console("Starting optimization...")

        # Run in thread
        thread = threading.Thread(target=self._optimization_worker, args=(config,))
        thread.daemon = True
        thread.start()

    def _optimization_worker(self, config):
        """Worker thread for optimization"""
        try:
            self.log_to_console(f"Configuration loaded: {len(self.inputs)} parameters")

            # Prepare parameters
            Dport_Dt_range = np.arange(config['dport_dt_min'],
                                       config['dport_dt_max'],
                                       config['dport_dt_step'])
            Dinj_Dt_range = np.arange(config['dinj_dt_min'],
                                      config['dinj_dt_max'],
                                      config['dinj_dt_step'])
            Lc_Dt_range = np.arange(config['lc_dt_min'],
                                    config['lc_dt_max'],
                                    config['lc_dt_step'])

            self.log_to_console(f"Dport/Dt range: {len(Dport_Dt_range)} points")
            self.log_to_console(f"Dinj/Dt range: {len(Dinj_Dt_range)} points")
            self.log_to_console(f"Lc/Dt range: {len(Lc_Dt_range)} points")
            self.log_to_console(f"Total configurations: {len(Dport_Dt_range) * len(Dinj_Dt_range) * len(Lc_Dt_range)}")

            # Prepare fuel and oxidizer dicts
            oxidizer = {
                "OxidizerCP": config['oxidizer_cp'],
                "OxidizerCEA": config['oxidizer_cea'],
                "Weight fraction": "100",
                "Exploded Formula": "",
                "Temperature [K]": "",
                "Specific Enthalpy [kj/mol]": ""
            }

            fuel = {
                "Fuels": [config['fuel_name']],
                "Weight fraction": ["100"],
                "Exploded Formula": [config['fuel_formula']],
                "Temperature [K]": [config['fuel_temp']],
                "Specific Enthalpy [kj/mol]": [config['fuel_enthalpy']]
            }

            self.log_to_console("Running simulation...")

            # Run optimization
            results = optimization.full_range_simulation(
                Dport_Dt_range, Dinj_Dt_range, Lc_Dt_range,
                config['eps'], config['ptank'], config['Ttank'],
                config['CD'], config['a'], config['n'], config['rho_fuel'],
                oxidizer, fuel, config['pamb'], config['gamma0']
            )

            # Store results
            self.optimization_results = {
                'arrays': results,
                'ranges': {
                    'Dport_Dt': Dport_Dt_range,
                    'Dinj_Dt': Dinj_Dt_range,
                    'Lc_Dt': Lc_Dt_range
                },
                'config': config
            }

            # Count convergence
            flag_array = results[-1]
            converged = np.sum(flag_array == 0)
            total = flag_array.size

            self.log_to_console(f"Optimization complete!")
            self.log_to_console(f"Converged: {converged}/{total} ({100 * converged / total:.1f}%)")
            self.log_to_console("Results stored. View in Output page.")

            # Re-enable button
            self.root.after(0, self._finish_optimization)

        except Exception as e:
            self.log_to_console(f"ERROR: {str(e)}")
            import traceback
            self.log_to_console(traceback.format_exc())
            self.root.after(0, self._finish_optimization)

    def _finish_optimization(self):
        """Clean up after optimization"""
        self.progress_bar.stop()
        self.run_btn.configure(state='normal', bg='#006400')
        self.is_optimizing = False
        self.progress_label.configure(text="Optimization complete")

    def show_output_page(self):
        title = tk.Label(self.content_frame, text="Output",
                         font=('Arial', 28, 'bold'), bg=self.bg_dark, fg=self.text_color)
        title.pack(pady=(0, 20))

        if self.optimization_results is None:
            info = tk.Label(self.content_frame,
                            text="No results available. Run optimization first.",
                            font=('Arial', 14), bg=self.bg_dark, fg=self.text_color)
            info.pack(pady=50)
            return

        # Create scrollable frame for results
        canvas = tk.Canvas(self.content_frame, bg=self.bg_dark)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_dark)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Display results summary
        results = self.optimization_results['arrays']
        flag_array = results[-1]

        summary_frame = tk.Frame(scrollable_frame, bg=self.bg_light, relief=tk.RIDGE, bd=2)
        summary_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(summary_frame, text="Optimization Summary", font=('Arial', 16, 'bold'),
                 bg=self.bg_light).pack(pady=10)

        converged = np.sum(flag_array == 0)
        total = flag_array.size

        summary_text = f"""
Total configurations: {total}
Converged: {converged} ({100 * converged / total:.1f}%)
Pressure diverged: {np.sum(flag_array == 1)}
CEA diverged: {np.sum(flag_array == -1)}
Both diverged: {np.sum(flag_array == 2)}
No solution: {np.sum(flag_array == 10)}
        """

        tk.Label(summary_frame, text=summary_text, font=('Arial', 12),
                 bg=self.bg_light, justify=tk.LEFT).pack(pady=10)

        # Best configuration (highest Is)
        if converged > 0:
            Is_array = results[16]
            mask = flag_array == 0
            Is_converged = np.where(mask, Is_array, -np.inf)
            best_idx = np.unravel_index(np.argmax(Is_converged), Is_converged.shape)

            best_frame = tk.Frame(scrollable_frame, bg=self.bg_light, relief=tk.RIDGE, bd=2)
            best_frame.pack(fill=tk.X, padx=20, pady=10)

            tk.Label(best_frame, text="Best Configuration (Max Is)", font=('Arial', 16, 'bold'),
                     bg=self.bg_light).pack(pady=10)

            ranges = self.optimization_results['ranges']
            best_dport = ranges['Dport_Dt'][best_idx[0]]
            best_dinj = ranges['Dinj_Dt'][best_idx[1]]
            best_lc = ranges['Lc_Dt'][best_idx[2]]

            best_text = f"""
Dport/Dt: {best_dport:.3f}
Dinj/Dt: {best_dinj:.3f}
Lc/Dt: {best_lc:.3f}

Chamber Pressure: {results[0][best_idx]:.2f} Pa
Specific Impulse: {results[16][best_idx]:.2f} s
Mixture Ratio: {results[8][best_idx]:.3f}
Chamber Temperature: {results[10][best_idx]:.2f} K
            """

            tk.Label(best_frame, text=best_text, font=('Arial', 12),
                     bg=self.bg_light, justify=tk.LEFT).pack(pady=10)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Export button
        export_btn = tk.Button(self.content_frame, text="Export Results",
                               font=('Arial', 12, 'bold'),
                               bg='#006400', fg='white', relief=tk.RAISED,
                               padx=20, pady=10, command=self.export_results)
        export_btn.pack(side=tk.BOTTOM, pady=20)

    def export_results(self):
        """Export results to numpy file"""
        if self.optimization_results is None:
            messagebox.showerror("Error", "No results to export")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".npz",
            filetypes=[("NumPy files", "*.npz"), ("All files", "*.*")]
        )

        if filename:
            results = self.optimization_results['arrays']
            ranges = self.optimization_results['ranges']

            np.savez(filename,
                     pc=results[0], Fpc=results[1], p_inj=results[2],
                     mdot_ox=results[3], mdot_fuel=results[4], mdot=results[5],
                     Gox=results[6], r=results[7], MR=results[8],
                     eps=results[9], Tc=results[10], MW=results[11],
                     gamma=results[12], cs=results[13], CF_vac=results[14],
                     CF=results[15], Ivac=results[16], Is=results[17],
                     flag=results[18],
                     Dport_Dt_range=ranges['Dport_Dt'],
                     Dinj_Dt_range=ranges['Dinj_Dt'],
                     Lc_Dt_range=ranges['Lc_Dt'])

            messagebox.showinfo("Success", f"Results exported to:\n{filename}")

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
        config = self.get_config_dict()
        if config:
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
                        self.inputs[key].delete(0, tk.END)
                        self.inputs[key].insert(0, str(value))

                self.current_file = filename
                self.validate_inputs()
                messagebox.showinfo("Loaded", f"Configuration loaded from:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading file:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = HybridRocketGUI(root)
    root.mainloop()