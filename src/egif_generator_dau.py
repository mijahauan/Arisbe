"""
Fixed Dau-compliant EGIF generator with proper variable scoping.
Fixes the critical issue where variables defined in cuts were not marked as defining.

Key fix: Variables that first appear in any context (including cuts) are marked as defining (*x).
"""

from typing import Dict, Set, List, Optional, Tuple
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID, Alphabet


class EGIFGenerator:
    """Generates EGIF expressions from Dau-compliant graphs with proper variable scoping."""
    
    def __init__(self, graph: RelationalGraphWithCuts):
        self.graph = graph
        self.alphabet = Alphabet()
        self.vertex_labels = {}  # Maps vertex IDs to EGIF labels
        self.used_labels = set()
        self.defining_vertices = set()  # Track which vertices are defining
        
    def generate(self) -> str:
        """Generate EGIF expression from graph."""
        # Assign labels to vertices and determine defining occurrences
        self._assign_vertex_labels()
        
        # Generate content for sheet of assertion
        content = self._generate_context_content(self.graph.sheet)
        
        return content.strip()
    
    def _assign_vertex_labels(self):
        """Assign EGIF labels to vertices and determine defining occurrences."""
        self.vertex_labels = {}
        self.used_labels = set()
        self.defining_vertices = set()
        
        # Process vertices in order of first appearance (depth-first)
        self._assign_labels_recursive(self.graph.sheet, set())
    
    def _assign_labels_recursive(self, context_id: ElementID, processed_vertices: Set[ElementID]):
        """Recursively assign labels and track defining occurrences."""
        # Get area (direct contents) of this context
        area_elements = self.graph.get_area(context_id)
        
        # Process vertices in this area - mark first occurrence as defining
        for element_id in area_elements:
            if element_id in self.graph._vertex_map and element_id not in processed_vertices:
                vertex = self.graph.get_vertex(element_id)
                
                if vertex.is_generic:
                    # Generic vertex - assign fresh variable name and mark as defining
                    if element_id not in self.vertex_labels:
                        label = self.alphabet.get_fresh_name()
                        self.vertex_labels[element_id] = label
                        self.used_labels.add(label)
                        # Mark this vertex as defining since it's first occurrence
                        self.defining_vertices.add(element_id)
                else:
                    # Constant vertex - use its label
                    self.vertex_labels[element_id] = f'"{vertex.label}"'
                
                processed_vertices.add(element_id)
        
        # Process edges in this area to find bound variable occurrences
        for element_id in area_elements:
            if element_id in self.graph._edge_map:
                vertex_sequence = self.graph.get_incident_vertices(element_id)
                for vertex_id in vertex_sequence:
                    if vertex_id not in processed_vertices and vertex_id in self.graph._vertex_map:
                        vertex = self.graph.get_vertex(vertex_id)
                        if vertex.is_generic:
                            # This is a bound occurrence - find existing label
                            # Search all processed vertices for matching label
                            for processed_vid in processed_vertices:
                                if (processed_vid in self.graph._vertex_map and 
                                    processed_vid in self.vertex_labels):
                                    processed_vertex = self.graph.get_vertex(processed_vid)
                                    if (processed_vertex.is_generic and 
                                        processed_vertex.label == vertex.label):
                                        # Use same label but don't mark as defining
                                        self.vertex_labels[vertex_id] = self.vertex_labels[processed_vid]
                                        break
                            else:
                                # No matching label found - this shouldn't happen in valid EG
                                # But handle gracefully by creating new label
                                label = self.alphabet.get_fresh_name()
                                self.vertex_labels[vertex_id] = label
                                self.used_labels.add(label)
                        else:
                            # Constant vertex
                            self.vertex_labels[vertex_id] = f'"{vertex.label}"'
                        
                        processed_vertices.add(vertex_id)
        
        # Process cuts in this area
        for element_id in area_elements:
            if element_id in self.graph._cut_map:
                self._assign_labels_recursive(element_id, processed_vertices)
    
    def _generate_context_content(self, context_id: ElementID) -> str:
        """Generate content for a context using area (not full context)."""
        # Use area (direct contents) to avoid duplication
        area_elements = self.graph.get_area(context_id)
        
        content_parts = []
        
        # Generate isolated vertices first
        for element_id in area_elements:
            if element_id in self.graph._vertex_map:
                vertex = self.graph.get_vertex(element_id)
                if self.graph.is_vertex_isolated(element_id):
                    if vertex.is_generic:
                        # Generic isolated vertex - always defining
                        label = self.vertex_labels[element_id]
                        content_parts.append(f"*{label}")
                    else:
                        # Constant isolated vertex
                        content_parts.append(f'"{vertex.label}"')
        
        # Generate relations
        for element_id in area_elements:
            if element_id in self.graph._edge_map:
                relation_egif = self._generate_relation(element_id)
                content_parts.append(relation_egif)
        
        # Generate cuts
        for element_id in area_elements:
            if element_id in self.graph._cut_map:
                cut_egif = self._generate_cut(element_id)
                content_parts.append(cut_egif)
        
        return " ".join(content_parts)
    
    def _generate_relation(self, edge_id: ElementID) -> str:
        """Generate EGIF for a relation with proper defining/bound marking."""
        relation_name = self.graph.get_relation_name(edge_id)
        vertex_sequence = self.graph.get_incident_vertices(edge_id)
        
        # Generate arguments
        args = []
        for vertex_id in vertex_sequence:
            vertex = self.graph.get_vertex(vertex_id)
            
            if vertex.is_generic:
                label = self.vertex_labels[vertex_id]
                
                # Check if this vertex is defining in this relation
                if self._is_defining_occurrence(vertex_id, edge_id):
                    args.append(f"*{label}")
                else:
                    # Bound occurrence
                    args.append(label)
            else:
                # Constant vertex
                args.append(f'"{vertex.label}"')
        
        return f"({relation_name} {' '.join(args)})"
    
    def _generate_cut(self, cut_id: ElementID) -> str:
        """Generate EGIF for a cut."""
        cut_content = self._generate_context_content(cut_id)
        
        if cut_content:
            return f"~[ {cut_content} ]"
        else:
            return "~[ ]"
    
    def _is_defining_occurrence(self, vertex_id: ElementID, edge_id: ElementID) -> bool:
        """Check if vertex occurrence in this relation should be defining."""
        # Fixed logic for coreference: A vertex is defining in a relation if:
        # 1. It's a generic vertex, AND
        # 2. This is the first time we encounter this variable name in this context OR any parent context
        
        vertex = self.graph.get_vertex(vertex_id)
        if not vertex.is_generic:
            return False
        
        # Get the context where this edge appears
        edge_context = self.graph.get_context(edge_id)
        
        # Check current context and all parent contexts for this variable
        current_context = edge_context
        while current_context is not None:
            # Check if this variable appears in any earlier elements in current context
            context_area = self.graph.get_area(current_context)
            
            for element_id in context_area:
                if element_id == edge_id and current_context == edge_context:
                    # This is the current edge in the current context - if we haven't found the variable yet, it's defining
                    break
                
                if element_id in self.graph._edge_map:
                    # Check if this earlier edge uses the same variable
                    other_vertices = self.graph.get_incident_vertices(element_id)
                    for other_vertex_id in other_vertices:
                        if other_vertex_id == vertex_id:
                            # Same vertex instance - this is bound
                            return False
                        
                        # Check for same variable name (different instances)
                        if other_vertex_id in self.graph._vertex_map:
                            other_vertex = self.graph.get_vertex(other_vertex_id)
                            if (other_vertex.is_generic and 
                                hasattr(other_vertex, 'label') and
                                hasattr(vertex, 'label') and
                                other_vertex.label == vertex.label):
                                # Same variable name used earlier - this is bound
                                return False
            
            # Move to parent context
            if current_context == self.graph.sheet:
                break
            current_context = self.graph.get_context(current_context)
        
        # No earlier use found in this context or any parent context - this is defining
        return True


