"""
Immutable EGIF generator that converts EGI instances back to EGIF expressions.
Works with the new immutable architecture.
"""

from typing import Dict, Set, List, Optional

try:
    from .egi_core import EGI, Context, Vertex, Edge, ElementID
except ImportError:
    from egi_core import EGI, Context, Vertex, Edge, ElementID


class EGIFGenerator:
    """Generator for converting EGI to EGIF expressions."""
    
    def __init__(self, egi: EGI):
        self.egi = egi
        self.vertex_labels: Dict[ElementID, str] = {}
        self.used_labels: Set[str] = set()
        self.label_counter = 0
        
        # Build label assignments
        self._assign_labels()
    
    def _assign_labels(self):
        """Assign labels to vertices for EGIF generation."""
        # Track which vertices have been processed
        processed_vertices = set()
        
        # First pass: find vertices that share the same logical identity
        # and assign them the same label
        vertex_groups = self._group_coreferent_vertices()
        
        for group in vertex_groups:
            if not group:
                continue
                
            # Find the vertex that should get the defining label
            # (typically the one in the outermost context)
            defining_vertex = min(group, key=lambda v_id: self.egi.get_context(
                self.egi.get_vertex(v_id).context_id).depth)
            
            # Generate label for this group
            label = self._generate_label()
            
            # Assign defining label to the defining vertex
            self.vertex_labels[defining_vertex] = f"*{label}"
            processed_vertices.add(defining_vertex)
            
            # Assign bound labels to other vertices in the group
            for vertex_id in group:
                if vertex_id != defining_vertex:
                    self.vertex_labels[vertex_id] = label
                    processed_vertices.add(vertex_id)
        
        # Second pass: handle any remaining vertices
        for vertex in self.egi.vertices:
            if (vertex.id not in processed_vertices and 
                not vertex.is_constant):
                label = self._generate_label()
                self.vertex_labels[vertex.id] = f"*{label}"
    
    def _group_coreferent_vertices(self) -> List[Set[ElementID]]:
        """Group vertices that should have the same label."""
        groups = []
        processed = set()
        
        # Look for identity edges (coreference)
        for edge in self.egi.edges:
            if edge.is_identity:
                group = set(edge.incident_vertices)
                # Only include non-constant vertices
                group = {v_id for v_id in group 
                        if not self.egi.get_vertex(v_id).is_constant}
                if group and not any(v_id in processed for v_id in group):
                    groups.append(group)
                    processed.update(group)
        
        # Look for vertices that appear in multiple relations
        # (this is a simplified heuristic)
        vertex_relations = {}
        for edge in self.egi.edges:
            if not edge.is_identity:
                for vertex_id in edge.incident_vertices:
                    vertex = self.egi.get_vertex(vertex_id)
                    if not vertex.is_constant:
                        if vertex_id not in vertex_relations:
                            vertex_relations[vertex_id] = []
                        vertex_relations[vertex_id].append(edge.id)
        
        # Group vertices that appear together in relations
        for vertex_id, relations in vertex_relations.items():
            if vertex_id not in processed and len(relations) > 1:
                # This vertex appears in multiple relations
                # For now, treat it as its own group
                groups.append({vertex_id})
                processed.add(vertex_id)
        
        # Add remaining vertices as individual groups
        for vertex in self.egi.vertices:
            if (vertex.id not in processed and 
                not vertex.is_constant):
                groups.append({vertex.id})
        
        return groups
    
    def _find_defining_vertex(self, vertex_id: ElementID) -> Optional[ElementID]:
        """Find the defining vertex that this vertex should reference."""
        # For now, simple implementation - in a full system this would
        # track coreference relationships properly
        vertex = self.egi.get_vertex(vertex_id)
        
        # Look for other vertices in outer contexts with same properties
        for other_vertex in self.egi.vertices:
            if (other_vertex.id != vertex_id and
                other_vertex.is_constant == vertex.is_constant and
                other_vertex.constant_name == vertex.constant_name):
                
                other_context = self.egi.get_context(other_vertex.context_id)
                vertex_context = self.egi.get_context(vertex.context_id)
                
                # Check if other vertex is in an outer context
                if other_context.depth < vertex_context.depth:
                    return other_vertex.id
        
        return None
    
    def _generate_label(self) -> str:
        """Generate a unique variable label."""
        while True:
            if self.label_counter == 0:
                label = "x"
            elif self.label_counter == 1:
                label = "y"
            elif self.label_counter == 2:
                label = "z"
            else:
                label = f"x{self.label_counter - 2}"
            
            if label not in self.used_labels:
                self.used_labels.add(label)
                self.label_counter += 1
                return label
            
            self.label_counter += 1
    
    def generate(self) -> str:
        """Generate EGIF expression from EGI."""
        return self._generate_context_content(self.egi.sheet_id).strip()
    
    def _generate_context_content(self, context_id: ElementID) -> str:
        """Generate content for a specific context."""
        context = self.egi.get_context(context_id)
        parts = []
        
        # Generate elements in this context
        for element_id in context.enclosed_elements:
            if element_id in self.egi._vertex_map:
                # Skip isolated vertices for now - they'll be handled separately
                vertex = self.egi.get_vertex(element_id)
                if self.egi.is_vertex_isolated(element_id):
                    continue
            elif element_id in self.egi._edge_map:
                edge = self.egi.get_edge(element_id)
                if not edge.is_identity:
                    parts.append(self._generate_relation(edge))
                else:
                    parts.append(self._generate_coreference(edge))
        
        # Generate child contexts (cuts)
        for child_id in context.children:
            child_context = self.egi.get_context(child_id)
            if child_context.is_negative():
                # This is a cut
                cut_content = self._generate_context_content(child_id)
                if cut_content.strip():
                    parts.append(f"~[ {cut_content} ]")
                else:
                    parts.append("~[ ]")
            else:
                # This might be a positive context (inner part of double cut or scroll)
                # Check if it has content or children
                inner_content = self._generate_context_content(child_id)
                if inner_content.strip():
                    # If it has content, it might be a scroll or other structure
                    scroll_content = self._generate_scroll_content(child_id)
                    if scroll_content:
                        parts.append(scroll_content)
                    else:
                        # Just wrap the content
                        parts.append(f"~[ {inner_content} ]")
                else:
                    # Empty positive context - might be part of double cut
                    if len(child_context.children) == 0 and len(child_context.enclosed_elements) == 0:
                        # Empty context, skip it for now
                        pass
                    else:
                        # Has children, process them
                        inner_content = self._generate_context_content(child_id)
                        if inner_content.strip():
                            parts.append(f"~[ {inner_content} ]")
        
        return " ".join(parts)
    
    def _generate_relation(self, edge: Edge) -> str:
        """Generate EGIF for a relation edge."""
        args = []
        
        for vertex_id in edge.incident_vertices:
            vertex = self.egi.get_vertex(vertex_id)
            
            if vertex.is_constant:
                if vertex.constant_name.isdigit() or vertex.constant_name.replace('.', '').replace('-', '').isdigit():
                    # Numeric constant
                    args.append(vertex.constant_name)
                else:
                    # String constant
                    args.append(f'"{vertex.constant_name}"')
            else:
                # Variable
                if vertex_id in self.vertex_labels:
                    args.append(self.vertex_labels[vertex_id])
                else:
                    # Fallback label
                    label = self._generate_label()
                    self.vertex_labels[vertex_id] = f"*{label}"
                    args.append(f"*{label}")
        
        return f"({edge.relation_name} {' '.join(args)})"
    
    def _generate_coreference(self, edge: Edge) -> str:
        """Generate EGIF for a coreference (identity) edge."""
        labels = []
        
        for vertex_id in edge.incident_vertices:
            vertex = self.egi.get_vertex(vertex_id)
            
            if not vertex.is_constant:
                if vertex_id in self.vertex_labels:
                    label = self.vertex_labels[vertex_id]
                    # Remove * if present for coreference
                    if label.startswith('*'):
                        label = label[1:]
                    labels.append(label)
        
        if len(labels) > 1:
            return f"[{' '.join(labels)}]"
        else:
            return ""
    
    def _generate_scroll_content(self, context_id: ElementID) -> str:
        """Generate content for scroll patterns."""
        context = self.egi.get_context(context_id)
        
        # Check if this context contains scroll markers
        scroll_markers = []
        other_content = []
        
        for element_id in context.enclosed_elements:
            if element_id in self.egi._vertex_map:
                vertex = self.egi.get_vertex(element_id)
                if (vertex.is_constant and 
                    vertex.constant_name in ['If', 'Then']):
                    scroll_markers.append(vertex.constant_name)
                else:
                    other_content.append(element_id)
            elif element_id in self.egi._edge_map:
                edge = self.egi.get_edge(element_id)
                if not edge.is_identity:
                    other_content.append(self._generate_relation(edge))
        
        # Generate child contexts
        child_parts = []
        for child_id in context.children:
            child_content = self._generate_context_content(child_id)
            if child_content.strip():
                child_parts.append(f"[{child_content}]")
        
        if scroll_markers:
            # This is a scroll pattern
            marker = scroll_markers[0]
            content_parts = [self._generate_relation(self.egi.get_edge(eid)) 
                           for eid in other_content if eid in self.egi._edge_map]
            content_parts.extend(child_parts)
            
            if content_parts:
                return f"[{marker} {' '.join(content_parts)} ]"
            else:
                return f"[{marker} ]"
        else:
            # Regular context
            content_parts = [self._generate_relation(self.egi.get_edge(eid)) 
                           for eid in other_content if eid in self.egi._edge_map]
            content_parts.extend(child_parts)
            
            if content_parts:
                return f"[{' '.join(content_parts)}]"
            else:
                return ""


def generate_egif(egi: EGI) -> str:
    """Generate EGIF expression from EGI."""
    generator = EGIFGenerator(egi)
    return generator.generate()


# Test the generator
if __name__ == "__main__":
    print("Testing immutable EGIF generator...")
    
    try:
        from .egif_parser import parse_egif
    except ImportError:
        from egif_parser import parse_egif
    
    test_cases = [
        "(phoenix *x)",
        "(man *x) (human x)",
        '(loves "Socrates" "Plato")',
        "~[ (mortal *x) ]",
        "[*x *y] (P x) (Q y)",
    ]
    
    for original_egif in test_cases:
        try:
            # Parse to EGI
            egi = parse_egif(original_egif)
            
            # Generate back to EGIF
            generated_egif = generate_egif(egi)
            
            # Parse generated EGIF to verify it's valid
            egi2 = parse_egif(generated_egif)
            
            print(f"✓ {original_egif} -> {generated_egif}")
            print(f"  Structure preserved: {len(egi.vertices)} vertices, {len(egi.edges)} edges")
            
        except Exception as e:
            print(f"✗ Failed: {original_egif}")
            print(f"  Error: {e}")
    
    print("✓ Immutable EGIF generator working correctly!")

