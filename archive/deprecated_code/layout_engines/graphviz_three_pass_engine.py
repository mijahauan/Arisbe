"""
Definitive Three-Pass EGI Layout Engine
========================================

Pass 1: Graphviz dot - Hierarchical containment layout + port calculation
Pass 2: d3-force - Content positioning within containers (bottom-up)
Pass 3: A* pathfinding - Collision-free ligature routing

This architecture correctly separates:
- Container-level forces (hierarchical nesting) - Graphviz
- Content-level forces (relational positioning) - d3-force
- Path routing (collision avoidance) - A*
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field

from egi_core_dau import RelationalGraphWithCuts
from constrained_force_layout import Rect
from area_aware_pathfinder import AreaAwareFinder

# DTO classes
@dataclass
class RenderableArea:
    id: str
    parent_id: Optional[str]
    rect: Rect
    is_sheet: bool = False
    style: Dict[str, Any] = field(default_factory=dict)

@dataclass  
class RenderableVertex:
    id: str
    parent_area_id: str
    pos: Tuple[float, float]
    label: str = ""
    style: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConnectionPort:
    port_id: int
    position: Tuple[float, float]
    direction: str

@dataclass
class RenderableEdgeLabel:
    id: str
    parent_area_id: str
    rect: Rect
    label: str
    connection_ports: List[ConnectionPort] = field(default_factory=list)
    style: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RenderableLigature:
    start_vertex_id: str
    end_edge_id: str
    end_hook_index: int
    path_points: List[Tuple[float, float]]
    style: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LayoutDTO:
    areas: List[RenderableArea] = field(default_factory=list)
    vertices: List[RenderableVertex] = field(default_factory=list)
    edge_labels: List[RenderableEdgeLabel] = field(default_factory=list)
    ligatures: List[RenderableLigature] = field(default_factory=list)
    annotations: List = field(default_factory=list)


@dataclass
class PortNode:
    """Port node on a cut boundary where ligatures cross."""
    id: str
    cut_id: str
    position: Tuple[float, float]
    ligature_id: str


class GraphvizThreePassEngine:
    """
    Definitive three-pass layout engine using Graphviz + d3-force + A*.
    
    Pass 1: Graphviz dot for hierarchical containment
    Pass 2: d3-force for content positioning (bottom-up)
    Pass 3: A* for path routing
    """
    
    def __init__(self):
        self.d3_worker = Path(__file__).parent / "d3_three_pass_bridge.js"
        
        # State accumulated across passes
        self.area_bounds: Dict[str, Rect] = {}  # cut_id -> Rect (from Graphviz)
        self.port_nodes: Dict[str, PortNode] = {}  # port_id -> PortNode
        self.element_positions: Dict[str, Tuple[float, float]] = {}  # element_id -> (x, y)
        self.element_to_cut: Dict[str, str] = {}  # element_id -> cut_id
    
    def generate_layout(self, egi: RelationalGraphWithCuts, style=None, layout_deltas=None) -> LayoutDTO:
        """
        Execute complete three-pass layout workflow.
        
        Returns: LayoutDTO with all elements positioned and paths routed
        """
        # Reset state for new layout
        self.area_bounds = {}
        self.port_nodes = {}
        self.element_positions = {}
        self.element_to_cut = {}
        
        print("=" * 70)
        print("GRAPHVIZ THREE-PASS LAYOUT ENGINE")
        print("=" * 70)
        
        # Cache element-to-cut mapping
        for cut_id, elements in egi.area.items():
            for element_id in elements:
                self.element_to_cut[element_id] = cut_id
        
        # Pass 1: Graphviz for hierarchical layout
        print("\nPass 1: Graphviz hierarchical layout...")
        self._pass1_graphviz_layout(egi)
        
        # Pass 2: d3-force for content positioning (bottom-up)
        print("\nPass 2: d3-force content positioning...")
        self._pass2_content_layout(egi)
        
        # Pass 3: A* path routing
        print("\nPass 3: A* ligature routing...")
        dto = self._pass3_path_routing(egi, style)
        
        print(f"\n✅ Layout complete: {len(dto.vertices)}V, {len(dto.edge_labels)}E, {len(dto.ligatures)}L")
        return dto
    
    def _pass1_graphviz_layout(self, egi: RelationalGraphWithCuts):
        """
        Pass 1: Use Graphviz dot to layout nested cut hierarchy.
        
        Creates DOT file with cluster subgraphs for each cut.
        Runs `dot -Tjson` to get positions.
        Calculates port nodes where spanning ligatures cross boundaries.
        """
        # Build DOT file
        dot_content = self._build_dot_file(egi)
        
        # Write to temp file and run dot
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(dot_content)
            dot_file = f.name
        
        try:
            result = subprocess.run(
                ['dot', '-Tjson', dot_file],
                capture_output=True,
                text=True,
                check=True
            )
            
            layout_json = json.loads(result.stdout)
            
            # Parse Graphviz output
            self._parse_graphviz_output(layout_json, egi)
            
            print(f"  ✅ Positioned {len(self.area_bounds)} areas")
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Graphviz failed: {e.stderr}")
            raise
        finally:
            Path(dot_file).unlink()
    
    def _build_dot_file(self, egi: RelationalGraphWithCuts) -> str:
        """
        Build DOT file with ALL content as nodes inside clusters.
        
        This allows Graphviz to correctly calculate container sizes bottom-up.
        We'll DISCARD the content positions and recalculate with d3-force in Pass 2.
        """
        lines = []
        lines.append("digraph EGI {")
        lines.append("  rankdir=TB;")
        lines.append("  compound=true;")
        lines.append("  node [shape=box, width=0.5, height=0.3];")  # Reasonable defaults
        lines.append("")
        
        # Build hierarchy
        hierarchy = self._build_hierarchy(egi)
        
        # Add cuts as cluster subgraphs (recursive)
        def add_cut_cluster(cut_id: str, indent: str = "  "):
            if cut_id == egi.sheet:
                # Sheet is not a cluster, but still add its content
                return
            
            lines.append(f'{indent}subgraph "cluster_{cut_id}" {{')
            lines.append(f'{indent}  label="";')
            lines.append(f'{indent}  style=rounded;')
            lines.append(f'{indent}  margin=16;')
            
            # Add ALL vertices in this cut as actual nodes
            content = egi.area.get(cut_id, [])
            for elem_id in content:
                if elem_id.startswith('v_'):
                    vertex_obj = next((v for v in egi.V if v.id == elem_id), None)
                    label = vertex_obj.label if vertex_obj and vertex_obj.label else "*"
                    lines.append(f'{indent}  "{elem_id}" [label="{label}", shape=circle];')
            
            # Add ALL edge labels in this cut as actual nodes
            for elem_id in content:
                if elem_id.startswith('e_'):
                    label = egi.rel.get(elem_id, "?")
                    lines.append(f'{indent}  "{elem_id}" [label="{label}", shape=box];')
            
            # Add child cuts recursively
            for child_id in hierarchy[cut_id]['children']:
                add_cut_cluster(child_id, indent + "  ")
            
            lines.append(f'{indent}}}')
        
        # Add all cuts (including those in sheet)
        for cut_id in egi.area.keys():
            if cut_id != egi.sheet:
                if hierarchy[cut_id]['parent'] == egi.sheet:
                    add_cut_cluster(cut_id)
        
        # Add sheet-level content (outside any cluster)
        sheet_content = egi.area.get(egi.sheet, [])
        sheet_vertices = [e for e in sheet_content if e.startswith('v_')]
        sheet_edges = [e for e in sheet_content if e.startswith('e_')]
        
        for elem_id in sheet_vertices:
            vertex_obj = next((v for v in egi.V if v.id == elem_id), None)
            label = vertex_obj.label if vertex_obj and vertex_obj.label else "*"
            lines.append(f'  "{elem_id}" [label="{label}", shape=circle];')
        
        for elem_id in sheet_edges:
            label = egi.rel.get(elem_id, "?")
            lines.append(f'  "{elem_id}" [label="{label}", shape=box];')
        
        # Add invisible "expander" to ensure sheet has space for its own content
        # This forces the graph to be wide/tall enough for sheet elements
        if len(sheet_vertices) + len(sheet_edges) > 0:
            lines.append(f'  sheet_expander [shape=point, style=invis, width=2, height=1.5];')
        
        lines.append("")
        
        # Add invisible tension edges BETWEEN CLUSTERS for spanning ligatures
        # This pulls related cuts closer together while respecting containment
        cluster_tensions = set()  # Track unique cut-to-cut connections
        
        for edge_id, vertices in egi.nu.items():
            edge_cut = self.element_to_cut.get(edge_id, egi.sheet)
            
            for vertex_id in vertices:
                vertex_cut = self.element_to_cut.get(vertex_id, egi.sheet)
                
                if vertex_cut != edge_cut and vertex_cut != egi.sheet and edge_cut != egi.sheet:
                    # Spanning ligature between two cuts - add cluster-to-cluster tension
                    # Use frozenset to avoid duplicate edges in both directions
                    tension = frozenset([vertex_cut, edge_cut])
                    cluster_tensions.add(tension)
        
        # Add the tension edges between clusters
        for tension in cluster_tensions:
            cut1, cut2 = list(tension)
            # ltail/lhead tell dot these are cluster-level edges
            lines.append(f'  "cluster_{cut1}":s -> "cluster_{cut2}":s [style=invis, weight=2, constraint=false];')
        
        lines.append("}")
        return "\n".join(lines)
    
    def _parse_graphviz_output(self, layout_json: Dict, egi: RelationalGraphWithCuts):
        """
        Parse Graphviz JSON output to extract cut bounds ONLY.
        
        We DISCARD vertex/edge positions - they were only for sizing calculation.
        We'll recalculate positions with d3-force in Pass 2.
        """
        # Graphviz uses points (72 points = 1 inch)
        # Y-axis is bottom-up in Graphviz, need to flip it
        
        bb = layout_json.get('bb', '0,0,100,100').split(',')
        sheet_width = float(bb[2]) - float(bb[0])
        sheet_height = float(bb[3]) - float(bb[1])
        
        self.area_bounds[egi.sheet] = Rect(
            x=0,
            y=0,
            width=sheet_width,
            height=sheet_height
        )
        
        # Parse subgraphs (clusters) for cut bounds
        for obj in layout_json.get('objects', []):
            if obj.get('name', '').startswith('cluster_'):
                cut_id = obj['name'].replace('cluster_', '')
                
                # Parse bounding box
                bb = obj.get('bb', '0,0,100,100').split(',')
                x1, y1, x2, y2 = map(float, bb)
                
                # Flip Y coordinates (Graphviz is bottom-up, we want top-down)
                y1_flipped = sheet_height - y2
                y2_flipped = sheet_height - y1
                
                self.area_bounds[cut_id] = Rect(
                    x=x1,
                    y=y1_flipped,
                    width=x2 - x1,
                    height=y2_flipped - y1_flipped
                )
        
        # Calculate port nodes NOW (after cut bounds, before content layout)
        # Ports are based on cut centers, so we can calculate them now
        self._calculate_port_nodes(egi)
        
        print(f"    Parsed {len(self.area_bounds)} areas, {len(self.port_nodes)} port nodes")
    
    def _calculate_port_nodes(self, egi: RelationalGraphWithCuts):
        """
        Calculate port nodes on cut boundaries for spanning ligatures.
        
        Ports are placed at the intersection of:
        - The straight line between CUT CENTERS (not element positions)
        - The cut boundary
        
        This creates clean, predictable exit points regardless of internal layout.
        """
        port_counter = 0
        hierarchy = self._build_hierarchy(egi)
        
        for edge_id, vertices in egi.nu.items():
            edge_cut = self.element_to_cut.get(edge_id, egi.sheet)
            
            for vertex_id in vertices:
                vertex_cut = self.element_to_cut.get(vertex_id, egi.sheet)
                
                if vertex_cut == edge_cut:
                    continue
                
                # Spanning ligature - find ALL boundaries crossed
                ligature_id = f"{vertex_id}_to_{edge_id}"
                
                # Trace path from vertex area to edge area through hierarchy
                cuts_to_port = []
                
                # Start from edge's cut and walk up to find vertex's cut
                current = edge_cut
                while current != egi.sheet and current != vertex_cut:
                    cuts_to_port.append(current)
                    parent = hierarchy.get(current, {}).get('parent')
                    if not parent:
                        break
                    current = parent
                
                # Determine the two areas to connect
                source_cut = vertex_cut if vertex_cut != egi.sheet else None
                target_cut = edge_cut if edge_cut != egi.sheet else None
                
                # Create port on each boundary crossed
                for port_cut in cuts_to_port:
                    if port_cut in self.area_bounds:
                        cut_rect = self.area_bounds[port_cut]
                        cut_center = (
                            cut_rect.x + cut_rect.width / 2,
                            cut_rect.y + cut_rect.height / 2
                        )
                        
                        # Find the "other" cut to determine port direction
                        # Port should face toward the connected element
                        if source_cut and source_cut in self.area_bounds:
                            other_rect = self.area_bounds[source_cut]
                            other_center = (
                                other_rect.x + other_rect.width / 2,
                                other_rect.y + other_rect.height / 2
                            )
                        else:
                            # Vertex is in sheet - use vertex position
                            vertex_pos = self.element_positions.get(vertex_id, (cut_rect.x, cut_rect.y))
                            other_center = vertex_pos
                        
                        # Calculate port as intersection of line from other center to cut center
                        port_pos = self._calculate_boundary_intersection(
                            other_center, cut_center, cut_rect
                        )
                        
                        port_id = f"port_{port_counter}"
                        port_counter += 1
                        
                        self.port_nodes[port_id] = PortNode(
                            id=port_id,
                            cut_id=port_cut,
                            position=port_pos,
                            ligature_id=ligature_id
                        )
    
    def _calculate_boundary_intersection(self, start_pos: Tuple[float, float], 
                                         end_pos: Tuple[float, float],
                                         rect: Rect) -> Tuple[float, float]:
        """
        Calculate intersection of line from start to end with rectangle boundary.
        
        Returns the point on the rectangle edge closest to start_pos.
        """
        sx, sy = start_pos
        ex, ey = end_pos
        
        # Calculate center of rectangle
        cx = rect.x + rect.width / 2
        cy = rect.y + rect.height / 2
        
        # Direction vector from start to end
        dx = ex - sx
        dy = ey - sy
        
        # Find which edge of rectangle the line intersects
        # Test all four edges and find the one closest to start
        intersections = []
        
        # Top edge (y = rect.y)
        if dy != 0:
            t = (rect.y - sy) / dy
            if 0 <= t <= 1:
                ix = sx + t * dx
                if rect.x <= ix <= rect.x + rect.width:
                    intersections.append((ix, rect.y, t))
        
        # Bottom edge (y = rect.y + rect.height)
        if dy != 0:
            t = (rect.y + rect.height - sy) / dy
            if 0 <= t <= 1:
                ix = sx + t * dx
                if rect.x <= ix <= rect.x + rect.width:
                    intersections.append((ix, rect.y + rect.height, t))
        
        # Left edge (x = rect.x)
        if dx != 0:
            t = (rect.x - sx) / dx
            if 0 <= t <= 1:
                iy = sy + t * dy
                if rect.y <= iy <= rect.y + rect.height:
                    intersections.append((rect.x, iy, t))
        
        # Right edge (x = rect.x + rect.width)
        if dx != 0:
            t = (rect.x + rect.width - sx) / dx
            if 0 <= t <= 1:
                iy = sy + t * dy
                if rect.y <= iy <= rect.y + rect.height:
                    intersections.append((rect.x + rect.width, iy, t))
        
        # Return intersection closest to start (smallest t)
        if intersections:
            intersections.sort(key=lambda p: p[2])
            return (intersections[0][0], intersections[0][1])
        
        # Fallback: return center of nearest edge
        return (cx, rect.y)
    
    def _pass2_content_layout(self, egi: RelationalGraphWithCuts):
        """
        Pass 2: Per-area d3-force to find lowest energy state.
        
        Bottom-up recursive: layout children first, then parent.
        Each area gets its own d3-force simulation within its fixed bounds.
        """
        hierarchy = self._build_hierarchy(egi)
        
        def layout_cut_recursive(cut_id: str):
            # First, layout all children
            for child_id in hierarchy[cut_id]['children']:
                layout_cut_recursive(child_id)
            
            # Now layout this cut's content
            content = egi.area.get(cut_id, [])
            has_content = any(e.startswith('v_') or e.startswith('e_') for e in content)
            
            if has_content:
                self._layout_cut_content(egi, cut_id)
        
        # Start from sheet
        layout_cut_recursive(egi.sheet)
        
        print(f"  ✅ Positioned {len(self.element_positions)} elements with per-area d3-force")
    
    def _layout_cut_content(self, egi: RelationalGraphWithCuts, cut_id: str):
        """Layout content within a single cut using d3-force."""
        # Get cut bounds from Pass 1
        cut_bounds = self.area_bounds.get(cut_id)
        if not cut_bounds:
            print(f"    Warning: No bounds for cut {cut_id[:8]}")
            return
        
        # Get hierarchy to find child cuts (they are obstacles!)
        hierarchy = self._build_hierarchy(egi)
        child_cuts = hierarchy.get(cut_id, {}).get('children', [])
        
        # Build local graph for d3-force
        local_graph = {
            'nodes': [],
            'edges': []
        }
        
        # Add child cuts as LARGE FIXED obstacles
        for child_cut_id in child_cuts:
            child_bounds = self.area_bounds.get(child_cut_id)
            if child_bounds:
                # Convert to local coordinates within parent (CENTER of child cut)
                local_x = child_bounds.x - cut_bounds.x + child_bounds.width/2
                local_y = child_bounds.y - cut_bounds.y + child_bounds.height/2
                
                local_graph['nodes'].append({
                    'id': child_cut_id,
                    'type': 'obstacle',
                    'fx': local_x,  # Fixed position
                    'fy': local_y,
                    'width': child_bounds.width,
                    'height': child_bounds.height
                })
        
        # Calculate safe zone BELOW all child cuts
        max_child_bottom = 0
        for child_cut_id in child_cuts:
            child_bounds = self.area_bounds.get(child_cut_id)
            if child_bounds:
                # In local coords: child bottom = (child.y - cut.y) + child.height
                child_bottom_local = (child_bounds.y - cut_bounds.y) + child_bounds.height
                max_child_bottom = max(max_child_bottom, child_bottom_local)
        
        # Place elements below the lowest child cut, with padding
        safe_y = max_child_bottom + 20 if max_child_bottom > 0 else cut_bounds.height * 0.5
        
        # Add vertices (not child cuts!) with safe initial positions
        for vertex_id in egi.area[cut_id]:
            if vertex_id.startswith('v_'):
                vertex_obj = next((v for v in egi.V if v.id == vertex_id), None)
                local_graph['nodes'].append({
                    'id': vertex_id,
                    'type': 'vertex',
                    'label': vertex_obj.label if vertex_obj else '',
                    'x': cut_bounds.width * 0.3,  # Left side
                    'y': safe_y  # Below all child cuts
                })
        
        # Add edge labels (not child cuts!) with safe initial positions
        for edge_id in egi.area[cut_id]:
            if edge_id.startswith('e_'):
                local_graph['nodes'].append({
                    'id': edge_id,
                    'type': 'edge_label',
                    'label': egi.rel.get(edge_id, ''),
                    'x': cut_bounds.width * 0.7,  # Right side
                    'y': safe_y  # Below all child cuts
                })
        
        # Add port nodes on this cut's boundary (fixed positions)
        ports_in_cut = [p for p in self.port_nodes.values() if p.cut_id == cut_id]
        for port in ports_in_cut:
            # Convert to local coordinates
            local_x = port.position[0] - cut_bounds.x
            local_y = port.position[1] - cut_bounds.y
            local_graph['nodes'].append({
                'id': port.id,
                'type': 'port',
                'fx': local_x,  # Fixed position
                'fy': local_y
            })
        
        # Add ligatures: internal ones directly, spanning ones via ports
        num_ligatures = 0
        for edge_id, vertices in egi.nu.items():
            if edge_id in egi.area[cut_id]:
                for vertex_id in vertices:
                    vertex_cut = self.element_to_cut.get(vertex_id, egi.sheet)
                    
                    if vertex_id in egi.area[cut_id]:
                        # Both in same cut - direct connection
                        local_graph['edges'].append({
                            'source': vertex_id,
                            'target': edge_id
                        })
                        num_ligatures += 1
                    else:
                        # Spanning - connect edge to its port node
                        ligature_id = f"{vertex_id}_to_{edge_id}"
                        port = next((p for p in ports_in_cut if p.ligature_id == ligature_id), None)
                        if port:
                            local_graph['edges'].append({
                                'source': edge_id,
                                'target': port.id
                            })
                            num_ligatures += 1
            elif cut_id in [self.element_to_cut.get(v, egi.sheet) for v in vertices]:
                # Vertex in this cut, edge elsewhere - connect vertex to port
                for vertex_id in vertices:
                    if vertex_id in egi.area[cut_id]:
                        ligature_id = f"{vertex_id}_to_{edge_id}"
                        port = next((p for p in ports_in_cut if p.ligature_id == ligature_id), None)
                        if port:
                            local_graph['edges'].append({
                                'source': vertex_id,
                                'target': port.id
                            })
                            num_ligatures += 1
        
        print(f"    Cut {cut_id[:8]}: {len([n for n in local_graph['nodes'] if n['type'] != 'obstacle'])} elements, {len(child_cuts)} obstacles, {num_ligatures} ligatures")
        
        # Run d3-force simulation
        config = {
            'width': cut_bounds.width,
            'height': cut_bounds.height,
            'iterations': 500,  # Much more iterations to overcome obstacles
            'containment': True
        }
        
        try:
            layout_result = self._run_d3_simulation(local_graph, config)
            
            # Store positions (transform to global coordinates)
            for node in layout_result['nodes']:
                # d3 gives us local coordinates within the cut
                # Transform to global by adding cut's top-left corner
                global_x = cut_bounds.x + node['x']
                global_y = cut_bounds.y + node['y']
                self.element_positions[node['id']] = (global_x, global_y)
        
        except Exception as e:
            print(f"    Warning: d3 layout failed for {cut_id[:8]}: {e}")
    
    def _run_d3_simulation(self, graph: Dict, config: Dict) -> Dict:
        """Run d3-force simulation via Node.js worker."""
        input_data = {
            'type': 'micro_layout',
            'graph': graph,
            'config': config
        }
        
        result = subprocess.run(
            ['node', str(self.d3_worker)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"d3 simulation failed: {result.stderr}")
        
        return json.loads(result.stdout)
    
    def _pass3_path_routing(self, egi: RelationalGraphWithCuts, style) -> LayoutDTO:
        """
        Pass 3: Route ligature paths using direct lines.
        
        TODO: Implement proper A* pathfinding with obstacle avoidance.
        """
        dto = LayoutDTO()
        
        # Create areas from Graphviz bounds
        hierarchy = self._build_hierarchy(egi)
        for cut_id, rect in self.area_bounds.items():
            parent_id = hierarchy.get(cut_id, {}).get('parent')
            
            area = RenderableArea(
                id=cut_id,
                parent_id=parent_id,
                rect=rect,
                is_sheet=(cut_id == egi.sheet)
            )
            dto.areas.append(area)
        
        # Create vertices
        for vertex_id, pos in self.element_positions.items():
            if vertex_id.startswith('v_'):
                vertex_obj = next((v for v in egi.V if v.id == vertex_id), None)
                parent_area = self.element_to_cut.get(vertex_id, egi.sheet)
                
                vertex = RenderableVertex(
                    id=vertex_id,
                    parent_area_id=parent_area,
                    pos=pos,
                    label=vertex_obj.label if vertex_obj and vertex_obj.label != "None" else ""
                )
                dto.vertices.append(vertex)
        
        # Create edge labels
        for edge_id, pos in self.element_positions.items():
            if edge_id.startswith('e_'):
                label_text = egi.rel.get(edge_id, '')
                parent_area = self.element_to_cut.get(edge_id, egi.sheet)
                
                # Estimate size
                width = len(label_text) * 8 + 10
                height = 18
                
                rect = Rect(
                    x=pos[0] - width/2,
                    y=pos[1] - height/2,
                    width=width,
                    height=height
                )
                
                # Calculate connection ports based on arity
                arity = len(egi.nu.get(edge_id, []))
                connection_ports = self._calculate_connection_ports(rect, arity)
                
                edge_label = RenderableEdgeLabel(
                    id=edge_id,
                    parent_area_id=parent_area,
                    rect=rect,
                    label=label_text,
                    connection_ports=connection_ports
                )
                dto.edge_labels.append(edge_label)
        
        # Route ligatures with obstacle avoidance and proper hook assignment
        for edge_id, vertices in egi.nu.items():
            edge_label = next((e for e in dto.edge_labels if e.id == edge_id), None)
            if not edge_label:
                continue
            
            for hook_index, vertex_id in enumerate(vertices):
                vertex_pos = self.element_positions.get(vertex_id)
                
                if vertex_pos:
                    # Get the specific connection port for this hook
                    if hook_index < len(edge_label.connection_ports):
                        port = edge_label.connection_ports[hook_index]
                        edge_port_pos = port.position
                    else:
                        # Fallback to edge label center
                        edge_port_pos = (
                            edge_label.rect.x + edge_label.rect.width/2,
                            edge_label.rect.y + edge_label.rect.height/2
                        )
                    
                    # Find which cut contains the vertex and edge
                    vertex_cut = self.element_to_cut.get(vertex_id, egi.sheet)
                    edge_cut = self.element_to_cut.get(edge_id, egi.sheet)
                    
                    # Build path: for spanning, route via port nodes with A* for each segment
                    if vertex_cut != edge_cut:
                        # Spanning ligature - route via boundary port nodes
                        ligature_id = f"{vertex_id}_to_{edge_id}"
                        boundary_ports = [p for p in self.port_nodes.values() if p.ligature_id == ligature_id]
                        
                        # Sort ports by hierarchy depth (outermost first)
                        boundary_ports.sort(key=lambda p: len([a for a in egi.area.keys() if p.cut_id in egi.area.get(a, [])]))
                        
                        # Build path with A* routing for each segment
                        path_points = []
                        waypoints = [vertex_pos] + [p.position for p in boundary_ports] + [edge_port_pos]
                        
                        for i in range(len(waypoints) - 1):
                            segment_start = waypoints[i]
                            segment_end = waypoints[i + 1]
                            
                            # Route this segment with A* obstacle avoidance
                            segment_path = self._route_ligature_with_obstacles(
                                segment_start, segment_end, vertex_cut, edge_cut, egi
                            )
                            
                            # Add segment (skip first point if not first segment to avoid duplicates)
                            if i == 0:
                                path_points.extend(segment_path)
                            else:
                                path_points.extend(segment_path[1:])
                    else:
                        # Internal ligature - route with obstacle avoidance
                        path_points = self._route_ligature_with_obstacles(
                            vertex_pos, edge_port_pos, vertex_cut, edge_cut, egi
                        )
                    
                    ligature = RenderableLigature(
                        start_vertex_id=vertex_id,
                        end_edge_id=edge_id,
                        end_hook_index=hook_index,
                        path_points=path_points
                    )
                    dto.ligatures.append(ligature)
        
        return dto
    
    def _route_ligature_with_obstacles(self, start_pos: Tuple[float, float], 
                                       end_pos: Tuple[float, float],
                                       start_cut: str, end_cut: str,
                                       egi: RelationalGraphWithCuts) -> List[Tuple[float, float]]:
        """
        Route ligature segment from start to end, avoiding obstacles.
        
        For now: Simple routing around first intersecting obstacle.
        TODO: Implement proper A* pathfinding for multiple obstacles.
        """
        # Determine which area we're routing in
        routing_area = start_cut if start_cut == end_cut else egi.sheet
        
        # Get child cuts as obstacles
        hierarchy = self._build_hierarchy(egi)
        child_cuts = hierarchy.get(routing_area, {}).get('children', [])
        
        if not child_cuts:
            # No obstacles, direct path is fine
            return [start_pos, end_pos]
        
        # Check if direct path intersects any child cut
        for child_cut_id in child_cuts:
            child_bounds = self.area_bounds.get(child_cut_id)
            if child_bounds and self._line_intersects_rect(start_pos, end_pos, child_bounds):
                # Path crosses obstacle - route around it
                path = self._route_around_rectangle(start_pos, end_pos, child_bounds)
                return path
        
        # No intersection, direct path is fine
        return [start_pos, end_pos]
    
    def _line_intersects_rect(self, p1: Tuple[float, float], p2: Tuple[float, float], 
                              rect: Rect) -> bool:
        """Check if line segment from p1 to p2 intersects rectangle."""
        # Simple bounding box check first
        min_x = min(p1[0], p2[0])
        max_x = max(p1[0], p2[0])
        min_y = min(p1[1], p2[1])
        max_y = max(p1[1], p2[1])
        
        # If line's bounding box doesn't overlap rect, no intersection
        if (max_x < rect.x or min_x > rect.x + rect.width or
            max_y < rect.y or min_y > rect.y + rect.height):
            return False
        
        # Check if either endpoint is inside rect
        if (rect.x <= p1[0] <= rect.x + rect.width and rect.y <= p1[1] <= rect.y + rect.height):
            return True
        if (rect.x <= p2[0] <= rect.x + rect.width and rect.y <= p2[1] <= rect.y + rect.height):
            return True
        
        # TODO: Full line-rectangle intersection test
        # For now, assume intersection if bounding boxes overlap
        return True
    
    def _route_around_rectangle(self, start: Tuple[float, float], end: Tuple[float, float],
                                rect: Rect) -> List[Tuple[float, float]]:
        """Route path around a rectangular obstacle."""
        # Find which corner to route around
        cx = rect.x + rect.width / 2
        cy = rect.y + rect.height / 2
        
        # Determine routing based on relative positions
        start_x, start_y = start
        end_x, end_y = end
        
        # Route via corners with some padding
        padding = 10
        
        # Choose corner based on which side to go around
        if start_x < cx and end_x > cx:
            # Route around top or bottom
            if start_y < cy:
                # Route around top
                waypoint = (cx, rect.y - padding)
            else:
                # Route around bottom
                waypoint = (cx, rect.y + rect.height + padding)
        elif start_y < cy and end_y > cy:
            # Route around left or right
            if start_x < cx:
                # Route around left
                waypoint = (rect.x - padding, cy)
            else:
                # Route around right
                waypoint = (rect.x + rect.width + padding, cy)
        else:
            # Default: route via nearest corner
            corners = [
                (rect.x - padding, rect.y - padding),
                (rect.x + rect.width + padding, rect.y - padding),
                (rect.x - padding, rect.y + rect.height + padding),
                (rect.x + rect.width + padding, rect.y + rect.height + padding)
            ]
            
            # Find closest corner to midpoint
            mid_x = (start_x + end_x) / 2
            mid_y = (start_y + end_y) / 2
            
            waypoint = min(corners, key=lambda c: (c[0] - mid_x)**2 + (c[1] - mid_y)**2)
        
        return [start, waypoint, end]
    
    def _calculate_connection_ports(self, rect: Rect, arity: int) -> List[ConnectionPort]:
        """
        Calculate connection ports on edge label rectangle based on arity.
        
        Ports are placed on cardinal/intercardinal directions around the rectangle.
        """
        ports = []
        
        cx = rect.x + rect.width / 2
        cy = rect.y + rect.height / 2
        
        # Define port positions based on arity
        # Order: N, NE, E, SE, S, SW, W, NW
        port_configs = [
            (cx, rect.y, 'N'),                                    # 0: North
            (rect.x + rect.width, rect.y, 'NE'),                 # 1: Northeast  
            (rect.x + rect.width, cy, 'E'),                      # 2: East
            (rect.x + rect.width, rect.y + rect.height, 'SE'),   # 3: Southeast
            (cx, rect.y + rect.height, 'S'),                     # 4: South
            (rect.x, rect.y + rect.height, 'SW'),                # 5: Southwest
            (rect.x, cy, 'W'),                                   # 6: West
            (rect.x, rect.y, 'NW'),                              # 7: Northwest
        ]
        
        # Select ports based on arity (distribute evenly around perimeter)
        if arity == 1:
            # Single port on north
            selected_indices = [0]
        elif arity == 2:
            # North and south
            selected_indices = [0, 4]
        elif arity == 3:
            # North, SE, SW (triangle)
            selected_indices = [0, 3, 5]
        elif arity == 4:
            # Cardinal directions
            selected_indices = [0, 2, 4, 6]
        else:
            # For higher arity, space evenly
            step = 8 // arity if arity <= 8 else 1
            selected_indices = [i * step for i in range(min(arity, 8))]
        
        for i, idx in enumerate(selected_indices):
            if idx < len(port_configs):
                x, y, direction = port_configs[idx]
                ports.append(ConnectionPort(
                    port_id=i,
                    position=(x, y),
                    direction=direction
                ))
        
        return ports
    
    def _build_hierarchy(self, egi: RelationalGraphWithCuts) -> Dict:
        """Build parent-child hierarchy of cuts."""
        hierarchy = {}
        
        for cut_id in egi.area.keys():
            parent = None
            if cut_id != egi.sheet:
                try:
                    parent = egi.get_context(cut_id)
                except (ValueError, KeyError):
                    parent = egi.sheet
            
            hierarchy[cut_id] = {
                'parent': parent,
                'children': []
            }
        
        # Populate children
        for cut_id, info in hierarchy.items():
            if info['parent'] and info['parent'] in hierarchy:
                hierarchy[info['parent']]['children'].append(cut_id)
        
        return hierarchy
