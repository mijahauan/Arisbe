# AlternativeSet Index-Over-Ink Re-Housing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-house the AlternativeSet layer as an index over real, gate-checked
chain steps (spec: `docs/superpowers/specs/2026-07-26-alternative-index-over-ink-design.md`),
proving the one producer→consumer loop (AC1–AC10) that unblocks Tasks 5–6.

**Architecture:** Two modules — `alternative_index.py` (record/register/AS-law)
and `alternative_trace.py` (dry-run trace + the PEEL-twin `trace_step`) — plus a
structured-unknowns producer in `semantic_game`, an attention-economy consumer,
register-snapshot persistence in `tomos_service`, a polarity-gate extension, and
wholesale retirement of the Task-4 dataclass layer (`alternative_set.py`,
`alternative_inquiry.py`, `erotetic_doubt.py`, the UoD alternative fields/methods).

**Tech Stack:** Python 3.12, uv, pytest. Existing house modules:
`proof_authoring.ProofChain`, `world_scroll.m_view/wrap_m`, `m_steps`,
`model_revision.assert_fact`, `model_materialization`, `quotation_overlay.lift_cut`,
`eg_navigation.same_graph/area_of`, `attention_economy`.

## Global Constraints

- **No protected-core change.** None of the touched files is in the protected set; never create `.core_modification_authorized`.
- **Deterministic everywhere**: sorted iteration wherever order could vary; no wall clock, no randomness (`ProofChain` timestamps are already deterministic).
- **Geometry-free**: no layout/DTO imports in the new modules.
- **Import pattern**: `from module_name import Foo` (never `from src.module_name`).
- **No float named `warrant`** (or `external_warrant`) anywhere in the new namespace — spec AC10.
- Run tests via `uv run pytest tests/<file> -q` from the repo root. Commit after every task (quality gates + 152 core tests run automatically on commit).
- The spec is the authority: `docs/superpowers/specs/2026-07-26-alternative-index-over-ink-design.md`. Where this plan and the spec disagree, the spec wins — flag the discrepancy instead of silently choosing.
- Full suite before final commit: `uv run pytest tests/ -q` — 0 failures required (~3900 pass today; old-layer tests are deleted in Task 9, new ones added throughout).

## File Structure

| File | Role |
|------|------|
| `src/alternative_index.py` (new) | `alt_key`, `Materiality`, `Reception`, `TrackRecord`/`SourceRecord`/`UntrackedSources`, `AlternativeRecord`, `AlternativeRegister`, `record_from_trace_step`, AS1–AS4 law (`run_/attest_alternative_record`), `classify_reception`/`receive` |
| `src/alternative_trace.py` (new) | `KyteProfile`, `BoundedRegister` (+snapshot/restore), `UnrepresentableAtomError`, `atom_and_denial_egif`, `trace_unknown`, `trace_step`, `trace_batch`, `fold_registers_from_chain` |
| `src/semantic_game.py` (modify) | `SemanticResult.unknown_atoms` + collection in `_atom_verdict`/`_holds` |
| `src/m_steps.py` (modify) | `peel_step` params carry `unknown_atoms` |
| `src/proof_character.py` (modify) | `TRACE_ALTERNATIVES` joins `NEUTRAL_RULES` |
| `src/attention_economy.py` (modify) | `QuarantineRegister`, `wants_from_alternatives` |
| `src/tomos_service.py` (modify) | `save_alternative_register`/`load_alternative_register` (attesting, raising); old alternatives API removed |
| `src/universe_of_discourse.py` (modify) | alternative fields/methods removed |
| Deleted | `src/alternative_set.py`, `src/alternative_inquiry.py`, `src/erotetic_doubt.py`, `tests/test_alternative_set.py`, `tests/test_alternative_inquiry.py`, `tests/test_erotetic_doubt.py`, `tests/test_uod_with_alternatives.py`, `tests/test_uod_with_doubts.py`, `tests/test_tomos_service_with_alternatives.py` |
| `tests/test_alternative_index.py` (new) | Tasks 1, 2, 7 |
| `tests/test_alternative_trace.py` (new) | Tasks 3, 4 |
| `tests/test_unknown_atoms.py` (new) | Task 5 |
| `tests/test_alternative_law.py` (new) | Task 6 |
| `tests/test_wants_from_alternatives.py` (new) | Task 8 |
| `tests/test_alternative_persistence.py` (new) | Task 9 |
| `tests/test_corpus_polarity_discipline.py` (modify) | Task 10 |
| `tests/test_alternative_loop.py` (new) | Task 11 — AC1–AC10 |

Every test file starts with the house header:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

---

### Task 1: `alternative_index.py` — core types

**Files:**
- Create: `src/alternative_index.py`
- Test: `tests/test_alternative_index.py`

**Interfaces:**
- Produces: `alt_key(relation: str, labels: Sequence[Optional[str]]) -> str`;
  `Materiality(tier, diverging, extra_true, extra_false, k3_true, k3_false)` frozen, `.to_dict()/.from_dict()`;
  `Reception(source, stance, classification, claim_egif, bears_evidence)` frozen, `.to_dict()/.from_dict()`;
  `TrackRecord(bets, hits, misses)` frozen with `.accuracy`; `SourceRecord` Protocol (`track_record(source) -> Optional[TrackRecord]`); `UntrackedSources`;
  `AlternativeRecord(...)` frozen with `.status`, `.to_dict()/.from_dict()`;
  exceptions `AlternativeLawViolation(AssertionError)`.

- [ ] **Step 1: Write the failing tests**

```python
"""AlternativeRecord / AlternativeRegister — the index over chain steps.

Spec: docs/superpowers/specs/2026-07-26-alternative-index-over-ink-design.md §2.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import dataclasses

import pytest

from alternative_index import (
    AlternativeRecord, Materiality, Reception, TrackRecord, UntrackedSources,
    alt_key,
)


class TestAltKey:
    def test_constants_and_generics(self):
        assert alt_key("white", ("Alba",)) == 'white("Alba")'
        assert alt_key("loves", ("Alba", None)) == 'loves("Alba",*)'
        assert alt_key("rains", ()) == "rains()"

    def test_arity_preserved(self):
        assert alt_key("loves", ("Alba", None)) != alt_key("loves", ("Alba",))


class TestMateriality:
    def test_vector_round_trips(self):
        m = Materiality(tier="material", diverging=("white",),
                        extra_true=('white("Dover")',), extra_false=(),
                        k3_true=None, k3_false=None)
        assert Materiality.from_dict(m.to_dict()) == m

    def test_no_scalar_field(self):
        names = {f.name for f in dataclasses.fields(Materiality)}
        assert "warrant" not in names and "score" not in names


class TestReception:
    def test_round_trips(self):
        r = Reception(source="fieldbook", stance="supports",
                      classification="legible-benign",
                      claim_egif='(swan "Dover")', bears_evidence=True)
        assert Reception.from_dict(r.to_dict()) == r


class TestTrackRecord:
    def test_accuracy(self):
        assert TrackRecord(bets=4, hits=3, misses=1).accuracy == 0.75
        assert TrackRecord(bets=0, hits=0, misses=0).accuracy is None

    def test_untracked_sources_answer_none(self):
        assert UntrackedSources().track_record("anyone") is None


class TestAlternativeRecord:
    def _rec(self, **kw):
        base = dict(
            key=alt_key("swan", ("Dover",)), relation="swan", labels=("Dover",),
            alternatives=('(swan "Dover")', '~[ (swan "Dover") ]'),
        )
        base.update(kw)
        return AlternativeRecord(**base)

    def test_valid_record_and_status(self):
        r = self._rec()
        assert r.status == "untraced"
        traced = dataclasses.replace(r, traced_by="step-2",
                                     materiality=Materiality(tier="bare"))
        assert traced.status == "traced"
        resolved = dataclasses.replace(traced, resolved_by="step-5",
                                       selection='(swan "Dover")')
        assert resolved.status == "resolved"

    def test_opaque_alternative_refused_at_birth(self):
        with pytest.raises(ValueError, match="parse"):
            self._rec(alternatives=("grounding-A", "grounding-B"))

    def test_non_interrogative_kind_refused(self):
        with pytest.raises(ValueError, match="kind"):
            self._rec(kind="modal")

    def test_selection_must_be_an_alternative(self):
        with pytest.raises(ValueError, match="selection"):
            self._rec(resolved_by="step-5", selection='(black "Dover")')

    def test_no_warrant_float_in_namespace(self):
        names = {f.name for f in dataclasses.fields(AlternativeRecord)}
        assert "warrant" not in names and "external_warrant" not in names

    def test_round_trips(self):
        r = self._rec(traced_by="step-2", materiality=Materiality(tier="material",
                      diverging=("white",)), receptions=(Reception(
                          source="s", stance="supports",
                          classification="legible-benign",
                          claim_egif=None, bears_evidence=False),),
                      posture_pressure=1)
        assert AlternativeRecord.from_dict(r.to_dict()) == r
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_alternative_index.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'alternative_index'`

- [ ] **Step 3: Implement `src/alternative_index.py` (core types)**

```python
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


__all__ = [
    "AlternativeLawViolation", "alt_key", "Materiality", "Reception",
    "TrackRecord", "SourceRecord", "UntrackedSources", "AlternativeRecord",
]
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_alternative_index.py -q`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add src/alternative_index.py tests/test_alternative_index.py
git commit -m "Task 1: alternative_index core types (alt_key, Materiality vector, Reception, record)"
```

---

### Task 2: `AlternativeRegister` — standing, bounded, snapshot/restore

**Files:**
- Modify: `src/alternative_index.py` (append)
- Test: `tests/test_alternative_index.py` (append)

**Interfaces:**
- Consumes: Task 1 types.
- Produces: `AlternativeRegister(capacity: int = 64)` with
  `note(record, *, round_idx) -> Optional[str]` (displaced key or None),
  `get(key) -> Optional[AlternativeRecord]`, `__len__`, `__contains__`,
  `open_records() -> List[AlternativeRecord]` (sorted by key),
  `records() -> List[AlternativeRecord]` (all, sorted by key),
  `resolve(key, *, resolved_by, selection) -> AlternativeRecord`,
  `receive(key, reception, *, round_idx) -> AlternativeRecord`,
  counters `admitted`/`displaced`/`displaced_keys: List[str]`,
  `snapshot() -> dict`, `AlternativeRegister.restore(state) -> AlternativeRegister`.
  (`settle_from_chain`/`rebuild_from_chain` come in Task 6.)

- [ ] **Step 1: Append failing tests to `tests/test_alternative_index.py`**

```python
from alternative_index import AlternativeRegister


def _record(rel="swan", labels=("Dover",), **kw):
    base = dict(key=alt_key(rel, labels), relation=rel, labels=labels,
                alternatives=(f'({rel} "{labels[0]}")', f'~[ ({rel} "{labels[0]}") ]'))
    base.update(kw)
    return AlternativeRecord(**base)


class TestAlternativeRegister:
    def test_dedup_by_key_touches_never_forks(self):
        reg = AlternativeRegister(capacity=4)
        reg.note(_record(), round_idx=1)
        reg.note(_record(), round_idx=5)               # same key re-arrives
        assert len(reg) == 1
        assert reg.get(alt_key("swan", ("Dover",))).last_touched_round == 5
        assert reg.get(alt_key("swan", ("Dover",))).emerged_round == 1

    def test_merge_adopts_evidence_never_wipes(self):
        # The V.3 regression pin: a later, less-informed arrival must not
        # reset the traced fields.
        reg = AlternativeRegister(capacity=4)
        traced = _record(traced_by="step-2", materiality=Materiality(tier="material"))
        reg.note(traced, round_idx=1)
        reg.note(_record(), round_idx=2)               # untraced re-arrival
        got = reg.get(traced.key)
        assert got.traced_by == "step-2"
        assert got.materiality.tier == "material"

    def test_lru_displacement_counted(self):
        reg = AlternativeRegister(capacity=2)
        reg.note(_record("a", ("1",)), round_idx=1)
        reg.note(_record("b", ("2",)), round_idx=2)
        displaced = reg.note(_record("c", ("3",)), round_idx=3)
        assert displaced == alt_key("a", ("1",))
        assert reg.displaced == 1
        assert reg.displaced_keys == [alt_key("a", ("1",))]
        assert len(reg) == 2

    def test_snapshot_restore_round_trips(self):
        reg = AlternativeRegister(capacity=2)
        reg.note(_record("a", ("1",)), round_idx=1)
        reg.note(_record("b", ("2",)), round_idx=2)
        reg.note(_record("c", ("3",)), round_idx=3)    # displaces a
        reg2 = AlternativeRegister.restore(reg.snapshot())
        assert reg2.snapshot() == reg.snapshot()

    def test_resolve_and_receive(self):
        reg = AlternativeRegister(capacity=4)
        r = _record()
        reg.note(r, round_idx=1)
        posture = Reception(source="pundit", stance="supports",
                            classification="legible-benign",
                            claim_egif=None, bears_evidence=False)
        got = reg.receive(r.key, posture, round_idx=2)
        assert got.posture_pressure == 1
        resolved = reg.resolve(r.key, resolved_by="step-9",
                               selection='(swan "Dover")')
        assert resolved.status == "resolved"
        assert reg.open_records() == []
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_alternative_index.py -q`
Expected: FAIL — `ImportError: cannot import name 'AlternativeRegister'`

- [ ] **Step 3: Append implementation to `src/alternative_index.py`**

```python
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
        self._records[record.key] = replace(record, last_touched_round=round_idx)
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
```

Append `"AlternativeRegister"` to `__all__`.

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_alternative_index.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/alternative_index.py tests/test_alternative_index.py
git commit -m "Task 2: AlternativeRegister — bounded, content-keyed, snapshot/restore, merge-never-wipe"
```

