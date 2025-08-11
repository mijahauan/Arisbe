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
        self.defining_vertices = set()  # legacy flagging (not used for hoisted defs)
        # Planned defining context per vertex (minimal common ancestor over all uses)
        self.vertex_def_context: Dict[ElementID, ElementID] = {}
        
    def generate(self) -> str:
        """Generate EGIF expression from graph."""
        # Assign labels to vertices and determine defining occurrences
        self._assign_vertex_labels()
        # Compute hoisted defining context for each generic vertex
        self._compute_vertex_def_contexts()
        
        # Generate content for sheet of assertion
        content = self._generate_context_content(self.graph.sheet)
        
        return content.strip()
    
    def _assign_vertex_labels(self):
        """Assign EGIF labels to vertices and determine defining occurrences."""
        self.vertex_labels = {}
        self.used_labels = set()
        self.defining_vertices = set()
        
        # CRITICAL FIX: Process vertices in ν mapping order to preserve argument order
        # This ensures the ν mapping order from Dau's formalism is strictly preserved
        self._assign_labels_preserving_nu_order(self.graph.sheet, set())

    # --- New: compute minimal common ancestor (enclosing) context for each vertex ---
    def _compute_vertex_def_contexts(self) -> None:
        """For each generic vertex, compute the minimal common ancestor area that contains all
        its predicate occurrences and assign that as the defining context.
        We will emit an isolated defining *x in that context.
        """
        # Build parent map for contexts (cuts); sheet has parent None
        parent: Dict[ElementID, Optional[ElementID]] = {}
        for cut in self.graph.Cut:
            parent[cut.id] = self.graph.get_context(cut.id)
        parent[self.graph.sheet] = None  # type: ignore

        def ancestors(ctx: Optional[ElementID]) -> List[Optional[ElementID]]:
            chain: List[Optional[ElementID]] = []
            cur = ctx
            seen = set()
            while cur is not None and cur not in seen:
                seen.add(cur)
                chain.append(cur)
                cur = parent.get(cur)
            chain.append(None)
            return chain

        def lca(ctxs: List[ElementID]) -> ElementID:
            if not ctxs:
                return self.graph.sheet
            a0 = ctxs[0]
            a0_chain = ancestors(a0)
            aset = set(a0_chain)
            for c in ctxs[1:]:
                c_chain = ancestors(c)
                # find first common from inner to outer along c_chain
                pick: Optional[ElementID] = None
                for cand in c_chain:
                    if cand in aset:
                        pick = cand
                        break
                if pick is None:
                    # As a safeguard, use sheet
                    return self.graph.sheet
                # tighten aset to ancestors of pick
                aset = set(ancestors(pick))
            # The innermost element of aset that is on a0_chain is the LCA; take first of a0_chain in aset
            for cand in a0_chain:
                if cand in aset and cand is not None:
                    return cand
            return self.graph.sheet

        # Collect contexts of usage for each generic vertex
        uses_by_vertex: Dict[ElementID, List[ElementID]] = {}
        for edge_id, vseq in self.graph.nu.items():
            edge_ctx = self.graph.get_context(edge_id)
            for vid in vseq:
                if vid in self.graph._vertex_map:
                    vobj = self.graph.get_vertex(vid)
                    if vobj.is_generic:
                        uses_by_vertex.setdefault(vid, []).append(edge_ctx)

        # Assign definition context
        self.vertex_def_context.clear()
        for vid, ctxs in uses_by_vertex.items():
            self.vertex_def_context[vid] = lca(ctxs)
    
    def _assign_labels_preserving_nu_order(self, context_id: ElementID, processed_vertices: Set[ElementID]):
        """Assign labels while strictly preserving ν mapping argument order."""
        # Get area (direct contents) of this context
        area_elements = self.graph.get_area(context_id)
        
        # CRITICAL: Process edges first to establish ν mapping order for vertices
        for element_id in area_elements:
            if element_id in self.graph._edge_map:
                # Get the exact ν mapping order for this edge
                vertex_sequence = self.graph.get_incident_vertices(element_id)
                
                # Process vertices in exact ν mapping order
                for vertex_id in vertex_sequence:
                    if vertex_id not in processed_vertices and vertex_id in self.graph._vertex_map:
                        vertex = self.graph.get_vertex(vertex_id)
                        
                        if vertex.is_generic:
                            if vertex_id not in self.vertex_labels:
                                # First occurrence - assign fresh label and mark as defining
                                label = self.alphabet.get_fresh_name()
                                self.vertex_labels[vertex_id] = label
                                self.used_labels.add(label)
                                self.defining_vertices.add(vertex_id)
                            # If already labeled, this is a bound occurrence (don't mark as defining)
                        else:
                            # Constant vertex - use its label
                            self.vertex_labels[vertex_id] = f'"{vertex.label}"'
                        
                        processed_vertices.add(vertex_id)
        
        # Process isolated vertices in this area
        for element_id in area_elements:
            if element_id in self.graph._vertex_map and element_id not in processed_vertices:
                vertex = self.graph.get_vertex(element_id)
                
                if vertex.is_generic:
                    # Isolated generic vertex - assign fresh label and mark as defining
                    label = self.alphabet.get_fresh_name()
                    self.vertex_labels[element_id] = label
                    self.used_labels.add(label)
                    self.defining_vertices.add(element_id)
                else:
                    # Isolated constant vertex - use its label
                    self.vertex_labels[element_id] = f'"{vertex.label}"'
                
                processed_vertices.add(element_id)
        
        # Process cuts in this area recursively
        for element_id in area_elements:
            if element_id in self.graph._cut_map:
                self._assign_labels_preserving_nu_order(element_id, processed_vertices)
    
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
        
        # Emit isolated defining variables planned for this context
        for vid, def_ctx in self.vertex_def_context.items():
            if def_ctx == context_id:
                # Only emit once; ensure label exists
                if vid in self.vertex_labels:
                    label = self.vertex_labels[vid]
                    content_parts.append(f"*{label}")
        
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
                # With hoisting, relation arguments are bound (no star)
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
        """With hoisted definitions, relation occurrences are always bound (no star)."""
        return False


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

