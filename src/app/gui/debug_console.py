# Franktorio Research Scanner
# Debug Console Window
# December 2025

import datetime

from PyQt5.QtWidgets import QMainWindow, QTextEdit, QPushButton
from PyQt5.QtCore import pyqtSignal

from config.vars import VERSION
from .colors import COLORS, convert_style_to_qss


class DebugConsoleWindow(QMainWindow):
    """A separate window for detailed debug console output."""
    debug_console_message = pyqtSignal(str)  # Signal to log messages to debug console
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Debug Console v{VERSION}")
        self.setGeometry(150, 150, 800, 600)
        
        self.dpi_scale = parent.dpi_scale if parent and hasattr(parent, 'dpi_scale') else 1.0
        
        
        # Apply main window background color
        main_style = {
            "styles": {
                "QMainWindow": {
                    "background-color": COLORS['background']
                }
            }
        }
        self.setStyleSheet(convert_style_to_qss(main_style))
        
        # Setup text area with styling to match main console
        self.debug_text_area = QTextEdit(self)
        self.debug_text_area.setReadOnly(True)
        
        # Apply console text area styling
        text_area_style = {
            "styles": {
                "QTextEdit": {
                    "background-color": COLORS['surface'],
                    "color": COLORS['text'],
                    "padding": "10px",
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px",
                    "font-family": "Consolas, monospace",
                    "font-size": f"{10 * self.dpi_scale}pt"
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
                },
                "QPushButton:pressed": {
                    "background-color": COLORS['button_inactive']
                }
            }
        }
        self.debug_text_area.setStyleSheet(convert_style_to_qss(text_area_style))
        self.setCentralWidget(self.debug_text_area)

        # Add bug report button
        self.bug_report_debug_button = QPushButton("Submit Bug Report", self.debug_text_area)
        self.bug_report_debug_button.setGeometry(10, 10, 140, 30)

        # Move button to bottom-right corner
        self.bug_report_debug_button.move(self.width() - self.bug_report_debug_button.width() - 10,
                                    self.height() - self.bug_report_debug_button.height() - 10)

        # Connect signal to slot
        self.debug_console_message.connect(self.log_debug_message)
        self.bug_report_debug_button.clicked.connect(self.open_bug_report_window)
        
        # Add initial header
    
    def update_scale(self, new_scale):
        """Update the dpi_scale and refresh styles"""
        self.dpi_scale = new_scale
        
        text_area_style = {
            "styles": {
                "QTextEdit": {
                    "background-color": COLORS['surface'],
                    "color": COLORS['text'],
                    "padding": "10px",
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px",
                    "font-family": "Consolas, monospace",
                    "font-size": f"{10 * self.dpi_scale}pt"
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
                },
                "QPushButton:pressed": {
                    "background-color": COLORS['button_inactive']
                }
            }
        }
        self.debug_text_area.setStyleSheet(convert_style_to_qss(text_area_style))
        self.debug_text_area.append("=" * 80)
        self.debug_text_area.append(f"Franktorio Research Scanner - Debug Console v{VERSION}")
        self.debug_text_area.append("=" * 80)
        self.debug_text_area.append("")

    def log_debug_message(self, message: str):
        """Log a debug message to the debug console."""
        MAX_CHARS = 50000
        now = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        formatted_message = f"{now} {message}"
        current_text = self.debug_text_area.toPlainText()
        self.debug_text_area.setText(current_text[-MAX_CHARS:] + formatted_message + "\n")
        self.debug_text_area.verticalScrollBar().setValue(self.debug_text_area.verticalScrollBar().maximum())

    def open_bug_report_window(self):
        """Open the bug report window."""
        # Get parent's bug report window
        if hasattr(self.parent(), 'bug_report_window'):
            self.parent().bug_report_window.show()
    
    def update_stats(self, stats: dict):
        """Update and display current debug statistics."""
        self.debug_text_area.append("\n" + "=" * 80)
        self.debug_text_area.append(f"Debug Statistics - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.debug_text_area.append("=" * 80)
        
        # Scanner stats
        self.debug_text_area.append("\n[Scanner Statistics]")
        self.debug_text_area.append(f"  Scanner Iterations:     {stats.get('scanner_iterations', 0)}")
        self.debug_text_area.append(f"  File Checks:            {stats.get('file_checks', 0)}")
        self.debug_text_area.append(f"  File Switches:          {stats.get('file_switches', 0)}")
        self.debug_text_area.append(f"  API Calls:              {stats.get('api_calls', 0)}")
        self.debug_text_area.append(f"  Session Requests:       {stats.get('session_requests', 0)}")
        self.debug_text_area.append(f"  Total Rooms Reported:   {stats.get('total_rooms_reported', 0)}")
        self.debug_text_area.append(f"  Errors Caught:          {stats.get('errors_caught', 0)}")
        
        # Stalker stats
        self.debug_text_area.append("\n[File Monitoring Statistics]")
        self.debug_text_area.append(f"  Total Reads:            {stats.get('stalker_reads', 0)}")
        self.debug_text_area.append(f"  Total Lines Read:       {stats.get('stalker_lines_read', 0)}")
        self.debug_text_area.append(f"  Empty Reads:            {stats.get('stalker_empty_reads', 0)}")
        
        # Parser stats
        self.debug_text_area.append("\n[Parser Statistics]")
        self.debug_text_area.append(f"  Total Lines Parsed:     {stats.get('total_lines_parsed', 0)}")
        self.debug_text_area.append(f"  Rooms Found:            {stats.get('rooms_found', 0)}")
        self.debug_text_area.append(f"  Locations Found:        {stats.get('locations_found', 0)}")
        self.debug_text_area.append(f"  Disconnects Detected:   {stats.get('disconnects_detected', 0)}")
        
        self.debug_text_area.append("\n" + "=" * 80 + "\n")
        self.debug_text_area.verticalScrollBar().setValue(self.debug_text_area.verticalScrollBar().maximum())
