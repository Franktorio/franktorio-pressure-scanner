# Franktorio Research Scanner
# Sync Window
# December 2025

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication, QMenu, QSlider, QWidgetAction
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

from .colors import COLORS, convert_style_to_qss


class SyncWindow(QMainWindow):
    """A window to display synchronized room information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sync - Room Status")
        self.setGeometry(300, 100, 350, 810)
        
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        
        # Variables for window dragging
        self.dragging = False
        self.drag_position = None
        
        from src.app.user_data.appdata import get_value_from_config
        self.persistent_window = get_value_from_config("sync_window_persistent", True)
        
        style = {
            "styles": {
                "QMainWindow": {
                    "background-color": COLORS['background'],
                    "border": f"1px solid {COLORS['border']}"
                },
                "#syncTitleBar": {
                    "background-color": COLORS['titlebar'],
                    "border-bottom": f"1px solid {COLORS['border']}"
                },
                "#syncTitleLabel": {
                    "color": COLORS['text'],
                    "font-size": "12px",
                    "font-weight": "bold"
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
                },
                "QPushButton": {
                    "background-color": COLORS['button_bg'],
                    "color": COLORS['button_text_active'],
                    "border": "none",
                    "font-size": "12px",
                    "width": "30px",
                    "height": "20px",
                    "border-radius": "3px"
                },
                "QPushButton:hover": {
                    "background-color": COLORS['button_hover']
                },
                "QPushButton#syncCloseButton": {
                    "background-color": "#ff5c5c",
                    "color": "#ffffff",
                },
                "QPushButton#syncCloseButton:hover": {
                    "background-color": "#ff1e1e"
                },
                "QPushButton#syncMinimizeButton": {
                    "background-color": "#000000",
                    "color": "#ffffff",
                },
                "QPushButton#syncMinimizeButton:hover": {
                    "background-color": "#333333"
                },
                "QPushButton#syncMenuButton": {
                    "background-color": COLORS['button_bg'],
                    "color": COLORS['button_text_active'],
                    "font-size": "14px",
                },
                "QPushButton#syncMenuButton:hover": {
                    "background-color": COLORS['button_hover']
                }
            }
        }
        
        self.setStyleSheet(convert_style_to_qss(style))

        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        main_container_layout = QVBoxLayout(central_widget)
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        main_container_layout.setSpacing(0)
        
        self._setup_title_bar()
        main_container_layout.addWidget(self.title_bar)
        
        content_widget = QWidget()
        main_container_layout.addWidget(content_widget)
        
        # Create vertical layout for all room widgets
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        self.player_list_widget = self._create_player_list_widget()
        main_layout.addWidget(self.player_list_widget)
        
        self.room_widgets = []
        for i in range(6):
            room_widget = self._create_room_widget(i + 1)
            self.room_widgets.append(room_widget)
            main_layout.addWidget(room_widget)
        
        main_layout.addStretch()
        
        from src.app.user_data.appdata import get_value_from_config
        saved_opacity = get_value_from_config("sync_window_opacity", 100)
        if hasattr(self, 'opacity_slider'):
            self.opacity_slider.setValue(saved_opacity)
            self.setWindowOpacity(saved_opacity / 100.0)
            if hasattr(self, 'opacity_value_label'):
                self.opacity_value_label.setText(f"{saved_opacity}%")
        
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.persistent_window)
        if hasattr(self, 'persistent_action'):
            self.persistent_action.setText("Persistent Window: ON" if self.persistent_window else "Persistent Window: OFF")
    
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
        players_label = QLabel("")
        players_label.setFont(QFont("Segoe UI", 8))
        players_label.setWordWrap(True)
        layout.addWidget(players_label)
        
        widget.players_label = players_label
        return widget
    
    def _setup_title_bar(self):
        """Setup custom title bar for sync window"""
        self.title_bar = QWidget(self)
        self.title_bar.setFixedHeight(30)
        self.title_bar.setObjectName("syncTitleBar")
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
        title_layout.setSpacing(10)
        
        # Title label
        title_label = QLabel("Sync - Room Status", self.title_bar)
        title_label.setObjectName("syncTitleLabel")
        title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        self.menu_button = QPushButton("≡", self.title_bar)
        self.menu_button.setObjectName("syncMenuButton")
        self.menu_button.setFixedSize(25, 20)
        self.menu_button.clicked.connect(self._show_dropdown_menu)
        title_layout.addWidget(self.menu_button)
        
        self._create_dropdown_menu()
        
        # Minimize button
        minimize_button = QPushButton("-", self.title_bar)
        minimize_button.setObjectName("syncMinimizeButton")
        minimize_button.setFixedSize(20, 20)
        minimize_button.clicked.connect(self.showMinimized)
        title_layout.addWidget(minimize_button)
        
        # Close button
        close_button = QPushButton("X", self.title_bar)
        close_button.setObjectName("syncCloseButton")
        close_button.setFixedSize(20, 20)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button)
    
    def _create_dropdown_menu(self):
        """Create dropdown menu with opacity slider and persistent window toggle"""
        self.dropdown_menu = QMenu(self)
        
        # Style the dropdown menu
        menu_style = f"""
            QMenu {{
                background-color: {COLORS['button_bg']};
                color: {COLORS['button_text_active']};
                border: 1px solid {COLORS['border']};
                padding: 5px;
            }}
            QMenu::item {{
                padding: 5px 20px;
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['button_hover']};
            }}
            QSlider::groove:horizontal {{
                background: {COLORS['surface']};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['button_text_active']};
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {COLORS['button_hover']};
            }}
        """
        self.dropdown_menu.setStyleSheet(menu_style)
        
        # Add Opacity Slider
        opacity_widget = QWidget()
        opacity_layout = QVBoxLayout(opacity_widget)
        opacity_layout.setContentsMargins(10, 5, 10, 5)
        opacity_layout.setSpacing(5)
        
        opacity_label = QLabel("Window Opacity")
        opacity_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold;")
        opacity_layout.addWidget(opacity_label)
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(30)  # 30% minimum opacity
        self.opacity_slider.setMaximum(100)  # 100% maximum opacity
        self.opacity_slider.setValue(100)  # Default to 100%
        self.opacity_slider.setTickPosition(QSlider.TicksBelow)
        self.opacity_slider.setTickInterval(10)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        
        self.opacity_value_label = QLabel("100%")
        self.opacity_value_label.setStyleSheet(f"color: {COLORS['text']};")
        self.opacity_value_label.setAlignment(Qt.AlignCenter)
        opacity_layout.addWidget(self.opacity_value_label)
        
        opacity_action = QWidgetAction(self.dropdown_menu)
        opacity_action.setDefaultWidget(opacity_widget)
        self.dropdown_menu.addAction(opacity_action)
        
        self.dropdown_menu.addSeparator()
        
        self.persistent_action = self.dropdown_menu.addAction("Persistent Window: ON")
        self.persistent_action.triggered.connect(self._toggle_persistent_window)
    
    def _show_dropdown_menu(self):
        """Show the dropdown menu below the menu button"""
        button_pos = self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft())
        self.dropdown_menu.exec_(button_pos)
    
    def _on_opacity_changed(self, value):
        """Handle opacity slider value change"""
        from src.app.user_data.appdata import set_value_in_config
        opacity = value / 100.0
        self.setWindowOpacity(opacity)
        self.opacity_value_label.setText(f"{value}%")
        set_value_in_config("sync_window_opacity", value)
    
    def _toggle_persistent_window(self):
        """Toggle persistent window (always on top) state"""
        from src.app.user_data.appdata import set_value_in_config
        self.persistent_window = not self.persistent_window
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.persistent_window)
        self.persistent_action.setText("Persistent Window: ON" if self.persistent_window else "Persistent Window: OFF")
        set_value_in_config("sync_window_persistent", self.persistent_window)
        self.show()
    
    def mousePressEvent(self, event):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.LeftButton:
            if self.title_bar.geometry().contains(event.pos()):
                self.dragging = True
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
                return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging"""
        if self.dragging and self.drag_position is not None:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            return
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.drag_position = None
            event.accept()
        super().mouseReleaseEvent(event)
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.parent():
            parent = self.parent()
            if hasattr(parent, 'is_syncing') and parent.is_syncing:
                parent._stop_websocket_sync()
                
                # Update sync state
                parent.is_syncing = False
                
                # Update menu action text if it exists
                if hasattr(parent, 'sync_action'):
                    parent.sync_action.setText("Join Scanning Session")
                
                # Log message
                if hasattr(parent, 'log_console_message'):
                    parent.log_console_message.emit("Sync window closed. Connection stopped.")
                
                # Clear the sync window
                self.clear_all()
        
        # Accept the close event
        event.accept()
    
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
        
        # Players title label (bold)
        players_title_label = QLabel("<b>Players:</b>")
        players_title_label.setFont(QFont("Segoe UI", 8))
        layout.addWidget(players_title_label)
        
        # Players list
        players_label = QLabel("")
        players_label.setFont(QFont("Segoe UI", 8))
        players_label.setWordWrap(True)
        layout.addWidget(players_label)
        
        # Image area
        image_label = QLabel("No Image")
        image_label.setProperty("class", "room-image")
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumHeight(70)
        image_label.setMaximumHeight(70)
        image_label.setMinimumWidth(300)
        image_label.setMaximumWidth(300)
        image_label.setScaledContents(False)
        image_label.setSizePolicy(image_label.sizePolicy().horizontalPolicy(), image_label.sizePolicy().verticalPolicy())
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
            
            # Display list of players or empty if none
            if players_list:
                players_text = ", ".join(players_list)
            else:
                players_text = ""
            widget.players_label.setText(players_text)
            
            if image_data:
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                # Scale to fill width and crop vertically
                scaled_pixmap = pixmap.scaled(
                    300,
                    70,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
                # Crop the image if it's taller than needed
                if scaled_pixmap.height() > 70:
                    # Center crop vertically
                    y_offset = (scaled_pixmap.height() - 70) // 2
                    scaled_pixmap = scaled_pixmap.copy(0, y_offset, 300, 70)
                widget.image_label.setPixmap(scaled_pixmap)
            else:
                widget.image_label.setText("No Image")
    
    def add_player(self, username: str):
        """Add a player to tracking."""
        if not hasattr(self, 'players'):
            self.players = {}
        
        if username not in self.players:
            self.players[username] = {"current_room": None}
            self._update_display()
    
    def remove_player(self, username: str):
        """Remove a player from tracking."""
        if hasattr(self, 'players') and username in self.players:
            del self.players[username]
            self._update_display()
    
    def change_player_room(self, username: str, room_name: str):
        """Change a player's current room."""
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
        if not hasattr(self, 'encountered_rooms'):
            self.encountered_rooms = []
        if not hasattr(self, 'players'):
            self.players = {}
        
        # Update player list widget
        if hasattr(self, 'player_list_widget'):
            if self.players:
                player_names = sorted(list(self.players.keys()))
                player_names = [f"[ {name} ]" for name in player_names]
                players_text = ", ".join(player_names)
            else:
                players_text = ""
            self.player_list_widget.players_label.setText(players_text)
            QApplication.processEvents()  # Update UI
        
        # Collect player names per room
        room_players = {}
        for username, data in self.players.items():
            current_room = data.get("current_room")
            if current_room:
                if current_room not in room_players:
                    room_players[current_room] = []
                room_players[current_room].append(f"[ {username} ]")
        
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
        self.players = {}
        self.encountered_rooms = []
        self._update_display()
