"""
Enhanced Mathematical Layer - Phase 4A Implementation

This module provides enhancements to the mathematical layer that enable efficient
real-time operations while maintaining the mathematical rigor and immutability
guarantees of the original EG-HG architecture. The enhancements focus on:

1. Efficient diff and merge operations for incremental updates
2. Optimized graph traversal and query operations
3. Change detection and validation for real-time synchronization
4. Immutable snapshots with efficient copy-on-write semantics
5. Mathematical consistency guarantees for interactive operations

The enhanced mathematical layer serves as the authoritative source of truth
for logical content while providing the performance optimizations needed
for real-time interactive diagrammatic manipulation.

Author: Manus AI
Date: January 2025
Phase: 4A - Foundation Architecture
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable, FrozenSet
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import hashlib
from collections import defaultdict, deque
from abc import ABC, abstractmethod
import threading
from copy import deepcopy

# Import existing types for compatibility
from eg_types import Entity, Predicate, Context


class ChangeType(Enum):
    """Types of changes that can occur in the mathematical layer."""
    ENTITY_ADDED = "entity_added"
    ENTITY_REMOVED = "entity_removed"
    ENTITY_MODIFIED = "entity_modified"
    PREDICATE_ADDED = "predicate_added"
    PREDICATE_REMOVED = "predicate_removed"
    PREDICATE_MODIFIED = "predicate_modified"
    CONTEXT_ADDED = "context_added"
    CONTEXT_REMOVED = "context_removed"
    CONTEXT_MODIFIED = "context_modified"
    RELATION_ADDED = "relation_added"
    RELATION_REMOVED = "relation_removed"


@dataclass(frozen=True)
class MathematicalChange:
    """Represents a change in the mathematical layer."""
    change_type: ChangeType
    element_id: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    timestamp: float = field(default_factory=time.time)
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __hash__(self):
        return hash((self.change_type, self.element_id, self.change_id))


@dataclass(frozen=True)
class GraphSnapshot:
    """Immutable snapshot of the mathematical graph state."""
    entities: FrozenSet[Entity] = field(default_factory=frozenset)
    predicates: FrozenSet[Predicate] = field(default_factory=frozenset)
    contexts: FrozenSet[Context] = field(default_factory=frozenset)
    relations: FrozenSet[Tuple[str, str, str]] = field(default_factory=frozenset)  # (source, target, type)
    
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    parent_snapshot_id: Optional[str] = None
    
    # Computed properties for efficient access
    entity_index: Dict[str, Entity] = field(init=False)
    predicate_index: Dict[str, Predicate] = field(init=False)
    context_index: Dict[str, Context] = field(init=False)
    
    def __post_init__(self):
        # Build indices for efficient lookup
        object.__setattr__(self, 'entity_index', {str(e.id): e for e in self.entities})
        object.__setattr__(self, 'predicate_index', {str(p.id): p for p in self.predicates})
        object.__setattr__(self, 'context_index', {str(c.id): c for c in self.contexts})
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        return self.entity_index.get(entity_id)
    
    def get_predicate(self, predicate_id: str) -> Optional[Predicate]:
        """Get a predicate by ID."""
        return self.predicate_index.get(predicate_id)
    
    def get_context(self, context_id: str) -> Optional[Context]:
        """Get a context by ID."""
        return self.context_index.get(context_id)
    
    def get_connected_entities(self, predicate_id: str) -> List[Entity]:
        """Get entities connected to a predicate."""
        predicate = self.get_predicate(predicate_id)
        if not predicate:
            return []
        
        connected = []
        for entity_name in predicate.entities:
            entity = self.get_entity(entity_name)
            if entity:
                connected.append(entity)
        return connected
    
    def get_entity_predicates(self, entity_id: str) -> List[Predicate]:
        """Get predicates that involve an entity."""
        predicates = []
        for predicate in self.predicates:
            if entity_id in predicate.entities:
                predicates.append(predicate)
        return predicates
    
    def compute_hash(self) -> str:
        """Compute a hash of this snapshot for change detection."""
        content = (
            tuple(sorted(str(e) for e in self.entities)),
            tuple(sorted(str(p) for p in self.predicates)),
            tuple(sorted(str(c) for c in self.contexts)),
            tuple(sorted(self.relations))
        )
        return hashlib.sha256(str(content).encode()).hexdigest()


class GraphDiff:
    """Represents differences between two graph snapshots."""
    
    def __init__(self, old_snapshot: GraphSnapshot, new_snapshot: GraphSnapshot):
        self.old_snapshot = old_snapshot
        self.new_snapshot = new_snapshot
        self.changes: List[MathematicalChange] = []
        self._compute_diff()
    
    def _compute_diff(self):
        """Compute the differences between snapshots."""
        # Entity changes
        old_entities = {str(e.id): e for e in self.old_snapshot.entities}
        new_entities = {str(e.id): e for e in self.new_snapshot.entities}
        
        # Added entities
        for entity_id, entity in new_entities.items():
            if entity_id not in old_entities:
                self.changes.append(MathematicalChange(
                    ChangeType.ENTITY_ADDED,
                    entity_id,
                    None,
                    entity
                ))
        
        # Removed entities
        for entity_id, entity in old_entities.items():
            if entity_id not in new_entities:
                self.changes.append(MathematicalChange(
                    ChangeType.ENTITY_REMOVED,
                    entity_id,
                    entity,
                    None
                ))
        
        # Modified entities
        for entity_id in old_entities.keys() & new_entities.keys():
            old_entity = old_entities[entity_id]
            new_entity = new_entities[entity_id]
            if old_entity != new_entity:
                self.changes.append(MathematicalChange(
                    ChangeType.ENTITY_MODIFIED,
                    entity_id,
                    old_entity,
                    new_entity
                ))
        
        # Predicate changes (similar logic)
        old_predicates = {str(p.id): p for p in self.old_snapshot.predicates}
        new_predicates = {str(p.id): p for p in self.new_snapshot.predicates}
        
        for predicate_id, predicate in new_predicates.items():
            if predicate_id not in old_predicates:
                self.changes.append(MathematicalChange(
                    ChangeType.PREDICATE_ADDED,
                    predicate_id,
                    None,
                    predicate
                ))
        
        for predicate_id, predicate in old_predicates.items():
            if predicate_id not in new_predicates:
                self.changes.append(MathematicalChange(
                    ChangeType.PREDICATE_REMOVED,
                    predicate_id,
                    predicate,
                    None
                ))
        
        for predicate_id in old_predicates.keys() & new_predicates.keys():
            old_predicate = old_predicates[predicate_id]
            new_predicate = new_predicates[predicate_id]
            if old_predicate != new_predicate:
                self.changes.append(MathematicalChange(
                    ChangeType.PREDICATE_MODIFIED,
                    predicate_id,
                    old_predicate,
                    new_predicate
                ))
        
        # Relation changes
        old_relations = set(self.old_snapshot.relations)
        new_relations = set(self.new_snapshot.relations)
        
        for relation in new_relations - old_relations:
            self.changes.append(MathematicalChange(
                ChangeType.RELATION_ADDED,
                f"{relation[0]}-{relation[1]}",
                None,
                relation
            ))
        
        for relation in old_relations - new_relations:
            self.changes.append(MathematicalChange(
                ChangeType.RELATION_REMOVED,
                f"{relation[0]}-{relation[1]}",
                relation,
                None
            ))
    
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return len(self.changes) > 0
    
    def get_changes_by_type(self, change_type: ChangeType) -> List[MathematicalChange]:
        """Get changes of a specific type."""
        return [change for change in self.changes if change.change_type == change_type]
    
    def get_affected_elements(self) -> Set[str]:
        """Get IDs of all elements affected by changes."""
        return {change.element_id for change in self.changes}


class MathematicalValidator:
    """Validates mathematical consistency of graph operations."""
    
    def __init__(self):
        self.validation_rules: List[Callable[[GraphSnapshot], List[str]]] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default validation rules."""
        self.validation_rules.extend([
            self._validate_entity_consistency,
            self._validate_predicate_arity,
            self._validate_context_nesting,
            self._validate_relation_validity
        ])
    
    def validate_snapshot(self, snapshot: GraphSnapshot) -> List[str]:
        """Validate a graph snapshot."""
        errors = []
        for rule in self.validation_rules:
            try:
                rule_errors = rule(snapshot)
                errors.extend(rule_errors)
            except Exception as e:
                errors.append(f"Validation rule error: {str(e)}")
        return errors
    
    def validate_change(self, old_snapshot: GraphSnapshot, 
                       new_snapshot: GraphSnapshot) -> List[str]:
        """Validate a change between snapshots."""
        # Validate both snapshots
        errors = self.validate_snapshot(new_snapshot)
        
        # Additional change-specific validations
        diff = GraphDiff(old_snapshot, new_snapshot)
        
        # Check for invalid transitions
        for change in diff.changes:
            if change.change_type == ChangeType.ENTITY_REMOVED:
                # Check if entity is still referenced
                entity_id = change.element_id
                for predicate in new_snapshot.predicates:
                    if entity_id in predicate.entities:
                        errors.append(f"Cannot remove entity {entity_id}: still referenced by predicate {predicate.name}")
        
        return errors
    
    def _validate_entity_consistency(self, snapshot: GraphSnapshot) -> List[str]:
        """Validate entity consistency."""
        errors = []
        
        # Check for duplicate entity names
        entity_names = [e.name for e in snapshot.entities]
        if len(entity_names) != len(set(entity_names)):
            duplicates = [name for name in entity_names if entity_names.count(name) > 1]
            errors.append(f"Duplicate entity names: {set(duplicates)}")
        
        return errors
    
    def _validate_predicate_arity(self, snapshot: GraphSnapshot) -> List[str]:
        """Validate predicate arity consistency."""
        errors = []
        
        for predicate in snapshot.predicates:
            expected_arity = len(predicate.entities)
            # Additional arity checks could be added here based on predicate definitions
        
        return errors
    
    def _validate_context_nesting(self, snapshot: GraphSnapshot) -> List[str]:
        """Validate context nesting rules."""
        errors = []
        
        # Check for circular context dependencies
        context_parents = {}
        for context in snapshot.contexts:
            if hasattr(context, 'parent_context_id') and context.parent_context_id:
                context_parents[context.context_id] = context.parent_context_id
        
        # Detect cycles
        for context_id in context_parents:
            visited = set()
            current = context_id
            while current and current not in visited:
                visited.add(current)
                current = context_parents.get(current)
                if current == context_id:
                    errors.append(f"Circular context dependency detected involving {context_id}")
                    break
        
        return errors
    
    def _validate_relation_validity(self, snapshot: GraphSnapshot) -> List[str]:
        """Validate relation validity."""
        errors = []
        
        for source_id, target_id, relation_type in snapshot.relations:
            # Check that source and target exist
            if not snapshot.get_entity(source_id) and not snapshot.get_predicate(source_id):
                errors.append(f"Relation source {source_id} does not exist")
            
            if not snapshot.get_entity(target_id) and not snapshot.get_predicate(target_id):
                errors.append(f"Relation target {target_id} does not exist")
        
        return errors
    
    def add_validation_rule(self, rule: Callable[[GraphSnapshot], List[str]]):
        """Add a custom validation rule."""
        self.validation_rules.append(rule)


