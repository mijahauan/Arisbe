#!/usr/bin/env python3
"""
Peirce Visual Conventions Module

This module implements Peirce's specific visual conventions for Existential Graphs:
- Thin lines for cuts (ovals/closed curves)
- Heavy lines for ligatures (lines of identity)
- Alternating shading for odd and even nesting levels
- Proper cut shapes (ovals, not rectangles)
- Consistent visual styling
"""

from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import math

@dataclass
class PeirceVisualStyle:
    """Peirce's specific visual conventions."""
    
    # Line styles
    cut_line_width: float = 2.0      # Thin lines for cuts
    ligature_line_width: float = 4.0  # Heavy lines for ligatures
    
    # Colors and shading (alternating by nesting level)
    even_level_fill: str = "#FFFFFF"    # White for even levels (0, 2, 4...)
    odd_level_fill: str = "#E8E8E8"     # Light gray for odd levels (1, 3, 5...)
    cut_stroke: str = "#000000"         # Black for cut outlines
    ligature_stroke: str = "#000000"    # Black for ligatures
    predicate_color: str = "#000000"    # Black text for predicates
    entity_color: str = "#000000"       # Black for entities
    
    # Typography
    predicate_font_size: int = 14       # Font size for predicate text
    predicate_font_family: str = "Arial" # Font family for predicates
    predicate_font_weight: str = "normal" # Font weight for predicates
    
    # Cut shape properties
    cut_corner_radius: float = 20.0     # Radius for rounded corners (oval-like)
    cut_oval_factor: float = 0.8        # Factor to make cuts more oval-like
    
    # Spacing and padding
    element_padding: float = 15.0       # Padding around elements
    cut_padding: float = 25.0           # Extra padding inside cuts
    min_element_spacing: float = 20.0   # Minimum space between elements
    ligature_endpoint_margin: float = 5.0  # Margin from element edge for ligature endpoints

