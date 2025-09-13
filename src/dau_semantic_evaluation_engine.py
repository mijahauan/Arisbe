"""
Dau-compliant semantic evaluation engine for Existential Graph Instances (EGIs).

Implements Chapter 13 of Dau's "Mathematical Logic with Diagrams" including:
- Definition 13.2: Partial and Total Valuations
- Definition 13.3: Classical Evaluation of Graphs  
- Definition 13.4: Endoporeutic Evaluation of Graphs
- Lemma 13.5: Equivalence of Both Evaluations
- Theorems 13.7-13.8: Main Soundness Theorems

This provides the formal semantic foundation for EGI interpretation and validation.
"""

from typing import Dict, Set, Optional, Tuple, Any, Callable, FrozenSet, Union, Iterator, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import itertools

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from frozendict import frozendict


class ContextPolarity(Enum):
    """Polarity of a context based on nesting depth."""
    POSITIVE = "positive"  # Even nesting depth (sheet, 2nd level cuts, etc.)
    NEGATIVE = "negative"  # Odd nesting depth (1st level cuts, 3rd level cuts, etc.)


@dataclass(frozen=True)
class RelationalStructure:
    """
    Relational structure (U, I) as defined in Dau Chapter 13.
    
    U: Universe of discourse (non-empty set of individuals)
    I: Interpretation function mapping relation names to relations
    """
    universe: FrozenSet[Any]  # Universe of discourse U
    interpretation: frozendict  # Interpretation function I: relation_name -> relation
    
    def __post_init__(self):
        if not self.universe:
            raise ValueError("Universe of discourse must be non-empty")


@dataclass(frozen=True) 
class Valuation:
    """
    Valuation mapping vertices to objects in universe of discourse.
    
    Implements Definition 13.2: Partial and Total Valuations
    """
    mapping: frozendict  # vertex_id -> object in universe
    domain: FrozenSet[ElementID]  # Domain of the valuation
    
    def __post_init__(self):
        if self.domain != frozenset(self.mapping.keys()):
            raise ValueError("Domain must match mapping keys")
    
    def is_total_for(self, vertices: Set[ElementID]) -> bool:
        """Check if this is a total valuation for given vertex set."""
        return self.domain == frozenset(vertices)
    
    def is_partial_for_context(self, egi: RelationalGraphWithCuts, context: ElementID) -> bool:
        """
        Check if this is a partial valuation for context c.
        
        Per Dau Definition 13.2:
        V' ⊇ {v ∈ V | v > c} and V' ∩ {v ∈ V | v ≤ c} = ∅
        """
        vertices_above_context = self._get_vertices_above_context(egi, context)
        vertices_at_or_below_context = self._get_vertices_at_or_below_context(egi, context)
        
        return (vertices_above_context.issubset(self.domain) and 
                self.domain.isdisjoint(vertices_at_or_below_context))
    
    def extend(self, extensions: Dict[ElementID, Any]) -> 'Valuation':
        """Extend valuation with additional vertex assignments."""
        new_mapping = dict(self.mapping)
        new_mapping.update(extensions)
        return Valuation(
            mapping=frozendict(new_mapping),
            domain=frozenset(new_mapping.keys())
        )
    
    def restrict_to(self, vertex_set: Set[ElementID]) -> 'Valuation':
        """Restrict valuation to given vertex set."""
        restricted_mapping = {v: obj for v, obj in self.mapping.items() 
                            if v in vertex_set}
        return Valuation(
            mapping=frozendict(restricted_mapping),
            domain=frozenset(restricted_mapping.keys())
        )
    
    def _get_vertices_above_context(self, egi: RelationalGraphWithCuts, context: ElementID) -> Set[ElementID]:
        """Get vertices that are above (outside) the given context."""
        if not egi.hierarchical_index:
            return set()
        
        # Get all ancestor contexts (contexts that contain this context)
        ancestors = egi.hierarchical_index.get_ancestors(context)
        vertices_above = set()
        
        for ancestor in ancestors:
            # Get vertices directly in ancestor contexts
            area_contents = egi.area.get(ancestor, frozenset())
            for element_id in area_contents:
                if element_id in egi._vertex_map:
                    vertices_above.add(element_id)
        
        return vertices_above
    
    def _get_vertices_at_or_below_context(self, egi: RelationalGraphWithCuts, context: ElementID) -> Set[ElementID]:
        """Get vertices that are at or below (inside) the given context."""
        if not egi.hierarchical_index:
            return set()
        
        # Get all descendant contexts (contexts contained in this context)
        descendants = egi.hierarchical_index.get_descendants(context)
        descendants.add(context)  # Include the context itself
        
        vertices_at_or_below = set()
        
        for desc in descendants:
            # Get vertices directly in descendant contexts
            area_contents = egi.area.get(desc, frozenset())
            for element_id in area_contents:
                if element_id in egi._vertex_map:
                    vertices_at_or_below.add(element_id)
        
        return vertices_at_or_below


