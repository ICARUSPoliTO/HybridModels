# config.py

# Colori tema
COLORS = {
    'bg_dark': '#2b2b2b',
    'bg_medium': '#3c3c3c',
    'bg_light': '#8c8c8c',
    'bg_active': '#5c5c5c',
    'text_color': 'white',
    'button_inactive': '#a0a0a0',
    'button_active': '#6c6c6c',
    'validation_ok': '#00aa00',
    'validation_error': 'red',
    'button_valid': '#006400',
    'button_invalid': '#8b0000'
}

# Font
FONTS = {
    'title': ('Arial', 28, 'bold'),
    'section': ('Arial', 16),
    'normal': ('Arial', 11),
    'small': ('Arial', 10),
    'header': ('Arial', 24, 'bold'),
    'subtitle': ('Arial', 12, 'bold')
}

# Liste predefinite
EASY_CEA_OX_LIST = [
    "Air", "CL2", "CL2(L)", "F2", "F2(L)", "H2O2(L)",
    "N2H4(L)", "N2O", "NH4NO3(I)", "O2", "O2(L)",
    "Select other options", "Custom with exploded formula"
]

EASY_CEA_FUEL_LIST = [
    "CH4", "CH4(L)", "H2", "H2(L)", "RP-1", "paraffin",
    "Select other options", "Custom with exploded formula"
]

FALLBACK_COOLPROP_FLUIDS = [
    "NitrousOxide", "Oxygen", "Nitrogen", "Water",
    "CarbonDioxide", "Methane", "Hydrogen"
]

# Valori predefiniti per paraffin
PARAFFIN_DEFAULTS = {
    'temperature': 533.0,
    'enthalpy': -1860.6
}   