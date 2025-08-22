#!/usr/bin/env python3
"""
Ergasterion Constraint Integration - Dynamic EGI Adjustment for Composition Mode

This module provides the bidirectional EGI-EGDF synchronization needed for
interactive composition in Ergasterion, where spatial edits can modify the
underlying logical graph structure.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.spatial_constraint_system import SpatialConstraintSystem, ConstraintViolation
from src.egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from src.layout_types import Coordinate, Bounds

class CompositionMode(Enum):
    """Composition modes for Ergasterion."""
    WARMUP = "warmup"      # Free composition, EGI adjusts to spatial changes
    STRICT = "strict"      # Spatial changes must respect existing EGI
    GUIDED = "guided"      # Spatial changes suggest EGI modifications

class SpatialEdit:
    """Represents a spatial edit operation."""
    def __init__(self, element_id: str, edit_type: str, old_value: Any, new_value: Any):
        self.element_id = element_id
        self.edit_type = edit_type  # 'move', 'resize', 'create', 'delete'
        self.old_value = old_value
        self.new_value = new_value
        self.timestamp = self._get_timestamp()
    
    def _get_timestamp(self) -> float:
        import time
        return time.time()

class EGIModification:
    """Represents a modification to the EGI structure."""
    def __init__(self, modification_type: str, element_data: Dict[str, Any]):
        self.modification_type = modification_type  # 'add_vertex', 'move_vertex_to_cut', etc.
        self.element_data = element_data
        self.timestamp = self._get_timestamp()
    
    def _get_timestamp(self) -> float:
        import time
        return time.time()

class ErgasterionConstraintIntegration:
    """
    Manages bidirectional synchronization between spatial edits and EGI structure
    for interactive composition in Ergasterion.
    """
    
    def __init__(self):
        self.constraint_system = SpatialConstraintSystem()
        self.composition_mode = CompositionMode.WARMUP
        self.edit_history: List[SpatialEdit] = []
        self.egi_modifications: List[EGIModification] = []
        self.current_egi: Optional[RelationalGraphWithCuts] = None
        
    def set_composition_mode(self, mode: CompositionMode):
        """Set the composition mode for handling spatial-logical interactions."""
        self.composition_mode = mode
        
    def set_egi(self, egi: RelationalGraphWithCuts):
        """Set the current EGI and initialize constraints."""
        self.current_egi = egi
        self.constraint_system.set_egi_reference(egi)
        
    def handle_spatial_edit(self, edit: SpatialEdit, current_layout: Dict[str, Any]) -> Tuple[Dict[str, Any], List[EGIModification]]:
        """
        Handle a spatial edit and return updated layout + EGI modifications.
        
        Returns:
            - Updated layout data
            - List of EGI modifications to apply
        """
        self.edit_history.append(edit)
        
        if self.composition_mode == CompositionMode.WARMUP:
            return self._handle_warmup_edit(edit, current_layout)
        elif self.composition_mode == CompositionMode.STRICT:
            return self._handle_strict_edit(edit, current_layout)
        elif self.composition_mode == CompositionMode.GUIDED:
            return self._handle_guided_edit(edit, current_layout)
        
        return current_layout, []
    
    def _handle_warmup_edit(self, edit: SpatialEdit, layout: Dict[str, Any]) -> Tuple[Dict[str, Any], List[EGIModification]]:
        """
        Handle edit in warmup mode - EGI adjusts to spatial changes.
        
        In warmup mode, spatial freedom is prioritized and the EGI structure
        is modified to match the spatial arrangement.
        """
        updated_layout = layout.copy()
        egi_modifications = []
        
        if edit.edit_type == 'move':
            # Apply the move
            if edit.element_id.startswith('v_'):  # Vertex move
                updated_layout.setdefault('vertex_positions', {})[edit.element_id] = edit.new_value
                
                # Check if vertex moved into a different cut area
                new_containing_cuts = self._find_cuts_containing_position(edit.new_value, layout)
                old_containing_cuts = self._get_vertex_containing_cuts(edit.element_id)
                
                if new_containing_cuts != old_containing_cuts:
                    # Generate EGI modification to update vertex containment
                    egi_modifications.append(EGIModification(
                        'update_vertex_containment',
                        {
                            'vertex_id': edit.element_id,
                            'old_cuts': old_containing_cuts,
                            'new_cuts': new_containing_cuts
                        }
                    ))
                    
            elif edit.element_id.startswith('c_'):  # Cut move/resize
                updated_layout.setdefault('cut_bounds', {})[edit.element_id] = edit.new_value
                
                # Check if cut resize affects vertex containment
                affected_vertices = self._find_vertices_affected_by_cut_change(edit.element_id, edit.old_value, edit.new_value, layout)
                for vertex_id in affected_vertices:
                    egi_modifications.append(EGIModification(
                        'update_vertex_containment_from_cut_change',
                        {
                            'vertex_id': vertex_id,
                            'cut_id': edit.element_id,
                            'cut_change': 'resize'
                        }
                    ))
        
        elif edit.edit_type == 'create':
            # Handle creation of new elements
            if edit.new_value.get('element_type') == 'vertex':
                # Add vertex to layout
                vertex_id = edit.element_id
                position = edit.new_value['position']
                updated_layout.setdefault('vertex_positions', {})[vertex_id] = position
                
                # Generate EGI modification to add vertex
                containing_cuts = self._find_cuts_containing_position(position, layout)
                egi_modifications.append(EGIModification(
                    'add_vertex',
                    {
                        'vertex_id': vertex_id,
                        'position': position,
                        'containing_cuts': containing_cuts,
                        'label': edit.new_value.get('label', '')
                    }
                ))
                
        elif edit.edit_type == 'delete':
            # Handle deletion
            if edit.element_id.startswith('v_'):
                # Remove vertex from layout
                updated_layout.get('vertex_positions', {}).pop(edit.element_id, None)
                
                # Generate EGI modification to remove vertex
                egi_modifications.append(EGIModification(
                    'remove_vertex',
                    {'vertex_id': edit.element_id}
                ))
        
        return updated_layout, egi_modifications
    
    def _handle_strict_edit(self, edit: SpatialEdit, layout: Dict[str, Any]) -> Tuple[Dict[str, Any], List[EGIModification]]:
        """
        Handle edit in strict mode - spatial changes must respect EGI.
        
        In strict mode, spatial edits are constrained to maintain EGI validity.
        """
        # Validate edit against constraints
        test_layout = layout.copy()
        
        if edit.edit_type == 'move':
            if edit.element_id.startswith('v_'):
                test_layout.setdefault('vertex_positions', {})[edit.element_id] = edit.new_value
            elif edit.element_id.startswith('c_'):
                test_layout.setdefault('cut_bounds', {})[edit.element_id] = edit.new_value
        
        # Check for constraint violations
        violations = self.constraint_system.validate_layout(test_layout)
        
        if violations:
            # Apply constraint fixes to make edit valid
            fixed_layout = self.constraint_system.apply_constraint_fixes(violations, test_layout)
            return fixed_layout, []  # No EGI modifications in strict mode
        else:
            return test_layout, []
    
    def _handle_guided_edit(self, edit: SpatialEdit, layout: Dict[str, Any]) -> Tuple[Dict[str, Any], List[EGIModification]]:
        """
        Handle edit in guided mode - suggest EGI modifications for spatial changes.
        
        In guided mode, spatial edits are allowed but EGI modifications are suggested
        rather than automatically applied.
        """
        # Similar to warmup but modifications are marked as suggestions
        updated_layout, modifications = self._handle_warmup_edit(edit, layout)
        
        # Mark modifications as suggestions
        for mod in modifications:
            mod.element_data['suggestion'] = True
            mod.element_data['confidence'] = self._calculate_modification_confidence(mod)
        
        return updated_layout, modifications
    
    def _find_cuts_containing_position(self, position: Coordinate, layout: Dict[str, Any]) -> List[str]:
        """Find all cuts that contain the given position."""
        containing_cuts = []
        x, y = position
        
        for cut_id, bounds in layout.get('cut_bounds', {}).items():
            x1, y1, x2, y2 = bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                containing_cuts.append(cut_id)
        
        return containing_cuts
    
    def _get_vertex_containing_cuts(self, vertex_id: str) -> List[str]:
        """Get cuts that currently contain the vertex according to EGI."""
        # This would query the current EGI structure
        # Placeholder implementation
        return []
    
    def _find_vertices_affected_by_cut_change(self, cut_id: str, old_bounds: Bounds, 
                                            new_bounds: Bounds, layout: Dict[str, Any]) -> List[str]:
        """Find vertices whose containment is affected by cut boundary change."""
        affected_vertices = []
        
        for vertex_id, position in layout.get('vertex_positions', {}).items():
            x, y = position
            
            # Check if vertex containment status changed
            old_contained = (old_bounds[0] <= x <= old_bounds[2] and old_bounds[1] <= y <= old_bounds[3])
            new_contained = (new_bounds[0] <= x <= new_bounds[2] and new_bounds[1] <= y <= new_bounds[3])
            
            if old_contained != new_contained:
                affected_vertices.append(vertex_id)
        
        return affected_vertices
    
    def _calculate_modification_confidence(self, modification: EGIModification) -> float:
        """Calculate confidence score for a suggested EGI modification."""
        # This would implement heuristics for modification confidence
        # Based on factors like spatial clarity, logical consistency, etc.
        return 0.8  # Placeholder
    
    def apply_egi_modifications(self, modifications: List[EGIModification]) -> RelationalGraphWithCuts:
        """Apply EGI modifications and return updated EGI."""
        if not self.current_egi:
            return None
        
        updated_egi = self.current_egi  # Would implement deep copy and modifications
        
        for mod in modifications:
            updated_egi = self._apply_single_modification(updated_egi, mod)
            self.egi_modifications.append(mod)
        
        return updated_egi
    
    def _apply_single_modification(self, egi: RelationalGraphWithCuts, 
                                 modification: EGIModification) -> RelationalGraphWithCuts:
        """Apply a single EGI modification."""
        # This would implement the actual EGI structure modifications
        # For now, return unchanged
        return egi
    
    def get_constraint_violations_for_layout(self, layout: Dict[str, Any]) -> List[ConstraintViolation]:
        """Get all constraint violations for a given layout."""
        return self.constraint_system.validate_layout(layout)
    
    def suggest_constraint_fixes(self, violations: List[ConstraintViolation], 
                               layout: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest fixes for constraint violations."""
        return self.constraint_system.apply_constraint_fixes(violations, layout)
    
    def get_edit_history(self) -> List[SpatialEdit]:
        """Get the history of spatial edits."""
        return self.edit_history.copy()
    
    def get_egi_modification_history(self) -> List[EGIModification]:
        """Get the history of EGI modifications."""
        return self.egi_modifications.copy()
    
    def undo_last_edit(self, current_layout: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[RelationalGraphWithCuts]]:
        """Undo the last spatial edit and associated EGI modifications."""
        if not self.edit_history:
            return current_layout, self.current_egi
        
        last_edit = self.edit_history.pop()
        
        # Revert the spatial change
        reverted_layout = current_layout.copy()
        
        if last_edit.edit_type == 'move':
            if last_edit.element_id.startswith('v_'):
                reverted_layout.setdefault('vertex_positions', {})[last_edit.element_id] = last_edit.old_value
            elif last_edit.element_id.startswith('c_'):
                reverted_layout.setdefault('cut_bounds', {})[last_edit.element_id] = last_edit.old_value
        
        # Revert associated EGI modifications
        # This would require more sophisticated EGI history tracking
        
        return reverted_layout, self.current_egi