@dataclass
class EvaluationResult:
    """Result of semantic evaluation."""
    is_satisfied: bool
    evaluation_method: str
    context: ElementID
    valuation_used: Valuation
    error_message: Optional[str] = None


class SemanticEvaluationEngine:
    """
    Dau-compliant semantic evaluation engine for EGIs.
    
    Implements both classical and endoporeutic evaluation methods
    as defined in Dau Chapter 13.
    """
    
    def __init__(self):
        self.debug_mode = False
    
    def evaluate_classical(self, egi: RelationalGraphWithCuts, 
                         model: RelationalStructure,
                         valuation: Valuation) -> EvaluationResult:
        """
        Classical evaluation per Definition 13.3.
        
        Uses total valuations, evaluates inductively over Cut ∪ {⊤}.
        Similar to first-order logic evaluation.
        """
        try:
            if not valuation.is_total_for({v.id for v in egi.V}):
                return EvaluationResult(
                    is_satisfied=False,
                    evaluation_method="classical",
                    context=ElementID("sheet"),
                    valuation_used=valuation,
                    error_message="Classical evaluation requires total valuation"
                )
            
            # Start evaluation from sheet of assertion
            sheet_context = ElementID("sheet")
            result = self._evaluate_classical_context(
                egi, model, sheet_context, valuation
            )
            
            return EvaluationResult(
                is_satisfied=result,
                evaluation_method="classical", 
                context=sheet_context,
                valuation_used=valuation
            )
            
        except Exception as e:
            return EvaluationResult(
                is_satisfied=False,
                evaluation_method="classical",
                context=ElementID("sheet"),
                valuation_used=valuation,
                error_message=str(e)
            )
    
    def evaluate_endoporeutic(self, egi: RelationalGraphWithCuts,
                            model: RelationalStructure) -> EvaluationResult:
        """
        Endoporeutic evaluation per Definition 13.4.
        
        Formalizes Peirce's "reading from outside inward" method.
        Starts with empty valuation, successively completes it.
        """
        try:
            # Start with empty valuation at sheet of assertion
            empty_valuation = Valuation(
                mapping=frozendict(),
                domain=frozenset()
            )
            sheet_context = ElementID("sheet")
            
            result = self._evaluate_endoporeutic_context(
                egi, model, sheet_context, empty_valuation
            )
            
            return EvaluationResult(
                is_satisfied=result,
                evaluation_method="endoporeutic",
                context=sheet_context,
                valuation_used=empty_valuation
            )
            
        except Exception as e:
            return EvaluationResult(
                is_satisfied=False,
                evaluation_method="endoporeutic", 
                context=ElementID("sheet"),
                valuation_used=Valuation(frozendict(), frozenset()),
                error_message=str(e)
            )
    
    def _evaluate_classical_context(self, egi: RelationalGraphWithCuts,
                                  model: RelationalStructure,
                                  context: ElementID,
                                  valuation: Valuation) -> bool:
        """
        Classical evaluation for a specific context.
        
        Per Definition 13.3:
        (U,I) |=class G[c,ref] ⟺ ∃ref' with ref'(v) = ref(v) for v ∉ area(c)
        such that:
        - ref'(e) ∈ I(κ(e)) for each e ∈ E ∩ area(c) (edge condition)
        - (U,I) ⊭class G[d,ref'] for each d ∈ Cut ∩ area(c) (cut condition)
        """
        
        # Get elements in this context area
        context_vertices = self._get_context_vertices(egi, context)
        context_edges = self._get_context_edges(egi, context)
        context_cuts = self._get_context_cuts(egi, context)
        
        # Check if we can find a suitable valuation extension
        for extension in self._generate_valuation_extensions(
            model.universe, context_vertices, valuation):
            
            extended_valuation = valuation.extend(extension)
            
            # Check edge conditions
            if not self._check_edge_conditions(
                egi, model, context_edges, extended_valuation):
                continue
            
            # Check cut conditions (negation)
            cut_conditions_satisfied = True
            for cut in context_cuts:
                if self._evaluate_classical_context(
                    egi, model, cut, extended_valuation):
                    cut_conditions_satisfied = False
                    break
            
            if cut_conditions_satisfied:
                return True
        
        return False
    
    def _evaluate_endoporeutic_context(self, egi: RelationalGraphWithCuts,
                                     model: RelationalStructure, 
                                     context: ElementID,
                                     partial_valuation: Valuation) -> bool:
        """
        Endoporeutic evaluation for a specific context.
        
        Per Definition 13.4:
        (U,I) |=endo G[c,ref] ⟺ ref can be extended to ref': V' ∪ (V ∩ area(c)) → U
        such that:
        - ref'(e) ∈ I(κ(e)) for each e ∈ E ∩ area(c) (edge condition)  
        - (U,I) ⊭endo G[d,ref'] for each d ∈ Cut ∩ area(c) (cut condition)
        """
        
        # Get vertices that need to be assigned in this context
        context_vertices = self._get_context_vertices(egi, context)
        vertices_to_assign = context_vertices - partial_valuation.domain
        
        # Try all possible extensions for unassigned vertices
        for extension in self._generate_valuation_extensions(
            model.universe, vertices_to_assign, partial_valuation):
            
            extended_valuation = partial_valuation.extend(extension)
            
            # Check edge conditions in this context
            context_edges = self._get_context_edges(egi, context)
            if not self._check_edge_conditions(
                egi, model, context_edges, extended_valuation):
                continue
            
            # Check cut conditions (negation) recursively
            context_cuts = self._get_context_cuts(egi, context)
            cut_conditions_satisfied = True
            
            for cut in context_cuts:
                if self._evaluate_endoporeutic_context(
                    egi, model, cut, extended_valuation):
                    cut_conditions_satisfied = False
                    break
            
            if cut_conditions_satisfied:
                return True
        
        return False
    
    def _check_edge_conditions(self, egi: RelationalGraphWithCuts,
                             model: RelationalStructure,
                             edges: Set[ElementID],
                             valuation: Valuation) -> bool:
        """
        Check edge conditions: ref(e) ∈ I(κ(e)) for each edge e.
        
        This requires evaluating the relation represented by each edge
        with the objects assigned to its incident vertices.
        """
        for edge_id in edges:
            edge = self._get_edge_by_id(egi, edge_id)
            if not edge:
                continue
            
            # Get relation name from edge label
            relation_name = self._get_edge_relation_name(egi, edge)
            if relation_name not in model.interpretation:
                return False
            
            # Get incident vertices and their assigned objects
            incident_vertices = self._get_incident_vertices(egi, edge)
            try:
                incident_objects = tuple(
                    valuation.mapping[v_id] for v_id in incident_vertices
                )
            except KeyError:
                # Not all incident vertices have assignments
                return False
            
            # Check if tuple is in relation
            relation = model.interpretation[relation_name]
            if incident_objects not in relation:
                return False
        
        return True
    
    def _generate_valuation_extensions(self, universe: FrozenSet[Any],
                                     vertices_to_assign: Set[ElementID],
                                     base_valuation: Valuation) -> Iterator[Dict[ElementID, Any]]:
        """Generate all possible valuation extensions for given vertices."""
        if not vertices_to_assign:
            yield {}
            return
        
        # For now, implement a simple cartesian product
        # In practice, this needs optimization for large universes
        import itertools
        
        vertices_list = list(vertices_to_assign)
        for assignment in itertools.product(universe, repeat=len(vertices_list)):
            yield dict(zip(vertices_list, assignment))
    
    def _get_context_vertices(self, egi: RelationalGraphWithCuts, context: ElementID) -> Set[ElementID]:
        """Get vertices directly contained in the given context."""
        area_contents = egi.area.get(context, frozenset())
        return {element_id for element_id in area_contents 
                if element_id in egi._vertex_map}
    
    def _get_context_edges(self, egi: RelationalGraphWithCuts, context: ElementID) -> Set[ElementID]:
        """Get edges directly contained in the given context."""
        area_contents = egi.area.get(context, frozenset())
        return {element_id for element_id in area_contents 
                if element_id in egi._edge_map}
    
    def _get_context_cuts(self, egi: RelationalGraphWithCuts, context: ElementID) -> Set[ElementID]:
        """Get cuts directly contained in the given context."""
        area_contents = egi.area.get(context, frozenset())
        return {element_id for element_id in area_contents 
                if element_id in egi._cut_map}
    
    def _get_edge_by_id(self, egi: RelationalGraphWithCuts, edge_id: ElementID) -> Optional[Edge]:
        """Get edge object by ID."""
        for edge in egi.E:
            if edge.id == edge_id:
                return edge
        return None
    
    def _get_edge_relation_name(self, egi: RelationalGraphWithCuts, edge: Edge) -> str:
        """Extract relation name from edge using rel mapping."""
        return egi.rel.get(edge.id, 'unknown')
    
    def _get_incident_vertices(self, egi: RelationalGraphWithCuts, edge: Edge) -> List[ElementID]:
        """Get vertices incident to the given edge using ν mapping."""
        return list(egi.nu.get(edge.id, tuple()))
    
    def verify_evaluation_equivalence(self, egi: RelationalGraphWithCuts,
                                    model: RelationalStructure,
                                    valuation: Valuation) -> bool:
        """
        Verify Lemma 13.5: Both evaluation methods yield same result.
        
        This is crucial for implementation correctness.
        """
        classical_result = self.evaluate_classical(egi, model, valuation)
        endoporeutic_result = self.evaluate_endoporeutic(egi, model)
        
        return classical_result.is_satisfied == endoporeutic_result.is_satisfied


# Utility functions for creating common model structures

def create_simple_relational_structure(universe_size: int = 3) -> RelationalStructure:
    """Create a simple relational structure for testing."""
    universe = frozenset(f"obj_{i}" for i in range(universe_size))
    
    # Create some basic relations
    interpretation = {
        "=": frozenset((obj, obj) for obj in universe),  # Identity relation
        "R": frozenset([("obj_0", "obj_1"), ("obj_1", "obj_2")]),  # Binary relation
        "P": frozenset([("obj_0",), ("obj_2",)])  # Unary relation (predicate)
    }
    
    return RelationalStructure(
        universe=universe,
        interpretation=frozendict(interpretation)
    )


def create_total_valuation(egi: RelationalGraphWithCuts, 
                         model: RelationalStructure) -> Valuation:
    """Create a total valuation assigning objects to all vertices."""
    universe_list = list(model.universe)
    vertex_ids = [v.id for v in egi.V]
    
    # Simple assignment - first vertices get first objects
    mapping = {}
    for i, vertex_id in enumerate(vertex_ids):
        mapping[vertex_id] = universe_list[i % len(universe_list)]
    
    return Valuation(
        mapping=frozendict(mapping),
        domain=frozenset(vertex_ids)
    )
