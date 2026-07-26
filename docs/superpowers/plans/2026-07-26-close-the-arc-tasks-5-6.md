# Closing the AlternativeSet Arc (Tasks 5–6 + Knob + Follow-On Batch) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the AlternativeSet arc: the temperament knob (author ruling 2026-07-26), the two new producers (thin spots → `hypothetical`, branch points → `modal`) on the proven index-over-ink wire, the AS1/AS3 tightenings, the `_ACK_ACTS` tripwire, the small cleanups, and the trace-bearing corpus exemplar `swan_alternatives`.

**Architecture:** Everything replicates the proven interrogative wire (spec D-1): every record holds the same `{atom, denial}` pair; only emergence ink differs. Two new PEEL-twin survey steps (`thin_spots_surveyed`, `branches_surveyed`) in a new module `src/alternative_survey.py`; law/register extensions in `src/alternative_index.py`; the knob in `src/attention_economy.py`; cleanups in `src/alternative_trace.py`; gate extensions in `tests/test_corpus_polarity_discipline.py`; one new corpus builder.

**Tech Stack:** Python 3.12 via `uv run`, pytest. No protected-core change anywhere in this plan.

**Spec:** `docs/superpowers/specs/2026-07-26-close-the-arc-tasks-5-6-design.md` (rulings D-1..D-6, ACs AC11–AC20). Governing parent: `2026-07-26-alternative-index-over-ink-design.md`.

## Global Constraints

- Work on branch `alt-close-the-arc` off `main` (create it before Task 1: `git checkout -b alt-close-the-arc`).
- Never touch protected modules (`tools/core_protection_system.py --report` lists them). None of the files in this plan are protected.
- Import pattern: `from module_name import Foo` (never `from src.module_name`).
- EGIs are immutable — builders/`with_*` constructors only.
- All tests deterministic and offline. Run tests with `uv run pytest`.
- Defaults must be **byte-identical** to shipped behavior everywhere flagged (knob defaults, `BoundedRegister` capacities ≥ 1, diverging computation).
- No field or vocabulary named `warrant` in any new namespace.
- Commit after every task (message style: `Task N: <what> — <key invariant>`).

---

### Task 1: `alternative_trace` cleanups (spec §4, AC19)

**Files:**
- Modify: `src/alternative_trace.py` (three spots: `BoundedRegister.admit` ~line 62; `trace_unknown` lines 190–223; `atom_and_denial_egif` docstring ~line 109)
- Test: `tests/test_alternative_trace.py` (append one class)

**Interfaces:**
- Consumes: shipped `trace_unknown`, `BoundedRegister`, `trace_batch`, `materialize_egi` (returns `(egi, report)`; `report.base_facts`/`report.derived_facts` are the counts `materialization_ratio` reads).
- Produces: identical public signatures; `BoundedRegister(0)` now admits nothing (returns the term as displaced, `displaced` counted, `admitted` unchanged).

- [ ] **Step 1: Write the failing tests** — append to `tests/test_alternative_trace.py`:

```python
class TestFollowOnCleanups:
    """Spec 2026-07-26-close-the-arc §4 / AC19."""

    def test_bounded_register_zero_capacity_admits_nothing(self):
        reg = BoundedRegister(0)
        out = reg.admit("a")
        assert out == "a"                      # refused, returned as displaced
        assert len(reg) == 0
        assert reg.displaced == 1
        assert reg.admitted == 0
        restored = BoundedRegister.restore(reg.snapshot())
        assert restored.snapshot() == reg.snapshot()

    def test_bounded_register_capacity_one_unchanged(self):
        reg = BoundedRegister(1)
        assert reg.admit("a") is None
        assert reg.admit("b") == "a"           # byte-identical to shipped LRU
        assert len(reg) == 1 and reg.displaced == 1 and reg.admitted == 2

    def test_diverging_simplification_is_equivalent(self):
        # rels_t ^ rels_f ⊆ {r for r,_ in extra_t ^ extra_f} — pin the
        # equivalence on sets exercising both original clauses.
        cases = [
            ({("p", ("a",))}, {("q", ("b",))}),               # one-side-only rels
            ({("p", ("a",)), ("r", ("c",))}, {("p", ("b",))}),  # shared rel, differing atoms
            ({("p", ("a",))}, {("p", ("a",))}),               # identical → empty
            (set(), {("q", ("b",))}),                          # empty side
        ]
        for extra_t, extra_f in cases:
            rels_t = {r for r, _ in extra_t}
            rels_f = {r for r, _ in extra_f}
            old = tuple(sorted(
                (rels_t ^ rels_f) | {r for r, _ in (extra_t ^ extra_f)}))
            new = tuple(sorted({r for r, _ in (extra_t ^ extra_f)}))
            assert old == new

    def test_k3_check_does_not_rematerialize(self, monkeypatch):
        import alternative_trace as at
        import model_materialization as mm
        calls = {"n": 0}
        real = mm.materialize_egi
        def counting(egi, **kw):
            calls["n"] += 1
            return real(egi, **kw)
        monkeypatch.setattr(at, "materialize_egi", counting)
        m = parse_egif('(swan "Ciel")')
        tr = trace_unknown(m, "phoenix", ("Ciel",),
                           s_register=BoundedRegister(8),
                           a_register=BoundedRegister(8))
        # empty branch-diffs exercise the K3 branch (tier reads "bare" here:
        # the explicit counts differ, 2 vs 1); base + true + false = 3 calls,
        # no fourth/fifth from materialization_ratio.
        assert tr.materiality.k3_true is not None      # the K3 branch ran
        assert calls["n"] == 3
        # numbers identical to an independent materialization_ratio read
        from model_materialization import materialization_ratio
        base = tr.materiality
        kc = materialization_ratio(assert_fact_helper(m, tr.atom_egif))
        assert base.k3_true == (kc.explicit, kc.derived)

    def test_refused_unknown_is_counted_at_batch_level(self):
        # D-5 as revised: raw embedded quote → refused AND counted.
        from proof_authoring import ProofChain
        from world_scroll import wrap_m
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        batch = trace_batch(pc, [("said", ('he said "hi"',))],
                            s_register=BoundedRegister(8),
                            a_register=BoundedRegister(8))
        assert len(batch.results) == 0
        assert len(batch.unrepresentable) == 1


def assert_fact_helper(m, atom_egif):
    from model_revision import assert_fact
    from world_scroll import m_view
    return assert_fact(m_view(m), atom_egif)
```

