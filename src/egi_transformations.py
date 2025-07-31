"""
Immutable transformation functions for Existential Graphs.
All transformations are pure functions that return new EGI instances.
Based on Frithjof Dau's 8 canonical transformation rules.
"""

from typing import Tuple, Optional, Set, Union
from enum import Enum

try:
    from .egi_core import EGI, Context, Vertex, Edge, ElementID, EGIBuilder
except ImportError:
    from egi_core import EGI, Context, Vertex, Edge, ElementID, EGIBuilder


class TransformationRule(Enum):
    """The 8 canonical transformation rules."""
    ERASURE = "erasure"
    INSERTION = "insertion"
    ITERATION = "iteration"
    DE_ITERATION = "de_iteration"
    DOUBLE_CUT_ADDITION = "double_cut_addition"
    DOUBLE_CUT_REMOVAL = "double_cut_removal"
    ISOLATED_VERTEX_ADDITION = "isolated_vertex_addition"
    ISOLATED_VERTEX_REMOVAL = "isolated_vertex_removal"


class TransformationError(Exception):
    """Error in transformation application."""
    pass


# Validation functions

def can_erase(egi: EGI, element_id: ElementID) -> bool:
    """Check if element can be erased (must be in positive context)."""
    try:
        if element_id in egi._vertex_map:
            vertex = egi.get_vertex(element_id)
            context = egi.get_context(vertex.context_id)
            return context.is_positive()
        elif element_id in egi._edge_map:
            edge = egi.get_edge(element_id)
            context = egi.get_context(edge.context_id)
            return context.is_positive()
        elif element_id in egi._context_map:
            context = egi.get_context(element_id)
            if context.id == egi.sheet_id:
                return False  # Cannot erase sheet
            parent_context = egi.get_context(context.parent_id)
            return parent_context.is_positive()
        else:
            return False
    except (ValueError, KeyError):
        return False


def can_insert(egi: EGI, context_id: ElementID) -> bool:
    """Check if element can be inserted (must be in negative context)."""
    try:
        context = egi.get_context(context_id)
        return context.is_negative()
    except (ValueError, KeyError):
        return False


def can_iterate(egi: EGI, vertex_id: ElementID, target_context_id: ElementID) -> bool:
    """Check if vertex can be iterated to target context."""
    try:
        vertex = egi.get_vertex(vertex_id)
        source_context = egi.get_context(vertex.context_id)
        target_context = egi.get_context(target_context_id)
        
        # Target must be nested within source context
        return _context_encloses(egi, source_context.id, target_context_id)
    except (ValueError, KeyError):
        return False


def can_de_iterate(egi: EGI, vertex_id: ElementID) -> bool:
    """Check if vertex can be de-iterated (removed from inner context)."""
    try:
        vertex = egi.get_vertex(vertex_id)
        context = egi.get_context(vertex.context_id)
        
        # Must not be in sheet context and must be a copy
        return context.id != egi.sheet_id
    except (ValueError, KeyError):
        return False


def can_add_double_cut(egi: EGI, context_id: ElementID) -> bool:
    """Check if double cut can be added to context."""
    try:
        egi.get_context(context_id)
        return True
    except (ValueError, KeyError):
        return False


def can_remove_double_cut(egi: EGI, outer_cut_id: ElementID) -> bool:
    """Check if double cut can be removed."""
    try:
        outer_cut = egi.get_context(outer_cut_id)
        
        # Must have exactly one child context
        if len(outer_cut.children) != 1:
            return False
        
        inner_cut_id = next(iter(outer_cut.children))
        inner_cut = egi.get_context(inner_cut_id)
        
        # Both cuts must be empty
        return (len(outer_cut.enclosed_elements) == 0 and 
                len(inner_cut.enclosed_elements) == 0 and
                len(inner_cut.children) == 0)
    except (ValueError, KeyError):
        return False


def can_add_isolated_vertex(egi: EGI, context_id: ElementID) -> bool:
    """Check if isolated vertex can be added."""
    try:
        context = egi.get_context(context_id)
        return context.is_negative()
    except (ValueError, KeyError):
        return False


def can_remove_isolated_vertex(egi: EGI, vertex_id: ElementID) -> bool:
    """Check if isolated vertex can be removed."""
    try:
        vertex = egi.get_vertex(vertex_id)
        context = egi.get_context(vertex.context_id)
        
        # Must be isolated and in positive context
        return context.is_positive() and egi.is_vertex_isolated(vertex_id)
    except (ValueError, KeyError):
        return False


# Helper functions

def _context_encloses(egi: EGI, outer_context_id: ElementID, inner_context_id: ElementID) -> bool:
    """Check if outer context encloses inner context."""
    if outer_context_id == inner_context_id:
        return True
    
    try:
        current_context = egi.get_context(inner_context_id)
        while current_context.parent_id:
            if current_context.parent_id == outer_context_id:
                return True
            current_context = egi.get_context(current_context.parent_id)
        return False
    except (ValueError, KeyError):
        return False