---

### Task 3: `alternative_trace.py` — the dry-run trace, V.4 fixed

**Files:**
- Create: `src/alternative_trace.py`
- Test: `tests/test_alternative_trace.py`

**Interfaces:**
- Consumes: `alternative_index.Materiality`, `alternative_index.alt_key`;
  `world_scroll.m_view`; `model_revision.assert_fact`;
  `model_materialization.materialize_egi/materialization_ratio`;
  `eg_navigation.area_of`; `egif_parser_dau.parse_egif`.
- Produces: `KyteProfile(s_capacity=32, a_capacity=32, alt_capacity=64)`;
  `BoundedRegister(capacity)` with `admit(term) -> Optional[str]`, `terms`,
  `__contains__`, `__len__`, `admitted`, `displaced`, `snapshot() -> dict`,
  `BoundedRegister.restore(state)`;
  `UnrepresentableAtomError(ValueError)`;
  `atom_and_denial_egif(relation, labels) -> Tuple[str, str]` (verification-parsed);
  `TraceResult(key, relation, labels, atom_egif, denial_egif, materiality,
  s_admitted, s_displaced, a_admitted, a_displaced)` frozen;
  `trace_unknown(m_egi, relation, labels, *, s_register, a_register) -> TraceResult`.

- [ ] **Step 1: Write the failing tests**

```python
"""The dry-run consequence trace (PEEL-twin housing) — V.4 fixed at the source.

Spec: docs/superpowers/specs/2026-07-26-alternative-index-over-ink-design.md §3.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from alternative_trace import (
    BoundedRegister, KyteProfile, TraceResult, UnrepresentableAtomError,
    atom_and_denial_egif, trace_unknown,
)
from egif_parser_dau import parse_egif

LAW = '~[ (swan *x) ~[ (white x) ] ]'
M0 = f'(swan "Ciel") (white "Ciel") {LAW}'


def _registers():
    p = KyteProfile()
    return BoundedRegister(p.s_capacity), BoundedRegister(p.a_capacity)


class TestAtomAndDenial:
    def test_ground_atom(self):
        atom, denial = atom_and_denial_egif("white", ("Alba",))
        assert atom == '(white "Alba")'
        assert denial == '~[ (white "Alba") ]'

    def test_generic_slot_renders_defining_variable_never_None(self):
        # The V.4 kill: an unwitnessed existential is a question about a line
        # of identity, never a constant named "None".
        atom, denial = atom_and_denial_egif("loves", ("Alba", None))
        assert atom == '(loves "Alba" *x)'
        assert '"None"' not in atom and '"None"' not in denial
        g = parse_egif(atom)                     # parses as a real existential
        assert sum(1 for v in g.V if v.is_generic) == 1

    def test_two_generic_slots_get_distinct_variables(self):
        atom, _ = atom_and_denial_egif("between", (None, "B", None))
        assert atom == '(between *x "B" *x2)'

    def test_unrepresentable_label_refused_never_mangled(self):
        with pytest.raises(UnrepresentableAtomError):
            atom_and_denial_egif("said", ('he said "hi"',))

    def test_escaped_label_round_trips(self):
        # A label already in the parser's escaped form round-trips fine.
        atom, _ = atom_and_denial_egif("said", ('he said \\"hi\\"',))
        parse_egif(atom)


class TestBoundedRegister:
    def test_lru_displacement_counted(self):
        r = BoundedRegister(2)
        assert r.admit("a") is None
        assert r.admit("b") is None
        assert r.admit("c") == "a"
        assert r.displaced == 1 and r.admitted == 3
        assert r.terms == ["b", "c"]

    def test_snapshot_restore_round_trips(self):
        r = BoundedRegister(2)
        r.admit("a"); r.admit("b"); r.admit("a"); r.admit("c")
        r2 = BoundedRegister.restore(r.snapshot())
        assert r2.snapshot() == r.snapshot()
        # Order semantics survive: "b" is now the LRU term.
        assert r2.admit("d") == "b"


class TestTraceUnknown:
    def test_material_through_the_law(self):
        # Asserting (swan "Dover") derives (white "Dover") via the law;
        # denying derives nothing: the branches diverge on "white".
        s, a = _registers()
        tr = trace_unknown(parse_egif(M0), "swan", ("Dover",),
                           s_register=s, a_register=a)
        assert tr.materiality.tier == "material"
        assert "white" in tr.materiality.diverging
        assert 'white("Dover")' in tr.materiality.extra_true

    def test_bare_when_no_law_touches_it(self):
        s, a = _registers()
        tr = trace_unknown(parse_egif(M0), "black", ("Dover",),
                           s_register=s, a_register=a)
        assert tr.materiality.tier == "bare"

    def test_m_is_never_mutated(self):
        import eg_navigation as nav
        m = parse_egif(M0)
        before = parse_egif(M0)
        s, a = _registers()
        trace_unknown(m, "swan", ("Dover",), s_register=s, a_register=a)
        assert nav.same_graph(m, before)

    def test_existential_traces_without_corruption(self):
        s, a = _registers()
        tr = trace_unknown(parse_egif(M0), "loves", ("Ciel", None),
                           s_register=s, a_register=a)
        assert '"None"' not in tr.atom_egif
        assert tr.materiality.tier in ("material", "bare", "spurious")

    def test_s_a_refinement_recorded_in_order(self):
        s, a = _registers()
        tr = trace_unknown(parse_egif(M0), "swan", ("Dover",),
                           s_register=s, a_register=a)
        assert "derivable:white" in tr.s_admitted
        assert "distinction:swan" in tr.s_admitted
        assert "resolve:swan" in tr.a_admitted
        assert f"distinction:swan" in s.terms
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_alternative_trace.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'alternative_trace'`

- [ ] **Step 3: Implement `src/alternative_trace.py`**

```python
"""The dry-run consequence trace and its chain housing — the trace half of
index-over-ink (spec §3, ruling R-A: TRACE as PEEL-twin).

The trace algorithm withstood Examination V; only its housing changes. What is
new here: the V.4 fix (a generic slot becomes a DEFINING VARIABLE — ``*x`` —
never the constant "None"; every emitted atom is verification-parsed and an
unrepresentable one raises, count-or-refuse), and BoundedRegister gains the
snapshot/restore every real standing register carries (V.6).

Deterministic; geometry-free; unprotected.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

from alternative_index import Materiality, alt_key
from eg_navigation import area_of
from egi_core_dau import RelationalGraphWithCuts
from egif_parser_dau import parse_egif
from model_materialization import materialization_ratio, materialize_egi
from model_revision import assert_fact
from world_scroll import m_view


class UnrepresentableAtomError(ValueError):
    """An unknown whose labels cannot be rendered as parseable EGIF — refused
    and counted by callers, never silently mangled (spec §3)."""


@dataclass(frozen=True)
class KyteProfile:
    """Species-parametrization seam: capacity bounds for the standing
    sign-vocabulary (S), action-repertoire (A), and question (alt) registers."""
    s_capacity: int = 32
    a_capacity: int = 32
    alt_capacity: int = 64


class BoundedRegister:
    """Capacity-bounded vocabulary register with LRU displacement, counted
    never silent — now with the snapshot/restore pair every real standing
    register in the codebase carries (V.6 dead)."""

    def __init__(self, capacity: int):
        self._capacity = capacity
        self._touch: Dict[str, int] = {}
        self._seq = 0
        self.admitted = 0
        self.displaced = 0

    def __len__(self) -> int:
        return len(self._touch)

    def __contains__(self, term: str) -> bool:
        return term in self._touch

    @property
    def terms(self) -> List[str]:
        return sorted(self._touch)

    def admit(self, term: str) -> Optional[str]:
        self._seq += 1
        if term in self._touch:
            self._touch[term] = self._seq
            return None
        displaced: Optional[str] = None
        if self._touch and len(self._touch) >= self._capacity:
            oldest_seq = min(self._touch.values())
            oldest = sorted(t for t, s in self._touch.items() if s == oldest_seq)[0]
            del self._touch[oldest]
            self.displaced += 1
            displaced = oldest
        self._touch[term] = self._seq
        self.admitted += 1
        return displaced

    def snapshot(self) -> dict:
        return {"capacity": self._capacity, "seq": self._seq,
                "touch": sorted(self._touch.items(), key=lambda kv: kv[1]),
                "admitted": self.admitted, "displaced": self.displaced}

    @staticmethod
    def restore(state: dict) -> "BoundedRegister":
        reg = BoundedRegister(int(state["capacity"]))
        reg._seq = int(state["seq"])
        reg._touch = {t: int(s) for t, s in state.get("touch", [])}
        reg.admitted = int(state.get("admitted", 0))
        reg.displaced = int(state.get("displaced", 0))
        return reg


def _admit_tracked(register: BoundedRegister, term: str,
                   admitted: List[str], displaced: List[str]) -> None:
    is_new = term not in register
    out = register.admit(term)
    if is_new:
        admitted.append(term)
    if out is not None:
        displaced.append(out)


# --------------------------------------------------------------------------- #
# Atom rendering — V.4 dead here                                              #
# --------------------------------------------------------------------------- #

def atom_and_denial_egif(relation: str, labels: Sequence[Optional[str]]
                         ) -> Tuple[str, str]:
    """Render ``(relation, labels)`` as (atom, denial) EGIF. A generic slot
    (None) becomes a defining variable (``*x``, ``*x2``, …); a constant slot
    is quoted. The result is VERIFICATION-PARSED: the atom must parse back to
    exactly ``(relation, labels)`` (generic slots as generic vertices), else
    ``UnrepresentableAtomError`` — refuse, never mangle."""
    parts: List[str] = []
    var_i = 0
    for l in labels:
        if l is None:
            var_i += 1
            parts.append("*x" if var_i == 1 else f"*x{var_i}")
        else:
            parts.append(f'"{l}"')
    atom = f"({relation}{''.join(' ' + p for p in parts)})"
    try:
        g = parse_egif(atom)
        edges = list(g.E)
        assert len(edges) == 1
        e = edges[0]
        got_rel = g.rel[e.id]
        got_labels = tuple(g.get_vertex(v).label for v in g.nu.get(e.id, ()))
    except Exception as exc:
        raise UnrepresentableAtomError(
            f"cannot render ({relation} {list(labels)!r}) as EGIF: {exc}")
    if got_rel != relation or got_labels != tuple(labels):
        raise UnrepresentableAtomError(
            f"({relation} {list(labels)!r}) does not survive the EGIF "
            f"round-trip (got ({got_rel} {list(got_labels)!r})) — refused")
    return atom, f"~[ {atom} ]"


# --------------------------------------------------------------------------- #
# The trace                                                                   #
# --------------------------------------------------------------------------- #

def _sheet_atoms(egi: RelationalGraphWithCuts
                 ) -> Set[Tuple[str, Tuple[Optional[str], ...]]]:
    """M's sheet-level ground atoms as (relation, labels) through m_view;
    generic vertices read as None."""
    egi = m_view(egi)
    out: Set[Tuple[str, Tuple[Optional[str], ...]]] = set()
    for e in egi.E:
        if e.id in egi.rel and area_of(egi, e.id) == egi.sheet:
            labels = tuple(egi.get_vertex(v).label for v in egi.nu.get(e.id, ()))
            out.add((egi.rel[e.id], labels))
    return out


def _atom_keys(atoms: Set[Tuple[str, Tuple[Optional[str], ...]]]
               ) -> Tuple[str, ...]:
    return tuple(sorted(alt_key(r, labels) for r, labels in atoms))


@dataclass(frozen=True)
class TraceResult:
    key: str
    relation: str
    labels: Tuple[Optional[str], ...]
    atom_egif: str
    denial_egif: str
    materiality: Materiality
    s_admitted: Tuple[str, ...]
    s_displaced: Tuple[str, ...]
    a_admitted: Tuple[str, ...]
    a_displaced: Tuple[str, ...]


def trace_unknown(
    m_egi: RelationalGraphWithCuts,
    relation: str,
    labels: Sequence[Optional[str]],
    *,
    s_register: BoundedRegister,
    a_register: BoundedRegister,
) -> TraceResult:
    """Trace the assert/deny branches of an UNKNOWN on a dry-run copy of M
    (never written back) and DISCOVER the materiality — the Task-4 algorithm
    (which withstood Examination V) in its new housing."""
    labels = tuple(labels)
    atom_egif, denial_egif = atom_and_denial_egif(relation, labels)

    base = m_view(m_egi)
    base_atoms = _sheet_atoms(materialize_egi(base)[0])
    atom_key_t = (relation, labels)

    true_egi = assert_fact(base, atom_egif)
    true_atoms = _sheet_atoms(materialize_egi(true_egi)[0])
    false_egi = assert_fact(base, denial_egif)
    false_atoms = _sheet_atoms(materialize_egi(false_egi)[0])

    extra_t = true_atoms - base_atoms - {atom_key_t}
    extra_f = false_atoms - base_atoms - {atom_key_t}

    k3_true: Optional[Tuple[int, int]] = None
    k3_false: Optional[Tuple[int, int]] = None
    if extra_t != extra_f:
        tier = "material"
    elif extra_t or extra_f:
        tier = "bare"
    else:
        # K3 honesty check rather than assuming "spurious".
        kt = materialization_ratio(true_egi)
        kf = materialization_ratio(false_egi)
        k3_true = (kt.explicit, kt.derived)
        k3_false = (kf.explicit, kf.derived)
        tier = "spurious" if k3_true == k3_false else "bare"

    # "Relations that differ between branches": relations present on one side
    # only, plus relations whose ATOM sets differ even where both sides name
    # the relation. Only a material tier carries a divergence.
    if tier == "material":
        rels_t = {r for r, _ in extra_t}
        rels_f = {r for r, _ in extra_f}
        diverging = tuple(sorted(
            (rels_t ^ rels_f) | {r for r, _ in (extra_t ^ extra_f)}))
    else:
        diverging = ()

    materiality = Materiality(
        tier=tier, diverging=diverging,
        extra_true=_atom_keys(extra_t), extra_false=_atom_keys(extra_f),
        k3_true=k3_true, k3_false=k3_false)

    s_admitted: List[str] = []
    s_displaced: List[str] = []
    for rel in sorted({r for r, _ in extra_t} | {r for r, _ in extra_f}):
        _admit_tracked(s_register, f"derivable:{rel}", s_admitted, s_displaced)
    if tier == "material":
        _admit_tracked(s_register, f"distinction:{relation}", s_admitted, s_displaced)

    a_admitted: List[str] = []
    a_displaced: List[str] = []
    _admit_tracked(a_register, f"resolve:{relation}", a_admitted, a_displaced)
    if tier == "material":
        _admit_tracked(a_register, f"condition-on:{relation}", a_admitted, a_displaced)
        for rel in sorted({r for r, _ in extra_t}):
            _admit_tracked(a_register, f"derive-via:{rel}", a_admitted, a_displaced)

    return TraceResult(
        key=alt_key(relation, labels), relation=relation, labels=labels,
        atom_egif=atom_egif, denial_egif=denial_egif, materiality=materiality,
        s_admitted=tuple(s_admitted), s_displaced=tuple(s_displaced),
        a_admitted=tuple(a_admitted), a_displaced=tuple(a_displaced))


__all__ = [
    "KyteProfile", "BoundedRegister", "UnrepresentableAtomError",
    "atom_and_denial_egif", "TraceResult", "trace_unknown",
]
```