Add the imports this needs at the top of the test file if absent: `from egif_parser_dau import parse_egif` and `from alternative_trace import trace_batch, trace_unknown` (check the file's existing imports first — most are already there).

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `uv run pytest tests/test_alternative_trace.py::TestFollowOnCleanups -v`
Expected: `test_bounded_register_zero_capacity_admits_nothing` FAILS (shipped code admits 1); `test_k3_check_does_not_rematerialize` FAILS (5 calls); the equivalence + refusal-count tests may already PASS (they pin invariants).

- [ ] **Step 3: Implement the three changes**

(a) `BoundedRegister.admit` — insert at the top of the method (after `self._seq += 1` and the already-present-refresh branch):

```python
        if self._capacity <= 0:
            # A zero-capacity register admits nothing: refuse-and-count.
            self.displaced += 1
            return term
```

(b) `trace_unknown` — capture the reports and drop the re-materialization. Replace lines 194–197 and the K3 branch:

```python
    true_egi = assert_fact(base, atom_egif)
    true_mat, true_report = materialize_egi(true_egi)
    true_atoms = _sheet_atoms(true_mat)
    false_egi = assert_fact(base, denial_egif)
    false_mat, false_report = materialize_egi(false_egi)
    false_atoms = _sheet_atoms(false_mat)
```

and in the `else:` branch:

```python
    else:
        # K3 honesty check rather than assuming "spurious" — read off the
        # reports the trace's own materialization already produced (the
        # counts materialization_ratio would recompute).
        k3_true = (true_report.base_facts, true_report.derived_facts)
        k3_false = (false_report.base_facts, false_report.derived_facts)
        tier = "spurious" if k3_true == k3_false else "bare"
```

Remove the now-unused `materialization_ratio` import **only if** nothing else in the module uses it (grep first).

(c) `diverging` — replace the material branch body:

```python
    if tier == "material":
        diverging = tuple(sorted({r for r, _ in (extra_t ^ extra_f)}))
    else:
        diverging = ()
```

and trim the comment above it to: `# "Relations that differ between branches": the relations of the atoms in the symmetric difference (a one-side-only relation necessarily appears there). Only a material tier carries a divergence.`

(d) `atom_and_denial_egif` docstring — append one sentence: `Labels are expected in the parser's escaped form (the EGIF parser retains backslashes and never unescapes); a raw embedded quote cannot round-trip and is refused — count-or-refuse, never mangle (spec D-5 as revised).`

- [ ] **Step 4: Run the file + the loop + gate neighbors**

Run: `uv run pytest tests/test_alternative_trace.py tests/test_alternative_loop.py tests/test_alternative_law.py tests/test_alternative_index.py -q`
Expected: all PASS (the equivalence guarantees AS2/gate recompute is undisturbed).

- [ ] **Step 5: Commit** — `git commit -am "Task 1: alternative_trace cleanups — BoundedRegister(0) refuses-and-counts, K3 reads the trace's own reports, diverging simplified (equivalence pinned), D-5 documented"`

---

### Task 2: the temperament knob (spec §1, AC11)

**Files:**
- Modify: `src/attention_economy.py` (`wants_from_alternatives`, lines 269–297)
- Test: `tests/test_wants_from_alternatives.py` (append one class)

**Interfaces:**
- Consumes: `AlternativeRecord.traced_by`; trace-step params key `s_admitted` (a list of strings like `"distinction:swan"`); `chain.steps[*].step_id` / `.parameters`.
- Produces: `wants_from_alternatives(register, *, round_idx=0, cost=1.0, s_register=None, source_record=None, chain=None, self_damping=0.5, cross_damping=0.5)` — defaults byte-identical to shipped behavior with or without `chain`.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_wants_from_alternatives.py` (reuse that file's existing record/register construction helpers; the test below builds a real two-trace chain so `s_admitted` is genuine ink):

```python
class TestTemperamentKnob:
    """The self-damping ruling (2026-07-26): reserved as a studiable dial.
    self_damping=1.0 → settle-first; 0.5 → explore-leaning; defaults 0.5/0.5
    byte-identical to the shipped wiring."""

    def _two_trace_loop(self):
        from egif_parser_dau import parse_egif
        from proof_authoring import ProofChain
        from world_scroll import wrap_m
        from alternative_index import AlternativeRegister, record_from_trace_step
        from alternative_trace import BoundedRegister, trace_batch
        import dataclasses
        law = '~[ (swan *x) ~[ (white x) ] ]'
        wrapped, _ = wrap_m(parse_egif(f'(swan "Ciel") (white "Ciel") {law}'))
        pc = ProofChain(wrapped)
        s_reg, a_reg = BoundedRegister(32), BoundedRegister(32)
        # Two unknowns of the SAME relation: the first trace admits
        # distinction:swan (material), the second finds it already standing —
        # its own s_admitted lacks it (the cross case, by construction).
        batch = trace_batch(pc, [("swan", ("Dover",)), ("swan", ("Eira",))],
                            s_register=s_reg, a_register=a_reg)
        assert len(batch.results) == 2
        chain = pc.to_chain()
        trace_steps = [s for s in chain.steps
                       if (s.parameters or {}).get("act") == "alternatives_traced"]
        register = AlternativeRegister(capacity=8)
        for step in trace_steps:
            register.note(record_from_trace_step(step), round_idx=0)
        return register, s_reg, chain

    def test_defaults_byte_identical_with_and_without_chain(self):
        register, s_reg, chain = self._two_trace_loop()
        without = {w.key: w.severity for w in wants_from_alternatives(
            register, s_register=s_reg)}
        with_chain = {w.key: w.severity for w in wants_from_alternatives(
            register, s_register=s_reg, chain=chain)}
        assert without == with_chain
        # shipped behavior: material 8.0 × 0.5 (distinction standing) = 4.0
        assert all(v == 4.0 for v in without.values())

    def test_settle_first_reads_self_admitted_at_full_severity(self):
        register, s_reg, chain = self._two_trace_loop()
        sev = {w.key: w.severity for w in wants_from_alternatives(
            register, s_register=s_reg, chain=chain,
            self_damping=1.0, cross_damping=0.5)}
        dover = alt_key("swan", ("Dover",))
        eira = alt_key("swan", ("Eira",))
        assert sev[dover] == 8.0     # own trace admitted the distinction
        assert sev[eira] == 4.0      # distinction arrived from Dover's trace

    def test_no_chain_cannot_distinguish_applies_cross(self):
        register, s_reg, _ = self._two_trace_loop()
        sev = {w.key: w.severity for w in wants_from_alternatives(
            register, s_register=s_reg,
            self_damping=1.0, cross_damping=0.5)}
        assert set(sev.values()) == {4.0}
```

Add `from alternative_index import alt_key` and `from attention_economy import wants_from_alternatives` to the file's imports if absent.

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_wants_from_alternatives.py::TestTemperamentKnob -v`
Expected: FAIL with `TypeError: wants_from_alternatives() got an unexpected keyword argument 'chain'`.

- [ ] **Step 3: Implement** — replace `wants_from_alternatives` in `src/attention_economy.py`:

```python
def wants_from_alternatives(register, *, round_idx: int = 0, cost: float = 1.0,
                            s_register=None, source_record=None,
                            chain=None, self_damping: float = 0.5,
                            cross_damping: float = 0.5) -> List[Want]:
    """Open AlternativeRecords as wants, severity from the TRACED materiality
    (spec §6): material > untraced (the trace itself is a worthwhile reach) >
    bare; spurious not emitted. A distinction already standing in the
    S-register damps severity — by ``self_damping`` when the record's OWN
    trace admitted it (told apart by dereferencing ``traced_by`` → the trace
    step's ``s_admitted`` params: the consumer re-reads licensed ink, the
    record holds nothing), else by ``cross_damping`` (don't pay twice for a
    distinction another trace earned). This is the reserved TEMPERAMENT dial
    (author ruling 2026-07-26): ``self_damping=1.0`` = settle-first,
    ``0.5`` = explore-leaning; defaults 0.5/0.5 are byte-identical to the
    pre-knob wiring, with or without ``chain``. A reception nudges severity
    ONLY when it bears evidence AND its source has a positive track record;
    untracked + agrees earns exactly nothing (ruling R-B's teeth)."""
    steps_by_id = ({s.step_id: s for s in chain.steps}
                   if chain is not None else {})
    out: List[Want] = []
    for record in register.open_records():
        tier = record.materiality.tier if record.materiality else "untraced"
        if tier == "spurious":
            continue
        severity = ALTERNATIVE_SEVERITY[tier]
        distinction = f"distinction:{record.relation}"
        if s_register is not None and distinction in s_register:
            factor = cross_damping
            step = steps_by_id.get(record.traced_by)
            if step is not None and distinction in (
                    (step.parameters or {}).get("s_admitted") or []):
                factor = self_damping
            severity *= factor
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

- [ ] **Step 4: Run knob + economy + loop tests**

Run: `uv run pytest tests/test_wants_from_alternatives.py tests/test_attention_economy.py tests/test_alternative_loop.py -q`
Expected: all PASS (AC4/AC5 untouched — defaults byte-identical).

- [ ] **Step 5: Commit** — `git commit -am "Task 2: the temperament knob — self_damping/cross_damping split, defaults byte-identical, dial resolved through licensed ink"`

---

### Task 3: `alternative_survey.py` — the two pure readers (spec §2, AC12/AC13 halves)

**Files:**
- Create: `src/alternative_survey.py`
- Test: `tests/test_alternative_survey.py` (new)

**Interfaces:**
- Consumes: `world_scroll.m_view`, `eg_navigation.area_of`/`child_cuts`, `dl_reasoning.ontology_signature`, `modal_query.leaf_states`, `tomos_service.TransformationChain`.
- Produces (Tasks 4/5/7/8/9 rely on these exact names):
  - `ThinSpotSurvey(unknowns, thin_but_grounded, lonely_individuals)` (frozen dataclass; `unknowns: Tuple[Tuple[str, Tuple[Optional[str], ...]], ...]`)
  - `BranchSurvey(fork_states, unknowns, evidence)` (frozen; `evidence: Tuple[Tuple[str, Tuple[str, ...], Tuple[str, ...]], ...]` = `(alt_key, witness_leaves, counterexample_leaves)`)
  - `survey_thin_spots(egi) -> ThinSpotSurvey`
  - `survey_branches(chain, *, upto=None, at=None) -> BranchSurvey`

- [ ] **Step 1: Write the failing tests** — create `tests/test_alternative_survey.py`:

```python
"""The two survey producers (spec 2026-07-26-close-the-arc §2, D-2/D-3)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from world_scroll import wrap_m

from alternative_index import alt_key
from alternative_survey import (BranchSurvey, ThinSpotSurvey, survey_branches,
                                survey_thin_spots)

# One-instance relation (swan/white grounded), a zero-grounded law body
# (dragon), its zero-grounded head (fears), and a lonely individual (Ciel
# appears twice → not lonely; Rex once → lonely).
FIXTURE_M = ('(swan "Ciel") (white "Ciel") (dog "Rex") '
             '~[ (dragon *x) ~[ (fears x) ] ]')


class TestThinSpotSurvey:
    def _survey(self):
        wrapped, _ = wrap_m(parse_egif(FIXTURE_M))
        return survey_thin_spots(wrapped)

    def test_zero_grounded_relations_surface_as_unary_existentials(self):
        s = self._survey()
        assert ("dragon", (None,)) in s.unknowns
        assert ("fears", (None,)) in s.unknowns

    def test_grounded_relations_do_not_surface(self):
        # D-2: a 1-instance relation's (r *x) already HOLDS — a record would
        # be born settled. Named, recordless.
        s = self._survey()
        surfaced = {r for r, _ in s.unknowns}
        assert "swan" not in surfaced and "dog" not in surfaced
        assert "dog" in s.thin_but_grounded
        assert "swan" in s.thin_but_grounded

    def test_lonely_individuals_named_recordless(self):
        s = self._survey()
        assert "Rex" in s.lonely_individuals
        assert "Ciel" not in s.lonely_individuals

    def test_deterministic_order(self):
        a, b = self._survey(), self._survey()
        assert a == b
        assert list(a.unknowns) == sorted(a.unknowns)


class TestBranchSurvey:
    def _forked_chain(self):
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        from world_scroll import enlarge_m
        from m_steps import admit_step
        base = pc.current_state_id
        admit_step(pc, '(cloudy "sky")', disposition="new_fact", branch="wx-a")
        pc.at(base)
        admit_step(pc, '(calm "sea")', disposition="new_fact", branch="wx-b")
        return pc, base

    def test_contested_atoms_surface_with_evidence(self):
        pc, base = self._forked_chain()
        s = survey_branches(pc.to_chain(), at=base)
        assert base in s.fork_states
        assert ("cloudy", ("sky",)) in s.unknowns
        assert ("calm", ("sea",)) in s.unknowns
        ev = {k: (ins, outs) for k, ins, outs in s.evidence}
        ins, outs = ev[alt_key("cloudy", ("sky",))]
        assert len(ins) == 1 and len(outs) == 1 and ins != outs

    def test_atoms_held_at_reference_state_do_not_surface(self):
        pc, base = self._forked_chain()
        # swan Ciel holds everywhere incl. the reference state → never contested
        s = survey_branches(pc.to_chain(), at=base)
        assert ("swan", ("Ciel",)) not in s.unknowns

    def test_upto_prefix_excludes_later_steps(self):
        pc, base = self._forked_chain()
        chain = pc.to_chain()
        first_step = chain.steps[0].step_id
        s = survey_branches(chain, upto=first_step, at=base)
        assert s.fork_states == () and s.unknowns == ()

    def test_no_fork_no_unknowns(self):
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        from m_steps import admit_step
        admit_step(pc, '(white "Ciel")', disposition="new_fact")
        s = survey_branches(pc.to_chain())
        assert s.fork_states == () and s.unknowns == ()
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_alternative_survey.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'alternative_survey'`.

- [ ] **Step 3: Implement** — create `src/alternative_survey.py`:

```python
"""Survey producers for the alternatives register — the emergence half of
Tasks 5–6 (spec 2026-07-26-close-the-arc-tasks-5-6-design §2).

Both surveys are PEEL-twins (Task 4 adds the recording steps): pure,
deterministic readers whose whole result rides in step params, recomputable
forever. Every surfaced question is the proven interrogative pair re-emerged
(D-1): the {atom, denial} alternatives, differing only in emergence ink.

D-2: only ZERO-grounded thin spots become questions — a 1-instance
relation's ``(r *x)`` already holds (the instance witnesses the existential;
a record would be born settled); those and lonely individuals are named,
recordless — the docket's beat. D-3: only ground atoms contested across
reachable futures and not held at the reference state become questions.

