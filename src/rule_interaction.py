"""
Rule Interaction Protocol — headless, platform-independent bridge between
user actions and formal transformation rule application.

Each of Dau's six rules has a distinct interaction pattern:

    DC+  Single-step: select elements to enclose (may be empty).
    DC-  Single-step: select the outer cut of a double-cut pair.
    ERA  Single-step: select a closed subgraph in a positive area.
    INS  Two-step:    (a) provide content to insert (EGIF or subgraph),
                      (b) select a negative target area.
    IT+  Two-step:    (a) select source subgraph,
                      (b) select destination area (more deeply nested).
    IT-  Single-step: select candidate copy (engine verifies isomorphism
                      with original in enclosing area).

This module provides a ``RuleInteraction`` for each rule that:
- Declares the required interaction steps
- Validates user input at each step
- Builds a valid ``TransformationContext`` when all steps are complete
- Applies the rule and returns the result

No GUI dependency — this is pure logic.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from egi_core_dau import AreaPolarity, ElementID, RelationalGraphWithCuts
from formal_transformation_rules import (
    TransformationContext,
    TransformationResult,
    DoubleCutInsertionRule,
    DoubleCutErasureRule,
    InsertionRule,
    ErasureRule,
    IterationRule,
    DeiterationRule,
)
from subgraph_closure_validator import SubgraphClosureValidator


# ---------------------------------------------------------------------------
# Interaction step descriptors
# ---------------------------------------------------------------------------

class StepKind(Enum):
    """Kind of user input a step requires."""
    SELECT_SUBGRAPH = "select_subgraph"
    SELECT_AREA = "select_area"
    PROVIDE_EGIF = "provide_egif"


@dataclass(frozen=True)
class InteractionStep:
    """One step in a rule's interaction workflow."""
    step_id: str
    kind: StepKind
    prompt: str                       # Human-readable instruction
    optional: bool = False            # True if step can be skipped


@dataclass
class StepResult:
    """Validated result of one interaction step."""
    step_id: str
    valid: bool
    data: Any = None                  # The validated selection / EGIF / area
    message: str = ""                 # Human-readable feedback
    expanded_selection: Optional[FrozenSet[ElementID]] = None  # If closure expanded


@dataclass
class InteractionState:
    """Tracks progress through a multi-step interaction."""
    rule_name: str
    egi: RelationalGraphWithCuts
    completed_steps: Dict[str, StepResult] = field(default_factory=dict)
    is_complete: bool = False
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Validation result for the complete interaction
# ---------------------------------------------------------------------------

