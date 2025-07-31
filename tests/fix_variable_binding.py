#!/usr/bin/env python3
"""
Variable Binding Fix
Addresses variable binding edge cases discovered during debugging

CHANGES: Fixed variable binding resolution to handle the fact that parser
doesn't store variable names in vertex labels. Instead, we track binding
relationships through the EGIF structure and context.
"""

import sys
import os
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egif_parser_dau import parse_egif
    from egi_core_dau import RelationalGraphWithCuts, ElementID
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the DAU-compliant modules are available")
    sys.exit(1)


@dataclass
class VariableBinding:
    """Represents a variable binding relationship."""
    variable_name: str
    defining_vertex_id: Optional[ElementID]  # None if no defining occurrence
    bound_occurrences: List[ElementID]  # Vertices where variable is bound
    contexts: Set[ElementID]  # Contexts where variable appears


class VariableBindingAnalyzer:
    """Analyzes variable binding relationships in EGI graphs."""
    
    def __init__(self, graph: RelationalGraphWithCuts, original_egif: str):
        self.graph = graph
        self.original_egif = original_egif
        self.bindings = {}
        self._analyze_bindings()
    
    def _analyze_bindings(self):
        """Analyze variable bindings from the original EGIF."""
        # Parse the EGIF to extract variable information
        # Since parser doesn't preserve variable names, we need to reconstruct
        # the binding relationships from the EGIF structure
        
        self._extract_variables_from_egif()
        self._map_variables_to_elements()
    
    def _extract_variables_from_egif(self):
        """Extract variable information from EGIF string."""
        import re
        
        # Find all variable occurrences in the EGIF
        # Defining occurrences: *x, *y, etc.
        defining_pattern = r'\*([a-zA-Z][a-zA-Z0-9]*)'
        defining_vars = re.findall(defining_pattern, self.original_egif)
        
        # Bound occurrences: x, y (not preceded by *)
        # This is trickier because we need to avoid matching relation names
        bound_pattern = r'(?<!\*)\b([a-z][a-zA-Z0-9]*)\b(?!\s*\()'
        potential_bound_vars = re.findall(bound_pattern, self.original_egif)
        
        # Filter bound variables to only include those that have defining occurrences
        bound_vars = [var for var in potential_bound_vars if var in defining_vars]
        
        # Initialize bindings
        for var in defining_vars:
            self.bindings[var] = VariableBinding(
                variable_name=var,
                defining_vertex_id=None,
                bound_occurrences=[],
                contexts=set()
            )
        
        print(f"Extracted variables:")
        print(f"  Defining: {defining_vars}")
        print(f"  Bound: {bound_vars}")
    
    def _map_variables_to_elements(self):
        """Map variables to actual graph elements."""
        # Since parser doesn't preserve variable names, we use structural matching
        # This is a simplified approach - in practice, we'd need more sophisticated
        # parsing to maintain the variable-to-element mapping
        
        # For now, assume each variable corresponds to a vertex in order of appearance
        vertices = list(self.graph.V)
        variable_names = list(self.bindings.keys())
        
        for i, var_name in enumerate(variable_names):
            if i < len(vertices):
                vertex = vertices[i]
                self.bindings[var_name].defining_vertex_id = vertex.id
                self.bindings[var_name].contexts.add(self.graph.get_context(vertex.id))
                
                # Find bound occurrences by looking at edges that use this vertex
                for edge in self.graph.E:
                    incident_vertices = self.graph.get_incident_vertices(edge.id)
                    if vertex.id in incident_vertices:
                        # This edge uses the variable
                        edge_context = self.graph.get_context(edge.id)
                        self.bindings[var_name].contexts.add(edge_context)
                        
                        # If the edge is in a different context, it's a bound occurrence
                        if edge_context != self.graph.get_context(vertex.id):
                            self.bindings[var_name].bound_occurrences.append(vertex.id)
    
    def get_variable_binding(self, variable_name: str) -> Optional[VariableBinding]:
        """Get binding information for a variable."""
        return self.bindings.get(variable_name)
    
    def is_variable_isolated(self, variable_name: str) -> bool:
        """Check if a variable is truly isolated (no bound occurrences)."""
        binding = self.bindings.get(variable_name)
        if not binding or not binding.defining_vertex_id:
            return False
        
        # Check if the defining vertex is isolated in the graph
        return self.graph.is_vertex_isolated(binding.defining_vertex_id)
    
    def validate_variable_consistency(self) -> List[str]:
        """Validate variable binding consistency."""
        errors = []
        
        for var_name, binding in self.bindings.items():
            # Check if defining vertex exists
            if not binding.defining_vertex_id:
                errors.append(f"Variable '{var_name}' has no defining occurrence")
                continue
            
            # Check if defining vertex is in graph
            vertex_ids = {v.id for v in self.graph.V}
            if binding.defining_vertex_id not in vertex_ids:
                errors.append(f"Variable '{var_name}' defining vertex not found in graph")
            
            # Check bound occurrences
            for bound_vertex_id in binding.bound_occurrences:
                if bound_vertex_id not in vertex_ids:
                    errors.append(f"Variable '{var_name}' bound occurrence not found in graph")
        
        return errors
    
    def can_remove_variable(self, variable_name: str) -> Tuple[bool, str]:
        """Check if a variable can be safely removed."""
        binding = self.bindings.get(variable_name)
        if not binding:
            return False, f"Variable '{variable_name}' not found"
        
        if not binding.defining_vertex_id:
            return False, f"Variable '{variable_name}' has no defining occurrence"
        
        # Check if variable is truly isolated (Dau's E_v = ∅ constraint)
        if not self.is_variable_isolated(variable_name):
            return False, f"Variable '{variable_name}' has incident edges (violates E_v = ∅)"
        
        # Check if removing would create undefined variables
        if binding.bound_occurrences:
            return False, f"Variable '{variable_name}' has bound occurrences that would become undefined"
        
        return True, "Variable can be safely removed"


