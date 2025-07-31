"""
Test Utilities for Transformation Rule Testing
Integrates element identification and context mapping for functional tests

CHANGES: Created to provide high-level utilities that combine element identification,
context mapping, and transformation function interfaces for seamless test execution.
"""

from typing import Optional, List, Set, Tuple, Any, Dict
from egi_core_dau import RelationalGraphWithCuts, ElementID
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from element_identification import ElementIdentifier, find_element_in_graph
from context_mapping import ContextMapper
import egi_transformations_dau as transforms


class TransformationTester:
    """High-level interface for testing transformation rules."""
    
    def __init__(self, base_egif: str):
        self.base_egif = base_egif
        self.graph = parse_egif(base_egif)
        self.identifier = ElementIdentifier(self.graph)
        self.mapper = ContextMapper(self.graph)
    
    def test_erasure(self, probe: str, position: str) -> Tuple[bool, str, Optional[str]]:
        """
        Test erasure transformation.
        
        Returns:
            (success, result_description, result_egif)
        """
        try:
            # Find element to erase
            element_ids = self.identifier.find_elements_by_egif_probe(probe, position)
            if not element_ids:
                return False, f"Element not found: {probe}", None
            
            element_id = element_ids[0]
            
            # Apply erasure
            result_graph = transforms.apply_erasure(self.graph, element_id)
            result_egif = generate_egif(result_graph)
            
            return True, "Erasure successful", result_egif
            
        except transforms.TransformationError as e:
            return False, f"Transformation prevented: {str(e)}", None
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    def test_insertion(self, probe: str, position: str) -> Tuple[bool, str, Optional[str]]:
        """
        Test insertion transformation.
        
        Returns:
            (success, result_description, result_egif)
        """
        try:
            # Get target context
            context_id = self.mapper.get_context_for_transformation("insertion", position, self.base_egif)
            if context_id is None:
                return False, f"Context not found for position: {position}", None
            
            # Parse probe to determine element type
            if probe.startswith('[') and probe.endswith(']'):
                # Isolated vertex
                content = probe[1:-1]
                if content.startswith('*'):
                    label = content[1:]
                    is_generic = True
                elif content.startswith('"') and content.endswith('"'):
                    label = content[1:-1]
                    is_generic = False
                else:
                    label = content
                    is_generic = True
                
                result_graph = transforms.apply_insertion(
                    self.graph, "vertex", context_id, 
                    label=label, is_generic=is_generic
                )
            
            elif probe.startswith('(') and probe.endswith(')'):
                # Relation/edge
                content = probe[1:-1]
                parts = content.split()
                if not parts:
                    return False, "Invalid relation probe", None
                
                relation_name = parts[0]
                vertex_specs = parts[1:]
                
                # For now, create simple edge - full implementation would handle vertex creation
                result_graph = transforms.apply_insertion(
                    self.graph, "edge", context_id,
                    relation_name=relation_name, vertex_sequence=()
                )
            
            else:
                return False, f"Unknown probe type: {probe}", None
            
            result_egif = generate_egif(result_graph)
            return True, "Insertion successful", result_egif
            
        except transforms.TransformationError as e:
            return False, f"Transformation prevented: {str(e)}", None
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    def test_iteration(self, probe: str, source_position: str, target_position: str) -> Tuple[bool, str, Optional[str]]:
        """
        Test iteration transformation.
        
        Returns:
            (success, result_description, result_egif)
        """
        try:
            # Find elements to iterate
            element_ids = self.identifier.find_elements_by_egif_probe(probe, source_position)
            if not element_ids:
                return False, f"Element not found: {probe}", None
            
            # Get source and target contexts
            source_context = self.mapper.get_context_by_position_description(source_position, self.base_egif)
            target_context = self.mapper.get_context_by_position_description(target_position, self.base_egif)
            
            if source_context is None or target_context is None:
                return False, "Source or target context not found", None
            
            # Apply iteration
            result_graph = transforms.apply_iteration(
                self.graph, set(element_ids), source_context, target_context
            )
            result_egif = generate_egif(result_graph)
            
            return True, "Iteration successful", result_egif
            
        except transforms.TransformationError as e:
            return False, f"Transformation prevented: {str(e)}", None
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    def test_de_iteration(self, probe: str, position: str) -> Tuple[bool, str, Optional[str]]:
        """
        Test de-iteration transformation.
        
        Returns:
            (success, result_description, result_egif)
        """
        try:
            # Find element to de-iterate
            element_ids = self.identifier.find_elements_by_egif_probe(probe, position)
            if not element_ids:
                return False, f"Element not found: {probe}", None
            
            element_id = element_ids[0]
            
            # Apply de-iteration
            result_graph = transforms.apply_de_iteration(self.graph, element_id)
            result_egif = generate_egif(result_graph)
            
            return True, "De-iteration successful", result_egif
            
        except transforms.TransformationError as e:
            return False, f"Transformation prevented: {str(e)}", None
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    def test_double_cut_addition(self, probe: str, position: str) -> Tuple[bool, str, Optional[str]]:
        """
        Test double cut addition transformation.
        
        Returns:
            (success, result_description, result_egif)
        """
        try:
            # Find elements to enclose
            element_ids = self.identifier.find_elements_by_egif_probe(probe, position)
            if not element_ids:
                return False, f"Elements not found: {probe}", None
            
            # Get context
            context_id = self.mapper.get_context_by_position_description(position, self.base_egif)
            if context_id is None:
                context_id = self.graph.sheet
            
            # Apply double cut addition
            result_graph = transforms.apply_double_cut_addition(
                self.graph, set(element_ids), context_id
            )
            result_egif = generate_egif(result_graph)
            
            return True, "Double cut addition successful", result_egif
            
        except transforms.TransformationError as e:
            return False, f"Transformation prevented: {str(e)}", None
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    def test_double_cut_removal(self, probe: str, position: str) -> Tuple[bool, str, Optional[str]]:
        """
        Test double cut removal transformation.
        
        Returns:
            (success, result_description, result_egif)
        """
        try:
            # Find outer cut to remove
            cut_ids = self.identifier.find_elements_by_egif_probe(probe, position)
            if not cut_ids:
                return False, f"Cut not found: {probe}", None
            
            cut_id = cut_ids[0]
            
            # Apply double cut removal
            result_graph = transforms.apply_double_cut_removal(self.graph, cut_id)
            result_egif = generate_egif(result_graph)
            
            return True, "Double cut removal successful", result_egif
            
        except transforms.TransformationError as e:
            return False, f"Transformation prevented: {str(e)}", None
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    def test_isolated_vertex_addition(self, probe: str, position: str) -> Tuple[bool, str, Optional[str]]:
        """
        Test isolated vertex addition transformation.
        
        Returns:
            (success, result_description, result_egif)
        """
        try:
            # Parse probe for vertex details
            if not (probe.startswith('[') and probe.endswith(']')):
                return False, f"Invalid isolated vertex probe: {probe}", None
            
            content = probe[1:-1]
            if content.startswith('*'):
                label = content[1:]
                vertex_type = "generic"
            elif content.startswith('"') and content.endswith('"'):
                label = content[1:-1]
                vertex_type = "constant"
            else:
                label = content
                vertex_type = "generic"
            
            # Get target context
            context_id = self.mapper.get_context_by_position_description(position, self.base_egif)
            if context_id is None:
                context_id = self.graph.sheet
            
            # Apply isolated vertex addition
            result_graph = transforms.apply_isolated_vertex_addition(
                self.graph, label, vertex_type, context_id
            )
            result_egif = generate_egif(result_graph)
            
            return True, "Isolated vertex addition successful", result_egif
            
        except transforms.TransformationError as e:
            return False, f"Transformation prevented: {str(e)}", None
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    def test_isolated_vertex_removal(self, probe: str, position: str) -> Tuple[bool, str, Optional[str]]:
        """
        Test isolated vertex removal transformation.
        
        Returns:
            (success, result_description, result_egif)
        """
        try:
            # Find vertex to remove
            vertex_ids = self.identifier.find_elements_by_egif_probe(probe, position)
            if not vertex_ids:
                return False, f"Vertex not found: {probe}", None
            
            vertex_id = vertex_ids[0]
            
            # Apply isolated vertex removal
            result_graph = transforms.apply_isolated_vertex_removal(self.graph, vertex_id)
            result_egif = generate_egif(result_graph)
            
            return True, "Isolated vertex removal successful", result_egif
            
        except transforms.TransformationError as e:
            return False, f"Transformation prevented: {str(e)}", None
        except Exception as e:
            return False, f"Error: {str(e)}", None


