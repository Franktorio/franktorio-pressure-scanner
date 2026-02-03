# Franktorio Research Scanner
# Main Window Builder with Overlay/Windowed Mode Support
# February 2026

import datetime
from email.mime import application
import threading
import time
import asyncio
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QShortcut, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QKeySequence, QMovie

from config.vars import MIN_WIDTH, MIN_HEIGHT, VERSION, LOADING_GIF_PATH
from .colors import COLORS, convert_style_to_qss
from .window_controls import WindowControlsMixin
from .widgets import WidgetSetupMixin
from .debug_console import DebugConsoleWindow
from .sync_window import SyncWindow
from .bug_report import BugReportWindow

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
    ws_connection_closed = pyqtSignal()  # Signal when websocket connection closes
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Franktorio Research Scanner")
        
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
        
        self.persistent_window = get_value_from_config("main_window_persistent", False)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.dpi_scale = 1

        self.init_window_controls()

        self.setup_title_bar()
        self.setup_main_widget()
        self.setup_images_widget()
        self.setup_image_description_widget()
        self.setup_server_information_widget()
        self.setup_main_console_widget()

        self.server_info_updated.connect(self.on_server_info_updated)
        self.room_info_updated.connect(self.on_room_info_updated)
        self.update_start_scan_button_state.connect(self.on_update_start_scan_button_state)
        self.update_stop_scan_button_state.connect(self.on_update_stop_scan_button_state)
        self.log_console_message.connect(self.on_log_console_message)
        self.version_check_ready.connect(self.on_version_check_ready)
        self.debug_console_button.clicked.connect(self.on_debug_console_button_clicked)

        # Debug console window
        self.debug_console_window = DebugConsoleWindow(self)
        
        # Bug report window
        self.bug_report_window = BugReportWindow(self)
        
        # Sync window
        self.sync_window = SyncWindow(self)
        self.sync_window.hide()  # Hidden by default until user starts syncing
        
        # Websocket tracking
        self.websocket_thread = None
        self.websocket_loop = None
        self.websocket_task = None
        self.is_syncing = False

        # Scanner object placeholder
        self.scanner = Scanner()
        self.setup_scanner()
        self.setup_rotating_images()
        
        if hasattr(self, 'sync_action'):
            self.sync_action.triggered.connect(self.on_sync_button_clicked)
        if hasattr(self, 'persistent_action'):
            self.persistent_action.triggered.connect(self.on_persistent_window_button_toggled)
        
        saved_opacity = get_value_from_config("main_window_opacity", 100)
        if hasattr(self, 'opacity_slider'):
            self.opacity_slider.setValue(saved_opacity)
            self.setWindowOpacity(saved_opacity / 100.0)
            if hasattr(self, 'opacity_value_label'):
                self.opacity_value_label.setText(f"{saved_opacity}%")
        
        if self.persistent_window:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            if hasattr(self, 'persistent_action'):
                self.persistent_action.setText("Persistent Window: ON")
            self.show()
            
    
    def animated_minimize(self):
        """Minimize window with fade-out animation"""
        self.minimize_animation = QPropertyAnimation(self, b"windowOpacity")
        self.minimize_animation.setDuration(200)
        self.minimize_animation.setStartValue(1.0)
        self.minimize_animation.setEndValue(0.0)
        self.minimize_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        def finish_minimize():
            self.showMinimized()
            saved_opacity = get_value_from_config("main_window_opacity", 100)
            self.setWindowOpacity(saved_opacity / 100.0)
        
        self.minimize_animation.finished.connect(finish_minimize)
        self.minimize_animation.start()
    
    def _get_dpi_scale(self):
        """Calculate DPI scaling factor"""
        try:
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
        for url in picture_urls[1:]:
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
            return
        
        self.loaded_images.extend(image_data_list)
        
        if self.current_image_index < len(self.loaded_images):
            if hasattr(self, 'loading_movie') and self.loading_movie.state() == QMovie.Running:
                self.loading_movie.stop()
                self.display_image_label.setMovie(None)
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

        self.stop_scan_button.setEnabled(False)

        self.start_scan_button.clicked.connect(self.scanner.start)
        self.stop_scan_button.clicked.connect(self.scanner.stop)
        
        if hasattr(self, 'persistent_action'):
            self.persistent_action.triggered.connect(self.on_persistent_window_button_toggled)
        
        self.prev_image_button.clicked.connect(self.on_backward_image_button_clicked)
        self.next_image_button.clicked.connect(self.on_forward_image_button_clicked)
        self.toggle_rotating_images_button.clicked.connect(self.on_toggle_rotating_images_clicked)
        
        self.clear_console_button.clicked.connect(self.on_clear_console_clicked)
        self.copy_console_button.clicked.connect(self.on_copy_console_clicked)
        self.set_log_dir_button.clicked.connect(self.on_set_log_dir_clicked)

        self.forward_image_requested.connect(self.on_forward_image_button_clicked)
        self.backward_image_requested.connect(self.on_backward_image_button_clicked)
        self.images_loaded.connect(self.on_images_loaded)
        
        self.ws_add_player.connect(self.sync_window.add_player)
        self.ws_remove_player.connect(self.sync_window.remove_player)
        self.ws_change_player_room.connect(self.sync_window.change_player_room)
        self.ws_new_room_encounter.connect(self.sync_window.new_room_encounter)
        self.ws_connection_closed.connect(self.on_websocket_connection_closed)

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
        
        set_gui_signals(
            self.ws_add_player,
            self.ws_remove_player,
            self.ws_change_player_room,
            self.ws_new_room_encounter,
            self.debug_console_window.debug_console_message,
            self.ws_connection_closed
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
                self.debug_console_window.debug_console_message.emit(f"[WS] Websocket thread error: {e}")
            finally:
                self.websocket_loop.close()
        
        self.websocket_thread = threading.Thread(target=run_websocket, daemon=True)
        self.websocket_thread.start()
    
    def _stop_websocket_sync(self):
        """Stop websocket connection and reset sync window"""
        if self.websocket_loop:
            try:
                self.websocket_loop.call_soon_threadsafe(self.websocket_loop.stop)
            except:
                pass
        self.websocket_thread = None
        self.sync_window.clear_all()
    
    def on_websocket_connection_closed(self):
        """Handle websocket connection closure and reset sync state"""
        if self.is_syncing:
            self.is_syncing = False
            
            if hasattr(self, 'sync_action'):
                self.sync_action.setText("Join Scanning Session")
            
            self.log_console_message.emit("Connection closed. Sync stopped.")
            self.sync_window.clear_all()
            self.sync_window.hide()
    
    def closeEvent(self, event):
        """Save window geometry before closing"""
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

        self.current_image_index = 0
        self.loaded_images = []
        self.total_images_expected = 0
        self.last_image_change_time = datetime.datetime.now().timestamp()
        self.current_room_name = room_name

        if not room_info.picture_urls:
            self.display_image_label.setPixmap(QPixmap())  # Clear image
            self.image_counter_label.setText("0/0")
            return
        
        self.total_images_expected = len(room_info.picture_urls)
        
        QApplication.processEvents()
        
        self._show_loading_gif()
        self.image_counter_label.setText(f"Loading...")

        QApplication.processEvents()
        
        
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
        
        self.current_image_index = (self.current_image_index + 1) % self.total_images_expected
        
        self.image_counter_label.setText(f"{self.current_image_index + 1}/{self.total_images_expected}")
        
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
        
        self.current_image_index = (self.current_image_index - 1) % self.total_images_expected
        
        self.image_counter_label.setText(f"{self.current_image_index + 1}/{self.total_images_expected}")
        
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
        
        if hasattr(self, 'persistent_action'):
            self.persistent_action.setText("Persistent Window: ON" if self.persistent_window else "Persistent Window: OFF")
        
        set_value_in_config("main_window_persistent", self.persistent_window)
        
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
            
            self._start_websocket_sync(username, socket_name)
            
            if hasattr(self, 'sync_action'):
                self.sync_action.setText("Stop Scanning Session")
            
            self.is_syncing = True
            self.log_console_message.emit(f"Starting sync with socket '{socket_name}' as '{username}'...")
            
            self.sync_window.show()
            self.sync_window.raise_()
            self.sync_window.activateWindow()
        else:
            self._stop_websocket_sync()
            
            if hasattr(self, 'sync_action'):
                self.sync_action.setText("Join Scanning Session")
            
            self.is_syncing = False
            self.log_console_message.emit("Sync stopped.")
            
            self.sync_window.hide()

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
