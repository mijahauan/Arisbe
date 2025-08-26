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
        # Planned defining context per generic vertex (minimal common ancestor over all uses)
        self.vertex_def_context: Dict[str, str] = {}
        # Cache for constant detection
        self._rho = None
        self._alphabet = None
        
    def generate(self) -> str:
        """Generate CGIF expression from graph."""
        if self.graph is None:
            raise TypeError("CGIFGenerator.generate() called without a graph. Provide one in constructor or use generate_cgif(graph).")
        # Cache helpers
        self._rho = getattr(self.graph, 'rho', None)
        self._alphabet = getattr(self.graph, 'alphabet', None)
        # Identify type relations (monadic relations on vertices)
        self._identify_type_relations()
        
        # Assign coreference labels to vertices
        self._assign_vertex_labels()
        # Compute hoisted defining contexts (LCA of uses) for generic vertices
        self._compute_vertex_def_contexts()
        
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
        """Assign CGIF coreference labels to vertices, preserving ν order like EGIF."""
        self.vertex_labels = {}
        self.used_labels = set()
        self.label_counter = 0

        processed: Set[str] = set()

        def assign_in_context(ctx_id: str) -> None:
            # Visit edges first in deterministic order, then isolated vertices, then cuts
            area = self.graph.area.get(ctx_id, set())

            # Edges sorted by (predicate, ν vertex ids)
            edge_ids: List[str] = [eid for eid in area if any(e.id == eid for e in self.graph.E)]
            def _edge_key(eid: str) -> Tuple[str, Tuple[str, ...]]:
                pred = self.graph.rel.get(eid, "")
                vseq = tuple(self.graph.nu.get(eid, []))
                return (pred, vseq)
            for eid in sorted(edge_ids, key=_edge_key):
                vseq = self.graph.nu.get(eid, [])
                for vid in vseq:
                    v = next((vx for vx in self.graph.V if vx.id == vid), None)
                    if v is None:
                        continue
                    if v.is_generic:
                        if vid not in self.vertex_labels:
                            lab = self._get_next_variable_label()
                            self.vertex_labels[vid] = f"*{lab}"
                            self.used_labels.add(self.vertex_labels[vid])
                        processed.add(vid)
                    else:
                        # Constants don't need a variable label
                        processed.add(vid)

            # Isolated vertices (generic first deterministically, then constants)
            vertex_ids: List[str] = [vid for vid in area if any(v.id == vid for v in self.graph.V)]
            # consider isolated if it doesn't appear in any ν of edges in this area
            incident_in_area: Set[str] = set()
            for eid in edge_ids:
                incident_in_area.update(self.graph.nu.get(eid, []))
            isolated = [vid for vid in vertex_ids if vid not in incident_in_area]
            def _vertex_key(vid: str) -> Tuple[int, str]:
                v = next((vx for vx in self.graph.V if vx.id == vid), None)
                if v is None:
                    return (2, vid)
                if v.is_generic:
                    # Use assigned label if any as sort key; else fallback to id
                    return (0, self.vertex_labels.get(vid, vid))
                return (1, v.label or vid)
            for vid in sorted(isolated, key=_vertex_key):
                v = next((vx for vx in self.graph.V if vx.id == vid), None)
                if v is None:
                    continue
                if v.is_generic and vid not in self.vertex_labels:
                    lab = self._get_next_variable_label()
                    self.vertex_labels[vid] = f"*{lab}"
                    self.used_labels.add(self.vertex_labels[vid])
                processed.add(vid)

            # Recurse into cuts deterministically
            cut_ids: List[str] = [cid for cid in area if any(c.id == cid for c in self.graph.Cut)]
            for cid in sorted(cut_ids):
                assign_in_context(cid)

        # Start at sheet
        assign_in_context(self.graph.sheet)
    
    def _get_next_variable_label(self) -> str:
        """Get next available variable label."""
        variables = ['x', 'y', 'z', 'u', 'v', 'w']
        
        if self.label_counter < len(variables):
            var = variables[self.label_counter]
        else:
            var = f'x{self.label_counter - len(variables) + 1}'
        
        self.label_counter += 1
        return var

    # --- Helpers for constants and arity ---
    def _is_constant_vertex(self, vid: str) -> bool:
        """Decide if vertex is a constant using rho when available, else legacy flags."""
        v = next((vx for vx in self.graph.V if vx.id == vid), None)
        if v is None:
            return False
        if self._rho is not None:
            cname = self._rho.get(vid)  # type: ignore[attr-defined]
            return cname is not None
        return not v.is_generic and bool(v.label)

    def _get_constant_name(self, vid: str) -> Optional[str]:
        v = next((vx for vx in self.graph.V if vx.id == vid), None)
        if v is None:
            return None
        if self._rho is not None:
            return self._rho.get(vid)  # type: ignore[attr-defined]
        return v.label

    def _format_constant(self, name: str) -> str:
        """Format constant for CGIF output: bare identifier if simple; otherwise quoted."""
        if name is None:
            return ''
        if name and self._is_simple_identifier(name):
            return name
        # escape quotes and backslashes
        esc = name.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{esc}"'

    @staticmethod
    def _is_simple_identifier(name: str) -> bool:
        import re
        return re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name) is not None

    def _validate_edge_arity(self, edge_id: str) -> None:
        if self._alphabet is None:
            return
        pred = self.graph.rel.get(edge_id, '')
        if pred in self._alphabet.ar:  # type: ignore[attr-defined]
            expected = self._alphabet.ar[pred]  # type: ignore[index]
            got = len(self.graph.nu.get(edge_id, []))
            if got != expected:
                raise ValueError(f"Arity mismatch for '{pred}': expected {expected}, got {got} (edge {edge_id})")
    
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

    # --- LCA-based definition planning (mirrors EGIF) ---
    def _compute_vertex_def_contexts(self) -> None:
        """For each generic vertex, compute the minimal common ancestor area that contains all
        its predicate occurrences and assign that as the defining context. We'll emit an
        untyped defining concept [*x] in that context.
        """
        # Build parent map for contexts (cuts); sheet has parent None
        parent: Dict[str, Optional[str]] = {}
        for cut in self.graph.Cut:
            parent[cut.id] = self.graph.get_context(cut.id)
        parent[self.graph.sheet] = None  # type: ignore

        def ancestors(ctx: Optional[str]) -> List[Optional[str]]:
            chain: List[Optional[str]] = []
            cur = ctx
            seen = set()
            while cur is not None and cur not in seen:
                seen.add(cur)
                chain.append(cur)
                cur = parent.get(cur)
            chain.append(None)
            return chain

        def lca(ctxs: List[str]) -> str:
            if not ctxs:
                return self.graph.sheet
            a0 = ctxs[0]
            a0_chain = ancestors(a0)
            aset = set(a0_chain)
            for c in ctxs[1:]:
                c_chain = ancestors(c)
                pick: Optional[str] = None
                for cand in c_chain:
                    if cand in aset:
                        pick = cand
                        break
                if pick is None:
                    return self.graph.sheet
                aset = set(ancestors(pick))
            for cand in a0_chain:
                if cand in aset and cand is not None:
                    return cand
            return self.graph.sheet

        # Collect contexts of usage for each generic vertex (via ν on edges)
        uses_by_vertex: Dict[str, List[str]] = {}
        for edge_id, vseq in self.graph.nu.items():
            edge_ctx = self.graph.get_context(edge_id)
            for vid in vseq:
                vobj = next((v for v in self.graph.V if v.id == vid), None)
                if vobj is not None and vobj.is_generic:
                    uses_by_vertex.setdefault(vid, []).append(edge_ctx)

        # Assign definition context
        self.vertex_def_context.clear()
        for vid, ctxs in uses_by_vertex.items():
            self.vertex_def_context[vid] = lca(ctxs)
    
    def _generate_area_expression(self, area_id: str) -> str:
        """Generate CGIF expression for area content."""
        elements = self._get_area_elements(area_id)
        
        cgif_parts = []
        
        # Emit planned untyped defining concepts [*x] for this area (deterministically by label)
        planned_defs: List[Tuple[str, str]] = []
        for vid, def_ctx in self.vertex_def_context.items():
            if def_ctx == area_id and vid in self.vertex_labels:
                planned_defs.append((self.vertex_labels[vid], vid))
        for label, vid in sorted(planned_defs, key=lambda x: x[0]):
            # label already includes leading '*'
            cgif_parts.append(f"[{label}]")
        
        # Generate typed concepts for monadic edges (type relations)
        processed_vertices = set()
        monadic_edges = [eid for eid in elements['edges'] if len(self.graph.nu.get(eid, [])) == 1]
        def _typed_key(eid: str) -> tuple:
            type_name = self.graph.rel.get(eid, "")
            vseq = self.graph.nu.get(eid, [])
            vid = vseq[0] if vseq else ""
            v = next((vx for vx in self.graph.V if vx.id == vid), None)
            vlabel = ""
            if v is not None:
                vlabel = (self.vertex_labels.get(vid, vid) if v.is_generic else (v.label or vid))
            return (type_name, vlabel, eid)
        for edge_id in sorted(monadic_edges, key=_typed_key):
            vertex_sequence = self.graph.nu.get(edge_id, [])
            vertex_id = vertex_sequence[0]
            concept = self._generate_typed_concept(edge_id, vertex_id)
            if concept:
                cgif_parts.append(concept)
                processed_vertices.add(vertex_id)

        # Generate concepts for vertices without type relations.
        # IMPORTANT: Generic vertices are emitted only via planned LCA-based defs above,
        # so here we include ONLY constants (non-generic) that are present without a type relation.
        remaining_vertices = []
        for vid in elements['vertices']:
            if vid in processed_vertices:
                continue
            v = next((vx for vx in self.graph.V if vx.id == vid), None)
            if v is None:
                continue
            if v.is_generic:
                # Skip generic vertices here; they are handled by planned_defs
                continue
            remaining_vertices.append(vid)
        def _vertex_key(vid: str) -> tuple:
            v = next((vx for vx in self.graph.V if vx.id == vid), None)
            if v is None:
                return (2, vid)
            if v.is_generic:
                return (0, self.vertex_labels.get(vid, vid), vid)
            else:
                return (1, v.label or vid, vid)
        for vertex_id in sorted(remaining_vertices, key=_vertex_key):
            concept = self._generate_untyped_concept(vertex_id)
            if concept:
                cgif_parts.append(concept)

        # Generate multi-argument relations (arity >= 2)
        poly_edges = [eid for eid in elements['edges'] if len(self.graph.nu.get(eid, [])) >= 2]
        def _rel_key(eid: str) -> tuple:
            pred = self.graph.rel.get(eid, "")
            vseq = self.graph.nu.get(eid, [])
            arg_labels: List[str] = []
            for vid in vseq:
                v = next((vx for vx in self.graph.V if vx.id == vid), None)
                if v is None:
                    arg_labels.append(vid)
                elif v.is_generic:
                    lab = self.vertex_labels.get(vid, vid)
                    # normalize generic to bound form for sorting without punctuation
                    arg_labels.append(lab.lstrip("*?"))
                else:
                    arg_labels.append(v.label or vid)
            return (pred, tuple(arg_labels), eid)
        for edge_id in sorted(poly_edges, key=_rel_key):
            rel = self._generate_relation(edge_id)
            if rel:
                cgif_parts.append(rel)

        # Generate negations from cuts
        for cut_id in sorted(elements['cuts']):
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
        
        if not self._is_constant_vertex(vertex_id):
            return f"[{type_name}: {vertex_label}]"
        else:
            # For constants, use the constant name (quoted if needed)
            cname = self._get_constant_name(vertex_id) or vertex.label or vertex_id
            return f"[{type_name}: {self._format_constant(cname)}]"
    
    def _generate_untyped_concept(self, vertex_id: str) -> str:
        """Generate untyped concept [*x] or [: John]."""
        vertex = next((v for v in self.graph.V if v.id == vertex_id), None)
        if not vertex:
            return ""
        
        if not self._is_constant_vertex(vertex_id):
            vertex_label = self.vertex_labels.get(vertex_id, vertex_id)
            return f"[{vertex_label}]"
        else:
            # Constant concept
            cname = self._get_constant_name(vertex_id) or vertex.label or vertex_id
            return f"[: {self._format_constant(cname)}]"
    
    def _generate_relation(self, edge_id: str) -> str:
        """Generate relation (Predicate ?x ?y)."""
        if edge_id not in self.graph.rel:
            return ""
        
        predicate = self.graph.rel[edge_id]
        
        # Get vertex arguments
        if edge_id not in self.graph.nu:
            return f"({predicate})"
        
        # Arity validation if alphabet is available
        self._validate_edge_arity(edge_id)
        vertex_sequence = self.graph.nu[edge_id]
        arguments = []
        
        for vertex_id in vertex_sequence:
            vertex = next((v for v in self.graph.V if v.id == vertex_id), None)
            if vertex:
                if not self._is_constant_vertex(vertex_id):
                    # Use bound label for generic vertices
                    label = self.vertex_labels.get(vertex_id, vertex_id)
                    if label.startswith('*'):
                        bound_label = '?' + label[1:]  # Convert *x to ?x
                    else:
                        bound_label = '?' + label
                    arguments.append(bound_label)
                else:
                    # Use constant name (quoted if needed)
                    cname = self._get_constant_name(vertex_id) or vertex.label or vertex_id
                    arguments.append(self._format_constant(cname))
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
