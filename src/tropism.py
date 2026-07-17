"""Tropism — the player's directed re-engagement with its source (increment 1: the warm-set
re-poll).

Design-of-record: ``docs/AUTOMATED_ENDOPOREUTIC_GAME.md`` §13 (drafted + affirmed 2026-07-02),
mandated empirically by runs 1–2 (RUN_2_LOG F2′): both passive membranes — the crawl (settled
surface) and the change stream (novelty frontier) — **never revisit** an entity, so mechanism
durability (P2) was vacuous twice. *Ingestion alone cannot test durability; only directed
re-engagement can.* The first tropism is the humblest one: **re-check what you hold.**

Placement (§4d made structural): tropism belongs to the **player — not to M and not to the
source**. :class:`WarmSetTropism` is a policy the runner consults at each poll boundary; it reads
the player's own state (M's standing facts + the disuse ledger + the run's label cache) and emits
the next re-reaches. The sources stay dumb fetchers and gain exactly one seam
(``RotatingWikidataSource.inject`` — front-of-queue, ``_seen``-exempt: a deliberate re-reach is
not a crawl duplicate).

What this must NOT do (§7 floor): the re-poll's aim is to **exercise the durability of settled
habits**, never to verify M against the world. A re-delivered unchanged value is a non-revising
round (the habit holding); a deprecation/changed value arrives as a denial that now *meets its
standing target* — the P2 event, disposed by the existing panel and ``ContradictionAgent``. No
new referee, no disposition change, nothing auto-promotes.

Increment 1 implements only the **irritation pole**; the musement pole and the
horizon-as-register remain future, named, unbuilt. Additive, geometry-free, no protected-core
change, no new §3.3 obligation.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Mapping, Optional, Tuple, Union

from agon_evolution import atom_key
from egif_parser_dau import parse_egif
from eg_navigation import area_of
from wikidata_source import _PQ_ID, _const


def reverse_labels(
    id_to_label: Mapping[str, str],
) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    """Reverse the run's label cache (``id → label``) into the ``label → id`` map the warm set
    needs. Labels are compared as M actually carries them — through the same :func:`_const`
    normalization the scribed facts went through at ingestion — so a cache label with quotes or
    control characters still finds its fact. Returns ``(label_to_id, ambiguous)`` where
    ``ambiguous`` maps each colliding label (two+ ids, one label) to its sorted candidate ids —
    split out, never silently resolved (§13 decision 5: run 3 skips + counts them)."""
    by_label: Dict[str, List[str]] = {}
    for eid, label in id_to_label.items():
        by_label.setdefault(_const(label), []).append(eid)
    label_to_id = {lab: ids[0] for lab, ids in by_label.items() if len(ids) == 1}
    ambiguous = {lab: sorted(ids) for lab, ids in by_label.items() if len(ids) > 1}
    return label_to_id, ambiguous


class WarmSetTropism:
    """The warm-set re-poll policy: ``reaches(model_egif, ledger)`` → the Q-ids backing M's
    **standing** (sheet-level) facts, priority **decay-adjacent first** — the facts whose
    relations are nearest their ttl are re-checked *while the target still stands*, before decay
    erases the evidence-bearer. That ordering is what makes durability testable, and it ties the
    policy to the irritation pole rather than to truth-tracking.

    ``labels`` is the run's ``id → label`` cache (or a zero-arg callable returning it — the
    driver passes ``source.known_labels`` so the policy always reads the cache the run actually
    resolved with). ``k`` is the warm-slot budget per poll: the driver sets it to
    ``warm_fraction × chunk_size``, so injecting ``k`` ids front-of-queue makes the next poll's
    chunk ``k`` warm + the remainder fresh — the economy-of-research mix.

    A fact's entity is its **item** (first argument by :func:`wikidata_source.statement_egif`
    construction). An item still bearing a bare Q-id is already an id; an ambiguous label is
    skipped and counted (``ambiguous_skipped``); a label the cache cannot reverse at all is
    skipped and counted (``unmapped_skipped``) — counted either way, never silent (the P1″
    debugging surface: redundancy ≈ 0 at warm_fraction 0.5 means the labels are not reversing
    or the ids are not reaching the fetch)."""

    def __init__(
        self,
        labels: Union[Mapping[str, str], Callable[[], Mapping[str, str]]],
        k: int = 4,
    ):
        self._labels = labels
        self._k = k
        self.ambiguous_skipped = 0     # distinct ambiguous labels skipped, cumulative
        self.unmapped_skipped = 0      # distinct irreversible labels skipped, cumulative
        self.emitted = 0               # warm ids emitted, cumulative

    def _label_map(self) -> Mapping[str, str]:
        return self._labels() if callable(self._labels) else self._labels

    def reaches(self, model_egif: str, ledger=None, k: Optional[int] = None) -> List[str]:
        """The next warm re-reaches. ``ledger`` is the runner's cross-segment
        :class:`agon_evolution.UsageLedger` (or ``None`` — then uniform over held entities,
        ordered deterministically): a fact's priority is its **atom's** last-delivered round,
        oldest first = decay-adjacent first — atom-precise since the atom-level decay rulebook
        (2026-07-03: re-check the *fact* nearest its ttl, not the name; a name-keyed entry from
        an older ledger still reads as a fallback). An entity backing several facts takes its
        most decay-adjacent one. Returns at most ``k`` distinct Q-ids."""
        budget = self._k if k is None else k
        if not model_egif or budget <= 0:
            return []
        from world_scroll import m_view
        egi = m_view(parse_egif(model_egif))   # M's standing facts (sweep #2)
        label_to_id, ambiguous = reverse_labels(self._label_map())
        last = ledger.snapshot() if ledger is not None else {}

        best: Dict[str, int] = {}                   # entity id → most decay-adjacent last-use
        skipped_ambiguous: set = set()
        skipped_unmapped: set = set()
        for edge in egi.E:
            if edge.id not in egi.rel or area_of(egi, edge.id) != egi.sheet:
                continue                            # standing facts only — laws/cuts are not re-reached
            args = egi.nu.get(edge.id, ())
            if not args:
                continue
            item = egi.get_vertex(args[0])          # the entity whose statement this is
            if item.is_generic or item.label is None:
                continue
            if _PQ_ID.match(item.label):
                entity = item.label                 # an unresolved id is already an id
            elif item.label in label_to_id:
                entity = label_to_id[item.label]
            elif item.label in ambiguous:
                skipped_ambiguous.add(item.label)   # §13 decision 5: skip + count
                continue
            else:
                skipped_unmapped.add(item.label)
                continue
            if not entity.startswith("Q"):
                continue                            # only entities are re-fetchable
            akey = atom_key(egi.rel[edge.id],
                            [egi.get_vertex(v).label for v in args])
            last_used = last.get(akey, last.get(egi.rel[edge.id], 0))
            if entity not in best or last_used < best[entity]:
                best[entity] = last_used
        self.ambiguous_skipped += len(skipped_ambiguous)
        self.unmapped_skipped += len(skipped_unmapped)
        # oldest last-use first (nearest decay); entity id breaks ties deterministically
        ordered = sorted(best, key=lambda e: (best[e], e))[:budget]
        self.emitted += len(ordered)
        return ordered


__all__ = ["WarmSetTropism", "reverse_labels"]
