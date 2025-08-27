"""
Transformation rules module for Ergasterion Practice Mode.

Implements Peirce's Existential Graph transformation rules with validation
and scaffolding for the practice mode of Ergasterion.

Based on Chapter 16 of Dau's formalization and Peirce's original rules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import uuid
from datetime import datetime

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut


class TransformationRuleType(Enum):
    """Types of EG transformation rules."""
    # Basic rules
    INSERTION = "insertion"
    ERASURE = "erasure" 
    ITERATION = "iteration"
    DEITERATION = "deiteration"
    
    # Cut rules
    DOUBLE_CUT_INSERTION = "double_cut_insertion"
    DOUBLE_CUT_ERASURE = "double_cut_erasure"
    
    # Advanced rules
    GENERALIZATION = "generalization"
    SPECIALIZATION = "specialization"


class ContextPolarity(Enum):
    """Polarity of contexts in EG."""
    POSITIVE = "positive"
    NEGATIVE = "negative"


@dataclass
class TransformationContext:
    """Context information for a transformation."""
    rule_type: TransformationRuleType
    source_elements: List[str]  # IDs of elements involved
    target_area: Optional[str] = None  # Target area for the transformation
    parameters: Dict[str, Any] = None  # Additional parameters
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ValidationResult:
    """Result of transformation validation."""
    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class TransformationResult:
    """Result of applying a transformation."""
    success: bool
    modified_graph: Optional[RelationalGraphWithCuts] = None
    changes_description: str = ""
    validation_result: Optional[ValidationResult] = None
    step_id: Optional[str] = None


class TransformationRule(ABC):
    """Abstract base class for EG transformation rules."""
    
    def __init__(self, rule_type: TransformationRuleType):
        self.rule_type = rule_type
        self.name = rule_type.value.replace('_', ' ').title()
        self.description = ""
    
    @abstractmethod
    def validate(self, graph: RelationalGraphWithCuts, 
                context: TransformationContext) -> ValidationResult:
        """Validate if the transformation can be applied."""
        pass
    
    @abstractmethod
    def apply(self, graph: RelationalGraphWithCuts, 
             context: TransformationContext) -> TransformationResult:
        """Apply the transformation to the graph."""
        pass
    
    def get_context_polarity(self, graph: RelationalGraphWithCuts, 
                           area_id: str) -> ContextPolarity:
        """Determine the polarity of a context area."""
        # Count nesting depth from sheet to area
        depth = 0
        current_area = area_id
        
        while current_area != graph.sheet:
            depth += 1
            # Find parent of current area
            parent_found = False
            for cut in graph.Cut:
                if cut.id == current_area:
                    # Find which area contains this cut
                    for area, contents in graph.area.items():
                        if cut.id in contents:
                            current_area = area
                            parent_found = True
                            break
                    break
            
            if not parent_found:
                break
        
        # Even depth = positive, odd depth = negative
        return ContextPolarity.POSITIVE if depth % 2 == 0 else ContextPolarity.NEGATIVE
    
    def get_elements_in_area(self, graph: RelationalGraphWithCuts, 
                           area_id: str) -> Dict[str, List[str]]:
        """Get all elements in a specific area."""
        area_contents = graph.area.get(area_id, frozenset())
        
        result = {
            "vertices": [],
            "edges": [],
            "cuts": []
        }
        
        for element_id in area_contents:
            # Check if it's a vertex
            for vertex in graph.V:
                if vertex.id == element_id:
                    result["vertices"].append(element_id)
                    break
            else:
                # Check if it's an edge
                for edge in graph.E:
                    if edge.id == element_id:
                        result["edges"].append(element_id)
                        break
                else:
                    # Check if it's a cut
                    for cut in graph.Cut:
                        if cut.id == element_id:
                            result["cuts"].append(element_id)
                            break
        
        return result


class InsertionRule(TransformationRule):
    """Rule for inserting graphs into any context."""
    
    def __init__(self):
        super().__init__(TransformationRuleType.INSERTION)
        self.description = "Insert any graph into any context"
    
    def validate(self, graph: RelationalGraphWithCuts, 
                context: TransformationContext) -> ValidationResult:
        """Validate insertion rule application."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check if target area exists
        target_area = context.target_area or graph.sheet
        if target_area != graph.sheet:
            area_exists = any(cut.id == target_area for cut in graph.Cut)
            if not area_exists:
                errors.append(f"Target area {target_area} does not exist")
        
        # Insertion is always valid (Peirce's rule)
        # But provide suggestions for good practice
        if target_area == graph.sheet:
            suggestions.append("Inserting into sheet of assertion (positive context)")
        else:
            polarity = self.get_context_polarity(graph, target_area)
            if polarity == ContextPolarity.NEGATIVE:
                suggestions.append("Inserting into negative context - consider logical implications")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def apply(self, graph: RelationalGraphWithCuts, 
             context: TransformationContext) -> TransformationResult:
        """Apply insertion rule."""
        validation = self.validate(graph, context)
        if not validation.is_valid:
            return TransformationResult(
                success=False,
                validation_result=validation
            )
        
        # For now, return success without actual modification
        # Full implementation would create new graph elements
        return TransformationResult(
            success=True,
            modified_graph=graph,  # Would be modified copy
            changes_description="Insertion rule applied",
            validation_result=validation,
            step_id=str(uuid.uuid4())
        )


