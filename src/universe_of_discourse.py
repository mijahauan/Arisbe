"""
Universe of Discourse - The Fundamental Entity

The Universe of Discourse (UoD) is the complete diachronic process of logical
reasoning. It captures both synchronic states (EGI snapshots) and diachronic
evolution (transformation history).

Key Insight:
- UoD = The entire film (diachronic process)
- EGI = A single frame (synchronic snapshot)
- Full meaning emerges from the sequence, not individual frames

Philosophical Foundation:
- Aligns with Peirce's pragmatism (meaning from transformations)
- Honors dialogical inquiry (justification through Endoporeutic Game)
- Captures fallibilism (knowledge evolves through inquiry)

See: UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md for complete philosophy
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from egi_core_dau import RelationalGraphWithCuts
from egi_transformation_history import (
    EGITransformationHistory,
    StateSnapshot,
    TransformationStep,
)


class UoDType(Enum):
    """
    Type of Universe of Discourse.
    
    Distinguishes between static (single state) and dynamic (full history) UoDs.
    """
    STANDALONE = "standalone"  # Single EGI state, no history (literature imports)
    HISTORICAL = "historical"  # Sequence of states + transformations (active reasoning)


class UoDCategory(Enum):
    """
    Category/provenance of Universe of Discourse.
    
    Distinguishes between static imports (literature examples) and dynamic
    reasoning sessions (user inquiry, proofs, games).
    """
    # Static imports (synchronic only, no transformation history)
    LITERATURE_EXAMPLE = "literature_example"  # Peirce, Roberts, Sowa, Dau examples
    CANONICAL_PATTERN = "canonical_pattern"    # Synthetic standard logical patterns
    
    # Dynamic reasoning sessions (full diachronic history)
    ACTIVE_INQUIRY = "active_inquiry"          # User's ongoing reasoning session
    THEOREM_PROOF = "theorem_proof"            # Mathematical proof in progress
    DOMAIN_MODEL = "domain_model"              # Real-world domain modeling
    EPG_SESSION = "epg_session"                # Endoporeutic Game session
    PRACTICE_SESSION = "practice_session"      # Ergasterion practice session
    
    # Archived reasoning (completed diachronic processes)
    COMPLETED_PROOF = "completed_proof"        # Finished, validated theorem proof
    PUBLISHED_ARGUMENT = "published_argument"  # Validated, published reasoning
    
    # Legacy compatibility
    PEIRCE = "peirce"                          # Alias for LITERATURE_EXAMPLE (Peirce)
    SCHOLARS = "scholars"                      # Alias for LITERATURE_EXAMPLE (scholars)
    USER_CREATED = "user_created"              # Alias for ACTIVE_INQUIRY


@dataclass
class UoDMetadata:
    """
    Metadata for a Universe of Discourse.
    
    Captures identity, provenance, authorship, and temporal information
    for both static and dynamic UoDs.
    """
    
    # Core identity
    uod_id: str                                # Unique identifier
    uod_type: UoDType                          # STANDALONE or HISTORICAL
    name: str                                  # Human-readable name
    description: str                           # Description of UoD purpose/content
    category: UoDCategory                      # Provenance/type of UoD
    
    # Timestamps
    created: datetime                          # When UoD was created
    last_modified: datetime                    # Last modification time
    
    # History information (for HISTORICAL UoDs)
    current_state_id: Optional[str] = None     # Current state in history
    total_states: int = 1                      # Total number of states
    total_transformations: int = 0             # Total transformations applied
    
    # Authorship and collaboration
    authors: List[str] = field(default_factory=list)       # Authors/contributors
    tags: Set[str] = field(default_factory=set)            # User-defined tags
    
    # Storage and references
    corpus_path: Optional[Path] = None         # Path in corpus
    source_citation: Optional[str] = None      # Citation (for literature imports)
    related_uods: List[str] = field(default_factory=list)  # Related UoD IDs
    
    # Domain and semantic context
    domain_contexts: Set[str] = field(default_factory=set)  # Domain contexts
    natural_language_summary: Optional[str] = None          # NL summary
    
    # Rendering and presentation
    style_name: str = "dau-compliant@1.0"  # Visual style for rendering (dau/peirce/sowa)
    
    # ===== Backward Compatibility Properties =====
    
    @property
    def entity_id(self) -> str:
        """Alias for uod_id (backward compatibility)."""
        return self.uod_id
    
    @property
    def entity_type(self) -> UoDType:
        """Alias for uod_type (backward compatibility)."""
        return self.uod_type
    
    # ===== Serialization =====
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "uod_id": self.uod_id,
            "uod_type": self.uod_type.value,
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
            "related_uods": self.related_uods,
            "domain_contexts": list(self.domain_contexts),
            "natural_language_summary": self.natural_language_summary,
            "style_name": self.style_name,
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'UoDMetadata':
        """
        Deserialize from dictionary.
        
        Supports both old (entity_id, entity_type) and new (uod_id, uod_type) field names
        for backward compatibility during migration.
        """
        # Backward compatibility: accept both old and new field names
        uod_id = data.get("uod_id") or data.get("entity_id")
        uod_type_str = data.get("uod_type") or data.get("entity_type", "standalone")
        category_str = data.get("category", "user_created")
        
        # Handle category aliases for backward compatibility
        category_map = {
            "peirce": UoDCategory.LITERATURE_EXAMPLE,
            "scholars": UoDCategory.LITERATURE_EXAMPLE,
            "canonical": UoDCategory.CANONICAL_PATTERN,
            "user_created": UoDCategory.ACTIVE_INQUIRY,
            "epg": UoDCategory.EPG_SESSION,
            "theorem_proving": UoDCategory.THEOREM_PROOF,
            "domain_modeling": UoDCategory.DOMAIN_MODEL,
            "universe": UoDCategory.ACTIVE_INQUIRY,
        }
        
        # Get category, with fallback handling
        if isinstance(category_str, str) and category_str in category_map:
            category = category_map[category_str]
        else:
            try:
                category = UoDCategory(category_str)
            except ValueError:
                category = UoDCategory.ACTIVE_INQUIRY  # Safe default
        
        return UoDMetadata(
            uod_id=uod_id,
            uod_type=UoDType(uod_type_str),
            name=data["name"],
            description=data["description"],
            category=category,
            created=datetime.fromisoformat(data["created"]),
            last_modified=datetime.fromisoformat(data["last_modified"]),
            current_state_id=data.get("current_state_id"),
            total_states=data.get("total_states", 1),
            total_transformations=data.get("total_transformations", 0),
            authors=data.get("authors", []),
            tags=set(data.get("tags", [])),
            source_citation=data.get("source_citation"),
            related_uods=data.get("related_uods", []),
            domain_contexts=set(data.get("domain_contexts", [])),
            natural_language_summary=data.get("natural_language_summary"),
            style_name=data.get("style_name", "dau-compliant@1.0"),
        )


@dataclass
class UniverseOfDiscourse:
    """
    The fundamental entity: a diachronic process of logical reasoning.
    
    A Universe of Discourse (UoD) is NOT a static EGI diagram, but the complete
    evolving environment in which EGIs exist, make sense, and undergo justified
    transformations.
    
    Components:
    1. Transformation History (the log): Recorded sequence of justified rule applications
    2. Synchronic States (the frames): (EGI, LayoutDeltas) at each point in time
    3. In-forming Events (the driver): User actions that drive evolution
    
    Metaphor: 
    - UoD = The entire film (diachronic process)
    - EGI = A single frame or photograph (synchronic snapshot)
    - Full meaning emerges from watching the sequence unfold
    
    Can represent:
    1. Static UoD: Single EGI state, no history (literature imports)
    2. Dynamic UoD: Complete transformation history (active reasoning)
    
    Usage Across Modules:
    - Organon (Archive): Browse history, explore states, export proofs
    - Ergasterion (Workshop): Practice transformations (ephemeral, no main UoD)
    - Agon (Arena): Validate changes, record history, Endoporeutic Game
    
    See: UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md for complete philosophy
    """
    
    # Core metadata
    metadata: UoDMetadata

    # Synchronic aspect: current state
    current_egi: RelationalGraphWithCuts       # Current logical structure
    current_layout_deltas: Optional[Dict[str, Any]] = None  # User layout preferences

    # Diachronic aspect: transformation history
    history: Optional[EGITransformationHistory] = None
    
    # Cached linear forms (invalidated on state change)
    _current_egif: Optional[str] = None
    _current_cgif: Optional[str] = None
    _current_clif: Optional[str] = None
    
    # ===== Identity Properties =====
    
    @property
    def uod_id(self) -> str:
        """Get UoD unique identifier."""
        return self.metadata.uod_id
    
    @property
    def name(self) -> str:
        """Get UoD human-readable name."""
        return self.metadata.name
    
    @property
    def uod_type(self) -> UoDType:
        """Get UoD type (STANDALONE or HISTORICAL)."""
        return self.metadata.uod_type
    
    @property
    def category(self) -> UoDCategory:
        """Get UoD category/provenance."""
        return self.metadata.category
    
    # ===== Type Checking Properties =====
    
    @property
    def is_standalone(self) -> bool:
        """
        Check if UoD is standalone (static, no history tracking).
        
        Returns True for literature imports and canonical patterns that
        have no transformation history tracking.
        
        A UoD is standalone if:
        1. It has NO history object, AND
        2. Its type is STANDALONE
        """
        return (
            self.history is None 
            and self.metadata.uod_type == UoDType.STANDALONE
        )
    
    @property
    def is_historical(self) -> bool:
        """
        Check if UoD has transformation history (dynamic reasoning).
        
        Returns True for active inquiry sessions, proofs, games, etc.
        that track complete diachronic evolution.
        
        A UoD is historical if:
        1. It has a history object (even with just initial state), OR
        2. Its type is HISTORICAL
        """
        return (
            self.history is not None 
            or self.metadata.uod_type == UoDType.HISTORICAL
        )
    
    @property
    def is_static(self) -> bool:
        """
        Check if UoD is a static import (literature example, canonical pattern).
        
        Static UoDs are imported from external sources and typically have
        no transformation history.
        """
        return self.category in {
            UoDCategory.LITERATURE_EXAMPLE,
            UoDCategory.CANONICAL_PATTERN,
            UoDCategory.PEIRCE,
            UoDCategory.SCHOLARS,
        }
    
    @property
    def is_dynamic(self) -> bool:
        """
        Check if UoD is a dynamic reasoning session.
        
        Dynamic UoDs are created and evolved by users through transformations,
        with complete history tracking.
        """
        return self.category in {
            UoDCategory.ACTIVE_INQUIRY,
            UoDCategory.THEOREM_PROOF,
            UoDCategory.DOMAIN_MODEL,
            UoDCategory.EPG_SESSION,
            UoDCategory.PRACTICE_SESSION,
            UoDCategory.USER_CREATED,
        }
    
    # ===== Linear Form Accessors =====
    
    def get_current_egif(self) -> str:
        """
        Get EGIF (Existential Graph Interchange Format) for current state.
        
        Cached for performance; invalidated on state change.
        """
        if self._current_egif is None:
            from egif_generator_dau import generate_egif
            self._current_egif = generate_egif(self.current_egi)
        return self._current_egif
    
    def get_current_cgif(self) -> Optional[str]:
        """
        Get CGIF (Conceptual Graph Interchange Format) for current state.
        
        Returns None if generation fails.
        """
        if self._current_cgif is None:
            try:
                from cgif_generator import generate_cgif
                self._current_cgif = generate_cgif(self.current_egi)
            except Exception:
                return None
        return self._current_cgif
    
    def get_current_clif(self) -> Optional[str]:
        """
        Get CLIF (Common Logic Interchange Format) for current state.
        
        Returns None if generation fails.
        """
        if self._current_clif is None:
            try:
                from clif_generator import generate_clif
                self._current_clif = generate_clif(self.current_egi)
            except Exception:
                return None
        return self._current_clif
    
    # ===== History Navigation =====
    
    def get_state(self, state_id: str) -> StateSnapshot:
        """
        Get a specific historical state by ID.
        
        Args:
            state_id: State identifier
            
        Returns:
            State snapshot (EGI + metadata at that point in time)
            
        Raises:
            ValueError: If UoD is standalone or state not found
        """
        if not self.is_historical:
            raise ValueError("Cannot get state from standalone UoD (no history)")
        
        if state_id not in self.history.states:
            raise ValueError(f"State {state_id} not found in UoD history")
        
        return self.history.states[state_id]
    
    def get_transformation(self, step_id: str) -> TransformationStep:
        """
        Get a specific transformation step by ID.
        
        Args:
            step_id: Transformation step identifier
            
        Returns:
            Transformation step (rule, context, result)
            
        Raises:
            ValueError: If UoD is standalone or step not found
        """
        if not self.is_historical:
            raise ValueError("Cannot get transformation from standalone UoD (no history)")
        
        if step_id not in self.history.transformations:
            raise ValueError(f"Transformation {step_id} not found in UoD history")
        
        return self.history.transformations[step_id]
    
    def get_state_range(self, from_state_id: str, to_state_id: str) -> List[StateSnapshot]:
        """
        Get sequence of states between two points in history.
        
        Args:
            from_state_id: Starting state
            to_state_id: Ending state
            
        Returns:
            List of state snapshots in chronological order
            
        Raises:
            ValueError: If UoD is standalone or states not found
        """
        if not self.is_historical:
            raise ValueError("Cannot get state range from standalone UoD (no history)")
        
        # Get path between states
        from_idx = self.history.state_sequence.index(from_state_id)
        to_idx = self.history.state_sequence.index(to_state_id)
        
        if from_idx > to_idx:
            from_idx, to_idx = to_idx, from_idx
        
        state_ids = self.history.state_sequence[from_idx:to_idx + 1]
        return [self.history.states[state_id] for state_id in state_ids]
    
    def get_current_state(self) -> StateSnapshot:
        """
        Get the current state snapshot.
        
        Returns:
            Current state snapshot
            
        Raises:
            ValueError: If UoD is standalone (no history)
        """
        if not self.is_historical:
            raise ValueError("Cannot get current state from standalone UoD (no history)")
        
        return self.history.get_current_state()
    
    # ===== State Management =====
    
    def promote_to_historical(self, initial_description: str = "Initial state"):
        """
        Promote standalone UoD to historical by creating initial snapshot.
        
        This converts a static UoD (e.g., literature import) into a dynamic
        UoD with transformation history tracking.
        
        Args:
            initial_description: Description of initial state
            
        Effects:
            - Creates EGITransformationHistory
            - Adds initial StateSnapshot
            - Updates metadata to HISTORICAL type
        """
        if self.history is not None:
            return  # Already has history, no-op
        
        # Create history (EGITransformationHistory creates initial state internally)
        self.history = EGITransformationHistory(
            initial_egi=self.current_egi,
            description=initial_description
        )
        
        # Update initial state with layout deltas
        if self.current_layout_deltas:
            initial_state = self.history.get_current_state()
            if initial_state.diagram_metadata is None:
                initial_state.diagram_metadata = {}
            initial_state.diagram_metadata["layout_deltas"] = self.current_layout_deltas
        
        # Update metadata
        self.metadata.uod_type = UoDType.HISTORICAL
        self.metadata.current_state_id = self.history.current_state_id
        self.metadata.total_states = 1
        self.metadata.last_modified = datetime.now()
    
    def update_current_state(
        self, 
        new_egi: RelationalGraphWithCuts,
        new_layout_deltas: Optional[Dict[str, Any]] = None
    ):
        """
        Update current state (invalidates caches).
        
        Args:
            new_egi: New current EGI
            new_layout_deltas: Optional new layout deltas (None = keep existing)
            
        Effects:
            - Updates current_egi
            - Updates current_layout_deltas if provided
            - Invalidates linear form caches
            - Updates last_modified timestamp
        """
        self.current_egi = new_egi
        
        if new_layout_deltas is not None:
            self.current_layout_deltas = new_layout_deltas
        
        # Invalidate caches
        self._current_egif = None
        self._current_cgif = None
        self._current_clif = None

        # Update metadata
        self.metadata.last_modified = datetime.now()


# ===== Backward Compatibility Aliases =====
# These allow existing code to continue working during transition period

# Type aliases
EntityType = UoDType           # Old name → New name
EntityCategory = UoDCategory   # Old name → New name
EntityMetadata = UoDMetadata   # Old name → New name
GraphEntity = UniverseOfDiscourse  # Old name → New name

# Note: After migration, these aliases can be removed and all code
# updated to use the new names directly.
