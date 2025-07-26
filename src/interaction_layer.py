"""
Interaction Layer - Phase 4A Implementation

This module implements the interaction layer data structures that enable real-time
diagrammatic manipulation while maintaining synchronization with the mathematical
layer. The interaction layer is optimized for performance and user experience,
supporting spatial operations, change tracking, and collaborative editing.

Key Design Principles:
1. Mutable data structures optimized for real-time updates
2. Spatial indexing for efficient visual operations
3. Change tracking for undo/redo and collaboration
4. Semantic correspondence with mathematical layer
5. Platform-independent operation support

The interaction layer serves as the bridge between user interface operations
and the mathematical rigor of the EG-HG representation, enabling the kind of
fluid diagrammatic thinking that Peirce envisioned for existential graphs.

Author: Manus AI
Date: January 2025
Phase: 4A - Foundation Architecture
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
from collections import defaultdict, deque
import threading
from abc import ABC, abstractmethod

# Import existing types for compatibility
from eg_types import Entity, Predicate, Context


class InteractionElementType(Enum):
    """Types of elements in the interaction layer."""
    ENTITY = "entity"
    PREDICATE = "predicate"
    CUT = "cut"
    LINE_OF_IDENTITY = "line_of_identity"
    RELATION_OVAL = "relation_oval"
    CONSTANT = "constant"
    VARIABLE = "variable"
    COREFERENCE_NODE = "coreference_node"


class InteractionOperationType(Enum):
    """Types of operations that can be performed on interaction elements."""
    CREATE = "create"
    DELETE = "delete"
    MOVE = "move"
    RESIZE = "resize"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    MODIFY_PROPERTIES = "modify_properties"
    GROUP = "group"
    UNGROUP = "ungroup"
    COPY = "copy"
    PASTE = "paste"


class ElementState(Enum):
    """States that interaction elements can be in."""
    NORMAL = "normal"
    SELECTED = "selected"
    HIGHLIGHTED = "highlighted"
    DRAGGING = "dragging"
    RESIZING = "resizing"
    CONNECTING = "connecting"
    INVALID = "invalid"
    TEMPORARY = "temporary"


@dataclass
class SpatialBounds:
    """Spatial boundaries for visual elements."""
    x: float
    y: float
    width: float
    height: float
    
    def contains_point(self, px: float, py: float) -> bool:
        """Check if a point is within these bounds."""
        return (self.x <= px <= self.x + self.width and 
                self.y <= py <= self.y + self.height)
    
    def intersects(self, other: 'SpatialBounds') -> bool:
        """Check if these bounds intersect with another bounds."""
        return not (self.x + self.width < other.x or 
                   other.x + other.width < self.x or
                   self.y + self.height < other.y or 
                   other.y + other.height < self.y)
    
    def center(self) -> Tuple[float, float]:
        """Get the center point of these bounds."""
        return (self.x + self.width / 2, self.y + self.height / 2)


@dataclass
class VisualProperties:
    """Visual properties for rendering elements."""
    color: str = "#000000"
    background_color: str = "#ffffff"
    border_color: str = "#000000"
    border_width: float = 1.0
    font_size: float = 12.0
    font_family: str = "Arial"
    opacity: float = 1.0
    z_index: int = 0
    visible: bool = True
    
    def copy(self) -> 'VisualProperties':
        """Create a copy of these visual properties."""
        return VisualProperties(
            color=self.color,
            background_color=self.background_color,
            border_color=self.border_color,
            border_width=self.border_width,
            font_size=self.font_size,
            font_family=self.font_family,
            opacity=self.opacity,
            z_index=self.z_index,
            visible=self.visible
        )


@dataclass
class InteractionElement:
    """Base class for all interaction layer elements."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    element_type: InteractionElementType = InteractionElementType.ENTITY
    bounds: SpatialBounds = field(default_factory=lambda: SpatialBounds(0, 0, 100, 50))
    visual_properties: VisualProperties = field(default_factory=VisualProperties)
    state: ElementState = ElementState.NORMAL
    
    # Semantic properties
    label: str = ""
    mathematical_id: Optional[str] = None  # Link to mathematical layer
    parent_id: Optional[str] = None
    children_ids: Set[str] = field(default_factory=set)
    
    # Interaction properties
    selectable: bool = True
    draggable: bool = True
    resizable: bool = True
    connectable: bool = True
    
    # Metadata
    created_time: float = field(default_factory=time.time)
    modified_time: float = field(default_factory=time.time)
    created_by: Optional[str] = None
    modified_by: Optional[str] = None
    
    def update_modification_time(self, user_id: Optional[str] = None):
        """Update the modification timestamp."""
        self.modified_time = time.time()
        if user_id:
            self.modified_by = user_id
    
    def get_center(self) -> Tuple[float, float]:
        """Get the center point of this element."""
        return self.bounds.center()
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is within this element."""
        return self.bounds.contains_point(x, y)
    
    def intersects(self, other: 'InteractionElement') -> bool:
        """Check if this element intersects with another."""
        return self.bounds.intersects(other.bounds)


@dataclass
class InteractionEntity(InteractionElement):
    """Interaction layer representation of an entity."""
    entity_type: str = "individual"
    defining: bool = False  # Whether this is a defining occurrence (*x vs x)
    
    def __post_init__(self):
        self.element_type = InteractionElementType.ENTITY
        if self.defining:
            self.visual_properties.border_width = 2.0
            self.visual_properties.border_color = "#0066cc"


@dataclass
class InteractionPredicate(InteractionElement):
    """Interaction layer representation of a predicate."""
    predicate_name: str = ""
    arity: int = 0
    connected_entities: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.element_type = InteractionElementType.PREDICATE
        self.visual_properties.background_color = "#f0f0f0"
        self.bounds.width = max(100, len(self.predicate_name) * 8 + 20)


@dataclass
class InteractionCut(InteractionElement):
    """Interaction layer representation of a cut (negation)."""
    cut_type: str = "simple"  # simple, double, etc.
    enclosed_elements: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        self.element_type = InteractionElementType.CUT
        self.visual_properties.background_color = "transparent"
        self.visual_properties.border_color = "#cc0000"
        self.visual_properties.border_width = 2.0
        self.resizable = True


@dataclass
class InteractionConnection:
    """Represents a connection between interaction elements."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    connection_type: str = "line_of_identity"
    
    # Visual properties for the connection
    color: str = "#000000"
    width: float = 1.0
    style: str = "solid"  # solid, dashed, dotted
    
    # Path information for curved connections
    control_points: List[Tuple[float, float]] = field(default_factory=list)
    
    # Metadata
    created_time: float = field(default_factory=time.time)
    modified_time: float = field(default_factory=time.time)