The structural readers mirror ``agon_llm.attention_brief``'s (kept local so
this module never imports the LLM layer)."""
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from eg_navigation import area_of, child_cuts
from egi_core_dau import RelationalGraphWithCuts
from world_scroll import m_view


@dataclass(frozen=True)
class ThinSpotSurvey:
    """What the thin-spot survey saw: surfaced unknowns + the named-recordless
    remainder (honest full brief)."""
    unknowns: Tuple[Tuple[str, Tuple[Optional[str], ...]], ...]
    thin_but_grounded: Tuple[str, ...]
    lonely_individuals: Tuple[str, ...]


@dataclass(frozen=True)
class BranchSurvey:
    """What the branch survey saw: fork states, contested-across-futures
    ground atoms, and the ◇-not-□ evidence (witness/counterexample leaves)
    per surfaced atom, keyed by alt_key."""
    fork_states: Tuple[str, ...]
    unknowns: Tuple[Tuple[str, Tuple[Optional[str], ...]], ...]
    evidence: Tuple[Tuple[str, Tuple[str, ...], Tuple[str, ...]], ...]


def _sheet_ground_atoms(egi: RelationalGraphWithCuts
                        ) -> Set[Tuple[str, Tuple[Optional[str], ...]]]:
    """Sheet-level atoms of M through m_view (generic slots read None)."""
    m = m_view(egi)
    out: Set[Tuple[str, Tuple[Optional[str], ...]]] = set()
    for e in m.E:
        if e.id in m.rel and area_of(m, e.id) == m.sheet:
            labels = tuple(m.get_vertex(v).label for v in m.nu.get(e.id, ()))
            out.add((m.rel[e.id], labels))
    return out


def _model_laws(egi: RelationalGraphWithCuts) -> List[Tuple[str, str]]:
    """(body, head) relation pairs of each standing scroll of M."""
    m = m_view(egi)
    laws: List[Tuple[str, str]] = []
    for outer in child_cuts(m, m.sheet):
        inner = child_cuts(m, outer)
        if not inner:
            continue
        body = next((m.rel[e.id] for e in m.E
                     if area_of(m, e.id) == outer and e.id in m.rel), None)
        head = next((m.rel[e.id] for e in m.E
                     if area_of(m, e.id) == inner[0] and e.id in m.rel), None)
        if body and head:
            laws.append((body, head))
    return laws


def survey_thin_spots(egi: RelationalGraphWithCuts) -> ThinSpotSurvey:
    """Read M for zero-grounded vocabulary relations and ungrounded law
    bodies (→ the unary existential question ``(r *x)`` each), naming the
    1-instance relations and lonely individuals recordless (D-2)."""
    from dl_reasoning import ontology_signature
    vocabulary = sorted(ontology_signature(egi))
    atoms = _sheet_ground_atoms(egi)
    rel_counts = Counter(r for r, _ in atoms)
    grounded = {r for r, _ in atoms}
    zero = {r for r in vocabulary if rel_counts.get(r, 0) == 0}
    zero |= {b for (b, _h) in _model_laws(egi) if b not in grounded}
    unknowns = tuple((r, (None,)) for r in sorted(zero))
    thin_but_grounded = tuple(sorted(
        r for r in vocabulary if rel_counts.get(r, 0) == 1))
    const_counts = Counter(
        lbl for _, labels in atoms for lbl in labels if lbl)
    lonely = tuple(sorted(c for c, n in const_counts.items() if n == 1))
    return ThinSpotSurvey(unknowns=unknowns,
                          thin_but_grounded=thin_but_grounded,
                          lonely_individuals=lonely)


def survey_branches(chain, *, upto: Optional[str] = None,
                    at: Optional[str] = None) -> BranchSurvey:
    """Enumerate fork states over the step prefix (all steps before ``upto``,
    or all steps) and surface the ground atoms contested across reachable
    leaves and not held at the reference state ``at`` (default: the prefix's
    current state). Pure DAG + m_view reading — recompute is re-reading."""
    from alternative_index import alt_key
    from modal_query import leaf_states
    from tomos_service import TransformationChain
    steps = list(chain.steps)
    if upto is not None:
        idx = next((i for i, s in enumerate(steps) if s.step_id == upto),
                   len(steps))
        steps = steps[:idx]
    prefix = TransformationChain(initial_state_id=chain.initial_state_id,
                                 steps=steps, states=chain.states)
    frm = Counter(s.from_state_id for s in steps)
    forks = tuple(sorted(sid for sid, n in frm.items() if n > 1))
    if not forks:
        return BranchSurvey((), (), ())
    ref = at if at is not None else prefix.current_state_id
    held = {a for a in _sheet_ground_atoms(chain.states[ref])
            if all(l is not None for l in a[1])}
    leaves = sorted(leaf_states(prefix))
    per_leaf: Dict[str, Set] = {
        leaf: {a for a in _sheet_ground_atoms(chain.states[leaf])
               if all(l is not None for l in a[1])}
        for leaf in leaves}
    universe = sorted(set().union(*per_leaf.values()))
    unknowns: List[Tuple[str, Tuple[Optional[str], ...]]] = []
    evidence: List[Tuple[str, Tuple[str, ...], Tuple[str, ...]]] = []
    for atom in universe:
        ins = tuple(l for l in leaves if atom in per_leaf[l])
        outs = tuple(l for l in leaves if atom not in per_leaf[l])
        if ins and outs and atom not in held:
            unknowns.append(atom)
            evidence.append((alt_key(atom[0], atom[1]), ins, outs))
    return BranchSurvey(fork_states=forks, unknowns=tuple(unknowns),
                        evidence=tuple(evidence))


__all__ = ["ThinSpotSurvey", "BranchSurvey", "survey_thin_spots",
           "survey_branches"]
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_alternative_survey.py -v`
Expected: all PASS. If `admit_step`'s signature complains about `branch=`, check `src/m_steps.py` — `admit_step(pc, fact_egif, *, disposition, ...)` forwards `branch` to `apply_derived`; if it lacks a `branch` param, fork instead with two different `pc.at(base)`-then-`admit_step` calls (the fork comes from the shared `from_state_id`, not the label) and drop the `branch=` kwargs.

- [ ] **Step 5: Commit** — `git commit -am "Task 3: alternative_survey pure readers — zero-grounded thin spots + contested-across-futures atoms, named-recordless remainders"`

---

### Task 4: the survey steps + `records_from_survey_step` (spec §2, AC12/AC13 halves)

**Files:**
- Modify: `src/alternative_survey.py` (append)
- Test: `tests/test_alternative_survey.py` (append)

**Interfaces:**
- Consumes: Task 3's readers; `pc.apply_derived(rule, transform, *, note, params, branch)`; `alternative_trace.atom_and_denial_egif`/`UnrepresentableAtomError`; `alternative_index.AlternativeRecord`/`alt_key`.
- Produces (Tasks 5/7/8/9 rely on):
  - `SURVEY_THIN_SPOTS = "SURVEY_THIN_SPOTS"`, `THIN_SPOTS_ACT = "thin_spots_surveyed"`
  - `SURVEY_BRANCHES = "SURVEY_BRANCHES"`, `BRANCHES_ACT = "branches_surveyed"`
  - `thin_spot_step(pc, *, budget=8, note=None, branch=None) -> ThinSpotSurvey`
  - `branch_survey_step(pc, *, budget=8, at=None, note=None, branch=None) -> BranchSurvey`
  - `records_from_survey_step(step, *, round_idx=0) -> List[AlternativeRecord]` (kind by act: `thin_spots_surveyed → "hypothetical"`, `branches_surveyed → "modal"`)
  - Step params for both acts: `act`, `earned: True`, `budget`, `unknown_atoms` (peel's exact `[[rel, ["*"|label, …]], …]` shape), `refused_budget` (alt_keys past budget); thin-spot adds `thin_but_grounded` + `lonely_individuals`; branch adds `at`, `fork_states`, `evidence` (`[[alt_key, [ins…], [outs…]], …]`).

- [ ] **Step 1: Write the failing tests** — append to `tests/test_alternative_survey.py`:

```python
from alternative_survey import (BRANCHES_ACT, THIN_SPOTS_ACT,
                                branch_survey_step, records_from_survey_step,
                                thin_spot_step)


class TestSurveySteps:
    def test_thin_spot_step_records_peel_shaped_params(self):
        wrapped, _ = wrap_m(parse_egif(FIXTURE_M))
        pc = ProofChain(wrapped)
        thin_spot_step(pc)
        step = pc.to_chain().steps[-1]
        p = step.parameters
        assert p["act"] == THIN_SPOTS_ACT and p["earned"] is True
        assert ["dragon", ["*"]] in p["unknown_atoms"]
        assert p["budget"] == 8 and p["refused_budget"] == []
        assert "dog" in p["thin_but_grounded"]
        assert "Rex" in p["lonely_individuals"]
        # identity transform: m_view unchanged
        assert step.from_state_id != step.to_state_id

    def test_budget_refuses_and_counts(self):
        wrapped, _ = wrap_m(parse_egif(FIXTURE_M))
        pc = ProofChain(wrapped)
        thin_spot_step(pc, budget=1)
        p = pc.to_chain().steps[-1].parameters
        assert len(p["unknown_atoms"]) == 1
        assert len(p["refused_budget"]) >= 1     # named, never dropped

    def test_records_from_thin_spot_step_are_hypothetical(self):
        wrapped, _ = wrap_m(parse_egif(FIXTURE_M))
        pc = ProofChain(wrapped)
        thin_spot_step(pc)
        step = pc.to_chain().steps[-1]
        recs = records_from_survey_step(step, round_idx=3)
        assert recs and all(r.kind == "hypothetical" for r in recs)
        assert all(r.emerged_from == step.step_id for r in recs)
        assert all(r.emerged_round == 3 for r in recs)
        by_key = {r.key: r for r in recs}
        dragon = by_key[alt_key("dragon", (None,))]
        assert dragon.alternatives[0] == "(dragon *x)"
        assert dragon.alternatives[1] == "~[ (dragon *x) ]"

    def test_branch_survey_step_records_evidence(self):
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        from m_steps import admit_step
        base = pc.current_state_id
        admit_step(pc, '(cloudy "sky")', disposition="new_fact")
        pc.at(base)
        admit_step(pc, '(calm "sea")', disposition="new_fact")
        pc.at(base)
        branch_survey_step(pc, at=base)
        step = pc.to_chain().steps[-1]
        p = step.parameters
        assert p["act"] == BRANCHES_ACT and p["at"] == base
        assert base in p["fork_states"]
        assert ["cloudy", ["sky"]] in p["unknown_atoms"]
        recs = records_from_survey_step(step)
        assert recs and all(r.kind == "modal" for r in recs)

    def test_records_from_non_survey_step_refused(self):
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        from m_steps import admit_step
        admit_step(pc, '(white "Ciel")', disposition="new_fact")
        import pytest
        with pytest.raises(ValueError):
            records_from_survey_step(pc.to_chain().steps[-1])
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_alternative_survey.py::TestSurveySteps -v`
Expected: FAIL with ImportError on the new names.

- [ ] **Step 3: Implement** — append to `src/alternative_survey.py`:

```python
SURVEY_THIN_SPOTS = "SURVEY_THIN_SPOTS"
THIN_SPOTS_ACT = "thin_spots_surveyed"
SURVEY_BRANCHES = "SURVEY_BRANCHES"
BRANCHES_ACT = "branches_surveyed"

_KIND_BY_ACT = {THIN_SPOTS_ACT: "hypothetical", BRANCHES_ACT: "modal"}


def _star(labels) -> List[str]:
    return ["*" if l is None else l for l in labels]


def thin_spot_step(pc, *, budget: int = 8, note: Optional[str] = None,
                   branch: Optional[str] = None) -> ThinSpotSurvey:
    """Record the thin-spot survey as a PEEL-twin identity step, earned at
    record time: the scan actually runs against pc.current; params carry the
    whole result; the gate recomputes it forever. Over-budget surfacings are
    refused-and-counted, never dropped."""
    from alternative_index import alt_key
    survey = survey_thin_spots(pc.current)
    surfaced = survey.unknowns[:budget]
    refused = survey.unknowns[budget:]
    params = {
        "act": THIN_SPOTS_ACT, "earned": True, "budget": budget,
        "unknown_atoms": [[r, _star(labels)] for r, labels in surfaced],
        "refused_budget": [alt_key(r, labels) for r, labels in refused],
        "thin_but_grounded": list(survey.thin_but_grounded),
        "lonely_individuals": list(survey.lonely_individuals),
    }
    pc.apply_derived(SURVEY_THIN_SPOTS, lambda g: g,
                     note=note or "thin-spot survey", params=params,
                     branch=branch)
    return survey


def branch_survey_step(pc, *, budget: int = 8, at: Optional[str] = None,
                       note: Optional[str] = None,
                       branch: Optional[str] = None) -> BranchSurvey:
    """Record the branch survey as a PEEL-twin identity step over the steps
    recorded so far (recompute = re-survey the prefix before this step)."""
    from alternative_index import alt_key
    ref = at if at is not None else pc.current_state_id
    survey = survey_branches(pc.to_chain(), at=ref)
    surfaced = survey.unknowns[:budget]
    refused = survey.unknowns[budget:]
    keys = {alt_key(r, labels) for r, labels in surfaced}
    params = {
        "act": BRANCHES_ACT, "earned": True, "budget": budget, "at": ref,
        "fork_states": list(survey.fork_states),
        "unknown_atoms": [[r, _star(labels)] for r, labels in surfaced],
        "refused_budget": [alt_key(r, labels) for r, labels in refused],
        "evidence": [[k, list(ins), list(outs)]
                     for k, ins, outs in survey.evidence if k in keys],
    }
    pc.apply_derived(SURVEY_BRANCHES, lambda g: g,
                     note=note or "branch survey", params=params,
                     branch=branch)
    return survey


def records_from_survey_step(step, *, round_idx: int = 0) -> List:
    """Mint AlternativeRecords from a recorded survey step's params alone —
    the survey twin of record_from_trace_step (the index stays a cache over
    the chain). Kind by act (D-1: one pair, three emergences)."""
    from alternative_index import AlternativeRecord, alt_key
    from alternative_trace import UnrepresentableAtomError, atom_and_denial_egif
    p = step.parameters or {}
    kind = _KIND_BY_ACT.get(p.get("act"))
    if kind is None:
        raise ValueError(f"step {step.step_id} is not a survey step")
    out: List[AlternativeRecord] = []
    for rel, labels in (p.get("unknown_atoms") or []):
        labs = tuple(None if l == "*" else l for l in labels)
        try:
            atom, denial = atom_and_denial_egif(rel, labs)
        except UnrepresentableAtomError:
            continue                      # refused at survey time too
        out.append(AlternativeRecord(
            key=alt_key(rel, labs), relation=rel, labels=labs,
            alternatives=(atom, denial), kind=kind,
            emerged_from=step.step_id, emerged_round=round_idx,
            last_touched_round=round_idx))
    return out
```

Extend `__all__` with the six new names. NOTE: this constructs `kind="hypothetical"`/`"modal"` records — Task 5 extends `KINDS_BUILT`, so until Task 5 lands, `records_from_survey_step` raises `ValueError` from `AlternativeRecord.__post_init__`. **Tasks 4 and 5 must land in this order but their tests only fully pass after Task 5** — run Step 4's subset accordingly: the params/step tests pass now; the two `records_from_*` tests are expected to fail with `kind ... is not built` until Task 5. Mark them `@pytest.mark.xfail(reason="KINDS_BUILT extended in Task 5", strict=True)` **and remove the marks in Task 5** (Task 5's checklist repeats this).

- [ ] **Step 4: Run the survey tests**

Run: `uv run pytest tests/test_alternative_survey.py -v`
Expected: step/params tests PASS; the two record-minting tests XFAIL (strict) with the kind refusal.

- [ ] **Step 5: Commit** — `git commit -am "Task 4: survey steps — PEEL-twin thin-spot + branch surveys, peel-shaped params, records_from_survey_step (kinds land in Task 5)"`

---

### Task 5: kinds, D-6, AS1 tightening, rebuild, docstring caveat (spec §3, AC14 + AC12/13 completion)

**Files:**
- Modify: `src/alternative_index.py` (`KINDS_BUILT` line ~142; `__post_init__` ~165; AS1 block 518–523; `_rebuild_from_chain` 454–475; `AlternativeRegister` docstring 225–228)
- Modify: `tests/test_alternative_survey.py` (remove the two xfail marks from Task 4)
- Modify: `tests/test_alternative_index.py` (amend `test_non_interrogative_kind_refused` ~line 82)
- Test: `tests/test_alternative_law.py` (append AS1 falsifier class)

**Interfaces:**
- Consumes: Task 4's `records_from_survey_step` + act names.
- Produces: `KINDS_BUILT = ("interrogative", "hypothetical", "modal")`; `_EMERGENCE_ACTS = ("peel", "thin_spots_surveyed", "branches_surveyed")`; D-6 construction invariant; AS1 refuses non-emergence `emerged_from`; `rebuild_from_chain` reads survey steps.

- [ ] **Step 1: Write/adjust the failing tests**

(a) In `tests/test_alternative_index.py`, replace `test_non_interrogative_kind_refused` with:

```python
    def test_unbuilt_kind_refused(self):
        with pytest.raises(ValueError, match="not built"):
            AlternativeRecord(key='p("a")', relation="p", labels=("a",),
                              alternatives=('(p "a")', '~[ (p "a") ]'),
                              kind="practical")

    def test_new_kinds_require_emerged_from(self):
        # D-6: a hypothetical/modal record's legitimacy IS the survey ink.
        for kind in ("hypothetical", "modal"):
            with pytest.raises(ValueError, match="emerged_from"):
                AlternativeRecord(key='p("a")', relation="p", labels=("a",),
                                  alternatives=('(p "a")', '~[ (p "a") ]'),
                                  kind=kind)
            rec = AlternativeRecord(key='p("a")', relation="p", labels=("a",),
                                    alternatives=('(p "a")', '~[ (p "a") ]'),
                                    kind=kind, emerged_from="step-1")
            assert rec.kind == kind
```

(b) Append to `tests/test_alternative_law.py`:

```python
class TestAS1Tightened:
    """A non-emergence emerged_from is now a violation (the silent pass died
    — spec 2026-07-26-close-the-arc §3, AC14)."""

    def _chain_with_admit(self):
        from egif_parser_dau import parse_egif
        from m_steps import admit_step, peel_step
        from proof_authoring import ProofChain
        from world_scroll import wrap_m
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        peel_step(pc, '(black "Dover")')
        peel_id = pc.to_chain().steps[-1].step_id
        admit_step(pc, '(white "Ciel")', disposition="new_fact")
        admit_id = pc.to_chain().steps[-1].step_id
        return pc.to_chain(), peel_id, admit_id

    def test_emerged_from_a_non_emergence_step_is_refused(self):
        chain, _peel_id, admit_id = self._chain_with_admit()
        rec = AlternativeRecord(
            key=alt_key("black", ("Dover",)), relation="black",
            labels=("Dover",),
            alternatives=('(black "Dover")', '~[ (black "Dover") ]'),
            emerged_from=admit_id)          # an admit is not an emergence
        report = run_alternative_record(rec, chain)
        assert any("AS1" in v and "emergence" in v for v in report.violations)

    def test_peel_emergence_still_passes(self):
        chain, peel_id, _ = self._chain_with_admit()
        rec = AlternativeRecord(
            key=alt_key("black", ("Dover",)), relation="black",
            labels=("Dover",),
            alternatives=('(black "Dover")', '~[ (black "Dover") ]'),
            emerged_from=peel_id)
        assert run_alternative_record(rec, chain).ok

    def test_survey_emergence_passes_and_rebuild_reads_surveys(self):
        from alternative_survey import thin_spot_step
        from egif_parser_dau import parse_egif
        from proof_authoring import ProofChain
        from world_scroll import wrap_m
        wrapped, _ = wrap_m(parse_egif(
            '(swan "Ciel") ~[ (dragon *x) ~[ (fears x) ] ]'))
        pc = ProofChain(wrapped)
        thin_spot_step(pc)
        chain = pc.to_chain()
        from alternative_survey import records_from_survey_step
        recs = records_from_survey_step(chain.steps[-1])
        assert recs
        for rec in recs:
            assert run_alternative_record(rec, chain).ok
        rebuilt = AlternativeRegister.rebuild_from_chain(chain)
        assert {r.key for r in recs} <= {r.key for r in rebuilt.records()}
        assert all(rebuilt.get(r.key).kind == "hypothetical" for r in recs)
```

Add any missing imports at the top of `tests/test_alternative_law.py` (`AlternativeRecord`, `AlternativeRegister`, `alt_key`, `run_alternative_record` come from `alternative_index` — check existing imports first).

(c) Remove the two `@pytest.mark.xfail` marks Task 4 placed in `tests/test_alternative_survey.py`.

- [ ] **Step 2: Run to verify failures**

Run: `uv run pytest tests/test_alternative_index.py tests/test_alternative_law.py::TestAS1Tightened tests/test_alternative_survey.py -v`
Expected: new-kind tests FAIL (`kind ... is not built`); AS1 falsifier FAILS (silent pass); survey record tests FAIL (kind refusal).

- [ ] **Step 3: Implement in `src/alternative_index.py`**

(a) `KINDS_BUILT = ("interrogative", "hypothetical", "modal")` — update the adjacent comment: the three built kinds share the interrogative {atom, denial} witness (exhaustive + exclusive by construction, spec D-1); further kinds remain refused until they declare theirs (V.8 discipline).

(b) In `__post_init__`, after the `KINDS_BUILT` check, add:

```python
        if self.kind in ("hypothetical", "modal") and self.emerged_from is None:
            raise ValueError(
                f"a {self.kind!r} record requires emerged_from — its "
                "legitimacy is the survey ink (spec D-6)")
```

(c) Add beside `_ACK_ACTS`:

```python
# The acts that lawfully SURFACE an open question (AS1): a peel's unknown,
# or one of the two survey PEEL-twins. All three park their surfacings under
# the params key "unknown_atoms" in the same [[rel, ["*"|label, …]], …]
# shape, so AS1 checks one code path.
_EMERGENCE_ACTS = ("peel", "thin_spots_surveyed", "branches_surveyed")
```

(d) Replace the AS1 `emerged_from` block (lines 518–523) with:

```python
    if record.emerged_from and record.emerged_from in steps_by_id:
        p = steps_by_id[record.emerged_from].parameters or {}
        if p.get("act") not in _EMERGENCE_ACTS:
            violations.append(
                f"AS1: emerged_from={record.emerged_from!r} is not an "
                f"emergence act (act={p.get('act')!r})")
        elif [record.relation, star_labels] not in (p.get("unknown_atoms") or []):
            violations.append(
                f"AS1: emerged_from step never surfaced {record.key}")
```

(e) In `_rebuild_from_chain`, after the `alternatives_traced` branch, add:

```python
        elif p.get("act") in ("thin_spots_surveyed", "branches_surveyed"):
            from alternative_survey import records_from_survey_step
            for rec in records_from_survey_step(s, round_idx=i):
                reg.note(rec, round_idx=i)
```

(the local import avoids the module cycle; `note`'s merge keeps the survey record's kind when a later trace record lands on the same key — chain order guarantees emergence precedes trace).

(f) Amend the `AlternativeRegister` docstring (lines 225–228) to end with: `Receptions are SNAPSHOT-ONLY: membrane arrivals were never chain steps, so rebuild_from_chain cannot recover them — LRU displacement + rebuild loses receptions (truth from the membrane, not from the chain). Snapshot/restore is their only succession path.` Add the matching one-line caveat to `_rebuild_from_chain`'s docstring.

- [ ] **Step 4: Run the affected files**

Run: `uv run pytest tests/test_alternative_index.py tests/test_alternative_law.py tests/test_alternative_survey.py tests/test_alternative_loop.py tests/test_alternative_persistence.py -q`
Expected: all PASS.

- [ ] **Step 5: Commit** — `git commit -am "Task 5: three built kinds (one witness, three emergences), D-6 invariant, AS1 emergence-act tightening, rebuild reads surveys, receptions-snapshot-only stated"`

---

### Task 6: AS3 tightening + settle alignment (spec §3, AC15)

**Files:**
- Modify: `src/alternative_index.py` (AS3 block 548–565; `_settle_from_chain` 426–451)
- Test: `tests/test_alternative_law.py` (append)

**Interfaces:**
- Consumes: shipped `_atom_holds`/`_denial_stands`/`_acknowledged`.
- Produces: AS3 = *introduced-by-step* (holds at `to_state`, not at `from_state`); `settle_from_chain` cites only introducing steps.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_alternative_law.py`:

```python
class TestAS3Introduction:
    """AS3 checks introduced-by-step, not stands-at-step (spec §3, AC15):
    a bystander acknowledged step whose from_state already held the answer
    cannot be cited as the resolution."""

    def _chain_two_admits(self):
        from egif_parser_dau import parse_egif
        from m_steps import admit_step, peel_step
        from proof_authoring import ProofChain
        from world_scroll import wrap_m
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        peel_step(pc, '(black "Dover")')
        peel_id = pc.to_chain().steps[-1].step_id
        admit_step(pc, '(black "Dover")', disposition="new_fact")
        introducing_id = pc.to_chain().steps[-1].step_id
        admit_step(pc, '(grey "Gull")', disposition="new_fact")
        bystander_id = pc.to_chain().steps[-1].step_id
        return pc, peel_id, introducing_id, bystander_id

    def _record(self, peel_id, resolved_by=None, selection=None):
        return AlternativeRecord(
            key=alt_key("black", ("Dover",)), relation="black",
            labels=("Dover",),
            alternatives=('(black "Dover")', '~[ (black "Dover") ]'),
            emerged_from=peel_id, resolved_by=resolved_by,
            selection=selection)

    def test_bystander_step_refused(self):
        pc, peel_id, _intro, bystander = self._chain_two_admits()
        rec = self._record(peel_id, resolved_by=bystander,
                           selection='(black "Dover")')
        report = run_alternative_record(rec, pc.to_chain())
        assert any("AS3" in v and "introduce" in v for v in report.violations)

    def test_introducing_step_passes(self):
        pc, peel_id, intro, _ = self._chain_two_admits()
        rec = self._record(peel_id, resolved_by=intro,
                           selection='(black "Dover")')
        assert run_alternative_record(rec, pc.to_chain()).ok

    def test_settle_cites_the_introducing_step(self):
        pc, peel_id, intro, _ = self._chain_two_admits()
        reg = AlternativeRegister(capacity=8)
        reg.note(self._record(peel_id), round_idx=0)
        resolved = reg.settle_from_chain(pc.to_chain())
        assert resolved == [alt_key("black", ("Dover",))]
        assert reg.get(alt_key("black", ("Dover",))).resolved_by == intro
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_alternative_law.py::TestAS3Introduction -v`
Expected: `test_bystander_step_refused` FAILS (shipped AS3 checks stands-at-step only); the other two PASS already (earliest-step scan happens to cite the introducer here) — they pin the alignment.

- [ ] **Step 3: Implement**

(a) Replace the AS3 `else:` branch (lines 558–565) with:

```python
            else:
                m_after = m_view(chain.states[s.to_state_id])
                m_before = m_view(chain.states[s.from_state_id])
                if record.selection == record.alternatives[0]:
                    if not _atom_holds(m_after, record.relation, record.labels):
                        violations.append(
                            "AS3: selected atom does not stand in M")
                    elif _atom_holds(m_before, record.relation, record.labels):
                        violations.append(
                            f"AS3: resolved_by {record.resolved_by} did not "
                            "introduce the selected atom (bystander step)")
                if record.selection == record.alternatives[1]:
                    if not _denial_stands(m_after, record.relation,
                                          record.labels):
                        violations.append(
                            "AS3: selected denial does not stand in M")
                    elif _denial_stands(m_before, record.relation,
                                        record.labels):
                        violations.append(
                            f"AS3: resolved_by {record.resolved_by} did not "
                            "introduce the selected denial (bystander step)")
```

(b) In `_settle_from_chain`, replace the inner scan body with:

```python
        for s in steps[start:]:
            if not _acknowledged(s.parameters):
                continue
            m_after = m_view(chain.states[s.to_state_id])
            m_before = m_view(chain.states[s.from_state_id])
            if (_atom_holds(m_after, rec.relation, rec.labels)
                    and not _atom_holds(m_before, rec.relation, rec.labels)):
                self.resolve(key, resolved_by=s.step_id, selection=atom_egif)
                resolved.append(key)
                break
            if (_denial_stands(m_after, rec.relation, rec.labels)
                    and not _denial_stands(m_before, rec.relation,
                                           rec.labels)):
                self.resolve(key, resolved_by=s.step_id, selection=denial_egif)
                resolved.append(key)
                break
```

and update its docstring: the earliest acknowledged step that **introduces** a settling answer is cited (an already-standing answer never picks up a bystander citation).

- [ ] **Step 4: Run the neighbors**

Run: `uv run pytest tests/test_alternative_law.py tests/test_alternative_loop.py tests/test_alternative_index.py tests/test_alternative_persistence.py tests/test_corpus_polarity_discipline.py -q`
Expected: all PASS (AC6's admit is the introducer, unaffected).

- [ ] **Step 5: Commit** — `git commit -am "Task 6: AS3 introduced-by-step + settle alignment — bystander citations refused"`

---

### Task 7: the two new wires end-to-end + the knob on the loop fixture (AC11, AC16)

**Files:**
- Test: `tests/test_alternative_loop.py` (append two classes; no src change expected)

**Interfaces:**
- Consumes: everything from Tasks 2–6.

- [ ] **Step 1: Write the tests** — append to `tests/test_alternative_loop.py`:

```python
class TestAC11TemperamentOnTheLoop:
    def test_defaults_byte_identical_and_dial_turns(self, loop):
        register, s_reg = loop["register"], loop["s_reg"]
        chain = loop["pc"].to_chain()
        base = {w.key: w.severity for w in wants_from_alternatives(
            register, s_register=s_reg)}
        with_chain = {w.key: w.severity for w in wants_from_alternatives(
            register, s_register=s_reg, chain=chain)}
        assert base == with_chain
        settle_first = {w.key: w.severity for w in wants_from_alternatives(
            register, s_register=s_reg, chain=chain, self_damping=1.0)}
        swan = alt_key("swan", ("Dover",))
        assert settle_first[swan] == 8.0        # own-trace admission undamped
        assert base[swan] == 4.0                # shipped natural wiring


class TestAC16TheTwoNewWires:
    HYP_M = ('(swan "Ciel") (white "Ciel") '
             '~[ (dragon *x) ~[ (fears x) ] ]')

    def _wire(self, pc, survey_step_fn, **step_kw):
        from alternative_survey import records_from_survey_step
        survey_step_fn(pc, **step_kw)
        step = pc.to_chain().steps[-1]
        recs = records_from_survey_step(step)
        register = AlternativeRegister(capacity=16)
        for rec in recs:
            register.note(rec, round_idx=0)
        s_reg, a_reg = BoundedRegister(32), BoundedRegister(32)
        batch = trace_batch(pc, [(r.relation, r.labels) for r in recs],
                            s_register=s_reg, a_register=a_reg)
        chain = pc.to_chain()
        traced = [s for s in chain.steps
                  if (s.parameters or {}).get("act") == "alternatives_traced"]
        for ts in traced[-len(batch.results):]:
            register.note(record_from_trace_step(ts), round_idx=0)
        return register, s_reg

    def test_hypothetical_wire(self):
        from alternative_survey import thin_spot_step
        wrapped, _ = wrap_m(parse_egif(self.HYP_M))
        pc = ProofChain(wrapped)
        register, s_reg = self._wire(pc, thin_spot_step)
        dragon = alt_key("dragon", (None,))
        rec = register.get(dragon)
        assert rec.kind == "hypothetical"
        assert rec.materiality.tier == "material"   # asserting dragon derives fears
        # the economy asks the material question first
        wants = wants_from_alternatives(register, s_register=None)
        econ = AttentionEconomy(musement_fraction=0.0)
        for w in wants:
            econ.register(w)
        assert econ.choose(1, round_idx=1)[0].key == (dragon,)
        # resolution lands via admit ink; settle cites it; the law holds
        from m_steps import admit_step
        admit_step(pc, '(dragon "Smaug")', disposition="new_fact")
        chain = pc.to_chain()
        assert register.settle_from_chain(chain) == [dragon]
        attest_alternative_record(register.get(dragon), chain)

    def test_modal_wire(self):
        from alternative_survey import branch_survey_step
        from m_steps import admit_step
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        base = pc.current_state_id
        admit_step(pc, '(cloudy "sky")', disposition="new_fact")
        pc.at(base)
        admit_step(pc, '(calm "sea")', disposition="new_fact")
        pc.at(base)
        register, _s = self._wire(pc, branch_survey_step, at=base)
        cloudy = alt_key("cloudy", ("sky",))
        assert register.get(cloudy).kind == "modal"
        # commit one future on the survey line: the record settles citing it
        admit_step(pc, '(cloudy "sky")', disposition="new_fact")
        chain = pc.to_chain()
        assert cloudy in register.settle_from_chain(chain)
        attest_alternative_record(register.get(cloudy), chain)
```

Add imports at the top of the file if absent: `from alternative_survey import ...` is done inline above; `AttentionEconomy` and `wants_from_alternatives` are already imported by the shipped file (verify).

- [ ] **Step 2: Run**

Run: `uv run pytest tests/test_alternative_loop.py -v`
Expected: all PASS. If `test_modal_wire`'s settle picks a different step id than expected, print `register.get(cloudy).resolved_by` — it must be the *introducing* admit on the survey line (the branch-A admit's to_state is not on the scan path only if the record's `emerged_from` index starts the scan after it; the scan runs over `chain.steps` linearly, so the branch-A admit *precedes* the survey step and is skipped by `start`). If it is not, the record's emergence index logic — `index_of.get(rec.emerged_from)` — already handles this; investigate rather than loosening the assertion.

- [ ] **Step 3: Commit** — `git commit -am "Task 7: AC11 + AC16 — the temperament dial on the loop fixture; hypothetical and modal wires end-to-end"`

---

### Task 8: gate extensions — survey recompute obligations + falsifiers + the `_ACK_ACTS` tripwire (AC18, gate halves of AC12/13)

**Files:**
- Test: `tests/test_corpus_polarity_discipline.py` (append after `test_a_doctored_trace_is_flagged`, ~line 449)

**Interfaces:**
- Consumes: `survey_thin_spots`, `survey_branches`, the act names, `alt_key`; the file's existing `_m_bearing_ids`/`_chain_states`/`tomos` fixtures; its `M_ACTS`.

- [ ] **Step 1: Write the tests** — append:

```python
@pytest.mark.parametrize("uod_id", _m_bearing_ids())
def test_recorded_thin_spot_surveys_recompute_identically(tomos, uod_id):
    """The PEEL discipline extended to the thin-spot survey: a recorded
    survey re-runs from its own from_state and must reproduce its params."""
    chain, _ = _chain_states(tomos, uod_id)
    if chain is None:
        pytest.skip("static board with no chain")
    surveys = [s for s in chain.steps
               if (s.parameters or {}).get("act") == "thin_spots_surveyed"]
    if not surveys:
        pytest.skip("no thin-spot survey steps")
    from alternative_index import alt_key
    from alternative_survey import survey_thin_spots
    for step in surveys:
        p = step.parameters
        survey = survey_thin_spots(chain.states[step.from_state_id])
        n = p["budget"]
        expect = [[r, ["*" if l is None else l for l in labels]]
                  for r, labels in survey.unknowns[:n]]
        refused = [alt_key(r, labels) for r, labels in survey.unknowns[n:]]
        assert (p["unknown_atoms"], p["refused_budget"],
                p["thin_but_grounded"], p["lonely_individuals"]) == \
            (expect, refused, list(survey.thin_but_grounded),
             list(survey.lonely_individuals)), (
            f"{uod_id}/{step.step_id}: recorded survey does not recompute")


@pytest.mark.parametrize("uod_id", _m_bearing_ids())
def test_recorded_branch_surveys_recompute_identically(tomos, uod_id):
    chain, _ = _chain_states(tomos, uod_id)
    if chain is None:
        pytest.skip("static board with no chain")
    surveys = [s for s in chain.steps
               if (s.parameters or {}).get("act") == "branches_surveyed"]
    if not surveys:
        pytest.skip("no branch survey steps")
    from alternative_index import alt_key
    from alternative_survey import survey_branches
    for step in surveys:
        p = step.parameters
        survey = survey_branches(chain, upto=step.step_id, at=p["at"])
        n = p["budget"]
        expect = [[r, ["*" if l is None else l for l in labels]]
                  for r, labels in survey.unknowns[:n]]
        keys = {e[0] for e in p["evidence"]}
        ev = [[k, list(ins), list(outs)]
              for k, ins, outs in survey.evidence if k in keys]
        assert (p["fork_states"], p["unknown_atoms"], p["evidence"]) == \
            (list(survey.fork_states), expect, ev), (
            f"{uod_id}/{step.step_id}: recorded branch survey does not recompute")


def test_a_doctored_survey_is_flagged():
    """Falsifier: a survey step whose params claim an unknown the re-survey
    does not surface must fail the recompute comparison."""
    from egif_parser_dau import parse_egif
    from proof_authoring import ProofChain
    from world_scroll import wrap_m
    from alternative_survey import survey_thin_spots, thin_spot_step
    wrapped, _ = wrap_m(parse_egif(
        '(swan "Ciel") ~[ (dragon *x) ~[ (fears x) ] ]'))
    pc = ProofChain(wrapped)
    thin_spot_step(pc)
    chain = pc.to_chain()
    step = chain.steps[-1]
    doctored = dict(step.parameters)
    doctored["unknown_atoms"] = doctored["unknown_atoms"] + [["unicorn", ["*"]]]
    survey = survey_thin_spots(chain.states[step.from_state_id])
    n = doctored["budget"]
    expect = [[r, ["*" if l is None else l for l in labels]]
              for r, labels in survey.unknowns[:n]]
    assert doctored["unknown_atoms"] != expect     # the lie is visible


def test_ack_acts_is_a_subset_of_the_gates_m_acts():
    """Drift tripwire: alternative_index._ACK_ACTS deliberately narrows
    M_ACTS (no-op settling scans omitted) but must never NAME an act the
    gate does not acknowledge."""
    from alternative_index import _ACK_ACTS
    assert set(_ACK_ACTS) <= set(M_ACTS), (
        "an _ACK_ACTS entry is unknown to the gate's M_ACTS — the two lists "
        "have drifted")
```

- [ ] **Step 2: Run the gate file**

Run: `uv run pytest tests/test_corpus_polarity_discipline.py -q`
Expected: all PASS — the two parametrized obligations skip everywhere (no corpus UoD carries survey steps *yet*; Task 9 de-vacuates), the falsifier and tripwire pass.

- [ ] **Step 3: Commit** — `git commit -am "Task 8: gate obligations for both surveys + falsifier + the _ACK_ACTS drift tripwire"`

---

### Task 9: the corpus exemplar `swan_alternatives` + AC17 + docs + full suite (AC17, AC20)

**Files:**
- Create: `tools/build_alternative_traces_exemplar.py`
- Modify: `CLAUDE.md` (the `alternative_index.py`/`alternative_trace.py` bullets; add an `alternative_survey.py` bullet; the tests list)
- Test: `tests/test_alternative_persistence.py` (append one class)

**Interfaces:**
- Consumes: everything above; `TomosService.save_uod_with_chain` + `save_alternative_register(uod_id, register, *, chain=)`; the UoD-construction pattern of `tools/build_episode_discharge_demo.py` (read it first and mirror its `UniverseOfDiscourse` construction, category `DOMAIN_MODEL`, provenance dict, and `main()` shape **exactly** — same imports, same service calls).
- Produces: corpus UoD `swan_alternatives` (category `domain_model`) whose chain carries ≥2 `alternatives_traced` steps, one `thin_spots_surveyed` step, one `branches_surveyed` step, a fork, and an introducing `m_enlargement` resolution; plus its `alternatives.jsonl` register sidecar.

- [ ] **Step 1: Write the builder** — create `tools/build_alternative_traces_exemplar.py` (mirroring `build_episode_discharge_demo.py`'s frame; the chain construction is):

```python
"""Build the trace-bearing corpus exemplar `swan_alternatives` — the UoD
that de-vacuates the polarity gate's trace- and survey-recompute
obligations (spec 2026-07-26-close-the-arc §5, AC17) and discharges AC7's
letter on real saved ink.

