"""
Enhanced Constraint Validation System for Ergasterion Phase 1

This module provides enhanced constraint validation that integrates with the drawing editor
and supports both Permissive and Strict modes with proper feedback and snap-back functionality.
"""

from typing import Dict, List, Tuple, Optional, Any
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QGraphicsScene

# Import the constraint engine functions
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "Arisbe" / "src" / "controller"))
from constraint_engine import validate_syntactic_constraints, validate_semantic_constraints


class ConstraintValidationResult:
    """Result of constraint validation with detailed feedback."""
    
    def __init__(self, is_valid: bool, violation_type: str = "", message: str = "", 
                 suggested_position: Optional[QPointF] = None, auto_adjustment: Optional[Dict] = None):
        self.is_valid = is_valid
        self.violation_type = violation_type  # "syntactic", "semantic", or ""
        self.message = message
        self.suggested_position = suggested_position
        self.auto_adjustment = auto_adjustment


class EnhancedConstraintValidator:
    """Enhanced constraint validator for Phase 1 implementation."""
    
    def __init__(self, scene: QGraphicsScene):
        self.scene = scene
        self.permissive_mode = True  # Default to permissive mode
        self.semantic_enabled = False
        
    def set_mode(self, permissive: bool, semantic_enabled: bool = False):
        """Set constraint validation mode."""
        self.permissive_mode = permissive
        self.semantic_enabled = semantic_enabled
        print(f"Constraint mode: {'Permissive' if permissive else 'Strict'}, Semantic: {semantic_enabled}")
    
    def validate_element_movement(self, item_id: str, new_position: QPointF, 
                                original_position: QPointF) -> ConstraintValidationResult:
        """Validate element movement with mode-specific behavior."""
        
        # Build DTO for validation
        dto = self._build_scene_dto(item_id, new_position)
        
        # Always validate syntactic constraints
        syntactic_ok, syntactic_msg, syntactic_info = validate_syntactic_constraints(dto)
        
        if not syntactic_ok:
            if self.permissive_mode:
                # Permissive mode: allow free drag, snap back on invalid drop
                return ConstraintValidationResult(
                    is_valid=False,
                    violation_type="syntactic",
                    message=f"Syntactic violation: {syntactic_msg}",
                    suggested_position=original_position
                )
            else:
                # Strict mode: prevent movement entirely
                return ConstraintValidationResult(
                    is_valid=False,
                    violation_type="syntactic",
                    message=f"Movement blocked: {syntactic_msg}",
                    suggested_position=original_position
                )
        
        # Validate semantic constraints if enabled
        if self.semantic_enabled:
            semantic_ok, semantic_msg, semantic_info = validate_semantic_constraints(dto)
            
            if not semantic_ok:
                if self.permissive_mode:
                    # Permissive mode: snap back
                    return ConstraintValidationResult(
                        is_valid=False,
                        violation_type="semantic",
                        message=f"Semantic violation: {semantic_msg}",
                        suggested_position=original_position
                    )
                else:
                    # Strict mode: attempt auto-adjustment
                    adjusted_position = self._attempt_auto_adjustment(item_id, new_position, semantic_info)
                    if adjusted_position:
                        return ConstraintValidationResult(
                            is_valid=True,
                            violation_type="semantic",
                            message=f"Auto-adjusted: {semantic_msg}",
                            suggested_position=adjusted_position,
                            auto_adjustment={"original": new_position, "adjusted": adjusted_position}
                        )
                    else:
                        return ConstraintValidationResult(
                            is_valid=False,
                            violation_type="semantic",
                            message=f"Cannot adjust: {semantic_msg}",
                            suggested_position=original_position
                        )
        
        # All constraints satisfied
        return ConstraintValidationResult(is_valid=True)
    
    def validate_element_creation(self, element_type: str, position: QPointF, 
                                area_id: str) -> ConstraintValidationResult:
        """Validate element creation at specified position."""
        
        # Create temporary DTO with new element
        dto = self._build_scene_dto()
        
        # Add the new element to DTO
        if element_type == "vertex":
            temp_id = "temp_vertex"
            dto.setdefault("vertices", {})[temp_id] = {
                "pos": (position.x(), position.y()),
                "radius": 4.0,
                "area_id": area_id
            }
        elif element_type == "predicate":
            temp_id = "temp_predicate"
            dto.setdefault("predicates", {})[temp_id] = {
                "rect": (position.x(), position.y(), 50.0, 20.0),  # Default size
                "text": "P",
                "area_id": area_id
            }
        elif element_type == "cut":
            temp_id = "temp_cut"
            dto.setdefault("cuts", {})[temp_id] = {
                "rect": (position.x(), position.y(), 150.0, 100.0),  # Default size
                "parent_id": area_id if area_id != "sheet" else None
            }
        
        # Validate with new element
        syntactic_ok, syntactic_msg, syntactic_info = validate_syntactic_constraints(dto)
        
        if not syntactic_ok:
            return ConstraintValidationResult(
                is_valid=False,
                violation_type="syntactic",
                message=f"Cannot create {element_type}: {syntactic_msg}"
            )
        
        if self.semantic_enabled:
            semantic_ok, semantic_msg, semantic_info = validate_semantic_constraints(dto)
            if not semantic_ok:
                return ConstraintValidationResult(
                    is_valid=False,
                    violation_type="semantic",
                    message=f"Cannot create {element_type}: {semantic_msg}"
                )
        
        return ConstraintValidationResult(is_valid=True)
    
    def _build_scene_dto(self, moving_item_id: str = None, new_position: QPointF = None) -> Dict[str, Any]:
        """Build DTO representation of current scene state."""
        dto = {
            "cuts": {},
            "vertices": {},
            "predicates": {},
            "ligatures": {}
        }
        
        # Collect all scene items
        for item in self.scene.items():
            if hasattr(item, 'cut_id'):
                # Cut item
                cut_rect = item.sceneBoundingRect()
                dto["cuts"][item.cut_id] = {
                    "rect": (cut_rect.x(), cut_rect.y(), cut_rect.width(), cut_rect.height())
                }
                
            elif hasattr(item, 'vertex_id'):
                # Vertex item
                pos = item.sceneBoundingRect().center()
                
                # Use new position if this is the item being moved
                if moving_item_id == f"vertex_{item.vertex_id}" and new_position:
                    pos = new_position
                
                dto["vertices"][item.vertex_id] = {
                    "pos": (pos.x(), pos.y()),
                    "radius": getattr(item, 'radius', 4.0),
                    "area_id": self._determine_area_for_position(pos)
                }
                
            elif hasattr(item, 'predicate_id'):
                # Predicate item
                rect = item.sceneBoundingRect()
                
                # Use new position if this is the item being moved
                if moving_item_id == f"predicate_{item.predicate_id}" and new_position:
                    rect = QRectF(new_position.x(), new_position.y(), rect.width(), rect.height())
                
                dto["predicates"][item.predicate_id] = {
                    "rect": (rect.x(), rect.y(), rect.width(), rect.height()),
                    "text": getattr(item, 'text', 'P'),
                    "area_id": self._determine_area_for_position(rect.center())
                }
        
        return dto
    
    def _determine_area_for_position(self, position: QPointF) -> str:
        """Determine which area contains the given position."""
        # Find the smallest cut that contains this position
        containing_cuts = []
        
        for item in self.scene.items():
            if hasattr(item, 'cut_id'):
                cut_rect = item.sceneBoundingRect()
                if cut_rect.contains(position):
                    area_size = cut_rect.width() * cut_rect.height()
                    containing_cuts.append({
                        'id': item.cut_id,
                        'area': area_size
                    })
        
        if containing_cuts:
            # Return the smallest cut (deepest nesting)
            smallest_cut = min(containing_cuts, key=lambda x: x['area'])
            return f"cut_{smallest_cut['id']}"
        else:
            return "sheet"
    
    def _attempt_auto_adjustment(self, item_id: str, position: QPointF, 
                                constraint_info: Dict) -> Optional[QPointF]:
        """Attempt to automatically adjust position to satisfy constraints."""
        # For Phase 1, we'll implement basic auto-adjustment
        # More sophisticated adjustment can be added in Phase 2
        
        # Try moving the element slightly in different directions
        adjustments = [
            QPointF(10, 0), QPointF(-10, 0), QPointF(0, 10), QPointF(0, -10),
            QPointF(10, 10), QPointF(-10, -10), QPointF(10, -10), QPointF(-10, 10)
        ]
        
        for adjustment in adjustments:
            test_position = position + adjustment
            dto = self._build_scene_dto(item_id, test_position)
            
            # Test if this position satisfies constraints
            syntactic_ok, _, _ = validate_syntactic_constraints(dto)
            if syntactic_ok:
                if self.semantic_enabled:
                    semantic_ok, _, _ = validate_semantic_constraints(dto)
                    if semantic_ok:
                        return test_position
                else:
                    return test_position
        
        return None  # No valid adjustment found


