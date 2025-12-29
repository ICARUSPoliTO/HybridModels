"""
Mission Output Page - Mission simulation results

Displays:
- Summary statistics table
- Key performance values
- Export to CSV functionality
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import csv
from config.constants import COLORS, FONTS


class MissionOutputPage:
    """Mission output page for simulation results"""
    
    def __init__(self, parent, controller=None):
        """
        Initialize mission output page
        
        Args:
            parent: Parent frame to contain this page
            controller: Application controller for accessing results
        """
        self.parent = parent
        self.controller = controller
        self.results = None
        self.time_data = None
        self.log_data = None
        
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
                 "Results will be displayed here.",
            font=FONTS['label'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            justify=tk.CENTER
        )
        info_text.pack(pady=40, padx=40)
    
    def display_results(self, time_data, performances, log_data):
        """
        Display mission simulation results
        
        Args:
            time_data: List of time points [s]
            performances: Dictionary of performance lists (normalized)
            log_data: Termination log string
        """
        self.time_data = time_data
        self.results = performances
        self.log_data = log_data
        
        # Clear existing content
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Create scrollable frame
        canvas = tk.Canvas(self.main_frame, bg=COLORS['bg_dark'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['bg_dark'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind('<Enter>', lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all("<MouseWheel>"))
        
        # Create sections
        self.create_summary_section(scrollable_frame)
        self.create_performance_section(scrollable_frame)
        self.create_termination_section(scrollable_frame)
        self.create_export_section(scrollable_frame)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_summary_section(self, parent):
        """Create summary statistics section"""
        section = tk.LabelFrame(
            parent, 
            text="Mission Summary", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, pady=10, padx=10)
        
        if not self.results or not self.time_data:
            return
        
        # Calculate summary statistics
        total_time = self.time_data[-1] if self.time_data else 0
        
        # Get key values (handle None values)
        def safe_max(lst):
            filtered = [x for x in lst if x is not None and np.isfinite(x)]
            return max(filtered) if filtered else 0
        
        def safe_mean(lst):
            filtered = [x for x in lst if x is not None and np.isfinite(x)]
            return np.mean(filtered) if filtered else 0
        
        def safe_min(lst):
            filtered = [x for x in lst if x is not None and np.isfinite(x)]
            return min(filtered) if filtered else 0
        
        thrust_list = self.results.get('Thrust', [])
        pc_list = self.results.get('pc', [])
        is_list = self.results.get('Is', [])
        mL_list = self.results.get('mL', [])
        m_fuel_list = self.results.get('m_fuel', [])
        
        # Summary data
        summary_data = [
            ("Total Simulation Time", f"{total_time:.3f} s"),
            ("Number of Time Steps", f"{len(self.time_data)}"),
            ("", ""),  # Separator
            ("Max Thrust", f"{safe_max(thrust_list):.2f} N"),
            ("Mean Thrust", f"{safe_mean(thrust_list):.2f} N"),
            ("", ""),
            ("Max Chamber Pressure", f"{safe_max(pc_list)/1e5:.2f} bar"),
            ("Mean Chamber Pressure", f"{safe_mean(pc_list)/1e5:.2f} bar"),
            ("", ""),
            ("Max Specific Impulse", f"{safe_max(is_list):.1f} s"),
            ("Mean Specific Impulse", f"{safe_mean(is_list):.1f} s"),
            ("", ""),
            ("Initial Oxidizer Mass", f"{safe_max(mL_list):.3f} kg"),
            ("Final Oxidizer Mass", f"{safe_min(mL_list):.3f} kg"),
            ("Oxidizer Consumed", f"{safe_max(mL_list) - safe_min(mL_list):.3f} kg"),
            ("", ""),
            ("Initial Fuel Mass", f"{safe_max(m_fuel_list):.3f} kg"),
            ("Final Fuel Mass", f"{safe_min(m_fuel_list):.3f} kg"),
            ("Fuel Consumed", f"{safe_max(m_fuel_list) - safe_min(m_fuel_list):.3f} kg"),
        ]
        
        for i, (label, value) in enumerate(summary_data):
            if label == "":
                continue
            tk.Label(
                section, text=label + ":", font=FONTS['label'],
                bg=COLORS['bg_medium'], fg=COLORS['text_color'], anchor='e'
            ).grid(row=i, column=0, sticky='e', padx=(10, 5), pady=2)
            tk.Label(
                section, text=value, font=FONTS['label'],
                bg=COLORS['bg_medium'], fg=COLORS['text_color'], anchor='w'
            ).grid(row=i, column=1, sticky='w', padx=(5, 10), pady=2)
    
    def create_performance_section(self, parent):
        """Create detailed performance data section"""
        section = tk.LabelFrame(
            parent, 
            text="Performance Data (Sample)", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, pady=10, padx=10)
        
        if not self.results:
            return
        
        # Create treeview for data table
        columns = ('Time [s]', 'Thrust [N]', 'pc [bar]', 'Tc [K]', 'Is [s]', 'MR')
        tree = ttk.Treeview(section, columns=columns, show='headings', height=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor='center')
        
        # Add sample data (every 10th point to avoid too many rows)
        time_list = self.time_data if self.time_data else []
        thrust_list = self.results.get('Thrust', [])
        pc_list = self.results.get('pc', [])
        tc_list = self.results.get('Tc', [])
        is_list = self.results.get('Is', [])
        mr_list = self.results.get('MR', [])
        
        step = max(1, len(time_list) // 20)  # Show ~20 rows
        for i in range(0, len(time_list), step):
            def safe_get(lst, idx, default=0):
                try:
                    val = lst[idx] if idx < len(lst) else default
                    return val if val is not None and np.isfinite(val) else default
                except:
                    return default
            
            row = (
                f"{safe_get(time_list, i):.4f}",
                f"{safe_get(thrust_list, i):.2f}",
                f"{safe_get(pc_list, i)/1e5:.3f}",
                f"{safe_get(tc_list, i):.1f}",
                f"{safe_get(is_list, i):.1f}",
                f"{safe_get(mr_list, i):.2f}"
            )
            tree.insert('', tk.END, values=row)
        
        # Scrollbar for treeview
        tree_scroll = ttk.Scrollbar(section, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
    
    def create_termination_section(self, parent):
        """Create termination log section"""
        section = tk.LabelFrame(
            parent, 
            text="Simulation Log", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.X, pady=10, padx=10)
        
        log_text = self.log_data if self.log_data else "No log available."
        
        tk.Label(
            section, text=log_text, font=FONTS['label'],
            bg=COLORS['bg_medium'], fg=COLORS['text_color'],
            justify=tk.LEFT, anchor='w'
        ).pack(padx=10, pady=10, fill=tk.X)
    
    def create_export_section(self, parent):
        """Create export buttons section"""
        section = tk.Frame(parent, bg=COLORS['bg_dark'])
        section.pack(fill=tk.X, pady=20, padx=10)
        
        tk.Button(
            section,
            text="Export to CSV",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.export_to_csv,
            cursor='hand2',
            padx=20, pady=10
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            section,
            text="Export Summary",
            font=FONTS['button'],
            bg=COLORS['button_inactive'],
            fg='black',
            command=self.export_summary,
            cursor='hand2',
            padx=20, pady=10
        ).pack(side=tk.LEFT, padx=10)
    
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
                
                # Get all keys from results
                keys = ['time'] + list(self.results.keys())
                writer.writerow(keys)
                
                # Write data rows
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
    
    def export_summary(self):
        """Export summary statistics to text file"""
        if not self.results or not self.time_data:
            messagebox.showerror("Error", "No results to export.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Mission Summary"
        )
        
        if not filepath:
            return
        
        try:
            def safe_max(lst):
                filtered = [x for x in lst if x is not None and np.isfinite(x)]
                return max(filtered) if filtered else 0
            
            def safe_mean(lst):
                filtered = [x for x in lst if x is not None and np.isfinite(x)]
                return np.mean(filtered) if filtered else 0
            
            def safe_min(lst):
                filtered = [x for x in lst if x is not None and np.isfinite(x)]
                return min(filtered) if filtered else 0
            
            with open(filepath, 'w') as f:
                f.write("=" * 50 + "\n")
                f.write("MISSION SIMULATION SUMMARY\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Total Simulation Time: {self.time_data[-1]:.3f} s\n")
                f.write(f"Number of Time Steps: {len(self.time_data)}\n\n")
                
                thrust_list = self.results.get('Thrust', [])
                f.write(f"Max Thrust: {safe_max(thrust_list):.2f} N\n")
                f.write(f"Mean Thrust: {safe_mean(thrust_list):.2f} N\n\n")
                
                pc_list = self.results.get('pc', [])
                f.write(f"Max Chamber Pressure: {safe_max(pc_list)/1e5:.2f} bar\n")
                f.write(f"Mean Chamber Pressure: {safe_mean(pc_list)/1e5:.2f} bar\n\n")
                
                is_list = self.results.get('Is', [])
                f.write(f"Max Specific Impulse: {safe_max(is_list):.1f} s\n")
                f.write(f"Mean Specific Impulse: {safe_mean(is_list):.1f} s\n\n")
                
                mL_list = self.results.get('mL', [])
                f.write(f"Oxidizer Consumed: {safe_max(mL_list) - safe_min(mL_list):.3f} kg\n")
                
                m_fuel_list = self.results.get('m_fuel', [])
                f.write(f"Fuel Consumed: {safe_max(m_fuel_list) - safe_min(m_fuel_list):.3f} kg\n\n")
                
                f.write("-" * 50 + "\n")
                f.write("TERMINATION LOG:\n")
                f.write("-" * 50 + "\n")
                f.write(self.log_data if self.log_data else "No log available.\n")
            
            messagebox.showinfo("Success", f"Summary exported to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{str(e)}")


# Helper function to create the mission output page
def create_mission_output_page(parent, controller=None):
    """
    Factory function to create mission output page
    
    Args:
        parent: Parent frame
        controller: Application controller
        
    Returns:
        MissionOutputPage instance
    """
    return MissionOutputPage(parent, controller)
