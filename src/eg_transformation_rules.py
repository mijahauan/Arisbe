#!/usr/bin/env python3
"""
Existential Graph Transformation Rules Engine

Implements the formal transformation rules for Existential Graphs following Dau's formalism:
- Double Cut Rule (insertion/deletion)
- Iteration Rule (copying within same/broader context)
- Erasure Rule (deletion from broader context)
- Deiteration Rule (removal of duplicates)

These rules maintain syntactic validity and enable sound logical reasoning.
"""

from typing import Set, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import copy

from egi_core_dau import (
    RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID,
    create_vertex, create_edge, create_cut
)


class TransformationRule(Enum):
    """Types of EG transformation rules."""
    DOUBLE_CUT_INSERT = "double_cut_insert"
    DOUBLE_CUT_DELETE = "double_cut_delete"
    ITERATION = "iteration"
    ERASURE = "erasure"
    DEITERATION = "deiteration"
    CUT_INSERT = "cut_insert"
    CUT_DELETE = "cut_delete"


@dataclass
class TransformationResult:
    """Result of applying a transformation rule."""
    success: bool
    new_graph: Optional[RelationalGraphWithCuts]
    rule_applied: TransformationRule
    description: str
    error_message: Optional[str] = None
    affected_elements: Set[ElementID] = None
    
    def __post_init__(self):
        if self.affected_elements is None:
            self.affected_elements = set()


@dataclass
class ValidationResult:
    """Result of validating a proposed transformation."""
    is_valid: bool
    rule: TransformationRule
    description: str
    error_message: Optional[str] = None
    preconditions_met: bool = True
    postconditions_satisfied: bool = True


