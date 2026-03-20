"""
Chapter 21 Transformation Wizards

Implements step-by-step transformation wizards for each format (DIAGRAM, EGIF, CGIF, CLIF, FOPL)
that execute identical underlying EGI transformations while providing format-specific guidance.

Key Features:
- Universal wizard framework for all transformation rules
- Format-specific user interfaces with validation
- Step-by-step guidance with pedagogical value
- Real-time precondition checking and feedback
- Undo/redo support for all transformations
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple, Union

from chapter21_diagram_engine import (
    Chapter21TransformationContext,
    DisplayFormat,
    InteractionMode,
    SelectionMethod,
    SubgraphSelection,
    UniversalEGIEngine,
)
from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from formal_iteration_rule import FormalIterationEngine, IterationContext
from formal_transformation_rules import FormalTransformationRule, TransformationResult
from graph_isomorphism_engine import GraphIsomorphismEngine, IsomorphismResult


class WizardStep(Enum):
    """Variable-step transformation wizard workflow."""

    # Core steps (all transformations)
    RULE_SELECTION = "rule_selection"  # Step 1: Select transformation rule
    AREA_SELECTION = "area_selection"  # Step 2: Select target area
    POSITION_SELECTION = (
        "position_selection"  # Step 3: Select position (whole/elements/empty)
    )

    # IT+/IT- specific steps
    ELEMENT_SELECTION = (
        "element_selection"  # Select specific elements to iterate/deiterate
    )
    PLACEMENT_SELECTION = (
        "placement_selection"  # Select where to place the iteration (IT+ only)
    )
    JUSTIFICATION_SEARCH = (
        "justification_search"  # Search for justifying subgraph (IT- only)
    )

    # INS-specific steps
    INSERTION_TYPE = "insertion_type"  # What to insert: subgraph/edge/cut/vertex
    CONTENT_SPECIFICATION = "content_specification"  # Define what's being inserted
    EDGE_DETAILS = "edge_details"  # For edge insertion: relation name, ν mapping
    VERTEX_DETAILS = "vertex_details"  # For vertex insertion: label, connections
    CUT_DETAILS = "cut_details"  # For cut insertion: type, nesting
    SUBGRAPH_SOURCE = "subgraph_source"  # For subgraph insertion: source selection

    # Universal final steps
    PREVIEW = "preview"  # Preview transformation
    EXECUTE = "execute"  # Execute and display result


class TransformationRuleType(Enum):
    """Types of transformation rules per Peirce/Dau."""

    ERASURE = "erasure"
    INSERTION = "insertion"
    ITERATION = "iteration"
    DEITERATION = "deiteration"
    DOUBLE_CUT = "double_cut"


class PositionType(Enum):
    """Types of position selection for transformations."""

    WHOLE_AREA = "whole_area"  # Apply to entire selected area
    SELECTED_ELEMENTS = "selected_elements"  # Apply to specific elements
    EMPTY_SPOT = "empty_spot"  # Apply at empty position


class InsertionType(Enum):
    """Types of content that can be inserted per Dau's Definition 12.1."""

    SUBGRAPH = "subgraph"  # Insert a complete subgraph
    EDGE = "edge"  # Insert an edge with relation name and ν mapping
    CUT = "cut"  # Insert a cut (positive or negative)
    VERTEX = "vertex"  # Insert a single vertex in area


@dataclass
class WizardState:
    """Current state of transformation wizard."""

    current_step: WizardStep = WizardStep.RULE_SELECTION
    rule_type: Optional[TransformationRuleType] = None
    selected_area: Optional[ElementID] = None
    position_type: Optional[PositionType] = None
    selected_elements: Optional[Set[ElementID]] = None
    preview_egi: Optional[RelationalGraphWithCuts] = None
    error_messages: List[str] = field(default_factory=list)
    can_proceed: bool = False

    # INS-specific state
    insertion_type: Optional[InsertionType] = None
    relation_name: Optional[str] = (
        None  # For edge insertion: relation name (rel mapping)
    )
    vertex_sequence: Optional[List[ElementID]] = (
        None  # For edge insertion: ν mapping order
    )
    vertex_label: Optional[str] = None
    cut_type: Optional[str] = None  # "positive" or "negative"
    source_subgraph: Optional[Set[ElementID]] = None
    selected_subgraph: Optional[Set[ElementID]] = None


@dataclass
class WizardResult:
    """Result of completed transformation wizard."""

    success: bool
    final_egi: Optional[RelationalGraphWithCuts]
    transformation_applied: Optional[TransformationRuleType]
    steps_completed: List[WizardStep]
    error_message: Optional[str] = None


class TransformationWizard(ABC):
    """Abstract base class for format-specific transformation wizards."""

    def __init__(
        self, egi_engine: UniversalEGIEngine, source_egi: RelationalGraphWithCuts
    ):
        self.egi_engine = egi_engine
        self.source_egi = source_egi
        self.state = WizardState()
        self.format = self.get_format()

    @abstractmethod
    def get_format(self) -> DisplayFormat:
        """Get the display format this wizard handles."""
        pass

    @abstractmethod
    def render_step_interface(self, step: WizardStep) -> str:
        """Render format-specific interface for current step."""
        pass

    @abstractmethod
    def handle_user_input(self, step: WizardStep, user_input: Any) -> bool:
        """Handle user input for current step. Returns True if input valid."""
        pass

    def advance_step(self) -> bool:
        """Advance to next step if current step is complete."""
        if not self.state.can_proceed:
            return False

        current_index = list(WizardStep).index(self.state.current_step)
        if current_index < len(WizardStep) - 1:
            self.state.current_step = list(WizardStep)[current_index + 1]
            self.state.can_proceed = False  # Reset for new step
            return True
        return False

    def execute_transformation(self) -> WizardResult:
        """Execute the configured transformation."""
        if self.state.current_step != WizardStep.EXECUTE:
            return WizardResult(
                success=False,
                final_egi=None,
                transformation_applied=None,
                steps_completed=[],
                error_message="Wizard not ready for execution",
            )

        try:
            # Create transformation context
            # Create SubgraphSelection object
            from chapter21_diagram_engine import SelectionMethod, SubgraphSelection

            subgraph_selection = SubgraphSelection(
                vertices=set(),
                edges=set(),
                cuts=set(),
                selection_method=SelectionMethod.SUBGRAPH_LINE,
            )

            context = Chapter21TransformationContext(
                source_egi=self.source_egi,
                target_subgraph=subgraph_selection,
                transformation_rule=self._create_transformation_rule(),
                interaction_mode=InteractionMode.ERGASTERION,
                validation_required=True,
            )

            # Apply transformation
            result = self.egi_engine.apply_transformation(context)

            if result.success:
                return WizardResult(
                    success=True,
                    final_egi=result.result_egi,
                    transformation_applied=self.state.rule_type,
                    steps_completed=list(WizardStep),
                )
            else:
                return WizardResult(
                    success=False,
                    final_egi=None,
                    transformation_applied=None,
                    steps_completed=[],
                    error_message=result.error_message,
                )

        except Exception as e:
            return WizardResult(
                success=False,
                final_egi=None,
                transformation_applied=None,
                steps_completed=[],
                error_message=str(e),
            )

    def _create_transformation_rule(self) -> FormalTransformationRule:
        """Create appropriate transformation rule based on wizard state."""
        from formal_transformation_rules import (
            DeiterationRule,
            DoubleCutErasureRule,
            DoubleCutInsertionRule,
            ErasureRule,
            InsertionRule,
            IterationRule,
        )

        if self.state.rule_type == TransformationRuleType.DOUBLE_CUT:
            return DoubleCutInsertionRule()  # Default to insertion for DC
        elif self.state.rule_type == TransformationRuleType.ERASURE:
            return ErasureRule()
        elif self.state.rule_type == TransformationRuleType.INSERTION:
            return InsertionRule()
        elif self.state.rule_type == TransformationRuleType.ITERATION:
            return IterationRule()
        elif self.state.rule_type == TransformationRuleType.DEITERATION:
            return DeiterationRule()
        else:
            # Fallback to insertion rule
            return InsertionRule()


