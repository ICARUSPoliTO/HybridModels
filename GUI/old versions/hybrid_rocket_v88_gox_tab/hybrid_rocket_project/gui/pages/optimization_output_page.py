"""
Optimization Output Page - Optimization results visualization

Displays optimization results with:
- Left side: Textual results with scroll
- Right side: 4 tabs with interactive contour plots (Response Surfaces)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from config.constants import COLORS, FONTS

# Matplotlib imports for embedding in tkinter
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class OptimizationOutputPage:
    """Optimization output page for results visualization"""
    
    # Define which variables go in each tab
    TAB_DEFINITIONS = {
        'Gox Analysis': {
            'variables': ['Gox_array'],
            'labels': {
                'Gox_array': 'Oxidizer Mass Flux - Gox [kg/(s·m²)]'
            },
            'units': {
                'Gox_array': 'kg/(s·m²)'
            },
            'single_plot': True  # Flag for special single large plot
        },
        'Performance': {
            'variables': ['Ivac_array', 'Is_array', 'cs_array', 'CF_vac_array', 'CF_array'],
            'labels': {
                'Ivac_array': 'Ivac [s]',
                'Is_array': 'Is [s]',
                'cs_array': 'c* [m/s]',
                'CF_vac_array': 'CF_vac',
                'CF_array': 'CF'
            },
            'units': {
                'Ivac_array': 's',
                'Is_array': 's',
                'cs_array': 'm/s',
                'CF_vac_array': '-',
                'CF_array': '-'
            }
        },
        'Pressures & Flows': {
            'variables': ['pc_array', 'mdot_array', 'mdot_ox_array', 'mdot_fuel_array'],
            'labels': {
                'pc_array': 'pc [bar]',
                'mdot_array': 'ṁ_total [kg/(s·m²)]',
                'mdot_ox_array': 'ṁ_ox [kg/(s·m²)]',
                'mdot_fuel_array': 'ṁ_fuel [kg/(s·m²)]'
            },
            'units': {
                'pc_array': 'bar',
                'mdot_array': 'kg/(s·m²)',
                'mdot_ox_array': 'kg/(s·m²)',
                'mdot_fuel_array': 'kg/(s·m²)'
            },
            'scale_factors': {
                'pc_array': 1e-5  # Pa to bar
            }
        },
        'Combustion': {
            'variables': ['MR_array', 'Tc_array', 'r_array'],
            'labels': {
                'MR_array': 'MR (O/F)',
                'Tc_array': 'Tc [K]',
                'r_array': 'r [m/s]'
            },
            'units': {
                'MR_array': '-',
                'Tc_array': 'K',
                'r_array': 'm/s'
            }
        },
        'Thermodynamics': {
            'variables': ['gamma_array', 'MW_array', 'eps_array', 'flag_array'],
            'labels': {
                'gamma_array': 'γ (gamma)',
                'MW_array': 'MW [kg/kmol]',
                'eps_array': 'ε (expansion ratio)',
                'flag_array': 'Convergence Flag'
            },
            'units': {
                'gamma_array': '-',
                'MW_array': 'kg/kmol',
                'eps_array': '-',
                'flag_array': '-'
            }
        }
    }
    
    def __init__(self, parent, controller=None):
        """
        Initialize optimization output page
        
        Args:
            parent: Parent frame to contain this page
            controller: ApplicationController instance (optional)
        """
        self.parent = parent
        self.controller = controller
        self.results = None
        self.ranges = None  # Will store Dport_Dt, Dinj_Dt, Lc_Dt ranges
        self.gox_min = 100.0  # Default Gox min
        self.gox_max = 800.0  # Default Gox max
        
        # Store references to plot elements for updates
        self.tab_canvases = {}
        self.tab_figures = {}
        self.slice_sliders = {}
        self.slice_labels = {}
        self.current_slice_indices = {}
        
        self.create_page()
    
    def create_page(self):
        """Create the optimization output page content"""
        # Title
        title = tk.Label(
            self.parent, 
            text="Optimization Output", 
            font=FONTS['title'],
            bg=COLORS['bg_dark'], 
            fg=COLORS['text_color']
        )
        title.pack(pady=20)
        
        # Main container with two columns
        main_container = tk.Frame(self.parent, bg=COLORS['bg_dark'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Configure grid weights - left side smaller, right side larger for plots
        main_container.grid_columnconfigure(0, weight=1, minsize=250)
        main_container.grid_columnconfigure(1, weight=5)
        main_container.grid_rowconfigure(0, weight=1)
        
        # LEFT SIDE - Results Values
        self.create_results_section(main_container)
        
        # RIGHT SIDE - Tabbed Plots
        self.create_plots_section(main_container)
        
        # Bottom buttons
        self.create_buttons()
    
    def create_results_section(self, parent):
        """Create left side results section"""
        left_frame = tk.LabelFrame(
            parent,
            text="Optimization Results",
            font=FONTS['section'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            width=280
        )
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        left_frame.grid_propagate(False)  # Prevent frame from resizing to fit contents
        
        # Scrollable text area for results
        text_frame = tk.Frame(left_frame, bg=COLORS['bg_medium'])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text = tk.Text(
            text_frame,
            yscrollcommand=scrollbar.set,
            font=('Courier', 9),
            bg='white',
            fg='black',
            wrap=tk.WORD,
            width=30
        )
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_text.yview)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            self.results_text.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(event):
            self.results_text.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            self.results_text.unbind_all("<MouseWheel>")
        
        self.results_text.bind('<Enter>', _bind_mousewheel)
        self.results_text.bind('<Leave>', _unbind_mousewheel)
        
        # Initial message
        self.results_text.insert(tk.END, "No results to display.\n\n")
        self.results_text.insert(tk.END, "Run an optimization from the Optimization page to see results here.")
        self.results_text.config(state=tk.DISABLED)
    
    def create_plots_section(self, parent):
        """Create right side plots section with tabs"""
        right_frame = tk.LabelFrame(
            parent,
            text="Response Surfaces",
            font=FONTS['section'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color']
        )
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        
        # Create notebook (tabbed interface)
        style = ttk.Style()
        style.configure('TNotebook', background=COLORS['bg_medium'])
        style.configure('TNotebook.Tab', font=FONTS['label'], padding=[10, 5])
        
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        for tab_name in self.TAB_DEFINITIONS.keys():
            tab_frame = tk.Frame(self.notebook, bg=COLORS['bg_medium'])
            self.notebook.add(tab_frame, text=tab_name)
            
            # Create placeholder content for each tab
            self.create_tab_placeholder(tab_frame, tab_name)
    
    def create_tab_placeholder(self, tab_frame, tab_name):
        """Create placeholder content for a tab before results are loaded"""
        placeholder = tk.Label(
            tab_frame,
            text=f"No data available for {tab_name}\n\n"
                 "Run an optimization to generate plots.",
            font=FONTS['label'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            justify=tk.CENTER
        )
        placeholder.pack(expand=True)
    
    def create_tab_content(self, tab_frame, tab_name):
        """Create actual plot content for a tab"""
        # Clear existing content
        for widget in tab_frame.winfo_children():
            widget.destroy()
        
        tab_def = self.TAB_DEFINITIONS[tab_name]
        variables = tab_def['variables']
        labels = tab_def['labels']
        
        # Filter to only include variables that exist in results
        available_vars = [v for v in variables if v in self.results]
        
        if not available_vars:
            placeholder = tk.Label(
                tab_frame,
                text=f"No data available for {tab_name}",
                font=FONTS['label'],
                bg=COLORS['bg_medium'],
                fg=COLORS['text_color']
            )
            placeholder.pack(expand=True)
            return
        
        # Main container for this tab
        main_frame = tk.Frame(tab_frame, bg=COLORS['bg_medium'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Slider frame at top
        slider_frame = tk.Frame(main_frame, bg=COLORS['bg_medium'])
        slider_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Slice dimension label
        tk.Label(
            slider_frame,
            text="Lc/Dt slice:",
            font=FONTS['label'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color']
        ).pack(side=tk.LEFT, padx=5)
        
        # Get Lc/Dt range size
        sample_data = self.results[available_vars[0]]
        lc_size = sample_data.shape[2]
        
        # Initialize slice index for this tab
        self.current_slice_indices[tab_name] = lc_size // 2
        
        # Slice value label
        slice_value_label = tk.Label(
            slider_frame,
            text=self.get_slice_label(tab_name),
            font=FONTS['label'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            width=20
        )
        slice_value_label.pack(side=tk.RIGHT, padx=5)
        self.slice_labels[tab_name] = slice_value_label
        
        # Slider
        slider = tk.Scale(
            slider_frame,
            from_=0,
            to=lc_size - 1,
            orient=tk.HORIZONTAL,
            length=300,
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            highlightthickness=0,
            command=lambda val, tn=tab_name: self.on_slice_change(tn, int(val))
        )
        slider.set(self.current_slice_indices[tab_name])
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.slice_sliders[tab_name] = slider
        
        # Plot frame with scrollable canvas
        plot_container = tk.Frame(main_frame, bg=COLORS['bg_medium'])
        plot_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollable area for plots
        plot_canvas = tk.Canvas(plot_container, bg=COLORS['bg_medium'], highlightthickness=0)
        plot_scrollbar = tk.Scrollbar(plot_container, orient=tk.VERTICAL, command=plot_canvas.yview)
        plot_frame = tk.Frame(plot_canvas, bg=COLORS['bg_medium'])
        
        plot_frame.bind(
            "<Configure>",
            lambda e: plot_canvas.configure(scrollregion=plot_canvas.bbox("all"))
        )
        
        plot_canvas.create_window((0, 0), window=plot_frame, anchor="nw")
        plot_canvas.configure(yscrollcommand=plot_scrollbar.set)
        
        # Mouse wheel scrolling for plot area
        def _on_plot_mousewheel(event):
            plot_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_plot_mousewheel(event):
            plot_canvas.bind_all("<MouseWheel>", _on_plot_mousewheel)
        
        def _unbind_plot_mousewheel(event):
            plot_canvas.unbind_all("<MouseWheel>")
        
        plot_canvas.bind('<Enter>', _bind_plot_mousewheel)
        plot_canvas.bind('<Leave>', _unbind_plot_mousewheel)
        
        plot_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        plot_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create figure with subplots
        n_plots = len(available_vars)
        n_cols = min(3, n_plots)
        n_rows = (n_plots + n_cols - 1) // n_cols
        
        fig = Figure(figsize=(12, 3.5 * n_rows), dpi=100)
        fig.patch.set_facecolor('#3c3c3c')
        
        self.tab_figures[tab_name] = {
            'figure': fig,
            'variables': available_vars,
            'labels': labels,
            'n_rows': n_rows,
            'n_cols': n_cols
        }
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.tab_canvases[tab_name] = canvas
        
        # Add toolbar for zoom/pan
        toolbar_frame = tk.Frame(plot_frame, bg=COLORS['bg_medium'])
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
        
        # Draw initial plots
        self.update_tab_plots(tab_name)
    
    def get_slice_label(self, tab_name):
        """Get the label text for current slice"""
        if self.ranges is None:
            return "N/A"
        
        idx = self.current_slice_indices.get(tab_name, 0)
        lc_range = self.ranges.get('Lc_Dt_range', [])
        
        if idx < len(lc_range):
            return f"Lc/Dt = {lc_range[idx]:.2f}"
        return f"Index = {idx}"
    
    def on_slice_change(self, tab_name, new_index):
        """Handle slider change for a tab"""
        self.current_slice_indices[tab_name] = new_index
        
        # Update slice label
        if tab_name in self.slice_labels:
            self.slice_labels[tab_name].config(text=self.get_slice_label(tab_name))
        
        # Update plots
        self.update_tab_plots(tab_name)
    
    def update_tab_plots(self, tab_name):
        """Update all plots in a tab with current slice"""
        if tab_name not in self.tab_figures:
            return
        
        fig_data = self.tab_figures[tab_name]
        fig = fig_data['figure']
        variables = fig_data['variables']
        labels = fig_data['labels']
        n_rows = fig_data['n_rows']
        n_cols = fig_data['n_cols']
        
        slice_idx = self.current_slice_indices.get(tab_name, 0)
        
        # Clear figure
        fig.clear()
        
        # Get axis ranges
        dport_range = self.ranges.get('Dport_Dt_range', np.arange(10))
        dinj_range = self.ranges.get('Dinj_Dt_range', np.arange(10))
        lc_range = self.ranges.get('Lc_Dt_range', np.arange(10))
        
        # Get scale factors if defined
        tab_def = self.TAB_DEFINITIONS[tab_name]
        scale_factors = tab_def.get('scale_factors', {})
        is_single_plot = tab_def.get('single_plot', False)
        
        # Create meshgrid for contour plots
        X, Y = np.meshgrid(dport_range, dinj_range)
        
        for i, var_name in enumerate(variables):
            ax = fig.add_subplot(n_rows, n_cols, i + 1)
            
            # Get data slice (Dport x Dinj at fixed Lc)
            data_3d = self.results[var_name]
            
            # Handle edge case where slice_idx is out of bounds
            if slice_idx >= data_3d.shape[2]:
                slice_idx = data_3d.shape[2] - 1
            
            data_2d = data_3d[:, :, slice_idx].T  # Transpose for correct orientation
            
            # Apply scale factor if defined
            if var_name in scale_factors:
                data_2d = data_2d * scale_factors[var_name]
            
            # Create contour plot
            try:
                # Filled contours
                levels = 20
                contourf = ax.contourf(X, Y, data_2d, levels=levels, cmap='RdYlBu_r')
                
                # Contour lines with labels
                contour_lines = ax.contour(X, Y, data_2d, levels=10, colors='black', 
                                           linewidths=0.5, alpha=0.7)
                ax.clabel(contour_lines, inline=True, fontsize=8, fmt='%.2f')
                
                # Colorbar
                cbar = fig.colorbar(contourf, ax=ax, shrink=0.8)
                cbar.ax.tick_params(labelsize=8)
                
                # Special handling for Gox_array: add limit lines and optimal point
                if var_name == 'Gox_array':
                    # Add Gox_min line (red dashed)
                    try:
                        cs_min = ax.contour(X, Y, data_2d, levels=[self.gox_min], 
                                           colors='red', linewidths=2.5, linestyles='--')
                        if len(cs_min.allsegs[0]) > 0:
                            ax.clabel(cs_min, inline=True, fontsize=10, 
                                     fmt=f'Gox_min={self.gox_min:.0f}', colors='red')
                    except:
                        pass  # Gox_min might be outside data range
                    
                    # Add Gox_max line (red dashed)
                    try:
                        cs_max = ax.contour(X, Y, data_2d, levels=[self.gox_max], 
                                           colors='red', linewidths=2.5, linestyles='--')
                        if len(cs_max.allsegs[0]) > 0:
                            ax.clabel(cs_max, inline=True, fontsize=10, 
                                     fmt=f'Gox_max={self.gox_max:.0f}', colors='red')
                    except:
                        pass  # Gox_max might be outside data range
                    
                    # Add optimal point marker if available and at this slice
                    if hasattr(self, 'optimal_indices') and self.optimal_indices is not None:
                        opt_i, opt_j, opt_k = self.optimal_indices
                        if opt_k == slice_idx:
                            opt_dport = dport_range[opt_i] if opt_i < len(dport_range) else opt_i
                            opt_dinj = dinj_range[opt_j] if opt_j < len(dinj_range) else opt_j
                            opt_gox = data_2d[opt_j, opt_i] if opt_j < data_2d.shape[0] and opt_i < data_2d.shape[1] else 0
                            ax.plot(opt_dport, opt_dinj, 'g*', markersize=20 if is_single_plot else 15, 
                                   markeredgecolor='white', markeredgewidth=2,
                                   label=f'Optimal (Gox={opt_gox:.1f})')
                            ax.legend(loc='upper right', fontsize=10 if is_single_plot else 8)
                    
                    # For single plot tab, add more info
                    if is_single_plot:
                        # Add text box with Gox limits info
                        lc_val = lc_range[slice_idx] if slice_idx < len(lc_range) else slice_idx
                        info_text = (f'Lc/Dt = {lc_val:.2f}\n'
                                    f'Gox limits: [{self.gox_min:.0f}, {self.gox_max:.0f}] kg/(s·m²)\n'
                                    f'Valid region: between red dashed lines')
                        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=9,
                               verticalalignment='top', bbox=dict(boxstyle='round', 
                               facecolor='white', alpha=0.8))
                
            except Exception as e:
                ax.text(0.5, 0.5, f"Error plotting:\n{str(e)}", 
                       transform=ax.transAxes, ha='center', va='center')
            
            # Labels and title
            fontsize_label = 11 if is_single_plot else 9
            fontsize_title = 14 if is_single_plot else 10
            ax.set_xlabel('Dport/Dt', fontsize=fontsize_label)
            ax.set_ylabel('Dinj/Dt', fontsize=fontsize_label)
            ax.set_title(labels.get(var_name, var_name), fontsize=fontsize_title, fontweight='bold')
            ax.tick_params(labelsize=10 if is_single_plot else 8)
        
        # Adjust layout
        fig.tight_layout()
        
        # Redraw canvas
        if tab_name in self.tab_canvases:
            self.tab_canvases[tab_name].draw()
    
    def create_buttons(self):
        """Create bottom buttons"""
        button_frame = tk.Frame(self.parent, bg=COLORS['bg_dark'])
        button_frame.pack(side=tk.BOTTOM, pady=20)
        
        self.save_button = tk.Button(
            button_frame,
            text="Save Results to CSV",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.save_results,
            cursor='hand2',
            padx=20,
            pady=10,
            state=tk.DISABLED  # Disabled until results are loaded
        )
        self.save_button.pack(side=tk.LEFT, padx=10)
        
        # Export to Excel button
        self.export_excel_button = tk.Button(
            button_frame,
            text="Export All to Excel",
            font=FONTS['button'],
            bg=COLORS['accent'],
            fg='white',
            command=self.export_to_excel,
            cursor='hand2',
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.export_excel_button.pack(side=tk.LEFT, padx=10)
        
        self.export_plots_button = tk.Button(
            button_frame,
            text="Export Plots",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.export_plots,
            cursor='hand2',
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.export_plots_button.pack(side=tk.LEFT, padx=10)
    
    def display_results(self, results, ranges=None, gox_min=100.0, gox_max=800.0):
        """
        Display optimization results
        
        Args:
            results: Dictionary of results from optimization
            ranges: Dictionary with Dport_Dt_range, Dinj_Dt_range, Lc_Dt_range (optional)
            gox_min: Minimum acceptable Gox [kg/(s·m²)]
            gox_max: Maximum acceptable Gox [kg/(s·m²)]
        """
        self.results = results
        self.gox_min = gox_min
        self.gox_max = gox_max
        
        # Try to get ranges from controller if not provided
        if ranges is None and self.controller is not None:
            inputs = self.controller.prepare_optimization_inputs()
            if inputs:
                self.ranges = {
                    'Dport_Dt_range': inputs.get('Dport_Dt_range', np.linspace(2, 5, 10)),
                    'Dinj_Dt_range': inputs.get('Dinj_Dt_range', np.linspace(0.5, 1, 10)),
                    'Lc_Dt_range': inputs.get('Lc_Dt_range', np.linspace(5, 15, 10))
                }
        else:
            self.ranges = ranges
        
        # If still no ranges, create default ones based on data shape
        if self.ranges is None:
            sample_key = list(results.keys())[0]
            shape = results[sample_key].shape
            self.ranges = {
                'Dport_Dt_range': np.arange(shape[0]),
                'Dinj_Dt_range': np.arange(shape[1]),
                'Lc_Dt_range': np.arange(shape[2])
            }
        
        # Update text results
        self._update_text_results()
        
        # Update plot tabs
        self._update_plot_tabs()
        
        # Enable buttons
        self.save_button.config(state=tk.NORMAL)
        self.export_excel_button.config(state=tk.NORMAL)
        self.export_plots_button.config(state=tk.NORMAL)
    
    def _update_text_results(self):
        """Update the text results panel"""
        # Enable text widget for editing
        self.results_text.config(state=tk.NORMAL)
        
        # Clear previous content
        self.results_text.delete(1.0, tk.END)
        
        # Format and display results
        self.results_text.insert(tk.END, "=" * 50 + "\n")
        self.results_text.insert(tk.END, "OPTIMIZATION RESULTS\n")
        self.results_text.insert(tk.END, "=" * 50 + "\n\n")
        
        # Display ranges info
        if self.ranges:
            self.results_text.insert(tk.END, "Parameter Ranges:\n")
            self.results_text.insert(tk.END, "-" * 30 + "\n")
            for name, values in self.ranges.items():
                display_name = name.replace('_range', '').replace('_', '/')
                self.results_text.insert(tk.END, 
                    f"{display_name}: [{values[0]:.3f} - {values[-1]:.3f}] ({len(values)} pts)\n")
            self.results_text.insert(tk.END, "\n")
        
        # Display Gox filter limits
        self.results_text.insert(tk.END, "Gox Filter Limits:\n")
        self.results_text.insert(tk.END, "-" * 30 + "\n")
        self.results_text.insert(tk.END, f"Gox_min = {self.gox_min:.1f} kg/(s·m²)\n")
        self.results_text.insert(tk.END, f"Gox_max = {self.gox_max:.1f} kg/(s·m²)\n")
        self.results_text.insert(tk.END, "\n")
        
        # ================================================================
        # BEST RESULTS RANKED BY Ivac (FILTERED BY GOX)
        # ================================================================
        self.results_text.insert(tk.END, "=" * 40 + "\n")
        self.results_text.insert(tk.END, "TOP 10 CONFIGURATIONS BY Ivac\n")
        self.results_text.insert(tk.END, "(filtered by Gox limits)\n")
        self.results_text.insert(tk.END, "=" * 40 + "\n\n")
        
        if 'Ivac_array' in self.results:
            ivac = self.results['Ivac_array']
            gox_arr = self.results.get('Gox_array', np.zeros_like(ivac))
            
            # Get ranges for display
            if self.ranges:
                dport_range = self.ranges.get('Dport_Dt_range', np.array([0]))
                dinj_range = self.ranges.get('Dinj_Dt_range', np.array([0]))
                lc_range = self.ranges.get('Lc_Dt_range', np.array([0]))
            else:
                dport_range = np.arange(ivac.shape[0])
                dinj_range = np.arange(ivac.shape[1])
                lc_range = np.arange(ivac.shape[2])
            
            # Flatten and get indices
            flat_ivac = ivac.flatten()
            flat_gox = gox_arr.flatten()
            
            # Valid mask: positive Ivac, finite, AND Gox within limits
            valid_mask = (flat_ivac > 0) & np.isfinite(flat_ivac)
            gox_mask = (flat_gox >= self.gox_min) & (flat_gox <= self.gox_max)
            combined_mask = valid_mask & gox_mask
            
            valid_indices = np.where(combined_mask)[0]
            
            # Count filtered out
            total_valid = np.sum(valid_mask)
            gox_filtered = total_valid - len(valid_indices)
            
            if gox_filtered > 0:
                self.results_text.insert(tk.END, 
                    f"Note: {gox_filtered} solutions excluded (Gox outside [{self.gox_min:.0f}, {self.gox_max:.0f}])\n\n")
            
            if len(valid_indices) > 0:
                # Sort by Ivac descending
                sorted_indices = valid_indices[np.argsort(flat_ivac[valid_indices])[::-1]]
                
                # Get top 10
                top_n = min(10, len(sorted_indices))
                
                # Header - added Gox column
                self.results_text.insert(tk.END, 
                    f"{'#':>3} {'Ivac[s]':>10} {'Is[s]':>10} {'Dport/Dt':>10} {'Dinj/Dt':>10} {'Lc/Dt':>10} {'MR':>8} {'pc[bar]':>10} {'Gox':>12}\n")
                self.results_text.insert(tk.END, "-" * 96 + "\n")
                
                # Get other arrays
                is_arr = self.results.get('Is_array', np.zeros_like(ivac))
                mr_arr = self.results.get('MR_array', np.zeros_like(ivac))
                pc_arr = self.results.get('pc_array', np.zeros_like(ivac))
                
                for rank, flat_idx in enumerate(sorted_indices[:top_n], 1):
                    # Convert flat index to 3D indices
                    idx = np.unravel_index(flat_idx, ivac.shape)
                    i, j, k = idx
                    
                    ivac_val = ivac[i, j, k]
                    is_val = is_arr[i, j, k] if is_arr.size > 0 else 0
                    mr_val = mr_arr[i, j, k] if mr_arr.size > 0 else 0
                    pc_val = pc_arr[i, j, k] / 1e5 if pc_arr.size > 0 else 0  # Pa to bar
                    gox_val = gox_arr[i, j, k] if gox_arr.size > 0 else 0
                    
                    dport_val = dport_range[i] if i < len(dport_range) else i
                    dinj_val = dinj_range[j] if j < len(dinj_range) else j
                    lc_val = lc_range[k] if k < len(lc_range) else k
                    
                    self.results_text.insert(tk.END, 
                        f"{rank:>3} {ivac_val:>10.2f} {is_val:>10.2f} {dport_val:>10.2f} {dinj_val:>10.3f} {lc_val:>10.2f} {mr_val:>8.2f} {pc_val:>10.2f} {gox_val:>12.2f}\n")
                
                self.results_text.insert(tk.END, "\n")
                
                # Best configuration summary (WITHIN GOX LIMITS)
                best_idx = sorted_indices[0]
                best_3d = np.unravel_index(best_idx, ivac.shape)
                i, j, k = best_3d
                
                self.results_text.insert(tk.END, "=" * 40 + "\n")
                self.results_text.insert(tk.END, "OPTIMAL CONFIGURATION\n")
                self.results_text.insert(tk.END, "(best Ivac within Gox limits)\n")
                self.results_text.insert(tk.END, "=" * 40 + "\n\n")
                
                best_dport = dport_range[i] if i < len(dport_range) else i
                best_dinj = dinj_range[j] if j < len(dinj_range) else j
                best_lc = lc_range[k] if k < len(lc_range) else k
                
                self.results_text.insert(tk.END, f"Dport/Dt = {best_dport:.3f}\n")
                self.results_text.insert(tk.END, f"Dinj/Dt  = {best_dinj:.4f}\n")
                self.results_text.insert(tk.END, f"Lc/Dt    = {best_lc:.3f}\n\n")
                
                self.results_text.insert(tk.END, f"Ivac = {ivac[i,j,k]:.2f} s\n")
                self.results_text.insert(tk.END, f"Is   = {is_arr[i,j,k]:.2f} s\n")
                self.results_text.insert(tk.END, f"MR   = {mr_arr[i,j,k]:.2f}\n")
                self.results_text.insert(tk.END, f"pc   = {pc_arr[i,j,k]/1e5:.2f} bar\n")
                self.results_text.insert(tk.END, f"Gox  = {gox_arr[i,j,k]:.2f} kg/(s·m²)\n")
                
                # Additional performance data if available
                cs_arr = self.results.get('cs_array', np.zeros_like(ivac))
                tc_arr = self.results.get('Tc_array', np.zeros_like(ivac))
                cf_arr = self.results.get('CF_array', np.zeros_like(ivac))
                
                if cs_arr.size > 0 and cs_arr[i,j,k] > 0:
                    self.results_text.insert(tk.END, f"c*   = {cs_arr[i,j,k]:.1f} m/s\n")
                if tc_arr.size > 0 and tc_arr[i,j,k] > 0:
                    self.results_text.insert(tk.END, f"Tc   = {tc_arr[i,j,k]:.0f} K\n")
                if cf_arr.size > 0 and cf_arr[i,j,k] > 0:
                    self.results_text.insert(tk.END, f"CF   = {cf_arr[i,j,k]:.3f}\n")
                
                # Store optimal indices for plotting
                self.optimal_indices = (i, j, k)
                
                self.results_text.insert(tk.END, "\n")
                self.results_text.insert(tk.END, "Copy these values to Mission Page!\n")
                self.results_text.insert(tk.END, "\n")
            else:
                self.results_text.insert(tk.END, 
                    "⚠️ No valid solutions found within Gox limits!\n")
                self.results_text.insert(tk.END, 
                    f"Try adjusting Gox_min ({self.gox_min}) or Gox_max ({self.gox_max})\n\n")
                self.optimal_indices = None
            
            # ================================================================
            # GOX RANGE STATISTICS
            # ================================================================
            self.results_text.insert(tk.END, "=" * 40 + "\n")
            self.results_text.insert(tk.END, "GOX STATISTICS (all solutions)\n")
            self.results_text.insert(tk.END, "=" * 40 + "\n\n")
            
            if gox_arr.size > 0:
                valid_gox = gox_arr[gox_arr > 0]
                if len(valid_gox) > 0:
                    gox_data_min = np.min(valid_gox)
                    gox_data_max = np.max(valid_gox)
                    gox_data_mean = np.mean(valid_gox)
                    self.results_text.insert(tk.END, f"Gox_min (data)  = {gox_data_min:.2f} kg/(s·m²)\n")
                    self.results_text.insert(tk.END, f"Gox_max (data)  = {gox_data_max:.2f} kg/(s·m²)\n")
                    self.results_text.insert(tk.END, f"Gox_mean (data) = {gox_data_mean:.2f} kg/(s·m²)\n")
                    self.results_text.insert(tk.END, "\n")
                else:
                    self.results_text.insert(tk.END, "No valid Gox data.\n\n")
            else:
                self.results_text.insert(tk.END, "Gox_array not available.\n\n")
        else:
            self.results_text.insert(tk.END, "No valid Ivac data found.\n\n")
        
        # ================================================================
        # ARRAY STATISTICS
        # ================================================================
        self.results_text.insert(tk.END, "=" * 40 + "\n")
        self.results_text.insert(tk.END, "ARRAY STATISTICS\n")
        self.results_text.insert(tk.END, "=" * 40 + "\n\n")
        
        for key, value in self.results.items():
            if isinstance(value, np.ndarray):
                # Filter out zeros/invalid values for statistics
                valid_data = value[value != 0]
                if len(valid_data) == 0:
                    valid_data = value
                
                self.results_text.insert(tk.END, f"{key}:\n")
                self.results_text.insert(tk.END, f"  Shape: {value.shape}\n")
                self.results_text.insert(tk.END, f"  Min:   {np.min(valid_data):.4e}\n")
                self.results_text.insert(tk.END, f"  Max:   {np.max(valid_data):.4e}\n")
                self.results_text.insert(tk.END, f"  Mean:  {np.mean(valid_data):.4e}\n")
                self.results_text.insert(tk.END, f"  Std:   {np.std(valid_data):.4e}\n")
                self.results_text.insert(tk.END, "\n")
            else:
                self.results_text.insert(tk.END, f"{key}: {value}\n\n")
        
        # Disable editing
        self.results_text.config(state=tk.DISABLED)
    
    def _update_plot_tabs(self):
        """Update all plot tabs with new data"""
        # Get tab frames from notebook
        for i, tab_name in enumerate(self.TAB_DEFINITIONS.keys()):
            tab_frame = self.notebook.nametowidget(self.notebook.tabs()[i])
            self.create_tab_content(tab_frame, tab_name)
    
    def save_results(self):
        """Save results to CSV"""
        if self.results is None:
            messagebox.showwarning("No Results", "No results to save.")
            return
        
        if self.controller is None:
            messagebox.showerror("Error", "Controller not available.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Results"
        )
        
        if filepath:
            success, message = self.controller.save_results(filepath)
            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
    
    def export_plots(self):
        """Export current plots to image files"""
        if not self.tab_figures:
            messagebox.showwarning("No Plots", "No plots to export.")
            return
        
        # Ask for directory
        directory = filedialog.askdirectory(title="Select Export Directory")
        
        if directory:
            try:
                for tab_name, fig_data in self.tab_figures.items():
                    fig = fig_data['figure']
                    filename = f"{directory}/{tab_name.replace(' ', '_').replace('&', 'and')}_plots.png"
                    fig.savefig(filename, dpi=150, bbox_inches='tight', 
                               facecolor='white', edgecolor='none')
                
                messagebox.showinfo("Success", f"Plots exported to {directory}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export plots: {str(e)}")
    
    def export_to_excel(self):
        """Export all results to Excel with one sheet per Lc/Dt value"""
        if self.results is None:
            messagebox.showwarning("No Results", "No results to export.")
            return
        
        if self.ranges is None:
            messagebox.showerror("Error", "Parameter ranges not available.")
            return
        
        try:
            import pandas as pd
            from datetime import datetime
        except ImportError:
            messagebox.showerror("Error", 
                "pandas library required for Excel export.\n"
                "Install with: pip install pandas openpyxl")
            return
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        default_filename = f"optimization_results_{timestamp}.xlsx"
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Export All Results to Excel",
            initialfile=default_filename
        )
        
        if not filepath:
            return
        
        try:
            # Get ranges
            dport_range = self.ranges.get('Dport_Dt_range', np.array([0]))
            dinj_range = self.ranges.get('Dinj_Dt_range', np.array([0]))
            lc_range = self.ranges.get('Lc_Dt_range', np.array([0]))
            
            # Get arrays
            ivac = self.results.get('Ivac_array', np.zeros((1,1,1)))
            is_arr = self.results.get('Is_array', np.zeros_like(ivac))
            mr_arr = self.results.get('MR_array', np.zeros_like(ivac))
            pc_arr = self.results.get('pc_array', np.zeros_like(ivac))
            gox_arr = self.results.get('Gox_array', np.zeros_like(ivac))
            tc_arr = self.results.get('Tc_array', np.zeros_like(ivac))
            cs_arr = self.results.get('cs_array', np.zeros_like(ivac))
            cf_arr = self.results.get('CF_array', np.zeros_like(ivac))
            cf_vac_arr = self.results.get('CF_vac_array', np.zeros_like(ivac))
            
            # Create Excel writer
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                
                # ============================================
                # SUMMARY SHEET - TOP 10 (filtered by Gox)
                # ============================================
                summary_data = []
                
                flat_ivac = ivac.flatten()
                flat_gox = gox_arr.flatten()
                
                valid_mask = (flat_ivac > 0) & np.isfinite(flat_ivac)
                gox_mask = (flat_gox >= self.gox_min) & (flat_gox <= self.gox_max)
                combined_mask = valid_mask & gox_mask
                valid_indices = np.where(combined_mask)[0]
                
                if len(valid_indices) > 0:
                    sorted_indices = valid_indices[np.argsort(flat_ivac[valid_indices])[::-1]]
                    top_n = min(10, len(sorted_indices))
                    
                    for rank, flat_idx in enumerate(sorted_indices[:top_n], 1):
                        idx = np.unravel_index(flat_idx, ivac.shape)
                        i, j, k = idx
                        
                        summary_data.append({
                            'Rank': rank,
                            'Dport/Dt': dport_range[i] if i < len(dport_range) else i,
                            'Dinj/Dt': dinj_range[j] if j < len(dinj_range) else j,
                            'Lc/Dt': lc_range[k] if k < len(lc_range) else k,
                            'Ivac [s]': ivac[i, j, k],
                            'Is [s]': is_arr[i, j, k],
                            'MR (O/F)': mr_arr[i, j, k],
                            'pc [bar]': pc_arr[i, j, k] / 1e5,
                            'Gox [kg/(s·m²)]': gox_arr[i, j, k],
                            'Tc [K]': tc_arr[i, j, k],
                            'c* [m/s]': cs_arr[i, j, k],
                            'CF': cf_arr[i, j, k],
                            'Gox_valid': True
                        })
                
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Summary_TOP10', index=False)
                
                # Add info row
                info_df = pd.DataFrame({
                    'Info': [
                        f'Gox filter: [{self.gox_min}, {self.gox_max}] kg/(s·m²)',
                        f'Total solutions: {ivac.size}',
                        f'Valid solutions (in Gox range): {len(valid_indices)}',
                        f'Export timestamp: {timestamp}'
                    ]
                })
                # Write info starting from row after summary
                info_df.to_excel(writer, sheet_name='Summary_TOP10', 
                                startrow=len(summary_data) + 3, index=False)
                
                # ============================================
                # ONE SHEET PER Lc/Dt VALUE
                # ============================================
                for k, lc_val in enumerate(lc_range):
                    sheet_data = []
                    
                    for i, dport_val in enumerate(dport_range):
                        for j, dinj_val in enumerate(dinj_range):
                            # Get values at this point
                            ivac_val = ivac[i, j, k]
                            is_val = is_arr[i, j, k]
                            mr_val = mr_arr[i, j, k]
                            pc_val = pc_arr[i, j, k] / 1e5  # Pa to bar
                            gox_val = gox_arr[i, j, k]
                            tc_val = tc_arr[i, j, k]
                            cs_val = cs_arr[i, j, k]
                            cf_val = cf_arr[i, j, k]
                            
                            # Check if Gox is valid
                            gox_valid = (gox_val >= self.gox_min) and (gox_val <= self.gox_max)
                            
                            sheet_data.append({
                                'Dport/Dt': dport_val,
                                'Dinj/Dt': dinj_val,
                                'Ivac [s]': ivac_val,
                                'Is [s]': is_val,
                                'MR (O/F)': mr_val,
                                'pc [bar]': pc_val,
                                'Gox [kg/(s·m²)]': gox_val,
                                'Tc [K]': tc_val,
                                'c* [m/s]': cs_val,
                                'CF': cf_val,
                                'Gox_valid': gox_valid
                            })
                    
                    # Create DataFrame and write to sheet
                    df_sheet = pd.DataFrame(sheet_data)
                    
                    # Sheet name (Excel limits to 31 chars)
                    sheet_name = f"Lc_Dt={lc_val:.2f}"
                    if len(sheet_name) > 31:
                        sheet_name = sheet_name[:31]
                    
                    df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Success message
            n_sheets = len(lc_range) + 1  # +1 for summary
            messagebox.showinfo("Export Complete", 
                f"Results exported to:\n{filepath}\n\n"
                f"Created {n_sheets} sheets:\n"
                f"• 1 Summary (TOP 10)\n"
                f"• {len(lc_range)} sheets (one per Lc/Dt value)\n\n"
                f"Total rows: {ivac.size}")
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            messagebox.showerror("Export Error", 
                f"Failed to export to Excel:\n{str(e)}\n\n{tb}")


# Helper function to create the optimization output page
def create_optimization_output_page(parent, controller=None):
    """
    Factory function to create optimization output page
    
    Args:
        parent: Parent frame
        controller: ApplicationController instance (optional)
        
    Returns:
        OptimizationOutputPage instance
    """
    return OptimizationOutputPage(parent, controller)
