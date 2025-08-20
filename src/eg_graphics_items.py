"""
Qt Graphics Framework items for Existential Graph elements.

This module provides QGraphicsItem subclasses for each type of EG element,
replacing all custom hit detection and coordinate tracking with Qt's proven
scene-graph architecture.
"""

from typing import Optional, Dict, Any, List, Set
from PySide6.QtWidgets import (QGraphicsRectItem, QGraphicsEllipseItem, 
                               QGraphicsLineItem, QGraphicsTextItem, QGraphicsItemGroup,
                               QGraphicsItem, QGraphicsPathItem)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath
from typing import Dict, Any, Optional, List

class EGSelectionOverlay(QGraphicsPathItem):
    """
    EG-specific selection overlay that provides visual feedback and constraint enforcement.
    
    This overlay system ensures selection is constrained to valid subgraphs or exclusive areas,
    not just arbitrary Qt selection. It provides contextual visual feedback based on the
    type of selection (single element, subgraph, area, etc.).
    """
    
    def __init__(self, selection_type: str = "single"):
        super().__init__()
        self.selection_type = selection_type
        self.selected_elements: Set[str] = set()
        
        # Configure overlay appearance
        self.setZValue(1000)  # Always on top
        self.setPen(QPen(QColor(0, 120, 255, 180), 2, Qt.DashLine))  # Blue dashed outline
        self.setBrush(QBrush(QColor(0, 120, 255, 30)))  # Semi-transparent blue fill
        
        # Disable interaction (overlay only)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
    
    def update_selection(self, elements: Set[str], bounds: QRectF):
        """Update the overlay to highlight the selected elements."""
        self.selected_elements = elements
        
        # Create path based on selection type
        path = QPainterPath()
        
        if self.selection_type == "single":
            # Simple rectangle for single element
            path.addRect(bounds)
        elif self.selection_type == "subgraph":
            # Rounded rectangle for subgraph selection
            path.addRoundedRect(bounds, 8, 8)
        elif self.selection_type == "area":
            # Dotted line rectangle for area selection
            self.setPen(QPen(QColor(255, 165, 0, 180), 2, Qt.DotLine))  # Orange dotted
            self.setBrush(QBrush(QColor(255, 165, 0, 20)))  # Semi-transparent orange
            path.addRect(bounds)
        
        self.setPath(path)
        self.setVisible(True)
    
    def clear_selection(self):
        """Clear the selection overlay."""
        self.selected_elements.clear()
        self.setVisible(False)


class EGGraphicsItem(QGraphicsItem):
    """Base class for all Existential Graph graphics items with EG-specific selection."""
    
    def __init__(self, element_id: str, egi_data: Dict[str, Any]):
        super().__init__()
        self.element_id = element_id
        self.egi_data = egi_data
        self.connected_elements: Set[str] = set()  # For group-aware operations
        
        # Enable EG-constrained selection and movement
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Custom selection behavior
        self.setAcceptHoverEvents(True)
    
    def get_element_id(self) -> str:
        """Get the EGI element ID this graphics item represents."""
        return self.element_id
    
    def get_egi_data(self) -> Dict[str, Any]:
        """Get the EGI data associated with this element."""
        return self.egi_data
    
    def set_connected_elements(self, connected_ids: Set[str]):
        """Set the IDs of elements connected to this one for group operations."""
        self.connected_elements = connected_ids
    
    def get_connected_elements(self) -> Set[str]:
        """Get the IDs of elements that should move together with this one."""
        return self.connected_elements
    
    def is_valid_selection_with(self, other_elements: Set[str]) -> bool:
        """
        Check if this element can be validly selected together with other elements.
        
        EG-specific constraint: Selection must form a valid subgraph or be within
        the same logical area (cut). This prevents invalid operations like selecting
        elements across cut boundaries that would violate EG semantics.
        """
        # TODO: Implement EG-specific validation logic
        # For now, allow all selections (will be enhanced with area constraints)
        return True
    
    def hoverEnterEvent(self, event):
        """Provide visual feedback when hovering over selectable elements."""
        super().hoverEnterEvent(event)
        # TODO: Add hover highlight effect
        
    def hoverLeaveEvent(self, event):
        """Remove visual feedback when leaving selectable elements."""
        super().hoverLeaveEvent(event)
        # TODO: Remove hover highlight effect


