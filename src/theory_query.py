"""
Theory query — is the universal G a *theorem* of the theory M?

Design-of-record: ``docs/DOMAIN_ORACLE_AND_M.md`` §6.1 (materialization) and
``docs/GENERATION_AND_TESTING.md`` clarification 1 (model-checking vs inference).

The peel (``semantic_game.evaluate``) is **model-checking**: it asks whether G holds
in the *facts* of M.  Materialization (``model_materialization``) fills those facts
out by forward-chaining M's Horn rules.  But a real **T-box ontology** — Porphyry,
FOAF, the SUMO upper spine — is almost all rules and few or no individuals.  Over an
empty A-box a subsumption proposal ``~[ (Object *x) ~[ (Entity x) ] ]`` reads
*vacuously* TRUE closed (the wrong reason — a nonsense universal reads TRUE too) or
UNKNOWN open.  Model-checking simply cannot decide a theorem of the theory.

The decision that *can* is **deduction**, and for the Horn/Datalog fragment it is the
standard, complete, terminating procedure — **freeze a fresh witness**:

  1. take the universal G = ``~[ B(x⃗) ~[ H(x⃗) ] ]`` (body → head, range-restricted);
  2. mint a fresh constant for each line of identity in B and assert B over those
     constants — an *arbitrary* individual nowhere mentioned in M;
  3. materialize M ∪ {frozen B} (run M's rules over the witness);
  4. check H over the same constants.  Because the witnesses are arbitrary, H holding
     of them means G holds *universally* — G is a theorem of M.

Soundness: the fresh constants occur nowhere in M, so any derivation of H(witnesses)
uses only M's universally-quantified rules; it therefore holds for *every*
substitution.  Completeness for the Horn fragment: the least Herbrand model is the
unique minimal model, so a head atom is derivable iff the Horn theory entails it.

Honesty about the residue: if M carries **non-Horn** axioms that materialization had
to skip, a *negative* result is reported ``UNKNOWN`` (the Horn fragment doesn't prove
G, but the skipped axioms might), not ``FALSE``.  When M is wholly Horn, a negative is
a definite ``FALSE`` (not a theorem).  A positive is always ``TRUE`` — derivation is
sound regardless of the skipped residue.

This is the **deduction** the design-of-record routes to "the contest/deduction
game": ``entails`` answers "does G follow from the theory M?", the question the peel
is not built to answer, and the one that makes *ontology-as-M* real for a T-box.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from egi_core_dau import (
    RelationalGraphWithCuts,
    create_edge,
    create_vertex,
)
from model_materialization import materialize_egi

# A line-of-identity key in a query: ("c", label) constant / ("g", vertex_id) generic.
Key = Tuple[str, str]
# A query atom: (relation_name, (key, ...)) in nu-order.
QAtom = Tuple[str, Tuple[Key, ...]]


@dataclass(frozen=True)
class FrozenWitness:
    """A fresh constant minted for one of G's universally-quantified lines."""

    constant: str        # the fresh individual (e.g. "__w1")
    display: str = ""     # how the line appears in G (for the transcript)


@dataclass
class TheoryQueryResult:
    """Whether the universal G is a theorem of the theory M — and how it was decided."""

    applicable: bool                 # was G a single range-restricted Horn universal?
    verdict: str = "unknown"         # "true" | "false" | "unknown"
    body_egif: str = ""              # the antecedent B (display)
    head_egif: str = ""              # the consequent H (display)
    witnesses: List[FrozenWitness] = field(default_factory=list)
    derived: List[str] = field(default_factory=list)   # head atoms found in M ∪ {B}
    missing: List[str] = field(default_factory=list)   # head atoms not derivable
    skipped_in_theory: int = 0       # non-Horn axioms M had to leave behind
    detail: str = ""

    @property
    def holds(self) -> bool:
        return self.verdict == "true"

    @property
    def summary(self) -> str:
        if not self.applicable:
            return self.detail or "not a universal Horn query"
        v = self.verdict.upper()
        if self.verdict == "true":
            return f"{v} — G is a theorem of M (frozen witness derives the head)"
        if self.verdict == "false":
            return f"{v} — not a theorem (head underivable; M is wholly Horn)"
        return (f"{v} — the Horn fragment doesn't prove G; "
                f"{self.skipped_in_theory} non-Horn axiom(s) might")


# ---------------------------------------------------------------------------
# Recognising a universal Horn query  ~[ B ~[ H ] ]
# ---------------------------------------------------------------------------