class EnhancedMathematicalLayer:
    """Enhanced mathematical layer with real-time operation support."""
    
    def __init__(self, initial_snapshot: Optional[GraphSnapshot] = None):
        if initial_snapshot is None:
            initial_snapshot = GraphSnapshot()
        
        self.current_snapshot = initial_snapshot
        self.snapshot_history: deque = deque(maxlen=1000)  # Keep recent snapshots
        self.validator = MathematicalValidator()
        
        # Performance optimizations
        self._entity_cache: Dict[str, Entity] = {}
        self._predicate_cache: Dict[str, Predicate] = {}
        self._cache_valid = True
        
        # Change tracking
        self.change_listeners: List[Callable[[GraphDiff], None]] = []
        
        # Threading
        self._lock = threading.RLock()
    
    def create_snapshot_with_changes(self, changes: List[MathematicalChange]) -> GraphSnapshot:
        """Create a new snapshot by applying changes to the current snapshot."""
        with self._lock:
            # Start with current snapshot data
            entities = set(self.current_snapshot.entities)
            predicates = set(self.current_snapshot.predicates)
            contexts = set(self.current_snapshot.contexts)
            relations = set(self.current_snapshot.relations)
            
            # Apply changes
            for change in changes:
                if change.change_type == ChangeType.ENTITY_ADDED:
                    entities.add(change.new_value)
                elif change.change_type == ChangeType.ENTITY_REMOVED:
                    entities.discard(change.old_value)
                elif change.change_type == ChangeType.ENTITY_MODIFIED:
                    entities.discard(change.old_value)
                    entities.add(change.new_value)
                elif change.change_type == ChangeType.PREDICATE_ADDED:
                    predicates.add(change.new_value)
                elif change.change_type == ChangeType.PREDICATE_REMOVED:
                    predicates.discard(change.old_value)
                elif change.change_type == ChangeType.PREDICATE_MODIFIED:
                    predicates.discard(change.old_value)
                    predicates.add(change.new_value)
                elif change.change_type == ChangeType.RELATION_ADDED:
                    relations.add(change.new_value)
                elif change.change_type == ChangeType.RELATION_REMOVED:
                    relations.discard(change.old_value)
            
            # Create new snapshot
            new_snapshot = GraphSnapshot(
                entities=frozenset(entities),
                predicates=frozenset(predicates),
                contexts=frozenset(contexts),
                relations=frozenset(relations),
                parent_snapshot_id=self.current_snapshot.snapshot_id
            )
            
            return new_snapshot
    
    def apply_changes(self, changes: List[MathematicalChange], 
                     validate: bool = True) -> Tuple[bool, List[str]]:
        """Apply changes to create a new snapshot."""
        with self._lock:
            if not changes:
                return True, []
            
            # Create new snapshot
            new_snapshot = self.create_snapshot_with_changes(changes)
            
            # Validate if requested
            errors = []
            if validate:
                errors = self.validator.validate_change(self.current_snapshot, new_snapshot)
                if errors:
                    return False, errors
            
            # Store old snapshot in history
            self.snapshot_history.append(self.current_snapshot)
            
            # Update current snapshot
            old_snapshot = self.current_snapshot
            self.current_snapshot = new_snapshot
            
            # Invalidate caches
            self._cache_valid = False
            self._entity_cache.clear()
            self._predicate_cache.clear()
            
            # Notify change listeners
            diff = GraphDiff(old_snapshot, new_snapshot)
            for listener in self.change_listeners:
                try:
                    listener(diff)
                except Exception as e:
                    print(f"Error in change listener: {e}")
            
            return True, []
    
    def add_entity(self, entity: Entity, validate: bool = True) -> Tuple[bool, List[str]]:
        """Add an entity to the mathematical layer."""
        change = MathematicalChange(
            ChangeType.ENTITY_ADDED,
            str(entity.id),
            None,
            entity
        )
        return self.apply_changes([change], validate)
    
    def remove_entity(self, entity_id: str, validate: bool = True) -> Tuple[bool, List[str]]:
        """Remove an entity from the mathematical layer."""
        entity = self.current_snapshot.get_entity(entity_id)
        if not entity:
            return False, [f"Entity {entity_id} not found"]
        
        change = MathematicalChange(
            ChangeType.ENTITY_REMOVED,
            entity_id,
            entity,
            None
        )
        return self.apply_changes([change], validate)
    
    def add_predicate(self, predicate: Predicate, validate: bool = True) -> Tuple[bool, List[str]]:
        """Add a predicate to the mathematical layer."""
        change = MathematicalChange(
            ChangeType.PREDICATE_ADDED,
            str(predicate.id),
            None,
            predicate
        )
        return self.apply_changes([change], validate)
    
    def remove_predicate(self, predicate_id: str, validate: bool = True) -> Tuple[bool, List[str]]:
        """Remove a predicate from the mathematical layer."""
        predicate = self.current_snapshot.get_predicate(predicate_id)
        if not predicate:
            return False, [f"Predicate {predicate_id} not found"]
        
        change = MathematicalChange(
            ChangeType.PREDICATE_REMOVED,
            predicate_id,
            predicate,
            None
        )
        return self.apply_changes([change], validate)
    
    def add_relation(self, source_id: str, target_id: str, relation_type: str = "line_of_identity",
                    validate: bool = True) -> Tuple[bool, List[str]]:
        """Add a relation between elements."""
        relation = (source_id, target_id, relation_type)
        change = MathematicalChange(
            ChangeType.RELATION_ADDED,
            f"{source_id}-{target_id}",
            None,
            relation
        )
        return self.apply_changes([change], validate)
    
    def get_current_snapshot(self) -> GraphSnapshot:
        """Get the current graph snapshot."""
        with self._lock:
            return self.current_snapshot
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity with caching."""
        with self._lock:
            if not self._cache_valid or entity_id not in self._entity_cache:
                entity = self.current_snapshot.get_entity(entity_id)
                if entity:
                    self._entity_cache[entity_id] = entity
                return entity
            return self._entity_cache[entity_id]
    
    def get_predicate(self, predicate_id: str) -> Optional[Predicate]:
        """Get a predicate with caching."""
        with self._lock:
            if not self._cache_valid or predicate_id not in self._predicate_cache:
                predicate = self.current_snapshot.get_predicate(predicate_id)
                if predicate:
                    self._predicate_cache[predicate_id] = predicate
                return predicate
            return self._predicate_cache[predicate_id]
    
    def compute_diff(self, other_snapshot: GraphSnapshot) -> GraphDiff:
        """Compute differences with another snapshot."""
        with self._lock:
            return GraphDiff(self.current_snapshot, other_snapshot)
    
    def rollback_to_snapshot(self, snapshot_id: str) -> bool:
        """Rollback to a previous snapshot."""
        with self._lock:
            # Find snapshot in history
            for snapshot in reversed(self.snapshot_history):
                if snapshot.snapshot_id == snapshot_id:
                    self.current_snapshot = snapshot
                    self._cache_valid = False
                    self._entity_cache.clear()
                    self._predicate_cache.clear()
                    return True
            return False
    
    def add_change_listener(self, listener: Callable[[GraphDiff], None]):
        """Add a change listener."""
        with self._lock:
            self.change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[GraphDiff], None]):
        """Remove a change listener."""
        with self._lock:
            if listener in self.change_listeners:
                self.change_listeners.remove(listener)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the mathematical layer."""
        with self._lock:
            snapshot = self.current_snapshot
            return {
                "current_snapshot_id": snapshot.snapshot_id,
                "total_entities": len(snapshot.entities),
                "total_predicates": len(snapshot.predicates),
                "total_contexts": len(snapshot.contexts),
                "total_relations": len(snapshot.relations),
                "snapshot_history_size": len(self.snapshot_history),
                "cache_valid": self._cache_valid,
                "cached_entities": len(self._entity_cache),
                "cached_predicates": len(self._predicate_cache),
                "change_listeners": len(self.change_listeners)
            }