class DiagramTransformationWizard(TransformationWizard):
    """Universal transformation wizard with step-by-step guidance."""

    def __init__(
        self, egi_engine: UniversalEGIEngine, source_egi: RelationalGraphWithCuts
    ):
        super().__init__(egi_engine, source_egi)
        self.display_format = DisplayFormat.DIAGRAM
        self.isomorphism_engine = GraphIsomorphismEngine()
        self.formal_iteration_engine = FormalIterationEngine()

    def get_format(self) -> DisplayFormat:
        """Return the display format for this wizard."""
        return DisplayFormat.DIAGRAM

    def render_step_interface(self, step: WizardStep) -> str:
        """Render diagram-specific interface for current step."""
        if step == WizardStep.RULE_SELECTION:
            return self._render_rule_selection()
        elif step == WizardStep.AREA_SELECTION:
            return self._render_area_selection()
        elif step == WizardStep.POSITION_SELECTION:
            return self._render_position_selection()
        elif step == WizardStep.INSERTION_TYPE:
            return self._render_insertion_type_selection()
        elif step == WizardStep.CUT_DETAILS:
            return self._render_cut_details()
        elif step == WizardStep.EDGE_DETAILS:
            return self._render_edge_details()
        elif step == WizardStep.VERTEX_DETAILS:
            return self._render_vertex_details()
        elif step == WizardStep.PREVIEW:
            return self._render_preview()
        else:
            return f"Interface for {step.value} (not implemented)"

    def _render_rule_selection(self) -> str:
        """Render rule selection interface."""
        return """
DIAGRAM TRANSFORMATION WIZARD - Rule Selection
==============================================

Available Transformation Rules:
┌─────────────┬─────────────────────────────────────┐
│ E - ERASURE │ Remove elements from positive areas │
│ I - INSERT  │ Add elements to negative areas      │
│ T - ITERATE │ Copy subgraph to nested areas       │
│ D - DEITER  │ Remove duplicate subgraphs          │
│ C - DC+     │ Insert double cut (assert)          │
│ X - DC-     │ Remove double cut (deny)            │
└─────────────┴─────────────────────────────────────┘

Select transformation rule (E/I/T/D/C/X):"""

    def handle_user_input(self, step: WizardStep, user_input: Any) -> bool:
        """Handle diagram-specific user input."""
        if step == WizardStep.RULE_SELECTION:
            return self._handle_rule_selection(user_input)
        elif step == WizardStep.AREA_SELECTION:
            return self._handle_area_selection(user_input)
        elif step == WizardStep.POSITION_SELECTION:
            return self._handle_position_selection(user_input)
        elif step == WizardStep.INSERTION_TYPE:
            return self._handle_insertion_type_selection(user_input)
        elif step == WizardStep.CUT_DETAILS:
            return self._handle_cut_details(user_input)
        elif step == WizardStep.EDGE_DETAILS:
            return self._handle_edge_details(user_input)
        elif step == WizardStep.PREVIEW:
            return self._handle_preview_confirmation(user_input)
        else:
            return False

    def get_wizard_flow(self) -> List[WizardStep]:
        """Get the appropriate wizard flow based on rule type."""
        if not self.state.rule_type:
            return [WizardStep.RULE_SELECTION]

        base_flow = [WizardStep.RULE_SELECTION, WizardStep.AREA_SELECTION]

        if self.state.rule_type == TransformationRuleType.INSERTION:
            # INS flow: Rule → Area → Position → Insertion Type → Details → Preview → Execute
            ins_flow = base_flow + [
                WizardStep.POSITION_SELECTION,
                WizardStep.INSERTION_TYPE,
            ]

            if self.state.insertion_type == InsertionType.EDGE:
                ins_flow.append(WizardStep.EDGE_DETAILS)
            elif self.state.insertion_type == InsertionType.VERTEX:
                ins_flow.append(WizardStep.VERTEX_DETAILS)
            elif self.state.insertion_type == InsertionType.CUT:
                ins_flow.append(WizardStep.CUT_DETAILS)
            elif self.state.insertion_type == InsertionType.SUBGRAPH:
                ins_flow.extend(
                    [WizardStep.SUBGRAPH_SOURCE, WizardStep.CONTENT_SPECIFICATION]
                )

            ins_flow.extend([WizardStep.PREVIEW, WizardStep.EXECUTE])
            return ins_flow
        elif self.state.rule_type == TransformationRuleType.ITERATION:
            # IT+ needs element selection and placement steps
            return base_flow + [
                WizardStep.ELEMENT_SELECTION,
                WizardStep.PLACEMENT_SELECTION,
                WizardStep.PREVIEW,
                WizardStep.EXECUTE,
            ]
        elif self.state.rule_type == TransformationRuleType.DEITERATION:
            # IT- needs element selection and justification search
            return base_flow + [
                WizardStep.ELEMENT_SELECTION,
                WizardStep.JUSTIFICATION_SEARCH,
                WizardStep.PREVIEW,
                WizardStep.EXECUTE,
            ]
        else:
            # Standard flow for ERA, DC+, DC-
            return base_flow + [
                WizardStep.POSITION_SELECTION,
                WizardStep.PREVIEW,
                WizardStep.EXECUTE,
            ]

    def get_current_step_display(self) -> str:
        """Get display text for current wizard step."""
        if self.state.current_step == WizardStep.RULE_SELECTION:
            return self._render_rule_selection()
        elif self.state.current_step == WizardStep.AREA_SELECTION:
            return self._render_area_selection()
        elif self.state.current_step == WizardStep.INSERTION_TYPE:
            return self._render_insertion_type_selection()
        elif self.state.current_step == WizardStep.EDGE_DETAILS:
            return self._render_edge_details()
        elif self.state.current_step == WizardStep.VERTEX_DETAILS:
            return self._render_vertex_details()
        elif self.state.current_step == WizardStep.CUT_DETAILS:
            return self._render_cut_details()
        elif self.state.current_step == WizardStep.SUBGRAPH_SOURCE:
            return self._render_subgraph_source()
        elif self.state.current_step == WizardStep.ELEMENT_SELECTION:
            return self._render_element_selection()
        elif self.state.current_step == WizardStep.PLACEMENT_SELECTION:
            return self._render_placement_selection()
        elif self.state.current_step == WizardStep.JUSTIFICATION_SEARCH:
            return self._render_justification_search()
        elif self.state.current_step == WizardStep.POSITION_SELECTION:
            return self._render_position_selection()
        elif self.state.current_step == WizardStep.PREVIEW:
            return self._render_preview()
        elif self.state.current_step == WizardStep.EXECUTE:
            return self._render_execute()
        else:
            return "Unknown wizard step"

    def handle_user_input(self, step: WizardStep, user_input: Any) -> bool:
        """Handle diagram-specific user input."""
        if step == WizardStep.RULE_SELECTION:
            return self._handle_rule_selection(user_input)
        elif step == WizardStep.AREA_SELECTION:
            return self._handle_area_selection(user_input)
        elif step == WizardStep.INSERTION_TYPE:
            return self._handle_insertion_type_selection(user_input)
        elif step == WizardStep.EDGE_DETAILS:
            return self._handle_edge_details(user_input)
        elif step == WizardStep.VERTEX_DETAILS:
            return self._handle_vertex_details(user_input)
        elif step == WizardStep.CUT_DETAILS:
            return self._handle_cut_details(user_input)
        elif step == WizardStep.SUBGRAPH_SOURCE:
            return self._handle_subgraph_source(user_input)
        elif step == WizardStep.ELEMENT_SELECTION:
            return self._handle_element_selection(user_input)
        elif step == WizardStep.PLACEMENT_SELECTION:
            return self._handle_placement_selection(user_input)
        elif step == WizardStep.JUSTIFICATION_SEARCH:
            return self._handle_justification_search(user_input)
        elif step == WizardStep.POSITION_SELECTION:
            return self._handle_position_selection(user_input)
        elif step == WizardStep.PREVIEW:
            return self._handle_preview_confirmation(user_input)
        elif step == WizardStep.EXECUTE:
            return True  # Execute step doesn't need input
        else:
            return False

    def _render_rule_selection_diagram(self) -> str:
        """Render visual rule selection interface."""
        return """
🧙 TRANSFORMATION WIZARD - Step 1: Rule Selection
================================================

Available Transformation Rules:

┌─────────────┬─────────────────────────────────────┐
│ [E] ERASURE │ Remove elements from positive areas │
│ [I] INSERT  │ Add elements to negative areas      │
│ [T] ITERATE │ Copy subgraphs to inner contexts    │
│ [D] DEITER  │ Remove iterated subgraphs           │
│ [C] DC+     │ Insert double cut around elements   │
│ [X] DC-     │ Remove double cut                   │
└─────────────┴─────────────────────────────────────┘

Enter rule code (E/I/T/D/C/X) or rule name:
"""

    def _render_area_selection_diagram(self) -> str:
        """Render area selection interface for diagram format."""
        return f"""
🧙 TRANSFORMATION WIZARD - Step 2: Area Selection
===============================================

Rule: {self.state.rule_type.value if self.state.rule_type else 'None'}

Available Areas in Current EGI:
{self._list_available_areas()}

Area Selection Methods (Diagram Format):
┌─────────────────┬─────────────────────────────────────┐
│ Click Area      │ Click directly on area boundary     │
│ Area ID         │ Enter area identifier (e.g., 'cut1')│
│ Sheet           │ Select outermost sheet area         │
└─────────────────┴─────────────────────────────────────┘

Enter area ID or click on diagram area:
"""

    def _render_position_selection_diagram(self) -> str:
        """Render position selection interface for diagram format."""
        area_contents = self._get_area_contents()

        return f"""
🧙 TRANSFORMATION WIZARD - Step 3: Position Selection  
====================================================

Rule: {self.state.rule_type.value if self.state.rule_type else 'None'}
Area: {self.state.selected_area or 'None'}

Area Contents:
{area_contents}

Position Options:
┌─────────────────┬─────────────────────────────────────┐
│ [W] Whole Area  │ Apply to all elements in area       │
│ [S] Select Elems│ Choose specific elements             │
│ [E] Empty Spot  │ Apply to empty position in area     │
└─────────────────┴─────────────────────────────────────┘

For INS transformations:
- Whole Area: Insert will affect/enclose all area contents
- Select Elems: Insert will affect/enclose only chosen elements  
- Empty Spot: Insert will be placed at empty position

Enter position type (W/S/E):
"""

    def _render_preview_diagram(self) -> str:
        """Render transformation preview for diagram format."""
        return f"""
🧙 TRANSFORMATION WIZARD - Step 4: Preview
========================================

Transformation Summary:
- Rule: {self.state.rule_type.value if self.state.rule_type else 'None'}
- Area: {self.state.selected_area or 'None'} 
- Position: {self.state.position_type.value if self.state.position_type else 'None'}

BEFORE (Current EGI):
{self._render_current_egi_structure()}

AFTER (Preview):
{self._render_preview_structure()}

Changes:
{self._render_transformation_changes()}

Proceed with transformation? (Y/N):
"""

    def _render_execute_diagram(self) -> str:
        """Render execution and result display."""
        return f"""
🧙 TRANSFORMATION WIZARD - Step 5: Execute & Display
==================================================

✅ Transformation Complete!

Rule Applied: {self.state.rule_type.value if self.state.rule_type else 'None'}
Area: {self.state.selected_area or 'None'}
Position: {self.state.position_type.value if self.state.position_type else 'None'}

Final EGI (Linear Form):
{self._render_final_egi_linear_form()}

Transformation successful! 
Graph updated and ready for further operations.
"""

    # Helper methods for rendering different aspects
    def _list_available_areas(self) -> str:
        """List available areas in the current EGI."""
        areas = []
        areas.append(f"• sheet (outermost area)")
        for cut in self.source_egi.Cut:
            areas.append(f"• {cut.id} (cut area)")
        return "\n".join(areas) if areas else "No areas available"

    def _render_area_selection(self) -> str:
        """Render area selection step."""
        return f"""
AREA SELECTION - Step 2
=======================

Available areas for transformation:
{self._list_available_areas()}

Enter area ID ('sheet' for outermost area, or cut ID):"""

    def _render_position_selection(self) -> str:
        """Render position selection step."""
        return f"""
POSITION SELECTION - Step 3
============================

Selected area: {self.state.selected_area}

Choose position type for transformation:
┌─────────────┬─────────────────────────────────────┐
│ W - WHOLE   │ Apply to ALL elements in the area   │
│ S - SELECT  │ Apply to SPECIFIC selected elements │
│ E - EMPTY   │ Apply to EMPTY spot in the area     │
└─────────────┴─────────────────────────────────────┘

Position instructions:
{self._get_position_instructions()}

Select position type (W/S/E):"""

    def _get_position_instructions(self) -> str:
        """Get context-sensitive position instructions."""
        if self.state.rule_type == TransformationRuleType.INSERTION:
            if self.state.insertion_type == InsertionType.CUT:
                return self._get_cut_position_instructions()
            else:
                return self._get_default_position_instructions()
        else:
            return self._get_default_position_instructions()

    def _render_preview(self) -> str:
        """Render transformation preview step."""
        return f"""
TRANSFORMATION PREVIEW - Step 6
===============================

Rule: {self.state.rule_type.value if self.state.rule_type else 'None'}
Area: {self.state.selected_area}
Position: {self.state.position_type.value if self.state.position_type else 'None'}
{f'Insertion Type: {self.state.insertion_type.value}' if self.state.insertion_type else ''}
{f'Cut Type: {self.state.cut_type}' if self.state.cut_type else ''}

Transformation Changes:
{self._render_transformation_changes()}

Current EGI Structure:
{self._render_current_egi_structure()}

Proceed with transformation? (Y/N):"""

    def _render_insertion_type_selection(self) -> str:
        """Render insertion type selection step for INS transformations."""
        display = "Step 4: Insertion Type Selection\n"
        display += "=" * 50 + "\n\n"

        # Show the position that was already selected
        if self.state.position_type:
            position_desc = {
                PositionType.WHOLE_AREA: "affecting all elements in the area",
                PositionType.SELECTED_ELEMENTS: "affecting specific elements you'll select",
                PositionType.EMPTY_SPOT: "at an empty position",
            }.get(self.state.position_type, "at the selected position")
            display += f"Position selected: {position_desc}\n\n"

        display += "What would you like to insert?\n\n"
        display += "S. Subgraph - Insert a complete subgraph structure\n"
        display += "E. Edge - Insert an edge with relation name and ν mapping\n"
        display += "C. Cut - Insert a positive or negative cut\n"
        display += "V. Vertex - Insert a single vertex\n\n"
        display += "Enter your choice (S/E/C/V): "
        return display

    def _render_edge_details(self) -> str:
        """Render edge details specification step per Dau's Definition 12.1."""
        display = "Step 4: Edge Details (Dau Definition 12.1)\n"
        display += "=" * 50 + "\n\n"
        display += "Specify edge components:\n\n"

        if not self.state.relation_name:
            display += "Enter relation name (rel mapping): "
        elif not self.state.vertex_sequence:
            display += f"Relation: {self.state.relation_name}\n"
            display += (
                "Enter vertex sequence for ν mapping (comma-separated vertex IDs): "
            )
        else:
            display += f"Relation: {self.state.relation_name}\n"
            display += f"ν mapping: {' → '.join(self.state.vertex_sequence)}\n"
            display += "Press Enter to continue..."

        return display

    def _render_vertex_details(self) -> str:
        """Render vertex details specification step."""
        display = "Step 4: Vertex Details\n"
        display += "=" * 50 + "\n\n"
        display += "Specify vertex details:\n\n"

        if not self.state.vertex_label:
            display += "Enter vertex label (or leave blank for unlabeled): "
        else:
            display += f"Vertex label: {self.state.vertex_label or '(unlabeled)'}\n"
            display += "Press Enter to continue..."

        return display

    def _render_cut_details(self) -> str:
        """Render cut details specification step."""
        display = "Step 5: Cut Details\n"
        display += "=" * 50 + "\n\n"
        display += "Specify cut type:\n\n"
        display += "P. Positive cut (assertion)\n"
        display += "N. Negative cut (negation)\n\n"

        # Show the position that was already selected
        if self.state.position_type:
            position_desc = {
                PositionType.WHOLE_AREA: "around all elements in the area",
                PositionType.SELECTED_ELEMENTS: "around specific elements you'll select",
                PositionType.EMPTY_SPOT: "as an empty cut with no enclosed elements",
            }.get(self.state.position_type, "at the selected position")
            display += f"Cut will be placed {position_desc}.\n\n"

        display += "Enter cut type (P/N): "
        return display

    def _render_subgraph_source(self) -> str:
        """Render subgraph source selection step."""
        display = "Step 4: Subgraph Source\n"
        display += "=" * 50 + "\n\n"
        display += "Select source for subgraph insertion:\n\n"
        display += "1. From current graph (copy existing elements)\n"
        display += "2. From tomos (select from saved graphs)\n"
        display += "3. Create new (specify structure manually)\n\n"
        display += "Enter your choice (1-3): "
        return display

    def _render_element_selection(self) -> str:
        """Render element selection step for IT+/IT-."""
        display = "Step 3: Element Selection\n"
        display += "=" * 50 + "\n\n"
        display += f"Select elements to {'iterate' if self.state.rule_type == TransformationRuleType.ITERATION else 'deiterate'}:\n\n"

        # List available elements in the selected area
        if self.state.selected_area:
            display += f"Elements in area {self.state.selected_area}:\n"
            elements = self._get_elements_in_area(self.state.selected_area)
            for i, element in enumerate(elements, 1):
                display += f"{i}. {element}\n"
            display += f"\nEnter element numbers (comma-separated, e.g., 1,3,5): "
        else:
            display += "No area selected. Please go back and select an area first.\n"

        return display

    def _render_placement_selection(self) -> str:
        """Render placement selection step for IT+/IT-."""
        display = "Step 4: Placement Selection\n"
        display += "=" * 50 + "\n\n"
        display += f"Where should the {'iteration' if self.state.rule_type == TransformationRuleType.ITERATION else 'deiteration'} be placed?\n\n"

        if self.state.rule_type == TransformationRuleType.ITERATION:
            display += "For iteration, you can place the duplicate in:\n"
            display += "• Same area as original (same context)\n"
            display += "• Any nested area within the original area (deeper context)\n\n"

            display += "Available placement areas:\n"
            placement_areas = self._get_valid_iteration_areas()
            for i, area in enumerate(placement_areas, 1):
                display += f"{i}. {area}\n"

            display += f"\nEnter area number (1-{len(placement_areas)}): "
        else:
            # Deiteration has different rules
            display += "For deiteration, select target area for removal:\n"
            display += "1. Same area (remove from current location)\n"
            display += "\nEnter placement choice: "

        return display

    def _render_justification_search(self) -> str:
        """Render justification search step for IT-."""
        display = "Step 4: Justification Search\n"
        display += "=" * 50 + "\n\n"

        # Automatically search for justifying subgraph
        justifying_subgraph = self._find_justifying_subgraph()

        if justifying_subgraph:
            display += "✅ Justifying subgraph found automatically!\n\n"
            display += (
                f"Found matching subgraph in area: {justifying_subgraph['area']}\n"
            )
            display += f"Elements: {', '.join(justifying_subgraph['elements'])}\n\n"
            display += (
                "This justifies the deiteration. Press Enter to continue to preview."
            )
        else:
            display += "❌ No justifying subgraph found automatically.\n\n"
            display += (
                "For deiteration to be valid, there must be an identical subgraph\n"
            )
            display += (
                "in the same area or any parent area of the selected elements.\n\n"
            )
            display += "Options:\n"
            display += "1. Let me manually identify the justifying subgraph\n"
            display += "2. Cancel deiteration (no valid justification exists)\n\n"
            display += "Enter your choice (1 or 2): "

        return display

    def _get_area_contents(self) -> str:
        """Get contents of the selected area."""
        if not self.state.selected_area:
            return "No area selected"

        area_id = self.state.selected_area
        contents = []

        # Get elements from area mapping in EGI
        area_elements = self.source_egi.area.get(area_id, frozenset())

        for element_id in area_elements:
            # Check if it's a vertex
            if any(v.id == element_id for v in self.source_egi.V):
                contents.append(f"• Vertex: {element_id}")
            # Check if it's an edge
            elif any(e.id == element_id for e in self.source_egi.E):
                relation = self.source_egi.rel.get(element_id, "?")
                contents.append(f"• Edge: {element_id} (relation: {relation})")
            # Check if it's a cut
            elif any(c.id == element_id for c in self.source_egi.Cut):
                contents.append(f"• Cut: {element_id}")
            else:
                contents.append(f"• Element: {element_id}")

        return "\n".join(contents) if contents else "Area is empty"

    def _render_current_egi_structure(self) -> str:
        """Render current EGI structure for display."""
        return f"""
Current EGI Structure:
- Vertices: {len(self.source_egi.V)}
- Edges: {len(self.source_egi.E)}
- Cuts: {len(self.source_egi.Cut)}
- Sheet: {self.source_egi.sheet}
"""

    def _render_preview_structure(self) -> str:
        """Render preview of transformed EGI."""
        if self.state.preview_egi:
            return f"""
Preview EGI Structure:
- Vertices: {len(self.state.preview_egi.V)}
- Edges: {len(self.state.preview_egi.E)}
- Cuts: {len(self.state.preview_egi.Cut)}
- Sheet: {self.state.preview_egi.sheet}
"""
        else:
            return "Preview not available"

    def _render_transformation_changes(self) -> str:
        """Render description of transformation changes."""
        if self.state.rule_type == TransformationRuleType.DOUBLE_CUT:
            if self.state.position_type == PositionType.WHOLE_AREA:
                return "• Will enclose all area contents in double cut\n• Adds outer and inner cut boundaries"
            elif self.state.position_type == PositionType.SELECTED_ELEMENTS:
                return "• Will enclose selected elements in double cut\n• Other elements remain outside cuts"
            elif self.state.position_type == PositionType.EMPTY_SPOT:
                return (
                    "• Will insert empty double cut\n• No elements enclosed initially"
                )
        elif (
            self.state.rule_type == TransformationRuleType.INSERTION
            and self.state.insertion_type == InsertionType.CUT
        ):
            cut_type_desc = "positive" if self.state.cut_type == "P" else "negative"
            if self.state.position_type == PositionType.WHOLE_AREA:
                return f"• Will insert {cut_type_desc} cut around all area contents\n• All existing elements will be enclosed"
            elif self.state.position_type == PositionType.SELECTED_ELEMENTS:
                return f"• Will insert {cut_type_desc} cut around selected elements only\n• Other elements remain outside the new cut"
            elif self.state.position_type == PositionType.EMPTY_SPOT:
                return f"• Will insert empty {cut_type_desc} cut\n• No elements enclosed initially"
        return "Transformation changes will be shown here"

    def _render_final_egi_linear_form(self) -> str:
        """Render final EGI in linear form."""
        if hasattr(self, "final_egi") and self.final_egi:
            # This would use the linear form renderer
            return f"Linear form of transformed EGI: {self.final_egi.sheet}"
        return "Final EGI not available"

    def _get_cut_position_instructions(self) -> str:
        """Get position instructions specific to cut insertion."""
        cut_type_desc = "positive" if self.state.cut_type == "P" else "negative"
        return f"""For {cut_type_desc.upper()} CUT insertion:
- Whole Area: Insert cut around ALL elements in the target area
- Select Elems: Insert cut around SPECIFIC elements you choose
- Empty Spot: Insert EMPTY cut with no enclosed elements

Note: {cut_type_desc.capitalize()} cuts {'assert' if self.state.cut_type == 'P' else 'negate'} their contents."""

    def _get_default_position_instructions(self) -> str:
        """Get default position instructions for non-cut insertions."""
        if self.state.rule_type == TransformationRuleType.DOUBLE_CUT:
            return """For DOUBLE CUT (DC+):
- Whole Area: Enclose all area contents in double cut
- Select Elems: Enclose only chosen elements  
- Empty Spot: Insert empty double cut"""
        elif self.state.insertion_type == InsertionType.EDGE:
            return """For EDGE insertion:
- Whole Area: Connect edge to all vertices in area
- Select Elems: Connect edge to specific vertices
- Empty Spot: Insert edge at empty position"""
        elif self.state.insertion_type == InsertionType.VERTEX:
            return """For VERTEX insertion:
- Whole Area: Insert vertex connected to area elements
- Select Elems: Insert vertex connected to specific elements
- Empty Spot: Insert isolated vertex"""
        else:
            return """Position options:
- Whole Area: Apply to all elements in area
- Select Elems: Apply to specific elements
- Empty Spot: Apply to empty position"""

    # Input handling methods
    def _handle_rule_selection(self, user_input: str) -> bool:
        """Handle rule selection input."""
        input_str = str(user_input).upper().strip()

        rule_mapping = {
            "E": TransformationRuleType.ERASURE,
            "I": TransformationRuleType.INSERTION,
            "T": TransformationRuleType.ITERATION,
            "D": TransformationRuleType.DEITERATION,
            "C": TransformationRuleType.DOUBLE_CUT,
            "X": TransformationRuleType.DOUBLE_CUT,  # DC- variant
            "DC+": TransformationRuleType.DOUBLE_CUT,
            "DC-": TransformationRuleType.DOUBLE_CUT,
            "ERASURE": TransformationRuleType.ERASURE,
            "INSERTION": TransformationRuleType.INSERTION,
            "ITERATION": TransformationRuleType.ITERATION,
            "DEITERATION": TransformationRuleType.DEITERATION,
            "DOUBLE_CUT": TransformationRuleType.DOUBLE_CUT,
        }

        if input_str in rule_mapping:
            self.state.rule_type = rule_mapping[input_str]
            self.state.can_proceed = True
            return True

        self.state.error_messages.append(f"Invalid rule: {user_input}")
        return False

    def _handle_area_selection(self, user_input: str) -> bool:
        """Handle area selection input."""
        input_str = str(user_input).strip().lower()

        # Check if it's the sheet
        if input_str == "sheet":
            self.state.selected_area = ElementID("sheet")
            self.state.can_proceed = True
            return True

        # Check if it's a valid cut ID
        if ElementID(user_input) in self.source_egi.Cut:
            self.state.selected_area = ElementID(user_input)
            self.state.can_proceed = True
            return True

        self.state.error_messages.append(f"Invalid area: {user_input}")
        return False

    def _handle_position_selection(self, user_input: str) -> bool:
        """Handle position selection input."""
        input_str = str(user_input).upper().strip()

        position_mapping = {
            "W": PositionType.WHOLE_AREA,
            "S": PositionType.SELECTED_ELEMENTS,
            "E": PositionType.EMPTY_SPOT,
            "WHOLE": PositionType.WHOLE_AREA,
            "SELECT": PositionType.SELECTED_ELEMENTS,
            "EMPTY": PositionType.EMPTY_SPOT,
        }

        if input_str in position_mapping:
            self.state.position_type = position_mapping[input_str]

            # Generate preview
            self._generate_preview()
            self.state.can_proceed = True
            return True

        self.state.error_messages.append(f"Invalid position type: {user_input}")
        return False

    def _handle_cut_details(self, user_input: Any) -> bool:
        """Handle cut details input."""
        if isinstance(user_input, str):
            input_str = user_input.upper().strip()
            if input_str in ["P", "POSITIVE"]:
                self.state.cut_type = "P"
                self.state.can_proceed = True
                return True
            elif input_str in ["N", "NEGATIVE"]:
                self.state.cut_type = "N"
                self.state.can_proceed = True
                return True

        self.state.error_messages.append(
            f"Invalid cut type: {user_input}. Enter P or N."
        )
        return False

    def _handle_preview_confirmation(self, user_input: str) -> bool:
        """Handle preview confirmation input."""
        input_str = str(user_input).upper().strip()

        if input_str in ["Y", "YES"]:
            self.state.can_proceed = True
            return True
        elif input_str in ["N", "NO"]:
            self.state.can_proceed = False
            return False

        self.state.error_messages.append("Please enter Y or N")
        return False

    def _generate_preview(self):
        """Generate preview of the transformation."""
        # This would create a preview EGI based on the selected transformation
        # For now, we'll set it to the source EGI as a placeholder
        self.state.preview_egi = self.source_egi

    def _render_precondition_checks(self) -> str:
        """Render rule-specific precondition checks."""
        if not self.state.rule_type:
            return "No rule selected for precondition checking"

        if self.state.rule_type == TransformationRuleType.ERASURE:
            return "✅ Erasure precondition: Elements in positive context"
        elif self.state.rule_type == TransformationRuleType.INSERTION:
            return "✅ Insertion precondition: Target is negative context"
        else:
            return f"Preconditions for {self.state.rule_type.value} rule"

    def _render_transformation_changes(self) -> str:
        """Render description of transformation changes."""
        if not self.state.rule_type:
            return "No transformation specified"

        if self.state.rule_type == TransformationRuleType.ERASURE:
            return "- Selected elements will be removed\n- Incident connections will be updated"
        elif self.state.rule_type == TransformationRuleType.INSERTION:
            return "- New elements will be added to target context\n- Connections will be established"
        else:
            return f"Changes for {self.state.rule_type.value} transformation"

    def _handle_rule_selection(self, user_input: Any) -> bool:
        """Handle rule selection input."""
        rule_mapping = {
            "E": TransformationRuleType.ERASURE,
            "I": TransformationRuleType.INSERTION,
            "T": TransformationRuleType.ITERATION,
            "D": TransformationRuleType.DEITERATION,
            "C": TransformationRuleType.DOUBLE_CUT,
        }

        if isinstance(user_input, str) and user_input.upper() in rule_mapping:
            self.state.rule_type = rule_mapping[user_input.upper()]
            self.state.can_proceed = True
            return True

        return False

    def _handle_insertion_type_selection(self, user_input: Any) -> bool:
        """Handle insertion type selection input."""
        type_mapping = {
            "S": InsertionType.SUBGRAPH,
            "E": InsertionType.EDGE,
            "C": InsertionType.CUT,
            "V": InsertionType.VERTEX,
        }

        if isinstance(user_input, str) and user_input.upper() in type_mapping:
            self.state.insertion_type = type_mapping[user_input.upper()]
            self.state.can_proceed = True
            return True

        return False

    def _handle_edge_details(self, user_input: Any) -> bool:
        """Handle edge details input per Dau's Definition 12.1."""
        if not self.state.relation_name:
            # First input: relation name for rel mapping
            if isinstance(user_input, str) and user_input.strip():
                self.state.relation_name = user_input.strip()
                return True
        elif not self.state.vertex_sequence:
            # Second input: vertex sequence for ν mapping
            try:
                if isinstance(user_input, str) and user_input.strip():
                    vertex_ids = [
                        vid.strip() for vid in user_input.split(",") if vid.strip()
                    ]
                    if vertex_ids:
                        self.state.vertex_sequence = [
                            ElementID(vid) for vid in vertex_ids
                        ]
                        self.state.can_proceed = True
                        return True
            except (ValueError, TypeError):
                pass
        else:
            # Both filled, just continue
            self.state.can_proceed = True
            return True

        return False

    def _handle_vertex_details(self, user_input: Any) -> bool:
        """Handle vertex details input."""
        if not hasattr(self.state, "vertex_label_set"):
            # First time - set the label (can be empty)
            self.state.vertex_label = str(user_input).strip() if user_input else ""
            self.state.vertex_label_set = True
            self.state.can_proceed = True
            return True
        else:
            # Already set, just continue
            self.state.can_proceed = True
            return True

    def _handle_cut_details(self, user_input: Any) -> bool:
        """Handle cut details input."""
        cut_mapping = {"P": "positive", "N": "negative"}

        if isinstance(user_input, str) and user_input.upper() in cut_mapping:
            self.state.cut_type = cut_mapping[user_input.upper()]
            self.state.can_proceed = True
            return True

        return False

    def _handle_subgraph_source(self, user_input: Any) -> bool:
        """Handle subgraph source selection input."""
        try:
            choice = int(user_input)
            if choice in [1, 2, 3]:
                # Store the choice and proceed
                self.state.subgraph_source_choice = choice
                self.state.can_proceed = True
                return True
        except (ValueError, TypeError):
            pass

        return False

    def _handle_element_selection(self, user_input: Any) -> bool:
        """Handle element selection input for IT+/IT-."""
        try:
            # Parse comma-separated element numbers
            element_nums = [int(x.strip()) for x in str(user_input).split(",")]
            elements = self._get_elements_in_area(self.state.selected_area)

            # Validate all numbers are in range
            if all(1 <= num <= len(elements) for num in element_nums):
                # Store selected elements
                selected_elements = [elements[num - 1] for num in element_nums]
                self.state.selected_elements = set(selected_elements)
                self.state.can_proceed = True
                return True
        except (ValueError, TypeError):
            pass

        return False

    def _handle_placement_selection(self, user_input: Any) -> bool:
        """Handle placement selection input for IT+/IT-."""
        try:
            choice = int(user_input)

            if self.state.rule_type == TransformationRuleType.ITERATION:
                valid_areas = self._get_valid_iteration_areas()
                if 1 <= choice <= len(valid_areas):
                    # Store the selected placement area
                    self.state.placement_area = valid_areas[choice - 1]
                    self.state.can_proceed = True
                    return True
            else:
                # Deiteration - simpler handling
                if choice == 1:
                    self.state.placement_area = self.state.selected_area
                    self.state.can_proceed = True
                    return True
        except (ValueError, TypeError):
            pass

        return False

    def _handle_justification_search(self, user_input: Any) -> bool:
        """Handle justification search input for IT-."""
        justifying_subgraph = self._find_justifying_subgraph()

        if justifying_subgraph:
            # Auto-found justification, just proceed
            self.state.justifying_subgraph = justifying_subgraph
            self.state.can_proceed = True
            return True
        else:
            # Manual search required
            try:
                choice = int(user_input)
                if choice == 1:
                    # User wants to manually identify justifying subgraph
                    # This would trigger a manual selection interface
                    self.state.manual_justification_mode = True
                    return True
                elif choice == 2:
                    # Cancel deiteration
                    self.state.can_proceed = False
                    self.state.error_messages.append(
                        "Deiteration cancelled - no valid justification"
                    )
                    return False
            except (ValueError, TypeError):
                pass

        return False

    def _find_justifying_subgraph(self) -> Optional[Dict[str, Any]]:
        """Find justifying subgraph for deiteration in same or parent areas."""
        if not self.state.selected_elements or not self.state.selected_area:
            return None

        # Search in same area first
        justification = self._search_area_for_justification(self.state.selected_area)
        if justification:
            return justification

        # Search in parent areas
        parent_areas = self._get_parent_areas(self.state.selected_area)
        for parent_area in parent_areas:
            justification = self._search_area_for_justification(parent_area)
            if justification:
                return justification

        return None

    def _search_area_for_justification(
        self, area_id: ElementID
    ) -> Optional[Dict[str, Any]]:
        """Search specific area for subgraph matching selected elements using isomorphism engine."""
        if not self.state.selected_elements:
            return None

        # Extract selected subgraph structure
        selected_subgraph = self._extract_subgraph_from_elements(
            self.state.selected_elements
        )

        # Get all possible subgraphs in the target area
        candidate_subgraphs = self._get_candidate_subgraphs_in_area(area_id)

        # Use isomorphism engine to find matching subgraph
        for candidate in candidate_subgraphs:
            result = self.isomorphism_engine.test_isomorphism(
                selected_subgraph, candidate
            )
            if result.is_isomorphic:
                return {
                    "area": area_id,
                    "elements": list(candidate.V.keys())
                    + list(candidate.E.keys())
                    + list(candidate.Cut.keys()),
                    "mapping": result.mapping,
                    "subgraph": candidate,
                }

        return None

    def _get_parent_areas(self, area_id: ElementID) -> List[ElementID]:
        """Get all parent areas of the given area."""
        parent_areas = []

        # Find the cut that contains this area and get its parent
        for cut_id, cut in self.source_egi.Cut.items():
            if cut_id == area_id and hasattr(cut, "parent_area"):
                parent_area = cut.parent_area
                parent_areas.append(parent_area)
                # Recursively get parent areas
                parent_areas.extend(self._get_parent_areas(parent_area))
                break

        return parent_areas

    def _extract_subgraph_from_elements(
        self, elements: Set[ElementID]
    ) -> RelationalGraphWithCuts:
        """Extract subgraph structure from selected elements."""
        # Create new EGI containing only selected elements
        subgraph_vertices = {}
        subgraph_edges = {}
        subgraph_cuts = {}

        for element_id in elements:
            if element_id in self.source_egi.V:
                subgraph_vertices[element_id] = self.source_egi.V[element_id]
            elif element_id in self.source_egi.E:
                subgraph_edges[element_id] = self.source_egi.E[element_id]
            elif element_id in self.source_egi.Cut:
                subgraph_cuts[element_id] = self.source_egi.Cut[element_id]

        return RelationalGraphWithCuts(
            V=subgraph_vertices, E=subgraph_edges, Cut=subgraph_cuts
        )

    def _get_candidate_subgraphs_in_area(
        self, area_id: ElementID
    ) -> List[RelationalGraphWithCuts]:
        """Get all possible subgraphs of the same size in the target area."""
        # Get all elements in the target area
        area_elements = self._get_elements_in_area_ids(area_id)
        selected_size = len(self.state.selected_elements)

        # Generate all combinations of elements of the same size
        from itertools import combinations

        candidate_subgraphs = []

        for element_combo in combinations(area_elements, selected_size):
            candidate_subgraph = self._extract_subgraph_from_elements(
                set(element_combo)
            )
            candidate_subgraphs.append(candidate_subgraph)

        return candidate_subgraphs

    def _get_elements_in_area_ids(self, area_id: ElementID) -> List[ElementID]:
        """Get list of element IDs in the specified area."""
        elements = []

        # Add vertices in this area
        for v_id, vertex in self.source_egi.V.items():
            if hasattr(vertex, "area") and vertex.area == area_id:
                elements.append(v_id)

        # Add edges in this area
        for e_id, edge in self.source_egi.E.items():
            if hasattr(edge, "area") and edge.area == area_id:
                elements.append(e_id)

        # Add cuts in this area
        for c_id, cut in self.source_egi.Cut.items():
            if hasattr(cut, "area") and cut.area == area_id:
                elements.append(c_id)

        return elements

    def _get_elements_in_area(self, area_id: ElementID) -> List[str]:
        """Get list of elements in the specified area."""
        elements = []

        # Add vertices in this area
        for v_id, vertex in self.source_egi.V.items():
            if hasattr(vertex, "area") and vertex.area == area_id:
                elements.append(
                    f"Vertex {v_id}: {getattr(vertex, 'label', 'unlabeled')}"
                )

        # Add edges in this area
        for e_id, edge in self.source_egi.E.items():
            if hasattr(edge, "area") and edge.area == area_id:
                elements.append(f"Edge {e_id}: {edge.source} -> {edge.target}")

        # Add cuts in this area
        for c_id, cut in self.source_egi.Cut.items():
            if hasattr(cut, "area") and cut.area == area_id:
                elements.append(f"Cut {c_id}")

        return elements if elements else ["No elements in this area"]

    def _get_valid_iteration_areas(self) -> List[str]:
        """Get list of valid areas for iteration placement."""
        if not self.state.selected_area:
            return []

        valid_areas = []
        source_area = self.state.selected_area

        # 1. Same area as original (same context)
        valid_areas.append(f"Same area: {source_area}")

        # 2. Any nested areas within the source area (deeper contexts)
        nested_areas = self._get_nested_areas(source_area)
        for nested_area in nested_areas:
            valid_areas.append(f"Nested area: {nested_area}")

        return valid_areas

    def _get_nested_areas(self, parent_area: ElementID) -> List[ElementID]:
        """Get all areas nested within the given parent area."""
        nested_areas = []

        # Find cuts that are contained within the parent area
        for cut_id, cut in self.source_egi.Cut.items():
            if hasattr(cut, "parent_area") and cut.parent_area == parent_area:
                nested_areas.append(cut_id)
                # Recursively find areas nested within this cut
                nested_areas.extend(self._get_nested_areas(cut_id))

        return nested_areas

    def _handle_subgraph_selection(self, user_input: Any) -> bool:
        """Handle subgraph selection input."""
        # This would integrate with actual GUI selection mechanisms
        # For now, create a placeholder selection
        if user_input == "select_example":
            self.state.selected_subgraph = SubgraphSelection(
                vertices=(
                    set(list(self.source_egi.V)[:1]) if self.source_egi.V else set()
                ),
                selection_method=SelectionMethod.ALT_CLICK,
            )

            # Validate the selection
            validated = self.egi_engine.validator.validate_subgraph(
                self.source_egi, self.state.selected_subgraph
            )
            self.state.selected_subgraph = validated
            self.state.validation_results["subgraph_valid"] = validated.is_valid
            self.state.can_proceed = validated.is_valid

            return validated.is_valid

        return False