@dataclass
class ApplyResult:
    """Result of applying a rule through the interaction protocol."""
    success: bool
    result_egi: Optional[RelationalGraphWithCuts] = None
    rule_name: str = ""
    message: str = ""
    changes_made: Dict[str, Any] = field(default_factory=dict)
    transformation_result: Optional[TransformationResult] = None
    context: Optional[TransformationContext] = None


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class RuleInteraction:
    """Base class for rule-specific interaction workflows.

    Subclasses override ``steps``, ``validate_step``, and ``build_context``.
    The ``apply`` method is final — it validates all steps, builds the context,
    checks preconditions, and applies the rule.
    """

    rule_name: str = ""

    def steps(self) -> List[InteractionStep]:
        """Declare the interaction steps this rule requires."""
        raise NotImplementedError

    def validate_step(
        self,
        step: InteractionStep,
        user_input: Any,
        state: InteractionState,
    ) -> StepResult:
        """Validate user input for one step. Returns StepResult."""
        raise NotImplementedError

    def build_context(self, state: InteractionState) -> TransformationContext:
        """Build a TransformationContext from completed steps."""
        raise NotImplementedError

    def apply(self, state: InteractionState) -> ApplyResult:
        """Validate all steps, build context, apply rule.

        This is the final entry point — it does NOT re-validate steps that
        are already in ``state.completed_steps``.  Call ``validate_step``
        for each step first.
        """
        # Ensure all required steps are completed
        required = [s for s in self.steps() if not s.optional]
        for step in required:
            if step.step_id not in state.completed_steps:
                return ApplyResult(
                    success=False,
                    rule_name=self.rule_name,
                    message=f"Missing required step: {step.prompt}",
                )
            sr = state.completed_steps[step.step_id]
            if not sr.valid:
                return ApplyResult(
                    success=False,
                    rule_name=self.rule_name,
                    message=f"Step '{step.step_id}' invalid: {sr.message}",
                )

        # Build context
        try:
            context = self.build_context(state)
        except Exception as exc:
            return ApplyResult(
                success=False,
                rule_name=self.rule_name,
                message=f"Failed to build context: {exc}",
            )

        # Apply rule
        result = self._get_rule().apply_transformation(context)

        if not result.success:
            return ApplyResult(
                success=False,
                rule_name=self.rule_name,
                message=f"Rule rejected: {result.error_message}",
                context=context,
                transformation_result=result,
            )

        return ApplyResult(
            success=True,
            result_egi=result.result_egi,
            rule_name=self.rule_name,
            message=f"Applied {self.rule_name}",
            changes_made=result.changes_made,
            context=context,
            transformation_result=result,
        )

    def _get_rule(self):
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_element_area(egi: RelationalGraphWithCuts, element_id: ElementID) -> Optional[ElementID]:
    """Find which area directly contains an element."""
    for area_id, contents in egi.area.items():
        if element_id in contents:
            return area_id
    return None


def _all_in_same_area(
    egi: RelationalGraphWithCuts,
    element_ids: FrozenSet[ElementID],
) -> Optional[ElementID]:
    """Return the common area if all elements are in the same area, else None."""
    if not element_ids:
        return None
    areas = {_find_element_area(egi, eid) for eid in element_ids}
    if len(areas) == 1:
        return areas.pop()
    return None


# ---------------------------------------------------------------------------
# DC+ Interaction
# ---------------------------------------------------------------------------

class DCPlusInteraction(RuleInteraction):
    """DC+ (Double Cut Insertion): select elements to enclose."""

    rule_name = "DC+"

    def steps(self) -> List[InteractionStep]:
        return [
            InteractionStep(
                step_id="select",
                kind=StepKind.SELECT_SUBGRAPH,
                prompt="Select elements to enclose in a double cut (or select nothing for empty double cut).",
                optional=True,
            ),
        ]

    def validate_step(self, step, user_input, state):
        egi = state.egi
        selection: FrozenSet[ElementID] = frozenset(user_input) if user_input else frozenset()

        if not selection:
            # Empty selection → insert empty double cut on sheet
            return StepResult(
                step_id=step.step_id,
                valid=True,
                data={"selection": frozenset(), "area": egi.sheet},
                message="Will insert empty double cut on sheet.",
            )

        # All selected elements must be in the same area
        area = _all_in_same_area(egi, selection)
        if area is None:
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message="All selected elements must be in the same area.",
            )

        return StepResult(
            step_id=step.step_id,
            valid=True,
            data={"selection": selection, "area": area},
            message=f"Will enclose {len(selection)} element(s) in area {area}.",
        )

    def build_context(self, state):
        step_data = state.completed_steps.get("select")
        if step_data and step_data.valid:
            selection = step_data.data["selection"]
            area = step_data.data["area"]
        else:
            # No selection step → empty double cut on sheet
            selection = frozenset()
            area = state.egi.sheet

        polarity, depth = state.egi.area_polarity(area)
        return TransformationContext(
            source_egi=state.egi,
            target_area=area,
            selected_subgraph=selection,
            area_polarity=polarity,
            nesting_depth=depth,
        )

    def _get_rule(self):
        return DoubleCutInsertionRule()


