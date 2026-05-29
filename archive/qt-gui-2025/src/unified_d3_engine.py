"""
Unified D3 Layout Engine - DEFINITIVE RECURSIVE ARCHITECTURE

PURE BOTTOM-UP RECURSION:
- Python orchestrates recursive traversal of cut hierarchy
- Each D3 call solves ONE cut's layout (simple, self-contained)
- Child cuts become fixed-size obstacles in parent simulations
- No post-processing, no multi-phase conflicts, pure separation

Author: Definitive architecture implementation
Date: 2025-10-12
"""

import json
import subprocess
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_dto import Point, BoundingBox, LigaturePath, LayoutDTO  # noqa: F401 (re-exported)


# ============================================================================
# UNIFIED D3 ENGINE - RECURSIVE ORCHESTRATOR
# ============================================================================

class UnifiedD3Engine:
    """
    Definitive Recursive Bottom-Up Layout Engine.
    
    ARCHITECTURE:
    1. Build cut hierarchy from EGI.area
    2. Find leaf cuts (no child cuts)
    3. Layout leaves first (call D3 with simple content only)
    4. Work up hierarchy: layout each parent with child cuts as obstacles
    """
    
    def __init__(self):
        """Initialize layout engine."""
        # Caches for bottom-up recursive layout
        self.element_sizes: Dict[ElementID, Tuple[float, float]] = {}
        self.element_positions: Dict[ElementID, Point] = {}
        self.cut_bboxes: Dict[ElementID, BoundingBox] = {}
        # User constraints (pinned positions)
        self.layout_deltas: Optional[Dict] = None
    
    def generate_layout(
        self,
        egi: RelationalGraphWithCuts,
        style,
        layout_deltas: Optional[Dict] = None
    ) -> LayoutDTO:
        """
        Generate layout using recursive bottom-up approach.
        
        Args:
            egi: The EGI model to layout
            style: Style specification
            layout_deltas: User-defined position overrides
        
        Returns:
            Complete LayoutDTO ready for rendering
        """
        # CRITICAL: Clear all cached state from previous layouts
        self.element_sizes.clear()
        self.element_positions.clear()
        self.cut_bboxes.clear()
        
        # Store layout deltas for this layout pass
        self.layout_deltas = layout_deltas or {}
        
        print("\n" + "="*70)
        print("DEFINITIVE RECURSIVE D3 LAYOUT ENGINE")
        print("="*70)
        print(f"Input: {len(egi.V)}V, {len(egi.E)}E, {len(egi.Cut)}C")
        if self.layout_deltas:
            print(f"User constraints: {len(self.layout_deltas)} pinned positions")
        
        # Step 1: Calculate element sizes
        print("\nStep 1: Calculating element sizes...")
        self._calculate_sizes(egi, style)
        
        # Step 2: Build cut hierarchy
        print("\nStep 2: Building cut hierarchy...")
        hierarchy = self._build_cut_hierarchy(egi)
        self._print_hierarchy(hierarchy, egi)
        
        # Step 3: Recursive bottom-up layout
        print("\nStep 3: Recursive bottom-up layout...")
        self._layout_recursively(egi.sheet, egi, style, hierarchy, layout_deltas or {})
        
        # Step 4: Build final DTO
        print("\nStep 4: Building LayoutDTO...")
        dto = self._build_dto(egi, style)
        
        print(f"\n✅ Layout complete: {len(dto.vertex_positions)}V, "
              f"{len(dto.predicate_positions)}P, {len(dto.cut_bounds)}C")
        print("\nFinal cut bounds:")
        for cut_id, bbox in dto.cut_bounds.items():
            print(f"  {cut_id}: ({bbox.min_x:.1f}, {bbox.min_y:.1f}) -> "
                  f"({bbox.max_x:.1f}, {bbox.max_y:.1f}) [{bbox.width:.1f}x{bbox.height:.1f}]")
        print("="*70 + "\n")
        
        return dto
    
    def _calculate_sizes(self, egi: RelationalGraphWithCuts, style):
        """Calculate bounding-box sizes for all vertices and predicates (non-cut elements).

        Layout model — label-beside-vertex:
            Each vertex is rendered as a filled circle (Dau "heavy dot") with its
            label appearing to the *right* of the circle rather than below it.
            The bounding box therefore spans:

                width  = circle_diameter + gap (8 px) + text_width + right_margin (4 px)
                height = max(circle_diameter, text_height)

            Text width is estimated as ``len(label) * 6.2`` pixels, which is the
            average character advance for the default sans-serif font at the
            configured point size.  For unlabelled (anonymous) vertices the
            bounding box is exactly the circle diameter.

        For predicates (edges), the bounding box is sized tightly around the
        relation name text using ``style.predicate_char_width`` and
        ``style.predicate_height``, with 3 px horizontal and 2 px vertical
        padding on each side.

        Sizes are stored in ``self.element_sizes`` keyed by element ID and are
        consumed by ``_layout_single_cut`` when building the D3 payload.

        Args:
            egi: The EGI whose vertices and edges need sizing.
            style: Style specification supplying ``vertex_radius``,
                ``predicate_char_width``, and ``predicate_height``.
        """
        for v in egi.V:
            radius = style.vertex_radius
            circle_size = radius * 2

            # Account for vertex label text BESIDE the spot (not below)
            label = v.label or ""
            if label:
                # Estimate text dimensions (6.2px per char per style)
                text_width = len(label) * 6.2
                text_height = 14
                # Label appears BESIDE vertex (to the right)
                # Width = circle + gap + text
                width = circle_size + 8 + text_width + 4  # 8px gap, 4px right margin
                # Height = max of circle and text
                height = max(circle_size, text_height)
            else:
                width = circle_size
                height = circle_size

            self.element_sizes[v.id] = (width, height)

        for e in egi.E:
            label = egi.get_relation_name(e.id)
            # Tight boundary around text (Dau style - minimal padding)
            char_width = style.predicate_char_width
            text_height = style.predicate_height
            width = len(label) * char_width + 6  # 3px padding each side
            height = text_height + 4  # 2px padding top/bottom
            self.element_sizes[e.id] = (width, height)
    
    def _build_cut_hierarchy(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, List[ElementID]]:
        """
        Build cut hierarchy: which cuts are children of which cuts.
        
        Returns:
            Dict mapping cut_id -> list of child cut IDs
        """
        hierarchy = {}
        
        # Handle sheet (egi.sheet is already a string ID, not an object)
        children = egi.area.get(egi.sheet, frozenset())
        child_cuts = [c.id for c in egi.Cut if c.id in children]
        hierarchy[egi.sheet] = child_cuts
        
        # Handle regular cuts
        for cut in egi.Cut:
            children = egi.area.get(cut.id, frozenset())
            child_cuts = [c.id for c in egi.Cut if c.id in children]
            hierarchy[cut.id] = child_cuts
        
        return hierarchy
    
    def _print_hierarchy(self, hierarchy: Dict, egi: RelationalGraphWithCuts):
        """Print cut hierarchy for debugging."""
        print("  Cut hierarchy:")
        for cut_id, child_cuts in hierarchy.items():
            # Get content for this area
            area_contents = egi.area.get(cut_id, frozenset())
            vertices = [v.id for v in egi.V if v.id in area_contents]
            predicates = [egi.get_relation_name(e.id) for e in egi.E if e.id in area_contents]
            
            if cut_id == egi.sheet:
                print(f"    SHEET:")
                print(f"      Content: {len(vertices)}V {predicates}")
                print(f"      Child cuts: {child_cuts}")
            else:
                print(f"    {cut_id}:")
                print(f"      Content: {len(vertices)}V {predicates}")
                print(f"      Child cuts: {child_cuts}")
    
    def _layout_recursively(
        self,
        cut_id: ElementID,
        egi: RelationalGraphWithCuts,
        style,
        hierarchy: Dict[ElementID, List[ElementID]],
        layout_deltas: Dict
    ):
        """
        Recursively layout a cut and all its children (bottom-up).
        
        Base case: Leaf cut (no child cuts) - layout simple content
        Recursive case: Layout children first, then layout this cut with children as obstacles
        """
        child_cut_ids = hierarchy.get(cut_id, [])
        
        print(f"\n  Layouting {cut_id}...")
        print(f"    Child cuts: {child_cut_ids}")
        
        # RECURSIVE STEP: Layout all child cuts first
        for child_id in child_cut_ids:
            self._layout_recursively(child_id, egi, style, hierarchy, layout_deltas)
        
        # BASE CASE: Now layout this cut's own content
        # Get simple content (vertices and predicates, NOT child cuts)
        area_contents = egi.area.get(cut_id, frozenset())
        vertices = [v for v in egi.V if v.id in area_contents]
        predicates = [e for e in egi.E if e.id in area_contents]
        
        print(f"    Simple content: {len(vertices)}V, {len(predicates)}P")
        print(f"    Child cut obstacles: {len(child_cut_ids)}")
        
        # Call D3 worker for this single cut
        positions, bbox = self._layout_single_cut(
            cut_id,
            vertices,
            predicates,
            child_cut_ids,
            egi,
            style,
            layout_deltas
        )
        
        # Store results for content elements
        for elem_id, (x, y) in positions.items():
            # Check if this is a child cut (obstacle) - update its bbox AND translate its content
            if elem_id in child_cut_ids:
                old_bbox = self.cut_bboxes[elem_id]
                old_center_x = (old_bbox.min_x + old_bbox.max_x) / 2
                old_center_y = (old_bbox.min_y + old_bbox.max_y) / 2
                
                # Calculate translation offset
                offset_x = x - old_center_x
                offset_y = y - old_center_y
                
                # Update bbox position to where D3 placed it
                half_w = old_bbox.width / 2
                half_h = old_bbox.height / 2
                self.cut_bboxes[elem_id] = BoundingBox(
                    min_x=x - half_w,
                    min_y=y - half_h,
                    max_x=x + half_w,
                    max_y=y + half_h
                )
                
                # CRITICAL: Recursively translate all descendants
                self._translate_cut_and_descendants(elem_id, offset_x, offset_y, egi)
                
                print(f"      Repositioned child cut {elem_id}: ({x:.1f}, {y:.1f}), "
                      f"offset: ({offset_x:.1f}, {offset_y:.1f})")
            else:
                # Regular content element
                self.element_positions[elem_id] = Point(x, y)
        
        self.cut_bboxes[cut_id] = bbox
        
        print(f"    ✓ {cut_id} bbox: {bbox.width:.1f}x{bbox.height:.1f}")
    
    def _translate_cut_and_descendants(
        self,
        cut_id: ElementID,
        offset_x: float,
        offset_y: float,
        egi: RelationalGraphWithCuts
    ):
        """
        Recursively translate a cut and all its descendants by (offset_x, offset_y).
        
        This is needed when a child cut is repositioned in parent layout - we must
        move the cut's content AND all its child cuts (and their content, recursively).
        """
        # Translate all content elements in this cut
        contents = egi.area.get(cut_id, frozenset())
        for content_id in contents:
            # Translate content elements (vertices, predicates)
            if content_id in self.element_positions:
                old_pos = self.element_positions[content_id]
                self.element_positions[content_id] = Point(
                    old_pos.x + offset_x,
                    old_pos.y + offset_y
                )
            
            # Recursively translate child cuts
            if content_id in self.cut_bboxes:
                # This is a child cut - translate its bbox
                old_bbox = self.cut_bboxes[content_id]
                self.cut_bboxes[content_id] = BoundingBox(
                    min_x=old_bbox.min_x + offset_x,
                    min_y=old_bbox.min_y + offset_y,
                    max_x=old_bbox.max_x + offset_x,
                    max_y=old_bbox.max_y + offset_y
                )
                
                # Recursively translate the child cut's descendants
                self._translate_cut_and_descendants(content_id, offset_x, offset_y, egi)
    
    def _layout_single_cut(
        self,
        cut_id: ElementID,
        vertices: List,
        predicates: List,
        child_cut_ids: List[ElementID],
        egi: RelationalGraphWithCuts,
        style,
        layout_deltas: Dict
    ) -> Tuple[Dict[str, Tuple[float, float]], BoundingBox]:
        """
        Call D3 worker to layout ONE cut's contents.
        
        Returns:
            (positions dict, tight bounding box)
        """
        # Build payload for D3
        content_nodes = []
        
        # Add vertices
        for v in vertices:
            width, height = self.element_sizes[v.id]
            node = {
                'id': v.id,
                'type': 'vertex',
                'label': v.label or "",
                'width': width,
                'height': height
            }
            if v.id in layout_deltas:
                delta = layout_deltas[v.id]
                if hasattr(delta, 'new_position') and delta.new_position:
                    node['fx'] = delta.new_position[0]
                    node['fy'] = delta.new_position[1]
            content_nodes.append(node)
        
        # Add predicates
        for e in predicates:
            width, height = self.element_sizes[e.id]
            node = {
                'id': e.id,
                'type': 'edge_label',
                'label': egi.get_relation_name(e.id),
                'width': width,
                'height': height
            }
            if e.id in layout_deltas:
                delta = layout_deltas[e.id]
                if hasattr(delta, 'new_position') and delta.new_position:
                    node['fx'] = delta.new_position[0]
                    node['fy'] = delta.new_position[1]
            content_nodes.append(node)
        
        # Add child cuts as fixed-size obstacles
        # NOTE: Child cuts are already laid out, but in their own local space
        # We need to let them float initially, then update their bbox after parent layout
        obstacles = []
        for child_id in child_cut_ids:
            if child_id in self.cut_bboxes:
                bbox = self.cut_bboxes[child_id]
                # Start at center of parent bounds - will be positioned by simulation
                obstacles.append({
                    'id': child_id,
                    'type': 'cut_obstacle',
                    'width': bbox.width,
                    'height': bbox.height
                    # Don't set x, y - let D3 position them
                })
        
        # Build links (ν-connections)
        links = []
        for e in predicates:
            for v_id in egi.get_incident_vertices(e.id):
                if v_id in [v.id for v in vertices]:
                    links.append({
                        'source': e.id,
                        'target': v_id
                    })
        
        payload = {
            'content': content_nodes,
            'obstacles': obstacles,
            'links': links,
            'bounds': {'width': 600, 'height': 450},
            'seed': 42
        }
        
        # Call D3 worker
        result = self._call_d3_worker(payload)
        
        return result['positions'], result['bbox']
    
    def _call_d3_worker(self, payload: dict) -> dict:
        """Invoke the D3 force-simulation worker via a Node.js subprocess.

        Subprocess protocol:
            - The payload dict is JSON-serialised and written to the worker's
              stdin (``input=json.dumps(payload)``).
            - ``unified_d3_worker.js`` reads from stdin, runs a D3 force
              simulation, and writes a single JSON object to stdout with two
              top-level keys:

                  ``positions``: dict mapping element-id strings to
                      ``{"x": float, "y": float}`` objects for every node
                      (content nodes AND cut obstacles).

                  ``bbox``: object with keys ``min_x``, ``min_y``, ``max_x``,
                      ``max_y`` (any may be ``null`` if the cut is empty).

            - Stderr is captured; any Node.js runtime errors are printed and
              re-raised via ``subprocess.CalledProcessError``.
            - A 10-second timeout is enforced to prevent hangs if Node is not
              installed or the simulation diverges.

        Empty-cut handling: when the worker returns ``null`` bbox values
        (no content), a 100×100 px default bounding box is used so the cut
        circle remains visible in the rendered diagram.

        Args:
            payload: Dict with keys ``content`` (list of node dicts),
                ``obstacles`` (list of child-cut obstacle dicts), ``links``
                (list of source/target dicts), ``bounds``, and ``seed``.

        Returns:
            Dict with keys ``positions`` (mapping element-id -> (x, y) tuple)
            and ``bbox`` (BoundingBox instance).

        Raises:
            FileNotFoundError: if ``unified_d3_worker.js`` is not found.
            subprocess.CalledProcessError: if Node exits with non-zero status.
            subprocess.TimeoutExpired: if the worker does not complete within
                10 seconds.
            json.JSONDecodeError: if the worker output is not valid JSON.
        """
        worker_path = Path(__file__).parent / 'unified_d3_worker.js'

        if not worker_path.exists():
            raise FileNotFoundError(f"D3 worker not found: {worker_path}")
        
        try:
            result = subprocess.run(
                ['node', str(worker_path)],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
        except subprocess.CalledProcessError as e:
            print(f"ERROR: D3 worker failed: {e}")
            print(f"STDERR: {e.stderr}")
            raise
        except subprocess.TimeoutExpired:
            print("ERROR: D3 worker timed out")
            raise
        
        # Parse output
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse D3 output: {e}")
            print(f"Output: {result.stdout[:500]}")
            raise
        
        # Convert bbox
        bbox_data = output['bbox']
        
        # Handle empty cuts - D3 returns None values if no content
        # Give empty cuts a minimum size for visibility
        if bbox_data['min_x'] is None or bbox_data['max_x'] is None:
            # Empty cut - use default minimum size
            min_size = 100.0
            bbox = BoundingBox(
                min_x=-min_size / 2,
                min_y=-min_size / 2,
                max_x=min_size / 2,
                max_y=min_size / 2
            )
        else:
            bbox = BoundingBox(
                min_x=bbox_data['min_x'],
                min_y=bbox_data['min_y'],
                max_x=bbox_data['max_x'],
                max_y=bbox_data['max_y']
            )
        
        # Convert positions
        positions = {
            elem_id: (pos['x'], pos['y'])
            for elem_id, pos in output['positions'].items()
        }
        
        return {'positions': positions, 'bbox': bbox}
    
    def _circle_boundary_point(self, cx: float, cy: float, radius: float,
                              target_x: float, target_y: float) -> Tuple[float, float]:
        """Return the point on a circle's boundary that lies on the ray toward a target.

        Used to compute the attachment point of a ligature line at a vertex
        circle, so the line appears to terminate at the edge of the spot rather
        than at its centre.

        Args:
            cx: X coordinate of the circle's centre.
            cy: Y coordinate of the circle's centre.
            radius: Radius of the circle.
            target_x: X coordinate of the target point (e.g., predicate centre).
            target_y: Y coordinate of the target point.

        Returns:
            (x, y) of the boundary point on the circle closest to *target*.
            Falls back to ``(cx + radius, cy)`` when centre == target.
        """
        dx = target_x - cx
        dy = target_y - cy
        distance = math.sqrt(dx * dx + dy * dy)
        if distance == 0:
            return cx + radius, cy
        # Unit vector toward target
        ux = dx / distance
        uy = dy / distance
        # Point on boundary
        return cx + ux * radius, cy + uy * radius
    
    def _rect_boundary_point(self, rect_cx: float, rect_cy: float,
                            rect_w: float, rect_h: float,
                            target_x: float, target_y: float) -> Tuple[float, float]:
        """Return the point on a rectangle's boundary that lies on the ray from its centre toward a target.

        Used to compute the hook attachment point for a ligature line at a
        predicate label rectangle, so the line visually connects to the edge
        of the box rather than its centre.

        The algorithm shoots a parametric ray from the rectangle centre and
        checks intersection with each of the four axis-aligned edges, keeping
        the intersection with the smallest positive parameter ``t``.

        Args:
            rect_cx: X coordinate of the rectangle's centre.
            rect_cy: Y coordinate of the rectangle's centre.
            rect_w: Full width of the rectangle.
            rect_h: Full height of the rectangle.
            target_x: X coordinate of the target point (e.g., vertex centre).
            target_y: Y coordinate of the target point.

        Returns:
            (x, y) of the boundary intersection point closest to *target*.
            Returns ``(rect_cx, rect_cy)`` when centre == target.
        """
        dx = target_x - rect_cx
        dy = target_y - rect_cy
        
        if dx == 0 and dy == 0:
            return rect_cx, rect_cy
        
        # Find intersection with rectangle edges
        half_w = rect_w / 2
        half_h = rect_h / 2
        
        # Determine which edge the ray intersects
        # Use parametric ray: P = center + t * direction
        # Check intersection with all 4 edges, pick closest
        
        t_min = float('inf')
        result = (rect_cx, rect_cy)
        
        # Right edge (x = cx + half_w)
        if dx > 0:
            t = half_w / dx
            y = rect_cy + t * dy
            if abs(y - rect_cy) <= half_h and t < t_min:
                t_min = t
                result = (rect_cx + half_w, y)
        
        # Left edge (x = cx - half_w)
        if dx < 0:
            t = -half_w / dx
            y = rect_cy + t * dy
            if abs(y - rect_cy) <= half_h and t < t_min:
                t_min = t
                result = (rect_cx - half_w, y)
        
        # Top edge (y = cy - half_h)
        if dy < 0:
            t = -half_h / dy
            x = rect_cx + t * dx
            if abs(x - rect_cx) <= half_w and t < t_min:
                t_min = t
                result = (x, rect_cy - half_h)
        
        # Bottom edge (y = cy + half_h)
        if dy > 0:
            t = half_h / dy
            x = rect_cx + t * dx
            if abs(x - rect_cx) <= half_w and t < t_min:
                t_min = t
                result = (x, rect_cy + half_h)
        
        return result
    
    def _build_dto(
        self,
        egi: RelationalGraphWithCuts,
        style
    ) -> LayoutDTO:
        """Assemble the final LayoutDTO from positions and bboxes computed by the recursive layout.

        After ``_layout_recursively`` has populated ``self.element_positions``
        (vertex and predicate centres) and ``self.cut_bboxes`` (cut bounding
        boxes), this method:

        1. Separates element positions into ``vertex_positions`` and
           ``predicate_positions`` by matching against the EGI's V and E sets.
        2. Builds ``ligature_paths``: for each predicate–vertex incidence pair
           (ν-relation), a two-point path is created from the predicate's
           rectangle boundary (hook attachment) to the vertex centre.  The
           vertex end is the *centre* so that the rendered spot circle sits on
           top of the line, giving visual continuity.
        3. Computes a viewport ``BoundingBox`` that encloses all positions and
           cut bboxes with a 30 px margin.

        Args:
            egi: Source EGI (used for vertex/edge/cut membership and ν-relation).
            style: Style specification (attached to the returned DTO).

        Returns:
            A fully populated ``LayoutDTO`` ready for ``SimpleSVGRenderer``.
        """
        
        # Extract positions by type
        vertex_positions = {
            v.id: self.element_positions[v.id]
            for v in egi.V
            if v.id in self.element_positions
        }
        
        predicate_positions = {
            e.id: self.element_positions[e.id]
            for e in egi.E
            if e.id in self.element_positions
        }
        
        # Build ligature paths with proper connection points
        # Predicate end: boundary (creates hook)
        # Vertex end: CENTER (ligature extends through vertex spot)
        ligature_paths = []
        for e in egi.E:
            if e.id not in predicate_positions:
                continue
            e_pos = predicate_positions[e.id]
            e_size = self.element_sizes.get(e.id, (40, 20))
            
            for v_id in egi.get_incident_vertices(e.id):
                if v_id not in vertex_positions:
                    continue
                    
                v_pos = vertex_positions[v_id]
                
                # Predicate end: boundary point (for hook attachment)
                e_boundary = self._rect_boundary_point(
                    e_pos.x, e_pos.y, e_size[0], e_size[1],
                    v_pos.x, v_pos.y
                )
                
                # Vertex end: CENTER (ligature continues through vertex spot)
                # This creates visual continuity - spot renders on top of line
                
                ligature_paths.append(LigaturePath(
                    predicate_id=e.id,
                    vertex_id=v_id,
                    points=(Point(e_boundary[0], e_boundary[1]), 
                           Point(v_pos.x, v_pos.y))  # CENTER, not boundary!
                ))
        
        # Area hierarchy
        area_hierarchy = {
            area_id: set(contents)
            for area_id, contents in egi.area.items()
        }
        
        # Viewport from all positions
        all_x = [p.x for p in vertex_positions.values()] + \
                [p.x for p in predicate_positions.values()]
        all_y = [p.y for p in vertex_positions.values()] + \
                [p.y for p in predicate_positions.values()]
        
        for bbox in self.cut_bboxes.values():
            all_x.extend([bbox.min_x, bbox.max_x])
            all_y.extend([bbox.min_y, bbox.max_y])
        
        if all_x and all_y:
            viewport = BoundingBox(
                min(all_x) - 30, min(all_y) - 30,
                max(all_x) + 30, max(all_y) + 30
            )
        else:
            viewport = BoundingBox(0, 0, 800, 600)
        
        return LayoutDTO(
            vertex_positions=vertex_positions,
            predicate_positions=predicate_positions,
            cut_bounds=self.cut_bboxes,
            ligature_paths=ligature_paths,
            area_hierarchy=area_hierarchy,
            viewport_bounds=viewport,
            sheet_id=egi.sheet,
            style=style
        )
