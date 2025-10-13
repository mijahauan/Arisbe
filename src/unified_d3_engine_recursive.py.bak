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
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

from egi_core_dau import RelationalGraphWithCuts, ElementID


# ============================================================================
# LAYOUT DTO - Single canonical format
# ============================================================================

@dataclass
class Point:
    """2D point."""
    x: float
    y: float


@dataclass
class BoundingBox:
    """Axis-aligned bounding box."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    
    @property
    def width(self) -> float:
        return self.max_x - self.min_x
    
    @property
    def height(self) -> float:
        return self.max_y - self.min_y
    
    @property
    def center(self) -> Point:
        return Point(
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2
        )


@dataclass
class LigaturePath:
    """Path for a ligature connection."""
    predicate_id: ElementID
    vertex_id: ElementID
    points: Tuple[Point, ...]


@dataclass
class LayoutDTO:
    """Platform-independent layout result."""
    vertex_positions: Dict[ElementID, Point]
    predicate_positions: Dict[ElementID, Point]
    cut_bounds: Dict[ElementID, BoundingBox]
    ligature_paths: List[LigaturePath]
    area_hierarchy: Dict[ElementID, Set[ElementID]]
    viewport_bounds: BoundingBox
    sheet_id: ElementID
    style: any = None


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
    5. Assemble final LayoutDTO
    """
    
    def __init__(self):
        self.element_sizes: Dict[ElementID, Tuple[float, float]] = {}
        self.element_positions: Dict[ElementID, Point] = {}
        self.cut_bboxes: Dict[ElementID, BoundingBox] = {}
    
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
        
        print("\n" + "="*70)
        print("DEFINITIVE RECURSIVE D3 LAYOUT ENGINE")
        print("="*70)
        print(f"Input: {len(egi.V)}V, {len(egi.E)}E, {len(egi.Cut)}C")
        
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
        """Calculate sizes for all non-cut elements."""
        for v in egi.V:
            radius = style.vertex_radius
            self.element_sizes[v.id] = (radius * 2, radius * 2)
        
        for e in egi.E:
            label = egi.get_relation_name(e.id)
            width = max(50, len(label) * 8 + 20)
            height = max(30, 16 + 10)
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
                if hasattr(delta, 'position') and delta.position:
                    node['fx'] = delta.position[0]
                    node['fy'] = delta.position[1]
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
                if hasattr(delta, 'position') and delta.position:
                    node['fx'] = delta.position[0]
                    node['fy'] = delta.position[1]
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
        """Call D3 worker subprocess."""
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
    
    def _build_dto(
        self,
        egi: RelationalGraphWithCuts,
        style
    ) -> LayoutDTO:
        """Build final LayoutDTO from recursively calculated positions."""
        
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
        
        # Build ligature paths
        ligature_paths = []
        for e in egi.E:
            if e.id not in predicate_positions:
                continue
            ex, ey = predicate_positions[e.id].x, predicate_positions[e.id].y
            
            for v_id in egi.get_incident_vertices(e.id):
                if v_id in vertex_positions:
                    vx, vy = vertex_positions[v_id].x, vertex_positions[v_id].y
                    ligature_paths.append(LigaturePath(
                        predicate_id=e.id,
                        vertex_id=v_id,
                        points=(Point(ex, ey), Point(vx, vy))
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
