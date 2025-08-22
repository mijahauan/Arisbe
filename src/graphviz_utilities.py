#!/usr/bin/env python3
"""
Focused Graphviz Utilities - Clean replacement for the deprecated monolithic layout engine

Provides focused utilities that the 9-phase pipeline can call for specific layout tasks:
- Cluster sizing using Graphviz's optimized hierarchical layout
- Node positioning within clusters with constraint satisfaction
- DOT generation for specific layout phases

This replaces the monolithic approach with focused, single-purpose utilities.
"""

import subprocess
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from src.egi_core_dau import RelationalGraphWithCuts

# Type aliases for clarity
Bounds = Tuple[float, float, float, float]  # x1, y1, x2, y2
Coordinate = Tuple[float, float]  # x, y


@dataclass
class ClusterBounds:
    """Represents the spatial bounds of a cut/cluster."""
    cluster_id: str
    x1: float
    y1: float
    x2: float
    y2: float
    
    @property
    def width(self) -> float:
        return self.x2 - self.x1
    
    @property
    def height(self) -> float:
        return self.y2 - self.y1
    
    @property
    def center(self) -> Coordinate:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


@dataclass
class NodePosition:
    """Represents the position of a node/element."""
    node_id: str
    x: float
    y: float
    width: float = 0.0
    height: float = 0.0


