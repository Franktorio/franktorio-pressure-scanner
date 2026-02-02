# Franktorio Research Scanner
# Sync Window
# December 2025

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

from .colors import COLORS, convert_style_to_qss


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

        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        
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
        players_label = QLabel("")
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
