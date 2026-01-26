# Franktorio Research Scanner
# Widget Setup Methods
# December 2025

import threading

from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QFontMetrics
from PyQt5.QtWidgets import QApplication

from config.vars import VERSION, APP_ICON_PATH

from .colors import COLORS, convert_style_to_qss


class ElidedLabel(QLabel):
    """Label that automatically elides text that's too long"""
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self._full_text = text
        
    def setText(self, text):
        """Override setText to store full text and elide if needed"""
        self._full_text = text
        self._updateText()
        
    def _updateText(self):
        """Update displayed text with elision if needed"""
        if not self._full_text:
            super().setText('')
            return
            
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self._full_text, Qt.ElideRight, self.width())
        super().setText(elided)
        self.setToolTip(self._full_text)  # Show full text on hover
    
    def resizeEvent(self, event):
        """Re-elide text when widget is resized"""
        super().resizeEvent(event)
        self._updateText()


class WidgetSetupMixin:
    """Mixin class for widget setup methods"""
    
    def _layout_image_widget_elements(self):
        """Helper function to layout image widget elements dynamically"""
        if not hasattr(self, 'images_widget'):
            return
            
        widget_width = self.images_widget.width()
        widget_height = self.images_widget.height()
        
        # Image label uses 85% of vertical space at top (reduced from 90% to make room for button)
        image_height = int(widget_height * 0.85)
        self.display_image_label.setGeometry(0, 0, widget_width, image_height)
        
        # Update displayed image if any
        if hasattr(self, 'loaded_images') and self.loaded_images:
            current_image = self.loaded_images[self.current_image_index]
            if current_image:
                pixmap = QPixmap()
                pixmap.loadFromData(current_image)
                # Use KeepAspectRatioByExpanding to fill space and crop if needed
                scaled_pixmap = pixmap.scaled(
                    self.display_image_label.width(),
                    self.display_image_label.height(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
                self.display_image_label.setPixmap(scaled_pixmap)
        
        # Bottom area for controls (remaining 15%)
        button_area_top = image_height
        button_area_height = widget_height - image_height
        button_size = int(30 * self.dpi_scale)
        
        # Split bottom area in half - top half for counter and nav buttons, bottom half for toggle button
        half_button_area = button_area_height // 2
        
        # Center navigation buttons and counter vertically in the top half of button area
        button_y = button_area_top + (half_button_area - button_size) // 2
        
        self.prev_image_button.setGeometry(10, button_y, button_size, button_size)
        self.next_image_button.setGeometry(widget_width - button_size - 10, button_y, button_size, button_size)
        
        image_label_size = int(20 * self.dpi_scale)
        self.image_counter_label.setFixedSize(image_label_size * 4, image_label_size)
        counter_width = self.image_counter_label.width()
        counter_x = (widget_width - counter_width) // 2
        counter_y = button_area_top + (half_button_area - self.image_counter_label.height()) // 2
        self.image_counter_label.move(counter_x, counter_y)
        
        # Position toggle rotating images button in bottom half, centered
        toggle_button_width = int(150 * self.dpi_scale)
        toggle_button_height = int(25 * self.dpi_scale)
        toggle_button_x = (widget_width - toggle_button_width) // 2
        toggle_button_y = button_area_top + half_button_area + (half_button_area - toggle_button_height) // 2
        self.toggle_rotating_images_button.setGeometry(toggle_button_x, toggle_button_y, toggle_button_width, toggle_button_height)
    
    def _layout_server_info_labels(self):
        """Helper function to layout server info labels dynamically"""
        if not hasattr(self, 'server_country_label'):
            return
        
        self.server_info_title.adjustSize()
        self.server_country_label.adjustSize()
        self.server_region_label.adjustSize()
        self.server_city_label.adjustSize()

        self.server_info_layout.setContentsMargins(10, 10, 10, 10)
        
        self.server_info_title.move(
            (self.server_info_widget.width() - self.server_info_title.width()) // 2,
            10
        )
        self.server_country_label.move(10, int(1/3 * self.server_info_widget.height()) - self.server_country_label.height())
        self.server_region_label.move(10, int(2/3 * self.server_info_widget.height() - self.server_region_label.height()))
        self.server_city_label.move(10, int(self.server_info_widget.height() - self.server_city_label.height()))
        # Push labels to the top
        self.server_info_layout.addStretch()

    def _layout_console_widget_elements(self):
        """Helper function to layout console widget elements dynamically"""
        if not hasattr(self, 'console_text_area'):
            return
        
        widget_width = self.main_console_widget.width()
        widget_height = self.main_console_widget.height()
        
        # Button dimensions
        button_width = int(100 * self.dpi_scale)
        button_height = int(30 * self.dpi_scale)
        button_spacing = int(10 * self.dpi_scale)
        margin = 10
        
        # Position buttons on the right side, stacked vertically
        button_x = widget_width - button_width - margin
        
        self.clear_console_button.setGeometry(
            button_x, 
            margin, 
            button_width, 
            button_height
        )
        
        self.copy_console_button.setGeometry(
            button_x, 
            margin + button_height + button_spacing, 
            button_width, 
            button_height
        )
        
        self.set_log_dir_button.setGeometry(
            button_x, 
            margin + 2 * (button_height + button_spacing), 
            button_width, 
            button_height
        )
        
        # Console text area takes the remaining space on the left
        console_width = button_x - 2 * margin
        self.console_text_area.setGeometry(
            margin, 
            margin, 
            console_width, 
            widget_height - 2 * margin
        )

    def _update_widget_sizes(self):
        """Update all widget sizes when window is resized"""
        # Update title bar width
        self.title_bar.setFixedWidth(self.width())
        
        # Update main widget size
        self.main_widget.setGeometry(0, int(30 * self.dpi_scale), 
                                    self.width(), 
                                    self.height() - int(30 * self.dpi_scale))
        
        # Update all child widgets
        margin = 10
        title_bar_height = int(30 * self.dpi_scale)
        main_width = self.main_widget.width()
        main_height = self.main_widget.height()
        
        # Calculate sizes
        images_width = (main_width - 3 * margin) * 3 // 4
        images_height = (main_height - 3 * margin) * 3 // 4
        sidebar_width = main_width - images_width - 3 * margin
        sidebar_top_height = images_height
        sidebar_bottom_height = main_height - images_height - 3 * margin
        console_height = sidebar_bottom_height
        
        # Update widget geometries
        self.images_widget.setGeometry(margin, margin, images_width, images_height)
        self.image_description_widget.setGeometry(images_width + 2 * margin, margin, 
                                                 sidebar_width, sidebar_top_height)
        self.server_info_widget.setGeometry(images_width + 2 * margin, 
                                           images_height + 2 * margin, 
                                           sidebar_width, sidebar_bottom_height)
        self.main_console_widget.setGeometry(margin, images_height + 2 * margin, 
                                            images_width, console_height)
        
        # Layout image widget elements
        self._layout_image_widget_elements()
        
        # Layout server info labels
        self._layout_server_info_labels()

        # Layout console widget elements
        self._layout_console_widget_elements()
    
    def setup_title_bar(self):
        """Setup custom title bar with close, minimize, maximize buttons"""
        style = {
            "styles": {
                "#titleBar": {
                    "background-color": COLORS['titlebar'],
                    "border-bottom": f"1px solid {COLORS['border']}"
                },
                "#titleBarLabel": {
                    "color": COLORS['text'],
                    "font-size": f"{12 * self.dpi_scale}px",
                    "font-weight": "bold"
                },
                "QPushButton": {
                    "background-color": COLORS['button_bg'],
                    "color": COLORS['button_text_active'],
                    "border": "none",
                    "font-size": f"{12 * self.dpi_scale}px",
                    "width": f"{30 * self.dpi_scale}px",
                    "height": f"{20 * self.dpi_scale}px",
                    "border-radius": f"{3 * self.dpi_scale}px"
                },
                "QPushButton:hover": {
                    "background-color": COLORS['button_hover']
                },
                "QPushButton#closeButton": {
                    "background-color": "#ff5c5c",
                    "color": "#ffffff",
                },
                "QPushButton#closeButton:hover": {
                    "background-color": "#ff1e1e"
                },
                "QPushButton:pressed": {
                    "background-color": COLORS['button_inactive']
                },
                "QPushButton:disabled": {
                    "color": COLORS['button_text_inactive'],
                    "background-color": COLORS['button_inactive']
                }
            }
        }
        qss = convert_style_to_qss(style)
        self.title_bar = QWidget(self)
        self.title_bar.setFixedHeight(int(30 * self.dpi_scale))
        self.title_bar.setFixedWidth(self.width())
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setMouseTracking(True)

        # Create layout and attach it to the widget
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 5, 0)
        title_layout.setSpacing(10)

        # Put a small square with the application icon on the left
        self.app_icon_label = QLabel(self.title_bar)
        self.app_icon_label.setFixedSize(int(20 * self.dpi_scale), int(20 * self.dpi_scale))
        pixmap = QPixmap(APP_ICON_PATH)
        scaled_pixmap = pixmap.scaled(
            self.app_icon_label.width(),
            self.app_icon_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.app_icon_label.setPixmap(scaled_pixmap)
        title_layout.addWidget(self.app_icon_label)

        # Create label
        self.title_label = ElidedLabel(f"Franktorio's Research Scanner", self.title_bar)
        self.title_label.setObjectName("titleBarLabel")
        self.title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        # Create font and adjust letter spacing
        font = QFont("OCR A Extended", int(12 * self.dpi_scale), QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.6 * self.dpi_scale)  # spacing in pixels

        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_layout.addWidget(self.title_label)

        # Create <> to open detailed console for debugging
        self.debug_console_button = QPushButton("<>", self.title_bar)
        self.debug_console_button.setFixedSize(int(25 * self.dpi_scale), int(20 * self.dpi_scale))
        title_layout.addWidget(self.debug_console_button)

        # Create Start Scan button
        self.start_scan_button = QPushButton("Start Scan", self.title_bar)
        self.start_scan_button.setMinimumWidth(int(70 * self.dpi_scale))
        self.start_scan_button.setFixedHeight(int(20 * self.dpi_scale))
        title_layout.addWidget(self.start_scan_button)

        # Create Stop Scan button
        self.stop_scan_button = QPushButton("Stop Scan", self.title_bar)
        self.stop_scan_button.setMinimumWidth(int(70 * self.dpi_scale))
        self.stop_scan_button.setFixedHeight(int(20 * self.dpi_scale))
        title_layout.addWidget(self.stop_scan_button)

        # Create Persistent Window button
        self.persistent_window_button = QPushButton("Persistent Window: OFF", self.title_bar)
        self.persistent_window_button.setMinimumWidth(int(140 * self.dpi_scale))
        self.persistent_window_button.setFixedHeight(int(20 * self.dpi_scale))
        title_layout.addWidget(self.persistent_window_button)
        
        # Create X button on right side
        self.close_button = QPushButton("X", self.title_bar)
        self.close_button.clicked.connect(self.close)
        self.close_button.setFixedSize(int(20 * self.dpi_scale), int(20 * self.dpi_scale))
        self.close_button.setObjectName("closeButton")
        title_layout.addWidget(self.close_button)
        self.close_button.clicked.connect(self._exit_button_clicked)

        self.title_bar.setStyleSheet(qss)
        self.title_bar.show()
    
    def setup_main_widget(self):
        """Setup main widget area below title bar"""
        style = {
            "styles": {
                "#mainWidget": {
                    "background-color": COLORS['background']
                }
            }
        }
        qss = convert_style_to_qss(style)
        self.main_widget = QWidget(self)
        self.main_widget.setGeometry(0, int(30 * self.dpi_scale), self.width(), self.height() - int(30 * self.dpi_scale))
        self.main_widget.setObjectName("mainWidget")
        self.main_widget.setStyleSheet(qss)
        self.main_widget.setMouseTracking(True)
        self.main_widget.show()
    
    def setup_images_widget(self):
        """Setup image display area"""
        style = {
            "styles": {
                "#imagesWidget": {
                    "background-color": COLORS['background'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px"
                },
                "#imagesWidget QLabel": {
                    "color": COLORS['text'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "5px"
                },
                "#imagesWidget QPushButton": {
                    "background-color": COLORS['button_bg'],
                    "color": COLORS['button_text_active'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "5px",
                    "padding": "5px"
                },
                "#imagesWidget QPushButton:hover": {
                    "background-color": COLORS['button_hover']
                },
                "#imagesWidget QPushButton:pressed": {
                    "background-color": COLORS['button_inactive']
                },
                "#imagesWidget QLabel#imageCounterLabel": {
                    "background-color": COLORS['surface_light'],
                    "color": COLORS['text'],
                    "border": "none",
                    "padding": "3px"
                }
            }
        }
        qss = convert_style_to_qss(style)
        self.images_widget = QWidget(self.main_widget)
        self.images_widget.setGeometry(10, 10, (self.main_widget.width() - 20) * 3 // 4, (self.main_widget.height() - 20) * 3 // 4)
        self.images_widget.setObjectName("imagesWidget")
        self.images_widget.setStyleSheet(qss)
        self.images_widget.setMouseTracking(True)
        self.images_widget.show()

        # Add 1 big image label to cycle through images like a slideshow
        self.current_image_index = 0
        self.loaded_images = []

        self.display_image_label = QLabel("No image to display...", self.images_widget)
        self.display_image_label.setAlignment(Qt.AlignCenter)

        # Add image counter label
        font = QFont("Segoe UI", int(11 * self.dpi_scale))
        self.image_counter_label = QLabel("0/0", self.images_widget)
        self.image_counter_label.setObjectName("imageCounterLabel")
        self.image_counter_label.setFont(font)
        self.image_counter_label.setAlignment(Qt.AlignCenter)

        # Add back and forward buttons to cycle through images
        self.prev_image_button = QPushButton("<", self.images_widget)
        self.next_image_button = QPushButton(">", self.images_widget)
        
        # Add toggle rotating images button
        self.toggle_rotating_images_button = QPushButton("Rotating Images: OFF", self.images_widget)
        toggle_font = QFont("Segoe UI", int(9 * self.dpi_scale))
        self.toggle_rotating_images_button.setFont(toggle_font)
        
        # Layout the image widget elements
        self._layout_image_widget_elements()
        
    
    def setup_image_description_widget(self):
        """Setup image description area"""
        style = {
            "styles": {
                "#imageDescriptionWidget": {
                    "background-color": COLORS['surface'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px"
                },
                "#imageDescriptionWidget QLabel": {
                    "color": COLORS['text'],
                    "border": "none",
                    "padding": "5px"
                },
                "#imageDescriptionWidget QPushButton": {
                    "background-color": COLORS['button_bg'],
                    "color": COLORS['button_text_active'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "5px",
                    "padding": "5px",
                    "font-size": f"{11 * self.dpi_scale}px"
                },
                "#imageDescriptionWidget QPushButton:hover": {
                    "background-color": COLORS['button_hover']
                },
                "#imageDescriptionWidget QPushButton:pressed": {
                    "background-color": COLORS['button_inactive']
                }
            }
        }
        qss = convert_style_to_qss(style)
        self.image_description_widget = QWidget(self.main_widget)
        self.image_description_widget.setGeometry((self.main_widget.width() - 20) * 3 // 4 + 20, 10, (self.main_widget.width() - 20) // 4 - 10, (self.main_widget.height() - 20) * 3 // 4)
        self.image_description_widget.setObjectName("imageDescriptionWidget")
        self.image_description_widget.setStyleSheet(qss)
        self.image_description_widget.setMouseTracking(True)
        self.image_description_widget.show()

        font = QFont("Segoe UI", int(11 * self.dpi_scale))

        # Create a vertical layout for better space management
        layout = QVBoxLayout(self.image_description_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Copy room name button
        self.copy_room_name_button = QPushButton("Copy Room Name", self.image_description_widget)
        self.copy_room_name_button.setFont(font)
        self.copy_room_name_button.setMinimumHeight(int(25 * self.dpi_scale))
        self.copy_room_name_button.clicked.connect(self._copy_room_name_to_clipboard)
        layout.addWidget(self.copy_room_name_button)

        # Room name label
        self.room_name_label = QLabel("<b>Room:</b> N/A", self.image_description_widget)
        self.room_name_label.setFont(font)
        self.room_name_label.setWordWrap(True)
        self.room_name_label.setMinimumHeight(int(30 * self.dpi_scale))
        layout.addWidget(self.room_name_label)

        # Room type label
        self.room_type_label = QLabel("<b>Type:</b> N/A", self.image_description_widget)
        self.room_type_label.setFont(font)
        self.room_type_label.setWordWrap(True)
        self.room_type_label.setMinimumHeight(int(30 * self.dpi_scale))
        layout.addWidget(self.room_type_label)

        # Description label (takes more space)
        self.room_description_label = QLabel("<b>Description:</b> N/A", self.image_description_widget)
        self.room_description_label.setFont(font)
        self.room_description_label.setWordWrap(True)
        self.room_description_label.setMinimumHeight(int(60 * self.dpi_scale))
        self.room_description_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(self.room_description_label, 1)  # Stretch factor of 1

        # Tags label
        self.room_tags_label = QLabel("<b>Tags:</b> N/A", self.image_description_widget)
        self.room_tags_label.setFont(font)
        self.room_tags_label.setWordWrap(True)
        self.room_tags_label.setMinimumHeight(int(30 * self.dpi_scale))
        layout.addWidget(self.room_tags_label)

        # Add spacer at the bottom to push everything up
        layout.addStretch()

    def _copy_room_name_to_clipboard(self):
        """Copy the room name to clipboard"""
        text = self.room_name_label.text()
        # Split by whitespace and get index 1 (the actual room name after "Room:")
        parts = text.split()
        if len(parts) > 1:
            room_name = parts[1]
            clipboard = QApplication.clipboard()
            clipboard.setText(room_name)
            self.copy_room_name_button.setText("Copied!")
            self.copy_room_name_button.setEnabled(False)

        def _reset_button_text():
            """Reset button text after a delay"""
            threading.Event().wait(1.5)
            self.copy_room_name_button.setEnabled(True)
            self.copy_room_name_button.setText("Copy Room Name")

        # Make a small thread to change button text temporarily
        threading.Thread(target=_reset_button_text, daemon=True).start()


    def setup_server_information_widget(self):
        """Setup server information area"""
        style = {
            "styles": {
                "#serverInfoWidget": {
                    "background-color": COLORS['surface_light'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px"
                },
                "#serverInfoWidget QLabel": {
                    "color": COLORS['text'],
                    "border":  f"1px solid {COLORS['border']}",
                    "border-radius": "5px"
                },
                "#serverInfoTitle QLabel": {
                    "padding-bottom": "5px"
                }
            }
        }
        qss = convert_style_to_qss(style)
        self.server_info_widget = QWidget(self.main_widget)
        self.server_info_widget.setGeometry((self.main_widget.width() - 20) * 3 // 4 + 20, (self.main_widget.height() - 20) * 3 // 4 + 20, (self.main_widget.width() - 20) // 4 - 10, (self.main_widget.height() - 20) // 4 - 10)
        self.server_info_widget.setObjectName("serverInfoWidget")
        self.server_info_widget.setStyleSheet(qss)
        self.server_info_widget.setMouseTracking(True)
        self.server_info_widget.show()

        font = QFont("Segoe UI", int(11 * self.dpi_scale))

        # Setup four labels to represent server info
        self.server_info_layout = QVBoxLayout(self.server_info_widget)

        self.server_info_title = ElidedLabel("<b>Server Information</b>", self.server_info_widget)
        self.server_info_title.setFont(font)
        self.server_info_title.setObjectName("serverInfoTitle")
        self.server_info_title.setAlignment(Qt.AlignCenter)
        self.server_info_layout.addWidget(self.server_info_title)

        self.server_country_label = ElidedLabel("<b>Country:</b> N/A", self.server_info_widget)
        self.server_country_label.setFont(font)
        self.server_info_layout.addWidget(self.server_country_label)

        self.server_region_label = ElidedLabel("<b>Region:</b> N/A", self.server_info_widget)
        self.server_region_label.setFont(font)
        self.server_info_layout.addWidget(self.server_region_label)

        self.server_city_label = ElidedLabel("<b>City:</b> N/A", self.server_info_widget)
        self.server_city_label.setFont(font)
        self.server_info_layout.addWidget(self.server_city_label)
        
        # Layout the server info labels
        self._layout_server_info_labels()

    def setup_main_console_widget(self):
        """Setup main console area"""
        style = {
            "styles": {
                "#mainConsoleWidget": {
                    "background-color": COLORS['surface'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px"
                },
                "#mainConsoleWidget QTextEdit": {
                    "background-color": COLORS['surface'],
                    "color": COLORS['text'],
                    "padding": "1px",
                    "border": "none",
                    "QScrollBar": {
                        "display": "none"
                    }
                },
                "#mainConsoleWidget QScrollBar": {
                    "width": "0px",
                    "height": "0px"
                },
                "#mainConsoleWidget QPushButton": {
                    "background-color": COLORS['button_bg'],
                    "color": COLORS['button_text_active'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": f"{5 * self.dpi_scale}px",
                    "padding": "5px",
                    "font-size": f"{10 * self.dpi_scale}px",
                    "font-weight": "500"
                },
                "#mainConsoleWidget QPushButton:hover": {
                    "background-color": COLORS['button_hover']
                },
                "#mainConsoleWidget QPushButton:pressed": {
                    "background-color": COLORS['button_inactive']
                },
                "#mainConsoleWidget QPushButton:disabled": {
                    "color": COLORS['button_text_inactive'],
                    "background-color": COLORS['button_inactive']
                }
            }
        }
        qss = convert_style_to_qss(style)
        self.main_console_widget = QWidget(self.main_widget)
        self.main_console_widget.setGeometry(10, (self.main_widget.height() - 20) * 3 // 4 + 20, (self.main_widget.width() - 20) * 3 // 4, (self.main_widget.height() - 20) // 4 - 10)
        self.main_console_widget.setObjectName("mainConsoleWidget")
        self.main_console_widget.setStyleSheet(qss)
        self.main_console_widget.setMouseTracking(True)
        self.main_console_widget.show()

        font = QFont("Segoe UI", int(10 * self.dpi_scale))

        # Setup console text area
        self.console_text_area = QTextEdit(f"Scanner version: {VERSION}", self.main_console_widget)
        self.console_text_area.setFont(font)
        self.console_text_area.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.console_text_area.setReadOnly(True)

        # Create console control buttons
        self.clear_console_button = QPushButton("Clear", self.main_console_widget)
        self.clear_console_button.setFont(font)

        self.copy_console_button = QPushButton("Copy", self.main_console_widget)
        self.copy_console_button.setFont(font)

        # Determine button text based on current log path
        from src.app.user_data.appdata import get_value_from_config
        current_log_path = get_value_from_config("set_log_path", "")
        button_text = "Remove Log Dir" if current_log_path else "Set Log Dir"
        self.set_log_dir_button = QPushButton(button_text, self.main_console_widget)
        self.set_log_dir_button.setFont(font)
        
        # Layout console elements
        self._layout_console_widget_elements()

    def _exit_button_clicked(self):
        """Handle exit button click"""
        self.close()
