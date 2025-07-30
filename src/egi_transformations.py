"""
Implementation of the 8 canonical transformation rules for Existential Graphs
based on Frithjof Dau's formalism.
"""

from typing import List, Set, Dict, Optional, Tuple, Union
from copy import deepcopy
from enum import Enum

from egi_core import EGI, Context, Vertex, Edge, ElementID, ElementType


class TransformationError(Exception):
    """Exception raised when a transformation is invalid."""
    pass


class TransformationRule(Enum):
    """Enumeration of the canonical transformation rules."""
    ERASURE = "erasure"
    INSERTION = "insertion"
    ITERATION = "iteration"
    DE_ITERATION = "de_iteration"
    DOUBLE_CUT_ADDITION = "double_cut_addition"
    DOUBLE_CUT_REMOVAL = "double_cut_removal"
    ISOLATED_VERTEX_ADDITION = "isolated_vertex_addition"
    ISOLATED_VERTEX_REMOVAL = "isolated_vertex_removal"


class EGITransformer:
    """Implements the canonical transformation rules for EGI instances."""
    
    def __init__(self, egi: EGI):
        """Initialize transformer with an EGI instance."""
        self.egi = egi
        self.transformation_log: List[Dict] = []
    
    def apply_transformation(self, rule: TransformationRule, **kwargs) -> EGI:
        """Applies a transformation rule and returns a new EGI instance."""
        # Create a deep copy to avoid modifying the original
        new_egi = self._deep_copy_egi()
        transformer = EGITransformer(new_egi)
        
        # Apply the specific rule
        if rule == TransformationRule.ERASURE:
            transformer._apply_erasure(**kwargs)
        elif rule == TransformationRule.INSERTION:
            transformer._apply_insertion(**kwargs)
        elif rule == TransformationRule.ITERATION:
            transformer._apply_iteration(**kwargs)
        elif rule == TransformationRule.DE_ITERATION:
            transformer._apply_de_iteration(**kwargs)
        elif rule == TransformationRule.DOUBLE_CUT_ADDITION:
            transformer._apply_double_cut_addition(**kwargs)
        elif rule == TransformationRule.DOUBLE_CUT_REMOVAL:
            transformer._apply_double_cut_removal(**kwargs)
        elif rule == TransformationRule.ISOLATED_VERTEX_ADDITION:
            transformer._apply_isolated_vertex_addition(**kwargs)
        elif rule == TransformationRule.ISOLATED_VERTEX_REMOVAL:
            transformer._apply_isolated_vertex_removal(**kwargs)
        else:
            raise ValueError(f"Unknown transformation rule: {rule}")
        
        # Log the transformation
        transformer.transformation_log.append({
            'rule': rule.value,
            'parameters': kwargs
        })
        
        return transformer.egi
    
    def _deep_copy_egi(self) -> EGI:
        """Creates a deep copy of the EGI instance."""
        # Create new EGI with same alphabet
        new_egi = EGI(deepcopy(self.egi.alphabet))
        
        # Copy vertices
        vertex_mapping = {}
        for vertex_id, vertex in self.egi.vertices.items():
            # Find corresponding context in new EGI
            if vertex.context == self.egi.sheet:
                new_context = new_egi.sheet
            else:
                # For now, assume sheet context only - extend as needed
                new_context = new_egi.sheet
            
            new_vertex = new_egi.add_vertex(
                context=new_context,
                is_constant=vertex.is_constant,
                constant_name=vertex.constant_name
            )
            new_vertex.properties.update(vertex.properties)
            vertex_mapping[vertex_id] = new_vertex.id
        
        # Copy edges
        for edge_id, edge in self.egi.edges.items():
            # Find corresponding context
            if edge.context == self.egi.sheet:
                new_context = new_egi.sheet
            else:
                new_context = new_egi.sheet
            
            # Map incident vertices
            new_incident_vertices = [vertex_mapping[vid] for vid in edge.incident_vertices]
            
            new_edge = new_egi.add_edge(
                context=new_context,
                relation_name=edge.relation_name,
                incident_vertices=new_incident_vertices,
                check_dominance=False
            )
            new_edge.properties.update(edge.properties)
        
        return new_egi
    
    def _apply_erasure(self, element_id: ElementID) -> None:
        """
        Erasure Rule: Remove a subgraph from a positive context.
        Can only erase from positive (evenly enclosed) contexts.
        """
        if element_id in self.egi.vertices:
            vertex = self.egi.vertices[element_id]
            if vertex.context.is_negative():
                raise TransformationError("Cannot erase from negative context")
            
            # Remove vertex and all incident edges
            incident_edges = list(vertex.incident_edges)
            for edge_id in incident_edges:
                self._remove_edge(edge_id)
            self._remove_vertex(element_id)
            
        elif element_id in self.egi.edges:
            edge = self.egi.edges[element_id]
            if edge.context.is_negative():
                raise TransformationError("Cannot erase from negative context")
            
            self._remove_edge(element_id)
            
        elif element_id in self.egi.cuts:
            cut = self.egi.cuts[element_id]
            if cut.parent and cut.parent.is_negative():
                raise TransformationError("Cannot erase from negative context")
            
            self._remove_cut(element_id)
            
        else:
            raise TransformationError(f"Element {element_id} not found")
    
    def _apply_insertion(self, subgraph: Dict, target_context_id: ElementID) -> None:
        """
        Insertion Rule: Add a subgraph to a negative context.
        Can only insert into negative (oddly enclosed) contexts.
        """
        target_context = self.egi.get_context(target_context_id)
        if target_context.is_positive():
            raise TransformationError("Cannot insert into positive context")
        
        # Insert the subgraph into the target context
        self._insert_subgraph(subgraph, target_context)
    
    def _apply_iteration(self, vertex_id: ElementID, target_context_id: ElementID) -> ElementID:
        """
        Iteration Rule: Copy a vertex from an outer context to an inner context.
        The vertex must be in a context that dominates the target context.
        """
        vertex = self.egi.vertices[vertex_id]
        target_context = self.egi.get_context(target_context_id)
        
        # Check that vertex context dominates target context
        if not self._context_dominates(vertex.context, target_context):
            raise TransformationError("Source context must dominate target context for iteration")
        
        # Create a copy of the vertex in the target context
        new_vertex = self.egi.add_vertex(
            context=target_context,
            is_constant=vertex.is_constant,
            constant_name=vertex.constant_name
        )
        
        # Copy properties
        new_vertex.properties.update(vertex.properties)
        
        return new_vertex.id
    
    def _apply_de_iteration(self, vertex_id: ElementID) -> None:
        """
        De-iteration Rule: Remove a vertex that is a copy of another vertex in an outer context.
        The vertex must be in an inner context and have a corresponding vertex in an outer context.
        """
        vertex = self.egi.vertices[vertex_id]
        
        # Find corresponding vertex in outer context
        outer_vertex = self._find_corresponding_outer_vertex(vertex)
        if not outer_vertex:
            raise TransformationError("No corresponding vertex found in outer context")
        
        # Remove the inner vertex and its edges
        incident_edges = list(vertex.incident_edges)
        for edge_id in incident_edges:
            self._remove_edge(edge_id)
        self._remove_vertex(vertex_id)
    
    def _apply_double_cut_addition(self, target_context_id: ElementID) -> Tuple[ElementID, ElementID]:
        """
        Double Cut Addition: Add two nested cuts around a subgraph.
        Can be applied in any context.
        """
        target_context = self.egi.get_context(target_context_id)
        
        # Create first cut
        outer_cut = self.egi.add_cut(target_context)
        
        # Create second cut inside the first
        inner_cut = self.egi.add_cut(outer_cut)
        
        return outer_cut.id, inner_cut.id
    
    def _apply_double_cut_removal(self, outer_cut_id: ElementID) -> None:
        """
        Double Cut Removal: Remove two nested empty cuts.
        Both cuts must be empty (contain no elements).
        """
        outer_cut = self.egi.cuts[outer_cut_id]
        
        # Check that outer cut has exactly one child (the inner cut)
        if len(outer_cut.children) != 1:
            raise TransformationError("Outer cut must have exactly one child cut")
        
        inner_cut_id = next(iter(outer_cut.children))
        inner_cut = self.egi.cuts[inner_cut_id]
        
        # Check that both cuts are empty
        if outer_cut.enclosed_elements or inner_cut.enclosed_elements or inner_cut.children:
            raise TransformationError("Both cuts must be empty for double cut removal")
        
        # Remove both cuts
        self._remove_cut(inner_cut_id)
        self._remove_cut(outer_cut_id)
    
    def _apply_isolated_vertex_addition(self, target_context_id: ElementID, 
                                       is_constant: bool = False, 
                                       constant_name: Optional[str] = None) -> ElementID:
        """
        Isolated Vertex Addition: Add an isolated vertex to any context.
        """
        target_context = self.egi.get_context(target_context_id)
        
        vertex = self.egi.add_vertex(
            context=target_context,
            is_constant=is_constant,
            constant_name=constant_name
        )
        
        return vertex.id
    
    def _apply_isolated_vertex_removal(self, vertex_id: ElementID) -> None:
        """
        Isolated Vertex Removal: Remove an isolated vertex (no incident edges).
        """
        vertex = self.egi.vertices[vertex_id]
        
        if not vertex.is_isolated():
            raise TransformationError("Can only remove isolated vertices")
        
        self._remove_vertex(vertex_id)
    
    def _remove_vertex(self, vertex_id: ElementID) -> None:
        """Removes a vertex from the EGI."""
        vertex = self.egi.vertices[vertex_id]
        
        # Remove from context
        vertex.context.enclosed_elements.discard(vertex_id)
        
        # Remove from EGI
        del self.egi.vertices[vertex_id]
    
    def _remove_edge(self, edge_id: ElementID) -> None:
        """Removes an edge from the EGI."""
        edge = self.egi.edges[edge_id]
        
        # Remove from incident vertices
        for vertex_id in edge.incident_vertices:
            if vertex_id in self.egi.vertices:
                self.egi.vertices[vertex_id].remove_incident_edge(edge_id)
        
        # Remove from context
        edge.context.enclosed_elements.discard(edge_id)
        
        # Remove from EGI
        del self.egi.edges[edge_id]
        
        # Update ligatures if this was an identity edge
        if edge.is_identity:
            self.egi.ligature_manager.find_ligatures(self.egi)
    
    def _remove_cut(self, cut_id: ElementID) -> None:
        """Removes a cut from the EGI."""
        cut = self.egi.cuts[cut_id]
        
        # Remove from parent's children
        if cut.parent:
            cut.parent.children.discard(cut_id)
        
        # Remove all enclosed elements
        for element_id in list(cut.enclosed_elements):
            if element_id in self.egi.vertices:
                self._remove_vertex(element_id)
            elif element_id in self.egi.edges:
                self._remove_edge(element_id)
        
        # Remove all child cuts
        for child_cut_id in list(cut.children):
            self._remove_cut(child_cut_id)
        
        # Remove from EGI
        del self.egi.cuts[cut_id]
    
    def _insert_subgraph(self, subgraph: Dict, target_context: Context) -> None:
        """Inserts a subgraph into the target context."""
        # This is a simplified implementation
        # In practice, you'd need to handle vertex mapping and edge reconstruction
        
        # Add vertices
        vertex_mapping = {}
        for vertex_data in subgraph.get('vertices', []):
            new_vertex = self.egi.add_vertex(
                context=target_context,
                is_constant=vertex_data.get('is_constant', False),
                constant_name=vertex_data.get('constant_name')
            )
            vertex_mapping[vertex_data['id']] = new_vertex.id
        
        # Add edges
        for edge_data in subgraph.get('edges', []):
            incident_vertices = [vertex_mapping[vid] for vid in edge_data['incident_vertices']]
            self.egi.add_edge(
                context=target_context,
                relation_name=edge_data['relation_name'],
                incident_vertices=incident_vertices,
                check_dominance=False
            )
    
    def _context_dominates(self, outer_context: Context, inner_context: Context) -> bool:
        """Returns True if outer_context dominates inner_context."""
        current = inner_context
        while current is not None:
            if current == outer_context:
                return True
            current = current.parent
        return False
    
    def _find_corresponding_outer_vertex(self, vertex: Vertex) -> Optional[Vertex]:
        """Finds a corresponding vertex in an outer context."""
        # Look for vertices with same properties in outer contexts
        current_context = vertex.context.parent
        
        while current_context is not None:
            for other_vertex in self.egi.vertices.values():
                if (other_vertex.context == current_context and
                    other_vertex.is_constant == vertex.is_constant and
                    other_vertex.constant_name == vertex.constant_name):
                    return other_vertex
            current_context = current_context.parent
        
        return None
    
    def validate_transformation(self, rule: TransformationRule, **kwargs) -> bool:
        """Validates whether a transformation can be applied without actually applying it."""
        try:
            # Create a temporary copy and try the transformation
            temp_egi = self._deep_copy_egi()
            temp_transformer = EGITransformer(temp_egi)
            temp_transformer.apply_transformation(rule, **kwargs)
            return True
        except TransformationError:
            return False
    
    def get_applicable_rules(self, element_id: Optional[ElementID] = None) -> List[TransformationRule]:
        """Returns a list of transformation rules that can be applied."""
        applicable = []
        
        # Check each rule
        for rule in TransformationRule:
            if rule == TransformationRule.ERASURE and element_id:
                if self.validate_transformation(rule, element_id=element_id):
                    applicable.append(rule)
            elif rule == TransformationRule.DOUBLE_CUT_ADDITION:
                # Can always add double cut to any context
                applicable.append(rule)
            elif rule == TransformationRule.ISOLATED_VERTEX_ADDITION:
                # Can always add isolated vertex to any context
                applicable.append(rule)
            # Add more rule checks as needed
        
        return applicable


