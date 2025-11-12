# utils/chemistry.py

def explode_formula(formula):
    '''Convert chemical formula to expanded format'''
    formula = formula.replace(" ", "")
    exploded_formula = ""
    prec = "1"

    for i, char in enumerate(formula):
        if char.isupper() and char.isalpha():
            if prec.isdigit():
                exploded_formula = exploded_formula + " " + char
            else:
                exploded_formula = exploded_formula + " " + "1" + " " + char
            prec = char
        elif char.islower() and char.isalpha():
            if prec.isupper() and prec.isalpha():
                exploded_formula = exploded_formula + char
            prec = char
        elif char.isdigit():
            if prec.isalpha():
                exploded_formula = exploded_formula + " " + char
            elif prec.isdigit():
                exploded_formula = exploded_formula + char
            prec = char
        if i == (len(formula) - 1) and char.isalpha():
            exploded_formula = exploded_formula + " " + "1"

    exploded_formula = exploded_formula.strip()
    return exploded_formula
"""

# ---------------------------------------------------------------------------
# ui/styles.py - Gestione stili
# ---------------------------------------------------------------------------
"""
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