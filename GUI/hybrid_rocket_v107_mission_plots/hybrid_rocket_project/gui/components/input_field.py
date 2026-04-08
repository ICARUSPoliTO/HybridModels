"""
Reusable Input Field Component

Provides standardized input fields for consistent UI across pages.
"""

import tkinter as tk
from config.constants import COLORS, FONTS


class InputField:
    """
    Reusable input field component
    
    Creates a labeled entry field with consistent styling.
    """
    
    def __init__(self, parent, label_text: str, default_value: str = "", 
                 width: int = 30, row: int = 0):
        """
        Create an input field
        
        Args:
            parent: Parent frame
            label_text: Label text to display
            default_value: Default value for the field
            width: Width of entry widget
            row: Grid row for placement
        """
        self.frame = tk.Frame(parent, bg=COLORS['bg_medium'])
        self.frame.grid(row=row, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        parent.grid_columnconfigure(0, weight=1)
        
        # Label
        self.label = tk.Label(
            self.frame, 
            text=label_text, 
            font=FONTS['label'],
            bg=COLORS['bg_medium'], 
            fg=COLORS['text_color']
        )
        self.label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Entry
        self.entry = tk.Entry(self.frame, font=FONTS['label'], width=width)
        self.entry.pack(side=tk.RIGHT)
        
        if default_value:
            self.entry.insert(0, default_value)
    
    def get(self) -> str:
        """Get the current value"""
        return self.entry.get()
    
    def set(self, value: str):
        """Set the value"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
    
    def clear(self):
        """Clear the field"""
        self.entry.delete(0, tk.END)
    
    def get_entry_widget(self):
        """Get the underlying entry widget for advanced usage"""
        return self.entry


def create_input_field(parent, key: str, label: str, inputs_dict: dict,
                      default: str = "", row: int = 0, col: int = 0) -> tk.Entry:
    """
    Helper function to create an input field and store it in inputs dictionary
    
    Args:
        parent: Parent frame
        key: Key to store entry in inputs_dict
        label: Label text
        inputs_dict: Dictionary to store the entry widget
        default: Default value
        row: Grid row
        col: Grid column (0 or 2 for left/right positioning)
        
    Returns:
        The entry widget
    """
    # Create label
    label_widget = tk.Label(
        parent,
        text=label,
        font=FONTS['label'],
        bg=COLORS['bg_medium'],
        fg=COLORS['text_color'],
        anchor='e'
    )
    label_widget.grid(row=row, column=col, sticky='e', padx=(10, 5), pady=5)
    
    # Create entry
    entry = tk.Entry(parent, font=FONTS['label'], width=15)
    entry.grid(row=row, column=col+1, sticky='w', padx=(5, 10), pady=5)
    
    if default:
        entry.insert(0, default)
    
    inputs_dict[key] = entry
    return entry
