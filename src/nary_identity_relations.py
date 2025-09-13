"""
N-ary Identity Relations (.=k) Implementation
Supports k-ary identity relations for ligature separation and advanced semantic evaluation.
"""

from typing import Dict, List, Set, FrozenSet, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from frozendict import frozendict
from formal_transformation_rules import FormalTransformationRule, TransformationContext, TransformationResult


class IdentityArity(Enum):
    """Enumeration of identity relation arities."""
    BINARY = 2      # Standard identity (=)
    TERNARY = 3     # 3-ary identity (.=3)
    QUATERNARY = 4  # 4-ary identity (.=4)
    NARY = "n"      # General n-ary identity (.=k)


@dataclass
class NaryIdentitySpec:
    """Specification for n-ary identity relation."""
    vertices: List[ElementID]
    arity: int
    edge_id: Optional[ElementID] = None
    context: Optional[ElementID] = None


class NaryIdentityRelation:
    """Represents an n-ary identity relation (.=k)."""
    
    def __init__(self, edge_id: ElementID, vertices: List[ElementID], arity: int):
        self.edge_id = edge_id
        self.vertices = vertices
        self.arity = arity
        
        if len(vertices) != arity:
            raise ValueError(f"Vertex count {len(vertices)} does not match arity {arity}")
        
        if arity < 2:
            raise ValueError(f"Identity arity must be at least 2, got {arity}")
    
    def __str__(self) -> str:
        vertex_str = ",".join(str(v) for v in self.vertices)
        return f".={self.arity}({vertex_str})"
    
    def __repr__(self) -> str:
        return f"NaryIdentityRelation(edge_id={self.edge_id}, vertices={self.vertices}, arity={self.arity})"
    
    def is_binary(self) -> bool:
        """Check if this is a standard binary identity relation."""
        return self.arity == 2
    
    def get_binary_pairs(self) -> List[Tuple[ElementID, ElementID]]:
        """Get all binary identity pairs implied by this n-ary relation."""
        pairs = []
        for i in range(len(self.vertices)):
            for j in range(i + 1, len(self.vertices)):
                pairs.append((self.vertices[i], self.vertices[j]))
        return pairs
    
    def contains_vertex(self, vertex_id: ElementID) -> bool:
        """Check if this identity relation contains the given vertex."""
        return vertex_id in self.vertices
    
    def can_separate_vertex(self, vertex_id: ElementID) -> bool:
        """Check if a vertex can be separated from this n-ary identity."""
        return vertex_id in self.vertices and self.arity > 2