Sanity anchor: with `M0`'s law, tracing `("swan", ("Dover",))` must yield
`tier == "material"` and `diverging == ("white",)` — exactly what
`test_material_through_the_law` pins.

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_alternative_trace.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/alternative_trace.py tests/test_alternative_trace.py
git commit -m "Task 3: alternative_trace — dry-run trace with V.4 fix (defining variables, verification parse, refuse-not-mangle)"
```

---

### Task 4: `trace_step` — the PEEL-twin chain step

**Files:**
- Modify: `src/alternative_trace.py` (append), `src/proof_character.py:103`
- Modify: `src/alternative_index.py` (append `record_from_trace_step`)
- Test: `tests/test_alternative_trace.py` (append)

**Interfaces:**
- Consumes: `proof_authoring.ProofChain.apply_derived`; Task 3's `trace_unknown`.
- Produces: `TRACE_ALTERNATIVES = "TRACE_ALTERNATIVES"`;
  `trace_step(pc, relation, labels, *, s_register, a_register, note=None, branch=None) -> TraceResult`;
  `trace_batch(pc, unknowns, *, s_register, a_register, budget=8) -> TraceBatch`
  where `TraceBatch(results: List[TraceResult], refused_budget: List[str], unrepresentable: List[str])`;
  `alternative_index.record_from_trace_step(step) -> AlternativeRecord`.

- [ ] **Step 1: Append failing tests to `tests/test_alternative_trace.py`**

```python
import eg_navigation as nav
from alternative_index import record_from_trace_step
from alternative_trace import TRACE_ALTERNATIVES, trace_batch, trace_step
from proof_authoring import ProofChain
from world_scroll import m_view, wrap_m


def _chain_from(m_egif: str) -> ProofChain:
    wrapped, _ = wrap_m(parse_egif(m_egif))
    return ProofChain(wrapped)


class TestTraceStep:
    def test_recorded_earned_and_identity(self):
        pc = _chain_from(M0)
        before = pc.current
        s, a = _registers()
        tr = trace_step(pc, "swan", ("Dover",), s_register=s, a_register=a)
        step = pc.to_chain().steps[-1]
        assert step.rule_name == TRACE_ALTERNATIVES
        p = step.parameters
        assert p["act"] == "alternatives_traced" and p["earned"] is True
        assert p["tier"] == tr.materiality.tier == "material"
        assert p["labels"] == ["Dover"]
        assert p["key"] == 'swan("Dover")'
        # Identity transform, fresh state, m_view untouched.
        assert step.from_state_id != step.to_state_id
        assert nav.same_graph(m_view(pc.current), m_view(before))

    def test_trace_is_neutral_for_proof_character(self):
        from proof_character import character_of_chain
        pc = _chain_from(M0)
        s, a = _registers()
        trace_step(pc, "swan", ("Dover",), s_register=s, a_register=a)
        assert character_of_chain(pc.to_chain()).character == "corollarial"

    def test_record_from_trace_step(self):
        pc = _chain_from(M0)
        s, a = _registers()
        trace_step(pc, "loves", ("Ciel", None), s_register=s, a_register=a)
        step = pc.to_chain().steps[-1]
        rec = record_from_trace_step(step)
        assert rec.key == 'loves("Ciel",*)'
        assert rec.labels == ("Ciel", None)
        assert rec.traced_by == step.step_id
        assert rec.status == "traced"

    def test_batch_budget_count_or_refuse(self):
        pc = _chain_from(M0)
        s, a = _registers()
        unknowns = [("swan", ("Dover",)), ("black", ("Dover",)),
                    ("swan", ("Dover",))]          # duplicate → one trace
        batch = trace_batch(pc, unknowns, s_register=s, a_register=a, budget=1)
        assert len(batch.results) == 1
        assert batch.refused_budget == ['black("Dover")']

    def test_batch_counts_unrepresentable(self):
        pc = _chain_from(M0)
        s, a = _registers()
        batch = trace_batch(pc, [("said", ('a "quote"',))],
                            s_register=s, a_register=a)
        assert batch.results == []
        assert len(batch.unrepresentable) == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_alternative_trace.py -q`
Expected: FAIL — `ImportError: cannot import name 'TRACE_ALTERNATIVES'`

- [ ] **Step 3: Implement**

Append to `src/alternative_trace.py`:

```python
TRACE_ALTERNATIVES = "TRACE_ALTERNATIVES"


def trace_step(pc, relation: str, labels: Sequence[Optional[str]], *,
               s_register: BoundedRegister, a_register: BoundedRegister,
               note: Optional[str] = None, branch: Optional[str] = None
               ) -> TraceResult:
    """Record the trace as a PEEL-twin chain step (ruling R-A): an identity
    transform (fresh state, never a self-loop) whose params carry the trace
    actually run against the chain's current state — earned at record time,
    re-checkable forever (the gate recomputes it, Task 10)."""
    tr = trace_unknown(pc.current, relation, labels,
                       s_register=s_register, a_register=a_register)
    m = tr.materiality
    params = {
        "act": "alternatives_traced", "earned": True,
        "relation": relation,
        "labels": ["*" if l is None else l for l in tr.labels],
        "key": tr.key,
        "atom_egif": tr.atom_egif, "denial_egif": tr.denial_egif,
        "tier": m.tier, "diverging": list(m.diverging),
        "extra_true": list(m.extra_true), "extra_false": list(m.extra_false),
        "k3_true": list(m.k3_true) if m.k3_true is not None else None,
        "k3_false": list(m.k3_false) if m.k3_false is not None else None,
        "s_admitted": list(tr.s_admitted), "s_displaced": list(tr.s_displaced),
        "a_admitted": list(tr.a_admitted), "a_displaced": list(tr.a_displaced),
    }
    pc.apply_derived(TRACE_ALTERNATIVES, lambda g: g,
                     note=note or f"trace: {tr.key} → {m.tier}",
                     params=params, branch=branch)
    return tr


@dataclass(frozen=True)
class TraceBatch:
    results: Tuple[TraceResult, ...]
    refused_budget: Tuple[str, ...]        # keys refused by the trace budget
    unrepresentable: Tuple[str, ...]       # reprs refused by rendering


def trace_batch(pc, unknowns, *, s_register: BoundedRegister,
                a_register: BoundedRegister, budget: int = 8) -> TraceBatch:
    """Trace up to ``budget`` distinct unknowns (first-occurrence order);
    the rest are REFUSED AND COUNTED (count-or-refuse, never silent).
    Unrepresentable unknowns are counted separately."""
    seen: Set[Tuple[str, Tuple[Optional[str], ...]]] = set()
    results: List[TraceResult] = []
    refused: List[str] = []
    unrepresentable: List[str] = []
    for relation, labels in unknowns:
        key_t = (relation, tuple(labels))
        if key_t in seen:
            continue
        seen.add(key_t)
        try:
            key = alt_key(relation, tuple(labels))
        except Exception:
            key = repr(key_t)
        if len(results) >= budget:
            refused.append(key)
            continue
        try:
            results.append(trace_step(pc, relation, tuple(labels),
                                      s_register=s_register,
                                      a_register=a_register))
        except UnrepresentableAtomError:
            unrepresentable.append(key)
    return TraceBatch(results=tuple(results), refused_budget=tuple(refused),
                      unrepresentable=tuple(unrepresentable))
```

Extend `__all__` with `"TRACE_ALTERNATIVES", "trace_step", "TraceBatch", "trace_batch"`.

Modify `src/proof_character.py` line 103:

```python
NEUTRAL_RULES = frozenset({"PEEL", "QUOTE", "TRACE_ALTERNATIVES"})
```

(A trace record, like a verdict record, is an act, not an inference.)

Append to `src/alternative_index.py`:

```python
def record_from_trace_step(step) -> AlternativeRecord:
    """Rebuild the index entry from a recorded TRACE step's params alone —
    the index is a cache over the chain, never a second authority."""
    p = step.parameters or {}
    if p.get("act") != "alternatives_traced":
        raise ValueError(f"step {step.step_id} is not a trace step")
    labels = tuple(None if l == "*" else l for l in p["labels"])
    return AlternativeRecord(
        key=p["key"], relation=p["relation"], labels=labels,
        alternatives=(p["atom_egif"], p["denial_egif"]),
        traced_by=step.step_id,
        materiality=Materiality(
            tier=p["tier"], diverging=tuple(p.get("diverging", ())),
            extra_true=tuple(p.get("extra_true", ())),
            extra_false=tuple(p.get("extra_false", ())),
            k3_true=tuple(p["k3_true"]) if p.get("k3_true") is not None else None,
            k3_false=tuple(p["k3_false"]) if p.get("k3_false") is not None else None,
        ))
