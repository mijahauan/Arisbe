#!/usr/bin/env python3
"""
Background Validation System for Existential Graphs

Provides real-time validation and transformation suggestions that integrate
with the Phase 2 selection and action systems. Ensures all operations
maintain syntactic validity and provides intelligent feedback.
"""

from typing import Set, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import time

from egi_core_dau import RelationalGraphWithCuts, ElementID
from eg_transformation_rules import (
    EGTransformationEngine, BackgroundValidator, TransformationRule,
    TransformationResult, ValidationResult
)


class ValidationLevel(Enum):
    """Levels of validation strictness."""
    PERMISSIVE = "permissive"    # Allow most operations
    STANDARD = "standard"        # Standard EG rules
    STRICT = "strict"           # Strict mathematical rigor


@dataclass
class ValidationFeedback:
    """Real-time validation feedback for user actions."""
    is_valid: bool
    level: ValidationLevel
    message: str
    suggestions: List[str]
    available_transformations: List[Dict]
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class RealTimeValidator:
    """
    Real-time validation system that provides immediate feedback
    as users interact with the EG diagram.
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level
        self.transformation_engine = EGTransformationEngine()
        self.background_validator = BackgroundValidator(self.transformation_engine)
        
        # Callbacks for real-time feedback
        self.validation_callbacks: List[Callable[[ValidationFeedback], None]] = []
        
        # Cache for performance
        self.validation_cache = {}
        self.cache_timeout = 1.0  # seconds
        
    def add_validation_callback(self, callback: Callable[[ValidationFeedback], None]):
        """Add callback for validation feedback updates."""
        self.validation_callbacks.append(callback)
    
    def validate_action(self, graph: RelationalGraphWithCuts,
                       action_type: str,
                       selection: Set[ElementID],
                       **action_params) -> ValidationFeedback:
        """Validate a proposed user action in real-time."""
        
        # Create cache key
        cache_key = self._create_cache_key(graph, action_type, selection, action_params)
        
        # Check cache
        if cache_key in self.validation_cache:
            cached_result, timestamp = self.validation_cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                return cached_result
        
        # Perform validation
        feedback = self._perform_action_validation(graph, action_type, selection, action_params)
        
        # Cache result
        self.validation_cache[cache_key] = (feedback, time.time())
        
        # Notify callbacks
        for callback in self.validation_callbacks:
            try:
                callback(feedback)
            except Exception as e:
                print(f"Validation callback error: {e}")
        
        return feedback
    
    def _perform_action_validation(self, graph: RelationalGraphWithCuts,
                                  action_type: str,
                                  selection: Set[ElementID],
                                  action_params: Dict) -> ValidationFeedback:
        """Perform the actual validation logic."""
        
        suggestions = []
        warnings = []
        available_transformations = []
        
        # Validate based on action type
        if action_type == "insert_cut":
            return self._validate_cut_insertion(graph, selection, action_params)
        
        elif action_type == "insert_predicate":
            return self._validate_predicate_insertion(graph, selection, action_params)
        
        elif action_type == "insert_loi":
            return self._validate_loi_insertion(graph, selection, action_params)
        
        elif action_type == "delete":
            return self._validate_deletion(graph, selection, action_params)
        
        elif action_type == "move":
            return self._validate_movement(graph, selection, action_params)
        
        elif action_type == "edit_predicate":
            return self._validate_predicate_edit(graph, selection, action_params)
        
        elif action_type == "apply_transformation":
            return self._validate_transformation_application(graph, selection, action_params)
        
        else:
            return ValidationFeedback(
                is_valid=False,
                level=self.validation_level,
                message=f"Unknown action type: {action_type}",
                suggestions=[],
                available_transformations=[]
            )
    
    def _validate_cut_insertion(self, graph: RelationalGraphWithCuts,
                               selection: Set[ElementID],
                               params: Dict) -> ValidationFeedback:
        """Validate cut insertion action."""
        
        target_area = params.get('target_area')
        enclosed_elements = params.get('enclosed_elements', set())
        
        # Use transformation engine to validate
        validation = self.transformation_engine.validate_transformation(
            graph, TransformationRule.CUT_INSERT,
            target_area=target_area,
            enclosed_elements=enclosed_elements
        )
        
        suggestions = []
        if validation.is_valid:
            suggestions.append("Cut insertion will create proper negation boundary")
            if not enclosed_elements:
                suggestions.append("Empty cut represents contradiction (⊥)")
            else:
                suggestions.append(f"Cut will negate {len(enclosed_elements)} enclosed elements")
        
        # Check for double cut opportunities
        available_transformations = self._get_contextual_transformations(graph, selection)
        
        return ValidationFeedback(
            is_valid=validation.is_valid,
            level=self.validation_level,
            message=validation.description,
            suggestions=suggestions,
            available_transformations=available_transformations
        )
    
    def _validate_predicate_insertion(self, graph: RelationalGraphWithCuts,
                                     selection: Set[ElementID],
                                     params: Dict) -> ValidationFeedback:
        """Validate predicate insertion action."""
        
        target_area = params.get('target_area')
        predicate_name = params.get('predicate_name', 'NewPredicate')
        arity = params.get('arity', 1)
        
        suggestions = []
        warnings = []
        
        # Check if predicate name already exists
        existing_predicates = set(graph.rel.values())
        if predicate_name in existing_predicates:
            warnings.append(f"Predicate '{predicate_name}' already exists in graph")
        
        # Validate arity
        if arity < 1:
            return ValidationFeedback(
                is_valid=False,
                level=self.validation_level,
                message="Predicate arity must be at least 1",
                suggestions=["Use arity ≥ 1 for valid predicates"],
                available_transformations=[]
            )
        
        suggestions.append(f"Will create {arity}-ary predicate '{predicate_name}'")
        suggestions.append(f"Will generate {arity} new vertices for arguments")
        
        if arity > 3:
            warnings.append("High arity predicates may be difficult to visualize clearly")
        
        return ValidationFeedback(
            is_valid=True,
            level=self.validation_level,
            message=f"Predicate insertion is valid",
            suggestions=suggestions,
            available_transformations=self._get_contextual_transformations(graph, selection),
            warnings=warnings
        )
    
    def _validate_loi_insertion(self, graph: RelationalGraphWithCuts,
                               selection: Set[ElementID],
                               params: Dict) -> ValidationFeedback:
        """Validate Line of Identity insertion action."""
        
        target_area = params.get('target_area')
        
        suggestions = [
            "Line of Identity represents an individual (extant thing)",
            "Can be connected to predicates via hooks",
            "Can branch to show identity relationships"
        ]
        
        return ValidationFeedback(
            is_valid=True,
            level=self.validation_level,
            message="Line of Identity insertion is valid",
            suggestions=suggestions,
            available_transformations=self._get_contextual_transformations(graph, selection)
        )
    
    def _validate_deletion(self, graph: RelationalGraphWithCuts,
                          selection: Set[ElementID],
                          params: Dict) -> ValidationFeedback:
        """Validate deletion action using Erasure rule."""
        
        if not selection:
            return ValidationFeedback(
                is_valid=False,
                level=self.validation_level,
                message="No elements selected for deletion",
                suggestions=["Select elements to delete"],
                available_transformations=[]
            )
        
        # Use transformation engine to validate erasure
        validation = self.transformation_engine.validate_transformation(
            graph, TransformationRule.ERASURE,
            elements_to_erase=selection
        )
        
        suggestions = []
        warnings = []
        
        if validation.is_valid:
            suggestions.append(f"Will erase {len(selection)} elements")
            
            # Check for orphaned elements
            edges_to_delete = selection & graph.E
            for edge_id in edges_to_delete:
                if edge_id in graph.nu:
                    vertex_ids = graph.nu[edge_id]
                    for vertex_id in vertex_ids:
                        # Check if vertex will become orphaned
                        connected_edges = [eid for eid, vids in graph.nu.items() 
                                         if vertex_id in vids and eid not in selection]
                        if not connected_edges:
                            warnings.append(f"Vertex {vertex_id[-8:]} will become orphaned")
        
        return ValidationFeedback(
            is_valid=validation.is_valid,
            level=self.validation_level,
            message=validation.description,
            suggestions=suggestions,
            available_transformations=self._get_contextual_transformations(graph, selection),
            warnings=warnings
        )
    
    def _validate_movement(self, graph: RelationalGraphWithCuts,
                          selection: Set[ElementID],
                          params: Dict) -> ValidationFeedback:
        """Validate movement action (appearance-only)."""
        
        if not selection:
            return ValidationFeedback(
                is_valid=False,
                level=self.validation_level,
                message="No elements selected for movement",
                suggestions=["Select elements to move"],
                available_transformations=[]
            )
        
        suggestions = [
            "Movement is appearance-only (preserves logical structure)",
            "Spatial positioning does not affect logical meaning",
            "Ensure visual clarity after movement"
        ]
        
        # Check for potential area boundary violations
        warnings = []
        target_area = params.get('target_area')
        if target_area:
            for element_id in selection:
                current_area = self._find_element_area(graph, element_id)
                if current_area != target_area:
                    warnings.append(f"Moving {element_id[-8:]} across area boundaries requires logical operation")
        
        return ValidationFeedback(
            is_valid=True,
            level=self.validation_level,
            message="Movement is valid (appearance-only change)",
            suggestions=suggestions,
            available_transformations=self._get_contextual_transformations(graph, selection),
            warnings=warnings
        )
    
    def _validate_predicate_edit(self, graph: RelationalGraphWithCuts,
                                selection: Set[ElementID],
                                params: Dict) -> ValidationFeedback:
        """Validate predicate editing action."""
        
        if len(selection) != 1:
            return ValidationFeedback(
                is_valid=False,
                level=self.validation_level,
                message="Select exactly one predicate to edit",
                suggestions=["Single predicate selection required"],
                available_transformations=[]
            )
        
        element_id = next(iter(selection))
        
        if element_id not in graph.E:
            return ValidationFeedback(
                is_valid=False,
                level=self.validation_level,
                message="Selected element is not a predicate",
                suggestions=["Select a predicate (edge) to edit"],
                available_transformations=[]
            )
        
        current_name = graph.rel.get(element_id, "Unknown")
        current_arity = len(graph.nu.get(element_id, ()))
        new_name = params.get('new_name', current_name)
        new_arity = params.get('new_arity', current_arity)
        
        suggestions = [
            f"Current: {current_name}({current_arity})",
            f"New: {new_name}({new_arity})"
        ]
        
        warnings = []
        if new_arity != current_arity:
            warnings.append("Changing arity requires updating vertex connections")
        
        return ValidationFeedback(
            is_valid=True,
            level=self.validation_level,
            message="Predicate edit is valid",
            suggestions=suggestions,
            available_transformations=self._get_contextual_transformations(graph, selection),
            warnings=warnings
        )
    
    def _validate_transformation_application(self, graph: RelationalGraphWithCuts,
                                           selection: Set[ElementID],
                                           params: Dict) -> ValidationFeedback:
        """Validate application of formal transformation rule."""
        
        rule = params.get('rule')
        if not rule:
            return ValidationFeedback(
                is_valid=False,
                level=self.validation_level,
                message="No transformation rule specified",
                suggestions=["Select a transformation rule"],
                available_transformations=[]
            )
        
        # Use transformation engine to validate
        validation = self.transformation_engine.validate_transformation(
            graph, rule, **params
        )
        
        suggestions = []
        if validation.is_valid:
            suggestions.append(f"Rule {rule.value} can be applied")
            suggestions.append("Transformation preserves logical equivalence")
        
        return ValidationFeedback(
            is_valid=validation.is_valid,
            level=self.validation_level,
            message=validation.description,
            suggestions=suggestions,
            available_transformations=self._get_contextual_transformations(graph, selection)
        )
    
    def _get_contextual_transformations(self, graph: RelationalGraphWithCuts,
                                       selection: Set[ElementID]) -> List[Dict]:
        """Get available transformations for current context."""
        
        return self.background_validator.get_available_transformations(graph, selection)
    
    def _find_element_area(self, graph: RelationalGraphWithCuts, element_id: ElementID) -> Optional[ElementID]:
        """Find which area contains the given element."""
        
        for area_id, elements in graph.area.items():
            if element_id in elements:
                return area_id
        return None
    
    def _create_cache_key(self, graph: RelationalGraphWithCuts, action_type: str,
                         selection: Set[ElementID], params: Dict) -> str:
        """Create cache key for validation result."""
        
        # Simple hash-based key (could be more sophisticated)
        graph_hash = hash(frozenset(graph.V) | frozenset(graph.E) | frozenset(graph.Cut))
        selection_hash = hash(frozenset(selection))
        params_hash = hash(frozenset(params.items()) if params else frozenset())
        
        return f"{action_type}_{graph_hash}_{selection_hash}_{params_hash}"


class ValidationIntegration:
    """
    Integration layer that connects background validation with
    the Phase 2 selection and action systems.
    """
    
    def __init__(self, real_time_validator: RealTimeValidator):
        self.validator = real_time_validator
        self.current_feedback: Optional[ValidationFeedback] = None
        
        # UI update callbacks
        self.ui_update_callbacks: List[Callable[[ValidationFeedback], None]] = []
        
        # Set up validation callback
        self.validator.add_validation_callback(self._on_validation_update)
    
    def add_ui_callback(self, callback: Callable[[ValidationFeedback], None]):
        """Add callback for UI updates."""
        self.ui_update_callbacks.append(callback)
    
    def _on_validation_update(self, feedback: ValidationFeedback):
        """Handle validation feedback updates."""
        self.current_feedback = feedback
        
        # Notify UI callbacks
        for callback in self.ui_update_callbacks:
            try:
                callback(feedback)
            except Exception as e:
                print(f"UI callback error: {e}")
    
    def validate_selection_action(self, graph: RelationalGraphWithCuts,
                                 action_type: str,
                                 selected_elements: Set[ElementID],
                                 **action_params) -> ValidationFeedback:
        """Validate action with current selection."""
        
        return self.validator.validate_action(
            graph, action_type, selected_elements, **action_params
        )
    
    def get_action_suggestions(self, graph: RelationalGraphWithCuts,
                              selected_elements: Set[ElementID]) -> List[str]:
        """Get suggestions for actions based on current selection."""
        
        suggestions = []
        
        if not selected_elements:
            suggestions.extend([
                "Select elements to see available actions",
                "Drag to select area for insertion operations",
                "Use transformation rules for logical operations"
            ])
        elif len(selected_elements) == 1:
            element_id = next(iter(selected_elements))
            if element_id in graph.E:
                suggestions.extend([
                    "Edit predicate name or arity",
                    "Delete predicate (Erasure rule)",
                    "Copy to broader context (Iteration rule)"
                ])
            elif element_id in graph.V:
                suggestions.extend([
                    "Connect to predicates",
                    "Delete vertex (Erasure rule)",
                    "Branch Line of Identity"
                ])
            elif element_id in graph.Cut:
                suggestions.extend([
                    "Delete cut contents",
                    "Check for double cut deletion",
                    "Insert elements inside cut"
                ])
        else:
            suggestions.extend([
                "Enclose selection with cut",
                "Delete selected elements (Erasure rule)",
                "Apply transformation rules to subgraph"
            ])
        
        return suggestions
    
    def get_transformation_opportunities(self, graph: RelationalGraphWithCuts) -> List[Dict]:
        """Get available transformation opportunities for entire graph."""
        
        return self.validator.background_validator.get_available_transformations(graph)


# Factory function for easy setup
def create_validation_system(validation_level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationIntegration:
    """Create a complete validation system with integration layer."""
    
    real_time_validator = RealTimeValidator(validation_level)
    integration = ValidationIntegration(real_time_validator)
    
    return integration