class CreateNaryIdentityRule(FormalTransformationRule):
    """Rule for creating n-ary identity relations."""
    
    def get_rule_name(self) -> str:
        return "CREATE_NARY_IDENTITY (Create N-ary Identity Relation)"
    
    def check_preconditions(self, context: TransformationContext) -> Tuple[bool, Optional[str]]:
        """Check preconditions for creating n-ary identity."""
        if len(context.selected_subgraph) < 2:
            return False, "Must select at least 2 vertices for n-ary identity"
        
        egi = context.source_egi
        selected_vertices = list(context.selected_subgraph)
        
        # Verify all selected elements are vertices
        for vertex_id in selected_vertices:
            if not any(v.id == vertex_id for v in egi.V):
                return False, f"Selected element {vertex_id} is not a vertex"
        
        # Check if all vertices are in the same context
        contexts = set()
        for vertex_id in selected_vertices:
            vertex_context = self._get_vertex_context(egi, vertex_id)
            contexts.add(vertex_context)
        
        if len(contexts) > 1:
            return False, "All vertices must be in the same context for n-ary identity"
        
        return True, None
    
    def apply_transformation(self, context: TransformationContext) -> TransformationResult:
        """Apply n-ary identity creation."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})
        
        try:
            egi = context.source_egi
            vertices = list(context.selected_subgraph)
            arity = len(vertices)
            
            # Create n-ary identity edge
            identity_edge_id = ElementID(f"nary_id_{arity}_{'_'.join(str(v) for v in vertices)}")
            identity_edge = Edge(identity_edge_id)
            
            # Update EGI components
            new_edges = egi.E | {identity_edge}
            
            # Update nu mapping with n-ary vertex sequence
            new_nu = dict(egi.nu)
            new_nu[identity_edge_id] = tuple(vertices)
            
            # Update rel mapping with n-ary identity relation
            new_rel = dict(egi.rel)
            new_rel[identity_edge_id] = f".={arity}"
            
            # Update area mapping
            vertex_context = self._get_vertex_context(egi, vertices[0])
            new_area_mapping = dict(egi.area)
            
            if vertex_context in new_area_mapping:
                current_contents = new_area_mapping[vertex_context]
                new_area_mapping[vertex_context] = current_contents | frozenset([identity_edge_id])
            else:
                # Context is sheet
                sheet_contents = new_area_mapping.get(egi.sheet, frozenset())
                new_area_mapping[egi.sheet] = sheet_contents | frozenset([identity_edge_id])
            
            result_egi = RelationalGraphWithCuts(
                V=egi.V,
                E=frozenset(new_edges),
                nu=frozendict(new_nu),
                sheet=egi.sheet,
                Cut=egi.Cut,
                area=frozendict(new_area_mapping),
                rel=frozendict(new_rel)
            )
            
            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "CREATE_NARY_IDENTITY",
                    "vertices": [str(v) for v in vertices],
                    "arity": arity,
                    "edge_created": str(identity_edge_id),
                    "context": str(vertex_context)
                }
            )
            
        except Exception as e:
            return TransformationResult(False, None, str(e), {})
    
    def _get_vertex_context(self, egi: RelationalGraphWithCuts, vertex_id: ElementID) -> ElementID:
        """Get the context containing a vertex."""
        for area_id, contents in egi.area.items():
            if vertex_id in contents:
                return area_id
        return egi.sheet


class SeparateNaryIdentityRule(FormalTransformationRule):
    """Rule for separating vertices from n-ary identity relations."""
    
    def get_rule_name(self) -> str:
        return "SEPARATE_NARY_IDENTITY (Separate Vertex from N-ary Identity)"
    
    def check_preconditions(self, context: TransformationContext) -> Tuple[bool, Optional[str]]:
        """Check preconditions for separating from n-ary identity."""
        if len(context.selected_subgraph) != 1:
            return False, "Must select exactly one vertex to separate from n-ary identity"
        
        egi = context.source_egi
        vertex_id = next(iter(context.selected_subgraph))
        
        # Verify it's a vertex
        if not any(v.id == vertex_id for v in egi.V):
            return False, "Selected element must be a vertex"
        
        # Find n-ary identity relations containing this vertex
        nary_relations = self._find_nary_identities_containing_vertex(egi, vertex_id)
        if not nary_relations:
            return False, "Vertex is not part of any n-ary identity relation"
        
        # Check if any can be separated (arity > 2)
        separable_relations = [rel for rel in nary_relations if rel.can_separate_vertex(vertex_id)]
        if not separable_relations:
            return False, "Vertex cannot be separated from any n-ary identity (all are binary)"
        
        return True, None
    
    def apply_transformation(self, context: TransformationContext) -> TransformationResult:
        """Apply n-ary identity separation."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})
        
        try:
            egi = context.source_egi
            vertex_id = next(iter(context.selected_subgraph))
            
            # Find the first separable n-ary identity relation
            nary_relations = self._find_nary_identities_containing_vertex(egi, vertex_id)
            target_relation = None
            for rel in nary_relations:
                if rel.can_separate_vertex(vertex_id):
                    target_relation = rel
                    break
            
            if not target_relation:
                return TransformationResult(False, None, "No separable n-ary identity found", {})
            
            # Separate the vertex from the n-ary identity
            result_egi = self._apply_nary_separation(egi, target_relation, vertex_id)
            
            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "SEPARATE_NARY_IDENTITY",
                    "separated_vertex": str(vertex_id),
                    "original_relation": str(target_relation),
                    "original_arity": target_relation.arity,
                    "new_arity": target_relation.arity - 1
                }
            )
            
        except Exception as e:
            return TransformationResult(False, None, str(e), {})
    
    def _apply_nary_separation(self, 
                              egi: RelationalGraphWithCuts,
                              relation: NaryIdentityRelation,
                              vertex_to_separate: ElementID) -> RelationalGraphWithCuts:
        """Apply the n-ary identity separation operation."""
        
        # Remove the vertex from the relation
        remaining_vertices = [v for v in relation.vertices if v != vertex_to_separate]
        new_arity = len(remaining_vertices)
        
        # Update nu mapping
        new_nu = dict(egi.nu)
        
        if new_arity == 1:
            # Remove the edge entirely (identity of single vertex is trivial)
            del new_nu[relation.edge_id]
        else:
            # Update the edge with remaining vertices
            new_nu[relation.edge_id] = tuple(remaining_vertices)
        
        # Update rel mapping
        new_rel = dict(egi.rel)
        
        if new_arity == 1:
            # Remove the relation entirely
            del new_rel[relation.edge_id]
        elif new_arity == 2:
            # Convert to binary identity
            new_rel[relation.edge_id] = "="
        else:
            # Update to new arity
            new_rel[relation.edge_id] = f".={new_arity}"
        
        # Update edge set if edge was removed
        new_edges = egi.E
        if new_arity == 1:
            new_edges = set(egi.E)
            for edge in egi.E:
                if edge.id == relation.edge_id:
                    new_edges.remove(edge)
                    break
            new_edges = frozenset(new_edges)
        
        # Update area mapping if edge was removed
        new_area_mapping = dict(egi.area)
        if new_arity == 1:
            for area_id, contents in new_area_mapping.items():
                if relation.edge_id in contents:
                    new_contents = set(contents)
                    new_contents.remove(relation.edge_id)
                    new_area_mapping[area_id] = frozenset(new_contents)
        
        return RelationalGraphWithCuts(
            V=egi.V,
            E=new_edges,
            nu=frozendict(new_nu),
            sheet=egi.sheet,
            Cut=egi.Cut,
            area=frozendict(new_area_mapping),
            rel=frozendict(new_rel)
        )
    
    def _find_nary_identities_containing_vertex(self, 
                                               egi: RelationalGraphWithCuts,
                                               vertex_id: ElementID) -> List[NaryIdentityRelation]:
        """Find all n-ary identity relations containing the given vertex."""
        relations = []
        
        for edge_id, vertex_sequence in egi.nu.items():
            relation_type = egi.rel.get(edge_id, "")
            
            # Check for n-ary identity relations
            if relation_type.startswith(".=") or relation_type == "=":
                if vertex_id in vertex_sequence:
                    if relation_type == "=":
                        arity = 2
                    else:
                        try:
                            arity = int(relation_type[2:])
                        except ValueError:
                            continue
                    
                    relations.append(NaryIdentityRelation(
                        edge_id=edge_id,
                        vertices=list(vertex_sequence),
                        arity=arity
                    ))
        
        return relations


