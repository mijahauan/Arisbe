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

**The dragons.** ``docs/FIELD_GUIDE_AND_DRAGONS.md`` marks eight "here-be-dragons"
pitfalls.  Five of them are *drawable* — a single graph you can be asked to render,
where the tempting wrong move surfaces as a specific legible-diff finding — and each
such challenge carries the ``dragon`` it trains plus the field-guide ``antidote``,
shown when the grade comes back wrong.  The mapping:

    🐉1 missing outer cut ("every" vs "some-isn't")  → ``universal``
    🐉2 blank sheet vs the empty cut (true vs false) → ``empty-cut``
    🐉3 the double cut you may *not* remove          → ``double-cut`` (vs ``scroll``)
    🐉4 a line declares (``*x``) vs refers (``x``)   → ``conjunction``
    🐉5 argument order is not symmetric              → ``argument-order``

Dragons 6–8 ("which graph is closer to reality", "I need a mark for *possibly*",
"I named it, so it counts") are *conceptual* — no single graph draws them — so they
belong to the warrant / correspondence-not-truth surfaces, not this bank.  See
``list_dragons()`` for the drawable walk and the field guide for the full eight.
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
    # Dragon metadata (``docs/FIELD_GUIDE_AND_DRAGONS.md``).  ``dragon`` is the
    # field-guide pitfall number this challenge trains (None for a pure warm-up
    # rung); ``temptation`` names the common wrong move; ``antidote`` is the
    # field-guide one-liner, shown when the grade comes back wrong.
    dragon: Optional[int] = None
    temptation: str = ""
    antidote: str = ""


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
        dragon=5,
        temptation='Swapping the hooks: (loves "Juliet" "Romeo") is a different, silent claim.',
        antidote="Order is part of the meaning, and it is drawable — read the hooks "
                 "clockwise around the spot. When a relation isn't symmetric, check the "
                 "order the way you'd check a minus sign.",
    ),
    Challenge(
        id="empty-cut",
        title="The empty cut — false",
        prompt_egif='~[ ]',
        difficulty=2,
        hint="A cut drawn around nothing. Not the same as a blank sheet.",
        dragon=2,
        temptation="Treating a cut-around-nothing like a blank sheet. The blank sheet "
                   "means true; an empty cut means false.",
        antidote="An empty cut is the strongest claim you can make — it says 'this is "
                 "impossible.' Put one next to anything and you've declared the whole "
                 "sheet false. When you mean 'true / nothing left to say,' you want the "
                 "blank, not a cut around a blank.",
    ),
    Challenge(
        id="conjunction",
        title="A shared line of identity",
        prompt_egif='(man *x) (mortal x)',
        difficulty=3,
        hint="Two relations on one line of identity: the same (unnamed) thing is both.",
        dragon=4,
        temptation="Drawing two separate lines — saying 'some man, and separately, "
                   "something mortal.' The line never connected.",
        antidote="A line declares once (*x) and refers everywhere else (x) — and in the "
                 "drawn form it is one connected line. Star a line once, where it first "
                 "appears; thread the same line through every spot that is the same thing.",
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
        hint="A cut inside a cut, with content in the outer ring: the outer denies "
             "(inner-affirmed AND outer-affirmed) — an implication.",
    ),
    Challenge(
        id="double-cut",
        title="The removable double cut",
        prompt_egif='~[ ~[ (mortal "Socrates") ] ]',
        difficulty=4,
        hint="Two cuts directly nested with NOTHING in the ring between them.",
        dragon=3,
        temptation="Confusing this with the scroll. They look almost identical, but the "
                   "scroll has a relation sitting in the ring between the two cuts — and "
                   "that one is NOT a removable double cut.",
        antidote="Before peeling two nested cuts, look in the ring between them. Empty? "
                 "Then it's a removable double cut (~[ ~[ P ] ] = P). Anything there? "
                 "Then it's a scroll doing its job — peeling it would turn 'if P then Q' "
                 "into 'P and Q,' inventing a claim.",
    ),
    Challenge(
        id="universal",
        title="Every man is mortal",
        prompt_egif='~[ (man *x) ~[ (mortal x) ] ]',
        difficulty=5,
        hint="A scroll with one line of identity running from the outer cut into the inner one — ∀x(man→mortal). Where the line sits is the whole meaning.",
        dragon=1,
        temptation="Leaving the antecedent bare on the sheet: (man *x) ~[ (mortal x) ] "
                   "reads 'there is a man who is NOT mortal' — the opposite of what you meant.",
        antidote="A conditional always lives inside an outer cut, with the conclusion "
                 "nested one deeper. If your 'if-then' has its antecedent sitting bare on "
                 "the sheet, you've drawn an existential, not a universal.",
    ),
]


def list_challenges() -> List[Challenge]:
    """The full bank, in difficulty order."""
    return sorted(CHALLENGE_BANK, key=lambda c: (c.difficulty, c.id))


def list_dragons() -> List[Challenge]:
    """The drawable-dragon walk: the field-guide pitfalls a learner can meet by
    drawing, ordered by dragon number (1 → 5).  See
    ``docs/FIELD_GUIDE_AND_DRAGONS.md``; dragons 6–8 are conceptual and not here.
    """
    return sorted(
        (c for c in CHALLENGE_BANK if c.dragon is not None),
        key=lambda c: c.dragon,
    )


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
