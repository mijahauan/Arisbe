"""
EG Canvas Widget for Ergasterion Workshop

Interactive canvas widget for editing and transforming Existential Graphs.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QPoint, QRect
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

class EGCanvasWidget(QWidget):
    """Interactive canvas widget for Existential Graph editing."""
    
    # Signals
    element_selected = Signal(str)  # element_id
    element_moved = Signal(str, QPoint)  # element_id, new_position
    transformation_requested = Signal(str, str)  # transformation_type, element_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Canvas properties
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: white; border: 1px solid gray;")
        
        # Graph data
        self.current_egi = None
        self.spatial_primitives = []
        
        # Interaction state
        self.selected_element = None
        self.dragging = False
        self.drag_start = QPoint()
        self.hover_element = None
        
        # Visual settings
        self.vertex_radius = 20
        self.edge_width = 2
        self.cut_width = 3
        self.selection_color = QColor(0, 102, 204)
        self.hover_color = QColor(102, 153, 255)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
    
    def set_graph(self, egi, spatial_primitives):
        """Set the graph to display."""
        self.current_egi = egi
        self.spatial_primitives = spatial_primitives
        self.selected_element = None
        self.hover_element = None
        self.update()
    
    def paintEvent(self, event):
        """Paint the canvas."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.current_egi or not self.spatial_primitives:
            # Draw placeholder text
            painter.setPen(QPen(QColor(128, 128, 128)))
            painter.setFont(QFont("Arial", 14))
            painter.drawText(self.rect(), Qt.AlignCenter, 
                           "Load an EGIF to begin editing\n\nUse File → Load or paste EGIF in input area")
            return
        
        # Draw cuts first (background)
        self._draw_cuts(painter)
        
        # Draw edges
        self._draw_edges(painter)
        
        # Draw vertices (foreground)
        self._draw_vertices(painter)
        
        # Draw selection highlight
        if self.selected_element:
            self._draw_selection_highlight(painter)
    
    def _draw_vertices(self, painter):
        """Draw vertices."""
        if not self.current_egi:
            return
            
        for vertex in self.current_egi.V:
            primitive = self._find_primitive(vertex.id)
            if not primitive:
                continue
            
            x, y = primitive['position']
            
            # Determine colors
            fill_color = QColor(230, 243, 255)  # Light blue
            border_color = QColor(0, 102, 204)  # Dark blue
            
            if vertex.id == self.hover_element:
                fill_color = self.hover_color
            if vertex.id == self.selected_element:
                border_color = self.selection_color
                painter.setPen(QPen(border_color, 3))
            else:
                painter.setPen(QPen(border_color, 2))
            
            painter.setBrush(QBrush(fill_color))
            
            # Draw vertex circle
            painter.drawEllipse(x - self.vertex_radius, y - self.vertex_radius, 
                              self.vertex_radius * 2, self.vertex_radius * 2)
            
            # Draw label
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(x - 20, y + 5, 40, 20, Qt.AlignCenter, vertex.label)
    
    def _draw_edges(self, painter):
        """Draw edges."""
        if not self.current_egi:
            return
            
        painter.setPen(QPen(QColor(51, 51, 51), self.edge_width))
        
        for edge in self.current_egi.E:
            primitive = self._find_primitive(edge.id)
            if not primitive:
                continue
            
            # For now, draw edges as simple lines
            # In a full implementation, this would connect actual vertices
            x, y = primitive['position']
            painter.drawLine(x - 30, y, x + 30, y)
            
            # Draw edge label
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(x - 15, y - 10, edge.label)
            painter.setPen(QPen(QColor(51, 51, 51), self.edge_width))
    
    def _draw_cuts(self, painter):
        """Draw cuts."""
        if not self.current_egi:
            return
            
        painter.setPen(QPen(QColor(255, 102, 0), self.cut_width))  # Orange
        painter.setBrush(QBrush(Qt.NoBrush))  # No fill
        
        for cut in self.current_egi.Cut:
            primitive = self._find_primitive(cut.id)
            if not primitive:
                continue
            
            bounds = primitive.get('bounds')
            if bounds and len(bounds) == 4:
                x1, y1, x2, y2 = bounds
                
                # Highlight if selected or hovered
                if cut.id == self.selected_element:
                    painter.setPen(QPen(self.selection_color, self.cut_width + 1))
                elif cut.id == self.hover_element:
                    painter.setPen(QPen(self.hover_color, self.cut_width))
                else:
                    painter.setPen(QPen(QColor(255, 102, 0), self.cut_width))
                
                # Draw cut as rounded rectangle
                painter.drawRoundedRect(x1, y1, x2 - x1, y2 - y1, 10, 10)
    
    def _draw_selection_highlight(self, painter):
        """Draw selection highlight around selected element."""
        if not self.selected_element:
            return
            
        primitive = self._find_primitive(self.selected_element)
        if not primitive:
            return
        
        painter.setPen(QPen(self.selection_color, 2, Qt.DashLine))
        painter.setBrush(QBrush(Qt.NoBrush))
        
        x, y = primitive['position']
        
        # Draw selection box around element
        if primitive['element_type'] == 'vertex':
            painter.drawEllipse(x - self.vertex_radius - 5, y - self.vertex_radius - 5,
                              (self.vertex_radius + 5) * 2, (self.vertex_radius + 5) * 2)
        elif primitive['element_type'] == 'cut':
            bounds = primitive.get('bounds', [x-50, y-50, x+50, y+50])
            x1, y1, x2, y2 = bounds
            painter.drawRect(x1 - 5, y1 - 5, x2 - x1 + 10, y2 - y1 + 10)
    
    def _find_primitive(self, element_id):
        """Find spatial primitive for element ID."""
        for primitive in self.spatial_primitives:
            if primitive.get('element_id') == element_id:
                return primitive
        return None
    
    def _find_element_at_position(self, pos):
        """Find element at given position."""
        x, y = pos.x(), pos.y()
        
        # Check vertices first (smaller targets)
        if self.current_egi:
            for vertex in self.current_egi.V:
                primitive = self._find_primitive(vertex.id)
                if primitive:
                    vx, vy = primitive['position']
                    if ((x - vx) ** 2 + (y - vy) ** 2) <= self.vertex_radius ** 2:
                        return vertex.id
            
            # Check cuts
            for cut in self.current_egi.Cut:
                primitive = self._find_primitive(cut.id)
                if primitive:
                    bounds = primitive.get('bounds')
                    if bounds and len(bounds) == 4:
                        x1, y1, x2, y2 = bounds
                        if x1 <= x <= x2 and y1 <= y <= y2:
                            return cut.id
        
        return None
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            element_id = self._find_element_at_position(event.pos())
            
            if element_id:
                self.selected_element = element_id
                self.dragging = True
                self.drag_start = event.pos()
                self.element_selected.emit(element_id)
                self.update()
            else:
                self.selected_element = None
                self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move."""
        # Update hover element
        hover_element = self._find_element_at_position(event.pos())
        if hover_element != self.hover_element:
            self.hover_element = hover_element
            self.update()
        
        # Handle dragging
        if self.dragging and self.selected_element:
            # For now, just emit signal - actual movement would update spatial primitives
            self.element_moved.emit(self.selected_element, event.pos())
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
    
    def keyPressEvent(self, event):
        """Handle key press."""
        if event.key() == Qt.Key_Delete and self.selected_element:
            # Request deletion transformation
            self.transformation_requested.emit("delete", self.selected_element)
        elif event.key() == Qt.Key_Escape:
            self.selected_element = None
            self.update()
    
    def clear(self):
        """Clear the canvas."""
        self.current_egi = None
        self.spatial_primitives = []
        self.selected_element = None
        self.hover_element = None
        self.update()