The story: the swan M carries an ungrounded dragon→fears law. A peel
surfaces two unknowns; the thin-spot survey surfaces the dragon question;
traces discover dragon is MATERIAL (asserting it derives fears) while black
is bare; two entertained futures fork the DAG; the branch survey reads the
contested weather; an admit introduces the dragon ground — the register
settles citing that step. Every record attests against the saved chain."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from world_scroll import wrap_m

from alternative_index import AlternativeRegister, record_from_trace_step
from alternative_survey import (branch_survey_step, records_from_survey_step,
                                thin_spot_step)
from alternative_trace import BoundedRegister, trace_batch
from m_steps import admit_step, peel_step

UOD_ID = "swan_alternatives"
M0 = ('(swan "Ciel") (white "Ciel") '
      '~[ (swan *x) ~[ (white x) ] ] '
      '~[ (dragon *y) ~[ (fears y) ] ]')
PROPOSAL = '(swan "Dover") (black "Dover")'


def build_chain():
    wrapped, _ = wrap_m(parse_egif(M0))
    pc = ProofChain(wrapped)
    register = AlternativeRegister(capacity=16)
    s_reg, a_reg = BoundedRegister(32), BoundedRegister(32)

    # 1. PEEL surfaces the proposal's unknowns.
    result = peel_step(pc, PROPOSAL, note="the Dover proposal")
    peel_id = pc.to_chain().steps[-1].step_id

    # 2. The thin-spot survey surfaces the ungrounded dragon law.
    thin_spot_step(pc, note="what is M thin on?")
    thin_id = pc.to_chain().steps[-1].step_id
    for rec in records_from_survey_step(pc.to_chain().steps[-1]):
        register.note(rec, round_idx=0)

    # 3. Trace peel unknowns + survey unknowns (one batch, budgeted).
    unknowns = list(result.unknown_atoms) + [
        (r.relation, r.labels) for r in register.records()]
    batch = trace_batch(pc, unknowns, s_register=s_reg, a_register=a_reg)
    chain = pc.to_chain()
    traced = [s for s in chain.steps
              if (s.parameters or {}).get("act") == "alternatives_traced"]
    import dataclasses
    for ts in traced[-len(batch.results):]:
        rec = record_from_trace_step(ts)
        if register.get(rec.key) is None:
            rec = dataclasses.replace(rec, emerged_from=peel_id)
        register.note(rec, round_idx=0)

    # 4. Two entertained futures fork the DAG; the branch survey reads them.
    base = pc.current_state_id
    admit_step(pc, '(cloudy "sky")', disposition="new_fact",
               note="future A: weather turns")
    pc.at(base)
    admit_step(pc, '(calm "sea")', disposition="new_fact",
               note="future B: fair passage")
    pc.at(base)
    branch_survey_step(pc, at=base, note="what do the futures contest?")
    for rec in records_from_survey_step(pc.to_chain().steps[-1]):
        register.note(rec, round_idx=1)

    # 5. The introducing resolution: the dragon question closes.
    admit_step(pc, '(dragon "Smaug")', disposition="new_fact",
               note="a dragon is attested")
    register.settle_from_chain(pc.to_chain())
    return pc, register


