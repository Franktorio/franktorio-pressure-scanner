# Franktorio Research Scanner
# Main Entry Point
# December 2025

import sys
import os
from PyQt5.QtCore import QSharedMemory, Qt
from src.app.gui import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from src.app.user_data.appdata import setup_user_data, get_value_from_config
setup_user_data()
from config.vars import APP_ICON_PATH

# Enable high DPI scaling support for Windows
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

if sys.platform == 'win32':
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(2)
    except:
        pass

app = QApplication(sys.argv)
app.setApplicationName("Franktorio Research Scanner")
app.setApplicationDisplayName("Franktorio Research Scanner")

# Single-instance enforcement
shared_memory = QSharedMemory("FranktorioScannerInstance")
if not shared_memory.create(1):
    print("Another instance is already running. Exiting...")
    sys.exit(0)
shared_memory.attach()


window = MainWindow()
window.show()


# Turn png into QIcon
app_icon = QIcon(APP_ICON_PATH)

# Place QIcon
app.setWindowIcon(app_icon)

# Emit config values to GUI
log_directory = get_value_from_config("set_log_path", "Automatic Detection")
window.log_console_message.emit(f"Log directory from config: {log_directory}")

try:
    sys.exit(app.exec_())
except Exception as e:
    print(f"An error occurred: {e}")