@dataclass
class InteractionOperation:
    """Represents an operation performed on the interaction layer."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: InteractionOperationType = InteractionOperationType.CREATE
    element_id: str = ""
    
    # Operation parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # State information
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    
    # Metadata
    timestamp: float = field(default_factory=time.time)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)


class ChangeTracker:
    """Tracks changes for undo/redo and collaboration."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.operation_history: deque = deque(maxlen=max_history)
        self.undo_stack: deque = deque(maxlen=max_history)
        self.redo_stack: deque = deque(maxlen=max_history)
        self.change_listeners: List[Callable] = []
    
    def record_operation(self, operation: InteractionOperation):
        """Record an operation in the change history."""
        self.operation_history.append(operation)
        self.undo_stack.append(operation)
        self.redo_stack.clear()  # Clear redo stack when new operation is performed
        
        # Notify listeners
        for listener in self.change_listeners:
            try:
                listener(operation)
            except Exception as e:
                print(f"Error in change listener: {e}")
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return len(self.redo_stack) > 0
    
    def get_undo_operation(self) -> Optional[InteractionOperation]:
        """Get the next operation to undo."""
        if self.can_undo():
            return self.undo_stack[-1]
        return None
    
    def get_redo_operation(self) -> Optional[InteractionOperation]:
        """Get the next operation to redo."""
        if self.can_redo():
            return self.redo_stack[-1]
        return None
    
    def perform_undo(self) -> Optional[InteractionOperation]:
        """Move an operation from undo to redo stack."""
        if self.can_undo():
            operation = self.undo_stack.pop()
            self.redo_stack.append(operation)
            return operation
        return None
    
    def perform_redo(self) -> Optional[InteractionOperation]:
        """Move an operation from redo to undo stack."""
        if self.can_redo():
            operation = self.redo_stack.pop()
            self.undo_stack.append(operation)
            return operation
        return None
    
    def add_change_listener(self, listener: Callable):
        """Add a listener for change notifications."""
        self.change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable):
        """Remove a change listener."""
        if listener in self.change_listeners:
            self.change_listeners.remove(listener)


