"""
Qt Diagram Renderer - Convert LayoutDTO to interactive QGraphicsScene.

This renderer creates native Qt graphics items for full interactivity:
- Vertices as QGraphicsEllipseItem (draggable, selectable)
- Predicates as QGraphicsTextItem (draggable, selectable)  
- Ligatures as QGraphicsPathItem (visual feedback)
- Cuts as QGraphicsRectItem (visual hierarchy)

Used by Ergasterion for interactive editing.
"""

from typing import Dict, Optional, Set
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsTextItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsItem,
)

from unified_d3_engine import LayoutDTO, Point
from egi_core_dau import RelationalGraphWithCuts


class InteractiveGraphicsItem:
    """Mixin for interactive diagram elements - adds element_id and interactive flags."""
    
    def setup_interactive(self, element_id: str):
        """Set up interactive properties. Call this after QGraphicsItem.__init__."""
        self.element_id = element_id
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges, True)
        self.setAcceptHoverEvents(True)
        
        # Track if this item has moved
        self._original_pos = None
        self._has_moved = False
    
    def itemChange(self, change, value):
        """Track when item position changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if self._original_pos is None:
                self._original_pos = value
            else:
                self._has_moved = True
        return super().itemChange(change, value)


class InteractiveVertexItem(QGraphicsEllipseItem, InteractiveGraphicsItem):
    """Interactive vertex (draggable circle with label)."""
    
    def __init__(self, vertex_id: str, position: Point, radius: float, label: str):
        # Initialize graphics item
        super().__init__(-radius, -radius, radius*2, radius*2)
        # Set up interactive properties
        self.setup_interactive(vertex_id)
        
        # Set position
        self.setPos(position.x, position.y)
        
        # Style
        pen = QPen(QColor("#000000"))
        pen.setWidth(1)
        self.setPen(pen)
        self.setBrush(QBrush(QColor("#000000")))
        
        # Label
        if label:
            self.label_item = QGraphicsTextItem(label, self)
            font = QFont("Times New Roman", 11)
            self.label_item.setFont(font)
            # Position label to the right of vertex
            self.label_item.setPos(radius + 5, -radius - 5)
        else:
            self.label_item = None
    
    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        pen = QPen(QColor("#1E88E5"))
        pen.setWidth(2)
        self.setPen(pen)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Remove highlight."""
        pen = QPen(QColor("#000000"))
        pen.setWidth(1)
        self.setPen(pen)
        super().hoverLeaveEvent(event)