class ErasureRule(TransformationRule):
    """Rule for erasing graphs from positive contexts only."""
    
    def __init__(self):
        super().__init__(TransformationRuleType.ERASURE)
        self.description = "Erase any graph from positive context only"
    
    def validate(self, graph: RelationalGraphWithCuts, 
                context: TransformationContext) -> ValidationResult:
        """Validate erasure rule application."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check that elements exist
        for element_id in context.source_elements:
            element_exists = False
            
            # Check vertices
            for vertex in graph.V:
                if vertex.id == element_id:
                    element_exists = True
                    break
            
            if not element_exists:
                # Check edges
                for edge in graph.E:
                    if edge.id == element_id:
                        element_exists = True
                        break
            
            if not element_exists:
                # Check cuts
                for cut in graph.Cut:
                    if cut.id == element_id:
                        element_exists = True
                        break
            
            if not element_exists:
                errors.append(f"Element {element_id} does not exist")
        
        # Check that elements are in positive contexts
        for element_id in context.source_elements:
            # Find which area contains this element
            element_area = None
            for area_id, contents in graph.area.items():
                if element_id in contents:
                    element_area = area_id
                    break
            
            if element_area:
                polarity = self.get_context_polarity(graph, element_area)
                if polarity == ContextPolarity.NEGATIVE:
                    errors.append(f"Cannot erase {element_id} from negative context")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def apply(self, graph: RelationalGraphWithCuts, 
             context: TransformationContext) -> TransformationResult:
        """Apply erasure rule."""
        validation = self.validate(graph, context)
        if not validation.is_valid:
            return TransformationResult(
                success=False,
                validation_result=validation
            )
        
        # For now, return success without actual modification
        return TransformationResult(
            success=True,
            modified_graph=graph,  # Would be modified copy
            changes_description=f"Erased elements: {', '.join(context.source_elements)}",
            validation_result=validation,
            step_id=str(uuid.uuid4())
        )


class IterationRule(TransformationRule):
    """Rule for copying elements within the same context."""
    
    def __init__(self):
        super().__init__(TransformationRuleType.ITERATION)
        self.description = "Copy any graph within the same context"
    
    def validate(self, graph: RelationalGraphWithCuts, 
                context: TransformationContext) -> ValidationResult:
        """Validate iteration rule application."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check that source elements exist and are in same context
        source_areas = set()
        
        for element_id in context.source_elements:
            element_exists = False
            element_area = None
            
            # Find element and its area
            for area_id, contents in graph.area.items():
                if element_id in contents:
                    element_exists = True
                    element_area = area_id
                    source_areas.add(area_id)
                    break
            
            if not element_exists:
                errors.append(f"Element {element_id} does not exist")
        
        # All elements must be in the same area
        if len(source_areas) > 1:
            errors.append("All elements must be in the same context for iteration")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def apply(self, graph: RelationalGraphWithCuts, 
             context: TransformationContext) -> TransformationResult:
        """Apply iteration rule."""
        validation = self.validate(graph, context)
        if not validation.is_valid:
            return TransformationResult(
                success=False,
                validation_result=validation
            )
        
        return TransformationResult(
            success=True,
            modified_graph=graph,  # Would be modified copy
            changes_description=f"Iterated elements: {', '.join(context.source_elements)}",
            validation_result=validation,
            step_id=str(uuid.uuid4())
        )


