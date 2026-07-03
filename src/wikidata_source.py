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
from dataclasses import asdict, dataclass
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Set, Tuple

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
    """A value/item → an EGIF constant token: quotes/backslashes stripped and control
    characters (newlines, tabs — fresh human edits carry them; found live 2026-07-02, run 2)
    replaced by spaces, so the string stays well-formed and single-line."""
    cleaned = "".join(
        c if c.isprintable() else " "
        for c in value.replace('"', "").replace("\\", ""))
    return cleaned.strip() or "?"


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
# P/Q id → label resolution (legibility)                                      #
# --------------------------------------------------------------------------- #
#
# ``wbgetentities`` returns entity-valued fields as bare P/Q ids, and an M full of
# ``(p31 "Q42" "Q5")`` is unreadable through the audit lens — legibility is the point of the
# whole system. The pure half (collect + substitute) is offline-testable; only
# :func:`wblabels_fetch` touches the network.

_PQ_ID = re.compile(r"^[PQ]\d+$")


def collect_ids(statements: Sequence[WikidataStatement]) -> List[str]:
    """The distinct P/Q ids appearing in the statements (item, property, value), in first-seen
    order — the lookup set for :func:`wblabels_fetch`."""
    seen: set = set()
    out: List[str] = []
    for s in statements:
        for token in (s.item, s.prop, s.value):
            if _PQ_ID.match(token) and token not in seen:
                seen.add(token)
                out.append(token)
    return out


def unresolved_fraction(statements: Sequence[WikidataStatement]) -> float:
    """The **legibility tripwire** (§10): the fraction of the statements' (item, property,
    value) tokens still bare P/Q ids after label resolution. 0.0 = fully legible; a spike
    means resolution is silently degrading — exactly how the 2024 ``mul``-label change
    manifested (labels stopped resolving and nothing complained). Surface it per poll (the
    source records it; see :attr:`WikidataSource.legibility`) so a live run's digest stream
    shows the failure instead of M quietly filling with Q-ids. Empty input reads 0.0."""
    total = unresolved = 0
    for s in statements:
        for token in (s.item, s.prop, s.value):
            total += 1
            if _PQ_ID.match(token):
                unresolved += 1
    return (unresolved / total) if total else 0.0


def resolve_labels(
    statements: Sequence[WikidataStatement], labels: Mapping[str, str]
) -> List[WikidataStatement]:
    """The statements with P/Q ids replaced by their labels where known. An id with no label
    stays an id — honesty over legibility (never fabricate a name)."""
    return [
        WikidataStatement(
            item=labels.get(s.item, s.item),
            prop=labels.get(s.prop, s.prop),
            value=labels.get(s.value, s.value),
            rank=s.rank,
            referenced=s.referenced,
        )
        for s in statements
    ]


def wblabels_fetch(
    ids: Sequence[str],
    *,
    lang: str = "en",
    endpoint: str = "https://www.wikidata.org/w/api.php",
    timeout: float = 20.0,
) -> Dict[str, str]:  # pragma: no cover - network; wire it, don't unit-test it
    """Labels for P/Q ids via ``wbgetentities`` ``props=labels``, batched at 50 ids per request
    (the anonymous API cap). Asks for ``lang`` **and** ``mul`` — since 2024 an item whose name
    is language-independent (most person/place names) carries one ``mul`` label *instead of* an
    ``en`` one (Q42's "Douglas Adams" lives there; found live 2026-07-01). ``lang`` wins where
    both exist. Returns ``id → label``; an id with no label in either is absent
    (``resolve_labels`` then leaves it as the id)."""
    ids = [i for i in ids if _PQ_ID.match(i)]
    out: Dict[str, str] = {}
    for start in range(0, len(ids), 50):
        batch = ids[start:start + 50]
        data = _api_json({
            "action": "wbgetentities", "ids": "|".join(batch),
            "props": "labels", "format": "json", "languages": f"{lang}|mul",
        }, endpoint, timeout)
        for eid, entity in (data.get("entities") or {}).items():
            labels = entity.get("labels") or {}
            label = (labels.get(lang) or labels.get("mul") or {}).get("value")
            if label:
                out[eid] = label
    return out


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
        self.legibility: List[float] = []   # per-poll unresolved-id fraction (the tripwire)

    @classmethod
    def from_fetch(cls, fetch: Callable[[], Sequence[WikidataStatement]], *, polls: int):
        """Build a source that calls ``fetch`` once per poll for ``polls`` polls (a live adapter
        supplies ``fetch``; each call returns the statements available now)."""
        return cls([list(fetch()) for _ in range(polls)])

    def fetch(self) -> Sequence[WikiDispute]:
        if self._i >= len(self._polls):
            return []
        statements = self._polls[self._i]
        self.legibility.append(unresolved_fraction(statements))
        batch = statements_to_disputes(statements)
        self._i += 1
        return batch

    def exhausted(self) -> bool:
        return self._i >= len(self._polls)