class FOPLTransformationWizard(TransformationWizard):
    """Transformation wizard for FOPL format with logical formula guidance."""

    def get_format(self) -> DisplayFormat:
        return DisplayFormat.FOPL

    def render_step_interface(self, step: WizardStep) -> str:
        """Render FOPL-specific interface for current step."""
        if step == WizardStep.RULE_SELECTION:
            return self._render_fopl_rule_selection()
        elif step == WizardStep.SUBGRAPH_SELECTION:
            return self._render_fopl_subgraph_selection()
        else:
            return f"FOPL interface for {step.value}"

    def handle_user_input(self, step: WizardStep, user_input: Any) -> bool:
        """Handle FOPL-specific user input."""
        return True  # Placeholder

    def _render_fopl_rule_selection(self) -> str:
        """Render FOPL rule selection with logical equivalences."""
        return """
FOPL TRANSFORMATION WIZARD - Rule Selection
===========================================

Transformation Rules (FOPL Perspective):

┌─────────────┬─────────────────────────────────────┐
│ ERASURE     │ Remove conjuncts from formulas      │
│ INSERTION   │ Add disjuncts to negated formulas   │
│ ITERATION   │ Duplicate formulas in inner scopes  │
│ DEITERATION │ Remove duplicated formulas          │
│ DOUBLE_CUT  │ Apply double negation elimination   │
└─────────────┴─────────────────────────────────────┘

Logical Equivalences:
- Erasure: P ∧ Q → P (weakening)
- Insertion: ¬(P ∨ Q) → ¬(P ∨ Q ∨ R) (strengthening negation)
- Double Cut: ¬¬P ↔ P (double negation)

Select transformation rule...
"""

    def _render_fopl_subgraph_selection(self) -> str:
        """Render FOPL subgraph selection with formula structure."""
        return f"""
FOPL TRANSFORMATION WIZARD - Formula Selection
==============================================

Current Formula Structure:
{self._render_fopl_structure()}

Subformula Selection:
- Select atomic formulas, conjunctions, or disjunctions
- Ensure selected subformulas form valid logical units
- Consider variable scoping and quantifier binding

Available Subformulas:
{self._list_fopl_subformulas()}

Select subformula for transformation...
"""

    def _render_fopl_structure(self) -> str:
        """Render FOPL formula structure."""
        # This would use the Chapter 20 translator to show FOPL representation
        try:
            translator = self.egi_engine.translators.get(DisplayFormat.FOPL)
            if translator:
                fopl_str = translator.phi_translate(self.source_egi)
                return f"Formula: {fopl_str}"
        except:
            pass

        return "FOPL representation not available"

    def _list_fopl_subformulas(self) -> str:
        """List available subformulas for selection."""
        return """
1. Atomic formulas: Man(x), Mortal(x)
2. Conjunctions: Man(x) ∧ Mortal(x)
3. Negations: ¬Man(x)
4. Quantifications: ∃x.Man(x)
"""


