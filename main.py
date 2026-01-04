# Franktorio Research Scanner
# Main Entry Point
# December 2025

from email.charset import QP
import sys
from PyQt5.QtCore import QSharedMemory
from src.app.gui import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

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

app_icon_path = "config/images/researchfrankbadge.ico"

# Turn png into QIcon
app_icon = QIcon(app_icon_path)
app.setWindowIcon(app_icon)

try:
    sys.exit(app.exec_())
except Exception as e:
    print(f"An error occurred: {e}")