# --------------------------------------------------------------------------- #
# The label cache — politeness across polls                                    #
# --------------------------------------------------------------------------- #

class LabelCache:
    """An in-memory ``id → label`` cache shared across a run's polls. A rotating frontier
    re-encounters the same property ids (P31, P569, …) every poll; without the cache every poll
    re-asks the API for them. ``lookup`` fetches only the ids not yet seen — including
    **negative caching** (an id the API returned no label for is not re-asked). ``fetched``
    counts ids actually sent to the API (the politeness accounting)."""

    def __init__(self, fetch: Callable[..., Dict[str, str]] = None):
        self._fetch = fetch if fetch is not None else wblabels_fetch
        self._labels: Dict[str, str] = {}
        self._no_label: Set[str] = set()
        self.fetched = 0

    def lookup(self, ids: Sequence[str]) -> Dict[str, str]:
        missing = [i for i in ids
                   if _PQ_ID.match(i) and i not in self._labels and i not in self._no_label]
        if missing:
            self.fetched += len(missing)
            got = self._fetch(missing)
            self._labels.update(got)
            self._no_label.update(i for i in missing if i not in got)
        return {i: self._labels[i] for i in ids if i in self._labels}


# --------------------------------------------------------------------------- #
# The poll record — every live poll persisted for offline replay              #
# --------------------------------------------------------------------------- #
#
# §11's determinism canary made real: a live run whose polls are recorded replays offline —
# ``WikidataSource(replay_polls(path))`` re-drives the identical trajectory, so "would the
# current code produce the same run?" is a cheap diff, not an argument.

def record_poll(path: str, statements: Sequence[WikidataStatement]) -> None:
    """Append one poll's (resolved) statements to ``path`` as a JSONL line."""
    import json
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps([asdict(s) for s in statements]) + "\n")