# ---------------------------------------------------------------------------
# DC- Interaction
# ---------------------------------------------------------------------------

class DCMinusInteraction(RuleInteraction):
    """DC- (Double Cut Erasure): select the outer cut of a double-cut pair."""

    rule_name = "DC-"

    def steps(self) -> List[InteractionStep]:
        return [
            InteractionStep(
                step_id="select_outer_cut",
                kind=StepKind.SELECT_SUBGRAPH,
                prompt="Select the outer cut of a double-cut pair to erase.",
            ),
        ]

    def validate_step(self, step, user_input, state):
        egi = state.egi
        selection: FrozenSet[ElementID] = frozenset(user_input) if user_input else frozenset()

        if len(selection) != 1:
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message="Select exactly one cut (the outer cut of a double-cut pair).",
            )

        outer_cut_id = next(iter(selection))

        # Must be a cut
        if not any(c.id == outer_cut_id for c in egi.Cut):
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message=f"'{outer_cut_id}' is not a cut.",
            )

        # Must contain exactly one element, which must be a cut (inner)
        outer_contents = egi.area.get(outer_cut_id, frozenset())
        if len(outer_contents) != 1:
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message=f"Outer cut must contain exactly one element (the inner cut). "
                        f"Found {len(outer_contents)} elements.",
            )

        inner_candidate = next(iter(outer_contents))
        if not any(c.id == inner_candidate for c in egi.Cut):
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message=f"The single element inside the outer cut must be a cut. "
                        f"Found '{inner_candidate}' which is not a cut.",
            )

        # Valid double-cut pair identified
        area = _find_element_area(egi, outer_cut_id)
        return StepResult(
            step_id=step.step_id,
            valid=True,
            data={"outer_cut": outer_cut_id, "inner_cut": inner_candidate, "area": area},
            message=f"Double-cut pair found: outer={outer_cut_id}, inner={inner_candidate}.",
        )

    def build_context(self, state):
        data = state.completed_steps["select_outer_cut"].data
        area = data["area"]
        polarity, depth = state.egi.area_polarity(area)
        return TransformationContext(
            source_egi=state.egi,
            target_area=area,
            selected_subgraph=frozenset([data["outer_cut"]]),
            area_polarity=polarity,
            nesting_depth=depth,
        )

    def _get_rule(self):
        return DoubleCutErasureRule()


# ---------------------------------------------------------------------------
# ERA Interaction
# ---------------------------------------------------------------------------

class ERAInteraction(RuleInteraction):
    """ERA (Erasure): select a closed subgraph in a positive area."""

    rule_name = "ERA"

    def steps(self) -> List[InteractionStep]:
        return [
            InteractionStep(
                step_id="select",
                kind=StepKind.SELECT_SUBGRAPH,
                prompt="Select elements to erase (must form a closed subgraph in a positive area).",
            ),
        ]

    def validate_step(self, step, user_input, state):
        egi = state.egi
        selection: FrozenSet[ElementID] = frozenset(user_input) if user_input else frozenset()

        if not selection:
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message="Select at least one element to erase.",
            )

        # All elements must be in the same area
        area = _all_in_same_area(egi, selection)
        if area is None:
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message="All selected elements must be in the same area.",
            )

        # Area must be positive (recto)
        polarity, depth = egi.area_polarity(area)
        if polarity is not AreaPolarity.POSITIVE:
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message=f"Erasure only allowed in positive (recto) areas. "
                        f"Area {area} is {polarity.value} (depth {depth}).",
            )

        # Subgraph must be closed (with auto-expansion)
        validator = SubgraphClosureValidator(egi)
        analysis = validator.analyze_closure(selection, allow_expansion=True)

        if not analysis.is_closed:
            violations = "; ".join(v.description for v in analysis.violations[:3])
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message=f"Selection is not a closed subgraph: {violations}",
            )

        expanded = analysis.closed_subgraph
        return StepResult(
            step_id=step.step_id,
            valid=True,
            data={"selection": expanded, "area": area},
            message=analysis.get_summary(),
            expanded_selection=expanded if expanded != selection else None,
        )

    def build_context(self, state):
        data = state.completed_steps["select"].data
        area = data["area"]
        polarity, depth = state.egi.area_polarity(area)
        return TransformationContext(
            source_egi=state.egi,
            target_area=area,
            selected_subgraph=data["selection"],
            area_polarity=polarity,
            nesting_depth=depth,
        )

    def _get_rule(self):
        return ErasureRule()


