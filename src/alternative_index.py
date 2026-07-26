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


# INTENTIONAL narrowing vs the polarity gate's M_ACTS
# (tests/test_corpus_polarity_discipline.py): "episode_entertained",
# "episode_abandoned", and "m_refold" are omitted on purpose. None of the
# three ever introduces sheet-level content that could settle an open
# record (an entertained exhibit lives nested under a rider, an abandonment
# and a refold change no sheet-level fact) — including them would only add
# no-op scans. Revisit this list if the gate's M_ACTS ever grows a new
# settling act.
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


def _denial_stands(m, relation: str, labels: Tuple[Optional[str], ...]) -> bool:
    """Does a SHEET-LEVEL bare denial of (relation, labels) stand in m?
    A bare denial is a sheet-level cut whose area holds exactly ONE edge and
    NO nested cuts, with matching relation and argument labels (a generic
    slot, None, matches a generic vertex; a constant slot matches by label —
    read through nu regardless of where the vertex is homed, so a constant
    co-referring with sheet facts still matches). Structural on purpose:
    lift_cut demands a self-contained subtree, which a co-referring constant
    or an entertained exhibit legally violates. Sheet-level-only keeps
    mention inert: an exhibit's inner ~[P] is nested (the exhibit's own cut
    is the sheet-level one, and it contains nested cuts, so it never reads
    as a bare denial)."""
    edge_ids = {e.id for e in m.E}
    cut_ids = {c.id for c in m.Cut}
    for cid in sorted(m.area.get(m.sheet, frozenset())):
        if cid not in cut_ids:
            continue
        contents = m.area.get(cid, frozenset())
        inner_edges = [x for x in sorted(contents) if x in edge_ids]
        inner_cuts = [x for x in contents if x in cut_ids]
        if len(inner_edges) != 1 or inner_cuts:
            continue
        eid = inner_edges[0]
        if m.rel.get(eid) != relation:
            continue
        got = [m.get_vertex(v) for v in m.nu.get(eid, ())]
        if len(got) != len(labels):
            continue
        ok = True
        for want, vert in zip(labels, got):
            if want is None:
                if not vert.is_generic:
                    ok = False
                    break
            elif vert.label != want:
                ok = False
                break
        if ok:
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
            if _denial_stands(m, rec.relation, rec.labels):
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
                denial_settles = _denial_stands(m, record.relation, record.labels)
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


# --- reception classification (spec §5) -----------------------------------------

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
        claim_edge_ids = {e.id for e in claim.E}
        claim_cut_ids = {c.id for c in claim.Cut}
        sheet_ids = claim.area.get(claim.sheet, frozenset())
        sheet_edges = [x for x in sheet_ids if x in claim_edge_ids]
        sheet_cuts = [x for x in sheet_ids if x in claim_cut_ids]
        if len(sheet_edges) == 1 and not sheet_cuts:
            # the claim IS a bare atom — does M carry a standing denial of it?
            eid = sheet_edges[0]
            labels = tuple(claim.get_vertex(v).label
                           for v in claim.nu.get(eid, ()))
            conflict = _denial_stands(m, claim.rel[eid], labels)
        elif len(sheet_cuts) == 1 and not sheet_edges:
            # the claim IS a bare denial — does M carry the denied atom?
            cid = sheet_cuts[0]
            inner = claim.area.get(cid, frozenset())
            inner_edges = [x for x in inner if x in claim_edge_ids]
            inner_cuts = [x for x in inner if x in claim_cut_ids]
            if len(inner_edges) == 1 and not inner_cuts:
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


__all__ = [
    "AlternativeLawViolation", "alt_key", "Materiality", "Reception",
    "TrackRecord", "SourceRecord", "UntrackedSources", "AlternativeRecord",
    "AlternativeRegister", "record_from_trace_step",
    "AlternativeLawReport", "run_alternative_record", "attest_alternative_record",
    "classify_reception",
]