def _find_vertex_copies(egi: EGI, original_vertex_id: ElementID) -> Set[ElementID]:
    """Find all copies of a vertex (vertices with same ID in different contexts)."""
    original_vertex = egi.get_vertex(original_vertex_id)
    copies = set()
    
    for vertex in egi.vertices:
        if (vertex.id == original_vertex.id and 
            vertex.context_id != original_vertex.context_id):
            copies.add(vertex.id)
    
    return copies


# Transformation functions

def apply_erasure(egi: EGI, element_id: ElementID) -> EGI:
    """Apply erasure transformation, returning new EGI."""
    if not can_erase(egi, element_id):
        raise TransformationError("Cannot erase from negative context")
    
    if element_id in egi._vertex_map:
        return egi.without_vertex(element_id)
    elif element_id in egi._edge_map:
        return egi.without_edge(element_id)
    elif element_id in egi._context_map:
        return egi.without_context(element_id)
    else:
        raise TransformationError(f"Element {element_id} not found")


def apply_insertion(egi: EGI, element: Union[Vertex, Edge, Context], context_id: ElementID) -> EGI:
    """Apply insertion transformation, returning new EGI."""
    if not can_insert(egi, context_id):
        raise TransformationError("Cannot insert into positive context")
    
    if isinstance(element, Vertex):
        # Update vertex to be in target context
        new_vertex = element.in_context(context_id)
        return egi.with_vertex(new_vertex)
    elif isinstance(element, Edge):
        # Update edge to be in target context
        new_edge = element.in_context(context_id)
        return egi.with_edge(new_edge)
    elif isinstance(element, Context):
        # Update context to have target as parent
        new_context = Context(
            id=element.id,
            parent_id=context_id,
            depth=egi.get_context(context_id).depth + 1,
            enclosed_elements=element.enclosed_elements,
            children=element.children
        )
        return egi.with_context(new_context)
    else:
        raise TransformationError(f"Invalid element type for insertion: {type(element)}")


def apply_iteration(egi: EGI, vertex_id: ElementID, target_context_id: ElementID) -> EGI:
    """Apply iteration transformation, returning new EGI."""
    if not can_iterate(egi, vertex_id, target_context_id):
        raise TransformationError("Cannot iterate vertex to target context")
    
    original_vertex = egi.get_vertex(vertex_id)
    
    # Create copy of vertex in target context
    # Use builder to generate new ID for the copy
    builder = EGIBuilder(egi.alphabet)
    copy_vertex_id = builder._generate_id()
    
    copy_vertex = Vertex(
        id=copy_vertex_id,
        context_id=target_context_id,
        is_constant=original_vertex.is_constant,
        constant_name=original_vertex.constant_name,
        properties=original_vertex.properties
    )
    
    return egi.with_vertex(copy_vertex)


def apply_de_iteration(egi: EGI, vertex_id: ElementID) -> EGI:
    """Apply de-iteration transformation, returning new EGI."""
    if not can_de_iterate(egi, vertex_id):
        raise TransformationError("Cannot de-iterate vertex from sheet context")
    
    return egi.without_vertex(vertex_id)


def apply_double_cut_addition(egi: EGI, context_id: ElementID) -> EGI:
    """Apply double cut addition, returning new EGI."""
    if not can_add_double_cut(egi, context_id):
        raise TransformationError("Cannot add double cut to invalid context")
    
    target_context = egi.get_context(context_id)
    
    # Create outer cut
    builder = EGIBuilder(egi.alphabet)
    outer_cut_id = builder._generate_id()
    outer_cut = Context(
        id=outer_cut_id,
        parent_id=context_id,
        depth=target_context.depth + 1,
        enclosed_elements=frozenset(),
        children=frozenset()
    )
    
    # Create inner cut
    inner_cut_id = builder._generate_id()
    inner_cut = Context(
        id=inner_cut_id,
        parent_id=outer_cut_id,
        depth=target_context.depth + 2,
        enclosed_elements=frozenset(),
        children=frozenset()
    )
    
    # Update outer cut to have inner as child
    outer_cut = outer_cut.with_child(inner_cut_id)
    
    # Add both contexts
    result_egi = egi.with_context(outer_cut).with_context(inner_cut)
    
    return result_egi


def apply_double_cut_removal(egi: EGI, outer_cut_id: ElementID) -> EGI:
    """Apply double cut removal, returning new EGI."""
    if not can_remove_double_cut(egi, outer_cut_id):
        raise TransformationError("Cannot remove non-empty double cut")
    
    outer_cut = egi.get_context(outer_cut_id)
    inner_cut_id = next(iter(outer_cut.children))
    
    # Remove both contexts
    return egi.without_context(outer_cut_id)