# ---------------------------------------------------------------------------
# INS Interaction
# ---------------------------------------------------------------------------

class INSInteraction(RuleInteraction):
    """INS (Insertion): provide content + select a negative target area.

    Content is provided as EGIF text.  The engine parses it, assigns fresh
    IDs to avoid collisions, and merges the parsed graph's sheet-level
    elements into the target area.
    """

    rule_name = "INS"

    def steps(self) -> List[InteractionStep]:
        return [
            InteractionStep(
                step_id="provide_content",
                kind=StepKind.PROVIDE_EGIF,
                prompt="Provide the content to insert (as EGIF text).",
            ),
            InteractionStep(
                step_id="select_target",
                kind=StepKind.SELECT_AREA,
                prompt="Select the negative (verso) area to insert into.",
            ),
        ]

    def validate_step(self, step, user_input, state):
        if step.step_id == "provide_content":
            return self._validate_content(user_input, state)
        elif step.step_id == "select_target":
            return self._validate_target(user_input, state)
        return StepResult(step_id=step.step_id, valid=False, message="Unknown step.")

    def _validate_content(self, egif_text, state):
        if not egif_text or not str(egif_text).strip():
            return StepResult(
                step_id="provide_content",
                valid=False,
                message="EGIF text is required.",
            )
        # Try parsing
        try:
            from egif_parser_dau import parse_egif
            parsed = parse_egif(str(egif_text))
            sheet_contents = parsed.area.get(parsed.sheet, frozenset())
            elem_count = len(parsed.V) + len(parsed.E) + len(parsed.Cut)
            return StepResult(
                step_id="provide_content",
                valid=True,
                data={"egif": str(egif_text), "parsed_egi": parsed},
                message=f"Parsed EGIF: {elem_count} elements, {len(sheet_contents)} top-level.",
            )
        except Exception as exc:
            return StepResult(
                step_id="provide_content",
                valid=False,
                message=f"EGIF parse error: {exc}",
            )

    def _validate_target(self, area_id, state):
        egi = state.egi
        area_id = str(area_id)

        if area_id not in egi.area:
            return StepResult(
                step_id="select_target",
                valid=False,
                message=f"Area '{area_id}' does not exist in the current graph.",
            )

        polarity, depth = egi.area_polarity(area_id)
        if polarity is not AreaPolarity.NEGATIVE:
            return StepResult(
                step_id="select_target",
                valid=False,
                message=f"Insertion only allowed in negative (verso) areas. "
                        f"Area {area_id} is {polarity.value} (depth {depth}).",
            )

        return StepResult(
            step_id="select_target",
            valid=True,
            data={"area": area_id},
            message=f"Target area {area_id} is negative (depth {depth}). Ready to insert.",
        )

    def build_context(self, state):
        content_data = state.completed_steps["provide_content"].data
        target_data = state.completed_steps["select_target"].data

        area = target_data["area"]
        polarity, depth = state.egi.area_polarity(area)

        # Store the parsed EGI on the context for the unified INS implementation
        context = TransformationContext(
            source_egi=state.egi,
            target_area=area,
            selected_subgraph=frozenset(),  # INS inserts new content, not existing elements
            area_polarity=polarity,
            nesting_depth=depth,
        )
        # Attach parsed insertion EGI as extra data for the rule
        context.insertion_egi = content_data["parsed_egi"]
        context.insertion_egif = content_data["egif"]
        return context

    def _get_rule(self):
        return InsertionRule()

    def apply(self, state):
        """Override apply to use the unified INS implementation."""
        # Validate all steps
        required = [s for s in self.steps() if not s.optional]
        for step in required:
            if step.step_id not in state.completed_steps:
                return ApplyResult(
                    success=False,
                    rule_name=self.rule_name,
                    message=f"Missing required step: {step.prompt}",
                )
            sr = state.completed_steps[step.step_id]
            if not sr.valid:
                return ApplyResult(
                    success=False,
                    rule_name=self.rule_name,
                    message=f"Step '{step.step_id}' invalid: {sr.message}",
                )

        # Build context
        context = self.build_context(state)

        # Use the unified EGIF-based insertion (same logic as game engine)
        result = insert_from_egif(
            state.egi,
            context.target_area,
            context.insertion_egif,
        )

        if not result.success:
            return ApplyResult(
                success=False,
                rule_name=self.rule_name,
                message=f"Insertion failed: {result.error_message}",
                context=context,
                transformation_result=result,
            )

        return ApplyResult(
            success=True,
            result_egi=result.result_egi,
            rule_name=self.rule_name,
            message=f"Inserted content into area {context.target_area}.",
            changes_made=result.changes_made,
            context=context,
            transformation_result=result,
        )


