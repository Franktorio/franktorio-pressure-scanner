# Franktorio Research Scanner
# Main Entry Point
# December 2025

import os
import sys
from PyQt5.QtCore import QSharedMemory
from src.app.gui import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from src.app.user_data.appdata import setup_user_data, get_value_from_config

app = QApplication(sys.argv)
app.setApplicationName("Franktorio Research Scanner")
app.setApplicationDisplayName("Franktorio Research Scanner")

# Single-instance enforcement
shared_memory = QSharedMemory("FranktorioScannerInstance")
if not shared_memory.create(1):
    print("Another instance is already running. Exiting...")
    sys.exit(0)
shared_memory.attach()

setup_user_data()

window = MainWindow()
window.show()

# Load application icon config\images\researchfrankbadge.ico
app_icon_path = os.path.join("config", "images", "researchfrankbadge.ico")

# Turn png into QIcon
app_icon = QIcon(app_icon_path)

# Place QIcon
app.setWindowIcon(app_icon)

# Emit config values to GUI
log_directory = get_value_from_config("set_log_path", "Automatic Detection")
window.log_console_message.emit(f"Log directory from config: {log_directory}")

try:
    sys.exit(app.exec_())
except Exception as e:
    print(f"An error occurred: {e}")