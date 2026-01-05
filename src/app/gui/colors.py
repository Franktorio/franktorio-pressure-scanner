# Franktorio Research Scanner
# GUI Colors and Styling Utilities
# December 2025

# Color Palette
COLORS = {
    'background': "#120f1a",          # Main background
    'surface': "#1a1426",             # Surface/panel color
    'surface_light': "#241c33",       # Lighter surface variant
    'titlebar': "#0e0b14",            # Title bar background
    'border': "#3a2f52",              # Border color
    'accent': "#6f4bb8",              # Accent color (purple)
    'text': "#e6e1f0",                # Primary text
    'text_secondary': "#b8aecf",      # Secondary text
    'button_bg': "#2a2040",           # Button background
    'button_hover': "#3a2b5c",        # Button hover background
    'button_inactive': "#1a1426",     # Button inactive background
    'button_text_active': "#ffffff",  # Button active text
    'button_text_inactive': "#7f7399",# Button inactive text
}




def convert_style_to_qss(style_dict):
    """Convert JSON style dictionary to QSS string"""
    qss = ""
    for selector, properties in style_dict["styles"].items():
        qss += f"{selector} {{\n"
        for prop, value in properties.items():
            qss += f"    {prop}: {value};\n"
        qss += "}\n\n"
    return qss