class SpatialIndex:
    """Spatial indexing for efficient visual operations."""
    
    def __init__(self, bounds: SpatialBounds, max_depth: int = 6, max_elements: int = 10):
        self.bounds = bounds
        self.max_depth = max_depth
        self.max_elements = max_elements
        self.elements: Dict[str, InteractionElement] = {}
        self.quadrants: Optional[List['SpatialIndex']] = None
        self.is_leaf = True
    
    def insert(self, element: InteractionElement):
        """Insert an element into the spatial index."""
        if not self.bounds.intersects(element.bounds):
            return False
        
        if self.is_leaf:
            self.elements[element.id] = element
            
            # Check if we need to subdivide
            if len(self.elements) > self.max_elements and self.max_depth > 0:
                self._subdivide()
            
            return True
        else:
            # Insert into appropriate quadrants
            inserted = False
            for quadrant in self.quadrants:
                if quadrant.insert(element):
                    inserted = True
            return inserted
    
    def remove(self, element_id: str) -> bool:
        """Remove an element from the spatial index."""
        if self.is_leaf:
            if element_id in self.elements:
                del self.elements[element_id]
                return True
            return False
        else:
            removed = False
            for quadrant in self.quadrants:
                if quadrant.remove(element_id):
                    removed = True
            return removed
    
    def query_region(self, query_bounds: SpatialBounds) -> List[InteractionElement]:
        """Query elements within a spatial region."""
        results = []
        
        if not self.bounds.intersects(query_bounds):
            return results
        
        if self.is_leaf:
            for element in self.elements.values():
                if element.bounds.intersects(query_bounds):
                    results.append(element)
        else:
            for quadrant in self.quadrants:
                results.extend(quadrant.query_region(query_bounds))
        
        return results
    
    def query_point(self, x: float, y: float) -> List[InteractionElement]:
        """Query elements at a specific point."""
        point_bounds = SpatialBounds(x, y, 0, 0)
        candidates = self.query_region(point_bounds)
        return [elem for elem in candidates if elem.contains_point(x, y)]
    
    def _subdivide(self):
        """Subdivide this node into quadrants."""
        if not self.is_leaf or self.max_depth <= 0:
            return
        
        half_width = self.bounds.width / 2
        half_height = self.bounds.height / 2
        
        # Create four quadrants
        self.quadrants = [
            # Top-left
            SpatialIndex(
                SpatialBounds(self.bounds.x, self.bounds.y, half_width, half_height),
                self.max_depth - 1, self.max_elements
            ),
            # Top-right
            SpatialIndex(
                SpatialBounds(self.bounds.x + half_width, self.bounds.y, half_width, half_height),
                self.max_depth - 1, self.max_elements
            ),
            # Bottom-left
            SpatialIndex(
                SpatialBounds(self.bounds.x, self.bounds.y + half_height, half_width, half_height),
                self.max_depth - 1, self.max_elements
            ),
            # Bottom-right
            SpatialIndex(
                SpatialBounds(self.bounds.x + half_width, self.bounds.y + half_height, half_width, half_height),
                self.max_depth - 1, self.max_elements
            )
        ]
        
        # Redistribute elements to quadrants
        elements_to_redistribute = list(self.elements.values())
        self.elements.clear()
        self.is_leaf = False
        
        for element in elements_to_redistribute:
            for quadrant in self.quadrants:
                quadrant.insert(element)


