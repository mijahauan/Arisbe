#!/usr/bin/env python3
"""
Pipeline Contract Validation

This module provides runtime validation for all pipeline handoffs to prevent
API confusion and integration errors. Every pipeline component should use
these validators to ensure contract compliance.
"""

from typing import Any, Dict, Set, Tuple, List, Optional, Union
try:
    from typing import TypeGuard  # Python 3.10+
except Exception:  # Python 3.9 fallback
    try:
        from typing_extensions import TypeGuard  # type: ignore
    except Exception:
        # Define a no-op TypeGuard for type checking fallback
        from typing import Callable  # type: ignore
        def TypeGuard(x: Any) -> Any:  # type: ignore
            return x
from dataclasses import is_dataclass
from enum import Enum
import inspect

# API Version Management
PIPELINE_API_VERSION = "1.0.0"
COMPATIBLE_VERSIONS = ["1.0.0"]

class ContractViolationError(Exception):
    """Raised when a pipeline contract is violated."""
    pass

# Annotation System Contracts
class AnnotationType(Enum):
    """Types of annotations that can be applied to EG diagrams."""
    ARITY_NUMBERING = "arity_numbering"          # Number hooks for n-ary predicates
    ARGUMENT_LABELS = "argument_labels"          # Label predicate arguments (input/output)
    VARIABLE_BINDING = "variable_binding"        # Show variable binding relationships
    LOGICAL_STRUCTURE = "logical_structure"      # Highlight logical patterns
    CONTAINMENT_AREAS = "containment_areas"      # Show area boundaries explicitly
    TRANSFORMATION_HINTS = "transformation_hints" # Show available EG rule applications

class AnnotationConfig:
    """Configuration for annotation rendering."""
    def __init__(self, 
                 annotation_type: AnnotationType,
                 enabled: bool = False,
                 style_options: Optional[Dict[str, Any]] = None,
                 target_elements: Optional[Set[str]] = None):
        self.annotation_type = annotation_type
        self.enabled = enabled
        self.style_options = style_options or {}
        self.target_elements = target_elements  # None means all applicable elements

class AnnotationLayer:
    """Represents a layer of annotations over a base diagram."""
    def __init__(self, 
                 layer_id: str,
                 annotations: List[AnnotationConfig],
                 z_order: int = 0):
        self.layer_id = layer_id
        self.annotations = annotations
        self.z_order = z_order  # Higher numbers render on top

def validate_relational_graph_with_cuts(obj: Any) -> TypeGuard[Any]:
    """
    Validate that an object conforms to the RelationalGraphWithCuts contract.
    
    Required attributes:
    - V: frozenset of vertex IDs
    - E: frozenset of edge IDs  
    - Cut: frozenset of cut IDs
    - sheet: sheet area ID
    """
    if not hasattr(obj, 'V'):
        raise ContractViolationError(f"RelationalGraphWithCuts missing 'V' attribute. Got: {type(obj)}")
    
    if not hasattr(obj, 'E'):
        raise ContractViolationError(f"RelationalGraphWithCuts missing 'E' attribute. Got: {type(obj)}")
        
    if not hasattr(obj, 'Cut'):
        raise ContractViolationError(f"RelationalGraphWithCuts missing 'Cut' attribute. Got: {type(obj)}")
        
    if not hasattr(obj, 'sheet'):
        raise ContractViolationError(f"RelationalGraphWithCuts missing 'sheet' attribute. Got: {type(obj)}")
    
    if not isinstance(obj.V, frozenset):
        raise ContractViolationError(f"RelationalGraphWithCuts.V must be frozenset, got: {type(obj.V)}")
        
    if not isinstance(obj.E, frozenset):
        raise ContractViolationError(f"RelationalGraphWithCuts.E must be frozenset, got: {type(obj.E)}")
        
    if not isinstance(obj.Cut, frozenset):
        raise ContractViolationError(f"RelationalGraphWithCuts.Cut must be frozenset, got: {type(obj.Cut)}")
    
    return True

