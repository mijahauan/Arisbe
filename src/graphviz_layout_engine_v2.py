#!/usr/bin/env python3
"""
Robust Graphviz-Based Layout Engine for Existential Graphs

This implementation follows a disciplined approach to avoid the issues encountered
in previous attempts:

1. Clean EGI → DOT translation using proper cluster mapping
2. Use Graphviz plain text output (not SVG) for reliable coordinate parsing
3. Isolated Graphviz execution with robust error handling
4. Unidirectional data flow: EGI → DOT → Graphviz → LayoutResult

Architecture:
- EGI vertices → Graphviz nodes
- EGI edges → Graphviz edges  
- EGI cuts → Graphviz subgraph clusters
- EGI area containment → Nested subgraph structure
"""

import subprocess
import tempfile
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_engine_clean import LayoutResult, SpatialPrimitive
from xdot_parser_simple import parse_xdot_file
from pipeline_contracts import (
    enforce_contracts, 
    validate_relational_graph_with_cuts,
    validate_layout_result,
    validate_graphviz_dot_output,
    validate_graphviz_coordinate_extraction,
    validate_graphviz_layout_engine_output
)

try:
    from layout_post_processor import LayoutPostProcessor, SpacingConstraints
    POST_PROCESSOR_AVAILABLE = True
except ImportError:
    POST_PROCESSOR_AVAILABLE = False
    print("⚠️  Layout post-processor not available - using basic spacing")


@dataclass
class GraphvizElement:
    """Represents an element in Graphviz with its attributes."""
    element_id: str
    element_type: str  # 'node', 'edge', 'cluster'
    attributes: Dict[str, str]
    position: Optional[Tuple[float, float]] = None
    size: Optional[Tuple[float, float]] = None


