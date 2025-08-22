#!/usr/bin/env python3
"""
EGI System - Clean, Simple, Parsimonious

Single source of truth for existential graphs with minimal operations:
1. EGI Repository - maintains canonical graph state
2. Formal Operations - modify EGI while preserving Dau compliance  
3. Projections - generate EGIF/EGDF from EGI on demand

No complex controllers, pipelines, or adapters. Just essential operations.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from abc import ABC, abstractmethod
from copy import deepcopy
import uuid

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut


@dataclass
class OperationResult:
    """Result of applying an operation to EGI."""
    success: bool
    error: Optional[str] = None
    modified_elements: Set[str] = None


class EGIOperation(ABC):
    """Base class for operations that modify EGI while preserving Dau compliance."""
    
    @abstractmethod
    def apply(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        """Apply operation and return new EGI state."""
        pass
    
    @abstractmethod
    def validate(self, egi: RelationalGraphWithCuts) -> bool:
        """Check if operation preserves Dau compliance."""
        pass


class InsertVertex(EGIOperation):
    """Insert a vertex into specified area."""
    
    def __init__(self, vertex_id: str, area_id: str = 'sheet'):
        self.vertex_id = vertex_id
        self.area_id = area_id
    
    def validate(self, egi: RelationalGraphWithCuts) -> bool:
        # Vertex must not already exist
        return not any(v.id == self.vertex_id for v in egi.V)
    
    def apply(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        new_egi = deepcopy(egi)
        new_egi.V.add(Vertex(id=self.vertex_id))
        
        # Add to area
        if self.area_id not in new_egi.area:
            new_egi.area[self.area_id] = frozenset()
        new_egi.area[self.area_id] = new_egi.area[self.area_id] | {self.vertex_id}
        
        return new_egi


class InsertEdge(EGIOperation):
    """Insert an edge (predicate) connecting vertices."""
    
    def __init__(self, edge_id: str, relation: str, vertices: List[str], area_id: str = 'sheet'):
        self.edge_id = edge_id
        self.relation = relation
        self.vertices = vertices
        self.area_id = area_id
    
    def validate(self, egi: RelationalGraphWithCuts) -> bool:
        # Edge must not exist, vertices must exist
        if any(e.id == self.edge_id for e in egi.E):
            return False
        return all(any(v.id == vid for v in egi.V) for vid in self.vertices)
    
    def apply(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        new_egi = deepcopy(egi)
        new_egi.E.add(Edge(id=self.edge_id))
        new_egi.rel[self.edge_id] = self.relation
        new_egi.nu[self.edge_id] = tuple(self.vertices)
        
        # Add to area
        if self.area_id not in new_egi.area:
            new_egi.area[self.area_id] = frozenset()
        new_egi.area[self.area_id] = new_egi.area[self.area_id] | {self.edge_id}
        
        return new_egi


class InsertCut(EGIOperation):
    """Insert a cut (negation area)."""
    
    def __init__(self, cut_id: str, parent_area: str = 'sheet'):
        self.cut_id = cut_id
        self.parent_area = parent_area
    
    def validate(self, egi: RelationalGraphWithCuts) -> bool:
        return not any(c.id == self.cut_id for c in egi.Cut)
    
    def apply(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        new_egi = deepcopy(egi)
        new_egi.Cut.add(Cut(id=self.cut_id))
        new_egi.area[self.cut_id] = frozenset()
        
        return new_egi


class EGIRepository:
    """Single source of truth for EGI state."""
    
    def __init__(self, initial_egi: RelationalGraphWithCuts = None):
        self.egi = initial_egi or RelationalGraphWithCuts()
        self.observers: List[callable] = []
    
    def apply(self, operation: EGIOperation) -> OperationResult:
        """Apply operation if valid."""
        if not operation.validate(self.egi):
            return OperationResult(success=False, error="Operation validation failed")
        
        try:
            new_egi = operation.apply(self.egi)
            self.egi = new_egi
            self._notify_observers()
            return OperationResult(success=True)
        except Exception as e:
            return OperationResult(success=False, error=str(e))
    
    def get_state(self) -> RelationalGraphWithCuts:
        """Get current EGI state (read-only)."""
        return deepcopy(self.egi)
    
    def observe(self, callback: callable):
        """Add observer for state changes."""
        self.observers.append(callback)
    
    def _notify_observers(self):
        """Notify observers of state change."""
        for observer in self.observers:
            observer(self.egi)


class EGIFProjection:
    """Generate EGIF linear form from EGI."""
    
    def generate(self, egi: RelationalGraphWithCuts) -> str:
        """Convert EGI to EGIF string."""
        from egif_generator_dau import EGIFGenerator
        return EGIFGenerator().generate_egif(egi)


class EGDFProjection:
    """Generate EGDF visual form from EGI."""
    
    def generate(self, egi: RelationalGraphWithCuts) -> Dict:
        """Convert EGI to EGDF document with basic layout."""
        # Simple spatial layout - just position elements
        spatial_primitives = []
        
        # Position vertices
        for i, vertex in enumerate(egi.V):
            spatial_primitives.append({
                'type': 'vertex',
                'id': vertex.id,
                'bounds': {'x': i * 100, 'y': 50, 'width': 80, 'height': 30}
            })
        
        # Position edges
        for i, edge in enumerate(egi.E):
            spatial_primitives.append({
                'type': 'edge', 
                'id': edge.id,
                'bounds': {'x': i * 100, 'y': 100, 'width': 120, 'height': 20}
            })
        
        # Position cuts
        for i, cut in enumerate(egi.Cut):
            spatial_primitives.append({
                'type': 'cut',
                'id': cut.id, 
                'bounds': {'x': i * 150, 'y': 150, 'width': 200, 'height': 100}
            })
        
        return {
            'egi_structure': {
                'vertices': [v.id for v in egi.V],
                'edges': [e.id for e in egi.E], 
                'cuts': [c.id for c in egi.Cut],
                'relations': dict(egi.rel),
                'connections': dict(egi.nu),
                'areas': {k: list(v) for k, v in egi.area.items()}
            },
            'visual_layout': {
                'spatial_primitives': spatial_primitives
            }
        }


class EGISystem:
    """Complete EGI system - repository + projections."""
    
    def __init__(self):
        self.repository = EGIRepository()
        self.egif_projection = EGIFProjection()
        self.egdf_projection = EGDFProjection()
    
    # Repository operations
    def insert_vertex(self, vertex_id: str, area_id: str = 'sheet') -> OperationResult:
        return self.repository.apply(InsertVertex(vertex_id, area_id))
    
    def insert_edge(self, edge_id: str, relation: str, vertices: List[str], area_id: str = 'sheet') -> OperationResult:
        return self.repository.apply(InsertEdge(edge_id, relation, vertices, area_id))
    
    def insert_cut(self, cut_id: str, parent_area: str = 'sheet') -> OperationResult:
        return self.repository.apply(InsertCut(cut_id, parent_area))
    
    # Projections
    def to_egif(self) -> str:
        return self.egif_projection.generate(self.repository.get_state())
    
    def to_egdf(self) -> Dict:
        return self.egdf_projection.generate(self.repository.get_state())
    
    def get_egi(self) -> RelationalGraphWithCuts:
        return self.repository.get_state()
    
    def observe_changes(self, callback: callable):
        self.repository.observe(callback)


# Factory
def create_egi_system() -> EGISystem:
    """Create new EGI system instance."""
    return EGISystem()
