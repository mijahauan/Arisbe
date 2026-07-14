"""**The arena** — the place set aside for testing, and why it must be a cut.

The author's observation, and it is a theorem rather than a convention:

    A contest must occur *somewhere*. That somewhere must be a **negated context**,
    so that what happens inside cannot ramify outward — the sandbox of an operating
    system, drawn. And since the blank sheet of assertion HAS no negated context,
    the very first act of a contest starting from nothing must be a **DC+**: make
    the place before you can posit anything in it.

Why it is forced, in three lines:

1. **The sheet asserts.** Anything scribed at depth 0 is *asserted*, full stop. There
   is nowhere on a blank sheet to put a hypothesis without thereby claiming it.
2. **Insertion is sound only in a negative context.** That is Dau's rule, and it is
   exactly the isolation guarantee: whatever you scribe into an odd-depth area, the
   enclosing sheet stays true. You cannot break, from inside the arena, what was
   already asserted outside it. *A malfunction within does not ramify outward.*
3. **DC+ is the only move that makes such a place while asserting nothing.** The
   empty double cut ``~[ ~[ ] ]`` is logically inert — it says exactly what the blank
   sheet says — yet it creates two areas:

       ~[            ← the ARENA: depth 1, NEGATIVE. Positing here is free and sound.
            ~[  ]    ← the HOLD:  depth 2, positive. Where a conclusion may be drawn.
          ]

   And a filled double cut is precisely a **scroll**: ``~[ A ~[ B ] ]`` = *A → B*.
   So the arena is literally the antecedent-place of a conditional.

**Hence the mode contract, explained rather than stipulated.** What you win in the
arena is not ``B`` — it is ``A → B``. The hypothesis is *discharged into* the result,
and that is why nothing earned in a contest may simply be moved onto the corpus's
sheet: it was never established unconditionally. To test is to hypothesise; to
hypothesise is to enter a scroll; and what comes out of a scroll is a conditional.

**The corpus already obeys this**, which is the evidence that it is not a doctrine
invented after the fact: every proof in ``tomos`` that starts from the blank sheet
begins **DC+ then INS** (``peirce_law``, ``theorem_praeclarum``). The ones that start
from a graph *already carrying a cut* go straight to INS — the place was there.
The ones that need no insertion at all (``beta_modus_ponens``: corollarial) never
open an arena, because they never posit anything.

Additive, geometry-free; every move here is an ordinary Dau rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import eg_navigation as nav
from egi_core_dau import ElementID, RelationalGraphWithCuts
from proof_authoring import apply_rule


@dataclass(frozen=True)
class Arena:
    """A place set aside for testing.

    ``arena`` is the **negative** area (odd depth) — where positing is free and
    sound, and where a hypothesis goes. ``hold`` is the **positive** area inside it,
    where a conclusion may be drawn. Together they are a scroll: what the arena
    holds is the antecedent, what the hold holds is the consequent."""

    arena: ElementID          # the outer cut's area — negative; posit here
    hold: ElementID           # the inner cut's area — positive; conclude here

    def reading(self) -> str:
        return ("if <what is posited in the arena> then <what is drawn in the hold> "
                "— a scroll; the hypothesis is discharged INTO the result.")


def polarity_of(egi: RelationalGraphWithCuts, area: ElementID) -> str:
    """``"positive"`` (even depth — asserts) or ``"negative"`` (odd depth — denies).
    Insertion is sound only in the negative."""
    depth = 0
    cur = area
    parents = nav.cut_parents(egi) if hasattr(nav, "cut_parents") else None
    from presentation_ops import cut_parents
    parents = cut_parents(egi)
    while cur != egi.sheet:
        depth += 1
        cur = parents.get(cur)
        if cur is None:
            break
    return "positive" if depth % 2 == 0 else "negative"


def open_arena(egi: RelationalGraphWithCuts,
               area: Optional[ElementID] = None) -> Tuple[RelationalGraphWithCuts, Arena]:
    """**Make the place.** DC+ — insert an empty double cut into ``area`` (the sheet
    by default).

    Logically inert: the graph after says exactly what the graph before said. But it
    now HAS a negative context — the arena — and until it does, there is nowhere to
    posit a hypothesis that is not an assertion.

    Returns the new EGI and the :class:`Arena` (the negative area to posit in, and
    the positive hold to conclude in)."""
    target = area or egi.sheet
    before = set(egi.Cut)
    g = apply_rule("DC+", egi, target=target)
    fresh = [c.id for c in g.Cut if c.id not in before]
    if len(fresh) != 2:
        raise ValueError(f"DC+ should create exactly two cuts; it created {len(fresh)}")
    from presentation_ops import cut_parents
    parents = cut_parents(g)
    # the outer of the pair is the one whose parent is the target area
    outer = next(c for c in fresh if parents.get(c) == target)
    inner = next(c for c in fresh if c != outer)
    return g, Arena(arena=outer, hold=inner)


def posit(egi: RelationalGraphWithCuts, arena: Arena, egif: str
          ) -> RelationalGraphWithCuts:
    """**Posit a hypothesis in the arena** — INS into the negative context.

    Sound, unconditionally: this is the sandbox guarantee. Whatever you scribe here,
    everything the sheet asserted outside the arena remains true. You are not
    claiming the hypothesis; you are supposing it, and the supposition is *fenced*.
    """
    if polarity_of(egi, arena.arena) != "negative":
        raise ValueError(
            "the arena is not a negative context — positing there would ASSERT the "
            "hypothesis rather than suppose it (and Insertion would be unsound)")
    return apply_rule("INS", egi, egif=egif, target=arena.arena)


def is_arena(egi: RelationalGraphWithCuts, area: ElementID) -> bool:
    """Is this area a place where testing may happen — i.e. negative?"""
    return polarity_of(egi, area) == "negative"


def preparatory_moves(egi: RelationalGraphWithCuts) -> List[str]:
    """What a contest must do *first*, given the graph it starts from.

    - From a **blank sheet**: ``["DC+"]`` — there is no negative context, so one must
      be made before anything can be supposed.
    - From a graph that **already carries a cut**: ``[]`` — the place exists; posit
      straight into it.

    This is the preparatory step made explicit, and it is exactly what the corpus's
    blank-sheet proofs already do."""
    for c in nav.child_cuts(egi, egi.sheet):
        return []                       # a negative context already exists
    return ["DC+"]


__all__ = ["Arena", "open_arena", "posit", "polarity_of", "is_arena",
           "preparatory_moves"]
