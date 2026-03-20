"""
Abstract Layout Units (ALU) Coordinate System

Provides view-independent layout calculations with automatic scaling to device pixels.
This enables consistent spatial relationships across different rendering contexts
(screen, print, export) while maintaining proper proportions and readability.

Key Features:
- View-independent calculations in abstract units
- Automatic scaling based on rendering context
- Minimum readability constraints (8px text minimum)
- Adaptive fitting to available space
"""

from typing import Dict, Tuple
from enum import Enum
from dataclasses import dataclass
from PySide6.QtCore import QRectF, QPointF, QSizeF


class ViewContext(Enum):
    """Different rendering contexts with their scaling requirements."""
    SCREEN = "screen"      # Interactive display
    PRINT = "print"        # High-resolution printing
    EXPORT = "export"      # Image/SVG export
    THUMBNAIL = "thumbnail"  # Small preview


@dataclass
class ViewSpecification:
    """Specification for a particular view context."""
    base_scale: float      # Base ALU → pixels conversion
    min_text_height: float # Minimum text height in pixels
    max_scale: float       # Maximum allowed scale
    min_scale: float       # Minimum allowed scale


class ALUCoordinateSystem:
    """
    Abstract Layout Units coordinate system with view-specific scaling.
    
    All layout calculations are performed in ALU, then converted to device
    pixels based on the target view context and available space.
    """
    
    def __init__(self):
        # View specifications (ALU → pixels)
        self.view_specs = {
            ViewContext.SCREEN: ViewSpecification(
                base_scale=20.0,      # 20 pixels per ALU
                min_text_height=8.0,  # 8px minimum text
                max_scale=50.0,       # 50px per ALU maximum
                min_scale=5.0         # 5px per ALU minimum
            ),
            ViewContext.PRINT: ViewSpecification(
                base_scale=72.0,      # 72 points per ALU (1 inch at 72 DPI)
                min_text_height=6.0,  # 6pt minimum text
                max_scale=144.0,      # 144pt per ALU maximum
                min_scale=18.0        # 18pt per ALU minimum
            ),
            ViewContext.EXPORT: ViewSpecification(
                base_scale=100.0,     # 100 pixels per ALU (high resolution)
                min_text_height=12.0, # 12px minimum text
                max_scale=200.0,      # 200px per ALU maximum
                min_scale=25.0        # 25px per ALU minimum
            ),
            ViewContext.THUMBNAIL: ViewSpecification(
                base_scale=8.0,       # 8 pixels per ALU (compact)
                min_text_height=6.0,  # 6px minimum text
                max_scale=16.0,       # 16px per ALU maximum
                min_scale=4.0         # 4px per ALU minimum
            )
        }
    
    def calculate_optimal_scale(self, alu_bounds: Dict[str, 'ALURect'], 
                              available_size: QSizeF, 
                              view_context: ViewContext) -> float:
        """
        Calculate optimal scale factor to fit ALU layout in available space
        while maintaining readability constraints.
        
        Args:
            alu_bounds: Dictionary of ALU rectangles to fit
            available_size: Available space in device pixels
            view_context: Target rendering context
            
        Returns:
            Optimal scale factor (ALU → pixels)
        """
        spec = self.view_specs[view_context]
        
        if not alu_bounds:
            return spec.base_scale
        
        # Calculate total ALU bounds
        min_x = min(rect.x for rect in alu_bounds.values())
        max_x = max(rect.x + rect.width for rect in alu_bounds.values())
        min_y = min(rect.y for rect in alu_bounds.values())
        max_y = max(rect.y + rect.height for rect in alu_bounds.values())
        
        total_alu_width = max_x - min_x
        total_alu_height = max_y - min_y
        
        # Calculate scale factors to fit in available space
        if total_alu_width > 0 and total_alu_height > 0:
            scale_x = available_size.width() / total_alu_width
            scale_y = available_size.height() / total_alu_height
            fit_scale = min(scale_x, scale_y) * 0.9  # 90% to leave margins
        else:
            fit_scale = spec.base_scale
        
        # Apply constraints
        optimal_scale = max(spec.min_scale, min(spec.max_scale, fit_scale))
        
        # Ensure text readability
        if optimal_scale < spec.min_text_height / 1.0:  # Assume 1 ALU = standard text height
            optimal_scale = max(optimal_scale, spec.min_text_height / 1.0)
        
        print(f"ALU scale calculation: {total_alu_width:.1f}×{total_alu_height:.1f} ALU "
              f"→ {available_size.width():.0f}×{available_size.height():.0f}px "
              f"= {optimal_scale:.1f}px/ALU ({view_context.value})")
        
        return optimal_scale
    
    def convert_alu_to_device(self, alu_bounds: Dict[str, 'ALURect'], 
                             scale: float) -> Dict[str, QRectF]:
        """
        Convert ALU bounds to device pixel coordinates.
        
        Args:
            alu_bounds: Dictionary of ALU rectangles
            scale: Scale factor (ALU → pixels)
            
        Returns:
            Dictionary of QRectF in device pixels
        """
        device_bounds = {}
        
        for area_id, alu_rect in alu_bounds.items():
            device_bounds[area_id] = alu_rect.to_qrectf(scale)
        
        return device_bounds
    
    def get_element_positions(self, alu_bounds: Dict[str, 'ALURect'], 
                            scale: float) -> Dict[str, QPointF]:
        """
        Get element center positions in device coordinates.
        
        Args:
            alu_bounds: Dictionary of ALU rectangles
            scale: Scale factor (ALU → pixels)
            
        Returns:
            Dictionary of center points in device pixels
        """
        positions = {}
        
        for area_id, alu_rect in alu_bounds.items():
            center_x, center_y = alu_rect.center()
            positions[area_id] = QPointF(center_x * scale, center_y * scale)
        
        return positions
    
    def get_view_specification(self, view_context: ViewContext) -> ViewSpecification:
        """Get view specification for a rendering context."""
        return self.view_specs[view_context]
    
    def create_viewport_bounds(self, alu_bounds: Dict[str, 'ALURect'], 
                             scale: float, margin: float = 20.0) -> QRectF:
        """
        Create viewport bounds that encompass all elements with margin.
        
        Args:
            alu_bounds: Dictionary of ALU rectangles
            scale: Scale factor (ALU → pixels)
            margin: Margin in device pixels
            
        Returns:
            Viewport bounds in device pixels
        """
        if not alu_bounds:
            return QRectF(-100, -100, 200, 200)
        
        # Convert to device coordinates
        device_bounds = self.convert_alu_to_device(alu_bounds, scale)
        
        # Calculate encompassing bounds
        min_x = min(rect.x() for rect in device_bounds.values())
        max_x = max(rect.x() + rect.width() for rect in device_bounds.values())
        min_y = min(rect.y() for rect in device_bounds.values())
        max_y = max(rect.y() + rect.height() for rect in device_bounds.values())
        
        # Add margin
        viewport = QRectF(
            min_x - margin,
            min_y - margin,
            (max_x - min_x) + 2 * margin,
            (max_y - min_y) + 2 * margin
        )
        
        return viewport

    def scale_polygon(self, polygon: 'Polygon', scale: float) -> 'Polygon':
        """
        Scale a shapely Polygon by a given factor.

        Args:
            polygon: The input shapely Polygon.
            scale: The factor to scale by.

        Returns:
            A new, scaled shapely Polygon.
        """
        from shapely.geometry import Polygon

        def scale_coords(coords):
            return [(x * scale, y * scale) for x, y in coords]

        if not polygon or polygon.is_empty:
            return polygon

        # Scale the exterior
        new_exterior = scale_coords(polygon.exterior.coords)

        # Scale all interior holes
        new_interiors = [scale_coords(interior.coords) for interior in polygon.interiors]

        return Polygon(new_exterior, new_interiors)