def main(argv=None):
    # Mirror tools/build_episode_discharge_demo.py exactly for the UoD
    # construction, category DOMAIN_MODEL, provenance, and save calls:
    #   service.save_uod_with_chain(uod, chain, provenance=...)
    #   service.save_alternative_register(UOD_ID, register, chain=chain)
    ...
```

Complete `main()` by copying `build_episode_discharge_demo.py`'s frame (UoD construction, `TomosService` instantiation against the repo `tomos/` root, provenance dict naming this spec, `if __name__ == "__main__": main()`), substituting `UOD_ID`, the chain from `build_chain()`, and adding the `save_alternative_register(UOD_ID, register, chain=pc.to_chain())` call **after** `save_uod_with_chain`.

- [ ] **Step 2: Run the builder + the gate**

Run: `uv run python tools/build_alternative_traces_exemplar.py && uv run pytest tests/test_corpus_polarity_discipline.py -q`
Expected: builder exits clean; the gate passes with `swan_alternatives` now parametrized in — and crucially `test_recorded_traces_recompute_identically`, `test_recorded_thin_spot_surveys_recompute_identically`, and `test_recorded_branch_surveys_recompute_identically` all **execute (not skip)** for it. Verify: `uv run pytest "tests/test_corpus_polarity_discipline.py::test_recorded_traces_recompute_identically[swan_alternatives]" -v` → PASS (not SKIPPED).

- [ ] **Step 3: Write the persistence test** — append to `tests/test_alternative_persistence.py`:

```python
class TestSwanAlternativesExemplar:
    """AC17: the corpus exemplar exists, carries the trace/survey ink, and
    its register attests at the boundary."""

    def test_exemplar_carries_the_ink_and_attests(self):
        from tomos_service import TomosService
        svc = TomosService(Path(__file__).parent.parent / "tomos")
        chain = svc.load_chain("swan_alternatives")
        acts = [(s.parameters or {}).get("act") for s in chain.steps]
        assert acts.count("alternatives_traced") >= 2
        assert "thin_spots_surveyed" in acts
        assert "branches_surveyed" in acts
        register = svc.load_alternative_register("swan_alternatives")
        assert len(register) >= 3
        from alternative_index import attest_alternative_record
        for rec in register.records():
            attest_alternative_record(rec, chain)
        resolved = [r for r in register.records() if r.status == "resolved"]
        assert resolved                       # the dragon question closed
        kinds = {r.kind for r in register.records()}
        assert {"interrogative", "hypothetical", "modal"} <= kinds
