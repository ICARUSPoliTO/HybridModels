"""
Mission Output Page - Mission simulation results

Displays mission simulation results, trajectory, and performance data.
"""

import tkinter as tk
from tkinter import ttk
from config.constants import COLORS, FONTS


class MissionOutputPage:
    """Mission output page for simulation results"""
    
    def __init__(self, parent):
        """
        Initialize mission output page
        
        Args:
            parent: Parent frame to contain this page
        """
        self.parent = parent
        
        self.create_page()
    
    def create_page(self):
        """Create the mission output page content"""
        # Title
        title = tk.Label(
            self.parent, 
            text="Mission Output", 
            font=FONTS['title'],
            bg=COLORS['bg_dark'], 
            fg=COLORS['text_color']
        )
        title.pack(pady=20)
        
        # Scrollable frame
        canvas = tk.Canvas(self.parent, bg=COLORS['bg_dark'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        main_frame = tk.Frame(canvas, bg=COLORS['bg_dark'])
        
        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_mousewheel)
        canvas.bind('<Leave>', _unbind_mousewheel)
        
        # Placeholder content
        self.create_placeholder_content(main_frame)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_placeholder_content(self, parent):
        """Create placeholder content for the mission output page"""
        section = tk.LabelFrame(
            parent, 
            text="Mission Simulation Results (Coming Soon)", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        info_text = tk.Label(
            section,
            text="This page will display:\n\n"
                 "• Flight trajectory\n"
                 "• Altitude vs time plot\n"
                 "• Velocity profile\n"
                 "• Thrust curve\n"
                 "• Apogee data\n"
                 "• Recovery analysis\n"
                 "• Mission statistics\n"
                 "• And more...\n\n"
                 "Ready to be customized!",
            font=FONTS['label'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            justify=tk.LEFT
        )
        info_text.pack(pady=40, padx=40)


# Helper function to create the mission output page
def create_mission_output_page(parent):
    """
    Factory function to create mission output page
    
    Args:
        parent: Parent frame
        
    Returns:
        MissionOutputPage instance
    """
    return MissionOutputPage(parent)