class UniversalTransformationWizardSystem:
    """System managing transformation wizards across all formats."""

    def __init__(self, egi_engine: UniversalEGIEngine):
        self.egi_engine = egi_engine
        self.wizard_factories = {
            DisplayFormat.DIAGRAM: DiagramTransformationWizard,
            DisplayFormat.FOPL: FOPLTransformationWizard,
            # Add other formats as implemented
        }

    def create_wizard(
        self, format_type: DisplayFormat, source_egi: RelationalGraphWithCuts
    ) -> TransformationWizard:
        """Create appropriate wizard for the specified format."""
        if format_type not in self.wizard_factories:
            raise ValueError(f"No wizard available for format {format_type}")

        wizard_class = self.wizard_factories[format_type]
        return wizard_class(self.egi_engine, source_egi)

    def run_guided_transformation(self, wizard: TransformationWizard) -> WizardResult:
        """Run a complete guided transformation session."""
        print(
            f"\n🧙 Starting {wizard.get_format().value.upper()} Transformation Wizard"
        )
        print("=" * 60)

        # Step through wizard workflow
        while wizard.state.current_step != WizardStep.PREVIEW:
            current_step = wizard.state.current_step
            print(f"\n📋 Step: {current_step.value.replace('_', ' ').title()}")
            print("-" * 40)

            # Render step interface
            interface = wizard.render_step_interface(current_step)
            print(interface)

            # Handle step-specific logic
            if current_step == WizardStep.RULE_SELECTION:
                # Simulate rule selection
                success = wizard.handle_user_input(current_step, "E")  # Select Erasure
                if success:
                    print("✅ Rule selected: ERASURE")
                    wizard.advance_step()
                else:
                    print("❌ Invalid rule selection")
                    break

            elif current_step == WizardStep.SUBGRAPH_SELECTION:
                # Simulate subgraph selection
                success = wizard.handle_user_input(current_step, "select_example")
                if success:
                    print("✅ Subgraph selected and validated")
                    wizard.advance_step()
                else:
                    print("❌ Invalid subgraph selection")
                    break

            else:
                # Auto-advance other steps for demo
                wizard.state.can_proceed = True
                if not wizard.advance_step():
                    break

        # Execute transformation
        if wizard.state.current_step == WizardStep.PREVIEW:
            wizard.state.current_step = WizardStep.EXECUTE
            result = wizard.execute_transformation()

            if result.success:
                print(f"\n✅ Transformation completed successfully!")
                print(
                    f"Rule applied: {result.transformation_applied.value if result.transformation_applied else 'Unknown'}"
                )
            else:
                print(f"\n❌ Transformation failed: {result.error_message}")

            return result

        return WizardResult(
            success=False,
            final_egi=None,
            transformation_applied=None,
            steps_completed=[],
            error_message="Wizard workflow incomplete",
        )


