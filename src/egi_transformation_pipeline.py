"""
Complete EGI transformation pipeline with concrete transformation rule implementations.
Implements the immutable transformation principle: EGI → rule → new EGI.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
import uuid

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from frozendict import frozendict
from immutable_transformation_architecture import (
    TransformationRule, TransformationRuleType, ImmutableEGIRepository, 
    EGISnapshot, TransformationStep, ContextType
)


class ConcreteInsertionRule(TransformationRule):
    """Concrete implementation of vertex/edge insertion in positive contexts."""
    
    def can_apply(self, egi: RelationalGraphWithCuts, context: ContextType) -> bool:
        """Insertion allowed in positive contexts (even nesting depth)."""
        return True  # Simplified - would check actual context polarity
    
    def apply(self, egi: RelationalGraphWithCuts, 
             transformation_data: Dict[str, Any]) -> RelationalGraphWithCuts:
        """Apply insertion transformation to create new EGI."""
        element_type = transformation_data.get("element_type")
        element_id = transformation_data.get("element_id")
        target_area = transformation_data.get("target_area", egi.sheet)
        
        if element_type == "vertex":
            return self._insert_vertex(egi, element_id, target_area)
        elif element_type == "edge":
            return self._insert_edge(egi, element_id, target_area, transformation_data)
        elif element_type == "cut":
            return self._insert_cut(egi, element_id, target_area, transformation_data)
        else:
            raise ValueError(f"Unknown element type: {element_type}")
    
    def _insert_vertex(self, egi: RelationalGraphWithCuts, vertex_id: str, 
                      target_area: ElementID) -> RelationalGraphWithCuts:
        """Insert a new vertex into the specified area."""
        new_vertex = Vertex(vertex_id)
        new_vertices = egi.V | frozenset([new_vertex])
        
        # Update area mapping to include new vertex
        current_area_contents = egi.area.get(target_area, frozenset())
        new_area_contents = current_area_contents | frozenset([vertex_id])
        new_area_mapping = dict(egi.area)
        new_area_mapping[target_area] = new_area_contents
        
        return RelationalGraphWithCuts(
            V=new_vertices,
            E=egi.E,
            nu=egi.nu,
            sheet=egi.sheet,
            Cut=egi.Cut,
            area=frozendict(new_area_mapping),
            rel=egi.rel
        )
    
    def _insert_edge(self, egi: RelationalGraphWithCuts, edge_id: str,
                    target_area: ElementID, transformation_data: Dict[str, Any]) -> RelationalGraphWithCuts:
        """Insert a new edge with specified vertex connections."""
        new_edge = Edge(edge_id)
        new_edges = egi.E | frozenset([new_edge])
        
        # Get vertex sequence and relation name from transformation data
        vertex_sequence = transformation_data.get("vertex_sequence", ())
        relation_name = transformation_data.get("relation_name", "")
        
        # Update nu mapping
        new_nu_mapping = dict(egi.nu)
        new_nu_mapping[edge_id] = vertex_sequence
        
        # Update relation mapping
        new_rel_mapping = dict(egi.rel)
        if relation_name:
            new_rel_mapping[edge_id] = relation_name
        
        # Update area mapping
        current_area_contents = egi.area.get(target_area, frozenset())
        new_area_contents = current_area_contents | frozenset([edge_id])
        new_area_mapping = dict(egi.area)
        new_area_mapping[target_area] = new_area_contents
        
        return RelationalGraphWithCuts(
            V=egi.V,
            E=new_edges,
            nu=frozendict(new_nu_mapping),
            sheet=egi.sheet,
            Cut=egi.Cut,
            area=frozendict(new_area_mapping),
            rel=frozendict(new_rel_mapping)
        )
    
    def _insert_cut(self, egi: RelationalGraphWithCuts, cut_id: str,
                   target_area: ElementID, transformation_data: Dict[str, Any]) -> RelationalGraphWithCuts:
        """Insert a new cut around specified elements."""
        new_cut = Cut(cut_id)
        new_cuts = egi.Cut | frozenset([new_cut])
        
        # Get elements to be enclosed by the cut
        enclosed_elements = transformation_data.get("enclosed_elements", frozenset())
        
        # Update area mappings
        new_area_mapping = dict(egi.area)
        
        # Remove enclosed elements from current area
        current_area_contents = egi.area.get(target_area, frozenset())
        remaining_contents = current_area_contents - enclosed_elements
        new_area_mapping[target_area] = remaining_contents | frozenset([cut_id])
        
        # Create new area for the cut containing the enclosed elements
        new_area_mapping[cut_id] = enclosed_elements
        
        return RelationalGraphWithCuts(
            V=egi.V,
            E=egi.E,
            nu=egi.nu,
            sheet=egi.sheet,
            Cut=new_cuts,
            area=frozendict(new_area_mapping),
            rel=egi.rel
        )
    
    def get_rule_type(self) -> TransformationRuleType:
        return TransformationRuleType.INSERTION


class ConcreteErasureRule(TransformationRule):
    """Concrete implementation of element erasure in negative contexts."""
    
    def can_apply(self, egi: RelationalGraphWithCuts, context: ContextType) -> bool:
        """Erasure allowed in negative contexts (odd nesting depth)."""
        return True  # Simplified - would check actual context polarity
    
    def apply(self, egi: RelationalGraphWithCuts, 
             transformation_data: Dict[str, Any]) -> RelationalGraphWithCuts:
        """Apply erasure transformation to create new EGI."""
        element_type = transformation_data.get("element_type")
        element_id = transformation_data.get("element_id")
        
        if element_type == "vertex":
            return self._erase_vertex(egi, element_id)
        elif element_type == "edge":
            return self._erase_edge(egi, element_id)
        elif element_type == "cut":
            return self._erase_cut(egi, element_id)
        else:
            raise ValueError(f"Unknown element type: {element_type}")
    
    def _erase_vertex(self, egi: RelationalGraphWithCuts, vertex_id: str) -> RelationalGraphWithCuts:
        """Erase a vertex and update all related mappings."""
        # Remove vertex from vertex set
        new_vertices = frozenset(v for v in egi.V if v.id != vertex_id)
        
        # Remove vertex from nu mappings (edges that reference this vertex)
        new_nu_mapping = {}
        for edge_id, vertex_seq in egi.nu.items():
            filtered_seq = tuple(v_id for v_id in vertex_seq if v_id != vertex_id)
            if filtered_seq:  # Only keep edges that still have vertices
                new_nu_mapping[edge_id] = filtered_seq
        
        # Remove vertex from area mappings
        new_area_mapping = {}
        for area_id, area_contents in egi.area.items():
            new_area_mapping[area_id] = area_contents - frozenset([vertex_id])
        
        return RelationalGraphWithCuts(
            V=new_vertices,
            E=egi.E,
            nu=frozendict(new_nu_mapping),
            sheet=egi.sheet,
            Cut=egi.Cut,
            area=frozendict(new_area_mapping),
            rel=egi.rel
        )
    
    def _erase_edge(self, egi: RelationalGraphWithCuts, edge_id: str) -> RelationalGraphWithCuts:
        """Erase an edge and update all related mappings."""
        # Remove edge from edge set
        new_edges = frozenset(e for e in egi.E if e.id != edge_id)
        
        # Remove edge from nu mapping
        new_nu_mapping = dict(egi.nu)
        if edge_id in new_nu_mapping:
            del new_nu_mapping[edge_id]
        
        # Remove edge from relation mapping
        new_rel_mapping = dict(egi.rel)
        if edge_id in new_rel_mapping:
            del new_rel_mapping[edge_id]
        
        # Remove edge from area mappings
        new_area_mapping = {}
        for area_id, area_contents in egi.area.items():
            new_area_mapping[area_id] = area_contents - frozenset([edge_id])
        
        return RelationalGraphWithCuts(
            V=egi.V,
            E=new_edges,
            nu=frozendict(new_nu_mapping),
            sheet=egi.sheet,
            Cut=egi.Cut,
            area=frozendict(new_area_mapping),
            rel=frozendict(new_rel_mapping)
        )
    
    def _erase_cut(self, egi: RelationalGraphWithCuts, cut_id: str) -> RelationalGraphWithCuts:
        """Erase a cut and move its contents to parent area."""
        # Remove cut from cut set
        new_cuts = frozenset(c for c in egi.Cut if c.id != cut_id)
        
        # Find parent area containing this cut
        parent_area = None
        for area_id, area_contents in egi.area.items():
            if cut_id in area_contents:
                parent_area = area_id
                break
        
        if not parent_area:
            raise ValueError(f"Cut {cut_id} not found in any area")
        
        # Get contents of the cut being erased
        cut_contents = egi.area.get(cut_id, frozenset())
        
        # Update area mappings
        new_area_mapping = dict(egi.area)
        
        # Remove cut from parent area and add its contents
        parent_contents = egi.area.get(parent_area, frozenset())
        new_parent_contents = (parent_contents - frozenset([cut_id])) | cut_contents
        new_area_mapping[parent_area] = new_parent_contents
        
        # Remove the cut's area mapping
        if cut_id in new_area_mapping:
            del new_area_mapping[cut_id]
        
        return RelationalGraphWithCuts(
            V=egi.V,
            E=egi.E,
            nu=egi.nu,
            sheet=egi.sheet,
            Cut=new_cuts,
            area=frozendict(new_area_mapping),
            rel=egi.rel
        )
    
    def get_rule_type(self) -> TransformationRuleType:
        return TransformationRuleType.ERASURE


class ConcreteIterationRule(TransformationRule):
    """Concrete implementation of subgraph iteration (copying)."""
    
    def can_apply(self, egi: RelationalGraphWithCuts, context: ContextType) -> bool:
        """Iteration allowed in any context."""
        return True
    
    def apply(self, egi: RelationalGraphWithCuts, 
             transformation_data: Dict[str, Any]) -> RelationalGraphWithCuts:
        """Apply iteration transformation to copy a subgraph."""
        source_elements = transformation_data.get("source_elements", set())
        target_area = transformation_data.get("target_area", egi.sheet)
        
        # Generate new IDs for copied elements
        element_mapping = {}
        for element_id in source_elements:
            element_mapping[element_id] = f"{element_id}_copy_{uuid.uuid4().hex[:8]}"
        
        new_vertices = set(egi.V)
        new_edges = set(egi.E)
        new_cuts = set(egi.Cut)
        new_nu_mapping = dict(egi.nu)
        new_rel_mapping = dict(egi.rel)
        new_area_mapping = dict(egi.area)
        
        # Copy vertices
        for vertex in egi.V:
            if vertex.id in source_elements:
                new_vertex_id = element_mapping[vertex.id]
                new_vertices.add(Vertex(new_vertex_id))
        
        # Copy edges
        for edge in egi.E:
            if edge.id in source_elements:
                new_edge_id = element_mapping[edge.id]
                new_edges.add(Edge(new_edge_id))
                
                # Update nu mapping for copied edge
                original_vertex_seq = egi.nu.get(edge.id, ())
                new_vertex_seq = tuple(
                    element_mapping.get(v_id, v_id) for v_id in original_vertex_seq
                )
                new_nu_mapping[new_edge_id] = new_vertex_seq
                
                # Update relation mapping
                if edge.id in egi.rel:
                    new_rel_mapping[new_edge_id] = egi.rel[edge.id]
        
        # Copy cuts
        for cut in egi.Cut:
            if cut.id in source_elements:
                new_cut_id = element_mapping[cut.id]
                new_cuts.add(Cut(new_cut_id))
                
                # Update area mapping for copied cut
                original_cut_contents = egi.area.get(cut.id, frozenset())
                new_cut_contents = frozenset(
                    element_mapping.get(elem_id, elem_id) for elem_id in original_cut_contents
                )
                new_area_mapping[new_cut_id] = new_cut_contents
        
        # Add copied elements to target area
        copied_element_ids = frozenset(element_mapping.values())
        current_target_contents = egi.area.get(target_area, frozenset())
        new_area_mapping[target_area] = current_target_contents | copied_element_ids
        
        return RelationalGraphWithCuts(
            V=frozenset(new_vertices),
            E=frozenset(new_edges),
            nu=frozendict(new_nu_mapping),
            sheet=egi.sheet,
            Cut=frozenset(new_cuts),
            area=frozendict(new_area_mapping),
            rel=frozendict(new_rel_mapping)
        )
    
    def get_rule_type(self) -> TransformationRuleType:
        return TransformationRuleType.ITERATION


class EGITransformationPipeline:
    """Complete pipeline for EGI transformations with concrete rules."""
    
    def __init__(self):
        self.repository = ImmutableEGIRepository()
        self.rules = {
            TransformationRuleType.INSERTION: ConcreteInsertionRule(),
            TransformationRuleType.ERASURE: ConcreteErasureRule(),
            TransformationRuleType.ITERATION: ConcreteIterationRule(),
        }
    
    def apply_transformation(self, source_egi_id: str, rule_type: TransformationRuleType,
                           transformation_data: Dict[str, Any], context_type: ContextType,
                           logical_justification: str = "") -> str:
        """Apply a transformation rule to create a new EGI."""
        
        # Get source EGI
        source_snapshot = self.repository.get_egi_snapshot(source_egi_id)
        if not source_snapshot:
            raise ValueError(f"Source EGI {source_egi_id} not found")
        
        # Get transformation rule
        rule = self.rules.get(rule_type)
        if not rule:
            raise ValueError(f"Transformation rule {rule_type} not implemented")
        
        # Check if rule can be applied
        if not rule.can_apply(source_snapshot.egi_state, context_type):
            raise ValueError(f"Rule {rule_type} cannot be applied in context {context_type}")
        
        # Apply transformation to create new EGI
        new_egi_state = rule.apply(source_snapshot.egi_state, transformation_data)
        
        # Create new EGI snapshot
        new_egi_id = str(uuid.uuid4())
        step_id = str(uuid.uuid4())
        
        from datetime import datetime
        timestamp = datetime.now()
        
        new_snapshot = EGISnapshot(
            egi_id=new_egi_id,
            egi_state=new_egi_state,
            timestamp=timestamp,
            context_type=context_type,
            provenance_step_id=step_id,
            logical_description=logical_justification,
            spatial_layout=frozendict(transformation_data.get('spatial_layout', {}))
        )
        
        # Create transformation step
        transformation_step = TransformationStep(
            step_id=step_id,
            rule_type=rule_type,
            source_egi_id=source_egi_id,
            target_egi_id=new_egi_id,
            transformation_data=frozendict(transformation_data),
            timestamp=timestamp,
            context_type=context_type,
            logical_justification=logical_justification,
            spatial_changes=frozendict(transformation_data.get('spatial_changes', {}))
        )
        
        # Store in repository
        self.repository.store_egi_snapshot(new_snapshot)
        self.repository.store_transformation_step(transformation_step)
        
        return new_egi_id
    
    def get_egi_state(self, egi_id: str) -> Optional[RelationalGraphWithCuts]:
        """Get the EGI state for a given ID."""
        snapshot = self.repository.get_egi_snapshot(egi_id)
        return snapshot.egi_state if snapshot else None
    
    def get_transformation_history(self, egi_id: str) -> List[TransformationStep]:
        """Get the complete transformation history leading to an EGI."""
        return self.repository.get_egi_history(egi_id)


def demonstrate_concrete_transformations():
    """Demonstrate concrete EGI transformations."""
    
    pipeline = EGITransformationPipeline()
    
    print("🔧 Concrete EGI Transformation Pipeline Demo")
    print("=" * 50)
    
    # Create initial EGI
    initial_egi = RelationalGraphWithCuts(
        V=frozenset([Vertex("v1")]),
        E=frozenset(),
        nu=frozendict(),
        sheet="sheet",
        Cut=frozenset(),
        area=frozendict({"sheet": frozenset(["v1"])}),
        rel=frozendict()
    )
    
    initial_egi_id = "initial_concrete"
    from datetime import datetime
    initial_snapshot = EGISnapshot(
        egi_id=initial_egi_id,
        egi_state=initial_egi,
        timestamp=datetime.now(),
        context_type=ContextType.ERGASTERION,
        provenance_step_id=None,
        logical_description="Initial EGI with single vertex v1",
        spatial_layout=frozendict({"v1": (100, 100)})
    )
    
    pipeline.repository.store_egi_snapshot(initial_snapshot)
    
    print(f"📍 Initial EGI: {len(initial_egi.V)} vertices, {len(initial_egi.E)} edges")
    
    # Apply vertex insertion
    egi_2_id = pipeline.apply_transformation(
        source_egi_id=initial_egi_id,
        rule_type=TransformationRuleType.INSERTION,
        transformation_data={
            "element_type": "vertex",
            "element_id": "v2",
            "target_area": "sheet"
        },
        context_type=ContextType.ERGASTERION,
        logical_justification="Insert vertex v2 for conjunction"
    )
    
    egi_2_state = pipeline.get_egi_state(egi_2_id)
    print(f"✅ After vertex insertion: {len(egi_2_state.V)} vertices, {len(egi_2_state.E)} edges")
    
    # Apply edge insertion
    egi_3_id = pipeline.apply_transformation(
        source_egi_id=egi_2_id,
        rule_type=TransformationRuleType.INSERTION,
        transformation_data={
            "element_type": "edge",
            "element_id": "e1",
            "target_area": "sheet",
            "vertex_sequence": ("v1", "v2"),
            "relation_name": "Loves"
        },
        context_type=ContextType.ERGASTERION,
        logical_justification="Insert edge e1 connecting v1 and v2"
    )
    
    egi_3_state = pipeline.get_egi_state(egi_3_id)
    print(f"✅ After edge insertion: {len(egi_3_state.V)} vertices, {len(egi_3_state.E)} edges")
    print(f"   Edge e1 connects: {egi_3_state.nu.get('e1', ())}")
    print(f"   Edge e1 relation: {egi_3_state.rel.get('e1', 'N/A')}")
    
    # Apply cut insertion
    egi_4_id = pipeline.apply_transformation(
        source_egi_id=egi_3_id,
        rule_type=TransformationRuleType.INSERTION,
        transformation_data={
            "element_type": "cut",
            "element_id": "c1",
            "target_area": "sheet",
            "enclosed_elements": frozenset(["v2", "e1"])
        },
        context_type=ContextType.ERGASTERION,
        logical_justification="Insert cut c1 around v2 and e1 for negation"
    )
    
    egi_4_state = pipeline.get_egi_state(egi_4_id)
    print(f"✅ After cut insertion: {len(egi_4_state.V)} vertices, {len(egi_4_state.E)} edges, {len(egi_4_state.Cut)} cuts")
    print(f"   Sheet contains: {egi_4_state.area.get('sheet', frozenset())}")
    print(f"   Cut c1 contains: {egi_4_state.area.get('c1', frozenset())}")
    
    # Apply iteration (copy subgraph)
    egi_5_id = pipeline.apply_transformation(
        source_egi_id=egi_4_id,
        rule_type=TransformationRuleType.ITERATION,
        transformation_data={
            "source_elements": {"v1"},
            "target_area": "sheet"
        },
        context_type=ContextType.ERGASTERION,
        logical_justification="Iterate vertex v1 for logical conjunction"
    )
    
    egi_5_state = pipeline.get_egi_state(egi_5_id)
    print(f"✅ After iteration: {len(egi_5_state.V)} vertices, {len(egi_5_state.E)} edges, {len(egi_5_state.Cut)} cuts")
    
    # Show transformation history
    history = pipeline.get_transformation_history(egi_5_id)
    print(f"\n📈 Transformation History:")
    for i, step in enumerate(history, 1):
        print(f"   {i}. {step.rule_type.value}: {step.logical_justification}")
    
    return pipeline


if __name__ == "__main__":
    demonstrate_concrete_transformations()