class PredicateGraphicsItem(QGraphicsTextItem):
    """Graphics item for predicate text with EGI identity."""
    
    def __init__(self, element_id: str, egi_data: Dict[str, Any], predicate_name: str, position: tuple):
        super().__init__()
        
        # Store EGI identity (composition instead of inheritance)
        self.element_id = element_id
        self.egi_data = egi_data
        
        # Set predicate text and styling
        self.setPlainText(predicate_name)
        font = QFont("Arial", 12)
        self.setFont(font)
        self.setDefaultTextColor(QColor(0, 0, 0))  # Black text
        
        # Position the item
        x, y = position
        self.setPos(x, y)
        
        # Enable selection and movement
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        
        print(f"📝 Created PredicateGraphicsItem '{predicate_name}' at ({x:.1f}, {y:.1f})")
    
    def get_element_id(self) -> str:
        """Get the EGI element ID this graphics item represents."""
        return self.element_id


class VertexGraphicsItem(QGraphicsEllipseItem):
    """Graphics item for vertex spots with EGI identity."""
    
    def __init__(self, element_id: str, egi_data: Dict[str, Any], position: tuple, vertex_name: str = None, radius: float = 2.5):
        # Create circle at (0,0) in item coordinates - Qt will handle scene positioning
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        
        # Position the item in the scene using Qt's coordinate system
        x, y = position
        self.setPos(x, y)
        
        # Store EGI identity (composition instead of inheritance)
        self.element_id = element_id
        self.egi_data = egi_data
        self.vertex_name = vertex_name
        
        # Set vertex styling
        pen = QPen(QColor(0, 0, 0), 1)  # Black outline
        brush = QBrush(QColor(0, 0, 0))  # Black fill
        self.setPen(pen)
        self.setBrush(brush)
        
        # Add text label for vertex constant name (like "Socrates")
        print(f"🔍 DEBUG: VertexGraphicsItem received vertex_name = '{vertex_name}'")
        if vertex_name:
            from PySide6.QtWidgets import QGraphicsTextItem
            
            self.text_item = QGraphicsTextItem(vertex_name, self)
            font = QFont("Arial", 12)  # Larger font
            self.text_item.setFont(font)
            
            # Set text color to ensure visibility
            self.text_item.setDefaultTextColor(QColor(0, 0, 0))  # Black text
            
            # Position text next to vertex spot
            # Item coordinates: circle is centered at (0,0), extends from (-radius,-radius) to (+radius,+radius)
            text_x = radius + 8  # Right of the circle edge
            text_y = -6  # Slightly above center
            self.text_item.setPos(text_x, text_y)
            
            # Ensure text is on top layer
            self.text_item.setZValue(10)  # High z-value to stay on top
            
            print(f"🔍 DEBUG: Created text item '{vertex_name}' at ({text_x}, {text_y}) with font size {font.pointSize()}")
        else:
            print(f"🔍 DEBUG: No vertex_name provided, skipping text creation")
        
        # Enable selection and movement
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        
        vertex_display = f" '{vertex_name}'" if vertex_name else ""
        print(f"⚫ Created VertexGraphicsItem{vertex_display} at ({x:.1f}, {y:.1f})")
    
    def get_element_id(self) -> str:
        """Get the EGI element ID this graphics item represents."""
        return self.element_id
    
    def itemChange(self, change, value):
        """Override to enforce constraints and update EGI model on movement."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # TODO: Implement constraint validation here
            # - Check if new position violates syntactic rules
            # - Validate against area containment (vertices must stay in logical areas)
            # - Update EGI model if movement is valid
            # - Emit signal to update chiron
            print(f"🔄 Vertex {self.element_id} attempting to move to {value}")
            
        return super().itemChange(change, value)


class CutGraphicsItem(QGraphicsRectItem):
    """Graphics item for cut boundaries with containment hierarchy."""
    
    def __init__(self, element_id: str, egi_data: Dict[str, Any], bounds: tuple):
        x1, y1, x2, y2 = bounds
        super().__init__(x1, y1, x2 - x1, y2 - y1)
        
        # Store EGI identity (composition instead of inheritance)
        self.element_id = element_id
        self.egi_data = egi_data
        
        # Set cut styling - fine drawn line, no fill, ROUNDED CORNERS per Dau
        pen = QPen(QColor(0, 0, 0), 1)  # Black line
        brush = QBrush()  # No fill
        self.setPen(pen)
        self.setBrush(brush)
        
        # Dau compliance: Rounded rectangles (NOT sharp corners)
        # Set corner radius for rounded rectangle appearance
        self.corner_radius = 8.0  # Moderate rounding per Dau convention
        
        # Ensure cuts render in background (lower Z-index than ligatures)
        self.setZValue(0)  # Background layer, ligatures will be at Z=5
        
        # Enable containment - this cut can contain other items
        self.setFlag(QGraphicsItem.ItemClipsChildrenToShape, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        
        print(f"✂️ Created CutGraphicsItem with bounds ({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})")
    
    def paint(self, painter, option, widget=None):
        """Override to draw rounded rectangle per Dau specification."""
        # Get the rectangle bounds
        rect = self.rect()
        
        # Draw rounded rectangle instead of sharp corners
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(rect, self.corner_radius, self.corner_radius)
    
    def get_element_id(self) -> str:
        """Get the EGI element ID this graphics item represents."""
        return self.element_id
    
    def add_contained_item(self, item: QGraphicsItem):
        """Add an item to this cut's containment hierarchy."""
        item.setParentItem(self)
        print(f"📦 Added {item.get_element_id() if hasattr(item, 'get_element_id') else 'item'} to cut {self.element_id}")


