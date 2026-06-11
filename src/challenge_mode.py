"""
Challenge mode — correspondence, learned by doing.

Design-of-record: ``docs/FREEFORM_COMPOSITION_AND_LEARNING.md`` (build step 4).

The freeform canvas trains the *machine's* tolerance for human drawings; challenge
mode trains the *human's* hand.  Present a linear form, ask the author to draw it
freehand, then read their drawing into an EGI and compare it to the parsed target.
The grader is isomorphism (``same_graph``, via ``egi_diff``); the feedback is the
**legible EGI diff** — the discrepancy report, in EG vocabulary (missing / extra /
scope / incidence / order), not a pixel comparison.  A drawing that *looks*
different but denotes the same graph passes; one that looks similar but mis-scopes a
line fails with a scope finding (the gold Beta error).

This module is the gradeable core, standalone and web-independent:

    list_challenges() / get_challenge(id)   — the curated difficulty gradient
    grade(target, attempt) -> DiffReport     — same_graph + legible_diff

The bank is a deliberate gradient (single relation → argument order → conjunction →
negation → the scroll → the universal with a line crossing a cut boundary), so the
hard cases the reader was de-risked on are exactly the ones the learner climbs to.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union

from egi_core_dau import RelationalGraphWithCuts
from egi_diff import DiffReport, legible_diff
from egif_parser_dau import parse_egif


@dataclass(frozen=True)
class Challenge:
    """One challenge: a linear form to draw, with a difficulty rank and a hint.

    The ``prompt_egif`` is what the learner reads and must render freehand; the
    drawing is never shown (that is the point — the correspondence has to be
    reconstructed, not copied).
    """

    id: str
    title: str
    prompt_egif: str
    difficulty: int     # 1 (easiest) … 5 (a shared line crossing a cut boundary)
    hint: str = ""


# The gradient.  Each rung introduces exactly one new correspondence skill.
CHALLENGE_BANK: List[Challenge] = [
    Challenge(
        id="one-relation",
        title="One relation",
        prompt_egif='(man "Socrates")',
        difficulty=1,
        hint="A single predicate on one named individual: a spot, its name, and the relation.",
    ),
    Challenge(
        id="argument-order",
        title="Argument order",
        prompt_egif='(loves "Romeo" "Juliet")',
        difficulty=2,
        hint="A binary relation — the order of the two individuals is part of what it says.",
    ),
    Challenge(
        id="conjunction",
        title="A shared line of identity",
        prompt_egif='(man *x) (mortal x)',
        difficulty=3,
        hint="Two relations on one line of identity: the same (unnamed) thing is both.",
    ),
    Challenge(
        id="negation",
        title="A denial",
        prompt_egif='~[ (happy "Socrates") ]',
        difficulty=3,
        hint="One cut around the relation: it denies that the thing inside holds.",
    ),
    Challenge(
        id="scroll",
        title="If–then (the scroll)",
        prompt_egif='~[ (man "Socrates") ~[ (mortal "Socrates") ] ]',
        difficulty=4,
        hint="A cut inside a cut: the outer denies (inner-affirmed AND outer-affirmed) — an implication.",
    ),
    Challenge(
        id="universal",
        title="Every man is mortal",
        prompt_egif='~[ (man *x) ~[ (mortal x) ] ]',
        difficulty=5,
        hint="A scroll with one line of identity running from the outer cut into the inner one — ∀x(man→mortal). Where the line sits is the whole meaning.",
    ),
]


def list_challenges() -> List[Challenge]:
    """The full bank, in difficulty order."""
    return sorted(CHALLENGE_BANK, key=lambda c: (c.difficulty, c.id))


def get_challenge(challenge_id: str) -> Optional[Challenge]:
    """Look up a challenge by id, or ``None``."""
    for c in CHALLENGE_BANK:
        if c.id == challenge_id:
            return c
    return None


def grade(
    target: Union[str, RelationalGraphWithCuts],
    attempt: RelationalGraphWithCuts,
) -> DiffReport:
    """Grade an attempt against a target.

    ``target`` may be an EGIF string (parsed here) or an already-built EGI.  Returns
    the legible diff: ``matches`` is true iff the attempt denotes the same graph as
    the target; otherwise the findings explain, in EG vocabulary, exactly how they
    differ.
    """
    t = parse_egif(target) if isinstance(target, str) else target
    return legible_diff(t, attempt)
