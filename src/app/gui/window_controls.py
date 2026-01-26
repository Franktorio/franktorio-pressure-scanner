# Franktorio Research Scanner
# Window Controls Mixin
# December 2025

from PyQt5.QtCore import Qt, QPoint
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

        # Enable mouse tracking for cursor updates
        self.setMouseTracking(True)

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
            # Check if mouse is on title bar first
            if self.title_bar.geometry().contains(event.pos()):
                self.setCursor(Qt.ArrowCursor)
            else:
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