class LigatureGraphicsItem(QGraphicsPathItem):
    """Graphics item for identity lines (ligatures) with rectilinear routing."""
    
    def __init__(self, element_id: str, egi_data: Dict[str, Any], curve_points: List[tuple]):
        super().__init__()
        
        # Store EGI identity and path data
        self.element_id = element_id
        self.egi_data = egi_data
        self.curve_points = curve_points
        
        # Create rectilinear path from curve points
        path = QPainterPath()
        if curve_points and len(curve_points) >= 2:
            # Start path at first point
            x1, y1 = curve_points[0]
            path.moveTo(x1, y1)
            
            # Add lines to each subsequent point (creates L-shaped paths)
            for i in range(1, len(curve_points)):
                x, y = curve_points[i]
                path.lineTo(x, y)
        
        self.setPath(path)
        
        # Set ligature styling using Dau-compliant heavy line width (4.0pt)
        pen = QPen(QColor(0, 0, 0), 4.0)  # Black heavy lines, 4.0pt width per Dau conventions
        pen.setCapStyle(Qt.RoundCap)  # Rounded line ends
        pen.setJoinStyle(Qt.RoundJoin)  # Rounded corners for L-shapes
        self.setPen(pen)
        
        # Ensure ligatures render on top of EVERYTHING (highest Z-index)
        self.setZValue(100)  # Much higher than any other element
        
        # Enable selection and movement
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        
        start_point = curve_points[0] if curve_points else (0, 0)
        end_point = curve_points[-1] if curve_points else (0, 0)
        print(f"━━ Created LigatureGraphicsItem from ({start_point[0]:.1f}, {start_point[1]:.1f}) to ({end_point[0]:.1f}, {end_point[1]:.1f}) with {len(curve_points)} points")
    
    def get_element_id(self) -> str:
        """Get the EGI element ID this graphics item represents."""
        return self.element_id


class EGGraphicsItemGroup(QGraphicsItemGroup):
    """Group for managing connected EG elements that move together."""
    
    def __init__(self, group_id: str):
        super().__init__()
        self.group_id = group_id
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        
        print(f"🔗 Created EGGraphicsItemGroup: {group_id}")
    
    def add_connected_item(self, item: QGraphicsItem):
        """Add an item to this connected group."""
        self.addToGroup(item)
        print(f"🔗 Added {item.get_element_id() if hasattr(item, 'get_element_id') else 'item'} to group {self.group_id}")
