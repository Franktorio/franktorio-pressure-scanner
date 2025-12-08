# Franktorio Research Scanner
# GUI Module
# December 2025

import sys
import json
import PyQt5
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy, QDialog, QInputDialog,
    QLineEdit, QComboBox, QCheckBox, QRadioButton, QSlider, QProgressBar,
    QSpinBox, QDoubleSpinBox, QGroupBox, QTabWidget, QListWidget, QTableWidget,
    QTableWidgetItem, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QCursor

from config.vars import MIN_WIDTH, MIN_HEIGHT, RESIZE_MARGIN

# Color Palette
COLORS = {
    'background': "#1f1f1f",          # Main background
    'surface': "#252525",             # Surface/panel color
    'surface_light': "#333333",       # Lighter surface variant
    'titlebar': '#1e1e1e',            # Title bar background
    'border': "#8F8F8F",              # Border color
    'accent': '#5a5a5a',              # Accent color
    'text': '#e0e0e0',                # Primary text
    'text_secondary': '#b0b0b0',      # Secondary text
    'button_bg': '#3a3a3a',           # Button background
    'button_hover': '#505050',        # Button hover background
    'button_inactive': '#2a2a2a',     # Button inactive background
    'button_text_active': '#ffffff',  # Button active text
    'button_text_inactive': '#7a7a7a',# Button inactive text
    'toggled_on': '#4caf50',          # Toggle on color
}


def convert_style_to_qss(style_dict):
    """Convert JSON style dictionary to QSS string"""
    qss = ""
    for selector, properties in style_dict["styles"].items():
        qss += f"{selector} {{\n"
        for prop, value in properties.items():
            qss += f"    {prop}: {value};\n"
        qss += "}\n\n"
    return qss


class MainWindow(QMainWindow):
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

        # Remove window frame for custom styling
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.dpi_scale = self._get_dpi_scale()

        # Window dragging and resizing state
        self.dragging = False
        self.resizing = False
        self.resize_edge = None
        self.drag_position = QPoint()
        self.resize_margin = RESIZE_MARGIN
        self.initial_geometry = None  # Store initial geometry for resize

        # Enable mouse tracking for cursor updates
        self.setMouseTracking(True)

        self.setup_title_bar()
        self.setup_main_widget()
        self.setup_images_widget()
        self.setup_image_description_widget()
        self.setup_server_information_widget()
        self.setup_main_console_widget()

    
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

    def mousePressEvent(self, event):
        """Handle mouse press for dragging and resizing"""
        if event.button() == Qt.LeftButton:
            # Check if clicking on title bar for dragging
            if self.title_bar.geometry().contains(event.pos()):
                self.dragging = True
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
                return
            
            # Check if clicking on edge for resizing
            edge = self._get_resize_edge(event.pos())
            if edge:
                self.resizing = True
                self.resize_edge = edge
                self.drag_position = event.globalPos()
                self.initial_geometry = self.geometry()  # Store initial geometry
                event.accept()
                return
        
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging, resizing, and cursor changes"""
        if self.dragging:
            # Move window
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            return
        
        if self.resizing and self.resize_edge:
            # Resize window
            self._resize_window(event.globalPos())
            event.accept()
            return
        
        # Update cursor based on position
        if not self.resizing:
            edge = self._get_resize_edge(event.pos())
            if edge:
                self._set_resize_cursor(edge)
            else:
                self.setCursor(Qt.ArrowCursor)
        
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop dragging/resizing"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self.resize_edge = None
            self.initial_geometry = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        
        super().mouseReleaseEvent(event)

    def _get_resize_edge(self, pos):
        """Determine which edge/corner the mouse is near"""
        rect = self.rect()
        margin = self.resize_margin
        
        left = pos.x() <= margin
        right = pos.x() >= rect.width() - margin
        top = pos.y() <= margin
        bottom = pos.y() >= rect.height() - margin
        
        if left and top:
            return 'top-left'
        elif right and top:
            return 'top-right'
        elif left and bottom:
            return 'bottom-left'
        elif right and bottom:
            return 'bottom-right'
        elif left:
            return 'left'
        elif right:
            return 'right'
        elif top:
            return 'top'
        elif bottom:
            return 'bottom'
        
        return None

    def _set_resize_cursor(self, edge):
        """Set appropriate cursor for resize edge"""
        cursor_map = {
            'top': Qt.SizeVerCursor,
            'bottom': Qt.SizeVerCursor,
            'left': Qt.SizeHorCursor,
            'right': Qt.SizeHorCursor,
            'top-left': Qt.SizeFDiagCursor,
            'bottom-right': Qt.SizeFDiagCursor,
            'top-right': Qt.SizeBDiagCursor,
            'bottom-left': Qt.SizeBDiagCursor
        }
        self.setCursor(cursor_map.get(edge, Qt.ArrowCursor))

    def _resize_window(self, global_pos):
        """Resize window so edge moves to where the mouse is"""
        if not self.initial_geometry:
            return
        
        geo = self.geometry()
        initial_geo = self.initial_geometry
        min_width = MIN_WIDTH
        min_height = MIN_HEIGHT
        
        # Calculate where the edge should be based on mouse position
        if 'left' in self.resize_edge:
            new_left = global_pos.x()
            new_width = initial_geo.right() - new_left
            if new_width >= min_width:
                geo.setLeft(new_left)
        
        if 'right' in self.resize_edge:
            new_right = global_pos.x()
            new_width = new_right - initial_geo.left()
            if new_width >= min_width:
                geo.setRight(new_right)
        
        if 'top' in self.resize_edge:
            new_top = global_pos.y()
            new_height = initial_geo.bottom() - new_top
            if new_height >= min_height:
                geo.setTop(new_top)
        
        if 'bottom' in self.resize_edge:
            new_bottom = global_pos.y()
            new_height = new_bottom - initial_geo.top()
            if new_height >= min_height:
                geo.setBottom(new_bottom)
        
        self.setGeometry(geo)
        self._update_widget_sizes()

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