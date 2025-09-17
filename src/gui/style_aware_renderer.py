"""
Style-Aware Diagram Renderer

Renders EGI diagrams using the abstract style manager system.
Supports multiple visual styles while maintaining logical independence.
"""

from typing import Dict, List, Optional, Tuple
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtGui import QPainter, QPainterPath

from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex, ElementID
from gui.style_manager import DiagramStyle, get_current_style, STYLE_MANAGER
from gui.styles.dau_compliant_style import DauCompliantStyle
from gui.styles.peirce_authentic_style import PeirceAuthenticStyle


class StyleAwareRenderer:
    """Renders EGI diagrams using pluggable visual styles."""
    
    def __init__(self, style_id: Optional[str] = None):
        self.current_style_id = style_id
        self.scene = None
        self.rendered_items = {}  # element_id -> QGraphicsItem
        
        # Initialize default styles if none registered
        self._ensure_default_styles()
    
    def _ensure_default_styles(self):
        """Register default styles if style manager is empty."""
        if not STYLE_MANAGER.list_styles():
            STYLE_MANAGER.register_style(DauCompliantStyle())
            STYLE_MANAGER.register_style(PeirceAuthenticStyle())
            STYLE_MANAGER.set_current_style("dau-compliant@1.0")
    
    def get_active_style(self) -> DiagramStyle:
        """Get the currently active style."""
        if self.current_style_id:
            style = STYLE_MANAGER.get_style(self.current_style_id)
            if style:
                return style
        
        # Fall back to global current style
        current = get_current_style()
        if current:
            return current
        
        # Final fallback to Dau compliant
        return DauCompliantStyle()
    
    def set_style(self, style_id: str) -> bool:
        """Set the active style for this renderer."""
        if STYLE_MANAGER.get_style(style_id):
            self.current_style_id = style_id
            return True
        return False
    
    def render_to_scene(self, egi: RelationalGraphWithCuts, scene: QGraphicsScene,
                       layout_positions: Optional[Dict[ElementID, Tuple[float, float]]] = None):
        """Render EGI to Qt graphics scene using current style."""
        self.scene = scene
        self.rendered_items.clear()
        scene.clear()
        
        style = self.get_active_style()
        
        # Set background
        layout_style = style.get_layout_style()
        scene.setBackgroundBrush(layout_style.sheet_color)
        
        # Generate layout if not provided
        if layout_positions is None:
            layout_positions = self._generate_simple_layout(egi)
        
        # Render in proper order: cuts first (background), then vertices/edges (foreground)
        self._render_cuts(egi, style, layout_positions)
        self._render_vertices(egi, style, layout_positions)
        self._render_edges(egi, style, layout_positions)
        self._render_ligatures(egi, style, layout_positions)
    
    def _render_cuts(self, egi: RelationalGraphWithCuts, style: DiagramStyle,
                    layout_positions: Dict[ElementID, Tuple[float, float]]):
        """Render all cuts with style-appropriate appearance."""
        cut_style = style.get_cut_style()
        
        for cut in egi.Cut:
            cut_bounds = self._calculate_cut_bounds(cut.id, egi, layout_positions)
            
            if cut_style.shape_type == "rounded_rectangle":
                item = self.scene.addRect(cut_bounds)
                item.setPen(cut_style.get_pen())
                item.setBrush(cut_style.get_brush())
                # TODO: Implement rounded corners via custom paint
            elif cut_style.shape_type == "oval":
                item = self.scene.addEllipse(cut_bounds)
                item.setPen(cut_style.get_pen())
                item.setBrush(cut_style.get_brush())
            
            self.rendered_items[cut.id] = item
    
    def _render_vertices(self, egi: RelationalGraphWithCuts, style: DiagramStyle,
                        layout_positions: Dict[ElementID, Tuple[float, float]]):
        """Render all vertices with style-appropriate appearance."""
        vertex_style = style.get_vertex_style()
        
        for vertex in egi.V:
            if vertex.id in layout_positions:
                x, y = layout_positions[vertex.id]
                
                if vertex_style.shape_type == "circle":
                    bounds = QRectF(
                        x - vertex_style.radius, y - vertex_style.radius,
                        vertex_style.radius * 2, vertex_style.radius * 2
                    )
                    item = self.scene.addEllipse(bounds)
                elif vertex_style.shape_type == "square":
                    bounds = QRectF(
                        x - vertex_style.radius, y - vertex_style.radius,
                        vertex_style.radius * 2, vertex_style.radius * 2
                    )
                    item = self.scene.addRect(bounds)
                
                item.setPen(vertex_style.get_pen())
                item.setBrush(vertex_style.get_brush())
                self.rendered_items[vertex.id] = item
                
                # Add vertex label if present
                if vertex.label:
                    label_style = style.get_label_style()
                    label_item = self.scene.addText(vertex.label, label_style.get_font())
                    label_item.setDefaultTextColor(label_style.color)
                    label_item.setPos(x + vertex_style.label_offset, y - vertex_style.radius)
    
    def _render_edges(self, egi: RelationalGraphWithCuts, style: DiagramStyle,
                     layout_positions: Dict[ElementID, Tuple[float, float]]):
        """Render all edges (predicates) with style-appropriate appearance."""
        predicate_style = style.get_predicate_style()
        
        for edge in egi.E:
            if edge.id in layout_positions:
                x, y = layout_positions[edge.id]
                
                if predicate_style.shape_type == "line":
                    # Horizontal line for predicate
                    item = self.scene.addLine(
                        x - predicate_style.length/2, y,
                        x + predicate_style.length/2, y
                    )
                    item.setPen(predicate_style.get_pen())
                    self.rendered_items[edge.id] = item
                
                # Add relation label if present
                relation_name = egi.rel.get(edge.id)
                if relation_name:
                    label_style = style.get_label_style()
                    label_item = self.scene.addText(relation_name, label_style.get_font())
                    label_item.setDefaultTextColor(label_style.color)
                    label_item.setPos(x - len(relation_name) * 3, y - 20)
    
    def _render_ligatures(self, egi: RelationalGraphWithCuts, style: DiagramStyle,
                         layout_positions: Dict[ElementID, Tuple[float, float]]):
        """Render ligatures (connections) with style-appropriate routing."""
        ligature_style = style.get_ligature_style()
        
        for edge_id, vertex_sequence in egi.nu.items():
            if len(vertex_sequence) >= 2 and edge_id in layout_positions:
                edge_pos = layout_positions[edge_id]
                
                # Connect edge to each incident vertex
                for vertex_id in vertex_sequence:
                    if vertex_id in layout_positions:
                        vertex_pos = layout_positions[vertex_id]
                        
                        if ligature_style.connection_type == "straight":
                            item = self.scene.addLine(
                                edge_pos[0], edge_pos[1],
                                vertex_pos[0], vertex_pos[1]
                            )
                        elif ligature_style.connection_type == "orthogonal":
                            # L-shaped connection
                            path = QPainterPath()
                            path.moveTo(edge_pos[0], edge_pos[1])
                            path.lineTo(vertex_pos[0], edge_pos[1])  # Horizontal first
                            path.lineTo(vertex_pos[0], vertex_pos[1])  # Then vertical
                            item = self.scene.addPath(path)
                        
                        item.setPen(ligature_style.get_pen())
    
    def _calculate_cut_bounds(self, cut_id: str, egi: RelationalGraphWithCuts,
                             layout_positions: Dict[ElementID, Tuple[float, float]]) -> QRectF:
        """Calculate bounding rectangle for a cut based on its contents."""
        cut_style = self.get_active_style().get_cut_style()
        
        # Find all elements contained in this cut
        contained_elements = egi.area.get(cut_id, set())
        
        if not contained_elements:
            # Empty cut - use default size
            return QRectF(0, 0, 100, 60)
        
        # Find bounding box of contained elements
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for element_id in contained_elements:
            if element_id in layout_positions:
                x, y = layout_positions[element_id]
                min_x = min(min_x, x - 20)  # Add element radius/size
                max_x = max(max_x, x + 20)
                min_y = min(min_y, y - 20)
                max_y = max(max_y, y + 20)
        
        if min_x == float('inf'):
            return QRectF(0, 0, 100, 60)
        
        # Add cut padding
        return QRectF(
            min_x - cut_style.padding,
            min_y - cut_style.padding,
            (max_x - min_x) + 2 * cut_style.padding,
            (max_y - min_y) + 2 * cut_style.padding
        )
    
    def _generate_simple_layout(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, Tuple[float, float]]:
        """Generate simple grid layout if no layout provided."""
        positions = {}
        x, y = 50, 50
        spacing = 80
        
        # Position vertices
        for vertex in egi.V:
            positions[vertex.id] = (x, y)
            x += spacing
            if x > 400:
                x = 50
                y += spacing
        
        # Position edges near their vertices
        for edge in egi.E:
            if edge.id in egi.nu:
                vertex_sequence = egi.nu[edge.id]
                if vertex_sequence:
                    # Position at centroid of incident vertices
                    vertex_positions = [positions.get(v, (0, 0)) for v in vertex_sequence if v in positions]
                    if vertex_positions:
                        avg_x = sum(pos[0] for pos in vertex_positions) / len(vertex_positions)
                        avg_y = sum(pos[1] for pos in vertex_positions) / len(vertex_positions)
                        positions[edge.id] = (avg_x, avg_y - 30)  # Offset above vertices
        
        return positions
    
    def highlight_element(self, element_id: str, highlight: bool = True):
        """Highlight or unhighlight a rendered element."""
        if element_id in self.rendered_items:
            item = self.rendered_items[element_id]
            if highlight:
                # Create highlighted appearance
                current_pen = item.pen()
                highlight_pen = current_pen
                highlight_pen.setWidthF(current_pen.widthF() * 1.5)
                highlight_pen.setColor(current_pen.color().lighter(150))
                item.setPen(highlight_pen)
            else:
                # Restore original appearance - would need to cache original pens
                pass
