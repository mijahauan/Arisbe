"""Reliability derived, never stored.

The socialization sitting's §6a ruling (2026-08-01): reliability is not a
standing property of a peer and is **no field anywhere**. It is recomputed from
the record's own resolution history — how a source's contributions stood across
the branching DAG — which makes it *index over ink*: re-checkable forever, and
unable to go stale the way a cached number does.

That last property answers the sitting's §3 in the one place it can be answered
internally. A stored reliability number is exactly a pre-coordinated codebook:
it cannot report its own drift. A reliability *recomputed from resolution
history* carries its decoder with it, so a change in what a source is worth
shows up as a changed computation rather than as a stale constant nobody
re-checks.

**Two guards, both from rulings.**

*No scalar.* :class:`SourceStanding` carries counts and exposes no aggregate —
no ``score``, no ``ratio``, no ``net``. This is ``THE_MEASURE_OF_KNOWLEDGE``'s
vector guard, and it is also the re-measurement pass's hard-won rule: a derived
scalar invites a gate, and ``net_score`` was measured rising in *both*
directions of the thing it was meant to gate. A caller wanting a comparison
states it on the components.

*Address-blind.* Examination VIII, from the author's prophet-without-honour
case: provenance and legitimacy run independently of network intimacy and
sometimes inversely. Nothing here consults reach, proximity, or contact
frequency — there is no parameter by which it could — so legitimacy cannot
collapse into proximity even in a world where near contact is cheap.

Geometry-free and unprotected. Reads :mod:`notion_provenance`; the dependency
never runs the other way.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Tuple

from model_materialization import materialize_egi
from modal_query import necessarily, possibly
from notion_provenance import ProvenanceRecord, provenance_records
from tomos_service import TransformationChain
from world_scroll import m_view

Atom = Tuple[str, Tuple[str, ...]]


@dataclass(frozen=True)
class SourceStanding:
    """What the record says about one source — counts only, never a verdict.

    ``relation`` is Examination VII ruling 1's **domain index** at the
    granularity the general machinery has, and the granularity ``Unit.peers``
    already uses (per-author, per-relation), so a later migration is
    like-for-like rather than a redesign. ``None`` means *across all domains*,
    which is a sum of counts and still not a score."""

    source: str
    relation: Optional[str]
    contributed: int
    affirmed: int
    necessary: int
    possible: int
    absent: int


def _derived_atoms(egi) -> FrozenSet[Atom]:
    """The ground atoms M holds once forward-chained — the notions actually
    standing, derived ones included."""
    facts, _report = materialize_egi(m_view(egi))
    atoms = set()
    for eid in facts.rel:
        labels = [facts.get_vertex(v).label for v in facts.nu[eid]]
        if all(l is not None for l in labels):
            atoms.add((facts.rel[eid], tuple(labels)))
    return frozenset(atoms)


def _holds(notion_atoms: FrozenSet[Atom]):
    """Predicate: *this state derives every atom of the notion*.

    ``modal_query.scribes_relation`` is too coarse (any atom of that relation)
    and ``equals_graph`` too strict (whole-sheet identity), so the reader
    supplies its own. An empty notion never counts as standing — otherwise a
    non-ground notion would read as necessary everywhere for free."""
    if not notion_atoms:
        return lambda egi: False
    return lambda egi: notion_atoms <= _derived_atoms(egi)


def _all_records(chain: TransformationChain) -> Dict[Tuple[str, str],
                                                     ProvenanceRecord]:
    """Every provenance record anywhere in the DAG, keyed by ``(source, key)``.

    Read across **all** states, not off the last one. What a source contributed
    is everything it ever contributed on any trajectory; reading the final
    state alone makes a source's record depend on the order branches happened
    to be written, which is not a fact about the source. ``affirmed`` is
    likewise *affirmed anywhere* — an affirmation on one branch is a real event
    even if a sibling never made it."""
    merged: Dict[Tuple[str, str], ProvenanceRecord] = {}
    for state in chain.states.values():
        for rec in provenance_records(state):
            ident = (rec.source, rec.key)
            prior = merged.get(ident)
            if prior is None:
                merged[ident] = rec
            elif rec.affirmed and not prior.affirmed:
                merged[ident] = rec
    return merged


def _records_for(chain: TransformationChain, source: str,
                 relation: Optional[str]) -> List[ProvenanceRecord]:
    return [r for r in _all_records(chain).values()
            if r.source == source
            and (relation is None or relation in r.relations)]


def standing_of(chain: TransformationChain, *, source: str,
                relation: Optional[str] = None,
                over: str = "leaves") -> SourceStanding:
    """How this source's contributions stood, recomputed from the chain.

    ``necessary`` / ``possible`` / ``absent`` compose the existing ◇/□ machinery
    over each contributed notion: □ = it derives on every reachable world, ◇ =
    on some but not all, absent = nowhere. A recorded-but-unaffirmed notion
    reads ``absent`` — *held* is not *held true*, which is the conditional
    form's whole point."""
    records = _records_for(chain, source, relation)
    counts = {"necessary": 0, "possible": 0, "absent": 0}
    for rec in records:
        predicate = _holds(rec.notion_atoms)
        if necessarily(chain, predicate, over=over).holds:
            counts["necessary"] += 1
        elif possibly(chain, predicate, over=over).holds:
            counts["possible"] += 1
        else:
            counts["absent"] += 1
    return SourceStanding(
        source=source, relation=relation,
        contributed=len(records),
        affirmed=sum(1 for r in records if r.affirmed),
        **counts)


def standings(chain: TransformationChain, *, relation: Optional[str] = None,
              over: str = "leaves") -> List[SourceStanding]:
    """Every source appearing in the record, each read independently.

    A list, deliberately — not a ranking. Ordering by any component would be
    the scalar the vector guard forbids, wearing a sort key."""
    sources = sorted({src for src, _key in _all_records(chain)})
    return [standing_of(chain, source=s, relation=relation, over=over)
            for s in sources]


__all__ = ["SourceStanding", "standing_of", "standings"]
