"""
Existential Graph Graphics Items for EGRF v3.0

Implements proper rendering for EGRF v3.0 layout data with correct
Peirce conventions: thin black cuts, plain text predicates, heavy line entities.
"""

import sys
import os
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path

from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsEllipseItem, QGraphicsRectItem, 
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsPathItem
)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QFont, QColor, QPen, QBrush, QPainter, QPainterPath
)


class EGGraphicsItem(QGraphicsItem):
    """Base class for Existential Graph elements."""
    
    def __init__(self, element_id: str, layout_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.element_id = element_id
        self.layout_data = layout_data
        
        # Initialize default values first
        self.width = 100
        self.height = 50
        self.nesting_level = 0
        
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Set position and size from layout data
        if layout_data:
            pos = layout_data.get('position', {'x': 0, 'y': 0})
            self.setPos(pos['x'], pos['y'])
            
            size = layout_data.get('size', {'width': 100, 'height': 50})
            self.width = size['width']
            self.height = size['height']
            
            self.nesting_level = layout_data.get('nesting_level', 0)
    
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter: QPainter, option, widget):
        # Default implementation - subclasses should override
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawRect(self.boundingRect())


class ContextItem(EGGraphicsItem):
    """Graphics item for EG contexts (sheet and cuts) with proper alternating shading."""
    
    def __init__(self, element_id: str, layout_data: Dict[str, Any], parent=None):
        super().__init__(element_id, layout_data, parent)
        
        # Determine context type from layout data
        self.element_type = layout_data.get('element_type', 'context')
        self.semantic_role = layout_data.get('semantic_role', '')
        self.is_sheet = (self.nesting_level == 0)
        
        # Set z-value based on nesting level 
        # Sheet should be at the bottom, cuts should be above it
        # Higher nesting levels should appear above lower ones
        if self.is_sheet:
            self.setZValue(-100)  # Sheet at the very bottom
        else:
            # Cuts: higher nesting level = higher z-value (appear on top)
            self.setZValue(self.nesting_level)
    
    def paint(self, painter: QPainter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.is_sheet:
            # Sheet of Assertion: minimal visual presence, white background
            painter.setPen(QPen(QColor(150, 150, 150), 1))
            painter.setBrush(QBrush(QColor(255, 255, 255)))  # White (even level 0)
            painter.drawRect(self.boundingRect())
            
            # Add label in top-left corner
            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(10, 20, "Sheet of Assertion")
            
        else:
            # Cut: thin black line oval with alternating shading
            # Determine background color based on nesting level
            if self.nesting_level % 2 == 0:
                # Even level: white
                fill_color = QColor(255, 255, 255)
            else:
                # Odd level: light gray
                fill_color = QColor(240, 240, 240)
            
            # Draw cut as oval with thin black line
            painter.setPen(QPen(QColor(0, 0, 0), 1))  # Thin black line
            painter.setBrush(QBrush(fill_color))
            painter.drawEllipse(self.boundingRect())
            
            # Add semantic role label for debugging
            if self.semantic_role:
                painter.setPen(QPen(QColor(100, 100, 100)))
                painter.setFont(QFont("Arial", 8))
                label_text = f"L{self.nesting_level}"
                if 'Universal' in self.semantic_role:
                    label_text += " ∀"
                elif 'Existential' in self.semantic_role:
                    label_text += " ∃"
                elif 'Implication' in self.semantic_role:
                    label_text += " →"
                elif 'Consequent' in self.semantic_role:
                    label_text += " ⊃"
                painter.drawText(5, 15, label_text)


class PredicateItem(EGGraphicsItem):
    """Graphics item for EG predicates with plain text and invisible oval boundaries."""
    
    def __init__(self, element_id: str, layout_data: Dict[str, Any], parent=None):
        super().__init__(element_id, layout_data, parent)
        
        # Extract predicate name from layout data
        self.predicate_name = layout_data.get('name', 'P')
        
        # Predicates appear above contexts
        self.setZValue(10)
        
        # Get hook points from layout data
        self.hook_points = layout_data.get('hook_points', [])
    
    def get_hook_point(self, side: str = 'left') -> QPointF:
        """Get a hook connection point by side."""
        for hook in self.hook_points:
            if hook.get('side') == side:
                # Convert to local coordinates
                return QPointF(hook['x'] - self.pos().x(), hook['y'] - self.pos().y())
        
        # Default to center if no hook found
        return QPointF(self.width / 2, self.height / 2)
    
    def get_global_hook_point(self, side: str = 'left') -> QPointF:
        """Get a hook connection point in global coordinates."""
        for hook in self.hook_points:
            if hook.get('side') == side:
                return QPointF(hook['x'], hook['y'])
        
        # Default to global center
        return self.pos() + QPointF(self.width / 2, self.height / 2)
    
    def paint(self, painter: QPainter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw invisible oval boundary for debugging (normally invisible)
        if False:  # Set to True for debugging
            painter.setPen(QPen(QColor(200, 200, 200), 1, Qt.DashLine))
            painter.setBrush(QBrush(Qt.NoBrush))
            painter.drawEllipse(self.boundingRect())
        
        # Draw predicate name as plain text (no background)
        # Text should have the background shading of the area it resides in
        painter.setPen(QPen(QColor(0, 0, 0)))  # Black text
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        
        # Center the text in the bounding rectangle
        text_rect = self.boundingRect()
        painter.drawText(text_rect, Qt.AlignCenter, self.predicate_name)
        
        # Draw hook points for debugging
        if False:  # Set to True for debugging
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            for hook in self.hook_points:
                local_x = hook['x'] - self.pos().x()
                local_y = hook['y'] - self.pos().y()
                painter.drawEllipse(QPointF(local_x, local_y), 3, 3)


class EntityItem(EGGraphicsItem):
    """Graphics item for EG entities (lines of identity) with heavy black lines and proper connections."""
    
    def __init__(self, element_id: str, layout_data: Dict[str, Any], parent=None):
        super().__init__(element_id, layout_data, parent)
        
        # Extract entity information
        self.entity_name = layout_data.get('name', '')
        self.entity_type = layout_data.get('entity_type', 'constant')
        
        # Get line segments from layout data
        self.line_segments = layout_data.get('line_segments', [])
        self.connected_predicates = layout_data.get('connected_predicates', [])
        
        # Entities appear above contexts but below predicates
        self.setZValue(5)
    
    def paint(self, painter: QPainter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw line of identity as heavy line (thicker than cut lines)
        painter.setPen(QPen(QColor(0, 0, 0), 3))  # Heavy black line
        
        if self.line_segments:
            # Draw each line segment
            for segment in self.line_segments:
                if segment.get('type') == 'line':
                    points = segment.get('points', [])
                    if len(points) >= 2:
                        for i in range(len(points) - 1):
                            start_point = QPointF(
                                points[i]['x'] - self.pos().x(),
                                points[i]['y'] - self.pos().y()
                            )
                            end_point = QPointF(
                                points[i + 1]['x'] - self.pos().x(),
                                points[i + 1]['y'] - self.pos().y()
                            )
                            painter.drawLine(start_point, end_point)
        else:
            # Default: draw horizontal line
            y_center = self.height / 2
            painter.drawLine(QPointF(0, y_center), QPointF(self.width, y_center))
        
        # Add entity label if it's a universal variable
        if self.entity_name and self.entity_type == 'variable':
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.setFont(QFont("Arial", 10, QFont.Italic))
            # Position label near the start of the line
            painter.drawText(QPointF(5, 15), f"∀{self.entity_name}")


class ConnectionManager:
    """Manages connections between entities and predicates using EGRF v3.0 data."""
    
    def __init__(self):
        self.connections = {}  # element_id -> layout_data
    
    def add_element(self, element_id: str, layout_data: Dict[str, Any]):
        """Add an element with its layout data."""
        self.connections[element_id] = layout_data
    
    def get_connected_elements(self, element_id: str) -> List[str]:
        """Get all elements connected to the given element."""
        if element_id not in self.connections:
            return []
        
        layout_data = self.connections[element_id]
        return layout_data.get('connected_predicates', [])
    
    def update_connections(self, layout_data: Dict[str, Any]):
        """Update all connection data."""
        self.connections = layout_data

