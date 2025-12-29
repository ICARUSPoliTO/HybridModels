import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import numpy as np


# ==================== DATA MODELS ====================

@dataclass
class InputField:
    value: Any = None
    is_valid: bool = False
    error_message: str = ""


@dataclass
class PageData:
    fields: Dict[str, InputField] = field(default_factory=dict)

    def get_values(self) -> Dict[str, Any]:
        return {k: v.value for k, v in self.fields.items() if v.is_valid}

    def is_all_valid(self) -> bool:
        return all(f.is_valid for f in self.fields.values())


# ==================== VALIDATORS ====================

class Validator:
    @staticmethod
    def validate_float(value: str, min_val: float = None, max_val: float = None,
                       exclusive: bool = False) -> tuple[bool, str, float]:
        if not value.strip():
            return False, "Field is required", None
        try:
            val = float(value)
            if min_val is not None:
                if exclusive and val <= min_val:
                    return False, f"Must be > {min_val}", None
                elif not exclusive and val < min_val:
                    return False, f"Must be >= {min_val}", None
            if max_val is not None:
                if exclusive and val >= max_val:
                    return False, f"Must be < {max_val}", None
                elif not exclusive and val > max_val:
                    return False, f"Must be <= {max_val}", None
            return True, "", val
        except ValueError:
            return False, "Must be a number", None

    @staticmethod
    def validate_int(value: str, min_val: int = None, max_val: int = None,
                     exclusive: bool = False) -> tuple[bool, str, int]:
        if not value.strip():
            return False, "Field is required", None
        try:
            val = int(value)
            if min_val is not None:
                if exclusive and val <= min_val:
                    return False, f"Must be > {min_val}", None
                elif not exclusive and val < min_val:
                    return False, f"Must be >= {min_val}", None
            if max_val is not None:
                if exclusive and val >= max_val:
                    return False, f"Must be < {max_val}", None
                elif not exclusive and val > max_val:
                    return False, f"Must be <= {max_val}", None
            return True, "", val
        except ValueError:
            return False, "Must be an integer", None

    @staticmethod
    def validate_string(value: str) -> tuple[bool, str, str]:
        if not value.strip():
            return False, "Field is required", None
        return True, "", value.strip()


# ==================== DATA CONTROLLER ====================

class DataController:
    def __init__(self):
        self.pages_data: Dict[str, PageData] = {}
        self.optimization_results: Optional[Any] = None

    def register_page(self, page_name: str):
        if page_name not in self.pages_data:
            self.pages_data[page_name] = PageData()

    def update_field(self, page_name: str, field_name: str, value: Any, is_valid: bool, error: str = ""):
        if page_name not in self.pages_data:
            self.register_page(page_name)
        self.pages_data[page_name].fields[field_name] = InputField(value, is_valid, error)

    def get_page_data(self, page_name: str) -> PageData:
        return self.pages_data.get(page_name, PageData())

    def get_all_data(self) -> Dict[str, Dict[str, Any]]:
        return {page: data.get_values() for page, data in self.pages_data.items()}

    def is_page_valid(self, page_name: str) -> bool:
        return self.pages_data.get(page_name, PageData()).is_all_valid()

    def save_to_csv(self, filename: str):
        all_data = self.get_all_data()
        rows = []
        for page, fields in all_data.items():
            for field_name, value in fields.items():
                rows.append([page, field_name, value])

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Page', 'Field', 'Value'])
            writer.writerows(rows)

    def set_optimization_results(self, results: Any):
        self.optimization_results = results

    def get_optimization_results(self) -> Any:
        return self.optimization_results


# ==================== BACKEND SIMULATION ====================