class InteractivePredicateItem(QGraphicsTextItem, InteractiveGraphicsItem):
    """Interactive predicate (draggable text)."""
    
    def __init__(self, predicate_id: str, position: Point, label: str):
        # Initialize text item
        super().__init__(label)
        # Set up interactive properties
        self.setup_interactive(predicate_id)
        
        # Set font
        font = QFont("Times New Roman", 12)
        self.setFont(font)
        
        # Center text at position
        bounds = self.boundingRect()
        self.setPos(position.x - bounds.width()/2, position.y - bounds.height()/2)
        
        # Make background transparent
        self.setDefaultTextColor(QColor("#000000"))
    
    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        self.setDefaultTextColor(QColor("#1E88E5"))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Remove highlight."""
        self.setDefaultTextColor(QColor("#000000"))
        super().hoverLeaveEvent(event)


class LigaturePathItem(QGraphicsPathItem):
    """Non-interactive ligature path (visual only)."""
    
    def __init__(self, points: list):
        super().__init__()
        
        # Create path from points
        path = QPainterPath()
        if points:
            path.moveTo(points[0].x, points[0].y)
            for point in points[1:]:
                path.lineTo(point.x, point.y)
        
        self.setPath(path)
        
        # Style
        pen = QPen(QColor("#000000"))
        pen.setWidth(2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
        
        # Not selectable/movable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)


class CutRectItem(QGraphicsRectItem):
    """Non-interactive cut boundary (visual only)."""
    
    def __init__(self, cut_id: str, bounds: 'BoundingBox', polarity: int):
        x = bounds.min_x
        y = bounds.min_y
        w = bounds.max_x - bounds.min_x
        h = bounds.max_y - bounds.min_y
        
        super().__init__(x, y, w, h)
        
        self.cut_id = cut_id
        
        # Style based on polarity
        pen = QPen(QColor("#000000"))
        pen.setWidth(1.5)
        self.setPen(pen)
        
        # Fill for odd polarity
        if polarity % 2 == 1:
            self.setBrush(QBrush(QColor(0, 0, 0, 20)))  # Light gray
        else:
            self.setBrush(QBrush(Qt.GlobalColor.transparent))
        
        # Not selectable/movable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        
        # Send to back
        self.setZValue(-1)


class QtDiagramRenderer:
    """
    Renders LayoutDTO as interactive QGraphicsScene.
    
    Creates native Qt graphics items for full interactivity in Ergasterion mode.
    """
    
    def __init__(self):
        self.vertex_items: Dict[str, InteractiveVertexItem] = {}
        self.predicate_items: Dict[str, InteractivePredicateItem] = {}
        self.ligature_items: list = []
        self.cut_items: Dict[str, CutRectItem] = {}
    
    def render_to_scene(
        self, 
        dto: LayoutDTO, 
        egi: RelationalGraphWithCuts
    ) -> QGraphicsScene:
        """
        Render LayoutDTO as interactive QGraphicsScene.
        
        Args:
            dto: Layout information
            egi: EGI model for labels/properties
            
        Returns:
            QGraphicsScene with interactive items
        """
        print(f"QtDiagramRenderer.render_to_scene: {len(dto.vertex_positions)}V, {len(dto.predicate_positions)}P")
        scene = QGraphicsScene()
        
        # Clear previous items
        self.vertex_items.clear()
        self.predicate_items.clear()
        self.ligature_items.clear()
        self.cut_items.clear()
        
        # Get style from DTO
        style = dto.style
        
        # 1. Render cuts (background)
        polarity_map = self._compute_polarity_map(egi, dto.sheet_id)
        for cut_id, bounds in dto.cut_bounds.items():
            if cut_id != dto.sheet_id:  # Don't render sheet
                polarity = polarity_map.get(cut_id, 0)
                cut_item = CutRectItem(cut_id, bounds, polarity)
                scene.addItem(cut_item)
                self.cut_items[cut_id] = cut_item
        
        # 2. Render ligatures (middle layer)
        for ligature in dto.ligature_paths:
            ligature_item = LigaturePathItem(ligature.points)
            scene.addItem(ligature_item)
            self.ligature_items.append(ligature_item)
        
        # 3. Render vertices (interactive, top layer)
        for vertex_id, point in dto.vertex_positions.items():
            # Get vertex label from EGI
            vertex = egi._vertex_map.get(vertex_id)
            label = vertex.label if vertex and vertex.label else ""
            
            vertex_item = InteractiveVertexItem(
                vertex_id,
                point,
                style.vertex_radius,
                label
            )
            scene.addItem(vertex_item)
            self.vertex_items[vertex_id] = vertex_item
        
        # 4. Render predicates (interactive, top layer)
        for pred_id, point in dto.predicate_positions.items():
            # Get predicate name from EGI.rel mapping
            label = egi.rel.get(pred_id, "?")
            
            pred_item = InteractivePredicateItem(pred_id, point, label)
            scene.addItem(pred_item)
            self.predicate_items[pred_id] = pred_item
        
        # Set scene bounds
        vb = dto.viewport_bounds
        scene.setSceneRect(vb.min_x, vb.min_y, vb.max_x - vb.min_x, vb.max_y - vb.min_y)
        
        return scene
    
    def _compute_polarity_map(self, egi: RelationalGraphWithCuts, sheet_id: str) -> Dict[str, int]:
        """Compute polarity (nesting depth) for each cut."""
        polarity_map = {sheet_id: 0}
        
        # Use EGI.Cut (capital C) to get cuts
        # For now, simple approach: all cuts are polarity 1
        for cut in egi.Cut:
            if cut.id != sheet_id:
                polarity_map[cut.id] = 1
        
        return polarity_map
    
    def get_selected_elements(self, scene: QGraphicsScene) -> Set[str]:
        """Get IDs of currently selected elements."""
        selected = set()
        for item in scene.selectedItems():
            if isinstance(item, InteractiveGraphicsItem):
                selected.add(item.element_id)
        return selected
    
    def clear_selection(self, scene: QGraphicsScene):
        """Clear all selections."""
        scene.clearSelection()
    
    def select_elements(self, scene: QGraphicsScene, element_ids: Set[str]):
        """Select specific elements by ID."""
        for item in scene.items():
            if isinstance(item, InteractiveGraphicsItem):
                item.setSelected(item.element_id in element_ids)
