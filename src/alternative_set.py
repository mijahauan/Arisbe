"""
Alternative Set: Formal Structure for Holding and Testing Alternatives

An AlternativeSet is a generalization of the erotetic Doubt structure to
cover any deliberative context where alternatives are held, tested, and
committed to. This unifies:

- Interrogative contexts (Q: "which answer?")
- Hypothetical reasoning (Q: "which theory?")
- Modal exploration (Q: "which future?")
- Counterfactual thinking (Q: "if X, then?")
- Agentive deliberation (Q: "which action?")
- Epistemic inquiry (Q: "which world?")
- Metacognitive reflection (Q: "what could I do?")

Core insight: Deliberation = holding alternatives in mind, testing them,
committing to one, tracing the path. This structure captures that process
regardless of context.

Philosophical Foundation:
- Formalizes Peirce's dialogical doubt (not psychological doubt)
- Grounds inquiry in erotetic logic (Hamblin, Cross-Pollard)
- Embeds alternatives in the diachronic UoD as metadata (never EGI content)
- Applies to any decision point in reasoning, action, or perception

See: docs/superpowers/plans/2026-07-25-item-4-phase-2-doubt-implementation.md
"""

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Literal, Optional, Set

from egi_core_dau import RelationalGraphWithCuts


@dataclass(frozen=True)
class AlternativeSet:
    """Formal structure for holding and testing alternatives.

    An AlternativeSet captures the structure of deliberation (in any context)
    as it evolves through a UoD: the presupposition that must hold, the set
    of possible selections being considered, and the lifecycle tracking how
    the alternatives were narrowed (or re-emerged in a new form).

    Core semantics (encoded via current_selection cardinality):
    - len(current_selection) == 0: unresolved (no selection yet)
    - 0 < len(current_selection) < len(alternatives): partial (narrowed)
    - len(current_selection) == 1: resolved (committed)

    Attributes:
        id: Unique identifier within a UoD (e.g., "a0", "a1", ...)
        context: EGI state that must hold for the alternative-set to be well-posed
        alternatives: Set of EGI hashes representing possible selections
        current_selection: Subset of alternatives that have been narrowed/explored
        kind: Semantic category discriminating use case (interrogative/hypothetical/etc.)
        emerged_at_state: State ID where alternatives first appeared
        resolved_at_state: State ID where alternatives were resolved (if ever)
        selection_path: Ordered list of state IDs through narrowing occurred
        warrant: Confidence in the alternative-set itself (0.0–1.0)
        source: Where the alternative-set originated (e.g., "unknown_verdict", "oracle")
    """

    # Identity
    id: str

    # Core deliberative structure (presupposition + alternatives)
    context: RelationalGraphWithCuts
    alternatives: FrozenSet[str]
    current_selection: FrozenSet[str] = frozenset()

    # Kind discriminates use case (determines semantics)
    kind: Literal[
        "interrogative",     # Q: "which answer to this question?"
        "hypothetical",      # Q: "which theory explains this?"
        "modal",             # Q: "which future is possible?"
        "counterfactual",    # Q: "if X were true, then?"
        "agentive",          # Q: "which action should I take?"
        "epistemic",         # Q: "which world is actual?"
        "metacognitive",     # Q: "what could I do/think?"
        "other",             # Unspecified
    ] = "other"

    # Lifecycle tracking
    emerged_at_state: str = ""
    resolved_at_state: Optional[str] = None
    selection_path: List[str] = field(default_factory=list)

    # Metadata
    warrant: float = 1.0
    source: str = "unspecified"

    # ===== Status Encoding (via current_selection cardinality) =====

    @property
    def status(self) -> Literal["unresolved", "partial", "resolved"]:
        """
        Encode status via current_selection cardinality (immutable semantics).

        - unresolved: len(current_selection) == 0
        - partial: 0 < len(current_selection) < len(alternatives)
        - resolved: len(current_selection) == 1
        """
        if not self.current_selection:
            return "unresolved"
        elif len(self.current_selection) == 1:
            return "resolved"
        else:
            return "partial"

    # ===== Deliberative Operations =====

    def narrow_to(self, choices: Set[str]) -> "AlternativeSet":
        """Narrow alternatives to a subset.

        Reduces current_selection to the intersection of the provided choices
        and alternatives. If current_selection becomes non-empty and we were
        unresolved, status transitions to "partial".

        Args:
            choices: The subset of alternatives to narrow to

        Returns:
            A new AlternativeSet with narrowed alternatives and updated selection

        Raises:
            ValueError: If choices is empty or has no overlap with alternatives
        """
        if not choices:
            raise ValueError("Cannot narrow to an empty set of choices")

        narrowed = frozenset(choices & self.alternatives)
        if not narrowed:
            raise ValueError("No overlap between choices and alternatives")

        return AlternativeSet(
            id=self.id,
            context=self.context,
            alternatives=narrowed,
            current_selection=frozenset(choices & narrowed),
            kind=self.kind,
            emerged_at_state=self.emerged_at_state,
            resolved_at_state=self.resolved_at_state,
            selection_path=self.selection_path,
            warrant=self.warrant,
            source=self.source,
        )

    def select(self, choice: str) -> "AlternativeSet":
        """Commit to one alternative; resolve the choice.

        Sets current_selection to {choice} and locks status to "resolved".
        The resolved_at_state must be supplied separately (typically by the
        UoD when recording the resolution).

        Args:
            choice: The EGI hash of the chosen alternative

        Returns:
            A new AlternativeSet with status locked to "resolved"

        Raises:
            ValueError: If choice is not in alternatives
        """
        if choice not in self.alternatives:
            raise ValueError(f"Choice {choice} not in alternatives")

        return AlternativeSet(
            id=self.id,
            context=self.context,
            alternatives=self.alternatives,
            current_selection=frozenset({choice}),
            kind=self.kind,
            emerged_at_state=self.emerged_at_state,
            resolved_at_state=self.resolved_at_state,
            selection_path=self.selection_path,
            warrant=self.warrant,
            source=self.source,
        )

    def deepen(self, new_alternatives: Set[str]) -> "AlternativeSet":
        """Discover new possible alternatives.

        Expands alternatives by adding new_alternatives. If alternatives was
        previously narrowed (current_selection is non-empty), status returns
        to "partial" to reflect the re-opening of deliberation.

        Args:
            new_alternatives: New alternatives to add

        Returns:
            A new AlternativeSet with expanded alternatives

        Raises:
            ValueError: If new_alternatives is empty
        """
        if not new_alternatives:
            raise ValueError("Cannot deepen with an empty set of alternatives")

        expanded = frozenset(self.alternatives | new_alternatives)
        new_status_via_selection = "partial" if self.current_selection else self.current_selection

        return AlternativeSet(
            id=self.id,
            context=self.context,
            alternatives=expanded,
            current_selection=self.current_selection,
            kind=self.kind,
            emerged_at_state=self.emerged_at_state,
            resolved_at_state=self.resolved_at_state,
            selection_path=self.selection_path,
            warrant=self.warrant,
            source=self.source,
        )

    def remerge_with(self, new_context: RelationalGraphWithCuts) -> "AlternativeSet":
        """Abductive re-emergence: same alternatives, new context.

        The alternative-set is re-opened with a new context (typically a refined
        state of the UoD), returning selection to empty (status to "unresolved").
        This models the abductive cycle where alternatives re-appear in a new
        presuppositional context.

        Args:
            new_context: The updated EGI state that the alternatives reappear in

        Returns:
            A new AlternativeSet with the same alternatives but updated context
        """
        return AlternativeSet(
            id=self.id,
            context=new_context,
            alternatives=self.alternatives,
            current_selection=frozenset(),
            kind=self.kind,
            emerged_at_state=self.emerged_at_state,
            resolved_at_state=None,
            selection_path=self.selection_path,
            warrant=self.warrant,
            source=self.source,
        )

    # ===== Serialization =====

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON persistence.

        Converts the EGI context to EGIF string format (the canonical
        linear form). All other fields are JSON-native.

        Returns:
            A dictionary with all AlternativeSet fields, ready for JSON serialization
        """
        from egif_generator_dau import generate_egif

        return {
            "id": self.id,
            "context": generate_egif(self.context),
            "alternatives": sorted(self.alternatives),
            "current_selection": sorted(self.current_selection),
            "kind": self.kind,
            "emerged_at_state": self.emerged_at_state,
            "resolved_at_state": self.resolved_at_state,
            "selection_path": self.selection_path,
            "warrant": self.warrant,
            "source": self.source,
        }

    @staticmethod
    def from_dict(data: dict) -> "AlternativeSet":
        """Deserialize from dictionary (JSON persistence).

        Reconstructs an AlternativeSet from its serialized form, converting the
        context back to an EGI by parsing its EGIF string.

        Args:
            data: Dictionary with all AlternativeSet fields

        Returns:
            An AlternativeSet instance

        Raises:
            KeyError: If required fields are missing
            ValueError: If data is malformed
        """
        from egif_parser_dau import parse_egif

        return AlternativeSet(
            id=data["id"],
            context=parse_egif(data["context"]),
            alternatives=frozenset(data["alternatives"]),
            current_selection=frozenset(data.get("current_selection", [])),
            kind=data.get("kind", "other"),
            emerged_at_state=data.get("emerged_at_state", ""),
            resolved_at_state=data.get("resolved_at_state"),
            selection_path=data.get("selection_path", []),
            warrant=data.get("warrant", 1.0),
            source=data.get("source", "unspecified"),
        )


# ===== Backward Compatibility Alias =====
# For migration period: old code using Doubt can gradually switch to AlternativeSet
Doubt = AlternativeSet
