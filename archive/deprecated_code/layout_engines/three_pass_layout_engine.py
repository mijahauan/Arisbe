"""
Three-Pass EGI Layout Engine
============================

This is the DEFINITIVE layout architecture using:
1. Pass 1: Macro-layout (position cuts, calculate port nodes)
2. Pass 2: Micro-layouts (recursive bottom-up, ports as pinned nodes)
3. Pass 3: Path routing (A* with fixed ports)

Port nodes are the critical interface between container boundaries and content.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field

from egi_core_dau import RelationalGraphWithCuts
from constrained_force_layout import Rect
from area_aware_pathfinder import AreaAwareFinder

# DTO classes (copied from definitive_egi_layout_engine)
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
    """A port node is a fixed point on a container boundary where ligatures cross."""
    id: str
    cut_id: str  # Which cut this port belongs to
    position: Tuple[float, float]  # Absolute (x, y) in final coordinates
    direction: str  # 'N', 'S', 'E', 'W' - which side of the cut
    ligatures: List[str] = field(default_factory=list)  # Which ligatures use this port


class ThreePassLayoutEngine:
    """
    The definitive EGI layout engine using a 3-pass architecture.
    
    Pass 1: Macro-layout positions cuts and calculates port nodes
    Pass 2: Micro-layouts arrange content within cuts (bottom-up, ports pinned)
    Pass 3: Path routing draws ligatures through ports
    """
    
    def __init__(self):
        self.bridge_script = Path(__file__).parent / "d3_three_pass_bridge.js"
        self.grid_resolution = 2.0  # Grid cells per pixel for A*
        
        # State accumulated across passes
        self.port_nodes: Dict[str, PortNode] = {}  # port_id -> PortNode
        self.cut_positions: Dict[str, Tuple[float, float]] = {}  # cut_id -> (cx, cy)
        self.cut_sizes: Dict[str, Tuple[float, float]] = {}  # cut_id -> (width, height)
        self.element_positions: Dict[str, Tuple[float, float]] = {}  # element_id -> (x, y)
        self.element_to_cut: Dict[str, str] = {}  # element_id -> cut_id (cached)
    
    def generate_layout(self, egi: RelationalGraphWithCuts, style=None, layout_deltas=None) -> LayoutDTO:
        """
        Execute the complete 3-pass layout workflow.
        
        Returns: LayoutDTO with all elements positioned and paths routed
        """
        # Pass 1: Macro-layout
        self._pass1_macro_layout(egi)
        
        # Pass 2: Micro-layouts (recursive, bottom-up)
        self._pass2_micro_layouts(egi)
        
        # Pass 3: Path routing
        dto = self._pass3_path_routing(egi, style)
        
        return dto
    
    def _pass1_macro_layout(self, egi: RelationalGraphWithCuts):
        """
        Pass 1: Position cuts and calculate port nodes.
        
        Uses d3-force to position cuts relative to each other based on
        ligatures that span between them. Port nodes are the intersection
        points where these ligatures cross cut boundaries.
        """
        # Cache element-to-cut mapping
        for cut_id, elements in egi.area.items():
            for element_id in elements:
                self.element_to_cut[element_id] = cut_id
        
        # Initialize all cuts with default positions and sizes
        # This ensures we never have None values
        for cut_id in egi.area.keys():
            if cut_id not in self.cut_positions:
                self.cut_positions[cut_id] = (400, 300)
            if cut_id not in self.cut_sizes:
                self.cut_sizes[cut_id] = (200, 150)
        
        # Build macro-graph: cuts as nodes, spanning ligatures as edges
        macro_graph = self._build_macro_graph(egi)
        
        print(f"Pass 1: Macro-graph has {len(macro_graph['nodes'])} nodes, {len(macro_graph['edges'])} edges")
        
        # Execute d3-force layout on macro-graph
        try:
            macro_layout = self._run_d3_macro_layout(macro_graph)
            print(f"Pass 1: D3 returned {len(macro_layout.get('nodes', []))} positioned nodes")
        except Exception as e:
            print(f"Pass 1: D3 macro-layout failed: {e}")
            # Fallback: use simple positions
            macro_layout = {'nodes': macro_graph['nodes'], 'edges': macro_graph['edges']}
            for i, node in enumerate(macro_layout['nodes']):
                node['x'] = 400
                node['y'] = 300
                node['width'] = 200
                node['height'] = 150
        
        # Extract cut positions
        for node in macro_layout['nodes']:
            cut_id = node['id']
            x = node.get('x', 400)
            y = node.get('y', 300)
            self.cut_positions[cut_id] = (x, y)
            
            # Initial size estimate (will be refined in Pass 2)
            width = node.get('width', 200)
            height = node.get('height', 150)
            self.cut_sizes[cut_id] = (width, height)
            
            print(f"  Cut {cut_id[:8]}: pos=({x:.0f},{y:.0f}), size=({width}x{height})")
        
        # Calculate port nodes from spanning edges
        for edge in macro_layout['edges']:
            source_id = edge['source']
            target_id = edge['target']
            ligature_id = edge['ligature_id']
            
            # Calculate intersection points on boundaries
            port_a = self._calculate_port_on_boundary(source_id, target_id)
            port_b = self._calculate_port_on_boundary(target_id, source_id)
            
            # Store port nodes
            port_a_id = f"port_{source_id}_{ligature_id}"
            port_b_id = f"port_{target_id}_{ligature_id}"
            
            self.port_nodes[port_a_id] = PortNode(
                id=port_a_id,
                cut_id=source_id,
                position=port_a['position'],
                direction=port_a['direction'],
                ligatures=[ligature_id]
            )
            
            self.port_nodes[port_b_id] = PortNode(
                id=port_b_id,
                cut_id=target_id,
                position=port_b['position'],
                direction=port_b['direction'],
                ligatures=[ligature_id]
            )
    
    def _pass2_micro_layouts(self, egi: RelationalGraphWithCuts):
        """
        Pass 2: Recursive bottom-up micro-layouts.
        
        For each cut, arrange its content with ports as pinned nodes.
        This creates attractive forces pulling content toward exit ports.
        """
        hierarchy = self._build_cut_hierarchy(egi)
        
        # Process cuts bottom-up
        def layout_cut_recursive(cut_id: str):
            # First, layout all child cuts
            children = hierarchy[cut_id]['children']
            for child_id in children:
                layout_cut_recursive(child_id)
            
            # Now layout this cut's content
            # Only layout if there's actual content (vertices or edges)
            content = egi.area.get(cut_id, [])
            has_content = any(e.startswith('v_') or e.startswith('e_') for e in content)
            
            if has_content:
                try:
                    self._layout_cut_content(egi, cut_id, hierarchy)
                except Exception as e:
                    print(f"Warning: Failed to layout cut {cut_id[:8]}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue with defaults - cut already has position/size from Pass 1
        
        # Start from sheet (root)
        layout_cut_recursive(egi.sheet)
        
        # Calculate final bounding box for sheet from all content
        if egi.sheet in self.cut_positions:
            min_x, min_y = float('inf'), float('inf')
            max_x, max_y = float('-inf'), float('-inf')
            
            # Include all cuts
            for cut_id, pos in self.cut_positions.items():
                if cut_id != egi.sheet:
                    size = self.cut_sizes.get(cut_id)
                    if size and size[0] and size[1]:
                        min_x = min(min_x, pos[0] - size[0]/2)
                        min_y = min(min_y, pos[1] - size[1]/2)
                        max_x = max(max_x, pos[0] + size[0]/2)
                        max_y = max(max_y, pos[1] + size[1]/2)
            
            # Include all elements
            for elem_pos in self.element_positions.values():
                if elem_pos and len(elem_pos) == 2:
                    min_x = min(min_x, elem_pos[0] - 20)
                    min_y = min(min_y, elem_pos[1] - 20)
                    max_x = max(max_x, elem_pos[0] + 20)
                    max_y = max(max_y, elem_pos[1] + 20)
            
            if min_x != float('inf') and max_x != float('-inf'):
                padding = 30
                sheet_width = max_x - min_x + 2*padding
                sheet_height = max_y - min_y + 2*padding
                
                # Ensure minimum size
                sheet_width = max(sheet_width, 400)
                sheet_height = max(sheet_height, 300)
                
                self.cut_sizes[egi.sheet] = (sheet_width, sheet_height)
                # Center the sheet
                self.cut_positions[egi.sheet] = (
                    (min_x + max_x) / 2,
                    (min_y + max_y) / 2
                )
            else:
                # Fallback if no content
                self.cut_sizes[egi.sheet] = (800, 600)
                self.cut_positions[egi.sheet] = (400, 300)
        
        print(f"Pass 2: Positioned {len(self.element_positions)} elements")
    
    def _pass3_path_routing(self, egi: RelationalGraphWithCuts, style) -> LayoutDTO:
        """
        Pass 3: Route all ligature paths using A* pathfinding.
        
        Paths are segmented at port nodes:
        - Internal segment: content -> port
        - Boundary segment: port -> port
        - Continue until final content node
        """
        dto = LayoutDTO()
        
        # Create areas from cut positions and sizes
        for cut_id, pos in self.cut_positions.items():
            size = self.cut_sizes.get(cut_id)
            if size is None or size[0] is None or size[1] is None:
                print(f"Warning: Cut {cut_id[:8]} has no size, using default")
                size = (200, 150)
            
            # Get parent safely
            parent_id = None
            if cut_id != egi.sheet:
                try:
                    parent_id = egi.get_context(cut_id)
                except (ValueError, KeyError):
                    # Cut not found in context, might be sheet
                    parent_id = None
            
            # Create rectangle (top-left corner based)
            rect = Rect(
                x=pos[0] - size[0]/2,
                y=pos[1] - size[1]/2,
                width=size[0],
                height=size[1]
            )
            
            area = RenderableArea(
                id=cut_id,
                parent_id=parent_id,
                rect=rect,
                is_sheet=(cut_id == egi.sheet)
            )
            dto.areas.append(area)
        
        # Create vertices from element positions
        for vertex_id in [v.id for v in egi.V]:
            if vertex_id in self.element_positions:
                pos = self.element_positions[vertex_id]
                vertex_obj = next(v for v in egi.V if v.id == vertex_id)
                parent_area = self._get_cut_for_element(egi, vertex_id)
                
                vertex = RenderableVertex(
                    id=vertex_id,
                    parent_area_id=parent_area,
                    pos=pos,
                    label=vertex_obj.label if vertex_obj.label != "None" else ""
                )
                dto.vertices.append(vertex)
        
        # Create edge labels from element positions
        for edge_id, label_text in egi.rel.items():
            if edge_id in self.element_positions:
                pos = self.element_positions[edge_id]
                parent_area = self._get_cut_for_element(egi, edge_id)
                
                # Estimate text size
                char_width = 8
                char_height = 12
                width = len(label_text) * char_width + 10
                height = char_height + 6
                
                rect = Rect(
                    x=pos[0] - width/2,
                    y=pos[1] - height/2,
                    width=width,
                    height=height
                )
                
                edge_label = RenderableEdgeLabel(
                    id=edge_id,
                    parent_area_id=parent_area,
                    rect=rect,
                    label=label_text,
                    connection_ports=[]  # No ports needed in 3-pass system
                )
                dto.edge_labels.append(edge_label)
        
        # Route each ligature through its ports
        for edge_id, vertices in egi.nu.items():
            for vertex_id in vertices:
                path = self._route_ligature_through_ports(
                    egi, vertex_id, edge_id, dto
                )
                
                if path:
                    ligature = RenderableLigature(
                        start_vertex_id=vertex_id,
                        end_edge_id=edge_id,
                        end_hook_index=0,
                        path_points=path
                    )
                    dto.ligatures.append(ligature)
        
        return dto
    
    def _build_macro_graph(self, egi: RelationalGraphWithCuts) -> Dict:
        """Build macro-graph: ONLY top-level cuts as nodes, spanning ligatures as edges."""
        nodes = []
        edges = []
        
        # Build hierarchy first to identify top-level cuts
        hierarchy = self._build_cut_hierarchy(egi)
        
        # Add ONLY top-level cuts (direct children of sheet) as nodes
        for cut_id in egi.area.keys():
            if cut_id != egi.sheet:
                parent = hierarchy[cut_id]['parent']
                if parent == egi.sheet or parent is None:
                    # This is a top-level cut
                    nodes.append({
                        'id': cut_id,
                        'type': 'cut',
                        'content_count': len(egi.area[cut_id])
                    })
        
        # Add sheet
        nodes.append({
            'id': egi.sheet,
            'type': 'sheet',
            'content_count': len(egi.area[egi.sheet])
        })
        
        # Add edges for ligatures that span cuts
        for edge_id, vertices in egi.nu.items():
            edge_cut = self._get_cut_for_element(egi, edge_id)
            
            for vertex_id in vertices:
                vertex_cut = self._get_cut_for_element(egi, vertex_id)
                
                if vertex_cut != edge_cut:
                    # Spanning ligature
                    edges.append({
                        'source': vertex_cut,
                        'target': edge_cut,
                        'ligature_id': f"{vertex_id}_{edge_id}"
                    })
        
        return {'nodes': nodes, 'edges': edges}
    
    def _run_d3_macro_layout(self, macro_graph: Dict) -> Dict:
        """Execute d3-force macro-layout via Node.js subprocess."""
        input_data = {
            'type': 'macro_layout',
            'graph': macro_graph,
            'config': {
                'width': 800,
                'height': 600,
                'iterations': 300
            }
        }
        
        result = subprocess.run(
            ['node', str(self.bridge_script)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"D3 macro-layout failed: {result.stderr}")
        
        return json.loads(result.stdout)
    
    def _calculate_port_on_boundary(self, cut_id: str, towards_cut_id: str) -> Dict:
        """Calculate port position on cut boundary facing towards another cut."""
        cut_pos = self.cut_positions[cut_id]
        towards_pos = self.cut_positions[towards_cut_id]
        cut_size = self.cut_sizes[cut_id]
        
        cx, cy = cut_pos
        tx, ty = towards_pos
        width, height = cut_size
        
        # Determine which side of the cut faces the target
        dx = tx - cx
        dy = ty - cy
        
        if abs(dx) > abs(dy):
            # East or West
            if dx > 0:
                # East side
                return {
                    'position': (cx + width/2, cy),
                    'direction': 'E'
                }
            else:
                # West side
                return {
                    'position': (cx - width/2, cy),
                    'direction': 'W'
                }
        else:
            # North or South
            if dy > 0:
                # South side
                return {
                    'position': (cx, cy + height/2),
                    'direction': 'S'
                }
            else:
                # North side
                return {
                    'position': (cx, cy - height/2),
                    'direction': 'N'
                }
    
    def _build_cut_hierarchy(self, egi: RelationalGraphWithCuts) -> Dict:
        """Build parent-child hierarchy of cuts."""
        hierarchy = {}
        
        for cut_id in egi.area.keys():
            parent = None
            if cut_id != egi.sheet:
                try:
                    parent = egi.get_context(cut_id)
                except (ValueError, KeyError):
                    # Cut not in a context, treat as top-level
                    parent = None
            
            hierarchy[cut_id] = {
                'parent': parent,
                'children': []
            }
        
        # Populate children
        for cut_id, info in hierarchy.items():
            if info['parent'] and info['parent'] in hierarchy:
                hierarchy[info['parent']]['children'].append(cut_id)
        
        return hierarchy
    
    def _layout_cut_content(self, egi: RelationalGraphWithCuts, cut_id: str, hierarchy: Dict):
        """Layout content within a single cut using d3-force with pinned ports."""
        # Build local graph for this cut
        local_graph = self._build_local_graph(egi, cut_id)
        
        # Add pinned port nodes
        ports_for_cut = [p for p in self.port_nodes.values() if p.cut_id == cut_id]
        for port in ports_for_cut:
            local_graph['nodes'].append({
                'id': port.id,
                'type': 'port',
                'fx': port.position[0],  # Fixed x
                'fy': port.position[1],  # Fixed y
            })
        
        # Add edges connecting content to ports
        for port in ports_for_cut:
            for ligature_id in port.ligatures:
                # Parse ligature_id (format: "vertex_id_edge_id")
                parts = ligature_id.split('_', 2)
                if len(parts) >= 3:
                    vertex_id = f"{parts[0]}_{parts[1]}"
                    edge_id = f"{parts[2]}_{parts[3]}" if len(parts) > 3 else parts[2]
                    
                    # Add edge from vertex/edge to port
                    if vertex_id in egi.area[cut_id]:
                        local_graph['edges'].append({
                            'source': vertex_id,
                            'target': port.id
                        })
                    if edge_id in egi.area[cut_id]:
                        local_graph['edges'].append({
                            'source': edge_id,
                            'target': port.id
                        })
        
        # Execute constrained micro-layout
        layout_result = self._run_d3_micro_layout(local_graph, cut_id)
        
        # Get cut dimensions for coordinate transform (BEFORE updating size)
        cut_pos = self.cut_positions.get(cut_id, (400, 300))
        original_cut_size = self.cut_sizes.get(cut_id, (200, 150))
        
        # Ensure we have valid sizes
        if original_cut_size is None or original_cut_size[0] is None or original_cut_size[1] is None:
            original_cut_size = (200, 150)
        
        # Update cut size based on actual bounding box first
        if 'bbox' in layout_result:
            bbox = layout_result['bbox']
            actual_width = bbox.get('width', 200)
            actual_height = bbox.get('height', 150)
            
            # Ensure valid dimensions
            if actual_width is None or actual_width <= 0:
                actual_width = 200
            if actual_height is None or actual_height <= 0:
                actual_height = 150
                
            self.cut_sizes[cut_id] = (actual_width, actual_height)
        
        # Cut rect in global space (using ACTUAL size from bbox)
        final_cut_size = self.cut_sizes.get(cut_id, (200, 150))
        if final_cut_size is None or final_cut_size[0] is None or final_cut_size[1] is None:
            final_cut_size = (200, 150)
            
        cut_global_x = cut_pos[0] - final_cut_size[0]/2
        cut_global_y = cut_pos[1] - final_cut_size[1]/2
        
        # Store element positions (transformed to global)
        for node in layout_result['nodes']:
            if node['type'] == 'port':
                # Don't store port positions (already fixed)
                continue
            elif node['type'] == 'child_cut':
                # Update child cut position - it's now positioned relative to parent
                if 'bbox' in layout_result:
                    global_x = cut_global_x + node['x'] - layout_result['bbox']['x']
                    global_y = cut_global_y + node['y'] - layout_result['bbox']['y']
                else:
                    global_x = cut_global_x + node['x']
                    global_y = cut_global_y + node['y']
                
                # Store the child cut's new position
                self.cut_positions[node['id']] = (global_x, global_y)
                # Size already set from bottom-up recursion
            else:
                # Regular elements (vertices, edge labels)
                if 'bbox' in layout_result:
                    global_x = cut_global_x + node['x'] - layout_result['bbox']['x']
                    global_y = cut_global_y + node['y'] - layout_result['bbox']['y']
                else:
                    global_x = cut_global_x + node['x']
                    global_y = cut_global_y + node['y']
                self.element_positions[node['id']] = (global_x, global_y)
    
    def _build_local_graph(self, egi: RelationalGraphWithCuts, cut_id: str) -> Dict:
        """Build local graph for content within a cut, including child cuts."""
        nodes = []
        edges = []
        
        # Get hierarchy to find child cuts
        hierarchy = self._build_cut_hierarchy(egi)
        child_cuts = hierarchy.get(cut_id, {}).get('children', [])
        
        # Add child cuts as large nodes (they act as obstacles)
        for child_cut_id in child_cuts:
            # Child cuts need size info
            child_size = self.cut_sizes.get(child_cut_id, (100, 80))
            nodes.append({
                'id': child_cut_id,
                'type': 'child_cut',
                'width': child_size[0],
                'height': child_size[1]
            })
        
        # Add vertices in this cut
        for vertex_id in egi.area[cut_id]:
            if vertex_id.startswith('v_'):
                nodes.append({
                    'id': vertex_id,
                    'type': 'vertex'
                })
        
        # Add edge labels in this cut
        for edge_id in egi.area[cut_id]:
            if edge_id.startswith('e_'):
                nodes.append({
                    'id': edge_id,
                    'type': 'edge_label',
                    'label': egi.rel[edge_id]
                })
        
        # Add internal ligatures (both endpoints in this cut)
        for edge_id, vertices in egi.nu.items():
            if edge_id in egi.area[cut_id]:
                for vertex_id in vertices:
                    if vertex_id in egi.area[cut_id]:
                        edges.append({
                            'source': vertex_id,
                            'target': edge_id
                        })
        
        return {'nodes': nodes, 'edges': edges}
    
    def _run_d3_micro_layout(self, local_graph: Dict, cut_id: str) -> Dict:
        """Execute constrained d3-force micro-layout via Node.js."""
        cut_size = self.cut_sizes[cut_id]
        
        input_data = {
            'type': 'micro_layout',
            'graph': local_graph,
            'config': {
                'width': cut_size[0],
                'height': cut_size[1],
                'iterations': 200,
                'containment': True
            }
        }
        
        result = subprocess.run(
            ['node', str(self.bridge_script)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"D3 micro-layout failed: {result.stderr}")
        
        return json.loads(result.stdout)
    
    def _route_ligature_through_ports(self, egi: RelationalGraphWithCuts, 
                                     vertex_id: str, edge_id: str, dto: LayoutDTO) -> List[Tuple[float, float]]:
        """
        Route ligature from vertex to edge label, segmented at port nodes.
        
        Path structure:
        - If same cut: direct path vertex -> edge
        - If different cuts: vertex -> port_a -> port_b -> edge
        """
        # Find which cuts the elements are in
        vertex_cut = self._get_cut_for_element(egi, vertex_id)
        edge_cut = self._get_cut_for_element(egi, edge_id)
        
        if vertex_cut == edge_cut:
            # Internal ligature - direct path
            return self._route_internal_path(vertex_id, edge_id, dto)
        else:
            # Spanning ligature - route through ports
            return self._route_spanning_path(vertex_id, edge_id, dto)
    
    def _get_cut_for_element(self, egi: Optional[RelationalGraphWithCuts], element_id: str) -> str:
        """Find which cut contains an element (uses cache)."""
        cut = self.element_to_cut.get(element_id)
        if cut:
            return cut
        # If not in cache and we have egi, search for it
        if egi:
            for cut_id, elements in egi.area.items():
                if element_id in elements:
                    self.element_to_cut[element_id] = cut_id
                    return cut_id
            return egi.sheet
        return 'sheet'  # Fallback
    
    def _route_internal_path(self, vertex_id: str, edge_id: str, dto: LayoutDTO) -> List[Tuple[float, float]]:
        """Route path for ligature within same cut using direct line."""
        # For now: simple direct path
        # TODO: Use A* pathfinding for obstacle avoidance
        
        vertex_pos = self.element_positions.get(vertex_id)
        edge_pos = self.element_positions.get(edge_id)
        
        if not vertex_pos or not edge_pos:
            return []
        
        return [vertex_pos, edge_pos]
    
    def _route_spanning_path(self, vertex_id: str, edge_id: str, dto: LayoutDTO) -> List[Tuple[float, float]]:
        """Route path for ligature spanning cuts, segmented at ports."""
        # Find the relevant port nodes
        ligature_key = f"{vertex_id}_{edge_id}"
        
        # Find ports for this ligature
        ports = [p for p in self.port_nodes.values() if ligature_key in p.ligatures]
        
        if len(ports) < 2:
            # Fallback to direct path
            return self._route_internal_path(vertex_id, edge_id, dto)
        
        # Build path segments: vertex -> port_a -> port_b -> edge
        path = []
        
        # Segment 1: vertex to its port
        vertex_pos = self.element_positions.get(vertex_id)
        if vertex_pos:
            path.append(vertex_pos)
            
            # Find port in vertex's cut
            vertex_cut = self._get_cut_for_element(None, vertex_id)  # Will use cached
            vertex_port = next((p for p in ports if p.cut_id == vertex_cut), None)
            
            if vertex_port:
                path.append(vertex_port.position)
                
                # Segment 2: port to port (boundary crossing)
                edge_cut = self._get_cut_for_element(None, edge_id)
                edge_port = next((p for p in ports if p.cut_id == edge_cut), None)
                
                if edge_port:
                    path.append(edge_port.position)
                    
                    # Segment 3: port to edge
                    edge_pos = self.element_positions.get(edge_id)
                    if edge_pos:
                        path.append(edge_pos)
        
        return path if len(path) >= 2 else []
