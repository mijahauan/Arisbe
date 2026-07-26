"""Wire peel-UNKNOWN verdicts into interrogative AlternativeSets — Item 4 Phase 2, Task 4.

Design-of-record: ``docs/superpowers/specs/2026-07-25-alternative-set-inquiry-principle.md``
(the governing principle: never pre-filter alternatives by assumed consequences — detect
them, trace what each actually leads to, and let the *discovered* distinctions define
materiality) and ``docs/superpowers/plans/2026-07-25-item-4-phase-2-tasks-4-6-revised.md``
§"Task 4".

``src/query_docket.py`` already turns a peel's Kleene UNKNOWN — an ``(relation, labels)``
atom the oracle could not decide — into an ephemeral docket *want*. This module adds the
persistent half: the same UNKNOWN also becomes an interrogative :class:`AlternativeSet`
whose two alternatives (the ground atom and its cut-wrapped denial) are traced by actually
materializing each branch on a **dry-run** copy of M (never written back), comparing the
derived consequences, and only *then* assigning warrant. A kyte's standing sign- and
action-vocabulary (:class:`BoundedRegister`, bounded per :class:`KyteProfile`) is refined
within its capacity — admission may displace the least-recently-touched term, counted
never silently dropped.

Geometry-free (no layout/DTO imports); deterministic (sorted iteration everywhere an order
could vary; no wall-clock, no randomness). Reads ``world_scroll.m_view`` so a resident M's
cells are traced correctly (sweep #2); ``model_revision.assert_fact`` already juxtaposes
*any* EGIF onto the sheet by text concatenation + reparse regardless of shape, which is
exactly the ``discourse_membrane`` denial idiom (a cut-wrapped fact scribed onto the
sheet) — used directly for both the TRUE and the FALSE (denial) branch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from alternative_set import AlternativeSet
from eg_navigation import area_of
from egi_core_dau import RelationalGraphWithCuts
from model_materialization import materialization_ratio, materialize_egi
from model_revision import assert_fact
from world_scroll import m_view


# --------------------------------------------------------------------------- #
# Deliverable 1: the species-parametrization seam + bounded-capacity register  #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class KyteProfile:
    """Species-parametrization seam (author's ruling: kytes come in species
    parametrized by capacity/duration; duration is future work, not built here).
    ``s_capacity`` bounds the standing sign-vocabulary register, ``a_capacity``
    the standing action-repertoire register."""

    s_capacity: int = 32
    a_capacity: int = 32


class BoundedRegister:
    """A capacity-bounded vocabulary register — the disuse-decay mechanics
    ``interrogative_from_unknown`` refines S and A within.

    Modeled on the bounded-register-with-counted-drops pattern in
    ``src/attention_economy.py`` (``Horizon`` / ``AttentionEconomy._wants``),
    specialized to plain vocabulary terms with **least-recently-used**
    displacement: every admission (new or a refresh of an existing term)
    stamps a strictly increasing touch-sequence number, so an eviction always
    picks the smallest-sequence (least-recently-touched) term. Ties cannot
    arise under that scheme (every admit call draws a fresh sequence number),
    but a residual tie is broken lexicographically rather than assumed away —
    checked honestly, per this codebase's ``attest_overview`` discipline.
    """

    def __init__(self, capacity: int):
        self._capacity = capacity
        self._touch: Dict[str, int] = {}
        self._seq = 0
        self.admitted = 0     # terms ever newly admitted (a refresh doesn't count)
        self.displaced = 0    # terms ever displaced — never silently lost

    def __len__(self) -> int:
        return len(self._touch)

    def __contains__(self, term: str) -> bool:
        return term in self._touch

    @property
    def terms(self) -> List[str]:
        """The standing vocabulary, sorted (deterministic introspection)."""
        return sorted(self._touch)

    def admit(self, term: str) -> Optional[str]:
        """Admit ``term``. Returns the displaced term if the register was full
        (``None`` if nothing was displaced, including the refresh case)."""
        self._seq += 1
        if term in self._touch:
            self._touch[term] = self._seq       # refresh (touch) — no displacement
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


def _admit_tracked(
    register: BoundedRegister, term: str, expansion: Set[str], decayed: Set[str]
) -> None:
    """Admit ``term`` to ``register``, recording it in ``expansion`` iff it was
    genuinely new (not a refresh) and recording whatever it displaced in
    ``decayed`` — the per-call bookkeeping ``interrogative_from_unknown`` needs
    for ``s_expansion``/``s_decayed`` (and the ``a_*`` twins)."""
    is_new = term not in register
    displaced = register.admit(term)
    if is_new:
        expansion.add(term)
    if displaced is not None:
        decayed.add(displaced)


# --------------------------------------------------------------------------- #
# The bare-sheet ground-atom reading (a local copy of query_docket's idiom —   #
# never import a private name from another module)                            #
# --------------------------------------------------------------------------- #

def _sheet_atoms(egi: RelationalGraphWithCuts) -> Set[Tuple[str, Tuple[str, ...]]]:
    """M's standing sheet-level ground atoms as ``(relation, (label, ...))``
    tuples, read through ``m_view`` (identity on a bare sheet, the flattened
    cells on a resident M)."""
    egi = m_view(egi)
    out: Set[Tuple[str, Tuple[str, ...]]] = set()
    for e in egi.E:
        if e.id in egi.rel and area_of(egi, e.id) == egi.sheet:
            labels = tuple(egi.get_vertex(v).label for v in egi.nu.get(e.id, ()))
            out.add((egi.rel[e.id], labels))
    return out


def _atom_egif(relation: str, labels: Sequence[str]) -> str:
    """The ground-atom EGIF for ``(relation, labels)``, e.g. ``(white "Alba")``."""
    quoted = "".join(f' "{label}"' for label in labels)
    return f"({relation}{quoted})"


def _describe(
    tier: str, relation: str,
    extra_t: Set[Tuple[str, Tuple[str, ...]]],
    extra_f: Set[Tuple[str, Tuple[str, ...]]],
) -> str:
    """A deterministic one-line report naming the tier and the differing
    derived relations."""
    diff_rels = sorted({r for r, _ in extra_t} | {r for r, _ in extra_f})
    if tier == "material":
        return (
            f"material distinction: asserting vs denying ({relation} ...) diverges "
            f"on derived relation(s) {', '.join(diff_rels)}"
        )
    if tier == "bare":
        return (
            f"bare distinction: only the asserted/denied ({relation} ...) atom "
            f"itself distinguishes the branches — no downstream consequence found yet"
        )
    return (
        f"spurious: asserting and denying ({relation} ...) are indistinguishable "
        f"in traced consequences — collapse to one"
    )


# --------------------------------------------------------------------------- #
# Deliverable 2: the core wiring                                              #
# --------------------------------------------------------------------------- #

def interrogative_from_unknown(
    m_egi: RelationalGraphWithCuts,
    relation: str,
    labels: Sequence[str],
    *,
    alt_id: str,
    state_id: str,
    profile: KyteProfile = KyteProfile(),
    s_register: BoundedRegister,
    a_register: BoundedRegister,
    external_input: Optional[str] = None,
    external_input_source: str = "none",
    external_agrees: Optional[bool] = None,
) -> AlternativeSet:
    """Build the interrogative ``AlternativeSet`` for a peel-UNKNOWN on
    ``(relation, labels)`` against ``m_egi`` (never mutated — every trace runs
    on a dry-run copy). See the module docstring for the staged design; the
    stage numbers below match the principle doc's inquiry cycle."""

    # 1. Detect (unfiltered) — the alternatives are exactly {atom, denial}.
    atom_egif = _atom_egif(relation, labels)
    denial_egif = f"~[ {atom_egif} ]"

    # 2. Trace (internal, dry-run — m_egi is never mutated: base is a fresh
    #    reading, and both branches are built from it, never written back).
    base = m_view(m_egi)
    base_facts_egi, _ = materialize_egi(base)
    base_atoms = _sheet_atoms(base_facts_egi)
    atom_key = (relation, tuple(labels))

    true_egi = assert_fact(base, atom_egif)
    true_facts_egi, _ = materialize_egi(true_egi)
    true_atoms = _sheet_atoms(true_facts_egi)

    false_egi = assert_fact(base, denial_egif)
    false_facts_egi, _ = materialize_egi(false_egi)
    false_atoms = _sheet_atoms(false_facts_egi)

    extra_t = true_atoms - base_atoms - {atom_key}
    extra_f = false_atoms - base_atoms - {atom_key}

    # 3. Discover distinctions (compare, don't assume).
    if extra_t != extra_f:
        tier = "material"
        warrant = 1.0
    elif extra_t or extra_f:
        # Equal but non-empty on both sides — the same non-trivial consequence
        # follows either way; treat as bare (the asserted/denied atom's shadow
        # is all that's discoverable here, not a real divergence).
        tier = "bare"
        warrant = 0.5
    else:
        # extra_t == extra_f == set() — check K3 honestly rather than assume
        # "spurious" (should be impossible for assert-vs-deny: the TRUE branch
        # always carries one more explicit fact than the FALSE branch).
        k3_true = materialization_ratio(true_egi)
        k3_false = materialization_ratio(false_egi)
        if (k3_true.explicit, k3_true.derived) == (k3_false.explicit, k3_false.derived):
            tier = "spurious"
            warrant = 0.0
        else:
            tier = "bare"
            warrant = 0.5

    consequence_description = _describe(tier, relation, extra_t, extra_f)

    # 4. Refine S within bounds.
    s_expansion: Set[str] = set()
    s_decayed: Set[str] = set()
    diff_rels = sorted({r for r, _ in extra_t} | {r for r, _ in extra_f})
    for rel in diff_rels:
        _admit_tracked(s_register, f"derivable:{rel}", s_expansion, s_decayed)
    if tier == "material":
        _admit_tracked(s_register, f"distinction:{relation}", s_expansion, s_decayed)

    # 5. Refine A within bounds.
    a_expansion: Set[str] = set()
    a_decayed: Set[str] = set()
    _admit_tracked(a_register, f"resolve:{relation}", a_expansion, a_decayed)
    if tier == "material":
        _admit_tracked(a_register, f"condition-on:{relation}", a_expansion, a_decayed)
        for rel in sorted({r for r, _ in extra_t}):
            _admit_tracked(a_register, f"derive-via:{rel}", a_expansion, a_decayed)

    # 6. External reception.
    if external_agrees is None:
        external_warrant = 0.0
    elif external_agrees:
        external_warrant = 0.9         # received, not derived — never 1.0
    else:
        external_warrant = 0.1
        warrant = min(warrant, 0.5)     # conflicting sources → further inquiry

    # 7. Return — context is the base m_view EGI (the presupposition under
    #    which the question is well-posed); unresolved (no selection yet).
    return AlternativeSet(
        id=alt_id,
        context=base,
        alternatives=frozenset({atom_egif, denial_egif}),
        current_selection=frozenset(),
        kind="interrogative",
        emerged_at_state=state_id,
        resolved_at_state=None,
        selection_path=[],
        warrant=warrant,
        source="unknown_in_peel",
        consequence_description=consequence_description,
        s_expansion=frozenset(s_expansion),
        s_decayed=frozenset(s_decayed),
        a_expansion=frozenset(a_expansion),
        a_decayed=frozenset(a_decayed),
        external_input=external_input,
        external_input_source=external_input_source,
        external_warrant=external_warrant,
    )


