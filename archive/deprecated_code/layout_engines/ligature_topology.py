#!/usr/bin/env python3
"""
Ligature Topology Analysis - Pass 0

Pre-processing step that analyzes the complete topological structure of ligatures
before layout begins. This provides high-level structural understanding that informs
all subsequent layout passes.

Key Insights:
- A ligature is a complete line of identity connecting a relation to its arguments
- It may branch (multiple vertices to one edge)
- It may span multiple areas (requiring ports)
- It is ONE continuous line, not separate segments

This analysis transforms raw ν mappings into complete ligature topology.
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from egi_core_dau import RelationalGraphWithCuts


@dataclass
class LigatureSegment:
    """
    A segment of a ligature between two waypoints.
    
    Waypoints can be:
    - Vertex positions
    - Branch points (where ligature splits)
    - Port positions (boundary crossings)
    """
    start_id: str  # vertex_id, port_id, or branch_id
    end_id: str    # vertex_id, port_id, branch_id, or edge_id
    start_area: str
    end_area: str
    crosses_boundary: bool


@dataclass
class LigatureTopology:
    """
    Complete topology of a single ligature (line of identity).
    
    A ligature connects one edge (relation) to N vertices (arguments).
    It is ONE continuous line that may branch and span multiple areas.
    """
    edge_id: str
    vertex_ids: List[str]
    
    # Structural properties
    is_branching: bool  # True if multiple vertices (needs branch point)
    is_spanning: bool   # True if crosses area boundaries
    
    # Area information
    edge_area: str
    vertex_areas: Dict[str, str]  # vertex_id -> area_id
    crossed_areas: Set[str]  # All areas this ligature passes through
    
    # Topology details
    requires_ports: bool
    port_boundaries: List[Tuple[str, str]]  # (from_area, to_area) pairs
    branch_point_needed: bool
    
    # Calculated during layout
    branch_point_position: Optional[Tuple[float, float]] = None
    port_positions: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    def get_hook_index(self, vertex_id: str) -> int:
        """Get the hook index (ν mapping order) for a vertex."""
        return self.vertex_ids.index(vertex_id)
    
    def is_simple(self) -> bool:
        """True if ligature is simple: single vertex, same area, no branching."""
        return len(self.vertex_ids) == 1 and not self.is_spanning


@dataclass
class TopologyAnalysis:
    """
    Complete topological analysis of all ligatures in an EGI.
    
    This is the output of Pass 0, used by all subsequent passes.
    """
    ligatures: Dict[str, LigatureTopology]  # edge_id -> topology
    
    # Quick lookups
    crossing_ligatures: List[str]  # edge_ids that span areas
    branching_ligatures: List[str]  # edge_ids with multiple vertices
    simple_ligatures: List[str]    # edge_ids that are simple
    
    # Area-based indexing
    ligatures_in_area: Dict[str, Set[str]]  # area_id -> set of edge_ids
    ligatures_crossing_boundary: Dict[Tuple[str, str], Set[str]]  # (area1, area2) -> edge_ids
    
    def get_ligature(self, edge_id: str) -> Optional[LigatureTopology]:
        """Get topology for a specific ligature."""
        return self.ligatures.get(edge_id)
    
    def get_crossings_for_areas(self, area1: str, area2: str) -> Set[str]:
        """Get all ligatures crossing between two specific areas."""
        key1 = (area1, area2)
        key2 = (area2, area1)
        result = set()
        if key1 in self.ligatures_crossing_boundary:
            result.update(self.ligatures_crossing_boundary[key1])
        if key2 in self.ligatures_crossing_boundary:
            result.update(self.ligatures_crossing_boundary[key2])
        return result


class LigatureTopologyAnalyzer:
    """
    Pass 0: Topological Analysis
    
    Analyzes the complete structure of all ligatures before layout begins.
    This pre-processing step provides essential information for:
    
    - Pass 1 (Graphviz): Where to add tension edges for spanning ligatures
    - Pass 2 (d3-force): Where to create branch nodes for optimal Y-junctions
    - Pass 3 (A* Pathfinding): Complete ligature structure for routing
    """
    
    def __init__(self, egi: RelationalGraphWithCuts, element_to_cut: Dict[str, str]):
        """
        Initialize analyzer.
        
        Args:
            egi: The EGI graph to analyze
            element_to_cut: Mapping of element IDs to their containing area
        """
        self.egi = egi
        self.element_to_cut = element_to_cut
    
    def analyze(self) -> TopologyAnalysis:
        """
        Perform complete topological analysis.
        
        Returns:
            TopologyAnalysis with complete ligature structure
        """
        ligatures = {}
        crossing = []
        branching = []
        simple = []
        
        # Analyze each edge (relation) and its connected vertices
        for edge_id, vertex_ids in self.egi.nu.items():
            topology = self._analyze_ligature(edge_id, vertex_ids)
            ligatures[edge_id] = topology
            
            # Categorize
            if topology.is_spanning:
                crossing.append(edge_id)
            if topology.is_branching:
                branching.append(edge_id)
            if topology.is_simple():
                simple.append(edge_id)
        
        # Build area-based indexes
        ligatures_in_area = self._build_area_index(ligatures)
        ligatures_crossing = self._build_crossing_index(ligatures)
        
        return TopologyAnalysis(
            ligatures=ligatures,
            crossing_ligatures=crossing,
            branching_ligatures=branching,
            simple_ligatures=simple,
            ligatures_in_area=ligatures_in_area,
            ligatures_crossing_boundary=ligatures_crossing
        )
    
    def _analyze_ligature(self, edge_id: str, vertex_ids: List[str]) -> LigatureTopology:
        """
        Analyze a single ligature's complete topology.
        
        Args:
            edge_id: The edge (relation) this ligature connects to
            vertex_ids: All vertices connected to this edge (in ν order)
            
        Returns:
            Complete LigatureTopology
        """
        # Determine areas
        edge_area = self.element_to_cut.get(edge_id, self.egi.sheet)
        vertex_areas = {v_id: self.element_to_cut.get(v_id, self.egi.sheet) 
                       for v_id in vertex_ids}
        
        # Identify all areas this ligature touches
        all_areas = {edge_area}
        all_areas.update(vertex_areas.values())
        
        # Check properties
        is_branching = len(vertex_ids) > 1
        is_spanning = len(all_areas) > 1
        
        # Determine port requirements
        port_boundaries = []
        if is_spanning:
            # Find all unique boundary crossings
            for v_id in vertex_ids:
                v_area = vertex_areas[v_id]
                if v_area != edge_area:
                    # This vertex is in a different area - crossing required
                    boundary = self._find_boundary(v_area, edge_area)
                    if boundary and boundary not in port_boundaries:
                        port_boundaries.append(boundary)
        
        requires_ports = len(port_boundaries) > 0
        
        # Branch point needed if multiple vertices AND at least one is in same area as edge
        # (Branch point goes in the edge's area, connects to all vertices)
        branch_point_needed = False
        if is_branching:
            # Check if ANY vertex is in the same area as the edge
            same_area_vertices = [v for v in vertex_ids if vertex_areas[v] == edge_area]
            # Or if ALL vertices are in different areas (need branch in edge's area)
            diff_area_vertices = [v for v in vertex_ids if vertex_areas[v] != edge_area]
            
            # Branch point needed if:
            # 1. Multiple vertices in same area as edge (branch locally)
            # 2. OR multiple vertices all in different areas (branch at edge, then span)
            if len(same_area_vertices) > 1 or len(diff_area_vertices) > 1:
                branch_point_needed = True
        
        return LigatureTopology(
            edge_id=edge_id,
            vertex_ids=list(vertex_ids),
            is_branching=is_branching,
            is_spanning=is_spanning,
            edge_area=edge_area,
            vertex_areas=vertex_areas,
            crossed_areas=all_areas,
            requires_ports=requires_ports,
            port_boundaries=port_boundaries,
            branch_point_needed=branch_point_needed
        )
    
    def _find_boundary(self, area1: str, area2: str) -> Optional[Tuple[str, str]]:
        """
        Find the boundary between two areas.
        
        Returns:
            (parent, child) tuple if one area contains the other, else None
        """
        # Check if area1 contains area2
        if area2 in self.egi.area.get(area1, []):
            return (area1, area2)
        
        # Check if area2 contains area1
        if area1 in self.egi.area.get(area2, []):
            return (area2, area1)
        
        # Areas are not directly adjacent - find path
        # For now, return None (will need hierarchy traversal for complex cases)
        return None
    
    def _build_area_index(self, ligatures: Dict[str, LigatureTopology]) -> Dict[str, Set[str]]:
        """Build index of which ligatures touch each area."""
        index = {}
        for edge_id, topology in ligatures.items():
            for area in topology.crossed_areas:
                if area not in index:
                    index[area] = set()
                index[area].add(edge_id)
        return index
    
    def _build_crossing_index(self, ligatures: Dict[str, LigatureTopology]) -> Dict[Tuple[str, str], Set[str]]:
        """Build index of which ligatures cross each boundary."""
        index = {}
        for edge_id, topology in ligatures.items():
            for boundary in topology.port_boundaries:
                if boundary not in index:
                    index[boundary] = set()
                index[boundary].add(edge_id)
        return index


def analyze_ligature_topology(egi: RelationalGraphWithCuts, 
                              element_to_cut: Dict[str, str]) -> TopologyAnalysis:
    """
    Convenience function to perform topological analysis.
    
    Args:
        egi: The EGI graph
        element_to_cut: Element to area mapping
        
    Returns:
        Complete TopologyAnalysis
    """
    analyzer = LigatureTopologyAnalyzer(egi, element_to_cut)
    return analyzer.analyze()
