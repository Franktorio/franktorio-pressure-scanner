# Franktorio Research Scanner
# Main Window Builder
# December 2025

import datetime
from email.mime import application
import threading
import time
import asyncio
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QShortcut, QTextEdit, QPushButton, QLabel,
    QWidget, QVBoxLayout, QHBoxLayout, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QKeySequence, QMovie, QFont

from config.vars import MIN_WIDTH, MIN_HEIGHT, VERSION, LOADING_GIF_PATH
from .colors import COLORS, convert_style_to_qss
from .window_controls import WindowControlsMixin
from .widgets import WidgetSetupMixin

from src.app.scanner.scanner import Scanner
from src.api.scanner import RoomInfo
from src.api.images import download_image

from src.app.user_data.appdata import set_value_in_config, get_value_from_config

class MainWindow(WindowControlsMixin, WidgetSetupMixin, QMainWindow):
    # Define signals
    server_info_updated = pyqtSignal(dict)  # Signal to update server info widget with dictionary
    room_info_updated = pyqtSignal(RoomInfo)    # Signal to update room info widget with string
    update_start_scan_button_state = pyqtSignal(bool)  # Signal to update scan button state
    update_stop_scan_button_state = pyqtSignal(bool)   # Signal to update stop button state
    log_console_message = pyqtSignal(str)  # Signal to log messages to console
    version_check_ready = pyqtSignal(str)  # Signal when version check completes with latest version
    forward_image_requested = pyqtSignal()  # Signal to request forward image
    backward_image_requested = pyqtSignal()  # Signal to request backward image
    images_loaded = pyqtSignal(list, list, str)  # Signal when images are loaded (image_data_list, picture_urls, room_name)
    
    # Websocket signals for sync functionality
    ws_add_player = pyqtSignal(str)  # Signal to add player to sync window
    ws_remove_player = pyqtSignal(str)  # Signal to remove player from sync window
    ws_change_player_room = pyqtSignal(str, str)  # Signal to change player room (username, room_name)
    ws_new_room_encounter = pyqtSignal(str)  # Signal for new room encounter (room_name)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Franktorio Research Scanner")
        
        # Load saved window geometry or use defaults
        saved_geometry = get_value_from_config("window_geometry", None)
        if saved_geometry and isinstance(saved_geometry, dict):
            self.setGeometry(
                saved_geometry.get("x", 100),
                saved_geometry.get("y", 100),
                saved_geometry.get("width", MIN_WIDTH),
                saved_geometry.get("height", MIN_HEIGHT)
            )
        else:
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
        self.dpi_scale = 1

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
        self.debug_console_button.clicked.connect(self.on_debug_console_button_clicked)
        self.sync_button.clicked.connect(self.on_sync_button_clicked)

        # Debug console window
        self.debug_console_window = DebugConsoleWindow(self)
        
        # Bug report window
        self.bug_report_window = BugReportWindow(self)
        
        # Sync window
        self.sync_window = SyncWindow(self)
        
        # Websocket tracking
        self.websocket_thread = None
        self.websocket_loop = None
        self.websocket_task = None
        self.is_syncing = False

        # Scanner object placeholder
        self.scanner = Scanner()
        self.setup_scanner()
        self.setup_rotating_images()
            
    
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
    
    def _rotating_image_worker(self):
        """Worker thread to handle rotating images every 5 seconds"""
        while True:
            if not self.loaded_images or not self.rotating_images_enabled:
                time.sleep(0.5)
                continue
            
            current_time = datetime.datetime.now().timestamp()
            if current_time - self.last_image_change_time >= self.time_between_image_changes:
                self.forward_image_requested.emit()
                self.last_image_change_time = current_time
    
    def _show_loading_gif(self):
        """Display the loading gif animation"""
        self.loading_movie = QMovie(LOADING_GIF_PATH)
        self.loading_movie.setScaledSize(QSize(50, 50))
        self.display_image_label.setMovie(self.loading_movie)
        self.loading_movie.start()
    
    def _download_images_thread(self, picture_urls, room_name):
        """Thread worker to download remaining images (after first)"""
        downloaded_images = []
        # Skip first image since it's already downloaded
        for url in picture_urls[1:]:
            # Check if we're still on the same room before downloading
            if self.current_room_name != room_name:
                # Room changed, abort this download
                return
            image_data = download_image(url)
            downloaded_images.append(image_data)
        
        # Emit signal with downloaded images and room name for validation
        self.images_loaded.emit(downloaded_images, picture_urls, room_name)
    
    def on_images_loaded(self, image_data_list, picture_urls, room_name):
        """Slot to handle when remaining images have been downloaded"""
        if self.current_room_name != room_name:
            # Room has changed, ignore these images
            return
        
        self.loaded_images.extend(image_data_list)
        
        # If user is still viewing a loaded image, update display if loading gif is showing
        if self.current_image_index < len(self.loaded_images):
            # Stop loading gif if it's showing
            if hasattr(self, 'loading_movie') and self.loading_movie.state() == QMovie.Running:
                self.loading_movie.stop()
                self.display_image_label.setMovie(None)
                # Display the now-loaded image
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
            
            # Update counter
            self.image_counter_label.setText(f"{self.current_image_index + 1}/{self.total_images_expected}")
    
    def setup_rotating_images(self):
        """Rotating image setup"""
        self.current_image_index = 0
        self.loaded_images = []
        self.total_images_expected = 0  # Track total expected images for counter
        self.time_between_image_changes = 3 # Seconds
        self.last_image_change_time = datetime.datetime.now().timestamp()
        self.rotating_images_enabled = False  # Start with rotating disabled
        self.current_room_name = None  # Track which room's images are currently being downloaded

        self.rotating_image_thread = threading.Thread(target=self._rotating_image_worker, daemon=True)
        self.rotating_image_thread.start()  # Start the thread

    
    def setup_scanner(self):
        """Setup scanner and connect signals"""
        self.scanner.set_server_info_signal(self.server_info_updated)
        self.scanner.set_room_info_signal(self.room_info_updated)
        self.scanner.set_start_button_signal(self.update_start_scan_button_state)
        self.scanner.set_stop_button_signal(self.update_stop_scan_button_state)
        self.scanner.set_log_console_message_signal(self.log_console_message)
        self.scanner.set_version_check_ready_signal(self.version_check_ready)
        self.scanner.set_debug_console_message_signal(self.debug_console_window.debug_console_message)

        # Disable stop scan button initially
        self.stop_scan_button.setEnabled(False)

        # Connect start and stop buttons
        self.start_scan_button.clicked.connect(self.scanner.start)
        self.stop_scan_button.clicked.connect(self.scanner.stop)
        self.persistent_window_button.clicked.connect(self.on_persistent_window_button_toggled)
        self.prev_image_button.clicked.connect(self.on_backward_image_button_clicked)
        self.next_image_button.clicked.connect(self.on_forward_image_button_clicked)
        self.toggle_rotating_images_button.clicked.connect(self.on_toggle_rotating_images_clicked)
        
        # Connect console button signals
        self.clear_console_button.clicked.connect(self.on_clear_console_clicked)
        self.copy_console_button.clicked.connect(self.on_copy_console_clicked)
        self.set_log_dir_button.clicked.connect(self.on_set_log_dir_clicked)

        # Connect image navigation signals
        self.forward_image_requested.connect(self.on_forward_image_button_clicked)
        self.backward_image_requested.connect(self.on_backward_image_button_clicked)
        self.images_loaded.connect(self.on_images_loaded)
        
        # Connect websocket signals
        self.ws_add_player.connect(self.sync_window.add_player)
        self.ws_remove_player.connect(self.sync_window.remove_player)
        self.ws_change_player_room.connect(self.sync_window.change_player_room)
        self.ws_new_room_encounter.connect(self.sync_window.new_room_encounter)

        # Emit empty log message
        self.log_console_message.emit(f"")

        # Bind , and . keys for image navigation
        # TODO: REPLACE WITH A SEPARATE KEY LISTENER AS PYQT5 ONLY LISTENS IF WINDOW IS FOCUSED
        self.shortcut_next_image = QShortcut(QKeySequence("."), self)
        self.shortcut_prev_image = QShortcut(QKeySequence(","), self)

        self.shortcut_next_image.activated.connect(self.on_forward_image_button_clicked)
        self.shortcut_prev_image.activated.connect(self.on_backward_image_button_clicked)

    def resizeEvent(self, event):
        """Override resizeEvent to update widget sizes when window is resized"""
        super().resizeEvent(event)
        if hasattr(self, 'main_widget'):
            self._update_widget_sizes()
    
    def _start_websocket_sync(self, username: str, socket_name: str):
        """Start websocket connection in a separate thread"""
        from src.api.websocket import websocket_loop, set_gui_signals
        
        # Set the GUI signals for the websocket module
        set_gui_signals(
            self.ws_add_player,
            self.ws_remove_player,
            self.ws_change_player_room,
            self.ws_new_room_encounter
        )
        
        def run_websocket():
            """Run websocket loop in a separate thread"""
            self.websocket_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.websocket_loop)
            if self.scanner:
                current_room = self.scanner.latest_rooms[-1] if self.scanner.latest_rooms else "Unknown"
            try:
                self.websocket_loop.run_until_complete(websocket_loop(username, socket_name, current_room))
            except Exception as e:
                print(f"Websocket error: {e}")
            finally:
                self.websocket_loop.close()
        
        self.websocket_thread = threading.Thread(target=run_websocket, daemon=True)
        self.websocket_thread.start()
    
    def _stop_websocket_sync(self):
        """Stop websocket connection"""
        if self.websocket_loop:
            try:
                self.websocket_loop.call_soon_threadsafe(self.websocket_loop.stop)
            except:
                pass
        self.websocket_thread = None
        self.sync_window.clear_all()
    
    def closeEvent(self, event):
        """Save window geometry before closing"""
        # Stop websocket if running
        if self.is_syncing:
            self._stop_websocket_sync()
        
        geometry = self.geometry()
        window_geometry = {
            "x": geometry.x(),
            "y": geometry.y(),
            "width": geometry.width(),
            "height": geometry.height()
        }
        set_value_in_config("window_geometry", window_geometry)
        super().closeEvent(event)

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

        # Reset image state
        self.current_image_index = 0
        self.loaded_images = []
        self.total_images_expected = 0
        self.last_image_change_time = datetime.datetime.now().timestamp()
        self.current_room_name = room_name  # Track current room to prevent race conditions

        # Exit early if no images
        if not room_info.picture_urls:
            self.display_image_label.setPixmap(QPixmap())  # Clear image
            self.image_counter_label.setText("0/0")
            return
        
        # Set total expected images
        self.total_images_expected = len(room_info.picture_urls)
        
        # Update window
        QApplication.processEvents()
        
        # Show loading gif while first image downloads
        self._show_loading_gif()
        self.image_counter_label.setText(f"Loading...")

        QApplication.processEvents()
        
        
        # Stop loading gif
        if hasattr(self, 'loading_movie'):
            self.loading_movie.stop()
            self.display_image_label.setMovie(None)
        
        # Store and display first image
        self.image_counter_label.setText(f"1/{self.total_images_expected}")
        loaded_first_image = False
        for url in room_info.picture_urls:
            image_data = download_image(url)
            if image_data:
                self.loaded_images.append(image_data)
                if not loaded_first_image:
                    # Display first image immediately
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)
                    scaled_pixmap = pixmap.scaled(
                        self.display_image_label.width(),
                        self.display_image_label.height(),
                        Qt.KeepAspectRatioByExpanding,
                        Qt.SmoothTransformation
                    )
                    self.display_image_label.setPixmap(scaled_pixmap)
                    loaded_first_image = True
            QApplication.processEvents()



    def on_forward_image_button_clicked(self):
        """Slot to handle forward image button click"""
        if self.total_images_expected == 0:
            return
        
        # Calculate next index based on total expected images
        self.current_image_index = (self.current_image_index + 1) % self.total_images_expected
        
        # Update counter label with total expected images
        self.image_counter_label.setText(f"{self.current_image_index + 1}/{self.total_images_expected}")
        
        # Check if the image at this index has been loaded yet
        if self.current_image_index < len(self.loaded_images):
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
        else:
            # Image not loaded yet, show loading gif
            self._show_loading_gif()

    def on_backward_image_button_clicked(self):
        """Slot to handle backward image button click"""
        if self.total_images_expected == 0:
            return
        
        # Calculate previous index based on total expected images
        self.current_image_index = (self.current_image_index - 1) % self.total_images_expected
        
        # Update counter label with total expected images
        self.image_counter_label.setText(f"{self.current_image_index + 1}/{self.total_images_expected}")
        
        # Check if the image at this index has been loaded yet
        if self.current_image_index < len(self.loaded_images):
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
        else:
            # Image not loaded yet, show loading gif
            self._show_loading_gif()


    def on_persistent_window_button_toggled(self):
        """Slot to handle persistent window button toggled"""
        self.persistent_window = not self.persistent_window
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.persistent_window)
        self.persistent_window_button.setText("Persistent Window: ON" if self.persistent_window else "Persistent Window: OFF")
        self.show()
    
    def on_toggle_rotating_images_clicked(self):
        """Slot to handle toggle rotating images button click"""
        self.rotating_images_enabled = not self.rotating_images_enabled
        self.toggle_rotating_images_button.setText("Rotating Images: ON" if self.rotating_images_enabled else "Rotating Images: OFF")
        if self.rotating_images_enabled:
            self.last_image_change_time = datetime.datetime.now().timestamp()
    
    def on_update_start_scan_button_state(self, enabled):
        """Slot to handle start scan button state updates"""
        self.start_scan_button.setEnabled(enabled)
    
    def on_update_stop_scan_button_state(self, enabled):
        """Slot to handle stop scan button state updates"""
        self.stop_scan_button.setEnabled(enabled)

    def on_debug_console_button_clicked(self):
        """Slot to handle debug console button click"""
        # Update debug stats before showing window
        stats = self.scanner.get_debug_stats()
        self.debug_console_window.update_stats(stats)
        self.debug_console_window.show()
    
    def on_sync_button_clicked(self):
        """Slot to handle sync button click"""
        if not self.is_syncing:
            
            username, ok1 = QInputDialog.getText(self, "Sync - Enter Username", "Username:")
            if not ok1 or not username:
                return
            
            socket_name, ok2 = QInputDialog.getText(self, "Sync - Enter Socket Name", "Socket Name:")
            if not ok2 or not socket_name:
                return
            
            # Start websocket connection
            self._start_websocket_sync(username, socket_name)
            self.sync_button.setText("Stop Sync")
            self.is_syncing = True
            self.log_console_message.emit(f"Starting sync with socket '{socket_name}' as '{username}'...")
        else:
            # Stop websocket connection
            self._stop_websocket_sync()
            self.sync_button.setText("Sync")
            self.is_syncing = False
            self.log_console_message.emit("Sync stopped.")
        
        self.sync_window.show()
        self.sync_window.raise_()
        self.sync_window.activateWindow()

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
        from src.app.user_data.appdata import get_value_from_config
        
        current_log_path = get_value_from_config("set_log_path", "")
        
        # If there's already a path set, remove it
        if current_log_path != "":
            set_value_in_config("set_log_path", '')
            self.log_console_message.emit("Log directory removed, defaulting to Automatic Detection")
            self.log_console_message.emit(">> RESTART REQUIRED << for changes to take effect")
            self.set_log_dir_button.setText("Set Log Dir")
        else:
            # Otherwise, open dialog to set new path
            dir_path = QFileDialog.getExistingDirectory(self, "Select Log Directory", os.path.expanduser("~"))
            
            if dir_path:
                set_value_in_config("set_log_path", dir_path)
                self.log_console_message.emit(f"Log directory set to: {dir_path}")
                self.log_console_message.emit(">> RESTART REQUIRED << for changes to take effect")
                self.set_log_dir_button.setText("Undo Log Dir")
            else:
                self.log_console_message.emit("Log directory selection cancelled")

