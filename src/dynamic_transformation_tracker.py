"""
Dynamic Transformation Tracker: Maintains spatial correspondences during interactive transformations.

This system handles:
1. Element insertion/deletion with automatic area assignment
2. Cut resizing with containment preservation
3. Overlap avoidance during dynamic layout changes
4. Real-time spatial correspondence updates
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Callable
from enum import Enum

from PySide6.QtCore import QPointF, QRectF, QObject, Signal
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import QGraphicsScene

from egi_core_dau import ElementID, RelationalGraphWithCuts, Vertex, Edge, Cut
from spatial_area_manager import SpatialAreaManager


class TransformationType(Enum):
    """Types of transformations that can be applied to the diagram."""
    INSERT_VERTEX = "insert_vertex"
    DELETE_VERTEX = "delete_vertex"
    INSERT_EDGE = "insert_edge"
    DELETE_EDGE = "delete_edge"
    INSERT_CUT = "insert_cut"
    DELETE_CUT = "delete_cut"
    MOVE_ELEMENT = "move_element"
    RESIZE_CUT = "resize_cut"


@dataclass
class TransformationEvent:
    """Represents a transformation event that affects spatial layout."""
    transformation_type: TransformationType
    element_id: ElementID
    target_area: Optional[ElementID] = None
    new_position: Optional[QPointF] = None
    new_bounds: Optional[QRectF] = None
    affected_elements: Set[ElementID] = None
    
    def __post_init__(self):
        if self.affected_elements is None:
            self.affected_elements = set()


class DynamicTransformationTracker(QObject):
    """
    Tracks and manages spatial correspondences during interactive transformations.
    
    This system ensures that:
    - New elements are positioned in appropriate areas
    - Existing elements maintain their area assignments
    - Cuts resize to accommodate new content
    - No overlapping occurs during transformations
    """
    
    # Signals
    transformation_applied = Signal(TransformationEvent)
    spatial_update_required = Signal()
    containment_violation = Signal(ElementID, ElementID)  # element, expected_area
    
    def __init__(self, spatial_manager: SpatialAreaManager, graphics_scene: QGraphicsScene):
        super().__init__()
        self.spatial_manager = spatial_manager
        self.graphics_scene = graphics_scene
        self.current_egi: Optional[RelationalGraphWithCuts] = None
        self.layout_positions: Dict[ElementID, QPointF] = {}
        self.cut_bounds: Dict[ElementID, QRectF] = {}
        
        # Transformation history for undo/redo
        self.transformation_history: List[TransformationEvent] = []
        self.max_history_size = 100
        
        # Layout constraints
        self.min_cut_padding = 30.0
        self.min_element_spacing = 20.0
        self.auto_resize_cuts = True
        
    def initialize(self, egi: RelationalGraphWithCuts, layout_positions: Dict[ElementID, QPointF], 
                   cut_bounds: Dict[ElementID, QRectF]):
        """Initialize with current EGI state."""
        self.current_egi = egi
        self.layout_positions = layout_positions.copy()
        self.cut_bounds = cut_bounds.copy()
        
    def apply_transformation(self, event: TransformationEvent) -> bool:
        """Apply a transformation and update spatial correspondences."""
        print(f"DEBUG: Applying transformation {event.transformation_type} for element {event.element_id}")
        
        success = False
        
        if event.transformation_type == TransformationType.INSERT_VERTEX:
            success = self._handle_vertex_insertion(event)
        elif event.transformation_type == TransformationType.DELETE_VERTEX:
            success = self._handle_vertex_deletion(event)
        elif event.transformation_type == TransformationType.INSERT_EDGE:
            success = self._handle_edge_insertion(event)
        elif event.transformation_type == TransformationType.DELETE_EDGE:
            success = self._handle_edge_deletion(event)
        elif event.transformation_type == TransformationType.INSERT_CUT:
            success = self._handle_cut_insertion(event)
        elif event.transformation_type == TransformationType.DELETE_CUT:
            success = self._handle_cut_deletion(event)
        elif event.transformation_type == TransformationType.MOVE_ELEMENT:
            success = self._handle_element_move(event)
        elif event.transformation_type == TransformationType.RESIZE_CUT:
            success = self._handle_cut_resize(event)
        
        if success:
            # Update transformation history
            self.transformation_history.append(event)
            if len(self.transformation_history) > self.max_history_size:
                self.transformation_history.pop(0)
            
            # Emit signals
            self.transformation_applied.emit(event)
            self.spatial_update_required.emit()
            
            print(f"DEBUG: Transformation applied successfully")
        else:
            print(f"ERROR: Failed to apply transformation {event.transformation_type}")
        
        return success
    
    def _handle_vertex_insertion(self, event: TransformationEvent) -> bool:
        """Handle insertion of a new vertex."""
        if not event.target_area or not event.new_position:
            return False
        
        # Verify position is within target area
        actual_area = self.spatial_manager.get_area_at_point(event.new_position)
        if actual_area != event.target_area:
            # Find safe position within target area
            safe_position = self.spatial_manager.get_safe_position_in_area(event.target_area, self.min_cut_padding)
            if safe_position:
                event.new_position = safe_position
                print(f"DEBUG: Adjusted vertex position to {safe_position} for area {event.target_area}")
            else:
                return False
        
        # Update layout positions
        self.layout_positions[event.element_id] = event.new_position
        
        # Check if target area needs resizing
        if self.auto_resize_cuts and event.target_area != self.current_egi.sheet:
            self._resize_cut_for_content(event.target_area)
        
        return True
    
    def _handle_vertex_deletion(self, event: TransformationEvent) -> bool:
        """Handle deletion of a vertex."""
        if event.element_id in self.layout_positions:
            del self.layout_positions[event.element_id]
        
        # Find area containing this vertex
        containing_area = None
        for area_id, contents in self.current_egi.area.items():
            if event.element_id in contents:
                containing_area = area_id
                break
        
        # Check if containing cut can be resized smaller
        if containing_area and containing_area != self.current_egi.sheet and self.auto_resize_cuts:
            self._resize_cut_for_content(containing_area)
        
        return True
    
    def _handle_edge_insertion(self, event: TransformationEvent) -> bool:
        """Handle insertion of a new edge."""
        if not event.target_area or not event.new_position:
            return False
        
        # Verify position is within target area
        actual_area = self.spatial_manager.get_area_at_point(event.new_position)
        if actual_area != event.target_area:
            # Find safe position within target area
            safe_position = self.spatial_manager.get_safe_position_in_area(event.target_area, self.min_cut_padding)
            if safe_position:
                event.new_position = safe_position
                print(f"DEBUG: Adjusted edge position to {safe_position} for area {event.target_area}")
            else:
                return False
        
        # Update layout positions
        self.layout_positions[event.element_id] = event.new_position
        
        # Check if target area needs resizing
        if self.auto_resize_cuts and event.target_area != self.current_egi.sheet:
            self._resize_cut_for_content(event.target_area)
        
        return True
    
    def _handle_edge_deletion(self, event: TransformationEvent) -> bool:
        """Handle deletion of an edge."""
        if event.element_id in self.layout_positions:
            del self.layout_positions[event.element_id]
        
        # Find area containing this edge
        containing_area = None
        for area_id, contents in self.current_egi.area.items():
            if event.element_id in contents:
                containing_area = area_id
                break
        
        # Check if containing cut can be resized smaller
        if containing_area and containing_area != self.current_egi.sheet and self.auto_resize_cuts:
            self._resize_cut_for_content(containing_area)
        
        return True
    
    def _handle_cut_insertion(self, event: TransformationEvent) -> bool:
        """Handle insertion of a new cut."""
        if not event.target_area or not event.new_bounds:
            return False
        
        # Ensure new cut doesn't overlap with existing cuts
        adjusted_bounds = self._find_non_overlapping_bounds(event.new_bounds, event.target_area)
        if not adjusted_bounds:
            return False
        
        # Update cut bounds
        self.cut_bounds[event.element_id] = adjusted_bounds
        
        # Update spatial manager
        self.spatial_manager.update_cut_boundary(event.element_id, adjusted_bounds)
        
        # Resize parent area if needed
        if self.auto_resize_cuts and event.target_area != self.current_egi.sheet:
            self._resize_cut_for_content(event.target_area)
        
        return True
    
    def _handle_cut_deletion(self, event: TransformationEvent) -> bool:
        """Handle deletion of a cut."""
        if event.element_id in self.cut_bounds:
            del self.cut_bounds[event.element_id]
        
        # Remove from spatial manager
        if event.element_id in self.spatial_manager.area_items:
            item = self.spatial_manager.area_items[event.element_id]
            self.graphics_scene.removeItem(item)
            del self.spatial_manager.area_items[event.element_id]
        
        return True
    
    def _handle_element_move(self, event: TransformationEvent) -> bool:
        """Handle moving an element to a new position."""
        if not event.new_position:
            return False
        
        # Check if new position changes area assignment
        new_area = self.spatial_manager.get_area_at_point(event.new_position)
        old_position = self.layout_positions.get(event.element_id)
        old_area = None
        
        if old_position:
            old_area = self.spatial_manager.get_area_at_point(old_position)
        
        # Update position
        self.layout_positions[event.element_id] = event.new_position
        
        # If area changed, update EGI structure and resize cuts
        if new_area != old_area:
            print(f"DEBUG: Element {event.element_id} moved from area {old_area} to {new_area}")
            
            # Resize affected cuts
            if old_area and old_area != self.current_egi.sheet and self.auto_resize_cuts:
                self._resize_cut_for_content(old_area)
            
            if new_area and new_area != self.current_egi.sheet and self.auto_resize_cuts:
                self._resize_cut_for_content(new_area)
        
        return True
    
    def _handle_cut_resize(self, event: TransformationEvent) -> bool:
        """Handle manual resizing of a cut."""
        if not event.new_bounds:
            return False
        
        # Ensure resized cut doesn't overlap with siblings
        adjusted_bounds = self._find_non_overlapping_bounds(event.new_bounds, None, exclude_cut=event.element_id)
        if not adjusted_bounds:
            return False
        
        # Ensure all contained elements remain within bounds
        if not self._validate_cut_contains_elements(event.element_id, adjusted_bounds):
            # Expand bounds to contain all elements
            adjusted_bounds = self._expand_bounds_for_elements(event.element_id, adjusted_bounds)
        
        # Update cut bounds
        self.cut_bounds[event.element_id] = adjusted_bounds
        
        # Update spatial manager
        self.spatial_manager.update_cut_boundary(event.element_id, adjusted_bounds)
        
        return True
    
    def _resize_cut_for_content(self, cut_id: ElementID):
        """Automatically resize a cut to fit its content with appropriate padding."""
        if cut_id == self.current_egi.sheet or cut_id not in self.cut_bounds:
            return
        
        # Find all elements in this cut
        cut_elements = []
        if cut_id in self.current_egi.area:
            for elem_id in self.current_egi.area[cut_id]:
                if elem_id in self.layout_positions:
                    cut_elements.append(elem_id)
        
        if not cut_elements:
            # Empty cut - use minimum size
            current_bounds = self.cut_bounds[cut_id]
            min_size = 100.0
            center = current_bounds.center()
            new_bounds = QRectF(center.x() - min_size/2, center.y() - min_size/2, min_size, min_size)
        else:
            # Calculate bounds needed for all elements
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            
            for elem_id in cut_elements:
                pos = self.layout_positions[elem_id]
                min_x = min(min_x, pos.x())
                max_x = max(max_x, pos.x())
                min_y = min(min_y, pos.y())
                max_y = max(max_y, pos.y())
            
            # Add padding
            padding = self.min_cut_padding
            new_bounds = QRectF(
                min_x - padding, min_y - padding,
                max_x - min_x + 2 * padding, max_y - min_y + 2 * padding
            )
        
        # Ensure minimum size
        if new_bounds.width() < 80:
            center_x = new_bounds.center().x()
            new_bounds.setLeft(center_x - 40)
            new_bounds.setRight(center_x + 40)
        
        if new_bounds.height() < 60:
            center_y = new_bounds.center().y()
            new_bounds.setTop(center_y - 30)
            new_bounds.setBottom(center_y + 30)
        
        # Check for overlaps and adjust
        adjusted_bounds = self._find_non_overlapping_bounds(new_bounds, None, exclude_cut=cut_id)
        if adjusted_bounds:
            self.cut_bounds[cut_id] = adjusted_bounds
            self.spatial_manager.update_cut_boundary(cut_id, adjusted_bounds)
            print(f"DEBUG: Resized cut {cut_id} to {adjusted_bounds}")
    
    def _find_non_overlapping_bounds(self, desired_bounds: QRectF, parent_area: Optional[ElementID] = None, 
                                   exclude_cut: Optional[ElementID] = None) -> Optional[QRectF]:
        """Find bounds that don't overlap with existing cuts."""
        # Simple implementation - could be enhanced with more sophisticated algorithms
        test_bounds = QRectF(desired_bounds)
        
        max_attempts = 10
        for attempt in range(max_attempts):
            overlaps = False
            
            for cut_id, cut_bounds in self.cut_bounds.items():
                if cut_id == exclude_cut:
                    continue
                
                if test_bounds.intersects(cut_bounds):
                    overlaps = True
                    # Move test bounds to avoid overlap
                    if test_bounds.center().x() < cut_bounds.center().x():
                        test_bounds.moveRight(cut_bounds.left() - 10)
                    else:
                        test_bounds.moveLeft(cut_bounds.right() + 10)
                    break
            
            if not overlaps:
                return test_bounds
        
        return None  # Could not find non-overlapping position
    
    def _validate_cut_contains_elements(self, cut_id: ElementID, bounds: QRectF) -> bool:
        """Check if cut bounds contain all elements assigned to the cut."""
        if cut_id not in self.current_egi.area:
            return True
        
        margin = 10.0  # Small margin for element positioning
        safe_bounds = bounds.adjusted(margin, margin, -margin, -margin)
        
        for elem_id in self.current_egi.area[cut_id]:
            if elem_id in self.layout_positions:
                pos = self.layout_positions[elem_id]
                if not safe_bounds.contains(pos):
                    return False
        
        return True
    
    def _expand_bounds_for_elements(self, cut_id: ElementID, current_bounds: QRectF) -> QRectF:
        """Expand cut bounds to contain all assigned elements."""
        if cut_id not in self.current_egi.area:
            return current_bounds
        
        # Find bounds of all elements
        element_positions = []
        for elem_id in self.current_egi.area[cut_id]:
            if elem_id in self.layout_positions:
                element_positions.append(self.layout_positions[elem_id])
        
        if not element_positions:
            return current_bounds
        
        # Calculate required bounds
        min_x = min(pos.x() for pos in element_positions)
        max_x = max(pos.x() for pos in element_positions)
        min_y = min(pos.y() for pos in element_positions)
        max_y = max(pos.y() for pos in element_positions)
        
        # Add padding
        padding = self.min_cut_padding
        expanded_bounds = QRectF(
            min_x - padding, min_y - padding,
            max_x - min_x + 2 * padding, max_y - min_y + 2 * padding
        )
        
        # Take union with current bounds to ensure we don't shrink
        return current_bounds.united(expanded_bounds)
    
    def get_transformation_history(self) -> List[TransformationEvent]:
        """Get history of applied transformations."""
        return self.transformation_history.copy()
    
    def clear_history(self):
        """Clear transformation history."""
        self.transformation_history.clear()
    
    def debug_spatial_state(self) -> str:
        """Generate debug information about current spatial state."""
        info = ["=== Dynamic Transformation Tracker State ==="]
        info.append(f"Layout positions: {len(self.layout_positions)}")
        info.append(f"Cut bounds: {len(self.cut_bounds)}")
        info.append(f"Transformation history: {len(self.transformation_history)}")
        
        # Check for spatial violations
        violations = 0
        for element_id, position in self.layout_positions.items():
            expected_area = None
            for area_id, contents in self.current_egi.area.items():
                if element_id in contents:
                    expected_area = area_id
                    break
            
            if expected_area:
                actual_area = self.spatial_manager.get_area_at_point(position)
                if actual_area != expected_area:
                    violations += 1
        
        info.append(f"Spatial violations: {violations}")
        
        return "\n".join(info)
