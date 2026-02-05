# Franktorio Research Scanner
# Window Controls Mixin
# December 2025

from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtWidgets import QApplication
from config.vars import MAX_HEIGHT, MAX_WIDTH, MIN_HEIGHT, MIN_WIDTH, RESIZE_MARGIN

class WindowControlsMixin:
    """Mixin class for window dragging and resizing functionality"""
    
    def init_window_controls(self):
        """Initialize window control state variables"""
        # Window dragging and resizing state
        self.dragging = False
        self.resizing = False
        self.resize_edge = None
        self.drag_position = QPoint()
        self.resize_margin = RESIZE_MARGIN
        self.initial_geometry = None  # Store initial geometry for resize
        self.cursor_override_active = False  # Track if we've set an override cursor

        # Enable mouse tracking for cursor updates
        self.setMouseTracking(True)
    
    def install_title_bar_event_filter(self):
        """Install event filter on title bar to handle resize from top"""
        if hasattr(self, 'title_bar'):
            self.title_bar.installEventFilter(self)

    def mousePressEvent(self, event):
        """Handle mouse press for dragging and resizing"""
        if event.button() == Qt.LeftButton:
            # Check if clicking on edge for resizing first (takes priority)
            edge = self._get_resize_edge(event.pos())
            if edge:
                self.resizing = True
                self.resize_edge = edge
                self.drag_position = event.globalPos()
                self.initial_geometry = self.geometry()  # Store initial geometry
                event.accept()
                return
            
            # Then check for title bar dragging
            if self.title_bar.geometry().contains(event.pos()):
                self.dragging = True
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
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
            # Check for resize edge first (takes priority)
            edge = self._get_resize_edge(event.pos())
            if edge:
                self._set_resize_cursor(edge)
            else:
                if self.cursor_override_active:
                    QApplication.restoreOverrideCursor()
                    self.cursor_override_active = False
        
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop dragging/resizing"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self.resize_edge = None
            self.initial_geometry = None
            if self.cursor_override_active:
                QApplication.restoreOverrideCursor()
                self.cursor_override_active = False
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
        """Set appropriate cursor for resize edge using override cursor"""
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
        cursor = cursor_map.get(edge, Qt.ArrowCursor)
        
        # Use override cursor to ensure it shows even over child widgets
        if self.cursor_override_active:
            QApplication.restoreOverrideCursor()
        QApplication.setOverrideCursor(cursor)
        self.cursor_override_active = True

    def _resize_window(self, global_pos):
        """Resize window so edge moves to where the mouse is"""
        if not self.initial_geometry:
            return
        
        geo = self.geometry()
        initial_geo = self.initial_geometry
        min_width = int(MIN_WIDTH * self.dpi_scale)
        min_height = int(MIN_HEIGHT * self.dpi_scale)
        max_width = MAX_WIDTH
        max_height = MAX_HEIGHT
        
        # Calculate where the edge should be based on mouse position
        if 'left' in self.resize_edge:
            new_left = global_pos.x()
            new_width = initial_geo.right() - new_left
            if min_width <= new_width <= max_width:
                geo.setLeft(new_left)
        
        if 'right' in self.resize_edge:
            new_right = global_pos.x()
            new_width = new_right - initial_geo.left()
            if min_width <= new_width <= max_width:
                geo.setRight(new_right)
        
        if 'top' in self.resize_edge:
            new_top = global_pos.y()
            new_height = initial_geo.bottom() - new_top
            if min_height <= new_height <= max_height:
                geo.setTop(new_top)
        
        if 'bottom' in self.resize_edge:
            new_bottom = global_pos.y()
            new_height = new_bottom - initial_geo.top()
            if min_height <= new_height <= max_height:
                geo.setBottom(new_bottom)
        
        self.setGeometry(geo)
        self._update_widget_sizes()
    
    def eventFilter(self, obj, event):
        """Event filter to handle mouse events on title bar"""
        if obj == self.title_bar:
            if event.type() == QEvent.MouseMove:
                # Convert title bar position to window position
                window_pos = self.title_bar.mapTo(self, event.pos())
                edge = self._get_resize_edge(window_pos)
                
                if self.resizing and self.resize_edge:
                    self._resize_window(event.globalPos())
                    return True
                elif edge:
                    self._set_resize_cursor(edge)
                    return False  # Let title bar handle its own events too
                else:
                    if self.cursor_override_active:
                        QApplication.restoreOverrideCursor()
                        self.cursor_override_active = False
                    
            elif event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    # Convert title bar position to window position
                    window_pos = self.title_bar.mapTo(self, event.pos())
                    edge = self._get_resize_edge(window_pos)
                    
                    if edge:
                        self.resizing = True
                        self.resize_edge = edge
                        self.drag_position = event.globalPos()
                        self.initial_geometry = self.geometry()
                        return True  # Consume event
                        
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton and self.resizing:
                    self.resizing = False
                    self.resize_edge = None
                    self.initial_geometry = None
                    if self.cursor_override_active:
                        QApplication.restoreOverrideCursor()
                        self.cursor_override_active = False
                    return True
        
        return super().eventFilter(obj, event)
