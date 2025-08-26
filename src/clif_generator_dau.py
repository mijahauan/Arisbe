"""
Dau-compliant CLIF (Common Logic Interchange Format) generator.
Converts RelationalGraphWithCuts structures to CLIF expressions.

CLIF Generation Strategy:
- Atomic formulas from edges: (P x y)
- Negation from cuts: (not ...)
- Conjunction from multiple elements in same area: (and ...)
- Variable scoping handled through quantification
- Proper parenthesization and formatting

Maintains same rigor as EGIF generator with proper variable management.
"""

from typing import Dict, Set, List, Optional, Tuple
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID


class CLIFGenerator:
    """Generates CLIF expressions from Dau-compliant graphs."""
    
    def __init__(self, graph: Optional[RelationalGraphWithCuts] = None):
        # Allow optional graph for legacy API compatibility
        self.graph = graph
        self.vertex_labels = {}  # Maps vertex IDs to CLIF variable names
        self.used_labels = set()
        self.variable_counter = 0
        
    def generate(self) -> str:
        """Generate CLIF expression from graph."""
        if self.graph is None:
            raise TypeError("CLIFGenerator.generate() called without a graph. Provide one in constructor or use generate_clif(graph).")
        # Assign variable names to vertices
        self._assign_vertex_labels()
        
        # Generate CLIF for sheet area (top level)
        sheet_elements = self._get_area_elements(self.graph.sheet)
        
        if not sheet_elements:
            return ""
        
        # Generate expression for sheet content
        clif_expr = self._generate_area_expression(self.graph.sheet)
        
        return clif_expr.strip()

    # Legacy-friendly instance method used by tests
    def generate_clif(self, graph: RelationalGraphWithCuts) -> str:
        """Legacy API: clif_gen.generate_clif(graph) -> str"""
        self.graph = graph
        return self.generate()
    
    def _assign_vertex_labels(self):
        """Assign CLIF variable names to vertices, preserving ν order like EGIF/CGIF."""
        self.vertex_labels = {}
        self.used_labels = set()
        self.variable_counter = 0

        processed: Set[str] = set()

        def assign_in_context(ctx_id: str) -> None:
            area = self.graph.area.get(ctx_id, set())

            # Edges sorted by (predicate, ν vertex ids)
            edge_ids: List[str] = [eid for eid in area if any(e.id == eid for e in self.graph.E)]
            def _edge_key(eid: str) -> tuple:
                pred = self.graph.rel.get(eid, "")
                vseq = tuple(self.graph.nu.get(eid, []))
                return (pred, vseq)
            for eid in sorted(edge_ids, key=_edge_key):
                vseq = self.graph.nu.get(eid, [])
                for vid in vseq:
                    v = next((vx for vx in self.graph.V if vx.id == vid), None)
                    if v is None:
                        continue
                    if v.is_generic and vid not in self.vertex_labels:
                        label = self._get_next_variable_name()
                        self.vertex_labels[vid] = label
                        self.used_labels.add(label)
                    processed.add(vid)

            # Isolated vertices: ensure generics get labels too
            vertex_ids: List[str] = [vid for vid in area if any(v.id == vid for v in self.graph.V)]
            incident_in_area: Set[str] = set()
            for eid in edge_ids:
                incident_in_area.update(self.graph.nu.get(eid, []))
            isolated = [vid for vid in vertex_ids if vid not in incident_in_area]
            def _vertex_key(vid: str) -> tuple:
                v = next((vx for vx in self.graph.V if vx.id == vid), None)
                if v is None:
                    return (2, vid)
                if v.is_generic:
                    return (0, self.vertex_labels.get(vid, vid))
                return (1, v.label or vid)
            for vid in sorted(isolated, key=_vertex_key):
                v = next((vx for vx in self.graph.V if vx.id == vid), None)
                if v is None:
                    continue
                if v.is_generic and vid not in self.vertex_labels:
                    label = self._get_next_variable_name()
                    self.vertex_labels[vid] = label
                    self.used_labels.add(label)
                processed.add(vid)

            # Recurse into cuts deterministically
            cut_ids: List[str] = [cid for cid in area if any(c.id == cid for c in self.graph.Cut)]
            for cid in sorted(cut_ids):
                assign_in_context(cid)

        assign_in_context(self.graph.sheet)
    
    def _get_next_variable_name(self) -> str:
        """Get next available variable name."""
        variables = ['x', 'y', 'z', 'u', 'v', 'w']
        
        if self.variable_counter < len(variables):
            var = variables[self.variable_counter]
        else:
            var = f'x{self.variable_counter - len(variables) + 1}'
        
        self.variable_counter += 1
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
        """Generate CLIF expression for area content."""
        elements = self._get_area_elements(area_id)
        
        # Generate atomic formulas from edges
        atomic_formulas = []
        def _edge_key(eid: str) -> tuple:
            pred = self.graph.rel.get(eid, "")
            vseq = self.graph.nu.get(eid, [])
            arg_labels: List[str] = []
            for vid in vseq:
                lab = self.vertex_labels.get(vid, vid)
                arg_labels.append(lab)
            return (pred, tuple(arg_labels), eid)
        for edge_id in sorted(elements['edges'], key=_edge_key):
            formula = self._generate_atomic_formula(edge_id)
            if formula:
                atomic_formulas.append(formula)
        
        # Generate negations from cuts
        negations = []
        for cut_id in sorted(elements['cuts']):
            negation = self._generate_cut_expression(cut_id)
            if negation:
                negations.append(negation)
        
        # Combine all formulas
        all_formulas = atomic_formulas + negations
        
        if len(all_formulas) == 0:
            return ""
        elif len(all_formulas) == 1:
            return all_formulas[0]
        else:
            # Multiple formulas - use conjunction
            return f"(and {' '.join(all_formulas)})"
    
    def _generate_atomic_formula(self, edge_id: str) -> str:
        """Generate atomic formula from edge."""
        if edge_id not in self.graph.rel:
            return ""
        
        predicate = self.graph.rel[edge_id]
        
        # Get vertex arguments
        if edge_id not in self.graph.nu:
            return f"({predicate})"
        
        vertex_sequence = self.graph.nu[edge_id]
        arguments = []
        
        for vertex_id in vertex_sequence:
            v = next((vx for vx in self.graph.V if vx.id == vertex_id), None)
            if v is None:
                arguments.append(vertex_id)
                continue
            if v.is_generic:
                # Use the assigned variable label
                arguments.append(self.vertex_labels.get(vertex_id, vertex_id))
            else:
                # Use constant name directly
                arguments.append(v.label or vertex_id)
        
        if arguments:
            return f"({predicate} {' '.join(arguments)})"
        else:
            return f"({predicate})"
    
    def _generate_cut_expression(self, cut_id: str) -> str:
        """Generate negation expression from cut."""
        cut_content = self._generate_area_expression(cut_id)
        
        if not cut_content:
            return ""
        
        return f"(not {cut_content})"
    
    def _get_free_variables(self, area_id: str) -> Set[str]:
        """Get free variables in area (for quantification)."""
        free_vars = set()
        elements = self._get_area_elements(area_id)
        
        # Collect variables from edges in this area
        for edge_id in elements['edges']:
            if edge_id in self.graph.nu:
                for vertex_id in self.graph.nu[edge_id]:
                    if vertex_id in self.vertex_labels:
                        free_vars.add(self.vertex_labels[vertex_id])
        
        # Recursively collect from cuts
        for cut_id in elements['cuts']:
            free_vars.update(self._get_free_variables(cut_id))
        
        return free_vars
    
    def generate_with_quantification(self) -> str:
        """Generate CLIF with explicit quantification."""
        if self.graph is None:
            raise TypeError("CLIFGenerator.generate_with_quantification() requires a graph.")
        # Get all free variables in sheet
        free_vars = self._get_free_variables(self.graph.sheet)
        
        # Generate main expression
        main_expr = self._generate_area_expression(self.graph.sheet)
        
        if not main_expr:
            return ""
        
        # Add universal quantification for free variables
        if free_vars:
            var_list = ' '.join(sorted(free_vars))
            return f"(forall ({var_list}) {main_expr})"
        else:
            return main_expr


# Factory function
def generate_clif(egi: RelationalGraphWithCuts) -> str:
    """Generate CLIF expression from EGI structure."""
    generator = CLIFGenerator(egi)
    return generator.generate()


def generate_clif_with_quantification(egi: RelationalGraphWithCuts) -> str:
    """Generate CLIF expression with explicit quantification."""
    generator = CLIFGenerator(egi)
    return generator.generate_with_quantification()
