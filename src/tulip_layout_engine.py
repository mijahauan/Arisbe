"""
Tulip Layout Engine for EGI with Compound Graph Support

Translates EGI to Tulip compound graph:
- Vertices → Tulip nodes (is_predicate=False)
- Edge labels → Tulip predicate nodes (is_predicate=True)  
- Nu mapping → Binary edges with hook_index property
- Areas → Tulip meta-nodes (containment hierarchy)

Tulip optimizes node positions with hierarchical layout.
Final ligature routing done with area-aware A* pathfinding.
"""

from typing import Dict, Tuple, Optional
from pathlib import Path

try:
    # tulip-python package structure: import tulip, then use tulip.tlp
    import tulip
    tlp = tulip.tlp
    # Check if it's the right tulip (graph visualization)
    if not hasattr(tlp, 'newGraph'):
        raise ImportError("Wrong tulip package (temporal logic, not graph viz)")
    TULIP_AVAILABLE = True
except (ImportError, AttributeError) as e:
    TULIP_AVAILABLE = False
    tlp = None

from egi_core_dau import RelationalGraphWithCuts
from constrained_force_layout import Rect


class TulipLayoutEngine:
    """
    Layout engine using Tulip's hierarchical graph layout.
    
    Key insight: N-ary relations modeled as "predicate nodes" connected
    to argument vertices via binary edges with hook indices.
    """
    
    def __init__(self):
        if not TULIP_AVAILABLE:
            raise RuntimeError(
                "Tulip graph visualization library not available.\n"
                "Note: A different 'tulip' package (temporal logic) may be installed.\n"
                "To use Tulip layout, uninstall temporal tulip and install graph tulip:\n"
                "  pip uninstall tulip\n"
                "  pip install tulip-python\n"
                "Falling back to alternative layout engine."
            )
        
        self.graph = None
        self.egi_to_tulip = {}  # EGI element ID → Tulip node
        self.tulip_to_egi = {}  # Tulip node → EGI element ID
        self.meta_nodes = {}    # Area ID → Tulip meta-node
    
    def generate_layout(self, egi: RelationalGraphWithCuts, hierarchy: Dict,
                       area_bounds: Dict, algorithm: str = "Hierarchical Graph") -> Tuple[Dict, Dict]:
        """
        Generate layout using Tulip nested graph hierarchy.
        
        Key insight: Cuts are subgraphs that appear as nodes in their parent.
        
        Args:
            egi: The EGI structure
            hierarchy: Area hierarchy (for reference)
            area_bounds: Initial area size hints
            algorithm: Tulip layout algorithm name
            
        Returns:
            (global_positions, area_bounds) compatible with existing pipeline
        """
        # Create main Tulip graph (represents the Sheet)
        self.graph = tlp.newGraph()
        
        # Add properties (these are inherited by subgraphs)
        is_predicate = self.graph.getBooleanProperty("is_predicate")
        hook_index = self.graph.getIntegerProperty("hook_index")
        area_id_prop = self.graph.getStringProperty("area_id")
        label_prop = self.graph.getStringProperty("viewLabel")
        size_prop = self.graph.getSizeProperty("viewSize")
        
        # Map area IDs to their graphs (Sheet → main graph, Cuts → subgraphs)
        area_graphs = {egi.sheet: self.graph}
        
        # Step 1: Create subgraphs for cuts (hierarchically)
        def create_subgraphs_recursive(area_id, parent_graph):
            """Recursively create subgraphs for nested cuts"""
            for child_id in hierarchy[area_id]['children']:
                # Create subgraph for this cut
                # The subgraph itself represents the cut as a container
                subgraph = parent_graph.addSubGraph()
                area_graphs[child_id] = subgraph
                
                # Recursively create subgraphs for nested cuts
                create_subgraphs_recursive(child_id, subgraph)
        
        create_subgraphs_recursive(egi.sheet, self.graph)
        
        # Step 2: Create vertex nodes in their appropriate subgraph
        for area_id, elements in egi.area.items():
            # Get the graph for this area (main graph or subgraph)
            target_graph = area_graphs.get(area_id, self.graph)
            
            for elem_id in elements:
                # Skip cuts (they're subgraphs, not nodes)
                if elem_id in egi.area:
                    continue
                
                # Check if it's a vertex
                if elem_id not in egi.nu:
                    node = target_graph.addNode()
                    self.egi_to_tulip[elem_id] = node
                    self.tulip_to_egi[node] = elem_id
                    
                    is_predicate[node] = False
                    area_id_prop[node] = area_id
                    label_prop[node] = f"*{elem_id[:4]}"  # Vertex marker
                    size_prop[node] = tlp.Size(6, 6, 1)
                    
        
        # Step 3: Create predicate nodes (edge labels) in their appropriate subgraph
        for edge_id in egi.nu.keys():
            # Find which area this edge is in
            edge_area = None
            for area_id, elements in egi.area.items():
                if edge_id in elements:
                    edge_area = area_id
                    break
            
            if not edge_area:
                continue  # Skip if edge not assigned to any area
            
            # Get the graph for this area
            target_graph = area_graphs.get(edge_area, self.graph)
            
            node = target_graph.addNode()
            self.egi_to_tulip[edge_id] = node
            self.tulip_to_egi[node] = edge_id
            
            is_predicate[node] = True
            label = egi.rel.get(edge_id, "?")
            label_prop[node] = label
            
            # Size based on label length
            width = max(20, len(label) * 8)
            size_prop[node] = tlp.Size(width, 12, 1)
            
            area_id_prop[node] = edge_area
        
        # Step 4: Create binary edges from predicate nodes to vertices
        for edge_id, vertex_sequence in egi.nu.items():
            predicate_node = self.egi_to_tulip[edge_id]
            
            for k, vertex_id in enumerate(vertex_sequence, start=1):
                if vertex_id in self.egi_to_tulip:
                    vertex_node = self.egi_to_tulip[vertex_id]
                    
                    # Create binary edge
                    tulip_edge = self.graph.addEdge(predicate_node, vertex_node)
                    
                    # Store hook index
                    hook_index[tulip_edge] = k
        
        # Step 5: BOTTOM-UP LAYOUT PASS
        # Layout each subgraph independently, then use their sizes in parent layout
        
        # Map each graph to its layout property
        layout_props = {}
        
        # Recursive bottom-up layout
        def layout_subgraph_bottomup(graph_id, graph_obj):
            """Layout a subgraph and all its children (leaves first)"""
            
            # Create dedicated layout property for this graph
            layout_props[graph_id] = graph_obj.getLayoutProperty(f"layout_{graph_id}")
            
            # First, recursively layout all children
            for child_id in hierarchy[graph_id]['children']:
                if child_id in area_graphs:
                    child_graph = area_graphs[child_id]
                    layout_subgraph_bottomup(child_id, child_graph)
                    
                    # After child is laid out, calculate its bounding box
                    child_layout = layout_props[child_id]
                    child_nodes = list(child_graph.getNodes())
                    
                    if child_nodes:
                        min_x = min(child_layout[n].x() for n in child_nodes) if child_nodes else 0
                        max_x = max(child_layout[n].x() for n in child_nodes) if child_nodes else 100
                        min_y = min(child_layout[n].y() for n in child_nodes) if child_nodes else 0
                        max_y = max(child_layout[n].y() for n in child_nodes) if child_nodes else 100
                        
                        width = max_x - min_x + 40  # padding
                        height = max_y - min_y + 40
                        
                        # In parent's layout, set size for this subgraph's meta-node
                        # (The subgraph appears as a node in parent)
                        size_prop[child_graph] = tlp.Size(width, height, 1)
            
            # Now layout THIS graph's direct contents
            my_layout = layout_props[graph_id]
            params = tlp.getDefaultPluginParameters('GEM (Frick)')
            graph_obj.applyLayoutAlgorithm('GEM (Frick)', my_layout, params)
        
        # Start bottom-up traversal from sheet
        layout_subgraph_bottomup(egi.sheet, self.graph)
        
        # Use the root graph's layout as the final layout
        layout_prop = layout_props[egi.sheet]
        
        # Step 6: Extract positions
        global_positions = {'vertices': {}, 'edge_labels': {}}
        
        for tulip_node in self.graph.getNodes():
            if tulip_node in self.tulip_to_egi:
                egi_id = self.tulip_to_egi[tulip_node]
                pos = layout_prop[tulip_node]
                area = area_id_prop[tulip_node]
                
                if is_predicate[tulip_node]:
                    # It's an edge label
                    label = label_prop[tulip_node]
                    size = size_prop[tulip_node]
                    
                    global_positions['edge_labels'][egi_id] = {
                        'x': pos.x(),
                        'y': pos.y(),
                        'width': size.width(),
                        'height': size.height(),
                        'label': label,
                        'parent_area_id': area
                    }
                else:
                    # It's a vertex
                    global_positions['vertices'][egi_id] = {
                        'x': pos.x(),
                        'y': pos.y(),
                        'parent_area_id': area
                    }
        
        # Step 7: Calculate area bounds from element positions
        calculated_bounds = self._calculate_bounds_from_positions(
            global_positions, hierarchy, egi
        )
        
        return global_positions, calculated_bounds
    
    def _calculate_bounds_from_positions(self, global_positions: Dict, 
                                        hierarchy: Dict, egi: RelationalGraphWithCuts) -> Dict:
        """Calculate tight area bounds from element positions"""
        area_bounds = {}
        
        # For each area, find bounding box of its elements
        for area_id, info in hierarchy.items():
            min_x = float('inf')
            max_x = float('-inf')
            min_y = float('inf')
            max_y = float('-inf')
            
            # Check vertices
            for v_id in info['vertices']:
                if v_id in global_positions['vertices']:
                    pos = global_positions['vertices'][v_id]
                    min_x = min(min_x, pos['x'] - 10)
                    max_x = max(max_x, pos['x'] + 10)
                    min_y = min(min_y, pos['y'] - 10)
                    max_y = max(max_y, pos['y'] + 10)
            
            # Check edges
            for e_id in info['edges']:
                if e_id in global_positions['edge_labels']:
                    pos = global_positions['edge_labels'][e_id]
                    min_x = min(min_x, pos['x'] - pos['width']/2)
                    max_x = max(max_x, pos['x'] + pos['width']/2)
                    min_y = min(min_y, pos['y'] - pos['height']/2)
                    max_y = max(max_y, pos['y'] + pos['height']/2)
            
            # Add child bounds
            for child_id in info['children']:
                if child_id in area_bounds:
                    child = area_bounds[child_id]
                    min_x = min(min_x, child.x)
                    max_x = max(max_x, child.x + child.width)
                    min_y = min(min_y, child.y)
                    max_y = max(max_y, child.y + child.height)
            
            if min_x != float('inf'):
                # Add margin
                margin = 20 if area_id == egi.sheet else 15
                area_bounds[area_id] = Rect(
                    min_x - margin,
                    min_y - margin,
                    (max_x - min_x) + 2 * margin,
                    (max_y - min_y) + 2 * margin
                )
            else:
                # Empty area
                area_bounds[area_id] = Rect(0, 0, 100, 100)
        
        return area_bounds