class DebugConsoleWindow(QMainWindow):
    """A separate window for detailed debug console output."""
    debug_console_message = pyqtSignal(str)  # Signal to log messages to debug console
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Debug Console v{VERSION}")
        self.setGeometry(150, 150, 800, 600)
        
        
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
                    "font-size": "10pt"
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


class SyncWindow(QMainWindow):
    """A window to display synchronized room information."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sync - Room Status")
        self.setGeometry(300, 100, 350, 780)
        
        style = {
            "styles": {
                "QMainWindow": {
                    "background-color": COLORS['background']
                },
                ".room-widget": {
                    "background-color": COLORS['surface_light'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px"
                },
                ".player-list-widget": {
                    "background-color": COLORS['surface_light'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px",
                    "padding": "8px"
                },
                "QLabel": {
                    "color": COLORS['text'],
                    "background-color": "transparent",
                    "border": "none"
                },
                ".room-image": {
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "5px",
                    "background-color": COLORS['surface']
                }
            }
        }
        
        # Apply styles
        self.setStyleSheet(convert_style_to_qss(style))

        self.setWindowFlag(Qt.WindowStaysOnTopHint, parent.persistent_window)
        
        # Create central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # Create vertical layout for all room widgets
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create player list widget at the top
        self.player_list_widget = self._create_player_list_widget()
        main_layout.addWidget(self.player_list_widget)
        
        # Create 6 room widgets
        self.room_widgets = []
        for i in range(6):
            room_widget = self._create_room_widget(i + 1)
            self.room_widgets.append(room_widget)
            main_layout.addWidget(room_widget)
        
        # Add stretch at the bottom to keep widgets at top
        main_layout.addStretch()
    
    def _create_player_list_widget(self):
        """Create a widget to display all players currently in the socket."""
        widget = QWidget()
        widget.setObjectName("player-list-widget")
        widget.setProperty("class", "player-list-widget")
        widget.setMinimumHeight(50)
        widget.setMaximumHeight(80)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Title
        title_label = QLabel("Connected Players")
        title_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        layout.addWidget(title_label)
        
        # Players list
        players_label = QLabel("None")
        players_label.setFont(QFont("Segoe UI", 8))
        players_label.setWordWrap(True)
        layout.addWidget(players_label)
        
        widget.players_label = players_label
        return widget
    
    def _create_room_widget(self, room_number):
        """Create a single room widget with room name, players, and image."""
        widget = QWidget()
        widget.setObjectName("room-widget")
        widget.setProperty("class", "room-widget")
        widget.setMinimumHeight(140)
        widget.setMaximumHeight(140)
        
        # Create layout for this room widget
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # Room name
        room_name_label = QLabel(f"Room Name {room_number}")
        room_name_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(room_name_label)
        
        # Players list
        players_label = QLabel("Players: None")
        players_label.setFont(QFont("Segoe UI", 8))
        players_label.setWordWrap(True)
        layout.addWidget(players_label)
        
        # Image area
        image_label = QLabel("No Image")
        image_label.setProperty("class", "room-image")
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumHeight(70)
        image_label.setMaximumHeight(70)
        image_label.setScaledContents(False)
        layout.addWidget(image_label)
        
        # Store references for later updates
        widget.room_name_label = room_name_label
        widget.players_label = players_label
        widget.image_label = image_label
        
        return widget
    
    def update_room_widget(self, index, room_name, players_list, image_data=None):
        """Update a specific room widget with new data."""
        if 0 <= index < len(self.room_widgets):
            widget = self.room_widgets[index]
            widget.room_name_label.setText(room_name)
            
            # Display list of players or "None" if empty
            if players_list:
                players_text = f"Players: {', '.join(players_list)}"
            else:
                players_text = "Players: None"
            widget.players_label.setText(players_text)
            
            if image_data:
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                scaled_pixmap = pixmap.scaled(
                    widget.image_label.width(),
                    widget.image_label.height(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
                widget.image_label.setPixmap(scaled_pixmap)
            else:
                widget.image_label.setText("No Image")
    
    def add_player(self, username: str):
        """Add a player to tracking."""
        print(f"[WS] Add player: {username}")
        if not hasattr(self, 'players'):
            self.players = {}
        
        if username not in self.players:
            self.players[username] = {"current_room": None}
            self._update_display()
    
    def remove_player(self, username: str):
        """Remove a player from tracking."""
        print(f"[WS] Remove player: {username}")
        if hasattr(self, 'players') and username in self.players:
            del self.players[username]
            self._update_display()
    
    def change_player_room(self, username: str, room_name: str):
        """Change a player's current room."""
        print(f"[WS] Change player room: {username} -> {room_name}")
        if not hasattr(self, 'players'):
            self.players = {}
        
        if username not in self.players:
            self.players[username] = {}
        
        self.players[username]["current_room"] = room_name
        self._update_display()
    
    def new_room_encounter(self, room_name: str):
        """Add a new room encounter."""
        from src.api.images import download_image
        from src.api.scanner import _get_room_info
        print(f"[WS] New room encounter: {room_name}")
        if not hasattr(self, 'encountered_rooms'):
            self.encountered_rooms = []

        if not hasattr(self, 'image_map'):
            self.image_map = {}
        
        if room_name not in self.encountered_rooms:
            self.encountered_rooms.insert(0, room_name)  # Add to front
            if len(self.encountered_rooms) > 6:
                self.encountered_rooms = self.encountered_rooms[:6]  # Keep only 6 most recent
            
            self._update_display()  # Update display before downloading
            QApplication.processEvents()  # Update UI
            
            # Get room info and download first image
            room_info = _get_room_info(room_name)
            if room_info and room_info.picture_urls:
                image_data = download_image(room_info.picture_urls[0])
                self.image_map[room_name] = image_data
            else:
                self.image_map[room_name] = None
            
            self._update_display()  # Update again after image download
            QApplication.processEvents()  # Update UI
    
    def _update_display(self):
        """Update the display with current room and player data."""
        print("[WS] Updating display")
        if not hasattr(self, 'encountered_rooms'):
            self.encountered_rooms = []
        if not hasattr(self, 'players'):
            self.players = {}
        
        # Update player list widget
        if hasattr(self, 'player_list_widget'):
            if self.players:
                player_names = sorted(list(self.players.keys()))
                players_text = ", ".join(player_names)
            else:
                players_text = "None"
            self.player_list_widget.players_label.setText(players_text)
            QApplication.processEvents()  # Update UI
        
        # Collect player names per room
        room_players = {}
        for username, data in self.players.items():
            current_room = data.get("current_room")
            if current_room:
                if current_room not in room_players:
                    room_players[current_room] = []
                room_players[current_room].append(username)
        
        # Update widgets with the 6 most recent rooms
        for i in range(6):
            QApplication.processEvents()  # Update UI during iteration
            if i < len(self.encountered_rooms):
                room_name = self.encountered_rooms[i]
                players_list = room_players.get(room_name, [])
                image_data = self.image_map.get(room_name) if hasattr(self, 'image_map') else None
                self.update_room_widget(i, room_name, players_list, image_data)
            else:
                self.update_room_widget(i, f"Room {i + 1}", [])
    
    def clear_all(self):
        """Clear all players and rooms."""
        print("[WS] Clearing all sync data")
        self.players = {}
        self.encountered_rooms = []
        self._update_display()


class BugReportWindow(QMainWindow):
    """A window to submit bug reports."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Submit Bug Report")
        self.setGeometry(200, 200, 600, 400)
        
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
                    "font-size": "10pt"
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

        