"""
Style-Aware Layout System - Integration between Layout Engine and Style System

This module bridges the Layout Engine with the existing style infrastructure to support:
1. Dau Compliant - Mathematical precision, clean formal appearance
2. Sowa Compliant - Conceptual graph conventions  
3. Peirce Handwritten - Organic, irregular, manuscript-like
4. User Defined - Customizable styling

Key insight: Visual style directly affects spatial layout calculations.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import math

from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_engine import LayoutEngine, LayoutResult, Point, BoundingBox


@dataclass(frozen=True)
class StyleLayoutParameters:
    """Layout parameters extracted from visual style"""
    
    # Spacing parameters
    element_spacing: float           # Distance between elements
    diagram_margin: float           # Margin around entire diagram
    cut_padding: float              # Space inside cuts
    cut_nesting_margin: float       # Extra space for nested cuts
    
    # Element sizing
    vertex_radius: float            # Vertex visual size affects spacing
    line_thickness: float           # Line thickness affects visual separation
    font_size: float                # Font size affects text bounds
    
    # Layout algorithm preferences
    prefer_equal_spacing: bool      # Distribute elements evenly in areas
    prefer_centered_layout: bool    # Center single elements in areas
    prefer_grid_alignment: bool     # Snap to grid positions
    
    # Style-specific layout rules
    use_organic_positioning: bool   # Peirce handwritten style
    use_mathematical_precision: bool # Dau compliant style
    use_conceptual_grouping: bool   # Sowa compliant style


class StyleAwareLayoutEngine:
    """Enhanced layout engine that adapts to visual style requirements"""
    
    def __init__(self):
        self.base_engine = LayoutEngine()
    
    def compute_style_aware_layout(self, 
                                 egi: RelationalGraphWithCuts,
                                 diagram_style: 'DiagramStyle',
                                 view_config: Optional['ViewConfiguration'] = None) -> LayoutResult:
        """
        Compute layout that adapts to the specific visual style requirements
        """
        # Extract style-specific layout parameters
        layout_params = self._extract_layout_parameters(diagram_style)
        
        # Choose layout algorithm based on style
        if layout_params.use_organic_positioning:
            return self._compute_organic_layout(egi, layout_params, view_config)
        elif layout_params.use_mathematical_precision:
            return self._compute_mathematical_layout(egi, layout_params, view_config)
        elif layout_params.use_conceptual_grouping:
            return self._compute_conceptual_layout(egi, layout_params, view_config)
        else:
            # Default to enhanced base layout with style parameters
            return self.base_engine.compute_layout(egi, view_config, diagram_style)
    
    def _extract_layout_parameters(self, diagram_style: 'DiagramStyle') -> StyleLayoutParameters:
        """Extract layout-affecting parameters from visual style"""
        
        layout_style = diagram_style.get_layout_style()
        cut_style = diagram_style.get_cut_style()
        vertex_style = diagram_style.get_vertex_style()
        label_style = diagram_style.get_label_style()
        
        # Determine style-specific layout preferences
        style_id = diagram_style.style_id
        
        return StyleLayoutParameters(
            # Basic spacing from style
            element_spacing=layout_style.element_spacing,
            diagram_margin=layout_style.diagram_margin,
            cut_padding=cut_style.padding,
            cut_nesting_margin=cut_style.nesting_margin,
            
            # Element sizing affects layout
            vertex_radius=vertex_style.radius,
            line_thickness=cut_style.line_width,
            font_size=label_style.font_size,
            
            # Layout preferences based on style type
            prefer_equal_spacing=True,
            prefer_centered_layout=True,
            prefer_grid_alignment="dau" in style_id.lower(),
            
            # Style-specific algorithms
            use_organic_positioning="peirce" in style_id.lower() and "handwritten" in style_id.lower(),
            use_mathematical_precision="dau" in style_id.lower(),
            use_conceptual_grouping="sowa" in style_id.lower()
        )
    
    def _compute_organic_layout(self, 
                              egi: RelationalGraphWithCuts,
                              params: StyleLayoutParameters,
                              view_config: Optional['ViewConfiguration']) -> LayoutResult:
        """
        Peirce handwritten style - organic, slightly irregular positioning
        """
        vertex_positions = {}
        
        # Organic positioning with slight irregularity
        x, y = params.diagram_margin, params.diagram_margin
        irregularity_factor = 0.15  # 15% position variation
        
        for i, vertex in enumerate(egi.V):
            # Add slight organic variation to grid positions
            x_offset = math.sin(i * 0.7) * params.element_spacing * irregularity_factor
            y_offset = math.cos(i * 1.1) * params.element_spacing * irregularity_factor
            
            vertex_positions[vertex.id] = Point(x + x_offset, y + y_offset)
            
            x += params.element_spacing
            if x > 400:  # TODO: Make configurable
                x = params.diagram_margin
                y += params.element_spacing
        
        # Calculate cut bounds with organic margins
        cut_bounds = self._calculate_organic_cut_bounds(egi, vertex_positions, params)
        
        # Calculate viewport
        viewport = self._calculate_viewport(vertex_positions, cut_bounds, params)
        
        return LayoutResult(
            cut_bounds=cut_bounds,
            vertex_positions=vertex_positions,
            edge_paths={},  # TODO: Implement organic ligature routing
            viewport_bounds=viewport
        )
    
    def _compute_mathematical_layout(self, 
                                   egi: RelationalGraphWithCuts,
                                   params: StyleLayoutParameters,
                                   view_config: Optional['ViewConfiguration']) -> LayoutResult:
        """
        Dau compliant style - precise, grid-aligned, mathematical
        """
        vertex_positions = {}
        
        # Precise grid positioning
        grid_size = params.element_spacing
        x, y = params.diagram_margin, params.diagram_margin
        
        for vertex in egi.V:
            # Snap to precise grid positions
            grid_x = round(x / grid_size) * grid_size
            grid_y = round(y / grid_size) * grid_size
            
            vertex_positions[vertex.id] = Point(grid_x, grid_y)
            
            x += grid_size
            if x > 400:  # TODO: Make configurable
                x = params.diagram_margin
                y += grid_size
        
        # Calculate cut bounds with precise margins
        cut_bounds = self._calculate_precise_cut_bounds(egi, vertex_positions, params)
        
        # Calculate viewport
        viewport = self._calculate_viewport(vertex_positions, cut_bounds, params)
        
        return LayoutResult(
            cut_bounds=cut_bounds,
            vertex_positions=vertex_positions,
            edge_paths={},  # TODO: Implement orthogonal ligature routing
            viewport_bounds=viewport
        )
    
    def _compute_conceptual_layout(self, 
                                 egi: RelationalGraphWithCuts,
                                 params: StyleLayoutParameters,
                                 view_config: Optional['ViewConfiguration']) -> LayoutResult:
        """
        Sowa compliant style - conceptual grouping, hierarchical
        """
        # TODO: Implement Sowa-style conceptual grouping
        # For now, use mathematical layout as base
        return self._compute_mathematical_layout(egi, params, view_config)
    
    def _calculate_organic_cut_bounds(self, 
                                    egi: RelationalGraphWithCuts,
                                    vertex_positions: Dict[ElementID, Point],
                                    params: StyleLayoutParameters) -> Dict[ElementID, BoundingBox]:
        """Calculate cut bounds with organic, slightly irregular margins"""
        cut_bounds = {}
        
        for cut in egi.Cut:
            cut_elements = egi.area.get(cut.id, frozenset())
            if cut_elements:
                xs = [vertex_positions[eid].x for eid in cut_elements if eid in vertex_positions]
                ys = [vertex_positions[eid].y for eid in cut_elements if eid in vertex_positions]
                
                if xs and ys:
                    # Organic margins with slight variation
                    base_margin = params.cut_padding
                    margin_variation = base_margin * 0.2  # 20% variation
                    
                    left_margin = base_margin + math.sin(len(xs)) * margin_variation
                    right_margin = base_margin + math.cos(len(ys)) * margin_variation
                    top_margin = base_margin + math.sin(len(xs) * 1.3) * margin_variation
                    bottom_margin = base_margin + math.cos(len(ys) * 1.7) * margin_variation
                    
                    cut_bounds[cut.id] = BoundingBox(
                        min(xs) - left_margin, min(ys) - top_margin,
                        max(xs) + right_margin, max(ys) + bottom_margin
                    )
        
        return cut_bounds
    
    def _calculate_precise_cut_bounds(self, 
                                    egi: RelationalGraphWithCuts,
                                    vertex_positions: Dict[ElementID, Point],
                                    params: StyleLayoutParameters) -> Dict[ElementID, BoundingBox]:
        """Calculate cut bounds with precise, uniform margins"""
        cut_bounds = {}
        
        for cut in egi.Cut:
            cut_elements = egi.area.get(cut.id, frozenset())
            if cut_elements:
                xs = [vertex_positions[eid].x for eid in cut_elements if eid in vertex_positions]
                ys = [vertex_positions[eid].y for eid in cut_elements if eid in vertex_positions]
                
                if xs and ys:
                    # Precise, uniform margins
                    margin = params.cut_padding
                    
                    cut_bounds[cut.id] = BoundingBox(
                        min(xs) - margin, min(ys) - margin,
                        max(xs) + margin, max(ys) + margin
                    )
        
        return cut_bounds
    
    def _calculate_viewport(self, 
                          vertex_positions: Dict[ElementID, Point],
                          cut_bounds: Dict[ElementID, BoundingBox],
                          params: StyleLayoutParameters) -> BoundingBox:
        """Calculate viewport bounds with style-aware margins"""
        all_x = [p.x for p in vertex_positions.values()]
        all_y = [p.y for p in vertex_positions.values()]
        
        # Include cut bounds
        for bounds in cut_bounds.values():
            all_x.extend([bounds.min_x, bounds.max_x])
            all_y.extend([bounds.min_y, bounds.max_y])
        
        if all_x and all_y:
            return BoundingBox(
                min(all_x) - params.diagram_margin, min(all_y) - params.diagram_margin,
                max(all_x) + params.diagram_margin, max(all_y) + params.diagram_margin
            )
        else:
            return BoundingBox(0, 0, params.diagram_margin * 4, params.diagram_margin * 4)
