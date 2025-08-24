#!/usr/bin/env python3
"""
EGI ↔ Spatial Correspondence System with Chapter 16 Ligature Handling

This module implements the core correspondence between EGI logical structure
and spatial visual representation, incorporating Dau's Chapter 16 principles
for ligature handling and rearrangement.

Key Architectural Components:
1. Logical Layer: EGI mathematical relationships
2. Correspondence Layer: Bidirectional mapping with Chapter 16 constraints  
3. Spatial Layer: Visual representation with styling integration point
4. Interaction Layer: User manipulation with mathematical validation

Chapter 16 Integration:
- Lemma 16.1: Moving branches along ligatures (connection point repositioning)
- Lemma 16.2: Extending/restricting ligatures (vertex addition/removal)
- Lemma 16.3: Ligature retraction (simplification when valid)
- Definition 16.4: General ligature rearrangement framework
"""

from typing import Dict, List, Set, Tuple, Optional, Any
import os
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import math
from enum import Enum

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from styling.style_manager import create_style_manager


class LigatureTransformationType(Enum):
    """Types of ligature transformations from Chapter 16."""
    MOVE_BRANCH = "move_branch"          # Lemma 16.1
    EXTEND_LIGATURE = "extend_ligature"   # Lemma 16.2  
    RESTRICT_LIGATURE = "restrict_ligature" # Lemma 16.2
    RETRACT_LIGATURE = "retract_ligature"   # Lemma 16.3
    REARRANGE_LIGATURE = "rearrange_ligature" # Definition 16.4


@dataclass
class SpatialBounds:
    """Spatial bounding rectangle with containment operations."""
    x: float
    y: float
    width: float
    height: float
    
    def contains_point(self, px: float, py: float) -> bool:
        """Check if point is within bounds."""
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)
    
    def contains_bounds(self, other: 'SpatialBounds') -> bool:
        """Check if other bounds are fully contained."""
        return (self.contains_point(other.x, other.y) and
                self.contains_point(other.x + other.width, other.y + other.height))
    
    def center(self) -> Tuple[float, float]:
        """Get center point."""
        return (self.x + self.width/2, self.y + self.height/2)


@dataclass
class BranchingPoint:
    """Branching point on a ligature with Chapter 16 positioning freedom."""
    ligature_id: str
    position_on_ligature: float  # 0.0 to 1.0 along ligature path
    spatial_position: Tuple[float, float]
    connected_predicates: List[str] = field(default_factory=list)
    constant_label: Optional[str] = None
    
    def can_move_to(self, new_position: float) -> bool:
        """Check if branching point can move to new position (always True per Lemma 16.1)."""
        return 0.0 <= new_position <= 1.0


@dataclass 
class LigatureGeometry:
    """Spatial representation of a ligature with Chapter 16 constraints."""
    ligature_id: str
    vertices: List[str]  # Vertex IDs in this ligature
    spatial_path: List[Tuple[float, float]]  # Continuous path waypoints
    branching_points: List[BranchingPoint]
    
    def validate_chapter16_constraints(self) -> bool:
        """Validate ligature satisfies Chapter 16 mathematical constraints."""
        # All vertices in ligature must have same constant labels (for retraction)
        # Branching points must be on the continuous path
        # Connection topology must preserve identity relationships
        return True  # Simplified for now


@dataclass
class SpatialElement:
    """Element with both logical and spatial properties."""
    element_id: str
    element_type: str  # 'vertex', 'edge', 'cut', 'ligature'
    logical_area: str
    spatial_bounds: SpatialBounds
    
    # Chapter 16 specific properties
    ligature_geometry: Optional[LigatureGeometry] = None
    is_branching_point: bool = False
    parent_ligature: Optional[str] = None
    relation_name: Optional[str] = None


@dataclass
class CorrespondenceMapping:
    """Bidirectional mapping between EGI logic and spatial representation."""
    egi_to_spatial: Dict[str, str]  # EGI element ID -> Spatial element ID
    spatial_to_egi: Dict[str, str]  # Spatial element ID -> EGI element ID
    ligature_mappings: Dict[str, LigatureGeometry]  # Ligature ID -> Geometry
    area_mappings: Dict[str, SpatialBounds]  # Area ID -> Spatial bounds
    
    def get_spatial_for_egi(self, egi_id: str) -> Optional[str]:
        """Get spatial element ID for EGI element."""
        return self.egi_to_spatial.get(egi_id)
    
    def get_egi_for_spatial(self, spatial_id: str) -> Optional[str]:
        """Get EGI element ID for spatial element."""
        return self.spatial_to_egi.get(spatial_id)


class Chapter16Validator:
    """Validates ligature transformations according to Chapter 16 principles."""
    
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
    
    def validate_branch_movement(self, ligature_id: str, branch_point: BranchingPoint, 
                                new_position: float) -> bool:
        """Validate branch movement per Lemma 16.1."""
        # Branch can move anywhere along ligature without changing meaning
        return 0.0 <= new_position <= 1.0
    
    def validate_ligature_extension(self, ligature_id: str, new_vertex_id: str) -> bool:
        """Validate ligature extension per Lemma 16.2."""
        # New vertex must have identity edge to existing ligature vertex
        # Must preserve vertex labeling constraints
        return True  # Simplified for now
    
    def validate_ligature_retraction(self, ligature_id: str, target_vertex: str) -> bool:
        """Validate ligature retraction per Lemma 16.3."""
        # All vertices in ligature must have same label for retraction
        ligature_vertices = self._get_ligature_vertices(ligature_id)
        if len(ligature_vertices) <= 1:
            return False
            
        # Check if all vertices have same constant label
        labels = set()
        for vertex_id in ligature_vertices:
            # Would check vertex labeling function ρ(v)
            labels.add("*")  # Simplified - assume generic vertices
        
        return len(labels) == 1  # Can only retract if all same label
    
    def validate_ligature_rearrangement(self, old_geometry: LigatureGeometry, 
                                      new_geometry: LigatureGeometry) -> bool:
        """Validate ligature rearrangement per Definition 16.4."""
        # Vertex set must remain the same
        if set(old_geometry.vertices) != set(new_geometry.vertices):
            return False
        
        # Connection topology must preserve identity relationships
        # Branching points can move freely along path
        return True
    
    def _get_ligature_vertices(self, ligature_id: str) -> List[str]:
        """Get all vertices in a ligature."""
        # Would analyze EGI structure to find connected identity vertices
        return []  # Simplified for now


