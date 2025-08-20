#!/usr/bin/env python3
"""
Area-Aware EGDF Generator

Enhances the canonical EGDF generator with Shapely-based area management
to ensure precise area boundary compliance and optimized positioning.

This module integrates ShapelyAreaManager with the existing EGDF pipeline
to provide constraint-based positioning that respects Dau's logical areas.
"""

from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass
import math

# Core imports
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
from layout_engine_clean import SpatialPrimitive, Coordinate, Bounds, LayoutResult
from pipeline_contracts import enforce_contracts
from egdf_dau_canonical import DauCompliantEGDFGenerator, DauVisualConstants, LigatureGeometry
from shapely_area_manager import ShapelyAreaManager, Rectangle


@dataclass
class AreaConstraints:
    """Area constraint information for element positioning."""
    element_id: str
    area_id: str
    desired_position: Coordinate
    constraints: Dict[str, Any]  # Additional positioning constraints


class AreaAwareEGDFGenerator(DauCompliantEGDFGenerator):
    """
    Area-aware EGDF generator with Shapely-based constraint management.
    
    Extends the canonical EGDF generator to ensure all elements respect
    logical area boundaries while optimizing visual positioning within
    those constraints.
    """
    
    def __init__(self, canvas_bounds: Rectangle = (0, 0, 800, 600)):
        """
        Initialize area-aware EGDF generator.
        
        Args:
            canvas_bounds: (x1, y1, x2, y2) bounds of the drawing canvas
        """
        super().__init__()
        self.canvas_bounds = canvas_bounds
        self.area_manager: Optional[ShapelyAreaManager] = None
        self.area_constraints: List[AreaConstraints] = []
    
    def generate_egdf_from_layout(self, 
                                egi: RelationalGraphWithCuts,
                                layout_result: LayoutResult) -> List[SpatialPrimitive]:
        """
        Generate area-aware EGDF from EGI and Graphviz layout.
        
        This enhanced version creates an area management system and ensures
        all elements are positioned within their logical area constraints.
        """
        # 1. Initialize area management system from EGI
        self.area_manager = self._create_area_manager_from_egi(egi, layout_result)
        
        # 2. Generate primitives with area constraints
        primitives = []
        
        # Generate cut primitives (these define the areas)
        cut_primitives = self._generate_cut_primitives(egi, layout_result)
        primitives.extend(cut_primitives)
        
        # Generate predicate primitives with area constraints
        predicate_primitives = self._generate_area_aware_predicate_primitives(
            egi, layout_result
        )
        primitives.extend(predicate_primitives)
        
        # Generate ligature and vertex primitives with area constraints
        ligature_primitives, vertex_primitives = self._generate_area_aware_ligature_system(
            egi, layout_result, predicate_primitives
        )
        primitives.extend(ligature_primitives)
        primitives.extend(vertex_primitives)
        
        # Debug output to track primitive generation
        print(f"🔍 DEBUG: Generated primitives breakdown:")
        print(f"  - {len(cut_primitives)} cuts")
        print(f"  - {len(predicate_primitives)} predicates") 
        print(f"  - {len(ligature_primitives)} ligatures")
        print(f"  - {len(vertex_primitives)} vertices")
        
        # 3. Validate all placements respect area constraints
        validation_errors = self._validate_area_placements(primitives)
        if validation_errors:
            print(f"⚠️  Area constraint violations: {len(validation_errors)}")
            for error in validation_errors[:5]:  # Show first 5 errors
                print(f"   {error}")
        
        return primitives
    
    def _create_area_manager_from_egi(self, 
                                    egi: RelationalGraphWithCuts,
                                    layout_result: LayoutResult) -> ShapelyAreaManager:
        """Create area manager from EGI structure and layout."""
        manager = ShapelyAreaManager(self.canvas_bounds)
        
        # Create cut areas from EGI cuts and layout clusters
        for cut in egi.Cut:
            cut_id = cut.id if hasattr(cut, 'id') else str(cut)
            
            # Find corresponding cluster bounds in layout
            cut_bounds = self._find_cut_bounds_in_layout(cut_id, layout_result)
            if cut_bounds:
                try:
                    # Determine parent area (sheet or another cut)
                    parent_area_id = self._determine_parent_area(cut, egi)
                    created_area_id = manager.create_cut_area(parent_area_id, cut_bounds)
                    print(f"✅ Created area {created_area_id} for cut {cut_id} in {parent_area_id}")
                    
                    # Store mapping from cut_id to created area_id for later lookup
                    if not hasattr(manager, 'cut_id_mapping'):
                        manager.cut_id_mapping = {}
                    manager.cut_id_mapping[cut_id] = created_area_id
                    
                except ValueError as e:
                    print(f"⚠️  Failed to create area for cut {cut_id}: {e}")
        
        return manager
    
    def _find_cut_bounds_in_layout(self, cut_id: str, 
                                 layout_result: LayoutResult) -> Optional[Rectangle]:
        """Find the bounds of a cut in the layout result."""
        for element_id, primitive in layout_result.primitives.items():
            if (primitive.element_type == 'cut' and element_id == cut_id):
                bounds = primitive.bounds
                # bounds is a tuple (x1, y1, x2, y2)
                return bounds
        return None
    
    def _determine_parent_area(self, cut: Cut, egi: RelationalGraphWithCuts) -> str:
        """Determine the parent area for a cut (sheet or another cut)."""
        # For now, assume all cuts are direct children of the sheet
        # In a more sophisticated implementation, we would analyze the
        # area mapping in egi.area to determine nesting relationships
        return "sheet"
    
    def _generate_area_aware_predicate_primitives(self, 
                                                egi: RelationalGraphWithCuts,
                                                layout_result: LayoutResult) -> List[SpatialPrimitive]:
        """Generate predicate primitives with area constraint validation."""
        primitives = []
        
        for edge in egi.E:
            # Find corresponding node in layout
            node_primitive = None
            for element_id, primitive in layout_result.primitives.items():
                if (primitive.element_type == 'predicate' and 
                    element_id == edge.id if hasattr(edge, 'id') else str(edge)):
                    node_primitive = primitive
                    break
            
            if node_primitive:
                # Determine which area this predicate should be in
                predicate_area_id = self._determine_element_area(edge, egi)
                
                # Optimize position within area constraints
                optimized_position = self._optimize_position_in_area(
                    node_primitive.position, predicate_area_id
                )
                
                if optimized_position:
                    # Create area-constrained predicate primitive
                    predicate_primitive = SpatialPrimitive(
                        element_id=node_primitive.element_id,
                        element_type='predicate',
                        position=optimized_position,
                        bounds=node_primitive.bounds,
                        z_index=2,  # Predicates above cuts
                        parent_area=predicate_area_id  # Use parent_area field for area tracking
                    )
                    primitives.append(predicate_primitive)
                    
                    # Record area placement
                    if self.area_manager:
                        self.area_manager.place_element(
                            predicate_primitive.element_id,
                            optimized_position,
                            predicate_area_id
                        )
                else:
                    print(f"⚠️  Could not place predicate {edge} in area {predicate_area_id}")
        
        return primitives
    
    def _generate_area_aware_ligature_system(self, 
                                           egi: RelationalGraphWithCuts,
                                           layout_result: LayoutResult,
                                           predicate_primitives: List[SpatialPrimitive]) -> Tuple[List[SpatialPrimitive], List[SpatialPrimitive]]:
        """Generate ligature and vertex primitives with area constraints."""
        ligature_primitives = []
        vertex_primitives = []
        
        # Group vertices by shared identity
        identity_groups = self._group_vertices_by_identity(egi)
        
        # Debug output for identity grouping
        print(f"🔍 DEBUG: Identity groups found:")
        for identity_key, vertices in identity_groups.items():
            vertex_ids = [v.id if hasattr(v, 'id') else str(v) for v in vertices]
            print(f"  - {identity_key}: {len(vertices)} vertices {vertex_ids}")
        
        for identity_id, vertex_instances in identity_groups.items():
            # Process ALL vertex instances (single or multiple) - they all need to be rendered
            
            # Get vertex positions from layout, optimized for area constraints
            vertex_positions = []
            vertex_area_ids = []
            
            for vertex_instance in vertex_instances:
                vertex = vertex_instance['vertex']
                edge_id = vertex_instance['edge_id']
                instance_id = vertex_instance['instance_id']
                
                # Find predicate position in layout to position vertex near it
                predicate_position = None
                for element_id, primitive in layout_result.primitives.items():
                    if element_id == edge_id and primitive.element_type == 'predicate':
                        predicate_position = primitive.position
                        break
                
                if predicate_position:
                    # Position vertex closely attached to its predicate for clear visual connection
                    # Place vertices directly adjacent to predicate with minimal spacing
                    argument_index = vertex_instance['argument_index']
                    
                    # Calculate minimal attachment position with cardinal directions
                    # Use minimal padding (3.0pt horizontal, 2.0pt vertical) around predicate text
                    if argument_index == 0:
                        # North attachment: minimal vertical padding above predicate
                        vertex_position = (predicate_position[0], predicate_position[1] - 8)
                    elif argument_index == 1:
                        # East attachment: minimal horizontal padding to right of predicate
                        vertex_position = (predicate_position[0] + 15, predicate_position[1])
                    elif argument_index == 2:
                        # South attachment: minimal vertical padding below predicate
                        vertex_position = (predicate_position[0], predicate_position[1] + 8)
                    else:
                        # West attachment: minimal horizontal padding to left of predicate
                        vertex_position = (predicate_position[0] - 15, predicate_position[1])
                    
                    # Determine area for this vertex instance
                    area_id = self._determine_element_area(vertex, egi)
                    
                    # Optimize position within area constraints
                    optimized_position = self._optimize_position_in_area(vertex_position, area_id)
                    if optimized_position:
                        vertex_positions.append(optimized_position)
                        vertex_area_ids.append(area_id)
                        
                        # Create vertex primitive with unique instance ID
                        vertex_primitive = SpatialPrimitive(
                            element_id=instance_id,
                            element_type='vertex',
                            position=optimized_position,
                            bounds=(
                                optimized_position[0] - self.constants.vertex_radius,
                                optimized_position[1] - self.constants.vertex_radius,
                                optimized_position[0] + self.constants.vertex_radius,
                                optimized_position[1] + self.constants.vertex_radius
                            ),
                            z_index=3,  # Vertices above predicates
                            parent_area=area_id  # Use parent_area field for area tracking
                        )
                        vertex_primitives.append(vertex_primitive)
                        
                        # Record area placement
                        if self.area_manager:
                            self.area_manager.place_element(instance_id, optimized_position, area_id)
            
            # Generate area-aware ligature connecting vertices
            if len(vertex_positions) >= 2:
                ligature_primitive = self._create_area_aware_ligature(
                    identity_id, vertex_positions, vertex_area_ids
                )
                if ligature_primitive:
                    ligature_primitives.append(ligature_primitive)
        
        return ligature_primitives, vertex_primitives
    
    def _group_vertices_by_identity(self, egi: RelationalGraphWithCuts) -> Dict[str, List]:
        """Group vertex instances by their identity for ligature generation.
        
        Based on nu mapping: creates vertex instances for each predicate argument,
        then groups them by the actual vertex ID they reference for identity lines.
        """
        identity_groups = {}
        
        # Create vertex instances based on nu mapping (predicate arguments)
        for edge_id, vertex_sequence in egi.nu.items():
            for argument_index, vertex_id in enumerate(vertex_sequence):
                # Find the actual vertex object
                vertex = None
                for v in egi.V:
                    if (hasattr(v, 'id') and v.id == vertex_id) or str(v) == vertex_id:
                        vertex = v
                        break
                
                if vertex:
                    # Create a unique vertex instance for this predicate argument
                    vertex_instance = {
                        'vertex': vertex,
                        'vertex_id': vertex_id,
                        'edge_id': edge_id,
                        'argument_index': argument_index,
                        'instance_id': f"{vertex_id}_in_{edge_id}_{argument_index}"
                    }
                    
                    # Group by the actual vertex ID from nu mapping
                    # This ensures vertices with same ID are connected by identity lines
                    identity_key = vertex_id
                    
                    if identity_key not in identity_groups:
                        identity_groups[identity_key] = []
                    identity_groups[identity_key].append(vertex_instance)
        
        return identity_groups
    
    def _determine_element_area(self, element, egi: RelationalGraphWithCuts) -> str:
        """Determine which area an element belongs to based on EGI structure."""
        element_id = element.id if hasattr(element, 'id') else str(element)
        
        # Check EGI area mapping
        for area_id, element_set in egi.area.items():
            if element_id in element_set:
                # If this is the sheet area, always return "sheet"
                if area_id == "sheet" or area_id.startswith("sheet_"):
                    return "sheet"
                
                # If this is a cut area, map to the actual area manager ID
                if hasattr(self.area_manager, 'cut_id_mapping'):
                    mapped_area_id = self.area_manager.cut_id_mapping.get(area_id)
                    if mapped_area_id:
                        return mapped_area_id
                
                # Fallback: return the area_id as-is (might not exist in area manager)
                return area_id
        
        # Default to sheet if not found in any cut
        return "sheet"
    
    def _optimize_position_in_area(self, desired_position: Coordinate, 
                                 area_id: str) -> Optional[Coordinate]:
        """Optimize element position within area constraints, avoiding boundaries."""
        if not self.area_manager:
            return desired_position
        
        # Get optimized position from area manager
        optimized_pos = self.area_manager.optimize_position_in_area(
            f"temp_{hash(desired_position)}", desired_position, area_id
        )
        
        if optimized_pos:
            # Add boundary padding to ensure vertices are clearly inside areas
            # This prevents vertices from landing ambiguously on cut boundaries
            boundary_padding = 8.0  # Pixels of padding from area boundaries
            
            # Apply padding by moving position slightly inward from boundaries
            x, y = optimized_pos
            padded_position = (x + boundary_padding, y + boundary_padding)
            
            # Verify the padded position is still within the area
            final_pos = self.area_manager.optimize_position_in_area(
                f"padded_{hash(padded_position)}", padded_position, area_id
            )
            
            return final_pos if final_pos else optimized_pos
        
        return optimized_pos
    
    def _find_vertex_position_in_layout(self, vertex_id: str, 
                                      layout_result: LayoutResult) -> Optional[Coordinate]:
        """Find vertex position in layout result."""
        for element_id, primitive in layout_result.primitives.items():
            if (primitive.element_type == 'vertex' and element_id == vertex_id):
                return primitive.position
        return None
    
    def _create_area_aware_ligature(self, identity_id: str,
                                   vertex_positions: List[Coordinate],
                                   vertex_area_ids: List[str]) -> Optional[SpatialPrimitive]:
        """Create ligature with rectilinear routing and minimal predicate attachment padding."""
        if len(vertex_positions) < 2:
            return None
        
        # Generate rectilinear paths with minimal 90-degree angles
        curve_points = []
        
        if len(vertex_positions) == 2:
            # Create L-shaped rectilinear path between two vertices
            start_x, start_y = vertex_positions[0]
            end_x, end_y = vertex_positions[1]
            
            # Calculate shortest rectilinear path
            dx = abs(end_x - start_x)
            dy = abs(end_y - start_y)
            
            if dx > dy:
                # Horizontal-first routing (fewer turns for wide spacing)
                mid_x = end_x
                mid_y = start_y
                curve_points = [vertex_positions[0], (mid_x, mid_y), vertex_positions[1]]
            else:
                # Vertical-first routing (fewer turns for tall spacing)
                mid_x = start_x
                mid_y = end_y
                curve_points = [vertex_positions[0], (mid_x, mid_y), vertex_positions[1]]
        else:
            # Multi-vertex ligature: use rectilinear star pattern
            base_vertex = vertex_positions[0]
            for other_vertex in vertex_positions[1:]:
                start_x, start_y = base_vertex
                end_x, end_y = other_vertex
                
                # Add rectilinear segment
                dx = abs(end_x - start_x)
                dy = abs(end_y - start_y)
                
                if dx > dy:
                    mid_x = end_x
                    mid_y = start_y
                    curve_points.extend([base_vertex, (mid_x, mid_y), other_vertex])
                else:
                    mid_x = start_x
                    mid_y = end_y
                    curve_points.extend([base_vertex, (mid_x, mid_y), other_vertex])
        
        # Calculate bounds for the ligature
        bounds = self._calculate_path_bounds(curve_points)
        
        return SpatialPrimitive(
            element_id=f"ligature_{identity_id}",
            element_type='identity_line',
            position=curve_points[0] if curve_points else (0, 0),
            bounds=bounds,
            z_index=1,  # Ligatures above cuts, below vertices
            curve_points=curve_points  # Use curve_points field for ligature path
        )
    
    def _validate_area_placements(self, primitives: List[SpatialPrimitive]) -> List[str]:
        """Validate that all primitives respect area constraints."""
        errors = []
        
        if not self.area_manager:
            return errors
        
        for primitive in primitives:
            if primitive.element_type in ['vertex', 'predicate']:
                area_id = primitive.parent_area
                if area_id:
                    can_place = self.area_manager.can_place_element(
                        primitive.element_id, primitive.position, area_id
                    )
                    if not can_place:
                        errors.append(
                            f"Element {primitive.element_id} at {primitive.position} "
                            f"violates area {area_id} constraints"
                        )
        
        return errors
    
    def get_area_debug_info(self) -> Dict[str, Any]:
        """Get debugging information about area management."""
        if not self.area_manager:
            return {}
        
        return {
            'area_hierarchy': self.area_manager.get_area_hierarchy(),
            'validation_errors': self.area_manager.validate_all_placements(),
            'canvas_bounds': self.canvas_bounds
        }


# Factory function for easy integration
def create_area_aware_egdf_generator(canvas_bounds: Rectangle = (0, 0, 800, 600)) -> AreaAwareEGDFGenerator:
    """Create area-aware EGDF generator with specified canvas bounds."""
    return AreaAwareEGDFGenerator(canvas_bounds)


if __name__ == "__main__":
    print("🎯 Area-Aware EGDF Generator")
    print("=" * 50)
    print("✅ Shapely-based area management integrated")
    print("✅ Area-constrained element positioning")
    print("✅ Dau-compliant logical area boundaries")
    print("🚀 Ready for EG diagram generation with precise area control")