def validate_layout_result(obj: Any) -> TypeGuard[Any]:
    """
    Validate that an object conforms to the LayoutResult contract.
    
    Required attributes:
    - primitives: Dict[str, SpatialPrimitive]
    - canvas_bounds: Tuple[float, float, float, float]
    - containment_hierarchy: Dict[str, Set[str]]
    """
    if not hasattr(obj, 'primitives'):
        raise ContractViolationError(f"LayoutResult missing 'primitives' attribute. Got: {type(obj)}")
    
    if not hasattr(obj, 'canvas_bounds'):
        raise ContractViolationError(f"LayoutResult missing 'canvas_bounds' attribute. Got: {type(obj)}")
        
    if not hasattr(obj, 'containment_hierarchy'):
        raise ContractViolationError(f"LayoutResult missing 'containment_hierarchy' attribute. Got: {type(obj)}")
    
    if not isinstance(obj.primitives, dict):
        raise ContractViolationError(f"LayoutResult.primitives must be dict, got: {type(obj.primitives)}")
        
    if not isinstance(obj.canvas_bounds, tuple) or len(obj.canvas_bounds) != 4:
        raise ContractViolationError(f"LayoutResult.canvas_bounds must be 4-tuple, got: {obj.canvas_bounds}")
        
    if not isinstance(obj.containment_hierarchy, dict):
        raise ContractViolationError(f"LayoutResult.containment_hierarchy must be dict, got: {type(obj.containment_hierarchy)}")
    
    # Validate that primitives is not empty for valid graphs
    if len(obj.primitives) == 0:
        raise ContractViolationError("LayoutResult.primitives cannot be empty for valid graphs")
    
    return True

def validate_spatial_primitive(obj: Any) -> TypeGuard[Any]:
    """
    Validate that an object conforms to the SpatialPrimitive contract.
    
    Required attributes:
    - element_id: str
    - element_type: str
    - position: Tuple[float, float]
    - bounds: Tuple[float, float, float, float]
    """
    if not hasattr(obj, 'element_id'):
        raise ContractViolationError(f"SpatialPrimitive missing 'element_id' attribute. Got: {type(obj)}")
        
    if not hasattr(obj, 'element_type'):
        raise ContractViolationError(f"SpatialPrimitive missing 'element_type' attribute. Got: {type(obj)}")
        
    if not hasattr(obj, 'position'):
        raise ContractViolationError(f"SpatialPrimitive missing 'position' attribute. Got: {type(obj)}")
        
    if not hasattr(obj, 'bounds'):
        raise ContractViolationError(f"SpatialPrimitive missing 'bounds' attribute. Got: {type(obj)}")
    
    if not isinstance(obj.element_id, str):
        raise ContractViolationError(f"SpatialPrimitive.element_id must be str, got: {type(obj.element_id)}")
        
    if not isinstance(obj.element_type, str):
        raise ContractViolationError(f"SpatialPrimitive.element_type must be str, got: {type(obj.element_type)}")
        
    if not isinstance(obj.position, tuple) or len(obj.position) != 2:
        raise ContractViolationError(f"SpatialPrimitive.position must be 2-tuple, got: {obj.position}")
        
    if not isinstance(obj.bounds, tuple) or len(obj.bounds) != 4:
        raise ContractViolationError(f"SpatialPrimitive.bounds must be 4-tuple, got: {obj.bounds}")
    
    return True

def validate_canvas_interface(obj: Any) -> TypeGuard[Any]:
    """
    Validate that an object conforms to the Canvas interface contract.
    
    Required methods:
    - draw_line, draw_circle, draw_text, save_to_file
    """
    required_methods = ['draw_line', 'draw_circle', 'draw_text', 'save_to_file']
    
    for method_name in required_methods:
        if not hasattr(obj, method_name):
            raise ContractViolationError(f"Canvas missing required method '{method_name}'. Got: {type(obj)}")
        
        if not callable(getattr(obj, method_name)):
            raise ContractViolationError(f"Canvas.{method_name} must be callable")
    
    return True

