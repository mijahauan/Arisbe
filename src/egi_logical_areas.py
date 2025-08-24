"""
EGI Logical Areas - Fundamental logical-spatial correspondence system.

This module implements the core logical structure of Existential Graphs where:
- Only two logical operators exist: negation (~[]) and conjunction (spatial juxtaposition)
- All operations are graph-to-graph, never element-to-area
- Cuts represent negation - removing enclosed space from enclosing space view
- Conjunction cannot happen across negation boundaries
"""

from typing import Dict, Set, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class LogicalOperator(Enum):
    """The only two logical operators in Existential Graphs."""
    NEGATION = "negation"      # Represented by cuts ~[]
    CONJUNCTION = "conjunction"  # Represented by spatial juxtaposition


@dataclass
class EGIGraph:
    """A complete EGI graph that can be added to logical areas."""
    graph_id: str
    vertices: Set[str]
    edges: Set[str]
    cuts: Set[str]
    nu_mapping: Dict[str, Set[str]]  # edge -> incident vertices
    relation_mapping: Dict[str, str]  # edge -> relation name
    
    def is_empty(self) -> bool:
        """Check if this is an empty graph."""
        return not (self.vertices or self.edges or self.cuts)
    
    def contains_only_vertex(self) -> bool:
        """Check if graph contains only a single vertex."""
        return len(self.vertices) == 1 and not self.edges and not self.cuts
    
    def contains_only_edge(self) -> bool:
        """Check if graph contains only a single edge."""
        return len(self.edges) == 1 and not self.cuts
    
    def contains_only_cut(self) -> bool:
        """Check if graph contains only a single cut."""
        return len(self.cuts) == 1 and not self.vertices and not self.edges


class LogicalArea:
    """
    A logical area in the EGI system.
    
    Logical areas correspond to spatial regions and implement the fundamental
    logical operators through containment and negation.
    """
    
    def __init__(self, area_id: str, parent_area: Optional[str] = None, is_cut: bool = False):
        self.area_id = area_id
        self.parent_area = parent_area
        self.is_cut = is_cut  # True if this area represents a negation (~[])
        self.contained_graphs: List[EGIGraph] = []
        self.child_areas: List[str] = []  # Nested areas (cuts or sub-regions)
        
    def add_graph(self, graph: EGIGraph) -> bool:
        """
        Add a complete graph to this logical area.
        This is the ONLY way to add content to areas.
        """
        if not isinstance(graph, EGIGraph):
            raise ValueError("Can only add EGIGraph objects to logical areas")
        
        # Validate that conjunction doesn't cross negation boundaries
        if not self._validate_conjunction_constraints(graph):
            return False
            
        self.contained_graphs.append(graph)
        return True
    
    def add_child_area(self, child_area_id: str) -> None:
        """Add a nested logical area (typically a cut)."""
        if child_area_id not in self.child_areas:
            self.child_areas.append(child_area_id)
    
    def _validate_conjunction_constraints(self, new_graph: EGIGraph) -> bool:
        """
        Validate that adding this graph doesn't violate conjunction constraints.
        Conjunction cannot happen across negation boundaries.
        """
        # For now, allow all additions - constraints can be refined
        return True
    
    def get_all_vertices(self) -> Set[str]:
        """Get all vertices contained in this logical area."""
        vertices = set()
        for graph in self.contained_graphs:
            vertices.update(graph.vertices)
        return vertices
    
    def get_all_edges(self) -> Set[str]:
        """Get all edges contained in this logical area."""
        edges = set()
        for graph in self.contained_graphs:
            edges.update(graph.edges)
        return edges
    
    def get_logical_size(self) -> int:
        """
        Get the logical size of this area based on contained graphs.
        Size is NOT spatial but logical - number of graphs contained.
        """
        return len(self.contained_graphs)


