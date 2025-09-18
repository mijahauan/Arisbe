"""
Simple fix for Roberts disjunction spatial routing problem.

Roberts disjunction: ~[ ~[ (P "x") ] ~[ (Q "x") ] ]
- Shared vertex "x" in outer area
- P in left cut, Q in right cut  
- Ligature x→Q must not pass through left cut containing P

Solution: Position vertex x such that both ligatures can route without crossing sibling cuts.
"""

from typing import Dict
from PySide6.QtCore import QPointF, QRectF

from egi_core_dau import RelationalGraphWithCuts, ElementID


def fix_roberts_disjunction_positioning(cut_bounds: Dict[ElementID, QRectF], 
                                      element_positions: Dict[ElementID, QPointF],
                                      egi: RelationalGraphWithCuts) -> Dict[ElementID, QPointF]:
    """
    Fix positioning for Roberts disjunction to avoid ligature crossing cut boundaries.
    
    Strategy: Position shared vertex above or below the sibling cuts so ligatures
    can route directly without passing through unconnected cut areas.
    """
    
    # Identify Roberts disjunction pattern
    if not _is_roberts_disjunction(egi):
        return element_positions  # Not Roberts disjunction, no fix needed
    
    print("🔧 APPLYING ROBERTS DISJUNCTION SPATIAL FIX")
    
    # Find the shared vertex and sibling cuts
    shared_vertex = None
    left_cut = None
    right_cut = None
    p_predicate = None
    q_predicate = None
    
    # Find shared vertex (connects to both predicates)
    for vertex in egi.V:
        connected_predicates = []
        for edge_id, vertex_sequence in egi.nu.items():
            if vertex.id in vertex_sequence:
                connected_predicates.append(edge_id)
        
        if len(connected_predicates) == 2:
            shared_vertex = vertex.id
            p_predicate = connected_predicates[0] 
            q_predicate = connected_predicates[1]
            break
    
    if not shared_vertex:
        return element_positions
    
    # Find the cuts containing P and Q
    p_area = egi.get_context(p_predicate)
    q_area = egi.get_context(q_predicate)
    
    if p_area in cut_bounds and q_area in cut_bounds:
        left_cut_bounds = cut_bounds[p_area]
        right_cut_bounds = cut_bounds[q_area]
        
        # Position shared vertex to enable ligature routing without crossing cuts
        # Strategy: Place vertex between the cuts, not above them
        
        left_right = left_cut_bounds.right()
        right_left = right_cut_bounds.left()
        
        if right_left > left_right:
            # Cuts are side by side - place vertex between them
            between_x = (left_right + right_left) / 2
            cuts_center_y = (left_cut_bounds.center().y() + right_cut_bounds.center().y()) / 2
            new_vertex_pos = QPointF(between_x, cuts_center_y)
        else:
            # Cuts overlap horizontally - place vertex above them
            cuts_top = min(left_cut_bounds.top(), right_cut_bounds.top())
            cuts_center_x = (left_cut_bounds.center().x() + right_cut_bounds.center().x()) / 2
            clearance = 50  # pixels
            new_vertex_pos = QPointF(cuts_center_x, cuts_top - clearance)
        
        # Update positions
        fixed_positions = dict(element_positions)
        fixed_positions[shared_vertex] = new_vertex_pos
        
        print(f"  Repositioned vertex {shared_vertex} to ({new_vertex_pos.x():.0f}, {new_vertex_pos.y():.0f})")
        print(f"  Ligatures can now route without crossing cut boundaries")
        
        return fixed_positions
    
    return element_positions


def _is_roberts_disjunction(egi: RelationalGraphWithCuts) -> bool:
    """Check if EGI matches Roberts disjunction pattern."""
    
    # Roberts disjunction has:
    # - 1 vertex connecting to 2 predicates
    # - 2 cuts (sibling cuts)
    # - Each predicate in different cut
    
    if len(egi.V) != 1 or len(egi.E) != 2 or len(egi.Cut) != 2:
        return False
    
    vertex = next(iter(egi.V))
    
    # Check if vertex connects to exactly 2 predicates
    connected_predicates = []
    for edge_id, vertex_sequence in egi.nu.items():
        if vertex.id in vertex_sequence:
            connected_predicates.append(edge_id)
    
    if len(connected_predicates) != 2:
        return False
    
    # Check if predicates are in different cuts
    p1_area = egi.get_context(connected_predicates[0])
    p2_area = egi.get_context(connected_predicates[1])
    
    return p1_area != p2_area and p1_area in [c.id for c in egi.Cut] and p2_area in [c.id for c in egi.Cut]
