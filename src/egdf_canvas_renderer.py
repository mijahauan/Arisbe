#!/usr/bin/env python3
"""
EGDF Canvas Renderer - Clean Qt Implementation

A from-scratch Qt canvas implementation that directly renders EGDF spatial primitives
with perfect Dau compliance. This replaces the problematic existing canvas code.

Key Design Principles:
1. Direct EGDF → Qt rendering (no intermediate layers)
2. Proven spatial primitives from our working canonical pipeline
3. Simple, clean Qt drawing commands
4. Dau-compliant visual conventions
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from PySide6.QtCore import Qt, QPointF, QRectF
import math

class DauVisualStyle:
    """Dau-compliant visual styling for Existential Graphs."""
    
    def __init__(self):
        # Heavy identity lines (Dau's key convention)
        self.identity_line_width = 6.0
        self.identity_line_color = QColor(0, 0, 0)  # Black
        
        # Fine cut boundaries 
        self.cut_line_width = 1.5
        self.cut_line_color = QColor(0, 0, 0)  # Black
        self.cut_fill = None  # No fill
        
        # Vertex spots (identity markers)
        self.vertex_radius = 4.0
        self.vertex_color = QColor(0, 0, 0)  # Black filled
        
        # Predicate text
        self.predicate_font_family = "Arial"
        self.predicate_font_size = 12
        self.predicate_text_color = QColor(0, 0, 0)  # Black
        
        # Canvas
        self.background_color = QColor(255, 255, 255)  # White


class EGDFCanvasRenderer(QWidget):
    """
    Clean Qt canvas that renders EGDF spatial primitives directly.
    
    Takes EGDF spatial primitives from our proven canonical pipeline
    and renders them with perfect Dau compliance using Qt drawing commands.
    """
    
    def __init__(self, width: int = 800, height: int = 600, parent=None):
        super().__init__(parent)
        
        # Canvas properties
        self.canvas_width = width
        self.canvas_height = height
        self.setFixedSize(width, height)
        
        # Visual style
        self.style = DauVisualStyle()
        
        # EGDF data to render
        self.spatial_primitives: List[Dict[str, Any]] = []
        self.egi_graph = None  # For accessing relation names
        
        # Coordinate mapping
        self.logical_bounds: Tuple[float, float, float, float] = (0, 0, width, height)
        
        # Set background
        self.setStyleSheet(f"background-color: {self.style.background_color.name()};")
    
    def load_egdf(self, egdf_document, egi_graph=None):
        """Load EGDF document and prepare for rendering."""
        try:
            # Extract spatial primitives from EGDF
            if hasattr(egdf_document, 'visual_layout') and egdf_document.visual_layout:
                self.spatial_primitives = egdf_document.visual_layout.get('spatial_primitives', [])
                self.egi_graph = egi_graph
                
                # Calculate logical bounds from spatial primitives
                self._calculate_logical_bounds()
                
                print(f"✓ EGDF loaded: {len(self.spatial_primitives)} spatial primitives")
                
                # Trigger repaint
                self.update()
                return True
            else:
                print("⚠ No visual_layout in EGDF document")
                return False
                
        except Exception as e:
            print(f"❌ Failed to load EGDF: {e}")
            return False
    
    def _calculate_logical_bounds(self):
        """Calculate logical coordinate bounds from spatial primitives."""
        if not self.spatial_primitives:
            return
        
        # Find min/max coordinates from all primitives
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for prim in self.spatial_primitives:
            if isinstance(prim, dict) and 'bounds' in prim:
                x1, y1, x2, y2 = prim['bounds']
                min_x = min(min_x, x1)
                min_y = min(min_y, y1)
                max_x = max(max_x, x2)
                max_y = max(max_y, y2)
            elif isinstance(prim, dict) and 'position' in prim:
                x, y = prim['position']
                min_x = min(min_x, x - 10)  # Add padding
                min_y = min(min_y, y - 10)
                max_x = max(max_x, x + 10)
                max_y = max(max_y, y + 10)
        
        # Add padding
        padding = 20
        self.logical_bounds = (
            min_x - padding,
            min_y - padding, 
            max_x + padding,
            max_y + padding
        )
        
        print(f"✓ Logical bounds: {self.logical_bounds}")
    
    def _map_coordinate(self, logical_x: float, logical_y: float) -> Tuple[float, float]:
        """Map logical coordinates to canvas pixel coordinates."""
        lx1, ly1, lx2, ly2 = self.logical_bounds
        
        # Map to canvas coordinates
        canvas_x = ((logical_x - lx1) / (lx2 - lx1)) * self.canvas_width
        canvas_y = ((logical_y - ly1) / (ly2 - ly1)) * self.canvas_height
        
        return canvas_x, canvas_y
    
    def paintEvent(self, event):
        """Qt paint event - render all EGDF spatial primitives."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Clear background
        painter.fillRect(self.rect(), self.style.background_color)
        
        if not self.spatial_primitives:
            # Show "No diagram loaded" message
            painter.setPen(QPen(QColor(128, 128, 128), 1))
            painter.drawText(self.rect(), Qt.AlignCenter, "No diagram loaded")
            return
        
        # CRITICAL: Clear and rebuild actual drawn positions for hit detection
        self.actual_drawn_positions = {}
        
        # Render all elements in z-order
        self._render_cuts(painter)
        self._render_predicates(painter)
        self._render_vertices(painter)
        self._render_text_primitives(painter)
        self._render_identity_lines(painter)
        
        print(f"✓ Rendered {len(self.spatial_primitives)} spatial primitives")
        print(f"✓ Captured {len(self.actual_drawn_positions)} actual drawn positions")
    
    def _render_cuts(self, painter: QPainter):
        """Render cut boundaries as rounded rectangles."""
        pen = QPen(self.style.cut_line_color, self.style.cut_line_width)
        painter.setPen(pen)
        painter.setBrush(QBrush())  # No fill
        
        for prim in self.spatial_primitives:
            if isinstance(prim, dict) and prim.get('element_type') == 'cut':
                bounds = prim.get('bounds')
                if bounds:
                    x1, y1, x2, y2 = bounds
                    
                    # Map to canvas coordinates
                    cx1, cy1 = self._map_coordinate(x1, y1)
                    cx2, cy2 = self._map_coordinate(x2, y2)
                    
                    # Draw rounded rectangle (preserves full area)
                    rect = QRectF(cx1, cy1, cx2 - cx1, cy2 - cy1)
                    corner_radius = 8.0  # Dau-compliant rounded corners
                    painter.drawRoundedRect(rect, corner_radius, corner_radius)
    
    def _render_predicates(self, painter: QPainter):
        """Render predicate text."""
        font = QFont(self.style.predicate_font_family, self.style.predicate_font_size)
        painter.setFont(font)
        painter.setPen(QPen(self.style.predicate_text_color, 1))
        
        for prim in self.spatial_primitives:
            if isinstance(prim, dict) and prim.get('element_type') == 'predicate':
                position = prim.get('position')
                element_id = prim.get('element_id')
                
                if position and element_id:
                    x, y = position
                    cx, cy = self._map_coordinate(x, y)
                    
                    # Get predicate name from display_name field (consistent with Preparation canvas)
                    predicate_name = prim.get('display_name') or self._get_predicate_name(element_id)
                    
                    # Draw text centered at position
                    painter.drawText(QPointF(cx, cy), predicate_name)
                    
                    # CRITICAL: Capture actual drawn position and bounds for hit detection
                    text_width = len(predicate_name) * 8  # Estimate text width
                    text_height = 16  # Estimate text height
                    actual_bounds = (
                        cx - text_width/2,  # left
                        cy - text_height/2, # top
                        cx + text_width/2,  # right
                        cy + text_height/2  # bottom
                    )
                    self.actual_drawn_positions[element_id] = {
                        'element_type': 'predicate',
                        'pixel_position': (cx, cy),
                        'pixel_bounds': actual_bounds
                    }
                    print(f"📍 Captured predicate {element_id} at pixel ({cx:.1f}, {cy:.1f}), bounds {actual_bounds}")
    
    def _render_vertices(self, painter: QPainter):
        """Render vertex spots as filled circles with constant names."""
        pen = QPen(self.style.vertex_color, 1)
        brush = QBrush(self.style.vertex_color)
        painter.setPen(pen)
        painter.setBrush(brush)
        
        for prim in self.spatial_primitives:
            if isinstance(prim, dict) and prim.get('element_type') == 'vertex':
                position = prim.get('position')
                element_id = prim.get('element_id')
                if position:
                    x, y = position
                    cx, cy = self._map_coordinate(x, y)
                    
                    # Draw filled circle (vertex spot)
                    painter.drawEllipse(
                        QPointF(cx, cy),
                        self.style.vertex_radius,
                        self.style.vertex_radius
                    )
                    
                    # Render vertex constant name (like "Socrates") if available
                    vertex_name = prim.get('display_name')
                    if vertex_name:
                        # Position text next to vertex spot
                        text_x = cx + self.style.vertex_radius + 8
                        text_y = cy + 4  # Slightly below center
                        
                        # Set font for vertex labels
                        vertex_font = QFont(self.style.predicate_font_family, 10)
                        painter.setFont(vertex_font)
                        painter.setPen(QPen(self.style.predicate_text_color, 1))
                        
                        painter.drawText(QPointF(text_x, text_y), vertex_name)
                        print(f"📝 Rendered vertex label '{vertex_name}' at ({text_x:.1f}, {text_y:.1f})")
                    
                    # CRITICAL: Capture actual drawn position and bounds for hit detection
                    radius = self.style.vertex_radius
                    actual_bounds = (
                        cx - radius,  # left
                        cy - radius,  # top
                        cx + radius,  # right
                        cy + radius   # bottom
                    )
                    self.actual_drawn_positions[element_id] = {
                        'element_type': 'vertex',
                        'pixel_position': (cx, cy),
                        'pixel_bounds': actual_bounds
                    }
                    print(f"📍 Captured vertex {element_id} at pixel ({cx:.1f}, {cy:.1f}), bounds {actual_bounds}")
    
    def _render_text_primitives(self, painter: QPainter):
        """Render text primitives generated by EGDF specification."""
        font = QFont(self.style.predicate_font_family, self.style.predicate_font_size)
        painter.setFont(font)
        painter.setPen(QPen(self.style.predicate_text_color, 1))
        
        for prim in self.spatial_primitives:
            if isinstance(prim, dict) and prim.get('element_type') == 'text':
                position = prim.get('position')
                text_content = prim.get('text_content')
                
                if position and text_content:
                    x, y = position
                    cx, cy = self._map_coordinate(x, y)
                    painter.drawText(QPointF(cx, cy), text_content)
    
    def _render_identity_lines(self, painter: QPainter):
        """Render heavy identity lines using proper ligature primitives."""
        pen = QPen(self.style.identity_line_color, self.style.identity_line_width)
        painter.setPen(pen)
        
        # Render each ligature primitive as a separate line
        for prim in self.spatial_primitives:
            if isinstance(prim, dict) and prim.get('element_type') == 'identity_line':
                curve_points = prim.get('curve_points', [])
                
                if len(curve_points) >= 2:
                    # Draw line segments between consecutive points
                    for i in range(len(curve_points) - 1):
                        start_x, start_y = curve_points[i]
                        end_x, end_y = curve_points[i + 1]
                        
                        # Map to canvas coordinates
                        cs_x, cs_y = self._map_coordinate(start_x, start_y)
                        ce_x, ce_y = self._map_coordinate(end_x, end_y)
                        
                        # Draw heavy line segment
                        painter.drawLine(QPointF(cs_x, cs_y), QPointF(ce_x, ce_y))
    
    def _get_predicate_name(self, element_id: str) -> str:
        """Get predicate name from EGI graph relations."""
        if self.egi_graph and hasattr(self.egi_graph, 'rel'):
            return self.egi_graph.rel.get(element_id, element_id)
        return element_id
    

    
    def clear_diagram(self):
        """Clear the current diagram."""
        self.spatial_primitives = []
        self.egi_graph = None
        self.update()
    
    def find_element_at_point(self, x: float, y: float) -> Optional[str]:
        """Find element at given canvas coordinates using actual drawn positions."""
        print(f"🔍 Hit test at canvas point ({x:.1f}, {y:.1f})")
        
        # CRITICAL: Use actual drawn positions captured during rendering
        if not hasattr(self, 'actual_drawn_positions') or not self.actual_drawn_positions:
            print(f"  ❌ No actual drawn positions available - renderer hasn't captured them yet")
            return None
        
        # Check all actual drawn positions for hits
        for element_id, drawn_info in self.actual_drawn_positions.items():
            element_type = drawn_info.get('element_type')
            pixel_bounds = drawn_info.get('pixel_bounds')
            
            if not pixel_bounds:
                continue
                
            left, top, right, bottom = pixel_bounds
            print(f"  🎯 Checking {element_type} {element_id}: pixel bounds ({left:.1f}, {top:.1f}, {right:.1f}, {bottom:.1f})")
            
            if left <= x <= right and top <= y <= bottom:
                print(f"  ✅ HIT: {element_id} at actual drawn position!")
                return element_id
            else:
                print(f"  ❌ MISS: {element_id} - point outside actual drawn bounds")
        
        print(f"  ❌ No element found at ({x:.1f}, {y:.1f}) in actual drawn positions")
        return None
    
    def get_element_visual_bounds(self, element_id: str) -> Optional[tuple]:
        """Get visual bounds of element using actual drawn positions."""
        print(f"🔍 Getting visual bounds for element: {element_id}")
        
        # CRITICAL: Use actual drawn positions captured during rendering
        if hasattr(self, 'actual_drawn_positions') and element_id in self.actual_drawn_positions:
            drawn_info = self.actual_drawn_positions[element_id]
            pixel_bounds = drawn_info.get('pixel_bounds')
            if pixel_bounds:
                print(f"✅ Found actual drawn bounds for {element_id}: {pixel_bounds}")
                return pixel_bounds
        
        print(f"❌ No actual drawn bounds found for element: {element_id}")
        return None


def create_egdf_canvas(width: int = 800, height: int = 600) -> EGDFCanvasRenderer:
    """Factory function to create an EGDF canvas renderer."""
    return EGDFCanvasRenderer(width, height)


if __name__ == "__main__":
    # Test the EGDF canvas renderer
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    canvas = create_egdf_canvas(800, 600)
    canvas.show()
    
    print("🎨 EGDF Canvas Renderer Test")
    print("Canvas created and displayed")
    
    sys.exit(app.exec())