def run_transformation_test(rule_name: str, base_egif: str, probe: str, 
                          position: str, **kwargs) -> Tuple[bool, str, Optional[str]]:
    """
    Convenience function to run a transformation test.
    
    Args:
        rule_name: Name of transformation rule
        base_egif: Base EGIF string
        probe: Element to transform
        position: Position description
        **kwargs: Additional arguments (e.g., target_position for iteration)
    
    Returns:
        (success, result_description, result_egif)
    """
    tester = TransformationTester(base_egif)
    
    if rule_name.lower() == "erasure":
        return tester.test_erasure(probe, position)
    elif rule_name.lower() == "insertion":
        return tester.test_insertion(probe, position)
    elif rule_name.lower() == "iteration":
        target_position = kwargs.get("target_position", position)
        return tester.test_iteration(probe, position, target_position)
    elif rule_name.lower() == "de_iteration" or rule_name.lower() == "deiteration":
        return tester.test_de_iteration(probe, position)
    elif rule_name.lower() == "double_cut_addition":
        return tester.test_double_cut_addition(probe, position)
    elif rule_name.lower() == "double_cut_removal":
        return tester.test_double_cut_removal(probe, position)
    elif rule_name.lower() == "isolated_vertex_addition":
        return tester.test_isolated_vertex_addition(probe, position)
    elif rule_name.lower() == "isolated_vertex_removal":
        return tester.test_isolated_vertex_removal(probe, position)
    else:
        return False, f"Unknown rule: {rule_name}", None