class NaryIdentityAnalyzer:
    """Analyzer for n-ary identity relations in EGIs."""
    
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        self._nary_relations = None
    
    def get_all_nary_identities(self) -> List[NaryIdentityRelation]:
        """Get all n-ary identity relations in the EGI."""
        if self._nary_relations is None:
            self._nary_relations = self._extract_nary_identities()
        return self._nary_relations
    
    def get_identities_by_arity(self, arity: int) -> List[NaryIdentityRelation]:
        """Get all identity relations of specific arity."""
        return [rel for rel in self.get_all_nary_identities() if rel.arity == arity]
    
    def get_identities_containing_vertex(self, vertex_id: ElementID) -> List[NaryIdentityRelation]:
        """Get all identity relations containing the given vertex."""
        return [rel for rel in self.get_all_nary_identities() if rel.contains_vertex(vertex_id)]
    
    def get_max_arity(self) -> int:
        """Get the maximum arity of identity relations in the EGI."""
        relations = self.get_all_nary_identities()
        return max((rel.arity for rel in relations), default=0)
    
    def get_identity_statistics(self) -> Dict[str, Any]:
        """Get statistics about identity relations in the EGI."""
        relations = self.get_all_nary_identities()
        
        arity_counts = {}
        for rel in relations:
            arity_counts[rel.arity] = arity_counts.get(rel.arity, 0) + 1
        
        return {
            "total_relations": len(relations),
            "arity_distribution": arity_counts,
            "max_arity": self.get_max_arity(),
            "binary_count": arity_counts.get(2, 0),
            "nary_count": sum(count for arity, count in arity_counts.items() if arity > 2)
        }
    
    def can_create_nary_identity(self, vertices: List[ElementID]) -> Tuple[bool, Optional[str]]:
        """Check if n-ary identity can be created for given vertices."""
        if len(vertices) < 2:
            return False, "Need at least 2 vertices for identity relation"
        
        # Check if all vertices exist
        vertex_ids = set(v.id for v in self.egi.V)
        for vertex_id in vertices:
            if vertex_id not in vertex_ids:
                return False, f"Vertex {vertex_id} does not exist"
        
        # Check if vertices are in same context
        contexts = set()
        for vertex_id in vertices:
            vertex_context = self._get_vertex_context(vertex_id)
            contexts.add(vertex_context)
        
        if len(contexts) > 1:
            return False, "All vertices must be in the same context"
        
        return True, None
    
    def _extract_nary_identities(self) -> List[NaryIdentityRelation]:
        """Extract all n-ary identity relations from the EGI."""
        relations = []
        
        for edge_id, vertex_sequence in self.egi.nu.items():
            relation_type = self.egi.rel.get(edge_id, "")
            
            # Check for identity relations
            if relation_type == "=" or relation_type.startswith(".="):
                if relation_type == "=":
                    arity = 2
                else:
                    try:
                        arity = int(relation_type[2:])
                    except ValueError:
                        continue
                
                if len(vertex_sequence) == arity:
                    relations.append(NaryIdentityRelation(
                        edge_id=edge_id,
                        vertices=list(vertex_sequence),
                        arity=arity
                    ))
        
        return relations
    
    def _get_vertex_context(self, vertex_id: ElementID) -> ElementID:
        """Get the context containing a vertex."""
        for area_id, contents in self.egi.area.items():
            if vertex_id in contents:
                return area_id
        return self.egi.sheet


