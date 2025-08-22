#!/usr/bin/env python3
"""
EGI Repository - Single Source of Truth for Graph State

This repository maintains the canonical EGI representation and ensures
all modifications preserve Dau compliance through formal operations.
"""

from typing import Dict, List, Optional, Any, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import uuid
from copy import deepcopy

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut


class OperationType(Enum):
    """Types of formal operations on EGI."""
    INSERT_VERTEX = "insert_vertex"
    DELETE_VERTEX = "delete_vertex"
    INSERT_EDGE = "insert_edge"
    DELETE_EDGE = "delete_edge"
    INSERT_CUT = "insert_cut"
    DELETE_CUT = "delete_cut"
    MOVE_ELEMENT = "move_element"
    MODIFY_RELATION = "modify_relation"


@dataclass
class OperationResult:
    """Result of applying a formal operation."""
    success: bool
    error_message: Optional[str] = None
    modified_elements: Set[str] = None
    egi_state: Optional[RelationalGraphWithCuts] = None


class FormalOperation(ABC):
    """Base class for all EGI operations that preserve Dau compliance."""
    
    def __init__(self, operation_id: str = None):
        self.operation_id = operation_id or str(uuid.uuid4())
        self.operation_type: OperationType = None
    
    @abstractmethod
    def validate(self, egi: RelationalGraphWithCuts) -> bool:
        """Validate that this operation preserves Dau compliance."""
        pass
    
    @abstractmethod
    def apply(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        """Apply the operation to the EGI, returning new state."""
        pass
    
    @abstractmethod
    def get_affected_elements(self) -> Set[str]:
        """Return IDs of elements affected by this operation."""
        pass


class InsertVertexOperation(FormalOperation):
    """Formal operation to insert a vertex into the EGI."""
    
    def __init__(self, vertex_id: str, area_id: str = None, **kwargs):
        super().__init__()
        self.operation_type = OperationType.INSERT_VERTEX
        self.vertex_id = vertex_id
        self.area_id = area_id or 'sheet'
        self.vertex_data = kwargs
    
    def validate(self, egi: RelationalGraphWithCuts) -> bool:
        """Ensure vertex doesn't already exist and area is valid."""
        # Check vertex doesn't exist
        if any(v.id == self.vertex_id for v in egi.V):
            return False
        
        # Check area exists (if not sheet)
        if self.area_id != 'sheet':
            if not any(c.id == self.area_id for c in egi.Cut):
                return False
        
        return True
    
    def apply(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        """Insert vertex into EGI."""
        new_egi = deepcopy(egi)
        
        # Create new vertex
        vertex = Vertex(id=self.vertex_id, **self.vertex_data)
        new_egi.V.add(vertex)
        
        # Add to area mapping
        if self.area_id not in new_egi.area:
            new_egi.area[self.area_id] = frozenset()
        new_egi.area[self.area_id] = new_egi.area[self.area_id] | {self.vertex_id}
        
        return new_egi
    
    def get_affected_elements(self) -> Set[str]:
        return {self.vertex_id, self.area_id}


class EGIRepository:
    """Repository maintaining canonical EGI state with formal operations."""
    
    def __init__(self, initial_egi: RelationalGraphWithCuts = None):
        self.current_egi = initial_egi or RelationalGraphWithCuts()
        self.operation_history: List[FormalOperation] = []
        self.observers: List[callable] = []
    
    def get_current_state(self) -> RelationalGraphWithCuts:
        """Get current EGI state (read-only copy)."""
        return deepcopy(self.current_egi)
    
    def apply_operation(self, operation: FormalOperation) -> OperationResult:
        """Apply a formal operation to the EGI."""
        try:
            # Validate operation
            if not operation.validate(self.current_egi):
                return OperationResult(
                    success=False,
                    error_message=f"Operation {operation.operation_id} failed validation"
                )
            
            # Apply operation
            new_egi = operation.apply(self.current_egi)
            
            # Update state
            self.current_egi = new_egi
            self.operation_history.append(operation)
            
            # Notify observers
            self._notify_observers(operation)
            
            return OperationResult(
                success=True,
                modified_elements=operation.get_affected_elements(),
                egi_state=deepcopy(new_egi)
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"Operation {operation.operation_id} failed: {str(e)}"
            )
    
    def add_observer(self, observer: callable):
        """Add observer for EGI state changes."""
        self.observers.append(observer)
    
    def remove_observer(self, observer: callable):
        """Remove observer."""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def _notify_observers(self, operation: FormalOperation):
        """Notify all observers of state change."""
        for observer in self.observers:
            try:
                observer(self.current_egi, operation)
            except Exception as e:
                print(f"Observer notification failed: {e}")
    
    def get_operation_history(self) -> List[FormalOperation]:
        """Get history of applied operations."""
        return self.operation_history.copy()
    
    def validate_current_state(self) -> bool:
        """Validate that current EGI state is Dau-compliant."""
        # TODO: Implement comprehensive Dau compliance validation
        return True


# Factory function
def create_egi_repository(initial_egi: RelationalGraphWithCuts = None) -> EGIRepository:
    """Create a new EGI repository instance."""
    return EGIRepository(initial_egi)
