"""The first *live* source — Wikidata structured claims.

Design-of-record: ``docs/AUTOMATED_ENDOPOREUTIC_GAME.md`` §4b/§10. Wikidata is the cheapest,
cleanest real source to plug into the automated Endoporeutic Game because its dispute structure
is already *structured* — no NL parsing:

  * a **statement** = an item + a property + a value (a ground binary fact);
  * a **reference** = provenance — a referenced statement is a ``reliable_source`` resolution, an
    unreferenced one a bare ``consensus``;
  * a **rank** = the resolution outcome — ``preferred``/``normal`` stand; ``deprecated`` is a
    value the community keeps on record as *wrong* (a **relinquishment** — settled False);
  * **competing values** for one (item, property) = the contestation (an ``edit war`` proxy).

This maps almost 1:1 onto ``wiki_dispute_membrane.WikiDispute``, so a Wikidata slice drives the
whole pipeline unchanged — the ``LiveRunner`` (paced, bounded, checkpointed), the
``WikiDisputeFeed``, and the §6 dispute-learning (``mechanism_principles`` etc.). Adding the
opt-in ``agon_evolution.ContradictionAgent`` to the panel lets a **deprecated** statement
actually *retract* the superseded value, so a reliable-source correction overturns a bare one —
and ``mechanism_principles`` then differentiates *durable* (referenced) from non-durable
(deprecated/bare) knowledge.

The network boundary is a single injectable ``fetch`` callable, so **CI runs entirely offline**
on recorded fixtures; :func:`wbgetentities_fetch` is the real Wikidata call (stdlib ``urllib``,
no dependency, no auth) and is used only when wired by a caller. Additive, geometry-free,
imports no protected module's internals. Correspondence-not-truth holds: Wikidata is low-warrant
input; nothing auto-promotes to the attested corpus.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence

from wiki_dispute_membrane import Resolution, WikiDispute, WikiEdit


@dataclass
class WikidataStatement:
    """One Wikidata statement, flattened. ``item`` and ``prop`` are human-readable labels (or
    Q/P ids); ``value`` is the stringified value; ``rank`` ∈ preferred/normal/deprecated;
    ``referenced`` is whether it carries at least one reference (its provenance)."""
    item: str
    prop: str
    value: str
    rank: str = "normal"
    referenced: bool = False


_SAFE = re.compile(r"[^0-9a-z]+")


def _relation_name(prop: str) -> str:
    """A property label → an EGIF-safe lowercase relation name (``date of birth`` → ``date_of_birth``)."""
    return _SAFE.sub("_", prop.strip().lower()).strip("_") or "prop"


def _const(value: str) -> str:
    """A value/item → an EGIF constant token (quotes stripped so the string stays well-formed)."""
    return value.replace('"', "").replace("\\", "").strip() or "?"


def statement_egif(s: WikidataStatement) -> str:
    """A statement as a ground binary fact ``(prop "item" "value")``."""
    return f'({_relation_name(s.prop)} "{_const(s.item)}" "{_const(s.value)}")'


def _mechanism(referenced: bool) -> str:
    return "reliable_source" if referenced else "consensus"


def statements_to_disputes(
    statements: Sequence[WikidataStatement],
) -> List[WikiDispute]:
    """Group statements by (item, property) into :class:`WikiDispute`s — one per (item, property),
    its competing values the contestation. A deprecated statement becomes a *relinquishment*
    (settled False, scribed as a negation so the ``ContradictionAgent`` retracts the value); a
    preferred/normal one stands, with its mechanism set by whether it is referenced."""
    groups: Dict[tuple, List[WikidataStatement]] = {}
    order: List[tuple] = []
    for s in statements:
        key = (s.item, s.prop, s.value, s.rank, s.referenced)  # one dispute per distinct statement
        pair = (s.item, s.prop)
        groups.setdefault(key, []).append(s)
        if key not in order:
            order.append(key)

    # contestation: how many distinct values compete for each (item, property)
    competing: Dict[tuple, int] = {}
    for (item, prop, value, _rank, _ref) in order:
        competing[(item, prop)] = competing.get((item, prop), 0) + 1

    disputes: List[WikiDispute] = []
    for (item, prop, value, rank, referenced) in order:
        s = WikidataStatement(item, prop, value, rank, referenced)
        egif = statement_egif(s)
        reverts = max(0, competing[(item, prop)] - 1)   # >1 competing value ⇒ contested
        edits = [WikiEdit("wikidata", True)] + [WikiEdit("contested", False)] * reverts
        if rank == "deprecated":
            # a value kept on record as wrong — relinquish it (scribed as a denial)
            disputes.append(WikiDispute(
                egif, edits, Resolution("deprecated", False), world_egif=f"~[ {egif} ]"))
        else:
            disputes.append(WikiDispute(
                egif, edits, Resolution(_mechanism(referenced), True)))
    return disputes


# --------------------------------------------------------------------------- #
# The live source                                                             #
# --------------------------------------------------------------------------- #

class WikidataSource:
    """A live source of Wikidata disputes. ``fetch_batches`` is an iterable of *polls*; each poll
    yields a list of :class:`WikidataStatement` (from the injected callable — a real API call, or
    a fixture in CI). Each poll is converted to a batch of :class:`WikiDispute`s. Implements the
    ``live_runner.LiveSource`` socket; pair with ``feed_factory=WikiDisputeFeed``."""

    def __init__(self, polls: Sequence[Sequence[WikidataStatement]]):
        self._polls = [list(p) for p in polls]
        self._i = 0

    @classmethod
    def from_fetch(cls, fetch: Callable[[], Sequence[WikidataStatement]], *, polls: int):
        """Build a source that calls ``fetch`` once per poll for ``polls`` polls (a live adapter
        supplies ``fetch``; each call returns the statements available now)."""
        return cls([list(fetch()) for _ in range(polls)])

    def fetch(self) -> Sequence[WikiDispute]:
        if self._i >= len(self._polls):
            return []
        batch = statements_to_disputes(self._polls[self._i])
        self._i += 1
        return batch

    def exhausted(self) -> bool:
        return self._i >= len(self._polls)


# --------------------------------------------------------------------------- #
# The real Wikidata call — stdlib only, no auth; NOT exercised in CI          #
# --------------------------------------------------------------------------- #

def wbgetentities_fetch(
    entity_ids: Sequence[str],
    *,
    lang: str = "en",
    endpoint: str = "https://www.wikidata.org/w/api.php",
    timeout: float = 20.0,
) -> List[WikidataStatement]:  # pragma: no cover - network; wire it, don't unit-test it
    """The real Wikidata read: ``wbgetentities`` for the given Q-ids, flattened to
    :class:`WikidataStatement`. Public, no auth, no dependency (``urllib``). Value stringifying
    is best-effort (entity-id → its id, time → the time string, quantity → amount, string →
    value). Property/value entity ids are left as ids unless a label lookup is added by the
    caller. Be polite: batch ids, cache, and pace via ``LiveRunConfig.min_interval_s``."""
    import json
    import urllib.parse
    import urllib.request

    q = urllib.parse.urlencode({
        "action": "wbgetentities", "ids": "|".join(entity_ids),
        "props": "claims", "format": "json", "languages": lang,
    })
    with urllib.request.urlopen(f"{endpoint}?{q}", timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    def _value(snak) -> Optional[str]:
        if snak.get("snaktype") != "value":
            return None
        dv = snak.get("datavalue", {})
        v = dv.get("value")
        t = dv.get("type")
        if t == "wikibase-entityid":
            return v.get("id")
        if t == "time":
            return v.get("time")
        if t == "quantity":
            return v.get("amount")
        if t == "monolingualtext":
            return v.get("text")
        return v if isinstance(v, str) else json.dumps(v, sort_keys=True)

    out: List[WikidataStatement] = []
    for qid, entity in (data.get("entities") or {}).items():
        for pid, claims in (entity.get("claims") or {}).items():
            for claim in claims:
                val = _value(claim.get("mainsnak", {}))
                if val is None:
                    continue
                out.append(WikidataStatement(
                    item=qid, prop=pid, value=val,
                    rank=claim.get("rank", "normal"),
                    referenced=bool(claim.get("references")),
                ))
    return out


__all__ = [
    "WikidataStatement", "statement_egif", "statements_to_disputes",
    "WikidataSource", "wbgetentities_fetch",
]