class PeirceVisualConventions:
    """
    Applies Peirce's visual conventions to layout elements.
    """
    
    def __init__(self):
        self.style = PeirceVisualStyle()
    
    def apply_visual_conventions(self, layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply Peirce's visual conventions to the layout data.
        
        Args:
            layout_data: Dictionary with positioned elements
            
        Returns:
            Enhanced layout data with visual styling applied
        """
        enhanced_layout = {}
        
        for element_id, element_data in layout_data.items():
            enhanced_element = element_data.copy()
            
            # Apply visual styling based on element type and nesting level
            element_type = element_data.get('type', 'unknown')
            nesting_level = element_data.get('nesting_level', 0)
            
            if element_type == 'context':
                enhanced_element['visual_style'] = self._get_context_style(nesting_level)
                enhanced_element['shape'] = self._get_context_shape(element_data)
            elif element_type == 'predicate':
                enhanced_element['visual_style'] = self._get_predicate_style()
                enhanced_element['text_style'] = self._get_text_style()
            elif element_type == 'entity':
                enhanced_element['visual_style'] = self._get_entity_style()
                enhanced_element['line_segments'] = self._enhance_ligature_style(
                    element_data.get('line_segments', [])
                )
            
            enhanced_layout[element_id] = enhanced_element
        
        return enhanced_layout
    
    def _get_context_style(self, nesting_level: int) -> Dict[str, Any]:
        """Get visual style for context elements (cuts/sheet)."""
        # Alternating shading based on nesting level
        if nesting_level % 2 == 0:
            fill_color = self.style.even_level_fill
        else:
            fill_color = self.style.odd_level_fill
        
        return {
            'fill_color': fill_color,
            'stroke_color': self.style.cut_stroke,
            'line_width': self.style.cut_line_width,
            'opacity': 0.7 if nesting_level > 0 else 1.0  # Slight transparency for cuts
        }
    
    def _get_context_shape(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get shape properties for context elements."""
        position = element_data.get('position', (0, 0))
        size = element_data.get('size', (100, 100))
        nesting_level = element_data.get('nesting_level', 0)
        
        x, y = position
        width, height = size
        
        if nesting_level == 0:
            # Sheet of assertion - rectangular
            return {
                'type': 'rectangle',
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'corner_radius': 0
            }
        else:
            # Cuts - oval-like shapes
            return {
                'type': 'oval',
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'corner_radius': min(width, height) * 0.3  # More oval-like
            }
    
    def _get_predicate_style(self) -> Dict[str, Any]:
        """Get visual style for predicate elements."""
        return {
            'fill_color': 'transparent',
            'stroke_color': 'transparent',
            'text_color': self.style.predicate_color,
            'line_width': 0
        }
    
    def _get_text_style(self) -> Dict[str, Any]:
        """Get text styling for predicates."""
        return {
            'font_family': self.style.predicate_font_family,
            'font_size': self.style.predicate_font_size,
            'font_weight': self.style.predicate_font_weight,
            'text_align': 'center',
            'vertical_align': 'middle'
        }
    
    def _get_entity_style(self) -> Dict[str, Any]:
        """Get visual style for entity elements."""
        return {
            'fill_color': 'transparent',
            'stroke_color': 'transparent',
            'line_width': 0,
            'visible': False  # Entities are invisible - only their ligatures are visible
        }
    
    def _enhance_ligature_style(self, line_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance ligature line segments with proper styling."""
        enhanced_segments = []
        
        for segment in line_segments:
            enhanced_segment = segment.copy()
            
            # Apply heavy line styling for ligatures
            enhanced_segment['style'] = {
                'stroke_color': self.style.ligature_stroke,
                'line_width': self.style.ligature_line_width,
                'line_cap': 'round',  # Rounded line caps
                'line_join': 'round'  # Rounded line joins
            }
            
            # Adjust endpoints to not overlap with element boundaries
            start = segment.get('start', (0, 0))
            end = segment.get('end', (0, 0))
            
            enhanced_segment['start'] = self._adjust_ligature_endpoint(start, end, True)
            enhanced_segment['end'] = self._adjust_ligature_endpoint(end, start, False)
            
            enhanced_segments.append(enhanced_segment)
        
        return enhanced_segments
    
    def _adjust_ligature_endpoint(self, point: Tuple[float, float], 
                                 other_point: Tuple[float, float], 
                                 is_start: bool) -> Tuple[float, float]:
        """Adjust ligature endpoint to maintain margin from element boundaries."""
        x, y = point
        other_x, other_y = other_point
        
        # Calculate direction vector
        dx = other_x - x
        dy = other_y - y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return point
        
        # Normalize direction vector
        dx_norm = dx / length
        dy_norm = dy / length
        
        # Apply margin
        margin = self.style.ligature_endpoint_margin
        if is_start:
            # Move start point slightly toward the end
            adjusted_x = x + dx_norm * margin
            adjusted_y = y + dy_norm * margin
        else:
            # Move end point slightly toward the start
            adjusted_x = x - dx_norm * margin
            adjusted_y = y - dy_norm * margin
        
        return (adjusted_x, adjusted_y)
    
    def get_rendering_instructions(self, enhanced_layout: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate rendering instructions for the GUI.
        
        Args:
            enhanced_layout: Layout data with visual conventions applied
            
        Returns:
            Rendering instructions for the graphics system
        """
        instructions = {
            'elements': [],
            'ligatures': [],
            'z_order': []  # Rendering order (back to front)
        }
        
        # Sort elements by nesting level for proper z-ordering
        elements_by_level = {}
        for element_id, element_data in enhanced_layout.items():
            level = element_data.get('nesting_level', 0)
            if level not in elements_by_level:
                elements_by_level[level] = []
            elements_by_level[level].append((element_id, element_data))
        
        # Add elements in z-order (lowest level first, but ligatures always on top)
        for level in sorted(elements_by_level.keys()):
            # First add contexts for this level
            for element_id, element_data in elements_by_level[level]:
                element_type = element_data.get('type', 'unknown')
                
                if element_type == 'context':
                    instructions['elements'].append({
                        'id': element_id,
                        'type': 'context',
                        'shape': element_data.get('shape', {}),
                        'style': element_data.get('visual_style', {}),
                        'z_index': level * 10  # Contexts at base z-index for their level
                    })
            
            # Then add predicates for this level
            for element_id, element_data in elements_by_level[level]:
                element_type = element_data.get('type', 'unknown')
                
                if element_type == 'predicate':
                    instructions['elements'].append({
                        'id': element_id,
                        'type': 'predicate',
                        'position': element_data.get('position', (0, 0)),
                        'size': element_data.get('size', (0, 0)),
                        'text': self._get_predicate_text(element_data),
                        'style': element_data.get('visual_style', {}),
                        'z_index': level * 10 + 5  # Predicates above contexts
                    })
        
        # Add ligatures last (highest z-index) so they appear on top
        max_z_index = (max(elements_by_level.keys()) + 1) * 10 if elements_by_level else 100
        for level in sorted(elements_by_level.keys()):
            for element_id, element_data in elements_by_level[level]:
                element_type = element_data.get('type', 'unknown')
                
                if element_type == 'entity':
                    # Process ligatures for this entity
                    line_segments = element_data.get('line_segments', [])
                    for i, segment in enumerate(line_segments):
                        instructions['ligatures'].append({
                            'id': f"{element_id}_ligature_{i}",
                            'start': segment.get('start', (0, 0)),
                            'end': segment.get('end', (0, 0)),
                            'style': {
                                'stroke_color': self.style.ligature_stroke,
                                'stroke_width': self.style.ligature_line_width,
                                'line_cap': 'round'
                            },
                            'z_index': max_z_index  # Ligatures always on top
                        })
        
        return instructions
    
    def _get_predicate_text(self, element_data: Dict[str, Any]) -> str:
        """Extract predicate text from element data."""
        # Use the actual name from the element data
        return element_data.get('name', 'P')

def test_peirce_visual_conventions():
    """Test the Peirce visual conventions module."""
    conventions = PeirceVisualConventions()
    
    # Test with sample layout data
    sample_layout = {
        'context_1': {
            'type': 'context',
            'position': (100, 100),
            'size': (200, 150),
            'nesting_level': 1
        },
        'predicate_1': {
            'type': 'predicate',
            'position': (150, 150),
            'size': (80, 40),
            'nesting_level': 1,
            'name': 'Man'
        }
    }
    
    enhanced = conventions.apply_visual_conventions(sample_layout)
    instructions = conventions.get_rendering_instructions(enhanced)
    
    print("✓ Peirce Visual Conventions applied successfully")
    print(f"✓ Generated {len(instructions['elements'])} element instructions")
    print(f"✓ Generated {len(instructions['ligatures'])} ligature instructions")

if __name__ == "__main__":
    test_peirce_visual_conventions()