# ---------------------------------------------------------------------------
# IT+ Interaction
# ---------------------------------------------------------------------------

class ITPlusInteraction(RuleInteraction):
    """IT+ (Iteration): copy subgraph to a more deeply nested area."""

    rule_name = "IT+"

    def steps(self) -> List[InteractionStep]:
        return [
            InteractionStep(
                step_id="select_source",
                kind=StepKind.SELECT_SUBGRAPH,
                prompt="Select the subgraph to copy (iteration source).",
            ),
            InteractionStep(
                step_id="select_dest",
                kind=StepKind.SELECT_AREA,
                prompt="Select the destination area (must be nested inside the source area).",
            ),
        ]

    def validate_step(self, step, user_input, state):
        if step.step_id == "select_source":
            return self._validate_source(user_input, state)
        elif step.step_id == "select_dest":
            return self._validate_dest(user_input, state)
        return StepResult(step_id=step.step_id, valid=False, message="Unknown step.")

    def _validate_source(self, user_input, state):
        egi = state.egi
        selection: FrozenSet[ElementID] = frozenset(user_input) if user_input else frozenset()

        if not selection:
            return StepResult(
                step_id="select_source",
                valid=False,
                message="Select at least one element as the iteration source.",
            )

        # All elements must be in the same area
        area = _all_in_same_area(egi, selection)
        if area is None:
            return StepResult(
                step_id="select_source",
                valid=False,
                message="All source elements must be in the same area.",
            )

        # Must be closed
        validator = SubgraphClosureValidator(egi)
        analysis = validator.analyze_closure(selection, allow_expansion=True)
        if not analysis.is_closed:
            violations = "; ".join(v.description for v in analysis.violations[:3])
            return StepResult(
                step_id="select_source",
                valid=False,
                message=f"Source must be a closed subgraph: {violations}",
            )

        expanded = analysis.closed_subgraph
        return StepResult(
            step_id="select_source",
            valid=True,
            data={"selection": expanded, "source_area": area},
            message=f"Source: {len(expanded)} elements in area {area}. "
                    f"Now select destination area.",
            expanded_selection=expanded if expanded != selection else None,
        )

    def _validate_dest(self, area_id, state):
        egi = state.egi
        area_id = str(area_id)

        if area_id not in egi.area:
            return StepResult(
                step_id="select_dest",
                valid=False,
                message=f"Area '{area_id}' does not exist.",
            )

        # Source must be completed first
        source_step = state.completed_steps.get("select_source")
        if not source_step or not source_step.valid:
            return StepResult(
                step_id="select_dest",
                valid=False,
                message="Complete the source selection first.",
            )

        source_area = source_step.data["source_area"]

        # Destination must be nested inside (or equal to) the source area
        # Per Dau: IT+ copies from area A into any area B where A encloses B
        if source_area != area_id:
            hi = egi.hierarchical_index
            if hi and not hi.is_ancestor(source_area, area_id):
                return StepResult(
                    step_id="select_dest",
                    valid=False,
                    message=f"Destination area must be nested inside source area {source_area}. "
                            f"Area {area_id} is not enclosed by {source_area}.",
                )

        return StepResult(
            step_id="select_dest",
            valid=True,
            data={"dest_area": area_id},
            message=f"Destination area {area_id} accepted. Ready to apply IT+.",
        )

    def build_context(self, state):
        source_data = state.completed_steps["select_source"].data
        dest_data = state.completed_steps["select_dest"].data

        # IT+ uses the destination area as target_area
        dest_area = dest_data["dest_area"]
        polarity, depth = state.egi.area_polarity(dest_area)

        context = TransformationContext(
            source_egi=state.egi,
            target_area=dest_area,
            selected_subgraph=source_data["selection"],
            area_polarity=polarity,
            nesting_depth=depth,
        )
        # Attach source area for the rule
        context.source_area = source_data["source_area"]
        return context

    def _get_rule(self):
        return IterationRule()


