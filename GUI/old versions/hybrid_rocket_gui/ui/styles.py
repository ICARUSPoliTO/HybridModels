# ui/styles.py

from tkinter import ttk
from config import COLORS


class StyleManager:
    def __init__(self, root):
        self.style = ttk.Style()
        self.colors = COLORS
        self._configure_styles()
    
    def _configure_styles(self):
        self.style.configure("Rounded.TButton",
                           font=('Arial', 11),
                           padding=6,
                           relief="flat",
                           borderwidth=0,
                           background=self.colors['button_inactive'],
                           foreground='black')
        
        self.style.map("Rounded.TButton",
                      background=[('active', self.colors['button_active']), 
                                ('!active', self.colors['button_inactive'])],
                      foreground=[('active', 'white'), ('!active', 'black')])
    
    def set_button_valid(self):
        self.style.configure("Rounded.TButton", 
                           background=self.colors['button_valid'])
    
    def set_button_invalid(self):
        self.style.configure("Rounded.TButton", 
                           background=self.colors['button_invalid'])