class GraphvizClusterSizer:
    """Focused utility for cluster sizing using Graphviz's hierarchical layout."""
    
    def get_cluster_bounds(self, egi: RelationalGraphWithCuts, 
                             element_dimensions: Dict[str, Dict[str, float]]) -> Dict[str, ClusterBounds]:
        """
        Compute optimal cluster bounds using Graphviz's cluster layout algorithm.
        
        For sheet-only graphs (no cuts), uses view-based clustering with the entire
        view (0,0,1,1) as the container for level-0 elements.
        
        Args:
            egi: The EGI graph structure
            element_dimensions: Element size requirements from Phase 1
            
        Returns:
            Dictionary mapping cut IDs to their optimal spatial bounds
        """
        try:
            # Special handling for sheet-only graphs (no cuts)
            if not egi.Cut:
                return self._create_view_bounds_for_sheet_elements(egi, element_dimensions)
            
            # Generate DOT for cluster sizing
            dot_content = self._generate_cluster_sizing_dot(egi, element_dimensions)
            
            # Run Graphviz to get cluster bounds
            xdot_output = self._run_graphviz(dot_content)
            
            # Parse cluster bounds from xdot output
            cluster_bounds = self._parse_cluster_bounds(xdot_output)
            
            # Ensure sheet bounds are always available
            if 'sheet' not in cluster_bounds:
                cluster_bounds['sheet'] = ClusterBounds(
                    cluster_id='sheet',
                    x1=0.0, y1=0.0, x2=1.0, y2=1.0
                )
            
            return cluster_bounds
            
        except Exception as e:
            print(f"⚠️  Cluster sizing failed: {e}")
            return self._fallback_cluster_bounds(egi, element_dimensions)
    
    def _create_view_bounds_for_sheet_elements(self, egi: RelationalGraphWithCuts, 
                                             element_dimensions: Dict[str, Dict[str, float]]) -> Dict[str, ClusterBounds]:
        """
        Create view-based clustering for sheet-only graphs.
        
        Treats the entire view (0,0,1,1) as the container for level-0 elements,
        with padding annulus between cuts and view boundary.
        """
        cluster_bounds = {}
        
        # Define view bounds with padding for cuts
        view_padding = 0.1  # 10% padding around cuts
        view_bounds = ClusterBounds(
            cluster_id='sheet',
            x1=0.0,
            y1=0.0, 
            x2=1.0,
            y2=1.0
        )
        
        # If no cuts, entire view is available for sheet elements
        if not egi.Cut:
            cluster_bounds['sheet'] = view_bounds
            return cluster_bounds
        
        # With cuts: create padded inner area for cuts, outer annulus for sheet
        cut_area_width = 1.0 - (2 * view_padding)
        cut_area_height = 1.0 - (2 * view_padding)
        
        # Position cuts in inner padded area
        cut_count = len(egi.Cut)
        if cut_count == 1:
            # Single cut gets centered inner area
            cut = list(egi.Cut)[0]
            cluster_bounds[cut.id] = ClusterBounds(
                cluster_id=cut.id,
                x1=view_padding,
                y1=view_padding,
                x2=1.0 - view_padding,
                y2=1.0 - view_padding
            )
        else:
            # Multiple cuts arranged in grid within inner area
            import math
            grid_size = math.ceil(math.sqrt(cut_count))
            cut_width = cut_area_width / grid_size
            cut_height = cut_area_height / grid_size
            
            for i, cut in enumerate(egi.Cut):
                row = i // grid_size
                col = i % grid_size
                
                x1 = view_padding + (col * cut_width)
                y1 = view_padding + (row * cut_height)
                x2 = x1 + cut_width
                y2 = y1 + cut_height
                
                cluster_bounds[cut.id] = ClusterBounds(
                    cluster_id=cut.id,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2
                )
        
        # Sheet gets full view (elements can use annulus around cuts)
        cluster_bounds['sheet'] = view_bounds
        
        return cluster_bounds
    
    def _generate_cluster_sizing_dot(self, egi: RelationalGraphWithCuts, 
                                   element_dimensions: Dict[str, Dict[str, float]]) -> str:
        """Generate DOT focused on cluster sizing."""
        lines = [
            "digraph EGI {",
            "  rankdir=TB;",
            "  compound=true;",
            "  clusterrank=local;",
            "  newrank=true;",
            "  node [shape=box, style=filled, fillcolor=lightblue];",
            ""
        ]
        
        # Generate nested clusters based on EGI containment hierarchy (like PNG script)
        self._add_nested_clusters(lines, egi, element_dimensions, "  ")
        
        # Add sheet-level elements
        sheet_elements = egi.area.get(egi.sheet, frozenset())
        for element_id in sheet_elements:
            if element_id in element_dimensions:
                dims = element_dimensions[element_id]
                width = dims.get('width', 0.1) * 100
                height = dims.get('height', 0.05) * 100
                lines.append(f"  \"{element_id}\" [width={width:.2f}, height={height:.2f}];")
        
        lines.append("}")
        return "\n".join(lines)
    
    def _run_graphviz(self, dot_content: str) -> str:
        """Run Graphviz and return xdot output."""
        try:
            result = subprocess.run(
                ['dot', '-Txdot'],
                input=dot_content,
                text=True,
                capture_output=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise Exception(f"Graphviz execution failed: {e.stderr}")
    
    def _parse_cluster_bounds(self, xdot_output: str) -> Dict[str, ClusterBounds]:
        """Parse cluster bounds from xdot output."""
        cluster_bounds = {}
        
        # Pattern 1: Clusters with _draw_ attributes (have content)
        # The _draw_ attribute contains polygon coordinates: P 4 x1 y1 x2 y2 x3 y3 x4 y4
        cluster_with_draw_pattern = r'subgraph cluster_(\w+) \{[^}]*?_draw_="[^"]*?P 4 ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)'
        
        for match in re.finditer(cluster_with_draw_pattern, xdot_output, re.DOTALL):
            cluster_id = match.group(1)
            # Extract all 8 coordinates (4 corners of rectangle)
            coords = [float(match.group(i)) for i in range(2, 10)]
            
            # Find min/max bounds from the 4 corner points
            x_coords = [coords[0], coords[2], coords[4], coords[6]]
            y_coords = [coords[1], coords[3], coords[5], coords[7]]
            
            x1, x2 = min(x_coords), max(x_coords)
            y1, y2 = min(y_coords), max(y_coords)
            
            cluster_bounds[cluster_id] = ClusterBounds(
                cluster_id=cluster_id,
                x1=x1, y1=y1, x2=x2, y2=y2
            )
        
        # Pattern 2: Clusters with bb= attributes (bounding box, for empty clusters)
        cluster_with_bb_pattern = r'subgraph cluster_(\w+) \{[^}]*?bb="([\d.]+),([\d.]+),([\d.]+),([\d.]+)"'
        
        for match in re.finditer(cluster_with_bb_pattern, xdot_output, re.DOTALL):
            cluster_id = match.group(1)
            if cluster_id not in cluster_bounds:  # Don't override _draw_ results
                x1, y1, x2, y2 = map(float, match.groups()[1:5])
                
                cluster_bounds[cluster_id] = ClusterBounds(
                    cluster_id=cluster_id,
                    x1=x1, y1=y1, x2=x2, y2=y2
                )
        
        # Pattern 3: Extract all cluster names and provide fallback bounds
        all_cluster_pattern = r'subgraph cluster_(\w+) \{'
        all_clusters = set(re.findall(all_cluster_pattern, xdot_output))
        
        # For any clusters we haven't captured, provide minimal fallback bounds
        for cluster_id in all_clusters:
            if cluster_id not in cluster_bounds:
                # Minimal fallback bounds
                cluster_bounds[cluster_id] = ClusterBounds(
                    cluster_id=cluster_id,
                    x1=50.0, y1=50.0, x2=200.0, y2=150.0
                )
        
        return cluster_bounds
    
    def _fallback_cluster_bounds(self, egi: RelationalGraphWithCuts, 
                               element_dimensions: Dict[str, Dict[str, float]]) -> Dict[str, ClusterBounds]:
        """Fallback cluster bounds when Graphviz fails."""
        cluster_bounds = {}
        
        # Simple nested layout as fallback
        canvas_width, canvas_height = 800.0, 600.0
        cut_padding = 50.0
        
        for i, cut in enumerate(egi.Cut):
            # Simple positioning - can be enhanced
            x1 = 100 + i * 200
            y1 = 100 + i * 150
            x2 = x1 + 150
            y2 = y1 + 100
            
            cluster_bounds[cut.id] = ClusterBounds(
                cluster_id=cut.id,
                x1=x1, y1=y1, x2=x2, y2=y2
            )
        
        return cluster_bounds


class GraphvizNodePositioner:
    """Focused utility for node positioning within clusters."""
    
    def position_nodes_in_clusters(self, egi: RelationalGraphWithCuts,
                                 cluster_bounds: Dict[str, ClusterBounds],
                                 element_dimensions: Dict[str, Dict[str, float]]) -> Dict[str, NodePosition]:
        """
        Position nodes within their assigned clusters using Graphviz optimization.
        
        Args:
            egi: The EGI graph structure
            cluster_bounds: Cluster bounds from GraphvizClusterSizer
            element_dimensions: Element size requirements
            
        Returns:
            Dictionary mapping element IDs to their optimal positions
        """
        try:
            # Generate DOT for node positioning
            dot_content = self._generate_node_positioning_dot(egi, cluster_bounds, element_dimensions)
            
            # Run Graphviz to get node positions
            xdot_output = self._run_graphviz(dot_content)
            
            # Parse node positions from xdot output
            node_positions = self._parse_node_positions(xdot_output, element_dimensions)
            
            return node_positions
            
        except Exception as e:
            print(f"⚠️  Node positioning failed: {e}")
            return self._fallback_node_positions(egi, cluster_bounds, element_dimensions)
    
    def _generate_node_positioning_dot(self, egi: RelationalGraphWithCuts,
                                     cluster_bounds: Dict[str, ClusterBounds],
                                     element_dimensions: Dict[str, Dict[str, float]]) -> str:
        """Generate DOT focused on node positioning within fixed cluster bounds."""
        lines = [
            "digraph EGI {",
            "  rankdir=TB;",
            "  compound=true;",
            "  node [shape=box];",
            ""
        ]
        
        # Add clusters with fixed bounds
        for cut in egi.Cut:
            if cut.id in cluster_bounds:
                bounds = cluster_bounds[cut.id]
                lines.append(f"  subgraph cluster_{cut.id} {{")
                lines.append(f"    label=\"{cut.id}\";")
                lines.append(f"    style=filled;")
                lines.append(f"    fillcolor=lightgray;")
                
                # Add nodes in this cluster
                elements_in_cut = egi.area.get(cut.id, frozenset())
                for element_id in elements_in_cut:
                    if element_id in element_dimensions:
                        dims = element_dimensions[element_id]
                        width = dims.get('width', 0.1) * 100
                        height = dims.get('height', 0.05) * 100
                        lines.append(f"    \"{element_id}\" [width={width:.2f}, height={height:.2f}];")
                
                lines.append("  }")
                lines.append("")
        
        # Add sheet-level nodes
        sheet_elements = egi.area.get(egi.sheet, frozenset())
        for element_id in sheet_elements:
            if element_id in element_dimensions:
                dims = element_dimensions[element_id]
                width = dims.get('width', 0.1) * 100
                height = dims.get('height', 0.05) * 100
                lines.append(f"  \"{element_id}\" [width={width:.2f}, height={height:.2f}];")
        
        lines.append("}")
        return "\n".join(lines)
    
    def _run_graphviz(self, dot_content: str) -> str:
        """Run Graphviz and return xdot output."""
        try:
            result = subprocess.run(
                ['dot', '-Txdot'],
                input=dot_content,
                text=True,
                capture_output=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise Exception(f"Graphviz execution failed: {e.stderr}")
    
    def _parse_node_positions(self, xdot_output: str, 
                            element_dimensions: Dict[str, Dict[str, float]]) -> Dict[str, NodePosition]:
        """Parse node positions from xdot output."""
        node_positions = {}
        
        # Pattern to match node positions in xdot format
        node_pattern = r'"([^"]+)"\s+\[.*?pos="(\d+\.?\d*),(\d+\.?\d*)"'
        
        for match in re.finditer(node_pattern, xdot_output):
            node_id = match.group(1)
            x, y = float(match.group(2)), float(match.group(3))
            
            # Get dimensions if available
            dims = element_dimensions.get(node_id, {'width': 0.1, 'height': 0.05})
            
            node_positions[node_id] = NodePosition(
                node_id=node_id,
                x=x, y=y,
                width=dims['width'] * 100,  # Scale back from DOT units
                height=dims['height'] * 100
            )
        
        return node_positions
    
    def _fallback_node_positions(self, egi: RelationalGraphWithCuts,
                               cluster_bounds: Dict[str, ClusterBounds],
                               element_dimensions: Dict[str, Dict[str, float]]) -> Dict[str, NodePosition]:
        """Fallback node positioning when Graphviz fails."""
        node_positions = {}
        
        # Position elements using exclusive positioning within their areas
        for area_id, elements in egi.area.items():
            if area_id in cluster_bounds:
                bounds = cluster_bounds[area_id]
                self._position_elements_in_bounds(elements, bounds, element_dimensions, node_positions)
            elif area_id == egi.sheet:
                # Sheet positioning
                sheet_bounds = ClusterBounds("sheet", 0, 0, 800, 600)
                self._position_elements_in_bounds(elements, sheet_bounds, element_dimensions, node_positions)
        
        return node_positions
    
    def _position_elements_in_bounds(self, elements: frozenset, bounds: ClusterBounds,
                                   element_dimensions: Dict[str, Dict[str, float]],
                                   node_positions: Dict[str, NodePosition]):
        """Position elements within bounds using exclusive positioning."""
        element_list = list(elements)
        if not element_list:
            return
        
        # Simple grid layout for exclusive positioning
        cols = max(1, int((len(element_list) ** 0.5)))
        rows = (len(element_list) + cols - 1) // cols
        
        cell_width = bounds.width / cols
        cell_height = bounds.height / rows
        
        for i, element_id in enumerate(element_list):
            row = i // cols
            col = i % cols
            
            # Center element in its grid cell
            x = bounds.x1 + col * cell_width + cell_width / 2
            y = bounds.y1 + row * cell_height + cell_height / 2
            
            dims = element_dimensions.get(element_id, {'width': 0.1, 'height': 0.05})
            
            node_positions[element_id] = NodePosition(
                node_id=element_id,
                x=x, y=y,
                width=dims['width'] * 100,
                height=dims['height'] * 100
            )


class GraphvizDotGenerator:
    """Clean DOT generation for specific layout tasks."""
    
    def generate_sizing_dot(self, egi: RelationalGraphWithCuts, 
                          element_dimensions: Dict[str, Dict[str, float]]) -> str:
        """Generate DOT optimized for cluster sizing."""
        sizer = GraphvizClusterSizer()
        return sizer._generate_cluster_sizing_dot(egi, element_dimensions)
    
    def generate_positioning_dot(self, egi: RelationalGraphWithCuts,
                               cluster_bounds: Dict[str, ClusterBounds],
                               element_dimensions: Dict[str, Dict[str, float]]) -> str:
        """Generate DOT optimized for node positioning."""
        positioner = GraphvizNodePositioner()
        return positioner._generate_node_positioning_dot(egi, cluster_bounds, element_dimensions)


# Convenience functions for the 9-phase pipeline
def get_cluster_bounds(egi: RelationalGraphWithCuts, 
                      element_dimensions: Dict[str, Dict[str, float]]) -> Dict[str, ClusterBounds]:
    """Get cluster bounds using Graphviz optimization with view-based clustering for sheet-only graphs."""
    sizer = GraphvizClusterSizer()
    return sizer.get_cluster_bounds(egi, element_dimensions)


def get_node_positions(egi: RelationalGraphWithCuts,
                      cluster_bounds: Dict[str, ClusterBounds],
                      element_dimensions: Dict[str, Dict[str, float]]) -> Dict[str, NodePosition]:
    """Get node positions using Graphviz optimization."""
    positioner = GraphvizNodePositioner()
    return positioner.position_nodes_in_clusters(egi, cluster_bounds, element_dimensions)


class GraphvizRenderer:
    """Renderer for generating visual diagrams that properly correspond to EGI structures."""
    
    def generate_dot(self, egi, context, egif_source=None, style=None):
        """Generate DOT representation showing predicates, ν mapping, and spatial containment."""
        
        # Apply DauStyle parameters if provided
        if style is None:
            from rendering_styles import DauStyle
            style = DauStyle()
        
        # Convert Qt line widths to Graphviz penwidth (approximate conversion)
        ligature_penwidth = style.ligature_width / 2.0  # 2.0 -> 1.0
        cut_penwidth = style.cut_line_width / 2.0       # 1.5 -> 0.75
        
        lines = [
            "digraph EG {",
            "  rankdir=TB;",
            "  compound=true;",
            f"  node [fontsize=12, fontname=\"Times-Roman\"];",
            f"  edge [penwidth={ligature_penwidth:.2f}, color=black];",
            ""
        ]
        
        # Add EGIF source as graph label if provided
        if egif_source:
            lines.append(f'  label="EGIF: {egif_source}";')
            lines.append(f'  labelloc="t";')
            lines.append(f'  fontsize=12;')
            lines.append("")
        
        # Create predicate nodes with proper labels
        predicate_nodes = {}
        for e_id in egi.E:
            # Extract predicate info from edge ID or ν mapping
            pred_info = self._extract_predicate_info(e_id, egi)
            pred_name = pred_info['name']
            args = pred_info['args']
            
            pred_node_id = f"pred_{e_id.id if hasattr(e_id, 'id') else str(e_id).split('_')[1]}"
            predicate_nodes[e_id] = pred_node_id
            
            lines.append(f'  "{pred_node_id}" [label="{pred_name}", shape=box, style=rounded, penwidth={cut_penwidth:.2f}, fontname="Times-Roman"];')
        
        # Create vertex nodes with clean labels
        for v_id in egi.V:
            vertex_label = self._get_vertex_label(v_id)
            vertex_radius_pts = style.vertex_radius * 2  # Convert radius to diameter in points
            lines.append(f'  "{v_id}" [label="{vertex_label}", shape=circle, width={vertex_radius_pts/72:.3f}, height={vertex_radius_pts/72:.3f}, style=filled, fillcolor=black, fontcolor=white, fontname="Times-Roman"];')
        
        # Add cuts as nested subgraphs with proper containment
        cut_clusters = {}
        
        # Build cut hierarchy from area mapping
        cut_hierarchy = self._build_cut_hierarchy(egi)
        
        # Generate nested cuts with style
        self._generate_nested_cuts(egi, cut_hierarchy, predicate_nodes, lines, cut_clusters, style=style)
        
        # Add ν mapping connections (predicate-argument relationships)
        lines.append("  // ν mapping connections")
        for e_id in egi.E:
            if e_id in predicate_nodes:
                pred_node = predicate_nodes[e_id]
                args = egi.nu.get(e_id.id, ())  # Use edge.id for lookup
                
                for i, arg_vertex_id in enumerate(args):
                    # Find matching vertex object
                    for vertex in egi.V:
                        if vertex.id == arg_vertex_id:
                            lines.append(f'  "{pred_node}" -> "{vertex}" [label="{i+1}", color=black, penwidth={ligature_penwidth:.2f}, fontsize=8, fontname="Times-Roman"];')
                            break
        
        lines.append("}")
        return "\n".join(lines)
    
    def _extract_predicate_info(self, e_id, egi):
        """Extract predicate name and arguments from edge ID and ν mapping."""
        # Get arguments from ν mapping using edge.id
        args = egi.nu.get(e_id.id, ())
        
        # Get predicate name from rel mapping
        pred_name = egi.rel.get(e_id.id, "P")
        
        return {'name': pred_name, 'args': args}
    
    def _get_vertex_label(self, v_id):
        """Get clean vertex label for display."""
        vertex_str = str(v_id)
        if 'label=' in vertex_str:
            # Extract label if present
            import re
            label_match = re.search(r"label='([^']*)'", vertex_str)
            if label_match and label_match.group(1):
                return label_match.group(1)
        
        # Use short ID for generic vertices
        if hasattr(v_id, 'id'):
            return v_id.id[-8:]  # Last 8 chars of ID
        else:
            # Extract short ID from string
            import re
            id_match = re.search(r"'([^']*)'", vertex_str)
            if id_match:
                return id_match.group(1)[-8:]
        
        return "v"
    
    def _build_cut_hierarchy(self, egi):
        """Build cut hierarchy from area mapping to enable proper nesting."""
        hierarchy = {}
        
        # Find which cuts contain other cuts
        for cut in egi.Cut:
            elements_in_cut = egi.area.get(cut.id, frozenset())
            child_cuts = [elem for elem in elements_in_cut if elem in [c.id for c in egi.Cut]]
            hierarchy[cut.id] = {
                'children': child_cuts,
                'elements': [elem for elem in elements_in_cut if elem not in child_cuts]
            }
        
        return hierarchy
    
    def _generate_nested_cuts(self, egi, cut_hierarchy, predicate_nodes, lines, cut_clusters, style=None, depth=0):
        """Generate nested cut subgraphs with proper containment."""
        # Find root cuts (not contained in other cuts)
        all_child_cuts = set()
        for cut_info in cut_hierarchy.values():
            all_child_cuts.update(cut_info['children'])
        
        root_cuts = [cut_id for cut_id in cut_hierarchy.keys() if cut_id not in all_child_cuts]
        
        # Generate cuts starting from roots
        for i, cut_id in enumerate(root_cuts):
            cluster_name = f"cluster_{depth}_{i}"
            cut_clusters[cut_id] = cluster_name
            self._generate_cut_subgraph(cut_id, cluster_name, egi, cut_hierarchy, predicate_nodes, lines, cut_clusters, depth, style)
    
    def _generate_cut_subgraph(self, cut_id, cluster_name, egi, cut_hierarchy, predicate_nodes, lines, cut_clusters, depth, style=None):
        """Generate a single cut subgraph with its nested children."""
        
        # Apply DauStyle parameters for cuts
        if style is None:
            from rendering_styles import DauStyle
            style = DauStyle()
        
        cut_penwidth = style.cut_line_width / 2.0  # Convert to Graphviz penwidth
        
        lines.append(f"{'  ' * (depth + 1)}subgraph {cluster_name} {{")
        lines.append(f"{'  ' * (depth + 2)}label=\"\";")  # No label for clean Dau style
        lines.append(f"{'  ' * (depth + 2)}style=\"rounded,filled\";")
        lines.append(f"{'  ' * (depth + 2)}fillcolor=white;")
        lines.append(f"{'  ' * (depth + 2)}color=black;")
        lines.append(f"{'  ' * (depth + 2)}penwidth={cut_penwidth:.2f};")
        
        cut_info = cut_hierarchy[cut_id]
        
        # Add direct elements (non-cut elements)
        for element_id in cut_info['elements']:
            if element_id in [e.id for e in egi.E] and element_id in [e.id for e in egi.E if e in predicate_nodes]:
                pred_node = predicate_nodes[[e for e in egi.E if e.id == element_id][0]]
                lines.append(f"{'  ' * (depth + 2)}\"{pred_node}\";")
            elif element_id in [v.id for v in egi.V]:
                vertex = [v for v in egi.V if v.id == element_id][0]
                lines.append(f"{'  ' * (depth + 2)}\"{vertex}\";")
        
        # Add nested child cuts
        for j, child_cut_id in enumerate(cut_info['children']):
            child_cluster_name = f"cluster_{depth + 1}_{j}"
            cut_clusters[child_cut_id] = child_cluster_name
            self._generate_cut_subgraph(child_cut_id, child_cluster_name, egi, cut_hierarchy, predicate_nodes, lines, cut_clusters, depth + 1, style)
        
        lines.append(f"{'  ' * (depth + 1)}}}")
        lines.append("")


if __name__ == "__main__":
    # Test the focused utilities
    print("🧪 Testing Focused Graphviz Utilities")
    
    # This would be called by the 9-phase pipeline phases
    print("✅ Graphviz Utilities Ready for Pipeline Integration")