def _as_universal_horn(
    g: RelationalGraphWithCuts,
) -> Optional[Tuple[List[QAtom], List[QAtom]]]:
    """If ``g`` is a single sheet-level range-restricted Horn scroll ``~[ B ~[ H ] ]``,
    return ``(body_atoms, head_atoms)``; otherwise ``None``.

    Mirrors ``model_materialization``'s Horn classification: exactly one sheet-level
    cut, exactly one cut nested in it (the head), no deeper negation, and every line
    of identity in the head also occurring in the body (no fresh existential head).
    """
    vmap = {v.id: v for v in g.V}
    edge_ids = {e.id for e in g.E}
    cut_ids = {c.id for c in g.Cut}

    sheet_cuts = [x for x in g.area.get(g.sheet, ()) if x in cut_ids]
    sheet_edges = [x for x in g.area.get(g.sheet, ()) if x in edge_ids]
    # A clean universal is one scroll on an otherwise-empty sheet.
    if len(sheet_cuts) != 1 or sheet_edges:
        return None
    c1 = sheet_cuts[0]
    inner = [x for x in g.area.get(c1, ()) if x in cut_ids]
    if len(inner) != 1:
        return None
    c2 = inner[0]
    if any(x in cut_ids for x in g.area.get(c2, ())):
        return None  # negation in the head — not Horn

    def keyv(vid: str) -> Key:
        v = vmap[vid]
        return ("c", v.label) if (not v.is_generic and v.label) else ("g", vid)

    def atoms_in(area_id: str) -> List[QAtom]:
        return [
            (g.get_relation_name(eid), tuple(keyv(v) for v in g.nu[eid]))
            for eid in g.area.get(area_id, ()) if eid in edge_ids
        ]

    body = atoms_in(c1)
    head = atoms_in(c2)
    if not body or not head:
        return None
    body_gen = {k for _r, args in body for k in args if k[0] == "g"}
    head_gen = {k for _r, args in head for k in args if k[0] == "g"}
    if not head_gen <= body_gen:
        return None  # range-restriction: a fresh individual in the head
    return body, head


# ---------------------------------------------------------------------------
# The decision: freeze a witness, materialize M ∪ {B}, check H
# ---------------------------------------------------------------------------

def _atom_egif(rel: str, args: Tuple[str, ...]) -> str:
    quoted = "".join(' "' + a + '"' for a in args)
    return f"({rel}{quoted})"


def entails(
    theory: RelationalGraphWithCuts,
    query: RelationalGraphWithCuts,
) -> TheoryQueryResult:
    """Decide whether the universal ``query`` is a theorem of the theory ``theory``.

    ``theory`` is M as authored (facts + Horn rules — e.g. a corpus ontology UoD);
    ``query`` is a candidate universal ``~[ B ~[ H ] ]`` (a subsumption, a typing
    rule).  Returns a :class:`TheoryQueryResult`; ``applicable`` is False when the
    query is not a range-restricted Horn universal (the caller should fall back to the
    ordinary peel).
    """
    from world_scroll import m_view

    # A world-scrolled theory (the validity discipline) is read through its
    # antecedent area — the frozen witness below must land at M's own level,
    # not at depth 0 beside the scroll. Legacy sheet-level theories unchanged.
    theory = m_view(theory)

    parsed = _as_universal_horn(query)
    if parsed is None:
        return TheoryQueryResult(
            applicable=False,
            detail="query is not a single range-restricted Horn universal "
                   "~[ B ~[ H ] ]; use the ordinary peel",
        )
    body, head = parsed

    # Freeze: a fresh constant per generic line of identity in the body.
    fresh: Dict[Key, str] = {}
    witnesses: List[FrozenWitness] = []
    for _rel, args in body:
        for k in args:
            if k[0] == "g" and k not in fresh:
                name = f"__w{len(fresh) + 1}"
                fresh[k] = name
                witnesses.append(FrozenWitness(constant=name))

    def ground(k: Key) -> str:
        return k[1] if k[0] == "c" else fresh[k]

    frozen_body = [
        _atom_egif(rel, tuple(ground(k) for k in args)) for rel, args in body
    ]
    head_atoms = [
        (rel, tuple(ground(k) for k in args)) for rel, args in head
    ]
    body_egif = " ".join(frozen_body)
    head_egif = " ".join(_atom_egif(rel, args) for rel, args in head_atoms)

    # Materialize M ∪ {frozen B}: run the theory's rules over the arbitrary witness.
    # Build the combined graph **directly** (not via EGIF text) so a CLIF/COLORE theory
    # carrying names EGIF can't round-trip (e.g. ``Warm-blooded``) still materializes.
    combined = theory
    vid_of: Dict[str, str] = {}
    for rel, args in body:
        for k in args:
            g = ground(k)
            if g not in vid_of:
                v = create_vertex(label=g, is_generic=False)
                combined = combined.with_vertex(v)
                vid_of[g] = v.id
    for rel, args in body:
        combined = combined.with_edge(
            create_edge(), tuple(vid_of[ground(k)] for k in args), rel)
    facts_egi, report = materialize_egi(combined)

    # Check H over the same witnesses against the materialized facts.
    present = {
        (facts_egi.get_relation_name(eid),
         tuple(_label(facts_egi, v) for v in facts_egi.nu[eid]))
        for eid in facts_egi.area.get(facts_egi.sheet, ())
        if eid in {e.id for e in facts_egi.E}
    }
    derived, missing = [], []
    for rel, args in head_atoms:
        disp = _atom_egif(rel, args)
        (derived if (rel, args) in present else missing).append(disp)

    skipped = len(report.skipped)
    if not missing:
        verdict, detail = "true", "frozen witness derives the head — a theorem of M"
    elif skipped == 0:
        verdict, detail = "false", "head underivable and M is wholly Horn — not a theorem"
    else:
        verdict, detail = ("unknown",
                           "head underivable from M's Horn fragment; "
                           f"{skipped} non-Horn axiom(s) left to the contest game")

    return TheoryQueryResult(
        applicable=True,
        verdict=verdict,
        body_egif=body_egif,
        head_egif=head_egif,
        witnesses=witnesses,
        derived=derived,
        missing=missing,
        skipped_in_theory=skipped,
        detail=detail,
    )


def _label(egi: RelationalGraphWithCuts, vid: str) -> str:
    v = next((x for x in egi.V if x.id == vid), None)
    if v is not None and not v.is_generic and v.label:
        return v.label
    return vid