def validate_canvas_drawing_style(style: dict, operation: str) -> None:
    """
    Validate that a drawing style dictionary conforms to canvas API expectations.
    
    This catches internal API mismatches like 'line_width' vs 'width'.
    """
    if operation in ['line', 'circle', 'oval']:
        # Check for common API mismatches
        if 'line_width' in style:
            raise ContractViolationError(
                f"Canvas style API mismatch: found 'line_width' but canvas expects 'width'. "
                f"Style: {style}"
            )
        
        # Validate expected style keys
        valid_keys = {'color', 'width', 'fill_color', 'line_style'}
        invalid_keys = set(style.keys()) - valid_keys
        if invalid_keys:
            raise ContractViolationError(
                f"Canvas style contains invalid keys: {invalid_keys}. "
                f"Valid keys for {operation}: {valid_keys}"
            )
    
    elif operation == 'text':
        valid_keys = {'color', 'font_size', 'bold', 'font_family'}
        invalid_keys = set(style.keys()) - valid_keys
        if invalid_keys:
            raise ContractViolationError(
                f"Canvas text style contains invalid keys: {invalid_keys}. "
                f"Valid keys for text: {valid_keys}"
            )

# Annotation System Validation Functions
def validate_annotation_config(obj: Any) -> TypeGuard[AnnotationConfig]:
    """
    Validate that an object conforms to the AnnotationConfig contract.
    
    Required attributes:
    - annotation_type: AnnotationType
    - enabled: bool
    - style_options: Dict[str, Any]
    - target_elements: Optional[Set[str]]
    """
    if not isinstance(obj, AnnotationConfig):
        raise ContractViolationError(f"Expected AnnotationConfig, got: {type(obj)}")
    
    if not isinstance(obj.annotation_type, AnnotationType):
        raise ContractViolationError(f"annotation_type must be AnnotationType, got: {type(obj.annotation_type)}")
    
    if not isinstance(obj.enabled, bool):
        raise ContractViolationError(f"enabled must be bool, got: {type(obj.enabled)}")
    
    if not isinstance(obj.style_options, dict):
        raise ContractViolationError(f"style_options must be dict, got: {type(obj.style_options)}")
    
    if obj.target_elements is not None and not isinstance(obj.target_elements, set):
        raise ContractViolationError(f"target_elements must be Set[str] or None, got: {type(obj.target_elements)}")
    
    return True

def validate_annotation_layer(obj: Any) -> TypeGuard[AnnotationLayer]:
    """
    Validate that an object conforms to the AnnotationLayer contract.
    
    Required attributes:
    - layer_id: str
    - annotations: List[AnnotationConfig]
    - z_order: int
    """
    if not isinstance(obj, AnnotationLayer):
        raise ContractViolationError(f"Expected AnnotationLayer, got: {type(obj)}")
    
    if not isinstance(obj.layer_id, str):
        raise ContractViolationError(f"layer_id must be str, got: {type(obj.layer_id)}")
    
    if not isinstance(obj.annotations, list):
        raise ContractViolationError(f"annotations must be List[AnnotationConfig], got: {type(obj.annotations)}")
    
    for i, annotation in enumerate(obj.annotations):
        try:
            validate_annotation_config(annotation)
        except ContractViolationError as e:
            raise ContractViolationError(f"Invalid annotation at index {i}: {e}")
    
    if not isinstance(obj.z_order, int):
        raise ContractViolationError(f"z_order must be int, got: {type(obj.z_order)}")
    
    return True

