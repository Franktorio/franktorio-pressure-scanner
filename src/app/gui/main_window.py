# Franktorio Research Scanner
# Main Window Builder
# December 2025

import datetime
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QShortcut
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QKeySequence

from config.vars import MIN_WIDTH, MIN_HEIGHT, VERSION
from .colors import COLORS, convert_style_to_qss
from .window_controls import WindowControlsMixin
from .widgets import WidgetSetupMixin

from src.app.scanner.scanner import Scanner
from src.api.scanner import RoomInfo
from src.api.images import download_image

from src.app.user_data.appdata import set_value_in_config

class MainWindow(WindowControlsMixin, WidgetSetupMixin, QMainWindow):
    # Define signals
    server_info_updated = pyqtSignal(dict)  # Signal to update server info widget with dictionary
    room_info_updated = pyqtSignal(RoomInfo)    # Signal to update room info widget with string
    update_start_scan_button_state = pyqtSignal(bool)  # Signal to update scan button state
    update_stop_scan_button_state = pyqtSignal(bool)   # Signal to update stop button state
    log_console_message = pyqtSignal(str)  # Signal to log messages to console
    version_check_ready = pyqtSignal(str)  # Signal when version check completes with latest version
    
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
        self.persistent_window = False

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

        # Connect signals to slots
        self.server_info_updated.connect(self.on_server_info_updated)
        self.room_info_updated.connect(self.on_room_info_updated)
        self.update_start_scan_button_state.connect(self.on_update_start_scan_button_state)
        self.update_stop_scan_button_state.connect(self.on_update_stop_scan_button_state)
        self.log_console_message.connect(self.on_log_console_message)
        self.version_check_ready.connect(self.on_version_check_ready)

        # Scanner object placeholder
        self.scanner = Scanner()
        self.setup_scanner()
            
    
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
    
    def setup_scanner(self):
        """Setup scanner and connect signals"""
        self.scanner.set_server_info_signal(self.server_info_updated)
        self.scanner.set_room_info_signal(self.room_info_updated)
        self.scanner.set_start_button_signal(self.update_start_scan_button_state)
        self.scanner.set_stop_button_signal(self.update_stop_scan_button_state)
        self.scanner.set_log_console_message_signal(self.log_console_message)
        self.scanner.set_version_check_ready_signal(self.version_check_ready)

        # Disable stop scan button initially
        self.stop_scan_button.setEnabled(False)

        # Connect start and stop buttons
        self.start_scan_button.clicked.connect(self.scanner.start)
        self.stop_scan_button.clicked.connect(self.scanner.stop)
        self.persistent_window_button.clicked.connect(self.on_persistent_window_button_toggled)
        self.prev_image_button.clicked.connect(self.on_backward_image_button_clicked)
        self.next_image_button.clicked.connect(self.on_forward_image_button_clicked)
        
        # Connect console button signals
        self.clear_console_button.clicked.connect(self.on_clear_console_clicked)
        self.copy_console_button.clicked.connect(self.on_copy_console_clicked)
        self.set_log_dir_button.clicked.connect(self.on_set_log_dir_clicked)

        # Emit empty log message
        self.log_console_message.emit(f"")

        # Bind , and . keys for image navigation
        # TODO: REPLACE WITH A SEPARATE KEY LISTENER AS PYQT5 ONLY LISTENS IF WINDOW IS FOCUSED
        self.shortcut_next_image = QShortcut(QKeySequence("."), self)
        self.shortcut_prev_image = QShortcut(QKeySequence(","), self)

        self.shortcut_next_image.activated.connect(self.on_forward_image_button_clicked)
        self.shortcut_prev_image.activated.connect(self.on_backward_image_button_clicked)

    def on_log_console_message(self, message: str):
        """Slot to handle logging messages to console"""
        MAX_CHARS = 5000
        now = ""  if message == "" else f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        formatted_message = f"{now} {message}\n"
        self.console_text_area.setText(self.console_text_area.toPlainText()[-MAX_CHARS:] + formatted_message) # Keep last MAX_CHARS chars
        self.console_text_area.verticalScrollBar().setValue(self.console_text_area.verticalScrollBar().maximum()) # Auto-scroll to bottom

    def on_server_info_updated(self, info_dict: dict):
        """Slot to handle server info updates"""
        # Update server info labels with new information
        country = info_dict.get("country", "N/A")
        region = info_dict.get("region", "N/A")
        city = info_dict.get("city", "N/A")
        
        self.server_country_label.setText(f"<b>Country:</b> {country}")
        self.server_region_label.setText(f"<b>Region:</b> {region}")
        self.server_city_label.setText(f"<b>City:</b> {city}")

        # Adjust label sizes
        self.server_country_label.adjustSize()
        self.server_region_label.adjustSize()
        self.server_city_label.adjustSize()
    
    def on_room_info_updated(self, room_info: RoomInfo):
        """Slot to handle room info updates"""
        room_name = room_info.room_name if room_info.room_name else "N/A"
        roomtype = room_info.roomtype if room_info.roomtype else "N/A"
        description = room_info.description if room_info.description else "N/A"
        tags = ", ".join(room_info.tags) if room_info.tags else "N/A"
        
        self.room_name_label.setText(f"<b>Room:</b> {room_name}")
        self.room_type_label.setText(f"<b>Type:</b> {roomtype}")
        self.room_description_label.setText(f"<b>Description:</b> {description}")
        self.room_tags_label.setText(f"<b>Tags:</b> {tags}")
        
        # Adjust label sizes
        self.room_name_label.adjustSize()
        self.room_type_label.adjustSize()
        self.room_description_label.adjustSize()
        self.room_tags_label.adjustSize()

        # Download and display images
        self.current_image_index = 0
        self.loaded_images = []

        QApplication.processEvents()

        # Exit early if no images
        if not room_info.picture_urls:
            self.display_image_label.setPixmap(QPixmap())  # Clear image
            self.image_counter_label.setText("0/0")
            return
        
        # Download first image
        first_image_data = download_image(room_info.picture_urls[0])
        self.loaded_images.append(first_image_data)

        total_images = len(room_info.picture_urls)
        self.image_counter_label.setText(f"1/{total_images}")

        # Display the first image
        if first_image_data:
            pixmap = QPixmap()
            pixmap.loadFromData(first_image_data)
            scaled_pixmap = pixmap.scaled(
                self.display_image_label.width(),
                self.display_image_label.height(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            self.display_image_label.setPixmap(scaled_pixmap)
        QApplication.processEvents()

        # Load rest of the images
        for url in room_info.picture_urls[1:]:
            image_data = download_image(url)
            self.loaded_images.append(image_data)
            QApplication.processEvents()


    def on_forward_image_button_clicked(self):
        """Slot to handle forward image button click"""
        if not self.loaded_images:
            return
        self.current_image_index = (self.current_image_index + 1) % len(self.loaded_images)
        
        # Update counter label
        total_images = len(self.loaded_images)
        self.image_counter_label.setText(f"{self.current_image_index + 1}/{total_images}")
        
        current_image = self.loaded_images[self.current_image_index]

        if current_image:
            pixmap = QPixmap()
            pixmap.loadFromData(current_image)
            scaled_pixmap = pixmap.scaled(
                self.display_image_label.width(),
                self.display_image_label.height(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            self.display_image_label.setPixmap(scaled_pixmap)

    def on_backward_image_button_clicked(self):
        """Slot to handle backward image button click"""
        if not self.loaded_images:
            return
        self.current_image_index = (self.current_image_index - 1) % len(self.loaded_images)
        
        # Update counter label
        total_images = len(self.loaded_images)
        self.image_counter_label.setText(f"{self.current_image_index + 1}/{total_images}")
        
        current_image = self.loaded_images[self.current_image_index]

        if current_image:
            pixmap = QPixmap()
            pixmap.loadFromData(current_image)
            scaled_pixmap = pixmap.scaled(
                self.display_image_label.width(),
                self.display_image_label.height(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            self.display_image_label.setPixmap(scaled_pixmap)


    def on_persistent_window_button_toggled(self):
        """Slot to handle persistent window button toggled"""
        self.persistent_window = not self.persistent_window
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.persistent_window)
        self.persistent_window_button.setText("Persistent Window: ON" if self.persistent_window else "Persistent Window: OFF")
        self.show()
    
    def on_update_start_scan_button_state(self, enabled):
        """Slot to handle start scan button state updates"""
        self.start_scan_button.setEnabled(enabled)
    
    def on_update_stop_scan_button_state(self, enabled):
        """Slot to handle stop scan button state updates"""
        self.stop_scan_button.setEnabled(enabled)

    def on_version_check_ready(self, latest_version: str):
        """Slot to handle version check completion"""
        if not latest_version or latest_version == "unknown":
            self.log_console_message.emit("Version check completed (unable to retrieve latest version)")
            return
        
        if latest_version != VERSION:
            from PyQt5.QtWidgets import QMessageBox
            self.log_console_message.emit(f"New version available: {latest_version} (current: {VERSION})")
            
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Update Available")
            msg_box.setTextFormat(Qt.RichText)
            msg_box.setText(
                f"A new version of Franktorio Research Scanner is available!<br><br>"
                f"Current version: {VERSION}<br>"
                f"Latest version: {latest_version}<br><br>"
                f"Please visit <a href=\"https://github.com/Franktorio/franktorio-pressure-scanner/releases\">the repository</a> to download the latest version."
            )
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
        else:
            self.log_console_message.emit(f"Running latest version: {VERSION}")
    
    def on_clear_console_clicked(self):
        """Slot to handle clear console button click"""
        self.console_text_area.clear()
        self.log_console_message.emit(f"Console cleared (version: {VERSION})")
    
    def on_copy_console_clicked(self):
        """Slot to handle copy console button click"""
        console_text = self.console_text_area.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(console_text)
        self.log_console_message.emit("Console text copied to clipboard")
    
    def on_set_log_dir_clicked(self):
        """Slot to handle set log directory button click"""
        
        dir_path = QFileDialog.getExistingDirectory(self, "Select Log Directory", os.path.expanduser("~"))
        
        if dir_path:
            set_value_in_config("set_log_path", dir_path)
            self.log_console_message.emit(f"Log directory set to: {dir_path}")
        else:
            set_value_in_config("set_log_path", '')
            self.log_console_message.emit("Log directory selection cancelled, defaulting to Automatic Detection")