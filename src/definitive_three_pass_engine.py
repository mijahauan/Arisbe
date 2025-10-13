#!/usr/bin/env python3
"""
Definitive Four-Pass EGI Layout Engine (COMPLETE)

ARCHITECTURAL STATUS (2025-01-10):
✅ Pass 0: Topological analysis
✅ Phase 1-4: Complete architectural refactoring
✅ Visual quality: All refinements complete

COMPLETE FOUR-PASS ARCHITECTURE:

Pass 0: Topological Analysis - Understand ligature structure
    - Analyzes complete ligature topology BEFORE layout
    - Identifies: crossing ligatures, branching ligatures, simple ligatures
    - Builds: area indexes, boundary crossing maps
    - Output: TopologyAnalysis used by all subsequent passes

Pass 1: Graphviz dot - Container sizing ONLY
    - Input: Cut hierarchy ONLY (clusters + dummy nodes + tension edges)
    - Uses: Topology analysis for tension edges (crossing ligatures)
    - Output: Container geometry (KEPT)
    - NO content nodes, NO port nodes - ONLY containers!

Post-Pass 1: Geometric port calculation
    - Calculates ports from fixed container boundaries
    - Uses: Topology analysis for port requirements
    - Line-rectangle intersection for boundary crossings
    - NOT extracted from Graphviz

Pass 2: d3-force - Recursive bottom-up content layout
    - NO Graphviz hints (starts from scratch)
    - Uses: Topology analysis for branch nodes (Y-junctions)
    - True bottom-up: innermost cuts first
    - Child cuts as large fixed obstacles
    - Returns bounding boxes for future dynamic sizing

Pass 3: Area-aware A* pathfinding - Intelligent ligature routing
    - Uses: Complete topology for routing decisions
    - Same-area paths: Avoid obstacles using A* search
    - Cross-area paths: Route through geometric ports
    - Branch handling: Optimal Y-junction positioning
    - Path smoothing: Ramer-Douglas-Peucker algorithm
    - Respects Dau's ligature rules (avoid vs. cross)
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

from egi_core_dau import RelationalGraphWithCuts
from constrained_force_layout import Rect
from style_loader import StyleLoader, StyleSpecification
from egif_generator_dau import EGIFGenerator
from area_aware_astar import AreaAwareAStarPathfinder
from ligature_topology import analyze_ligature_topology, TopologyAnalysis

# Import LayoutDeltas from old engine for user position overrides
try:
    from definitive_egi_layout_engine import LayoutDeltas, LayoutDelta
except ImportError:
    # Fallback definitions if old engine not available
    @dataclass
    class LayoutDelta:
        element_id: str
        delta_type: str
        original_position: Optional[Tuple[float, float]] = None
        new_position: Optional[Tuple[float, float]] = None
        custom_path: Optional[List[Tuple[float, float]]] = None
        nu_mapping_key: Optional[str] = None
    
    @dataclass
    class LayoutDeltas:
        deltas: Dict[str, LayoutDelta] = field(default_factory=dict)
        deterministic_seed: Optional[int] = None


# DTO Classes
@dataclass
class ConnectionPort:
    port_id: int
    position: Tuple[float, float]
    direction: str


@dataclass
class RenderableArea:
    id: str
    parent_id: Optional[str]
    rect: Rect
    is_sheet: bool = False
    style: Dict = field(default_factory=dict)  # For highlighting and visual effects


@dataclass
class RenderableVertex:
    id: str
    parent_area_id: str
    pos: Tuple[float, float]
    label: str = ""
    style: Dict = field(default_factory=dict)  # For highlighting and visual effects


@dataclass
class RenderableEdgeLabel:
    id: str
    parent_area_id: str
    rect: Rect
    label: str
    connection_ports: List[ConnectionPort] = field(default_factory=list)
    style: Dict = field(default_factory=dict)  # For highlighting and visual effects


@dataclass
class RenderableLigature:
    start_vertex_id: str
    end_edge_id: str
    end_hook_index: int
    path_points: List[Tuple[float, float]]
    style: Dict = field(default_factory=dict)  # For highlighting and visual effects


@dataclass
class LayoutDTO:
    areas: List[RenderableArea] = field(default_factory=list)
    vertices: List[RenderableVertex] = field(default_factory=list)
    edge_labels: List[RenderableEdgeLabel] = field(default_factory=list)
    ligatures: List[RenderableLigature] = field(default_factory=list)
    annotations: List[Any] = field(default_factory=list)  # For comments, labels, etc.


@dataclass
class PortNode:
    id: str
    cut_id: str
    position: Tuple[float, float]
    ligature_id: str


class DefinitiveThreePassEngine:
    """Clean three-pass implementation from scratch."""
    
    def __init__(self):
        self.area_bounds: Dict[str, Rect] = {}
        self.element_positions: Dict[str, Tuple[float, float]] = {}
        self.port_nodes: Dict[str, PortNode] = {}
        self.element_to_cut: Dict[str, str] = {}
        self.layout_deltas: Optional[LayoutDeltas] = None
        
    def generate_layout(self, 
                       egi: RelationalGraphWithCuts,
                       style: Optional[StyleSpecification] = None,
                       layout_deltas: Optional[LayoutDeltas] = None,
                       debug_prefix: Optional[str] = None) -> LayoutDTO:
        """Execute three-pass layout generation."""
        print("=" * 70)
        print("DEFINITIVE THREE-PASS LAYOUT ENGINE")
        print("=" * 70)
        print()
        
        # Clear state from any previous runs
        self.area_bounds.clear()
        self.element_positions.clear()
        self.port_nodes.clear()
        self.element_to_cut.clear()
        self.layout_deltas = layout_deltas
        
        # Load style if not provided
        if style is None:
            loader = StyleLoader()
            style = loader.load_default_style()
        
        self.style = style
        
        # Generate EGIF for reference
        self.egif = EGIFGenerator(egi).generate()
        print(f"EGIF: {self.egif}")
        print()
        
        # Build element mapping
        self._build_element_mapping(egi)
        
        # Pass 0: Topological Analysis
        print("Pass 0: Topological analysis...")
        self.topology = analyze_ligature_topology(egi, self.element_to_cut)
        print(f"  ✅ {len(self.topology.ligatures)} ligatures analyzed")
        print(f"     - {len(self.topology.crossing_ligatures)} crossing areas")
        print(f"     - {len(self.topology.branching_ligatures)} with branches")
        print(f"     - {len(self.topology.simple_ligatures)} simple")
        print()
        
        # Pass 1
        print("Pass 1: Container hierarchy (Graphviz)...")
        self._pass1_containers(egi)
        if debug_prefix:
            self._debug_pass1(debug_prefix, egi)
        
        # Post-Pass 1: Calculate ports geometrically
        print("\nPost-Pass 1: Calculating ports geometrically...")
        self._calculate_ports_geometrically(egi)
        print(f"  ✅ {len(self.port_nodes)} ports calculated from boundaries")
        
        # Pass 2
        print("\nPass 2: Content layout (d3-force)...")
        self._pass2_content(egi)
        if debug_prefix:
            self._debug_pass2(debug_prefix, egi)
        
        # Pass 3
        print("\nPass 3: Ligature routing (A*)...")
        dto = self._pass3_ligatures(egi, style)
        if debug_prefix:
            self._debug_pass3(debug_prefix, dto, egi)
        
        print(f"\n✅ Complete: {len(dto.vertices)}V, {len(dto.edge_labels)}E, {len(dto.ligatures)}L")
        return dto
    
    def _build_element_mapping(self, egi: RelationalGraphWithCuts):
        """Map each element to its containing cut."""
        for cut_id, elements in egi.area.items():
            for elem_id in elements:
                self.element_to_cut[elem_id] = cut_id
    
    # === PASS 1 ===
    
    def _pass1_containers(self, egi: RelationalGraphWithCuts):
        """
        Use Graphviz to SIZE containers only.
        
        PHASE 1+3 FIXES:
        - Input: Full hierarchy with nodes (for sizing estimation)
        - Output: Container geometry (KEPT), node positions (DISCARDED)
        - Ports: NO LONGER in dot input (calculated geometrically after)
        """
        dot_content = self._build_dot(egi)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(dot_content)
            dot_file = f.name
        
        try:
            result = subprocess.run(
                ['dot', '-Tjson', dot_file],
                capture_output=True, text=True, check=True
            )
            layout_json = json.loads(result.stdout)
            self._parse_dot_output(layout_json, egi)
            print(f"  ✅ {len(self.area_bounds)} containers sized (ports calculated next)")
        finally:
            Path(dot_file).unlink()
    
    def _build_dot(self, egi: RelationalGraphWithCuts) -> str:
        """
        Build DOT for container sizing ONLY.
        
        CORRECT ARCHITECTURE:
        - ONLY includes Cut hierarchy (as clusters)
        - ONLY includes invisible tension edges between related cuts
        - NO vertex or edge content nodes (they're positioned by Pass 2)
        
        Purpose: Get container geometry ONLY. Content positioning is Pass 2's job.
        """
        lines = ["digraph {"]
        lines.append("  rankdir=TB;")
        lines.append("  compound=true;")
        lines.append(f"  fontname=\"{self.style.font_family}\";")
        lines.append(f"  fontsize={self.style.font_size};")
        lines.append("")
        
        hierarchy = self._build_hierarchy(egi)
        
        def add_cut_cluster(cut_id: str, indent="  "):
            """
            Add cut as cluster with SIZE ESTIMATE (NO CONTENT).
            
            Strategy: Replace actual content with a single invisible placeholder
            sized based on estimated content needs. This gives Graphviz a good
            size estimate without forcing it to layout the actual content.
            """
            # Add child cuts as nested subgraphs
            for child_cut_id in hierarchy[cut_id]['children']:
                if child_cut_id == egi.sheet:
                    continue
                
                lines.append(f'{indent}subgraph "cluster_{child_cut_id}" {{')
                lines.append(f'{indent}  label="";')  # No label on cuts
                lines.append(f'{indent}  margin={int(self.style.cut_padding)};')
                lines.append(f'{indent}  style=rounded;')
                
                # Estimate size based on content count
                content_count = len([e for e in egi.area.get(child_cut_id, []) 
                                    if e.startswith(('v_', 'e_'))])
                
                # Calculate estimated dimensions
                # Heuristic: sqrt(n) rows of elements, with padding
                if content_count == 0:
                    # Empty cut: small placeholder
                    est_width = 1.0
                    est_height = 0.5
                elif content_count <= 2:
                    # Small cut: horizontal arrangement
                    est_width = content_count * 1.0
                    est_height = 0.75
                else:
                    # Larger cut: rough square arrangement
                    import math
                    rows = math.ceil(math.sqrt(content_count))
                    cols = math.ceil(content_count / rows)
                    est_width = cols * 0.8
                    est_height = rows * 0.6
                
                # Add single invisible placeholder node with estimated size
                # This gives Graphviz size information without laying out content
                lines.append(f'{indent}  "{child_cut_id}_dummy" [shape=box, style=invis, '
                           f'width={est_width:.2f}, height={est_height:.2f}];')
                
                # Recursively add child clusters
                add_cut_cluster(child_cut_id, indent + "  ")
                
                lines.append(f'{indent}}}')
        
        # Start with sheet and add all cut clusters
        add_cut_cluster(egi.sheet, "  ")
        
        # Add invisible tension edges between cuts with crossing ligatures
        # This pulls related cuts closer together in the layout
        # Uses topology analysis from Pass 0
        if hasattr(self, 'topology') and self.topology:
            added_tension = set()
            for boundary in self.topology.ligatures_crossing_boundary:
                area1, area2 = boundary
                # Only add tension between actual cuts (not sheet)
                if area1 != egi.sheet and area2 != egi.sheet:
                    # Create tension edge between the cuts
                    key = tuple(sorted([area1, area2]))
                    if key not in added_tension:
                        added_tension.add(key)
                        # Invisible edge with high weight pulls cuts closer
                        lines.append(f'  "{area1}_dummy" -> "{area2}_dummy" [style=invis, weight=5.0];')
        
        lines.append("}")
        return "\n".join(lines)
    
    def _parse_dot_output(self, layout_json: Dict, egi: RelationalGraphWithCuts):
        """
        Extract ONLY container bounds from DOT output.
        
        CRITICAL: Node positions are DISCARDED (not extracted).
        Port positions will be calculated geometrically after this step.
        """
        bb = layout_json['bb'].split(',')
        w, h = float(bb[2]), float(bb[3])
        
        self.area_bounds[egi.sheet] = Rect(0, 0, w, h)
        
        # Extract container bounds ONLY
        for obj in layout_json.get('objects', []):
            if obj.get('name', '').startswith('cluster_'):
                cut_id = obj['name'].replace('cluster_', '')
                bb = list(map(float, obj['bb'].split(',')))
                self.area_bounds[cut_id] = Rect(bb[0], h - bb[3], bb[2] - bb[0], bb[3] - bb[1])
        
        # Port calculation moved to _calculate_ports_geometrically() called after Pass 1
    
    def _calculate_ports_geometrically(self, egi: RelationalGraphWithCuts):
        """
        Calculate port positions GEOMETRICALLY from container boundaries.
        
        PHASE 3 FIX: Called AFTER Pass 1 completes.
        Ports are NOT in dot input - calculated from fixed boundaries.
        
        For multi-level crossings (e.g., double cuts), create a port
        on EACH boundary in the path from source to target.
        """
        port_counter = 0
        hierarchy = self._build_hierarchy(egi)
        
        for edge_id, vertices in egi.nu.items():
            edge_cut = self.element_to_cut.get(edge_id, egi.sheet)
            
            for vertex_id in vertices:
                vertex_cut = self.element_to_cut.get(vertex_id, egi.sheet)
                ligature_id = f"{vertex_id}_to_{edge_id}"
                
                if vertex_cut == edge_cut:
                    continue  # Internal ligature, no port needed
                
                # Find the path from vertex area to edge area
                # Create a port on EACH boundary crossed
                path = self._find_area_path(vertex_cut, edge_cut, hierarchy)
                
                if not path or len(path) < 2:
                    continue  # No valid path
                
                # Create ports for each boundary crossing in the path
                for i in range(len(path) - 1):
                    from_area = path[i]
                    to_area = path[i + 1]
                    
                    # Determine which cut's boundary the port goes on
                    # Port is always on the INNER (child) boundary
                    if to_area in hierarchy.get(from_area, {}).get('children', []):
                        port_cut = to_area  # Going deeper
                    elif from_area in hierarchy.get(to_area, {}).get('children', []):
                        port_cut = from_area  # Going up
                    else:
                        continue  # Shouldn't happen in valid path
                    
                    if port_cut not in self.area_bounds:
                        continue
                    
                    # Calculate port position based on neighboring areas
                    port_rect = self.area_bounds[port_cut]
                    
                    # Get centers of the two areas being connected
                    if from_area == vertex_cut or from_area == edge_cut:
                        # Use actual element area
                        from_center = self._get_area_center(from_area)
                    else:
                        # Intermediate area - use its center
                        from_center = self._get_area_center(from_area)
                    
                    if to_area == vertex_cut or to_area == edge_cut:
                        to_center = self._get_area_center(to_area)
                    else:
                        to_center = self._get_area_center(to_area)
                    
                    # Calculate intersection with boundary
                    port_pos = self._calculate_boundary_intersection(
                        from_center, to_center, port_rect
                    )
                    
                    port_id = f"port_{port_counter}"
                    port_counter += 1
                    
                    self.port_nodes[port_id] = PortNode(
                        id=port_id,
                        cut_id=port_cut,
                        position=port_pos,
                        ligature_id=ligature_id
                    )
    
    def _find_area_path(self, from_area: str, to_area: str, hierarchy: Dict) -> List[str]:
        """
        Find the path through the area hierarchy from from_area to to_area.
        
        Returns a list of area IDs representing the path, e.g., [A, B, C]
        means go from A to B to C, crossing two boundaries.
        """
        # Check if one is ancestor of the other (direct nesting)
        from_ancestors = self._get_ancestors(from_area, hierarchy)
        to_ancestors = self._get_ancestors(to_area, hierarchy)
        
        # Case 1: to_area is nested inside from_area (going down)
        if from_area in to_ancestors:
            # Build path from from_area down to to_area
            path = []
            current = to_area
            while current != from_area:
                path.append(current)
                parent = hierarchy.get(current, {}).get('parent')
                if parent is None:
                    break
                current = parent
            path.append(from_area)
            path.reverse()
            return path
        
        # Case 2: from_area is nested inside to_area (going up)
        if to_area in from_ancestors:
            # Build path from from_area up to to_area
            path = [from_area]
            current = from_area
            while current != to_area:
                parent = hierarchy.get(current, {}).get('parent')
                if parent is None:
                    break
                path.append(parent)
                current = parent
            return path
        
        # Case 3: Siblings - find common ancestor and route through it
        common = None
        for anc in from_ancestors:
            if anc in to_ancestors:
                common = anc
                break
        
        if common is None:
            return []
        
        # Path up from from_area to common
        up_path = [from_area]
        current = from_area
        while current != common:
            parent = hierarchy.get(current, {}).get('parent')
            if parent is None:
                break
            up_path.append(parent)
            current = parent
        
        # Path down from common to to_area
        down_path = [to_area]
        current = to_area
        while current != common:
            parent = hierarchy.get(current, {}).get('parent')
            if parent is None:
                break
            down_path.append(parent)
            current = parent
        
        # Combine: up_path + reversed down_path (without duplicating common)
        down_path.reverse()
        path = up_path + down_path[1:]  # Skip common in down_path
        
        return path
    
    def _get_ancestors(self, area: str, hierarchy: Dict) -> List[str]:
        """Get all ancestors of an area, from closest to furthest."""
        ancestors = []
        current = area
        while True:
            parent = hierarchy.get(current, {}).get('parent')
            if parent is None:
                break
            ancestors.append(parent)
            current = parent
        return ancestors
    
    def _get_area_center(self, area: str) -> Tuple[float, float]:
        """Get the center point of an area."""
        if area not in self.area_bounds:
            return (0, 0)
        rect = self.area_bounds[area]
        return (rect.x + rect.width / 2, rect.y + rect.height / 2)
    
    def _calculate_boundary_intersection(self, 
                                        start: Tuple[float, float],
                                        end: Tuple[float, float],
                                        rect: Rect) -> Tuple[float, float]:
        """Calculate where line from start to end intersects rect boundary."""
        sx, sy = start
        ex, ey = end
        
        dx = ex - sx
        dy = ey - sy
        
        intersections = []
        
        # Test each edge
        if dy != 0:
            # Top edge
            t = (rect.y - sy) / dy
            if 0 <= t <= 1:
                ix = sx + t * dx
                if rect.x <= ix <= rect.x + rect.width:
                    intersections.append((ix, rect.y, t))
            
            # Bottom edge
            t = (rect.y + rect.height - sy) / dy
            if 0 <= t <= 1:
                ix = sx + t * dx
                if rect.x <= ix <= rect.x + rect.width:
                    intersections.append((ix, rect.y + rect.height, t))
        
        if dx != 0:
            # Left edge
            t = (rect.x - sx) / dx
            if 0 <= t <= 1:
                iy = sy + t * dy
                if rect.y <= iy <= rect.y + rect.height:
                    intersections.append((rect.x, iy, t))
            
            # Right edge
            t = (rect.x + rect.width - sx) / dx
            if 0 <= t <= 1:
                iy = sy + t * dy
                if rect.y <= iy <= rect.y + rect.height:
                    intersections.append((rect.x + rect.width, iy, t))
        
        if intersections:
            intersections.sort(key=lambda p: p[2])
            return (intersections[0][0], intersections[0][1])
        
        # Fallback
        return (rect.x + rect.width / 2, rect.y)
    
    # NOTE: _identify_boundary_ports removed (Phase 3)
    # Ports now calculated geometrically via _calculate_ports_geometrically()
    
    def _build_hierarchy(self, egi: RelationalGraphWithCuts) -> Dict:
        """Build cut hierarchy."""
        h = {cut_id: {'parent': None, 'children': []} for cut_id in egi.area}
        
        # Ensure sheet is always in hierarchy (even for empty graphs)
        if egi.sheet not in h:
            h[egi.sheet] = {'parent': None, 'children': []}
        
        for cut_id in egi.area:
            if cut_id == egi.sheet:
                continue
            parent = egi.sheet
            for other in egi.area:
                if other != cut_id and cut_id in egi.area.get(other, []):
                    parent = other
                    break
            h[cut_id]['parent'] = parent
            h[parent]['children'].append(cut_id)
        return h
    
    # === PASS 2 ===
    
    def _pass2_content(self, egi: RelationalGraphWithCuts):
        """
        TRUE RECURSIVE BOTTOM-UP content layout.
        
        CRITICAL ARCHITECTURE:
        1. Layout innermost (leaf) cuts FIRST
        2. Child cuts are treated as large fixed obstacles in parent
        3. No Graphviz hints - d3-force discovers optimal positions
        4. Returns final bounding box for each cut (for future dynamic sizing)
        """
        hierarchy = self._build_hierarchy(egi)
        
        def layout_recursive(cut_id: str) -> Optional[Rect]:
            """
            Layout cut content recursively (bottom-up).
            
            Returns:
                Final bounding box of cut's content (currently fixed from Pass 1)
            """
            # FIRST: Recursively layout all children (BOTTOM-UP)
            child_boxes = {}
            for child_id in hierarchy[cut_id]['children']:
                child_box = layout_recursive(child_id)
                if child_box:
                    child_boxes[child_id] = child_box
            
            # THEN: Layout this cut's own content
            # (with children as fixed obstacles)
            
            # Handle empty graphs (no area entry for sheet)
            if cut_id not in egi.area:
                return self.area_bounds.get(cut_id)
            
            content = [e for e in egi.area[cut_id] if e.startswith(('v_', 'e_'))]
            
            # Skip if no content and no children
            if not content and not child_boxes:
                return self.area_bounds.get(cut_id)
            
            # Layout this cut WITH child boxes as obstacles
            self._layout_cut(egi, cut_id, child_boxes)
            
            # Return final bounding box (currently from Pass 1, but could be dynamic)
            return self.area_bounds.get(cut_id)
        
        # Start recursion from sheet (root)
        layout_recursive(egi.sheet)
        print(f"  ✅ {len(self.element_positions)} elements positioned (bottom-up)")
        
        # DEBUG: Summary of all positions
        print(f"\n  Final element positions after Pass 2:")
        for elem_id, pos in sorted(self.element_positions.items()):
            elem_type = "Vertex" if elem_id.startswith('v_') else "Edge"
            print(f"    {elem_id} ({elem_type}): {pos}")
    
    def _layout_cut(self, egi: RelationalGraphWithCuts, cut_id: str, child_boxes: Dict[str, Rect]):
        """
        Layout one cut's content with d3-force worker.
        
        CRITICAL: Child cuts treated as large fixed obstacles.
        
        Args:
            egi: The EGI graph
            cut_id: The cut to layout
            child_boxes: Dict mapping child cut IDs to their final bounding boxes
        """
        # DEBUG: Show what we're processing
        content = [e for e in egi.area.get(cut_id, []) if e.startswith(('v_', 'e_'))]
        print(f"    Processing {cut_id}:")
        print(f"      Content: {len(content)} elements {content}")
        print(f"      Children: {len(child_boxes)} cuts {list(child_boxes.keys())}")
        bounds = self.area_bounds[cut_id]
        payload = {
            'bounds': {'x': bounds.x, 'y': bounds.y, 'width': bounds.width, 'height': bounds.height},
            'nodes': [],
            'links': [],
            'obstacles': [],
            'portNodes': []
        }
        
        for elem_id in egi.area[cut_id]:
            if elem_id.startswith('v_'):
                node = {'id': elem_id, 'type': 'vertex'}
                # Add actual dimensions from style for spatial/logical correspondence
                node['width'] = self.style.vertex_radius * 2
                node['height'] = self.style.vertex_radius * 2
                # NO Graphviz hints! Let d3-force discover optimal position from scratch
                payload['nodes'].append(node)
            elif elem_id.startswith('e_'):
                node = {'id': elem_id, 'type': 'edge_label'}
                # Add actual dimensions from style for spatial/logical correspondence
                label = egi.rel.get(elem_id, '?')
                node['width'] = len(label) * self.style.predicate_char_width + 2 * self.style.text_margin
                node['height'] = self.style.predicate_height
                # NO Graphviz hints! Let d3-force discover optimal position from scratch
                payload['nodes'].append(node)
        
        # Apply user position overrides from LayoutDeltas (pinned positions)
        if self.layout_deltas:
            for delta in self.layout_deltas.deltas.values():
                if delta.delta_type in ('vertex_position', 'edge_position') and delta.new_position:
                    # Find the node in the payload
                    for node in payload['nodes']:
                        if node['id'] == delta.element_id:
                            # Transform to cut-local coordinates
                            node['x'] = delta.new_position[0] - bounds.x
                            node['y'] = delta.new_position[1] - bounds.y
                            # Mark as pinned (D3 will use fx/fy)
                            node['pinned'] = True
                            break
        
        # Add deterministic seed if specified
        if self.layout_deltas and self.layout_deltas.deterministic_seed is not None:
            payload['seed'] = self.layout_deltas.deterministic_seed
        
        # Add boundary keepout zones - ONLY for actual cuts (not sheet)
        # Sheet has no visual boundary, so no keepout needed
        # Cuts have visual boundaries, so elements must stay away from edges
        if cut_id != egi.sheet:
            keepout = 20  # 20 pixels clearance from cut boundary
            
            # Top boundary keepout
            payload['obstacles'].append({
                'id': f'{cut_id}_boundary_top',
                'x': bounds.width / 2,
                'y': keepout / 2,
                'width': bounds.width,
                'height': keepout
            })
            
            # Bottom boundary keepout
            payload['obstacles'].append({
                'id': f'{cut_id}_boundary_bottom',
                'x': bounds.width / 2,
                'y': bounds.height - keepout / 2,
                'width': bounds.width,
                'height': keepout
            })
            
            # Left boundary keepout
            payload['obstacles'].append({
                'id': f'{cut_id}_boundary_left',
                'x': keepout / 2,
                'y': bounds.height / 2,
                'width': keepout,
                'height': bounds.height
            })
            
            # Right boundary keepout
            payload['obstacles'].append({
                'id': f'{cut_id}_boundary_right',
                'x': bounds.width - keepout / 2,
                'y': bounds.height / 2,
                'width': keepout,
                'height': bounds.height
            })
        
        # Add child cuts as obstacles (BOTTOM-UP: children already laid out)
        # These are treated as large fixed nodes that content must avoid
        for child_id, child_box in child_boxes.items():
            payload['obstacles'].append({
                'id': child_id,
                'x': child_box.x - bounds.x + child_box.width/2,
                'y': child_box.y - bounds.y + child_box.height/2,
                'width': child_box.width,
                'height': child_box.height
            })
        
        # PORT PAIRS: The critical insight!
        # Ports have dual nature:
        # - External port: visible in parent's space (on outer side of boundary)
        # - Internal port (ghost): visible in child's space (just inside boundary)
        
        child_ids = list(child_boxes.keys())
        
        # 1. Internal ports: For ligatures entering THIS cut from parent
        #    These are "ghost" ports just inside this cut's boundary
        for port_id, port_node in self.port_nodes.items():
            if port_node.cut_id == cut_id:
                # This port is on our boundary, create INTERNAL ghost
                # Position: slightly inside the boundary (5px inset)
                port_x = port_node.position[0] - bounds.x
                port_y = port_node.position[1] - bounds.y
                
                # Move inward from boundary
                if port_y < 5:  # Top edge
                    port_y = 5
                elif port_y > bounds.height - 5:  # Bottom edge
                    port_y = bounds.height - 5
                elif port_x < 5:  # Left edge
                    port_x = 5
                elif port_x > bounds.width - 5:  # Right edge
                    port_x = bounds.width - 5
                
                payload['portNodes'].append({
                    'id': f'{port_id}_internal',
                    'x': port_x,
                    'y': port_y
                })
        
        # 2. External ports: For ligatures exiting to children
        #    These are on child boundaries, visible in THIS cut's space
        for port_id, port_node in self.port_nodes.items():
            if port_node.cut_id in child_ids:
                port_x = port_node.position[0] - bounds.x
                port_y = port_node.position[1] - bounds.y
                payload['portNodes'].append({
                    'id': f'{port_id}_external',
                    'x': port_x,
                    'y': port_y
                })
        
        # Add links (internal and to port nodes)
        node_ids = [n['id'] for n in payload['nodes']]
        
        for edge_id, vertices in egi.nu.items():
            edge_cut = self.element_to_cut.get(edge_id, egi.sheet)
            
            for v_id in vertices:
                vertex_cut = self.element_to_cut.get(v_id, egi.sheet)
                ligature_id = f"{v_id}_to_{edge_id}"
                
                # Case 1: Both in this area - direct link
                if v_id in node_ids and edge_id in node_ids:
                    payload['links'].append({'source': v_id, 'target': edge_id})
                
                # Case 2: Spanning ligature - link to appropriate port pair
                elif v_id in node_ids or edge_id in node_ids:
                    # Find the port node for this ligature
                    port = next((p for p in self.port_nodes.values() 
                               if p.ligature_id == ligature_id), None)
                    
                    if port:
                        # Determine which port pair to use:
                        # - If port is on THIS cut's boundary: use INTERNAL ghost
                        # - If port is on CHILD's boundary: use EXTERNAL port
                        
                        if port.cut_id == cut_id:
                            # Port on our boundary - use internal ghost
                            port_id = f'{port.id}_internal'
                        elif port.cut_id in child_ids:
                            # Port on child's boundary - use external port
                            port_id = f'{port.id}_external'
                        else:
                            continue  # Port not relevant to this cut
                        
                        if v_id in node_ids:
                            # Vertex in this area, link to port
                            payload['links'].append({'source': v_id, 'target': port_id})
                        elif edge_id in node_ids:
                            # Edge in this area, link from port
                            payload['links'].append({'source': port_id, 'target': edge_id})
        
        # DEBUG: Log payload details
        print(f"      D3 payload for {cut_id}:")
        print(f"        Nodes: {len(payload['nodes'])} {[n['id'] for n in payload['nodes']]}")
        print(f"        Links: {len(payload['links'])}")
        print(f"        Obstacles: {len(payload['obstacles'])}")
        print(f"        Ports: {len(payload['portNodes'])}")
        
        # Call worker
        worker = Path(__file__).parent / 'd3_layout_worker.js'
        result = None
        try:
            result = subprocess.run(
                ['node', str(worker)],
                input=json.dumps(payload),
                capture_output=True, text=True, check=True
            )
            positions = json.loads(result.stdout)
            
            # DEBUG: Log returned positions
            print(f"      D3 returned {len(positions)} positions:")
            for node_id, pos in positions.items():
                global_pos = (bounds.x + pos['x'], bounds.y + pos['y'])
                self.element_positions[node_id] = global_pos
                print(f"        {node_id}: local({pos['x']:.1f}, {pos['y']:.1f}) → global{global_pos}")
                
        except Exception as e:
            # ERROR: Print for debugging
            print(f"    ⚠️  D3 worker error for {cut_id}: {e}")
            if result and result.stderr:
                print(f"    ⚠️  D3 worker stderr: {result.stderr}")
            if result and result.stdout:
                print(f"    ⚠️  D3 worker stdout: {result.stdout[:500]}")
            print(f"    ⚠️  Payload sent: {json.dumps(payload, indent=2)[:1000]}")
            # Fallback: center
            print(f"    ⚠️  Falling back to center position for all nodes")
            for node in payload['nodes']:
                self.element_positions[node['id']] = (bounds.x + bounds.width/2, bounds.y + bounds.height/2)
    
    # === PASS 3 ===
    
    def _pass3_ligatures(self, egi: RelationalGraphWithCuts, style: Optional[dict]) -> LayoutDTO:
        """Route ligatures and build DTO."""
        dto = LayoutDTO()
        
        # Add areas
        hierarchy = self._build_hierarchy(egi)
        for cut_id, rect in self.area_bounds.items():
            parent_id = hierarchy.get(cut_id, {}).get('parent')
            dto.areas.append(RenderableArea(
                id=cut_id,
                parent_id=parent_id,
                rect=rect,
                is_sheet=(cut_id == egi.sheet)
            ))
        
        # Add vertices
        for v in egi.V:
            if v.id in self.element_positions:
                pos = self.element_positions[v.id]
                dto.vertices.append(RenderableVertex(
                    id=v.id,
                    parent_area_id=self.element_to_cut[v.id],
                    pos=pos,
                    label=v.label or ""  # Show name if defined, otherwise just the spot
                ))
        
        # Add edges  
        for edge_id, label in egi.rel.items():
            if edge_id in self.element_positions:
                pos = self.element_positions[edge_id]
                # Use style parameters for tight, precise boundaries
                text_width = len(label) * self.style.predicate_char_width
                w = text_width + 2 * self.style.text_margin
                h = self.style.predicate_height
                rect = Rect(pos[0] - w/2, pos[1] - h/2, w, h)
                
                arity = len(egi.nu.get(edge_id, []))
                ports = self._calc_ports(rect, arity)
                
                dto.edge_labels.append(RenderableEdgeLabel(
                    id=edge_id,
                    parent_area_id=self.element_to_cut[edge_id],
                    rect=rect,
                    label=label,
                    connection_ports=ports
                ))
        
        # Add ligatures (PHASE 4: Area-aware A* pathfinding)
        # Initialize A* pathfinder
        pathfinder = AreaAwareAStarPathfinder(
            area_bounds=self.area_bounds,
            area_hierarchy=self._build_hierarchy(egi),
            grid_resolution=5.0  # 5 pixel grid
        )
        
        # Add obstacles: vertices and edge labels
        for v in dto.vertices:
            v_rect = Rect(
                v.pos[0] - self.style.vertex_radius,
                v.pos[1] - self.style.vertex_radius,
                self.style.vertex_radius * 2,
                self.style.vertex_radius * 2
            )
            pathfinder.add_obstacle(v_rect, 'vertex', v.parent_area_id)
        
        for e in dto.edge_labels:
            pathfinder.add_obstacle(e.rect, 'edge', e.parent_area_id)
        
        # Route each ligature
        for edge_id, vertices in egi.nu.items():
            edge_obj = next((e for e in dto.edge_labels if e.id == edge_id), None)
            if not edge_obj:
                continue
            
            for hook_idx, v_id in enumerate(vertices):
                v_pos = self.element_positions.get(v_id)
                if not v_pos:
                    continue
                
                ligature_key = f"{v_id}_to_{edge_id}"
                
                # Determine areas
                v_area = self.element_to_cut.get(v_id, egi.sheet)
                e_area = self.element_to_cut.get(edge_id, egi.sheet)
                
                # Calculate approach-aware hook position
                # Hook should be on the side where the ligature approaches
                e_center = (edge_obj.rect.x + edge_obj.rect.width/2,
                           edge_obj.rect.y + edge_obj.rect.height/2)
                
                # Calculate approach angle from vertex (or port) to edge center
                if v_area != e_area:
                    # Cross-area: Approach from port
                    port_positions = [p.position for p in self.port_nodes.values() 
                                    if p.ligature_id == ligature_key]
                    approach_from = port_positions[0] if port_positions else v_pos
                else:
                    # Same-area: Approach directly from vertex
                    approach_from = v_pos
                
                # Calculate which side of the edge label to attach to
                dx = approach_from[0] - e_center[0]
                dy = approach_from[1] - e_center[1]
                
                # Determine closest edge of rectangle
                rect = edge_obj.rect
                if abs(dx) > abs(dy):
                    # Approaching from left or right
                    if dx > 0:
                        # Approaching from right -> hook on right
                        e_pos = (rect.x + rect.width, rect.y + rect.height/2)
                    else:
                        # Approaching from left -> hook on left
                        e_pos = (rect.x, rect.y + rect.height/2)
                else:
                    # Approaching from top or bottom
                    if dy > 0:
                        # Approaching from bottom -> hook on bottom
                        e_pos = (rect.x + rect.width/2, rect.y + rect.height)
                    else:
                        # Approaching from top -> hook on top
                        e_pos = (rect.x + rect.width/2, rect.y)
                
                # Check for custom path from user
                custom_path = None
                if self.layout_deltas:
                    for delta in self.layout_deltas.deltas.values():
                        if (delta.delta_type == 'ligature_path' and 
                            delta.nu_mapping_key == ligature_key and 
                            delta.custom_path):
                            custom_path = delta.custom_path
                            break
                
                # Calculate path
                if custom_path:
                    path_points = custom_path
                elif v_area == e_area:
                    # PHASE 4: Same-area path (avoid obstacles)
                    path_points = pathfinder.find_path(v_pos, e_pos, v_area, e_area)
                    path_points = pathfinder.smooth_path(path_points)
                else:
                    # PHASE 4: Cross-area path (use ports)
                    port_positions = [p.position for p in self.port_nodes.values() 
                                    if p.ligature_id == ligature_key]
                    path_points = pathfinder.find_path(v_pos, e_pos, v_area, e_area, port_positions)
                    path_points = pathfinder.smooth_path(path_points)
                
                dto.ligatures.append(RenderableLigature(
                    start_vertex_id=v_id,
                    end_edge_id=edge_id,
                    end_hook_index=hook_idx,
                    path_points=path_points
                ))
        
        print(f"  ✅ {len(dto.ligatures)} ligatures routed (area-aware A*)")
        return dto
    
    def _calc_ports(self, rect: Rect, arity: int) -> List[ConnectionPort]:
        """Calculate connection ports on edge label."""
        ports = []
        if arity == 1:
            ports.append(ConnectionPort(0, (rect.x + rect.width/2, rect.y), 'N'))
        elif arity == 2:
            ports.append(ConnectionPort(0, (rect.x, rect.y + rect.height/2), 'W'))
            ports.append(ConnectionPort(1, (rect.x + rect.width, rect.y + rect.height/2), 'E'))
        else:
            spacing = rect.width / (arity + 1)
            for i in range(arity):
                ports.append(ConnectionPort(i, (rect.x + spacing * (i+1), rect.y), 'N'))
        return ports
    
    # === DEBUG OUTPUT ===
    
    def _debug_pass1(self, prefix: str, egi: RelationalGraphWithCuts):
        """Save Pass 1 debug SVG with EGIF."""
        sheet = self.area_bounds.get(egi.sheet, Rect(0, 0, 600, 400))
        svg = [f'<svg width="{sheet.width}" height="{sheet.height + 40}" xmlns="http://www.w3.org/2000/svg">']
        
        # Add EGIF at top
        svg.append(f'<text x="10" y="20" font-family="monospace" font-size="12">EGIF: {self.egif}</text>')
        svg.append('<g transform="translate(0, 30)">')
        
        # Add containers (sheet gets dotted boundary for debug only)
        for cut_id, rect in self.area_bounds.items():
            if cut_id == egi.sheet:
                # Sheet: dotted boundary (debug only, won't appear in final)
                svg.append(f'<rect x="{rect.x}" y="{rect.y}" width="{rect.width}" height="{rect.height}" fill="none" stroke="lightgray" stroke-width="1" stroke-dasharray="5,5"/>')
                svg.append(f'<text x="{rect.x + 5}" y="{rect.y + 15}" font-size="10" fill="lightgray">Sheet (unbounded)</text>')
            else:
                # Cuts: solid boundary (negation)
                svg.append(f'<rect x="{rect.x}" y="{rect.y}" width="{rect.width}" height="{rect.height}" fill="none" stroke="blue" stroke-width="2"/>')
                svg.append(f'<text x="{rect.x + 5}" y="{rect.y + 15}" font-size="10" fill="gray">{cut_id[:8]}</text>')
        
        svg.append('</g>')
        svg.append('</svg>')
        Path(f"{prefix}_pass1_containers.svg").write_text('\n'.join(svg))
        print(f"    Debug: {prefix}_pass1_containers.svg")
    
    def _debug_pass2(self, prefix: str, egi: RelationalGraphWithCuts):
        """Save Pass 2 debug SVG with EGIF."""
        sheet = self.area_bounds.get(egi.sheet, Rect(0, 0, 600, 400))
        svg = [f'<svg width="{sheet.width}" height="{sheet.height + 40}" xmlns="http://www.w3.org/2000/svg">']
        
        # Add EGIF
        svg.append(f'<text x="10" y="20" font-family="monospace" font-size="12">EGIF: {self.egif}</text>')
        svg.append('<g transform="translate(0, 30)">')
        
        # Containers (sheet dotted for debug, cuts solid)
        for cut_id, rect in self.area_bounds.items():
            if cut_id == egi.sheet:
                svg.append(f'<rect x="{rect.x}" y="{rect.y}" width="{rect.width}" height="{rect.height}" fill="none" stroke="lightgray" stroke-width="1" stroke-dasharray="5,5"/>')
            else:
                svg.append(f'<rect x="{rect.x}" y="{rect.y}" width="{rect.width}" height="{rect.height}" fill="none" stroke="lightgray"/>')
        
        # Elements
        for elem_id, pos in self.element_positions.items():
            svg.append(f'<circle cx="{pos[0]}" cy="{pos[1]}" r="5" fill="red"/>')
            svg.append(f'<text x="{pos[0] + 8}" y="{pos[1] + 4}" font-size="8" fill="gray">{elem_id[:6]}</text>')
        
        svg.append('</g>')
        svg.append('</svg>')
        Path(f"{prefix}_pass2_content.svg").write_text('\n'.join(svg))
        print(f"    Debug: {prefix}_pass2_content.svg")
    
    def _debug_pass3(self, prefix: str, dto: LayoutDTO, egi: RelationalGraphWithCuts):
        """Save Pass 3 debug SVG with EGIF."""
        sheet = next((a for a in dto.areas if a.is_sheet), None)
        if not sheet:
            return
        
        svg = [f'<svg width="{sheet.rect.width}" height="{sheet.rect.height + 40}" xmlns="http://www.w3.org/2000/svg">']
        
        # Add EGIF
        svg.append(f'<text x="10" y="20" font-family="monospace" font-size="12">EGIF: {self.egif}</text>')
        svg.append('<g transform="translate(0, 30)">')
        
        # Ligatures (behind everything)
        for lig in dto.ligatures:
            points = ' '.join(f"{p[0]},{p[1]}" for p in lig.path_points)
            svg.append(f'<polyline points="{points}" fill="none" stroke="#666" stroke-width="2"/>')
        
        # Areas (ONLY cuts have boundaries - sheet is unbounded!)
        for area in dto.areas:
            if not area.is_sheet:
                # Cuts have solid boundaries (representing negation)
                svg.append(f'<rect x="{area.rect.x}" y="{area.rect.y}" width="{area.rect.width}" height="{area.rect.height}" fill="none" stroke="blue" stroke-width="2" rx="{self.style.cut_corner_radius}"/>')
        
        # Vertices
        for v in dto.vertices:
            svg.append(f'<circle cx="{v.pos[0]}" cy="{v.pos[1]}" r="{self.style.vertex_radius}" fill="white" stroke="black" stroke-width="2"/>')
            svg.append(f'<text x="{v.pos[0]}" y="{v.pos[1]+4}" text-anchor="middle" font-size="{self.style.font_size}">{v.label}</text>')
        
        # Edge labels
        for e in dto.edge_labels:
            svg.append(f'<rect x="{e.rect.x}" y="{e.rect.y}" width="{e.rect.width}" height="{e.rect.height}" fill="white" stroke="black" stroke-width="2"/>')
            svg.append(f'<text x="{e.rect.x + e.rect.width/2}" y="{e.rect.y + e.rect.height/2 + 4}" text-anchor="middle" font-size="{self.style.font_size}">{e.label}</text>')
        
        svg.append('</g>')
        svg.append('</svg>')
        Path(f"{prefix}_pass3_final.svg").write_text('\n'.join(svg))
        print(f"    Debug: {prefix}_pass3_final.svg")