def validate_annotated_layout_result(obj: Any) -> TypeGuard[Any]:
    """
    Validate that an object conforms to the AnnotatedLayoutResult contract.
    
    This extends LayoutResult with annotation layers.
    
    Required attributes (from LayoutResult):
    - primitives: Dict[str, SpatialPrimitive]
    - canvas_bounds: Tuple[float, float, float, float]
    - containment_hierarchy: Dict[str, Set[str]]
    
    Additional attributes for annotations:
    - annotation_layers: List[AnnotationLayer]
    - active_annotations: Set[AnnotationType]
    """
    # First validate as standard LayoutResult
    validate_layout_result(obj)
    
    # Then validate annotation-specific attributes
    if not hasattr(obj, 'annotation_layers'):
        raise ContractViolationError(f"AnnotatedLayoutResult missing 'annotation_layers' attribute")
    
    if not isinstance(obj.annotation_layers, list):
        raise ContractViolationError(f"annotation_layers must be List[AnnotationLayer], got: {type(obj.annotation_layers)}")
    
    for i, layer in enumerate(obj.annotation_layers):
        try:
            validate_annotation_layer(layer)
        except ContractViolationError as e:
            raise ContractViolationError(f"Invalid annotation layer at index {i}: {e}")
    
    if not hasattr(obj, 'active_annotations'):
        raise ContractViolationError(f"AnnotatedLayoutResult missing 'active_annotations' attribute")
    
    if not isinstance(obj.active_annotations, set):
        raise ContractViolationError(f"active_annotations must be Set[AnnotationType], got: {type(obj.active_annotations)}")
    
    for annotation_type in obj.active_annotations:
        if not isinstance(annotation_type, AnnotationType):
            raise ContractViolationError(f"active_annotations must contain AnnotationType, got: {type(annotation_type)}")
    
    return True

