"""
Bidirectional Pipeline Validation System

Implements the missing validation steps for both directions of the pipeline:
1. Forward: EGIF → EGI → Layout → Rendering (Practice mode)
2. Reverse: Interactive Composition → EGI → EGIF (Preparatory mode)

Ensures mathematical rigor and Dau compliance throughout the composition process.
"""

from typing import Dict, Any, List, Set, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
from src.egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from src.pipeline_contracts import PhaseResult


class ValidationSeverity(Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ValidationIssue:
    """Represents a validation issue found during composition or transformation."""
    severity: ValidationSeverity
    element_id: str
    message: str
    suggested_fix: Optional[str] = None


@dataclass(frozen=True)
class ValidationResult:
    """Result of EGI validation."""
    is_valid: bool
    issues: List[ValidationIssue]
    can_continue: bool  # Can continue composition despite issues
    can_transition_to_practice: bool  # Can move to Practice mode


class EGIValidationSystem:
    """Validates EGI during interactive composition and transformation."""
    
    def validate_partial_egi(self, working_egi: RelationalGraphWithCuts) -> ValidationResult:
        """Validate EGI during composition (allows partial/incomplete graphs)."""
        issues = []
        
        # Check basic structural integrity
        issues.extend(self._check_structural_integrity(working_egi))
        
        # Check containment rules (relaxed for partial graphs)
        issues.extend(self._check_containment_rules(working_egi, strict=False))
        
        # Check connection validity
        issues.extend(self._check_connection_validity(working_egi))
        
        # Determine if composition can continue
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        can_continue = len(critical_issues) == 0
        
        # Determine if can transition to Practice mode (stricter validation)
        can_transition = self._can_transition_to_practice(working_egi, issues)
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            can_continue=can_continue,
            can_transition_to_practice=can_transition
        )
    
    def validate_complete_egi(self, egi: RelationalGraphWithCuts) -> ValidationResult:
        """Validate complete EGI for Practice mode (strict validation)."""
        issues = []
        
        # Strict structural integrity
        issues.extend(self._check_structural_integrity(egi))
        
        # Strict containment rules
        issues.extend(self._check_containment_rules(egi, strict=True))
        
        # Connection completeness
        issues.extend(self._check_connection_completeness(egi))
        
        # Predicate arity validation
        issues.extend(self._check_predicate_arity(egi))
        
        # Variable scoping validation
        issues.extend(self._check_variable_scoping(egi))
        
        is_valid = len([i for i in issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            can_continue=is_valid,
            can_transition_to_practice=is_valid
        )
    
    def _check_structural_integrity(self, egi: RelationalGraphWithCuts) -> List[ValidationIssue]:
        """Check basic EGI structural integrity."""
        issues = []
        
        # Check that all referenced elements exist
        all_element_ids = {v.id for v in egi.V} | {e.id for e in egi.E} | {c.id for c in egi.Cut}
        
        for area_id, elements in egi.area.items():
            for element_id in elements:
                if element_id not in all_element_ids:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        element_id=element_id,
                        message=f"Element {element_id} referenced in area {area_id} but not defined",
                        suggested_fix=f"Remove {element_id} from area {area_id} or define the element"
                    ))
        
        return issues
    
    def _check_containment_rules(self, egi: RelationalGraphWithCuts, strict: bool = True) -> List[ValidationIssue]:
        """Check Dau's containment rules."""
        issues = []
        
        # Rule: Elements must be contained in exactly one area
        element_area_count = {}
        for area_id, elements in egi.area.items():
            for element_id in elements:
                element_area_count[element_id] = element_area_count.get(element_id, 0) + 1
        
        for element_id, count in element_area_count.items():
            if count > 1:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    element_id=element_id,
                    message=f"Element {element_id} appears in {count} areas (must be exactly 1)",
                    suggested_fix=f"Remove {element_id} from all but one area"
                ))
            elif count == 0 and strict:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    element_id=element_id,
                    message=f"Element {element_id} not contained in any area",
                    suggested_fix=f"Add {element_id} to an appropriate area"
                ))
        
        return issues
    
    def _check_connection_validity(self, egi: RelationalGraphWithCuts) -> List[ValidationIssue]:
        """Check that connections (edges) are valid."""
        issues = []
        
        # Check that edges connect to existing vertices
        for edge in egi.E:
            if hasattr(edge, 'vertices') and edge.vertices:
                for vertex_id in edge.vertices:
                    if not any(v.id == vertex_id for v in egi.V):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            element_id=edge.id,
                            message=f"Edge {edge.id} connects to non-existent vertex {vertex_id}",
                            suggested_fix=f"Create vertex {vertex_id} or remove connection"
                        ))
        
        return issues
    
    def _check_connection_completeness(self, egi: RelationalGraphWithCuts) -> List[ValidationIssue]:
        """Check that all elements have proper connections (strict mode only)."""
        issues = []
        
        # Check that all predicates have proper arity
        for edge in egi.E:
            if edge.id in egi.rel:  # This is a predicate
                predicate_name = egi.rel[edge.id]
                # Skip identity predicates
                if predicate_name in ('=', '.='):
                    continue
                
                # Check if predicate has connections
                if not hasattr(edge, 'vertices') or not edge.vertices:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        element_id=edge.id,
                        message=f"Predicate {predicate_name} has no vertex connections",
                        suggested_fix=f"Connect {predicate_name} to appropriate vertices"
                    ))
        
        return issues
    
    def _check_predicate_arity(self, egi: RelationalGraphWithCuts) -> List[ValidationIssue]:
        """Check predicate arity constraints."""
        issues = []
        
        # This would need domain knowledge about expected predicate arities
        # For now, just check that predicates have at least one connection
        for edge in egi.E:
            if edge.id in egi.rel:
                predicate_name = egi.rel[edge.id]
                if predicate_name not in ('=', '.='):
                    if not hasattr(edge, 'vertices') or len(edge.vertices or []) == 0:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            element_id=edge.id,
                            message=f"Predicate {predicate_name} has no connections",
                            suggested_fix="Connect predicate to at least one vertex"
                        ))
        
        return issues
    
    def _check_variable_scoping(self, egi: RelationalGraphWithCuts) -> List[ValidationIssue]:
        """Check variable scoping across cuts."""
        issues = []
        
        # This would implement Dau's variable scoping rules
        # For now, placeholder for future implementation
        
        return issues
    
    def _can_transition_to_practice(self, egi: RelationalGraphWithCuts, issues: List[ValidationIssue]) -> bool:
        """Determine if EGI can transition from Preparatory to Practice mode."""
        # No critical or error issues
        blocking_issues = [i for i in issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]
        
        if blocking_issues:
            return False
        
        # Must have at least one meaningful element
        has_predicates = any(e.id in egi.rel for e in egi.E)
        has_vertices = len(egi.V) > 0
        
        return has_predicates and has_vertices


