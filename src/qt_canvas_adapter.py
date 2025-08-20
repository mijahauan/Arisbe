"""
Qt Canvas Adapter - Foundation Stub

Provides a Qt-based canvas widget for diagram rendering and interaction.
This is a foundation stub that avoids NumPy compatibility issues.
"""

from typing import Optional, List, Tuple, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
from typing import List, Any

class QtCanvasAdapter(QWidget):
    """
    Qt-based canvas adapter for diagram rendering.
    
    Foundation stub implementation that provides basic canvas functionality
    without complex dependencies.
    """
    
    # Signals
    element_selected = Signal(str)  # element_id
    element_clicked = Signal(str, int, int)  # element_id, x, y
    canvas_clicked = Signal(int, int)  # x, y
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Canvas state
        self.zoom_factor = 1.0
        self.spatial_primitives = []
        self.egi = None  # Store EGI reference for z-order calculations
        self.setMinimumSize(600, 400)
        self.selected_elements = []
        self.diagram_data = None
        self.spatial_primitives = []
        
        # Canvas properties
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        print("✓ QtCanvasAdapter initialized for native Qt painting")
    
    def _setup_placeholder(self):
        """Set up placeholder content."""
        # No placeholder needed - canvas will draw directly
        pass
    
    def paintEvent(self, event):
        """Handle paint events."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background grid
        self._draw_grid(painter)
        
        # Always try to draw spatial primitives if available
        if hasattr(self, 'spatial_primitives') and self.spatial_primitives:
            print(f"Canvas drawing {len(self.spatial_primitives)} spatial primitives")
            self._draw_egdf_primitives(painter)
        else:
            print("Canvas has no spatial primitives - drawing placeholder")
            self._draw_placeholder_elements(painter)
        
        painter.end()
    
    def _draw_grid(self, painter):
        """Draw background grid."""
        painter.setPen(QPen(QColor(240, 240, 240), 1))
        
        width = self.width()
        height = self.height()
        
        # Draw grid lines
        for x in range(0, width, 20):
            painter.drawLine(x, 0, x, height)
        
        for y in range(0, height, 20):
            painter.drawLine(0, y, width, y)
    
    def _get_cut_nesting_depth(self, cut_id):
        """Calculate nesting depth of a cut based on EGI area mapping."""
        if not hasattr(self, 'egi') or not self.egi:
            return 0
        
        # Find how deeply this cut is nested by traversing area mappings
        depth = 0
        current_areas = set()
        
        # Find which areas contain this cut
        for context_id, area_elements in self.egi.area.items():
            if cut_id in area_elements:
                current_areas.add(context_id)
        
        # Count nesting levels - cuts contained in other cuts have higher depth
        for context_id in current_areas:
            if context_id != self.egi.sheet:  # Not the sheet
                depth += 1
        
        return depth
    
    def _get_element_area_depth(self, element_id):
        """Calculate area depth of an element based on EGI area mapping."""
        if not hasattr(self, 'egi') or not self.egi:
            return 0
        
        # Find which area this element belongs to
        for context_id, area_elements in self.egi.area.items():
            if element_id in area_elements:
                if context_id == self.egi.sheet:
                    return 0  # Sheet has lowest depth
                else:
                    # Element is in a cut - calculate cut's nesting depth
                    return self._get_cut_nesting_depth(context_id)
        
        return 0
    
    def _calculate_cut_bounds(self, cut_id, primitive):
        """Calculate bounds for a cut to encompass all contained elements."""
        canvas_width = self.width()
        canvas_height = self.height()
        
        if not hasattr(self, 'egi') or not self.egi:
            # Fallback to primitive bounds with padding
            default_bounds = primitive.get('bounds', (0.4, 0.4, 0.6, 0.6))
            abs_left = default_bounds[0] * canvas_width
            abs_top = default_bounds[1] * canvas_height  
            abs_right = default_bounds[2] * canvas_width
            abs_bottom = default_bounds[3] * canvas_height
            padding = 20
            return (abs_left - padding, abs_top - padding, 
                    abs_right + padding, abs_bottom + padding)
        
        # Find all elements in this cut's area
        contained_elements = self.egi.area.get(cut_id, frozenset())
        
        if not contained_elements:
            # No contained elements, use primitive bounds
            default_bounds = primitive.get('bounds', (0.4, 0.4, 0.6, 0.6))
            abs_left = default_bounds[0] * canvas_width
            abs_top = default_bounds[1] * canvas_height  
            abs_right = default_bounds[2] * canvas_width
            abs_bottom = default_bounds[3] * canvas_height
            padding = 20
            return (abs_left - padding, abs_top - padding, 
                    abs_right + padding, abs_bottom + padding)
        
        # Calculate bounding box of all contained elements
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for element_id in contained_elements:
            # Find this element in spatial primitives
            for p in self.spatial_primitives:
                if isinstance(p, dict) and p.get('element_id') == element_id:
                    bounds = p.get('bounds', (0.5, 0.5, 0.5, 0.5))
                    min_x = min(min_x, bounds[0] * canvas_width)
                    min_y = min(min_y, bounds[1] * canvas_height)
                    max_x = max(max_x, bounds[2] * canvas_width)
                    max_y = max(max_y, bounds[3] * canvas_height)
                    break
        
        # Add padding around contained elements
        padding = 30  # pixels
        if min_x != float('inf'):
            return (min_x - padding, min_y - padding, 
                    max_x + padding, max_y + padding)
        else:
            # Fallback if no elements found
            default_bounds = primitive.get('bounds', (0.4, 0.4, 0.6, 0.6))
            abs_left = default_bounds[0] * canvas_width
            abs_top = default_bounds[1] * canvas_height  
            abs_right = default_bounds[2] * canvas_width
            abs_bottom = default_bounds[3] * canvas_height
            padding = 20
            return (abs_left - padding, abs_top - padding, 
                    abs_right + padding, abs_bottom + padding)
    
    def _draw_egdf_primitives(self, painter):
        """Draw EGDF spatial primitives with proper z-order for existential graphs."""
        canvas_width = self.width()
        canvas_height = self.height()
        
        # Sort primitives by z-order: Sheet (lowest) -> nested cuts -> predicates/vertices -> ligatures -> annotations (highest)
        def get_z_order(primitive):
            if isinstance(primitive, dict):
                element_type = primitive.get('element_type', 'unknown')
                element_id = primitive.get('element_id', 'unknown')
            else:
                element_type = getattr(primitive, 'element_type', 'unknown')
                element_id = getattr(primitive, 'element_id', 'unknown')
            
            # Z-order hierarchy
            if element_id == 'sheet':
                return 0  # Sheet has lowest z-order
            elif element_type == 'cut':
                # More nested cuts have higher z-order (calculated from nesting depth)
                return 10 + self._get_cut_nesting_depth(element_id)
            elif element_type in ['predicate', 'vertex']:
                # Predicates and vertices track their area's z-order
                return 20 + self._get_element_area_depth(element_id)
            elif element_type == 'ligature':
                return 100  # Ligatures have high z-order (can span cuts)
            elif element_type == 'annotation':
                return 200  # Annotations have highest z-order
            else:
                return 50  # Default for unknown types
        
        sorted_primitives = sorted(self.spatial_primitives, key=get_z_order)
        
        # Draw primitives in z-order
        for primitive in sorted_primitives:
            if isinstance(primitive, dict):
                element_type = primitive.get('element_type', 'unknown')
                element_id = primitive.get('element_id', 'unknown')
                position = primitive.get('position', (0.5, 0.5))
                bounds = primitive.get('bounds', (0.4, 0.4, 0.6, 0.6))
                
                # Convert relative coordinates to pixels
                rel_x, rel_y = position
                canvas_x = rel_x * canvas_width
                canvas_y = rel_y * canvas_height
                
                # Convert bounds
                if len(bounds) == 4:
                    rel_left, rel_top, rel_right, rel_bottom = bounds
                    abs_left = rel_left * canvas_width
                    abs_top = rel_top * canvas_height
                    abs_width = (rel_right - rel_left) * canvas_width
                    abs_height = (rel_bottom - rel_top) * canvas_height
                else:
                    abs_left, abs_top, abs_width, abs_height = canvas_x - 25, canvas_y - 15, 50, 30
                
                if element_type == 'predicate':
                    # Draw predicate with clear background and tight boundary for ligature attachment
                    painter.setBrush(QBrush())  # No fill - clear background
                    painter.setPen(QPen(QColor(0, 0, 0), 1))  # Thin line for tight boundary
                    
                    # Add text first to calculate tight bounds
                    text_content = primitive.get('text_content', element_id)
                    font_metrics = painter.fontMetrics()
                    text_rect = font_metrics.boundingRect(text_content)
                    
                    # Calculate tight bounds around text
                    text_x = int(canvas_x - text_rect.width() / 2)
                    text_y = int(canvas_y + text_rect.height() / 4)
                    
                    # Draw tight rectangle around text
                    padding = 2
                    tight_rect = (text_x - padding, text_y - text_rect.height() + padding,
                                 text_rect.width() + 2*padding, text_rect.height())
                    painter.drawRect(*tight_rect)
                    
                    # Draw text
                    painter.drawText(text_x, text_y, text_content)
                    
                elif element_type == 'vertex':
                    # Draw vertex as small dot, larger than ligature line width
                    painter.setBrush(QBrush(QColor(0, 0, 0)))
                    painter.setPen(QPen(QColor(0, 0, 0), 0))  # No outline
                    # Use 6x6 pixel size - larger than ligature line width (typically 1-2px)
                    painter.drawEllipse(int(canvas_x - 3), int(canvas_y - 3), 6, 6)
                    
                elif element_type == 'cut':
                    # Draw cut as rectangle with rounded corners
                    painter.setBrush(QBrush())  # No fill
                    painter.setPen(QPen(QColor(0, 0, 0), 2))
                    # Calculate size to encompass all contained elements
                    cut_bounds = self._calculate_cut_bounds(element_id, primitive)
                    
                    # Draw rounded rectangle for cut
                    from PySide6.QtCore import QRectF
                    rect = QRectF(cut_bounds[0], cut_bounds[1], 
                                 cut_bounds[2] - cut_bounds[0], 
                                 cut_bounds[3] - cut_bounds[1])
                    painter.drawRoundedRect(rect, 10, 10)  # 10px corner radius
    
    def _draw_single_primitive(self, painter, primitive, canvas_width, canvas_height):
        """Draw a single primitive element."""
        if isinstance(primitive, dict):
            element_type = primitive.get('element_type', 'unknown')
            element_id = primitive.get('element_id', 'unknown')
            position = primitive.get('position', (0, 0))
            bounds = primitive.get('bounds', (0, 0, 0.1, 0.05))
        else:
            # Object-based primitives
            element_type = getattr(primitive, 'element_type', 'unknown')
            element_id = getattr(primitive, 'element_id', 'unknown')
            position = getattr(primitive, 'position', (0, 0))
            bounds = getattr(primitive, 'bounds', (0, 0, 0.1, 0.05))
            
            # Check if coordinates are already in pixel space (> 1.0) or relative space (0.0-1.0)
            rel_x, rel_y = position
            if rel_x > 1.0 or rel_y > 1.0:
                # Already in pixel coordinates - use directly
                canvas_x = rel_x
                canvas_y = rel_y
            else:
                # Relative coordinates - convert to pixels
                canvas_x = rel_x * canvas_width
                canvas_y = rel_y * canvas_height
            
            # Convert bounds to absolute bounds
            if len(bounds) == 4:
                rel_left, rel_top, rel_right, rel_bottom = bounds
                # Check if bounds are already in pixel space or relative space
                if rel_left > 1.0 or rel_top > 1.0:
                    # Already in pixel coordinates
                    abs_left = rel_left
                    abs_top = rel_top
                    abs_width = rel_right - rel_left
                    abs_height = rel_bottom - rel_top
                else:
                    # Relative coordinates - convert to pixels
                    abs_left = rel_left * canvas_width
                    abs_top = rel_top * canvas_height
                    abs_width = (rel_right - rel_left) * canvas_width
                    abs_height = (rel_bottom - rel_top) * canvas_height
            else:
                # Fallback for old format
                abs_left, abs_top, abs_width, abs_height = canvas_x - 25, canvas_y - 15, 50, 30
            
            if element_type == 'vertex':
                # Draw vertex as a filled circle using absolute coordinates
                painter.setBrush(QBrush(QColor(0, 0, 0)))
                painter.setPen(QPen(QColor(0, 0, 0), 2))
                painter.drawEllipse(int(abs_left), int(abs_top), int(abs_width), int(abs_height))
                
            elif element_type == 'predicate':
                # Draw predicate as a rectangle (predicate box) using absolute coordinates
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.setPen(QPen(QColor(0, 0, 0), 2))
                painter.drawRect(int(abs_left), int(abs_top), int(abs_width), int(abs_height))
                
                # Add predicate text
                text_content = primitive.get('text_content', primitive.get('text', element_id))
                painter.drawText(int(abs_left + 5), int(abs_top + abs_height/2 + 5), text_content)
                
                # Debug: print coordinate conversion
                print(f"Element {element_id}: pos=({rel_x:.3f},{rel_y:.3f}) canvas_size=({canvas_width}x{canvas_height}) final_pos=({canvas_x:.1f},{canvas_y:.1f})")
                print(f"  bounds: {bounds} -> abs_bounds: ({abs_left:.1f},{abs_top:.1f},{abs_width:.1f},{abs_height:.1f})")
                
            elif element_type == 'cut':
                # Draw cut as an oval using absolute coordinates
                painter.setBrush(QBrush())  # No fill
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.drawEllipse(int(abs_left), int(abs_top), int(abs_width), int(abs_height))
                
            elif element_type == 'ligature':
                # Draw ligature as a heavy line using absolute coordinates
                painter.setPen(QPen(QColor(0, 0, 0), 4))  # Heavy line
                # For now, draw as a simple line - path data would be in primitive
                path = getattr(primitive, 'path', None) if hasattr(primitive, 'path') else primitive.get('path', [])
                if len(path) >= 2:
                    for i in range(len(path) - 1):
                        start_x, start_y = path[i]
                        end_x, end_y = path[i + 1]
                        painter.drawLine(
                            int(start_x * canvas_width), int(start_y * canvas_height),
                            int(end_x * canvas_width), int(end_y * canvas_height)
                        )
        

    
    def _draw_placeholder_elements(self, painter):
        """Draw placeholder diagram elements."""
        # Draw a simple example diagram
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        
        # Draw a predicate box
        painter.drawRect(50, 50, 80, 30)
        painter.drawText(55, 70, "Predicate")
        
        # Draw a vertex
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(200, 60, 10, 10)
        
        # Draw a line of identity
        painter.setPen(QPen(QColor(0, 0, 0), 3))
        painter.drawLine(130, 65, 200, 65)
        
        # Draw a cut
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawEllipse(30, 30, 200, 80)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        x, y = event.position().x(), event.position().y()
        
        # Emit canvas click signal
        self.canvas_clicked.emit(int(x), int(y))
        
        # Check for element selection (placeholder logic)
        if 50 <= x <= 130 and 50 <= y <= 80:
            self.element_selected.emit("predicate_1")
        elif 195 <= x <= 215 and 55 <= y <= 75:
            self.element_selected.emit("vertex_1")
    
    # Public API methods
    def clear(self):
        """Clear the canvas."""
        self.selected_elements.clear()
        self.update()
    
    def zoom_in(self):
        """Zoom in on the canvas."""
        self.zoom_factor *= 1.2
        self.update()
    
    def zoom_out(self):
        """Zoom out on the canvas."""
        self.zoom_factor /= 1.2
        self.update()
    
    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.zoom_factor = 1.0
        self.update()
    
    def set_selection(self, element_ids: List[str]):
        """Set selected elements."""
        self.selected_elements = element_ids.copy()
        self.update()
    
    def get_selection(self) -> List[str]:
        """Get currently selected elements."""
        return self.selected_elements.copy()
    
    def render_diagram(self, diagram_data: Any):
        """Render diagram data using existing GraphvizLayoutEngine pipeline."""
        # Store diagram data for rendering
        self.diagram_data = diagram_data
        
        # Extract spatial primitives from EGDF visual_layout (already processed by GraphvizLayoutEngine)
        self.spatial_primitives = []
        
        if hasattr(diagram_data, 'visual_layout') and 'spatial_primitives' in diagram_data.visual_layout:
            # Use the spatial primitives that were already generated by the canonical pipeline
            self.spatial_primitives = diagram_data.visual_layout['spatial_primitives']
            print(f"✓ Canvas: Using pre-computed spatial primitives: {len(self.spatial_primitives)} elements")
        else:
            print("⚠ Canvas: No spatial primitives found in EGDF visual_layout")
            print(f"⚠ Canvas: Available EGDF attributes: {[attr for attr in dir(diagram_data) if not attr.startswith('_')]}")
        
        self.update()
    
    def add_overlay(self, overlay_type: str, data: Any):
        """Add visual overlay (stub implementation)."""
        print(f"Adding overlay: {overlay_type}")
        self.update()
    
    def remove_overlay(self, overlay_type: str):
        """Remove visual overlay (stub implementation)."""
        print(f"Removing overlay: {overlay_type}")
        self.update()