class ConstraintModeManager:
    """Manager for constraint modes and validation."""
    
    def __init__(self, validator: EnhancedConstraintValidator):
        self.validator = validator
        self.current_mode = "permissive"
        
    def set_permissive_mode(self):
        """Set to permissive mode: free drag, snap back on invalid drop."""
        self.current_mode = "permissive"
        self.validator.set_mode(permissive=True, semantic_enabled=False)
        
    def set_strict_mode(self, semantic_enabled: bool = True):
        """Set to strict mode: enforce constraints with auto-adjustment."""
        self.current_mode = "strict"
        self.validator.set_mode(permissive=False, semantic_enabled=semantic_enabled)
    
    def get_mode_description(self) -> str:
        """Get description of current mode."""
        if self.current_mode == "permissive":
            return "Permissive: Free drag, snap back on invalid drop"
        else:
            semantic_status = "ON" if self.validator.semantic_enabled else "OFF"
            return f"Strict: Constraint enforcement with auto-adjustment (Semantic: {semantic_status})"


# Integration functions for the drawing editor
def integrate_enhanced_constraints(drawing_view, scene):
    """Integrate enhanced constraint validation into the drawing view."""
    
    # Create validator and mode manager
    validator = EnhancedConstraintValidator(scene)
    mode_manager = ConstraintModeManager(validator)
    
    # Add to drawing view
    drawing_view.constraint_validator = validator
    drawing_view.constraint_mode_manager = mode_manager
    
    # Override validation method
    def enhanced_validate_final_position(item_id, scene_pos):
        """Enhanced validation with mode-specific behavior."""
        # Get original position
        original_pos = drawing_view.drag_start_scene_pos or scene_pos
        
        # Validate movement
        result = validator.validate_element_movement(item_id, scene_pos, original_pos)
        
        if not result.is_valid:
            print(f"CONSTRAINT VIOLATION: {result.message}")
            
            # Handle based on mode
            if result.suggested_position:
                # Move to suggested position (snap back or auto-adjust)
                item = drawing_view._get_item_by_id(item_id)
                if item:
                    item.setPos(result.suggested_position)
                    print(f"Moved {item_id} to suggested position: {result.suggested_position}")
            
            return False
        
        return True
    
    # Replace the validation method
    drawing_view._validate_final_position = enhanced_validate_final_position
    
    return validator, mode_manager


# Example usage and testing
if __name__ == "__main__":
    print("Enhanced Constraint Validation System")
    print("Features:")
    print("- Permissive mode: Free drag with snap-back")
    print("- Strict mode: Constraint enforcement with auto-adjustment")
    print("- Syntactic and semantic constraint validation")
    print("- Detailed feedback and suggested positions")
    print("- Integration with Phase 1 drawing editor")

