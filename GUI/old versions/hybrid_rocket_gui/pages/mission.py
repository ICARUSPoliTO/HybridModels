import tkinter as tk
from config import COLORS, FONTS


class MissionPage:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.app = main_app
        self.colors = COLORS
        self.fonts = FONTS
    
    def show(self):
        label = tk.Label(self.parent, text="MISSION - Coming soon",
                         font=('Arial', 20), bg=self.colors['bg_dark'], 
                         fg=self.colors['text_color'])
        label.pack(expand=True)