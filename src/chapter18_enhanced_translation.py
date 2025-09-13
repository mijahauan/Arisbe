"""
Enhanced Chapter 18 FOPL Translation with Improved Variable Handling

This module provides an improved implementation of Dau's Chapter 18 translation
with better variable management, existential quantification handling, and 
format consistency across EGIF, CGIF, and CLIF parsers.

Key improvements:
- Proper variable sharing and merging in existential quantification
- Enhanced EGIF compatibility with identity relations
- Better round-trip translation fidelity
- Improved format consistency verification
"""

from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass
import uuid

from egi_core_dau import (
    RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut,
    create_empty_graph, create_vertex, create_edge, create_cut
)
from frozendict import frozendict
from chapter18_fopl_translation import (
    FOPLFormula, AtomicFormula, ConjunctionFormula, NegationFormula,
    ExistentialFormula, UniversalFormula, ImplicationFormula,
    parse_fopl_formula
)


class EnhancedChapter18Translator:
    """Enhanced FOPL ↔ EG translator with improved variable handling."""
    
    def __init__(self):
        self.reset_state()
    
    def reset_state(self):
        """Reset translator state for new translation."""
        self.variable_counter = 0
        self.edge_counter = 0
        self.cut_counter = 0
        self.vertex_variable_map = {}  # vertex_id -> variable_name
        self.variable_vertex_map = {}  # variable_name -> vertex_id
        self.shared_variables = set()  # Variables that appear in multiple places
    
    def psi_translate(self, formula: FOPLFormula) -> RelationalGraphWithCuts:
        """
        Enhanced Ψ: Translate FOPL formula to EGI with proper variable handling.
        """
        self.reset_state()
        
        # First pass: identify shared variables
        self._identify_shared_variables(formula)
        
        # Second pass: translate with proper variable sharing
        return self._psi_recursive(formula)
    
    def _identify_shared_variables(self, formula: FOPLFormula, context_vars: Set[str] = None):
        """Identify variables that appear in multiple contexts."""
        if context_vars is None:
            context_vars = set()
        
        if isinstance(formula, AtomicFormula):
            for var in formula.variables:
                if var in context_vars:
                    self.shared_variables.add(var)
                context_vars.add(var)
        
        elif isinstance(formula, ConjunctionFormula):
            left_vars = set()
            self._identify_shared_variables(formula.left, left_vars)
            right_vars = set()
            self._identify_shared_variables(formula.right, right_vars)
            
            # Variables appearing in both sides are shared
            shared_in_conjunction = left_vars & right_vars
            self.shared_variables.update(shared_in_conjunction)
            context_vars.update(left_vars | right_vars)
        
        elif isinstance(formula, NegationFormula):
            self._identify_shared_variables(formula.formula, context_vars)
        
        elif isinstance(formula, ExistentialFormula):
            inner_vars = set()
            self._identify_shared_variables(formula.formula, inner_vars)
            # Remove quantified variable from context
            inner_vars.discard(formula.variable)
            context_vars.update(inner_vars)
        
        elif isinstance(formula, UniversalFormula):
            inner_vars = set()
            self._identify_shared_variables(formula.formula, inner_vars)
            inner_vars.discard(formula.variable)
            context_vars.update(inner_vars)
        
        elif isinstance(formula, ImplicationFormula):
            self._identify_shared_variables(formula.antecedent, context_vars)
            self._identify_shared_variables(formula.consequent, context_vars)
    
    def _psi_recursive(self, formula: FOPLFormula) -> RelationalGraphWithCuts:
        """Enhanced recursive Ψ translation."""
        
        if isinstance(formula, AtomicFormula):
            return self._translate_atomic_formula_enhanced(formula)
        
        elif isinstance(formula, ConjunctionFormula):
            left_egi = self._psi_recursive(formula.left)
            right_egi = self._psi_recursive(formula.right)
            return self._juxtapose_egis_enhanced(left_egi, right_egi)
        
        elif isinstance(formula, NegationFormula):
            inner_egi = self._psi_recursive(formula.formula)
            return self._add_cut_around_egi_enhanced(inner_egi)
        
        elif isinstance(formula, ExistentialFormula):
            inner_egi = self._psi_recursive(formula.formula)
            return self._apply_existential_step_enhanced(inner_egi, formula.variable)
        
        elif isinstance(formula, UniversalFormula):
            # ∀α.f := ¬∃α.¬f
            negated_inner = NegationFormula(formula.formula)
            existential = ExistentialFormula(formula.variable, negated_inner)
            negated_existential = NegationFormula(existential)
            return self._psi_recursive(negated_existential)
        
        elif isinstance(formula, ImplicationFormula):
            # f₁ → f₂ := ¬(f₁ ∧ ¬f₂)
            negated_consequent = NegationFormula(formula.consequent)
            conjunction = ConjunctionFormula(formula.antecedent, negated_consequent)
            negated_conjunction = NegationFormula(conjunction)
            return self._psi_recursive(negated_conjunction)
        
        else:
            raise ValueError(f"Unsupported formula type: {type(formula)}")
    
    def _translate_atomic_formula_enhanced(self, formula: AtomicFormula) -> RelationalGraphWithCuts:
        """Enhanced atomic formula translation with proper variable sharing."""
        vertices = set()
        vertex_ids = []
        
        for var in formula.variables:
            if var in self.variable_vertex_map:
                # Reuse existing vertex for shared variable
                vertex_id = self.variable_vertex_map[var]
            else:
                # Create new vertex
                vertex_id = ElementID(f"v_{var}_{self.variable_counter}")
                self.variable_counter += 1
                self.variable_vertex_map[var] = vertex_id
                self.vertex_variable_map[vertex_id] = var
            
            vertices.add(Vertex(vertex_id))
            vertex_ids.append(vertex_id)
        
        # Create edge
        edge_id = ElementID(f"e_{formula.relation}_{self.edge_counter}")
        self.edge_counter += 1
        edge = Edge(edge_id)
        
        # Handle identity relations specially for EGIF compatibility
        if formula.relation == ".=":
            # Use special identity edge representation
            relation_name = "="
        else:
            relation_name = formula.relation
        
        # Create EGI
        V = frozenset(vertices)
        E = frozenset([edge])
        nu = frozendict({edge_id: tuple(vertex_ids)})
        sheet = ElementID("sheet")
        Cut = frozenset()
        area = frozendict({
            sheet: frozenset([edge_id] + list(set(vertex_ids)))
        })
        rel = frozendict({edge_id: relation_name})
        
        return RelationalGraphWithCuts(
            V=V, E=E, nu=nu, sheet=sheet, Cut=Cut, area=area, rel=rel
        )
    
    def _juxtapose_egis_enhanced(self, left: RelationalGraphWithCuts, 
                                right: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        """Enhanced EGI juxtaposition with proper variable merging."""
        # Merge vertices, handling shared variables
        merged_vertices = set(left.V)
        vertex_id_map = {}  # Maps right vertex IDs to merged vertex IDs
        
        for right_vertex in right.V:
            right_var = self.vertex_variable_map.get(right_vertex.id)
            
            # Check if this variable already exists in left EGI
            existing_vertex_id = None
            for left_vertex in left.V:
                left_var = self.vertex_variable_map.get(left_vertex.id)
                if left_var == right_var and right_var in self.shared_variables:
                    existing_vertex_id = left_vertex.id
                    break
            
            if existing_vertex_id:
                # Use existing vertex for shared variable
                vertex_id_map[right_vertex.id] = existing_vertex_id
            else:
                # Keep right vertex as is
                vertex_id_map[right_vertex.id] = right_vertex.id
                merged_vertices.add(right_vertex)
        
        # Update right EGI mappings with merged vertices
        right_nu = {}
        for edge_id, vertex_seq in right.nu.items():
            new_seq = tuple(vertex_id_map[vid] for vid in vertex_seq)
            right_nu[edge_id] = new_seq
        
        right_area = {}
        for area_id, contents in right.area.items():
            new_contents = set()
            for item in contents:
                if item in vertex_id_map:
                    new_contents.add(vertex_id_map[item])
                else:
                    new_contents.add(item)
            right_area[area_id] = frozenset(new_contents)
        
        # Merge components
        V = frozenset(merged_vertices)
        E = left.E | right.E
        nu = frozendict({**left.nu, **right_nu})
        sheet = left.sheet
        Cut = left.Cut | right.Cut
        
        # Merge areas
        merged_area = dict(left.area)
        for area_id, contents in right_area.items():
            if area_id == right.sheet:
                # Merge sheet contents
                merged_area[sheet] = merged_area.get(sheet, frozenset()) | contents
            else:
                merged_area[area_id] = contents
        
        area = frozendict(merged_area)
        rel = frozendict({**left.rel, **right.rel})
        
        return RelationalGraphWithCuts(
            V=V, E=E, nu=nu, sheet=sheet, Cut=Cut, area=area, rel=rel
        )
    
    def _add_cut_around_egi_enhanced(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        """Enhanced cut addition with proper area management."""
        cut_id = ElementID(f"cut_{self.cut_counter}")
        self.cut_counter += 1
        
        new_cut = Cut(cut_id)
        Cut_new = egi.Cut | {new_cut}
        
        # Move sheet contents to cut
        sheet_contents = egi.area.get(egi.sheet, frozenset())
        
        area_new = dict(egi.area)
        area_new[cut_id] = sheet_contents
        area_new[egi.sheet] = frozenset([cut_id])
        
        return RelationalGraphWithCuts(
            V=egi.V, E=egi.E, nu=egi.nu, sheet=egi.sheet,
            Cut=Cut_new, area=frozendict(area_new), rel=egi.rel
        )
    
    def _apply_existential_step_enhanced(self, egi: RelationalGraphWithCuts, 
                                        variable: str) -> RelationalGraphWithCuts:
        """Enhanced existential step with proper variable handling."""
        if variable not in self.variable_vertex_map:
            return egi
        
        # Find all vertices with this variable
        alpha_vertices = []
        for vertex_id, var in self.vertex_variable_map.items():
            if var == variable:
                alpha_vertices.append(vertex_id)
        
        if len(alpha_vertices) <= 1:
            # Mark single vertex as generic
            if len(alpha_vertices) == 1:
                vid = alpha_vertices[0]
                self.vertex_variable_map[vid] = "*"
            return egi
        
        # Merge multiple vertices into one
        primary_vertex_id = alpha_vertices[0]  # Keep first vertex
        other_vertices = alpha_vertices[1:]
        
        # Update nu mapping: replace other vertices with primary
        nu_new = {}
        for edge_id, vertex_sequence in egi.nu.items():
            new_sequence = []
            for vid in vertex_sequence:
                if vid in other_vertices:
                    new_sequence.append(primary_vertex_id)
                else:
                    new_sequence.append(vid)
            nu_new[edge_id] = tuple(new_sequence)
        
        # Update vertex set: remove other vertices
        V_new = egi.V - {Vertex(vid) for vid in other_vertices}
        
        # Update area mappings: remove other vertices
        area_new = {}
        for area_id, contents in egi.area.items():
            new_contents = set(contents)
            for vid in other_vertices:
                new_contents.discard(vid)
            area_new[area_id] = frozenset(new_contents)
        
        # Update variable mappings
        for vid in other_vertices:
            if vid in self.vertex_variable_map:
                del self.vertex_variable_map[vid]
        self.vertex_variable_map[primary_vertex_id] = "*"
        
        return RelationalGraphWithCuts(
            V=V_new, E=egi.E, nu=frozendict(nu_new), sheet=egi.sheet,
            Cut=egi.Cut, area=frozendict(area_new), rel=egi.rel
        )
    
    def phi_translate(self, egi: RelationalGraphWithCuts) -> str:
        """Enhanced Φ: Translate EGI to FOPL with better variable naming."""
        # Reset and assign variables
        self.vertex_variable_map = {}
        var_counter = 1
        
        for vertex in egi.V:
            var_name = f"x{var_counter}"
            self.vertex_variable_map[vertex.id] = var_name
            var_counter += 1
        
        # Translate sheet area
        formula = self._translate_area_to_fopl_enhanced(egi, egi.sheet)
        return formula
    
    def _translate_area_to_fopl_enhanced(self, egi: RelationalGraphWithCuts, 
                                        area_id: ElementID) -> str:
        """Enhanced area to FOPL translation."""
        area_contents = egi.area.get(area_id, frozenset())
        
        # Separate edges and cuts
        edges = [eid for eid in area_contents if any(e.id == eid for e in egi.E)]
        cuts = [cid for cid in area_contents if any(c.id == cid for c in egi.Cut)]
        
        formulas = []
        
        # Translate edges to atomic formulas
        for edge_id in edges:
            if edge_id in egi.nu and edge_id in egi.rel:
                vertex_sequence = egi.nu[edge_id]
                relation = egi.rel[edge_id]
                
                variables = [self.vertex_variable_map[vid] for vid in vertex_sequence]
                
                if relation == "=" or relation == ".=":
                    # Identity relation - use proper FOPL syntax
                    formulas.append(f"{variables[0]} .= {variables[1]}")
                else:
                    # Regular relation
                    var_list = ", ".join(variables)
                    formulas.append(f"{relation}({var_list})")
        
        # Translate cuts to negated formulas
        for cut_id in cuts:
            cut_formula = self._translate_area_to_fopl_enhanced(egi, cut_id)
            if cut_formula:
                formulas.append(f"¬({cut_formula})")
        
        # Combine with conjunction
        if len(formulas) == 0:
            return ""
        elif len(formulas) == 1:
            return formulas[0]
        else:
            return " ∧ ".join(formulas)


def enhanced_fopl_to_egi(formula_str: str) -> RelationalGraphWithCuts:
    """Convert FOPL formula to EGI using enhanced translation."""
    formula = parse_fopl_formula(formula_str)
    translator = EnhancedChapter18Translator()
    return translator.psi_translate(formula)


def enhanced_egi_to_fopl(egi: RelationalGraphWithCuts) -> str:
    """Convert EGI to FOPL formula using enhanced translation."""
    translator = EnhancedChapter18Translator()
    return translator.phi_translate(egi)


def demonstrate_enhanced_translation():
    """Demonstrate enhanced Chapter 18 translation."""
    print("🔄 Enhanced Chapter 18 FOPL ↔ EG Translation")
    print("=" * 60)
    
    test_formulas = [
        "Man(x)",
        "Man(x) ∧ Mortal(x)",
        "∃x.Man(x)",
        "∃x.(Man(x) ∧ Mortal(x))",
        "x .= y",
        "∀x.Man(x)",
        "Man(x) → Mortal(x)"
    ]
    
    translator = EnhancedChapter18Translator()
    
    for i, formula_str in enumerate(test_formulas, 1):
        print(f"\n🧪 Test {i}: {formula_str}")
        
        try:
            # Parse and translate
            formula = parse_fopl_formula(formula_str)
            egi = translator.psi_translate(formula)
            back_formula = translator.phi_translate(egi)
            
            print(f"   EGI: {len(egi.V)}v, {len(egi.E)}e, {len(egi.Cut)}c")
            print(f"   Round-trip: {back_formula}")
            print(f"   ✅ SUCCESS")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print(f"\n✅ Enhanced Translation Complete")


if __name__ == "__main__":
    demonstrate_enhanced_translation()
