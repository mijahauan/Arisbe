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
try:
    from routing.visibility_router import PyVisVisibilityRouter  # optional
except Exception:  # pragma: no cover
    PyVisVisibilityRouter = None  # type: ignore
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
    # Optional annotation/superscript bounds
    vertex_sup_bounds: Optional[SpatialBounds] = None  # for variable labels near vertex
    edge_sup_bounds: Optional[SpatialBounds] = None    # for arity superscript near predicate


# --- Staged layout scaffolding: logical layout -> canvas fit -> optimize ---
@dataclass
class LogicalArea:
    """Unitless logical area with containment relation and estimated size."""
    id: str
    parent: Optional[str]
    children: List[str] = field(default_factory=list)
    est_width: float = 1.0
    est_height: float = 1.0


@dataclass
class LogicalElement:
    """Unitless logical element (vertex or predicate) placed within a logical area."""
    id: str
    kind: str  # 'vertex' | 'edge'
    area_id: str
    est_width: float = 1.0
    est_height: float = 1.0
    x: float = 0.0
    y: float = 0.0


@dataclass
class LogicalLayout:
    """Complete logical layout: areas, elements, and logical ligature endpoints."""
    areas: Dict[str, LogicalArea] = field(default_factory=dict)
    elements: Dict[str, LogicalElement] = field(default_factory=dict)
    ligature_endpoints: List[Tuple[str, str]] = field(default_factory=list)  # (vertex_id, edge_id)


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
        # Optional pyvisgraph router
        self._pv_router = None
        try:
            if PyVisVisibilityRouter is not None:
                self._pv_router = PyVisVisibilityRouter(pad=0.0)
        except Exception:
            self._pv_router = None
        # Feature flag: 'direct' (current behavior) or 'staged' (logical -> fit)
        self.layout_mode: str = 'direct'
    
    def generate_spatial_layout(self) -> Dict[str, SpatialElement]:
        """Generate spatial layout from EGI with Chapter 16 ligature handling."""
        # If staged mode is enabled, run experimental pipeline
        if getattr(self, 'layout_mode', 'direct') == 'staged':
            return self.generate_spatial_layout_staged()
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
        # Phase 3c: Compute superscript annotation bounds (variable labels and arity)
        self._position_superscripts(layout)
        
        # Phase 4: Apply styling (RESERVED INTEGRATION POINT)
        layout = self._apply_styling_system(layout)
        
        # Phase 5: Validate Chapter 16 constraints
        self._validate_chapter16_compliance(layout)
        
        return layout

    # --- New staged pipeline entrypoint (opt-in) ---
    def generate_spatial_layout_staged(self, canvas_size: Tuple[int, int] = (1200, 800)) -> Dict[str, SpatialElement]:
        """Experimental staged pipeline: logical layout -> canvas fit -> optimize.
        Currently returns the same result as generate_spatial_layout while we
        implement the staged steps incrementally.
        """
        # Build logical layout (placeholder)
        logical = self.build_logical_layout()
        # Fit to canvas to compute area mappings and transforms (placeholder)
        area_mappings, transforms = self.fit_to_canvas(logical, canvas_size)
        # If fitter provided area mappings, seed correspondence so downstream uses them
        if area_mappings:
            self.correspondence.area_mappings.update(area_mappings)
        # Fall back to existing direct pipeline for now
        return self.generate_spatial_layout()

    # --- Staged pipeline helpers (placeholders to be filled in) ---
    def build_logical_layout(self) -> LogicalLayout:
        """Construct a unitless logical layout. Placeholder: builds the area tree and
        records element membership with rough size estimates; no positions yet."""
        ll = LogicalLayout()
        # Areas: sheet is implicit parent
        # Build parent links from existing EGI cut structure
        for c in self.egi.Cut:
            parent = self._determine_cut_parent_area(c.id)
            la = LogicalArea(id=c.id, parent=parent)
            ll.areas[c.id] = la
        # Populate children lists
        for a in ll.areas.values():
            if a.parent in ll.areas:
                ll.areas[a.parent].children.append(a.id)
        # Elements: vertices and edges with rough size estimates
        ts_edge = self.style.resolve(type="edge", role="edge.label_text")
        est_char_w = float(ts_edge.get("estimate_char_width", 6.0))
        est_h_txt = float(ts_edge.get("estimate_height", 14.0))
        pad = ts_edge.get("padding", [2, 1])
        try:
            pad_x = float(pad[0]) if isinstance(pad, (list, tuple)) and len(pad) >= 1 else 2.0
            pad_y = float(pad[1]) if isinstance(pad, (list, tuple)) and len(pad) >= 2 else 1.0
        except Exception:
            pad_x, pad_y = 2.0, 1.0
        for v in self.egi.V:
            area_id = self._determine_vertex_area(v.id)
            ll.elements[v.id] = LogicalElement(id=v.id, kind='vertex', area_id=area_id, est_width=10.0, est_height=10.0)
        for e in self.egi.E:
            area_id = self._determine_element_area(e.id)
            label = self.egi.rel.get(e.id, "") if hasattr(self.egi, 'rel') else ""
            est_w = max(18.0, est_char_w * len(label) + 2 * pad_x)
            est_h = est_h_txt + 2 * pad_y
            ll.elements[e.id] = LogicalElement(id=e.id, kind='edge', area_id=area_id, est_width=est_w, est_height=est_h)
        # Ligature endpoints: connect each vertex to its incident edges
        for e in self.egi.E:
            for vid in self.egi.nu.get(e.id, ()):  # type: ignore[attr-defined]
                ll.ligature_endpoints.append((vid, e.id))
        return ll

    def fit_to_canvas(self, logical_layout: LogicalLayout, canvas_size: Tuple[int, int]) -> Tuple[Dict[str, SpatialBounds], Dict[str, Tuple[float, float, float, float]]]:
        """Compute area rectangles and per-area affine transforms from logical space to canvas.
        Produces precomputed area rectangles respecting containment and rough proportionality
        to content. This is a first-pass heuristic; later iterations can refine packing.
        """
        area_mappings: Dict[str, SpatialBounds] = {}
        transforms: Dict[str, Tuple[float, float, float, float]] = {}

        # Build index of elements per area
        elems_in_area: Dict[str, List[LogicalElement]] = {}
        for el in logical_layout.elements.values():
            elems_in_area.setdefault(el.area_id, []).append(el)

        # Recursive size calculation using area ~ sum(element areas) + sum(child areas)
        layout_tokens = self.style.resolve(type="layout")
        pad_in = float(layout_tokens.get("cut_padding", 20.0))
        gap = float(layout_tokens.get("cut_child_gap", 12.0))
        min_w, min_h = 80.0, 60.0

        computed_size: Dict[str, Tuple[float, float]] = {}

        def size_area(aid: str) -> Tuple[float, float]:
            if aid in computed_size:
                return computed_size[aid]
            # Content area from elements
            els = elems_in_area.get(aid, [])
            elem_area = 0.0
            max_elem_w = 0.0
            max_elem_h = 0.0
            for el in els:
                elem_area += max(1.0, el.est_width) * max(1.0, el.est_height)
                max_elem_w = max(max_elem_w, el.est_width)
                max_elem_h = max(max_elem_h, el.est_height)
            # Children
            children = logical_layout.areas.get(aid, LogicalArea(aid, None)).children
            child_sizes: List[Tuple[float, float]] = []
            for cid in children:
                cw, ch = size_area(cid)
                child_sizes.append((cw, ch))
            child_area = sum(cw * ch for cw, ch in child_sizes)
            max_child_w = max((cw for cw, _ in child_sizes), default=0.0)
            max_child_h = max((ch for _, ch in child_sizes), default=0.0)
            total_area = elem_area + child_area
            # Heuristic square-ish box
            inner_w = max(math.sqrt(total_area) if total_area > 0 else 0.0, max_elem_w, max_child_w)
            inner_h = max((total_area / inner_w) if inner_w > 0 else 0.0, max_elem_h, max_child_h)
            inner_w = max(inner_w, min_w - 2 * pad_in)
            inner_h = max(inner_h, min_h - 2 * pad_in)
            w = inner_w + 2 * pad_in
            h = inner_h + 2 * pad_in
            computed_size[aid] = (w, h)
            return w, h

        # Compute sizes bottom-up
        for aid in logical_layout.areas.keys():
            size_area(aid)

        # Determine top-level cuts (direct children of sheet)
        top_levels = [a.id for a in logical_layout.areas.values() if a.parent == self.egi.sheet]
        # Pack top-levels horizontally into a logical canvas, then scale to target canvas
        x_cursor = 20.0
        y_cursor = 20.0
        row_height = 0.0
        logical_canvas_w = 0.0
        logical_canvas_h = 0.0
        max_row_w = 1000.0  # arbitrary logical row width before wrap
        for aid in top_levels:
            w, h = computed_size[aid]
            if x_cursor + w > max_row_w and x_cursor > 20.0:
                # wrap
                x_cursor = 20.0
                y_cursor += row_height + gap
                row_height = 0.0
            area_mappings[aid] = SpatialBounds(x_cursor, y_cursor, w, h)
            x_cursor += w + gap
            row_height = max(row_height, h)
            logical_canvas_w = max(logical_canvas_w, x_cursor)
            logical_canvas_h = max(logical_canvas_h, y_cursor + row_height)

        # Place children within their parent interiors stacked vertically
        def place_children(aid: str):
            parent_bounds = area_mappings.get(aid)
            if not parent_bounds:
                return
            inner_x = parent_bounds.x + pad_in
            inner_y = parent_bounds.y + pad_in
            inner_w = max(0.0, parent_bounds.width - 2 * pad_in)
            # Stack
            cy = inner_y
            for cid in logical_layout.areas.get(aid, LogicalArea(aid, None)).children:
                cw, ch = computed_size[cid]
                # Clamp child to parent's inner width
                cw = min(cw, inner_w)
                area_mappings[cid] = SpatialBounds(inner_x, cy, cw, ch)
                cy += ch + gap
                place_children(cid)

        for aid in top_levels:
            place_children(aid)

        # Compute scale to fit target canvas
        canvas_w, canvas_h = float(canvas_size[0]), float(canvas_size[1])
        used_w = max((b.x + b.width for b in area_mappings.values()), default=1.0) + 20.0
        used_h = max((b.y + b.height for b in area_mappings.values()), default=1.0) + 20.0
        sx = canvas_w / used_w if used_w > 0 else 1.0
        sy = canvas_h / used_h if used_h > 0 else 1.0
        s = min(1.0, sx, sy)  # do not upscale above 1.0 for now

        # Apply scaling
        for aid, b in list(area_mappings.items()):
            nb = SpatialBounds(b.x * s, b.y * s, b.width * s, b.height * s)
            area_mappings[aid] = nb
            transforms[aid] = (s, s, 0.0, 0.0)

        return area_mappings, transforms
    
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
            # Put a hard cap to avoid pathological hierarchies causing long walks
            MAX_DEPTH = 256
            while True:
                if cur in seen:
                    # Detected a cycle in parent references; return current depth as a fallback
                    return depth
                if depth >= MAX_DEPTH:
                    # Defensive cap
                    return depth
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
            
            # If staged fitter provided bounds, use them; else compute default
            pre_bounds = self.correspondence.area_mappings.get(cut.id)
            if pre_bounds:
                bounds = pre_bounds
            else:
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
            # Only consult precomputed mappings when staged fitter is active
            if getattr(self, 'layout_mode', 'direct') == 'staged' and parent_area != self.egi.sheet:
                parent_bounds = self.correspondence.area_mappings.get(parent_area)
            else:
                parent_bounds = None
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
                # If child desired size exceeds parent's inner size, expand parent to fit
                parent_inner_w = max(0.0, parent_bounds.width - 2 * pad_in)
                parent_inner_h = max(0.0, parent_bounds.height - 2 * pad_in)
                need_expand_w = cut_width > parent_inner_w
                need_expand_h = cut_height > parent_inner_h
                if need_expand_w or need_expand_h:
                    # Grow parent minimally to accommodate child + padding
                    new_parent_w = parent_bounds.width
                    new_parent_h = parent_bounds.height
                    if need_expand_w:
                        delta_w = (cut_width - parent_inner_w)
                        new_parent_w = parent_bounds.width + max(0.0, delta_w)
                    if need_expand_h:
                        delta_h = (cut_height - parent_inner_h)
                        new_parent_h = parent_bounds.height + max(0.0, delta_h)
                    new_parent_bounds = SpatialBounds(parent_bounds.x, parent_bounds.y, new_parent_w, new_parent_h)
                    # Update parent in current layout if present
                    parent_elt = layout.get(parent_area)
                    if parent_elt and getattr(parent_elt, 'element_type', None) == 'cut':
                        layout[parent_area] = SpatialElement(
                            element_id=parent_elt.element_id,
                            element_type=parent_elt.element_type,
                            logical_area=parent_elt.logical_area,
                            spatial_bounds=new_parent_bounds
                        )
                    # Update correspondence mapping for parent area
                    self.correspondence.area_mappings[parent_area] = new_parent_bounds
                    # Update placed_bounds entry for the parent so sibling overlap checks see new size
                    updated_pb: List[Tuple[SpatialBounds, Optional[str]]] = []
                    for pb, pb_parent in placed_bounds:
                        if pb is parent_bounds and pb_parent == self._determine_cut_parent_area(parent_area):
                            updated_pb.append((new_parent_bounds, pb_parent))
                        else:
                            # If this tuple corresponds directly to the parent itself (parent id as element), keep same parent tag
                            if pb is parent_bounds and pb_parent == self._determine_cut_parent_area(parent_area):
                                updated_pb.append((new_parent_bounds, pb_parent))
                            else:
                                updated_pb.append((pb, pb_parent))
                    placed_bounds = updated_pb
                    parent_bounds = new_parent_bounds
                    # Recompute child anchor after parent expansion
                    nx = parent_bounds.x + pad_in
                    ny = parent_bounds.y + pad_in
                    parent_inner_w = max(0.0, parent_bounds.width - 2 * pad_in)
                    parent_inner_h = max(0.0, parent_bounds.height - 2 * pad_in)
                # Place child at requested size, clamped only by updated parent inner size (should now fit)
                nwidth = min(cut_width, max(10.0, parent_inner_w))
                nheight = min(cut_height, max(10.0, parent_inner_h))
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
                    if os.environ.get('ARISBE_DEBUG_EGI') == '1':
                        print(f"DEBUG: Sibling-overlap shift guard tripped for cut {cut.id} in parent {parent_area}; bounds={bounds}")
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

            # Ensure every vertex participating in the ligature is rendered as a visible dot/spot
            # This fixes the GUI symptom where only one vertex was shown.
            if vertex_ids:
                for vertex_id in vertex_ids:
                    # Skip if this vertex was already created earlier in the pipeline
                    if vertex_id in layout:
                        continue
                    # Seed new vertex positions uniquely within their logical area to avoid overlap.
                    # Use a golden-angle spiral around the area's center based on how many vertices
                    # are already placed in that area.
                    logical_area = self._determine_vertex_area(vertex_id)
                    area_bounds = self.correspondence.area_mappings.get(logical_area)
                    if area_bounds:
                        cx, cy = area_bounds.center()
                    else:
                        cx, cy = (200.0, 200.0)
                    # Count existing vertices in this area to pick a unique angle/radius
                    placed_in_area = 0
                    for _eid, _elem in layout.items():
                        if getattr(_elem, 'element_type', '') != 'vertex':
                            continue
                        if getattr(_elem, 'logical_area', None) == logical_area:
                            placed_in_area += 1
                    # Golden angle in radians ~ 137.507764°
                    golden = 2.399963229728653
                    k = placed_in_area
                    base_radius = 36.0
                    radius_growth = 10.0
                    r = base_radius + radius_growth * k
                    ang = golden * k
                    seed = (cx + r * math.cos(ang), cy + r * math.sin(ang))
                    center_pos = self._pick_safe_point_in_area(logical_area, layout, seed)
                    vertex_bounds = SpatialBounds(center_pos[0] - 5, center_pos[1] - 5, 10, 10)
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

            connected_vertices = tuple(self.egi.nu.get(edge.id, ()))
            # Arity-aware: handle 0-ary and n-ary uniformly
            logical_area = self._determine_element_area(edge.id)
            if not connected_vertices:
                # 0-ary predicate: pick a safe point in its logical area
                cx, cy = self._pick_safe_point_in_area(logical_area, layout, (200.0, 200.0))
            else:
                # Centroid of all argument vertices (use their centers if present, else safe points)
                pts: List[Tuple[float, float]] = []
                for vid in connected_vertices:
                    ve = layout.get(vid)
                    if ve and ve.spatial_bounds:
                        pts.append(ve.spatial_bounds.center())
                    else:
                        v_area = self._determine_vertex_area(vid)
                        pts.append(self._pick_safe_point_in_area(v_area, layout, (200.0, 200.0)))
                sx = sum(p[0] for p in pts)
                sy = sum(p[1] for p in pts)
                cx, cy = (sx / max(1, len(pts)), sy / max(1, len(pts)))

            # Initial offset from centroid to avoid sitting on top of vertices
            init_radius = 80.0
            px = cx + init_radius
            py = cy
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
            # Collision avoidance: keep predicate bounds from overlapping vertex spot
            # and other predicate labels already placed in the same area.
            def rects_overlap(a: SpatialBounds, b: SpatialBounds, margin: float = 0.0) -> bool:
                return not (a.x + a.width <= b.x - margin or b.x + b.width <= a.x - margin or
                            a.y + a.height <= b.y - margin or b.y + b.height <= a.y - margin)
            # Gather obstacles: all argument vertex spots and existing predicate labels in same area
            obstacles: List[SpatialBounds] = []
            for vid in connected_vertices:
                ve = layout.get(vid)
                if ve and ve.spatial_bounds:
                    obstacles.append(ve.spatial_bounds)
            for oid, oelem in layout.items():
                if getattr(oelem, 'element_type', '') != 'edge':
                    continue
                # Same logical area only
                if self._determine_element_area(oid) != logical_area:
                    continue
                obstacles.append(oelem.spatial_bounds)
            # Iteratively push label outward from base if overlapping any obstacle
            guard = 0
            layout_tokens = self.style.resolve(type="layout")
            step = float(layout_tokens.get("predicate_separation_step", 12.0))
            sep_margin = float(layout_tokens.get("predicate_separation_margin", 2.0))
            while any(rects_overlap(bounds, ob, sep_margin) for ob in obstacles):
                # Push further along the radial from base toward current label center
                rcx, rcy = bounds.center()
                vx, vy = cx, cy
                dx, dy = rcx - vx, rcy - vy
                d = math.hypot(dx, dy)
                if d < 1e-6:
                    dx, dy, d = 1.0, 0.0, 1.0
                ux, uy = dx / d, dy / d
                rcx, rcy = rcx + ux * step, rcy + uy * step
                # Rebuild bounds around the new center
                bounds = SpatialBounds(rcx - est_w / 2.0, rcy - est_h / 2.0, est_w, est_h)
                bounds = self._clamp_bounds_into_area(bounds, logical_area)
                bounds = self._avoid_child_cut_holes(bounds, logical_area, layout)
                guard += 1
                if guard > 50:
                    break
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
            # We will create arms from EVERY vertex on the ligature to predicates
            # incident to that vertex. Keep path continuous by inserting the base
            # point before each vertex's arm set.
            bases: List[Tuple[str, Tuple[float, float]]] = []
            for v_id in geom.vertices:
                v_elem = layout.get(v_id)
                if v_elem and v_elem.spatial_bounds:
                    bases.append((v_id, v_elem.spatial_bounds.center()))
            if not bases:
                continue

            # Build obstacle list for the ligature's area (use first vertex)
            lig_area = self._determine_ligature_area([geom.vertices[0]])
            obstacles: List[Tuple[float, float, float, float]] = []
            for c in self.egi.Cut:
                parent = self._determine_cut_parent_area(c.id)
                if parent == lig_area:
                    b = self.correspondence.area_mappings.get(c.id)
                    if b:
                        obstacles.append((b.x, b.y, b.width, b.height))

            # We now create ONE LIGATURE PER (vertex, edge) PAIR. For each connected predicate,
            # build a dedicated path from the vertex base to the predicate hook (with routing),
            # and emit it as its own SpatialElement. Finally, remove the original combined ligature.
            created_any = False
            for v_id, base in bases:
                connected = vertex_to_edges.get(v_id, [])
                if not connected:
                    continue
                for eid in connected:
                    e_elem = layout.get(eid)
                    if not e_elem:
                        continue
                    # Compute unique hook on predicate boundary
                    vseq = tuple(self.egi.nu.get(eid, ()))
                    try:
                        arg_index = vseq.index(v_id)
                    except ValueError:
                        arg_index = 0
                    arity = max(1, len(vseq))
                    hook_x, hook_y = self._hook_point_for_edge_argument(e_elem.spatial_bounds, arg_index, arity)
                    ex, ey = hook_x, hook_y
                    # Inward nudge
                    ls = self.style.resolve(type="ligature", role="ligature.arm")
                    eps_in = float(ls.get("border_overlap", 1.0))
                    rcx, rcy = e_elem.spatial_bounds.center()
                    ix, iy = (rcx - ex, rcy - ey)
                    ilen = math.hypot(ix, iy)
                    if ilen > 1e-6 and eps_in > 0:
                        ex += (ix / ilen) * eps_in
                        ey += (iy / ilen) * eps_in
                    # Minimal visible length
                    min_len = float(ls.get("min_length", 12.0))
                    dist = math.hypot(ex - base[0], ey - base[1])
                    if dist < min_len and dist > 1e-6:
                        ux, uy = (ex - base[0]) / dist, (ey - base[1]) / dist
                        ex, ey = ex + ux * (min_len - dist), ey + uy * (min_len - dist)
                    # Obstacles
                    lig_area = self._determine_ligature_area([v_id])
                    edge_area = self._determine_element_area(eid)
                    eff_obs = obstacles if edge_area == lig_area else []
                    label_obs: List[Tuple[float, float, float, float]] = []
                    if edge_area == lig_area:
                        for oid, oelem in layout.items():
                            if oid == eid:
                                continue
                            if getattr(oelem, 'element_type', '') != 'edge':
                                continue
                            if self._determine_element_area(oid) != edge_area:
                                continue
                            ob = oelem.spatial_bounds
                            pad = float(self.style.resolve(type="layout").get("label_obstacle_padding", 6.0))
                            label_obs.append((ob.x - pad, ob.y - pad, ob.width + 2 * pad, ob.height + 2 * pad))
                        ob = e_elem.spatial_bounds
                        pad = float(self.style.resolve(type="layout").get("label_obstacle_padding", 6.0))
                        label_obs.append((ob.x - pad, ob.y - pad, ob.width + 2 * pad, ob.height + 2 * pad))
                    # Approach point near hook
                    ux, uy = hook_x - rcx, hook_y - rcy
                    ulen = math.hypot(ux, uy)
                    if ulen > 1e-6:
                        ux, uy = ux / ulen, uy / ulen
                    else:
                        ux, uy = 1.0, 0.0
                    approach_margin = float(self.style.resolve(type="layout").get("ligature_approach_margin", 4.0))
                    approach_pt = (hook_x + ux * approach_margin, hook_y + uy * approach_margin)
                    if edge_area != lig_area:
                        cut_b = self.correspondence.area_mappings.get(edge_area)
                        if cut_b:
                            ax, ay = approach_pt
                            ax = min(max(ax, cut_b.x + 1.0), cut_b.x + cut_b.width - 1.0)
                            ay = min(max(ay, cut_b.y + 1.0), cut_b.y + cut_b.height - 1.0)
                            approach_pt = (ax, ay)
                    # Route base -> approach with visibility avoiding obstacles and forbidding leaving area
                    # Build boundary walls around lig_area so the path stays inside, and child cuts are holes
                    area_bounds = self.correspondence.area_mappings.get(lig_area)
                    area_walls: List[Tuple[float, float, float, float]] = []
                    if area_bounds:
                        ax, ay, aw, ah = area_bounds.x, area_bounds.y, area_bounds.width, area_bounds.height
                        BIG = 100000.0
                        # Left wall
                        area_walls.append((ax - BIG, ay - BIG, BIG, ah + 2 * BIG))
                        # Right wall
                        area_walls.append((ax + aw, ay - BIG, BIG, ah + 2 * BIG))
                        # Top wall
                        area_walls.append((ax - BIG, ay - BIG, aw + 2 * BIG, BIG))
                        # Bottom wall
                        area_walls.append((ax - BIG, ay + ah, aw + 2 * BIG, BIG))
                    # Route with combined obstacles
                    arm_path = self._visibility_route(base, approach_pt, label_obs + eff_obs + area_walls)
                    if (not arm_path) and (edge_area != lig_area):
                        arm_path = [base, approach_pt]
                    if not arm_path:
                        continue
                    # Ensure the path starts from base and ends at hook point
                    if arm_path[0] != base:
                        arm_path = [base] + arm_path
                    if arm_path[-1] != (ex, ey):
                        arm_path = arm_path + [(ex, ey)]
                    # Post-process this small path with the same repair routine used below
                    # but localized to this path; reuse the existing repair section by
                    # temporarily assigning and running the same logic on 'arm_path'.
                    # Build global rect lists once
                    raw_label_rects_all: List[Tuple[float, float, float, float]] = []
                    label_rects: List[Tuple[float, float, float, float]] = []
                    for oid, oelem in layout.items():
                        if getattr(oelem, 'element_type', '') != 'edge':
                            continue
                        ob = oelem.spatial_bounds
                        raw_label_rects_all.append((ob.x, ob.y, ob.width, ob.height))
                        pad = float(self.style.resolve(type="layout").get("label_obstacle_padding", 6.0))
                        label_rects.append((ob.x - pad, ob.y - pad, ob.width + 2 * pad, ob.height + 2 * pad))
                    raw_cut_rects_all: List[Tuple[float, float, float, float]] = []
                    for c in self.egi.Cut:
                        b = self.correspondence.area_mappings.get(c.id)
                        if b:
                            raw_cut_rects_all.append((b.x, b.y, b.width, b.height))
                    def _pt_in_rect(p: Tuple[float, float], r: Tuple[float, float, float, float]) -> bool:
                        rx, ry, rw, rh = r
                        return (rx < p[0] < rx + rw) and (ry < p[1] < ry + rh)
                    def _pt_on_rect_border(p: Tuple[float, float], r: Tuple[float, float, float, float]) -> bool:
                        rx, ry, rw, rh = r
                        on_left = abs(p[0] - rx) < 1e-6 and (ry - 1e-6) <= p[1] <= (ry + rh + 1e-6)
                        on_right = abs(p[0] - (rx + rw)) < 1e-6 and (ry - 1e-6) <= p[1] <= (ry + rh + 1e-6)
                        on_top = abs(p[1] - ry) < 1e-6 and (rx - 1e-6) <= p[0] <= (rx + rw + 1e-6)
                        on_bottom = abs(p[1] - (ry + rh)) < 1e-6 and (rx - 1e-6) <= p[0] <= (rx + rw + 1e-6)
                        return on_left or on_right or on_top or on_bottom
                    def _seg_still_crosses(path: List[Tuple[float, float]]) -> bool:
                        for j in range(1, len(path)):
                            pa = path[j-1]
                            pb = path[j]
                            for rr in raw_label_rects_all:
                                if self._segment_intersects_rect(pa, pb, rr):
                                    ain = _pt_in_rect(pa, rr) or _pt_on_rect_border(pa, rr)
                                    bin = _pt_in_rect(pb, rr) or _pt_on_rect_border(pb, rr)
                                    if not (ain ^ bin):
                                        return True
                            for rr in raw_cut_rects_all:
                                if self._segment_intersects_rect(pa, pb, rr):
                                    ain = _pt_in_rect(pa, rr) or _pt_on_rect_border(pa, rr)
                                    bin = _pt_in_rect(pb, rr) or _pt_on_rect_border(pb, rr)
                                    if not (ain ^ bin):
                                        return True
                        return False
                    # Robust re-route to clean pass-throughs (labels and cuts)
                    base_pad = float(self.style.resolve(type="layout").get("label_obstacle_padding", 6.0))
                    padded_cuts = [(x - base_pad, y - base_pad, w + 2 * base_pad, h + 2 * base_pad) for (x, y, w, h) in raw_cut_rects_all]
                    repaired = [arm_path[0]]
                    for i in range(1, len(arm_path)):
                        a, bpt = repaired[-1], arm_path[i]
                        # Detect true pass-throughs of any label rect
                        offending_rect: Optional[Tuple[float, float, float, float]] = None
                        crosses = False
                        for rr in raw_label_rects_all:
                            if self._segment_intersects_rect(a, bpt, rr):
                                ain = _pt_in_rect(a, rr) or _pt_on_rect_border(a, rr)
                                bin = _pt_in_rect(bpt, rr) or _pt_on_rect_border(bpt, rr)
                                if not (ain ^ bin):
                                    crosses = True
                                    offending_rect = rr
                                    break
                        if not crosses:
                            repaired.append(bpt)
                            continue
                        # 1) Try visibility route around padded obstacles (labels + cuts)
                        seg2 = self._visibility_route(a, bpt, label_rects + padded_cuts)
                        def _seg_still_crosses(path: List[Tuple[float, float]]) -> bool:
                            for j in range(1, len(path)):
                                pa, pb = path[j-1], path[j]
                                for rr in raw_label_rects_all:
                                    if self._segment_intersects_rect(pa, pb, rr):
                                        ain = _pt_in_rect(pa, rr) or _pt_on_rect_border(pa, rr)
                                        bin = _pt_in_rect(pb, rr) or _pt_on_rect_border(pb, rr)
                                        if not (ain ^ bin):
                                            return True
                                for rr in raw_cut_rects_all:
                                    if self._segment_intersects_rect(pa, pb, rr):
                                        ain = _pt_in_rect(pa, rr) or _pt_on_rect_border(pa, rr)
                                        bin = _pt_in_rect(pb, rr) or _pt_on_rect_border(pb, rr)
                                        if not (ain ^ bin):
                                            return True
                            return False
                        if seg2 and not _seg_still_crosses(seg2):
                            if repaired[-1] == seg2[0]:
                                repaired.extend(seg2[1:])
                            else:
                                repaired.extend(seg2)
                            continue
                        # 2) Corner detours around the offending rect with extra padding
                        if offending_rect is not None:
                            rx, ry, rw, rh = offending_rect
                            pad_try = max(base_pad, 12.0)
                            def build_padded_rects(extra: float) -> List[Tuple[float, float, float, float]]:
                                out: List[Tuple[float, float, float, float]] = []
                                for rr in raw_label_rects_all:
                                    x, y, w, h = rr
                                    p = base_pad + extra
                                    out.append((x - p, y - p, w + 2 * p, h + 2 * p))
                                for rr in raw_cut_rects_all:
                                    x, y, w, h = rr
                                    p = base_pad + extra
                                    out.append((x - p, y - p, w + 2 * p, h + 2 * p))
                                return out
                            label_rects_padded = build_padded_rects(pad_try - base_pad)
                            candidates = [
                                (rx - pad_try, ry - pad_try),
                                (rx + rw + pad_try, ry - pad_try),
                                (rx + rw + pad_try, ry + rh + pad_try),
                                (rx - pad_try, ry + rh + pad_try),
                            ]
                            success = False
                            for c in candidates:
                                det1 = self._visibility_route(a, c, label_rects_padded)
                                det2 = self._visibility_route(c, bpt, label_rects_padded)
                                if det1 and det2 and not _seg_still_crosses(det1) and not _seg_still_crosses(det2):
                                    if repaired[-1] == det1[0]:
                                        repaired.extend(det1[1:])
                                    else:
                                        repaired.extend(det1)
                                    if repaired[-1] == det2[0]:
                                        repaired.extend(det2[1:])
                                    else:
                                        repaired.extend(det2)
                                    success = True
                                    break
                            if not success:
                                # 3) L-shaped fallback detours
                                heavy_extra = max(24.0 - base_pad, 12.0)
                                label_rects_heavy = build_padded_rects(heavy_extra)
                                dx, dy = bpt[0] - a[0], bpt[1] - a[1]
                                L = math.hypot(dx, dy) or 1.0
                                nx, ny = -dy / L, dx / L
                                offset = pad_try
                                waypoints = [
                                    (a[0] + nx * offset, a[1] + ny * offset),
                                    (a[0] - nx * offset, a[1] - ny * offset),
                                ]
                                lsuccess = False
                                for w in waypoints:
                                    det1 = self._visibility_route(a, w, label_rects_heavy)
                                    det2 = self._visibility_route(w, bpt, label_rects_heavy)
                                    if det1 and det2 and not _seg_still_crosses(det1) and not _seg_still_crosses(det2):
                                        if repaired[-1] == det1[0]:
                                            repaired.extend(det1[1:])
                                        else:
                                            repaired.extend(det1)
                                        if repaired[-1] == det2[0]:
                                            repaired.extend(det2[1:])
                                        else:
                                            repaired.extend(det2)
                                        lsuccess = True
                                        break
                                if lsuccess:
                                    continue
                        # Give up this segment; keep original to avoid infinite loops
                        repaired.append(bpt)
                    arm_path = repaired
                    # Fail-closed validation: the arm must remain within its logical area.
                    # If the edge is in a child cut, allow the final waypoint to enter that child.
                    try:
                        if edge_area == lig_area:
                            self._assert_path_within_area(arm_path, lig_area)
                        else:
                            self._assert_path_within_area(arm_path, lig_area, allowed_child=edge_area, allow_last_inside_child=True)
                    except AssertionError:
                        # If invalid, attempt one more route with heavier label padding; else re-raise
                        heavy_pad = float(self.style.resolve(type="layout").get("label_obstacle_padding", 6.0)) * 2.0
                        heavy_labels = []
                        for oid, oelem in layout.items():
                            if getattr(oelem, 'element_type', '') == 'edge':
                                ob = oelem.spatial_bounds
                                heavy_labels.append((ob.x - heavy_pad, ob.y - heavy_pad, ob.width + 2 * heavy_pad, ob.height + 2 * heavy_pad))
                        retry = self._visibility_route(base, approach_pt, heavy_labels + area_walls)
                        if retry:
                            if retry[0] != base:
                                retry = [base] + retry
                            if retry[-1] != (ex, ey):
                                retry = retry + [(ex, ey)]
                            if edge_area == lig_area:
                                self._assert_path_within_area(retry, lig_area)
                            else:
                                self._assert_path_within_area(retry, lig_area, allowed_child=edge_area, allow_last_inside_child=True)
                            arm_path = retry
                        else:
                            # Fail-closed: raise explicit error
                            raise
                    # Emit spatial element for this pair
                    new_id = f"{lid}__{v_id}__{eid}"
                    lg = LigatureGeometry(ligature_id=new_id, vertices=[v_id], spatial_path=arm_path, branching_points=[])
                    new_bounds = self._ligature_bounds_excluding_children(lig_area, arm_path, layout)
                    layout[new_id] = SpatialElement(element_id=new_id, element_type='ligature', logical_area=lig_area, spatial_bounds=new_bounds, ligature_geometry=lg)
                    self.correspondence.ligature_mappings[new_id] = lg
                    created_any = True

            # Optional vertex-side trunk consolidation: share base->hub segment across
            # ligatures that connect to the same vertex (predicate independence preserved).
            if created_any:
                layout_tokens = self.style.resolve(type="layout")
                enable_branch = bool(layout_tokens.get("enable_vertex_branch_consolidation", False))
                if enable_branch:
                    # Group newly created ligatures by vertex id
                    base_by_vertex: Dict[str, Tuple[float, float]] = {vid: b for vid, b in bases}
                    for v_id, base in base_by_vertex.items():
                        # Collect ligature IDs created for this vertex
                        created_ids: List[str] = []
                        for eid in vertex_to_edges.get(v_id, []):
                            nid = f"{lid}__{v_id}__{eid}"
                            if nid in self.correspondence.ligature_mappings:
                                created_ids.append(nid)
                        if len(created_ids) <= 1:
                            continue
                        # Determine hub direction by averaging initial arm directions
                        avg_dx = 0.0
                        avg_dy = 0.0
                        samples = 0
                        for nid in created_ids:
                            geom_i = self.correspondence.ligature_mappings.get(nid)
                            if not geom_i or not geom_i.spatial_path or len(geom_i.spatial_path) < 2:
                                continue
                            p0, p1 = geom_i.spatial_path[0], geom_i.spatial_path[1]
                            dx, dy = (p1[0] - p0[0], p1[1] - p0[1])
                            L = math.hypot(dx, dy)
                            if L > 1e-6:
                                avg_dx += dx / L
                                avg_dy += dy / L
                                samples += 1
                        if samples == 0:
                            continue
                        avg_dx /= samples
                        avg_dy /= samples
                        norm = math.hypot(avg_dx, avg_dy) or 1.0
                        avg_dx /= norm
                        avg_dy /= norm
                        trunk_len = float(layout_tokens.get("ligature_trunk_offset", 12.0))
                        hub = (base[0] + avg_dx * trunk_len, base[1] + avg_dy * trunk_len)
                        # Clamp hub into the correct area (avoid leaving ligature area)
                        v_area = self._determine_ligature_area([v_id])
                        area_bounds = self.correspondence.area_mappings.get(v_area)
                        if area_bounds:
                            hx = min(max(hub[0], area_bounds.x + 1.0), area_bounds.x + area_bounds.width - 1.0)
                            hy = min(max(hub[1], area_bounds.y + 1.0), area_bounds.y + area_bounds.height - 1.0)
                            hub = (hx, hy)
                        # Build obstacles in vertex area
                        label_obs_v: List[Tuple[float, float, float, float]] = []
                        pad_v = float(layout_tokens.get("label_obstacle_padding", 6.0))
                        for oid, oelem in layout.items():
                            if getattr(oelem, 'element_type', '') != 'edge':
                                continue
                            if self._determine_element_area(oid) != v_area:
                                continue
                            ob = oelem.spatial_bounds
                            label_obs_v.append((ob.x - pad_v, ob.y - pad_v, ob.width + 2 * pad_v, ob.height + 2 * pad_v))
                        # Add child cut holes in this area as obstacles
                        cut_obs_v: List[Tuple[float, float, float, float]] = []
                        for c in self.egi.Cut:
                            parent = self._determine_cut_parent_area(c.id)
                            if parent == v_area:
                                b = self.correspondence.area_mappings.get(c.id)
                                if b:
                                    cut_obs_v.append((b.x, b.y, b.width, b.height))
                        # Route base -> hub with visibility avoiding obstacles and forbidding leaving area
                        # Build boundary walls around v_area so the path stays inside, and child cuts are holes
                        area_walls_v: List[Tuple[float, float, float, float]] = []
                        if area_bounds:
                            ax, ay, aw, ah = area_bounds.x, area_bounds.y, area_bounds.width, area_bounds.height
                            BIG = 100000.0
                            # Left wall
                            area_walls_v.append((ax - BIG, ay - BIG, BIG, ah + 2 * BIG))
                            # Right wall
                            area_walls_v.append((ax + aw, ay - BIG, BIG, ah + 2 * BIG))
                            # Top wall
                            area_walls_v.append((ax - BIG, ay - BIG, aw + 2 * BIG, BIG))
                            # Bottom wall
                            area_walls_v.append((ax - BIG, ay + ah, aw + 2 * BIG, BIG))
                        b2h = self._visibility_route(base, hub, label_obs_v + cut_obs_v + area_walls_v) or [base, hub]
                        # Update each per-pair ligature path to include shared trunk and reroute from hub
                        for nid in created_ids:
                            geom_i = self.correspondence.ligature_mappings.get(nid)
                            if not geom_i or not geom_i.spatial_path or len(geom_i.spatial_path) < 2:
                                continue
                            old = geom_i.spatial_path
                            # Ensure first point equals base
                            if old[0] != base:
                                # connect to old[0] first
                                conn = self._visibility_route(base, old[0], label_obs_v + cut_obs_v + area_walls_v) or [base, old[0]]
                                prefix = conn
                            else:
                                prefix = []
                            # Build new path: base->hub trunk, then hub->old[1], then rest
                            newp: List[Tuple[float, float]] = []
                            newp.append(base)
                            # append b2h without duplicating base
                            if b2h[0] == base:
                                newp.extend(b2h[1:])
                            else:
                                newp.extend(b2h)
                            # If we added a prefix connector, include it after hub (rare)
                            if prefix:
                                # connect hub to start of prefix if needed
                                hub_to_pref = self._visibility_route(newp[-1], prefix[0], label_obs_v + cut_obs_v + area_walls_v)
                                if hub_to_pref:
                                    if newp[-1] == hub_to_pref[0]:
                                        newp.extend(hub_to_pref[1:])
                                    else:
                                        newp.extend(hub_to_pref)
                                newp.extend(prefix[1:])
                            # Connect from hub to old[1]
                            target_after_hub = old[1]
                            hub_to_first = self._visibility_route(newp[-1], target_after_hub, label_obs_v + cut_obs_v + area_walls_v)
                            if hub_to_first:
                                if newp[-1] == hub_to_first[0]:
                                    newp.extend(hub_to_first[1:])
                                else:
                                    newp.extend(hub_to_first)
                            # Append the rest of the existing path
                            newp.extend(old[2:])
                            # Final repair using existing pass-through fixer for per-pair arms
                            # Reuse the local repair approach: collect rects (already above in this function)
                            raw_label_rects_all: List[Tuple[float, float, float, float]] = []
                            label_rects_all: List[Tuple[float, float, float, float]] = []
                            for oid, oelem in layout.items():
                                if getattr(oelem, 'element_type', '') != 'edge':
                                    continue
                                ob = oelem.spatial_bounds
                                raw_label_rects_all.append((ob.x, ob.y, ob.width, ob.height))
                                label_rects_all.append((ob.x - pad_v, ob.y - pad_v, ob.width + 2 * pad_v, ob.height + 2 * pad_v))
                            raw_cut_rects_all: List[Tuple[float, float, float, float]] = []
                            for c in self.egi.Cut:
                                b = self.correspondence.area_mappings.get(c.id)
                                if b:
                                    raw_cut_rects_all.append((b.x, b.y, b.width, b.height))
                            def _pt_in_rect2(p: Tuple[float, float], r: Tuple[float, float, float, float]) -> bool:
                                rx, ry, rw, rh = r
                                return (rx < p[0] < rx + rw) and (ry < p[1] < ry + rh)
                            def _pt_on_border2(p: Tuple[float, float], r: Tuple[float, float, float, float]) -> bool:
                                rx, ry, rw, rh = r
                                on_left = abs(p[0] - rx) < 1e-6 and (ry - 1e-6) <= p[1] <= (ry + rh + 1e-6)
                                on_right = abs(p[0] - (rx + rw)) < 1e-6 and (ry - 1e-6) <= p[1] <= (ry + rh + 1e-6)
                                on_top = abs(p[1] - ry) < 1e-6 and (rx - 1e-6) <= p[0] <= (rx + rw + 1e-6)
                                on_bottom = abs(p[1] - (ry + rh)) < 1e-6 and (rx - 1e-6) <= p[0] <= (rx + rw + 1e-6)
                                return on_left or on_right or on_top or on_bottom
                            def _pass_through(a: Tuple[float, float], bpt: Tuple[float, float]) -> bool:
                                for rr in raw_label_rects_all + raw_cut_rects_all:
                                    if self._segment_intersects_rect(a, bpt, rr):
                                        ain = _pt_in_rect2(a, rr) or _pt_on_border2(a, rr)
                                        binv = _pt_in_rect2(bpt, rr) or _pt_on_border2(bpt, rr)
                                        if not (ain ^ binv):
                                            return True
                                return False
                            repaired = [newp[0]]
                            for i in range(1, len(newp)):
                                a, bpt = repaired[-1], newp[i]
                                if _pass_through(a, bpt):
                                    seg2 = self._visibility_route(a, bpt, label_rects_all + cut_obs_v + area_walls_v)
                                    if seg2:
                                        if repaired[-1] == seg2[0]:
                                            repaired.extend(seg2[1:])
                                        else:
                                            repaired.extend(seg2)
                                    else:
                                        repaired.append(bpt)
                                else:
                                    repaired.append(bpt)
                            # Fail-closed validation: ensure consolidated path remains in area
                            self._assert_path_within_area(repaired, v_area)
                            # Update geometry and bounds
                            geom_i.spatial_path = repaired
                            nb = self._ligature_bounds_excluding_children(v_area, repaired, layout)
                            layout[nid].spatial_bounds = nb
                            try:
                                bp = BranchingPoint(ligature_id=nid, position_on_ligature=0.05, spatial_position=hub, constant_label=self._get_vertex_constant_label(v_id))
                                geom_i.branching_points.append(bp)
                            except Exception:
                                pass
                            new_bounds_i = self._ligature_bounds_excluding_children(v_area, repaired, layout)
                            se = layout.get(nid)
                            if se:
                                se.spatial_bounds = new_bounds_i
                                se.ligature_geometry = geom_i
                                self.correspondence.ligature_mappings[nid] = geom_i

            # Remove the original combined ligature element if we created per-pair ligatures
            if created_any:
                layout.pop(lid, None)
                self.correspondence.ligature_mappings.pop(lid, None)
                continue

            # Fallback (should not happen): if nothing created, keep old path logic for safety
            new_path: List[Tuple[float, float]] = []
            # Post-process: repair any segment that intersects a predicate label rect.
            lig_area = self._determine_ligature_area([geom.vertices[0]])
            # Build raw and padded label rects for ALL predicate labels across areas,
            # and include ALL cut rectangles as additional obstacles to avoid.
            raw_label_rects_all: List[Tuple[float, float, float, float]] = []
            label_rects: List[Tuple[float, float, float, float]] = []
            for oid, oelem in layout.items():
                if getattr(oelem, 'element_type', '') != 'edge':
                    continue
                ob = oelem.spatial_bounds
                raw_label_rects_all.append((ob.x, ob.y, ob.width, ob.height))
                layout_tokens = self.style.resolve(type="layout")
                pad = float(layout_tokens.get("label_obstacle_padding", 6.0))
                label_rects.append((ob.x - pad, ob.y - pad, ob.width + 2 * pad, ob.height + 2 * pad))
            # All cut rects (used as obstacles during post-processing)
            raw_cut_rects_all: List[Tuple[float, float, float, float]] = []
            for c in self.egi.Cut:
                b = self.correspondence.area_mappings.get(c.id)
                if b:
                    raw_cut_rects_all.append((b.x, b.y, b.width, b.height))
            # Local helpers to mirror test semantics
            def _pt_in_rect(p: Tuple[float, float], r: Tuple[float, float, float, float]) -> bool:
                rx, ry, rw, rh = r
                return (rx < p[0] < rx + rw) and (ry < p[1] < ry + rh)
            def _pt_on_rect_border(p: Tuple[float, float], r: Tuple[float, float, float, float]) -> bool:
                rx, ry, rw, rh = r
                on_left = abs(p[0] - rx) < 1e-6 and (ry - 1e-6) <= p[1] <= (ry + rh + 1e-6)
                on_right = abs(p[0] - (rx + rw)) < 1e-6 and (ry - 1e-6) <= p[1] <= (ry + rh + 1e-6)
                on_top = abs(p[1] - ry) < 1e-6 and (rx - 1e-6) <= p[0] <= (rx + rw + 1e-6)
                on_bottom = abs(p[1] - (ry + rh)) < 1e-6 and (rx - 1e-6) <= p[0] <= (rx + rw + 1e-6)
                return on_left or on_right or on_top or on_bottom
            # Iterate repair up to a few passes to remove cascading crossings
            passes = 0
            path_in = new_path
            while passes < 6:
                repaired: List[Tuple[float, float]] = []
                any_fixed = False
                for i, pt in enumerate(path_in):
                    if i == 0:
                        repaired.append(pt)
                        continue
                    a = repaired[-1]
                    b = pt
                    # Check intersection against unpadded rects (test uses raw); reroute only
                    # true pass-throughs (both endpoints outside but segment cuts the rect).
                    crosses = False
                    offending_rect: Optional[Tuple[float, float, float, float]] = None
                    # Track whether we successfully replaced this segment with a detour
                    detoured = False
                    for rect in raw_label_rects_all:
                        if self._segment_intersects_rect(a, b, rect):
                            a_in = _pt_in_rect(a, rect) or _pt_on_rect_border(a, rect)
                            b_in = _pt_in_rect(b, rect) or _pt_on_rect_border(b, rect)
                            if not (a_in ^ b_in):
                                crosses = True
                                offending_rect = rect
                                break
                    if crosses:
                        # Rerouting policy:
                        # - A reroute is accepted ONLY if it eliminates true pass-throughs of any
                        #   predicate label rectangle. A pass-through means a segment intersects a
                        #   label rect while both endpoints are outside that rect. Touching or entering
                        #   from one side and stopping inside is permitted (endpoints on/inside allowed).
                        # - Try a direct visibility route first, then corner-detours using padded
                        #   rectangles, then a last-resort L-shaped detour. Each candidate path is
                        #   validated with `_seg_still_crosses()` before acceptance.
                        # Only mark any_fixed if we actually change the segment
                        modified = False
                        # Attempt a direct visibility-route around current label and cut obstacles.
                        # Important: we only accept reroutes that truly eliminate pass-throughs
                        # (segments that cut across a label rect while both endpoints lie outside).
                        # Build combined padded obstacles (labels + cuts)
                        layout_tokens = self.style.resolve(type="layout")
                        base_pad = float(layout_tokens.get("label_obstacle_padding", 6.0))
                        padded_cuts = [(x - base_pad, y - base_pad, w + 2 * base_pad, h + 2 * base_pad) for (x, y, w, h) in raw_cut_rects_all]
                        seg = self._visibility_route(a, b, label_rects + padded_cuts)
                        # Validate that the rerouted seg no longer performs a true pass-through
                        def _seg_still_crosses(path: List[Tuple[float, float]]) -> bool:
                            for j in range(1, len(path)):
                                pa = path[j-1]
                                pb = path[j]
                                # Check against label rects
                                for rr in raw_label_rects_all:
                                    if self._segment_intersects_rect(pa, pb, rr):
                                        ain = _pt_in_rect(pa, rr) or _pt_on_rect_border(pa, rr)
                                        bin = _pt_in_rect(pb, rr) or _pt_on_rect_border(pb, rr)
                                        if not (ain ^ bin):
                                            return True
                                # Also ensure we do not pass through any cut rectangle
                                for rr in raw_cut_rects_all:
                                    if self._segment_intersects_rect(pa, pb, rr):
                                        ain = _pt_in_rect(pa, rr) or _pt_on_rect_border(pa, rr)
                                        bin = _pt_in_rect(pb, rr) or _pt_on_rect_border(pb, rr)
                                        if not (ain ^ bin):
                                            return True
                            return False
                        if seg and not _seg_still_crosses(seg):
                            if repaired and repaired[-1] == seg[0]:
                                repaired.extend(seg[1:])
                            else:
                                repaired.extend(seg)
                            # We handled the crossing by rerouting this segment; proceed to next pass
                            any_fixed = True
                            detoured = True
                            break
                        # Fallback: try routing via a corner outside the offending rect (and padded rects).
                        # We again only accept detours that avoid true pass-throughs.
                        detoured = False
                        if offending_rect is not None:
                            rx, ry, rw, rh = offending_rect
                            layout_tokens = self.style.resolve(type="layout")
                            base_pad = float(layout_tokens.get("label_obstacle_padding", 6.0))
                            pad_try = max(base_pad, 12.0)
                            def build_padded_rects(extra: float) -> List[Tuple[float, float, float, float]]:
                                out: List[Tuple[float, float, float, float]] = []
                                # Include labels
                                for rr in raw_label_rects_all:
                                    x, y, w, h = rr
                                    p = base_pad + extra
                                    out.append((x - p, y - p, w + 2 * p, h + 2 * p))
                                # Include cuts
                                for rr in raw_cut_rects_all:
                                    x, y, w, h = rr
                                    p = base_pad + extra
                                    out.append((x - p, y - p, w + 2 * p, h + 2 * p))
                                return out
                            # First attempt with moderately increased padding
                            label_rects_padded = build_padded_rects(pad_try - base_pad)
                            candidates = [
                                (rx - pad_try, ry - pad_try),
                                (rx + rw + pad_try, ry - pad_try),
                                (rx + rw + pad_try, ry + rh + pad_try),
                                (rx - pad_try, ry + rh + pad_try),
                            ]
                            success = False
                            for c in candidates:
                                det1 = self._visibility_route(a, c, label_rects_padded)
                                det2 = self._visibility_route(c, b, label_rects_padded)
                                if det1 and det2 and not _seg_still_crosses(det1) and not _seg_still_crosses(det2):
                                    any_fixed = True
                                    if repaired[-1] == det1[0]:
                                        repaired.extend(det1[1:])
                                    else:
                                        repaired.extend(det1)
                                    if repaired[-1] == det2[0]:
                                        repaired.extend(det2[1:])
                                    else:
                                        repaired.extend(det2)
                                    success = True
                                    break
                            if not success:
                                # Retry with heavy padding to strongly repel path from labels.
                                heavy_extra = max(24.0 - base_pad, 12.0)
                                label_rects_heavy = build_padded_rects(heavy_extra)
                                for c in candidates:
                                    det1 = self._visibility_route(a, c, label_rects_heavy)
                                    det2 = self._visibility_route(c, b, label_rects_heavy)
                                    if det1 and det2 and not _seg_still_crosses(det1) and not _seg_still_crosses(det2):
                                        any_fixed = True
                                        if repaired[-1] == det1[0]:
                                            repaired.extend(det1[1:])
                                        else:
                                            repaired.extend(det1)
                                        if repaired[-1] == det2[0]:
                                            repaired.extend(det2[1:])
                                        else:
                                            repaired.extend(det2)
                                        success = True
                                        break
                            if not success:
                                # As a last resort, try an L-shaped detour: from a, step perpendicular by
                                # an offset, then route to b. Accept only if both legs avoid pass-throughs.
                                dx, dy = b[0] - a[0], b[1] - a[1]
                                L = math.hypot(dx, dy) or 1.0
                                nx, ny = -dy / L, dx / L
                                offset = pad_try
                                waypoints = [
                                    (a[0] + nx * offset, a[1] + ny * offset),
                                    (a[0] - nx * offset, a[1] - ny * offset),
                                ]
                                for w in waypoints:
                                    det1 = self._visibility_route(a, w, label_rects_heavy)
                                    det2 = self._visibility_route(w, b, label_rects_heavy)
                                    if det1 and det2 and not _seg_still_crosses(det1) and not _seg_still_crosses(det2):
                                        any_fixed = True
                                        if repaired[-1] == det1[0]:
                                            repaired.extend(det1[1:])
                                        else:
                                            repaired.extend(det1)
                                        if repaired[-1] == det2[0]:
                                            repaired.extend(det2[1:])
                                        else:
                                            repaired.extend(det2)
                                        success = True
                                        break
                                if not success:
                                    # Give up this segment (keep original); tests will surface the issue.
                                    # Do not mark detoured/any_fixed so we can continue scanning later segments.
                                    pass
                        # Only break early if we actually modified the path
                        if any_fixed:
                            detoured = True
                            break
                        if not detoured:
                            repaired.append(b)
                    else:
                        repaired.append(b)
                path_out = repaired
                passes += 1
                if not any_fixed:
                    break
                path_in = path_out
            # Update geometry and bounds using the final repaired path
            geom.spatial_path = path_out
            # Use the area of the first vertex to determine child-hole exclusions
            nb = self._ligature_bounds_excluding_children(lig_area, path_out, layout)
            elt.spatial_bounds = nb

    def _hook_point_for_edge_argument(self, bounds: SpatialBounds, index: int, arity: int) -> Tuple[float, float]:
        """Return a unique point on the rectangle boundary of a predicate label box
        for the given argument index in ν(edge). We distribute hooks evenly along
        the rectangle's perimeter, offsetting by half a slot to avoid corners.
        """
        # Guard
        if arity <= 0:
            return bounds.center()
        # Perimeter parameter t in [0, P)
        P = 2.0 * (bounds.width + bounds.height)
        if P <= 0.0:
            return bounds.center()
        # Half-slot offset prevents hooks sitting exactly on corners
        slot = P / float(arity)
        t = (index + 0.5) * slot
        # Reduce t modulo perimeter
        t = t % P
        x0, y0, w, h = bounds.x, bounds.y, bounds.width, bounds.height
        # Map t along rectangle: top edge (left->right), right edge (top->bottom),
        # bottom edge (right->left), left edge (bottom->top)
        if t <= w:
            return (x0 + t, y0)
        t -= w
        if t <= h:
            return (x0 + w, y0 + t)
        t -= h
        if t <= w:
            return (x0 + w - t, y0 + h)
        t -= w
        # Left edge
        return (x0, y0 + h - t)

    def _position_superscripts(self, layout: Dict[str, SpatialElement]) -> None:
        """Compute collision-avoided positions for:
        - vertex variable label superscripts (small text near vertex dot)
        - predicate arity superscripts (small text near the edge label box top-right)
        Bounds are estimated using style tokens and adjusted to avoid overlaps with
        nearby obstacles in the same logical area and to stay out of child cut holes.
        """
        # Style tokens for estimation
        vts = self.style.resolve(type="vertex", role="vertex.superscript_text")
        v_est_w = float(vts.get("estimate_char_width", 5.0))
        v_est_h = float(vts.get("estimate_height", 10.0))
        ets = self.style.resolve(type="edge", role="edge.superscript_text")
        e_est_w = float(ets.get("estimate_char_width", 4.0))
        e_est_h = float(ets.get("estimate_height", 9.0))
        layout_tokens = self.style.resolve(type="layout")
        step = float(layout_tokens.get("predicate_separation_step", 12.0))
        sep_margin = float(layout_tokens.get("predicate_separation_margin", 2.0))

        # Helper for overlap test
        def rects_overlap(a: SpatialBounds, b: SpatialBounds, margin: float = 0.0) -> bool:
            return not (a.x + a.width <= b.x - margin or b.x + b.width <= a.x - margin or
                        a.y + a.height <= b.y - margin or b.y + b.height <= a.y - margin)

        # Build quick lookup for area bounds and child cut holes per area
        area_children: Dict[str, List[SpatialBounds]] = {}
        for c in self.egi.Cut:
            parent = self._determine_cut_parent_area(c.id)
            if not parent:
                continue
            b = self.correspondence.area_mappings.get(c.id)
            if b:
                area_children.setdefault(parent, []).append(b)

        # Vertex superscripts near the vertex dot, avoid edge labels in same area
        for vid, v_elem in list(layout.items()):
            if v_elem.element_type != 'vertex' or not v_elem.spatial_bounds:
                continue
            area_id = v_elem.logical_area
            cx, cy = v_elem.spatial_bounds.center()
            # Base offset direction: top-right by default
            off = vts.get("offset", [-18, -16])
            try:
                base_dx, base_dy = float(off[0]), float(off[1])
            except Exception:
                base_dx, base_dy = -12.0, -10.0
            # Estimate a small one or two character superscript box
            est_w = max(10.0, v_est_w * 2.0)
            est_h = max(8.0, v_est_h)
            bounds = SpatialBounds(cx + base_dx, cy + base_dy, est_w, est_h)
            # Gather obstacles: vertex spot, predicate labels in same area, and other vertex supers if placed
            obstacles: List[SpatialBounds] = [v_elem.spatial_bounds]
            for oid, oelem in layout.items():
                if oid == vid:
                    continue
                if getattr(oelem, 'element_type', '') == 'edge' and self._determine_element_area(oid) == area_id:
                    obstacles.append(oelem.spatial_bounds)
                if getattr(oelem, 'element_type', '') == 'vertex' and self._determine_element_area(oid) == area_id and getattr(oelem, 'vertex_sup_bounds', None):
                    obstacles.append(oelem.vertex_sup_bounds)  # type: ignore[arg-type]
            # Push diagonally outward until no overlap
            guard = 0
            while any(rects_overlap(bounds, ob, sep_margin) for ob in obstacles):
                # Move further away from the vertex center along the offset direction
                bx, by = bounds.center()
                dx, dy = (bx - cx, by - cy)
                d = math.hypot(dx, dy)
                if d < 1e-6:
                    dx, dy, d = 1.0, -1.0, math.sqrt(2.0)
                ux, uy = dx / d, dy / d
                nbx, nby = bx + ux * step * 0.6, by + uy * step * 0.6
                bounds = SpatialBounds(nbx - est_w / 2.0, nby - est_h / 2.0, est_w, est_h)
                # Keep inside area and outside child holes if applicable
                bounds = self._clamp_bounds_into_area(bounds, area_id)
                bounds = self._avoid_child_cut_holes(bounds, area_id, layout)
                guard += 1
                if guard > 40:
                    break
            v_elem.vertex_sup_bounds = bounds

        # Edge arity superscripts: near top-right of edge label box, avoid other labels
        for eid, e_elem in list(layout.items()):
            if e_elem.element_type != 'edge' or not e_elem.spatial_bounds:
                continue
            area_id = e_elem.logical_area
            ex, ey, ew, eh = (e_elem.spatial_bounds.x, e_elem.spatial_bounds.y,
                               e_elem.spatial_bounds.width, e_elem.spatial_bounds.height)
            # Target initial pos: a little above-right corner
            init_x = ex + ew + 2.0
            init_y = ey - e_est_h - 2.0
            est_w = max(8.0, e_est_w * 2.0)
            est_h = max(6.0, e_est_h)
            bounds = SpatialBounds(init_x, init_y, est_w, est_h)
            # Obstacles: this edge label, other edge labels in same area, vertex spots, existing edge supers
            obstacles: List[SpatialBounds] = [e_elem.spatial_bounds]
            for oid, oelem in layout.items():
                if oid == eid:
                    continue
                if getattr(oelem, 'element_type', '') == 'edge' and self._determine_element_area(oid) == area_id:
                    obstacles.append(oelem.spatial_bounds)
                    if getattr(oelem, 'edge_sup_bounds', None):
                        obstacles.append(oelem.edge_sup_bounds)  # type: ignore[arg-type]
                if getattr(oelem, 'element_type', '') == 'vertex' and self._determine_element_area(oid) == area_id:
                    obstacles.append(oelem.spatial_bounds)
                    if getattr(oelem, 'vertex_sup_bounds', None):
                        obstacles.append(oelem.vertex_sup_bounds)  # type: ignore[arg-type]
            # Push outward from the edge label center towards the corner direction
            guard = 0
            rcx, rcy = e_elem.spatial_bounds.center()
            while any(rects_overlap(bounds, ob, sep_margin) for ob in obstacles):
                bx, by = bounds.center()
                dx, dy = (bx - rcx, by - rcy)
                d = math.hypot(dx, dy)
                if d < 1e-6:
                    dx, dy, d = 1.0, -1.0, math.sqrt(2.0)
                ux, uy = dx / d, dy / d
                nbx, nby = bx + ux * step * 0.6, by + uy * step * 0.6
                bounds = SpatialBounds(nbx - est_w / 2.0, nby - est_h / 2.0, est_w, est_h)
                bounds = self._clamp_bounds_into_area(bounds, area_id)
                bounds = self._avoid_child_cut_holes(bounds, area_id, layout)
                guard += 1
                if guard > 40:
                    break
            e_elem.edge_sup_bounds = bounds

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

        # Post-process: ensure the bounds do NOT overlap any child cut rectangle.
        def rects_overlap(ax: float, ay: float, aw: float, ah: float, b: SpatialBounds) -> bool:
            return not (ax + aw <= b.x or b.x + b.width <= ax or ay + ah <= b.y or b.y + b.height <= ay)

        guard = 0
        eps = 0.5  # minimal separation from child borders
        while any(rects_overlap(nx, ny, w, h, cb) for cb in child_bounds) and guard < 12:
            for cb in child_bounds:
                if not rects_overlap(nx, ny, w, h, cb):
                    continue
                # Compute overlap extents on each side
                right_overlap = (nx + w) - cb.x  # >0 if our right intrudes into child's left
                left_overlap = (cb.x + cb.width) - nx  # >0 if our left intrudes into child's right
                top_overlap = (cb.y + cb.height) - ny  # >0 if our top intrudes into child's bottom
                bottom_overlap = (ny + h) - cb.y  # >0 if our bottom intrudes into child's top

                # Determine minimal adjustment axis to resolve overlap
                # We consider four potential nudges/shrinks; pick the smallest movement that resolves.
                candidates: List[Tuple[float, str]] = []
                if right_overlap > 0 and nx < cb.x:
                    candidates.append((right_overlap + eps, 'shrink_right'))
                if left_overlap > 0 and nx >= cb.x:
                    candidates.append((left_overlap + eps, 'shift_right'))
                if bottom_overlap > 0 and ny < cb.y:
                    candidates.append((bottom_overlap + eps, 'shrink_bottom'))
                if top_overlap > 0 and ny >= cb.y:
                    candidates.append((top_overlap + eps, 'shift_down'))
                if not candidates:
                    # Fallback: shrink slightly
                    w = max(1.0, w - eps)
                    h = max(1.0, h - eps)
                else:
                    candidates.sort(key=lambda t: t[0])
                    _, action = candidates[0]
                    if action == 'shrink_right':
                        # Reduce width so right edge sits just to the left of child
                        new_w = max(1.0, cb.x - nx - eps)
                        w = min(w, new_w)
                    elif action == 'shift_right':
                        # Move bounds to the right of child
                        nx = cb.x + cb.width + eps
                    elif action == 'shrink_bottom':
                        new_h = max(1.0, cb.y - ny - eps)
                        h = min(h, new_h)
                    elif action == 'shift_down':
                        ny = cb.y + cb.height + eps
                # Re-clamp into area after adjustment
                nx = min(max(nx, area_b.x), area_b.x + max(0.0, area_b.width - w))
                ny = min(max(ny, area_b.y), area_b.y + max(0.0, area_b.height - h))
            guard += 1

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
        
        # Create ligatures for vertices connected to at least one edge
        ligature_counter = 1
        for vertex_id, connected_edges in vertex_to_edges.items():
            if len(connected_edges) >= 1:  # Vertex participates in at least one relation
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
                    # Insert explicit boundary waypoint at the cut border to preserve the crossing
                    hit = self._segment_rect_intersection_point(
                        (base_x, base_y), pred, (dest_bounds.x, dest_bounds.y, dest_bounds.width, dest_bounds.height)
                    )
                    if hit is not None:
                        segment_path = [(base_x, base_y), hit, pred]
                    else:
                        segment_path = [(base_x, base_y), pred]
                else:
                    # No bounds yet; fallback to straight segment
                    segment_path = [(base_x, base_y), pred]
            else:
                # For same-area, ensure target is outside child cuts too
                if eff_obstacles:
                    pred = self._pick_safe_point_in_area(vertex_area, layout, pred)
                # Route from center to predicate target using effective obstacles
                segment_path = self._visibility_route((base_x, base_y), pred, eff_obstacles)
            path_points.extend(segment_path)
        
        # Debug logging removed for quiet output by default. Use ARISBE_DEBUG_ROUTING to re-enable locally.
        # Ensure we have at least a basic path
        if not path_points:
            path_points = [(base_x, base_y), (base_x + 50, base_y)]
        # Debug logging removed for quiet output by default. Use ARISBE_DEBUG_ROUTING to re-enable locally.
        
        return path_points

    # --- Routing helpers to avoid cut rectangles ---
    def _visibility_route(self, start: Tuple[float, float], end: Tuple[float, float],
                          obstacles: List[Tuple[float, float, float, float]]) -> List[Tuple[float, float]]:
        """Route a polyline from start to end avoiding rectangular obstacles.
        Prefer pyvisgraph if available; otherwise use built-in light visibility routing.
        """
        # First, try pyvisgraph-backed router if available
        try:
            if self._pv_router is not None:
                routed = self._pv_router.route(start, end, obstacles)
                if routed:
                    return routed
        except Exception:
            pass
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

    def _segment_rect_intersection_point(self, p1: Tuple[float, float], p2: Tuple[float, float],
                                         rect: Tuple[float, float, float, float]) -> Tuple[float, float] | None:
        """Return a single intersection point of segment p1-p2 with rectangle rect if any.
        Chooses the first edge that intersects.
        """
        x, y, w, h = rect
        rx1, ry1, rx2, ry2 = x, y, x + w, y + h
        edges = [((rx1, ry1), (rx2, ry1)), ((rx2, ry1), (rx2, ry2)), ((rx2, ry2), (rx1, ry2)), ((rx1, ry2), (rx1, ry1))]
        for a, b in edges:
            pt = self._segment_intersection_point(p1, p2, a, b)
            if pt is not None:
                return pt
        return None

    def _segment_intersection_point(self, p1: Tuple[float, float], p2: Tuple[float, float],
                                    q1: Tuple[float, float], q2: Tuple[float, float]) -> Tuple[float, float] | None:
        """Compute intersection point of segments p1-p2 and q1-q2 if they intersect; else None."""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = q1
        x4, y4 = q2
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if denom == 0:
            return None
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / denom
        if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
            ix = x1 + t * (x2 - x1)
            iy = y1 + t * (y2 - y1)
            return (ix, iy)
        return None
    
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
    
    def _assert_path_within_area(self, path: List[Tuple[float, float]], area_id: str, *, allowed_child: Optional[str] = None, allow_last_inside_child: bool = False) -> None:
        """Fail-closed validator: assert that every point of the polyline lies within
        the logical area bounds (if any) and outside the interiors of all child cuts of that area.

        Points on borders are allowed within a small epsilon.
        Raises AssertionError on violation.
        """
        if not path:
            raise AssertionError("Empty path is invalid for area validation")
        eps = 1e-6
        eps_area = 0.5  # allow tiny overshoot when checking area bounds
        # Area bounds (may be None for sheet)
        area_bounds = self.correspondence.area_mappings.get(area_id)
        # Collect child cut rects (direct children only) and track mapping from id -> rect
        child_rects: List[Tuple[str, SpatialBounds]] = []
        for c in self.egi.Cut:
            if self._determine_cut_parent_area(c.id) == area_id:
                b = self.correspondence.area_mappings.get(c.id)
                if b:
                    child_rects.append((c.id, b))
        def point_in_rect_strict(px: float, py: float, r: SpatialBounds) -> bool:
            return (r.x + eps < px < r.x + r.width - eps) and (r.y + eps < py < r.y + r.height - eps)
        def point_in_rect_with_border(px: float, py: float, r: SpatialBounds) -> bool:
            return (r.x - eps_area <= px <= r.x + r.width + eps_area) and (r.y - eps_area <= py <= r.y + r.height + eps_area)
        # Check each waypoint
        for idx, (px, py) in enumerate(path):
            # Must be inside area bounds if area is bounded
            if area_bounds is not None and not point_in_rect_with_border(px, py, area_bounds):
                # If we have an allowed child, and the point is inside that child (with border), accept
                if allow_last_inside_child and allowed_child is not None:
                    for cid, r in child_rects:
                        if cid == allowed_child and point_in_rect_with_border(px, py, r):
                            break
                    else:
                        raise AssertionError("Path leaves its logical area bounds")
                else:
                    raise AssertionError("Path leaves its logical area bounds")
            # Must not be strictly inside any child cut
            for cid, r in child_rects:
                inside = point_in_rect_strict(px, py, r)
                if not inside:
                    continue
                # Allow entering a specific child cut if configured
                if allow_last_inside_child and allowed_child is not None and cid == allowed_child:
                    continue
                raise AssertionError("Path enters child cut interior")
    
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
