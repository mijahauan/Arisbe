"""
GraphEntity - Unified Diachronic-Synchronic Model

Represents both standalone EGIs and historical sequences.
Foundation for scalable storage and access across all GUI modes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Literal, Optional, Set

from egi_core_dau import RelationalGraphWithCuts
from egi_transformation_history import (
    EGITransformationHistory,
    StateSnapshot,
    TransformationStep,
)


class EntityType(Enum):
    """Type of graph entity."""
    STANDALONE = "standalone"  # Single EGI state, no history
    HISTORICAL = "historical"  # Sequence of states + transformations


class EntityCategory(Enum):
    """Category/provenance of entity."""
    PEIRCE = "peirce"              # From Peirce's writings
    SCHOLARS = "scholars"          # From secondary literature
    CANONICAL = "canonical"        # Synthetic standard patterns
    EPG = "epg"                    # Endoporeutic Game positions
    THEOREM_PROVING = "theorem_proving"  # Mathematical proofs
    DOMAIN_MODELING = "domain_modeling"  # Real-world applications
    USER_CREATED = "user_created"  # User-generated content
    UNIVERSE = "universe"          # Living universe of discourse


@dataclass
class EntityMetadata:
    """Metadata for a graph entity."""
    
    entity_id: str
    entity_type: EntityType
    name: str
    description: str
    category: EntityCategory
    
    # Timestamps
    created: datetime
    last_modified: datetime
    
    # History info (for historical entities)
    current_state_id: Optional[str] = None
    total_states: int = 1
    total_transformations: int = 0
    
    # Authorship and collaboration
    authors: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    
    # Storage locations
    corpus_path: Optional[Path] = None
    
    # Source citation (for literature examples)
    source_citation: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "created": self.created.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "current_state_id": self.current_state_id,
            "total_states": self.total_states,
            "total_transformations": self.total_transformations,
            "authors": self.authors,
            "tags": list(self.tags),
            "source_citation": self.source_citation,
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'EntityMetadata':
        """Deserialize from dictionary."""
        return EntityMetadata(
            entity_id=data["entity_id"],
            entity_type=EntityType(data["entity_type"]),
            name=data["name"],
            description=data["description"],
            category=EntityCategory(data["category"]),
            created=datetime.fromisoformat(data["created"]),
            last_modified=datetime.fromisoformat(data["last_modified"]),
            current_state_id=data.get("current_state_id"),
            total_states=data.get("total_states", 1),
            total_transformations=data.get("total_transformations", 0),
            authors=data.get("authors", []),
            tags=set(data.get("tags", [])),
            source_citation=data.get("source_citation"),
        )


@dataclass
class GraphEntity:
    """
    Unified entity representing both synchronic and diachronic aspects.
    
    Can represent:
    1. Standalone EGI (single state, no history)
    2. Historical sequence (multiple states + transformations)
    
    Provides unified interface for corpus management and GUI access.
    """
    
    # Metadata
    metadata: EntityMetadata
    
    # Synchronic aspect (current state)
    current_egi: RelationalGraphWithCuts
    
    # Diachronic aspect (for historical entities)
    history: Optional[EGITransformationHistory] = None
    
    # Cached data
    _current_egif: Optional[str] = None
    _current_cgif: Optional[str] = None
    _current_clif: Optional[str] = None
    
    @property
    def entity_id(self) -> str:
        """Get entity ID."""
        return self.metadata.entity_id
    
    @property
    def name(self) -> str:
        """Get entity name."""
        return self.metadata.name
    
    @property
    def entity_type(self) -> EntityType:
        """Get entity type."""
        return self.metadata.entity_type
    
    @property
    def is_standalone(self) -> bool:
        """Check if entity is standalone (no history)."""
        return (
            self.history is None 
            or len(self.history.states) <= 1
        )
    
    @property
    def is_historical(self) -> bool:
        """Check if entity has transformation history."""
        return (
            self.history is not None 
            and len(self.history.states) > 1
        )
    
    def get_current_egif(self) -> str:
        """Get EGIF for current state."""
        if self._current_egif is None:
            from egif_generator_dau import generate_egif
            self._current_egif = generate_egif(self.current_egi)
        return self._current_egif
    
    def get_current_cgif(self) -> Optional[str]:
        """Get CGIF for current state."""
        if self._current_cgif is None:
            try:
                from cgif_generator import generate_cgif
                self._current_cgif = generate_cgif(self.current_egi)
            except Exception:
                return None
        return self._current_cgif
    
    def get_current_clif(self) -> Optional[str]:
        """Get CLIF for current state."""
        if self._current_clif is None:
            try:
                from clif_generator import generate_clif
                self._current_clif = generate_clif(self.current_egi)
            except Exception:
                return None
        return self._current_clif
    
    def get_state(self, state_id: str) -> StateSnapshot:
        """
        Get a specific historical state.
        
        Args:
            state_id: State identifier
            
        Returns:
            State snapshot
            
        Raises:
            ValueError: If entity is standalone or state not found
        """
        if not self.is_historical:
            raise ValueError("Cannot get state from standalone entity")
        
        if state_id not in self.history.states:
            raise ValueError(f"State {state_id} not found in history")
        
        return self.history.states[state_id]
    
    def get_transformation(self, step_id: str) -> TransformationStep:
        """
        Get a specific transformation step.
        
        Args:
            step_id: Transformation step identifier
            
        Returns:
            Transformation step
            
        Raises:
            ValueError: If entity is standalone or step not found
        """
        if not self.is_historical:
            raise ValueError("Cannot get transformation from standalone entity")
        
        if step_id not in self.history.steps:
            raise ValueError(f"Transformation {step_id} not found in history")
        
        return self.history.steps[step_id]
    
    def get_state_range(self, from_state_id: str, to_state_id: str) -> List[StateSnapshot]:
        """
        Get range of states in sequence.
        
        Args:
            from_state_id: Starting state
            to_state_id: Ending state
            
        Returns:
            List of state snapshots in order
        """
        if not self.is_historical:
            raise ValueError("Cannot get state range from standalone entity")
        
        # Get path between states
        path = self.history.get_path_between_states(from_state_id, to_state_id)
        return [self.history.states[state_id] for state_id in path]
    
    def promote_to_historical(self, initial_description: str = "Initial state"):
        """
        Promote standalone entity to historical by creating initial snapshot.
        
        Args:
            initial_description: Description of initial state
        """
        if self.is_historical:
            return  # Already historical
        
        from egi_transformation_history import EGITransformationHistory, StateSnapshot
        import uuid
        
        # Create initial state snapshot
        state_id = f"state_{uuid.uuid4().hex[:8]}"
        snapshot = StateSnapshot(
            state_id=state_id,
            egi=self.current_egi,
            timestamp=datetime.now(),
            step_number=0,
            description=initial_description,
            linear_forms={
                "egif": self.get_current_egif(),
            }
        )
        
        # Create history
        self.history = EGITransformationHistory(
            history_id=f"history_{self.entity_id}",
            initial_state=snapshot
        )
        
        # Update metadata
        self.metadata.entity_type = EntityType.HISTORICAL
        self.metadata.current_state_id = state_id
        self.metadata.total_states = 1
        self.metadata.last_modified = datetime.now()
    
    def update_current_state(self, new_egi: RelationalGraphWithCuts):
        """
        Update current state (invalidates caches).
        
        Args:
            new_egi: New current EGI
        """
        self.current_egi = new_egi
        
        # Invalidate caches
        self._current_egif = None
        self._current_cgif = None
        self._current_clif = None
        
        # Update metadata
        self.metadata.last_modified = datetime.now()
