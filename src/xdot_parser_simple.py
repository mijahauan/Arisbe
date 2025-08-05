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
        """Extract node positions and dimensions."""
        nodes = []
        
        # Use a more robust approach: find all pos="..." attributes first
        # Then look backwards to find the node name
        pos_pattern = r'pos="([^"]+)"'
        
        for pos_match in re.finditer(pos_pattern, content):
            pos_str = pos_match.group(1)
            pos_start = pos_match.start()
            
            # Look backwards to find the node name and opening bracket
            # Search up to 500 characters back
            search_start = max(0, pos_start - 500)
            search_region = content[search_start:pos_start]
            
            # Find the last node name before this pos attribute
            node_name_pattern = r'(\w+)\s*\['
            node_matches = list(re.finditer(node_name_pattern, search_region))
            
            if node_matches:
                node_name = node_matches[-1].group(1)  # Get the last match
                
                # Look both backwards and forwards from pos to find width and height
                # (attributes can appear before or after pos in xdot format)
                search_end = min(len(content), pos_match.end() + 500)
                forward_region = content[pos_match.end():search_end]
                backward_region = content[search_start:pos_match.start()]
                
                # Search in both directions
                width_match = (re.search(r'width=([0-9.]+)', forward_region) or 
                              re.search(r'width=([0-9.]+)', backward_region))
                height_match = (re.search(r'height=([0-9.]+)', forward_region) or 
                               re.search(r'height=([0-9.]+)', backward_region))
                
                if width_match and height_match:
                    try:
                        width = float(width_match.group(1))
                        height = float(height_match.group(1))
                        
                        # Parse position (comma-separated x,y)
                        if ',' in pos_str:
                            x, y = map(float, pos_str.split(','))
                            nodes.append(XdotNode(node_name, (x, y), width, height))
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
