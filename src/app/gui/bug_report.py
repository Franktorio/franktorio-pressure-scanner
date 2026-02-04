# Franktorio Research Scanner
# Bug Report Window
# December 2025

from PyQt5.QtWidgets import QMainWindow, QTextEdit, QPushButton, QLabel

from .colors import COLORS, convert_style_to_qss


class BugReportWindow(QMainWindow):
    """A window to submit bug reports."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Submit Bug Report")
        self.setGeometry(200, 200, 600, 400)
        
        self.dpi_scale = parent.dpi_scale if parent and hasattr(parent, 'dpi_scale') else 1.0
        
        style = {
            "styles": {
                "QMainWindow": {
                    "background-color": COLORS['background']
                },
                "QTextEdit": {
                    "background-color": COLORS['surface'],
                    "color": COLORS['text'],
                    "padding": "10px",
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px",
                    "font-family": "Consolas, monospace",
                    "font-size": f"{10 * self.dpi_scale}pt"
                },
                "QLabel": {
                    "color": COLORS['text'],
                    "background-color": COLORS['surface'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "5px"
                },
                "QPushButton": {
                    "background-color": COLORS['button_bg'],
                    "color": COLORS['button_text_active'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "5px",
                    "padding": "5px"
                },
                "QPushButton:hover": {
                    "background-color": COLORS['button_hover']
                }
                
            }
        }

        # Apply styles
        self.setStyleSheet(convert_style_to_qss(style))

        self.title_label = QLabel("FEATURE NOT IMPLEMENTED; DOES NOTHING", self)
        self.title_label.setGeometry(20, 20, 560, 30)

        self.bug_report_text_area = QTextEdit(self)
        self.bug_report_text_area.setGeometry(20, 60, 560, 250)

        self.submit_button = QPushButton("Submit Report", self)
        self.submit_button.setGeometry(240, 330, 120, 40)
    
    def update_scale(self, new_scale):
        """Update the dpi_scale and refresh styles"""
        self.dpi_scale = new_scale
        
        style = {
            "styles": {
                "QMainWindow": {
                    "background-color": COLORS['background']
                },
                "QTextEdit": {
                    "background-color": COLORS['surface'],
                    "color": COLORS['text'],
                    "padding": "10px",
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px",
                    "font-family": "Consolas, monospace",
                    "font-size": f"{10 * self.dpi_scale}pt"
                },
                "QLabel": {
                    "color": COLORS['text'],
                    "background-color": COLORS['surface'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "5px"
                },
                "QPushButton": {
                    "background-color": COLORS['button_bg'],
                    "color": COLORS['button_text_active'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "5px",
                    "padding": "5px"
                },
                "QPushButton:hover": {
                    "background-color": COLORS['button_hover']
                }
            }
        }
        self.setStyleSheet(convert_style_to_qss(style))
    
    def submit_report(self):
        """Submit the bug report (functionality to be implemented)."""
        report_text = self.bug_report_text_area.toPlainText()

        # Get both the consoles' text for context
        main_console_text = ""
        debug_console_text = ""

        if hasattr(self.parent(), 'console_text_area'):
            main_console_text = self.parent().console_text_area.toPlainText()
        
        if hasattr(self.parent(), 'debug_console_window'):
            debug_console_text = self.parent().debug_console_window.debug_text_area.toPlainText()