# ---------------------------------------------------------------------------
# IT- Interaction
# ---------------------------------------------------------------------------

class ITMinusInteraction(RuleInteraction):
    """IT- (Deiteration): select candidate copy; engine verifies isomorphism."""

    rule_name = "IT-"

    def steps(self) -> List[InteractionStep]:
        return [
            InteractionStep(
                step_id="select_candidate",
                kind=StepKind.SELECT_SUBGRAPH,
                prompt="Select the subgraph to deiterate (must be an iterated copy).",
            ),
        ]

    def validate_step(self, step, user_input, state):
        egi = state.egi
        selection: FrozenSet[ElementID] = frozenset(user_input) if user_input else frozenset()

        if not selection:
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message="Select at least one element as the deiteration candidate.",
            )

        # All elements must be in the same area
        area = _all_in_same_area(egi, selection)
        if area is None:
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message="All candidate elements must be in the same area.",
            )

        # Must be closed
        validator = SubgraphClosureValidator(egi)
        analysis = validator.analyze_closure(selection, allow_expansion=True)
        if not analysis.is_closed:
            violations = "; ".join(v.description for v in analysis.violations[:3])
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message=f"Candidate must be a closed subgraph: {violations}",
            )

        expanded = analysis.closed_subgraph

        # Verify isomorphism: an isomorphic copy must exist in an enclosing area
        from graph_isomorphism_engine import GraphIsomorphismEngine
        iso_engine = GraphIsomorphismEngine()

        # Collect enclosing areas (ancestors of the candidate's area)
        enclosing_areas = []
        if egi.hierarchical_index:
            ancestors = egi.hierarchical_index.get_ancestors(area)
            # Exclude the candidate's own area — the original must be in a
            # strictly enclosing area
            enclosing_areas = [a for a in ancestors if a != area]
        else:
            # Fallback: walk up
            current = area
            while current != egi.sheet:
                parent = _find_element_area(egi, current)
                if parent is None:
                    break
                enclosing_areas.append(parent)
                current = parent

        if not enclosing_areas:
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message=f"No enclosing areas found — the candidate is on the sheet "
                        f"and cannot be a deiterable copy.",
            )

        # Search for isomorphic original in enclosing areas
        matches = iso_engine.find_isomorphic_subgraphs(
            egi, expanded, enclosing_areas
        )

        if not matches:
            return StepResult(
                step_id=step.step_id,
                valid=False,
                message=f"No isomorphic original found in enclosing areas "
                        f"{enclosing_areas}. The candidate is not an iterated copy.",
            )

        return StepResult(
            step_id=step.step_id,
            valid=True,
            data={
                "selection": expanded,
                "area": area,
                "original_matches": matches,
            },
            message=f"Isomorphic original found in {len(matches)} enclosing area(s). "
                    f"Ready to deiterate.",
            expanded_selection=expanded if expanded != selection else None,
        )

    def build_context(self, state):
        data = state.completed_steps["select_candidate"].data
        area = data["area"]
        polarity, depth = state.egi.area_polarity(area)
        return TransformationContext(
            source_egi=state.egi,
            target_area=area,
            selected_subgraph=data["selection"],
            area_polarity=polarity,
            nesting_depth=depth,
        )

    def _get_rule(self):
        return DeiterationRule()


