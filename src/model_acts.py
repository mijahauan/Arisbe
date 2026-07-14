"""**The two acts by which M changes** — and why they are not symmetric.

The author's question: *M contains "all swans are white". How do we erase it? ERA
happens only in a positive context. And if we want to add something? INS happens only
in a negative context.*

Working it through gives the sharpest result in the whole design, because the two
halves come out **completely different**:

**ERASING FROM M IS A RULE.** M's laws and facts sit on the **sheet** — depth 0,
*positive*. ERA erases from a positive context. So relinquishing "all swans are
white" is a **genuine Dau ERA**, and it is **sound**: erasure is a *weakening* rule
(M ⊨ M−law). Dropping a belief can never make you assert a falsehood; you only come
to say *less*. Logically, retraction is **free** — the calculus always permits it.

**ADDING TO M IS NOT A RULE AT ALL.** INS reaches only *negative* contexts, and the
sheet is positive. Try it and the engine refuses: *"Insertion only allowed in negative
(verso) areas."* And it is not just INS — **not one of the six rules can put new
content in a positive context.** That is not a gap in the calculus. It is the calculus
telling the truth:

    You cannot DEDUCE your way to new information.

So admitting `(black "Nox")` into M is **not an inference**. It is **juxtaposition** —
the bare act of scribing on the sheet — which for Peirce *is* the act of assertion,
and it enters from **outside** the calculus: from an observation, a report, a source.
It is **ampliative** (``proof_character``), and what it costs is **warrant**.

**Hence the asymmetry, which is the doctrine in one line:**

    The calculus can license you to GIVE UP a belief.
    It can never license you to ACQUIRE one.

**And the same graph, in two places, is two different speech acts.** Insert
`(black "Nox")` into a *negative* arena (``contest_context``) and you have **supposed**
it — free, sound, fenced. Juxtapose the identical graph on the *positive* sheet and
you have **asserted** it — no rule permits this, and you owe a warrant. *The polarity
of the place determines the illocutionary force.* That is why the arena is safe and
the sheet is not.

Additive; wraps ``model_revision`` rather than replacing it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import eg_navigation as nav
from egi_core_dau import RelationalGraphWithCuts
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif

RELINQUISH = "relinquish"     # a rule (ERA). Sound. Free.
ASSERT = "assert"             # not a rule. Ampliative. Costs warrant.


class UnwarrantedAssertion(ValueError):
    """Raised when something would be scribed onto M's sheet with no warrant.

    No rule of inference licenses adding content to a positive context, so an
    assertion cannot be *justified by the calculus*. Its warrant must come from
    somewhere — an observation, a report, a source, a decision. Refusing the
    unwarranted case is the calculus being honest about what it cannot do."""


@dataclass(frozen=True)
class Act:
    """One change to M, with the only two facts that matter about it: whether a
    rule licensed it, and what it cost."""

    kind: str                       # RELINQUISH | ASSERT
    is_rule: bool                   # was this a Dau rule application?
    sound: bool                     # is the result entailed by what came before?
    warrant: Optional[str] = None   # the source — REQUIRED for an assertion
    note: str = ""

    @property
    def summary(self) -> str:
        if self.kind == RELINQUISH:
            return ("relinquish — a genuine ERA on the positive sheet. Sound "
                    "(weakening: M ⊨ M−X). The calculus always permits giving up.")
        return (f"assert — NOT a rule: no inference reaches a positive context. "
                f"Ampliative, and it costs warrant [{self.warrant}].")


def relinquish(model: RelationalGraphWithCuts, subgraph_egif: str
               ) -> tuple:
    """**Give up part of M** — the law, the fact, the habit.

    This *is* a rule: the sheet is positive and ERA erases from a positive context.
    Sound by construction (erasure weakens), so it needs **no warrant** — you may
    always come to believe less. Returns ``(new_model, Act)``.

    Falls back to a structural removal only where Dau's for-erasure closure refuses
    the cut (a sheet-level cut sharing a line of identity across its boundary); the
    ``Act`` records honestly whether a rule licensed the move."""
    from model_revision import retract_subgraph

    target = parse_egif(subgraph_egif)
    by_rule = _try_era(model, subgraph_egif)
    if by_rule is not None:
        return by_rule, Act(
            kind=RELINQUISH, is_rule=True, sound=True,
            note="erased from the positive sheet by ERA — a Dau rule; sound.")
    # Not ERA-able (a boundary-crossing ligature): remove structurally, and SAY so.
    out = retract_subgraph(model, subgraph_egif)
    return out, Act(
        kind=RELINQUISH, is_rule=False, sound=True,
        note=("removed structurally: Dau's for-erasure closure refused this cut "
              "(a line of identity crosses its boundary). Still a weakening — M "
              "says less — but not licensed by ERA, and recorded as such."))


def _try_era(model: RelationalGraphWithCuts, subgraph_egif: str):
    """Erase the matching sheet-level cut by a real ERA, or ``None`` if the rule
    refuses / nothing matches."""
    from eg_navigation import same_graph
    from proof_authoring import apply_rule

    target = parse_egif(subgraph_egif)
    for cut in nav.child_cuts(model, model.sheet):
        try:
            out = apply_rule("ERA", model, selection=[cut])
        except Exception:
            continue
        # the right cut is the one whose removal leaves M-minus-the-subgraph
        try:
            if same_graph(parse_egif(f"{generate_egif(out)} {subgraph_egif}".strip()),
                          model):
                return out
        except Exception:
            continue
    return None


def assert_into(model: RelationalGraphWithCuts, graph_egif: str, *,
                warrant: Optional[str] = None) -> tuple:
    """**Admit something new into M** — a fact, a law, an observation.

    **No rule does this.** INS reaches only negative contexts; the sheet is positive;
    and no other rule puts new content anywhere. So this is *juxtaposition* — the act
    of scribing, which is assertion itself — and it is **ampliative**: it adds what no
    inference compels.

    Therefore ``warrant`` is **required**, and :class:`UnwarrantedAssertion` is raised
    without one. This is not bureaucracy: the calculus genuinely cannot justify an
    addition, so *something else must*, and the record must say what. Returns
    ``(new_model, Act)``."""
    if not (warrant and str(warrant).strip()):
        raise UnwarrantedAssertion(
            "nothing may be scribed onto M's sheet without a warrant. No rule of "
            "inference reaches a positive context — an addition is not deduced but "
            "ASSERTED, and an assertion owes a source (an observation, a report, a "
            "decision). To *suppose* it instead, insert it into a negative arena "
            "(contest_context.posit) — that is free, and it is fenced.")
    from model_revision import assert_fact

    out = assert_fact(model, graph_egif)
    return out, Act(kind=ASSERT, is_rule=False, sound=False, warrant=str(warrant),
                    note=("juxtaposed onto the positive sheet — the act of assertion. "
                          "No rule licenses it; the warrant does."))


def speech_act_of(model: RelationalGraphWithCuts, area) -> str:
    """**The polarity of the place determines the illocutionary force.**

    Scribe a graph in a *negative* area and you have **supposed** it (free, sound,
    fenced — the arena). Scribe the identical graph in a *positive* area and you have
    **asserted** it (no rule permits it; it owes warrant). Same ink, different act."""
    from contest_context import polarity_of

    return "suppose" if polarity_of(model, area) == "negative" else "assert"


__all__ = ["RELINQUISH", "ASSERT", "Act", "UnwarrantedAssertion",
           "relinquish", "assert_into", "speech_act_of"]