def analyze_variable_bindings(egif: str) -> VariableBindingAnalyzer:
    """Analyze variable bindings in an EGIF."""
    graph = parse_egif(egif)
    return VariableBindingAnalyzer(graph, egif)


def test_variable_binding_analysis():
    """Test variable binding analysis."""
    
    print("=" * 80)
    print("TESTING VARIABLE BINDING ANALYSIS")
    print("=" * 80)
    
    test_cases = [
        "[*x] ~[(P x)]",  # x is bound in P
        "[*x] [*y] ~[(P z)]",  # x and y are isolated, z is undefined
        "(P *x) (Q x)",  # x is defined and bound
        "~[(Human *x) ~[(Mortal x)]]",  # x is defined and bound across contexts
        "[*x] [*y] ~[(R x y)]",  # x and y are bound in R
    ]
    
    for i, egif in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {egif}")
        print("-" * 40)
        
        try:
            analyzer = analyze_variable_bindings(egif)
            
            print("Variable Bindings:")
            for var_name, binding in analyzer.bindings.items():
                print(f"  {var_name}:")
                print(f"    Defining vertex: {binding.defining_vertex_id}")
                print(f"    Bound occurrences: {binding.bound_occurrences}")
                print(f"    Contexts: {binding.contexts}")
                print(f"    Is isolated: {analyzer.is_variable_isolated(var_name)}")
                
                can_remove, reason = analyzer.can_remove_variable(var_name)
                print(f"    Can remove: {can_remove} ({reason})")
            
            # Validate consistency
            errors = analyzer.validate_variable_consistency()
            if errors:
                print("Validation Errors:")
                for error in errors:
                    print(f"  ❌ {error}")
            else:
                print("✅ Variable binding is consistent")
        
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


def test_isolated_vertex_removal_validation():
    """Test validation for isolated vertex removal."""
    
    print("\n" + "=" * 80)
    print("TESTING ISOLATED VERTEX REMOVAL VALIDATION")
    print("=" * 80)
    
    test_cases = [
        {
            "egif": "[*x] ~[(P x)]",
            "variable_to_remove": "x",
            "expected_valid": False,
            "reason": "x has bound occurrence in P"
        },
        {
            "egif": "[*x] [*y] ~[(P z)]",
            "variable_to_remove": "x",
            "expected_valid": True,
            "reason": "x is truly isolated"
        },
        {
            "egif": "[*x] [*y] ~[(P z)]",
            "variable_to_remove": "y",
            "expected_valid": True,
            "reason": "y is truly isolated"
        },
        {
            "egif": "(P *x)",
            "variable_to_remove": "x",
            "expected_valid": False,
            "reason": "x is connected to relation P"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['egif']}")
        print(f"Attempting to remove: {test_case['variable_to_remove']}")
        print(f"Expected: {'Valid' if test_case['expected_valid'] else 'Invalid'} ({test_case['reason']})")
        print("-" * 60)
        
        try:
            analyzer = analyze_variable_bindings(test_case["egif"])
            can_remove, reason = analyzer.can_remove_variable(test_case["variable_to_remove"])
            
            if can_remove == test_case["expected_valid"]:
                print(f"✅ Correct: {reason}")
            else:
                print(f"❌ Incorrect: Expected {test_case['expected_valid']}, got {can_remove}")
                print(f"   Reason: {reason}")
        
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    test_variable_binding_analysis()
    test_isolated_vertex_removal_validation()