def replay_polls(path: str) -> List[List[WikidataStatement]]:
    """Read a :func:`record_poll` file back into polls — hand to ``WikidataSource`` to replay
    the recorded run offline."""
    import json
    polls: List[List[WikidataStatement]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                polls.append([WikidataStatement(**d) for d in json.loads(line)])
    return polls


def parseable_disputes(disputes: Sequence[WikiDispute]) -> Tuple[List[WikiDispute], int]:
    """The **parse gate** (never-poison, at the membrane): a dispute whose claim or scribed
    ground truth does not parse as EGIF must not reach the loop — one exotic string from a
    live source must never kill an unattended run (found live 2026-07-02: a URL value carrying
    ``#`` read as an EGIF comment and crashed run 2's fifth segment; the lexer is fixed too —
    this gate is the defense in depth). Returns ``(kept, dropped_count)`` — drops are counted
    by the caller, never silent."""
    from egif_parser_dau import parse_egif
    kept: List[WikiDispute] = []
    dropped = 0
    for d in disputes:
        try:
            parse_egif(d.claim_egif)
            parse_egif(d.ground_truth())
            kept.append(d)
        except Exception:
            dropped += 1
    return kept, dropped


def _cap_by_entity(
    statements: Sequence[WikidataStatement], cap: Optional[int]
) -> Tuple[List[WikidataStatement], int]:
    """The **hub-degree bound** shared by the live sources: keep at most ``cap`` statements
    per entity (an entity's M is a star graph and the checkpoint attest is super-linear in hub
    degree — the measured §10 finding). Returns ``(kept, dropped_count)`` — drops are counted
    by the caller, never silent."""
    if cap is None:
        return list(statements), 0
    kept: List[WikidataStatement] = []
    taken: Dict[str, int] = {}
    dropped = 0
    for s in statements:
        if taken.get(s.item, 0) < cap:
            taken[s.item] = taken.get(s.item, 0) + 1
            kept.append(s)
        else:
            dropped += 1
    return kept, dropped


# --------------------------------------------------------------------------- #
# The rotating frontier — run 1's live source                                  #
# --------------------------------------------------------------------------- #

class RotatingWikidataSource:
    """The **rotating-frontier** live source (run 1, §11): a queue of Q-ids consumed
    ``chunk_size`` per poll, fetched **lazily at poll time** — so the runner's pacing actually
    paces the API (``WikidataSource.from_fetch`` prefetches eagerly at construction and is not
    suitable for a live run). With ``crawl`` (the default) each poll **grows the frontier**:
    entity-valued statement values (Q-ids) not yet seen are enqueued for later polls, bounded
    by ``frontier_cap`` — ids dropped at the cap are *counted* (``frontier_dropped``), never
    silent. One :class:`LabelCache` serves the whole run; every poll's resolved statements are
    appended to ``record_path`` (offline replay) and its ``unresolved_fraction`` to
    ``legibility`` (the tripwire). ``fetch_ids`` is injectable — CI runs on fixtures; production
    wires the real ``wbgetentities_fetch(ids, with_labels=False)`` (labels resolve here, through
    the cache). ``save_state``/``load_state`` persist the frontier (queue, cursor, cache) so a
    resumed run continues its crawl instead of restarting from the seeds.

    ``per_entity_cap`` bounds how many statements one entity contributes per poll — the
    **hub-degree bound**: an M built from one entity's facts is a star graph (one individual
    shared by every atom), and the §3.3 attest at each checkpoint routes ligatures through a
    visibility graph that is super-linear in hub degree (measured 2026-07-02: ~0.3 s synthetic,
    ~28 s at a 25-fact star, ~452 s at 46). Capped statements are *counted*
    (``statements_dropped``), never silent."""

    def __init__(
        self,
        seed_ids: Sequence[str],
        *,
        chunk_size: int = 8,
        crawl: bool = True,
        frontier_cap: int = 400,
        per_entity_cap: Optional[int] = None,
        fetch_ids: Optional[Callable[[Sequence[str]], Sequence[WikidataStatement]]] = None,
        record_path: Optional[str] = None,
        label_fetch: Optional[Callable[..., Dict[str, str]]] = None,
    ):
        self._queue: List[str] = list(dict.fromkeys(seed_ids))
        self._seen: Set[str] = set(self._queue)
        self._i = 0
        self._chunk = chunk_size
        self._crawl = crawl
        self._cap = frontier_cap
        self._entity_cap = per_entity_cap
        self._fetch_ids = fetch_ids or (
            lambda ids: wbgetentities_fetch(ids, with_labels=False))
        self._record = record_path
        self._cache = LabelCache(label_fetch)
        self.legibility: List[float] = []
        self.frontier_dropped = 0
        self.statements_dropped = 0
        self.unparseable_dropped = 0
        self.injected = 0

    def inject(self, ids: Sequence[str]) -> None:
        """The tropism seam (§13): deliberately re-reach these entities at the **next poll**.
        Injected ids go front-of-queue and **bypass ``_seen``** — the whole point: ``_seen``
        exists to stop the *crawl* re-enqueueing what it already met, and a deliberate re-reach
        is not a crawl duplicate. Ids already pending ahead of the cursor are skipped (about to
        be reached anyway), non-Q tokens are ignored, and everything injected is counted
        (``injected``), never silent. The frontier cap does not apply — a warm re-reach is
        consumed next poll, not parked."""
        pending = set(self._queue[self._i:])
        fresh = [i for i in dict.fromkeys(ids)
                 if i.startswith("Q") and _PQ_ID.match(i) and i not in pending]
        if not fresh:
            return
        self._queue[self._i:self._i] = fresh
        self._seen.update(fresh)
        self.injected += len(fresh)

    def known_labels(self) -> Dict[str, str]:
        """The run's resolved ``id → label`` map — what the warm-set tropism reverses to
        recover entity ids from M's (label-carrying) facts. A copy; the cache stays private."""
        return dict(self._cache._labels)

    def fetch(self) -> Sequence[WikiDispute]:
        if self._i >= len(self._queue):
            return []
        ids = self._queue[self._i:self._i + self._chunk]
        self._i += len(ids)
        statements, dropped = _cap_by_entity(list(self._fetch_ids(ids)), self._entity_cap)
        self.statements_dropped += dropped
        if self._crawl:
            for s in statements:
                v = s.value
                if v.startswith("Q") and _PQ_ID.match(v) and v not in self._seen:
                    if len(self._queue) < self._cap:
                        self._seen.add(v)
                        self._queue.append(v)
                    else:
                        self.frontier_dropped += 1
        statements = resolve_labels(statements, self._cache.lookup(collect_ids(statements)))
        if self._record:
            record_poll(self._record, statements)
        self.legibility.append(unresolved_fraction(statements))
        disputes, bad = parseable_disputes(statements_to_disputes(statements))
        self.unparseable_dropped += bad
        return disputes

    def exhausted(self) -> bool:
        return self._i >= len(self._queue)

    # -- frontier persistence (the source half of a kill + resume) -------------
    def save_state(self, path: str) -> None:
        import json
        import os
        state = {
            "version": 1,
            "queue": self._queue, "cursor": self._i,
            "frontier_dropped": self.frontier_dropped,
            "statements_dropped": self.statements_dropped,
            "unparseable_dropped": self.unparseable_dropped,
            "injected": self.injected,
            "labels": self._cache._labels, "no_label": sorted(self._cache._no_label),
            "legibility": self.legibility,
        }
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=1)
        os.replace(tmp, path)

    @classmethod
    def load_state(cls, path: str, **kwargs) -> "RotatingWikidataSource":
        import json
        with open(path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
        src = cls(state["queue"], **kwargs)
        # verbatim, not through the constructor's dedup: a persisted warm re-reach (§13 inject)
        # is a deliberate duplicate and must survive the resume
        src._queue = list(state["queue"])
        src._seen = set(src._queue)
        src._i = state["cursor"]
        src.frontier_dropped = state.get("frontier_dropped", 0)
        src.statements_dropped = state.get("statements_dropped", 0)
        src.unparseable_dropped = state.get("unparseable_dropped", 0)
        src.injected = state.get("injected", 0)
        src._cache._labels.update(state.get("labels", {}))
        src._cache._no_label.update(state.get("no_label", []))
        src.legibility = list(state.get("legibility", []))
        return src


# --------------------------------------------------------------------------- #
# The change stream — run 2's live source (recentchanges)                     #
# --------------------------------------------------------------------------- #
#
# Run 1's finding (runs/RUN_1_LOG.md F2/F3): the crawl samples the wiki-world's *settled
# surface* (1 deprecated statement in 432 — contestation lives in the tail and the change
# stream), and a relinquishment only bites when its target still stands in the working set.
# The change stream fixes both at once: each poll asks which items were *just edited* and
# fetches those — so the sample skews to where the wiki-world is actively settling its
# disagreements, and an entity edited again is fetched again, meaning a deprecation arrives
# while the bare value it overturns may still stand in M (recency-selection IS the revisit).

def rc_ids(data: Dict) -> Tuple[List[str], Optional[str]]:
    """The pure half of the ``recentchanges`` read: the API payload → (ordered distinct
    item Q-ids, the newest timestamp seen — the next poll's continuation point). Non-item
    titles (properties, talk pages) are skipped; newest-first order is preserved."""
    ids: List[str] = []
    seen: Set[str] = set()
    newest: Optional[str] = None
    for rc in ((data.get("query") or {}).get("recentchanges") or []):
        if newest is None:
            newest = rc.get("timestamp")          # the API lists newest first
        title = rc.get("title", "")
        if title.startswith("Q") and _PQ_ID.match(title) and title not in seen:
            seen.add(title)
            ids.append(title)
    return ids, newest


class RecentChangesSource:
    """Run 2's live source — **the change stream**. Each poll: ``fetch_changes(since)`` (the
    real ``recentchanges`` call, or a fixture in CI) → :func:`rc_ids` → fetch those entities'
    statements → the same hub cap / label cache / poll record / legibility tripwire as the
    rotating source. **Never exhausts** (a live stream keeps flowing); the runner's stop
    conditions — ``max_seconds`` / ``max_rounds`` / ``stop_file`` — are the only ends, and an
    empty poll (nothing edited since last time) simply paces and polls again.
    ``save_state``/``load_state`` persist the continuation timestamp + counters so a resumed
    run picks up the stream where it stopped."""

    def __init__(
        self,
        *,
        ids_per_poll: int = 8,
        per_entity_cap: Optional[int] = 25,
        since: Optional[str] = None,
        fetch_changes: Optional[Callable[[Optional[str]], Dict]] = None,
        fetch_ids: Optional[Callable[[Sequence[str]], Sequence[WikidataStatement]]] = None,
        record_path: Optional[str] = None,
        label_fetch: Optional[Callable[..., Dict[str, str]]] = None,
    ):
        self._ids_per_poll = ids_per_poll
        self._entity_cap = per_entity_cap
        self._since = since
        self._fetch_changes = fetch_changes or (
            lambda since: recentchanges_fetch(since=since))
        self._fetch_ids = fetch_ids or (
            lambda ids: wbgetentities_fetch(ids, with_labels=False))
        self._record = record_path
        self._cache = LabelCache(label_fetch)
        self.legibility: List[float] = []
        self.statements_dropped = 0
        self.unparseable_dropped = 0
        self.polls = 0

    def fetch(self) -> Sequence[WikiDispute]:
        data = self._fetch_changes(self._since)
        self.polls += 1
        ids, newest = rc_ids(data)
        if newest:
            self._since = newest                  # continuation: next poll = changes since now
        ids = ids[: self._ids_per_poll]
        if not ids:
            return []                             # quiet stream — the runner paces + re-polls
        statements, dropped = _cap_by_entity(list(self._fetch_ids(ids)), self._entity_cap)
        self.statements_dropped += dropped
        statements = resolve_labels(statements, self._cache.lookup(collect_ids(statements)))
        if self._record:
            record_poll(self._record, statements)
        self.legibility.append(unresolved_fraction(statements))
        disputes, bad = parseable_disputes(statements_to_disputes(statements))
        self.unparseable_dropped += bad
        return disputes

    def exhausted(self) -> bool:
        return False                              # a live stream never ends of itself

    # -- stream persistence (the source half of a kill + resume) ---------------
    def save_state(self, path: str) -> None:
        import json
        import os
        state = {
            "version": 1,
            "since": self._since,
            "polls": self.polls,
            "statements_dropped": self.statements_dropped,
            "unparseable_dropped": self.unparseable_dropped,
            "labels": self._cache._labels, "no_label": sorted(self._cache._no_label),
            "legibility": self.legibility,
        }
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=1)
        os.replace(tmp, path)

    @classmethod
    def load_state(cls, path: str, **kwargs) -> "RecentChangesSource":
        import json
        with open(path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
        src = cls(since=state.get("since"), **kwargs)
        src.polls = state.get("polls", 0)
        src.statements_dropped = state.get("statements_dropped", 0)
        src.unparseable_dropped = state.get("unparseable_dropped", 0)
        src._cache._labels.update(state.get("labels", {}))
        src._cache._no_label.update(state.get("no_label", []))
        src.legibility = list(state.get("legibility", []))
        return src


# --------------------------------------------------------------------------- #
# The real Wikidata call — stdlib only, no auth; NOT exercised in CI          #
# --------------------------------------------------------------------------- #

_USER_AGENT = "Arisbe/alpha (https://github.com/mijahauan/Arisbe; automated-EPG live source)"


def _api_json(params: Dict[str, str], endpoint: str,
              timeout: float):  # pragma: no cover - network; wire it, don't unit-test it
    """One anonymous GET → parsed JSON. Sends a descriptive User-Agent (Wikimedia API
    etiquette) and verifies TLS against ``certifi``'s bundle when available (the stock stdlib
    context has no CA bundle wired on e.g. MacPorts/pyenv Pythons and fails the handshake)."""
    import json
    import ssl
    import urllib.parse
    import urllib.request

    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
    req = urllib.request.Request(
        f"{endpoint}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def recentchanges_fetch(
    *,
    since: Optional[str] = None,
    limit: int = 50,
    show: str = "!bot",
    endpoint: str = "https://www.wikidata.org/w/api.php",
    timeout: float = 20.0,
) -> Dict:  # pragma: no cover - network; wire it, don't unit-test it
    """The real change-stream read: ``list=recentchanges`` over the item namespace, newest
    first, back to ``since`` (the previous poll's newest timestamp — the continuation point;
    omit for "the most recent ``limit`` changes"). ``show='!bot'`` excludes bot edits by
    default — Wikidata's volume is mostly bots, and the human edits are where the disputes
    live; pass ``show=''`` to include everything. Feed the payload to :func:`rc_ids`."""
    params = {
        "action": "query", "list": "recentchanges", "format": "json",
        "rcnamespace": "0", "rctype": "edit|new",
        "rcprop": "title|timestamp", "rclimit": str(limit),
    }
    if show:
        params["rcshow"] = show
    if since:
        params["rcend"] = since   # rcdir=older (default): newest → back to `since`
    return _api_json(params, endpoint, timeout)


def wbgetentities_fetch(
    entity_ids: Sequence[str],
    *,
    lang: str = "en",
    endpoint: str = "https://www.wikidata.org/w/api.php",
    timeout: float = 20.0,
    with_labels: bool = True,
) -> List[WikidataStatement]:  # pragma: no cover - network; wire it, don't unit-test it
    """The real Wikidata read: ``wbgetentities`` for the given Q-ids, flattened to
    :class:`WikidataStatement`. Public, no auth, no dependency (``urllib``). Value stringifying
    is best-effort (entity-id → its id, time → the time string, quantity → amount, string →
    value). With ``with_labels`` (the default) every P/Q id encountered — item, property, and
    entity-valued value — is resolved to its ``lang`` label via :func:`wblabels_fetch`, so the
    facts scribed onto M are legible (``(place_of_birth "Douglas Adams" "Cambridge")``, not
    ``(p19 "Q42" "Q350")``); an id with no label stays an id. Be polite: batch ids, cache, and
    pace via ``LiveRunConfig.min_interval_s``."""
    import json

    data = _api_json({
        "action": "wbgetentities", "ids": "|".join(entity_ids),
        "props": "claims", "format": "json", "languages": lang,
    }, endpoint, timeout)

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
    if with_labels and out:
        out = resolve_labels(out, wblabels_fetch(
            collect_ids(out), lang=lang, endpoint=endpoint, timeout=timeout))
    return out


__all__ = [
    "WikidataStatement", "statement_egif", "statements_to_disputes",
    "collect_ids", "resolve_labels", "unresolved_fraction", "wblabels_fetch",
    "parseable_disputes",
    "LabelCache", "record_poll", "replay_polls", "RotatingWikidataSource",
    "rc_ids", "RecentChangesSource", "recentchanges_fetch",
    "WikidataSource", "wbgetentities_fetch",
]
