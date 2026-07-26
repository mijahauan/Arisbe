"""The AlternativeSet as an index over real chain steps — index-over-ink.

Design-of-record: docs/superpowers/specs/2026-07-26-alternative-index-over-ink-design.md
(rulings R-A..R-F). The record HOLDS no evidence: every evidentiary claim is a
pointer to a gate-checked chain step (`emerged_from` / `traced_by` /
`resolved_by`), re-checkable forever (the QuotationMark pattern applied to
deliberation). The governing philosophy is unchanged from
docs/superpowers/specs/2026-07-25-alternative-set-inquiry-principle.md:
never pre-filter; trace consequences; materiality discovered, not assumed.

No field in this namespace is named ``warrant`` — that word stays doctrinal
(the ○/⛓/⚔ gradient). Materiality is a vector, never a scalar; reception is
held beside it, never folded in.

Deterministic; geometry-free; unprotected.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Protocol, Sequence, Tuple, runtime_checkable


class AlternativeLawViolation(AssertionError):
    """An AlternativeRecord that breaks the AS1–AS4 law."""


# --------------------------------------------------------------------------- #
# Identity                                                                    #
# --------------------------------------------------------------------------- #

def alt_key(relation: str, labels: Sequence[Optional[str]]) -> str:
    """Content-derived identity, arity preserved: a constant slot renders
    quoted, a generic slot (None) renders ``*`` — ``loves("Alba",*)``.
    The same doubt seen twice is the same key (the standing question)."""
    parts = ",".join('"%s"' % l if l is not None else "*" for l in labels)
    return f"{relation}({parts})"


# --------------------------------------------------------------------------- #
# Materiality — the vector (V.1/V.2 dead: no scalar, no doctrinal word)        #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Materiality:
    """What the trace DISCOVERED, as a vector. ``tier`` names the discovered
    class; ``diverging`` the relations that differ between the assert/deny
    branches; ``extra_true``/``extra_false`` the branch-delta atom keys
    (alt_key strings); ``k3_*`` the (explicit, derived) pairs when the K3
    honesty check was consulted. Reception is NOT a component (spec §2)."""

    tier: str                                  # "material" | "bare" | "spurious"
    diverging: Tuple[str, ...] = ()
    extra_true: Tuple[str, ...] = ()
    extra_false: Tuple[str, ...] = ()
    k3_true: Optional[Tuple[int, int]] = None
    k3_false: Optional[Tuple[int, int]] = None

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "diverging": list(self.diverging),
            "extra_true": list(self.extra_true),
            "extra_false": list(self.extra_false),
            "k3_true": list(self.k3_true) if self.k3_true is not None else None,
            "k3_false": list(self.k3_false) if self.k3_false is not None else None,
        }

    @staticmethod
    def from_dict(d: dict) -> "Materiality":
        return Materiality(
            tier=d["tier"],
            diverging=tuple(d.get("diverging", ())),
            extra_true=tuple(d.get("extra_true", ())),
            extra_false=tuple(d.get("extra_false", ())),
            k3_true=tuple(d["k3_true"]) if d.get("k3_true") is not None else None,
            k3_false=tuple(d["k3_false"]) if d.get("k3_false") is not None else None,
        )


# --------------------------------------------------------------------------- #
# Reception — membrane input (spec §5; ruling R-B)                            #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Reception:
    """One membrane arrival bearing on a record. ``classification`` is the
    contextualization-adequacy taxonomy (legible-benign / contested /
    illegible / adversarial); ``bears_evidence`` = the arrival carried a
    parseable claim (posture alone never counts — the political-play hook)."""

    source: str
    stance: str                                # "supports" | "disputes" | "novel"
    classification: str
    claim_egif: Optional[str] = None
    bears_evidence: bool = False

    def to_dict(self) -> dict:
        return {"source": self.source, "stance": self.stance,
                "classification": self.classification,
                "claim_egif": self.claim_egif,
                "bears_evidence": self.bears_evidence}

    @staticmethod
    def from_dict(d: dict) -> "Reception":
        return Reception(source=d["source"], stance=d["stance"],
                         classification=d["classification"],
                         claim_egif=d.get("claim_egif"),
                         bears_evidence=bool(d.get("bears_evidence", False)))


@dataclass(frozen=True)
class TrackRecord:
    """A source's compressed context: how its products have fared."""
    bets: int
    hits: int
    misses: int

    @property
    def accuracy(self) -> Optional[float]:
        decided = self.hits + self.misses
        return (self.hits / decided) if decided else None


