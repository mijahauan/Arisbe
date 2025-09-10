"""
User workflow integration for subgraph selection and transformation rule application.
Demonstrates the principle that all graph actions follow EG transformation rules.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from frozendict import frozendict


class TransformationContext(Enum):
    """Context polarity for transformation rule application."""
    POSITIVE = "positive"
    NEGATIVE = "negative"


@dataclass
class SubgraphSelection:
    """Represents a user-selected subgraph for transformation."""
    elements: Set[ElementID]
    context_area: ElementID  # The area containing the selection
    context_polarity: TransformationContext
    selection_bounds: Tuple[float, float, float, float]  # x, y, width, height


@dataclass
class ApplicableRule:
    """Represents a transformation rule applicable to a subgraph selection."""
    rule_name: str
    rule_type: str
    description: str
    preconditions: List[str]
    effects: List[str]
    confidence: float  # 0.0 to 1.0


@dataclass
class TransformationProposal:
    """Represents a proposed transformation with preview."""
    rule: ApplicableRule
    selection: SubgraphSelection
    preview_description: str
    resulting_elements: Set[ElementID]


class SubgraphSelector:
    """Handles subgraph selection from EG diagrams."""
    
    def __init__(self, graph: RelationalGraphWithCuts):
        self.graph = graph
    
    def select_by_bounds(self, x: float, y: float, width: float, height: float,
                        element_positions: Dict[ElementID, Tuple[float, float]]) -> SubgraphSelection:
        """Select subgraph elements within spatial bounds."""
        selected_elements = set()
        
        # Find elements within bounds
        for element_id, (elem_x, elem_y) in element_positions.items():
            if (x <= elem_x <= x + width and y <= elem_y <= y + height):
                selected_elements.add(element_id)
        
        # Determine containing area and context polarity
        context_area = self._find_containing_area(x + width/2, y + height/2)
        context_polarity = self._determine_context_polarity(context_area)
        
        return SubgraphSelection(
            elements=selected_elements,
            context_area=context_area,
            context_polarity=context_polarity,
            selection_bounds=(x, y, width, height)
        )
    
    def select_by_elements(self, element_ids: Set[ElementID]) -> SubgraphSelection:
        """Select subgraph by explicit element IDs."""
        # Find common containing area
        context_area = self._find_common_area(element_ids)
        context_polarity = self._determine_context_polarity(context_area)
        
        return SubgraphSelection(
            elements=element_ids,
            context_area=context_area,
            context_polarity=context_polarity,
            selection_bounds=(0, 0, 0, 0)  # Bounds not applicable for explicit selection
        )
    
    def _find_containing_area(self, x: float, y: float) -> ElementID:
        """Find the area containing the given spatial position."""
        # Start with sheet and work inward through nested cuts
        current_area = self.graph.sheet
        
        # This would need spatial information about cuts to determine containment
        # For now, return sheet as default
        return current_area
    
    def _find_common_area(self, element_ids: Set[ElementID]) -> ElementID:
        """Find the most specific area containing all selected elements."""
        # Find areas containing each element
        element_areas = []
        for element_id in element_ids:
            for area_id, area_contents in self.graph.area.items():
                if element_id in area_contents:
                    element_areas.append(area_id)
                    break
        
        # Find common area (simplified - would need proper area hierarchy)
        if element_areas:
            return element_areas[0]  # Simplified
        return self.graph.sheet
    
    def _determine_context_polarity(self, area_id: ElementID) -> TransformationContext:
        """Determine context polarity based on nesting depth."""
        # Count nesting depth to determine polarity
        depth = self._calculate_nesting_depth(area_id)
        return TransformationContext.POSITIVE if depth % 2 == 0 else TransformationContext.NEGATIVE
    
    def _calculate_nesting_depth(self, area_id: ElementID) -> int:
        """Calculate nesting depth of an area."""
        if area_id == self.graph.sheet:
            return 0
        
        # Count cuts containing this area (simplified)
        depth = 0
        for cut_id in self.graph.Cut:
            if area_id in self.graph.area.get(cut_id, frozenset()):
                depth += 1
        
        return depth


class TransformationRuleDiscovery:
    """Discovers applicable transformation rules for subgraph selections."""
    
    def __init__(self, graph: RelationalGraphWithCuts):
        self.graph = graph
        self.rule_catalog = self._initialize_rule_catalog()
    
    def discover_applicable_rules(self, selection: SubgraphSelection) -> List[ApplicableRule]:
        """Discover transformation rules applicable to the selection."""
        applicable_rules = []
        
        # Analyze selection structure
        vertices = [eid for eid in selection.elements if eid in self.graph.V]
        edges = [eid for eid in selection.elements if eid in self.graph.E]
        cuts = [eid for eid in selection.elements if eid in self.graph.Cut]
        
        # Check each rule in catalog
        for rule in self.rule_catalog:
            confidence = self._evaluate_rule_applicability(rule, selection, vertices, edges, cuts)
            if confidence > 0.0:
                rule.confidence = confidence
                applicable_rules.append(rule)
        
        # Sort by confidence
        applicable_rules.sort(key=lambda r: r.confidence, reverse=True)
        return applicable_rules
    
    def _initialize_rule_catalog(self) -> List[ApplicableRule]:
        """Initialize catalog of EG transformation rules."""
        return [
            ApplicableRule(
                rule_name="insertion",
                rule_type="basic",
                description="Insert new vertex or edge into positive context",
                preconditions=["Selection in positive context", "Valid insertion point"],
                effects=["New element added", "Graph remains valid"],
                confidence=0.0
            ),
            ApplicableRule(
                rule_name="erasure",
                rule_type="basic", 
                description="Remove vertex or edge from negative context",
                preconditions=["Selection in negative context", "Element exists"],
                effects=["Element removed", "Graph remains valid"],
                confidence=0.0
            ),
            ApplicableRule(
                rule_name="iteration",
                rule_type="advanced",
                description="Copy subgraph within same context",
                preconditions=["Valid subgraph", "Same context area"],
                effects=["Subgraph duplicated", "Logical conjunction"],
                confidence=0.0
            ),
            ApplicableRule(
                rule_name="deiteration",
                rule_type="advanced",
                description="Remove duplicate subgraph",
                preconditions=["Duplicate subgraphs exist", "Same context"],
                effects=["Duplicate removed", "Logical simplification"],
                confidence=0.0
            ),
            ApplicableRule(
                rule_name="double_cut_insertion",
                rule_type="cut_manipulation",
                description="Insert double cut around selection",
                preconditions=["Valid selection", "Any context"],
                effects=["Double cut added", "Logically equivalent"],
                confidence=0.0
            ),
            ApplicableRule(
                rule_name="double_cut_erasure",
                rule_type="cut_manipulation",
                description="Remove double cut",
                preconditions=["Double cut exists", "No intervening elements"],
                effects=["Double cut removed", "Logically equivalent"],
                confidence=0.0
            )
        ]
    
    def _evaluate_rule_applicability(self, rule: ApplicableRule, selection: SubgraphSelection,
                                   vertices: List[ElementID], edges: List[ElementID], 
                                   cuts: List[ElementID]) -> float:
        """Evaluate how applicable a rule is to the current selection."""
        confidence = 0.0
        
        if rule.rule_name == "insertion":
            # Insertion applicable in positive contexts with space for new elements
            if selection.context_polarity == TransformationContext.POSITIVE:
                confidence = 0.8
        
        elif rule.rule_name == "erasure":
            # Erasure applicable in negative contexts with existing elements
            if (selection.context_polarity == TransformationContext.NEGATIVE and 
                (vertices or edges)):
                confidence = 0.9
        
        elif rule.rule_name == "iteration":
            # Iteration applicable when we have a coherent subgraph
            if vertices and edges:
                confidence = 0.7
        
        elif rule.rule_name == "deiteration":
            # Deiteration applicable when duplicates might exist
            if len(vertices) > 1 or len(edges) > 1:
                confidence = 0.6
        
        elif rule.rule_name == "double_cut_insertion":
            # Always applicable for logical equivalence
            confidence = 0.5
        
        elif rule.rule_name == "double_cut_erasure":
            # Applicable when we have nested cuts
            if len(cuts) >= 2:
                confidence = 0.8
        
        return confidence


class WorkflowOrchestrator:
    """Orchestrates the complete user workflow from selection to transformation."""
    
    def __init__(self, graph: RelationalGraphWithCuts):
        self.graph = graph
        self.selector = SubgraphSelector(graph)
        self.rule_discovery = TransformationRuleDiscovery(graph)
    
    def create_transformation_workflow(self, selection: SubgraphSelection) -> List[TransformationProposal]:
        """Create complete workflow from selection to transformation proposals."""
        
        # Discover applicable rules
        applicable_rules = self.rule_discovery.discover_applicable_rules(selection)
        
        # Create transformation proposals
        proposals = []
        for rule in applicable_rules[:5]:  # Limit to top 5 rules
            proposal = TransformationProposal(
                rule=rule,
                selection=selection,
                preview_description=self._generate_preview_description(rule, selection),
                resulting_elements=self._predict_resulting_elements(rule, selection)
            )
            proposals.append(proposal)
        
        return proposals
    
    def _generate_preview_description(self, rule: ApplicableRule, selection: SubgraphSelection) -> str:
        """Generate human-readable preview of transformation effects."""
        element_count = len(selection.elements)
        context = "positive" if selection.context_polarity == TransformationContext.POSITIVE else "negative"
        
        if rule.rule_name == "insertion":
            return f"Insert new element into {context} context with {element_count} selected elements"
        elif rule.rule_name == "erasure":
            return f"Remove {element_count} elements from {context} context"
        elif rule.rule_name == "iteration":
            return f"Copy {element_count} elements within same context"
        elif rule.rule_name == "deiteration":
            return f"Remove duplicate among {element_count} elements"
        elif rule.rule_name == "double_cut_insertion":
            return f"Surround {element_count} elements with double cut"
        elif rule.rule_name == "double_cut_erasure":
            return f"Remove double cut around {element_count} elements"
        else:
            return f"Apply {rule.rule_name} to {element_count} elements"
    
    def _predict_resulting_elements(self, rule: ApplicableRule, selection: SubgraphSelection) -> Set[ElementID]:
        """Predict which elements will result from applying the transformation."""
        # Simplified prediction - in practice this would be more sophisticated
        if rule.rule_name == "insertion":
            # Would add new elements
            return selection.elements | {f"new_{rule.rule_name}_{len(selection.elements)}"}
        elif rule.rule_name == "erasure":
            # Would remove elements
            return set()
        else:
            # Most rules preserve existing elements
            return selection.elements


# Example usage and testing
def demonstrate_user_workflow():
    """Demonstrate the complete user workflow integration."""
    
    # Create a simple test graph
    from frozendict import frozendict
    
    vertices = frozenset([Vertex("v1"), Vertex("v2"), Vertex("v3")])
    edges = frozenset([Edge("e1"), Edge("e2")])
    cuts = frozenset([Cut("c1")])
    
    nu_mapping = frozendict({
        "e1": ("v1", "v2"),
        "e2": ("v2", "v3")
    })
    
    area_mapping = frozendict({
        "sheet": frozenset(["v1", "e1", "c1"]),
        "c1": frozenset(["v2", "e2", "v3"])
    })
    
    rel_mapping = frozendict({
        "e1": "Loves",
        "e2": "Knows"
    })
    
    graph = RelationalGraphWithCuts(
        V=vertices,
        E=edges,
        nu=nu_mapping,
        sheet="sheet",
        Cut=cuts,
        area=area_mapping,
        rel=rel_mapping
    )
    
    # Create workflow orchestrator
    orchestrator = WorkflowOrchestrator(graph)
    
    # Simulate user selection
    element_positions = {
        "v1": (50, 100),
        "v2": (150, 100), 
        "v3": (250, 100),
        "e1": (100, 100),
        "e2": (200, 100)
    }
    
    # Select subgraph by bounds
    selection = orchestrator.selector.select_by_bounds(
        x=40, y=90, width=120, height=20, element_positions=element_positions
    )
    
    # Create transformation workflow
    proposals = orchestrator.create_transformation_workflow(selection)
    
    print("🔧 User Workflow Integration Demo")
    print("=" * 50)
    print(f"📍 Selected {len(selection.elements)} elements in {selection.context_polarity.value} context")
    print(f"🎯 Found {len(proposals)} applicable transformation rules:")
    
    for i, proposal in enumerate(proposals, 1):
        print(f"\n{i}. {proposal.rule.rule_name.upper()} (confidence: {proposal.rule.confidence:.1f})")
        print(f"   📝 {proposal.rule.description}")
        print(f"   👁️  Preview: {proposal.preview_description}")
        print(f"   ✅ Preconditions: {', '.join(proposal.rule.preconditions)}")
    
    return orchestrator, proposals


if __name__ == "__main__":
    demonstrate_user_workflow()
