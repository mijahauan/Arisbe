"""
Dau-compliant CGIF (Conceptual Graph Interchange Format) generator.
Converts RelationalGraphWithCuts structures to CGIF expressions.

CGIF Generation Strategy:
- Vertices with type relations: [Type: *x] or [Type: John]
- Edges as relations: (Loves ?x John)
- Cuts as negation: ~[CG content]
- Generic vertices: [*x]
- Constants: [: John] or just John in relations
- Proper coreference label management

Maintains same rigor as EGIF and CLIF generators.
"""

from typing import Dict, Set, List, Optional, Tuple
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID


class CGIFGenerator:
    """Generates CGIF expressions from Dau-compliant graphs."""
    
    def __init__(self, graph: Optional[RelationalGraphWithCuts] = None):
        # Allow optional graph for legacy API compatibility
        self.graph = graph
        self.vertex_labels = {}  # Maps vertex IDs to CGIF coreference labels
        self.used_labels = set()
        self.label_counter = 0
        self.type_relations = set()  # Track which relations are type relations
        
    def generate(self) -> str:
        """Generate CGIF expression from graph."""
        if self.graph is None:
            raise TypeError("CGIFGenerator.generate() called without a graph. Provide one in constructor or use generate_cgif(graph).")
        # Identify type relations (monadic relations on vertices)
        self._identify_type_relations()
        
        # Assign coreference labels to vertices
        self._assign_vertex_labels()
        
        # Generate CGIF for sheet area (top level)
        cgif_expr = self._generate_area_expression(self.graph.sheet)
        
        return cgif_expr.strip()

    # Legacy-friendly instance method used by tests
    def generate_cgif(self, graph: RelationalGraphWithCuts) -> str:
        """Legacy API: cgif_gen.generate_cgif(graph) -> str"""
        self.graph = graph
        return self.generate()
    
    def _identify_type_relations(self):
        """Identify which relations are type relations (monadic predicates on vertices)."""
        self.type_relations = set()
        
        for edge in self.graph.E:
            if edge.id in self.graph.nu:
                vertex_sequence = self.graph.nu[edge.id]
                # Type relations are monadic (single argument)
                if len(vertex_sequence) == 1:
                    self.type_relations.add(edge.id)
    
    def _assign_vertex_labels(self):
        """Assign CGIF coreference labels to vertices."""
        self.vertex_labels = {}
        self.used_labels = set()
        self.label_counter = 0
        
        # Assign labels to all vertices
        for vertex in self.graph.V:
            if vertex.id not in self.vertex_labels:
                if vertex.is_generic:
                    label = self._get_next_variable_label()
                    self.vertex_labels[vertex.id] = f"*{label}"
                else:
                    # Constants use their label directly
                    self.vertex_labels[vertex.id] = vertex.label or vertex.id
                self.used_labels.add(self.vertex_labels[vertex.id])
    
    def _get_next_variable_label(self) -> str:
        """Get next available variable label."""
        variables = ['x', 'y', 'z', 'u', 'v', 'w']
        
        if self.label_counter < len(variables):
            var = variables[self.label_counter]
        else:
            var = f'x{self.label_counter - len(variables) + 1}'
        
        self.label_counter += 1
        return var
    
    def _get_area_elements(self, area_id: str) -> Dict[str, List[str]]:
        """Get elements in specified area, categorized by type."""
        elements = {
            'vertices': [],
            'edges': [],
            'cuts': []
        }
        
        if area_id not in self.graph.area:
            return elements
        
        area_elements = self.graph.area[area_id]
        
        for element_id in area_elements:
            # Check if it's a vertex
            if any(v.id == element_id for v in self.graph.V):
                elements['vertices'].append(element_id)
            # Check if it's an edge
            elif any(e.id == element_id for e in self.graph.E):
                elements['edges'].append(element_id)
            # Check if it's a cut
            elif any(c.id == element_id for c in self.graph.Cut):
                elements['cuts'].append(element_id)
        
        return elements
    
    def _generate_area_expression(self, area_id: str) -> str:
        """Generate CGIF expression for area content."""
        elements = self._get_area_elements(area_id)
        
        cgif_parts = []
        
        # Generate typed concepts for ALL edges (treating all as type relations)
        processed_vertices = set()
        for edge_id in elements['edges']:
            vertex_sequence = self.graph.nu.get(edge_id, [])
            if len(vertex_sequence) == 1:
                vertex_id = vertex_sequence[0]
                concept = self._generate_typed_concept(edge_id, vertex_id)
                if concept:
                    cgif_parts.append(concept)
                    processed_vertices.add(vertex_id)
        
        # Generate concepts for vertices without type relations
        for vertex_id in elements['vertices']:
            if vertex_id not in processed_vertices:
                concept = self._generate_untyped_concept(vertex_id)
                if concept:
                    cgif_parts.append(concept)
        
        # Generate negations from cuts
        for cut_id in elements['cuts']:
            negation = self._generate_cut_expression(cut_id)
            if negation:
                cgif_parts.append(negation)
        
        return ' '.join(cgif_parts)
    
    def _generate_typed_concept(self, edge_id: str, vertex_id: str) -> str:
        """Generate typed concept [Type: *x] or [Type: John]."""
        if edge_id not in self.graph.rel:
            return ""
        
        type_name = self.graph.rel[edge_id]
        vertex_label = self.vertex_labels.get(vertex_id, vertex_id)
        
        # Find the vertex to check if it's generic or constant
        vertex = next((v for v in self.graph.V if v.id == vertex_id), None)
        if not vertex:
            return ""
        
        if vertex.is_generic:
            return f"[{type_name}: {vertex_label}]"
        else:
            # For constants, use the constant name directly
            return f"[{type_name}: {vertex.label or vertex_id}]"
    
    def _generate_untyped_concept(self, vertex_id: str) -> str:
        """Generate untyped concept [*x] or [: John]."""
        vertex = next((v for v in self.graph.V if v.id == vertex_id), None)
        if not vertex:
            return ""
        
        if vertex.is_generic:
            vertex_label = self.vertex_labels.get(vertex_id, vertex_id)
            return f"[{vertex_label}]"
        else:
            # Constant concept
            return f"[: {vertex.label or vertex_id}]"
    
    def _generate_relation(self, edge_id: str) -> str:
        """Generate relation (Predicate ?x ?y)."""
        if edge_id not in self.graph.rel:
            return ""
        
        predicate = self.graph.rel[edge_id]
        
        # Get vertex arguments
        if edge_id not in self.graph.nu:
            return f"({predicate})"
        
        vertex_sequence = self.graph.nu[edge_id]
        arguments = []
        
        for vertex_id in vertex_sequence:
            vertex = next((v for v in self.graph.V if v.id == vertex_id), None)
            if vertex:
                if vertex.is_generic:
                    # Use bound label for generic vertices
                    label = self.vertex_labels.get(vertex_id, vertex_id)
                    if label.startswith('*'):
                        bound_label = '?' + label[1:]  # Convert *x to ?x
                    else:
                        bound_label = '?' + label
                    arguments.append(bound_label)
                else:
                    # Use constant name directly
                    arguments.append(vertex.label or vertex_id)
            else:
                arguments.append(vertex_id)
        
        if arguments:
            return f"({predicate} {' '.join(arguments)})"
        else:
            return f"({predicate})"
    
    def _generate_cut_expression(self, cut_id: str) -> str:
        """Generate negation expression ~[CG]."""
        cut_content = self._generate_area_expression(cut_id)
        
        if not cut_content:
            return ""
        
        return f"~[{cut_content}]"


# Factory function
def generate_cgif(egi: RelationalGraphWithCuts) -> str:
    """Generate CGIF expression from EGI structure."""
    generator = CGIFGenerator(egi)
    return generator.generate()