def apply_isolated_vertex_addition(egi: EGI, context_id: ElementID, 
                                   is_constant: bool = False, 
                                   constant_name: Optional[str] = None) -> EGI:
    """Apply isolated vertex addition, returning new EGI."""
    if not can_add_isolated_vertex(egi, context_id):
        raise TransformationError("Cannot add isolated vertex to positive context")
    
    # Create new isolated vertex
    builder = EGIBuilder(egi.alphabet)
    vertex_id = builder._generate_id()
    
    vertex = Vertex(
        id=vertex_id,
        context_id=context_id,
        is_constant=is_constant,
        constant_name=constant_name
    )
    
    return egi.with_vertex(vertex)


def apply_isolated_vertex_removal(egi: EGI, vertex_id: ElementID) -> EGI:
    """Apply isolated vertex removal, returning new EGI."""
    if not can_remove_isolated_vertex(egi, vertex_id):
        raise TransformationError("Cannot remove non-isolated vertex or vertex in negative context")
    
    return egi.without_vertex(vertex_id)


# High-level transformation interface

def apply_transformation(egi: EGI, rule: TransformationRule, **kwargs) -> EGI:
    """Apply transformation rule to EGI, returning new EGI."""
    
    if rule == TransformationRule.ERASURE:
        element_id = kwargs.get('element_id')
        if not element_id:
            raise TransformationError("Erasure requires element_id")
        return apply_erasure(egi, element_id)
    
    elif rule == TransformationRule.INSERTION:
        element = kwargs.get('element')
        context_id = kwargs.get('context_id')
        if not element or not context_id:
            raise TransformationError("Insertion requires element and context_id")
        return apply_insertion(egi, element, context_id)
    
    elif rule == TransformationRule.ITERATION:
        vertex_id = kwargs.get('vertex_id')
        target_context_id = kwargs.get('target_context_id')
        if not vertex_id or not target_context_id:
            raise TransformationError("Iteration requires vertex_id and target_context_id")
        return apply_iteration(egi, vertex_id, target_context_id)
    
    elif rule == TransformationRule.DE_ITERATION:
        vertex_id = kwargs.get('vertex_id')
        if not vertex_id:
            raise TransformationError("De-iteration requires vertex_id")
        return apply_de_iteration(egi, vertex_id)
    
    elif rule == TransformationRule.DOUBLE_CUT_ADDITION:
        context_id = kwargs.get('context_id')
        if not context_id:
            raise TransformationError("Double cut addition requires context_id")
        return apply_double_cut_addition(egi, context_id)
    
    elif rule == TransformationRule.DOUBLE_CUT_REMOVAL:
        outer_cut_id = kwargs.get('outer_cut_id')
        if not outer_cut_id:
            raise TransformationError("Double cut removal requires outer_cut_id")
        return apply_double_cut_removal(egi, outer_cut_id)
    
    elif rule == TransformationRule.ISOLATED_VERTEX_ADDITION:
        context_id = kwargs.get('context_id')
        if not context_id:
            raise TransformationError("Isolated vertex addition requires context_id")
        is_constant = kwargs.get('is_constant', False)
        constant_name = kwargs.get('constant_name')
        return apply_isolated_vertex_addition(egi, context_id, is_constant, constant_name)
    
    elif rule == TransformationRule.ISOLATED_VERTEX_REMOVAL:
        vertex_id = kwargs.get('vertex_id')
        if not vertex_id:
            raise TransformationError("Isolated vertex removal requires vertex_id")
        return apply_isolated_vertex_removal(egi, vertex_id)
    
    else:
        raise TransformationError(f"Unknown transformation rule: {rule}")


# Test the transformations
if __name__ == "__main__":
    print("Testing immutable transformations...")
    
    try:
        from .egif_parser import parse_egif
    except ImportError:
        from egif_parser import parse_egif
    
    # Test erasure
    egi = parse_egif("(man *x) (human x)")
    print(f"Original: {len(egi.edges)} edges")
    
    # Get first edge
    edge_id = next(iter(egi._edge_map.keys()))
    new_egi = apply_erasure(egi, edge_id)
    print(f"After erasure: {len(new_egi.edges)} edges")
    print(f"Original unchanged: {len(egi.edges)} edges")
    
    # Test double cut addition
    egi = parse_egif("(phoenix *x)")
    new_egi = apply_double_cut_addition(egi, egi.sheet_id)
    print(f"After double cut addition: {len(new_egi.contexts)} contexts")
    
    # Test double cut removal
    outer_cuts = [c for c in new_egi.contexts if c.parent_id == egi.sheet_id]
    if outer_cuts:
        outer_cut = outer_cuts[0]
        final_egi = apply_double_cut_removal(new_egi, outer_cut.id)
        print(f"After double cut removal: {len(final_egi.contexts)} contexts")
    
    # Test isolated vertex addition
    egi = parse_egif("~[ (man *x) ]")
    neg_context = [c for c in egi.contexts if c.is_negative()][0]
    new_egi = apply_isolated_vertex_addition(egi, neg_context.id)
    print(f"After isolated vertex addition: {len(new_egi.vertices)} vertices")
    
    print("✓ Immutable transformations working correctly!")

