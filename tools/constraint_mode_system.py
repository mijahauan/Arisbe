#!/usr/bin/env python3
"""
Constraint Mode System for Ergasterion

This implements the proper constraint system with:
1. Syntactic constraints (always ON) - prevent malformed diagrams
2. Semantic constraints (user-controlled) - lock to reference EGI when confirmed
3. UI controls for toggling constraint modes
4. Integration with existing coordinator and interaction systems
"""

from enum import Enum
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QGroupBox
from PySide6.QtGui import QFont


class ConstraintMode(Enum):
    """Constraint modes for diagram editing."""
    SYNTACTIC_ONLY = "syntactic_only"      # Free creation/editing - only syntactic constraints
    SEMANTIC_LOCKED = "semantic_locked"    # Locked to reference EGI - both syntactic and semantic


class ConstraintManager(QObject):
    """
    Manages constraint modes and validation for Ergasterion.
    
    Handles:
    - Syntactic constraints (always active)
    - Semantic constraints (user-controlled)
    - Mode transitions
    - Validation logic
    """
    
    # Signals for constraint mode changes
    mode_changed = Signal(ConstraintMode)
    constraint_violation = Signal(str, str)  # violation_type, message
    
    def __init__(self, coordinator=None):
        super().__init__()
        self.coordinator = coordinator
        self.current_mode = ConstraintMode.SYNTACTIC_ONLY
        self.reference_egi = None
        self.has_confirmed_match = False
        
        # Constraint settings
        self.syntactic_enabled = True  # Always ON
        self.semantic_enabled = False  # User-controlled
        
        print(f"ConstraintManager initialized in {self.current_mode.value} mode")
    
    def set_mode(self, mode: ConstraintMode, force: bool = False):
        """Set the constraint mode."""
        if mode == self.current_mode and not force:
            return
        
        old_mode = self.current_mode
        
        if mode == ConstraintMode.SEMANTIC_LOCKED:
            if not self.reference_egi:
                print("Cannot enable semantic constraints: No reference EGI available")
                return False
            
            if not self.has_confirmed_match and not force:
                print("Cannot enable semantic constraints: Diagram match not confirmed")
                return False
            
            self.semantic_enabled = True
            print("Semantic constraints ENABLED - diagram locked to reference EGI")
            
        elif mode == ConstraintMode.SYNTACTIC_ONLY:
            self.semantic_enabled = False
            self.has_confirmed_match = False
            print("Semantic constraints DISABLED - free editing mode")
        
        self.current_mode = mode
        self.mode_changed.emit(mode)
        
        print(f"Constraint mode changed: {old_mode.value} → {mode.value}")
        return True
    
    def set_reference_egi(self, egi):
        """Set the reference EGI for semantic constraints."""
        self.reference_egi = egi
        print(f"Reference EGI set: {getattr(egi, 'id', 'unknown')}")
    
    def confirm_diagram_match(self):
        """User confirms that current diagram matches the reference EGI."""
        if not self.reference_egi:
            print("Cannot confirm match: No reference EGI available")
            return False
        
        self.has_confirmed_match = True
        print("Diagram match confirmed - semantic constraints can now be enabled")
        return True
    
    def clear_reference_egi(self):
        """Clear reference EGI and return to syntactic-only mode."""
        self.reference_egi = None
        self.has_confirmed_match = False
        self.set_mode(ConstraintMode.SYNTACTIC_ONLY, force=True)
        print("Reference EGI cleared - returned to syntactic-only mode")
    
    # ========== SYNTACTIC CONSTRAINT VALIDATION ==========
    
    def validate_element_position(self, element_type: str, element_id: str, new_position, size=None) -> tuple[bool, str]:
        """
        Validate element position against syntactic constraints.
        
        Returns: (is_valid, error_message)
        """
        if not self.syntactic_enabled:
            return True, ""
        
        # Check for overlaps with other elements
        overlap_result = self._check_element_overlaps(element_type, element_id, new_position, size)
        if not overlap_result[0]:
            return overlap_result
        
        # Check for cut-specific constraints
        if element_type == "cut":
            cut_result = self._check_cut_constraints(element_id, new_position, size)
            if not cut_result[0]:
                return cut_result
        
        return True, ""
    
    def _check_element_overlaps(self, element_type: str, element_id: str, position, size=None) -> tuple[bool, str]:
        """Check for overlapping elements (syntactic constraint)."""
        if not self.coordinator:
            return True, ""
        
        # Get current diagram state
        diagram_state = getattr(self.coordinator, 'diagram_state', None)
        if not diagram_state:
            return True, ""
        
        # For now, implement basic overlap detection
        # TODO: Implement proper geometric overlap detection
        
        # Check overlapping cuts (most important)
        if element_type == "cut":
            for other_cut_id, other_cut in diagram_state.cuts.items():
                if other_cut_id == element_id:
                    continue
                
                # Simple bounding box overlap check
                if self._rectangles_overlap(position, size, other_cut.position, other_cut.size):
                    return False, f"Cut would overlap with cut {other_cut_id}"
        
        return True, ""
    
    def _check_cut_constraints(self, cut_id: str, position, size) -> tuple[bool, str]:
        """Check cut-specific syntactic constraints."""
        # Cuts can be nested but not overlapping
        # This is handled in _check_element_overlaps
        return True, ""
    
    def _rectangles_overlap(self, pos1, size1, pos2, size2) -> bool:
        """Check if two rectangles overlap."""
        if not (size1 and size2):
            return False
        
        # Rectangle 1: (x1, y1) to (x1 + w1, y1 + h1)
        x1, y1 = pos1.x, pos1.y
        w1, h1 = size1.width, size1.height
        
        # Rectangle 2: (x2, y2) to (x2 + w2, y2 + h2)
        x2, y2 = pos2.x, pos2.y
        w2, h2 = size2.width, size2.height
        
        # Check for overlap
        return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)
    
    # ========== SEMANTIC CONSTRAINT VALIDATION ==========
    
    def validate_element_area_change(self, element_type: str, element_id: str, new_area_id: str) -> tuple[bool, str]:
        """
        Validate element area change against semantic constraints.
        
        Returns: (is_valid, error_message)
        """
        if not self.semantic_enabled:
            return True, ""
        
        # In semantic mode, elements cannot change areas
        if not self.coordinator:
            return True, ""
        
        diagram_state = getattr(self.coordinator, 'diagram_state', None)
        if not diagram_state:
            return True, ""
        
        # Get current area for this element
        current_area = None
        if element_type == "vertex" and element_id in diagram_state.vertices:
            current_area = diagram_state.vertices[element_id].area_id
        elif element_type == "predicate" and element_id in diagram_state.predicates:
            current_area = diagram_state.predicates[element_id].area_id
        elif element_type == "cut" and element_id in diagram_state.cuts:
            current_area = diagram_state.cuts[element_id].area_id
        
        if current_area and current_area != new_area_id:
            return False, f"Semantic constraints: {element_type} {element_id} cannot move from area {current_area} to {new_area_id}"
        
        return True, ""
    
    def validate_name_change(self, element_type: str, element_id: str, new_name: str) -> tuple[bool, str]:
        """
        Validate name change against semantic constraints.
        
        Returns: (is_valid, error_message)
        """
        if not self.semantic_enabled:
            return True, ""
        
        return False, f"Semantic constraints: Cannot change {element_type} name while locked to reference EGI"
    
    def validate_arity_change(self, predicate_id: str, new_arity: int) -> tuple[bool, str]:
        """
        Validate arity change against semantic constraints.
        
        Returns: (is_valid, error_message)
        """
        if not self.semantic_enabled:
            return True, ""
        
        return False, f"Semantic constraints: Cannot change predicate arity while locked to reference EGI"
    
    # ========== STATUS AND INFO ==========
    
    def get_constraint_status(self) -> Dict[str, Any]:
        """Get current constraint status for UI display."""
        return {
            "mode": self.current_mode.value,
            "syntactic_enabled": self.syntactic_enabled,
            "semantic_enabled": self.semantic_enabled,
            "has_reference_egi": self.reference_egi is not None,
            "match_confirmed": self.has_confirmed_match,
            "can_enable_semantic": self.reference_egi is not None and self.has_confirmed_match
        }