def generate_egif(graph: RelationalGraphWithCuts) -> str:
    """Generate EGIF expression from Dau-compliant graph."""
    generator = EGIFGenerator(graph)
    return generator.generate()


if __name__ == "__main__":
    # Test the fixed generator
    print("=== Testing Fixed EGIF Generator ===")
    
    from egif_parser_dau import parse_egif
    
    test_cases = [
        # Basic relation
        "(man *x)",
        
        # Isolated vertices
        "*x",
        '"Socrates"',
        
        # Mixed
        "(man *x) *y",
        
        # Constants and variables
        '(loves "Socrates" *x)',
        
        # Simple cut - THIS WAS FAILING
        "~[ (mortal *x) ]",
        
        # Nested cuts - THIS WAS FAILING
        "~[ (man *x) ~[ (mortal x) ] ]",
        
        # Complex example
        '(human "Socrates") ~[ (mortal "Socrates") ] *x',
    ]
    
    print("Testing round-trip conversion (EGIF → Graph → EGIF):")
    
    for i, original_egif in enumerate(test_cases, 1):
        try:
            print(f"\n{i}. Original: {original_egif}")
            
            # Parse to graph
            graph = parse_egif(original_egif)
            print(f"   Parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
            
            # Generate back to EGIF
            generated_egif = generate_egif(graph)
            print(f"   Generated: {generated_egif}")
            
            # Test round-trip by parsing generated EGIF
            try:
                graph2 = parse_egif(generated_egif)
                print(f"   Round-trip: {len(graph2.V)} vertices, {len(graph2.E)} edges, {len(graph2.Cut)} cuts")
                
                # Check structural equivalence
                if (len(graph.V) == len(graph2.V) and 
                    len(graph.E) == len(graph2.E) and 
                    len(graph.Cut) == len(graph2.Cut)):
                    print("   ✓ Round-trip successful")
                else:
                    print("   ✗ Round-trip failed - structural mismatch")
            except Exception as e:
                print(f"   ✗ Round-trip parsing failed: {e}")
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    print("\n=== Critical Test: Variable Scoping in Cuts ===")
    
    # Test the specific cases that were failing
    critical_cases = [
        "~[ (mortal *x) ]",
        "~[ (man *x) ~[ (mortal x) ] ]"
    ]
    
    for egif in critical_cases:
        print(f"\nTesting: {egif}")
        try:
            graph = parse_egif(egif)
            generated = generate_egif(graph)
            print(f"Generated: {generated}")
            
            # Try to parse generated
            graph2 = parse_egif(generated)
            print("✓ Round-trip successful - variable scoping fixed!")
            
        except Exception as e:
            print(f"✗ Still failing: {e}")
    
    print("\n=== Fixed Generator Test Complete ===")