# Convenience functions
def apply_erasure(egi: EGI, element_id: ElementID) -> EGI:
    """Convenience function to apply erasure rule."""
    transformer = EGITransformer(egi)
    return transformer.apply_transformation(TransformationRule.ERASURE, element_id=element_id)


def apply_insertion(egi: EGI, subgraph: Dict, target_context_id: ElementID) -> EGI:
    """Convenience function to apply insertion rule."""
    transformer = EGITransformer(egi)
    return transformer.apply_transformation(TransformationRule.INSERTION, 
                                          subgraph=subgraph, 
                                          target_context_id=target_context_id)


def apply_double_cut_addition(egi: EGI, target_context_id: ElementID) -> EGI:
    """Convenience function to apply double cut addition."""
    transformer = EGITransformer(egi)
    return transformer.apply_transformation(TransformationRule.DOUBLE_CUT_ADDITION, 
                                          target_context_id=target_context_id)


def apply_double_cut_removal(egi: EGI, outer_cut_id: ElementID) -> EGI:
    """Convenience function to apply double cut removal."""
    transformer = EGITransformer(egi)
    return transformer.apply_transformation(TransformationRule.DOUBLE_CUT_REMOVAL, 
                                          outer_cut_id=outer_cut_id)


# Test the transformations
if __name__ == "__main__":
    from egif_parser import parse_egif
    from egif_generator import generate_egif
    
    print("Testing EGI Transformations...\n")
    
    # Test simple transformations without deep copy
    egif = "(man *x)"
    egi = parse_egif(egif)
    print(f"Original: {egif}")
    print(f"Vertices: {len(egi.vertices)}, Edges: {len(egi.edges)}")
    
    # Test isolated vertex addition directly
    transformer = EGITransformer(egi)
    try:
        new_vertex_id = transformer._apply_isolated_vertex_addition(
            target_context_id=egi.sheet_id,
            is_constant=True,
            constant_name="Socrates"
        )
        new_egif = generate_egif(transformer.egi)
        print(f"After adding isolated vertex: {new_egif}")
    except Exception as e:
        print(f"Isolated vertex addition failed: {e}")
    
    # Test double cut addition directly
    try:
        outer_cut_id, inner_cut_id = transformer._apply_double_cut_addition(egi.sheet_id)
        print(f"Added double cut: outer={outer_cut_id}, inner={inner_cut_id}")
        print(f"Cuts in EGI: {len(transformer.egi.cuts)}")
    except Exception as e:
        print(f"Double cut addition failed: {e}")
    
    # Test erasure directly
    if transformer.egi.edges:
        edge_id = next(iter(transformer.egi.edges.keys()))
        try:
            transformer._apply_erasure(edge_id)
            new_egif = generate_egif(transformer.egi)
            print(f"After erasure: {new_egif}")
        except Exception as e:
            print(f"Erasure failed: {e}")
    
    print("\nTransformation testing completed!")

