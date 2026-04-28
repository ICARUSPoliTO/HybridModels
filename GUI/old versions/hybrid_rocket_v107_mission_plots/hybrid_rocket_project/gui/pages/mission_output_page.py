"""
Mission Output Page - Mission simulation results with interactive plots

Displays:
- Summary statistics
- Interactive time-series plots (Thrust, Pressures, Temperatures, etc.)
- Export functionality
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import csv
from config.constants import COLORS, FONTS

# Import matplotlib with TkAgg backend
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class MissionOutputPage:
    """Mission output page for simulation results with plots"""
    
    # Define plot tabs with parameters
    PLOT_TABS = {
        'Thrust & Performance': ['Thrust', 'Is', 'Ivac'],
        'Pressures': ['pc', 'pinj', 'pT'],
        'Mass Flow': ['mdot', 'mdot_ox', 'mdot_fuel'],
        'Combustion': ['MR', 'Gox', 'r'],
        'Temperatures': ['Tc', 'Tc_CEA', 'TL'],
        'Masses': ['mL', 'm_fuel', 'mV'],
    }
    
    # Labels and units for each parameter
    PARAM_INFO = {
        'Thrust': ('Thrust', 'N'),
        'Is': ('Specific Impulse', 's'),
        'Ivac': ('Vacuum Isp', 's'),
        'pc': ('Chamber Pressure', 'bar', 1e-5),  # Scale factor Pa -> bar
        'pinj': ('Injector Pressure', 'bar', 1e-5),
        'pT': ('Tank Pressure', 'bar', 1e-5),
        'mdot': ('Total Mass Flow', 'kg/s'),
        'mdot_ox': ('Oxidizer Flow', 'kg/s'),
        'mdot_fuel': ('Fuel Flow', 'kg/s'),
        'MR': ('Mixture Ratio', '-'),
        'Gox': ('Oxidizer Mass Flux', 'kg/m²s'),
        'r': ('Regression Rate', 'mm/s', 1000),  # m/s -> mm/s
        'Tc': ('Chamber Temperature', 'K'),
        'Tc_CEA': ('CEA Temperature', 'K'),
        'TL': ('Tank Liquid Temp', 'K'),
        'mL': ('Oxidizer Mass', 'kg'),
        'm_fuel': ('Fuel Mass', 'kg'),
        'mV': ('Vapor Mass', 'kg'),
    }
    
    def __init__(self, parent, controller=None):
        """Initialize mission output page"""
        self.parent = parent
        self.controller = controller
        self.results = None
        self.time_data = None
        self.log_data = None
        
        # Plot-related
        self.figures = {}
        self.canvases = {}
        
        self.create_page()
    
    def create_page(self):
        """Create the mission output page content"""
        # Title
        title = tk.Label(
            self.parent, 
            text="Mission Results", 
            font=FONTS['title'],
            bg=COLORS['bg_dark'], 
            fg=COLORS['text_color']
        )
        title.pack(pady=20)
        
        # Main container
        self.main_frame = tk.Frame(self.parent, bg=COLORS['bg_dark'])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create initial placeholder
        self.create_placeholder()
    
    def create_placeholder(self):
        """Create placeholder when no results are available"""
        self.placeholder_frame = tk.Frame(self.main_frame, bg=COLORS['bg_dark'])
        self.placeholder_frame.pack(fill=tk.BOTH, expand=True)
        
        section = tk.LabelFrame(
            self.placeholder_frame, 
            text="Mission Simulation Results", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        info_text = tk.Label(
            section,
            text="No mission results available.\n\n"
                 "Go to the Mission page and click:\n"
                 "• 'Run Mission' - to simulate with fixed parameters\n"
                 "• 'Match Mission' - to find configuration matching requirements\n\n"
                 "Results will be displayed here with interactive plots.",
            font=FONTS['label'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            justify=tk.CENTER
        )
        info_text.pack(pady=40, padx=40)
    
    def display_results(self, time_data, performances, log_data):
        """Display mission simulation results with plots"""
        self.time_data = time_data
        self.results = performances
        self.log_data = log_data
        
        # Clear existing content
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Create main horizontal split: left (summary) | right (plots)
        paned = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL, 
                               bg=COLORS['bg_dark'], sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # === LEFT PANEL: Summary ===
        left_frame = tk.Frame(paned, bg=COLORS['bg_dark'], width=350)
        paned.add(left_frame, minsize=300)
        
        # Scrollable summary
        left_canvas = tk.Canvas(left_frame, bg=COLORS['bg_dark'], highlightthickness=0)
        left_scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=left_canvas.yview)
        left_scrollable = tk.Frame(left_canvas, bg=COLORS['bg_dark'])
        
        left_scrollable.bind("<Configure>", 
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")))
        left_canvas.create_window((0, 0), window=left_scrollable, anchor="nw")
        left_canvas.configure(yscrollcommand=left_scrollbar.set)
        
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.create_summary_section(left_scrollable)
        self.create_termination_section(left_scrollable)
        self.create_export_section(left_scrollable)
        
        # === RIGHT PANEL: Plots ===
        right_frame = tk.Frame(paned, bg=COLORS['bg_dark'])
        paned.add(right_frame, minsize=500)
        
        self.create_plots_section(right_frame)
    
    def create_summary_section(self, parent):
        """Create summary statistics section"""
        section = tk.LabelFrame(
            parent, 
            text="Mission Summary", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, pady=10, padx=5)
        
        if not self.results or not self.time_data:
            return
        
        # Safe value extractors
        def safe_max(lst):
            filtered = [x for x in lst if x is not None and np.isfinite(x)]
            return max(filtered) if filtered else 0
        
        def safe_mean(lst):
            filtered = [x for x in lst if x is not None and np.isfinite(x)]
            return np.mean(filtered) if filtered else 0
        
        def safe_min(lst):
            filtered = [x for x in lst if x is not None and np.isfinite(x)]
            return min(filtered) if filtered else 0
        
        total_time = self.time_data[-1] if self.time_data else 0
        
        thrust_list = self.results.get('Thrust', [])
        pc_list = self.results.get('pc', [])
        is_list = self.results.get('Is', [])
        mL_list = self.results.get('mL', [])
        m_fuel_list = self.results.get('m_fuel', [])
        
        # Summary data
        summary_data = [
            ("Simulation Time", f"{total_time:.3f} s"),
            ("Time Steps", f"{len(self.time_data)}"),
            ("", ""),
            ("Max Thrust", f"{safe_max(thrust_list):.1f} N"),
            ("Mean Thrust", f"{safe_mean(thrust_list):.1f} N"),
            ("", ""),
            ("Max pc", f"{safe_max(pc_list)/1e5:.2f} bar"),
            ("Mean pc", f"{safe_mean(pc_list)/1e5:.2f} bar"),
            ("", ""),
            ("Max Isp", f"{safe_max(is_list):.1f} s"),
            ("Mean Isp", f"{safe_mean(is_list):.1f} s"),
            ("", ""),
            ("Oxidizer Used", f"{safe_max(mL_list) - safe_min(mL_list):.3f} kg"),
            ("Fuel Used", f"{safe_max(m_fuel_list) - safe_min(m_fuel_list):.3f} kg"),
        ]
        
        row = 0
        for label, value in summary_data:
            if label == "":
                row += 1
                continue
            tk.Label(
                section, text=label + ":", font=('Arial', 10),
                bg=COLORS['bg_medium'], fg=COLORS['text_color'], anchor='e'
            ).grid(row=row, column=0, sticky='e', padx=(10, 5), pady=2)
            tk.Label(
                section, text=value, font=('Arial', 10, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['accent'], anchor='w'
            ).grid(row=row, column=1, sticky='w', padx=(5, 10), pady=2)
            row += 1
    
    def create_termination_section(self, parent):
        """Create termination log section"""
        section = tk.LabelFrame(
            parent, 
            text="Simulation Log", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, pady=10, padx=5)
        
        log_text = self.log_data if self.log_data else "No log available."
        
        tk.Label(
            section, text=log_text, font=('Arial', 9),
            bg=COLORS['bg_medium'], fg=COLORS['text_color'],
            justify=tk.LEFT, anchor='w', wraplength=300
        ).pack(padx=10, pady=10, fill=tk.X)
    
    def create_export_section(self, parent):
        """Create export buttons section"""
        section = tk.Frame(parent, bg=COLORS['bg_dark'])
        section.pack(fill=tk.X, pady=10, padx=5)
        
        tk.Button(
            section,
            text="💾 Export CSV",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.export_to_csv,
            cursor='hand2',
            padx=15, pady=8
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            section,
            text="📊 Export Excel",
            font=FONTS['button'],
            bg=COLORS['accent'],
            fg='white',
            command=self.export_to_excel,
            cursor='hand2',
            padx=15, pady=8
        ).pack(side=tk.LEFT, padx=5)
    
    def create_plots_section(self, parent):
        """Create tabbed plots section"""
        # Notebook for plot tabs
        style = ttk.Style()
        style.configure('Plot.TNotebook', background=COLORS['bg_dark'])
        style.configure('Plot.TNotebook.Tab', padding=[10, 5])
        
        notebook = ttk.Notebook(parent, style='Plot.TNotebook')
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a tab for each plot group
        for tab_name, params in self.PLOT_TABS.items():
            # Check if we have data for any param in this tab
            has_data = any(
                param in self.results and 
                any(v is not None for v in self.results.get(param, []))
                for param in params
            )
            
            if not has_data:
                continue
            
            tab_frame = tk.Frame(notebook, bg=COLORS['bg_dark'])
            notebook.add(tab_frame, text=tab_name)
            
            self._create_plot_tab(tab_frame, params)
    
    def _create_plot_tab(self, parent, params):
        """Create a single plot tab with multiple subplots"""
        # Filter params that have data
        valid_params = [p for p in params 
                       if p in self.results and 
                       any(v is not None for v in self.results.get(p, []))]
        
        if not valid_params:
            return
        
        n_plots = len(valid_params)
        
        # Create figure with subplots
        fig = Figure(figsize=(10, 3.5 * n_plots), dpi=100, facecolor=COLORS['bg_dark'])
        
        time = np.array(self.time_data)
        
        for i, param in enumerate(valid_params):
            ax = fig.add_subplot(n_plots, 1, i + 1)
            ax.set_facecolor(COLORS['bg_medium'])
            
            # Get data and apply scale factor if needed
            data = self.results.get(param, [])
            y_data = []
            for v in data:
                if v is not None and np.isfinite(v):
                    y_data.append(v)
                else:
                    y_data.append(np.nan)
            y_data = np.array(y_data)
            
            # Apply scale factor if defined
            info = self.PARAM_INFO.get(param, (param, '', 1))
            label = info[0]
            unit = info[1]
            scale = info[2] if len(info) > 2 else 1
            y_data = y_data * scale
            
            # Plot
            ax.plot(time[:len(y_data)], y_data, color=COLORS['accent'], linewidth=1.5)
            
            # Labels
            ax.set_xlabel('Time [s]', fontsize=10, color=COLORS['text_color'])
            ax.set_ylabel(f'{label} [{unit}]', fontsize=10, color=COLORS['text_color'])
            ax.set_title(f'{label} vs Time', fontsize=11, color=COLORS['text_color'], fontweight='bold')
            
            # Grid
            ax.grid(True, alpha=0.3, color=COLORS['text_muted'])
            ax.tick_params(colors=COLORS['text_color'])
            
            # Spine colors
            for spine in ax.spines.values():
                spine.set_color(COLORS['text_muted'])
        
        fig.tight_layout(pad=2.0)
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        
        # Toolbar
        toolbar_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
        
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def export_to_csv(self):
        """Export full results to CSV file"""
        if not self.results or not self.time_data:
            messagebox.showerror("Error", "No results to export.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Mission Results"
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                keys = ['time'] + list(self.results.keys())
                writer.writerow(keys)
                
                for i in range(len(self.time_data)):
                    row = [self.time_data[i]]
                    for key in list(self.results.keys()):
                        try:
                            val = self.results[key][i] if i < len(self.results[key]) else ''
                            if val is None:
                                val = ''
                            row.append(val)
                        except:
                            row.append('')
                    writer.writerow(row)
            
            messagebox.showinfo("Success", f"Results exported to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{str(e)}")
    
    def export_to_excel(self):
        """Export results to Excel file"""
        if not self.results or not self.time_data:
            messagebox.showerror("Error", "No results to export.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Export Mission Results to Excel"
        )
        
        if not filepath:
            return
        
        try:
            import pandas as pd
            
            # Create DataFrame
            data = {'time': self.time_data}
            for key, values in self.results.items():
                # Pad with None if shorter
                if len(values) < len(self.time_data):
                    values = list(values) + [None] * (len(self.time_data) - len(values))
                data[key] = values[:len(self.time_data)]
            
            df = pd.DataFrame(data)
            
            # Write to Excel
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Mission_Data', index=False)
                
                # Summary sheet
                summary_data = {
                    'Parameter': [],
                    'Max': [],
                    'Mean': [],
                    'Min': []
                }
                
                for key in ['Thrust', 'pc', 'Is', 'MR', 'Gox', 'Tc']:
                    if key in self.results:
                        vals = [v for v in self.results[key] if v is not None and np.isfinite(v)]
                        if vals:
                            summary_data['Parameter'].append(key)
                            summary_data['Max'].append(max(vals))
                            summary_data['Mean'].append(np.mean(vals))
                            summary_data['Min'].append(min(vals))
                
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            messagebox.showinfo("Success", f"Results exported to:\n{filepath}")
        except ImportError:
            messagebox.showerror("Error", "pandas/openpyxl not installed.\nUse CSV export instead.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{str(e)}")


def create_mission_output_page(parent, controller=None):
    """Factory function to create mission output page"""
    return MissionOutputPage(parent, controller)
