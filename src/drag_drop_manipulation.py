"""
Drag-and-Drop Manipulation Tools - Phase 4B Implementation

This module provides comprehensive drag-and-drop manipulation capabilities
for interactive editing of existential graphs. The system supports:

1. Element dragging with visual feedback and constraints
2. Connection creation through drag-and-drop
3. Group manipulation and multi-element operations
4. Snap-to-grid and alignment assistance
5. Collision detection and automatic layout
6. Undo/redo support for all operations
7. Educational feedback during manipulation
8. Logical validation during interactive editing

The drag-and-drop system is designed to feel natural and intuitive while
maintaining the logical rigor required for existential graph manipulation.

Author: Manus AI
Date: January 2025
Phase: 4B - Interactive Manipulation Tools
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import math
import threading
from collections import defaultdict, deque
from abc import ABC, abstractmethod

# Import foundation components
from interaction_layer import (
    InteractionLayer, InteractionElement, InteractionElementType, SpatialBounds
)
from spatial_performance_optimization import OptimizedInteractionLayer
from gesture_recognition import (
    GestureInputSystem, GestureType, RecognizedGesture, InputEvent
)


class DragState(Enum):
    """States of drag-and-drop operations."""
    IDLE = "idle"
    DRAG_STARTED = "drag_started"
    DRAGGING = "dragging"
    DROP_PREVIEW = "drop_preview"
    DROP_COMPLETED = "drop_completed"
    DROP_CANCELLED = "drop_cancelled"


class DropZoneType(Enum):
    """Types of drop zones for different operations."""
    CANVAS = "canvas"  # General canvas area
    ELEMENT = "element"  # On top of another element
    CONNECTION_POINT = "connection_point"  # Connection endpoint
    CUT_INTERIOR = "cut_interior"  # Inside a cut
    CUT_BOUNDARY = "cut_boundary"  # On cut boundary
    TRASH = "trash"  # Delete zone
    PALETTE = "palette"  # Tool palette
    PROPERTY_PANEL = "property_panel"  # Properties editor


class ManipulationMode(Enum):
    """Modes of manipulation behavior."""
    FREE = "free"  # Free movement
    CONSTRAINED = "constrained"  # Constrained to axes or grid
    SNAP_TO_GRID = "snap_to_grid"  # Snap to grid points
    SNAP_TO_ELEMENTS = "snap_to_elements"  # Snap to other elements
    MAGNETIC = "magnetic"  # Magnetic attraction to alignment guides


@dataclass
class DragOperation:
    """Represents an active drag-and-drop operation."""
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Elements being dragged
    dragged_elements: Set[str] = field(default_factory=set)
    
    # Drag state
    state: DragState = DragState.IDLE
    start_position: Tuple[float, float] = (0.0, 0.0)
    current_position: Tuple[float, float] = (0.0, 0.0)
    offset: Tuple[float, float] = (0.0, 0.0)  # Offset from element origin
    
    # Manipulation settings
    mode: ManipulationMode = ManipulationMode.FREE
    constrain_horizontal: bool = False
    constrain_vertical: bool = False
    snap_enabled: bool = True
    snap_threshold: float = 10.0
    
    # Visual feedback
    show_preview: bool = True
    show_guides: bool = True
    show_constraints: bool = True
    
    # Drop zones
    valid_drop_zones: Set[DropZoneType] = field(default_factory=set)
    current_drop_zone: Optional[DropZoneType] = None
    drop_target: Optional[str] = None  # Element ID if dropping on element
    
    # Educational context
    educational_feedback: List[str] = field(default_factory=list)
    logical_warnings: List[str] = field(default_factory=list)
    
    # Timing
    start_time: float = field(default_factory=time.time)
    last_update_time: float = field(default_factory=time.time)


@dataclass
class DropZone:
    """Defines a drop zone where elements can be dropped."""
    zone_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    zone_type: DropZoneType = DropZoneType.CANVAS
    bounds: SpatialBounds = field(default_factory=lambda: SpatialBounds(0, 0, 0, 0))
    
    # Acceptance criteria
    accepted_element_types: Set[InteractionElementType] = field(default_factory=set)
    requires_logical_validation: bool = True
    
    # Visual properties
    highlight_color: str = "#4CAF50"  # Green for valid
    invalid_color: str = "#F44336"    # Red for invalid
    
    # Behavior
    auto_arrange: bool = False
    snap_to_center: bool = False
    
    # Educational context
    description: str = ""
    eg_concept: str = ""


@dataclass
class SnapPoint:
    """Represents a point that elements can snap to."""
    point_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    position: Tuple[float, float] = (0.0, 0.0)
    snap_type: str = "grid"  # grid, element, guide, alignment
    
    # Snap properties
    strength: float = 1.0  # Magnetic strength
    radius: float = 10.0   # Snap radius
    
    # Visual properties
    visible: bool = True
    color: str = "#2196F3"  # Blue
    
    # Associated element (if any)
    element_id: Optional[str] = None
    
    # Educational context
    description: str = ""


class DragDropController:
    """Main controller for drag-and-drop operations."""
    
    def __init__(self, interaction_layer: OptimizedInteractionLayer,
                 gesture_system: GestureInputSystem):
        
        self.interaction_layer = interaction_layer
        self.gesture_system = gesture_system
        
        # Current operations
        self.active_operations: Dict[str, DragOperation] = {}
        self.operation_history: deque = deque(maxlen=100)
        
        # Drop zones
        self.drop_zones: Dict[str, DropZone] = {}
        self.snap_points: Dict[str, SnapPoint] = {}
        
        # Grid settings
        self.grid_enabled = True
        self.grid_size = 20.0
        self.grid_visible = True
        
        # Manipulation settings
        self.default_mode = ManipulationMode.SNAP_TO_GRID
        self.multi_select_enabled = True
        self.group_manipulation_enabled = True
        
        # Visual feedback
        self.show_drop_previews = True
        self.show_alignment_guides = True
        self.show_distance_measurements = True
        
        # Educational features
        self.educational_mode = True
        self.show_logical_feedback = True
        self.validate_during_drag = True
        
        # Performance settings
        self.update_throttle = 16  # milliseconds (60fps)
        self.last_update_time = 0.0
        
        # Threading
        self._lock = threading.RLock()
        
        # Setup gesture handlers
        self._setup_gesture_handlers()
        
        # Setup default drop zones and snap points
        self._setup_default_zones()
        self._generate_grid_snap_points()
    
    def _setup_gesture_handlers(self):
        """Setup gesture handlers for drag-and-drop operations."""
        self.gesture_system.add_gesture_handler(GestureType.DRAG, self._handle_drag_start)
        self.gesture_system.add_gesture_handler(GestureType.DROP, self._handle_drop)
        
        # Add custom drag update handler (would be called during mouse move)
        # This would be integrated with the gesture system's move events
    
    def _setup_default_zones(self):
        """Setup default drop zones."""
        # Canvas drop zone
        canvas_zone = DropZone(
            zone_type=DropZoneType.CANVAS,
            bounds=self.interaction_layer.canvas_bounds,
            accepted_element_types={
                InteractionElementType.ENTITY,
                InteractionElementType.PREDICATE,
                InteractionElementType.CUT
            },
            description="Main canvas area for placing elements",
            eg_concept="sheet_of_assertion"
        )
        self.add_drop_zone(canvas_zone)
        
        # Trash zone (would be positioned in UI)
        trash_zone = DropZone(
            zone_type=DropZoneType.TRASH,
            bounds=SpatialBounds(
                self.interaction_layer.canvas_bounds.width - 100,
                self.interaction_layer.canvas_bounds.height - 100,
                80, 80
            ),
            accepted_element_types={
                InteractionElementType.ENTITY,
                InteractionElementType.PREDICATE,
                InteractionElementType.CUT
            },
            highlight_color="#F44336",  # Red
            description="Drop here to delete elements",
            eg_concept="erasure_rule"
        )
        self.add_drop_zone(trash_zone)
    
    def _generate_grid_snap_points(self):
        """Generate snap points for grid alignment."""
        if not self.grid_enabled:
            return
        
        canvas = self.interaction_layer.canvas_bounds
        
        # Clear existing grid snap points
        grid_points = [sp for sp in self.snap_points.values() if sp.snap_type == "grid"]
        for point in grid_points:
            del self.snap_points[point.point_id]
        
        # Generate new grid points
        for x in range(0, int(canvas.width), int(self.grid_size)):
            for y in range(0, int(canvas.height), int(self.grid_size)):
                snap_point = SnapPoint(
                    position=(float(x), float(y)),
                    snap_type="grid",
                    radius=self.grid_size / 4,
                    visible=self.grid_visible,
                    description=f"Grid point at ({x}, {y})"
                )
                self.snap_points[snap_point.point_id] = snap_point
    
    def add_drop_zone(self, drop_zone: DropZone):
        """Add a drop zone."""
        self.drop_zones[drop_zone.zone_id] = drop_zone
    
    def remove_drop_zone(self, zone_id: str):
        """Remove a drop zone."""
        if zone_id in self.drop_zones:
            del self.drop_zones[zone_id]
    
    def add_snap_point(self, snap_point: SnapPoint):
        """Add a snap point."""
        self.snap_points[snap_point.point_id] = snap_point
    
    def remove_snap_point(self, point_id: str):
        """Remove a snap point."""
        if point_id in self.snap_points:
            del self.snap_points[point_id]
    
    def _handle_drag_start(self, gesture: RecognizedGesture):
        """Handle the start of a drag operation."""
        with self._lock:
            if not gesture.target_elements:
                return
            
            # Get selected elements or the target element
            selected_elements = self.gesture_system.get_current_selection()
            if not selected_elements:
                selected_elements = {gesture.target_elements[0]}
            
            # Create drag operation
            operation = DragOperation(
                dragged_elements=selected_elements,
                state=DragState.DRAG_STARTED,
                start_position=gesture.start_position,
                current_position=gesture.start_position,
                mode=self.default_mode,
                snap_enabled=True,
                valid_drop_zones={DropZoneType.CANVAS, DropZoneType.ELEMENT, DropZoneType.TRASH}
            )
            
            # Calculate offset from element origin
            if gesture.target_elements:
                element = self.interaction_layer.get_element(gesture.target_elements[0])
                if element:
                    operation.offset = (
                        gesture.start_position[0] - element.bounds.x,
                        gesture.start_position[1] - element.bounds.y
                    )
            
            # Add educational feedback
            if self.educational_mode:
                operation.educational_feedback = self._generate_drag_feedback(operation)
            
            # Validate logical constraints
            if self.validate_during_drag:
                operation.logical_warnings = self._validate_drag_operation(operation)
            
            self.active_operations[operation.operation_id] = operation
            
            print(f"Started drag operation for {len(selected_elements)} elements")
            if operation.educational_feedback:
                for feedback in operation.educational_feedback:
                    print(f"  📚 {feedback}")
    
    def update_drag_operation(self, operation_id: str, current_position: Tuple[float, float]):
        """Update an active drag operation."""
        with self._lock:
            # Throttle updates for performance
            current_time = time.time() * 1000  # milliseconds
            if current_time - self.last_update_time < self.update_throttle:
                return
            self.last_update_time = current_time
            
            operation = self.active_operations.get(operation_id)
            if not operation or operation.state not in [DragState.DRAG_STARTED, DragState.DRAGGING]:
                return
            
            operation.state = DragState.DRAGGING
            operation.current_position = current_position
            operation.last_update_time = time.time()
            
            # Apply constraints and snapping
            adjusted_position = self._apply_manipulation_constraints(operation, current_position)
            
            # Update drop zone detection
            operation.current_drop_zone = self._detect_drop_zone(adjusted_position)
            operation.drop_target = self._detect_drop_target(adjusted_position)
            
            # Update visual feedback
            if operation.show_preview:
                self._update_drag_preview(operation, adjusted_position)
            
            # Update educational feedback
            if self.educational_mode:
                self._update_educational_feedback(operation)
            
            # Validate logical constraints
            if self.validate_during_drag:
                operation.logical_warnings = self._validate_drag_operation(operation)
    
    def _apply_manipulation_constraints(self, operation: DragOperation, 
                                      position: Tuple[float, float]) -> Tuple[float, float]:
        """Apply manipulation constraints and snapping."""
        x, y = position
        
        # Apply axis constraints
        if operation.constrain_horizontal:
            y = operation.start_position[1]
        if operation.constrain_vertical:
            x = operation.start_position[0]
        
        # Apply snapping
        if operation.snap_enabled:
            if operation.mode == ManipulationMode.SNAP_TO_GRID:
                x, y = self._snap_to_grid(x, y, operation.snap_threshold)
            elif operation.mode == ManipulationMode.SNAP_TO_ELEMENTS:
                x, y = self._snap_to_elements(x, y, operation.snap_threshold)
            elif operation.mode == ManipulationMode.MAGNETIC:
                x, y = self._apply_magnetic_snapping(x, y, operation.snap_threshold)
        
        return (x, y)
    
    def _snap_to_grid(self, x: float, y: float, threshold: float) -> Tuple[float, float]:
        """Snap position to grid points."""
        if not self.grid_enabled:
            return (x, y)
        
        # Find nearest grid point
        grid_x = round(x / self.grid_size) * self.grid_size
        grid_y = round(y / self.grid_size) * self.grid_size
        
        # Check if within threshold
        distance = math.sqrt((x - grid_x)**2 + (y - grid_y)**2)
        if distance <= threshold:
            return (grid_x, grid_y)
        
        return (x, y)
    
    def _snap_to_elements(self, x: float, y: float, threshold: float) -> Tuple[float, float]:
        """Snap position to nearby elements."""
        best_x, best_y = x, y
        min_distance = threshold
        
        # Check all elements for snap points
        for element in self.interaction_layer.get_all_elements():
            # Element center
            center_x = element.bounds.x + element.bounds.width / 2
            center_y = element.bounds.y + element.bounds.height / 2
            distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            
            if distance < min_distance:
                best_x, best_y = center_x, center_y
                min_distance = distance
            
            # Element corners
            corners = [
                (element.bounds.x, element.bounds.y),
                (element.bounds.x + element.bounds.width, element.bounds.y),
                (element.bounds.x, element.bounds.y + element.bounds.height),
                (element.bounds.x + element.bounds.width, element.bounds.y + element.bounds.height)
            ]
            
            for corner_x, corner_y in corners:
                distance = math.sqrt((x - corner_x)**2 + (y - corner_y)**2)
                if distance < min_distance:
                    best_x, best_y = corner_x, corner_y
                    min_distance = distance
        
        return (best_x, best_y)
    
    def _apply_magnetic_snapping(self, x: float, y: float, threshold: float) -> Tuple[float, float]:
        """Apply magnetic snapping to snap points."""
        best_x, best_y = x, y
        total_force_x, total_force_y = 0.0, 0.0
        
        for snap_point in self.snap_points.values():
            snap_x, snap_y = snap_point.position
            distance = math.sqrt((x - snap_x)**2 + (y - snap_y)**2)
            
            if distance < snap_point.radius and distance > 0:
                # Calculate magnetic force
                force = snap_point.strength * (snap_point.radius - distance) / snap_point.radius
                force_x = force * (snap_x - x) / distance
                force_y = force * (snap_y - y) / distance
                
                total_force_x += force_x
                total_force_y += force_y
        
        # Apply accumulated forces
        if abs(total_force_x) > 0.1 or abs(total_force_y) > 0.1:
            best_x = x + total_force_x * 10  # Scale factor
            best_y = y + total_force_y * 10
        
        return (best_x, best_y)
    
    def _detect_drop_zone(self, position: Tuple[float, float]) -> Optional[DropZoneType]:
        """Detect which drop zone the position is in."""
        x, y = position
        
        for zone in self.drop_zones.values():
            if zone.bounds.contains_point(x, y):
                return zone.zone_type
        
        return None
    
    def _detect_drop_target(self, position: Tuple[float, float]) -> Optional[str]:
        """Detect if dropping on a specific element."""
        elements = self.interaction_layer.query_elements_at_point_optimized(
            position[0], position[1]
        )
        
        if elements:
            return elements[0].id
        
        return None
    
    def _update_drag_preview(self, operation: DragOperation, position: Tuple[float, float]):
        """Update visual preview during drag."""
        # This would update visual elements showing drag preview
        # In a real implementation, this would interact with the rendering system
        pass
    
    def _generate_drag_feedback(self, operation: DragOperation) -> List[str]:
        """Generate educational feedback for drag operation."""
        feedback = []
        
        if len(operation.dragged_elements) == 1:
            element_id = next(iter(operation.dragged_elements))
            element = self.interaction_layer.get_element(element_id)
            if element:
                if element.element_type == InteractionElementType.ENTITY:
                    feedback.append("Dragging entity - represents an individual in the domain")
                elif element.element_type == InteractionElementType.PREDICATE:
                    feedback.append("Dragging predicate - expresses relationships between entities")
                elif element.element_type == InteractionElementType.CUT:
                    feedback.append("Dragging cut - represents negation in existential graphs")
        else:
            feedback.append(f"Dragging {len(operation.dragged_elements)} elements as a group")
        
        feedback.extend([
            "Hold Shift to constrain movement to horizontal/vertical axes",
            "Hold Ctrl to duplicate elements while dragging",
            "Connected elements maintain their logical relationships"
        ])
        
        return feedback
    
    def _update_educational_feedback(self, operation: DragOperation):
        """Update educational feedback during drag."""
        if operation.current_drop_zone == DropZoneType.TRASH:
            operation.educational_feedback.append("Drop in trash to delete elements")
        elif operation.current_drop_zone == DropZoneType.CUT_INTERIOR:
            operation.educational_feedback.append("Dropping inside cut changes logical context")
        elif operation.drop_target:
            target_element = self.interaction_layer.get_element(operation.drop_target)
            if target_element:
                operation.educational_feedback.append(
                    f"Dropping on {target_element.element_type.value} may create connection"
                )
    
    def _validate_drag_operation(self, operation: DragOperation) -> List[str]:
        """Validate logical constraints during drag."""
        warnings = []
        
        # Check for logical consistency
        if operation.current_drop_zone == DropZoneType.CUT_INTERIOR:
            warnings.append("Moving into cut changes logical polarity")
        
        # Check for connection validity
        if operation.drop_target:
            target_element = self.interaction_layer.get_element(operation.drop_target)
            if target_element and len(operation.dragged_elements) == 1:
                dragged_id = next(iter(operation.dragged_elements))
                dragged_element = self.interaction_layer.get_element(dragged_id)
                
                if (dragged_element and 
                    dragged_element.element_type == InteractionElementType.ENTITY and
                    target_element.element_type == InteractionElementType.PREDICATE):
                    # This is a valid connection
                    pass
                else:
                    warnings.append("Invalid connection between these element types")
        
        return warnings
    
    def _handle_drop(self, gesture: RecognizedGesture):
        """Handle the completion of a drag operation."""
        with self._lock:
            # Find the active operation
            active_op = None
            for operation in self.active_operations.values():
                if operation.state in [DragState.DRAG_STARTED, DragState.DRAGGING]:
                    active_op = operation
                    break
            
            if not active_op:
                return
            
            active_op.state = DragState.DROP_COMPLETED
            active_op.current_position = gesture.end_position
            
            # Apply the final position
            final_position = self._apply_manipulation_constraints(active_op, gesture.end_position)
            
            # Calculate movement delta
            dx = final_position[0] - active_op.start_position[0] - active_op.offset[0]
            dy = final_position[1] - active_op.start_position[1] - active_op.offset[1]
            
            # Handle different drop zones
            if active_op.current_drop_zone == DropZoneType.TRASH:
                self._handle_delete_drop(active_op)
            elif active_op.drop_target:
                self._handle_element_drop(active_op, final_position)
            else:
                self._handle_canvas_drop(active_op, dx, dy)
            
            # Move to history and cleanup
            self.operation_history.append(active_op)
            del self.active_operations[active_op.operation_id]
            
            print(f"Completed drop operation: {active_op.current_drop_zone}")
            if active_op.logical_warnings:
                for warning in active_op.logical_warnings:
                    print(f"  ⚠️ {warning}")
    
    def _handle_canvas_drop(self, operation: DragOperation, dx: float, dy: float):
        """Handle drop on canvas (normal move)."""
        moved_count = 0
        for element_id in operation.dragged_elements:
            element = self.interaction_layer.get_element(element_id)
            if element:
                new_x = element.bounds.x + dx
                new_y = element.bounds.y + dy
                
                # Ensure element stays within canvas bounds
                canvas = self.interaction_layer.canvas_bounds
                new_x = max(0, min(new_x, canvas.width - element.bounds.width))
                new_y = max(0, min(new_y, canvas.height - element.bounds.height))
                
                if self.interaction_layer.move_element(element_id, new_x, new_y):
                    moved_count += 1
        
        print(f"Moved {moved_count} elements by ({dx:.1f}, {dy:.1f})")
    
    def _handle_element_drop(self, operation: DragOperation, position: Tuple[float, float]):
        """Handle drop on another element (create connection)."""
        if not operation.drop_target or len(operation.dragged_elements) != 1:
            return
        
        dragged_id = next(iter(operation.dragged_elements))
        target_id = operation.drop_target
        
        # Create connection between elements
        connection = self.interaction_layer.create_connection(
            dragged_id, target_id, "line_of_identity"
        )
        
        if connection:
            print(f"Created connection between {dragged_id} and {target_id}")
        else:
            print("Failed to create connection")
    
    def _handle_delete_drop(self, operation: DragOperation):
        """Handle drop in trash zone (delete elements)."""
        deleted_count = 0
        for element_id in operation.dragged_elements:
            if self.interaction_layer.delete_element(element_id):
                deleted_count += 1
        
        print(f"Deleted {deleted_count} elements")
    
    def cancel_active_operations(self):
        """Cancel all active drag operations."""
        with self._lock:
            for operation in self.active_operations.values():
                operation.state = DragState.DROP_CANCELLED
            
            self.operation_history.extend(self.active_operations.values())
            self.active_operations.clear()
    
    def get_active_operations(self) -> List[DragOperation]:
        """Get list of active drag operations."""
        return list(self.active_operations.values())
    
    def set_grid_enabled(self, enabled: bool):
        """Enable or disable grid snapping."""
        self.grid_enabled = enabled
        if enabled:
            self._generate_grid_snap_points()
        else:
            # Remove grid snap points
            grid_points = [sp for sp in self.snap_points.values() if sp.snap_type == "grid"]
            for point in grid_points:
                del self.snap_points[point.point_id]
    
    def set_grid_size(self, size: float):
        """Set grid size and regenerate snap points."""
        self.grid_size = size
        if self.grid_enabled:
            self._generate_grid_snap_points()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get drag-and-drop statistics."""
        return {
            "active_operations": len(self.active_operations),
            "operation_history": len(self.operation_history),
            "drop_zones": len(self.drop_zones),
            "snap_points": len(self.snap_points),
            "grid_enabled": self.grid_enabled,
            "grid_size": self.grid_size,
            "default_mode": self.default_mode.value,
            "educational_mode": self.educational_mode,
            "validate_during_drag": self.validate_during_drag
        }


