# Franktorio Research Scanner
# Widget Setup Methods
# December 2025

from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from .colors import COLORS, convert_style_to_qss


class WidgetSetupMixin:
    """Mixin class for widget setup methods"""
    
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

        # Create label
        self.title_label = QLabel("Franktorio's Research Scanner", self.title_bar)
        self.title_label.setObjectName("titleBarLabel")

        # Create font and adjust letter spacing
        font = QFont("OCR A Extended", int(12 * self.dpi_scale), QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.6 * self.dpi_scale)  # spacing in pixels

        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_layout.addWidget(self.title_label)

        # Create Start Scan button
        self.start_scan_button = QPushButton("Start Scan", self.title_bar)
        self.start_scan_button.setFixedSize(int(80 * self.dpi_scale), int(20 * self.dpi_scale))
        title_layout.addWidget(self.start_scan_button)

        # Create Stop Scan button
        self.stop_scan_button = QPushButton("Stop Scan", self.title_bar)
        self.stop_scan_button.setFixedSize(int(80 * self.dpi_scale), int(20 * self.dpi_scale))
        title_layout.addWidget(self.stop_scan_button)

        # Create Persisten Window button
        self.persistent_window_button = QPushButton("Persistent Window", self.title_bar)
        self.persistent_window_button.setFixedSize(int(120 * self.dpi_scale), int(20 * self.dpi_scale))
        title_layout.addWidget(self.persistent_window_button)
        
        # Create X button on right side
        self.close_button = QPushButton("X", self.title_bar)
        self.close_button.clicked.connect(self.close)
        self.close_button.setFixedSize(int(20 * self.dpi_scale), int(20 * self.dpi_scale))
        self.close_button.setObjectName("closeButton")
        title_layout.addWidget(self.close_button)

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
                    "background-color": COLORS['surface_light'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px"
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
    
    def setup_image_description_widget(self):
        """Setup image description area"""
        style = {
            "styles": {
                "#imageDescriptionWidget": {
                    "background-color": COLORS['surface'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px"
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

        # Setup labels to represent

    def setup_server_information_widget(self):
        """Setup server information area"""
        style = {
            "styles": {
                "#serverInfoWidget": {
                    "background-color": COLORS['surface_light'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px"
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

    def setup_main_console_widget(self):
        """Setup main console area"""
        style = {
            "styles": {
                "#mainConsoleWidget": {
                    "background-color": COLORS['surface'],
                    "border": f"1px solid {COLORS['border']}",
                    "border-radius": "10px"
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
