# sections/line_section.py

import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS


class LineSection:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.app = main_app
        self.colors = COLORS
        self.fonts = FONTS
    
    def create(self):
        section = tk.Frame(self.parent, bg=self.colors['bg_light'], relief=tk.RIDGE, bd=2)
        section.pack(fill=tk.X, pady=10, ipady=15)
        
        header_frame = tk.Frame(section, bg=self.colors['bg_light'])
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
        
        section_title = tk.Label(header_frame, text="Line", font=self.fonts['section'],
                                 bg=self.colors['bg_light'], fg='black')
        section_title.pack(side=tk.LEFT)
        
        import_btn = ttk.Button(header_frame, text="Import Line",
                                style="Rounded.TButton",
                                command=self.import_line_placeholder)
        import_btn.pack(side=tk.LEFT, padx=(20, 0))
    
    def import_line_placeholder(self):
        messagebox.showinfo("Info", "Import line function in development")
