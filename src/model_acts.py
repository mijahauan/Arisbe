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

**ADDING TO M — AND THE ERROR TO AVOID HERE.** INS reaches only *negative* contexts,
and the sheet is positive. Nor is it only INS: run through the six and ask which can
put content into a positive context —

    INS   negative only                                                    ✗
    IT+   copies less-enclosed → more-enclosed; cannot reach the sheet     ✗
    ERA   removes                                                          ✗
    IT−   removes                                                          ✗
    DC+   adds an INERT double cut — no content                            ✗
    DC−   erases a double cut, EXPOSING its contents to the enclosing area ✓

**DC− is the only one.** And it can only expose what was *already there, enclosed*. So:

    **Nothing ever appears uncircumscribed on the sheet.**
    A fact reaches a positive context only by DISCHARGE — never by insertion.

That is the author's point, and it corrects a glib earlier formulation of this module
("adding is juxtaposition"), which made a graph sound as though it could materialise
from nowhere. It cannot. **An observation enters ENCLOSED** — as the consequent of a
scroll whose antecedent is its **warrant** ::

    (reported "sighting-1697")                              ← the warrant, asserted
    ~[ (reported "sighting-1697") ~[ (black "Nox") ] ]      ← "if reported, then so"

and then two ordinary rules bring it out: **IT−** (deiterate the warrant, which the
sheet already asserts) and **DC−** (discharge). The fact is **derived**, and the
warrant is not metadata — it is the *antecedent*, in the graph, doing logical work.
That is :func:`admit_by_discharge`, and once M carries such a trust-law, new
observations enter **by rule**.

**Where the regress stops, and why that is not a cheat.** Something must be uttered:
no rule can *originate* content, and the trust-law itself, and the base facts, are
asserted by an **utterer**. But that act is not *uncontextualized* either — the sheet
of assertion IS a context (this universe of discourse, this episode), and to scribe on
it is to speak *in* it, as that utterer, taking responsibility. Peirce's own limit: the
perceptual judgment is where inference bottoms out, and it is an act, not a deduction.
:func:`assert_into` is that act, named as such, and it demands a warrant precisely
because the calculus cannot supply one.

**Hence the shape of the whole thing:**

    The calculus is closed under consequence. It cannot ORIGINATE.
    Every element on the sheet was either UTTERED, or DISCHARGED from something
    already circumscribed.

    It can license you to GIVE UP a belief (ERA — free, sound).
    It can license you to DRAW OUT what your beliefs already contained (DC− — free,
    sound, and only if the warrant holds).
    It can never license you to ACQUIRE one from nowhere.

**And the same graph, in two places, is two different speech acts.** Insert
`(black "Nox")` into a *negative* arena (``contest_context``) and you have **supposed**
it — free, sound, fenced. Have it *discharged* onto the *positive* sheet and you have
**derived** it. Scribe it there bare, and you have **uttered** it — no rule permits
that, and you owe a warrant. *The polarity of the place determines the illocutionary
force.*

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
DISCHARGE = "discharge"       # a rule (IT- then DC-). Sound. The ONLY way content
                              # reaches the sheet — and only content already there,
                              # circumscribed, waiting on its warrant.
UTTER = "utter"               # NOT a rule. The speech act. The only way content
                              # ORIGINATES — and it is never uncontextualized: an
                              # utterer says it, on an occasion, taking responsibility.
ASSERT = UTTER                # (kept: the older name for the same act)


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


def admit_by_discharge(model: RelationalGraphWithCuts, fact_egif: str,
                       warrant_egif: str) -> tuple:
    """**How an observation properly enters M: circumscribed, then discharged.**

    Nothing appears uncircumscribed on the sheet. The fact is *not* juxtaposed; it
    arrives **enclosed** — as the consequent of a scroll whose antecedent is its
    **warrant**::

        (warrant)                          ← the report, asserted
        ~[ (warrant) ~[ (fact) ] ]         ← "if it is reported, it is so"

    Then two ordinary rules bring it out:

      **IT−** deiterate the warrant inside the scroll (the sheet already asserts it),
      **DC−** discharge the double cut — and the fact lands on the sheet.

    So the fact is **derived, never inserted**, and the warrant is not metadata: it is
    the *antecedent*, visible in the graph, and doing logical work. Once M carries such
    a trust-law, new observations enter **by rule**.

    Returns ``(new_model, Act)``. Raises ``UnwarrantedAssertion`` if the warrant is not
    asserted, or if M carries no scroll conditioning ``fact`` on it — because then
    there is nothing to discharge, and the fact would have to appear from nowhere."""
    from proof_authoring import apply_rule

    warrant = parse_egif(warrant_egif)
    warrant_names = {warrant.rel[e] for e in warrant.rel}
    sheet_names = {model.rel[e] for e in nav.child_edges(model, model.sheet)
                   if e in model.rel}
    if not warrant_names <= sheet_names:
        raise UnwarrantedAssertion(
            f"the warrant {warrant_egif!r} is not asserted on M's sheet. A fact enters "
            f"only by DISCHARGE — it must already be circumscribed in a scroll whose "
            f"antecedent holds. Assert the warrant first (an utterance), or suppose it "
            f"in an arena.")

    fact = parse_egif(fact_egif)
    fact_names = {fact.rel[e] for e in fact.rel}
    for cut in nav.child_cuts(model, model.sheet):
        inner = nav.child_cuts(model, cut)
        ante = {model.rel[e] for e in nav.child_edges(model, cut) if e in model.rel}
        if len(inner) != 1 or not warrant_names <= ante:
            continue
        cons = {model.rel[e] for e in nav.child_edges(model, inner[0])
                if e in model.rel}
        if not fact_names <= cons:
            continue
        # discharge it: deiterate the warrant, then erase the double cut
        g = model
        for e in list(nav.child_edges(g, cut)):
            if g.rel.get(e) in warrant_names:
                g = apply_rule("IT-", g, selection=[e])
        g = apply_rule("DC-", g, selection=[cut])
        return g, Act(
            kind=DISCHARGE, is_rule=True, sound=True, warrant=warrant_egif,
            note=("DERIVED onto the sheet by IT- then DC-. The fact was never "
                  "inserted — it was already there, circumscribed, waiting on its "
                  "warrant. DC- is the ONLY rule that can put content in a positive "
                  "context, and it can only expose what was already enclosed."))

    raise UnwarrantedAssertion(
        f"M carries no scroll conditioning {fact_egif!r} on {warrant_egif!r}, so there "
        f"is nothing to discharge — the fact could only appear UNCIRCUMSCRIBED, and no "
        f"rule permits that. Add the trust-law (an utterance), or suppose the fact in "
        f"an arena.")


def speech_act_of(model: RelationalGraphWithCuts, area) -> str:
    """**The polarity of the place determines the illocutionary force.**

    Scribe a graph in a *negative* area and you have **supposed** it (free, sound,
    fenced — the arena). Scribe the identical graph in a *positive* area and you have
    **asserted** it (no rule permits it; it owes warrant). Same ink, different act."""
    from contest_context import polarity_of

    return "suppose" if polarity_of(model, area) == "negative" else "assert"


__all__ = ["RELINQUISH", "DISCHARGE", "UTTER", "ASSERT", "Act",
           "UnwarrantedAssertion", "relinquish", "assert_into",
           "admit_by_discharge", "speech_act_of"]