class DeiterationRule(TransformationRule):
    """Rule for removing duplicate elements in the same context."""
    
    def __init__(self):
        super().__init__(TransformationRuleType.DEITERATION)
        self.description = "Remove duplicate graphs in the same context"
    
    def validate(self, graph: RelationalGraphWithCuts, 
                context: TransformationContext) -> ValidationResult:
        """Validate deiteration rule application."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check that elements exist and are duplicates
        # This would require more sophisticated duplicate detection
        # For now, just check existence
        
        for element_id in context.source_elements:
            element_exists = False
            for area_id, contents in graph.area.items():
                if element_id in contents:
                    element_exists = True
                    break
            
            if not element_exists:
                errors.append(f"Element {element_id} does not exist")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def apply(self, graph: RelationalGraphWithCuts, 
             context: TransformationContext) -> TransformationResult:
        """Apply deiteration rule."""
        validation = self.validate(graph, context)
        if not validation.is_valid:
            return TransformationResult(
                success=False,
                validation_result=validation
            )
        
        return TransformationResult(
            success=True,
            modified_graph=graph,  # Would be modified copy
            changes_description=f"Deiterated elements: {', '.join(context.source_elements)}",
            validation_result=validation,
            step_id=str(uuid.uuid4())
        )


class DoubleCutInsertionRule(TransformationRule):
    """Rule for inserting double cuts (double negation)."""
    
    def __init__(self):
        super().__init__(TransformationRuleType.DOUBLE_CUT_INSERTION)
        self.description = "Insert double cut around any graph"
    
    def validate(self, graph: RelationalGraphWithCuts, 
                context: TransformationContext) -> ValidationResult:
        """Validate double cut insertion."""
        errors = []
        warnings = []
        suggestions = ["Double cut insertion is always valid (law of double negation)"]
        
        # Check target area exists
        target_area = context.target_area or graph.sheet
        if target_area != graph.sheet:
            area_exists = any(cut.id == target_area for cut in graph.Cut)
            if not area_exists:
                errors.append(f"Target area {target_area} does not exist")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def apply(self, graph: RelationalGraphWithCuts, 
             context: TransformationContext) -> TransformationResult:
        """Apply double cut insertion."""
        validation = self.validate(graph, context)
        if not validation.is_valid:
            return TransformationResult(
                success=False,
                validation_result=validation
            )
        
        return TransformationResult(
            success=True,
            modified_graph=graph,  # Would be modified copy with new cuts
            changes_description="Inserted double cut",
            validation_result=validation,
            step_id=str(uuid.uuid4())
        )


class DoubleCutErasureRule(TransformationRule):
    """Rule for erasing double cuts."""
    
    def __init__(self):
        super().__init__(TransformationRuleType.DOUBLE_CUT_ERASURE)
        self.description = "Erase double cut (remove double negation)"
    
    def validate(self, graph: RelationalGraphWithCuts, 
                context: TransformationContext) -> ValidationResult:
        """Validate double cut erasure."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check that we have exactly two nested cuts
        if len(context.source_elements) != 2:
            errors.append("Double cut erasure requires exactly two nested cuts")
            return ValidationResult(is_valid=False, errors=errors)
        
        outer_cut_id, inner_cut_id = context.source_elements
        
        # Verify both are cuts
        outer_exists = any(cut.id == outer_cut_id for cut in graph.Cut)
        inner_exists = any(cut.id == inner_cut_id for cut in graph.Cut)
        
        if not outer_exists:
            errors.append(f"Outer cut {outer_cut_id} does not exist")
        if not inner_exists:
            errors.append(f"Inner cut {inner_cut_id} does not exist")
        
        # Verify nesting relationship
        if outer_exists and inner_exists:
            outer_contents = graph.area.get(outer_cut_id, frozenset())
            if inner_cut_id not in outer_contents:
                errors.append("Cuts are not properly nested for double cut erasure")
            
            # Check that outer cut contains only the inner cut
            if len(outer_contents) != 1:
                warnings.append("Outer cut contains elements other than inner cut")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def apply(self, graph: RelationalGraphWithCuts, 
             context: TransformationContext) -> TransformationResult:
        """Apply double cut erasure."""
        validation = self.validate(graph, context)
        if not validation.is_valid:
            return TransformationResult(
                success=False,
                validation_result=validation
            )
        
        return TransformationResult(
            success=True,
            modified_graph=graph,  # Would be modified copy with cuts removed
            changes_description=f"Erased double cut: {context.source_elements}",
            validation_result=validation,
            step_id=str(uuid.uuid4())
        )


