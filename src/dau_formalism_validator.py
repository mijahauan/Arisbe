"""
Dau Formalism Validator

Validates EGI structures against Dau's Chapter 16 formalism requirements.
Ensures all ligature connections respect the fundamental context constraint:
ctx(va) = ctx(vb) for any connected vertices va, vb.

Based on Dau's Lemma 16.1: "Moving Branches along a Ligature in a Context"
"""

from typing import List, Tuple, Set
from dataclasses import dataclass

from egi_core_dau import RelationalGraphWithCuts, ElementID


@dataclass
class ContextViolation:
    """Represents a violation of Dau's context constraint."""
    element1: ElementID
    element2: ElementID
    context1: ElementID
    context2: ElementID
    violation_type: str
    description: str


class DauFormalismValidator:
    """
    Validates EGI structures against Dau's formalism requirements.
    
    Key Principle from Lemma 16.1:
    For any ligature connection between vertices va and vb,
    we must have ctx(va) = ctx(vb).
    """
    
    def validate_egi_formalism(self, egi: RelationalGraphWithCuts) -> Tuple[bool, List[ContextViolation]]:
        """
        Validate an EGI against Dau's formalism requirements.
        
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        
        # Check all edge-vertex connections for context violations
        for edge_id, vertex_sequence in egi.nu.items():
            edge_context = egi.get_context(edge_id)
            
            for vertex_id in vertex_sequence:
                vertex_context = egi.get_context(vertex_id)
                
                if edge_context != vertex_context:
                    violations.append(ContextViolation(
                        element1=edge_id,
                        element2=vertex_id,
                        context1=edge_context,
                        context2=vertex_context,
                        violation_type="CROSS_CONTEXT_CONNECTION",
                        description=f"Edge {edge_id} in context {edge_context} "
                                  f"connects to vertex {vertex_id} in context {vertex_context}. "
                                  f"Violates Dau's Lemma 16.1: ctx(edge) must equal ctx(vertex)."
                    ))
        
        # Check identity connections (ligatures) for same-context requirement
        identity_violations = self._check_identity_context_violations(egi)
        violations.extend(identity_violations)
        
        is_valid = len(violations) == 0
        return is_valid, violations
    
    def _check_identity_context_violations(self, egi: RelationalGraphWithCuts) -> List[ContextViolation]:
        """Check that all identity-connected vertices are in the same context."""
        violations = []
        
        # Find all identity edges
        identity_edges = []
        for edge_id, relation in egi.rel.items():
            if relation == "=" and edge_id in egi.nu:
                identity_edges.append((edge_id, egi.nu[edge_id]))
        
        # Check each identity connection
        for edge_id, vertex_sequence in identity_edges:
            if len(vertex_sequence) >= 2:
                contexts = [egi.get_context(vid) for vid in vertex_sequence]
                
                # All vertices in identity connection must have same context
                first_context = contexts[0]
                for i, context in enumerate(contexts[1:], 1):
                    if context != first_context:
                        violations.append(ContextViolation(
                            element1=vertex_sequence[0],
                            element2=vertex_sequence[i],
                            context1=first_context,
                            context2=context,
                            violation_type="IDENTITY_CROSS_CONTEXT",
                            description=f"Identity edge {edge_id} connects vertices "
                                      f"{vertex_sequence[0]} (context {first_context}) and "
                                      f"{vertex_sequence[i]} (context {context}). "
                                      f"Violates Dau's Lemma 16.1: vaΘvb requires ctx(va) = ctx(vb)."
                        ))
        
        return violations
    
    def print_validation_report(self, egi: RelationalGraphWithCuts) -> None:
        """Print a detailed validation report for an EGI."""
        print("🔍 DAU FORMALISM VALIDATION REPORT")
        print("=" * 50)
        
        is_valid, violations = self.validate_egi_formalism(egi)
        
        if is_valid:
            print("✅ EGI STRUCTURE IS VALID")
            print("All connections respect Dau's context constraints.")
        else:
            print(f"❌ EGI STRUCTURE VIOLATES DAU'S FORMALISM")
            print(f"Found {len(violations)} violation(s):")
            print()
            
            for i, violation in enumerate(violations, 1):
                print(f"Violation {i}: {violation.violation_type}")
                print(f"  Elements: {violation.element1} ↔ {violation.element2}")
                print(f"  Contexts: {violation.context1} ↔ {violation.context2}")
                print(f"  Description: {violation.description}")
                print()
        
        print("Dau's Lemma 16.1 Requirement:")
        print("  For any ligature connection between elements a and b,")
        print("  we must have ctx(a) = ctx(b).")
        print()
        
    def get_valid_connections(self, egi: RelationalGraphWithCuts) -> Set[Tuple[ElementID, ElementID]]:
        """
        Get all valid connections that respect Dau's formalism.
        
        Returns set of (element1, element2) tuples that can be validly connected.
        """
        valid_connections = set()
        
        for edge_id, vertex_sequence in egi.nu.items():
            edge_context = egi.get_context(edge_id)
            
            for vertex_id in vertex_sequence:
                vertex_context = egi.get_context(vertex_id)
                
                if edge_context == vertex_context:
                    valid_connections.add((edge_id, vertex_id))
        
        return valid_connections
    
    def suggest_corrections(self, egi: RelationalGraphWithCuts) -> List[str]:
        """
        Suggest corrections for Dau formalism violations.
        
        Returns list of suggested corrections.
        """
        is_valid, violations = self.validate_egi_formalism(egi)
        
        if is_valid:
            return ["EGI structure is already valid - no corrections needed."]
        
        suggestions = []
        
        for violation in violations:
            if violation.violation_type == "CROSS_CONTEXT_CONNECTION":
                suggestions.append(
                    f"Move {violation.element1} or {violation.element2} to the same context, "
                    f"or remove the connection between them."
                )
            elif violation.violation_type == "IDENTITY_CROSS_CONTEXT":
                suggestions.append(
                    f"Identity connection between {violation.element1} and {violation.element2} "
                    f"is invalid. Use Dau's transformation rules to move vertices to same context "
                    f"before establishing identity connection."
                )
        
        return suggestions