```

Extend that module's `__all__` with `"record_from_trace_step"`.

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_alternative_trace.py tests/test_alternative_index.py -q`
Expected: PASS. Also run `uv run pytest tests/test_m_steps.py -q` (proof_character change is additive; must stay green).

- [ ] **Step 5: Commit**

```bash
git add src/alternative_trace.py src/alternative_index.py src/proof_character.py tests/test_alternative_trace.py
git commit -m "Task 4: trace_step — the PEEL-twin TRACE_ALTERNATIVES step + record_from_trace_step + batch budget"
```

---

### Task 5: Producer — structured unknowns from the peel (AC1)

**Files:**
- Modify: `src/semantic_game.py` (`SemanticResult`, `evaluate`, `_holds`, `_atom_verdict`)
- Modify: `src/m_steps.py` (`peel_step` params)
- Test: `tests/test_unknown_atoms.py`

**Interfaces:**
- Produces: `SemanticResult.unknown_atoms: Tuple[Tuple[str, Tuple[Optional[str], ...]], ...]`
  (deterministic order; constant slots carry labels, generic slots `None`);
  `peel_step` records `params["unknown_atoms"]` as `[[rel, [label-or-"*", ...]], ...]`.

**Collection rule (exactly two sites, to avoid witness-combo spray):**
1. `_atom_verdict`: when the verdict is UNKNOWN **and every argument vertex is a
   constant** → collect `(rel, constant labels)`. (Ground unknowns — the Task-4 wire.)
2. `_holds`: at the open-world existential lift (the `v = UNKNOWN` return) →
   for each edge directly in this area **with at least one non-constant slot**,
   collect `(rel, labels)` where constants carry labels and every other slot is
   `None`. (The generic question, once per area, not per combo.)

- [ ] **Step 1: Write the failing tests**

```python
"""AC1 — the peel surfaces structured UNKNOWN atoms (the producer)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain_oracle import CorpusOracle
from egif_parser_dau import parse_egif
from m_steps import peel_step
from proof_authoring import ProofChain
from semantic_game import evaluate
from world_scroll import wrap_m

LAW = '~[ (swan *x) ~[ (white x) ] ]'
M0 = f'(swan "Ciel") (white "Ciel") {LAW}'


def _oracle(m_egif=M0):
    from model_materialization import materialize_egi
    m, _ = materialize_egi(parse_egif(m_egif))
    return CorpusOracle([("M", m)])


class TestUnknownAtoms:
    def test_ground_unknown_collected(self):
        r = evaluate(parse_egif('(swan "Dover")'), _oracle())
        assert r.verdict.value == "unknown"
        assert r.unknown_atoms == (("swan", ("Dover",)),)

    def test_true_verdict_collects_nothing(self):
        r = evaluate(parse_egif('(swan "Ciel")'), _oracle())
        assert r.verdict.value == "true"
        assert r.unknown_atoms == ()

    def test_existential_unknown_has_generic_slot(self):
        r = evaluate(parse_egif('(black *x)'), _oracle())
        assert r.verdict.value == "unknown"
        assert ("black", (None,)) in r.unknown_atoms

    def test_ground_unknown_inside_negation_collected(self):
        r = evaluate(parse_egif('~[ (swan "Dover") ~[ (white "Dover") ] ]'),
                     _oracle())
        assert ("swan", ("Dover",)) in r.unknown_atoms

    def test_deterministic_order(self):
        a = evaluate(parse_egif('(swan "Dover") (black "Dover")'), _oracle())
        b = evaluate(parse_egif('(swan "Dover") (black "Dover")'), _oracle())
        assert a.unknown_atoms == b.unknown_atoms
        assert list(a.unknown_atoms) == sorted(a.unknown_atoms, key=repr)


class TestPeelStepCarriesUnknowns:
    def test_params_carry_unknown_atoms(self):
        wrapped, _ = wrap_m(parse_egif(M0))
        pc = ProofChain(wrapped)
        peel_step(pc, '(swan "Dover") (black *x)')
        p = pc.to_chain().steps[-1].parameters
        assert ["swan", ["Dover"]] in p["unknown_atoms"]
        assert ["black", ["*"]] in p["unknown_atoms"]
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_unknown_atoms.py -q`
Expected: FAIL — `AttributeError: ... no attribute 'unknown_atoms'` (or unexpected keyword)

- [ ] **Step 3: Implement**

In `src/semantic_game.py`:

(a) Add the field to `SemanticResult` (after `witness_vertex_ids`):

```python
    unknown_atoms: Tuple[Tuple[str, Tuple[Optional[str], ...]], ...] = ()
```