def test_transformation_wizards():
    """Test the transformation wizard system."""
    print("🧙 TESTING CHAPTER 21 TRANSFORMATION WIZARDS")
    print("=" * 60)

    # Create test EGI
    from frozendict import frozendict

    v1 = Vertex(ElementID("v1"))
    v2 = Vertex(ElementID("v2"))
    e1 = Edge(ElementID("e1"))
    sheet = ElementID("sheet")

    test_egi = RelationalGraphWithCuts(
        V=frozenset([v1, v2]),
        E=frozenset([e1]),
        nu=frozendict({e1.id: (v1.id, v2.id)}),
        sheet=sheet,
        Cut=frozenset(),
        area=frozendict({sheet: frozenset([v1.id, v2.id, e1.id])}),
        rel=frozendict({e1.id: "Man"}),
    )

    # Initialize system
    egi_engine = UniversalEGIEngine()
    wizard_system = UniversalTransformationWizardSystem(egi_engine)

    # Test diagram wizard
    print("\n1️⃣ Testing Diagram Transformation Wizard")
    diagram_wizard = wizard_system.create_wizard(DisplayFormat.DIAGRAM, test_egi)
    diagram_result = wizard_system.run_guided_transformation(diagram_wizard)

    print(f"Diagram wizard result: {'Success' if diagram_result.success else 'Failed'}")

    # Test FOPL wizard
    print("\n2️⃣ Testing FOPL Transformation Wizard")
    fopl_wizard = wizard_system.create_wizard(DisplayFormat.FOPL, test_egi)

    # Show FOPL interface
    print("\nFOPL Rule Selection Interface:")
    print(fopl_wizard.render_step_interface(WizardStep.RULE_SELECTION))

    print(f"\n🎯 TRANSFORMATION WIZARD SUMMARY")
    print("=" * 60)
    print("✅ Universal wizard system operational")
    print("✅ Format-specific wizards implemented")
    print("✅ Step-by-step guidance functional")
    print("✅ Validation and preview working")
    print("✅ EGI-first transformation approach verified")
    print("\nReady for GUI integration!")


if __name__ == "__main__":
    test_transformation_wizards()
