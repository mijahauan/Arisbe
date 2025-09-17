"""
Dau Cut Renderer

Implements authentic cut rendering based on Dau's visual style.
Renders cuts as rounded rectangles with proper nesting and spacing.
"""

from typing import Dict, List, Tuple
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, QPainterPath
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem

from egi_core_dau import Cut, RelationalGraphWithCuts
from gui.dau_visual_style import DAU_STYLE, DauLayoutPrinciples


class DauCutItem(QGraphicsRectItem):
    """Graphics item for rendering a single cut with Dau styling."""
    
    def __init__(self, cut_id: str, bounds: QRectF, nesting_level: int = 0):
        super().__init__(bounds)
        self.cut_id = cut_id
        self.nesting_level = nesting_level
        
        # Apply Dau styling
        self.setPen(DAU_STYLE.get_cut_pen())
        self.setBrush(DAU_STYLE.get_cut_brush())
        
        # Set Z-value based on nesting (outer cuts behind inner cuts)
        self.setZValue(-nesting_level)
    
    def paint(self, painter: QPainter, option, widget=None):
        """Custom paint method for rounded rectangle cuts."""
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        
        # Draw rounded rectangle
        rect = self.rect()
        painter.drawRoundedRect(rect, DAU_STYLE.cut_corner_radius, DAU_STYLE.cut_corner_radius)


class DauCutRenderer:
    """Renders cuts following Dau's authentic visual style."""
    
    def __init__(self):
        self.cut_items = {}  # cut_id -> DauCutItem
        self.cut_hierarchy = {}  # cut_id -> parent_cut_id
        self.cut_contents = {}  # cut_id -> list of element_ids
    
    def render_cuts(self, egi: RelationalGraphWithCuts, scene) -> Dict[str, DauCutItem]:
        """Render all cuts in the EGI with proper nesting."""
        self.cut_items.clear()
        self.cut_hierarchy.clear()
        self.cut_contents.clear()
        
        # Build cut hierarchy from area mappings
        self._build_cut_hierarchy(egi)
        
        # Calculate cut bounds based on contents
        cut_bounds = self._calculate_cut_bounds(egi)
        
        # Create cut items with proper nesting levels
        for cut in egi.Cut:
            cut_id = cut.id
            bounds = cut_bounds.get(cut_id, QRectF(0, 0, 100, 100))
            nesting_level = self._get_nesting_level(cut_id)
            
            cut_item = DauCutItem(cut_id, bounds, nesting_level)
            self.cut_items[cut_id] = cut_item
            scene.addItem(cut_item)
        
        return self.cut_items
    
    def _build_cut_hierarchy(self, egi: RelationalGraphWithCuts):
        """Build hierarchy of cuts from area mappings."""
        # Analyze area mappings to determine cut containment
        for area_id, elements in egi.area.items():
            if area_id.startswith('cut_'):
                cut_id = area_id[4:]  # Remove 'cut_' prefix
                self.cut_contents[cut_id] = list(elements)
                
                # Find parent cut (cut that contains this cut)
                for other_area_id, other_elements in egi.area.items():
                    if other_area_id != area_id and other_area_id.startswith('cut_'):
                        other_cut_id = other_area_id[4:]
                        if cut_id in other_elements:
                            self.cut_hierarchy[cut_id] = other_cut_id
                            break
    
    def _calculate_cut_bounds(self, egi: RelationalGraphWithCuts) -> Dict[str, QRectF]:
        """Calculate bounds for each cut based on its contents."""
        cut_bounds = {}
        
        # Start with innermost cuts (no children) and work outward
        processed = set()
        
        while len(processed) < len(egi.Cut):
            for cut in egi.Cut:
                cut_id = cut.id
                if cut_id in processed:
                    continue
                
                # Check if all child cuts are processed
                child_cuts = [cid for cid, parent in self.cut_hierarchy.items() if parent == cut_id]
                if not all(child_id in processed for child_id in child_cuts):
                    continue
                
                # Calculate bounds for this cut
                bounds = self._calculate_single_cut_bounds(cut_id, egi, cut_bounds)
                cut_bounds[cut_id] = bounds
                processed.add(cut_id)
        
        return cut_bounds
    
    def _calculate_single_cut_bounds(self, cut_id: str, egi: RelationalGraphWithCuts, 
                                   existing_bounds: Dict[str, QRectF]) -> QRectF:
        """Calculate bounds for a single cut based on its contents."""
        contents = self.cut_contents.get(cut_id, [])
        
        if not contents:
            # Empty cut - use default size
            return QRectF(0, 0, 100, 60)
        
        # Find bounding box of all contents
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for element_id in contents:
            # Get element bounds (this would need to be coordinated with vertex/edge rendering)
            # For now, use placeholder positions
            if element_id.startswith('v_'):
                # Vertex position (would come from layout algorithm)
                x, y = self._get_element_position(element_id)
                min_x = min(min_x, x - DAU_STYLE.vertex_radius)
                max_x = max(max_x, x + DAU_STYLE.vertex_radius)
                min_y = min(min_y, y - DAU_STYLE.vertex_radius)
                max_y = max(max_y, y + DAU_STYLE.vertex_radius)
            elif element_id.startswith('cut_'):
                # Nested cut bounds
                child_cut_id = element_id[4:]
                if child_cut_id in existing_bounds:
                    child_bounds = existing_bounds[child_cut_id]
                    min_x = min(min_x, child_bounds.left())
                    max_x = max(max_x, child_bounds.right())
                    min_y = min(min_y, child_bounds.top())
                    max_y = max(max_y, child_bounds.bottom())
        
        if min_x == float('inf'):
            # No valid contents found
            return QRectF(0, 0, 100, 60)
        
        # Add padding around contents
        content_bounds = (min_x, min_y, max_x - min_x, max_y - min_y)
        padded_bounds = DauLayoutPrinciples.calculate_cut_bounds(content_bounds)
        
        return QRectF(padded_bounds[0], padded_bounds[1], padded_bounds[2], padded_bounds[3])
    
    def _get_element_position(self, element_id: str) -> Tuple[float, float]:
        """Get position of an element (placeholder - would integrate with layout)."""
        # This would be coordinated with the overall layout algorithm
        # For now, return placeholder positions
        hash_val = hash(element_id) % 1000
        return (hash_val % 200, (hash_val // 200) % 150)
    
    def _get_nesting_level(self, cut_id: str) -> int:
        """Get nesting level of a cut (0 = outermost)."""
        level = 0
        current = cut_id
        
        while current in self.cut_hierarchy:
            level += 1
            current = self.cut_hierarchy[current]
            if level > 10:  # Prevent infinite loops
                break
        
        return level
    
    def update_cut_bounds(self, cut_id: str, new_bounds: QRectF):
        """Update bounds of a cut item."""
        if cut_id in self.cut_items:
            self.cut_items[cut_id].setRect(new_bounds)
    
    def highlight_cut(self, cut_id: str, highlight: bool = True):
        """Highlight or unhighlight a cut."""
        if cut_id in self.cut_items:
            cut_item = self.cut_items[cut_id]
            if highlight:
                # Create highlighted pen
                highlight_pen = DAU_STYLE.get_cut_pen()
                highlight_pen.setColor(DAU_STYLE.cut_color.lighter(150))
                highlight_pen.setWidthF(DAU_STYLE.cut_line_width * 1.5)
                cut_item.setPen(highlight_pen)
            else:
                # Restore normal pen
                cut_item.setPen(DAU_STYLE.get_cut_pen())
