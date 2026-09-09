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

from typing import Any, Dict, List, Optional, Set, Tuple

from canonical_signature import compute_canonical_signatures
from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex


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
        # UUID-independent canonical signatures (populated in generate()).
        self._vertex_sig: Dict[ElementID, Any] = {}
        self._edge_sig: Dict[ElementID, Any] = {}
        self._cut_sig: Dict[ElementID, Any] = {}

    def generate(self) -> str:
        """Generate CGIF expression from graph."""
        if self.graph is None:
            raise TypeError(
                "CGIFGenerator.generate() called without a graph. Provide one in constructor or use generate_cgif(graph)."
            )
        # B-min: no linear syntax for the second-order layer (named limit).
        from second_order_limits import refuse_second_order_in_linear_form
        refuse_second_order_in_linear_form(self.graph, "CGIF")
        # Cache helpers
        self._rho = getattr(self.graph, "rho", None)
        self._alphabet = getattr(self.graph, "alphabet", None)
        # Compute canonical structural signatures so all subsequent sort keys
        # are UUID-independent (issue #6).
        self._vertex_sig, self._edge_sig, self._cut_sig = (
            compute_canonical_signatures(self.graph)
        )
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

            # Edges sorted by canonical structural signature (UUID-independent).
            edge_ids: List[str] = [
                eid for eid in area if any(e.id == eid for e in self.graph.E)
            ]

            for eid in sorted(edge_ids, key=lambda e: self._edge_sig[e]):
                vseq = self.graph.nu.get(eid, [])
                for vid in vseq:
                    v = next((vx for vx in self.graph.V if vx.id == vid), None)
                    if v is None:
                        continue
                    if v.is_generic:
                        if vid not in self.vertex_labels:
                            lab = self._get_next_variable_label()
                            self.vertex_labels[vid] = lab
                            self.used_labels.add(lab)
                        processed.add(vid)
                    else:
                        # Constants don't need a variable label
                        processed.add(vid)

            # Isolated vertices (generic first deterministically, then constants)
            vertex_ids: List[str] = [
                vid for vid in area if any(v.id == vid for v in self.graph.V)
            ]
            # consider isolated if it doesn't appear in any ν of edges in this area
            incident_in_area: Set[str] = set()
            for eid in edge_ids:
                incident_in_area.update(self.graph.nu.get(eid, []))
            isolated = [vid for vid in vertex_ids if vid not in incident_in_area]

            def _vertex_key(vid: str) -> Tuple[int, Any]:
                v = next((vx for vx in self.graph.V if vx.id == vid), None)
                if v is None:
                    return (2, self._vertex_sig.get(vid, ""))
                if v.is_generic:
                    return (0, self._vertex_sig.get(vid, ""))
                return (1, self._vertex_sig.get(vid, ""))

            for vid in sorted(isolated, key=_vertex_key):
                v = next((vx for vx in self.graph.V if vx.id == vid), None)
                if v is None:
                    continue
                if v.is_generic and vid not in self.vertex_labels:
                    lab = self._get_next_variable_label()
                    self.vertex_labels[vid] = lab
                    self.used_labels.add(lab)
                processed.add(vid)

            # Recurse into cuts in canonical structural order.
            cut_ids: List[str] = [
                cid for cid in area if any(c.id == cid for c in self.graph.Cut)
            ]
            for cid in sorted(cut_ids, key=lambda c: self._cut_sig[c]):
                assign_in_context(cid)

        # Start at sheet
        assign_in_context(self.graph.sheet)

    def _get_next_variable_label(self) -> str:
        """Get next available variable label."""
        variables = ["x", "y", "z", "u", "v", "w"]

        if self.label_counter < len(variables):
            var = variables[self.label_counter]
        else:
            var = f"x{self.label_counter - len(variables) + 1}"

        self.label_counter += 1
        return var

    # --- Helpers for constants and arity ---
    def _is_constant_vertex(self, vid: str) -> bool:
        """Decide if vertex is a constant using rho when available, else legacy flags."""
        v = next((vx for vx in self.graph.V if vx.id == vid), None)
        if v is None:
            return False
        if self._rho is not None and self._rho:  # Check if rho exists and is not empty
            cname = self._rho.get(vid)  # type: ignore[attr-defined]
            return cname is not None
        return not v.is_generic and bool(v.label)

    def _get_constant_name(self, vid: str) -> Optional[str]:
        v = next((vx for vx in self.graph.V if vx.id == vid), None)
        if v is None:
            return None
        if self._rho is not None and self._rho:  # Check if rho exists and is not empty
            return self._rho.get(vid)  # type: ignore[attr-defined]
        return v.label

    def _format_constant(self, name: str) -> str:
        """Format constant for CGIF output: bare identifier if simple; otherwise quoted."""
        if name is None:
            return ""
        if name and self._is_simple_identifier(name):
            return name
        # escape quotes and backslashes
        esc = name.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{esc}"'

    @staticmethod
    def _is_simple_identifier(name: str) -> bool:
        import re

        return re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name) is not None

    def _validate_edge_arity(self, edge_id: str) -> None:
        if self._alphabet is None:
            return
        pred = self.graph.rel.get(edge_id, "")
        if pred in self._alphabet.ar:  # type: ignore[attr-defined]
            expected = self._alphabet.ar[pred]  # type: ignore[index]
            got = len(self.graph.nu.get(edge_id, []))
            if got != expected:
                raise ValueError(
                    f"Arity mismatch for '{pred}': expected {expected}, got {got} (edge {edge_id})"
                )

    def _get_area_elements(self, area_id: str) -> Dict[str, List[str]]:
        """Get elements in specified area, categorized by type."""
        elements = {"vertices": [], "edges": [], "cuts": []}

        if area_id not in self.graph.area:
            return elements

        area_elements = self.graph.area[area_id]

        for element_id in area_elements:
            # Check if it's a vertex
            if any(v.id == element_id for v in self.graph.V):
                elements["vertices"].append(element_id)
            # Check if it's an edge
            elif any(e.id == element_id for e in self.graph.E):
                elements["edges"].append(element_id)
            # Check if it's a cut
            elif any(c.id == element_id for c in self.graph.Cut):
                elements["cuts"].append(element_id)

        return elements

    # --- LCA-based definition planning (mirrors EGIF) ---
    def _compute_vertex_def_contexts(self) -> None:
        """Decide the area in which each generic vertex's defining concept is written.

        The area is the least common ancestor of the vertex's occurrences **and
        of the area the graph itself puts the vertex in**. Including the
        vertex's own area is what keeps the placement honest: a line that sits
        outside all of its uses used to be written at the least common area of
        the uses alone, which moved it *inward*, and a line moved inward
        crosses a cut boundary into a context of the opposite polarity. So
        ``~[ *z ~[ (P z) ] ]`` — z at odd depth, read universally — was emitted
        with z one cut deeper and came back existential. Hoisting is outward
        only, in this direction as in the parser's.

        A vertex on no edge at all has no occurrences to gather, and used to be
        absent from the map and therefore written nowhere. It is written in its
        own area, like every other.
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

        # Seed each generic vertex with the area the graph puts it in, so that a
        # vertex with no occurrences is still placed and a vertex outside its
        # occurrences is never drawn inside them.
        uses_by_vertex: Dict[str, List[str]] = {
            v.id: [self.graph.get_context(v.id)]
            for v in self.graph.V
            if v.is_generic
        }
        for edge_id, vseq in self.graph.nu.items():
            edge_ctx = self.graph.get_context(edge_id)
            for vid in vseq:
                if vid in uses_by_vertex:
                    uses_by_vertex[vid].append(edge_ctx)

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
            cgif_parts.append(f"[* {label}]")

        # Generate typed concepts for monadic edges (type relations)
        processed_vertices = set()
        monadic_edges = [
            eid for eid in elements["edges"] if len(self.graph.nu.get(eid, [])) == 1
        ]

        for edge_id in sorted(monadic_edges, key=lambda e: self._edge_sig[e]):
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
        for vid in elements["vertices"]:
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
                return (2, self._vertex_sig.get(vid, ""))
            if v.is_generic:
                return (0, self._vertex_sig.get(vid, ""))
            return (1, self._vertex_sig.get(vid, ""))

        for vertex_id in sorted(remaining_vertices, key=_vertex_key):
            concept = self._generate_untyped_concept(vertex_id)
            if concept:
                cgif_parts.append(concept)

        # Generate relations with no arguments at all.
        #
        # These used to fall between the two buckets: monadic collected arity 1
        # and poly collected arity >= 2, so an edge of arity 0 was emitted by
        # neither and vanished. A graph made only of them — which is every
        # propositional exemplar in the corpus, de_morgan and peirce_law and
        # theorem_praeclarum among them — generated the empty string and read
        # back as the blank sheet.
        nullary_edges = [
            eid for eid in elements["edges"] if len(self.graph.nu.get(eid, [])) == 0
        ]

        for edge_id in sorted(nullary_edges, key=lambda e: self._edge_sig[e]):
            rel = self._generate_relation(edge_id)
            if rel:
                cgif_parts.append(rel)

        # Generate multi-argument relations (arity >= 2)
        poly_edges = [
            eid for eid in elements["edges"] if len(self.graph.nu.get(eid, [])) >= 2
        ]

        for edge_id in sorted(poly_edges, key=lambda e: self._edge_sig[e]):
            rel = self._generate_relation(edge_id)
            if rel:
                cgif_parts.append(rel)

        # Generate negations from cuts in canonical structural order.
        for cut_id in sorted(elements["cuts"], key=lambda c: self._cut_sig[c]):
            negation = self._generate_cut_expression(cut_id)
            if negation:
                cgif_parts.append(negation)

        return " ".join(cgif_parts)

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
            # Check if this is the defining context for the vertex
            if self.vertex_def_context.get(vertex_id) == self.graph.get_context(edge_id):
                return f"[{type_name}: *{vertex_label}]"
            else:
                return f"[{type_name}: ?{vertex_label}]"
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
            return f"[* {vertex_label}]"
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
                    arguments.append(f"?{label}")
                else:
                    # Use constant name (quoted if needed)
                    cname = (
                        self._get_constant_name(vertex_id) or vertex.label or vertex_id
                    )
                    arguments.append(self._format_constant(cname))
            else:
                arguments.append(vertex_id)

        if arguments:
            return f"({predicate} {' '.join(arguments)})"
        else:
            return f"({predicate})"

    def _generate_cut_expression(self, cut_id: str) -> str:
        """Generate negation expression ~[CG].

        An empty cut is written ``~[]`` rather than dropped. It is a cut like
        any other — the *hold* of the world-scroll is exactly this, an empty
        sibling that keeps the enclosing negation vacuously true — and it
        carries the same meaning whether or not anything is scribed inside it.
        Returning "" here removed one cut from every M-bearing graph in the
        corpus on the way out.
        """
        cut_content = self._generate_area_expression(cut_id)

        return f"~[{cut_content}]"


# Factory function
def generate_cgif(egi: RelationalGraphWithCuts) -> str:
    """Generate CGIF expression from EGI structure."""
    generator = CGIFGenerator(egi)
    return generator.generate()
