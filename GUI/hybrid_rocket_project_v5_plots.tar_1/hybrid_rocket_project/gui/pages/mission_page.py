"""
Mission Page - Mission parameters and flight profile

Contains fields for mission-specific parameters like burn time,
altitude, payload mass, etc.
"""

import tkinter as tk
from tkinter import ttk
from config.constants import COLORS, FONTS
from gui.components.input_field import create_input_field


class MissionPage:
    """Mission page for mission parameters"""
    
    def __init__(self, parent, inputs_dict: dict):
        """
        Initialize mission page
        
        Args:
            parent: Parent frame to contain this page
            inputs_dict: Shared dictionary for input fields
        """
        self.parent = parent
        self.inputs = inputs_dict
        
        self.create_page()
    
    def create_page(self):
        """Create the mission page content"""
        # Title
        title = tk.Label(
            self.parent, 
            text="Mission Parameters", 
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
        """Create placeholder content for the mission page"""
        section = tk.LabelFrame(
            parent, 
            text="Mission Parameters (Coming Soon)", 
            font=FONTS['section'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        section.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        info_text = tk.Label(
            section,
            text="This page will contain:\n\n"
                 "• Burn time\n"
                 "• Target altitude\n"
                 "• Payload mass\n"
                 "• Flight profile\n"
                 "• Launch conditions\n"
                 "• And more...\n\n"
                 "Ready to be customized!",
            font=FONTS['label'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_color'],
            justify=tk.LEFT
        )
        info_text.pack(pady=40, padx=40)


# Helper function to create the mission page
def create_mission_page(parent, inputs_dict):
    """
    Factory function to create mission page
    
    Args:
        parent: Parent frame
        inputs_dict: Shared inputs dictionary
        
    Returns:
        MissionPage instance
    """
    return MissionPage(parent, inputs_dict)