def validate_transformation_constraints(rule_name: str, base_egif: str, probe: str, 
                                      position: str) -> Tuple[bool, str]:
    """
    Validate transformation constraints without executing the transformation.
    
    Returns:
        (is_valid, reason)
    """
    try:
        graph = parse_egif(base_egif)
        identifier = ElementIdentifier(graph)
        mapper = ContextMapper(graph)
        
        # Check if elements exist
        element_ids = identifier.find_elements_by_egif_probe(probe, position)
        if not element_ids:
            return False, f"Element not found: {probe}"
        
        # Check context constraints
        context_id = mapper.get_context_by_position_description(position, base_egif)
        if context_id is None:
            return False, f"Context not found: {position}"
        
        # Rule-specific validation
        if rule_name.lower() == "erasure":
            if not graph.is_positive_context(context_id):
                return False, "Erasure only allowed in positive contexts"
        elif rule_name.lower() == "insertion":
            if not graph.is_negative_context(context_id):
                return False, "Insertion only allowed in negative contexts"
        elif rule_name.lower() == "isolated_vertex_removal":
            vertex_id = element_ids[0]
            if vertex_id in graph._vertex_map and not graph.is_vertex_isolated(vertex_id):
                return False, "Vertex has incident edges (E_v ≠ ∅)"
        
        return True, "Constraints satisfied"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def debug_element_identification(base_egif: str, probe: str, position: str) -> Dict[str, Any]:
    """
    Debug helper to show element identification process.
    
    Returns:
        Dictionary with debug information
    """
    try:
        graph = parse_egif(base_egif)
        identifier = ElementIdentifier(graph)
        mapper = ContextMapper(graph)
        
        # Find elements
        element_ids = identifier.find_elements_by_egif_probe(probe, position)
        
        # Get context
        context_id = mapper.get_context_by_position_description(position, base_egif)
        
        # Build debug info
        debug_info = {
            "base_egif": base_egif,
            "probe": probe,
            "position": position,
            "found_elements": element_ids,
            "target_context": context_id,
            "graph_vertices": [{"id": v.id, "label": v.label, "is_generic": v.is_generic} for v in graph.V],
            "graph_edges": [{"id": e.id, "relation": graph.get_relation_name(e.id), 
                           "vertices": graph.get_incident_vertices(e.id)} for e in graph.E],
            "graph_cuts": [{"id": c.id, "area": list(graph.get_area(c.id))} for c in graph.Cut],
            "context_hierarchy": mapper.get_context_hierarchy(),
            "context_polarity": mapper.get_context_polarity_map()
        }
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}

