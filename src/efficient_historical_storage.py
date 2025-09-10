"""
Efficient Historical Storage Model

Implements delta compression and structural diffs for minimal storage overhead
while maintaining fast replay capabilities for historical graphs.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import copy
import json
import zlib
from datetime import datetime

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
from historical_graph_model import HistoryEvent, HistoryEventType
from transformation_engine import OperationRequest, OperationResult, OperationType


class DeltaType(Enum):
    """Types of deltas in graph transformations."""
    ELEMENT_ADDED = "element_added"
    ELEMENT_REMOVED = "element_removed"
    ELEMENT_MODIFIED = "element_modified"
    RELATION_ADDED = "relation_added"
    RELATION_REMOVED = "relation_removed"
    CONTEXT_CHANGED = "context_changed"


@dataclass
class StructuralDelta:
    """A single structural change in the graph."""
    delta_type: DeltaType
    element_id: ElementID
    element_type: str  # "vertex", "edge", "cut"
    
    # Change data
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    
    # Relationship changes
    relation_type: Optional[str] = None  # "incidence", "area", "context"
    related_elements: Set[ElementID] = field(default_factory=set)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    compressed_data: Optional[bytes] = None


@dataclass
class TransformationDelta:
    """Complete delta for a transformation operation."""
    operation: OperationRequest
    result: OperationResult
    structural_deltas: List[StructuralDelta] = field(default_factory=list)
    
    # Compression metadata
    original_size: int = 0
    compressed_size: int = 0
    compression_ratio: float = 0.0
    
    # Fast access indices
    affected_elements: Set[ElementID] = field(default_factory=set)
    delta_types: Set[DeltaType] = field(default_factory=set)


class DeltaCompressor:
    """
    Compresses transformation deltas for efficient storage.
    """
    
    def __init__(self, compression_level: int = 6):
        self.compression_level = compression_level
    
    def compute_transformation_delta(self, before_egi: RelationalGraphWithCuts,
                                   after_egi: RelationalGraphWithCuts,
                                   operation: OperationRequest,
                                   result: OperationResult) -> TransformationDelta:
        """Compute structural delta between before and after states."""
        
        structural_deltas = []
        
        # Compare vertices
        structural_deltas.extend(self._compute_vertex_deltas(before_egi, after_egi))
        
        # Compare edges
        structural_deltas.extend(self._compute_edge_deltas(before_egi, after_egi))
        
        # Compare cuts
        structural_deltas.extend(self._compute_cut_deltas(before_egi, after_egi))
        
        # Compare relationships
        structural_deltas.extend(self._compute_relation_deltas(before_egi, after_egi))
        
        # Create transformation delta
        delta = TransformationDelta(
            operation=operation,
            result=result,
            structural_deltas=structural_deltas
        )
        
        # Compute metadata
        delta.affected_elements = {d.element_id for d in structural_deltas}
        delta.delta_types = {d.delta_type for d in structural_deltas}
        
        # Compress delta data
        self._compress_delta(delta)
        
        return delta
    
    def _compute_vertex_deltas(self, before: RelationalGraphWithCuts,
                             after: RelationalGraphWithCuts) -> List[StructuralDelta]:
        """Compute vertex-related deltas."""
        deltas = []
        
        before_vertices = {v.id: v for v in before.V}
        after_vertices = {v.id: v for v in after.V}
        
        # Added vertices
        for vertex_id in after_vertices.keys() - before_vertices.keys():
            vertex = after_vertices[vertex_id]
            deltas.append(StructuralDelta(
                delta_type=DeltaType.ELEMENT_ADDED,
                element_id=vertex_id,
                element_type="vertex",
                new_value=self._serialize_vertex(vertex)
            ))
        
        # Removed vertices
        for vertex_id in before_vertices.keys() - after_vertices.keys():
            vertex = before_vertices[vertex_id]
            deltas.append(StructuralDelta(
                delta_type=DeltaType.ELEMENT_REMOVED,
                element_id=vertex_id,
                element_type="vertex",
                old_value=self._serialize_vertex(vertex)
            ))
        
        # Modified vertices
        for vertex_id in before_vertices.keys() & after_vertices.keys():
            before_vertex = before_vertices[vertex_id]
            after_vertex = after_vertices[vertex_id]
            
            if not self._vertices_equal(before_vertex, after_vertex):
                deltas.append(StructuralDelta(
                    delta_type=DeltaType.ELEMENT_MODIFIED,
                    element_id=vertex_id,
                    element_type="vertex",
                    old_value=self._serialize_vertex(before_vertex),
                    new_value=self._serialize_vertex(after_vertex)
                ))
        
        return deltas
    
    def _compute_edge_deltas(self, before: RelationalGraphWithCuts,
                           after: RelationalGraphWithCuts) -> List[StructuralDelta]:
        """Compute edge-related deltas."""
        deltas = []
        
        before_edges = {e.id: e for e in before.E}
        after_edges = {e.id: e for e in after.E}
        
        # Added edges
        for edge_id in after_edges.keys() - before_edges.keys():
            edge = after_edges[edge_id]
            deltas.append(StructuralDelta(
                delta_type=DeltaType.ELEMENT_ADDED,
                element_id=edge_id,
                element_type="edge",
                new_value=self._serialize_edge(edge)
            ))
        
        # Removed edges
        for edge_id in before_edges.keys() - after_edges.keys():
            edge = before_edges[edge_id]
            deltas.append(StructuralDelta(
                delta_type=DeltaType.ELEMENT_REMOVED,
                element_id=edge_id,
                element_type="edge",
                old_value=self._serialize_edge(edge)
            ))
        
        # Modified edges
        for edge_id in before_edges.keys() & after_edges.keys():
            before_edge = before_edges[edge_id]
            after_edge = after_edges[edge_id]
            
            if not self._edges_equal(before_edge, after_edge):
                deltas.append(StructuralDelta(
                    delta_type=DeltaType.ELEMENT_MODIFIED,
                    element_id=edge_id,
                    element_type="edge",
                    old_value=self._serialize_edge(before_edge),
                    new_value=self._serialize_edge(after_edge)
                ))
        
        return deltas
    
    def _compute_cut_deltas(self, before: RelationalGraphWithCuts,
                          after: RelationalGraphWithCuts) -> List[StructuralDelta]:
        """Compute cut-related deltas."""
        deltas = []
        
        before_cuts = {c.id: c for c in before.Cut}
        after_cuts = {c.id: c for c in after.Cut}
        
        # Added cuts
        for cut_id in after_cuts.keys() - before_cuts.keys():
            cut = after_cuts[cut_id]
            deltas.append(StructuralDelta(
                delta_type=DeltaType.ELEMENT_ADDED,
                element_id=cut_id,
                element_type="cut",
                new_value=self._serialize_cut(cut)
            ))
        
        # Removed cuts
        for cut_id in before_cuts.keys() - after_cuts.keys():
            cut = before_cuts[cut_id]
            deltas.append(StructuralDelta(
                delta_type=DeltaType.ELEMENT_REMOVED,
                element_id=cut_id,
                element_type="cut",
                old_value=self._serialize_cut(cut)
            ))
        
        return deltas
    
    def _compute_relation_deltas(self, before: RelationalGraphWithCuts,
                               after: RelationalGraphWithCuts) -> List[StructuralDelta]:
        """Compute relationship deltas (incidence, area, etc.)."""
        deltas = []
        
        # Incidence relation changes
        deltas.extend(self._compute_incidence_deltas(before, after))
        
        # Area relation changes
        deltas.extend(self._compute_area_deltas(before, after))
        
        return deltas
    
    def _compute_incidence_deltas(self, before: RelationalGraphWithCuts,
                                after: RelationalGraphWithCuts) -> List[StructuralDelta]:
        """Compute incidence relation deltas."""
        deltas = []
        
        # Compare incidence mappings
        for edge_id in set(before.nu.keys()) | set(after.nu.keys()):
            before_vertices = set(before.nu.get(edge_id, []))
            after_vertices = set(after.nu.get(edge_id, []))
            
            if before_vertices != after_vertices:
                deltas.append(StructuralDelta(
                    delta_type=DeltaType.RELATION_MODIFIED if edge_id in before.nu and edge_id in after.nu 
                             else DeltaType.RELATION_ADDED if edge_id in after.nu 
                             else DeltaType.RELATION_REMOVED,
                    element_id=edge_id,
                    element_type="edge",
                    relation_type="incidence",
                    old_value=list(before_vertices) if before_vertices else None,
                    new_value=list(after_vertices) if after_vertices else None,
                    related_elements=before_vertices | after_vertices
                ))
        
        return deltas
    
    def _compute_area_deltas(self, before: RelationalGraphWithCuts,
                           after: RelationalGraphWithCuts) -> List[StructuralDelta]:
        """Compute area relation deltas."""
        deltas = []
        
        # Compare area mappings
        for cut_id in set(before.area.keys()) | set(after.area.keys()):
            before_elements = set(before.area.get(cut_id, frozenset()))
            after_elements = set(after.area.get(cut_id, frozenset()))
            
            if before_elements != after_elements:
                deltas.append(StructuralDelta(
                    delta_type=DeltaType.RELATION_MODIFIED if cut_id in before.area and cut_id in after.area
                             else DeltaType.RELATION_ADDED if cut_id in after.area
                             else DeltaType.RELATION_REMOVED,
                    element_id=cut_id,
                    element_type="cut",
                    relation_type="area",
                    old_value=list(before_elements) if before_elements else None,
                    new_value=list(after_elements) if after_elements else None,
                    related_elements=before_elements | after_elements
                ))
        
        return deltas
    
    def _compress_delta(self, delta: TransformationDelta):
        """Compress delta data for storage efficiency."""
        # Serialize delta data
        delta_data = {
            "operation": {
                "type": delta.operation.operation_type.value,
                "elements": delta.operation.target_elements,
                "parameters": delta.operation.parameters
            },
            "deltas": [
                {
                    "type": d.delta_type.value,
                    "element_id": d.element_id,
                    "element_type": d.element_type,
                    "old_value": d.old_value,
                    "new_value": d.new_value,
                    "relation_type": d.relation_type,
                    "related_elements": list(d.related_elements)
                }
                for d in delta.structural_deltas
            ]
        }
        
        # JSON serialize and compress
        json_data = json.dumps(delta_data, separators=(',', ':')).encode('utf-8')
        compressed_data = zlib.compress(json_data, self.compression_level)
        
        # Store compression metadata
        delta.original_size = len(json_data)
        delta.compressed_size = len(compressed_data)
        delta.compression_ratio = delta.compressed_size / delta.original_size if delta.original_size > 0 else 0
        
        # Store compressed data in first delta (or create new one if empty)
        if delta.structural_deltas:
            delta.structural_deltas[0].compressed_data = compressed_data
        else:
            # Create a metadata delta
            metadata_delta = StructuralDelta(
                delta_type=DeltaType.ELEMENT_MODIFIED,
                element_id="__metadata__",
                element_type="metadata",
                compressed_data=compressed_data
            )
            delta.structural_deltas.append(metadata_delta)
    
    def decompress_delta(self, delta: TransformationDelta) -> Dict[str, Any]:
        """Decompress delta data for replay."""
        compressed_data = None
        
        # Find compressed data
        for d in delta.structural_deltas:
            if d.compressed_data:
                compressed_data = d.compressed_data
                break
        
        if not compressed_data:
            return {}
        
        # Decompress and deserialize
        try:
            json_data = zlib.decompress(compressed_data)
            return json.loads(json_data.decode('utf-8'))
        except Exception:
            return {}
    
    def _serialize_vertex(self, vertex: Vertex) -> Dict[str, Any]:
        """Serialize vertex for delta storage."""
        return {
            "id": vertex.id,
            "label": getattr(vertex, 'label', ''),
            "type": getattr(vertex, 'type', ''),
            "properties": getattr(vertex, 'properties', {})
        }
    
    def _serialize_edge(self, edge: Edge) -> Dict[str, Any]:
        """Serialize edge for delta storage."""
        return {
            "id": edge.id,
            "label": getattr(edge, 'label', ''),
            "type": getattr(edge, 'type', ''),
            "properties": getattr(edge, 'properties', {})
        }
    
    def _serialize_cut(self, cut: Cut) -> Dict[str, Any]:
        """Serialize cut for delta storage."""
        return {
            "id": cut.id,
            "type": getattr(cut, 'type', ''),
            "properties": getattr(cut, 'properties', {})
        }
    
    def _vertices_equal(self, v1: Vertex, v2: Vertex) -> bool:
        """Compare vertices for equality."""
        return (v1.id == v2.id and 
                getattr(v1, 'label', '') == getattr(v2, 'label', '') and
                getattr(v1, 'type', '') == getattr(v2, 'type', ''))
    
    def _edges_equal(self, e1: Edge, e2: Edge) -> bool:
        """Compare edges for equality."""
        return (e1.id == e2.id and 
                getattr(e1, 'label', '') == getattr(e2, 'label', '') and
                getattr(e1, 'type', '') == getattr(e2, 'type', ''))


class EfficientHistoricalStorage:
    """
    Efficient storage system for historical graphs using delta compression.
    """
    
    def __init__(self, snapshot_interval: int = 10):
        self.compressor = DeltaCompressor()
        self.snapshot_interval = snapshot_interval
        
        # Storage for deltas and snapshots
        self.transformation_deltas: Dict[str, TransformationDelta] = {}
        self.snapshots: Dict[str, RelationalGraphWithCuts] = {}
        
        # Performance metrics
        self.storage_stats = {
            "total_transformations": 0,
            "total_snapshots": 0,
            "total_compressed_size": 0,
            "total_uncompressed_size": 0,
            "average_compression_ratio": 0.0
        }
    
    def store_transformation(self, event_id: str,
                           before_egi: RelationalGraphWithCuts,
                           after_egi: RelationalGraphWithCuts,
                           operation: OperationRequest,
                           result: OperationResult) -> TransformationDelta:
        """Store a transformation with delta compression."""
        
        # Compute delta
        delta = self.compressor.compute_transformation_delta(
            before_egi, after_egi, operation, result
        )
        
        # Store delta
        self.transformation_deltas[event_id] = delta
        
        # Update statistics
        self._update_storage_stats(delta)
        
        # Create snapshot if needed
        if self._should_create_snapshot(event_id):
            self.snapshots[event_id] = copy.deepcopy(after_egi)
            self.storage_stats["total_snapshots"] += 1
        
        return delta
    
    def replay_from_deltas(self, start_egi: RelationalGraphWithCuts,
                          delta_sequence: List[str]) -> RelationalGraphWithCuts:
        """Replay transformations from delta sequence."""
        current_egi = copy.deepcopy(start_egi)
        
        for event_id in delta_sequence:
            if event_id in self.transformation_deltas:
                delta = self.transformation_deltas[event_id]
                current_egi = self._apply_delta(current_egi, delta)
        
        return current_egi
    
    def _apply_delta(self, egi: RelationalGraphWithCuts, 
                    delta: TransformationDelta) -> RelationalGraphWithCuts:
        """Apply a transformation delta to an EGI."""
        result_egi = copy.deepcopy(egi)
        
        for structural_delta in delta.structural_deltas:
            if structural_delta.element_type == "metadata":
                continue  # Skip metadata deltas
            
            self._apply_structural_delta(result_egi, structural_delta)
        
        return result_egi
    
    def _apply_structural_delta(self, egi: RelationalGraphWithCuts, 
                              delta: StructuralDelta):
        """Apply a single structural delta."""
        
        if delta.delta_type == DeltaType.ELEMENT_ADDED:
            self._add_element_from_delta(egi, delta)
        elif delta.delta_type == DeltaType.ELEMENT_REMOVED:
            self._remove_element_from_delta(egi, delta)
        elif delta.delta_type == DeltaType.ELEMENT_MODIFIED:
            self._modify_element_from_delta(egi, delta)
        elif delta.delta_type in [DeltaType.RELATION_ADDED, DeltaType.RELATION_REMOVED, DeltaType.RELATION_MODIFIED]:
            self._modify_relation_from_delta(egi, delta)
    
    def _add_element_from_delta(self, egi: RelationalGraphWithCuts, delta: StructuralDelta):
        """Add element from delta."""
        if delta.element_type == "vertex" and delta.new_value:
            vertex = self._deserialize_vertex(delta.new_value)
            egi.V.add(vertex)
            egi._vertex_map[vertex.id] = vertex
        elif delta.element_type == "edge" and delta.new_value:
            edge = self._deserialize_edge(delta.new_value)
            egi.E.add(edge)
            egi._edge_map[edge.id] = edge
        elif delta.element_type == "cut" and delta.new_value:
            cut = self._deserialize_cut(delta.new_value)
            egi.Cut.add(cut)
            egi._cut_map[cut.id] = cut
    
    def _remove_element_from_delta(self, egi: RelationalGraphWithCuts, delta: StructuralDelta):
        """Remove element from delta."""
        element_id = delta.element_id
        
        if delta.element_type == "vertex" and element_id in egi._vertex_map:
            vertex = egi._vertex_map[element_id]
            egi.V.discard(vertex)
            del egi._vertex_map[element_id]
        elif delta.element_type == "edge" and element_id in egi._edge_map:
            edge = egi._edge_map[element_id]
            egi.E.discard(edge)
            del egi._edge_map[element_id]
            egi.nu.pop(element_id, None)
        elif delta.element_type == "cut" and element_id in egi._cut_map:
            cut = egi._cut_map[element_id]
            egi.Cut.discard(cut)
            del egi._cut_map[element_id]
            egi.area.pop(element_id, None)
    
    def _modify_element_from_delta(self, egi: RelationalGraphWithCuts, delta: StructuralDelta):
        """Modify element from delta."""
        # For now, treat as remove + add
        if delta.old_value:
            self._remove_element_from_delta(egi, delta)
        if delta.new_value:
            self._add_element_from_delta(egi, delta)
    
    def _modify_relation_from_delta(self, egi: RelationalGraphWithCuts, delta: StructuralDelta):
        """Modify relation from delta."""
        element_id = delta.element_id
        
        if delta.relation_type == "incidence" and delta.new_value:
            egi.nu[element_id] = tuple(delta.new_value)
        elif delta.relation_type == "area" and delta.new_value:
            egi.area[element_id] = frozenset(delta.new_value)
    
    def _deserialize_vertex(self, data: Dict[str, Any]) -> Vertex:
        """Deserialize vertex from delta data."""
        vertex = Vertex(data["id"])
        if "label" in data:
            vertex.label = data["label"]
        if "type" in data:
            vertex.type = data["type"]
        return vertex
    
    def _deserialize_edge(self, data: Dict[str, Any]) -> Edge:
        """Deserialize edge from delta data."""
        edge = Edge(data["id"])
        if "label" in data:
            edge.label = data["label"]
        if "type" in data:
            edge.type = data["type"]
        return edge
    
    def _deserialize_cut(self, data: Dict[str, Any]) -> Cut:
        """Deserialize cut from delta data."""
        cut = Cut(data["id"])
        if "type" in data:
            cut.type = data["type"]
        return cut
    
    def _should_create_snapshot(self, event_id: str) -> bool:
        """Determine if a snapshot should be created."""
        return len(self.transformation_deltas) % self.snapshot_interval == 0
    
    def _update_storage_stats(self, delta: TransformationDelta):
        """Update storage statistics."""
        self.storage_stats["total_transformations"] += 1
        self.storage_stats["total_compressed_size"] += delta.compressed_size
        self.storage_stats["total_uncompressed_size"] += delta.original_size
        
        # Update average compression ratio
        if self.storage_stats["total_uncompressed_size"] > 0:
            self.storage_stats["average_compression_ratio"] = (
                self.storage_stats["total_compressed_size"] / 
                self.storage_stats["total_uncompressed_size"]
            )
    
    def get_storage_efficiency(self) -> Dict[str, Any]:
        """Get storage efficiency metrics."""
        return {
            **self.storage_stats,
            "space_saved_bytes": (
                self.storage_stats["total_uncompressed_size"] - 
                self.storage_stats["total_compressed_size"]
            ),
            "space_saved_percentage": (
                (1 - self.storage_stats["average_compression_ratio"]) * 100
                if self.storage_stats["average_compression_ratio"] > 0 else 0
            )
        }
    
    def optimize_storage(self) -> Dict[str, Any]:
        """Optimize storage by creating additional snapshots or compacting deltas."""
        optimization_results = {
            "snapshots_created": 0,
            "deltas_compacted": 0,
            "space_saved": 0
        }
        
        # Create snapshots for frequently accessed sequences
        # Compact similar deltas
        # Remove redundant data
        
        return optimization_results