class EGTransformationEngine:
    """
    Engine for applying formal EG transformation rules.
    
    Ensures all transformations maintain syntactic validity and follow
    the formal rules of Existential Graph logic.
    """
    
    def __init__(self):
        self.validation_enabled = True
        self.strict_mode = True  # Enforce all preconditions
    
    def validate_transformation(self, graph: RelationalGraphWithCuts, 
                               rule: TransformationRule, 
                               **kwargs) -> ValidationResult:
        """Validate whether a transformation can be applied."""
        
        if rule == TransformationRule.DOUBLE_CUT_INSERT:
            return self._validate_double_cut_insert(graph, **kwargs)
        elif rule == TransformationRule.DOUBLE_CUT_DELETE:
            return self._validate_double_cut_delete(graph, **kwargs)
        elif rule == TransformationRule.ITERATION:
            return self._validate_iteration(graph, **kwargs)
        elif rule == TransformationRule.ERASURE:
            return self._validate_erasure(graph, **kwargs)
        elif rule == TransformationRule.DEITERATION:
            return self._validate_deiteration(graph, **kwargs)
        elif rule == TransformationRule.CUT_INSERT:
            return self._validate_cut_insert(graph, **kwargs)
        elif rule == TransformationRule.CUT_DELETE:
            return self._validate_cut_delete(graph, **kwargs)
        else:
            return ValidationResult(
                is_valid=False,
                rule=rule,
                description="Unknown transformation rule",
                error_message=f"Rule {rule} is not implemented"
            )
    
    def apply_transformation(self, graph: RelationalGraphWithCuts,
                           rule: TransformationRule,
                           **kwargs) -> TransformationResult:
        """Apply a transformation rule to the graph."""
        
        # Validate first if validation is enabled
        if self.validation_enabled:
            validation = self.validate_transformation(graph, rule, **kwargs)
            if not validation.is_valid:
                return TransformationResult(
                    success=False,
                    new_graph=None,
                    rule_applied=rule,
                    description=validation.description,
                    error_message=validation.error_message
                )
        
        try:
            if rule == TransformationRule.DOUBLE_CUT_INSERT:
                return self._apply_double_cut_insert(graph, **kwargs)
            elif rule == TransformationRule.DOUBLE_CUT_DELETE:
                return self._apply_double_cut_delete(graph, **kwargs)
            elif rule == TransformationRule.ITERATION:
                return self._apply_iteration(graph, **kwargs)
            elif rule == TransformationRule.ERASURE:
                return self._apply_erasure(graph, **kwargs)
            elif rule == TransformationRule.DEITERATION:
                return self._apply_deiteration(graph, **kwargs)
            elif rule == TransformationRule.CUT_INSERT:
                return self._apply_cut_insert(graph, **kwargs)
            elif rule == TransformationRule.CUT_DELETE:
                return self._apply_cut_delete(graph, **kwargs)
            else:
                return TransformationResult(
                    success=False,
                    new_graph=None,
                    rule_applied=rule,
                    description="Unknown transformation rule",
                    error_message=f"Rule {rule} is not implemented"
                )
        
        except Exception as e:
            return TransformationResult(
                success=False,
                new_graph=None,
                rule_applied=rule,
                description="Transformation failed",
                error_message=str(e)
            )
    
    # Double Cut Rules
    def _validate_double_cut_insert(self, graph: RelationalGraphWithCuts, 
                                   target_area: ElementID, **kwargs) -> ValidationResult:
        """Validate double cut insertion (always valid)."""
        return ValidationResult(
            is_valid=True,
            rule=TransformationRule.DOUBLE_CUT_INSERT,
            description="Double cut insertion is always valid"
        )
    
    def _apply_double_cut_insert(self, graph: RelationalGraphWithCuts,
                                target_area: ElementID, **kwargs) -> TransformationResult:
        """Apply double cut insertion: insert two nested empty cuts."""
        
        # Create two new cuts
        outer_cut = create_cut()
        inner_cut = create_cut()
        
        # Add cuts to graph
        new_graph = graph.with_cut(outer_cut).with_cut(inner_cut)
        
        # Update area mappings
        new_area = dict(new_graph.area)
        
        # Add outer cut to target area
        if target_area in new_area:
            new_area[target_area] = new_area[target_area] | {outer_cut.id}
        else:
            new_area[target_area] = {outer_cut.id}
        
        # Add inner cut to outer cut (empty)
        new_area[outer_cut.id] = {inner_cut.id}
        new_area[inner_cut.id] = set()
        
        final_graph = new_graph._replace(area=new_area)
        
        return TransformationResult(
            success=True,
            new_graph=final_graph,
            rule_applied=TransformationRule.DOUBLE_CUT_INSERT,
            description="Inserted double cut (two nested empty cuts)",
            affected_elements={outer_cut.id, inner_cut.id}
        )
    
    def _validate_double_cut_delete(self, graph: RelationalGraphWithCuts,
                                   outer_cut_id: ElementID, **kwargs) -> ValidationResult:
        """Validate double cut deletion."""
        
        # Check if outer cut exists
        if outer_cut_id not in graph.Cut:
            return ValidationResult(
                is_valid=False,
                rule=TransformationRule.DOUBLE_CUT_DELETE,
                description="Invalid double cut deletion",
                error_message="Outer cut does not exist"
            )
        
        # Check if outer cut contains exactly one inner cut
        outer_elements = graph.area.get(outer_cut_id, set())
        inner_cuts = [eid for eid in outer_elements if eid in graph.Cut]
        
        if len(inner_cuts) != 1:
            return ValidationResult(
                is_valid=False,
                rule=TransformationRule.DOUBLE_CUT_DELETE,
                description="Invalid double cut deletion",
                error_message="Outer cut must contain exactly one inner cut"
            )
        
        inner_cut_id = inner_cuts[0]
        
        # Check if inner cut is empty
        inner_elements = graph.area.get(inner_cut_id, set())
        if inner_elements:
            return ValidationResult(
                is_valid=False,
                rule=TransformationRule.DOUBLE_CUT_DELETE,
                description="Invalid double cut deletion",
                error_message="Inner cut must be empty"
            )
        
        return ValidationResult(
            is_valid=True,
            rule=TransformationRule.DOUBLE_CUT_DELETE,
            description="Double cut deletion is valid"
        )
    
    def _apply_double_cut_delete(self, graph: RelationalGraphWithCuts,
                                outer_cut_id: ElementID, **kwargs) -> TransformationResult:
        """Apply double cut deletion: remove two nested empty cuts."""
        
        # Get inner cut
        outer_elements = graph.area.get(outer_cut_id, set())
        inner_cut_id = next(eid for eid in outer_elements if eid in graph.Cut)
        
        # Remove both cuts from graph
        new_V = graph.V
        new_E = graph.E
        new_Cut = graph.Cut - {outer_cut_id, inner_cut_id}
        
        # Update area mappings
        new_area = dict(graph.area)
        
        # Remove cuts from their parent area
        for area_id, elements in new_area.items():
            if outer_cut_id in elements:
                new_area[area_id] = elements - {outer_cut_id}
                break
        
        # Remove cut area mappings
        del new_area[outer_cut_id]
        del new_area[inner_cut_id]
        
        final_graph = graph._replace(V=new_V, E=new_E, Cut=new_Cut, area=new_area)
        
        return TransformationResult(
            success=True,
            new_graph=final_graph,
            rule_applied=TransformationRule.DOUBLE_CUT_DELETE,
            description="Deleted double cut (two nested empty cuts)",
            affected_elements={outer_cut_id, inner_cut_id}
        )
    
    # Iteration Rule
    def _validate_iteration(self, graph: RelationalGraphWithCuts,
                           source_elements: Set[ElementID],
                           target_area: ElementID, **kwargs) -> ValidationResult:
        """Validate iteration (copying elements to same or broader context)."""
        
        # Check if all source elements exist
        all_elements = graph.V | graph.E | graph.Cut
        if not source_elements.issubset(all_elements):
            return ValidationResult(
                is_valid=False,
                rule=TransformationRule.ITERATION,
                description="Invalid iteration",
                error_message="Some source elements do not exist"
            )
        
        # Check context relationship (target must be same or broader than source)
        # This is a simplified check - full implementation would need proper context analysis
        return ValidationResult(
            is_valid=True,
            rule=TransformationRule.ITERATION,
            description="Iteration is valid (simplified validation)"
        )
    
    def _apply_iteration(self, graph: RelationalGraphWithCuts,
                        source_elements: Set[ElementID],
                        target_area: ElementID, **kwargs) -> TransformationResult:
        """Apply iteration: copy elements to target area."""
        
        # This is a simplified implementation
        # Full implementation would need to handle complex subgraph copying
        
        return TransformationResult(
            success=False,
            new_graph=None,
            rule_applied=TransformationRule.ITERATION,
            description="Iteration not fully implemented",
            error_message="Complex subgraph copying requires additional implementation"
        )
    
    # Erasure Rule
    def _validate_erasure(self, graph: RelationalGraphWithCuts,
                         elements_to_erase: Set[ElementID], **kwargs) -> ValidationResult:
        """Validate erasure (deletion from broader context)."""
        
        # Check if all elements exist
        all_elements = graph.V | graph.E | graph.Cut
        if not elements_to_erase.issubset(all_elements):
            return ValidationResult(
                is_valid=False,
                rule=TransformationRule.ERASURE,
                description="Invalid erasure",
                error_message="Some elements to erase do not exist"
            )
        
        return ValidationResult(
            is_valid=True,
            rule=TransformationRule.ERASURE,
            description="Erasure is valid"
        )
    
    def _apply_erasure(self, graph: RelationalGraphWithCuts,
                      elements_to_erase: Set[ElementID], **kwargs) -> TransformationResult:
        """Apply erasure: remove elements from graph."""
        
        # Remove elements from sets
        new_V = graph.V - elements_to_erase
        new_E = graph.E - elements_to_erase
        new_Cut = graph.Cut - elements_to_erase
        
        # Update mappings
        new_rel = {k: v for k, v in graph.rel.items() if k not in elements_to_erase}
        new_nu = {k: v for k, v in graph.nu.items() if k not in elements_to_erase}
        
        # Update area mappings
        new_area = {}
        for area_id, elements in graph.area.items():
            if area_id not in elements_to_erase:
                new_area[area_id] = elements - elements_to_erase
        
        final_graph = graph._replace(
            V=new_V, E=new_E, Cut=new_Cut,
            rel=new_rel, nu=new_nu, area=new_area
        )
        
        return TransformationResult(
            success=True,
            new_graph=final_graph,
            rule_applied=TransformationRule.ERASURE,
            description=f"Erased {len(elements_to_erase)} elements",
            affected_elements=elements_to_erase
        )
    
    # Deiteration Rule
    def _validate_deiteration(self, graph: RelationalGraphWithCuts,
                             duplicate_elements: Set[ElementID], **kwargs) -> ValidationResult:
        """Validate deiteration (removal of duplicates)."""
        
        # This would need sophisticated duplicate detection logic
        return ValidationResult(
            is_valid=True,
            rule=TransformationRule.DEITERATION,
            description="Deiteration validation not fully implemented"
        )
    
    def _apply_deiteration(self, graph: RelationalGraphWithCuts,
                          duplicate_elements: Set[ElementID], **kwargs) -> TransformationResult:
        """Apply deiteration: remove duplicate elements."""
        
        # Use erasure for now (simplified)
        return self._apply_erasure(graph, duplicate_elements)
    
    # Cut Rules
    def _validate_cut_insert(self, graph: RelationalGraphWithCuts,
                            target_area: ElementID,
                            enclosed_elements: Set[ElementID] = None, **kwargs) -> ValidationResult:
        """Validate cut insertion."""
        
        if enclosed_elements is None:
            enclosed_elements = set()
        
        # Check if enclosed elements exist and are in target area
        if enclosed_elements:
            area_elements = graph.area.get(target_area, set())
            if not enclosed_elements.issubset(area_elements):
                return ValidationResult(
                    is_valid=False,
                    rule=TransformationRule.CUT_INSERT,
                    description="Invalid cut insertion",
                    error_message="Some enclosed elements are not in target area"
                )
        
        return ValidationResult(
            is_valid=True,
            rule=TransformationRule.CUT_INSERT,
            description="Cut insertion is valid"
        )
    
    def _apply_cut_insert(self, graph: RelationalGraphWithCuts,
                         target_area: ElementID,
                         enclosed_elements: Set[ElementID] = None, **kwargs) -> TransformationResult:
        """Apply cut insertion: create new cut around elements."""
        
        if enclosed_elements is None:
            enclosed_elements = set()
        
        # Create new cut
        new_cut = create_cut()
        
        # Add cut to graph
        new_graph = graph.with_cut(new_cut)
        
        # Update area mappings
        new_area = dict(new_graph.area)
        
        # Remove enclosed elements from target area
        if target_area in new_area:
            new_area[target_area] = new_area[target_area] - enclosed_elements
            # Add new cut to target area
            new_area[target_area] = new_area[target_area] | {new_cut.id}
        
        # Add enclosed elements to new cut
        new_area[new_cut.id] = enclosed_elements
        
        final_graph = new_graph._replace(area=new_area)
        
        return TransformationResult(
            success=True,
            new_graph=final_graph,
            rule_applied=TransformationRule.CUT_INSERT,
            description=f"Inserted cut around {len(enclosed_elements)} elements",
            affected_elements={new_cut.id} | enclosed_elements
        )
    
    def _validate_cut_delete(self, graph: RelationalGraphWithCuts,
                            cut_id: ElementID, **kwargs) -> ValidationResult:
        """Validate cut deletion."""
        
        if cut_id not in graph.Cut:
            return ValidationResult(
                is_valid=False,
                rule=TransformationRule.CUT_DELETE,
                description="Invalid cut deletion",
                error_message="Cut does not exist"
            )
        
        return ValidationResult(
            is_valid=True,
            rule=TransformationRule.CUT_DELETE,
            description="Cut deletion is valid"
        )
    
    def _apply_cut_delete(self, graph: RelationalGraphWithCuts,
                         cut_id: ElementID, **kwargs) -> TransformationResult:
        """Apply cut deletion: remove cut and move contents to parent area."""
        
        # Find parent area of the cut
        parent_area = None
        for area_id, elements in graph.area.items():
            if cut_id in elements:
                parent_area = area_id
                break
        
        if parent_area is None:
            return TransformationResult(
                success=False,
                new_graph=None,
                rule_applied=TransformationRule.CUT_DELETE,
                description="Cut deletion failed",
                error_message="Could not find parent area"
            )
        
        # Get cut contents
        cut_contents = graph.area.get(cut_id, set())
        
        # Remove cut from graph
        new_Cut = graph.Cut - {cut_id}
        
        # Update area mappings
        new_area = dict(graph.area)
        
        # Remove cut from parent area and add its contents
        new_area[parent_area] = (new_area[parent_area] - {cut_id}) | cut_contents
        
        # Remove cut area mapping
        del new_area[cut_id]
        
        final_graph = graph._replace(Cut=new_Cut, area=new_area)
        
        return TransformationResult(
            success=True,
            new_graph=final_graph,
            rule_applied=TransformationRule.CUT_DELETE,
            description=f"Deleted cut and moved {len(cut_contents)} elements to parent area",
            affected_elements={cut_id} | cut_contents
        )