@runtime_checkable
class SourceRecord(Protocol):
    """The injectable trust seam (ruling R-B): trust from source track
    record, never from content posture."""
    def track_record(self, source: str) -> Optional[TrackRecord]: ...


class UntrackedSources:
    """The default SourceRecord: every source untracked — so agreement from
    an untracked source earns exactly nothing (the ruling's teeth)."""
    def track_record(self, source: str) -> Optional[TrackRecord]:
        return None


# --------------------------------------------------------------------------- #
# The record — an index over chain steps                                      #
# --------------------------------------------------------------------------- #

KINDS_BUILT = ("interrogative",)


@dataclass(frozen=True)
class AlternativeRecord:
    """Alternatives held in abeyance, as pointers into the chain. Immutable;
    lifecycle moves happen on the register (V.3's wiping methods are gone)."""

    key: str
    relation: str
    labels: Tuple[Optional[str], ...]
    alternatives: Tuple[str, ...]
    kind: str = "interrogative"
    emerged_from: Optional[str] = None
    traced_by: Optional[str] = None
    materiality: Optional[Materiality] = None
    resolved_by: Optional[str] = None
    selection: Optional[str] = None
    receptions: Tuple[Reception, ...] = ()
    posture_pressure: int = 0
    emerged_round: int = 0
    last_touched_round: int = 0

    def __post_init__(self):
        if self.kind not in KINDS_BUILT:
            raise ValueError(
                f"kind {self.kind!r} is not built — only {KINDS_BUILT} meets "
                "the index-over-ink invariants today (V.8 discipline)")
        from egif_parser_dau import parse_egif
        for alt in self.alternatives:
            try:
                parse_egif(alt)
            except Exception as e:
                raise ValueError(
                    f"alternative {alt!r} does not parse as EGIF — an opaque "
                    f"label is refused at birth (V.8): {e}")
        if self.selection is not None and self.selection not in self.alternatives:
            raise ValueError(
                f"selection {self.selection!r} is not one of the alternatives")

    @property
    def status(self) -> str:
        if self.resolved_by is not None:
            return "resolved"
        return "traced" if self.traced_by is not None else "untraced"

    def to_dict(self) -> dict:
        return {
            "key": self.key, "relation": self.relation,
            "labels": ["*" if l is None else l for l in self.labels],
            "alternatives": list(self.alternatives), "kind": self.kind,
            "emerged_from": self.emerged_from, "traced_by": self.traced_by,
            "materiality": self.materiality.to_dict() if self.materiality else None,
            "resolved_by": self.resolved_by, "selection": self.selection,
            "receptions": [r.to_dict() for r in self.receptions],
            "posture_pressure": self.posture_pressure,
            "emerged_round": self.emerged_round,
            "last_touched_round": self.last_touched_round,
        }

    @staticmethod
    def from_dict(d: dict) -> "AlternativeRecord":
        return AlternativeRecord(
            key=d["key"], relation=d["relation"],
            labels=tuple(None if l == "*" else l for l in d["labels"]),
            alternatives=tuple(d["alternatives"]), kind=d.get("kind", "interrogative"),
            emerged_from=d.get("emerged_from"), traced_by=d.get("traced_by"),
            materiality=(Materiality.from_dict(d["materiality"])
                         if d.get("materiality") else None),
            resolved_by=d.get("resolved_by"), selection=d.get("selection"),
            receptions=tuple(Reception.from_dict(r) for r in d.get("receptions", [])),
            posture_pressure=int(d.get("posture_pressure", 0)),
            emerged_round=int(d.get("emerged_round", 0)),
            last_touched_round=int(d.get("last_touched_round", 0)),
        )


