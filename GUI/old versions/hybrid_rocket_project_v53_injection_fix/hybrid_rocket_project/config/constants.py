"""
Application Constants and Configuration

Colors, fonts, and other application-wide constants.
"""

# Color scheme
COLORS = {
    'bg_dark': '#2b2b2b',
    'bg_medium': '#3c3c3c',
    'bg_light': '#8c8c8c',
    'bg_active': '#5c5c5c',
    'text_color': 'white',
    'text_muted': '#a0a0a0',
    'button_inactive': '#a0a0a0',
    'button_active': '#6c6c6c',
}

# Fonts
FONTS = {
    'title': ('Arial', 20, 'bold'),
    'header': ('Arial', 18, 'bold'),
    'section': ('Arial', 14, 'bold'),
    'label': ('Arial', 11),
    'button': ('Arial', 12),
    'small': ('Arial', 10),
}

# Window settings
WINDOW_CONFIG = {
    'title': 'Hybrid Rocket Simulator',
    'geometry': '1400x900',
    'min_width': 1200,
    'min_height': 700,
}

# Styling
BUTTON_STYLE = {
    'font': FONTS['button'],
    'padding': 6,
    'relief': 'flat',
    'borderwidth': 0,
}

# Validation ranges (can be customized per field)
DEFAULT_VALIDATION = {
    'min_value': None,
    'max_value': None,
    'exclusive': False,
    'is_int': False,
}

# File extensions
FILE_TYPES = {
    'config': [("CSV files", "*.csv"), ("All files", "*.*")],
    'optimization': [("CSV files", "*.csv"), ("All files", "*.*")],
    'results': [("CSV files", "*.csv"), ("All files", "*.*")],
}