class SpatialCorrespondenceEngine:
    """Main engine for EGI ↔ spatial correspondence with Chapter 16 support."""
    
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        self.validator = Chapter16Validator(egi)
        self.correspondence = CorrespondenceMapping({}, {}, {}, {})
        self.styling_integration_point = None  # Reserved for future styling system
        self.style = create_style_manager()
    
    def generate_spatial_layout(self) -> Dict[str, SpatialElement]:
        """Generate spatial layout from EGI with Chapter 16 ligature handling."""
        layout = {}
        
        # Phase 1: Generate cut areas (define containment)
        self._generate_cut_areas(layout)
        
        # Phase 2: Generate ligatures with branching points
        self._generate_ligatures_with_branching(layout)
        # Ensure bare vertices (not forming multi-edge ligatures) are still shown
        self._ensure_all_vertices_present(layout)
        
        # Phase 3: Position predicates with collision avoidance
        self._position_predicates(layout)
        # Phase 3b: Snap ligature endpoints to predicate centers now that predicates have bounds
        self._snap_ligatures_to_predicates(layout)
        
        # Phase 4: Apply styling (RESERVED INTEGRATION POINT)
        layout = self._apply_styling_system(layout)
        
        # Phase 5: Validate Chapter 16 constraints
        self._validate_chapter16_compliance(layout)
        
        return layout
    
    def _generate_cut_areas(self, layout: Dict[str, SpatialElement]):
        """Generate spatial areas for cuts with proper nesting."""
        # Generate all cuts with minimum default size, even if empty
        # Track placed bounds together with their parent area so we only de-conflict siblings
        placed_bounds: List[Tuple[SpatialBounds, Optional[str]]] = []
        # Helper to compute nesting depth (sheet=0)
        def cut_depth(cut_id: str) -> int:
            depth = 0
            cur = cut_id
            seen = set()
            while True:
                if cur in seen:
                    break
                seen.add(cur)
                parent = self._determine_cut_parent_area(cur)
                if parent == self.egi.sheet or parent is None:
                    return depth + 1  # parent is sheet => this cut depth 1
                depth += 1
                cur = parent
        # Sort cuts so parents come before children
        cuts_ordered = sorted(list(self.egi.Cut), key=lambda c: cut_depth(c.id))
        for i, cut in enumerate(cuts_ordered):
            # Check if cut has any content
            cut_contents = self.egi.area.get(cut.id, frozenset())
            
            # Position cut with minimum default size
            cut_x = 100 + i * 300
            cut_y = 80
            
            # Context-driven size estimate based on contents
            base_w, base_h = 150, 100
            add_w, add_h = 0, 0
            for elem_id in cut_contents:
                if elem_id in {e.id for e in self.egi.E}:
                    add_w += 90
                    add_h = max(add_h, 30)
                elif elem_id in {v.id for v in self.egi.V}:
                    add_w += 20
                    add_h = max(add_h, 20)
                elif elem_id in {c.id for c in self.egi.Cut}:
                    add_w += 160
                    add_h = max(add_h, 110)
            pad_w, pad_h = 40, 30
            cut_width = max(base_w, base_w + add_w) + pad_w
            cut_height = max(base_h, base_h + add_h) + pad_h
            
            # Default bounds before potential nesting placement
            bounds = SpatialBounds(cut_x, cut_y, cut_width, cut_height)
            # If this cut has a parent cut with known bounds, nest it inside with padding
            parent_area = self._determine_cut_parent_area(cut.id)
            parent_bounds = self.correspondence.area_mappings.get(parent_area) if parent_area != self.egi.sheet else None
            if not parent_bounds and parent_area != self.egi.sheet:
                # Fallback: use already-placed layout for parent in this pass
                parent_elt = layout.get(parent_area)
                if parent_elt and parent_elt.element_type == 'cut':
                    parent_bounds = parent_elt.spatial_bounds
            if parent_bounds:
                layout_tokens = self.style.resolve(type="layout")
                pad_in = float(layout_tokens.get("cut_padding", 20.0))
                nx = parent_bounds.x + pad_in
                ny = parent_bounds.y + pad_in
                # Ensure it fits; if too large, clamp to parent minus padding
                nwidth = min(cut_width, max(10.0, parent_bounds.width - 2 * pad_in))
                nheight = min(cut_height, max(10.0, parent_bounds.height - 2 * pad_in))
                bounds = SpatialBounds(nx, ny, nwidth, nheight)
            # Avoid overlaps with previously placed sibling cuts (simple shifting)
            def overlaps(a: SpatialBounds, b: SpatialBounds) -> bool:
                return not (a.x + a.width <= b.x or b.x + b.width <= a.x or
                            a.y + a.height <= b.y or b.y + b.height <= a.y)
            layout_tokens = self.style.resolve(type="layout")
            _ss = layout_tokens.get("sibling_shift", [40.0, 30.0])
            try:
                shift_dx = float(_ss[0]) if isinstance(_ss, (list, tuple)) and len(_ss) >= 1 else 40.0
                shift_dy = float(_ss[1]) if isinstance(_ss, (list, tuple)) and len(_ss) >= 2 else 30.0
            except Exception:
                shift_dx, shift_dy = 40.0, 30.0
            guard = 0
            # Only consider overlaps with siblings (same parent area)
            def any_sibling_overlap() -> bool:
                for pb, pb_parent in placed_bounds:
                    if pb_parent == parent_area and overlaps(bounds, pb):
                        return True
                return False
            while any_sibling_overlap():
                # If nested, try shifting within parent bounds; else global shift
                if parent_bounds:
                    nx = min(parent_bounds.x + parent_bounds.width - bounds.width - 10.0, bounds.x + shift_dx)
                    ny = min(parent_bounds.y + parent_bounds.height - bounds.height - 10.0, bounds.y + shift_dy)
                    bounds = SpatialBounds(nx, ny, bounds.width, bounds.height)
                    # Keep inside parent bounds just in case
                    bx = max(parent_bounds.x + 5.0, min(bounds.x, parent_bounds.x + parent_bounds.width - bounds.width - 5.0))
                    by = max(parent_bounds.y + 5.0, min(bounds.y, parent_bounds.y + parent_bounds.height - bounds.height - 5.0))
                    bounds = SpatialBounds(bx, by, bounds.width, bounds.height)
                else:
                    bounds = SpatialBounds(bounds.x + shift_dx, bounds.y + shift_dy, bounds.width, bounds.height)
                guard += 1
                if guard > 50:
                    break
            placed_bounds.append((bounds, parent_area))
            
            layout[cut.id] = SpatialElement(
                element_id=cut.id,
                element_type='cut',
                logical_area=self._determine_cut_parent_area(cut.id),
                spatial_bounds=bounds
            )
            
            # Update correspondence mapping
            self.correspondence.egi_to_spatial[cut.id] = cut.id
            self.correspondence.spatial_to_egi[cut.id] = cut.id
            self.correspondence.area_mappings[cut.id] = bounds
    
    def _generate_ligatures_with_branching(self, layout: Dict[str, SpatialElement]):
        """Generate ligatures with branching points per Chapter 16."""
        # Analyze EGI for identity edge networks (ligatures)
        ligatures = self._identify_ligatures()
        
        for ligature_id, vertex_ids in ligatures.items():
            # Create continuous path for ligature
            path_points = self._generate_ligature_path(vertex_ids, layout)
            
            # Add central vertex as a visible dot/spot
            if vertex_ids:
                vertex_id = vertex_ids[0]
                # Choose same safe central position used for routing so the dot sits on the ligature
                logical_area = self._determine_ligature_area(vertex_ids)
                center_pos = self._pick_safe_point_in_area(logical_area, layout, (200, 200))
                
                # Create vertex element for visualization
                vertex_bounds = SpatialBounds(center_pos[0] - 5, center_pos[1] - 5, 10, 10)
                # Clamp inside logical area for spatial exclusion
                vertex_bounds = self._clamp_bounds_into_area(vertex_bounds, logical_area)
                vertex_bounds = self._avoid_child_cut_holes(vertex_bounds, logical_area, layout)
                layout[vertex_id] = SpatialElement(
                    element_id=vertex_id,
                    element_type='vertex',
                    logical_area=logical_area,
                    spatial_bounds=vertex_bounds
                )
                # Update correspondence maps for vertex
                self.correspondence.egi_to_spatial[vertex_id] = vertex_id
                self.correspondence.spatial_to_egi[vertex_id] = vertex_id
            
            # Create branching points for constant vertices
            branching_points = []
            for i, vertex_id in enumerate(vertex_ids):
                # Position branching point along ligature path
                position_ratio = i / max(1, len(vertex_ids) - 1)
                spatial_pos = self._interpolate_path(path_points, position_ratio)
                
                branch_point = BranchingPoint(
                    ligature_id=ligature_id,
                    position_on_ligature=position_ratio,
                    spatial_position=spatial_pos,
                    constant_label=self._get_vertex_constant_label(vertex_id)
                )
                branching_points.append(branch_point)
            
            # Create ligature geometry
            ligature_geometry = LigatureGeometry(
                ligature_id=ligature_id,
                vertices=vertex_ids,
                spatial_path=path_points,
                branching_points=branching_points
            )
            
            # Add to layout
            lig_area = self._determine_ligature_area(vertex_ids)
            # Compute bounds excluding child holes inside lig_area
            bounds = self._ligature_bounds_excluding_children(lig_area, path_points, layout)
            layout[ligature_id] = SpatialElement(
                element_id=ligature_id,
                element_type='ligature',
                logical_area=lig_area,
                spatial_bounds=bounds,
                ligature_geometry=ligature_geometry
            )
            
            # Update correspondence
            self.correspondence.ligature_mappings[ligature_id] = ligature_geometry
    
    def _position_predicates(self, layout: Dict[str, SpatialElement]):
        """Position predicates, aligning with ligature star arms for visual connection."""
        # Group edges by their single shared vertex (current demo uses unary predicates)
        vertex_to_edges: Dict[str, List[str]] = {}
        for e in self.egi.E:
            vseq = self.egi.nu.get(e.id, ())
            for vid in vseq:
                vertex_to_edges.setdefault(vid, []).append(e.id)

        for edge in self.egi.E:
            if edge.id in layout:
                continue  # Already positioned

            connected_vertices = self.egi.nu.get(edge.id, ())
            if not connected_vertices:
                continue

            v_id = connected_vertices[0]
            group = vertex_to_edges.get(v_id, [])
            # Stable order based on insertion order of EGI edges
            n = max(1, len(group))
            try:
                i = group.index(edge.id)
            except ValueError:
                i = 0

            # Base at the vertex center if available, else safe area center
            base_x, base_y = 200.0, 200.0
            v_elem = layout.get(v_id)
            if v_elem and v_elem.spatial_bounds:
                base_x, base_y = v_elem.spatial_bounds.center()
            else:
                v_area = self._determine_vertex_area(v_id)
                base_x, base_y = self._pick_safe_point_in_area(v_area, layout, (base_x, base_y))

            # Match the ligature star: equally spaced angles
            angle = (2 * math.pi * i) / n
            radius = 80.0
            px = base_x + radius * math.cos(angle)
            py = base_y + radius * math.sin(angle)

            logical_area = self._determine_element_area(edge.id)
            px, py = self._pick_safe_point_in_area(logical_area, layout, (px, py))

            # Tight bounds estimation based on label length using style tokens
            label = self.egi.rel.get(edge.id, "") if hasattr(self.egi, 'rel') else ""
            ts = self.style.resolve(type="edge", role="edge.label_text")
            est_char_w = float(ts.get("estimate_char_width", 6.0))
            est_h = float(ts.get("estimate_height", 14.0))
            pad = ts.get("padding", [2, 1])
            try:
                pad_x = float(pad[0]) if isinstance(pad, (list, tuple)) and len(pad) >= 1 else 2.0
                pad_y = float(pad[1]) if isinstance(pad, (list, tuple)) and len(pad) >= 2 else 1.0
            except Exception:
                pad_x, pad_y = 2.0, 1.0
            est_w = max(18.0, est_char_w * len(label) + 2 * pad_x)
            est_h = est_h + 2 * pad_y
            bounds = SpatialBounds(px - est_w / 2.0, py - est_h / 2.0, est_w, est_h)
            bounds = self._clamp_bounds_into_area(bounds, logical_area)
            bounds = self._avoid_child_cut_holes(bounds, logical_area, layout)
            # Final fit: if assigned to a cut, force bounds to be fully contained within that cut
            cut_b = self.correspondence.area_mappings.get(logical_area)
            if cut_b:
                # Translate into cut if necessary
                nx = min(max(bounds.x, cut_b.x), cut_b.x + max(0.0, cut_b.width - bounds.width))
                ny = min(max(bounds.y, cut_b.y), cut_b.y + max(0.0, cut_b.height - bounds.height))
                nw = bounds.width
                nh = bounds.height
                # If label is larger than cut, shrink to fit minimally
                if nw > cut_b.width:
                    nw = max(8.0, cut_b.width - 2.0)
                    nx = cut_b.x + 1.0
                if nh > cut_b.height:
                    nh = max(6.0, cut_b.height - 2.0)
                    ny = cut_b.y + 1.0
                bounds = SpatialBounds(nx, ny, nw, nh)

            layout[edge.id] = SpatialElement(
                element_id=edge.id,
                element_type='edge',
                logical_area=logical_area,
                spatial_bounds=bounds,
                relation_name=self.egi.rel.get(edge.id, "") if hasattr(self.egi, 'rel') else ""
            )
            # Update correspondence maps for edge
            self.correspondence.egi_to_spatial[edge.id] = edge.id
            self.correspondence.spatial_to_egi[edge.id] = edge.id

    def _snap_ligatures_to_predicates(self, layout: Dict[str, SpatialElement]) -> None:
        """Rebuild each ligature path so arms terminate at the centers of predicate labels.
        Uses same-area obstacle routing around child cuts.
        """
        # Map vertex -> connected edges (predicates)
        vertex_to_edges: Dict[str, List[str]] = {}
        for e in self.egi.E:
            vseq = self.egi.nu.get(e.id, ())
            for vid in vseq:
                vertex_to_edges.setdefault(vid, []).append(e.id)

        # Iterate ligatures in current layout
        for lid, elt in list(layout.items()):
            if elt.element_type != 'ligature' or not getattr(elt, 'ligature_geometry', None):
                continue
            geom = elt.ligature_geometry
            if not geom.vertices:
                continue
            v_id = geom.vertices[0]
            v_elem = layout.get(v_id)
            if not v_elem or not v_elem.spatial_bounds:
                continue
            base = v_elem.spatial_bounds.center()

            # Collect predicate hooks on the label border and route from base to each
            connected = vertex_to_edges.get(v_id, [])
            if not connected:
                continue

            # Build obstacle list for the vertex's area
            lig_area = self._determine_ligature_area([v_id])
            obstacles: List[Tuple[float, float, float, float]] = []
            for c in self.egi.Cut:
                parent = self._determine_cut_parent_area(c.id)
                if parent == lig_area:
                    b = self.correspondence.area_mappings.get(c.id)
                    if b:
                        obstacles.append((b.x, b.y, b.width, b.height))

            new_path: List[Tuple[float, float]] = [base]
            for eid in connected:
                e_elem = layout.get(eid)
                if not e_elem:
                    continue
                # Compute hook point on predicate border toward the vertex base
                hook_x, hook_y = self._compute_border_hook(e_elem.spatial_bounds, base)
                ex, ey = hook_x, hook_y
                # Small inward offset so stroke visually meets/overlaps the border
                ls = self.style.resolve(type="ligature", role="ligature.arm")
                eps_in = float(ls.get("border_overlap", 1.0))
                # Move the hook slightly inward toward the predicate label center
                rcx, rcy = e_elem.spatial_bounds.center()
                ix, iy = (rcx - ex, rcy - ey)
                ilen = math.hypot(ix, iy)
                if ilen > 1e-6 and eps_in > 0:
                    ex += (ix / ilen) * eps_in
                    ey += (iy / ilen) * eps_in
                vx, vy = base
                dx, dy = (ex - vx, ey - vy)
                d0 = math.hypot(dx, dy)
                # Note: we no longer push outward along arm direction here; inward border_overlap
                # already guarantees a visual contact with the label box.
                # Guarantee minimal visible arm length
                min_len = float(ls.get("min_length", 12.0))
                dist = math.hypot(ex - vx, ey - vy)
                if dist < min_len and dist > 1e-6:
                    ux, uy = (ex - vx) / dist, (ey - vy) / dist
                    ex, ey = ex + ux * (min_len - dist), ey + uy * (min_len - dist)
                # Same-area avoidance only
                edge_area = self._determine_element_area(eid)
                eff_obs = obstacles if edge_area == lig_area else []
                # Also avoid other predicate label rectangles in the same area
                label_obs: List[Tuple[float, float, float, float]] = []
                if edge_area == lig_area:
                    # Add other predicates in same area as obstacles
                    for oid, oelem in layout.items():
                        if oid == eid:
                            continue
                        if getattr(oelem, 'element_type', '') != 'edge':
                            continue
                        # Only consider label boxes in same area
                        o_area = self._determine_element_area(oid)
                        if o_area != edge_area:
                            continue
                        ob = oelem.spatial_bounds
                        # Padding to keep a safe margin around text (forces earlier avoidance)
                        layout_tokens = self.style.resolve(type="layout")
                        pad = float(layout_tokens.get("label_obstacle_padding", 6.0))
                        label_obs.append((ob.x - pad, ob.y - pad, ob.width + 2 * pad, ob.height + 2 * pad))
                    # Add the target predicate label rect itself as an obstacle so routing
                    # to the approach point never crosses it. Use same padding.
                    ob = e_elem.spatial_bounds
                    layout_tokens = self.style.resolve(type="layout")
                    pad = float(layout_tokens.get("label_obstacle_padding", 6.0))
                    label_obs.append((ob.x - pad, ob.y - pad, ob.width + 2 * pad, ob.height + 2 * pad))
                # Build approach point just OUTSIDE the target predicate rect near the hook
                # so the routed path never crosses the target label box; only the final
                # short segment will enter it.
                rcx, rcy = e_elem.spatial_bounds.center()
                ux, uy = hook_x - rcx, hook_y - rcy
                ulen = math.hypot(ux, uy)
                if ulen > 1e-6:
                    ux, uy = ux / ulen, uy / ulen
                else:
                    ux, uy = 1.0, 0.0
                layout_tokens = self.style.resolve(type="layout")
                approach_margin = float(layout_tokens.get("ligature_approach_margin", 4.0))
                approach_pt = (hook_x + ux * approach_margin, hook_y + uy * approach_margin)
                # Route to approach point with obstacles
                seg = self._visibility_route(base, approach_pt, eff_obs + label_obs)
                # Ensure the path draws an arm from base to hook, then returns to base
                if seg:
                    # If last point already equals first, skip duplicate
                    if new_path and new_path[-1] == seg[0]:
                        new_path.extend(seg[1:])
                    else:
                        new_path.extend(seg)
                    # Append final short segment into the label box (inward overlap)
                    if new_path[-1] != (ex, ey):
                        new_path.append((ex, ey))
                    # Return to base to start next arm as a separate stroke in the same path
                    if new_path[-1] != base:
                        new_path.append(base)

            if not new_path:
                continue

            # Update geometry and bounds
            geom.spatial_path = new_path
            lig_area = self._determine_ligature_area([v_id])
            nb = self._ligature_bounds_excluding_children(lig_area, new_path, layout)
            elt.spatial_bounds = nb

    def _ligature_bounds_excluding_children(self, lig_area: str, path_points: List[Tuple[float, float]], layout: Dict[str, SpatialElement]) -> SpatialBounds:
        """Compute a ligature bounds rectangle inside lig_area excluding child cut holes.
        We derive the bounding box only from path points that are inside lig_area and not inside any child cut.
        Fallback to a tiny box at a safe point if all points are excluded.
        """
        # Area bounds
        area_b = self.correspondence.area_mappings.get(lig_area)
        if not area_b:
            # Not a cut: simple bounds
            return self._calculate_ligature_bounds(path_points)
        # Gather child cut bounds of this area
        child_bounds: List[SpatialBounds] = []
        for c in self.egi.Cut:
            parent = self._determine_cut_parent_area(c.id)
            if parent == lig_area:
                b = self.correspondence.area_mappings.get(c.id)
                if b:
                    child_bounds.append(b)
        def point_in_children(x: float, y: float) -> bool:
            for cb in child_bounds:
                if cb.contains_point(x, y):
                    return True
            return False
        # Filter points: inside area, outside children
        filtered: List[Tuple[float, float]] = []
        for (x, y) in path_points:
            if area_b.contains_point(x, y) and not point_in_children(x, y):
                filtered.append((x, y))
        if not filtered:
            # Fallback to a minimal box at a safe point within lig_area
            sx, sy = self._pick_safe_point_in_area(lig_area, layout, area_b.center())
            # Keep margin from children
            margin = 2.0
            sx = min(max(sx, area_b.x + margin), area_b.x + area_b.width - margin)
            sy = min(max(sy, area_b.y + margin), area_b.y + area_b.height - margin)
            return SpatialBounds(sx - 1.0, sy - 1.0, 2.0, 2.0)
        # Compute bounds from filtered points
        min_x = min(p[0] for p in filtered)
        max_x = max(p[0] for p in filtered)
        min_y = min(p[1] for p in filtered)
        max_y = max(p[1] for p in filtered)
        # Ensure minimal size
        w = max(1.0, max_x - min_x)
        h = max(1.0, max_y - min_y)
        # Clamp to area in case numerical tolerances push us out
        nx = min(max(min_x, area_b.x), area_b.x + area_b.width - w)
        ny = min(max(min_y, area_b.y), area_b.y + area_b.height - h)
        return SpatialBounds(nx, ny, w, h)

    def _compute_border_hook(self, rect: 'SpatialBounds', from_pt: Tuple[float, float]) -> Tuple[float, float]:
        """Return intersection point of ray from from_pt to rect center with rect border.
        If intersection fails due to degeneracy, fall back to rect center.
        """
        cx, cy = rect.center()
        # Define rectangle edges
        rx1, ry1 = rect.x, rect.y
        rx2, ry2 = rect.x + rect.width, rect.y + rect.height

        # Parametric ray: P(t) = from_pt + t*(dir), t>=0
        dx, dy = (cx - from_pt[0], cy - from_pt[1])
        if dx == 0 and dy == 0:
            return cx, cy

        # Compute t for intersection with each side, then check if the point lies on segment
        candidates: List[Tuple[float, float, float]] = []  # (t, x, y)
        def add_if_valid(t: float, x: float, y: float):
            if t >= 0 and rx1 - 1e-6 <= x <= rx2 + 1e-6 and ry1 - 1e-6 <= y <= ry2 + 1e-6:
                candidates.append((t, x, y))
        # Left (x=rx1)
        if dx != 0:
            t = (rx1 - from_pt[0]) / dx
            y = from_pt[1] + t * dy
            add_if_valid(t, rx1, y)
        # Right (x=rx2)
        if dx != 0:
            t = (rx2 - from_pt[0]) / dx
            y = from_pt[1] + t * dy
            add_if_valid(t, rx2, y)
        # Top (y=ry1)
        if dy != 0:
            t = (ry1 - from_pt[1]) / dy
            x = from_pt[0] + t * dx
            add_if_valid(t, x, ry1)
        # Bottom (y=ry2)
        if dy != 0:
            t = (ry2 - from_pt[1]) / dy
            x = from_pt[0] + t * dx
            add_if_valid(t, x, ry2)

        if not candidates:
            return cx, cy
        # Choose nearest intersection along the ray direction
        candidates.sort(key=lambda it: it[0])
        _, hx, hy = candidates[0]
        # Clamp to border (avoid floating imprecision slightly outside)
        hx = min(max(hx, rx1), rx2)
        hy = min(max(hy, ry1), ry2)
        return hx, hy
    
    # ===== Validation Helpers exposed for tests and GUI =====
    def validate_mapping_consistency(self, layout: Optional[Dict[str, SpatialElement]] = None) -> bool:
        """Ensure spatial elements correspond to EGI elements consistently.
        - Edge relation_name matches EGI rel
        - Round-trip egi_to_spatial and spatial_to_egi identities exist for edges/vertices
        - All EGI vertices/edges present in layout
        Raises ValueError on mismatch.
        """
        layout = layout or {}
        # Ensure layout has entries for all edges/vertices (cuts are handled elsewhere)
        egi_edge_ids = {e.id for e in self.egi.E}
        egi_vertex_ids = {v.id for v in self.egi.V}
        for eid in egi_edge_ids:
            if eid not in layout:
                raise ValueError(f"Missing spatial element for edge {eid}")
            se = layout[eid]
            if se.element_type != 'edge':
                raise ValueError(f"Spatial element for edge {eid} has wrong type {se.element_type}")
            expected_rel = self.egi.rel.get(eid, "") if hasattr(self.egi, 'rel') else ""
            if getattr(se, 'relation_name', None) != expected_rel:
                raise ValueError(f"Edge {eid} relation mismatch: spatial='{getattr(se, 'relation_name', None)}' vs egi='{expected_rel}'")
            # Round-trip mapping
            sid = self.correspondence.egi_to_spatial.get(eid)
            if not sid or self.correspondence.spatial_to_egi.get(sid) != eid:
                raise ValueError(f"Correspondence mapping missing/incorrect for edge {eid}")
        for vid in egi_vertex_ids:
            if vid not in layout:
                # A vertex may be implicit if not part of a multi-edge ligature; still require presence
                raise ValueError(f"Missing spatial element for vertex {vid}")
            se = layout[vid]
            if se.element_type != 'vertex':
                raise ValueError(f"Spatial element for vertex {vid} has wrong type {se.element_type}")
            sid = self.correspondence.egi_to_spatial.get(vid)
            if not sid or self.correspondence.spatial_to_egi.get(sid) != vid:
                raise ValueError(f"Correspondence mapping missing/incorrect for vertex {vid}")
        return True

    def validate_spatial_exclusion(self, layout: Optional[Dict[str, SpatialElement]] = None) -> bool:
        """Validate spatial exclusion principle:
        - Elements assigned to a parent area must not overlap child cut bounds (holes)
        - Elements assigned to a cut must be contained within that cut's bounds
        Simplified: we check bounding boxes; ligature paths are validated via their bounds.
        Raises ValueError on violation.
        """
        layout = layout or {}
        # Precompute area bounds from correspondence mapping (cuts)
        area_bounds = dict(self.correspondence.area_mappings)
        # Build parent->children cut map
        parent_children: Dict[str, List[str]] = {}
        for c in self.egi.Cut:
            parent = self._determine_cut_parent_area(c.id)
            parent_children.setdefault(parent, []).append(c.id)
        # Helper overlap
        def overlaps(a: SpatialBounds, b: SpatialBounds) -> bool:
            return not (a.x + a.width <= b.x or b.x + b.width <= a.x or a.y + a.height <= b.y or b.y + b.height <= a.y)
        def contains(inner: SpatialBounds, outer: SpatialBounds) -> bool:
            return outer.contains_bounds(inner)
        def path_intersects_rect(path: List[Tuple[float, float]], rect: SpatialBounds) -> bool:
            rx1, ry1 = rect.x, rect.y
            rx2, ry2 = rect.x + rect.width, rect.y + rect.height
            def seg_intersects(p1: Tuple[float, float], p2: Tuple[float, float]) -> bool:
                x1, y1 = p1
                x2, y2 = p2
                # Quick inside
                if (rx1 <= x1 <= rx2 and ry1 <= y1 <= ry2) or (rx1 <= x2 <= rx2 and ry1 <= y2 <= ry2):
                    return True
                # Segment vs rectangle edges
                edges = [((rx1, ry1), (rx2, ry1)), ((rx2, ry1), (rx2, ry2)), ((rx2, ry2), (rx1, ry2)), ((rx1, ry2), (rx1, ry1))]
                def orient(a, b, c):
                    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
                def on_seg(a, b, c):
                    return (min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1]))
                for a, b in edges:
                    o1 = orient((x1, y1), (x2, y2), a)
                    o2 = orient((x1, y1), (x2, y2), b)
                    o3 = orient(a, b, (x1, y1))
                    o4 = orient(a, b, (x2, y2))
                    if o1 == 0 and on_seg((x1, y1), (x2, y2), a):
                        return True
                    if o2 == 0 and on_seg((x1, y1), (x2, y2), b):
                        return True
                    if o3 == 0 and on_seg(a, b, (x1, y1)):
                        return True
                    if o4 == 0 and on_seg(a, b, (x2, y2)):
                        return True
                    if (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0):
                        return True
                return False
            for i in range(len(path) - 1):
                if seg_intersects(path[i], path[i+1]):
                    return True
            return False
        # Validate per element
        for sid, se in layout.items():
            if se.element_type not in ('edge', 'vertex', 'ligature'):
                continue
            area = se.logical_area
            se_bounds = se.spatial_bounds
            # If element is assigned to a cut, it must be inside that cut bounds
            if area in area_bounds:
                cut_b = area_bounds[area]
                if se.element_type == 'ligature':
                    # For ligatures, require base point to be inside the cut (arms may exit to other areas)
                    base_pt: Optional[Tuple[float, float]] = None
                    if getattr(se, 'ligature_geometry', None) and se.ligature_geometry.spatial_path:
                        base_pt = se.ligature_geometry.spatial_path[0]
                    else:
                        # Fallback to element center
                        base_pt = se_bounds.center()
                    if not cut_b.contains_point(base_pt[0], base_pt[1]):
                        raise ValueError(f"Ligature {sid} base point not inside assigned cut '{area}'")
                else:
                    if not contains(se_bounds, cut_b):
                        raise ValueError(f"Element {sid} assigned to cut '{area}' not fully contained within its bounds")
            # If element is assigned to a parent area, it must not overlap its child cuts
            children = parent_children.get(area, [])
            for child in children:
                child_b = area_bounds.get(child)
                if not child_b:
                    continue
                if overlaps(se_bounds, child_b):
                    if se.element_type == 'ligature':
                        # Allow overlap only if this ligature connects to a predicate placed in this child cut
                        target_areas: Set[str] = set()
                        if getattr(se, 'ligature_geometry', None) and se.ligature_geometry.vertices:
                            v_id = se.ligature_geometry.vertices[0]
                            # Collect areas of edges connected to this vertex
                            for e in self.egi.E:
                                vseq = self.egi.nu.get(e.id, ())
                                if v_id in vseq:
                                    t_area = self._determine_element_area(e.id)
                                    if t_area:
                                        target_areas.add(t_area)
                        # If path truly intersects the child rect and child is not a target area, it's a violation
                        if getattr(se, 'ligature_geometry', None) and path_intersects_rect(se.ligature_geometry.spatial_path, child_b):
                            if child in target_areas:
                                continue
                            raise ValueError(f"Ligature {sid} path intersects child cut '{child}' hole")
                        # Otherwise bounding box overlap without path crossing is acceptable
                        continue
                    raise ValueError(f"Element {sid} in area '{area}' overlaps child cut '{child}' hole")
        return True
    
    def _apply_styling_system(self, layout: Dict[str, SpatialElement]) -> Dict[str, SpatialElement]:
        """RESERVED INTEGRATION POINT for future styling system."""
        # This is where visual styling will be applied:
        # - Line thickness and color
        # - Font selection and sizing  
        # - Cut border styles
        # - Ligature rendering styles
        # - Branching point visualization
        
        # For now, return layout unchanged
        return layout
    
    def _validate_chapter16_compliance(self, layout: Dict[str, SpatialElement]):
        """Validate that spatial layout preserves Chapter 16 mathematical constraints."""
        for element in layout.values():
            if element.element_type == 'ligature' and element.ligature_geometry:
                if not element.ligature_geometry.validate_chapter16_constraints():
                    raise ValueError(f"Ligature {element.element_id} violates Chapter 16 constraints")
    
    def handle_branching_point_drag(self, ligature_id: str, branch_point_index: int, 
                                   new_position: float) -> bool:
        """Handle dragging of branching point along ligature per Lemma 16.1."""
        ligature_geometry = self.correspondence.ligature_mappings.get(ligature_id)
        if not ligature_geometry or branch_point_index >= len(ligature_geometry.branching_points):
            return False
        
        branch_point = ligature_geometry.branching_points[branch_point_index]
        
        # Validate movement per Chapter 16
        if not self.validator.validate_branch_movement(ligature_id, branch_point, new_position):
            return False
        
        # Update branching point position
        branch_point.position_on_ligature = new_position
        branch_point.spatial_position = self._interpolate_path(
            ligature_geometry.spatial_path, new_position
        )
        
        return True
    
    def apply_ligature_transformation(self, transformation_type: LigatureTransformationType,
                                    ligature_id: str, **kwargs) -> bool:
        """Apply Chapter 16 ligature transformation."""
        ligature_geometry = self.correspondence.ligature_mappings.get(ligature_id)
        if not ligature_geometry:
            return False
        
        if transformation_type == LigatureTransformationType.MOVE_BRANCH:
            return self.handle_branching_point_drag(
                ligature_id, kwargs['branch_index'], kwargs['new_position']
            )
        elif transformation_type == LigatureTransformationType.EXTEND_LIGATURE:
            return self._extend_ligature(ligature_id, kwargs['new_vertex_id'])
        elif transformation_type == LigatureTransformationType.RESTRICT_LIGATURE:
            return self._restrict_ligature(ligature_id, kwargs['remove_vertex_id'])
        elif transformation_type == LigatureTransformationType.RETRACT_LIGATURE:
            return self._retract_ligature(ligature_id, kwargs['target_vertex'])
        elif transformation_type == LigatureTransformationType.REARRANGE_LIGATURE:
            return self._rearrange_ligature(ligature_id, kwargs['new_geometry'])
        
        return False
    
    # Helper methods (simplified implementations)
    def _identify_ligatures(self) -> Dict[str, List[str]]:
        """Identify ligature networks from EGI identity edges."""
        ligatures = {}
        
        # Find all vertices that share identity edges (same vertex in multiple relations)
        vertex_to_edges = {}
        for edge in self.egi.E:
            vertices = self.egi.nu.get(edge.id, ())
            for vertex_id in vertices:
                if vertex_id not in vertex_to_edges:
                    vertex_to_edges[vertex_id] = []
                vertex_to_edges[vertex_id].append(edge.id)
        
        # Create ligatures for vertices connected to multiple edges
        ligature_counter = 1
        for vertex_id, connected_edges in vertex_to_edges.items():
            if len(connected_edges) > 1:  # Vertex appears in multiple relations
                ligature_id = f"ligature_{ligature_counter}"
                ligatures[ligature_id] = [vertex_id]  # The shared vertex
                ligature_counter += 1
        
        return ligatures
    
    def _generate_ligature_path(self, vertex_ids: List[str], layout: Dict[str, SpatialElement]) -> List[Tuple[float, float]]:
        """Generate continuous path for ligature connecting all related predicates."""
        if not vertex_ids:
            return [(100, 100), (200, 100)]
        
        # Find all edges connected to this vertex
        vertex_id = vertex_ids[0]  # The shared vertex
        connected_edges = []
        for edge in self.egi.E:
            vertices = self.egi.nu.get(edge.id, ())
            if vertex_id in vertices:
                connected_edges.append(edge.id)
        
        # Generate path connecting all predicate positions through central vertex
        path_points = []
        # Choose a safe central position in the ligature's logical area (outside child cuts)
        lig_area = self._determine_ligature_area([vertex_id])
        base_x, base_y = self._pick_safe_point_in_area(lig_area, layout, (200, 200))
        
        # Build same-area obstacle list from ALL descendant cuts of lig_area
        obstacles: List[Tuple[float, float, float, float]] = []
        def is_descendant_cut(cut_id: str, root_area: str) -> bool:
            # Walk up parent chain until sheet or None
            current = cut_id
            seen = set()
            while current and current not in seen:
                seen.add(current)
                parent = self._determine_cut_parent_area(current)
                if parent == root_area:
                    return True
                if parent == self.egi.sheet or parent is None:
                    return False
                current = parent
            return False
        # Prefer correspondence area mappings (stable even if layout ordering changes)
        for c in self.egi.Cut:
            if is_descendant_cut(c.id, lig_area) or self._determine_cut_parent_area(c.id) == lig_area:
                b = self.correspondence.area_mappings.get(c.id)
                if b:
                    obstacles.append((b.x, b.y, b.width, b.height))
        # Fallback to any cut elements already present in the layout rooted at lig_area (direct children)
        if not obstacles:
            for elt in layout.values():
                if elt.element_type == 'cut' and (elt.logical_area == lig_area):
                    b = elt.spatial_bounds
                    obstacles.append((b.x, b.y, b.width, b.height))
        
        # Create star pattern: center to each predicate and back, routed around cuts
        for i, edge_id in enumerate(connected_edges):
            # Ideal predicate target positions around the central vertex
            angle = (2 * math.pi * i) / max(1, len(connected_edges))
            radius = 80
            pred = (base_x + radius * math.cos(angle), base_y + radius * math.sin(angle))
            
            # Determine areas to enforce collision vs crossing
            edge_area = self._determine_element_area(edge_id)
            vertex_area = self._determine_vertex_area(vertex_id)
            # Same-area: avoid cuts. Cross-area: allow crossing (no obstacles)
            eff_obstacles = obstacles if edge_area == vertex_area else []
            # Cross-area: bias target toward destination area's center to ensure intentional crossing
            if edge_area != vertex_area:
                dest_bounds = self.correspondence.area_mappings.get(edge_area)
                if dest_bounds:
                    pred = dest_bounds.center()
            # For same-area, ensure target is outside child cuts too
            if eff_obstacles:
                pred = self._pick_safe_point_in_area(vertex_area, layout, pred)
            # Route from center to predicate target using effective obstacles
            segment_path = self._visibility_route((base_x, base_y), pred, eff_obstacles)
            path_points.extend(segment_path)
        
        # Optional debug: obstacles and path
        if os.environ.get('ARISBE_DEBUG_ROUTING') == '1':
            try:
                print('[DEBUG] lig_area=', lig_area)
                print('[DEBUG] obstacles=', obstacles)
                print('[DEBUG] path_points(before ensure)=', path_points)
            except Exception:
                pass
        # Ensure we have at least a basic path
        if not path_points:
            path_points = [(base_x, base_y), (base_x + 50, base_y)]
        if os.environ.get('ARISBE_DEBUG_ROUTING') == '1':
            try:
                print('[DEBUG] path_points(final)=', path_points)
            except Exception:
                pass
        
        return path_points

    # --- Routing helpers to avoid cut rectangles ---
    def _visibility_route(self, start: Tuple[float, float], end: Tuple[float, float],
                          obstacles: List[Tuple[float, float, float, float]]) -> List[Tuple[float, float]]:
        """Route a polyline from start to end avoiding rectangular obstacles using
        a simple visibility-graph with padded obstacle corners."""
        if not any(self._segment_intersects_rect(start, end, r) for r in obstacles):
            return [start, end]
        pad = 18.0
        nodes: List[Tuple[float, float]] = [start, end]
        for (x, y, w, h) in obstacles:
            nodes.extend([
                (x - pad, y - pad),
                (x + w + pad, y - pad),
                (x + w + pad, y + h + pad),
                (x - pad, y + h + pad),
            ])
        def clear(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
            for r in obstacles:
                if self._segment_intersects_rect(a, b, r):
                    return False
            return True
        # Build graph
        import math, heapq
        n = len(nodes)
        nbrs: Dict[int, List[Tuple[int, float]]] = {i: [] for i in range(n)}
        for i in range(n):
            for j in range(i + 1, n):
                if clear(nodes[i], nodes[j]):
                    d = math.hypot(nodes[i][0] - nodes[j][0], nodes[i][1] - nodes[j][1])
                    nbrs[i].append((j, d))
                    nbrs[j].append((i, d))
        # A*
        def h(i: int) -> float:
            return math.hypot(nodes[i][0] - nodes[1][0], nodes[i][1] - nodes[1][1])
        start_idx, goal_idx = 0, 1
        best = {start_idx: 0.0}
        prev: Dict[int, int] = {}
        pq = [(h(start_idx), 0.0, start_idx, -1)]
        while pq:
            _, g, u, p = heapq.heappop(pq)
            if u in prev:
                continue
            prev[u] = p
            if u == goal_idx:
                break
            for v, w in nbrs[u]:
                ng = g + w
                if ng < best.get(v, float('inf')):
                    best[v] = ng
                    heapq.heappush(pq, (ng + h(v), ng, v, u))
        if goal_idx not in prev:
            # Fallback: straight segment
            return [start, end]
        # Reconstruct
        path_idx = []
        cur = goal_idx
        while cur != -1:
            path_idx.append(cur)
            cur = prev.get(cur, -1)
        path_idx.reverse()
        path = [nodes[i] for i in path_idx]
        # Compress duplicates
        compact: List[Tuple[float, float]] = []
        for pt in path:
            if not compact or compact[-1] != pt:
                compact.append(pt)
        return compact

    def _segment_intersects_rect(self, p1: Tuple[float, float], p2: Tuple[float, float],
                                 rect: Tuple[float, float, float, float]) -> bool:
        x, y, w, h = rect
        rx1, ry1, rx2, ry2 = x, y, x + w, y + h
        # Quick reject if both points inside (we consider that intersecting for routing purposes)
        if (rx1 <= p1[0] <= rx2 and ry1 <= p1[1] <= ry2) or (rx1 <= p2[0] <= rx2 and ry1 <= p2[1] <= ry2):
            return True
        # Check segment against each rectangle edge
        edges = [((rx1, ry1), (rx2, ry1)), ((rx2, ry1), (rx2, ry2)), ((rx2, ry2), (rx1, ry2)), ((rx1, ry2), (rx1, ry1))]
        return any(self._segments_intersect(p1, p2, a, b) for a, b in edges)

    def _segments_intersect(self, p1: Tuple[float, float], p2: Tuple[float, float],
                            q1: Tuple[float, float], q2: Tuple[float, float]) -> bool:
        def orient(a, b, c):
            return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
        def on_seg(a, b, c):
            return (min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and
                    min(a[1], b[1]) <= c[1] <= max(a[1], b[1]))
        o1 = orient(p1, p2, q1)
        o2 = orient(p1, p2, q2)
        o3 = orient(q1, q2, p1)
        o4 = orient(q1, q2, p2)
        if o1 == 0 and on_seg(p1, p2, q1): return True
        if o2 == 0 and on_seg(p1, p2, q2): return True
        if o3 == 0 and on_seg(q1, q2, p1): return True
        if o4 == 0 and on_seg(q1, q2, p2): return True
        return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)
    
    def _interpolate_path(self, path: List[Tuple[float, float]], position: float) -> Tuple[float, float]:
        """Interpolate position along path."""
        if not path or position <= 0:
            return path[0] if path else (0, 0)
        if position >= 1:
            return path[-1] if path else (0, 0)
        
        # Linear interpolation between path points
        segment_length = 1.0 / max(1, len(path) - 1)
        segment_index = int(position / segment_length)
        local_position = (position % segment_length) / segment_length
        
        if segment_index >= len(path) - 1:
            return path[-1]
        
        p1 = path[segment_index]
        p2 = path[segment_index + 1]
        
        return (
            p1[0] + local_position * (p2[0] - p1[0]),
            p1[1] + local_position * (p2[1] - p1[1])
        )
    
    def _get_vertex_constant_label(self, vertex_id: str) -> Optional[str]:
        """Get constant label for vertex if any."""
        # Would check vertex labeling function ρ(v)
        return None  # Simplified
    
    def _calculate_ligature_bounds(self, path: List[Tuple[float, float]]) -> SpatialBounds:
        """Calculate bounding box for ligature path."""
        if not path:
            return SpatialBounds(0, 0, 0, 0)
        
        min_x = min(p[0] for p in path)
        max_x = max(p[0] for p in path)
        min_y = min(p[1] for p in path)
        max_y = max(p[1] for p in path)
        
        return SpatialBounds(min_x, min_y, max_x - min_x, max_y - min_y)
    
    def _determine_ligature_area(self, vertex_ids: List[str]) -> str:
        """Determine which area contains the ligature."""
        if not vertex_ids:
            return self.egi.sheet
        
        # Find the area containing the vertex
        vertex_id = vertex_ids[0]
        for area_id, area_contents in self.egi.area.items():
            if vertex_id in area_contents:
                return area_id
        
        return self.egi.sheet  # Default to sheet

    def _determine_vertex_area(self, vertex_id: str) -> str:
        """Determine which area contains a given vertex."""
        for area_id, area_contents in self.egi.area.items():
            if vertex_id in area_contents:
                return area_id
        return self.egi.sheet

    def _ensure_all_vertices_present(self, layout: Dict[str, SpatialElement]):
        """Add SpatialElements for vertices not already added via ligature processing."""
        for v in self.egi.V:
            if v.id in layout:
                continue
            # Place near center; clamp into logical area
            vx, vy = 200, 200
            v_bounds = SpatialBounds(vx - 5, vy - 5, 10, 10)
            area_id = self._determine_vertex_area(v.id)
            v_bounds = self._clamp_bounds_into_area(v_bounds, area_id)
            layout[v.id] = SpatialElement(
                element_id=v.id,
                element_type='vertex',
                logical_area=area_id,
                spatial_bounds=v_bounds
            )
    
    def _determine_cut_parent_area(self, cut_id: str) -> str:
        """Determine parent area for a cut."""
        # Find which area contains this cut
        for area_id, area_contents in self.egi.area.items():
            if cut_id in area_contents and area_id != cut_id:
                return area_id
        
        return self.egi.sheet  # Default to sheet
    
    def _calculate_predicate_position(self, connected_vertices: Tuple[str, ...], 
                                    layout: Dict[str, SpatialElement]) -> Tuple[float, float]:
        """Calculate position for predicate with collision avoidance."""
        if not connected_vertices:
            return (150, 120)
        
        vertex_id = connected_vertices[0]

        # Gather already positioned edge elements connected to this vertex
        positioned_edges: List[SpatialElement] = []
        for element in layout.values():
            if element.element_type == 'edge':
                edge_vertices = self.egi.nu.get(element.element_id, ())
                if vertex_id in edge_vertices:
                    positioned_edges.append(element)

        # Determine the logical area for the predicate: prefer the vertex's area
        vertex_area = self._determine_element_area(vertex_id)

        # Determine a geometric base (prefer the vertex bounds center; otherwise area center)
        base_x, base_y = 150.0, 120.0
        v_elem = layout.get(vertex_id)
        if v_elem and v_elem.spatial_bounds:
            base_x, base_y = v_elem.spatial_bounds.center()
        else:
            area_bounds = self.correspondence.area_mappings.get(vertex_area)
            if area_bounds:
                base_x, base_y = area_bounds.center()

        # Radial placement around the vertex with simple fan-out by number of edges
        radius = 60.0
        angle_step = 2 * math.pi / max(3, len(positioned_edges) + 3)
        angle = len(positioned_edges) * angle_step

        pred_x = base_x + radius * math.cos(angle)
        pred_y = base_y + radius * math.sin(angle)

        # Enforce minimum spacing from other predicates connected to the vertex
        for existing_edge in positioned_edges:
            existing_bounds = existing_edge.spatial_bounds
            cx = existing_bounds.x + existing_bounds.width * 0.5
            cy = existing_bounds.y + existing_bounds.height * 0.5
            distance = math.hypot(pred_x - cx, pred_y - cy)
            if distance < 48.0:
                angle += angle_step
                pred_x = base_x + radius * math.cos(angle)
                pred_y = base_y + radius * math.sin(angle)

        # Keep the point inside the logical area and outside child cuts
        pred_x, pred_y = self._pick_safe_point_in_area(vertex_area, layout, (pred_x, pred_y))

        return (pred_x, pred_y)
    
    def _determine_element_area(self, element_id: str) -> str:
        """Determine which area contains an element."""
        for area_id, elements in self.egi.area.items():
            if element_id in elements:
                return area_id
        return self.egi.sheet

    def _clamp_bounds_into_area(self, bounds: SpatialBounds, area_id: str) -> SpatialBounds:
        """Ensure the element bounds lie within the spatial bounds of its logical area.
        If area is the sheet (no explicit bounds), return unchanged."""
        if area_id == self.egi.sheet:
            return bounds
        # Get area spatial bounds if available; if not generated yet, return unchanged
        area_bounds = self.correspondence.area_mappings.get(area_id)
        if not area_bounds:
            # Try looking into current layout via area id presence (cut placed as element)
            return bounds
        pad = 6.0
        # Clamp the top-left within area minus padding
        new_x = max(area_bounds.x + pad, min(bounds.x, area_bounds.x + area_bounds.width - pad - bounds.width))
        new_y = max(area_bounds.y + pad, min(bounds.y, area_bounds.y + area_bounds.height - pad - bounds.height))
        return SpatialBounds(new_x, new_y, bounds.width, bounds.height)

    def _pick_safe_point_in_area(self, area_id: str, layout: Dict[str, SpatialElement], preferred: Tuple[float, float]) -> Tuple[float, float]:
        """Pick a point inside area_id and outside any child cuts, starting near preferred.
        If preferred lies within the union of child cuts, jump just outside the union bbox."""
        # If area has explicit bounds, start from its center; else use preferred
        area_bounds = self.correspondence.area_mappings.get(area_id)
        x, y = preferred
        if area_bounds:
            x, y = area_bounds.center()
        # Collect holes: include ALL descendant cuts of this area using correspondence mappings
        holes: List[SpatialBounds] = []
        def is_descendant_cut(cut_id: str, root_area: str) -> bool:
            current = cut_id
            seen = set()
            while current and current not in seen:
                seen.add(current)
                parent = self._determine_cut_parent_area(current)
                if parent == root_area:
                    return True
                if parent == self.egi.sheet or parent is None:
                    return False
                current = parent
            return False
        for c in self.egi.Cut:
            if is_descendant_cut(c.id, area_id) or self._determine_cut_parent_area(c.id) == area_id:
                b = self.correspondence.area_mappings.get(c.id)
                if b:
                    holes.append(b)
        def point_in_rect(px: float, py: float, r: SpatialBounds) -> bool:
            return r.x <= px <= r.x + r.width and r.y <= py <= r.y + r.height
        if holes:
            in_any = any(point_in_rect(x, y, h) for h in holes)
            if in_any:
                # Compute union bbox of holes
                min_x = min(h.x for h in holes)
                min_y = min(h.y for h in holes)
                max_x = max(h.x + h.width for h in holes)
                max_y = max(h.y + h.height for h in holes)
                margin = 16.0
                # Prefer top-left outside; if area bounds exist, clamp within area
                cand = (min_x - margin, min_y - margin)
                if area_bounds:
                    cand = (
                        max(area_bounds.x, min(cand[0], area_bounds.x + area_bounds.width)),
                        max(area_bounds.y, min(cand[1], area_bounds.y + area_bounds.height)),
                    )
                x, y = cand
                # If still inside any hole due to clamping, try bottom-right
                if any(point_in_rect(x, y, h) for h in holes):
                    cand = (max_x + margin, max_y + margin)
                    if area_bounds:
                        cand = (
                            max(area_bounds.x, min(cand[0], area_bounds.x + area_bounds.width)),
                            max(area_bounds.y, min(cand[1], area_bounds.y + area_bounds.height)),
                        )
                    x, y = cand
        else:
            # If we know there are child cuts by logic but no bounds yet and no area bounds, choose a conservative corner
            child_ids = [c.id for c in self.egi.Cut if c.id in self.egi.area.get(area_id, frozenset())]
            if child_ids and not area_bounds:
                # Prefer a central default to keep routing balanced for tests that expect possible crossings
                x, y = (200.0, 200.0)
        return (x, y)

    def _avoid_child_cut_holes(self, bounds: SpatialBounds, area_id: str, layout: Dict[str, SpatialElement]) -> SpatialBounds:
        """Nudge bounds out of any child cut rectangles in the same parent area (spatial exclusion)."""
        # Collect child cut rectangles for this area
        holes: List[SpatialBounds] = []
        for elt in layout.values():
            if elt.element_type == 'cut' and elt.logical_area == area_id:
                holes.append(elt.spatial_bounds)
        if not holes:
            child_ids = [c.id for c in self.egi.Cut if c.id in self.egi.area.get(area_id, frozenset())]
            for cid in child_ids:
                b = self.correspondence.area_mappings.get(cid)
                if b:
                    holes.append(b)

        def overlaps(a: SpatialBounds, b: SpatialBounds) -> bool:
            return not (a.x + a.width <= b.x or b.x + b.width <= a.x or a.y + a.height <= b.y or b.y + b.height <= a.y)

        adjusted = bounds
        guard = 0
        for hole in holes:
            # If overlapping, push minimally to the nearest outside side
            while overlaps(adjusted, hole) and guard < 50:
                # Distances to move left, right, up, down
                dx_left = (hole.x - (adjusted.x + adjusted.width)) if adjusted.x + adjusted.width > hole.x else 0
                dx_right = ((hole.x + hole.width) - adjusted.x) if adjusted.x < hole.x + hole.width else 0
                dy_up = (hole.y - (adjusted.y + adjusted.height)) if adjusted.y + adjusted.height > hole.y else 0
                dy_down = ((hole.y + hole.height) - adjusted.y) if adjusted.y < hole.y + hole.height else 0

                # Choose smallest absolute displacement that resolves overlap
                candidates = []
                if dx_left < 0: candidates.append(('left', abs(dx_left)))
                if dx_right > 0: candidates.append(('right', abs(dx_right)))
                if dy_up < 0: candidates.append(('up', abs(dy_up)))
                if dy_down > 0: candidates.append(('down', abs(dy_down)))

                if not candidates:
                    break
                direction = min(candidates, key=lambda x: x[1])[0]
                step = 8.0
                if direction == 'left':
                    adjusted = SpatialBounds(adjusted.x - step, adjusted.y, adjusted.width, adjusted.height)
                elif direction == 'right':
                    adjusted = SpatialBounds(adjusted.x + step, adjusted.y, adjusted.width, adjusted.height)
                elif direction == 'up':
                    adjusted = SpatialBounds(adjusted.x, adjusted.y - step, adjusted.width, adjusted.height)
                else:
                    adjusted = SpatialBounds(adjusted.x, adjusted.y + step, adjusted.width, adjusted.height)
                guard += 1
        return adjusted
    
    def _extend_ligature(self, ligature_id: str, new_vertex_id: str) -> bool:
        """Extend ligature with new vertex per Lemma 16.2."""
        return True  # Simplified
    
    def _restrict_ligature(self, ligature_id: str, remove_vertex_id: str) -> bool:
        """Remove vertex from ligature per Lemma 16.2."""
        return True  # Simplified
    
    def _retract_ligature(self, ligature_id: str, target_vertex: str) -> bool:
        """Retract ligature to single vertex per Lemma 16.3."""
        return self.validator.validate_ligature_retraction(ligature_id, target_vertex)
    
    def _rearrange_ligature(self, ligature_id: str, new_geometry: LigatureGeometry) -> bool:
        """Rearrange ligature topology per Definition 16.4."""
        old_geometry = self.correspondence.ligature_mappings.get(ligature_id)
        if not old_geometry:
            return False
        
        if self.validator.validate_ligature_rearrangement(old_geometry, new_geometry):
            self.correspondence.ligature_mappings[ligature_id] = new_geometry
            return True
        
        return False


# Integration with EGI System
def create_spatial_correspondence_engine(egi: RelationalGraphWithCuts) -> SpatialCorrespondenceEngine:
    """Factory function for creating correspondence engine."""
    return SpatialCorrespondenceEngine(egi)

# Backward-compatibility: legacy name used in tests and older modules
# Export EGISpatialCorrespondence as an alias of SpatialCorrespondenceEngine
EGISpatialCorrespondence = SpatialCorrespondenceEngine
