#!/usr/bin/env python3
"""
Definitive Three-Pass EGI Layout Engine

Pass 1: Graphviz dot - Container hierarchy and port calculation
Pass 2: d3-force - Content positioning with custom containment  
Pass 3: A* pathfinding - Ligature routing with obstacle avoidance
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
        
        # Pass 1
        print("Pass 1: Container hierarchy (Graphviz)...")
        self._pass1_containers(egi)
        if debug_prefix:
            self._debug_pass1(debug_prefix, egi)
        
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
        """Use Graphviz to position containers and calculate ports."""
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
            self._extract_graphviz_positions(layout_json, egi)  # NEW: Extract element positions
            print(f"  ✅ {len(self.area_bounds)} containers, {len(self.port_nodes)} ports")
        finally:
            Path(dot_file).unlink()
    
    def _build_dot(self, egi: RelationalGraphWithCuts) -> str:
        """
        Build DOT with properly nested clusters AND port nodes.
        
        CRITICAL: 
        1. Clusters must be nested INSIDE their parent clusters
        2. Port nodes must be included so Graphviz positions content near boundaries
        """
        lines = ["digraph {"]
        lines.append("  rankdir=TB;")
        lines.append("  compound=true;")
        lines.append(f"  fontname=\"{self.style.font_family}\";")
        lines.append(f"  fontsize={self.style.font_size};")
        lines.append(f"  node [fontname=\"{self.style.font_family}\", fontsize={self.style.font_size}];")
        lines.append(f"  edge [fontname=\"{self.style.font_family}\"];")
        
        # Check if this is a flat sheet (no nested cuts)
        hierarchy = self._build_hierarchy(egi)
        sheet_elements = egi.area.get(egi.sheet, [])
        is_flat_sheet = all(not elem.startswith('c_') for elem in sheet_elements)
        
        if is_flat_sheet and len(sheet_elements) > 0:
            # For flat sheets: increase spacing for better ligature visibility
            lines.append("  nodesep=1.5;")  # More space between nodes (default 0.25)
            lines.append("  ranksep=1.5;")  # More space between ranks (default 0.5)
        
        lines.append("")
        
        # PRE-CALCULATE which boundaries need ports
        boundary_ports = self._identify_boundary_ports(egi, hierarchy)
        
        def add_content_and_children(cut_id: str, indent="  "):
            """Add content nodes and child clusters for this cut."""
            content = egi.area.get(cut_id, [])
            
            # Add direct content (vertices and edges, but NOT child cuts)
            for elem_id in content:
                # Skip child cuts - they'll be added as nested clusters
                if elem_id.startswith('c_'):
                    continue
                    
                if elem_id.startswith('v_'):
                    v = next((x for x in egi.V if x.id == elem_id), None)
                    label = v.label if v else '*'
                    radius_inches = self.style.vertex_radius / 72.0  # Convert pixels to inches
                    lines.append(f'{indent}"{elem_id}" [label="{label}", shape=circle, width={radius_inches:.2f}, height={radius_inches:.2f}, fixedsize=true];')
                elif elem_id.startswith('e_'):
                    label = egi.rel.get(elem_id, '?')
                    # Calculate width based on text
                    text_width = len(label) * self.style.predicate_char_width + 2 * self.style.text_margin
                    width_inches = text_width / 72.0
                    height_inches = self.style.predicate_height / 72.0
                    lines.append(f'{indent}"{elem_id}" [label="{label}", shape=box, width={width_inches:.2f}, height={height_inches:.2f}];')
            
            # Add child cuts as nested subgraphs
            for child_cut_id in hierarchy[cut_id]['children']:
                if child_cut_id == egi.sheet:
                    continue
                    
                lines.append(f'{indent}subgraph "cluster_{child_cut_id}" {{')
                lines.append(f'{indent}  margin={int(self.style.cut_padding)};')
                lines.append(f'{indent}  style=rounded;')
                
                # Add port nodes for THIS cut's boundary (before content)
                # This ensures they're positioned on/near the cluster boundary
                for port_info in boundary_ports:
                    if port_info['cut_id'] == child_cut_id:
                        port_id = port_info['id']
                        lines.append(f'{indent}  "{port_id}" [label="", shape=point, width=0.01, height=0.01];')
                
                # Recursively add child's content and its children
                add_content_and_children(child_cut_id, indent + "  ")
                
                lines.append(f'{indent}}}')
        
        # Start with sheet content and children
        add_content_and_children(egi.sheet, "  ")
        
        # Add edges for ALL ligatures (both internal and spanning)
        # This tells Graphviz the graph topology so it can optimize layouts
        added_edges = set()
        
        for edge_id, vertices in egi.nu.items():
            edge_cut = self.element_to_cut.get(edge_id, egi.sheet)
            
            for vertex_id in vertices:
                vertex_cut = self.element_to_cut.get(vertex_id, egi.sheet)
                ligature_id = f"{vertex_id}_to_{edge_id}"
                
                if ligature_id in added_edges:
                    continue
                added_edges.add(ligature_id)
                
                if vertex_cut == edge_cut:
                    # INTERNAL ligature: direct edge so Graphviz optimizes placement
                    lines.append(f'  "{vertex_id}" -> "{edge_id}" [style=invis, len=1.0];')
                else:
                    # SPANNING ligature: route through port
                    port_info = next((p for p in boundary_ports if p['ligature_id'] == ligature_id), None)
                    if port_info:
                        port_id = port_info['id']
                        lines.append(f'  "{vertex_id}" -> "{port_id}" [style=invis, len=0.5];')
                        lines.append(f'  "{port_id}" -> "{edge_id}" [style=invis, len=0.5];')
        
        lines.append("}")
        return "\n".join(lines)
    
    def _extract_graphviz_positions(self, layout_json: Dict, egi: RelationalGraphWithCuts):
        """Extract element positions from Graphviz JSON output."""
        self.graphviz_positions = {}
        
        # Extract node positions from Graphviz output
        for obj in layout_json.get('objects', []):
            node_id = obj.get('name')
            if node_id and node_id.startswith(('v_', 'e_')):
                # Graphviz positions are in points, convert to our coordinate system
                pos = obj.get('pos')
                if pos:
                    coords = pos.split(',')
                    if len(coords) == 2:
                        x = float(coords[0])
                        y = float(coords[1])
                        self.graphviz_positions[node_id] = (x, y)
    
    def _parse_dot_output(self, layout_json: Dict, egi: RelationalGraphWithCuts):
        """Extract container bounds AND port positions from DOT output."""
        bb = layout_json['bb'].split(',')
        w, h = float(bb[2]), float(bb[3])
        
        self.area_bounds[egi.sheet] = Rect(0, 0, w, h)
        
        # Extract container bounds
        for obj in layout_json.get('objects', []):
            if obj.get('name', '').startswith('cluster_'):
                cut_id = obj['name'].replace('cluster_', '')
                bb = list(map(float, obj['bb'].split(',')))
                self.area_bounds[cut_id] = Rect(bb[0], h - bb[3], bb[2] - bb[0], bb[3] - bb[1])
        
        # Extract port positions from Graphviz layout
        hierarchy = self._build_hierarchy(egi)
        port_infos = self._identify_boundary_ports(egi, hierarchy)
        
        for port_info in port_infos:
            port_id = port_info['id']
            
            # Find this port node in the layout
            for obj in layout_json.get('objects', []):
                if obj.get('name') == port_id:
                    pos = obj.get('pos', '0,0').split(',')
                    x, y = float(pos[0]), float(pos[1])
                    
                    # Convert from Graphviz coordinates (y increases upward)
                    self.port_nodes[port_id] = PortNode(
                        id=port_id,
                        cut_id=port_info['cut_id'],
                        position=(x, h - y),  # Flip Y
                        ligature_id=port_info['ligature_id']
                    )
                    break
    
    def _calculate_ports(self, egi: RelationalGraphWithCuts):
        """
        Calculate port positions on cut boundaries where ligatures cross.
        
        CRITICAL: For multi-level crossings (e.g., double cuts), create a port
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
    
    def _identify_boundary_ports(self, egi: RelationalGraphWithCuts, hierarchy: Dict) -> List[Dict]:
        """
        Identify which boundaries need port nodes BEFORE Graphviz runs.
        Returns list of port info dicts with id, ligature_id, cut_id.
        """
        ports = []
        port_counter = 0
        
        for edge_id, vertices in egi.nu.items():
            edge_cut = self.element_to_cut.get(edge_id, egi.sheet)
            
            for vertex_id in vertices:
                vertex_cut = self.element_to_cut.get(vertex_id, egi.sheet)
                ligature_id = f"{vertex_id}_to_{edge_id}"
                
                if vertex_cut == edge_cut:
                    continue  # Internal ligature, no port needed
                
                # Find the path and create a port for each boundary
                path = self._find_area_path(vertex_cut, edge_cut, hierarchy)
                
                if not path or len(path) < 2:
                    continue
                
                for i in range(len(path) - 1):
                    from_area = path[i]
                    to_area = path[i + 1]
                    
                    # Determine which boundary gets the port
                    if to_area in hierarchy.get(from_area, {}).get('children', []):
                        port_cut = to_area
                    elif from_area in hierarchy.get(to_area, {}).get('children', []):
                        port_cut = from_area
                    else:
                        continue
                    
                    port_id = f"port_{port_counter}"
                    port_counter += 1
                    
                    ports.append({
                        'id': port_id,
                        'cut_id': port_cut,
                        'ligature_id': ligature_id
                    })
        
        return ports
    
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
        """Position content using d3-force worker."""
        hierarchy = self._build_hierarchy(egi)
        
        def layout_recursive(cut_id: str):
            for child in hierarchy[cut_id]['children']:
                layout_recursive(child)
            
            # Handle empty graphs (no area entry for sheet)
            if cut_id not in egi.area:
                return
            
            content = [e for e in egi.area[cut_id] if e.startswith(('v_', 'e_'))]
            if content:
                self._layout_cut(egi, cut_id, hierarchy)
        
        layout_recursive(egi.sheet)
        print(f"  ✅ {len(self.element_positions)} elements positioned")
    
    def _layout_cut(self, egi: RelationalGraphWithCuts, cut_id: str, hierarchy: Dict):
        """Layout one cut's content with d3 worker."""
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
                # Add Graphviz position as starting hint (if available)
                if elem_id in self.graphviz_positions:
                    gv_x, gv_y = self.graphviz_positions[elem_id]
                    # Transform to cut-local coordinates
                    node['x'] = gv_x - bounds.x
                    node['y'] = gv_y - bounds.y
                payload['nodes'].append(node)
            elif elem_id.startswith('e_'):
                node = {'id': elem_id, 'type': 'edge_label'}
                # Add actual dimensions from style for spatial/logical correspondence
                label = egi.rel.get(elem_id, '?')
                node['width'] = len(label) * self.style.predicate_char_width + 2 * self.style.text_margin
                node['height'] = self.style.predicate_height
                # Add Graphviz position as starting hint (if available)
                if elem_id in self.graphviz_positions:
                    gv_x, gv_y = self.graphviz_positions[elem_id]
                    # Transform to cut-local coordinates
                    node['x'] = gv_x - bounds.x
                    node['y'] = gv_y - bounds.y
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
        
        # Add child obstacles
        for child in hierarchy[cut_id]['children']:
            cb = self.area_bounds[child]
            payload['obstacles'].append({
                'id': child,
                'x': cb.x - bounds.x + cb.width/2,
                'y': cb.y - bounds.y + cb.height/2,
                'width': cb.width,
                'height': cb.height
            })
        
        # PORT PAIRS: The critical insight!
        # Ports have dual nature:
        # - External port: visible in parent's space (on outer side of boundary)
        # - Internal port (ghost): visible in child's space (just inside boundary)
        
        child_ids = hierarchy[cut_id]['children']
        
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
        
        # Call worker
        worker = Path(__file__).parent / 'd3_layout_worker.js'
        try:
            result = subprocess.run(
                ['node', str(worker)],
                input=json.dumps(payload),
                capture_output=True, text=True, check=True
            )
            positions = json.loads(result.stdout)
            for node_id, pos in positions.items():
                self.element_positions[node_id] = (bounds.x + pos['x'], bounds.y + pos['y'])
        except Exception as e:
            # Fallback: center
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
                    label=v.label or "*"
                ))
        
        # Add edges
        for edge_id, label in egi.rel.items():
            if edge_id in self.element_positions:
                pos = self.element_positions[edge_id]
                w = max(40, len(label) * 8)
                rect = Rect(pos[0] - w/2, pos[1] - 12, w, 24)
                
                arity = len(egi.nu.get(edge_id, []))
                ports = self._calc_ports(rect, arity)
                
                dto.edge_labels.append(RenderableEdgeLabel(
                    id=edge_id,
                    parent_area_id=self.element_to_cut[edge_id],
                    rect=rect,
                    label=label,
                    connection_ports=ports
                ))
        
        # Add ligatures (simple paths for now, with custom path support)
        for edge_id, vertices in egi.nu.items():
            edge_obj = next((e for e in dto.edge_labels if e.id == edge_id), None)
            if not edge_obj:
                continue
            
            for hook_idx, v_id in enumerate(vertices):
                v_pos = self.element_positions.get(v_id)
                if v_pos:
                    e_pos = (edge_obj.rect.x + edge_obj.rect.width/2,
                            edge_obj.rect.y + edge_obj.rect.height/2)
                    
                    # Check for custom ligature path from LayoutDeltas
                    custom_path = None
                    ligature_key = f"{v_id}_to_{edge_id}"
                    
                    if self.layout_deltas:
                        for delta in self.layout_deltas.deltas.values():
                            if (delta.delta_type == 'ligature_path' and 
                                delta.nu_mapping_key == ligature_key and 
                                delta.custom_path):
                                # TODO: Validate custom path doesn't cross obstacles
                                # For now, use it if provided
                                custom_path = delta.custom_path
                                break
                    
                    # Use custom path if available, otherwise straight line
                    path_points = custom_path if custom_path else [v_pos, e_pos]
                    
                    dto.ligatures.append(RenderableLigature(
                        start_vertex_id=v_id,
                        end_edge_id=edge_id,
                        end_hook_index=hook_idx,
                        path_points=path_points
                    ))
        
        print(f"  ✅ {len(dto.ligatures)} ligatures routed")
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