# ---------------------------------------------------------------------------
# Unified INS helper (shared by interaction protocol and game engine)
# ---------------------------------------------------------------------------

def insert_from_egif(
    host_egi: RelationalGraphWithCuts,
    target_area: ElementID,
    egif_text: str,
) -> TransformationResult:
    """Parse EGIF and merge its sheet-level elements into target_area.

    This is the canonical insertion implementation, used by both the
    interaction protocol (INSInteraction) and the Endoporeutic Game engine.

    Fresh UUIDs are assigned to all inserted elements to avoid ID collisions.
    Nested cuts and their contents are copied recursively.

    Args:
        host_egi: The graph to insert into.
        target_area: The area (must be negative) to receive the new elements.
        egif_text: EGIF string describing the content to insert.

    Returns:
        TransformationResult with the updated EGI on success.
    """
    # Validate polarity
    polarity, depth = host_egi.area_polarity(target_area)
    if polarity is not AreaPolarity.NEGATIVE:
        return TransformationResult(
            False, None,
            "INS only allowed in negative (verso) areas.", {}
        )

    try:
        import uuid
        from egif_parser_dau import parse_egif
        from egi_core_dau import Vertex, Edge, Cut as EGICut
        from frozendict import frozendict as fd

        insert_egi = parse_egif(egif_text)
        src_sheet_contents = insert_egi.area.get(insert_egi.sheet, frozenset())

        # Fresh ID generators
        id_map: Dict[ElementID, ElementID] = {}

        def fresh(prefix: str) -> ElementID:
            return ElementID(f"{prefix}_{uuid.uuid4().hex[:8]}")

        # Mutable copies of host components
        new_V = set(host_egi.V)
        new_E = set(host_egi.E)
        new_Cut = set(host_egi.Cut)
        new_nu: Dict = dict(host_egi.nu)
        new_rel: Dict = dict(host_egi.rel)
        new_area: Dict = dict(host_egi.area)
        new_rho: Dict = dict(getattr(host_egi, 'rho', {}))

        def copy_element(elem_id: ElementID) -> ElementID:
            """Recursively copy an element, assigning fresh IDs."""
            if elem_id in id_map:
                return id_map[elem_id]

            # Vertex?
            v_match = next((v for v in insert_egi.V if v.id == elem_id), None)
            if v_match is not None:
                nid = fresh("v")
                id_map[elem_id] = nid
                new_V.add(Vertex(id=nid, label=v_match.label, is_generic=v_match.is_generic))
                # Copy rho if present
                src_rho = getattr(insert_egi, 'rho', {})
                if elem_id in src_rho and src_rho[elem_id] is not None:
                    new_rho[nid] = src_rho[elem_id]
                return nid

            # Edge?
            e_match = next((e for e in insert_egi.E if e.id == elem_id), None)
            if e_match is not None:
                nid = fresh("e")
                id_map[elem_id] = nid
                new_E.add(Edge(nid))
                if elem_id in insert_egi.rel:
                    new_rel[nid] = insert_egi.rel[elem_id]
                return nid

            # Cut?
            c_match = next((c for c in insert_egi.Cut if c.id == elem_id), None)
            if c_match is not None:
                nid = fresh("c")
                id_map[elem_id] = nid
                new_Cut.add(EGICut(nid))
                # Recursively copy cut contents
                inner = insert_egi.area.get(elem_id, frozenset())
                new_inner = set()
                for inner_id in inner:
                    new_inner.add(copy_element(inner_id))
                new_area[nid] = frozenset(new_inner)
                return nid

            return elem_id  # Unknown — pass through

        # Copy all top-level elements from the insert graph
        top_new = set()
        for elem_id in src_sheet_contents:
            top_new.add(copy_element(elem_id))

        # Fix nu mappings for copied edges
        for orig_e, new_e in id_map.items():
            if any(new_e == e.id for e in new_E) and orig_e in insert_egi.nu:
                new_nu[new_e] = tuple(
                    id_map.get(vid, vid) for vid in insert_egi.nu[orig_e]
                )

        # Merge into target area
        existing = new_area.get(target_area, frozenset())
        new_area[target_area] = existing | frozenset(top_new)

        result_egi = RelationalGraphWithCuts(
            V=frozenset(new_V),
            E=frozenset(new_E),
            nu=fd(new_nu),
            sheet=host_egi.sheet,
            Cut=frozenset(new_Cut),
            area=fd(new_area),
            rel=fd(new_rel),
            rho=fd(new_rho) if new_rho else fd(),
        )

        return TransformationResult(
            success=True,
            result_egi=result_egi,
            error_message=None,
            changes_made={"rule": "INS", "inserted": list(top_new)},
        )
    except Exception as exc:
        return TransformationResult(False, None, str(exc), {})


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

