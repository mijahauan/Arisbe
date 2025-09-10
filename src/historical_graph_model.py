"""
Historical Graph Model

Graphs are not just static structures but carry their transformation history.
This creates a rich data model where:
- Graphs = transformation sequence + current state
- Full provenance tracking for research and education
- Version control through transformation history
- Ability to replay/undo transformation sequences
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union, Iterator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import json

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
from universal_composition import CompositionSequence, CompositionStep, CompositionSource
from transformation_engine import OperationRequest, OperationResult
from simplified_sheet_of_assertion import SheetOfAssertion, SheetMetadata, SheetPurpose


class HistoryEventType(Enum):
    """Types of events in graph history."""
    CREATION = "creation"                    # Initial graph creation
    TRANSFORMATION = "transformation"        # EG transformation rule application
    IMPORT = "import"                       # Import from external source
    MERGE = "merge"                         # Merge with another graph
    BRANCH = "branch"                       # Create branch from this state
    CHECKPOINT = "checkpoint"               # Manual save point
    ANNOTATION = "annotation"               # User annotation/comment


@dataclass
class HistoryEvent:
    """A single event in the graph's transformation history."""
    event_id: str
    event_type: HistoryEventType
    timestamp: datetime
    operation: Optional[OperationRequest] = None
    result: Optional[OperationResult] = None
    description: str = ""
    author: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # For branching and merging
    parent_event_id: Optional[str] = None
    merged_from: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "author": self.author,
            "metadata": self.metadata,
            "parent_event_id": self.parent_event_id,
            "merged_from": self.merged_from
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryEvent':
        """Deserialize event from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=HistoryEventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            description=data.get("description", ""),
            author=data.get("author", ""),
            metadata=data.get("metadata", {}),
            parent_event_id=data.get("parent_event_id"),
            merged_from=data.get("merged_from", [])
        )


class GraphHistory:
    """
    Complete transformation history of a graph.
    
    Tracks all transformations that led to the current state,
    enabling replay, undo, branching, and provenance analysis.
    """
    
    def __init__(self, initial_event: Optional[HistoryEvent] = None):
        self.events: Dict[str, HistoryEvent] = {}
        self.event_sequence: List[str] = []  # Chronological order
        self.current_event_id: Optional[str] = None
        self.branches: Dict[str, List[str]] = {}  # branch_name -> event_ids
        self.current_branch = "main"
        
        if initial_event:
            self.add_event(initial_event)
    
    def add_event(self, event: HistoryEvent) -> str:
        """Add an event to the history."""
        self.events[event.event_id] = event
        self.event_sequence.append(event.event_id)
        self.current_event_id = event.event_id
        
        # Add to current branch
        if self.current_branch not in self.branches:
            self.branches[self.current_branch] = []
        self.branches[self.current_branch].append(event.event_id)
        
        return event.event_id
    
    def create_transformation_event(self, operation: OperationRequest, 
                                  result: OperationResult,
                                  author: str = "") -> str:
        """Create and add a transformation event."""
        event = HistoryEvent(
            event_id=str(uuid.uuid4()),
            event_type=HistoryEventType.TRANSFORMATION,
            timestamp=datetime.now(),
            operation=operation,
            result=result,
            description=f"Applied {operation.operation_type.value}",
            author=author,
            parent_event_id=self.current_event_id
        )
        
        return self.add_event(event)
    
    def create_checkpoint(self, description: str, author: str = "") -> str:
        """Create a checkpoint event."""
        event = HistoryEvent(
            event_id=str(uuid.uuid4()),
            event_type=HistoryEventType.CHECKPOINT,
            timestamp=datetime.now(),
            description=description,
            author=author,
            parent_event_id=self.current_event_id
        )
        
        return self.add_event(event)
    
    def create_branch(self, branch_name: str, from_event_id: Optional[str] = None) -> bool:
        """Create a new branch from a specific event."""
        if branch_name in self.branches:
            return False
        
        start_event = from_event_id or self.current_event_id
        if not start_event or start_event not in self.events:
            return False
        
        # Create branch event
        branch_event = HistoryEvent(
            event_id=str(uuid.uuid4()),
            event_type=HistoryEventType.BRANCH,
            timestamp=datetime.now(),
            description=f"Created branch '{branch_name}'",
            parent_event_id=start_event
        )
        
        self.add_event(branch_event)
        
        # Initialize new branch
        self.branches[branch_name] = [branch_event.event_id]
        
        return True
    
    def switch_branch(self, branch_name: str) -> bool:
        """Switch to a different branch."""
        if branch_name not in self.branches:
            return False
        
        self.current_branch = branch_name
        # Set current event to latest in this branch
        if self.branches[branch_name]:
            self.current_event_id = self.branches[branch_name][-1]
        
        return True
    
    def get_events_to_replay(self, target_event_id: str) -> List[HistoryEvent]:
        """Get sequence of events needed to replay to a specific state."""
        if target_event_id not in self.events:
            return []
        
        # Build path from root to target event
        path = []
        current_id = target_event_id
        
        while current_id:
            event = self.events[current_id]
            path.insert(0, event)
            current_id = event.parent_event_id
        
        return path
    
    def get_transformation_sequence(self, target_event_id: Optional[str] = None) -> CompositionSequence:
        """Convert history to a composition sequence for replay."""
        target = target_event_id or self.current_event_id
        if not target:
            return CompositionSequence(CompositionSource.DE_NOVO)
        
        events = self.get_events_to_replay(target)
        sequence = CompositionSequence(CompositionSource.DE_NOVO)
        
        for event in events:
            if event.operation and event.event_type == HistoryEventType.TRANSFORMATION:
                step = CompositionStep(
                    operation=event.operation,
                    step_description=event.description
                )
                sequence.steps.append(step)
        
        return sequence
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the graph history."""
        transformation_count = sum(
            1 for event in self.events.values() 
            if event.event_type == HistoryEventType.TRANSFORMATION
        )
        
        return {
            "total_events": len(self.events),
            "transformations": transformation_count,
            "branches": len(self.branches),
            "current_branch": self.current_branch,
            "current_event": self.current_event_id,
            "creation_time": min(event.timestamp for event in self.events.values()) if self.events else None
        }
    
    def export_history(self) -> Dict[str, Any]:
        """Export complete history for serialization."""
        return {
            "events": {eid: event.to_dict() for eid, event in self.events.items()},
            "event_sequence": self.event_sequence,
            "branches": self.branches,
            "current_branch": self.current_branch,
            "current_event_id": self.current_event_id
        }
    
    @classmethod
    def import_history(cls, data: Dict[str, Any]) -> 'GraphHistory':
        """Import history from serialized data."""
        history = cls()
        
        # Import events
        for eid, event_data in data["events"].items():
            history.events[eid] = HistoryEvent.from_dict(event_data)
        
        history.event_sequence = data["event_sequence"]
        history.branches = data["branches"]
        history.current_branch = data["current_branch"]
        history.current_event_id = data["current_event_id"]
        
        return history