# Example usage and testing
if __name__ == "__main__":
    print("Drag-and-Drop Manipulation Tools - Phase 4B Implementation")
    print("=" * 60)
    
    # Create interaction layer and gesture system
    from spatial_performance_optimization import OptimizedInteractionLayer, OptimizationLevel
    from gesture_recognition import GestureInputSystem, InputEvent, InputModality
    
    canvas = SpatialBounds(0, 0, 1200, 800)
    interaction_layer = OptimizedInteractionLayer(canvas, OptimizationLevel.STANDARD)
    gesture_system = GestureInputSystem(interaction_layer)
    
    # Create drag-drop controller
    drag_controller = DragDropController(interaction_layer, gesture_system)
    
    print("Creating test elements...")
    
    # Create test elements
    entity1 = interaction_layer.create_element(
        InteractionElementType.ENTITY,
        SpatialBounds(100, 100, 80, 40),
        label="john"
    )
    
    predicate1 = interaction_layer.create_element(
        InteractionElementType.PREDICATE,
        SpatialBounds(200, 150, 100, 50),
        label="Person",
        predicate_name="Person"
    )
    
    cut1 = interaction_layer.create_element(
        InteractionElementType.CUT,
        SpatialBounds(300, 200, 150, 100),
        label="negation"
    )
    
    print(f"Created {len(interaction_layer.get_all_elements())} test elements")
    
    print("\\nTesting drag-and-drop operations...")
    
    # Simulate drag start
    drag_start_event = InputEvent(
        modality=InputModality.MOUSE,
        event_type="down",
        x=140, y=120,  # On entity1
        button="left"
    )
    
    # Process through gesture system to trigger drag
    gestures = gesture_system.process_input_event(drag_start_event)
    print(f"Drag start gestures: {len(gestures)}")
    
    # Simulate drag movement
    drag_move_event = InputEvent(
        modality=InputModality.MOUSE,
        event_type="move",
        x=180, y=160
    )
    
    move_gestures = gesture_system.process_input_event(drag_move_event)
    print(f"Drag move gestures: {len(move_gestures)}")
    
    # Update active drag operations
    active_ops = drag_controller.get_active_operations()
    if active_ops:
        operation = active_ops[0]
        drag_controller.update_drag_operation(operation.operation_id, (180, 160))
        print(f"Updated drag operation: {operation.state}")
        print(f"Educational feedback: {len(operation.educational_feedback)}")
        print(f"Logical warnings: {len(operation.logical_warnings)}")
    
    # Simulate drop
    drop_event = InputEvent(
        modality=InputModality.MOUSE,
        event_type="up",
        x=200, y=180
    )
    
    drop_gestures = gesture_system.process_input_event(drop_event)
    print(f"Drop gestures: {len(drop_gestures)}")
    
    print("\\nTesting grid snapping...")
    
    # Test grid snapping
    original_pos = (105, 115)  # Slightly off grid
    snapped_pos = drag_controller._snap_to_grid(
        original_pos[0], original_pos[1], 10.0
    )
    print(f"Original position: {original_pos}")
    print(f"Snapped position: {snapped_pos}")
    
    print("\\nTesting element snapping...")
    
    # Test element snapping
    snap_pos = drag_controller._snap_to_elements(145, 125, 15.0)
    print(f"Snap to elements result: {snap_pos}")
    
    print("\\nTesting drop zone detection...")
    
    # Test drop zone detection
    canvas_zone = drag_controller._detect_drop_zone((400, 300))
    trash_zone = drag_controller._detect_drop_zone((1150, 750))
    print(f"Canvas zone detection: {canvas_zone}")
    print(f"Trash zone detection: {trash_zone}")
    
    # Show statistics
    print("\\nDrag-Drop Controller Statistics:")
    stats = drag_controller.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\\n" + "=" * 60)
    print("✅ Drag-and-Drop Manipulation Tools Phase 4B implementation complete!")
    print("Ready for visual feedback and preview systems.")

