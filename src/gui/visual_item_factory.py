"""
Visual Item Factory

Creates Qt graphics items for different EGI elements based on style specifications
and rendering level requirements. Supports the viewport renderer's on-demand
visual element generation.
"""

from typing import Dict, Any, Optional
from PySide6.QtCore import QRectF, QPointF, Qt
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsEllipseItem, QGraphicsRectItem, 
    QGraphicsLineItem, QGraphicsPathItem, QGraphicsTextItem,
    QGraphicsItemGroup
)

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from gui.style_manager import DiagramStyle, CutStyle, LigatureStyle, VertexStyle
from gui.viewport_renderer import RenderableElement, RenderingLevel


class VisualItemFactory:
    """
    Factory for creating Qt graphics items from EGI elements.
    
    Handles different rendering levels and style specifications,
    creating appropriate visual representations for viewport rendering.
    """
    
    def __init__(self):
        self.item_cache: Dict[str, QGraphicsItem] = {}
        self.cache_enabled = True
        
    def create_vertex_item(
        self, 
        element_id: ElementID,
        egi: RelationalGraphWithCuts,
        style: DiagramStyle,
        rendering_level: RenderingLevel,
        position: QPointF
    ) -> Optional[QGraphicsItem]:
        """Create visual item for a vertex."""
        
        if element_id not in egi.V:
            return None
            
        vertex = egi.V[element_id]
        vertex_style = style.get_vertex_style()
        
        # Create based on rendering level
        if rendering_level == RenderingLevel.OVERVIEW:
            return self._create_simple_vertex(vertex, vertex_style, position)
        elif rendering_level == RenderingLevel.MEDIUM:
            return self._create_standard_vertex(vertex, vertex_style, position)
        elif rendering_level == RenderingLevel.DETAILED:
            return self._create_detailed_vertex(vertex, vertex_style, position, egi)
        else:  # MICROSCOPIC
            return self._create_debug_vertex(vertex, vertex_style, position, element_id)
            
    def create_edge_item(
        self,
        element_id: ElementID,
        egi: RelationalGraphWithCuts,
        style: DiagramStyle,
        rendering_level: RenderingLevel,
        start_pos: QPointF,
        end_pos: QPointF
    ) -> Optional[QGraphicsItem]:
        """Create visual item for an edge/ligature."""
        
        if element_id not in egi.E:
            return None
            
        edge = egi.E[element_id]
        ligature_style = style.get_ligature_style()
        
        # Create based on rendering level
        if rendering_level == RenderingLevel.OVERVIEW:
            return self._create_simple_edge(edge, ligature_style, start_pos, end_pos)
        elif rendering_level == RenderingLevel.MEDIUM:
            return self._create_standard_edge(edge, ligature_style, start_pos, end_pos)
        elif rendering_level == RenderingLevel.DETAILED:
            return self._create_detailed_edge(edge, ligature_style, start_pos, end_pos, egi)
        else:  # MICROSCOPIC
            return self._create_debug_edge(edge, ligature_style, start_pos, end_pos, element_id)
            
    def create_cut_item(
        self,
        element_id: ElementID,
        egi: RelationalGraphWithCuts,
        style: DiagramStyle,
        rendering_level: RenderingLevel,
        bounds: QRectF,
        nesting_level: int = 0
    ) -> Optional[QGraphicsItem]:
        """Create visual item for a cut."""
        
        if element_id not in egi.Cut:
            return None
            
        cut = egi.Cut[element_id]
        cut_style = style.get_cut_style(nesting_level)
        
        # Create based on rendering level
        if rendering_level == RenderingLevel.OVERVIEW:
            return self._create_simple_cut(cut, cut_style, bounds)
        elif rendering_level == RenderingLevel.MEDIUM:
            return self._create_standard_cut(cut, cut_style, bounds)
        elif rendering_level == RenderingLevel.DETAILED:
            return self._create_detailed_cut(cut, cut_style, bounds, egi)
        else:  # MICROSCOPIC
            return self._create_debug_cut(cut, cut_style, bounds, element_id)
    
    def _create_simple_vertex(
        self, 
        vertex: Vertex, 
        style: VertexStyle, 
        position: QPointF
    ) -> QGraphicsItem:
        """Create simplified vertex for overview rendering."""
        
        radius = max(2.0, style.radius * 0.5)  # Smaller for overview
        
        item = QGraphicsEllipseItem(
            position.x() - radius,
            position.y() - radius,
            radius * 2,
            radius * 2
        )
        
        # Simple styling
        pen = QPen(QColor(style.color))
        pen.setWidth(1)
        item.setPen(pen)
        
        brush = QBrush(QColor(style.fill_color))
        item.setBrush(brush)
        
        return item
        
    def _create_standard_vertex(
        self, 
        vertex: Vertex, 
        style: VertexStyle, 
        position: QPointF
    ) -> QGraphicsItem:
        """Create standard vertex with normal detail."""
        
        item = QGraphicsEllipseItem(
            position.x() - style.radius,
            position.y() - style.radius,
            style.radius * 2,
            style.radius * 2
        )
        
        # Apply full styling
        pen = QPen(QColor(style.color))
        pen.setWidth(style.line_width)
        item.setPen(pen)
        
        brush = QBrush(QColor(style.fill_color))
        item.setBrush(brush)
        
        return item
        
    def _create_detailed_vertex(
        self, 
        vertex: Vertex, 
        style: VertexStyle, 
        position: QPointF,
        egi: RelationalGraphWithCuts
    ) -> QGraphicsItem:
        """Create detailed vertex with labels and connections."""
        
        group = QGraphicsItemGroup()
        
        # Main vertex circle
        circle = self._create_standard_vertex(vertex, style, position)
        group.addToGroup(circle)
        
        # Add label if vertex has one
        if hasattr(vertex, 'label') and vertex.label:
            label_item = QGraphicsTextItem(vertex.label)
            label_item.setPos(
                position.x() + style.radius + 5,
                position.y() - 10
            )
            
            # Style the label
            font = QFont("Arial", 10)
            label_item.setFont(font)
            label_item.setDefaultTextColor(QColor(style.color))
            
            group.addToGroup(label_item)
            
        return group
        
    def _create_debug_vertex(
        self, 
        vertex: Vertex, 
        style: VertexStyle, 
        position: QPointF,
        element_id: ElementID
    ) -> QGraphicsItem:
        """Create debug vertex with ID and detailed information."""
        
        group = QGraphicsItemGroup()
        
        # Main vertex
        circle = self._create_standard_vertex(vertex, style, position)
        group.addToGroup(circle)
        
        # Debug ID label
        id_label = QGraphicsTextItem(str(element_id))
        id_label.setPos(position.x() - 20, position.y() - 30)
        
        font = QFont("Courier", 8)
        id_label.setFont(font)
        id_label.setDefaultTextColor(QColor(255, 0, 0))  # Red for debug
        
        group.addToGroup(id_label)
        
        return group
        
    def _create_simple_edge(
        self,
        edge: Edge,
        style: LigatureStyle,
        start_pos: QPointF,
        end_pos: QPointF
    ) -> QGraphicsItem:
        """Create simplified edge for overview rendering."""
        
        item = QGraphicsLineItem(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
        
        pen = QPen(QColor(style.color))
        pen.setWidth(max(1, int(style.line_width * 0.5)))  # Thinner for overview
        item.setPen(pen)
        
        return item
        
    def _create_standard_edge(
        self,
        edge: Edge,
        style: LigatureStyle,
        start_pos: QPointF,
        end_pos: QPointF
    ) -> QGraphicsItem:
        """Create standard edge with normal styling."""
        
        if style.connection_type == "curved":
            return self._create_curved_edge(edge, style, start_pos, end_pos)
        else:
            return self._create_straight_edge(edge, style, start_pos, end_pos)
            
    def _create_straight_edge(
        self,
        edge: Edge,
        style: LigatureStyle,
        start_pos: QPointF,
        end_pos: QPointF
    ) -> QGraphicsItem:
        """Create straight line edge."""
        
        item = QGraphicsLineItem(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
        
        pen = QPen(QColor(style.color))
        pen.setWidth(style.line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        item.setPen(pen)
        
        return item
        
    def _create_curved_edge(
        self,
        edge: Edge,
        style: LigatureStyle,
        start_pos: QPointF,
        end_pos: QPointF
    ) -> QGraphicsItem:
        """Create curved edge using QPainterPath."""
        
        path = QPainterPath()
        path.moveTo(start_pos)
        
        # Calculate control points for curve
        mid_x = (start_pos.x() + end_pos.x()) / 2
        mid_y = (start_pos.y() + end_pos.y()) / 2
        
        # Offset control point perpendicular to line
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
        length = (dx * dx + dy * dy) ** 0.5
        
        if length > 0:
            # Normalize and rotate 90 degrees
            offset_x = -dy / length * 20  # Curve height
            offset_y = dx / length * 20
            
            control_point = QPointF(mid_x + offset_x, mid_y + offset_y)
            path.quadTo(control_point, end_pos)
        else:
            path.lineTo(end_pos)
            
        item = QGraphicsPathItem(path)
        
        pen = QPen(QColor(style.color))
        pen.setWidth(style.line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        item.setPen(pen)
        
        return item
        
    def _create_detailed_edge(
        self,
        edge: Edge,
        style: LigatureStyle,
        start_pos: QPointF,
        end_pos: QPointF,
        egi: RelationalGraphWithCuts
    ) -> QGraphicsItem:
        """Create detailed edge with additional annotations."""
        
        group = QGraphicsItemGroup()
        
        # Main edge line
        line_item = self._create_standard_edge(edge, style, start_pos, end_pos)
        group.addToGroup(line_item)
        
        # Add relation label if available
        if hasattr(edge, 'relation') and edge.relation:
            mid_point = QPointF(
                (start_pos.x() + end_pos.x()) / 2,
                (start_pos.y() + end_pos.y()) / 2
            )
            
            label_item = QGraphicsTextItem(edge.relation)
            label_item.setPos(mid_point.x() - 10, mid_point.y() - 20)
            
            font = QFont("Arial", 9)
            label_item.setFont(font)
            label_item.setDefaultTextColor(QColor(style.color))
            
            group.addToGroup(label_item)
            
        return group
        
    def _create_debug_edge(
        self,
        edge: Edge,
        style: LigatureStyle,
        start_pos: QPointF,
        end_pos: QPointF,
        element_id: ElementID
    ) -> QGraphicsItem:
        """Create debug edge with ID information."""
        
        group = QGraphicsItemGroup()
        
        # Main edge
        line_item = self._create_standard_edge(edge, style, start_pos, end_pos)
        group.addToGroup(line_item)
        
        # Debug ID at midpoint
        mid_point = QPointF(
            (start_pos.x() + end_pos.x()) / 2,
            (start_pos.y() + end_pos.y()) / 2
        )
        
        id_label = QGraphicsTextItem(str(element_id))
        id_label.setPos(mid_point.x() - 15, mid_point.y() + 10)
        
        font = QFont("Courier", 8)
        id_label.setFont(font)
        id_label.setDefaultTextColor(QColor(0, 0, 255))  # Blue for debug
        
        group.addToGroup(id_label)
        
        return group
        
    def _create_simple_cut(
        self,
        cut: Cut,
        style: CutStyle,
        bounds: QRectF
    ) -> QGraphicsItem:
        """Create simplified cut for overview rendering."""
        
        item = QGraphicsRectItem(bounds)
        
        pen = QPen(QColor(style.color))
        pen.setWidth(max(1, int(style.line_width * 0.5)))
        item.setPen(pen)
        
        # No fill for overview
        item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        
        return item
        
    def _create_standard_cut(
        self,
        cut: Cut,
        style: CutStyle,
        bounds: QRectF
    ) -> QGraphicsItem:
        """Create standard cut with proper styling."""
        
        if hasattr(style, 'corner_radius') and style.corner_radius > 0:
            # Create rounded rectangle using path
            path = QPainterPath()
            path.addRoundedRect(bounds, style.corner_radius, style.corner_radius)
            
            item = QGraphicsPathItem(path)
        else:
            item = QGraphicsRectItem(bounds)
            
        pen = QPen(QColor(style.color))
        pen.setWidth(style.line_width)
        item.setPen(pen)
        
        if hasattr(style, 'fill_color') and style.fill_color:
            brush = QBrush(QColor(style.fill_color))
            item.setBrush(brush)
        else:
            item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            
        return item
        
    def _create_detailed_cut(
        self,
        cut: Cut,
        style: CutStyle,
        bounds: QRectF,
        egi: RelationalGraphWithCuts
    ) -> QGraphicsItem:
        """Create detailed cut with additional information."""
        
        group = QGraphicsItemGroup()
        
        # Main cut shape
        cut_item = self._create_standard_cut(cut, style, bounds)
        group.addToGroup(cut_item)
        
        # Add cut information if available
        if hasattr(cut, 'label') and cut.label:
            label_item = QGraphicsTextItem(cut.label)
            label_item.setPos(bounds.topLeft().x() + 5, bounds.topLeft().y() + 5)
            
            font = QFont("Arial", 9)
            label_item.setFont(font)
            label_item.setDefaultTextColor(QColor(style.color))
            
            group.addToGroup(label_item)
            
        return group
        
    def _create_debug_cut(
        self,
        cut: Cut,
        style: CutStyle,
        bounds: QRectF,
        element_id: ElementID
    ) -> QGraphicsItem:
        """Create debug cut with ID and boundary information."""
        
        group = QGraphicsItemGroup()
        
        # Main cut
        cut_item = self._create_standard_cut(cut, style, bounds)
        group.addToGroup(cut_item)
        
        # Debug ID label
        id_label = QGraphicsTextItem(str(element_id))
        id_label.setPos(bounds.topLeft().x() + 2, bounds.topLeft().y() - 15)
        
        font = QFont("Courier", 8)
        id_label.setFont(font)
        id_label.setDefaultTextColor(QColor(0, 128, 0))  # Green for debug
        
        group.addToGroup(id_label)
        
        # Bounds information
        bounds_text = f"{bounds.width():.0f}×{bounds.height():.0f}"
        bounds_label = QGraphicsTextItem(bounds_text)
        bounds_label.setPos(bounds.bottomLeft().x() + 2, bounds.bottomLeft().y() + 2)
        
        bounds_label.setFont(font)
        bounds_label.setDefaultTextColor(QColor(0, 128, 0))
        
        group.addToGroup(bounds_label)
        
        return group
