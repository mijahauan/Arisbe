"""Provenance in the ink: who provided, or whence arrived, a notion.

The author's ruled shape (2026-08-01) — **the antecedent is the provenance**:

    ~[ (provided_by "<source>" "<key>") ~[ <the notion> ] ]

read as *given that `<source>` provided this, the notion*. This is the
socialization sitting's §5.1 resolution (INS in verso, IT+ into sub-recto —
the received world held as a conditional whose antecedent is what was given)
with the provenance atom standing where the bare ``A`` stood. Nothing
contingent stands at depth 0, and the notion never claims the standing a
record would have had to license.

**Affirming** the antecedent is a second cell, the bare atom
``(provided_by "<source>" "<key>")``. Assert it and the notion *derives*,
through the Horn forward-chainer in :mod:`model_materialization`, which
already reads ``~[ B ~[ H ] ]``. No new inference machinery. Retract the
affirmation and the notion goes with it, because it was never stored.

**Plurality falls out literally**: two sources contributing one notion make
two conditionals with distinct keys, and the notion is derivable from either.
That is the sitting's §5.2 (a second authoritative adult) and corroboration —
one mechanism, one implementation.

Named apart from :mod:`provenance`, which is the unrelated bibliographic
bundle (theorem / EG-derivation / calculus layers, sidecar-persisted).

Geometry-free (no layout import, so no §3.3 obligation) and unprotected.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import FrozenSet, List, Tuple

from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from egi_core_dau import ElementID, RelationalGraphWithCuts
from world_scroll import enlarge_m, m_view

PROVIDED_BY = "provided_by"
"""The provenance relation: ``(provided_by "<source>" "<key>")``. Arity two —
who, and which notion. Deliberately *not* carrying the notion inline: the
notion is the conditional's consequent, standing beside the key as its own
decoder."""

_KEY_CHARS = 12
"""Length of the hex digest carried in the key. 12 hex chars = 48 bits, which
makes an accidental collision between two distinct notions in one model
negligible while keeping the constant short enough to read in a drawn graph
(the occlusion wall `oracle_notes` measured at 52/53 chars is far above this)."""


def notion_key(notion: RelationalGraphWithCuts) -> str:
    """A deterministic, content-derived id for ``notion``.

    **Load-bearing, not cosmetic** (design spec §5.2). With a generic ``*p`` in
    the antecedent instead of this constant, one source affirming one thing
    fires *every* conditional it ever contributed — measured: a notion never
    affirmed was derived anyway. The key is what makes the antecedent
    discriminate.

    Keyed on the *canonical* EGIF, so the same graph written two ways is one
    notion and a re-parse never mints a second record."""
    canonical = generate_egif(notion).strip()
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"n_{digest[:_KEY_CHARS]}"


@dataclass(frozen=True)
class ProvenanceRecord:
    """One conditional read back out of the ink.

    ``relations`` is Examination VII's **domain index** at the granularity the
    general machinery has — the relation names the notion uses. It is also how
    ``Unit.peers`` already keys (per-author, per-relation), so the eventual
    C-series migration is like-for-like rather than a redesign."""

    source: str
    key: str
    relations: FrozenSet[str]
    affirmed: bool
    cut_id: ElementID


def record_provenance(m: RelationalGraphWithCuts, *, source: str,
                      notion_egif: str) -> Tuple[RelationalGraphWithCuts, str]:
    """Record that ``source`` provided ``notion_egif`` — one licensed
    INS-of-cell of the conditional. Returns ``(graph, key)``.

    The notion is **held, not asserted**: it derives only once the antecedent
    is affirmed (:func:`affirm_provenance`)."""
    key = notion_key(parse_egif(notion_egif))
    cell = f'~[ ({PROVIDED_BY} "{source}" "{key}") ~[ {notion_egif.strip()} ] ]'
    return enlarge_m(m, cell), key


def affirm_provenance(m: RelationalGraphWithCuts, *, source: str,
                      key: str) -> RelationalGraphWithCuts:
    """Affirm that the arrival happened — one licensed INS-of-cell of the bare
    atom. The notion then *derives*; nothing stores it."""
    return enlarge_m(m, f'({PROVIDED_BY} "{source}" "{key}")')


def _atom_labels(g: RelationalGraphWithCuts, eid: ElementID) -> List[str]:
    return [g.get_vertex(v).label for v in g.nu[eid]]


def _relations_within(g: RelationalGraphWithCuts,
                      area: ElementID) -> FrozenSet[str]:
    """Relation names scribed anywhere inside ``area``, recursively."""
    names = set()
    for eid in g.rel:
        ctx = g.get_context(eid)
        while ctx is not None and ctx != g.sheet:
            if ctx == area:
                names.add(g.rel[eid])
                break
            ctx = g.get_context(ctx)
    return frozenset(names)


def provenance_records(m: RelationalGraphWithCuts) -> List[ProvenanceRecord]:
    """Every provenance conditional standing in M, with whether its antecedent
    has been affirmed. A pure read — nothing is cached anywhere."""
    held = m_view(m)
    affirmations = {
        (labels[0], labels[1])
        for eid in held.rel
        if held.rel[eid] == PROVIDED_BY
        and held.get_context(eid) == held.sheet
        and len(labels := _atom_labels(held, eid)) == 2
    }

    records = []
    for cut_id in (c.id for c in held.Cut
                   if held.get_context(c.id) == held.sheet):
        inner = [e for e in held.get_area(cut_id) if e in {c.id for c in held.Cut}]
        edges = [e for e in held.get_area(cut_id) if e in held.rel]
        if len(inner) != 1 or len(edges) != 1:
            continue
        (eid,), (consequent,) = edges, inner
        if held.rel[eid] != PROVIDED_BY:
            continue
        labels = _atom_labels(held, eid)
        if len(labels) != 2 or any(l is None for l in labels):
            continue
        source, key = labels
        records.append(ProvenanceRecord(
            source=source, key=key,
            relations=_relations_within(held, consequent),
            affirmed=(source, key) in affirmations,
            cut_id=cut_id))
    return sorted(records, key=lambda r: (r.source, r.key))


__all__ = ["PROVIDED_BY", "ProvenanceRecord", "notion_key",
           "record_provenance", "affirm_provenance", "provenance_records"]
