"""
Foundational graph building system that axiomatically starts with a sheet of assertion.
Implements proper EG transformation rules starting with DC+ (Double Cut insertion).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from frozendict import frozendict
from immutable_transformation_architecture import (
    ContextType,
    TransformationRuleType,
    TransformationStep,
)

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex


class SheetType(Enum):
    """Types of assertion sheets."""

    COMMON_SHEET = "common_sheet"  # Single shared sheet for all constructions
    INDIVIDUAL_SHEET = "individual_sheet"  # Separate sheet per construction


@dataclass
class AssertionSheet:
    """A sheet of assertion - the foundational context for all EG construction."""

    sheet_id: str
    sheet_type: SheetType
    title: str
    description: str
    base_egi_id: str  # The empty sheet (graph 0)
    first_cut_egi_id: Optional[str] = None  # After DC+ (graph 1)
    constructions: Dict[str, str] = field(
        default_factory=dict
    )  # construction_id -> egi_id
    created_at: datetime = field(default_factory=datetime.now)

    def has_working_area(self) -> bool:
        """Check if sheet has the oddly-enclosed area for insertions."""
        return self.first_cut_egi_id is not None


@dataclass
class GraphConstruction:
    """A graph construction built on an assertion sheet."""

    construction_id: str
    title: str
    description: str
    sheet_id: str
    starting_egi_id: str  # Usually the first cut area
    current_egi_id: str
    transformation_history: List[TransformationStep] = field(default_factory=list)
    is_complete: bool = False
    created_at: datetime = field(default_factory=datetime.now)


class FoundationalGraphBuilder:
    """
    Graph builder that axiomatically starts with sheets of assertion.
    Enforces proper EG transformation rule sequence.
    """

    def __init__(self, default_sheet_type: SheetType = SheetType.COMMON_SHEET):
        from egi_transformation_pipeline import EGITransformationPipeline

        self.pipeline = EGITransformationPipeline()
        self.default_sheet_type = default_sheet_type

        # State management
        self.assertion_sheets: Dict[str, AssertionSheet] = {}
        self.constructions: Dict[str, GraphConstruction] = {}
        self.common_sheet_id: Optional[str] = None

        # Pattern library for copy-paste functionality
        self.pattern_library: Dict[str, str] = {}  # pattern_name -> egi_id

        # Initialize common sheet if using shared approach
        if default_sheet_type == SheetType.COMMON_SHEET:
            self.common_sheet_id = self.create_assertion_sheet(
                "Common Assertion Sheet", "Shared sheet for all graph constructions"
            )

    def create_assertion_sheet(self, title: str, description: str) -> str:
        """Create a new assertion sheet starting with empty context (graph 0)."""
        sheet_id = str(uuid.uuid4())

        # Create the base empty EGI (graph 0)
        base_egi_id = self._create_empty_egi_id()

        sheet = AssertionSheet(
            sheet_id=sheet_id,
            sheet_type=self.default_sheet_type,
            title=title,
            description=description,
            base_egi_id=base_egi_id,
        )

        self.assertion_sheets[sheet_id] = sheet
        return sheet_id

    def prepare_sheet_for_construction(self, sheet_id: str) -> str:
        """
        Apply DC+ (Double Cut insertion) to create the oddly-enclosed area.
        This transforms graph 0 to graph 1, enabling subsequent insertions.
        """
        sheet = self.assertion_sheets.get(sheet_id)
        if not sheet:
            raise ValueError(f"Assertion sheet {sheet_id} not found")

        if sheet.has_working_area():
            return sheet.first_cut_egi_id

        # Apply DC+ transformation: insert double cut on empty sheet
        # This creates an oddly-enclosed area where insertions are permitted
        first_cut_egi_id = self.pipeline.apply_transformation(
            source_egi_id=sheet.base_egi_id,
            rule_type=TransformationRuleType.INSERTION,
            transformation_data={
                "element_type": "cut",
                "element_id": "outer_cut",
                "target_area": "sheet",
                "enclosed_elements": frozenset(),
            },
            context_type=ContextType.ERGASTERION,
            logical_justification="DC+ - Insert outer cut for double cut pattern",
        )

        # Insert inner cut to complete double cut pattern
        second_cut_egi_id = self.pipeline.apply_transformation(
            source_egi_id=first_cut_egi_id,
            rule_type=TransformationRuleType.INSERTION,
            transformation_data={
                "element_type": "cut",
                "element_id": "inner_cut",
                "target_area": "outer_cut",
                "enclosed_elements": frozenset(),
            },
            context_type=ContextType.ERGASTERION,
            logical_justification="DC+ - Insert inner cut to complete double cut pattern",
        )

        # Update sheet with working area
        sheet.first_cut_egi_id = second_cut_egi_id

        return second_cut_egi_id

    def start_construction(
        self, title: str, description: str, sheet_id: Optional[str] = None
    ) -> str:
        """Start a new graph construction on an assertion sheet."""

        # Use common sheet if none specified and it exists
        if sheet_id is None and self.common_sheet_id:
            sheet_id = self.common_sheet_id
        elif sheet_id is None:
            # Create individual sheet
            sheet_id = self.create_assertion_sheet(
                f"Sheet for {title}", f"Individual assertion sheet for {description}"
            )

        # Ensure sheet has working area (DC+ applied)
        working_egi_id = self.prepare_sheet_for_construction(sheet_id)

        construction_id = str(uuid.uuid4())
        construction = GraphConstruction(
            construction_id=construction_id,
            title=title,
            description=description,
            sheet_id=sheet_id,
            starting_egi_id=working_egi_id,
            current_egi_id=working_egi_id,
        )

        self.constructions[construction_id] = construction

        # Register construction with sheet
        sheet = self.assertion_sheets[sheet_id]
        sheet.constructions[construction_id] = working_egi_id

        return construction_id

    def add_to_construction(
        self,
        construction_id: str,
        transformation_data: Dict[str, Any],
        justification: str,
    ) -> str:
        """Add an element to a construction following EG rules."""
        construction = self.constructions.get(construction_id)
        if not construction:
            raise ValueError(f"Construction {construction_id} not found")

        if construction.is_complete:
            raise ValueError(f"Construction {construction_id} is already complete")

        # Determine appropriate rule type based on transformation data
        rule_type = self._determine_rule_type(transformation_data)

        # Apply transformation
        new_egi_id = self.pipeline.apply_transformation(
            source_egi_id=construction.current_egi_id,
            rule_type=rule_type,
            transformation_data=transformation_data,
            context_type=ContextType.ERGASTERION,
            logical_justification=justification,
        )

        # Update construction
        construction.current_egi_id = new_egi_id

        # Get transformation step for history
        history = self.pipeline.get_transformation_history(new_egi_id)
        if history:
            construction.transformation_history.append(history[-1])

        return new_egi_id

    def copy_subgraph_pattern(
        self, source_egi_id: str, target_construction_id: str, pattern_name: str
    ) -> str:
        """
        Copy a subgraph pattern from one context to another.
        This leverages the benefit of common sheets for reusing established patterns.
        """
        construction = self.constructions.get(target_construction_id)
        if not construction:
            raise ValueError(f"Target construction {target_construction_id} not found")

        # Get source EGI
        source_egi = self.pipeline.get_egi_state(source_egi_id)
        if not source_egi:
            raise ValueError(f"Source EGI {source_egi_id} not found")

        # For now, implement simple pattern copying
        # In a full implementation, this would involve sophisticated subgraph extraction
        # and insertion while maintaining proper ν mappings and area relationships

        # Store pattern for future use
        self.pattern_library[pattern_name] = source_egi_id

        # Apply pattern elements to target construction
        # This is a simplified implementation - full version would need careful
        # element ID remapping and area management

        new_egi_id = construction.current_egi_id

        # Copy vertices
        for vertex in source_egi.V:
            new_vertex_id = f"{pattern_name}_{vertex.element_id}"
            new_egi_id = self.add_to_construction(
                target_construction_id,
                {
                    "element_type": "vertex",
                    "element_id": new_vertex_id,
                    "target_area": "inner_cut",  # Insert in working area
                },
                f"Copy vertex {vertex.element_id} from pattern {pattern_name}",
            )

        # Copy edges (simplified - would need proper vertex sequence mapping)
        for edge in source_egi.E:
            if edge.element_id in source_egi.nu:
                vertex_sequence = source_egi.nu[edge.element_id]
                new_vertex_sequence = tuple(
                    f"{pattern_name}_{vid}" for vid in vertex_sequence
                )

                new_egi_id = self.add_to_construction(
                    target_construction_id,
                    {
                        "element_type": "edge",
                        "element_id": f"{pattern_name}_{edge.element_id}",
                        "target_area": "inner_cut",
                        "vertex_sequence": new_vertex_sequence,
                        "relation_name": source_egi.rel.get(edge.element_id, "R"),
                    },
                    f"Copy edge {edge.element_id} from pattern {pattern_name}",
                )

        return new_egi_id

    def create_disjunction_pattern(self, sheet_id: Optional[str] = None) -> str:
        """
        Create the standard disjunction pattern: two sibling cuts inside an enclosing cut.
        This can be copied and reused rather than reconstructed each time.
        """
        if sheet_id is None:
            sheet_id = self.common_sheet_id or self.create_assertion_sheet(
                "Disjunction Pattern Sheet", "Sheet for disjunction pattern"
            )

        construction_id = self.start_construction(
            "Disjunction Pattern",
            "Standard x OR y pattern with two sibling cuts",
            sheet_id,
        )

        # Create enclosing cut for disjunction
        self.add_to_construction(
            construction_id,
            {
                "element_type": "cut",
                "element_id": "disjunction_outer",
                "target_area": "inner_cut",
                "enclosed_elements": frozenset(),
            },
            "Create outer cut for disjunction pattern",
        )

        # Create first sibling cut (for x)
        self.add_to_construction(
            construction_id,
            {
                "element_type": "cut",
                "element_id": "disjunction_x_cut",
                "target_area": "disjunction_outer",
                "enclosed_elements": frozenset(),
            },
            "Create cut for x in disjunction",
        )

        # Create second sibling cut (for y)
        self.add_to_construction(
            construction_id,
            {
                "element_type": "cut",
                "element_id": "disjunction_y_cut",
                "target_area": "disjunction_outer",
                "enclosed_elements": frozenset(),
            },
            "Create cut for y in disjunction",
        )

        construction = self.constructions[construction_id]
        construction.is_complete = True

        # Store as reusable pattern
        self.pattern_library["disjunction_template"] = construction.current_egi_id

        return construction.current_egi_id

    def fill_disjunction_pattern(
        self,
        pattern_egi_id: str,
        x_elements: List[Dict[str, Any]],
        y_elements: List[Dict[str, Any]],
    ) -> str:
        """
        Fill a disjunction pattern with specific x and y elements.
        Demonstrates copy-paste workflow for established patterns.
        """
        # Create new construction for filled disjunction
        construction_id = self.start_construction(
            "Filled Disjunction",
            f"Disjunction with {len(x_elements)} x elements and {len(y_elements)} y elements",
        )

        # Copy the pattern structure
        self.copy_subgraph_pattern(pattern_egi_id, construction_id, "disjunction_base")

        # Fill x cut with elements
        for i, element in enumerate(x_elements):
            self.add_to_construction(
                construction_id,
                {
                    "element_type": element.get("type", "vertex"),
                    "element_id": f"x_{i}_{element.get('id', f'elem_{i}')}",
                    "target_area": "disjunction_base_disjunction_x_cut",
                },
                f"Add x element {i+1} to disjunction",
            )

        # Fill y cut with elements
        for i, element in enumerate(y_elements):
            self.add_to_construction(
                construction_id,
                {
                    "element_type": element.get("type", "vertex"),
                    "element_id": f"y_{i}_{element.get('id', f'elem_{i}')}",
                    "target_area": "disjunction_base_disjunction_y_cut",
                },
                f"Add y element {i+1} to disjunction",
            )

        construction = self.constructions[construction_id]
        construction.is_complete = True

        return construction.current_egi_id

    def _create_empty_egi_id(self) -> str:
        """Create an empty EGI and return its ID."""
        empty_egi = RelationalGraphWithCuts(
            V=frozenset(),
            E=frozenset(),
            nu=frozendict(),
            sheet=ElementID("sheet"),
            Cut=frozenset(),
            area=frozendict({ElementID("sheet"): frozenset()}),
            rel=frozendict(),
        )

        # Store in pipeline repository
        egi_id = str(uuid.uuid4())
        from immutable_transformation_architecture import EGISnapshot

        snapshot = EGISnapshot(
            egi_id=egi_id,
            egi_state=empty_egi,
            timestamp=datetime.now(),
            context_type=ContextType.SHEET_OF_ASSERTION,
            provenance_step_id=None,
            logical_description="Empty sheet of assertion (Graph 0)",
            spatial_layout=frozendict(),
        )
        self.pipeline.repository.store_egi_snapshot(snapshot)
        return egi_id

    def _determine_rule_type(
        self, transformation_data: Dict[str, Any]
    ) -> TransformationRuleType:
        """Determine appropriate transformation rule type."""
        # For now, most operations are insertions
        # Full implementation would analyze context and determine if erasure or iteration applies
        return TransformationRuleType.INSERTION

    def get_sheet_summary(self, sheet_id: str) -> Dict[str, Any]:
        """Get summary of an assertion sheet."""
        sheet = self.assertion_sheets.get(sheet_id)
        if not sheet:
            return {"error": "Sheet not found"}

        return {
            "sheet_id": sheet_id,
            "title": sheet.title,
            "description": sheet.description,
            "sheet_type": sheet.sheet_type.value,
            "has_working_area": sheet.has_working_area(),
            "constructions": len(sheet.constructions),
            "construction_list": list(sheet.constructions.keys()),
            "created_at": sheet.created_at.isoformat(),
        }

    def get_construction_summary(self, construction_id: str) -> Dict[str, Any]:
        """Get summary of a graph construction."""
        construction = self.constructions.get(construction_id)
        if not construction:
            return {"error": "Construction not found"}

        current_egi = self.pipeline.get_egi_state(construction.current_egi_id)

        return {
            "construction_id": construction_id,
            "title": construction.title,
            "description": construction.description,
            "sheet_id": construction.sheet_id,
            "is_complete": construction.is_complete,
            "transformation_steps": len(construction.transformation_history),
            "current_state": {
                "vertices": len(current_egi.V) if current_egi else 0,
                "edges": len(current_egi.E) if current_egi else 0,
                "cuts": len(current_egi.Cut) if current_egi else 0,
            },
            "created_at": construction.created_at.isoformat(),
        }


def demonstrate_foundational_building():
    """Demonstrate the foundational graph building approach."""

    print("📜 Foundational Graph Building System")
    print("=" * 40)
    print("Starting axiomatically with sheet of assertion...")

    builder = FoundationalGraphBuilder(SheetType.COMMON_SHEET)

    print(f"\n✅ Common assertion sheet created: {builder.common_sheet_id[:8]}...")

    # Demonstrate proper sequence: Graph 0 -> DC+ -> Graph 1 -> constructions
    print("\n🎯 Step 1: Apply DC+ to create working area")
    working_egi_id = builder.prepare_sheet_for_construction(builder.common_sheet_id)
    print(f"   Working area EGI: {working_egi_id[:8]}...")

    # Build simple conjunction
    print("\n🎯 Step 2: Build simple conjunction A ∧ B")
    conjunction_id = builder.start_construction(
        "Simple Conjunction", "A ∧ B built on assertion sheet"
    )

    builder.add_to_construction(
        conjunction_id,
        {"element_type": "vertex", "element_id": "A", "target_area": "inner_cut"},
        "Insert vertex A in oddly-enclosed area",
    )

    builder.add_to_construction(
        conjunction_id,
        {"element_type": "vertex", "element_id": "B", "target_area": "inner_cut"},
        "Insert vertex B for conjunction",
    )

    conjunction_summary = builder.get_construction_summary(conjunction_id)
    print(f"   Result: {conjunction_summary['current_state']}")

    # Create reusable disjunction pattern
    print("\n🎯 Step 3: Create reusable disjunction pattern")
    disjunction_pattern_id = builder.create_disjunction_pattern()
    print(f"   Pattern EGI: {disjunction_pattern_id[:8]}...")

    # Use pattern with copy-paste approach
    print("\n🎯 Step 4: Use pattern for P ∨ Q")
    filled_disjunction_id = builder.fill_disjunction_pattern(
        disjunction_pattern_id,
        [{"id": "P", "type": "vertex"}],
        [{"id": "Q", "type": "vertex"}],
    )

    print(f"   Filled disjunction EGI: {filled_disjunction_id[:8]}...")

    # Show system summary
    sheet_summary = builder.get_sheet_summary(builder.common_sheet_id)
    print(f"\n📊 System Summary:")
    print(f"   Assertion sheets: {len(builder.assertion_sheets)}")
    print(f"   Constructions: {len(builder.constructions)}")
    print(f"   Pattern library: {len(builder.pattern_library)}")
    print(f"   Sheet constructions: {sheet_summary['constructions']}")

    return builder


if __name__ == "__main__":
    demonstrate_foundational_building()
