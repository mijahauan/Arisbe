"""The docket of doubts — increment 2a, the minimum build (Q1-only).

Design-of-record: ``docs/AUTOMATED_ENDOPOREUTIC_GAME.md`` §15 (drafted 2026-07-03;
gate fired on run 5b's disposal; the five decisions AFFIRMED 2026-07-05). The system
already *names its own missing answers* — the peel's Kleene UNKNOWNs, M's structural
thin spots (``agon_llm.attention_brief``'s categories) — but until now no wire ran from
articulated doubt to executable reach: the tropism re-asks about what M *holds*
(identity-shaped), never about what M *lacks*. The docket is that wire's first stratum.

**What it is.** A player-side register of *named wants*: each entry a shape M neither
holds nor denies, carrying the relation wanted, the constants already bound (the grip a
membrane can grasp), why it is wanted (provenance), and age/attempts — **counted, never
silently dropped** (the ``attest_overview`` twin). Placement per §15 decision 2: a policy
consulted at the poll boundary, *composing with* ``WarmSetTropism`` (warm re-reach is the
docket's cheapest, lowest-articulation stratum — the two inject side by side).

**What it can ask (this increment).** Only **Q1** — entity re-reach through the existing
``inject(ids)`` seam: an entry whose constants reverse to entity ids rides the next
poll's chunk; an entry no Q1 vocabulary can express **waits, counted** (the honest
residue — ``inexpressible`` is the number the Q2/Q3 tiers exist to shrink; per the
affirmed ordering, the first live *resolving* source lands before those tiers are built).

**Where entries come from (this increment).**

- **thin spots of M**, recomputed per ``observe``: a relation with ≤1 grounded instance
  (grip = the lone atom's entity, if any) and a lonely individual (a constant appearing
  in exactly one atom — grip = itself). The same categories the Graphist's
  ``attention_brief`` names; computed here structurally, no LLM in the loop.
- **the peel's UNKNOWNs**, via ``note_unknowns`` — the seam an open-world caller feeds
  ``(relation, labels)`` pairs the oracle could not decide (the closed-world wiki loop
  rarely yields these; the resolving membrane will).

**Resolution.** ``observe(M)`` settles entries the sheet has come to answer (the wanted
relation gained a second instance; the lonely individual gained a second atom; the noted
unknown is now held) and ages the rest. v1 priority is the fixed lexicographic ordering
§15 pre-registered (cost tier — all Q1 here; fewest attempts first, so new doubts are
tried before retries; then age, oldest first — the starvation guard); a *learned*
priority is itself a finding to earn.

Geometry-free; deterministic; offline-testable end to end. Adds no §3.3 obligation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from collections import Counter

from egif_parser_dau import parse_egif
from eg_navigation import area_of
from tropism import reverse_labels

import re

_PQ_ID = re.compile(r"^[PQ]\d+$")

# A label a Q1 reach can plausibly grip: an entity-ish name, not a *value* (RUN_6
# F2⁶: 1,034 unreversible grips were timestamps, urls, identifiers, coordinate
# blobs — asking the membrane to re-fetch "+2012-03-31T00:00:00Z" is a category
# error the harvest should refuse up front).
def _griplike(label: str) -> bool:
    if not label or len(label) > 60:
        return False
    if label[0] in "+-0123456789":
        return False
    if label.startswith(("http://", "https://", "{")):
        return False
    return True


# --------------------------------------------------------------------------- #
# The entry — a named want                                                     #
# --------------------------------------------------------------------------- #

@dataclass
class DocketEntry:
    """One named want: a shape M neither holds nor denies.

    ``shape`` is the relation wanted (``"*"`` = anything more about the constants);
    ``constants`` the labels already bound — the grip a Q1 reach can grasp;
    ``provenance`` why it is wanted (``thin_spot(rare_relation)`` ·
    ``thin_spot(lonely_individual)`` · ``unknown_in_peel``). ``age`` counts
    ``observe`` passes survived; ``attempts`` counts Q1 asks emitted for it."""
    shape: str
    constants: Tuple[str, ...]
    provenance: str
    age: int = 0
    attempts: int = 0

    @property
    def key(self) -> Tuple[str, Tuple[str, ...]]:
        return (self.shape, self.constants)


# --------------------------------------------------------------------------- #
# The docket                                                                   #
# --------------------------------------------------------------------------- #

def _sheet_atoms(egi) -> List[Tuple[str, List[Optional[str]]]]:
    """Ground atoms on the sheet: (relation, [labels…]) — constants carry labels,
    generic vertices read as None."""
    out = []
    for e in egi.E:
        if e.id in egi.rel and area_of(egi, e.id) == egi.sheet:
            labels = [egi.get_vertex(v).label for v in egi.nu.get(e.id, ())]
            out.append((egi.rel[e.id], labels))
    return out


class QueryDocket:
    """The player's register of named wants, consulted at the poll boundary
    (see module docstring). ``labels`` is the run's ``id → label`` cache or a
    zero-arg callable returning it (the same contract as ``WarmSetTropism``);
    ``k`` the Q1 asks emitted per poll; ``max_entries`` bounds the register
    (past it, new harvests are *counted as deferred*, never silently lost)."""

    def __init__(
        self,
        labels: Union[Mapping[str, str], Callable[[], Mapping[str, str]]],
        k: int = 2,
        max_entries: int = 500,
        journal_path: Optional[str] = None,
    ):
        self._labels = labels
        self._k = k
        self._max = max_entries
        # The ask journal (2a.1, RUN_6 F1⁶): every Q1 ask appended as one JSONL line
        # (poll · entity · want-key · provenance) beside the polls record, so
        # ask-driven resolutions can be separated from stream-borne ones at disposal.
        self._journal_path = journal_path
        self._entries: Dict[Tuple[str, Tuple[str, ...]], DocketEntry] = {}
        self._deferred_keys: set = set()   # DISTINCT wants refused at the cap (F1⁶:
                                           # the old per-attempt count re-counted every
                                           # re-harvest pass — ~197k for ~200 wants)
        # Counters — the never-silent ledger.
        self.harvested = 0          # entries ever admitted
        self.resolved = 0           # entries the sheet came to answer
        self.emitted = 0            # Q1 asks emitted (attempts, summed)
        self.ambiguous_skipped = 0  # grips whose label reverses to several ids
        self.unmapped_skipped = 0   # grips the cache cannot reverse at all

    # -- introspection ---------------------------------------------------------
    @property
    def open_entries(self) -> List[DocketEntry]:
        """The active register, in the emission ordering (see ``reaches``)."""
        return sorted(self._entries.values(),
                      key=lambda e: (e.attempts, -e.age, e.key))

    @property
    def deferred(self) -> int:
        """DISTINCT wants refused at the register cap — counted, never lost silently."""
        return len(self._deferred_keys)

    @property
    def inexpressible(self) -> int:
        """Open entries no Q1 vocabulary can express (no constant grip) — the
        honest residue the Q2/Q3 tiers exist to shrink."""
        return sum(1 for e in self._entries.values() if not e.constants)

    def _label_map(self) -> Mapping[str, str]:
        return self._labels() if callable(self._labels) else self._labels

    def _admit(self, entry: DocketEntry) -> None:
        if entry.key in self._entries:
            return
        if len(self._entries) >= self._max:
            self._deferred_keys.add(entry.key)
            return
        self._entries[entry.key] = entry
        self._deferred_keys.discard(entry.key)
        self.harvested += 1

    # -- the seams --------------------------------------------------------------

    def note_unknowns(self, unknowns: Iterable[Tuple[str, Sequence[str]]]) -> None:
        """The peel-UNKNOWN seam: ``(relation, labels)`` atoms an oracle could not
        decide (open-world abstentions). Constants among the labels become the grip."""
        for rel, labels in unknowns:
            grip = tuple(l for l in labels if l)
            self._admit(DocketEntry(shape=rel, constants=grip,
                                    provenance="unknown_in_peel"))

    def observe(self, model_egif: str) -> None:
        """One docket tick against the carried M: **settle** what the sheet has come
        to answer, **age** the rest, **harvest** the thin spots M now exposes."""
        atoms = _sheet_atoms(parse_egif(model_egif)) if model_egif else []
        rel_counts = Counter(r for r, _ in atoms)
        const_counts = Counter(l for _, labels in atoms for l in labels if l)
        holds = {(r, tuple(l for l in labels if l)) for r, labels in atoms}

        # settle
        for key in list(self._entries):
            e = self._entries[key]
            done = (
                (e.provenance == "thin_spot(rare_relation)" and rel_counts.get(e.shape, 0) >= 2)
                or (e.provenance == "thin_spot(lonely_individual)"
                    and any(const_counts.get(c, 0) >= 2 for c in e.constants))
                or (e.provenance == "unknown_in_peel"
                    and (e.shape, e.constants) in holds)
            )
            if done:
                del self._entries[key]
                self.resolved += 1
            else:
                e.age += 1

        # harvest thin spots (the attention_brief categories, structurally).
        # Grips are FILTERED griplike (F2⁶): the entity-position (first) argument if
        # it is entity-ish, else no grip — an ungripped want waits as inexpressible
        # rather than burning asks on value-labels the cache can never reverse.
        for rel, n in rel_counts.items():
            if n <= 1:
                lone = next((labels for r, labels in atoms if r == rel), [])
                consts = [l for l in lone if l]
                grip = tuple(consts[:1]) if consts and _griplike(consts[0]) else ()
                self._admit(DocketEntry(shape=rel, constants=grip,
                                        provenance="thin_spot(rare_relation)"))
        for const, n in const_counts.items():
            if n == 1 and _griplike(const):    # a lonely timestamp is not an individual
                self._admit(DocketEntry(shape="*", constants=(const,),
                                        provenance="thin_spot(lonely_individual)"))

    def reaches(self, k: Optional[int] = None, poll: Optional[int] = None) -> List[str]:
        """The next Q1 asks: up to ``k`` distinct entity ids, from the top of the
        v1 ordering (fewest attempts, then oldest). A grip that is already a Q-id
        passes through; a label reverses via the cache; ambiguous/unreversible
        grips are skipped **and counted** (§13 decision 5's discipline). Emitting
        increments the entry's ``attempts`` — and appends one **journal line**
        per ask (2a.1: poll · entity · want-key · provenance) when a
        ``journal_path`` was given, so disposal can attribute resolutions."""
        budget = self._k if k is None else k
        if budget <= 0 or not self._entries:
            return []
        label_to_id, ambiguous = reverse_labels(self._label_map())
        out: List[str] = []
        asked: List[DocketEntry] = []
        skipped_amb: set = set()
        skipped_unm: set = set()
        for e in self.open_entries:
            if len(out) >= budget:
                break
            for c in e.constants:
                if _PQ_ID.match(c):
                    entity = c
                elif c in label_to_id:
                    entity = label_to_id[c]
                elif c in ambiguous:
                    skipped_amb.add(c)
                    continue
                else:
                    skipped_unm.add(c)
                    continue
                if entity.startswith("Q") and entity not in out:
                    out.append(entity)
                    asked.append(e)
                    e.attempts += 1
                    break
        self.ambiguous_skipped += len(skipped_amb)
        self.unmapped_skipped += len(skipped_unm)
        self.emitted += len(out)
        if self._journal_path and out:
            import json
            with open(self._journal_path, "a", encoding="utf-8") as fh:
                for entity, e in zip(out, asked):
                    fh.write(json.dumps({
                        "poll": poll, "entity": entity,
                        "want": [e.shape, list(e.constants)],
                        "provenance": e.provenance,
                        "attempts": e.attempts, "age": e.age,
                    }) + "\n")
        return out[:budget]

    # -- persistence (2a.1: the register survives a supervisor resume) -----------

    def snapshot(self) -> dict:
        """The register + counters as a JSON-able dict (for ``state.json``, the
        disuse-ledger pattern) — a resumed run keeps its wants, ages, attempts,
        and whole-run counters instead of starting a fresh docket per leg."""
        return {
            "entries": [
                {"shape": e.shape, "constants": list(e.constants),
                 "provenance": e.provenance, "age": e.age, "attempts": e.attempts}
                for e in self._entries.values()
            ],
            "deferred": [[k[0], list(k[1])] for k in self._deferred_keys],
            "counters": {"harvested": self.harvested, "resolved": self.resolved,
                         "emitted": self.emitted,
                         "ambiguous_skipped": self.ambiguous_skipped,
                         "unmapped_skipped": self.unmapped_skipped},
        }

    def restore(self, state: dict) -> None:
        self._entries = {}
        for d in state.get("entries", []):
            e = DocketEntry(shape=d["shape"], constants=tuple(d["constants"]),
                            provenance=d["provenance"], age=d.get("age", 0),
                            attempts=d.get("attempts", 0))
            self._entries[e.key] = e
        self._deferred_keys = {(s0, tuple(c)) for s0, c in state.get("deferred", [])}
        c = state.get("counters", {})
        self.harvested = c.get("harvested", 0)
        self.resolved = c.get("resolved", 0)
        self.emitted = c.get("emitted", 0)
        self.ambiguous_skipped = c.get("ambiguous_skipped", 0)
        self.unmapped_skipped = c.get("unmapped_skipped", 0)


__all__ = ["DocketEntry", "QueryDocket"]