class EGILogicalSystem:
    """
    The complete EGI logical system managing areas and graph operations.
    
    This system enforces the fundamental constraint that all operations
    are graph-to-graph, with proper logical-spatial correspondence.
    """
    
    def __init__(self, sheet_id: str):
        self.sheet_id = sheet_id
        self.logical_areas: Dict[str, LogicalArea] = {}
        self.area_hierarchy: Dict[str, List[str]] = {}  # parent -> children
        
        # Create the root sheet area (no negation)
        self.root_area = LogicalArea(sheet_id, parent_area=None, is_cut=False)
        self.logical_areas[sheet_id] = self.root_area
    
    def create_negation_area(self, cut_id: str, parent_area_id: str) -> bool:
        """
        Create a negation area (cut) within a parent area.
        This represents the logical operator ~[].
        """
        if parent_area_id not in self.logical_areas:
            return False
        
        parent_area = self.logical_areas[parent_area_id]
        
        # Create the cut area
        cut_area = LogicalArea(cut_id, parent_area=parent_area_id, is_cut=True)
        self.logical_areas[cut_id] = cut_area
        
        # Update hierarchy
        parent_area.add_child_area(cut_id)
        if parent_area_id not in self.area_hierarchy:
            self.area_hierarchy[parent_area_id] = []
        self.area_hierarchy[parent_area_id].append(cut_id)
        
        return True
    
    def add_graph_to_area(self, graph: EGIGraph, target_area_id: str) -> bool:
        """
        Add a complete graph to a logical area.
        This is the fundamental operation - no direct element addition allowed.
        """
        if target_area_id not in self.logical_areas:
            return False
        
        target_area = self.logical_areas[target_area_id]
        return target_area.add_graph(graph)
    
    def create_vertex_graph(self, vertex_id: str) -> EGIGraph:
        """Create a graph containing only a single vertex."""
        return EGIGraph(
            graph_id=f"graph_{vertex_id}",
            vertices={vertex_id},
            edges=set(),
            cuts=set(),
            nu_mapping={},
            relation_mapping={}
        )
    
    def create_edge_graph(self, edge_id: str, relation_name: str, 
                         incident_vertices: Set[str]) -> EGIGraph:
        """Create a graph containing an edge and its incident vertices."""
        return EGIGraph(
            graph_id=f"graph_{edge_id}",
            vertices=incident_vertices,
            edges={edge_id},
            cuts=set(),
            nu_mapping={edge_id: incident_vertices},
            relation_mapping={edge_id: relation_name}
        )
    
    def can_conjoin_graphs(self, area1_id: str, area2_id: str) -> bool:
        """
        Check if graphs in two areas can be conjoined.
        Conjunction cannot happen across negation boundaries.
        """
        if area1_id == area2_id:
            return True  # Same area - conjunction allowed
        
        # Check if areas are separated by negation
        return not self._separated_by_negation(area1_id, area2_id)
    
    def _separated_by_negation(self, area1_id: str, area2_id: str) -> bool:
        """Check if two areas are separated by a negation boundary."""
        # Find common ancestor and check for cuts in between
        path1 = self._get_path_to_root(area1_id)
        path2 = self._get_path_to_root(area2_id)
        
        # Find common ancestor
        common_ancestor = None
        for area in path1:
            if area in path2:
                common_ancestor = area
                break
        
        if not common_ancestor:
            return True  # No common ancestor - separated
        
        # Check if there are cuts between areas and common ancestor
        path1_to_ancestor = path1[:path1.index(common_ancestor)]
        path2_to_ancestor = path2[:path2.index(common_ancestor)]
        
        # If either path contains a cut, they're separated by negation
        for area_id in path1_to_ancestor + path2_to_ancestor:
            if area_id in self.logical_areas and self.logical_areas[area_id].is_cut:
                return True
        
        return False
    
    def _get_path_to_root(self, area_id: str) -> List[str]:
        """Get the path from an area to the root sheet."""
        path = []
        current = area_id
        
        while current and current in self.logical_areas:
            path.append(current)
            current = self.logical_areas[current].parent_area
        
        return path
    
    def get_area_logical_content(self, area_id: str) -> Dict[str, Any]:
        """Get the complete logical content of an area."""
        if area_id not in self.logical_areas:
            return {}
        
        area = self.logical_areas[area_id]
        
        return {
            'area_id': area_id,
            'is_negation': area.is_cut,
            'parent_area': area.parent_area,
            'child_areas': area.child_areas.copy(),
            'contained_graphs': [
                {
                    'graph_id': graph.graph_id,
                    'vertices': list(graph.vertices),
                    'edges': list(graph.edges),
                    'cuts': list(graph.cuts),
                    'nu_mapping': {k: list(v) for k, v in graph.nu_mapping.items()},
                    'relations': graph.relation_mapping.copy()
                }
                for graph in area.contained_graphs
            ],
            'logical_size': area.get_logical_size()
        }
    
    def validate_logical_consistency(self) -> List[str]:
        """Validate that the logical structure is consistent."""
        violations = []
        
        # Check that all cuts have proper parent areas
        for area_id, area in self.logical_areas.items():
            if area.is_cut and not area.parent_area:
                violations.append(f"Cut {area_id} has no parent area")
        
        # Check that conjunction constraints are respected
        # (This would be expanded based on specific EGI rules)
        
        return violations
