"""
EGIF Generator - Converts EGI instances back to EGIF format.
Implements the reverse of the EGIF parser.
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict

from egi_core import EGI, Context, Vertex, Edge, ElementID


class EGIFGenerator:
    """Generates EGIF expressions from EGI instances."""
    
    def __init__(self):
        self.vertex_labels: Dict[ElementID, str] = {}
        self.label_counter = 0
        self.used_labels: Set[str] = set()
    
    def generate(self, egi: EGI) -> str:
        """Generates an EGIF expression from an EGI instance."""
        # Reset state
        self.vertex_labels.clear()
        self.label_counter = 0
        self.used_labels.clear()
        
        # Assign labels to vertices
        self._assign_vertex_labels(egi)
        
        # Generate EGIF for the sheet of assertion
        egif_parts = self._generate_context_content(egi, egi.sheet)
        
        # Join parts with spaces
        return " ".join(egif_parts)
    
    def _assign_vertex_labels(self, egi: EGI) -> None:
        """Assigns labels to vertices based on their usage patterns."""
        # Track which vertices need defining labels and where they should be defined
        vertex_first_use: Dict[ElementID, Context] = {}
        vertex_contexts: Dict[ElementID, Set[Context]] = defaultdict(set)
        
        # Find first use and all contexts for each vertex
        for vertex_id, vertex in egi.vertices.items():
            if vertex.is_constant:
                continue
                
            # Track all contexts where this vertex appears
            for edge_id in vertex.incident_edges:
                edge = egi.edges[edge_id]
                vertex_contexts[vertex_id].add(edge.context)
                
                # Track first use (shallowest context)
                if vertex_id not in vertex_first_use:
                    vertex_first_use[vertex_id] = edge.context
                elif edge.context.depth < vertex_first_use[vertex_id].depth:
                    vertex_first_use[vertex_id] = edge.context
        
        # Assign labels
        for vertex_id, vertex in egi.vertices.items():
            if vertex.is_constant:
                # Use constant name as label
                self.vertex_labels[vertex_id] = f'"{vertex.constant_name}"'
            else:
                # Generate a unique label
                label = self._generate_unique_label()
                
                # Check if vertex appears in multiple contexts or multiple edges
                contexts = vertex_contexts.get(vertex_id, set())
                edge_count = len(vertex.incident_edges)
                
                # Use defining label if vertex appears in multiple contexts or multiple edges
                if len(contexts) > 1 or edge_count > 1:
                    self.vertex_labels[vertex_id] = f"*{label}"
                else:
                    self.vertex_labels[vertex_id] = f"*{label}"  # Always use defining for simplicity
    
    def _generate_unique_label(self) -> str:
        """Generates a unique label for a vertex."""
        while True:
            if self.label_counter < 26:
                label = chr(ord('x') + self.label_counter)
            else:
                label = f"x{self.label_counter - 25}"
            
            self.label_counter += 1
            
            if label not in self.used_labels:
                self.used_labels.add(label)
                return label
    
    def _vertex_crosses_contexts(self, egi: EGI, vertex_id: ElementID) -> bool:
        """Checks if a vertex is referenced across different contexts."""
        vertex = egi.vertices[vertex_id]
        vertex_context = vertex.context
        
        # Check if any edge connecting to this vertex is in a different context
        for edge_id in vertex.incident_edges:
            edge = egi.edges[edge_id]
            if edge.context != vertex_context:
                return True
        
        return False
    
    def _generate_context_content(self, egi: EGI, context: Context) -> List[str]:
        """Generates EGIF content for a specific context."""
        parts = []
        used_defining_labels = set()
        
        # Generate relations for edges in this context
        for edge in egi.edges.values():
            if edge.context == context:
                if not edge.is_identity:
                    # Regular relation
                    relation_egif = self._generate_relation(edge, used_defining_labels)
                    parts.append(relation_egif)
        
        # Generate identity edges as coreference nodes if needed
        identity_groups = self._find_identity_groups(egi, context)
        for group in identity_groups:
            if len(group) > 1:  # Only generate coreference for multiple vertices
                coreference_egif = self._generate_coreference(group, used_defining_labels)
                parts.append(coreference_egif)
        
        # Generate cuts (negations) in this context
        for cut_id in context.children:
            cut = egi.get_context(cut_id)
            cut_content = self._generate_context_content(egi, cut)
            
            if cut_content:
                # Check if this can be represented as a scroll
                if self._is_scroll_pattern(egi, cut):
                    scroll_egif = self._generate_scroll(egi, cut)
                    parts.append(scroll_egif)
                else:
                    # Regular negation
                    negation_content = " ".join(cut_content)
                    parts.append(f"~[ {negation_content} ]")
            else:
                # Empty negation
                parts.append("~[ ]")
        
        return parts
    
    def _generate_relation(self, edge: Edge, used_defining_labels: Set[str]) -> str:
        """Generates EGIF for a relation edge."""
        relation_name = edge.relation_name
        
        # Get vertex labels
        vertex_labels = []
        for vertex_id in edge.incident_vertices:
            label = self.vertex_labels[vertex_id]
            
            # Check if this should be a defining label
            if label.startswith("*"):
                base_label = label[1:]
                if base_label not in used_defining_labels:
                    # Use defining label
                    vertex_labels.append(label)
                    used_defining_labels.add(base_label)
                else:
                    # Use bound label
                    vertex_labels.append(base_label)
            else:
                vertex_labels.append(label)
        
        # Format as relation
        if vertex_labels:
            return f"({relation_name} {' '.join(vertex_labels)})"
        else:
            return f"({relation_name})"
    
    def _find_identity_groups(self, egi: EGI, context: Context) -> List[List[ElementID]]:
        """Finds groups of vertices connected by identity edges in this context."""
        identity_edges = [e for e in egi.edges.values() 
                         if e.is_identity and e.context == context]
        
        if not identity_edges:
            return []
        
        # Build connected components
        vertex_groups: Dict[ElementID, Set[ElementID]] = {}
        
        for edge in identity_edges:
            v1, v2 = edge.incident_vertices
            
            # Find existing groups
            group1 = vertex_groups.get(v1, {v1})
            group2 = vertex_groups.get(v2, {v2})
            
            # Merge groups
            merged_group = group1.union(group2)
            
            # Update all vertices in merged group
            for vertex_id in merged_group:
                vertex_groups[vertex_id] = merged_group
        
        # Extract unique groups
        seen_groups = set()
        unique_groups = []
        
        for group in vertex_groups.values():
            group_tuple = tuple(sorted(str(v) for v in group))
            if group_tuple not in seen_groups:
                seen_groups.add(group_tuple)
                unique_groups.append(list(group))
        
        return unique_groups
    
    def _generate_coreference(self, vertex_ids: List[ElementID], used_defining_labels: Set[str]) -> str:
        """Generates a coreference node for a group of vertices."""
        labels = []
        for vertex_id in vertex_ids:
            label = self.vertex_labels[vertex_id]
            
            # Check if this should be a defining label
            if label.startswith("*"):
                base_label = label[1:]
                if base_label not in used_defining_labels:
                    # Use defining label
                    labels.append(label)
                    used_defining_labels.add(base_label)
                else:
                    # Use bound label
                    labels.append(base_label)
            else:
                labels.append(label)
        
        return f"[{' '.join(labels)}]"
    
    def _is_scroll_pattern(self, egi: EGI, cut: Context) -> bool:
        """Checks if a cut represents a scroll pattern (If-Then)."""
        # A scroll pattern has exactly one child cut
        if len(cut.children) != 1:
            return False
        
        # The child cut should also be a simple negation
        child_cut_id = next(iter(cut.children))
        child_cut = egi.get_context(child_cut_id)
        
        # Child should not have further children (for simple scroll)
        return len(child_cut.children) == 0
    
    def _generate_scroll(self, egi: EGI, if_cut: Context) -> str:
        """Generates a scroll (If-Then) pattern."""
        used_defining_labels = set()
        
        # Generate If part
        if_content = []
        for edge in egi.edges.values():
            if edge.context == if_cut and not edge.is_identity:
                if_content.append(self._generate_relation(edge, used_defining_labels))
        
        # Generate Then part
        then_cut_id = next(iter(if_cut.children))
        then_cut = egi.get_context(then_cut_id)
        then_content = []
        for edge in egi.edges.values():
            if edge.context == then_cut and not edge.is_identity:
                then_content.append(self._generate_relation(edge, used_defining_labels))
        
        if_part = " ".join(if_content) if if_content else ""
        then_part = " ".join(then_content) if then_content else ""
        
        return f"[If {if_part} [Then {then_part} ] ]"


def generate_egif(egi: EGI) -> str:
    """Convenience function to generate EGIF from EGI."""
    generator = EGIFGenerator()
    return generator.generate(egi)


# Test the generator
if __name__ == "__main__":
    from egif_parser import parse_egif
    
    # Test cases
    test_cases = [
        "(phoenix *x)",
        "~[ (phoenix *x) ]",
        "(man *x) (human x) (African x)",
        "[*x *y] (P x) (Q y)",
        "(man *x) ~[ (mortal x) ]",
        '[If (thunder *x) [Then (lightning *y) ] ]',
        '(loves "Socrates" "Plato")'
    ]
    
    print("Testing EGIF Generator...\n")
    
    for i, original_egif in enumerate(test_cases, 1):
        print(f"Test {i}: {original_egif}")
        
        try:
            # Parse to EGI
            egi = parse_egif(original_egif)
            
            # Generate back to EGIF
            generated_egif = generate_egif(egi)
            print(f"Generated: {generated_egif}")
            
            # Test round-trip by parsing generated EGIF
            egi2 = parse_egif(generated_egif)
            
            # Check structural equivalence
            same_structure = (
                len(egi.vertices) == len(egi2.vertices) and
                len(egi.edges) == len(egi2.edges) and
                len(egi.cuts) == len(egi2.cuts)
            )
            
            print(f"Round-trip: {'✓' if same_structure else '✗'}")
            
        except Exception as e:
            print(f"Error: {e}")
        
        print()
    
    print("EGIF Generator testing completed!")