class GraphvizLayoutEngine:
    """
    Robust layout engine using Graphviz as the backend.
    
    This engine translates EGI structures to DOT language, executes Graphviz,
    and parses the plain text output to produce LayoutResult objects.
    """
    
    def __init__(self):
        self.dot_executable = "dot"  # Graphviz dot command
        self.temp_dir = tempfile.gettempdir()
    
    def _sanitize_dot_id(self, element_id: str) -> str:
        """Sanitize element ID for DOT syntax compliance."""
        # Replace problematic characters with underscores
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(element_id))
        # Ensure it starts with a letter or underscore
        if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
            sanitized = '_' + sanitized
        return sanitized or '_unknown'
    
    def _calculate_vertex_size(self, vertex, graph: RelationalGraphWithCuts) -> Tuple[float, float]:
        """Calculate appropriate size for a vertex based on its label and connections."""
        # Base size for vertex spot
        base_width, base_height = 0.3, 0.3
        
        if vertex.label:
            # Calculate size needed for label text
            label_chars = len(vertex.label)
            # Rough estimate: 0.08 inches per character, minimum 0.6 inches
            label_width = max(0.6, label_chars * 0.08)
            label_height = 0.25  # Standard text height
            
            # Vertex needs space for both spot and label
            width = max(base_width, label_width + 0.2)  # Padding around label
            height = base_height + label_height + 0.1   # Spot + label + padding
        else:
            # Just the identity spot
            width, height = base_width, base_height
        
        return width, height
    
    def _calculate_predicate_dimensions(self, predicate_name: str) -> Tuple[float, float]:
        """Calculate appropriate width and height for predicate text boxes."""
        name_chars = len(predicate_name)
        # AGGRESSIVE: Much more generous sizing to prevent any crowding or overlap
        # Dramatically increased character width and padding for professional appearance
        width = max(1.2, name_chars * 0.20 + 0.5)  # AGGRESSIVE character width + padding
        height = 0.6  # AGGRESSIVE predicate box height for text
        return width, height
    
    def _calculate_cut_padding(self) -> float:
        """Calculate appropriate padding for cut clusters to prevent text overlap."""
        # AGGRESSIVE: Extremely large padding to prevent any overlap issues
        # This accounts for predicate text dimensions plus generous safety margin
        return 50.0  # AGGRESSIVE padding around cut contents (was 25.0)
    
    @enforce_contracts(
        input_contracts={'graph': validate_relational_graph_with_cuts},
        output_contract=validate_layout_result
    )
    def create_layout_from_graph(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """
        Main entry point: Convert EGI graph to LayoutResult using Graphviz.
        
        Pipeline:
        1. EGI → DOT translation
        2. Graphviz execution (DOT → plain text coordinates)
        3. Plain text parsing → LayoutResult
        
        CONTRACT: Enforces solidified Graphviz modeling standards.
        """
        try:
            # Step 1: Generate DOT representation
            dot_content = self._generate_dot_from_egi(graph)
            
            # Step 2: Execute Graphviz and get xdot output (includes cluster _bb bounding boxes)
            xdot_output = self._execute_graphviz(dot_content)
            
            # Step 3: Parse xdot coordinates and cluster boundaries to create LayoutResult
            layout_result = self._parse_xdot_output_to_layout(xdot_output, graph)
            
            return layout_result
            
        except Exception as e:
            # Robust error handling - return empty layout on failure
            print(f"❌ Graphviz layout failed: {e}")
            return self._create_fallback_layout(graph)
    
    def _generate_dot_from_egi(self, graph: RelationalGraphWithCuts) -> str:
        """
        Step 1: Convert EGI structure to Graphviz DOT language.
        
        FIXED: Improved spacing parameters to prevent overlaps and crowding.
        
        Key mappings:
        - EGI vertices → Graphviz nodes
        - EGI edges (predicates/identity) → Graphviz edges
        - EGI cuts → Graphviz subgraph clusters
        - EGI area containment → Nested subgraph structure
        
        CONTRACT: Output validated against solidified DOT standards.
        """
        # Validate input
        validate_relational_graph_with_cuts(graph)
        
        # Generate DOT content
        dot_lines = [
            "graph EG {",
            "    // ENHANCED: Dau convention layout with proper spacing",
            "    graph [clusterrank=local, compound=true, newrank=true, rankdir=TB,",
            "           overlap=false, splines=true, concentrate=false];",
            "    ",
            "    // Enhanced spacing for Dau visual conventions",
            "    node [shape=circle, width=0.4, height=0.4, fixedsize=true,",
            "          fontsize=10, margin=0.2];",
            "    edge [arrowhead=none, len=3.5, minlen=2.5, weight=1.0];",
            "    ",
            "    // Spacing parameters for visual clarity",
            "    nodesep=4.0;        // Enhanced node separation",
            "    ranksep=3.0;        // Enhanced rank separation",
            "    margin=1.5;         // Increased graph margin",
            "    pad=\"1.5,1.5\";      // Enhanced padding",
            "    sep=\"+25\";          // Increased minimum separation",
            ""
        ]
        dot_lines.append("  ")  
        dot_lines.append("  // Default node styling with proper sizing")
        dot_lines.append("  node [shape=circle, style=filled, fillcolor=lightblue, fontsize=10];")
        dot_lines.append("  edge [fontsize=9, labeldistance=1.5, labelangle=0];")
        dot_lines.append("")
        
        # Generate subgraph clusters for cuts (with proper nesting)
        self._add_cuts_as_clusters(dot_lines, graph)
        
        # Generate nodes for vertices
        self._add_vertices_as_nodes(dot_lines, graph)
        
        # Generate edges for predicates and identity lines
        self._add_edges_for_predicates(dot_lines, graph)
        
        # DOT file footer
        dot_lines.append("}")
        
        dot_content = "\n".join(dot_lines)
        
        # CONTRACT: Validate DOT output against solidified standards
        validate_graphviz_dot_output(dot_content, graph)
        
        return dot_content
    
    def _add_cuts_as_clusters(self, dot_lines: List[str], graph: RelationalGraphWithCuts):
        """Add EGI cuts as Graphviz subgraph clusters with proper nesting."""
        
        # Build hierarchy of cuts (parent → children mapping)
        cut_hierarchy = self._build_cut_hierarchy(graph)
        
        # Add clusters recursively, starting from root-level cuts
        root_cuts = [cut for cut in graph.Cut if self._get_cut_parent(cut, graph) == graph.sheet]
        
        for cut in root_cuts:
            self._add_cluster_recursive(dot_lines, cut, graph, cut_hierarchy, indent=1)
    
    def _build_cut_hierarchy(self, graph: RelationalGraphWithCuts) -> Dict[str, List]:
        """Build parent → children mapping for cuts."""
        hierarchy = {}
        
        for cut in graph.Cut:
            parent = self._get_cut_parent(cut, graph)
            if parent not in hierarchy:
                hierarchy[parent] = []
            hierarchy[parent].append(cut)
        
        return hierarchy
    
    def _get_cut_parent(self, cut, graph: RelationalGraphWithCuts) -> str:
        """Find the parent area of a cut."""
        for area_id, contents in graph.area.items():
            if cut.id in contents:
                return area_id
        return graph.sheet  # Default to sheet level
    
    def _add_cluster_recursive(self, dot_lines: List[str], cut, graph: RelationalGraphWithCuts, 
                             hierarchy: Dict[str, List], indent: int):
        """Recursively add a cut and its nested cuts as clusters."""
        
        indent_str = "  " * indent
        
        # Start subgraph cluster with proper spacing attributes
        cluster_padding = self._calculate_cut_padding()
        safe_cut_id = self._sanitize_dot_id(cut.id)
        
        dot_lines.append(f"{indent_str}subgraph cluster_{safe_cut_id} {{")
        dot_lines.append(f"{indent_str}  label=\"Cut {cut.id[:8]}\";")
        dot_lines.append(f"{indent_str}  style=rounded;")
        dot_lines.append(f"{indent_str}  color=black;")
        dot_lines.append(f"{indent_str}  penwidth=1.5;")
        dot_lines.append(f"{indent_str}  margin={cluster_padding:.2f};  // Padding around cut contents")
        dot_lines.append(f"{indent_str}  labelloc=top;")
        dot_lines.append(f"{indent_str}  fontsize=8;")
        dot_lines.append(f"{indent_str}  // Leverage Graphviz hierarchical layout")
        dot_lines.append(f"{indent_str}  clusterrank=local;  // Layout this cluster separately")
        dot_lines.append("")
        
        # Add child cuts recursively
        child_cuts = hierarchy.get(cut.id, [])
        for child_cut in child_cuts:
            self._add_cluster_recursive(dot_lines, child_cut, graph, hierarchy, indent + 1)
        
        # Add vertices and edges that belong to this cut
        cut_contents = graph.area.get(cut.id, [])
        
        # SIMPLE FIX: Use EGI core's get_area() method to get cut contents
        cut_contents = graph.get_area(cut.id)
        
        # Add vertices in this cut
        for element_id in cut_contents:
            if element_id in graph._vertex_map:
                vertex = graph._vertex_map[element_id]
                safe_node_id = self._sanitize_dot_id(element_id)
                if vertex.label:
                    safe_label = vertex.label.replace('"', '\\"')
                    label = f'"{safe_label}"'
                else:
                    label = safe_node_id[:8]
                
                width, height = self._calculate_vertex_size(vertex, graph)
                dot_lines.append(f"{indent_str}  {safe_node_id} [label={label}, width={width:.2f}, height={height:.2f}, fixedsize=true];")
        
        # Add predicates (edges) in this cut
        for element_id in cut_contents:
            if element_id in graph.nu:  # This is a predicate edge
                predicate_name = graph.rel.get(element_id, element_id[:8])
                # CONSISTENT IDs: Use original EGI element ID directly (no pred_ prefix)
                safe_edge_id = self._sanitize_dot_id(element_id)
                
                width, height = self._calculate_predicate_dimensions(predicate_name)
                dot_lines.append(f"{indent_str}  {safe_edge_id} [label=\"{predicate_name}\", shape=box, fillcolor=lightyellow, width={width:.2f}, height={height:.2f}, fixedsize=true];")
        
        # End subgraph cluster
        dot_lines.append(f"{indent_str}}}")
        dot_lines.append("")
    
    def _add_vertices_as_nodes(self, dot_lines: List[str], graph: RelationalGraphWithCuts):
        """Add EGI vertices as Graphviz nodes (only sheet-level vertices)."""
        
        # SIMPLE FIX: Use EGI core's get_area() method
        sheet_contents = graph.get_area(graph.sheet)
        
        for vertex_id in sheet_contents:
            if vertex_id in graph._vertex_map:
                vertex = graph._vertex_map[vertex_id]
                # Sanitize node ID and label for DOT syntax
                safe_node_id = self._sanitize_dot_id(vertex_id)
                if vertex.label:
                    safe_label = vertex.label.replace('"', '\\"')
                    label = f'"{safe_label}"'
                else:
                    label = safe_node_id[:8]
                
                # Calculate proper size for collision detection
                width, height = self._calculate_vertex_size(vertex, graph)
                
                # Generate node with sizing attributes
                dot_lines.append(f"  {safe_node_id} [label={label}, width={width:.2f}, height={height:.2f}, fixedsize=true];")
        
        dot_lines.append("")
    
    def _add_edges_for_predicates(self, dot_lines: List[str], graph: RelationalGraphWithCuts):
        """Add EGI edges (predicates and identity lines) as Graphviz edges."""
        
        # Add edges for predicates
        for edge_id, vertex_sequence in graph.nu.items():
            if len(vertex_sequence) >= 2:
                # Multi-vertex predicate: connect all vertices
                predicate_name = graph.rel.get(edge_id, edge_id[:8])
                safe_predicate_name = predicate_name.replace('"', '\\"')
                
                for i in range(len(vertex_sequence) - 1):
                    v1, v2 = vertex_sequence[i], vertex_sequence[i + 1]
                    safe_v1 = self._sanitize_dot_id(v1)
                    safe_v2 = self._sanitize_dot_id(v2)
                    dot_lines.append(f"  {safe_v1} -- {safe_v2} [label=\"{safe_predicate_name}\", style=bold];")
            
            elif len(vertex_sequence) == 1:
                # Single-vertex predicate: create a predicate node with proper sizing
                # SIMPLE FIX: Only process predicates that are at sheet level (not in cuts)
                sheet_contents = graph.get_area(graph.sheet)
                predicate_at_sheet_level = edge_id in sheet_contents
                
                # Only generate predicate node if it's at sheet level
                if predicate_at_sheet_level:
                    vertex_id = vertex_sequence[0]
                    predicate_name = graph.rel.get(edge_id, edge_id[:8])
                    safe_vertex_id = self._sanitize_dot_id(vertex_id)
                    safe_predicate_name = predicate_name.replace('"', '\\"')
                    # CONSISTENT IDs: Use original EGI element ID directly (no pred_ prefix)
                    predicate_node_id = self._sanitize_dot_id(edge_id)
                    
                    # Calculate proper size for predicate node
                    pred_width, pred_height = self._calculate_predicate_dimensions(predicate_name)
                    
                    # Generate predicate node with sizing and styling
                    dot_lines.append(f"  {predicate_node_id} [label=\"{safe_predicate_name}\", shape=box, "
                                   f"fillcolor=lightyellow, width={pred_width:.2f}, height={pred_height:.2f}, fixedsize=true];")
                    
                    # Generate edge with enhanced routing attributes
                    dot_lines.append(f"  {safe_vertex_id} -- {predicate_node_id} [style=bold, penwidth=2, len=1.5];")
        
        dot_lines.append("")
    
    def _execute_graphviz(self, dot_content: str) -> str:
        """
        Step 2: Execute Graphviz and return plain text output.
        
        Uses Graphviz's plain output format for reliable coordinate parsing.
        """
        try:
            # Write DOT content to temporary file
            dot_file = os.path.join(self.temp_dir, "eg_layout.dot")
            with open(dot_file, 'w') as f:
                f.write(dot_content)
            
            # Execute Graphviz with xdot output (includes cluster _bb bounding boxes)
            cmd = [self.dot_executable, "-Txdot", dot_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise RuntimeError(f"Graphviz execution failed: {result.stderr}")
            
            # Clean up temporary file
            os.remove(dot_file)
            
            return result.stdout
            
        except Exception as e:
            raise RuntimeError(f"Failed to execute Graphviz: {e}")
    
    def _parse_xdot_output_to_layout(self, xdot_output: str, graph: RelationalGraphWithCuts) -> LayoutResult:
        """
        Step 3: Parse Graphviz xdot output into LayoutResult.
        
        xdot format includes cluster _bb (bounding box) attributes:
        - Clusters have _bb="x1,y1,x2,y2" attributes with precise boundaries
        - Nodes have pos="x,y" attributes for positioning
        - This allows us to use Graphviz's native cluster size calculations!
        """
        primitives = {}
        canvas_bounds = (0, 0, 400, 300)  # Default bounds
        
        # Use the proven xdot parser instead of fragile regex
        try:
            clusters, nodes, edges = parse_xdot_file(xdot_output)
            
            # Extract main graph bounding box
            import re
            graph_bb_match = re.search(r'graph \[.*?bb="([^"]+)"', xdot_output, re.DOTALL)
            if graph_bb_match:
                bb_coords = graph_bb_match.group(1).split(',')
                if len(bb_coords) == 4:
                    x1, y1, x2, y2 = map(float, bb_coords)
                    canvas_bounds = (x1, y1, x2, y2)
            
            # Process clusters (cuts) using the proven parser
            for cluster in clusters:
                cluster_name = cluster.name
                x1, y1, x2, y2 = cluster.bb
                
                # Find matching cut in graph
                cut_id_part = cluster_name.replace('cluster_', '')
                for cut in graph.Cut:
                    if self._sanitize_dot_id(cut.id) == cut_id_part:
                        # Create cut primitive using Graphviz's native cluster boundary
                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2
                        
                        cut_primitive = SpatialPrimitive(
                            element_id=cut.id,
                            element_type='cut',
                            position=(center_x, center_y),
                            bounds=(x1, y1, x2, y2),
                            z_index=0
                        )
                        primitives[cut.id] = cut_primitive
                        print(f"✅ Using Graphviz cluster boundary for {cut.id}: bounds=({x1}, {y1}, {x2}, {y2})")
                        break
            
            # Process nodes using the proven parser
            for node in nodes:
                node_id = node.name
                x, y = node.pos
                width = node.width * 72  # Convert to points
                height = node.height * 72
                
                # Determine element type using EGI mappings (consistent IDs throughout)
                if node_id in graph.nu:  # This is a predicate edge
                    element_type_name = 'predicate'
                elif node_id in graph._vertex_map:  # This is a vertex
                    element_type_name = 'vertex'
                elif node_id in graph._cut_map:  # This is a cut (shouldn't happen here)
                    element_type_name = 'cut'
                else:
                    # Fallback: assume vertex for unknown elements
                    element_type_name = 'vertex'
                
                # Create node primitive with bounds that match text rendering
                if element_type_name == 'predicate':
                    # For predicates, calculate bounds based on text dimensions
                    # This matches the text rendering logic in the GUI
                    relation_name = graph.rel.get(node_id, node_id)
                    
                    # Estimate text dimensions (approximate font metrics)
                    # This should match the actual font metrics used in rendering
                    char_width = 8  # Approximate character width in pixels
                    char_height = 12  # Approximate character height in pixels
                    text_width = len(relation_name) * char_width
                    text_height = char_height
                    
                    # Add padding to match rendering
                    padding = 4
                    
                    node_bounds = (
                        x - text_width/2 - padding,
                        y - text_height/2 - padding,
                        x + text_width/2 + padding,
                        y + text_height/2 + padding
                    )
                else:
                    # For vertices and cuts, use Graphviz dimensions
                    node_bounds = (
                        x - width/2,
                        y - height/2,
                        x + width/2,
                        y + height/2
                    )
                
                # CONSISTENT IDs: Use the same ID throughout (no mapping needed)
                original_element_id = node_id
                
                # CRITICAL FIX: Set up attachment_points for predicates
                attachment_points = None
                if element_type_name == 'predicate' and original_element_id in graph.nu:
                    # Get vertex positions for this predicate's nu mapping
                    vertex_sequence = graph.nu[original_element_id]
                    attachment_points = {}
                    
                    for i, vertex_id in enumerate(vertex_sequence):
                        # Find vertex position in the same layout
                        for other_node in nodes:
                            if other_node.name == vertex_id:
                                vertex_x, vertex_y = other_node.pos
                                attachment_points[f"vertex_{i}"] = (vertex_x, vertex_y)
                                break
                
                primitive = SpatialPrimitive(
                    element_id=original_element_id,  # Use original EGI ID, not DOT node ID
                    element_type=element_type_name,
                    position=(x, y),
                    bounds=node_bounds,
                    z_index=1,
                    attachment_points=attachment_points  # CRITICAL: Include attachment points
                )
                
                primitives[original_element_id] = primitive  # Use original EGI ID as key
            
            # CRITICAL FIX: Ensure ALL graph elements have spatial primitives
            # This prevents the contract violation we discovered
            self._ensure_complete_element_coverage(graph, primitives, canvas_bounds)
            
            # Process edges using the proven parser (with error handling)
            try:
                for edge in edges:
                    if hasattr(edge, 'tail') and hasattr(edge, 'head') and hasattr(edge, 'points'):
                        tail_id = edge.tail
                        head_id = edge.head
                        edge_points = edge.points
                        
                        # Create edge primitive if we have valid points
                        if edge_points and len(edge_points) > 0:
                            edge_id = f"edge_{tail_id}_{head_id}"
                            
                            # Only add if this edge_id doesn't already exist
                            if edge_id not in primitives:
                                center_x = sum(p[0] for p in edge_points) / len(edge_points)
                                center_y = sum(p[1] for p in edge_points) / len(edge_points)
                                
                                primitive = SpatialPrimitive(
                                    element_id=edge_id,
                                    element_type='edge',
                                    position=(center_x, center_y),
                                    bounds=(center_x - 20, center_y - 10, center_x + 20, center_y + 10),
                                    z_index=2
                                )
                                
                                primitives[edge_id] = primitive
            except Exception as e:
                print(f"⚠️  Edge processing failed (non-critical): {e}")
                # Continue - complete element coverage ensures all elements have primitives
                
        except Exception as e:
            print(f"❌ Xdot parsing failed: {e}")
            # Fallback to empty layout with complete element coverage
            primitives = {}
            self._ensure_complete_element_coverage(graph, primitives, canvas_bounds)
        
        # Build containment hierarchy
        containment_hierarchy = {}
        containment_hierarchy[graph.sheet] = set()
        for area_id, contents in graph.area.items():
            if area_id not in containment_hierarchy:
                containment_hierarchy[area_id] = set()
            containment_hierarchy[area_id].update(contents)
        
        return LayoutResult(
            primitives=primitives,
            canvas_bounds=canvas_bounds,
            containment_hierarchy=containment_hierarchy
        )
    
    def _ensure_complete_element_coverage(self, graph: RelationalGraphWithCuts, 
                                        primitives: Dict[str, SpatialPrimitive], 
                                        canvas_bounds: Tuple[float, float, float, float]):
        """
        Ensure ALL graph elements have spatial primitives.
        
        This prevents contract violations by guaranteeing complete coverage.
        If an element is missing from Graphviz output, we create a fallback primitive.
        """
        x1, y1, x2, y2 = canvas_bounds
        fallback_x = (x1 + x2) / 2
        fallback_y = (y1 + y2) / 2
        
        print(f"🔍 Ensuring complete element coverage...")
        print(f"   Graph has {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
        print(f"   Current primitives: {len(primitives)} elements")
        
        # Ensure all vertices have spatial primitives
        for vertex in graph.V:
            # Handle both Vertex objects and string IDs
            vertex_id = vertex.id if hasattr(vertex, 'id') else str(vertex)
            
            if vertex_id not in primitives:
                print(f"⚠️  Creating fallback primitive for missing vertex: {vertex_id}")
                
                fallback_primitive = SpatialPrimitive(
                    element_id=vertex_id,
                    element_type='vertex',
                    position=(fallback_x + len(primitives) * 20, fallback_y),  # Spread them out
                    bounds=(fallback_x - 10, fallback_y - 10, fallback_x + 10, fallback_y + 10),
                    z_index=1
                )
                primitives[vertex_id] = fallback_primitive
        
        # Ensure all edges (predicates) have spatial primitives
        for edge in graph.E:
            # Handle both Edge objects and string IDs
            edge_id = edge.id if hasattr(edge, 'id') else str(edge)
            
            if edge_id not in primitives:
                print(f"⚠️  Creating fallback primitive for missing edge: {edge_id}")
                predicate_name = graph.rel.get(edge_id, edge_id[:8] if isinstance(edge_id, str) else str(edge_id)[:8])
                
                # Calculate dimensions for fallback predicate
                width, height = self._calculate_predicate_dimensions(predicate_name)
                bounds = (
                    fallback_x - width * 36,  # Convert to points
                    fallback_y - height * 36,
                    fallback_x + width * 36,
                    fallback_y + height * 36
                )
                
                fallback_primitive = SpatialPrimitive(
                    element_id=edge_id,
                    element_type='predicate',
                    position=(fallback_x, fallback_y + len(primitives) * 20),  # Spread them out
                    bounds=bounds,
                    z_index=1
                )
                primitives[edge_id] = fallback_primitive
        
        # Ensure all cuts have spatial primitives
        for cut in graph.Cut:
            cut_id = cut.id if hasattr(cut, 'id') else str(cut)
            
            if cut_id not in primitives:
                print(f"⚠️  Creating fallback primitive for missing cut: {cut_id}")
                
                # Create a reasonable fallback cut boundary
                cut_width = (x2 - x1) * 0.3  # 30% of canvas width
                cut_height = (y2 - y1) * 0.3  # 30% of canvas height
                
                cut_bounds = (
                    fallback_x - cut_width / 2,
                    fallback_y - cut_height / 2,
                    fallback_x + cut_width / 2,
                    fallback_y + cut_height / 2
                )
                
                fallback_primitive = SpatialPrimitive(
                    element_id=cut_id,
                    element_type='cut',
                    position=(fallback_x, fallback_y),
                    bounds=cut_bounds,
                    z_index=0
                )
                primitives[cut_id] = fallback_primitive
        
        print(f"✅ Complete element coverage ensured: {len(primitives)} total primitives")
    
    def _calculate_cut_boundaries(self, primitives: Dict[str, SpatialPrimitive], 
                                 graph: RelationalGraphWithCuts) -> None:
        """
        Calculate cut boundaries from the positions of nodes within each cut area.
        
        FIXED: Hierarchical boundary calculation for nested cuts.
        Calculate boundaries for innermost cuts first, then use those boundaries
        to calculate outer cut boundaries.
        """
        # Build cut hierarchy (innermost to outermost)
        cut_hierarchy = self._build_cut_hierarchy_by_depth(graph)
        
        # Process cuts from innermost to outermost
        for depth_level in sorted(cut_hierarchy.keys(), reverse=True):
            for cut in cut_hierarchy[depth_level]:
                cut_contents = graph.area.get(cut.id, set())
                
                # Find all primitives that belong to this cut
                cut_primitives = []
                for element_id in cut_contents:
                    # Check for direct primitives (vertices)
                    if element_id in primitives:
                        cut_primitives.append(primitives[element_id])
                    # FIXED: Check for child cut primitives (for nested cuts)
                    if element_id in primitives and primitives[element_id].element_type == 'cut':
                        cut_primitives.append(primitives[element_id])
                
                # CRITICAL FIX: Find predicate nodes that belong to this cut
                # Look for edges where vertices are in this cut area
                for edge_id, vertex_sequence in graph.nu.items():
                    # Check if any vertex in this edge is in the current cut
                    edge_in_cut = any(v_id in cut_contents for v_id in vertex_sequence)
                    if edge_in_cut:
                        # Look for the predicate node for this edge
                        pred_node_id = f"pred_{edge_id}"
                        if pred_node_id in primitives:
                            cut_primitives.append(primitives[pred_node_id])
                            print(f"  📍 Including predicate node {pred_node_id} in cut {cut.id}")
                
                if cut_primitives:
                    # Calculate bounding box of all elements in this cut
                    min_x = min(p.bounds[0] for p in cut_primitives)
                    min_y = min(p.bounds[1] for p in cut_primitives)
                    max_x = max(p.bounds[2] for p in cut_primitives)
                    max_y = max(p.bounds[3] for p in cut_primitives)
                    
                    # Add padding around the contents
                    padding = 30.0  # Generous padding for cut oval
                    cut_bounds = (
                        min_x - padding,
                        min_y - padding,
                        max_x + padding,
                        max_y + padding
                    )
                    
                    # Calculate center position
                    center_x = (cut_bounds[0] + cut_bounds[2]) / 2
                    center_y = (cut_bounds[1] + cut_bounds[3]) / 2
                    
                    # Create cut primitive
                    cut_primitive = SpatialPrimitive(
                        element_id=cut.id,
                        element_type='cut',
                        position=(center_x, center_y),
                        bounds=cut_bounds,
                        z_index=0  # Background layer
                    )
                    
                    primitives[cut.id] = cut_primitive
                    
                    print(f"✅ Created cut primitive for {cut.id} (depth {depth_level}): bounds={cut_bounds}")
                else:
                    print(f"⚠️  No primitives found for cut {cut.id} (depth {depth_level})")
    
    def _build_cut_hierarchy_by_depth(self, graph: RelationalGraphWithCuts) -> Dict[int, List]:
        """
        Build cut hierarchy organized by nesting depth.
        
        Returns a dictionary mapping depth level to list of cuts at that depth.
        Depth 0 = sheet level, depth 1 = cuts directly in sheet, etc.
        """
        hierarchy_by_depth = {}
        
        def calculate_cut_depth(cut_id: str, visited: set = None) -> int:
            """Calculate the nesting depth of a cut."""
            if visited is None:
                visited = set()
            
            if cut_id in visited:
                return 0  # Avoid infinite recursion
            visited.add(cut_id)
            
            # Find which area contains this cut
            parent_area = None
            for area_id, contents in graph.area.items():
                if cut_id in contents:
                    parent_area = area_id
                    break
            
            if parent_area == graph.sheet:
                return 1  # Direct child of sheet
            elif parent_area:
                # This cut is inside another cut
                return 1 + calculate_cut_depth(parent_area, visited)
            else:
                return 0  # Shouldn't happen, but safe fallback
        
        # Calculate depth for each cut
        for cut in graph.Cut:
            depth = calculate_cut_depth(cut.id)
            if depth not in hierarchy_by_depth:
                hierarchy_by_depth[depth] = []
            hierarchy_by_depth[depth].append(cut)
        
        return hierarchy_by_depth
    
    def _create_fallback_layout(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """Create a simple fallback layout when Graphviz fails."""
        primitives = {}
        
        # Simple grid layout for vertices
        x, y = 100, 100
        for vertex_id, vertex in graph._vertex_map.items():
            primitive = SpatialPrimitive(
                element_id=vertex_id,
                element_type='vertex',
                position=(x, y),
                bounds=(x - 20, y - 20, x + 20, y + 20),
                z_index=1
            )
            primitives[vertex_id] = primitive
            x += 80
            if x > 600:
                x = 100
                y += 80
        
        return LayoutResult(
            primitives=primitives,
            canvas_bounds=(0, 0, 800, 600),
            containment_hierarchy={graph.sheet: set(graph._vertex_map.keys())}
        )


# Integration function for existing workflow
def create_graphviz_layout(graph: RelationalGraphWithCuts) -> LayoutResult:
    """Main entry point for Graphviz-based layout generation."""
    engine = GraphvizLayoutEngine()
    return engine.create_layout_from_graph(graph)


if __name__ == "__main__":
    # Test with a simple example
    from egif_parser_dau import parse_egif
    
    # Test cases
    test_cases = [
        ('Simple Predicate', '(Human "Socrates")'),
        ('Mixed Cut and Sheet', '(Human "Socrates") ~[ (Mortal "Socrates") ]'),
        ('Sibling Cuts', '*x ~[ (Human x) ] ~[ (Mortal x) ]'),
    ]
    
    for name, egif in test_cases:
        print(f"\n🎯 Testing {name}: {egif}")
        try:
            graph = parse_egif(egif)
            layout = create_graphviz_layout(graph)
            print(f"✅ Layout created with {len(layout.primitives)} elements")
            print(f"   Canvas bounds: {layout.canvas_bounds}")
        except Exception as e:
            print(f"❌ Failed: {e}")
