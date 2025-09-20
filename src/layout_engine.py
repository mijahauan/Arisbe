"""
Layout Engine - Bridge between EGI logical structure and visual representation
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, FrozenSet, List

from egi_core_dau import RelationalGraphWithCuts, ElementID


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class BoundingBox:
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    
    def contains_point(self, point: Point) -> bool:
        return (self.min_x < point.x < self.max_x and 
                self.min_y < point.y < self.max_y)
    
    def overlaps_with(self, other: 'BoundingBox') -> bool:
        """Check if this box overlaps with another box"""
        return not (self.max_x <= other.min_x or 
                   other.max_x <= self.min_x or
                   self.max_y <= other.min_y or 
                   other.max_y <= self.min_y)


@dataclass(frozen=True)
class Path:
    points: Tuple[Point, ...]


@dataclass(frozen=True)
class LayoutResult:
    """Platform-agnostic spatial arrangement"""
    cut_bounds: Dict[ElementID, BoundingBox]
    vertex_positions: Dict[ElementID, Point]
    edge_paths: Dict[ElementID, Path]
    viewport_bounds: BoundingBox
    
    def validate_spatial_compliance(self, egi: RelationalGraphWithCuts) -> 'SpatialComplianceResult':
        """Validate that spatial arrangement matches EGI logical structure"""
        violations = []
        
        # Check 1: Every element in a cut must be spatially contained
        for cut_id, cut_elements in egi.area.items():
            if cut_id == egi.sheet:
                continue  # Sheet has no spatial bounds
                
            if cut_id not in self.cut_bounds:
                violations.append(f"Cut {cut_id} has no spatial bounds")
                continue
                
            cut_bounds = self.cut_bounds[cut_id]
            for element_id in cut_elements:
                if element_id in self.vertex_positions:
                    vertex_pos = self.vertex_positions[element_id]
                    if not cut_bounds.contains_point(vertex_pos):
                        violations.append(f"Vertex {element_id} not contained in cut {cut_id}")
        
        # Check 2: No overlapping cuts at same nesting level
        cut_pairs = [(c1, c2) for c1 in self.cut_bounds for c2 in self.cut_bounds if c1 < c2]
        for cut1_id, cut2_id in cut_pairs:
            # Only check if they're at same nesting level (same parent)
            cut1_parent = self._get_cut_parent(cut1_id, egi)
            cut2_parent = self._get_cut_parent(cut2_id, egi)
            if cut1_parent == cut2_parent:
                bounds1 = self.cut_bounds[cut1_id]
                bounds2 = self.cut_bounds[cut2_id]
                if bounds1.overlaps_with(bounds2):
                    violations.append(f"Cuts {cut1_id} and {cut2_id} overlap at same level")
        
        return SpatialComplianceResult(
            is_compliant=len(violations) == 0,
            violations=violations
        )
    
    def _get_cut_parent(self, cut_id: ElementID, egi: RelationalGraphWithCuts) -> Optional[ElementID]:
        """Find which cut contains this cut"""
        for area_id, elements in egi.area.items():
            if cut_id in elements and area_id != egi.sheet:
                return area_id
        return None  # Cut is on sheet


@dataclass(frozen=True)
class SpatialComplianceResult:
    """Result of spatial compliance validation"""
    is_compliant: bool
    violations: List[str]


@dataclass(frozen=True)
class ViewConfiguration:
    """Configuration for how user wants to view the EGI"""
    # Focus and filtering
    focus_element: Optional[ElementID] = None      # Element to center view on
    context_radius: int = 2                       # How many nesting levels to show
    collapsed_cuts: FrozenSet[ElementID] = frozenset()  # Cuts to show collapsed
    
    # Layout preferences  
    layout_algorithm: str = "hierarchical"        # "hierarchical", "force_directed", "grid"
    vertex_spacing: float = 80.0                  # Distance between vertices
    cut_margin: float = 30.0                      # Margin inside cuts
    
    # Visual preferences
    show_vertex_labels: bool = True               # Show vertex text
    show_edge_labels: bool = True                 # Show relation names
    highlight_elements: FrozenSet[ElementID] = frozenset()  # Elements to highlight
    
    # Viewport preferences
    zoom_level: float = 1.0                       # Zoom factor
    pan_offset: Point = Point(0.0, 0.0)          # Pan offset


class LayoutEngine:
    """Core layout engine that enforces spatial-logical correspondence"""
    
    def compute_layout(self, egi: RelationalGraphWithCuts, 
                      view_config: Optional[ViewConfiguration] = None,
                      diagram_style: Optional['DiagramStyle'] = None) -> LayoutResult:
        """Translate EGI to spatial primitives - ENFORCES containment"""
        
        # Extract style parameters
        layout_style = diagram_style.get_layout_style() if diagram_style else None
        element_spacing = layout_style.element_spacing if layout_style else 80.0
        diagram_margin = layout_style.diagram_margin if layout_style else 50.0
        
        # Step 1: Position vertices using style-aware spacing
        vertex_positions = {}
        x, y = diagram_margin, diagram_margin
        for vertex in egi.V:
            vertex_positions[vertex.id] = Point(x, y)
            x += element_spacing
            if x > 400:  # TODO: Make this style-configurable
                x, y = diagram_margin, y + element_spacing
        
        # Step 2: Calculate cut bounds that contain their elements
        cut_bounds = {}
        for cut in egi.Cut:
            # Get elements in this cut from area mapping
            cut_elements = egi.area.get(cut.id, frozenset())
            if cut_elements:
                # Collect positions of all contained elements (vertices and nested cuts)
                xs, ys = [], []
                
                for element_id in cut_elements:
                    if element_id in vertex_positions:
                        # It's a vertex
                        pos = vertex_positions[element_id]
                        xs.extend([pos.x])
                        ys.extend([pos.y])
                    elif element_id in [c.id for c in egi.Cut]:
                        # It's a nested cut - we'll handle this in a second pass
                        pass
                
                # If we have any positioned elements, create bounds
                if xs and ys:
                    # Use style-aware cut padding
                    cut_style = diagram_style.get_cut_style() if diagram_style else None
                    margin = cut_style.padding if cut_style else 30.0
                    
                    cut_bounds[cut.id] = BoundingBox(
                        min(xs) - margin, min(ys) - margin,
                        max(xs) + margin, max(ys) + margin
                    )
                else:
                    # Cut with no vertices - create minimal bounds
                    default_size = element_spacing * 1.5
                    cut_bounds[cut.id] = BoundingBox(
                        diagram_margin, diagram_margin, 
                        diagram_margin + default_size, diagram_margin + default_size
                    )
        
        # Second pass: expand cut bounds to contain nested cuts
        for cut in egi.Cut:
            cut_elements = egi.area.get(cut.id, frozenset())
            nested_cuts = [eid for eid in cut_elements if eid in cut_bounds and eid != cut.id]
            
            if nested_cuts and cut.id in cut_bounds:
                # Expand this cut's bounds to contain nested cuts
                current_bounds = cut_bounds[cut.id]
                all_xs = [current_bounds.min_x, current_bounds.max_x]
                all_ys = [current_bounds.min_y, current_bounds.max_y]
                
                for nested_cut_id in nested_cuts:
                    nested_bounds = cut_bounds[nested_cut_id]
                    all_xs.extend([nested_bounds.min_x, nested_bounds.max_x])
                    all_ys.extend([nested_bounds.min_y, nested_bounds.max_y])
                
                # Use style-aware nesting margin
                cut_style = diagram_style.get_cut_style() if diagram_style else None
                nesting_margin = cut_style.nesting_margin if cut_style else 40.0
                
                cut_bounds[cut.id] = BoundingBox(
                    min(all_xs) - nesting_margin, min(all_ys) - nesting_margin,
                    max(all_xs) + nesting_margin, max(all_ys) + nesting_margin
                )
        
        # Step 3: Calculate viewport using style-aware margins
        all_x = [p.x for p in vertex_positions.values()]
        all_y = [p.y for p in vertex_positions.values()]
        
        # Include cut bounds in viewport calculation
        for bounds in cut_bounds.values():
            all_x.extend([bounds.min_x, bounds.max_x])
            all_y.extend([bounds.min_y, bounds.max_y])
        
        if all_x and all_y:
            viewport = BoundingBox(
                min(all_x) - diagram_margin, min(all_y) - diagram_margin,
                max(all_x) + diagram_margin, max(all_y) + diagram_margin
            )
        else:
            viewport = BoundingBox(0, 0, diagram_margin * 4, diagram_margin * 4)
        
        return LayoutResult(
            cut_bounds=cut_bounds,
            vertex_positions=vertex_positions,
            edge_paths={},
            viewport_bounds=viewport
        )