```

(Match the file's existing import style/fixtures for `TomosService` — reuse its `tomos` fixture if one exists.)

- [ ] **Step 4: Docs pass** — in `CLAUDE.md`: extend the `alternative_index.py` bullet with the three built kinds + AS1/AS3 tightenings; extend `alternative_trace.py` with the cleanups; add an `alternative_survey.py` bullet (the two PEEL-twin surveys, D-1/D-2/D-3 one-liners); note the temperament knob on the `attention_economy.py` bullet (author ruling, defaults byte-identical); add `test_alternative_survey.py` + the exemplar to the tests list. Keep each addition to the file's existing telegraphic style.

- [ ] **Step 5: Full suite (AC20)**

Run: `uv run pytest tests/ -q` (expect ~25–30 min)
Expected: **0 failed**. Record the exact tally for the commit message.

- [ ] **Step 6: Commit** — `git commit -am "Task 9: swan_alternatives corpus exemplar — gate obligations de-vacuated (AC17); docs; full suite <tally>"`

---

## Verification checklist (the reviewer's AC map)

| AC | Where proven |
|----|--------------|
| AC11 | Task 2 unit + Task 7 `TestAC11TemperamentOnTheLoop` |
| AC12 | Task 3 `TestThinSpotSurvey` + Task 4 params + Task 8 gate |
| AC13 | Task 3 `TestBranchSurvey` + Task 4 params + Task 8 gate |
| AC14 | Task 5 (D-6 + AS1 falsifier + emergence passes) |
| AC15 | Task 6 `TestAS3Introduction` |
| AC16 | Task 7 `TestAC16TheTwoNewWires` |
| AC17 | Task 9 (gate executes non-skipped on `swan_alternatives`; register attests) |
| AC18 | Task 8 tripwire |
| AC19 | Task 1 `TestFollowOnCleanups` |
| AC20 | Task 9 full suite |