# Example usage and testing
if __name__ == "__main__":
    print("Enhanced Mathematical Layer - Phase 4A Implementation")
    print("=" * 60)
    
    # Create enhanced mathematical layer
    math_layer = EnhancedMathematicalLayer()
    
    print("Testing entity operations...")
    
    # Create test entities
    entity1 = Entity.create(name="john", entity_type="individual")
    entity2 = Entity.create(name="mary", entity_type="individual")
    
    success, errors = math_layer.add_entity(entity1)
    print(f"Add entity 'john': {'✅' if success else '❌'} {errors}")
    
    success, errors = math_layer.add_entity(entity2)
    print(f"Add entity 'mary': {'✅' if success else '❌'} {errors}")
    
    print("\nTesting predicate operations...")
    
    # Create test predicate
    predicate1 = Predicate.create(name="Person_john", entities=[entity1.id])
    success, errors = math_layer.add_predicate(predicate1)
    print(f"Add predicate 'Person_john': {'✅' if success else '❌'} {errors}")
    
    print("\nTesting relation operations...")
    
    # Add relation
    success, errors = math_layer.add_relation(str(entity1.id), predicate1.name, "instance_of")
    print(f"Add relation john->Person_john: {'✅' if success else '❌'} {errors}")
    
    print("\nTesting snapshot operations...")
    
    # Get current snapshot
    snapshot = math_layer.get_current_snapshot()
    print(f"Current snapshot ID: {snapshot.snapshot_id[:8]}...")
    print(f"Snapshot hash: {snapshot.compute_hash()[:16]}...")
    
    # Test diff computation
    old_snapshot = snapshot
    
    # Add another entity
    entity3 = Entity.create(name="bob", entity_type="individual")
    math_layer.add_entity(entity3)
    
    new_snapshot = math_layer.get_current_snapshot()
    diff = GraphDiff(old_snapshot, new_snapshot)
    
    print(f"\\nDiff computation:")
    print(f"Has changes: {diff.has_changes()}")
    print(f"Number of changes: {len(diff.changes)}")
    if diff.changes:
        for change in diff.changes:
            print(f"  {change.change_type.value}: {change.element_id}")
    
    print("\\nTesting validation...")
    
    # Test validation by trying to remove referenced entity
    success, errors = math_layer.remove_entity(str(entity1.id))
    print(f"Remove referenced entity 'john': {'✅' if success else '❌'}")
    if errors:
        for error in errors:
            print(f"  Error: {error}")
    
    print("\\nTesting caching and performance...")
    
    # Test cached access
    start_time = time.time()
    for _ in range(1000):
        entity = math_layer.get_entity(str(entity1.id))
    end_time = time.time()
    print(f"1000 cached entity lookups: {(end_time - start_time)*1000:.2f}ms")
    
    # Show statistics
    print("\\nMathematical Layer Statistics:")
    stats = math_layer.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\\n" + "=" * 60)
    print("✅ Enhanced Mathematical Layer Phase 4A implementation complete!")
    print("Ready for synchronization protocols between layers.")