class TransformationEngine:
    """Engine for managing and applying EG transformation rules."""
    
    def __init__(self):
        self.rules: Dict[TransformationRuleType, TransformationRule] = {}
        self._initialize_rules()
    
    def _initialize_rules(self):
        """Initialize all transformation rules."""
        self.rules[TransformationRuleType.INSERTION] = InsertionRule()
        self.rules[TransformationRuleType.ERASURE] = ErasureRule()
        self.rules[TransformationRuleType.ITERATION] = IterationRule()
        self.rules[TransformationRuleType.DEITERATION] = DeiterationRule()
        self.rules[TransformationRuleType.DOUBLE_CUT_INSERTION] = DoubleCutInsertionRule()
        self.rules[TransformationRuleType.DOUBLE_CUT_ERASURE] = DoubleCutErasureRule()
    
    def get_available_rules(self) -> List[TransformationRule]:
        """Get list of available transformation rules."""
        return list(self.rules.values())
    
    def get_rule(self, rule_type: TransformationRuleType) -> Optional[TransformationRule]:
        """Get a specific transformation rule."""
        return self.rules.get(rule_type)
    
    def validate_transformation(self, graph: RelationalGraphWithCuts,
                              rule_type: TransformationRuleType,
                              context: TransformationContext) -> ValidationResult:
        """Validate a transformation before applying it."""
        rule = self.get_rule(rule_type)
        if not rule:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unknown rule type: {rule_type}"]
            )
        
        return rule.validate(graph, context)
    
    def apply_transformation(self, graph: RelationalGraphWithCuts,
                           rule_type: TransformationRuleType,
                           context: TransformationContext) -> TransformationResult:
        """Apply a transformation to the graph."""
        rule = self.get_rule(rule_type)
        if not rule:
            return TransformationResult(
                success=False,
                validation_result=ValidationResult(
                    is_valid=False,
                    errors=[f"Unknown rule type: {rule_type}"]
                )
            )
        
        return rule.apply(graph, context)
    
    def get_applicable_rules(self, graph: RelationalGraphWithCuts,
                           selected_elements: List[str]) -> List[Tuple[TransformationRuleType, ValidationResult]]:
        """Get rules that can be applied to the selected elements."""
        applicable = []
        
        for rule_type, rule in self.rules.items():
            # Create a basic context for validation
            context = TransformationContext(
                rule_type=rule_type,
                source_elements=selected_elements
            )
            
            validation = rule.validate(graph, context)
            if validation.is_valid:
                applicable.append((rule_type, validation))
        
        return applicable
    
    def suggest_next_moves(self, graph: RelationalGraphWithCuts,
                          selected_elements: List[str]) -> List[str]:
        """Suggest possible next transformation moves."""
        suggestions = []
        
        applicable_rules = self.get_applicable_rules(graph, selected_elements)
        
        for rule_type, validation in applicable_rules:
            rule = self.get_rule(rule_type)
            suggestion = f"{rule.name}: {rule.description}"
            if validation.suggestions:
                suggestion += f" ({'; '.join(validation.suggestions)})"
            suggestions.append(suggestion)
        
        return suggestions


# Global transformation engine instance
_transformation_engine = None

def get_transformation_engine() -> TransformationEngine:
    """Get the global transformation engine instance."""
    global _transformation_engine
    if _transformation_engine is None:
        _transformation_engine = TransformationEngine()
    return _transformation_engine