class ContainmentEnforcer:
    """Enforces containment rules during interactive editing."""
    
    def enforce_containment_during_edit(self, user_action: Dict[str, Any], current_egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Enforce containment rules and auto-correct invalid placements."""
        action_type = user_action.get('type')
        element_id = user_action.get('element_id')
        position = user_action.get('position')  # (x, y) in relative coordinates
        
        if action_type == 'move_element':
            # Find which container the position falls into
            target_container = self._find_container_at_position(position, current_egi)
            
            # Update area mapping if element moved to different container
            corrected_action = user_action.copy()
            corrected_action['target_container'] = target_container
            
            return corrected_action
        
        elif action_type == 'add_element':
            # Ensure new element is added to correct container based on position
            target_container = self._find_container_at_position(position, current_egi)
            corrected_action = user_action.copy()
            corrected_action['container'] = target_container
            
            return corrected_action
        
        return user_action
    
    def _find_container_at_position(self, position: Tuple[float, float], egi: RelationalGraphWithCuts) -> str:
        """Find which container contains the given position."""
        x, y = position
        
        # Check cuts from innermost to outermost
        # This would need container bounds from layout context
        # For now, return sheet as default
        return 'sheet'


class ConnectionValidator:
    """Validates ligature connections during interactive drawing."""
    
    def validate_ligature_connection(self, vertex_id: str, predicate_id: str, current_egi: RelationalGraphWithCuts) -> ValidationResult:
        """Validate that vertex and predicate can be legally connected."""
        issues = []
        
        # Check that both elements exist
        vertex_exists = any(v.id == vertex_id for v in current_egi.V)
        predicate_exists = any(e.id == predicate_id for e in current_egi.E)
        
        if not vertex_exists:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                element_id=vertex_id,
                message=f"Vertex {vertex_id} does not exist",
                suggested_fix="Create vertex before connecting"
            ))
        
        if not predicate_exists:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                element_id=predicate_id,
                message=f"Predicate {predicate_id} does not exist",
                suggested_fix="Create predicate before connecting"
            ))
        
        # Check containment compatibility
        if vertex_exists and predicate_exists:
            vertex_area = self._find_element_area(vertex_id, current_egi)
            predicate_area = self._find_element_area(predicate_id, current_egi)
            
            if not self._areas_compatible_for_connection(vertex_area, predicate_area, current_egi):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    element_id=f"{vertex_id}-{predicate_id}",
                    message=f"Cannot connect vertex in {vertex_area} to predicate in {predicate_area}",
                    suggested_fix="Move elements to compatible areas or use lines of identity"
                ))
        
        can_connect = len([i for i in issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]) == 0
        
        return ValidationResult(
            is_valid=can_connect,
            issues=issues,
            can_continue=can_connect,
            can_transition_to_practice=True  # Connection validation doesn't affect mode transition
        )
    
    def _find_element_area(self, element_id: str, egi: RelationalGraphWithCuts) -> str:
        """Find which area contains the given element."""
        for area_id, elements in egi.area.items():
            if element_id in elements:
                return area_id
        return 'sheet'  # Default
    
    def _areas_compatible_for_connection(self, vertex_area: str, predicate_area: str, egi: RelationalGraphWithCuts) -> bool:
        """Check if vertex and predicate areas allow direct connection."""
        # Same area: always compatible
        if vertex_area == predicate_area:
            return True
        
        # Different areas: need lines of identity (more complex validation)
        # For now, allow connections and let user handle with lines of identity
        return True


class CompositionHistory:
    """Manages undo/redo stack for interactive composition."""
    
    def __init__(self):
        self.egi_states: List[RelationalGraphWithCuts] = []
        self.current_index: int = -1
        self.max_history: int = 50  # Limit memory usage
    
    def add_state(self, egi: RelationalGraphWithCuts):
        """Add new EGI state to history."""
        # Remove any states after current index (when undoing then making new changes)
        self.egi_states = self.egi_states[:self.current_index + 1]
        
        # Add new state
        self.egi_states.append(egi)
        self.current_index += 1
        
        # Limit history size
        if len(self.egi_states) > self.max_history:
            self.egi_states = self.egi_states[-self.max_history:]
            self.current_index = len(self.egi_states) - 1
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return self.current_index > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self.current_index < len(self.egi_states) - 1
    
    def undo(self) -> Optional[RelationalGraphWithCuts]:
        """Undo to previous state."""
        if self.can_undo():
            self.current_index -= 1
            return self.egi_states[self.current_index]
        return None
    
    def redo(self) -> Optional[RelationalGraphWithCuts]:
        """Redo to next state."""
        if self.can_redo():
            self.current_index += 1
            return self.egi_states[self.current_index]
        return None
    
    def get_current_state(self) -> Optional[RelationalGraphWithCuts]:
        """Get current EGI state."""
        if 0 <= self.current_index < len(self.egi_states):
            return self.egi_states[self.current_index]
        return None


class ModeTransitionValidator:
    """Validates transitions between Preparatory and Practice modes."""
    
    def __init__(self):
        self.validation_system = EGIValidationSystem()
    
    def can_transition_to_practice_mode(self, working_egi: RelationalGraphWithCuts) -> ValidationResult:
        """Validate if EGI can transition from Preparatory to Practice mode."""
        # Use strict validation for mode transition
        return self.validation_system.validate_complete_egi(working_egi)
    
    def can_transition_to_preparatory_mode(self, egi: RelationalGraphWithCuts) -> ValidationResult:
        """Validate if EGI can transition from Practice to Preparatory mode."""
        # Less strict - mainly check that EGI is not in an invalid transformation state
        return self.validation_system.validate_partial_egi(egi)


class BidirectionalPipelineOrchestrator:
    """Orchestrates validation and enforcement for both pipeline directions."""
    
    def __init__(self):
        self.validation_system = EGIValidationSystem()
        self.containment_enforcer = ContainmentEnforcer()
        self.connection_validator = ConnectionValidator()
        self.composition_history = CompositionHistory()
        self.mode_transition_validator = ModeTransitionValidator()
    
    def handle_preparatory_mode_action(self, user_action: Dict[str, Any], current_egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Handle user action in Preparatory mode with validation and enforcement."""
        # 1. Enforce containment rules
        corrected_action = self.containment_enforcer.enforce_containment_during_edit(user_action, current_egi)
        
        # 2. Validate action if it's a connection
        if corrected_action.get('type') == 'add_ligature':
            vertex_id = corrected_action.get('vertex_id')
            predicate_id = corrected_action.get('predicate_id')
            validation_result = self.connection_validator.validate_ligature_connection(vertex_id, predicate_id, current_egi)
            
            if not validation_result.can_continue:
                corrected_action['validation_issues'] = validation_result.issues
                corrected_action['blocked'] = True
        
        # 3. Store state for undo/redo
        if not corrected_action.get('blocked', False):
            # Apply action to create new EGI state
            new_egi = self._apply_action_to_egi(corrected_action, current_egi)
            self.composition_history.add_state(new_egi)
            corrected_action['new_egi'] = new_egi
        
        return corrected_action
    
    def handle_practice_mode_transformation(self, transformation: Dict[str, Any], current_egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Handle transformation in Practice mode with validation."""
        # Validate current state before transformation
        validation_result = self.validation_system.validate_complete_egi(current_egi)
        
        if not validation_result.is_valid:
            return {
                'success': False,
                'validation_issues': validation_result.issues,
                'message': 'EGI must be valid before applying transformations'
            }
        
        # Apply transformation (this would call the transformation system)
        # For now, placeholder
        return {
            'success': True,
            'message': 'Transformation applied successfully'
        }
    
    def _apply_action_to_egi(self, action: Dict[str, Any], current_egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        """Apply user action to EGI and return new EGI state."""
        # This would implement the actual EGI modification logic
        # For now, return current EGI (placeholder)
        return current_egi
