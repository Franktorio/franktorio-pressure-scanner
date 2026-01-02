# Franktorio Research Scanner
# Main Window Builder
# December 2025

import sys
import json
import PyQt5
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy, QDialog, QInputDialog,
    QLineEdit, QComboBox, QCheckBox, QRadioButton, QSlider, QProgressBar,
    QSpinBox, QDoubleSpinBox, QGroupBox, QTabWidget, QListWidget, QTableWidget,
    QTableWidgetItem, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QCursor

from config.vars import MIN_WIDTH, MIN_HEIGHT, RESIZE_MARGIN
from .colors import COLORS, convert_style_to_qss
from .window_controls import WindowControlsMixin
from .widgets import WidgetSetupMixin


class MainWindow(WindowControlsMixin, WidgetSetupMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Franktorio Research Scanner")
        self.setGeometry(100, 100, MIN_WIDTH, MIN_HEIGHT)
        style = {
            "styles": {
                "QMainWindow": {
                    "background-color": COLORS['background']
                }
            }
        }
        qss = convert_style_to_qss(style)
        self.setStyleSheet(qss)

        # Remove window frame for custom styling
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.dpi_scale = self._get_dpi_scale()

        # Initialize window controls
        self.init_window_controls()

        # Setup UI components (defined in WidgetSetupMixin)
        self.setup_title_bar()
        self.setup_main_widget()
        self.setup_images_widget()
        self.setup_image_description_widget()
        self.setup_server_information_widget()
        self.setup_main_console_widget()

    
    def _get_dpi_scale(self):
        """Calculate DPI scaling factor"""
        try:
            # Get system DPI
            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                dpi = screen.logicalDotsPerInch()
                scale = dpi / 96.0
                return max(1.0, min(3.0, scale))
        except:
            pass
        return 1.0