# --------------------------------------------------------------------------- #
# Deliverable 3: the batch/call-site helper                                   #
# --------------------------------------------------------------------------- #

def alternatives_from_unknowns(
    unknowns: Iterable[Tuple[str, Sequence[str]]],
    m_egi: RelationalGraphWithCuts,
    *,
    state_id: str,
    id_prefix: str = "unk",
    profile: KyteProfile = KyteProfile(),
    s_register: Optional[BoundedRegister] = None,
    a_register: Optional[BoundedRegister] = None,
) -> List[AlternativeSet]:
    """The same ``unknowns`` iterable ``QueryDocket.note_unknowns`` receives,
    turned into one interrogative ``AlternativeSet`` per distinct
    ``(relation, labels)`` pair, in enumerated input order (deterministic ids
    ``f"{id_prefix}_{i}_{relation}"`` using each pair's first-occurrence
    index). An exact-duplicate pair within the batch is processed once and
    silently skipped thereafter — the docket already dedups on its side, so
    nothing beyond this docstring records it. ``s_register``/``a_register``
    default to a fresh :class:`BoundedRegister` per ``profile`` when omitted,
    and are **shared across the whole batch** (so decay can cross items, the
    same as a kyte's standing vocabulary would)."""
    if s_register is None:
        s_register = BoundedRegister(profile.s_capacity)
    if a_register is None:
        a_register = BoundedRegister(profile.a_capacity)

    seen: Set[Tuple[str, Tuple[str, ...]]] = set()
    result: List[AlternativeSet] = []
    for i, (relation, labels) in enumerate(unknowns):
        key = (relation, tuple(labels))
        if key in seen:
            continue
        seen.add(key)
        alt = interrogative_from_unknown(
            m_egi, relation, labels,
            alt_id=f"{id_prefix}_{i}_{relation}",
            state_id=state_id,
            profile=profile,
            s_register=s_register,
            a_register=a_register,
        )
        result.append(alt)
    return result


__all__ = [
    "KyteProfile",
    "BoundedRegister",
    "interrogative_from_unknown",
    "alternatives_from_unknowns",
]
