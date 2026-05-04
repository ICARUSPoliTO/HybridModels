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
import matplotlib.pyplot as plt


class MissionOutputPage:
    """Mission output page for simulation results with plots"""
    
    # Define plot tabs with parameters
    PLOT_TABS = {
        'Thrust & Performance': ['Thrust', 'Is', 'Ivac'],
        'Pressures': ['pc', 'pinj', 'ptank', 'pe'],
        'Mass Flow': ['mdot', 'mdot_ox', 'mdot_fuel'],
        'Combustion': ['MR', 'Gox', 'r'],
        'Nozzle': ['Me', 'pe', 'eps'],
        'Temperatures': ['Tc', 'Tc_CEA', 'Ttank'],
        'Masses': ['mL', 'm_fuel'],
        'Geometry': ['Ab', 'Ap'],
    }
    
    # Parameters that need Gox limits overlay
    PARAMS_WITH_GOX_LIMITS = ['Gox']
    
    # Labels and units for each parameter
    PARAM_INFO = {
        'Thrust': ('Thrust', 'N'),
        'Is': ('Specific Impulse', 's'),
        'Ivac': ('Vacuum Isp', 's'),
        'pc': ('Chamber Pressure', 'bar', 1e-5),  # Scale factor Pa -> bar
        'pinj': ('Injector Pressure', 'bar', 1e-5),
        'pT': ('Tank Pressure', 'bar', 1e-5),
        'pe': ('Nozzle Exit Pressure', 'bar', 1e-5),
        'ptank': ('Tank Pressure', 'bar', 1e-5),  # Alternative key
        'mdot': ('Total Mass Flow', 'kg/s'),
        'mdot_ox': ('Oxidizer Flow', 'kg/s'),
        'mdot_fuel': ('Fuel Flow', 'kg/s'),
        'MR': ('Mixture Ratio', '-'),
        'Gox': ('Oxidizer Mass Flux', 'kg/m²s'),
        'r': ('Regression Rate', 'mm/s', 1000),  # m/s -> mm/s
        'Me': ('Nozzle Exit Mach', '-'),
        'eps': ('Expansion Ratio', '-'),
        'Tc': ('Chamber Temperature', 'K'),
        'Tc_CEA': ('CEA Temperature', 'K'),
        'TL': ('Tank Liquid Temp', 'K'),
        'Ttank': ('Tank Temperature', 'K'),  # Alternative key
        'mL': ('Oxidizer Mass', 'kg'),
        'm_fuel': ('Fuel Mass', 'kg'),
        'mV': ('Vapor Mass', 'kg'),
        'Ab': ('Burning Area', 'm²'),
        'Ap': ('Port Area', 'm²'),
    }
    
    def __init__(self, parent, controller=None):
        """Initialize mission output page"""
        self.parent = parent
        self.controller = controller
        self.results = None
        self.time_data = None
        self.log_data = None
        self.geometry_history = None  # For grain geometry evolution
        
        # Gox limits for display
        self.gox_min = 100.0
        self.gox_max = 800.0
        
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
    
    def display_results(self, time_data, performances, log_data, 
                        gox_min=100.0, gox_max=800.0, geometry_history=None):
        """Display mission simulation results with plots
        
        Args:
            time_data: List of time values
            performances: Dict of performance arrays
            log_data: Simulation log text
            gox_min: Minimum Gox limit for plot overlay
            gox_max: Maximum Gox limit for plot overlay
            geometry_history: List of (x, y, t) tuples showing grain evolution
        """
        self.time_data = time_data
        self.results = performances
        self.log_data = log_data
        self.gox_min = gox_min
        self.gox_max = gox_max
        
        # Extract geometry history from results if not provided
        if geometry_history is None and 'x' in performances and 'y' in performances:
            x_list = performances.get('x', [])
            y_list = performances.get('y', [])
            if x_list and y_list and time_data:
                # Sample every N steps to avoid too many lines
                n_total = len(time_data)
                n_samples = min(20, n_total)  # Max 20 snapshots
                step = max(1, n_total // n_samples)
                
                geometry_history = []
                for i in range(0, n_total, step):
                    if i < len(x_list) and x_list[i] is not None:
                        x_arr = np.array(x_list[i]) if hasattr(x_list[i], '__iter__') else None
                        y_arr = np.array(y_list[i]) if hasattr(y_list[i], '__iter__') else None
                        if x_arr is not None and len(x_arr) > 0:
                            geometry_history.append((x_arr, y_arr, time_data[i]))
                
                # Always include last point
                if n_total > 0 and (n_total - 1) % step != 0:
                    i = n_total - 1
                    if i < len(x_list) and x_list[i] is not None:
                        x_arr = np.array(x_list[i]) if hasattr(x_list[i], '__iter__') else None
                        y_arr = np.array(y_list[i]) if hasattr(y_list[i], '__iter__') else None
                        if x_arr is not None and len(x_arr) > 0:
                            geometry_history.append((x_arr, y_arr, time_data[i]))
        
        self.geometry_history = geometry_history
        
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
        
        # Add Grain Geometry Evolution tab if data available
        if self.geometry_history and len(self.geometry_history) > 0:
            geom_frame = tk.Frame(notebook, bg=COLORS['bg_dark'])
            notebook.add(geom_frame, text='Grain Evolution')
            self._create_geometry_tab(geom_frame)
    
    def _create_geometry_tab(self, parent):
        """Create tab showing grain geometry evolution over time"""
        if not self.geometry_history or len(self.geometry_history) == 0:
            return
        
        # Create figure
        fig = Figure(figsize=(8, 8), dpi=100, facecolor=COLORS['bg_dark'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLORS['bg_medium'])
        
        n_snapshots = len(self.geometry_history)
        
        # Plot each snapshot with color gradient (blue -> red)
        for i, (x, y, t) in enumerate(self.geometry_history):
            if x is None or y is None:
                continue
            
            # Convert to numpy arrays if needed
            x = np.asarray(x).ravel()
            y = np.asarray(y).ravel()
            
            if len(x) < 3:
                continue
            
            # Close the polygon for plotting
            x_closed = np.append(x, x[0])
            y_closed = np.append(y, y[0])
            
            # Color gradient from blue (initial) to red (final)
            ratio = i / max(n_snapshots - 1, 1)
            color = (ratio, 0, 1 - ratio)  # RGB: blue to red
            
            # Line width: thicker for first and last
            if i == 0:
                lw = 2.5
                label = f't = {t:.2f} s (initial)'
            elif i == n_snapshots - 1:
                lw = 2.5
                label = f't = {t:.2f} s (final)'
            else:
                lw = 1.0
                label = None
            
            ax.plot(x_closed * 1000, y_closed * 1000, 
                   color=color, linewidth=lw, alpha=0.8, label=label)
        
        # Add chamber wall circle
        theta = np.linspace(0, 2*np.pi, 100)
        max_extent = 0
        for x, y, _ in self.geometry_history:
            if x is not None and len(x) > 0:
                x = np.asarray(x).ravel()
                y = np.asarray(y).ravel()
                max_extent = max(max_extent, np.max(np.abs(x)), np.max(np.abs(y)))
        
        if max_extent > 0:
            D_ch = max_extent * 2.2  # Slightly larger than grain
            ax.plot((D_ch/2)*1000*np.cos(theta), (D_ch/2)*1000*np.sin(theta), 
                   'k--', linewidth=1.5, alpha=0.5, label='Chamber wall')
        
        ax.set_xlabel('x [mm]', fontsize=11, color=COLORS['text_color'])
        ax.set_ylabel('y [mm]', fontsize=11, color=COLORS['text_color'])
        ax.set_title('Grain Geometry Evolution (Blue=Initial → Red=Final)', 
                    fontsize=12, color=COLORS['text_color'], fontweight='bold')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, color=COLORS['text_muted'])
        ax.tick_params(colors=COLORS['text_color'])
        ax.legend(loc='upper right', fontsize=9)
        
        for spine in ax.spines.values():
            spine.set_color(COLORS['text_muted'])
        
        fig.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        
        toolbar_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
        
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
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
            
            # Plot main data
            ax.plot(time[:len(y_data)], y_data, color=COLORS['accent'], linewidth=1.5, label=label)
            
            # Add Gox limits if this is the Gox parameter
            if param == 'Gox':
                t_range = time[:len(y_data)]
                ax.axhline(y=self.gox_min, color='red', linestyle='--', linewidth=2, 
                          label=f'Gox_min = {self.gox_min} kg/m²s')
                ax.axhline(y=self.gox_max, color='red', linestyle='--', linewidth=2,
                          label=f'Gox_max = {self.gox_max} kg/m²s')
                ax.legend(loc='upper right', fontsize=8)
                
                # Fill valid region
                y_min_plot = ax.get_ylim()[0]
                y_max_plot = ax.get_ylim()[1]
                ax.fill_between(t_range, self.gox_min, self.gox_max, 
                               alpha=0.1, color='green', label='Valid region')
            
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
