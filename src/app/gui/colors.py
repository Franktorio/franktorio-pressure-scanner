# Franktorio Research Scanner
# GUI Colors and Styling Utilities
# December 2025

# Color Palette
COLORS = {
    'background': "#1f1f1f",          # Main background
    'surface': "#252525",             # Surface/panel color
    'surface_light': "#333333",       # Lighter surface variant
    'titlebar': '#1e1e1e',            # Title bar background
    'border': "#8F8F8F",              # Border color
    'accent': '#5a5a5a',              # Accent color
    'text': '#e0e0e0',                # Primary text
    'text_secondary': '#b0b0b0',      # Secondary text
    'button_bg': '#3a3a3a',           # Button background
    'button_hover': '#505050',        # Button hover background
    'button_inactive': '#2a2a2a',     # Button inactive background
    'button_text_active': '#ffffff',  # Button active text
    'button_text_inactive': '#7a7a7a',# Button inactive text
    'toggled_on': "#934caf",          # Toggle on color
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