class HistoricalGraph:
    """
    A graph that maintains its complete transformation history.
    
    This is the core data model where graphs are transformation sequences
    plus current state, enabling rich provenance and version control.
    """
    
    def __init__(self, metadata: SheetMetadata, 
                 initial_egi: Optional[RelationalGraphWithCuts] = None,
                 creation_source: CompositionSource = CompositionSource.DE_NOVO):
        self.metadata = metadata
        self.current_egi = initial_egi or RelationalGraphWithCuts()
        
        # Initialize history with creation event
        creation_event = HistoryEvent(
            event_id=str(uuid.uuid4()),
            event_type=HistoryEventType.CREATION,
            timestamp=datetime.now(),
            description=f"Graph created from {creation_source.value}",
            metadata={"source": creation_source.value}
        )
        
        self.history = GraphHistory(creation_event)
        
        # Snapshots for efficient replay (stored at checkpoints)
        self.snapshots: Dict[str, RelationalGraphWithCuts] = {}
        self.snapshots[creation_event.event_id] = self.current_egi
    
    def apply_transformation(self, operation: OperationRequest, 
                           result: OperationResult, author: str = "") -> str:
        """Apply a transformation and record it in history."""
        # Update current EGI
        if result.success and result.modified_graph:
            self.current_egi = result.modified_graph
        
        # Record in history
        event_id = self.history.create_transformation_event(operation, result, author)
        
        # Update metadata
        self.metadata.update_modified()
        
        return event_id
    
    def create_checkpoint(self, description: str, author: str = "") -> str:
        """Create a checkpoint and snapshot."""
        event_id = self.history.create_checkpoint(description, author)
        
        # Store snapshot for efficient replay
        self.snapshots[event_id] = self.current_egi
        
        return event_id
    
    def replay_to_event(self, target_event_id: str) -> bool:
        """Replay transformations to reach a specific historical state."""
        if target_event_id not in self.history.events:
            return False
        
        # Find nearest snapshot
        replay_events = self.history.get_events_to_replay(target_event_id)
        start_snapshot = None
        start_index = 0
        
        for i, event in enumerate(replay_events):
            if event.event_id in self.snapshots:
                start_snapshot = self.snapshots[event.event_id]
                start_index = i + 1
        
        # Start from snapshot or beginning
        if start_snapshot:
            self.current_egi = start_snapshot
        else:
            self.current_egi = RelationalGraphWithCuts()
        
        # Replay transformations from snapshot point
        # This would require a replay engine that can re-execute operations
        # For now, we'll update the current event pointer
        self.history.current_event_id = target_event_id
        
        return True
    
    def get_transformation_sequence(self) -> CompositionSequence:
        """Get the complete transformation sequence that created this graph."""
        return self.history.get_transformation_sequence()
    
    def branch_from_event(self, branch_name: str, event_id: str) -> bool:
        """Create a new branch from a specific historical event."""
        return self.history.create_branch(branch_name, event_id)
    
    def merge_from_graph(self, other_graph: 'HistoricalGraph', author: str = "") -> str:
        """Merge another historical graph into this one."""
        # Create merge event
        merge_event = HistoryEvent(
            event_id=str(uuid.uuid4()),
            event_type=HistoryEventType.MERGE,
            timestamp=datetime.now(),
            description=f"Merged graph {other_graph.metadata.sheet_id}",
            author=author,
            parent_event_id=self.history.current_event_id,
            merged_from=[other_graph.history.current_event_id] if other_graph.history.current_event_id else []
        )
        
        # Add merge event to history
        event_id = self.history.add_event(merge_event)
        
        # The actual merging would be done through transformation operations
        # This records the provenance of the merge
        
        return event_id
    
    def export_with_history(self) -> Dict[str, Any]:
        """Export graph with complete history for storage."""
        return {
            "metadata": {
                "sheet_id": self.metadata.sheet_id,
                "title": self.metadata.title,
                "purpose": self.metadata.purpose.value,
                "description": self.metadata.description,
                "created_at": self.metadata.created_at.isoformat(),
                "modified_at": self.metadata.modified_at.isoformat(),
                "author": self.metadata.author,
                "version": self.metadata.version,
                "tags": self.metadata.tags
            },
            "current_egi": self._serialize_egi(self.current_egi),
            "history": self.history.export_history(),
            "snapshots": {eid: self._serialize_egi(egi) for eid, egi in self.snapshots.items()}
        }
    
    def _serialize_egi(self, egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Serialize EGI to dictionary (placeholder implementation)."""
        return {
            "vertices": len(egi.V),
            "edges": len(egi.E),
            "cuts": len(egi.Cut),
            "sheet": egi.sheet
            # Full serialization would include all graph data
        }
    
    @classmethod
    def import_with_history(cls, data: Dict[str, Any]) -> 'HistoricalGraph':
        """Import graph with complete history."""
        # Reconstruct metadata
        metadata_data = data["metadata"]
        metadata = SheetMetadata(
            sheet_id=metadata_data["sheet_id"],
            title=metadata_data["title"],
            purpose=SheetPurpose(metadata_data["purpose"]),
            description=metadata_data["description"],
            created_at=datetime.fromisoformat(metadata_data["created_at"]),
            modified_at=datetime.fromisoformat(metadata_data["modified_at"]),
            author=metadata_data["author"],
            version=metadata_data["version"],
            tags=metadata_data["tags"]
        )
        
        # Create historical graph
        graph = cls(metadata)
        
        # Import history
        graph.history = GraphHistory.import_history(data["history"])
        
        # Import snapshots (would need full EGI deserialization)
        # For now, placeholder
        
        return graph


class HistoricalGraphRepository:
    """
    Repository for managing historical graphs with provenance tracking.
    
    Provides storage, retrieval, and analysis of graphs with their
    complete transformation histories.
    """
    
    def __init__(self):
        self.graphs: Dict[str, HistoricalGraph] = {}
    
    def store_graph(self, graph: HistoricalGraph) -> str:
        """Store a historical graph."""
        self.graphs[graph.metadata.sheet_id] = graph
        return graph.metadata.sheet_id
    
    def load_graph(self, graph_id: str) -> Optional[HistoricalGraph]:
        """Load a historical graph."""
        return self.graphs.get(graph_id)
    
    def find_graphs_by_provenance(self, source_type: CompositionSource) -> List[HistoricalGraph]:
        """Find graphs created from a specific source type."""
        results = []
        
        for graph in self.graphs.values():
            # Check creation event
            if graph.history.events:
                first_event = next(iter(graph.history.events.values()))
                if first_event.metadata.get("source") == source_type.value:
                    results.append(graph)
        
        return results
    
    def get_transformation_statistics(self) -> Dict[str, Any]:
        """Get statistics about transformations across all graphs."""
        total_transformations = 0
        transformation_types = {}
        
        for graph in self.graphs.values():
            stats = graph.history.get_statistics()
            total_transformations += stats["transformations"]
        
        return {
            "total_graphs": len(self.graphs),
            "total_transformations": total_transformations,
            "transformation_types": transformation_types
        }