def full_range_simulation(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Mock optimization function"""
    time.sleep(2)

    results = {
        'pc_array': np.random.rand(10, 10, 10) * 1e6,
        'mdot_array': np.random.rand(10, 10, 10) * 10,
        'MR_array': np.random.rand(10, 10, 10) * 5,
        'Tc_array': np.random.rand(10, 10, 10) * 3000,
        'Is_array': np.random.rand(10, 10, 10) * 300,
        'flag_array': np.random.randint(0, 3, (10, 10, 10)),
        'converged': True,
        'message': 'Optimization completed successfully'
    }

    return results


# ==================== BASE PAGE ====================

class BasePage(tk.Frame):
    def __init__(self, parent, controller, page_name: str):
        super().__init__(parent, bg='#2b2b2b')
        self.controller = controller
        self.page_name = page_name
        self.controller.data_controller.register_page(page_name)
        self.entries: Dict[str, tk.Entry] = {}
        self.validation_params: Dict[str, Dict] = {}

    def create_labeled_entry(self, parent, label_text: str, field_name: str,
                             row: int, validator_type: str = 'float', **validator_kwargs) -> tk.Entry:
        label = tk.Label(parent, text=label_text, bg='#3c3c3c', fg='white',
                         font=('Arial', 10), anchor='w', width=25)
        label.grid(row=row, column=0, padx=10, pady=5, sticky='w')

        entry = tk.Entry(parent, font=('Arial', 10), width=30,
                         highlightthickness=2, highlightbackground='gray', highlightcolor='gray')
        entry.grid(row=row, column=1, padx=10, pady=5)

        self.entries[field_name] = entry
        self.validation_params[field_name] = {
            'validator_type': validator_type,
            **validator_kwargs
        }

        entry.bind('<KeyRelease>', lambda e: self.validate_field(field_name))
        entry.bind('<FocusOut>', lambda e: self.validate_field(field_name))

        return entry

    def validate_field(self, field_name: str):
        entry = self.entries[field_name]
        params = self.validation_params[field_name]
        value = entry.get()

        validator_type = params.pop('validator_type', 'float')

        if validator_type == 'float':
            is_valid, error, parsed_value = Validator.validate_float(value, **params)
        elif validator_type == 'int':
            is_valid, error, parsed_value = Validator.validate_int(value, **params)
        elif validator_type == 'string':
            is_valid, error, parsed_value = Validator.validate_string(value)
        else:
            is_valid, error, parsed_value = False, "Unknown validator", None

        params['validator_type'] = validator_type

        if is_valid:
            entry.configure(highlightbackground='#00aa00', highlightcolor='#00aa00')
        else:
            entry.configure(highlightbackground='red', highlightcolor='red')

        self.controller.data_controller.update_field(
            self.page_name, field_name, parsed_value, is_valid, error
        )

        return is_valid

    def validate_all(self) -> bool:
        all_valid = True
        for field_name in self.entries.keys():
            if not self.validate_field(field_name):
                all_valid = False
        return all_valid

    def save_data(self):
        if not self.validate_all():
            messagebox.showerror("Validation Error", "Please fix all invalid fields before saving.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Data"
        )

        if filename:
            try:
                self.controller.data_controller.save_to_csv(filename)
                messagebox.showinfo("Success", f"Data saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save data: {str(e)}")

    def send_to_optimization(self):
        if not self.validate_all():
            messagebox.showerror("Validation Error", "Please fix all invalid fields before sending to optimization.")
            return

        self.controller.show_page("OptimizationPage")


# ==================== INPUT PAGES ====================

class FuelOxidiserPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "FuelOxidiser")
        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(self, text="Fuel & Oxidiser Configuration",
                         font=('Arial', 16, 'bold'), bg='#2b2b2b', fg='white')
        title.pack(pady=20)

        form_frame = tk.Frame(self, bg='#3c3c3c', relief=tk.RIDGE, bd=2)
        form_frame.pack(padx=40, pady=20, fill=tk.BOTH, expand=True)

        self.create_labeled_entry(form_frame, "a (regression coefficient):", "a", 0,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(form_frame, "n (regression exponent):", "n", 1)
        self.create_labeled_entry(form_frame, "ρF (kg/m³):", "rho_fuel", 2,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(form_frame, "Oxidizer Temperature (K):", "ox_temp", 3,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(form_frame, "Oxidizer Enthalpy (kJ/mol):", "ox_enthalpy", 4)
        self.create_labeled_entry(form_frame, "Fuel Temperature (K):", "fuel_temp", 5,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(form_frame, "Fuel Enthalpy (kJ/mol):", "fuel_enthalpy", 6)

        button_frame = tk.Frame(self, bg='#2b2b2b')
        button_frame.pack(pady=20)

        save_btn = ttk.Button(button_frame, text="Save Data", command=self.save_data)
        save_btn.pack(side=tk.LEFT, padx=10)

        send_btn = ttk.Button(button_frame, text="Send to Optimization",
                              command=self.send_to_optimization)
        send_btn.pack(side=tk.LEFT, padx=10)


class InjectorPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Injector")
        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(self, text="Injector Configuration",
                         font=('Arial', 16, 'bold'), bg='#2b2b2b', fg='white')
        title.pack(pady=20)

        form_frame = tk.Frame(self, bg='#3c3c3c', relief=tk.RIDGE, bd=2)
        form_frame.pack(padx=40, pady=20, fill=tk.BOTH, expand=True)

        self.create_labeled_entry(form_frame, "CD (Discharge Coefficient):", "CD", 0,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(form_frame, "Gox_min (kg/s/m²):", "Gox_min", 1,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(form_frame, "Gox_max (kg/s/m²):", "Gox_max", 2,
                                  min_val=0, exclusive=True)

        button_frame = tk.Frame(self, bg='#2b2b2b')
        button_frame.pack(pady=20)

        save_btn = ttk.Button(button_frame, text="Save Data", command=self.save_data)
        save_btn.pack(side=tk.LEFT, padx=10)

        send_btn = ttk.Button(button_frame, text="Send to Optimization",
                              command=self.send_to_optimization)
        send_btn.pack(side=tk.LEFT, padx=10)


class NozzlePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Nozzle")
        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(self, text="Nozzle Configuration",
                         font=('Arial', 16, 'bold'), bg='#2b2b2b', fg='white')
        title.pack(pady=20)

        form_frame = tk.Frame(self, bg='#3c3c3c', relief=tk.RIDGE, bd=2)
        form_frame.pack(padx=40, pady=20, fill=tk.BOTH, expand=True)

        self.create_labeled_entry(form_frame, "ε (epsilon):", "epsilon", 0,
                                  min_val=1, exclusive=False)

        button_frame = tk.Frame(self, bg='#2b2b2b')
        button_frame.pack(pady=20)

        save_btn = ttk.Button(button_frame, text="Save Data", command=self.save_data)
        save_btn.pack(side=tk.LEFT, padx=10)

        send_btn = ttk.Button(button_frame, text="Send to Optimization",
                              command=self.send_to_optimization)
        send_btn.pack(side=tk.LEFT, padx=10)


class OptimizationInputPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "OptimizationInput")
        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(self, text="Optimization Parameters",
                         font=('Arial', 16, 'bold'), bg='#2b2b2b', fg='white')
        title.pack(pady=20)

        canvas = tk.Canvas(self, bg='#2b2b2b', highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#3c3c3c')

        scrollable_frame.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=40, pady=20)
        scrollbar.pack(side="right", fill="y")

        self.create_labeled_entry(scrollable_frame, "parameter_points:", "parameter_points", 0,
                                  validator_type='int', min_val=0, exclusive=True)
        self.create_labeled_entry(scrollable_frame, "Dport-Dt.min:", "Dport_Dt_min", 1,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(scrollable_frame, "Dport-Dt.max:", "Dport_Dt_max", 2,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(scrollable_frame, "Dinj-Dt.min:", "Dinj_Dt_min", 3,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(scrollable_frame, "Dinj-Dt.max:", "Dinj_Dt_max", 4,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(scrollable_frame, "Lc-Dt.min:", "Lc_Dt_min", 5,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(scrollable_frame, "Lc-Dt.max:", "Lc_Dt_max", 6,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(scrollable_frame, "Ptank (Pa):", "ptank", 7,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(scrollable_frame, "Ttank (K):", "Ttank", 8,
                                  min_val=0, exclusive=True)
        self.create_labeled_entry(scrollable_frame, "Pamb (Pa):", "pamb", 9,
                                  min_val=0, exclusive=True)

        button_frame = tk.Frame(self, bg='#2b2b2b')
        button_frame.pack(pady=20)

        save_btn = ttk.Button(button_frame, text="Save Data", command=self.save_data)
        save_btn.pack(side=tk.LEFT, padx=10)

        send_btn = ttk.Button(button_frame, text="Send to Optimization",
                              command=self.send_to_optimization)
        send_btn.pack(side=tk.LEFT, padx=10)


# ==================== OPTIMIZATION RESULTS PAGE ====================

class OptimizationPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg='#2b2b2b')
        self.controller = controller
        self.is_running = False
        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(self, text="Optimization",
                         font=('Arial', 16, 'bold'), bg='#2b2b2b', fg='white')
        title.pack(pady=20)

        info_frame = tk.Frame(self, bg='#3c3c3c', relief=tk.RIDGE, bd=2)
        info_frame.pack(padx=40, pady=10, fill=tk.BOTH, expand=True)

        info_label = tk.Label(info_frame, text="Click 'Run Optimization' to start the simulation.",
                              font=('Arial', 11), bg='#3c3c3c', fg='white', wraplength=600)
        info_label.pack(pady=20, padx=20)

        self.status_label = tk.Label(info_frame, text="Status: Ready",
                                     font=('Arial', 10, 'italic'), bg='#3c3c3c', fg='yellow')
        self.status_label.pack(pady=10)

        self.progress = ttk.Progressbar(info_frame, mode='indeterminate', length=400)
        self.progress.pack(pady=10)

        self.results_text = tk.Text(info_frame, height=15, width=70, bg='#1e1e1e',
                                    fg='white', font=('Courier', 9))
        self.results_text.pack(pady=20, padx=20)

        button_frame = tk.Frame(self, bg='#2b2b2b')
        button_frame.pack(pady=20)

        self.run_btn = ttk.Button(button_frame, text="Run Optimization",
                                  command=self.run_optimization)
        self.run_btn.pack(side=tk.LEFT, padx=10)

        export_btn = ttk.Button(button_frame, text="Export Results",
                                command=self.export_results)
        export_btn.pack(side=tk.LEFT, padx=10)

    def run_optimization(self):
        if self.is_running:
            messagebox.showwarning("Warning", "Optimization is already running!")
            return

        all_data = self.controller.data_controller.get_all_data()

        if not all_data:
            messagebox.showerror("Error", "No data available. Please fill input pages first.")
            return

        self.is_running = True
        self.run_btn.config(state='disabled')
        self.status_label.config(text="Status: Running...")
        self.progress.start(10)
        self.results_text.delete('1.0', tk.END)
        self.results_text.insert('1.0', "Starting optimization...\n")

        thread = threading.Thread(target=self._run_optimization_thread, args=(all_data,))
        thread.daemon = True
        thread.start()

    def _run_optimization_thread(self, input_data):
        try:
            results = full_range_simulation(input_data)
            self.controller.data_controller.set_optimization_results(results)
            self.after(0, self._on_optimization_complete, results, None)
        except Exception as e:
            self.after(0, self._on_optimization_complete, None, e)

    def _on_optimization_complete(self, results, error):
        self.is_running = False
        self.run_btn.config(state='normal')
        self.progress.stop()

        if error:
            self.status_label.config(text=f"Status: Error - {str(error)}")
            self.results_text.insert(tk.END, f"\nERROR: {str(error)}\n")
            messagebox.showerror("Optimization Error", str(error))
        else:
            self.status_label.config(text="Status: Complete")
            self.display_results(results)
            messagebox.showinfo("Success", "Optimization completed successfully!")

    def display_results(self, results):
        self.results_text.delete('1.0', tk.END)
        self.results_text.insert('1.0', "Optimization Results:\n")
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")

        if isinstance(results, dict):
            for key, value in results.items():
                if isinstance(value, np.ndarray):
                    self.results_text.insert(tk.END, f"{key}:\n")
                    self.results_text.insert(tk.END, f"  Shape: {value.shape}\n")
                    self.results_text.insert(tk.END, f"  Min: {np.min(value):.4f}\n")
                    self.results_text.insert(tk.END, f"  Max: {np.max(value):.4f}\n")
                    self.results_text.insert(tk.END, f"  Mean: {np.mean(value):.4f}\n\n")
                else:
                    self.results_text.insert(tk.END, f"{key}: {value}\n")
        else:
            self.results_text.insert(tk.END, str(results))

    def export_results(self):
        results = self.controller.data_controller.get_optimization_results()

        if results is None:
            messagebox.showwarning("Warning", "No results to export. Run optimization first.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Results"
        )

        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Key', 'Value'])
                    for key, value in results.items():
                        if isinstance(value, np.ndarray):
                            writer.writerow([key, f"Array shape {value.shape}"])
                        else:
                            writer.writerow([key, value])
                messagebox.showinfo("Success", f"Results exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results: {str(e)}")


# ==================== MAIN CONTROLLER ====================

class MainController(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Hybrid Rocket Engine Optimizer")
        self.geometry("900x700")
        self.configure(bg='#2b2b2b')

        self.data_controller = DataController()

        self.create_menu()

        container = tk.Frame(self, bg='#2b2b2b')
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for PageClass in (FuelOxidiserPage, InjectorPage, NozzlePage,
                          OptimizationInputPage, OptimizationPage):
            page_name = PageClass.__name__
            frame = PageClass(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_page("FuelOxidiserPage")

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        nav_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Navigation", menu=nav_menu)

        nav_menu.add_command(label="Fuel & Oxidiser",
                             command=lambda: self.show_page("FuelOxidiserPage"))
        nav_menu.add_command(label="Injector",
                             command=lambda: self.show_page("InjectorPage"))
        nav_menu.add_command(label="Nozzle",
                             command=lambda: self.show_page("NozzlePage"))
        nav_menu.add_command(label="Optimization Input",
                             command=lambda: self.show_page("OptimizationInputPage"))
        nav_menu.add_separator()
        nav_menu.add_command(label="Run Optimization",
                             command=lambda: self.show_page("OptimizationPage"))
        nav_menu.add_separator()
        nav_menu.add_command(label="Exit", command=self.quit)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)

        file_menu.add_command(label="Save All Data", command=self.save_all_data)
        file_menu.add_command(label="Exit", command=self.quit)

    def show_page(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def save_all_data(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save All Data"
        )

        if filename:
            try:
                self.data_controller.save_to_csv(filename)
                messagebox.showinfo("Success", f"All data saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save data: {str(e)}")


# ==================== MAIN ====================

if __name__ == "__main__":
    app = MainController()
    app.mainloop()