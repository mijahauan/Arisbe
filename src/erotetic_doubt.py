"""
Erotetic Logic: Formal Structure of Doubt and Questions

A Doubt is the erotetic (question-centered) structure of inquiry. It formalizes:
- Presupposition: What must hold for the question to be well-posed
- Erotetic_Core: The set of possible answers under consideration
- Status: Lifecycle state (unresolved → partial → resolved)
- Resolution Path: How the doubt moved through the UoD's history

Philosophical Foundation:
- Formalizes Peirce's dialogical doubt (not psychological doubt)
- Grounds inquiry in erotetic logic (Hamblin, Cross-Pollard)
- Embeds doubt in the diachronic UoD as metadata (never EGI content)

See: docs/superpowers/plans/2026-07-25-item-4-phase-2-doubt-implementation.md
"""

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Literal, Optional, Set

from egi_core_dau import RelationalGraphWithCuts


@dataclass(frozen=True)
class Doubt:
    """Formal erotetic structure of a doubt/question.

    A Doubt captures the structure of inquiry as it evolves through a UoD:
    the presupposition that must hold, the set of possible answers being
    considered, and the lifecycle tracking how the doubt was resolved (or
    re-emerged in a new form).

    Attributes:
        id: Unique identifier within a UoD (e.g., "d0", "d1", ...)
        presupposition: EGI state that must hold for the question to be well-posed
        erotetic_core: Set of EGI hashes representing possible answers
        current_answers: Subset of erotetic_core that have been admitted/explored
        status: Lifecycle state (unresolved/partial/resolved)
        emerged_at_state_id: State ID where doubt first appeared
        resolved_at_state_id: State ID where doubt was resolved (if ever)
        resolution_path: Ordered list of state IDs the doubt passed through
        kind: Semantic category of doubt (unknown_verdict/thin_spot/etc)
        warrant: Confidence in the doubt itself (0.0–1.0)
        source: Where the doubt originated (e.g., "unknown_verdict", "oracle")
    """

    # Erotetic structure (the question)
    id: str
    presupposition: RelationalGraphWithCuts
    erotetic_core: FrozenSet[str]
    current_answers: FrozenSet[str] = frozenset()

    # Status in the lifecycle
    status: Literal["unresolved", "partial", "resolved"] = "unresolved"

    # Lifecycle tracking
    emerged_at_state_id: str = ""
    resolved_at_state_id: Optional[str] = None
    resolution_path: List[str] = field(default_factory=list)

    # Metadata
    kind: Literal["unknown_verdict", "thin_spot", "unwitnessed", "branch_point", "other"] = "other"
    warrant: float = 1.0
    source: str = "unspecified"

    def narrow_to(self, answers: Set[str]) -> "Doubt":
        """Narrow erotetic core to a subset of answers.

        Updates current_answers to the intersection of the erotetic_core and
        the provided answers. If current_answers becomes non-empty and we were
        unresolved, status transitions to "partial".

        Args:
            answers: The subset of answers to narrow to

        Returns:
            A new Doubt with narrowed erotetic_core and updated status

        Raises:
            ValueError: If answers is empty or has no overlap with erotetic_core
        """
        if not answers:
            raise ValueError("Cannot narrow to an empty set of answers")

        narrowed = frozenset(answers & self.erotetic_core)
        if not narrowed:
            raise ValueError("No overlap between answers and erotetic_core")

        new_status = "partial" if self.status == "unresolved" else self.status

        return Doubt(
            id=self.id,
            presupposition=self.presupposition,
            erotetic_core=narrowed,
            current_answers=frozenset(answers & narrowed),
            status=new_status,
            emerged_at_state_id=self.emerged_at_state_id,
            resolved_at_state_id=self.resolved_at_state_id,
            resolution_path=self.resolution_path,
            kind=self.kind,
            warrant=self.warrant,
            source=self.source,
        )

    def resolve_to(self, answer: str) -> "Doubt":
        """Resolve to a single answer.

        Sets current_answers to {answer} and locks status to "resolved".
        The resolved_at_state_id must be supplied separately (typically
        by the UoD when recording the resolution).

        Args:
            answer: The EGI hash of the chosen answer

        Returns:
            A new Doubt with status locked to "resolved"

        Raises:
            ValueError: If answer is not in erotetic_core
        """
        if answer not in self.erotetic_core:
            raise ValueError(f"Answer {answer} not in erotetic_core")

        return Doubt(
            id=self.id,
            presupposition=self.presupposition,
            erotetic_core=self.erotetic_core,
            current_answers=frozenset({answer}),
            status="resolved",
            emerged_at_state_id=self.emerged_at_state_id,
            resolved_at_state_id=self.resolved_at_state_id,
            resolution_path=self.resolution_path,
            kind=self.kind,
            warrant=self.warrant,
            source=self.source,
        )

    def deepen(self, new_answers: Set[str]) -> "Doubt":
        """Discover new possible answers.

        Expands erotetic_core by adding new_answers. If erotetic_core was
        previously narrowed (current_answers is non-empty), status returns
        to "partial" to reflect the re-opening.

        Args:
            new_answers: New answers to add to erotetic_core

        Returns:
            A new Doubt with expanded erotetic_core

        Raises:
            ValueError: If new_answers is empty
        """
        if not new_answers:
            raise ValueError("Cannot deepen with an empty set of answers")

        expanded = frozenset(self.erotetic_core | new_answers)
        new_status = "partial" if self.current_answers else self.status

        return Doubt(
            id=self.id,
            presupposition=self.presupposition,
            erotetic_core=expanded,
            current_answers=self.current_answers,
            status=new_status,
            emerged_at_state_id=self.emerged_at_state_id,
            resolved_at_state_id=self.resolved_at_state_id,
            resolution_path=self.resolution_path,
            kind=self.kind,
            warrant=self.warrant,
            source=self.source,
        )

    def reemergent_from(self, new_presupposition: RelationalGraphWithCuts) -> "Doubt":
        """Abductive re-emergence: doubt recurs with refined presupposition.

        The doubt is re-opened with a new presupposition (typically a refined
        state of the UoD), returning status to "unresolved". This models the
        abductive cycle where a resolved doubt re-appears in a new context.

        Args:
            new_presupposition: The updated EGI state that the doubt reappears in

        Returns:
            A new Doubt with the same erotetic_core but updated presupposition
        """
        return Doubt(
            id=self.id,
            presupposition=new_presupposition,
            erotetic_core=self.erotetic_core,
            current_answers=frozenset(),
            status="unresolved",
            emerged_at_state_id=self.emerged_at_state_id,
            resolved_at_state_id=None,
            resolution_path=self.resolution_path,
            kind=self.kind,
            warrant=self.warrant,
            source=self.source,
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON persistence.

        Converts the EGI presupposition to EGIF string format (the canonical
        linear form). All other fields are JSON-native.

        Returns:
            A dictionary with all Doubt fields, ready for JSON serialization
        """
        from egif_generator_dau import generate_egif

        return {
            "id": self.id,
            "presupposition": generate_egif(self.presupposition),
            "erotetic_core": sorted(self.erotetic_core),
            "current_answers": sorted(self.current_answers),
            "status": self.status,
            "emerged_at_state_id": self.emerged_at_state_id,
            "resolved_at_state_id": self.resolved_at_state_id,
            "resolution_path": self.resolution_path,
            "kind": self.kind,
            "warrant": self.warrant,
            "source": self.source,
        }

    @staticmethod
    def from_dict(data: dict) -> "Doubt":
        """Deserialize from dictionary (JSON persistence).

        Reconstructs a Doubt from its serialized form, converting the
        presupposition back to an EGI by parsing its EGIF string.

        Args:
            data: Dictionary with all Doubt fields

        Returns:
            A Doubt instance

        Raises:
            KeyError: If required fields are missing
            ValueError: If data is malformed
        """
        from egif_parser_dau import parse_egif

        return Doubt(
            id=data["id"],
            presupposition=parse_egif(data["presupposition"]),
            erotetic_core=frozenset(data["erotetic_core"]),
            current_answers=frozenset(data.get("current_answers", [])),
            status=data.get("status", "unresolved"),
            emerged_at_state_id=data.get("emerged_at_state_id", ""),
            resolved_at_state_id=data.get("resolved_at_state_id"),
            resolution_path=data.get("resolution_path", []),
            kind=data.get("kind", "other"),
            warrant=data.get("warrant", 1.0),
            source=data.get("source", "unspecified"),
        )
