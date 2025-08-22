#!/usr/bin/env python3
"""
Dau Position Correction System

Transforms Graphviz spatial primitives into Dau-compliant positions that respect
EGI logical structure and visual conventions. This fixes the core issue where
Graphviz positions don't match the actual visual rendering requirements.

Uses API contracts to ensure pipeline integrity.
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import math

from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_phase_implementations import (
    ElementSizingPhase, ContainerSizingPhase, CollisionDetectionPhase,
    PredicatePositioningPhase, VertexPositioningPhase, HookAssignmentPhase,
    RectilinearLigaturePhase, BranchOptimizationPhase, AreaCompactionPhase,
    PhaseStatus
)
from spatial_awareness_system import SpatialAwarenessSystem
from layout_engine_clean import SpatialPrimitive, LayoutResult  # These types are still valid
from pipeline_contracts import (
    enforce_contracts, 
    validate_relational_graph_with_cuts,
    validate_layout_result,
    validate_spatial_primitive
)


@dataclass
class CorrectedPosition:
    """A position that has been corrected for Dau compliance."""
    element_id: str
    element_type: str
    original_pos: Tuple[float, float]
    corrected_pos: Tuple[float, float]
    correction_reason: str


@dataclass
class DauGeometry:
    """Geometric parameters for Dau-compliant positioning."""
    # Cut geometry
    cut_padding: float = 12.0           # Minimum clearance around cut contents
    cut_corner_radius: float = 8.0      # Rounded rectangle corner radius
    min_cut_aspect_ratio: float = 1.2   # Prevent overly narrow cuts
    
    # Vertex positioning
    vertex_spot_radius: float = 4.0     # Identity spot size
    vertex_clearance: float = 6.0       # Minimum distance from other elements
    
    # Predicate positioning
    predicate_text_padding: float = 4.0 # Padding around predicate text
    hook_clearance: float = 2.0         # Clearance around hook points
    
    # Ligature geometry
    ligature_width: float = 4.0         # Heavy line width
    ligature_clearance: float = 3.0     # Minimum clearance from other elements


class DauPositionCorrector:
    """Corrects Graphviz spatial primitives for Dau compliance."""
    
    def __init__(self, geometry: DauGeometry = None):
        self.geom = geometry or DauGeometry()
        self.corrections: List[CorrectedPosition] = []
    
    @enforce_contracts(
        input_contracts={
            'layout': validate_layout_result,
            'egi': validate_relational_graph_with_cuts
        },
        output_contract=validate_layout_result
    )
    def correct_layout(self, layout: LayoutResult, egi: RelationalGraphWithCuts) -> LayoutResult:
        """Apply Dau position corrections to a layout result."""
        self.corrections.clear()
        
        # Phase 1: Correct vertex positions to respect EGI area assignments
        corrected_primitives = []
        vertex_corrections = self._correct_vertex_positions(layout.primitives, egi)
        
        # Phase 2: Adjust cut boundaries to properly contain corrected contents
        cut_corrections = self._correct_cut_boundaries(layout.primitives, vertex_corrections, egi)
        
        # Phase 3: Optimize predicate positions for hook accessibility
        predicate_corrections = self._correct_predicate_positions(layout.primitives, vertex_corrections, egi)
        
        # Apply all corrections
        corrections_map = {}
        for correction in vertex_corrections + cut_corrections + predicate_corrections:
            corrections_map[correction.element_id] = correction.corrected_pos
        
        # Generate corrected primitives
        for primitive in layout.primitives.values():
            if primitive.element_id in corrections_map:
                # Create corrected primitive
                corrected_primitive = SpatialPrimitive(
                    element_id=primitive.element_id,
                    element_type=primitive.element_type,
                    position=corrections_map[primitive.element_id],
                    bounds=self._recompute_bounds(primitive, corrections_map[primitive.element_id]),
                    z_index=getattr(primitive, 'z_index', 0)
                )
                corrected_primitives.append(corrected_primitive)
            else:
                corrected_primitives.append(primitive)
        
        # Return corrected layout
        return LayoutResult(
            primitives={p.element_id: p for p in corrected_primitives},
            canvas_bounds=self._recompute_layout_bounds(corrected_primitives),
            containment_hierarchy=layout.containment_hierarchy  # Preserve original hierarchy
        )
    
    def _correct_vertex_positions(self, primitives: Dict[str, SpatialPrimitive], 
                                 egi: RelationalGraphWithCuts) -> List[CorrectedPosition]:
        """Correct vertex positions to respect EGI area assignments."""
        corrections = []
        
        for primitive in primitives.values():
            if primitive.element_type != 'vertex':
                continue
                
            vertex_id = primitive.element_id
            current_pos = primitive.position
            
            # Find the logical area this vertex should be in
            logical_area = self._get_vertex_logical_area(vertex_id, egi)
            
            # Check if current position respects the logical area
            if not self._position_respects_area(current_pos, logical_area, primitives):
                # Compute corrected position
                corrected_pos = self._compute_vertex_corrected_position(
                    vertex_id, current_pos, logical_area, primitives, egi
                )
                
                corrections.append(CorrectedPosition(
                    element_id=vertex_id,
                    element_type='vertex',
                    original_pos=current_pos,
                    corrected_pos=corrected_pos,
                    correction_reason=f"Moved to respect logical area {logical_area}"
                ))
                
                self.corrections.append(corrections[-1])
        
        return corrections
    
    def _get_vertex_logical_area(self, vertex_id: str, egi: RelationalGraphWithCuts) -> str:
        """Determine the logical area (context) where a vertex should be positioned."""
        # Find the vertex in the EGI
        vertex = next((v for v in egi.V if v.id == vertex_id), None)
        if not vertex:
            return ">"  # Default to sheet level
        
        # Use EGI area mapping to find the correct context
        for context, elements in egi.area.items():
            if vertex in elements:
                return context.id if hasattr(context, 'id') else str(context)
        
        return ">"  # Default to sheet level
    
    def _position_respects_area(self, pos: Tuple[float, float], area_id: str, 
                               primitives: Dict[str, SpatialPrimitive]) -> bool:
        """Check if a position is within the bounds of its logical area."""
        if area_id == ">":
            # Sheet level - always valid
            return True
        
        # Find the cut primitive for this area
        cut_primitive = primitives.get(area_id)
        if not cut_primitive or cut_primitive.element_type != 'cut':
            return True  # Can't validate, assume valid
        
        # Check if position is inside cut bounds
        x, y = pos
        x1, y1, x2, y2 = cut_primitive.bounds
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def _compute_vertex_corrected_position(self, vertex_id: str, current_pos: Tuple[float, float],
                                          logical_area: str, primitives: Dict[str, SpatialPrimitive],
                                          egi: RelationalGraphWithCuts) -> Tuple[float, float]:
        """Compute a corrected position for a vertex that respects its logical area."""
        if logical_area == ">":
            # Sheet level - use current position
            return current_pos
        
        # Find the cut bounds for the logical area
        cut_primitive = primitives.get(logical_area)
        if not cut_primitive:
            return current_pos
        
        x1, y1, x2, y2 = cut_primitive.bounds
        
        # Find connected predicates to determine optimal position
        connected_predicates = self._get_connected_predicates(vertex_id, egi)
        predicate_positions = []
        
        for pred_id in connected_predicates:
            pred_primitive = primitives.get(pred_id)
            if pred_primitive:
                predicate_positions.append(pred_primitive.position)
        
        if predicate_positions:
            # Position vertex at centroid of connected predicates, constrained to cut bounds
            centroid_x = sum(pos[0] for pos in predicate_positions) / len(predicate_positions)
            centroid_y = sum(pos[1] for pos in predicate_positions) / len(predicate_positions)
            
            # Constrain to cut bounds with padding
            padding = self.geom.cut_padding / 2
            corrected_x = max(x1 + padding, min(x2 - padding, centroid_x))
            corrected_y = max(y1 + padding, min(y2 - padding, centroid_y))
            
            return (corrected_x, corrected_y)
        else:
            # No connected predicates - center in cut
            return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def _get_connected_predicates(self, vertex_id: str, egi: RelationalGraphWithCuts) -> List[str]:
        """Find all predicates connected to a vertex via the ν mapping."""
        connected = []
        for edge_id, vertex_sequence in egi.nu.items():
            if vertex_id in [v.id for v in vertex_sequence]:
                connected.append(edge_id)
        return connected
    
    def _correct_cut_boundaries(self, primitives: Dict[str, SpatialPrimitive],
                               vertex_corrections: List[CorrectedPosition],
                               egi: RelationalGraphWithCuts) -> List[CorrectedPosition]:
        """Adjust cut boundaries to properly contain their corrected contents."""
        corrections = []
        
        # Build map of corrected positions
        corrected_positions = {c.element_id: c.corrected_pos for c in vertex_corrections}
        
        for primitive in primitives.values():
            if primitive.element_type != 'cut':
                continue
                
            cut_id = primitive.element_id
            current_bounds = primitive.bounds
            
            # Find all elements that should be contained in this cut
            contained_elements = self._get_cut_contents(cut_id, egi, primitives)
            
            if not contained_elements:
                continue
            
            # Compute required bounds to contain all elements
            required_bounds = self._compute_required_cut_bounds(
                contained_elements, primitives, corrected_positions
            )
            
            # Check if current bounds are sufficient
            if not self._bounds_contain_bounds(current_bounds, required_bounds):
                # Expand cut bounds
                expanded_bounds = self._expand_bounds(required_bounds, self.geom.cut_padding)
                
                # Convert bounds to center position for primitive
                center_x = (expanded_bounds[0] + expanded_bounds[2]) / 2
                center_y = (expanded_bounds[1] + expanded_bounds[3]) / 2
                
                corrections.append(CorrectedPosition(
                    element_id=cut_id,
                    element_type='cut',
                    original_pos=primitive.position,
                    corrected_pos=(center_x, center_y),
                    correction_reason="Expanded to contain corrected contents"
                ))
                
                self.corrections.append(corrections[-1])
        
        return corrections
    
    def _get_cut_contents(self, cut_id: str, egi: RelationalGraphWithCuts,
                         primitives: Dict[str, SpatialPrimitive]) -> List[str]:
        """Get all element IDs that should be contained within a cut."""
        contents = []
        
        # Find the cut context in EGI
        cut_context = None
        for context, elements in egi.area.items():
            if hasattr(context, 'id') and context.id == cut_id:
                cut_context = context
                break
        
        if cut_context:
            elements = egi.area.get(cut_context, set())
            contents = [elem.id for elem in elements if hasattr(elem, 'id')]
        
        return contents
    
    def _compute_required_cut_bounds(self, element_ids: List[str],
                                    primitives: Dict[str, SpatialPrimitive],
                                    corrected_positions: Dict[str, Tuple[float, float]]) -> Tuple[float, float, float, float]:
        """Compute the minimum bounds required to contain all specified elements."""
        if not element_ids:
            return (0, 0, 0, 0)
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for elem_id in element_ids:
            # Use corrected position if available, otherwise original
            if elem_id in corrected_positions:
                x, y = corrected_positions[elem_id]
            else:
                primitive = primitives.get(elem_id)
                if primitive:
                    x, y = primitive.position
                else:
                    continue
            
            # Add element-specific padding
            padding = self._get_element_padding(elem_id, primitives)
            
            min_x = min(min_x, x - padding)
            min_y = min(min_y, y - padding)
            max_x = max(max_x, x + padding)
            max_y = max(max_y, y + padding)
        
        return (min_x, min_y, max_x, max_y)
    
    def _get_element_padding(self, element_id: str, primitives: Dict[str, SpatialPrimitive]) -> float:
        """Get appropriate padding for an element type."""
        primitive = primitives.get(element_id)
        if not primitive:
            return 5.0
        
        if primitive.element_type == 'vertex':
            return self.geom.vertex_spot_radius + self.geom.vertex_clearance
        elif primitive.element_type == 'predicate':
            return 15.0  # Approximate text bounds
        else:
            return 5.0
    
    def _correct_predicate_positions(self, primitives: Dict[str, SpatialPrimitive],
                                    vertex_corrections: List[CorrectedPosition],
                                    egi: RelationalGraphWithCuts) -> List[CorrectedPosition]:
        """Optimize predicate positions for hook accessibility and visual clarity."""
        corrections = []
        
        # For now, keep predicate positions as-is
        # Future enhancement: optimize for ligature routing
        
        return corrections
    
    def _bounds_contain_bounds(self, outer: Tuple[float, float, float, float],
                              inner: Tuple[float, float, float, float]) -> bool:
        """Check if outer bounds completely contain inner bounds."""
        ox1, oy1, ox2, oy2 = outer
        ix1, iy1, ix2, iy2 = inner
        return ox1 <= ix1 and oy1 <= iy1 and ox2 >= ix2 and oy2 >= iy2
    
    def _expand_bounds(self, bounds: Tuple[float, float, float, float], 
                      padding: float) -> Tuple[float, float, float, float]:
        """Expand bounds by padding amount."""
        x1, y1, x2, y2 = bounds
        return (x1 - padding, y1 - padding, x2 + padding, y2 + padding)
    
    def _recompute_bounds(self, primitive: SpatialPrimitive, 
                         new_position: Tuple[float, float]) -> Tuple[float, float, float, float]:
        """Recompute bounds for a primitive with a new position."""
        if not primitive.bounds:
            return (new_position[0] - 5, new_position[1] - 5, 
                   new_position[0] + 5, new_position[1] + 5)
        
        # Translate bounds to new position
        old_x, old_y = primitive.position
        new_x, new_y = new_position
        dx = new_x - old_x
        dy = new_y - old_y
        
        x1, y1, x2, y2 = primitive.bounds
        return (x1 + dx, y1 + dy, x2 + dx, y2 + dy)
    
    def _recompute_layout_bounds(self, primitives: List[SpatialPrimitive]) -> Tuple[float, float, float, float]:
        """Recompute overall layout bounds from corrected primitives."""
        if not primitives:
            return (0, 0, 0, 0)
        
        min_x = min(p.bounds[0] for p in primitives if p.bounds)
        min_y = min(p.bounds[1] for p in primitives if p.bounds)
        max_x = max(p.bounds[2] for p in primitives if p.bounds)
        max_y = max(p.bounds[3] for p in primitives if p.bounds)
        
        return (min_x, min_y, max_x, max_y)
    
    def get_correction_report(self) -> str:
        """Generate a human-readable report of all corrections made."""
        if not self.corrections:
            return "No position corrections were needed."
        
        report = f"Applied {len(self.corrections)} position corrections:\n\n"
        
        for correction in self.corrections:
            report += f"• {correction.element_type.title()} {correction.element_id}:\n"
            report += f"  Original: {correction.original_pos}\n"
            report += f"  Corrected: {correction.corrected_pos}\n"
            report += f"  Reason: {correction.correction_reason}\n\n"
        
        return report


@enforce_contracts(
    input_contracts={
        'layout': validate_layout_result,
        'egi': validate_relational_graph_with_cuts
    },
    output_contract=validate_layout_result
)
def apply_dau_position_corrections(layout: LayoutResult, 
                                  egi: RelationalGraphWithCuts) -> LayoutResult:
    """Convenience function to apply Dau position corrections to a layout."""
    corrector = DauPositionCorrector()
    corrected_layout = corrector.correct_layout(layout, egi)
    
    # Print correction report for debugging
    report = corrector.get_correction_report()
    if corrector.corrections:
        print("🔧 Dau Position Corrections Applied:")
        print(report)
    
    return corrected_layout
