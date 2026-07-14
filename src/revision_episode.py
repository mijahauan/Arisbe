"""**The revision episode, unpacked** — what really happens when M meets a black swan.

``model_revision.revise_with_disposition`` performs a ``challenge_to_M`` in one
call: it retracts the impugned law *and* admits the anomaly (``content: "both"``).
The chain then records one opaque step — and ``proof_character`` says so, flagging
the swan chain as *"4 derived steps collapse primitive moves this reader cannot
see."* Four distinct acts, of three different logical kinds, are hidden in there:

  1. **PROPOSE** — a black swan is *entertained*. Not yet admitted: a candidate.
  2. **EXHIBIT** — the conflict between M and the observation is **derived**, not
     declared. This is a **deduction**, and it is the beat that was missing
     entirely: nothing in the old chain ever *showed* the contradiction; the
     Challenger recognised a refuting *shape* and asserted one.
  3. **FORK** — two ways to restore consistency (relinquish the law, or reject the
     report). A genuine **choice**, and therefore a real branch in the DAG.
  4. **DISPOSE** — retract + assert, *citing the exhibited conflict as its reason*.
     **Ampliative**, not deductive: no rule of inference compels it.

**Entertaining is enclosure** (the author's observation, and it is the load-bearing
one). To weigh two alternatives without asserting either, both must be scribed under
a cut; and to reason about M *inside* that cut you must copy M in — which is
**Iteration**, sound precisely because it copies from a less-enclosed context into a
more-enclosed one. So the M an episode deliberates over is an **iterated working
copy**, and what is derived inside the enclosure *cannot be exported by deduction*.
That cut boundary is not a technicality: it is what enforces the fact that **a
decision to revise M is not a deduction**. The old one-step implementation smuggled
the choice past the boundary and recorded only its result.

**The premiss the conflict needs.** A black swan contradicts "all swans are white"
only given *nothing is both black and white*. That law was never on M's sheet — it
lived in the Challenger's code. :func:`exhibit_conflict` requires it explicitly, so
the contradiction is a **checkable derivation** ending in the empty cut, rather than
a referee's say-so.

Geometry-free, deterministic, additive. Design-of-record: docs/EXEMPLARS.md and
docs/ENDOPOREUTIC_GAME_GUIDE.md (the disposition taxonomy this unpacks).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

import eg_navigation as nav
from derived_rules import universal_instantiation
from egif_parser_dau import parse_egif
from proof_authoring import ProofChain

# The four beats.
PROPOSE = "propose"
EXHIBIT = "exhibit"
FORK = "fork"
DISPOSE = "dispose"
BEATS = (PROPOSE, EXHIBIT, FORK, DISPOSE)


@dataclass
class ConflictExhibit:
    """A **derived** contradiction: M + the observation reach the empty cut.

    ``absurd`` is True iff the derivation actually reached ``~[ ]`` — absurdity, the
    graph that asserts the impossible. ``chain`` is the derivation itself (real Dau
    rule applications, replayable and checkable). ``working_copy`` records that this
    was conducted on an **iterated copy** of M: nothing here is asserted of M, and
    nothing derived here transfers to M by deduction."""

    absurd: bool
    chain: object = None
    steps: List[str] = field(default_factory=list)
    reason: str = ""
    working_copy: bool = True

    @property
    def summary(self) -> str:
        if not self.absurd:
            return "no contradiction could be derived — M and the observation coexist."
        return (f"contradiction DERIVED in {len(self.steps)} steps, ending in the "
                f"empty cut: {self.reason}")


def _empty_cut_on_sheet(egi) -> bool:
    """Is there an empty cut on the sheet — absurdity, scribed?"""
    for c in nav.child_cuts(egi, egi.sheet):
        if not nav.child_edges(egi, c) and not nav.child_cuts(egi, c):
            return True
    return False


def exhibit_conflict(
    model_egif: str,
    *,
    individual: str,
    law_relation: str,
    disjoint_relation: str,
) -> ConflictExhibit:
    """**Derive** the conflict rather than declare it.

    ``model_egif`` must carry, on one sheet: the observation about ``individual``
    (e.g. ``(swan "Nox") (black "Nox")``), the impugned law (a scroll over
    ``law_relation``, e.g. *all swans are white*), and the **disjointness law**
    that makes the observation a *refutation* at all (e.g. *nothing is both black
    and white*, a cut over ``disjoint_relation``).

    The derivation (all six moves are ordinary Dau rules, so a reader can check
    each one):

      1. **UI** — instantiate the law at the individual.
      2. **IT−** — deiterate the antecedent: the sheet already asserts it.
      3. **DC−** — discharge the double cut. The consequent is now on the sheet.
      4. **UI** — instantiate the disjointness law at the individual.
      5. **IT−** — deiterate one conjunct out of it…
      6. **IT−** — …and the other. The cut is left **empty**: absurdity.

    Returns a :class:`ConflictExhibit`; ``absurd`` is False (never an exception) if
    the graph does not in fact support the derivation — a conflict that cannot be
    derived is a finding, not a crash."""
    try:
        pc = ProofChain.from_egif(model_egif)

        def indiv(g):
            return nav.vertex_by_label(g, individual)

        def law(g):
            return nav.cut_holding_relation(g, g.sheet, law_relation)

        def disj(g):
            return nav.cut_holding_relation(g, g.sheet, disjoint_relation)

        def ground_cut(g, rel):
            """A sheet-level cut holding a *ground* ``rel`` edge on the individual —
            i.e. an instantiated copy, not the general law."""
            for c in nav.child_cuts(g, g.sheet):
                for e in nav.child_edges(g, c, rel):
                    vs = nav.vertices_of_edge(g, e)
                    if vs and g.get_vertex(vs[0]).label == individual:
                        return c
            return None

        def double_cut(g):
            for c in nav.child_cuts(g, g.sheet):
                if not nav.child_edges(g, c) and len(nav.child_cuts(g, c)) == 1:
                    return c
            return None

        pc.apply_derived(
            "UI",
            lambda g: universal_instantiation(
                g, universal_cut=law(g), target_area=g.sheet,
                join_vertex=indiv(g), edge_id="e_ui_law"),
            note=f"Instantiate the law at {individual}.")
        pc.apply("IT-",
                 select=lambda g: nav.child_edges(
                     g, ground_cut(g, law_relation), law_relation)[0],
                 note=f"Deiterate ({law_relation} {individual}) — the sheet already "
                      f"asserts it.")
        pc.apply("DC-", select=double_cut,
                 note="Discharge the double cut: the consequent lands on the sheet.")
        pc.apply_derived(
            "UI",
            lambda g: universal_instantiation(
                g, universal_cut=disj(g), target_area=g.sheet,
                join_vertex=indiv(g), edge_id="e_ui_disj"),
            note=f"Instantiate the disjointness law at {individual}.")
        pc.apply("IT-",
                 select=lambda g: nav.child_edges(
                     g, ground_cut(g, disjoint_relation), disjoint_relation)[0],
                 note="Deiterate the observed property out of the disjointness cut.")

        # The second conjunct: whatever else the disjointness cut still holds.
        def last_conjunct(g):
            for c in nav.child_cuts(g, g.sheet):
                kids = nav.child_edges(g, c)
                if len(kids) == 1 and not nav.child_cuts(g, c):
                    return kids[0]
            return None

        pc.apply("IT-", select=last_conjunct,
                 note="Deiterate the derived property too — the cut is now EMPTY.")

        chain = pc.to_chain()
        absurd = _empty_cut_on_sheet(pc.current)
        return ConflictExhibit(
            absurd=absurd,
            chain=chain,
            steps=[s.rule_name for s in chain.steps],
            reason=(f"the law forces ({disjoint_relation}-complement) of {individual}, "
                    f"but {individual} is observed otherwise — and nothing can be both."
                    if absurd else "the derivation did not reach absurdity"),
        )
    except Exception as exc:                       # a failed exhibit is a FINDING
        return ConflictExhibit(absurd=False, reason=f"could not derive: {exc}")


@dataclass
class Alternative:
    """One way to restore consistency — entertained, not asserted."""
    key: str
    label: str
    consequence: str


def alternatives(law_gloss: str, observation_gloss: str) -> List[Alternative]:
    """The two ways out, which the episode must *choose* between rather than
    deduce. Recorded as siblings in the DAG so the road not taken stays visible —
    a scientist's notebook keeps both."""
    return [
        Alternative(
            key="relinquish_law",
            label=f"Admit the observation; relinquish “{law_gloss}”.",
            consequence="M loses the over-general law and gains the anomaly. "
                        "(Abduction: the irritation of doubt revises the habit.)"),
        Alternative(
            key="reject_report",
            label=f"Keep “{law_gloss}”; reject the report.",
            consequence="M is unchanged; the observation is denied (a mis-sighting, "
                        "a mislabelled bird). Cheap now, and the cost falls due later "
                        "if the report was true."),
    ]


__all__ = [
    "PROPOSE", "EXHIBIT", "FORK", "DISPOSE", "BEATS",
    "ConflictExhibit", "exhibit_conflict", "Alternative", "alternatives",
]