RULE_INTERACTIONS: Dict[str, RuleInteraction] = {
    "DC+": DCPlusInteraction(),
    "DC-": DCMinusInteraction(),
    "ERA": ERAInteraction(),
    "INS": INSInteraction(),
    "IT+": ITPlusInteraction(),
    "IT-": ITMinusInteraction(),
}


def get_interaction(rule_name: str) -> RuleInteraction:
    """Get the interaction workflow for a rule by name."""
    if rule_name not in RULE_INTERACTIONS:
        raise ValueError(f"Unknown rule: {rule_name}. Valid: {list(RULE_INTERACTIONS.keys())}")
    return RULE_INTERACTIONS[rule_name]


def begin_interaction(rule_name: str, egi: RelationalGraphWithCuts) -> InteractionState:
    """Start a new interaction session for a rule."""
    if rule_name not in RULE_INTERACTIONS:
        raise ValueError(f"Unknown rule: {rule_name}")
    return InteractionState(rule_name=rule_name, egi=egi)


def advance_interaction(
    state: InteractionState,
    user_input: Any,
) -> StepResult:
    """Advance an interaction by providing input for the next incomplete step.

    Finds the first step not yet in ``state.completed_steps`` and validates
    ``user_input`` against it.
    """
    interaction = RULE_INTERACTIONS[state.rule_name]
    steps = interaction.steps()

    # Find next incomplete step
    for step in steps:
        if step.step_id not in state.completed_steps:
            result = interaction.validate_step(step, user_input, state)
            state.completed_steps[step.step_id] = result

            # Check if all required steps are now complete
            required = [s for s in steps if not s.optional]
            all_done = all(
                s.step_id in state.completed_steps and state.completed_steps[s.step_id].valid
                for s in required
            )
            state.is_complete = all_done
            return result

    # All steps already completed
    return StepResult(
        step_id="",
        valid=True,
        message="All steps already completed. Call apply().",
    )


def apply_interaction(state: InteractionState) -> ApplyResult:
    """Apply the rule after all interaction steps are complete."""
    interaction = RULE_INTERACTIONS[state.rule_name]
    return interaction.apply(state)