# Decorator for contract enforcement
def enforce_contracts(input_contracts=None, output_contract=None):
    """
    Decorator to enforce pipeline contracts on function inputs and outputs.
    
    Usage:
    @enforce_contracts(
        input_contracts={'graph': validate_relational_graph_with_cuts},
        output_contract=validate_layout_result
    )
    def create_layout_from_graph(graph):
        # ... implementation
        return layout_result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Validate inputs
            if input_contracts:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                for param_name, validator in input_contracts.items():
                    if param_name in bound_args.arguments:
                        param_value = bound_args.arguments[param_name]
                        try:
                            validator(param_value)
                        except ContractViolationError as e:
                            raise ContractViolationError(
                                f"Contract violation in {func.__name__}() parameter '{param_name}': {e}"
                            )
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Validate output
            if output_contract:
                try:
                    output_contract(result)
                except ContractViolationError as e:
                    raise ContractViolationError(
                        f"Contract violation in {func.__name__}() return value: {e}"
                    )
            
            return result
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator

# Pipeline stage validation functions
def validate_egif_to_egi_handoff(egif_input: str, egi_output: Any) -> None:
    """Validate the EGIF → EGI pipeline handoff."""
    if not isinstance(egif_input, str):
        raise ContractViolationError(f"EGIF input must be string, got: {type(egif_input)}")
    
    validate_relational_graph_with_cuts(egi_output)
    print(f"✅ EGIF → EGI handoff validated")

def validate_egi_to_layout_handoff(egi_input: Any, layout_output: Any) -> None:
    """Validate the EGI → Layout pipeline handoff."""
    validate_relational_graph_with_cuts(egi_input)
    validate_layout_result(layout_output)
    print(f"✅ EGI → Layout handoff validated")

def validate_layout_to_render_handoff(layout_input: Any, graph_input: Any, canvas_input: Any) -> None:
    """Validate the Layout → Render pipeline handoff."""
    validate_layout_result(layout_input)
    validate_relational_graph_with_cuts(graph_input)
    validate_canvas_interface(canvas_input)
    print(f"✅ Layout → Render handoff validated")

def validate_graphviz_dot_output(dot_content: str, graph: Any) -> bool:
    """
    Validate that DOT content conforms to solidified Graphviz modeling standards.
    
    This ensures the robust DOT generation we've established is maintained.
    """
    if not isinstance(dot_content, str):
        raise ContractViolationError(f"DOT content must be string, got: {type(dot_content)}")
    
    if not dot_content.strip():
        raise ContractViolationError("DOT content cannot be empty")
    
    # Verify essential Graphviz hierarchical attributes are present
    required_attrs = [
        'clusterrank=local',  # Cluster-local ranking
        'compound=true',      # Inter-cluster edges
        'newrank=true',       # Improved ranking
        'rankdir=TB'          # Top-bottom layout
    ]
    
    for attr in required_attrs:
        if attr not in dot_content:
            raise ContractViolationError(f"Missing required Graphviz attribute: {attr}")
    
    # Verify cluster structure matches EGI cuts
    cluster_count = dot_content.count('subgraph cluster_')
    expected_cuts = len(graph.Cut) if hasattr(graph, 'Cut') else 0
    
    if cluster_count != expected_cuts:
        raise ContractViolationError(
            f"Cluster count mismatch: DOT has {cluster_count} clusters, "
            f"EGI has {expected_cuts} cuts"
        )
    
    # Verify proper cluster nesting structure
    lines = dot_content.split('\n')
    cluster_depth = 0
    max_depth = 0
    
    for line in lines:
        if 'subgraph cluster_' in line:
            cluster_depth += 1
            max_depth = max(max_depth, cluster_depth)
        elif line.strip() == '}' and cluster_depth > 0:
            cluster_depth -= 1
    
    if cluster_depth != 0:
        raise ContractViolationError("Unbalanced cluster braces in DOT output")
    
    return True

def validate_graphviz_coordinate_extraction(xdot_output: str, layout_result: Any) -> bool:
    """
    Validate that coordinate extraction from xdot output produces valid layout results.
    
    This ensures the proven xdot parser approach is working correctly.
    """
    if not isinstance(xdot_output, str):
        raise ContractViolationError(f"xdot output must be string, got: {type(xdot_output)}")
    
    if not xdot_output.strip():
        raise ContractViolationError("xdot output cannot be empty")
    
    # Validate layout result structure
    validate_layout_result(layout_result)
    
    # Verify cluster boundaries are extracted for cuts
    cut_primitives = {
        elem_id: primitive for elem_id, primitive in layout_result.primitives.items()
        if primitive.element_type == 'cut'
    }
    
    # If xdot contains cluster boundaries, we should have extracted them
    if '_bb=' in xdot_output and not cut_primitives:
        raise ContractViolationError(
            "xdot output contains cluster boundaries but no cut primitives extracted"
        )
    
    # Verify proper containment for nested cuts
    if len(cut_primitives) >= 2:
        cuts = list(cut_primitives.values())
        cuts.sort(key=lambda x: (x.bounds[2] - x.bounds[0]) * (x.bounds[3] - x.bounds[1]))
        
        for i in range(len(cuts) - 1):
            inner_cut = cuts[i]
            outer_cut = cuts[i + 1]
            
            # Check if inner cut is properly contained within outer cut
            inner_x1, inner_y1, inner_x2, inner_y2 = inner_cut.bounds
            outer_x1, outer_y1, outer_x2, outer_y2 = outer_cut.bounds
            
            properly_contained = (
                outer_x1 <= inner_x1 and
                outer_y1 <= inner_y1 and
                outer_x2 >= inner_x2 and
                outer_y2 >= inner_y2
            )
            
            if not properly_contained:
                raise ContractViolationError(
                    f"Cut containment violation: inner cut {inner_cut.bounds} "
                    f"not properly contained in outer cut {outer_cut.bounds}"
                )
    
    return True

def validate_graphviz_layout_engine_output(graph: Any, layout_result: Any) -> bool:
    """
    Validate complete Graphviz layout engine output against solidified standards.
    
    This is the comprehensive contract for the entire Graphviz modeling system.
    """
    # Validate input graph
    validate_relational_graph_with_cuts(graph)
    
    # Validate output layout
    validate_layout_result(layout_result)
    
    # Verify all graph elements are represented in layout
    expected_elements = set()
    
    # Add vertices (extract IDs from Vertex objects)
    if hasattr(graph, 'V'):
        for vertex in graph.V:
            vertex_id = vertex.id if hasattr(vertex, 'id') else str(vertex)
            expected_elements.add(vertex_id)
    
    # Add edges/predicates (extract IDs from Edge objects)
    if hasattr(graph, 'E'):
        for edge in graph.E:
            edge_id = edge.id if hasattr(edge, 'id') else str(edge)
            expected_elements.add(edge_id)
    
    # Add cuts (extract IDs from Cut objects)
    if hasattr(graph, 'Cut'):
        for cut in graph.Cut:
            cut_id = cut.id if hasattr(cut, 'id') else str(cut)
            expected_elements.add(cut_id)
    
    # Check that all expected elements have spatial primitives
    layout_elements = set(layout_result.primitives.keys())
    missing_elements = expected_elements - layout_elements
    
    if missing_elements:
        raise ContractViolationError(
            f"Missing spatial primitives for elements: {missing_elements}"
        )
    
    # Verify canvas bounds are reasonable
    x1, y1, x2, y2 = layout_result.canvas_bounds
    if x2 <= x1 or y2 <= y1:
        raise ContractViolationError(
            f"Invalid canvas bounds: {layout_result.canvas_bounds}"
        )
    
    return True

# Comprehensive pipeline validation
def validate_full_pipeline(egif: str, graph: Any, layout: Any, canvas: Any) -> bool:
    """Validate the entire EGIF → EGI → Layout → Render pipeline."""
    try:
        validate_egif_to_egi_handoff(egif, graph)
        validate_egi_to_layout_handoff(graph, layout)
        validate_layout_to_render_handoff(layout, graph, canvas)
        
        # Add Graphviz-specific validation if this is a Graphviz layout
        if hasattr(layout, 'primitives') and any(
            primitive.element_type == 'cut' for primitive in layout.primitives.values()
        ):
            validate_graphviz_layout_engine_output(graph, layout)
        
        return True
    except ContractViolationError:
        return False

# Annotation-aware pipeline validation
def validate_annotation_to_render_handoff(layout: Any, annotation_layers: List[AnnotationLayer], canvas: Any):
    """Validate the AnnotatedLayout → Render pipeline handoff."""
    validate_annotated_layout_result(layout)
    validate_canvas_interface(canvas)
    
    # Validate that annotation layers are compatible with layout
    for layer in annotation_layers:
        validate_annotation_layer(layer)
        
        # Check that target elements exist in layout
        for annotation in layer.annotations:
            if annotation.target_elements:
                for element_id in annotation.target_elements:
                    if element_id not in layout.primitives:
                        raise ContractViolationError(
                            f"Annotation targets non-existent element: {element_id}"
                        )
    
    print("✓ Annotation → Render handoff validation passed")

def validate_annotated_pipeline(egif: str, graph: Any, layout: Any, 
                              annotation_layers: List[AnnotationLayer], canvas: Any):
    """Validate the entire EGIF → EGI → AnnotatedLayout → Render pipeline."""
    # Standard pipeline validation
    validate_egif_to_egi_handoff(egif, graph)
    validate_egi_to_layout_handoff(graph, layout)
    
    # Annotation-specific validation
    validate_annotation_to_render_handoff(layout, annotation_layers, canvas)
    
    print("✓ Full annotated pipeline validation passed")
    
    # Additional integration checks
    if hasattr(layout, 'primitives'):
        primitive_count = len(layout.primitives)
        element_count = len(graph.V) + len(graph.E) + len(graph.Cut)
        annotation_count = sum(len(layer.annotations) for layer in annotation_layers)
        
        if primitive_count == 0:
            raise ContractViolationError("Layout has no spatial primitives")
        
        print(f"✓ Layout contains {primitive_count} spatial primitives for {element_count} graph elements")
        print(f"✓ {len(annotation_layers)} annotation layers with {annotation_count} total annotations")

if __name__ == "__main__":
    print("Pipeline Contract Validation Module")
    print(f"API Version: {PIPELINE_API_VERSION}")
    print("Use this module to validate all pipeline handoffs and prevent API confusion.")