class ConstraintModeWidget(QWidget):
    """
    UI widget for controlling constraint modes.
    
    Provides buttons and status display for constraint management.
    """
    
    def __init__(self, constraint_manager: ConstraintManager, parent=None):
        super().__init__(parent)
        self.constraint_manager = constraint_manager
        self._setup_ui()
        self._connect_signals()
        self._update_display()
    
    def _setup_ui(self):
        """Set up the constraint mode UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Constraint Mode")
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Status display
        self.status_frame = QFrame()
        self.status_frame.setFrameStyle(QFrame.Shape.Box)
        status_layout = QVBoxLayout(self.status_frame)
        
        self.mode_label = QLabel("Mode: Syntactic Only")
        self.mode_label.setFont(QFont("Arial", 9))
        status_layout.addWidget(self.mode_label)
        
        self.constraints_label = QLabel("Constraints: Syntactic ✓")
        self.constraints_label.setFont(QFont("Arial", 8))
        status_layout.addWidget(self.constraints_label)
        
        self.egi_label = QLabel("Reference EGI: None")
        self.egi_label.setFont(QFont("Arial", 8))
        status_layout.addWidget(self.egi_label)
        
        layout.addWidget(self.status_frame)
        
        # Control buttons
        button_layout = QVBoxLayout()
        
        self.free_edit_btn = QPushButton("Free Edit Mode")
        self.free_edit_btn.setToolTip("Enable free editing with only syntactic constraints")
        button_layout.addWidget(self.free_edit_btn)
        
        self.lock_to_egi_btn = QPushButton("Lock to EGI")
        self.lock_to_egi_btn.setToolTip("Lock diagram to reference EGI (semantic constraints)")
        self.lock_to_egi_btn.setEnabled(False)
        button_layout.addWidget(self.lock_to_egi_btn)
        
        self.confirm_match_btn = QPushButton("Confirm Match")
        self.confirm_match_btn.setToolTip("Confirm that diagram matches reference EGI")
        self.confirm_match_btn.setEnabled(False)
        button_layout.addWidget(self.confirm_match_btn)
        
        layout.addLayout(button_layout)
        
        # Info text
        info_label = QLabel(
            "Syntactic: Prevents overlaps\n"
            "Semantic: Locks to reference EGI"
        )
        info_label.setFont(QFont("Arial", 7))
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)
    
    def _connect_signals(self):
        """Connect UI signals to constraint manager."""
        self.free_edit_btn.clicked.connect(
            lambda: self.constraint_manager.set_mode(ConstraintMode.SYNTACTIC_ONLY)
        )
        
        self.lock_to_egi_btn.clicked.connect(
            lambda: self.constraint_manager.set_mode(ConstraintMode.SEMANTIC_LOCKED)
        )
        
        self.confirm_match_btn.clicked.connect(
            self.constraint_manager.confirm_diagram_match
        )
        
        # Listen for constraint manager changes
        self.constraint_manager.mode_changed.connect(self._update_display)
    
    def _update_display(self):
        """Update the display based on current constraint status."""
        status = self.constraint_manager.get_constraint_status()
        
        # Update mode label
        mode_text = "Free Edit" if status["mode"] == "syntactic_only" else "Locked to EGI"
        self.mode_label.setText(f"Mode: {mode_text}")
        
        # Update constraints label
        constraints = []
        if status["syntactic_enabled"]:
            constraints.append("Syntactic ✓")
        if status["semantic_enabled"]:
            constraints.append("Semantic ✓")
        self.constraints_label.setText(f"Constraints: {', '.join(constraints)}")
        
        # Update EGI label
        egi_text = "Available" if status["has_reference_egi"] else "None"
        if status["match_confirmed"]:
            egi_text += " (Confirmed)"
        self.egi_label.setText(f"Reference EGI: {egi_text}")
        
        # Update button states
        self.free_edit_btn.setEnabled(status["mode"] != "syntactic_only")
        self.lock_to_egi_btn.setEnabled(status["can_enable_semantic"] and status["mode"] != "semantic_locked")
        self.confirm_match_btn.setEnabled(status["has_reference_egi"] and not status["match_confirmed"])
        
        # Update button styles
        if status["mode"] == "syntactic_only":
            self.free_edit_btn.setStyleSheet("background-color: #4CAF50; color: white;")
            self.lock_to_egi_btn.setStyleSheet("")
        else:
            self.free_edit_btn.setStyleSheet("")
            self.lock_to_egi_btn.setStyleSheet("background-color: #FF9800; color: white;")
    
    def set_reference_egi(self, egi):
        """Set reference EGI and update display."""
        self.constraint_manager.set_reference_egi(egi)
        self._update_display()
    
    def clear_reference_egi(self):
        """Clear reference EGI and update display."""
        self.constraint_manager.clear_reference_egi()
        self._update_display()


# ========== INTEGRATION HELPERS ==========

def integrate_constraint_system(drawing_editor, coordinator):
    """
    Integrate the constraint system into the existing drawing editor.
    
    Args:
        drawing_editor: RefactoredDrawingEditor instance
        coordinator: DiagramCoordinator instance
    
    Returns:
        ConstraintManager instance
    """
    # Create constraint manager
    constraint_manager = ConstraintManager(coordinator)
    
    # Create constraint mode widget
    constraint_widget = ConstraintModeWidget(constraint_manager)
    
    # Add to drawing editor as dock widget
    from PySide6.QtWidgets import QDockWidget
    from PySide6.QtCore import Qt
    
    constraint_dock = QDockWidget("Constraints", drawing_editor)
    constraint_dock.setWidget(constraint_widget)
    drawing_editor.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, constraint_dock)
    
    # Store references
    drawing_editor.constraint_manager = constraint_manager
    drawing_editor.constraint_widget = constraint_widget
    
    print("Constraint system integrated into drawing editor")
    return constraint_manager


if __name__ == "__main__":
    print("Constraint Mode System Implementation")
    print("=====================================")
    print()
    print("Features:")
    print("- Syntactic constraints (always ON): Prevent overlaps, malformed diagrams")
    print("- Semantic constraints (user-controlled): Lock to reference EGI")
    print("- UI controls for mode switching")
    print("- Integration with existing coordinator system")
    print()
    print("Usage:")
    print("1. Import and integrate into RefactoredDrawingEditor")
    print("2. Use constraint_manager.validate_* methods for validation")
    print("3. UI automatically updates based on constraint state")