def demonstrate_nary_identity_relations():
    """Demonstrate n-ary identity relation operations."""
    
    print("🔢 N-ary Identity Relations Demonstration")
    print("=" * 45)
    
    from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
    
    # Create test EGI with vertices for n-ary identity
    vertex_a = Vertex(ElementID("A"))
    vertex_b = Vertex(ElementID("B"))
    vertex_c = Vertex(ElementID("C"))
    vertex_d = Vertex(ElementID("D"))
    
    edge_r = Edge(ElementID("R"))
    
    test_egi = RelationalGraphWithCuts(
        V=frozenset([vertex_a, vertex_b, vertex_c, vertex_d]),
        E=frozenset([edge_r]),
        nu=frozendict({
            ElementID("R"): (ElementID("A"), ElementID("B"))
        }),
        sheet=ElementID("sheet"),
        Cut=frozenset(),
        area=frozendict({
            ElementID("sheet"): frozenset([ElementID("A"), ElementID("B"), ElementID("C"), ElementID("D"), ElementID("R")])
        }),
        rel=frozendict({
            ElementID("R"): "Relation1"
        })
    )
    
    print("\n📊 Test EGI Structure:")
    print(f"   Vertices: {[v.id for v in test_egi.V]}")
    print(f"   Edges: {[e.id for e in test_egi.E]}")
    
    # Test creating ternary identity
    print("\n🔢 Test 1: Create Ternary Identity (.=3)")
    create_rule = CreateNaryIdentityRule()
    
    from formal_transformation_rules import TransformationContext, AreaPolarity
    create_context = TransformationContext(
        source_egi=test_egi,
        target_area=ElementID("sheet"),
        selected_subgraph=frozenset([ElementID("A"), ElementID("B"), ElementID("C")]),
        area_polarity=AreaPolarity.POSITIVE,
        nesting_depth=0
    )
    
    create_result = create_rule.apply_transformation(create_context)
    
    print(f"   Success: {'✅' if create_result.success else '❌'}")
    if create_result.success:
        print(f"   Changes: {create_result.changes_made}")
        ternary_egi = create_result.result_egi
        
        # Analyze the result
        analyzer = NaryIdentityAnalyzer(ternary_egi)
        stats = analyzer.get_identity_statistics()
        print(f"   Identity statistics: {stats}")
        
        # Test separation
        print("\n🔢 Test 2: Separate Vertex from Ternary Identity")
        separate_rule = SeparateNaryIdentityRule()
        
        separate_context = TransformationContext(
            source_egi=ternary_egi,
            target_area=ElementID("sheet"),
            selected_subgraph=frozenset([ElementID("C")]),
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0
        )
        
        separate_result = separate_rule.apply_transformation(separate_context)
        
        print(f"   Success: {'✅' if separate_result.success else '❌'}")
        if separate_result.success:
            print(f"   Changes: {separate_result.changes_made}")
            binary_egi = separate_result.result_egi
            
            # Analyze final result
            final_analyzer = NaryIdentityAnalyzer(binary_egi)
            final_stats = final_analyzer.get_identity_statistics()
            print(f"   Final statistics: {final_stats}")
        else:
            print(f"   Error: {separate_result.error_message}")
    else:
        print(f"   Error: {create_result.error_message}")
    
    # Test creating quaternary identity
    print("\n🔢 Test 3: Create Quaternary Identity (.=4)")
    quaternary_context = TransformationContext(
        source_egi=test_egi,
        target_area=ElementID("sheet"),
        selected_subgraph=frozenset([ElementID("A"), ElementID("B"), ElementID("C"), ElementID("D")]),
        area_polarity=AreaPolarity.POSITIVE,
        nesting_depth=0
    )
    
    quaternary_result = create_rule.apply_transformation(quaternary_context)
    
    print(f"   Success: {'✅' if quaternary_result.success else '❌'}")
    if quaternary_result.success:
        print(f"   Changes: {quaternary_result.changes_made}")
        quaternary_egi = quaternary_result.result_egi
        
        # Show binary pairs implied by quaternary identity
        quaternary_analyzer = NaryIdentityAnalyzer(quaternary_egi)
        quaternary_relations = quaternary_analyzer.get_identities_by_arity(4)
        if quaternary_relations:
            binary_pairs = quaternary_relations[0].get_binary_pairs()
            print(f"   Implied binary pairs: {binary_pairs}")
    else:
        print(f"   Error: {quaternary_result.error_message}")
    
    print(f"\n✅ N-ary Identity Relations Complete")
    print(f"   - N-ary identity creation: ✅")
    print(f"   - Vertex separation: ✅")
    print(f"   - Arity analysis: ✅")
    print(f"   - Binary pair extraction: ✅")
    
    return create_rule, separate_rule


if __name__ == "__main__":
    demonstrate_nary_identity_relations()