(with docstring line: "``unknown_atoms``: the structured doubt harvest — every
atom the oracle could not decide, constants labelled, generic slots ``None``;
the producer seam of the alternative-index loop (spec §6).")

(b) In `evaluate`, initialize the collector before `_holds` and thread it into
the result:

```python
        self._unknowns: set = set()
        transcript: List[str] = []
        verdict, binding = self._holds(egi.sheet, {}, depth=0, transcript=transcript)
        ...
        return SemanticResult(
            verdict=verdict,
            transcript=transcript,
            winning_witness=decisive if verdict is Verdict3.TRUE else None,
            counterexample=decisive if verdict is Verdict3.FALSE else None,
            witness_vertex_ids=decisive_ids if verdict is not Verdict3.UNKNOWN else None,
            unknown_atoms=tuple(sorted(self._unknowns, key=repr)),
        )
```

(c) In `_atom_verdict`, collect the all-constant UNKNOWN (replace the final
two lines):

```python
        if present:
            return Verdict3.TRUE
        if not self.closed and all(v in self._const_label for v in verts):
            self._unknowns.add(
                (rel, tuple(self._const_label[v] for v in verts)))
        return Verdict3.FALSE if self.closed else Verdict3.UNKNOWN
```

(d) In `_holds`, at the open-world lift (immediately after
`v = Verdict3.UNKNOWN` inside `if v is not Verdict3.TRUE and not self.closed:`),
collect the area's generic-slotted atoms once:

```python
        v = _or3(disjuncts)
        # Open world: an unsatisfied existential might be satisfied by a larger M.
        if v is not Verdict3.TRUE and not self.closed:
            v = Verdict3.UNKNOWN
            for eid in contents:
                if eid in self._edge_ids:
                    labels = tuple(self._const_label.get(vid)
                                   for vid in self._egi.nu[eid])
                    if any(l is None for l in labels):
                        self._unknowns.add(
                            (self._egi.get_relation_name(eid), labels))
        self._note(transcript, depth, pol, area_id, beta, v)
        return v, None
```

In `src/m_steps.py`, add to `peel_step`'s `params` dict (after `"summary"`):

```python
        "unknown_atoms": [
            [rel, ["*" if l is None else l for l in labels]]
            for rel, labels in result.unknown_atoms
        ],
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_unknown_atoms.py tests/test_semantic_game.py tests/test_m_steps.py tests/test_corpus_polarity_discipline.py -q`
Expected: PASS — the existing semantic-game and gate suites must be untouched by the additive field.

- [ ] **Step 5: Commit**

```bash
git add src/semantic_game.py src/m_steps.py tests/test_unknown_atoms.py
git commit -m "Task 5: producer — SemanticResult.unknown_atoms + peel_step carries them (AC1)"
```

---

### Task 6: The AS law, settlement, and rebuild (AC6/AC8/AC9 units)

**Files:**
- Modify: `src/alternative_index.py` (append)
- Test: `tests/test_alternative_law.py`

**Interfaces:**
- Consumes: chain objects with `.steps` (each with `.step_id`, `.parameters`,
  `.from_state_id`, `.to_state_id`) and `.states: Dict[str, egi]`
  (`ProofChain.to_chain()` / `tomos_service.TransformationChain`);
  `alternative_trace.trace_unknown/atom_and_denial_egif` (lazy imports).
- Produces:
  `AlternativeRegister.settle_from_chain(chain) -> List[str]`;
  `AlternativeRegister.rebuild_from_chain(chain, *, capacity=64) -> AlternativeRegister` (staticmethod);
  `AlternativeLawReport(violations: Tuple[str, ...], horizon: Tuple[str, ...])` with `.ok`;
  `run_alternative_record(record, chain, *, trace_fn=None) -> AlternativeLawReport`;
  `attest_alternative_record(record, chain, *, trace_fn=None) -> None` (raises `AlternativeLawViolation`).

**The acknowledged-act rule** (mirrors the polarity gate's `_acknowledged`):

```python
_ACK_ACTS = ("m_enlargement", "m_retraction", "m_revision",
             "world_withdrawal", "m_discharge")

def _acknowledged(params) -> bool:
    act = (params or {}).get("act")
    if act == "quotation":
        return (params or {}).get("provenance") == "oracle-answer"
    return act in _ACK_ACTS
```

- [ ] **Step 1: Write the failing tests**

```python
"""AS1–AS4 — the AlternativeRecord law (spec §4) + settlement + rebuild."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import dataclasses

import pytest

from alternative_index import (
    AlternativeLawViolation, AlternativeRecord, AlternativeRegister,
    Materiality, alt_key, attest_alternative_record, record_from_trace_step,
    run_alternative_record,
)
from alternative_trace import BoundedRegister, trace_step
from egif_parser_dau import parse_egif
from m_steps import admit_step, peel_step
from proof_authoring import ProofChain
from world_scroll import wrap_m

LAW = '~[ (swan *x) ~[ (white x) ] ]'
M0 = f'(swan "Ciel") (white "Ciel") {LAW}'


def _chain():
    wrapped, _ = wrap_m(parse_egif(M0))
    return ProofChain(wrapped)


def _traced(pc):
    s, a = BoundedRegister(32), BoundedRegister(32)
    peel_step(pc, '(swan "Dover")')
    peel_id = pc.to_chain().steps[-1].step_id
    trace_step(pc, "swan", ("Dover",), s_register=s, a_register=a)
    step = pc.to_chain().steps[-1]
    rec = dataclasses.replace(record_from_trace_step(step),
                              emerged_from=peel_id)
    return rec, step


class TestLaw:
    def test_honest_record_passes(self):
        pc = _chain()
        rec, _ = _traced(pc)
        attest_alternative_record(rec, pc.to_chain())     # no raise

    def test_as1_bites_on_content_mismatch(self):
        pc = _chain()
        rec, _ = _traced(pc)
        doctored = dataclasses.replace(rec, relation="black",
                                       key=alt_key("black", ("Dover",)),
                                       alternatives=('(black "Dover")',
                                                     '~[ (black "Dover") ]'))
        with pytest.raises(AlternativeLawViolation, match="AS1"):
            attest_alternative_record(doctored, pc.to_chain())

    def test_as2_bites_on_doctored_materiality(self):
        pc = _chain()
        rec, _ = _traced(pc)
        doctored = dataclasses.replace(
            rec, materiality=Materiality(tier="spurious"))
        with pytest.raises(AlternativeLawViolation, match="AS2"):
            attest_alternative_record(doctored, pc.to_chain())

    def test_as3_bites_on_unlicensed_resolution(self):
        pc = _chain()
        rec, _ = _traced(pc)
        # Cite the PEEL step (not an acknowledged M-act) as the resolver.
        doctored = dataclasses.replace(rec, resolved_by=rec.emerged_from,
                                       selection=rec.alternatives[0])
        with pytest.raises(AlternativeLawViolation, match="AS3"):
            attest_alternative_record(doctored, pc.to_chain())

    def test_as4_horizon_names_untraced(self):
        rec = AlternativeRecord(
            key=alt_key("swan", ("Dover",)), relation="swan",
            labels=("Dover",),
            alternatives=('(swan "Dover")', '~[ (swan "Dover") ]'))
        pc = _chain()
        report = run_alternative_record(rec, pc.to_chain())
        assert report.ok                       # untraced is honest, not illegal
        assert any("untraced" in h for h in report.horizon)


class TestSettlement:
    def test_settles_citing_the_admitting_step(self):
        pc = _chain()
        rec, _ = _traced(pc)
        reg = AlternativeRegister()
        reg.note(rec, round_idx=0)
        admit_step(pc, '(swan "Dover")', disposition="new_fact")
        admit_id = pc.to_chain().steps[-1].step_id
        resolved = reg.settle_from_chain(pc.to_chain())
        assert resolved == [rec.key]
        got = reg.get(rec.key)
        assert got.resolved_by == admit_id
        assert got.selection == '(swan "Dover")'
        attest_alternative_record(got, pc.to_chain())      # AS3 holds

    def test_denial_branch_settles_too(self):
        pc = _chain()
        rec, _ = _traced(pc)
        reg = AlternativeRegister()
        reg.note(rec, round_idx=0)
        admit_step(pc, '~[ (swan "Dover") ]', disposition="new_fact")
        reg.settle_from_chain(pc.to_chain())
        assert reg.get(rec.key).selection == '~[ (swan "Dover") ]'

    def test_no_settlement_without_acknowledged_act(self):
        pc = _chain()
        rec, _ = _traced(pc)
        reg = AlternativeRegister()
        reg.note(rec, round_idx=0)
        assert reg.settle_from_chain(pc.to_chain()) == []


class TestRebuild:
    def test_register_rebuilds_from_chain_alone(self):
        pc = _chain()
        rec, _ = _traced(pc)
        admit_step(pc, '(swan "Dover")', disposition="new_fact")
        reg = AlternativeRegister()
        reg.note(rec, round_idx=0)
        reg.settle_from_chain(pc.to_chain())
        rebuilt = AlternativeRegister.rebuild_from_chain(pc.to_chain())
        got = rebuilt.get(rec.key)
        assert got is not None
        assert got.status == "resolved"
        assert got.traced_by == reg.get(rec.key).traced_by
        assert got.resolved_by == reg.get(rec.key).resolved_by
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_alternative_law.py -q`
Expected: FAIL — `ImportError: cannot import name 'attest_alternative_record'`

- [ ] **Step 3: Implement (append to `src/alternative_index.py`)**

```python
_ACK_ACTS = ("m_enlargement", "m_retraction", "m_revision",
             "world_withdrawal", "m_discharge")


def _acknowledged(params) -> bool:
    act = (params or {}).get("act")
    if act == "quotation":
        return (params or {}).get("provenance") == "oracle-answer"
    return act in _ACK_ACTS


def _atom_holds(m, relation: str, labels: Tuple[Optional[str], ...]) -> bool:
    """Does a sheet-level ground atom of ``m`` match (relation, labels)?
    A generic slot (None) matches any binding."""
    from eg_navigation import area_of
    for e in sorted(m.E, key=lambda e: e.id):
        if m.rel.get(e.id) != relation:
            continue
        if area_of(m, e.id) != m.sheet:
            continue
        got = tuple(m.get_vertex(v).label for v in m.nu.get(e.id, ()))
        if len(got) != len(labels):
            continue
        if all(l is None or l == g for l, g in zip(labels, got)):
            return True
    return False


def _denial_stands(m, denial_egif: str) -> bool:
    """Does a SHEET-LEVEL cut of ``m`` match the denial shape? (Sheet-level
    only: an entertained exhibit's inner ~[P] is nested and must not settle
    anything — mention is not assertion.)"""
    from eg_navigation import same_graph
    from egif_parser_dau import parse_egif
    from quotation_overlay import lift_cut
    shape = parse_egif(denial_egif)
    cut_ids = {c.id for c in m.Cut}
    for cid in sorted(m.area.get(m.sheet, frozenset())):
        if cid in cut_ids and same_graph(lift_cut(m, cid), shape):
            return True
    return False


# --- settlement + rebuild (methods appended onto AlternativeRegister) --------

def _settle_from_chain(self, chain) -> List[str]:
    """Resolve every open record whose branch some acknowledged step settled
    (spec §2): scan forward from the record's emergence for the EARLIEST
    acknowledged step whose to_state's m_view holds the atom (→ selection =
    atom) or a sheet-level denial (→ selection = denial); cite that step."""
    from world_scroll import m_view
    steps = list(chain.steps)
    index_of = {s.step_id: i for i, s in enumerate(steps)}
    resolved: List[str] = []
    for key in [r.key for r in self.open_records()]:
        rec = self._records[key]
        start = index_of.get(rec.emerged_from, 0) if rec.emerged_from else 0
        atom_egif, denial_egif = rec.alternatives[0], rec.alternatives[1]
        for s in steps[start:]:
            if not _acknowledged(s.parameters):
                continue
            m = m_view(chain.states[s.to_state_id])
            if _atom_holds(m, rec.relation, rec.labels):
                self.resolve(key, resolved_by=s.step_id, selection=atom_egif)
                resolved.append(key)
                break
            if _denial_stands(m, denial_egif):
                self.resolve(key, resolved_by=s.step_id, selection=denial_egif)
                resolved.append(key)
                break
    return resolved


def _rebuild_from_chain(chain, *, capacity: int = 64) -> "AlternativeRegister":
    """Re-derive the whole register from the chain alone — the proof that the
    index never became a second authority (spec §2, AC8)."""
    from alternative_trace import UnrepresentableAtomError, atom_and_denial_egif
    reg = AlternativeRegister(capacity=capacity)
    for i, s in enumerate(chain.steps):
        p = s.parameters or {}
        if p.get("act") == "peel":
            for rel, labels in (p.get("unknown_atoms") or []):
                labs = tuple(None if l == "*" else l for l in labels)
                try:
                    atom, denial = atom_and_denial_egif(rel, labs)
                except UnrepresentableAtomError:
                    continue                      # was refused at trace time too
                reg.note(AlternativeRecord(
                    key=alt_key(rel, labs), relation=rel, labels=labs,
                    alternatives=(atom, denial), emerged_from=s.step_id,
                    emerged_round=i), round_idx=i)
        elif p.get("act") == "alternatives_traced":
            reg.note(record_from_trace_step(s), round_idx=i)
    reg.settle_from_chain(chain)
    return reg


AlternativeRegister.settle_from_chain = _settle_from_chain
AlternativeRegister.rebuild_from_chain = staticmethod(_rebuild_from_chain)


# --- the law -----------------------------------------------------------------

@dataclass(frozen=True)
class AlternativeLawReport:
    violations: Tuple[str, ...] = ()
    horizon: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.violations


def _default_trace_fn(m_egi, relation, labels):
    from alternative_trace import BoundedRegister, trace_unknown
    return trace_unknown(m_egi, relation, labels,
                         s_register=BoundedRegister(32),
                         a_register=BoundedRegister(32)).materiality


def run_alternative_record(record: AlternativeRecord, chain, *,
                           trace_fn=None) -> AlternativeLawReport:
    """AS1–AS4, non-raising (spec §4). ``trace_fn(m_egi, relation, labels)
    -> Materiality`` defaults to the real trace with fresh registers (the
    S/A registers never affect materiality, so recompute is register-free)."""
    from world_scroll import m_view
    trace_fn = trace_fn or _default_trace_fn
    violations: List[str] = []
    horizon: List[str] = []
    steps_by_id = {s.step_id: s for s in chain.steps}
    star_labels = ["*" if l is None else l for l in record.labels]

    # AS1 — index resolves, content matches.
    for ref_name in ("emerged_from", "traced_by", "resolved_by"):
        ref = getattr(record, ref_name)
        if ref is not None and ref not in steps_by_id:
            violations.append(f"AS1: {ref_name}={ref!r} not in chain")
    if record.emerged_from and record.emerged_from in steps_by_id:
        p = steps_by_id[record.emerged_from].parameters or {}
        if p.get("act") == "peel":
            if [record.relation, star_labels] not in (p.get("unknown_atoms") or []):
                violations.append(
                    f"AS1: emerged_from step never surfaced {record.key}")
    if record.traced_by and record.traced_by in steps_by_id:
        p = steps_by_id[record.traced_by].parameters or {}
        if p.get("act") != "alternatives_traced":
            violations.append("AS1: traced_by is not a trace step")
        elif (p.get("relation") != record.relation
              or p.get("labels") != star_labels
              or tuple(record.alternatives) != (p.get("atom_egif"),
                                                p.get("denial_egif"))):
            violations.append(
                f"AS1: trace step params do not match record {record.key}")

    # AS2 — the trace recomputes.
    if (record.traced_by and record.traced_by in steps_by_id
            and record.materiality is not None
            and not any(v.startswith("AS1") for v in violations)):
        step = steps_by_id[record.traced_by]
        recomputed = trace_fn(chain.states[step.from_state_id],
                              record.relation, record.labels)
        if recomputed != record.materiality:
            violations.append(
                f"AS2: materiality does not recompute for {record.key} "
                f"(recorded {record.materiality.tier!r}, "
                f"recomputed {recomputed.tier!r})")

    # AS3 — resolution licensed.
    if record.resolved_by is not None:
        if record.selection is None:
            violations.append("AS3: resolved without a selection")
        if record.resolved_by in steps_by_id:
            s = steps_by_id[record.resolved_by]
            if not _acknowledged(s.parameters):
                violations.append(
                    f"AS3: resolved_by {record.resolved_by} is not an "
                    "acknowledged M-act")
            else:
                m = m_view(chain.states[s.to_state_id])
                atom_settles = _atom_holds(m, record.relation, record.labels)
                denial_settles = _denial_stands(m, record.alternatives[1])
                if record.selection == record.alternatives[0] and not atom_settles:
                    violations.append("AS3: selected atom does not stand in M")
                if record.selection == record.alternatives[1] and not denial_settles:
                    violations.append("AS3: selected denial does not stand in M")

    # AS4 — honest horizon (informational, never a violation).
    if record.traced_by is None:
        horizon.append(f"untraced: {record.key}")
    return AlternativeLawReport(violations=tuple(violations),
                                horizon=tuple(horizon))


def attest_alternative_record(record: AlternativeRecord, chain, *,
                              trace_fn=None) -> None:
    report = run_alternative_record(record, chain, trace_fn=trace_fn)
    if not report.ok:
        raise AlternativeLawViolation("; ".join(report.violations))
```

Extend `__all__` with `"AlternativeLawReport", "run_alternative_record", "attest_alternative_record"`.

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_alternative_law.py tests/test_alternative_index.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/alternative_index.py tests/test_alternative_law.py
git commit -m "Task 6: AS1-AS4 law + attestation + settle_from_chain (cites licensed ink) + rebuild_from_chain"
```

---

### Task 7: Reception classification, quarantine, routing (AC5 units)

**Files:**
- Modify: `src/alternative_index.py` (append `classify_reception`),
  `src/attention_economy.py` (append `QuarantineRegister`)
- Test: `tests/test_alternative_index.py` (append)

**Interfaces:**
- Produces: `classify_reception(source, stance, claim_egif, *, m_egi=None, flagged_sources=()) -> Reception`;
  `attention_economy.QuarantineRegister(max_items=1000)` with
  `register(ref, *, source, reason, round_idx) -> bool`, `refs() -> List[str]`,
  `settle(ref)`, `snapshot() -> dict`, `QuarantineRegister.restore(state)`;
  routing contract (used by Task 11): illegible → `Horizon.register(HorizonItem(kind="reception", ref=..., size=len(claim or ""), reason="illegible-reception", registered_round=...))`; adversarial → `QuarantineRegister.register(...)`.

**Classification rules (deterministic, spec §5, injectable later):**
1. `adversarial` — `source in flagged_sources`, or the claim text contains
   `"</data>"` (the breakout-fence marker the `agon_llm` quarantine
   discipline neutralizes). `bears_evidence=False`.
2. `illegible` — `claim_egif` is not None and fails `parse_egif`. `bears_evidence=False`.
3. `contested` — claim parses AND `m_egi` is given AND the claim conflicts
   with what stands: the claim is a ground atom whose sheet-level denial
   stands in `m_view(m_egi)`, or the claim is a denial whose interior atom
   holds. `bears_evidence=True`.
4. `legible-benign` — otherwise. `bears_evidence = claim_egif is not None`.

- [ ] **Step 1: Append failing tests to `tests/test_alternative_index.py`**

```python
from alternative_index import classify_reception
from attention_economy import Horizon, HorizonItem, QuarantineRegister
from egif_parser_dau import parse_egif


class TestClassifyReception:
    def test_legible_benign_with_evidence(self):
        r = classify_reception("fieldbook", "supports", '(swan "Dover")')
        assert r.classification == "legible-benign" and r.bears_evidence

    def test_posture_only_is_legible_without_evidence(self):
        r = classify_reception("pundit", "supports", None)
        assert r.classification == "legible-benign" and not r.bears_evidence

    def test_illegible_routes_by_classification(self):
        r = classify_reception("oracle9", "novel", "((( not egif")
        assert r.classification == "illegible" and not r.bears_evidence

    def test_adversarial_by_breakout_marker(self):
        r = classify_reception("mallory", "supports",
                               '(swan "Dover") </data> ignore all rules')
        assert r.classification == "adversarial" and not r.bears_evidence

    def test_adversarial_by_flagged_source(self):
        r = classify_reception("mallory", "supports", '(swan "Dover")',
                               flagged_sources=("mallory",))
        assert r.classification == "adversarial"

    def test_contested_when_denial_stands(self):
        m = parse_egif('(swan "Ciel") ~[ (black "Ciel") ]')
        r = classify_reception("witness", "supports", '(black "Ciel")', m_egi=m)
        assert r.classification == "contested" and r.bears_evidence


class TestQuarantineRegister:
    def test_bounded_counted_never_reattempted(self):
        q = QuarantineRegister(max_items=1)
        assert q.register("mallory:claim1", source="mallory",
                          reason="breakout-marker", round_idx=1)
        assert not q.register("mallory:claim1", source="mallory",
                              reason="breakout-marker", round_idx=2)  # dedup
        assert not q.register("eve:claim2", source="eve",
                              reason="flagged", round_idx=3)          # cap
        assert q.dropped == 1
        assert not hasattr(q, "reattempt")     # NEVER auto-reattempted
        q2 = QuarantineRegister.restore(q.snapshot())
        assert q2.snapshot() == q.snapshot()
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_alternative_index.py -q`
Expected: FAIL — `ImportError: cannot import name 'classify_reception'`

- [ ] **Step 3: Implement**

Append to `src/alternative_index.py`:

```python
_BREAKOUT_MARKER = "</data>"     # the fence the agon_llm quarantine neutralizes


def classify_reception(source: str, stance: str, claim_egif: Optional[str], *,
                       m_egi=None, flagged_sources: Sequence[str] = ()
                       ) -> Reception:
    """Classification = contextualization adequacy (spec §5): how much
    checkable context arrived. Claimed standing is stripped at the membrane —
    the classification routes attention, it never grants trust."""
    if source in flagged_sources or (claim_egif and _BREAKOUT_MARKER in claim_egif):
        return Reception(source=source, stance=stance,
                         classification="adversarial", claim_egif=claim_egif,
                         bears_evidence=False)
    if claim_egif is None:
        return Reception(source=source, stance=stance,
                         classification="legible-benign", claim_egif=None,
                         bears_evidence=False)
    from egif_parser_dau import parse_egif
    try:
        claim = parse_egif(claim_egif)
    except Exception:
        return Reception(source=source, stance=stance,
                         classification="illegible", claim_egif=claim_egif,
                         bears_evidence=False)
    if m_egi is not None:
        from world_scroll import m_view
        m = m_view(m_egi)
        conflict = False
        edges = list(claim.E)
        cuts = list(claim.Cut)
        if len(edges) == 1 and not cuts:
            conflict = _denial_stands(m, f"~[ {claim_egif.strip()} ]")
        elif len(cuts) == 1 and not edges:
            inner = [x for x in claim.area.get(cuts[0].id, frozenset())]
            inner_edges = [x for x in inner if x in {e.id for e in claim.E}]
            if len(inner_edges) == 1:
                eid = inner_edges[0]
                labels = tuple(claim.get_vertex(v).label
                               for v in claim.nu.get(eid, ()))
                conflict = _atom_holds(m, claim.rel[eid], labels)
        if conflict:
            return Reception(source=source, stance=stance,
                             classification="contested", claim_egif=claim_egif,
                             bears_evidence=True)
    return Reception(source=source, stance=stance,
                     classification="legible-benign", claim_egif=claim_egif,
                     bears_evidence=True)
```

Extend `__all__` with `"classify_reception"`.

Append to `src/attention_economy.py` (after `Horizon`), and add
`"QuarantineRegister"` to its `__all__`:

```python
class QuarantineRegister:
    """The adversarial cell of the reception taxonomy (spec §5): bounded,
    dedup'd by ref, drops counted, snapshot/restore — and deliberately NO
    reattempt method (quarantine is not the Horizon; nothing leaves it
    without a deliberate act)."""

    def __init__(self, max_items: int = 1000):
        self._max = max_items
        self._items: Dict[str, dict] = {}
        self.dropped = 0

    def register(self, ref: str, *, source: str, reason: str,
                 round_idx: int) -> bool:
        if ref in self._items:
            return False
        if len(self._items) >= self._max:
            self.dropped += 1
            return False
        self._items[ref] = {"source": source, "reason": reason,
                            "round": round_idx}
        return True

    def refs(self) -> List[str]:
        return sorted(self._items)

    def settle(self, ref: str) -> None:
        self._items.pop(ref, None)

    def snapshot(self) -> dict:
        return {"max": self._max, "dropped": self.dropped,
                "items": {k: dict(v) for k, v in sorted(self._items.items())}}

    @staticmethod
    def restore(state: dict) -> "QuarantineRegister":
        q = QuarantineRegister(max_items=int(state.get("max", 1000)))
        q.dropped = int(state.get("dropped", 0))
        q._items = {k: dict(v) for k, v in state.get("items", {}).items()}
        return q
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_alternative_index.py tests/test_attention_economy.py -q`
(If `tests/test_attention_economy.py` does not exist, run the arithmetic-world
suite that exercises the economy: `uv run pytest tests/ -q -k "attention or arithmetic"`.)
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/alternative_index.py src/attention_economy.py tests/test_alternative_index.py
git commit -m "Task 7: reception taxonomy (contextualization adequacy) + QuarantineRegister"
```

---

### Task 8: Consumer — `wants_from_alternatives` (AC4 unit)

**Files:**
- Modify: `src/attention_economy.py` (append)
- Test: `tests/test_wants_from_alternatives.py`

**Interfaces:**
- Consumes: `AlternativeRegister.open_records()`; `alternative_trace.BoundedRegister`
  (`__contains__`); `alternative_index.SourceRecord`.
- Produces: `wants_from_alternatives(register, *, round_idx=0, cost=1.0,
  s_register=None, source_record=None) -> List[Want]` and the named severity
  table `ALTERNATIVE_SEVERITY = {"material": 8.0, "untraced": 4.0, "bare": 2.0}`.

**Rules (spec §6, all of them):** spurious → not emitted; tier → base severity;
distinction already in the S-register (`f"distinction:{record.relation}"`) →
severity halved (the S-register's first reader); reception bonus ×1.25 (one-shot)
only when some reception `bears_evidence` AND `source_record.track_record(source)`
returns a record with `hits > misses`; untracked or posture-only receptions
change nothing. `created_round = record.emerged_round` (older doubts win ties),
`kind="alternative"`, `key=(record.key,)`, `payload=record`.

- [ ] **Step 1: Write the failing tests**

```python
"""AC4 unit — the traced materiality orders the asks (the consumer)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from alternative_index import (
    AlternativeRecord, AlternativeRegister, Materiality, Reception,
    TrackRecord, UntrackedSources, alt_key,
)
from alternative_trace import BoundedRegister
from attention_economy import AttentionEconomy, wants_from_alternatives


def _rec(rel, tier=None, **kw):
    base = dict(key=alt_key(rel, ("Dover",)), relation=rel, labels=("Dover",),
                alternatives=(f'({rel} "Dover")', f'~[ ({rel} "Dover") ]'),
                materiality=Materiality(tier=tier) if tier else None,
                traced_by="step-2" if tier else None)
    base.update(kw)
    return AlternativeRecord(**base)


def _register(*records):
    reg = AlternativeRegister()
    for i, r in enumerate(records):
        reg.note(r, round_idx=i)
    return reg


class TestWantsFromAlternatives:
    def test_severity_by_tier_and_spurious_not_emitted(self):
        reg = _register(_rec("a", "material"), _rec("b", "bare"),
                        _rec("c", None), _rec("d", "spurious"))
        wants = wants_from_alternatives(reg)
        by_rel = {w.payload.relation: w.severity for w in wants}
        assert by_rel == {"a": 8.0, "b": 2.0, "c": 4.0}

    def test_novelty_damping_reads_the_s_register(self):
        s = BoundedRegister(8)
        s.admit("distinction:a")
        reg = _register(_rec("a", "material"), _rec("b", "material"))
        wants = wants_from_alternatives(reg, s_register=s)
        by_rel = {w.payload.relation: w.severity for w in wants}
        assert by_rel["a"] == 4.0        # already-standing distinction: damped
        assert by_rel["b"] == 8.0

    def test_untracked_agreement_earns_exactly_nothing(self):
        agreed = _rec("a", "bare", receptions=(Reception(
            source="stranger", stance="supports",
            classification="legible-benign",
            claim_egif='(a "Dover")', bears_evidence=True),))
        reg = _register(agreed)
        wants = wants_from_alternatives(reg, source_record=UntrackedSources())
        assert wants[0].severity == 2.0            # unchanged

    def test_tracked_positive_source_gives_bounded_bonus(self):
        class OneGoodSource:
            def track_record(self, source):
                return TrackRecord(bets=4, hits=3, misses=1) \
                    if source == "fieldbook" else None
        evidenced = _rec("a", "bare", receptions=(Reception(
            source="fieldbook", stance="supports",
            classification="legible-benign",
            claim_egif='(a "Dover")', bears_evidence=True),))
        reg = _register(evidenced)
        wants = wants_from_alternatives(reg, source_record=OneGoodSource())
        assert wants[0].severity == 2.5            # 2.0 * 1.25, once

    def test_economy_asks_material_first_fifo_does_not(self):
        # The AC4 shape: FIFO (creation order) would ask "b" (bare, older)
        # first; the economy asks "a" (material) first.
        reg = _register(_rec("b", "bare", emerged_round=0),
                        _rec("a", "material", emerged_round=1))
        wants = wants_from_alternatives(reg)
        econ = AttentionEconomy(musement_fraction=0.0)
        for w in wants:
            econ.register(w)
        chosen = econ.choose(1, round_idx=0)
        assert chosen[0].payload.relation == "a"
        fifo = sorted(wants, key=lambda w: (w.created_round, repr(w.key)))
        assert fifo[0].payload.relation == "b"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_wants_from_alternatives.py -q`
Expected: FAIL — `ImportError: cannot import name 'wants_from_alternatives'`

- [ ] **Step 3: Implement (append to `src/attention_economy.py`)**

```python
ALTERNATIVE_SEVERITY = {"material": 8.0, "untraced": 4.0, "bare": 2.0}


def wants_from_alternatives(register, *, round_idx: int = 0, cost: float = 1.0,
                            s_register=None, source_record=None) -> List[Want]:
    """Open AlternativeRecords as wants, severity from the TRACED materiality
    (spec §6): material > untraced (the trace itself is a worthwhile reach) >
    bare; spurious not emitted. A distinction already standing in the
    S-register reads at half severity — the S-register's first reader (V.5
    closed). A reception nudges severity ONLY when it bears evidence AND its
    source has a positive track record; untracked + agrees earns exactly
    nothing (ruling R-B's teeth)."""
    out: List[Want] = []
    for record in register.open_records():
        tier = record.materiality.tier if record.materiality else "untraced"
        if tier == "spurious":
            continue
        severity = ALTERNATIVE_SEVERITY[tier]
        if s_register is not None and f"distinction:{record.relation}" in s_register:
            severity *= 0.5
        if source_record is not None:
            for rec in record.receptions:
                if not rec.bears_evidence:
                    continue
                tr = source_record.track_record(rec.source)
                if tr is not None and tr.hits > tr.misses:
                    severity *= 1.25
                    break                          # bounded, one-shot
        out.append(Want(kind="alternative", key=(record.key,), payload=record,
                        cost=cost, severity=severity,
                        created_round=record.emerged_round))
    return out
```

Add `"wants_from_alternatives"`, `"ALTERNATIVE_SEVERITY"` to `__all__`.

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_wants_from_alternatives.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/attention_economy.py tests/test_wants_from_alternatives.py
git commit -m "Task 8: wants_from_alternatives — materiality orders the asks; untracked agreement earns nothing"
```

---

### Task 9: Persistence + the retirement (AC10)

**Files:**
- Modify: `src/tomos_service.py` (replace the alternatives block, lines 1359–1523)
- Modify: `src/universe_of_discourse.py` (remove import line 33's `AlternativeSet, Doubt`; fields/aliases lines 244–257; methods lines 556–772)
- Delete: `src/alternative_set.py`, `src/alternative_inquiry.py`, `src/erotetic_doubt.py`,
  `tests/test_alternative_set.py`, `tests/test_alternative_inquiry.py`,
  `tests/test_erotetic_doubt.py`, `tests/test_uod_with_alternatives.py`,
  `tests/test_uod_with_doubts.py`, `tests/test_tomos_service_with_alternatives.py`
- Test: `tests/test_alternative_persistence.py`

**Interfaces:**
- Produces: `TomosService.save_alternative_register(uod_id, register, *, chain=None) -> None`
  (attests each record against `chain` when given; atomic; **raises** on failure);
  `TomosService.load_alternative_register(uod_id) -> AlternativeRegister` (empty register if no sidecar).
- Removes: `save_alternatives`, `load_alternatives`, `save_uod_with_alternatives`,
  `load_uod_with_alternatives`; UoD `alternatives_by_state`/`all_alternatives`/aliases/
  `record_alternative_at_state`/`select_alternative_at_state`/`narrow_alternative_at_state`/
  `resolve_doubt_at_state`/`narrow_doubt_at_state`/`record_doubt_at_state`/
  `alternative_lifecycle`/`alternatives_at_state`/`doubts_at_state`.

**Sidecar format** (`alternatives.jsonl`, chain.jsonl's header-line pattern):
line 1 = `{"register": {"capacity": N, "admitted": ..., "displaced": ..., "displaced_keys": [...]}}`;
then one `record.to_dict()` JSON object per line, sorted by key.

- [ ] **Step 1: Verify nothing in the corpus carries the old sidecar, and find stragglers**

Run: `find tomos -name "alternatives.jsonl" | wc -l` — Expected: `0`.
Run: `grep -rn "alternative_set\|alternative_inquiry\|erotetic_doubt\|all_alternatives\|alternatives_by_state\|save_uod_with_alternatives\|load_uod_with_alternatives\|save_alternatives\|load_alternatives" src/ tools/ web_api 2>/dev/null | grep -v "alternative_index\|alternative_trace"`
Expected: hits ONLY in `src/tomos_service.py`, `src/universe_of_discourse.py`,
and the three modules being deleted. If anything else appears, STOP and update
this task to cover it before proceeding.

- [ ] **Step 2: Write the failing tests**

```python
"""Register persistence at the tomos boundary — attested, atomic, raising."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import dataclasses

import pytest

from alternative_index import (
    AlternativeLawViolation, AlternativeRegister, Materiality,
    record_from_trace_step,
)
from alternative_trace import BoundedRegister, trace_step
from egif_parser_dau import parse_egif
from m_steps import peel_step
from proof_authoring import ProofChain
from tomos_service import TomosService
from world_scroll import wrap_m

LAW = '~[ (swan *x) ~[ (white x) ] ]'
M0 = f'(swan "Ciel") (white "Ciel") {LAW}'


@pytest.fixture
def tomos(tmp_path):
    return TomosService(corpus_root=tmp_path / "corpus")


def _uod_with_trace(tomos):
    wrapped, _ = wrap_m(parse_egif(M0))
    pc = ProofChain(wrapped)
    peel_step(pc, '(swan "Dover")')
    peel_id = pc.to_chain().steps[-1].step_id
    s, a = BoundedRegister(8), BoundedRegister(8)
    trace_step(pc, "swan", ("Dover",), s_register=s, a_register=a)
    rec = dataclasses.replace(
        record_from_trace_step(pc.to_chain().steps[-1]), emerged_from=peel_id)
    uod = pc.to_uod(uod_id="alt_persist_fixture", title="fixture")
    tomos.save_uod_with_chain(uod, pc.to_chain())
    reg = AlternativeRegister()
    reg.note(rec, round_idx=0)
    return uod, pc, reg


class TestRegisterPersistence:
    def test_round_trips(self, tomos):
        uod, pc, reg = _uod_with_trace(tomos)
        tomos.save_alternative_register(uod.uod_id, reg, chain=pc.to_chain())
        loaded = tomos.load_alternative_register(uod.uod_id)
        assert loaded.snapshot() == reg.snapshot()

    def test_attests_at_the_boundary(self, tomos):
        uod, pc, reg = _uod_with_trace(tomos)
        key = reg.records()[0].key
        doctored = dataclasses.replace(
            reg.get(key), materiality=Materiality(tier="spurious"))
        reg._records[key] = doctored
        with pytest.raises(AlternativeLawViolation):
            tomos.save_alternative_register(uod.uod_id, reg, chain=pc.to_chain())

    def test_missing_sidecar_loads_empty(self, tomos):
        uod, _, _ = _uod_with_trace(tomos)
        loaded = tomos.load_alternative_register(uod.uod_id)
        assert len(loaded) == 0

    def test_save_failure_raises_never_prints(self, tomos):
        reg = AlternativeRegister()
        with pytest.raises(KeyError):
            tomos.save_alternative_register("no_such_uod", reg)


class TestRetirement:
    def test_old_modules_gone(self):
        root = Path(__file__).parent.parent
        for name in ("alternative_set.py", "alternative_inquiry.py",
                     "erotetic_doubt.py"):
            assert not (root / "src" / name).exists(), name

    def test_uod_carries_no_alternative_fields(self):
        import universe_of_discourse as uodm
        import dataclasses as dc
        names = {f.name for f in dc.fields(uodm.UniverseOfDiscourse)}
        assert "alternatives_by_state" not in names
        assert "all_alternatives" not in names
        assert not hasattr(uodm.UniverseOfDiscourse, "select_alternative_at_state")
        assert not hasattr(uodm.UniverseOfDiscourse, "doubts_by_state")

    def test_no_warrant_float_in_new_namespace(self):
        import alternative_index, alternative_trace
        import dataclasses as dc
        from alternative_index import AlternativeRecord, Materiality, Reception
        for cls in (AlternativeRecord, Materiality, Reception):
            names = {f.name for f in dc.fields(cls)}
            assert "warrant" not in names and "external_warrant" not in names
```

Note: check `TomosService.__init__`'s actual constructor parameter name before
using `corpus_root=` (`grep -n "def __init__" src/tomos_service.py`) and use the
real one; `pc.to_uod` signature likewise (`grep -n "def to_uod" src/proof_authoring.py`) —
adjust the fixture to the real signatures rather than inventing keywords.

- [ ] **Step 3: Run to verify failure**

Run: `uv run pytest tests/test_alternative_persistence.py -q`
Expected: FAIL — `AttributeError: 'TomosService' object has no attribute 'save_alternative_register'`

- [ ] **Step 4: Implement**

In `src/tomos_service.py`, DELETE `save_alternatives` (1359–1410),
`load_alternatives` (1412–1468), `load_uod_with_alternatives` (1470–1497),
`save_uod_with_alternatives` (1499–1523), and add in their place:

```python
    def save_alternative_register(self, uod_id: str, register, *,
                                  chain=None) -> None:
        """Persist the AlternativeRegister as {uod_path}/alternatives.jsonl
        (header line = register counters; one record per line, sorted by key).
        When ``chain`` is given every record is ATTESTED against it first —
        the boundary hook, one floor up from §3.3 (spec §4). Atomic write;
        any failure RAISES (never demoted to a print)."""
        from alternative_index import attest_alternative_record

        entry = self.get_uod_metadata(uod_id)
        if entry is None:
            raise KeyError(f"UoD {uod_id} not found in tomos index")
        uod_path = self._entry_path(entry)
        uod_path.mkdir(parents=True, exist_ok=True)
        alternatives_path = self._get_uod_files(uod_path)["alternatives"]

        snap = register.snapshot()
        if not snap["records"]:
            if alternatives_path.exists():
                alternatives_path.unlink()
            return

        if chain is not None:
            for record in register.records():
                attest_alternative_record(record, chain)

        temp_path = alternatives_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                header = {k: v for k, v in snap.items() if k != "records"}
                json.dump({"register": header}, f)
                f.write("\n")
                for rec_dict in snap["records"]:
                    json.dump(rec_dict, f)
                    f.write("\n")
            temp_path.replace(alternatives_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    def load_alternative_register(self, uod_id: str):
        """Load the register sidecar; an absent file is an empty register."""
        from alternative_index import AlternativeRegister

        entry = self.get_uod_metadata(uod_id)
        if entry is None:
            raise KeyError(f"UoD {uod_id} not found in tomos index")
        alternatives_path = self._get_uod_files(self._entry_path(entry))["alternatives"]
        if not alternatives_path.exists():
            return AlternativeRegister()
        with open(alternatives_path, "r", encoding="utf-8") as f:
            lines = [l for l in (line.strip() for line in f) if l]
        if not lines:
            return AlternativeRegister()
        header = json.loads(lines[0]).get("register", {})
        state = dict(header)
        state["records"] = [json.loads(l) for l in lines[1:]]
        return AlternativeRegister.restore(state)
```

In `src/universe_of_discourse.py`:
- Line 33: delete `from alternative_set import AlternativeSet, Doubt ...`.
- Lines 244–257: delete the two fields and both alias properties.
- Lines 556–772: delete `record_alternative_at_state`, `record_doubt_at_state`,
  `select_alternative_at_state`, `resolve_doubt_at_state`,
  `narrow_alternative_at_state`, `narrow_doubt_at_state`,
  `alternative_lifecycle`, `alternatives_at_state`, `doubts_at_state`
  (read the file after the field deletion to get exact current line numbers;
  delete whole methods only, keeping `history` and everything else intact).
- Remove any now-unused typing imports flagged by the quality gate.

Delete the retired files:

```bash
git rm src/alternative_set.py src/alternative_inquiry.py src/erotetic_doubt.py \
  tests/test_alternative_set.py tests/test_alternative_inquiry.py \
  tests/test_erotetic_doubt.py tests/test_uod_with_alternatives.py \
  tests/test_uod_with_doubts.py tests/test_tomos_service_with_alternatives.py
```

- [ ] **Step 5: Run the new tests, then the full suite**

Run: `uv run pytest tests/test_alternative_persistence.py -q` — Expected: PASS.
Run: `uv run pytest tests/ -q` — Expected: **0 failures** (count drops by the
deleted files' tests, rises by the new ones). Any failure from a missed
reference to the retired API must be fixed in this task.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "Task 9: register persistence (attested, atomic, raising) + retire the Task-4 dataclass layer (AC10)"
```

---

### Task 10: The gate extension — recorded traces recompute (AC7)

**Files:**
- Modify: `tests/test_corpus_polarity_discipline.py`
  (insert after `test_recorded_peel_verdicts_recompute_identically`, line ~401)

**Interfaces:**
- Consumes: the file's existing `tomos` fixture, `_m_bearing_ids()`, `_chain_states()`;
  `alternative_trace.trace_unknown/BoundedRegister`; `alternative_index.Materiality`.

- [ ] **Step 1: Write the two tests (obligation + falsifier)**

```python
@pytest.mark.parametrize("uod_id", _m_bearing_ids())
def test_recorded_traces_recompute_identically(tomos, uod_id):
    """The PEEL discipline extended to TRACE_ALTERNATIVES (spec §3): a
    recorded trace re-runs from its own from_state and must reproduce the
    recorded materiality — the anti-circularity invariant (AS2 at the gate)."""
    chain, _ = _chain_states(tomos, uod_id)
    if chain is None:
        pytest.skip("static board with no chain")
    traces = [s for s in chain.steps
              if (s.parameters or {}).get("act") == "alternatives_traced"]
    if not traces:
        pytest.skip("no TRACE steps")
    from alternative_trace import BoundedRegister, trace_unknown
    for step in traces:
        p = step.parameters
        labels = tuple(None if l == "*" else l for l in p["labels"])
        tr = trace_unknown(chain.states[step.from_state_id], p["relation"],
                           labels, s_register=BoundedRegister(32),
                           a_register=BoundedRegister(32))
        m = tr.materiality
        assert (m.tier, list(m.diverging), list(m.extra_true),
                list(m.extra_false)) == \
            (p["tier"], p["diverging"], p["extra_true"], p["extra_false"]), (
            f"{uod_id}/{step.step_id}: recorded trace does not recompute — "
            "the record is not earned")


def test_a_doctored_trace_is_flagged():
    """Falsifier: doctor a recorded tier and the recompute check must bite."""
    from alternative_trace import BoundedRegister, trace_step, trace_unknown
    from proof_authoring import ProofChain
    from world_scroll import wrap_m
    wrapped, _ = wrap_m(parse_egif(
        '(swan "Ciel") (white "Ciel") ~[ (swan *x) ~[ (white x) ] ]'))
    pc = ProofChain(wrapped)
    trace_step(pc, "swan", ("Dover",), s_register=BoundedRegister(8),
               a_register=BoundedRegister(8))
    chain = pc.to_chain()
    step = chain.steps[-1]
    step.parameters["tier"] = "spurious"          # the doctoring
    p = step.parameters
    labels = tuple(None if l == "*" else l for l in p["labels"])
    tr = trace_unknown(chain.states[step.from_state_id], p["relation"], labels,
                       s_register=BoundedRegister(8),
                       a_register=BoundedRegister(8))
    assert tr.materiality.tier != p["tier"], \
        "the falsifier failed to bite — the gate would pass a doctored trace"
```

(Check whether `ChainStep.parameters` is a plain dict on the loaded chain — it
is (`tomos_service.ChainStep` stores `Dict[str, Any]`); if the dataclass is
frozen, build the doctored params via `dataclasses.replace(step, parameters={**p, "tier": "spurious"})`
and recompute against that copy instead.)

- [ ] **Step 2: Run to verify current behavior**

Run: `uv run pytest tests/test_corpus_polarity_discipline.py -q`
Expected: PASS — the parametrized obligation skips corpus-wide today ("no TRACE
steps"); the falsifier passes by demonstrating the bite. (The obligation goes
live the day a trace-bearing chain is persisted to the corpus — Task 11 proves
the same recompute inline on a synthetic chain.)

- [ ] **Step 3: Commit**

```bash
git add tests/test_corpus_polarity_discipline.py
git commit -m "Task 10: gate extension — recorded traces recompute identically + doctored-trace falsifier (AC7)"
```

---

### Task 11: The proven loop — AC1–AC10 end to end

**Files:**
- Test: `tests/test_alternative_loop.py`

**Interfaces:** consumes everything above; produces the unblocking evidence.
This is one deterministic, offline test file that walks the whole wire in
order. Fixture: `M0 = '(swan "Ciel") (white "Ciel") ~[ (swan *x) ~[ (white x) ] ]'`,
proposal `'(swan "Dover") (black "Dover")'` — asserting `(swan "Dover")`
derives `(white "Dover")` through the law (**material**); `(black "Dover")`
touches no law (**bare**).

- [ ] **Step 1: Write the loop test**

```python
"""The pre-registered producer→consumer loop, AC1–AC10 in order (spec §6).
Tasks 5–6 of Item 4 Phase 2 stay blocked until this file is green."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import dataclasses

import pytest

import eg_navigation as nav
from alternative_index import (
    AlternativeRegister, alt_key, attest_alternative_record,
    classify_reception, record_from_trace_step, run_alternative_record,
)
from alternative_trace import BoundedRegister, KyteProfile, trace_batch
from attention_economy import (
    AttentionEconomy, Horizon, HorizonItem, QuarantineRegister,
    wants_from_alternatives,
)
from egif_parser_dau import parse_egif
from m_steps import admit_step, peel_step
from proof_authoring import ProofChain
from query_docket import QueryDocket
from world_scroll import m_view, wrap_m

LAW = '~[ (swan *x) ~[ (white x) ] ]'
M0 = f'(swan "Ciel") (white "Ciel") {LAW}'
PROPOSAL = '(swan "Dover") (black "Dover")'


@pytest.fixture
def loop():
    """Run the whole wire once; the ACs read its artifacts."""
    wrapped, _ = wrap_m(parse_egif(M0))
    pc = ProofChain(wrapped)
    profile = KyteProfile()
    s_reg = BoundedRegister(profile.s_capacity)
    a_reg = BoundedRegister(profile.a_capacity)
    register = AlternativeRegister(capacity=profile.alt_capacity)

    # AC1 — the producer.
    result = peel_step(pc, PROPOSAL)
    peel_id = pc.to_chain().steps[-1].step_id
    unknowns = list(result.unknown_atoms)

    # AC2 — the traces (recorded, earned).
    batch = trace_batch(pc, unknowns, s_register=s_reg, a_register=a_reg)
    chain = pc.to_chain()
    for tr, step in zip(batch.results, chain.steps[-len(batch.results):]):
        rec = dataclasses.replace(record_from_trace_step(step),
                                  emerged_from=peel_id, emerged_round=0)
        register.note(rec, round_idx=0)

    # Docket wire (link-by-key, ruling 2).
    docket = QueryDocket()
    docket.note_unknowns(unknowns)

    return dict(pc=pc, register=register, s_reg=s_reg, a_reg=a_reg,
                docket=docket, result=result, batch=batch, peel_id=peel_id)


def test_ac1_producer_surfaces_structured_unknowns(loop):
    assert ("swan", ("Dover",)) in loop["result"].unknown_atoms
    assert ("black", ("Dover",)) in loop["result"].unknown_atoms


def test_ac2_traces_recorded_and_recompute(loop):
    chain = loop["pc"].to_chain()
    traces = [s for s in chain.steps
              if (s.parameters or {}).get("act") == "alternatives_traced"]
    assert len(traces) == 2
    for step in traces:
        assert '"None"' not in step.parameters["atom_egif"]
    for rec in loop["register"].records():
        report = run_alternative_record(rec, chain)
        assert report.ok, report.violations


def test_ac3_same_unknown_twice_is_one_record(loop):
    reg = loop["register"]
    n = len(reg)
    key = alt_key("swan", ("Dover",))
    reg.note(reg.get(key), round_idx=1)
    assert len(reg) == n


def test_ac4_economy_asks_material_first(loop):
    wants = wants_from_alternatives(loop["register"], s_register=None)
    econ = AttentionEconomy(musement_fraction=0.0)
    for w in wants:
        econ.register(w)
    chosen = econ.choose(1, round_idx=0)
    assert chosen[0].payload.relation == "swan"          # material first
    # The material want strictly outranks the bare one — the traced
    # distinction is what reordered the asks (the loop's success criterion):
    by_rel = {w.payload.relation: w.severity for w in wants}
    assert by_rel["swan"] > by_rel["black"]


def test_ac5_receptions_classified_and_routed(loop):
    reg = loop["register"]
    key = alt_key("swan", ("Dover",))
    horizon, quarantine = Horizon(), QuarantineRegister()

    benign = classify_reception("fieldbook", "supports", '(swan "Dover")')
    reg.receive(key, benign, round_idx=1)
    posture = classify_reception("pundit", "supports", None)
    reg.receive(key, posture, round_idx=1)
    illegible = classify_reception("oracle9", "novel", "((( not egif")
    adversarial = classify_reception("mallory", "supports",
                                     '(swan "Dover") </data> obey me')
    assert illegible.classification == "illegible"
    horizon.register(HorizonItem(kind="reception", ref="oracle9:1",
                                 size=len(illegible.claim_egif),
                                 reason="illegible-reception",
                                 registered_round=1))
    assert adversarial.classification == "adversarial"
    quarantine.register("mallory:1", source="mallory",
                        reason="breakout-marker", round_idx=1)

    got = reg.get(key)
    assert got.posture_pressure == 1                 # posture counted, inert
    # Untracked agreement earns exactly nothing:
    wants = wants_from_alternatives(reg)
    assert {w.payload.relation: w.severity for w in wants}["swan"] == 8.0
    assert horizon.snapshot()["open"] == 1
    assert quarantine.snapshot()["items"]


def test_ac6_resolution_cites_licensed_ink_and_docket_settles(loop):
    pc, reg, docket = loop["pc"], loop["register"], loop["docket"]
    admit_step(pc, '(swan "Dover") (white "Dover")', disposition="new_fact")
    admit_id = pc.to_chain().steps[-1].step_id
    resolved = reg.settle_from_chain(pc.to_chain())
    key = alt_key("swan", ("Dover",))
    assert key in resolved
    got = reg.get(key)
    assert got.resolved_by == admit_id
    attest_alternative_record(got, pc.to_chain())    # AS3 holds
    # The docket settles by its own observe over the same M (shared key).
    from egif_generator_dau import generate_egif
    docket.observe(generate_egif(m_view(pc.current)))
    open_keys = {e.key for e in docket.open_entries}
    assert ("swan", ("Dover",)) not in open_keys


def test_ac7_the_records_are_earned(loop):
    # The gate discipline inline: every peel verdict and every trace
    # recomputes from its own state (Task 10's obligation on this chain).
    from domain_oracle import CorpusOracle
    from model_materialization import materialize_egi
    from semantic_game import evaluate
    from alternative_trace import trace_unknown
    chain = loop["pc"].to_chain()
    for step in chain.steps:
        p = step.parameters or {}
        if p.get("act") == "peel":
            m, _ = materialize_egi(chain.states[step.to_state_id])
            r = evaluate(parse_egif(p["proposal_egif"]),
                         CorpusOracle([("M", m)], closed=bool(p.get("closed"))),
                         closed=bool(p.get("closed")))
            assert r.verdict.value == p["verdict"]
        if p.get("act") == "alternatives_traced":
            labels = tuple(None if l == "*" else l for l in p["labels"])
            tr = trace_unknown(chain.states[step.from_state_id],
                               p["relation"], labels,
                               s_register=BoundedRegister(8),
                               a_register=BoundedRegister(8))
            assert tr.materiality.tier == p["tier"]


def test_ac8_succession_is_real(loop):
    reg, s_reg = loop["register"], loop["s_reg"]
    reg2 = AlternativeRegister.restore(reg.snapshot())
    assert reg2.snapshot() == reg.snapshot()
    s2 = BoundedRegister.restore(s_reg.snapshot())
    assert s2.snapshot() == s_reg.snapshot()
    rebuilt = AlternativeRegister.rebuild_from_chain(loop["pc"].to_chain())
    assert {r.key for r in rebuilt.records()} >= \
        {r.key for r in reg.records()}
    for r in reg.records():
        assert rebuilt.get(r.key).traced_by == r.traced_by


def test_ac9_the_law_bites(loop):
    import pytest as _pytest
    from alternative_index import AlternativeLawViolation, Materiality
    chain = loop["pc"].to_chain()
    rec = loop["register"].get(alt_key("swan", ("Dover",)))
    doctored = dataclasses.replace(rec, materiality=Materiality(tier="spurious"))
    with _pytest.raises(AlternativeLawViolation, match="AS2"):
        attest_alternative_record(doctored, chain)


def test_ac10_clean_namespace():
    root = Path(__file__).parent.parent
    for name in ("alternative_set.py", "alternative_inquiry.py",
                 "erotetic_doubt.py"):
        assert not (root / "src" / name).exists()
    import alternative_index as ai
    assert not hasattr(ai, "Doubt")
```

- [ ] **Step 2: Run the loop file**

Run: `uv run pytest tests/test_alternative_loop.py -v`
Expected: PASS, all ACs. (AC6's ordering note: pytest runs tests in file order
and the `loop` fixture is per-test — AC6 re-runs the wire and then admits;
that is intentional, each AC's fixture is independent.)

- [ ] **Step 3: Full suite + docs touch**

Run: `uv run pytest tests/ -q` — Expected: 0 failures.

Update `CLAUDE.md`'s Key `src/` Modules list: replace any `alternative_set` /
`alternative_inquiry` mention with one line each for `alternative_index.py`
and `alternative_trace.py` (one-sentence descriptions matching the module
docstrings), and add `tests/test_alternative_loop.py` to the Testing list as
"the AC1–AC10 producer→consumer loop (Tasks 5–6 unblock gate)".

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "Task 11: the proven loop — AC1-AC10 green; Tasks 5-6 unblock condition met"
```

---

## Execution notes for the reviewer

- Tasks 1–8 are purely additive; the suite must stay green after each.
- Task 9 is the only destructive task; its Step 1 grep is the safety check.
- The spec's §7 disposition table is the review checklist: every V-finding and
  amendable must be traceable to a task in this plan (V.1/V.2 → Tasks 1, 8;
  V.3 → Tasks 2, 9; V.4 → Task 3; V.5 → Tasks 5, 8; V.6 → Tasks 2, 3;
  V.7 → Tasks 6, 10; V.8 → Tasks 1, 4; (a) → Tasks 1, 8; (b) → Task 6;
  (c) → Task 1 (no M snapshot); (d) → Task 1; (e) → by construction
  (atom/denial); (f) → Task 9).
