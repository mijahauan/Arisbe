"""
Simple xdot parser for extracting cluster boundaries and node positions.
Based on pyparsing approach from godot/xdot_parser.py but simplified for our needs.
"""

import re
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass

@dataclass
class XdotCluster:
    """Represents a cluster (subgraph) with its bounding box."""
    name: str
    bb: Tuple[float, float, float, float]  # x1, y1, x2, y2

@dataclass 
class XdotNode:
    """Represents a node with its position and dimensions."""
    name: str
    pos: Tuple[float, float]  # x, y
    width: float
    height: float

@dataclass
class XdotEdge:
    """Represents an edge with its path points."""
    tail: str
    head: str
    points: List[Tuple[float, float]]

class SimpleXdotParser:
    """
    Simple xdot parser that extracts the essential information we need:
    - Cluster bounding boxes (bb attributes)
    - Node positions (pos attributes) 
    - Edge paths (pos attributes)
    
    Uses regex for simplicity but handles nested structures correctly.
    """
    
    def parse_xdot(self, xdot_content: str) -> Tuple[List[XdotCluster], List[XdotNode], List[XdotEdge]]:
        """Parse xdot content and return clusters, nodes, and edges."""
        clusters = self._extract_clusters(xdot_content)
        nodes = self._extract_nodes(xdot_content)
        edges = self._extract_edges(xdot_content)
        
        return clusters, nodes, edges
    
    def _extract_clusters(self, content: str) -> List[XdotCluster]:
        """Extract cluster bounding boxes using a more robust approach."""
        clusters = []
        
        # Find all subgraph cluster declarations
        cluster_pattern = r'subgraph\s+(cluster_\w+)\s*\{'
        cluster_matches = list(re.finditer(cluster_pattern, content))
        
        for match in cluster_matches:
            cluster_name = match.group(1)
            start_pos = match.end()
            
            # Find the bb attribute for this cluster
            # Look for bb="..." within reasonable distance after cluster declaration
            search_region = content[start_pos:start_pos + 1000]  # Look ahead 1000 chars
            bb_match = re.search(r'bb="([^"]+)"', search_region)
            
            if bb_match:
                bb_coords = bb_match.group(1).split(',')
                if len(bb_coords) == 4:
                    try:
                        x1, y1, x2, y2 = map(float, bb_coords)
                        clusters.append(XdotCluster(cluster_name, (x1, y1, x2, y2)))
                    except ValueError:
                        continue
        
        return clusters
    
    def _extract_nodes(self, content: str) -> List[XdotNode]:
        """Extract node positions and dimensions.
        Robustly match each node's bracket block and read attributes inside it."""
        nodes: List[XdotNode] = []
        # Try to capture global node defaults (xdot emits a shared node block)
        # Example:
        # node [ ... height=0.4, ... width=0.4 ];
        default_width: Optional[float] = None
        default_height: Optional[float] = None
        node_defaults_match = re.search(r"\bnode\s*\[(?P<body>[^\]]+)\]", content, re.DOTALL)
        if node_defaults_match:
            body = node_defaults_match.group("body")
            dw = re.search(r"width=([0-9.]+)", body)
            dh = re.search(r"height=([0-9.]+)", body)
            if dw:
                try:
                    default_width = float(dw.group(1))
                except ValueError:
                    default_width = None
            if dh:
                try:
                    default_height = float(dh.group(1))
                except ValueError:
                    default_height = None
        # Match blocks like: <name> [ ... pos="x,y" ... width=h ... height=h ... ]
        # Use tempered dot to avoid crossing the closing bracket
        node_block_pattern = re.compile(r'(\w+)\s*\[(?:(?!\]).)*\]', re.DOTALL)
        for m in node_block_pattern.finditer(content):
            name = m.group(1)
            block = m.group(0)
            pos_m = re.search(r'pos="([0-9.]+),([0-9.]+)"', block)
            width_m = re.search(r'width=([0-9.]+)', block)
            height_m = re.search(r'height=([0-9.]+)', block)
            if not pos_m:
                continue
            try:
                x = float(pos_m.group(1))
                y = float(pos_m.group(2))
                if width_m:
                    width = float(width_m.group(1))
                elif default_width is not None:
                    width = default_width
                else:
                    # Fallback Graphviz default (inches) if not provided
                    width = 0.75
                if height_m:
                    height = float(height_m.group(1))
                elif default_height is not None:
                    height = default_height
                else:
                    height = 0.75
                nodes.append(XdotNode(name, (x, y), width, height))
            except ValueError:
                continue
        return nodes
    
    def _extract_edges(self, content: str) -> List[XdotEdge]:
        """Extract edge paths."""
        edges = []
        
        # Pattern to match edge definitions with pos attribute
        edge_pattern = r'(\w+)\s*--\s*(\w+)\s*\[[^]]*?pos="([^"]+)"[^]]*?\]'
        
        for match in re.finditer(edge_pattern, content, re.DOTALL):
            tail = match.group(1)
            head = match.group(2)
            pos_str = match.group(3)
            
            # Parse edge path points (space-separated coordinate pairs)
            points = []
            coord_pairs = pos_str.split()
            for coord_pair in coord_pairs:
                if ',' in coord_pair:
                    try:
                        x, y = map(float, coord_pair.split(','))
                        points.append((x, y))
                    except ValueError:
                        continue
            
            if points:
                edges.append(XdotEdge(tail, head, points))
        
        return edges

def parse_xdot_file(xdot_content: str) -> Tuple[List[XdotCluster], List[XdotNode], List[XdotEdge]]:
    """Convenience function to parse xdot content."""
    parser = SimpleXdotParser()
    return parser.parse_xdot(xdot_content)