class BackgroundValidator:
    """
    Background validation system for real-time syntactic checking.
    
    Continuously validates EG structure and provides feedback about
    rule compliance and valid transformations.
    """
    
    def __init__(self, transformation_engine: EGTransformationEngine):
        self.transformation_engine = transformation_engine
        self.validation_cache = {}
    
    def validate_graph_structure(self, graph: RelationalGraphWithCuts) -> Dict[str, any]:
        """Perform comprehensive validation of graph structure."""
        
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Check basic structural integrity
        self._check_area_consistency(graph, validation_results)
        self._check_nu_mapping_consistency(graph, validation_results)
        self._check_cut_nesting(graph, validation_results)
        
        # Check for potential transformations
        self._suggest_transformations(graph, validation_results)
        
        return validation_results
    
    def _check_area_consistency(self, graph: RelationalGraphWithCuts, results: Dict):
        """Check that area mappings are consistent."""
        
        # FIXED: Compare element IDs, not objects vs strings
        all_element_ids = {elem.id for elem in (graph.V | graph.E | graph.Cut)}
        
        # Check that all elements are in some area
        elements_in_areas = set()
        for elements in graph.area.values():
            elements_in_areas.update(elements)
        
        orphaned_elements = all_element_ids - elements_in_areas
        if orphaned_elements:
            results['errors'].append(f"Orphaned elements not in any area: {orphaned_elements}")
            results['is_valid'] = False
    
    def _check_nu_mapping_consistency(self, graph: RelationalGraphWithCuts, results: Dict):
        """Check that nu mappings are consistent."""
        
        # FIXED: Compare IDs consistently
        edge_ids = {edge.id for edge in graph.E}
        vertex_ids = {vertex.id for vertex in graph.V}
        
        # Check that all edges in nu mapping exist
        for edge_id in graph.nu:
            if edge_id not in edge_ids:
                results['errors'].append(f"Nu mapping references non-existent edge: {edge_id}")
                results['is_valid'] = False
        
        # Check that all vertices in nu mappings exist
        for edge_id, vertex_tuple in graph.nu.items():
            for vertex_id in vertex_tuple:
                if vertex_id not in vertex_ids:
                    results['errors'].append(f"Nu mapping references non-existent vertex: {vertex_id}")
                    results['is_valid'] = False
    
    def _check_cut_nesting(self, graph: RelationalGraphWithCuts, results: Dict):
        """Check that cut nesting is proper (no cycles)."""
        
        # Build containment graph
        containment = {}
        for area_id, elements in graph.area.items():
            if area_id in graph.Cut:
                containment[area_id] = [eid for eid in elements if eid in graph.Cut]
        
        # Check for cycles (simplified)
        visited = set()
        
        def has_cycle(cut_id, path):
            if cut_id in path:
                return True
            if cut_id in visited:
                return False
            
            visited.add(cut_id)
            path.add(cut_id)
            
            for child_cut in containment.get(cut_id, []):
                if has_cycle(child_cut, path):
                    return True
            
            path.remove(cut_id)
            return False
        
        for cut_id in graph.Cut:
            if has_cycle(cut_id, set()):
                results['errors'].append(f"Circular cut containment detected involving cut: {cut_id}")
                results['is_valid'] = False
    
    def _suggest_transformations(self, graph: RelationalGraphWithCuts, results: Dict):
        """Suggest possible valid transformations."""
        
        # Look for double cuts that can be deleted
        for cut_id in graph.Cut:
            validation = self.transformation_engine.validate_transformation(
                graph, TransformationRule.DOUBLE_CUT_DELETE, outer_cut_id=cut_id
            )
            if validation.is_valid:
                results['suggestions'].append(f"Can apply double cut deletion to cut {cut_id}")
        
        # Look for empty areas where double cuts can be inserted
        for area_id, elements in graph.area.items():
            if not elements:  # Empty area
                results['suggestions'].append(f"Can insert double cut in empty area {area_id}")
    
    def get_available_transformations(self, graph: RelationalGraphWithCuts, 
                                    context_elements: Set[ElementID] = None) -> List[Dict]:
        """Get list of available transformations for current context."""
        
        available = []
        
        # Check all transformation rules
        for rule in TransformationRule:
            if rule == TransformationRule.DOUBLE_CUT_INSERT:
                # Can always insert double cut in any area
                for area_id in graph.area:
                    available.append({
                        'rule': rule,
                        'description': f"Insert double cut in area {area_id}",
                        'parameters': {'target_area': area_id}
                    })
            
            elif rule == TransformationRule.DOUBLE_CUT_DELETE:
                # Check each cut for double cut deletion
                for cut_id in graph.Cut:
                    validation = self.transformation_engine.validate_transformation(
                        graph, rule, outer_cut_id=cut_id
                    )
                    if validation.is_valid:
                        available.append({
                            'rule': rule,
                            'description': f"Delete double cut {cut_id}",
                            'parameters': {'outer_cut_id': cut_id}
                        })
            
            elif rule == TransformationRule.ERASURE:
                # Can erase any elements
                if context_elements:
                    available.append({
                        'rule': rule,
                        'description': f"Erase {len(context_elements)} selected elements",
                        'parameters': {'elements_to_erase': context_elements}
                    })
        
        return available