class AlternativeRegister:
    """The standing, content-keyed, bounded register of open questions.
    A cache over the chain, never a second authority: records rebuild from
    the chain (Task 6's ``rebuild_from_chain``), so LRU displacement loses
    no truth, only cache. Snapshot/restore on the docket template (V.6)."""

    def __init__(self, capacity: int = 64):
        self._capacity = capacity
        self._records: Dict[str, AlternativeRecord] = {}
        self.admitted = 0
        self.displaced = 0
        self.displaced_keys: List[str] = []      # dedup'd, insertion order

    def __len__(self) -> int:
        return len(self._records)

    def __contains__(self, key: str) -> bool:
        return key in self._records

    def get(self, key: str) -> Optional[AlternativeRecord]:
        return self._records.get(key)

    def records(self) -> List[AlternativeRecord]:
        return [self._records[k] for k in sorted(self._records)]

    def open_records(self) -> List[AlternativeRecord]:
        return [r for r in self.records() if r.status != "resolved"]

    def note(self, record: AlternativeRecord, *, round_idx: int) -> Optional[str]:
        """Admit or touch by key. A re-arrival merges: evidence fields are
        adopted from whichever side carries them (never wiped — the V.3
        discipline); the earliest emergence stands; the touch is stamped.
        Returns the displaced key when the register was full, else None."""
        if record.key in self._records:
            old = self._records[record.key]
            self._records[record.key] = replace(
                old,
                emerged_from=old.emerged_from or record.emerged_from,
                traced_by=record.traced_by or old.traced_by,
                materiality=record.materiality or old.materiality,
                resolved_by=record.resolved_by or old.resolved_by,
                selection=record.selection or old.selection,
                receptions=old.receptions + tuple(
                    r for r in record.receptions if r not in old.receptions),
                posture_pressure=max(old.posture_pressure, record.posture_pressure),
                last_touched_round=round_idx,
            )
            return None
        displaced_key: Optional[str] = None
        if self._records and len(self._records) >= self._capacity:
            oldest = min(self._records.values(),
                         key=lambda r: (r.last_touched_round, r.key))
            displaced_key = oldest.key
            del self._records[oldest.key]
            self.displaced += 1
            if displaced_key not in self.displaced_keys:
                self.displaced_keys.append(displaced_key)
        self._records[record.key] = replace(record, last_touched_round=round_idx,
                                            emerged_round=round_idx)
        self.admitted += 1
        return displaced_key

    def resolve(self, key: str, *, resolved_by: str, selection: str) -> AlternativeRecord:
        rec = self._records[key]
        out = replace(rec, resolved_by=resolved_by, selection=selection)
        self._records[key] = out
        return out

    def receive(self, key: str, reception: Reception, *, round_idx: int) -> AlternativeRecord:
        """Attach a membrane arrival. A stance with no checkable content on
        an OPEN record is posture-only: counted, contributing nothing (the
        political-play hook, spec §5)."""
        rec = self._records[key]
        pressure = rec.posture_pressure
        if not reception.bears_evidence and rec.status != "resolved":
            pressure += 1
        out = replace(rec, receptions=rec.receptions + (reception,),
                      posture_pressure=pressure, last_touched_round=round_idx)
        self._records[key] = out
        return out

    def snapshot(self) -> dict:
        return {
            "capacity": self._capacity,
            "records": [r.to_dict() for r in self.records()],
            "admitted": self.admitted,
            "displaced": self.displaced,
            "displaced_keys": list(self.displaced_keys),
        }

    @staticmethod
    def restore(state: dict) -> "AlternativeRegister":
        reg = AlternativeRegister(capacity=int(state.get("capacity", 64)))
        for d in state.get("records", []):
            rec = AlternativeRecord.from_dict(d)
            reg._records[rec.key] = rec
        reg.admitted = int(state.get("admitted", 0))
        reg.displaced = int(state.get("displaced", 0))
        reg.displaced_keys = list(state.get("displaced_keys", []))
        return reg


__all__ = [
    "AlternativeLawViolation", "alt_key", "Materiality", "Reception",
    "TrackRecord", "SourceRecord", "UntrackedSources", "AlternativeRecord",
    "AlternativeRegister",
]
