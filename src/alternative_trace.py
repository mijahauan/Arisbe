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
from model_materialization import materialize_egi
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
        if self._capacity <= 0:
            # A zero-capacity register admits nothing: refuse-and-count.
            self.displaced += 1
            return term
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
    ``UnrepresentableAtomError`` — refuse, never mangle. Labels are expected in
    the parser's escaped form (the EGIF parser retains backslashes and never
    unescapes); a raw embedded quote cannot round-trip and is refused — count-or-refuse,
    never mangle (spec D-5 as revised)."""
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


def _matches_question(
    atom: Tuple[str, Tuple[Optional[str], ...]],
    relation: str,
    labels: Tuple[Optional[str], ...],
) -> bool:
    """Does ``atom`` match the ASKED question pattern (relation, labels) —
    slot-wise, with a None (generic) slot matching any label?

    For an all-constant question this is exact-match, identical to the old
    ``atom_key_t`` exclusion. For a question with a generic slot, ``assert_fact``
    skolemizes the generic to a fresh individual (e.g. ``_i1``) before the
    branch is re-read off the materialized facts-EGI, so the asked atom never
    equals its own post-skolemization key — the old exact-key exclusion missed
    it and it leaked into the consequence set, reading every generic question
    as "material" even with zero law consequence. Matching by pattern instead
    excludes the asked atom itself under any skolemization, and — deliberately
    — any OTHER same-relation atom that also matches the pattern (e.g. a second
    skolem instance of the same open question): a question whose only
    consequence is more instances of itself settles nothing beyond itself. A
    derived atom of a DIFFERENT relation carrying the same skolem constant
    (the genuine law consequence) still fails this match and remains a real
    extra."""
    rel, got = atom
    if rel != relation or len(got) != len(labels):
        return False
    return all(l is None or l == g for l, g in zip(labels, got))


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
    (which withstood Examination V) in its new housing.

    Consequence sets exclude the ASKED QUESTION PATTERN, not an exact atom
    key (Task 7 fix): see ``_matches_question`` for why an exact key misses
    a generic question's own skolemized atom and inflates materiality."""
    labels = tuple(labels)
    atom_egif, denial_egif = atom_and_denial_egif(relation, labels)

    base = m_view(m_egi)
    base_mat, base_report = materialize_egi(base)
    base_atoms = _sheet_atoms(base_mat)

    true_egi = assert_fact(base, atom_egif)
    true_mat, true_report = materialize_egi(true_egi)
    true_atoms = _sheet_atoms(true_mat)
    false_egi = assert_fact(base, denial_egif)
    false_mat, false_report = materialize_egi(false_egi)
    false_atoms = _sheet_atoms(false_mat)

    extra_t = {a for a in true_atoms - base_atoms
               if not _matches_question(a, relation, labels)}
    extra_f = {a for a in false_atoms - base_atoms
               if not _matches_question(a, relation, labels)}

    k3_true: Optional[Tuple[int, int]] = None
    k3_false: Optional[Tuple[int, int]] = None
    if extra_t != extra_f:
        tier = "material"
    elif extra_t or extra_f:
        tier = "bare"
    else:
        # K3 honesty check rather than assuming "spurious" — read off the
        # reports the trace's own materialization already produced (the
        # counts materialization_ratio would recompute).
        k3_true = (true_report.base_facts, true_report.derived_facts)
        k3_false = (false_report.base_facts, false_report.derived_facts)
        tier = "spurious" if k3_true == k3_false else "bare"

    # "Relations that differ between branches": the relations of the atoms in the symmetric difference (a one-side-only relation necessarily appears there). Only a material tier carries a divergence.
    if tier == "material":
        diverging = tuple(sorted({r for r, _ in (extra_t ^ extra_f)}))
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


__all__ = [
    "KyteProfile", "BoundedRegister", "UnrepresentableAtomError",
    "atom_and_denial_egif", "TraceResult", "trace_unknown",
    "TRACE_ALTERNATIVES", "trace_step", "TraceBatch", "trace_batch",
]