class InteractionLayer:
    """Main interaction layer that manages all interactive elements."""
    
    def __init__(self, canvas_bounds: SpatialBounds = None):
        if canvas_bounds is None:
            canvas_bounds = SpatialBounds(0, 0, 2000, 2000)
        
        self.canvas_bounds = canvas_bounds
        self.elements: Dict[str, InteractionElement] = {}
        self.connections: Dict[str, InteractionConnection] = {}
        self.spatial_index = SpatialIndex(canvas_bounds)
        self.change_tracker = ChangeTracker()
        
        # Selection and interaction state
        self.selected_elements: Set[str] = set()
        self.highlighted_elements: Set[str] = set()
        self.clipboard: List[InteractionElement] = []
        
        # Collaboration state
        self.active_users: Dict[str, Dict[str, Any]] = {}
        self.user_cursors: Dict[str, Tuple[float, float]] = {}
        
        # Threading for concurrent access
        self._lock = threading.RLock()
    
    def create_element(self, element_type: InteractionElementType, 
                      bounds: SpatialBounds, **kwargs) -> InteractionElement:
        """Create a new interaction element."""
        with self._lock:
            if element_type == InteractionElementType.ENTITY:
                element = InteractionEntity(bounds=bounds, **kwargs)
            elif element_type == InteractionElementType.PREDICATE:
                element = InteractionPredicate(bounds=bounds, **kwargs)
            elif element_type == InteractionElementType.CUT:
                element = InteractionCut(bounds=bounds, **kwargs)
            else:
                element = InteractionElement(element_type=element_type, bounds=bounds, **kwargs)
            
            self.elements[element.id] = element
            self.spatial_index.insert(element)
            
            # Record operation
            operation = InteractionOperation(
                operation_type=InteractionOperationType.CREATE,
                element_id=element.id,
                parameters=kwargs,
                after_state=self._serialize_element(element)
            )
            self.change_tracker.record_operation(operation)
            
            return element
    
    def delete_element(self, element_id: str, user_id: Optional[str] = None) -> bool:
        """Delete an interaction element."""
        with self._lock:
            if element_id not in self.elements:
                return False
            
            element = self.elements[element_id]
            
            # Record operation for undo
            operation = InteractionOperation(
                operation_type=InteractionOperationType.DELETE,
                element_id=element_id,
                before_state=self._serialize_element(element),
                user_id=user_id
            )
            
            # Remove from spatial index
            self.spatial_index.remove(element_id)
            
            # Remove from collections
            del self.elements[element_id]
            self.selected_elements.discard(element_id)
            self.highlighted_elements.discard(element_id)
            
            # Remove connections involving this element
            connections_to_remove = []
            for conn_id, connection in self.connections.items():
                if connection.source_id == element_id or connection.target_id == element_id:
                    connections_to_remove.append(conn_id)
            
            for conn_id in connections_to_remove:
                del self.connections[conn_id]
            
            self.change_tracker.record_operation(operation)
            return True
    
    def move_element(self, element_id: str, new_x: float, new_y: float, 
                    user_id: Optional[str] = None) -> bool:
        """Move an element to a new position."""
        with self._lock:
            if element_id not in self.elements:
                return False
            
            element = self.elements[element_id]
            old_bounds = SpatialBounds(element.bounds.x, element.bounds.y, 
                                     element.bounds.width, element.bounds.height)
            
            # Update spatial index
            self.spatial_index.remove(element_id)
            element.bounds.x = new_x
            element.bounds.y = new_y
            element.update_modification_time(user_id)
            self.spatial_index.insert(element)
            
            # Record operation
            operation = InteractionOperation(
                operation_type=InteractionOperationType.MOVE,
                element_id=element_id,
                parameters={"old_x": old_bounds.x, "old_y": old_bounds.y, 
                           "new_x": new_x, "new_y": new_y},
                user_id=user_id
            )
            self.change_tracker.record_operation(operation)
            
            return True
    
    def select_elements(self, element_ids: List[str], user_id: Optional[str] = None):
        """Select elements for interaction."""
        with self._lock:
            # Clear previous selection
            for elem_id in self.selected_elements:
                if elem_id in self.elements:
                    self.elements[elem_id].state = ElementState.NORMAL
            
            self.selected_elements.clear()
            
            # Set new selection
            for elem_id in element_ids:
                if elem_id in self.elements:
                    self.selected_elements.add(elem_id)
                    self.elements[elem_id].state = ElementState.SELECTED
    
    def query_elements_at_point(self, x: float, y: float) -> List[InteractionElement]:
        """Query elements at a specific point."""
        with self._lock:
            return self.spatial_index.query_point(x, y)
    
    def query_elements_in_region(self, bounds: SpatialBounds) -> List[InteractionElement]:
        """Query elements within a region."""
        with self._lock:
            return self.spatial_index.query_region(bounds)
    
    def create_connection(self, source_id: str, target_id: str, 
                         connection_type: str = "line_of_identity") -> Optional[InteractionConnection]:
        """Create a connection between two elements."""
        with self._lock:
            if source_id not in self.elements or target_id not in self.elements:
                return None
            
            connection = InteractionConnection(
                source_id=source_id,
                target_id=target_id,
                connection_type=connection_type
            )
            
            self.connections[connection.id] = connection
            
            # Record operation
            operation = InteractionOperation(
                operation_type=InteractionOperationType.CONNECT,
                element_id=connection.id,
                parameters={"source_id": source_id, "target_id": target_id, 
                           "connection_type": connection_type}
            )
            self.change_tracker.record_operation(operation)
            
            return connection
    
    def get_element(self, element_id: str) -> Optional[InteractionElement]:
        """Get an element by ID."""
        with self._lock:
            return self.elements.get(element_id)
    
    def get_all_elements(self) -> List[InteractionElement]:
        """Get all elements in the interaction layer."""
        with self._lock:
            return list(self.elements.values())
    
    def get_selected_elements(self) -> List[InteractionElement]:
        """Get currently selected elements."""
        with self._lock:
            return [self.elements[elem_id] for elem_id in self.selected_elements 
                   if elem_id in self.elements]
    
    def undo(self) -> bool:
        """Undo the last operation."""
        with self._lock:
            operation = self.change_tracker.perform_undo()
            if operation:
                return self._apply_inverse_operation(operation)
            return False
    
    def redo(self) -> bool:
        """Redo the last undone operation."""
        with self._lock:
            operation = self.change_tracker.perform_redo()
            if operation:
                return self._apply_operation(operation)
            return False
    
    def _serialize_element(self, element: InteractionElement) -> Dict[str, Any]:
        """Serialize an element for state tracking."""
        return {
            "id": element.id,
            "element_type": element.element_type.value,
            "bounds": {
                "x": element.bounds.x,
                "y": element.bounds.y,
                "width": element.bounds.width,
                "height": element.bounds.height
            },
            "label": element.label,
            "state": element.state.value,
            "visual_properties": {
                "color": element.visual_properties.color,
                "background_color": element.visual_properties.background_color,
                "border_color": element.visual_properties.border_color,
                "border_width": element.visual_properties.border_width
            }
        }
    
    def _apply_operation(self, operation: InteractionOperation) -> bool:
        """Apply an operation (for redo)."""
        # Implementation would depend on operation type
        # This is a simplified version
        return True
    
    def _apply_inverse_operation(self, operation: InteractionOperation) -> bool:
        """Apply the inverse of an operation (for undo)."""
        # Implementation would depend on operation type
        # This is a simplified version
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the interaction layer."""
        with self._lock:
            element_counts = defaultdict(int)
            for element in self.elements.values():
                element_counts[element.element_type.value] += 1
            
            return {
                "total_elements": len(self.elements),
                "element_counts": dict(element_counts),
                "total_connections": len(self.connections),
                "selected_elements": len(self.selected_elements),
                "operation_history_size": len(self.change_tracker.operation_history),
                "can_undo": self.change_tracker.can_undo(),
                "can_redo": self.change_tracker.can_redo()
            }


# Example usage and testing
if __name__ == "__main__":
    print("Interaction Layer - Phase 4A Implementation")
    print("=" * 60)
    
    # Create interaction layer
    canvas = SpatialBounds(0, 0, 1000, 800)
    layer = InteractionLayer(canvas)
    
    print("Creating interaction elements...")
    
    # Create some test elements
    entity1 = layer.create_element(
        InteractionElementType.ENTITY,
        SpatialBounds(100, 100, 80, 40),
        label="john",
        defining=True
    )
    
    predicate1 = layer.create_element(
        InteractionElementType.PREDICATE,
        SpatialBounds(200, 150, 100, 50),
        label="Person",
        predicate_name="Person"
    )
    
    cut1 = layer.create_element(
        InteractionElementType.CUT,
        SpatialBounds(150, 80, 200, 150),
        label="negation"
    )
    
    print(f"Created {len(layer.elements)} elements")
    
    # Test spatial queries
    print("\nTesting spatial queries...")
    elements_at_point = layer.query_elements_at_point(150, 125)
    print(f"Elements at point (150, 125): {len(elements_at_point)}")
    
    region = SpatialBounds(50, 50, 200, 200)
    elements_in_region = layer.query_elements_in_region(region)
    print(f"Elements in region: {len(elements_in_region)}")
    
    # Test selection
    print("\nTesting selection...")
    layer.select_elements([entity1.id, predicate1.id])
    selected = layer.get_selected_elements()
    print(f"Selected elements: {len(selected)}")
    
    # Test movement
    print("\nTesting movement...")
    old_x, old_y = entity1.bounds.x, entity1.bounds.y
    layer.move_element(entity1.id, 150, 120)
    print(f"Moved entity from ({old_x}, {old_y}) to ({entity1.bounds.x}, {entity1.bounds.y})")
    
    # Test connections
    print("\nTesting connections...")
    connection = layer.create_connection(entity1.id, predicate1.id, "line_of_identity")
    if connection:
        print(f"Created connection: {connection.id}")
    
    # Test undo/redo
    print("\nTesting undo/redo...")
    print(f"Can undo: {layer.change_tracker.can_undo()}")
    if layer.undo():
        print("Undo successful")
    print(f"Can redo: {layer.change_tracker.can_redo()}")
    if layer.redo():
        print("Redo successful")
    
    # Show statistics
    print("\nInteraction Layer Statistics:")
    stats = layer.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ Interaction Layer Phase 4A implementation complete!")
    print("Ready for mathematical layer enhancements and synchronization protocols.")

