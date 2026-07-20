# Examination IV Defect Docket Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute all 12 items of Examination IV's defect docket
(`docs/ADVERSARIAL_EXAMINATION.md` §"The defect docket") — the protected-core A3 fixes
(①–③), the structural M carry + gate replay + fallback scoping (④–⑥), the poise repair
(⑦), the pre-RUN-13 oracle riders (⑧–⑩), the oracle hardening quartet (⑪), the
instrument fixes (⑫) — plus the paste-ready doc amendments from the five panel briefs.

**Architecture:** Consequence order ①→⑫. The core opening (①–③) is one authorized
window: open, fix, close, marker removed. ④ deletes ⑥'s reason to exist (the fallback),
so they merge into one task. Every fix follows the examination's own diagnosis: replace
trusting a label with recomputing the fact (guards re-run on what is actually erased;
gates replay what they certify; seals verified, not reprinted). TDD per task; the full
suite must end 0 failed.

**Tech Stack:** Python 3.12 / uv / pytest. No new dependencies.

## Global Constraints

- **Protected core ritual:** Tasks 1–3 modify protected modules
  (`formal_transformation_rules.py`, `ligature_manipulation_rules.py`,
  `vertex_splitting_merging_rules.py`). Task 1 creates `.core_modification_authorized`
  (the author authorized the opening 2026-07-19); Task 4 removes it after the core
  subset passes. Commits during the window may also carry `CORE_AUTHORIZED:` in the body.
- **EGI is immutable** — never mutate; use `with_*` constructors / `_rebuild_graph`.
- **Import pattern:** `from module_name import Foo` (never `from src.module_name`).
- **Frontier ink → main only** (this is frontier work; do NOT touch `release/moses`).
- **Never guess signatures** — `grep -i <name> docs/ARISBE_CORE_API_REFERENCE.md` or read
  the module before calling.
- **The panel briefs are the spec detail:** `runs/EXAMINATION_IV_BRIEFS/panel_A…E*.md`.
  When a task cites a brief line, read that region before implementing.
- Run targeted tests per task; the **full suite** (`uv run pytest tests/ -q`) runs once at
  Task 14. Core tasks also run the core subset (Task 4).
- Commit after each task: `git add <files> && git commit` with a descriptive message.

---

### Task 1: Open the core + item ① — ERA/IT− closure-guard re-run

The demonstrated A3 break: `ErasureRule.check_preconditions`
(`src/formal_transformation_rules.py:803-810`) runs `_refuse_quotation_boundary` on the
**raw** `context.selected_subgraph`, then (`:818-836`) expands the closure with
`for_erasure=True` and stores `context.expanded_subgraph` — which
`apply_transformation` (`:867`) erases **without re-running the guard**. The for-erasure
expansion pulls the quoting name (an edge's private argument vertex) into the erasure
set from outside the selection; `_rebuild_graph`'s pruning then silently drops the
quotation entry → the oval is demoted to an asserted negation.
`DeiterationRule.apply_transformation` (`:1600,1626-1634`) delegates to
`ErasureRule.apply_transformation`, so the ERA fix closes IT− too.
Counterexample: `runs/EXAMINATION_IV_BRIEFS/panel_D_formal_discipline.md:73-85`.

**Files:**
- Create: `.core_modification_authorized` (repo root, empty)
- Modify: `src/formal_transformation_rules.py:818-838` (ERA `check_preconditions`)
- Test: `tests/test_second_order_conservativity.py` (corpus fixture lives here)

**Interfaces:**
- Consumes: `_refuse_quotation_boundary(egi, target_area, selection, allow_whole_unit=…)`
  (`formal_transformation_rules.py:129`), `SubgraphClosureValidator.analyze_closure`.
- Produces: no signature changes — ERA/IT− refuse when the *expanded* closure touches
  the quotation apparatus.

- [ ] **Step 1: Open the core window**

```bash
touch /Users/mjh/Sync/GitHub/Arisbe/.core_modification_authorized
uv run python tools/core_protection_system.py --report
```
Expected: report shows modification authorized.

- [ ] **Step 2: Write the failing regression test** (new class in
  `tests/test_second_order_conservativity.py`, using the existing `tomos` fixture at
  `:44-60`)

```python
from formal_transformation_rules import (
    AreaPolarity, ErasureRule, TransformationContext,
)

class TestClosureGuardOnExpandedSet:
    """Docket ①: the guard must see what will actually be erased (Examination IV)."""

    def test_direct_engine_era_of_host_ink_refuses_via_expanded_closure(self, tomos):
        uod = tomos.load_uod("swan_third_tense", attest=False)
        egi = uod.current_egi
        superseded = next(e for e in egi.E if egi.rel.get(e.id) == "superseded")
        ctx = TransformationContext(
            source_egi=egi,
            target_area=egi.get_context(superseded.id),
            selected_subgraph=frozenset({superseded.id}),
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0,
        )
        result = ErasureRule().apply_transformation(ctx)
        assert not result.success
        assert "quotation" in (result.error_message or "").lower()
```

(If `egi.get_context` is not the area accessor, find the edge's area via
`presentation_ops.element_area` or the `parent_area` idiom at
`formal_transformation_rules.py:793-795`. `nesting_depth`/`area_polarity` must describe
a positive area — mirror how `panel_D_formal_discipline.md:73-85` built the context.)

- [ ] **Step 3: Run it — must FAIL (the break reproduces)**

Run: `uv run pytest tests/test_second_order_conservativity.py::TestClosureGuardOnExpandedSet -x -q`
Expected: FAIL — `result.success` is True today (the demonstrated demotion).

- [ ] **Step 4: Fix — re-run the guard on the expanded closure**

In `ErasureRule.check_preconditions`, immediately after
`context.__dict__['expanded_subgraph'] = analysis.closed_subgraph` (`:836`):

```python
            # Examination IV docket ①: the for-erasure expansion can pull the
            # quotation apparatus (quoting name / oval / quoted ink) into the
            # erasure set from OUTSIDE the raw selection. The guard must judge
            # the set that will actually be erased, not the selection.
            refusal = _refuse_quotation_boundary(
                egi,
                context.target_area,
                frozenset(analysis.closed_subgraph),
                allow_whole_unit=True,
            )
            if refusal:
                return False, refusal
```

**Caution:** the legitimate whole-unit ERA (flagged cut + quoting name selected
together) expands to include the oval's interior contents. The guard with
`allow_whole_unit=True` must still admit that case —
`tests/test_rules_second_order.py::TestOpacity::test_era_of_the_whole_unit_succeeds`
(`:223`) is the canary. If the guard rejects the interior-bearing expanded set for a
selected whole unit, teach the re-run call to treat "unit's cut ∈ selection ⇒ its
interior is part of the unit" (read `_refuse_quotation_boundary` at `:129-190` first;
adjust only the call/guard logic needed to keep that test green).

- [ ] **Step 5: Run the new test + both second-order rule suites**

Run: `uv run pytest tests/test_second_order_conservativity.py tests/test_rules_second_order.py tests/test_second_order_core.py -q`
Expected: all PASS (new refusal + whole-unit ERA still succeeds).

- [ ] **Step 6: Add the IT− twin test** (same class): identical context construction but
  via `DeiterationRule` — since IT− delegates to ERA's apply path, assert the same
  refusal. If `DeiterationRule.check_preconditions` (`:1323`) refuses earlier for an
  unrelated reason (no matching outer copy), assert refusal either way and name the
  guard reason when reachable:

```python
    def test_deiteration_delegating_path_cannot_demote_the_oval(self, tomos):
        uod = tomos.load_uod("swan_third_tense", attest=False)
        egi = uod.current_egi
        superseded = next(e for e in egi.E if egi.rel.get(e.id) == "superseded")
        ctx = TransformationContext(
            source_egi=egi,
            target_area=egi.get_context(superseded.id),
            selected_subgraph=frozenset({superseded.id}),
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0,
        )
        from formal_transformation_rules import DeiterationRule
        result = DeiterationRule().apply_transformation(ctx)
        assert not result.success
```

- [ ] **Step 7: Run rule-interaction + proof suites (blessed path unharmed)**

Run: `uv run pytest tests/test_rule_interaction.py tests/test_logical_proof_exercises.py tests/test_beta_proof_exercises.py -q`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add tests/test_second_order_conservativity.py src/formal_transformation_rules.py .gitignore
git commit -m "Docket ①: ERA/IT− quotation guard re-runs on the expanded closure

CORE_AUTHORIZED: Examination IV docket items ①–③ (author, 2026-07-19)"
```
(Do NOT commit `.core_modification_authorized` itself; it stays as the local marker
until Task 4.)

---

### Task 2: Item ② — `_rebuild_graph` pruning invariant

`_rebuild_graph` (`src/formal_transformation_rules.py:101-107`) prunes the quotation
map with `if k in c_ids and v in v_ids` — when exactly one of (cut, name) survives, the
entry is silently dropped and the surviving cut stands unflagged. The invariant: an
entry is dropped only when BOTH are gone; exactly one surviving raises. This makes the
mention→assertion demotion unrepresentable on **every** reconstruction path.

**Files:**
- Modify: `src/formal_transformation_rules.py:60-108` (`_rebuild_graph`)
- Test: `tests/test_second_order_core.py`

**Interfaces:**
- Produces: `_rebuild_graph` raises `ValueError` on a split quotation unit (house style:
  all second-order structural invariants raise `ValueError` — `egi_core_dau.py:352,363`).
  Tasks 3's routed sites inherit this invariant.

- [ ] **Step 1: Write the failing tests** (new class in `tests/test_second_order_core.py`,
  reusing the `_host_with_quotation` fixture idiom at `:65`)

```python
from formal_transformation_rules import _rebuild_graph

class TestRebuildPruningInvariant:
    """Docket ②: a quotation entry dies whole or not at all."""

    def test_cut_survives_name_gone_raises(self):
        g = _host_with_quotation()          # host + quoting name + flagged cut
        name_id = next(iter(g.quotation.values()))
        with pytest.raises(ValueError, match="quotation"):
            _rebuild_graph(
                g,
                V=frozenset(v for v in g.V if v.id != name_id),
                E=g.E,
                nu=g.nu,
                cuts=g.Cut,
                area=frozendict({a: c - {name_id} for a, c in g.area.items()}),
                rel=g.rel,
            )

    def test_name_survives_cut_gone_raises(self):
        g = _host_with_quotation()
        cut_id = next(iter(g.quotation.keys()))
        interior = g.area.get(cut_id, frozenset())
        with pytest.raises(ValueError, match="quotation"):
            _rebuild_graph(
                g,
                V=frozenset(v for v in g.V if v.id not in interior),
                E=frozenset(e for e in g.E if e.id not in interior),
                nu=g.nu,
                cuts=frozenset(c for c in g.Cut if c.id != cut_id),
                area=frozendict({a: c - {cut_id} for a, c in g.area.items()
                                 if a != cut_id}),
                rel=g.rel,
            )

    def test_both_gone_prunes_cleanly_and_both_kept_survive(self):
        g = _host_with_quotation()
        rebuilt = _rebuild_graph(g, V=g.V, E=g.E, nu=g.nu, cuts=g.Cut,
                                 area=g.area, rel=g.rel)
        assert dict(rebuilt.quotation) == dict(g.quotation)
```

(Adapt the exact fixture/nu/rel bookkeeping to `_host_with_quotation`'s real shape —
read it first; the point is each test's survival pattern, not the plumbing.)

- [ ] **Step 2: Run — the two `raises` tests must FAIL** (silent drop today)

Run: `uv run pytest tests/test_second_order_core.py::TestRebuildPruningInvariant -q`

- [ ] **Step 3: Implement the invariant** — replace `:101-107`'s dict comprehension:

```python
    surviving_quotation = {}
    for k, v in source.quotation.items():
        cut_alive, name_alive = k in c_ids, v in v_ids
        if cut_alive and name_alive:
            surviving_quotation[k] = v
        elif cut_alive or name_alive:
            raise ValueError(
                f"quotation unit split by reconstruction: cut {k} "
                f"{'survives' if cut_alive else 'gone'}, name {v} "
                f"{'survives' if name_alive else 'gone'} — a quotation is "
                "erased whole or not at all"
            )
```
and pass `quotation=frozendict(surviving_quotation)`.

- [ ] **Step 4: Run the file + the rules suite**

Run: `uv run pytest tests/test_second_order_core.py tests/test_rules_second_order.py tests/test_second_order_conservativity.py -q`
Expected: PASS (with Task 1's guard, no engine path reaches the raise; the invariant is
defense in depth).

- [ ] **Step 5: Commit** — `git commit -m "Docket ②: _rebuild_graph refuses a split quotation unit"`

---

### Task 3: Item ③ — Chapter 16 map-forwarding

Six raw `RelationalGraphWithCuts(...)` construction sites forward only
`V,E,nu,sheet,Cut,area,rel`, stripping `alphabet`/`rho`/`sort`/`quotation`:
`ligature_manipulation_rules.py:99,289,449,653` and
`vertex_splitting_merging_rules.py:177,424` (the `:813`/`:514` sites are `__main__`
demos — leave them). Fix: route all six through `_rebuild_graph` (repairs all four maps
at once) **and** guard each rule against selections touching the quotation apparatus
(`_refuse_quotation_boundary` at the top of each `apply`, `deep=True` semantics like
IT±: these ligature/vertex ops re-plumb identity, so refuse the apparatus entirely).

**Files:**
- Modify: `src/ligature_manipulation_rules.py` (4 sites + guards),
  `src/vertex_splitting_merging_rules.py` (2 sites + guards)
- Test: `tests/test_rules_second_order.py` (new class `TestChapter16MapForwarding`)

**Interfaces:**
- Consumes: `_rebuild_graph(source, *, V, E, nu, cuts, area, rel)` and
  `_refuse_quotation_boundary` from `formal_transformation_rules` (both modules already
  import from it — verify, else add the import).
- Produces: Chapter 16 rules preserve `sort`/`quotation`/`rho`/`alphabet` on graphs the
  operation doesn't touch second-order-wise, and refuse loudly when the selection
  involves a quoting name, a flagged cut, or quoted ink.

- [ ] **Step 1: Write the failing tests**

```python
class TestChapter16MapForwarding:
    """Docket ③: preservation-or-refusal for the ligature/vertex modules."""

    def test_ligature_move_on_quotation_bearing_graph_preserves_maps_or_refuses(self):
        g = _quotation_bearing_host_with_spare_ligature()   # apparatus + unrelated ligature
        result = _apply_extend_restrict_on_the_unrelated_ligature(g)
        if result.success:
            assert dict(result.result_egi.quotation) == dict(g.quotation)
            assert dict(result.result_egi.sort) == dict(g.sort)
            assert dict(result.result_egi.rho) == dict(g.rho)
            assert result.result_egi.alphabet == g.alphabet
        else:
            assert "quotation" in (result.error_message or "").lower()

    def test_vertex_merge_targeting_the_quoting_name_refuses(self):
        g = _quotation_bearing_host_with_spare_ligature()
        result = _apply_vertex_merge_on_the_quoting_name(g)
        assert not result.success
```

Build the fixture inline per the file's convention (`create_cut`/`create_vertex` +
`.with_quotation_binding(...)`, module docstring `:71`); write one helper per exercised
rule (`ExtendRestrictLigatureRule`, `VertexMergingRule` — construct their contexts the
way the modules' own demos do). Cover at least one rule per module; the other routed
sites are covered by the shared `_rebuild_graph` path plus Task 2's invariant.

- [ ] **Step 2: Run — must FAIL** (maps silently stripped today)

Run: `uv run pytest tests/test_rules_second_order.py::TestChapter16MapForwarding -q`

- [ ] **Step 3: Implement** — at each of the six sites, replace the raw constructor:

```python
        # before (site pattern):
        # return RelationalGraphWithCuts(V=…, E=…, nu=…, sheet=…, Cut=…, area=…, rel=…)
        # after:
        return _rebuild_graph(graph, V=…, E=…, nu=…, cuts=…, area=…, rel=…)
```
and add at the top of each rule's `apply`/precondition path:

```python
        refusal = _refuse_quotation_boundary(
            graph, target_area, selection, allow_whole_unit=False, deep=True)
        if refusal:
            return TransformationResult(False, None, refusal, {})
```
(Match each rule's actual local variable names / area derivation; if a rule has no
selection concept, guard on the vertices/edges it will touch. Read
`_refuse_quotation_boundary`'s signature first — `deep=` exists for IT±'s refusal at
`:1335`; reuse the same arguments IT± uses.)

- [ ] **Step 4: Run the module suites**

Run: `uv run pytest tests/test_rules_second_order.py tests/ -q -k "ligature or splitting or merging"`
Expected: PASS — new tests green, existing Chapter 16 tests untouched (first-order
graphs have empty maps; `_rebuild_graph` forwards empties bit-identically).

- [ ] **Step 5: Fix `_rebuild_graph`'s docstring** (`formal_transformation_rules.py:75-79`)
  — it may now truthfully claim Chapter 16 routes through it; update the sentence.

- [ ] **Step 6: Commit** — `git commit -m "Docket ③: Chapter 16 rules route through _rebuild_graph + quotation guard"`

---

### Task 4: Close the core window

**Files:**
- Delete: `.core_modification_authorized`

- [ ] **Step 1: Run the core validation subset + the six §7 correspondence shapes**

```bash
uv run python tools/core_protection_system.py --report
uv run pytest tests/test_correspondence_invariant.py tests/test_chapter15_formal_calculus.py tests/test_rule_interaction.py tests/test_subgraph_closure_validation.py tests/test_second_order_core.py tests/test_rules_second_order.py tests/test_second_order_conservativity.py -q
```
Expected: all PASS. (If `test_chapter15_formal_calculus.py` doesn't exist under that
name, run the core list `core_protection_system.py:166-186` names.)

- [ ] **Step 2: Close the window**

```bash
rm /Users/mjh/Sync/GitHub/Arisbe/.core_modification_authorized
uv run python tools/core_protection_system.py --report
```
Expected: report shows core locked + CLEAN.

- [ ] **Step 3: Commit** any stragglers (nothing expected; the marker was never tracked).

---

### Task 5: Items ④ + ⑥ — structural M carry; the fallback dies

`live_runner.py` carries M across segments as EGIF text (`:393` `model_egif =
generate_egif(...)`; reseed `:409-417`; decay `:434`; digest `:447`; checkpoint `:318`;
resume `:295`). The EGIF round-trip merges cross-cell shared constants (the F2¹³
trigger), which made the licensed ERA refuse and forced the `_structural_retract_atom`
fallback (`agon_evolution.py:800-852`) — which matches label-identical atoms over ALL
of `g.E`, reaching inside denial cells and exhibits (item ⑥). Fix: carry
`egi_io.to_dict(egi)` (structural JSON — carries ids, `sort`, `quotation`;
`from_dict` restores). Then delete the fallback; replace its role with skip-and-count
(the house count-or-refuse idiom) for the one residual path (legacy EGIF checkpoints).

**Files:**
- Modify: `src/live_runner.py` (carry, `_save_state`, `resume`, constructor),
  `src/agon_evolution.py` (`_apply_decay` `:855-907`; delete
  `_structural_retract_atom` `:800-852`)
- Test: `tests/test_live_runner.py`, `tests/test_agon_evolution.py`

**Interfaces:**
- Consumes: `to_dict(egi) -> Dict` (`egi_io.py:15`), `from_dict(d) -> RelationalGraphWithCuts`
  (`egi_io.py:41`), `same_graph`, `world_scroll.retract_from_m` (cell-scoped, the only
  remaining retraction path).
- Produces: checkpoint JSON key `"model_json"` (structural dict); `resume` accepts
  legacy `"model_egif"` (parse once, carry structurally thereafter);
  `_apply_decay` on a refused licensed retraction records a skip
  (`decay_skipped` count + note), never structural surgery.

- [ ] **Step 1: Write the failing tests**

```python
def test_carry_preserves_resident_M_structurally_same_graph():
    """Docket ④: a constant shared across two cells survives the segment carry."""
    # Build a resident M: wrap_m / enlarge_m two cells both mentioning ("Opus")
    # (see test_world_scroll.py's construction idiom), run one ReplaySource
    # segment, and assert same_graph(final M, expected M). Under EGIF carry this
    # is False (constants merge); under to_dict carry it must hold.

def test_carry_preserves_quotation_bearing_cell():
    """V2a.2 composition test (a): a banked quotation cell survives the carry."""
    # Resident M with one cell holding a quotation (scribe_quotation into a cell
    # or with_quotation_binding); one segment; assert the final M's quotation
    # map is intact and same_graph holds. Under EGIF carry this RAISES
    # SecondOrderNotInLinearForm at generate_egif — the exact V2a.2 blocker.

def test_decay_never_reaches_denial_cells_or_exhibits():
    """Docket ⑥ pin: licensed decay is cell-scoped."""
    # Resident M: cell A holds (rel "A" "B"); cell B holds ~[ (rel "A" "B") ]
    # (a denial). Decay the standing atom (ttl forces it). Assert the denial
    # cut's interior atom survives; the standing atom is gone.

def test_decay_skip_is_counted_never_structural():
    """A retraction the licensed rule refuses is skipped and counted."""
    # Force a refusal (e.g. an atom whose argument vertex is shared cross-cell
    # by construction), run decay, assert the atom SURVIVES, a skip counter /
    # note records it, and no unlicensed surgery happened (same_graph with the
    # pre-decay M).
```

Write these as real tests against the ReplaySource + injected-clock harness already in
`tests/test_live_runner.py` (`:41-47,192-206` show the loop construction); the world-
scroll construction idioms are in `tests/test_world_scroll.py`. Update the existing
carry/resume tests that read `data["model_egif"]` (`:152,192-206,209,316,353`) to the
new `"model_json"` key — and keep ONE legacy-resume test: write an old-shape state file
with `"model_egif"` and assert `resume` still continues the run.

- [ ] **Step 2: Run — new tests FAIL** (`uv run pytest tests/test_live_runner.py -q`)

- [ ] **Step 3: Implement the structural carry** in `live_runner.py`:
  - carry variable `model_state: dict` (`to_dict(res.uod.current_egi)` at `:393`);
  - reseed path: `g = from_dict(model_state)` → `enlarge_m(...)` → `to_dict(g)`;
  - `_decay` operates on the EGI (`from_dict` in, `to_dict` out) via
    `retract_from_m` only;
  - `_save_state` writes `"model_json": model_state`; `resume` reads `"model_json"`,
    falling back to parsing legacy `"model_egif"` once;
  - constructor accepts an EGIF string OR a structural dict for the initial M
    (`isinstance(m, dict)`);
  - `_write_refusal_note` (`:556`) may keep EGIF for human legibility.

- [ ] **Step 4: Delete the fallback** in `agon_evolution.py`: remove
  `_structural_retract_atom` (`:800-852`); in `_apply_decay` (`:885-893`) replace the
  except-branch with skip-and-count:

```python
        except (AssertionError, ValueError) as exc:
            self._decay_skipped.append((atom_key, str(exc)))
            log_note = f"decay skipped (licensed rule refused): {exc}"
            continue   # the atom stands; the skip is recorded, never silent
```
(Adapt to the loop's actual structure; surface the count in `RoundOutcome`/digest the
way existing counters are surfaced.)

- [ ] **Step 5: Run** `uv run pytest tests/test_live_runner.py tests/test_agon_evolution.py tests/test_wikidata_source.py tests/test_wiki_dispute_membrane.py tests/test_resolving_membrane.py -q`
Expected: PASS (the membranes exercise the loop end-to-end).

- [ ] **Step 6: Commit** — `git commit -m "Docket ④+⑥: structural M carry (to_dict); F2¹³ fallback deleted, decay skip-and-count"`

---

### Task 6: Item ⑤ — the polarity gate replays derivations

The gate (`tests/test_corpus_polarity_discipline.py:124-157`) asserts derivation
*labels* (`m_enlargement ⇒ ["INS"]` …) but never re-executes them; only PEEL recomputes
(`:267-284`). Fix: for every replayable act, re-execute from `from_state` and assert
`same_graph` with `to_state`. Params suffice for 6 of 7 acts; `world_withdrawal`
(`revise_step`, `m_steps.py:440-451`) doesn't record `new_m_egif` — add it.

**Files:**
- Modify: `src/m_steps.py` (`revise_step` params gain `new_m_egif`)
- Test: `tests/test_corpus_polarity_discipline.py` (new gate test)

**Interfaces:**
- Consumes: `world_scroll.enlarge_m / retract_from_m / entertain_episode /
  discharge_episode / abandon_episode` (verify signatures in the module);
  `_chain_states` fixture idiom (`test_corpus_polarity_discipline.py:66-70`),
  `same_graph`.
- Produces: the standing gate `test_recorded_derivations_replay_identically`,
  parametrized over the 19 M-bearing UoDs.

- [ ] **Step 1: Add `new_m_egif` to `revise_step`'s recorded params** (`m_steps.py:440-451`)
  — one line in the params dict; update the docstring's param list.

- [ ] **Step 2: Write the gate test** (following the PEEL-recomputation pattern
  `:267-284` exactly — same fixture loading, same parametrization):

```python
def test_recorded_derivations_replay_identically(self, uod_id, tomos):
    """Docket ⑤: the gate re-executes what the record asserts (the PEEL
    pattern applied to derivations)."""
    chain = tomos.load_chain(uod_id)
    if chain is None:
        pytest.skip("no chain")
    replayed = skipped = 0
    for step in chain.steps:
        p = step.parameters or {}
        act, deriv = p.get("act"), p.get("derivation")
        if not act or not deriv:        # bare-fixture / honest-[] steps
            continue
        before = chain.states.get(step.from_state_id)
        after = chain.states.get(step.to_state_id)
        if before is None or after is None:
            continue
        if act == "m_enlargement":
            result = enlarge_m(before, p["fact_egif"])
        elif act == "m_retraction":
            result = retract_from_m(
                before, subgraph_egif=p.get("subgraph_egif"),
                relation=p.get("relation"), labels=p.get("labels"))
        elif act == "m_revision":
            g = retract_from_m(
                before, subgraph_egif=p.get("subgraph_egif"),
                relation=p.get("relation"), labels=p.get("labels"))
            result = enlarge_m(g, p["fact_egif"])
        elif act == "episode_entertained":
            result = entertain_episode(before, p["proposal_egif"])
        elif act == "m_discharge":
            result = discharge_episode(before, p["proposal_egif"])
        elif act == "episode_abandoned":
            result = abandon_episode(before, p["proposal_egif"])
        elif act == "world_withdrawal":
            if "new_m_egif" not in p:
                skipped += 1            # pre-amendment historical step
                continue
            result = withdraw_and_resupply(before, p["new_m_egif"])
        else:
            continue
        assert same_graph(_graph_of(result), after), (
            f"{uod_id}: {act} step to {step.to_state_id} does not replay")
        replayed += 1
    # the gate must actually bite somewhere across the corpus
    assert replayed > 0 or skipped >= 0
```

(`_graph_of`: several `world_scroll` functions return the graph directly, some return
tuples — read each signature and normalize. `retract_from_m`'s exact kwargs: read
`world_scroll.py:422+` first. Handle labels list/tuple coercion — recorded JSON gives
lists.)

- [ ] **Step 3: Run the gate corpus-wide** —
  `uv run pytest tests/test_corpus_polarity_discipline.py -q`
Expected: PASS with `replayed > 0` on the M-bearing UoDs. Any failure here is a REAL
finding (a chain whose record doesn't replay) — investigate before touching the test;
the likely benign causes are signature mismatches, not corpus rot.

- [ ] **Step 4: Add the falsifier** — a hand-built in-memory chain step whose
  `derivation: ["ERA"]` annotation lies about a structural edit; assert the replay
  detects the mismatch (`same_graph` False). Mirror the existing silent-⊥-door
  falsifier's construction (`:212-233`).

- [ ] **Step 5: Run + commit** —
  `uv run pytest tests/test_corpus_polarity_discipline.py tests/test_m_steps.py tests/test_world_scroll.py -q`
then `git commit -m "Docket ⑤: polarity gate replays recorded derivations; revise_step records new_m_egif"`

---

### Task 7: Item ⑦ — poise: thrash requires thrash; "storm" for absorbed tempo

`_window_reading` (`agon_metalearning.py:583-588`) labels a window "thrash" when
`stumbles > max_stumbles` even with `thrash == 0` — >1 *absorbed* stumbles (the
doctrine's own picture of competence, `:530-531`) reads as failure. Same bug in
`poise_from_digests` (`:659-660`, where thrash is never computable).

**Files:**
- Modify: `src/agon_metalearning.py` (`_window_reading` `:583-588`,
  `poise_from_digests` `:657-662`, docstrings `:555-556,563`)
- Test: `tests/test_agon_metalearning.py`

- [ ] **Step 1: Write the failing test + re-pin the digest test**

```python
def test_two_absorbed_stumbles_read_storm_not_thrash():
    """Docket ⑦: absorbed stumbles beyond threshold are 'storm: absorbing at
    rate' — a non-poised reading, but not the thrash that never happened."""
    # window with 2 stumble episodes, every situation consistently disposed
    # (thrash_situations == 0)
    reading = _the_window_reading_for_that_fixture(max_stumbles=1)
    assert reading.poised is False
    assert reading.failure == "storm"
```
And change `tests/test_agon_metalearning.py:284`:
`readings[2].failure == "thrash"` → `== "storm"` (the storm fixture has 4 stumbles, 0
computable thrash). `test_thrash_pole_inconsistent_disposition_breaks_poise` (`:252`)
stays as-is — now the only thrash path.

- [ ] **Step 2: Run — FAIL** (`uv run pytest tests/test_agon_metalearning.py -q`)

- [ ] **Step 3: Implement** — in `_window_reading`:

```python
        if engagement == 0.0:
            poised, failure = False, "rigidity"
        elif thrash > 0:
            poised, failure = False, "thrash"
        elif stumbles > max_stumbles:
            poised, failure = False, "storm"   # absorbing at rate — not thrash
        else:
            poised, failure = True, None
```
Same third branch in `poise_from_digests` (rigidity / storm / poised only — thrash is
not computable from a digest and must never be claimed there). Add "storm" to the
`failure` docstrings.

- [ ] **Step 4: Run + commit** — `uv run pytest tests/test_agon_metalearning.py -q`;
`git commit -m "Docket ⑦: poise gains the storm reading; thrash requires thrash"`

---

### Task 8: Item ⑧ — salted seal + verified reveals

`seal` (`oracle_notes.py:65-68`) is `sha256(forecast)` over a 4-word public vocabulary
— every seal is a precomputable constant. `build_reveals` (`:560-581`) reprints stored
hashes without recomputing. Fix per `panel_C…md:78-88`: per-question nonce stored
beside the plaintext in `forecasts.jsonl`; `build_reveals` recomputes
`sha256(nonce‖plaintext)` and marks mismatch `verdict: "seal-broken"`.

**Files:**
- Modify: `src/oracle_notes.py` (`seal`, `_render_question_block:260`,
  `record_asked:509-514`, `_latest_forecast:555-558`, `build_reveals:560-581`),
  `tools/run_vault_v0.py` (`_run_oracle:205` nonce generation)
- Test: `tests/test_oracle_notes.py` (new `TestSeal` class)

**Interfaces:**
- Produces: `seal(forecast: str, nonce: str = "") -> str` =
  `sha256((nonce + forecast).encode()).hexdigest()` (empty-nonce = legacy value, so old
  ledger rows still verify); `record_asked(..., nonce=...)` stores `"nonce"` in the
  forecast row; `render_note`/`_render_question_block` accept the per-qid nonce mapping
  so note-seal == ledger-seal; driver generates nonces via an injectable
  `nonce_factory=lambda: secrets.token_hex(8)` (tests inject deterministic ones).

- [ ] **Step 1: Write the failing tests**

```python
class TestSeal:
    def test_salted_seal_differs_from_dictionary_hash(self):
        assert seal("collected", "ab12") != seal("collected")
        assert seal("collected", "ab12") == hashlib.sha256(
            b"ab12collected").hexdigest()

    def test_reveals_recompute_and_flag_a_doctored_row(self, tmp_path):
        # record_asked with nonce; doctor the forecasts.jsonl row's
        # forecast_plain; build_reveals must emit verdict "seal-broken"
        ...
    def test_intact_row_reveals_hit_or_miss_as_before(self, tmp_path):
        ...
    def test_note_never_contains_nonce_or_plaintext(self):
        # render a note with sealed forecasts; assert nonce and forecast
        # plaintext absent from the markdown
        ...
```

- [ ] **Step 2: Run — FAIL** (`uv run pytest tests/test_oracle_notes.py::TestSeal -q`)

- [ ] **Step 3: Implement** the interface above. The coupling to resolve: the renderer
  currently recomputes the seal internally (`:260`) — thread a `nonces: dict[qid, str]`
  from `_run_oracle` (which generates them at candidate-selection time) through
  `render_note` to the block renderer AND into `record_asked`. `build_reveals`:

```python
        expected = seal(forecast["forecast_plain"], forecast.get("nonce", ""))
        verdict = ("seal-broken" if expected != forecast["forecast_hash"]
                   else score(forecast["forecast_plain"], answer))
```

- [ ] **Step 4: Run the oracle + e2e suites** —
`uv run pytest tests/test_oracle_notes.py tests/test_vault_world.py -q`

- [ ] **Step 5: Commit** — `git commit -m "Docket ⑧: salted seal, reveals recompute, seal-broken verdict"`

---

### Task 9: Item ⑨ — the People/ filter binds the question generator

The consent boundary (`People/`, `Kith_Kin/`, `Household/` metadata-only — vault spec
item 3) exists only in `vault_world.py`'s docstring. `_horizon_candidates`
(`oracle_notes.py:140-159`) promotes the two largest horizon items vault-wide — a
`People/x.pdf` becomes question text soliciting what the reader may not read.

**Files:**
- Modify: `src/vault_world.py` (export `METADATA_ONLY_DIRS = frozenset({"People",
  "Kith_Kin", "Household"})`), `src/oracle_notes.py` (`_horizon_candidates` filter)
- Test: `tests/test_oracle_notes.py`

- [ ] **Step 1: Failing test**

```python
def test_people_folder_never_yields_a_question_candidate():
    # horizon carries People/x.pdf (largest item) + Clippings/y.pdf;
    # candidates must ask about y.pdf only; the People item REMAINS on the
    # horizon (snapshot still counts it — excluded from asking, never dropped)
```

- [ ] **Step 2: Run — FAIL.**

- [ ] **Step 3: Implement** — in `_horizon_candidates`:

```python
        from vault_world import METADATA_ONLY_DIRS
        items = [it for it in items
                 if Path(it.ref).parts[:1] not in
                    tuple((d,) for d in METADATA_ONLY_DIRS)]
```
(or the cleaner `Path(it.ref).parts[0] not in METADATA_ONLY_DIRS` with a root-item
guard). The items stay registered on the `Horizon` — only promotion is suppressed.

- [ ] **Step 4: Run + commit** — `uv run pytest tests/test_oracle_notes.py -q`;
`git commit -m "Docket ⑨: consent boundary binds the question generator (People/ filter)"`

---

### Task 10: Item ⑩ — P2¹³ made falsifiable

P2¹³ as registered (`runs/RUN_13_LOG.md:18-20`) has no base rate, no instrument, no
comparator, and names a docket that nothing wires (`wants_from_docket` — dead code,
`attention_economy.py:200-209`). Operational form (`panel_C…md:70-72`): per segment, N
docket-selected + N template-random questions, seeded random order, unlabeled; the
author marks `**R:** trivial|non-trivial`; pass iff docket non-trivial rate exceeds
random by ≥25 points over ≥2 segments; ceiling canary at ≥90%.

**Files:**
- Modify: `src/oracle_notes.py` (`candidates_from_run` gains the docket arm; `**R:**`
  parsing in `parse_note`; `p2_13_report`), `tools/run_vault_v0.py` (`_run_oracle`
  wires the economy's docket + the random arm + seeded interleave; ratings ledger),
  `runs/RUN_13_LOG.md` (the pre-registration amendment)
- Test: `tests/test_oracle_notes.py`

**Interfaces:**
- Produces: `candidates_from_run(..., docket=None, rng=None)` — with a docket, emits N
  docket-selected candidates (`arm="docket"`) drawn via
  `wants_from_docket`/economy-ranked wants, and N template-random (`arm="random"`,
  same templates instantiated on seeded-random notes); arms recorded in
  `forecasts.jsonl` rows, NEVER in the note; `parse_note` returns per-qid `rating`
  from `**R:** trivial|non-trivial`; `OracleLedger.record_rating` → `ratings.jsonl`;
  `p2_13_report(ledger) -> dict` with per-segment rates, the ≥25-point/≥2-segment
  verdict, and `"uninformative"` when ≥90% of all rated questions are non-trivial.
  Default N=2 (respects the ≤5-question budget with the reflective).

- [ ] **Step 1: Failing tests** — (a) with a docket present, the note carries 2+2
  questions in seeded order with no arm labels in the markdown; (b) `parse_note`
  recovers `**R:**` ratings; (c) `p2_13_report` passes a fixture where docket-arm
  non-trivial rate is 100% vs random 50% over 2 segments, fails at <25 points, and
  reads `uninformative` at the ceiling; (d) `wants_from_docket` is actually called
  (a docket want's key shows up in a docket-arm candidate's provenance).

- [ ] **Step 2: Run — FAIL.**

- [ ] **Step 3: Implement.** The docket arm's question template voices a want (e.g. a
  `read`/`scan` want over a note the economy ranks high): "The docket ranks
  `<ref>` worth attention (<reason>). What is it, in a line?" — forecast `"unknown"`
  unless the want kind implies one. Keep templates parallel to the random arm's so
  blinding holds (same shapes, different selection).

- [ ] **Step 4: Amend `runs/RUN_13_LOG.md`** — append under P2¹³ (paste-ready,
  `panel_C…md:70-72`):

> **P2¹³ operational form (amended 2026-07-19, pre-first-note).** Per segment the note
> carries N docket-selected and N template-random questions in seeded random order,
> unlabeled; the author marks each `**R:** trivial|non-trivial`; pass iff the
> docket-selected non-trivial rate exceeds the template-random rate by ≥25 points over
> ≥2 segments. Ceiling canary: if the author rates ≥90% of all questions non-trivial in
> a segment, that segment is declared uninformative for P2¹³. All parts
> deterministic/offline except the author's marks.

- [ ] **Step 5: Run + commit** — `uv run pytest tests/test_oracle_notes.py -q`;
`git commit -m "Docket ⑩: P2¹³ operational — docket arm, R-instrument, comparator, ceiling canary"`

---

### Task 11: Item ⑪ — asked_ever expiry/drift, decline synonyms, preempt invariance, digest split

**Files:**
- Modify: `src/oracle_notes.py` (`asked_ever:544-550`, `parse_note:427`,
  candidate-template option order), `tools/run_vault_v0.py` (`:190` filter; digest),
  `src/probe_feed.py` (added/removed counters)
- Create: `tests/test_predict_never_preempt.py`
- Test: `tests/test_oracle_notes.py`, `tests/test_probe_feed.py`

- [ ] **Step 1: asked_ever re-eligibility.** `asked_ever(qid, within_last_n_notes=None)`
  — `None` keeps today's forever-suppression; an int means "asked within the last N
  distinct note dates". Driver (`run_vault_v0.py:190`) passes a default (6). Drift
  re-ask: `_run_oracle` re-asks ONE early question verbatim once ≥2 segments have
  passed since it was asked (a `reask` source, capped 1/note); a changed answer lands
  as a new outcome row (`record_outcome_once:539-541` already appends on change) and
  the digest counts it as `drift_data`. Tests: re-eligible after N; verbatim re-ask
  appears; changed answer preserved as a second row, first row intact.
- [ ] **Step 2: Decline synonyms.** At `parse_note:427` replace the single equality with
  a normalized set:

```python
_DECLINE_MARKERS = frozenset({"declined", "decline", "pass", "—", "-",
                              "rather not", "prefer not to say"})
...
elif answer.strip().rstrip(".").lower() in _DECLINE_MARKERS:
```
  Test: each marker (with trailing period / case variants) reads `declined`, AND a
  declined answer's text never appears in a subsequent note's Reveals section.
- [ ] **Step 3: Predict-never-preempt invariance test** (new file, modeled on
  `test_second_order_conservativity.py`): build a fixture M twice, identical except one
  carries a quoted `(asserted "author" ⌜P⌝)` cell (use `scribe_quotation` /
  `with_quotation_binding` inside a residence cell — `quotation_overlay` +
  `world_scroll` APIs); run the mechanical panel's disposition of one fixed proposal
  against both; assert identical disposition and verdict. Also the question-neutrality
  rider: seed-alternate the two-option order in `_provenance_candidates:105` /
  `_multi_journal_candidates:129` (rng-injected), test that both orders occur across a
  seeded run.
- [ ] **Step 4: Digest added/removed split.** `probe_feed.propose` (`:91-124`) computes
  `added = len(atoms - prev_atoms)`, `removed = len(prev_atoms - atoms)` alongside the
  symmetric-diff `events`; expose both on the feed; `run_vault_v0._digest` (`:61-80`)
  reports `m_added`/`m_removed` per segment. Test: a decayed atom shows in `removed`,
  not `added`.
- [ ] **Step 5: Run + commit** —
`uv run pytest tests/test_oracle_notes.py tests/test_probe_feed.py tests/test_predict_never_preempt.py -q`;
`git commit -m "Docket ⑪: asked_ever expiry + drift re-ask, decline synonyms, preempt invariance, digest split"`

---

### Task 12: Item ⑫a — K1 join + K3 re-derivation

**K1** (panel A D1.1, `panel_A:48`): the ratified measure's severity×ledger join does
not exist in code — `ScoreEntry` (`resolving_membrane.py:87-96`) has no severity field;
`select_best` is severity-blind. Build the declared join:
`K1 = Σ_hits w(sev) − Σ_misses w(sev)`, `w(sev) = sev` (declared linear weights;
the anchors' operational definition stays an open obligation carried in the docs).
**K3** (D1.3, `panel_A:50`): `ratio = derived/laws` ≈ N (the extent confound —
2.0/20.0/200.0 for the identical law). Re-derive: bounded
`ratio = derived/(explicit+derived) ∈ [0,1)`; keep the old number as
`yield_per_law` (honestly renamed).

**Files:**
- Modify: `src/resolving_membrane.py` (`ScoreEntry`, `record`, new `k1_score`,
  `select_best` severity-aware tiebreak), `src/model_materialization.py`
  (`KnowledgeCompression:445-475`)
- Test: `tests/test_resolving_membrane.py`, `tests/test_model_materialization.py`

- [ ] **Step 1: Failing tests.**

```python
def test_k1_severity_join_separates_equal_counts():
    # two ledgers, identical hit/miss counts; one's hits carry severity 8.0,
    # the other's 1.0; k1_score differs 8:1; net_score still ties (unchanged)

def test_k1_ordering_invariant_under_positive_scaling():
    # multiply every severity by 3: k1_score ordering over the two ledgers
    # is unchanged (the linear-weight invariance that IS provable; the full
    # monotone-rescale obligation stays a doc-carried concession)

def test_k3_ratio_is_extent_invariant():
    # the man/mortal law over 2 vs 20 individuals: ratio identical (0.5),
    # yield_per_law scales with N (2.0 vs 20.0)
```
Update the three existing K3 tests (`test_model_materialization.py:214-231`):
syllogism `ratio == 2.0` → `ratio == 0.5` and `yield_per_law == 2.0`; no-laws stays 0;
non-Horn still weighs `yield_per_law`'s denominator.

- [ ] **Step 2: Run — FAIL.**

- [ ] **Step 3: Implement.** `ScoreEntry` gains `severity: float = 1.0`;
  `record(..., severity=1.0)`; `k1_score` property = `sum(sev of hits) − sum(sev of
  misses)`; `select_best` keeps `net_score` primary (behavior-preserving) and
  documents `k1_score` as the severity-aware variant callers may rank by.
  `KnowledgeCompression`: `ratio = derived/(explicit+derived) if (explicit+derived)
  else 0.0`; `yield_per_law` = the old formula (skipped laws still weigh its
  denominator).

- [ ] **Step 4: Run + commit** —
`uv run pytest tests/test_resolving_membrane.py tests/test_model_materialization.py -q`;
`git commit -m "Docket ⑫a: K1 severity join built; K3 re-derived extent-invariant (yield_per_law kept)"`

---

### Task 13: Item ⑫b — attribution pins + churn-pump + ablation harness

Attribution (panel B 11(a), `panel_B:69-87`): yield = symmetric-diff churn credited to
every chosen want's kind (`probe_feed.py:97-98` → `attention_economy.observe:117-123`)
— decay counts as yield; budget>1 smears credit. Pins document it; the churn-pump
experiment tests the noisy-TV guard; the exam ablation harness promotes
`runs/EXAMINATION_IV_BRIEFS/ablation_pilot.py` and adds the discriminating-world +
cost-purse arms (panel B 3(d), `panel_B:51-54,109`).

**Files:**
- Create: `tools/run_rung1_ablation_exam4.py`
- Modify: `src/arithmetic_world.py` (discriminating-world seed variant),
  `src/probe_feed.py` (optional cost-purse accounting)
- Test: `tests/test_attention_economy.py` (pins), `tests/test_arithmetic_world.py`
  or the harness's own smoke test

- [ ] **Step 1: The two pins** (11(d).1) as tests that PASS by documenting current
  behavior, each with a comment naming it a defect pin:

```python
def test_pin_shrinking_model_credits_a_barren_kind():
    # decay-only delta (atoms leave M) still yields events > 0 credited to the
    # chosen kind — pinned as the known decay-counts-as-yield defect (⑫c)

def test_pin_budget_two_smears_first_delta_and_drops_second():
    # at probe_budget=2 the first proposal's delta credits both kinds and the
    # second proposal's delta is never observed — pinned defect (⑫c)
```

- [ ] **Step 2: The harness.** `tools/run_rung1_ablation_exam4.py`: copy
  `ablation_pilot.py`'s six arms (A0–A5) and add:
  - **discriminating-world arm**: seed the false law `~[ (square *x) ~[ (even x) ] ]`
    with NO severity-8 hunt wants over its instances (counterexample n=9 reachable only
    via severity-1 confirm/extend probes); report refutation round for economy vs
    scatter vs severity-greedy;
  - **cost-purse arm**: accumulate each executed want's `cost` and stop at a 30-unit
    purse; report refutation-or-exhaustion per arm.
  Deterministic, offline, CLI `--arm <name> --rounds N`. Smoke test: each arm runs 10
  rounds without error and the journal is reproducible (two runs identical).
- [ ] **Step 3: The churn-pump experiment** (11(d).2) as a harness arm:
  `--arm churn_pump` — ttl=8, 120 rounds, a persistent `refresh` kind re-delivering a
  fixed 5-atom block; the harness prints the refresh kind's yield trajectory and
  choice share (the REFUTES/SUSTAINS criterion is read off the run, pre-registered in
  the harness's docstring — this is a run artifact, not a CI assertion).
- [ ] **Step 4: Run + commit** —
`uv run pytest tests/test_attention_economy.py tests/test_arithmetic_world.py -q` and a
10-round smoke of each arm; `git commit -m "Docket ⑫b: attribution pins, churn-pump arm, exam ablation harness"`

---

### Task 14: Doc amendments + record close-out + full-suite verification

Apply the paste-ready amendments (proposed in the briefs, now ruled in by the author's
full-docket authorization), close the examination record, and verify everything.

**Files:**
- Modify: `docs/THE_MEASURE_OF_KNOWLEDGE.md`, `docs/THE_KYTOS.md`,
  `docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md`, `docs/CONTRIBUTION_AND_PRIOR_ART.md`,
  `docs/superpowers/specs/2026-07-17-vault-cycle-design.md`,
  `docs/ADVERSARIAL_EXAMINATION.md`, `CLAUDE.md`, `CURRENT_PLAN.md`

- [ ] **Step 1: Panel A amendments** (quoted in `panel_A_measure_kytos.md:48-51,119-120`):
  - MEASURE §2 K1 row: append *"K1 is a design: no join between severity and the ledger
    exists in code…"* → then UPDATE it: the join now exists (Task 12) — write the
    honest current state: the formula (`Σ_hits sev − Σ_misses sev`) is built; the
    anchors' operational definition (severity = measured refutation-power) remains an
    open obligation; ordering-invariance holds under positive linear rescaling only.
  - KYTOS §5: move K1 from **Built** to **Partially evidenced** with the panel's
    sentence, amended to note the join landed 2026-07-19.
  - MEASURE §2 sufficiency concession (D1.4): *"Sufficiency is not claimed: the four
    components cover the assertoric fragment…"* — paste verbatim.
  - K3: retitle the row — ratio is now `derived/(explicit+derived)` (bounded,
    extent-invariant); `yield_per_law` named for the old number; fix the §5 pedagogy
    line ("measure a lesson by its materialization ratio") to match.
  - Poise (D7.3): KYTOS §1/§3 — replace "poise is the observable of their ratios" with
    *"poise is a trace-reading we conjecture responds to the rate ratios; the linkage
    is unmeasured"*; move the rate-linkage to KYTOS §5 **Conjectured**; note the storm
    reading landed.
- [ ] **Step 2: Panel C amendments** (quoted in `panel_C_oracle_person_model.md:25,47-49,86,100,114`)
  to the vault spec: seal-then-reveal (salted + checked), decline/silence status,
  consent-binds-the-generator clause, answers-as-fallible-labels sentence, pre-emption-
  includes-selection sentence. Update each to reflect what Tasks 8–11 BUILT (the spec
  should read as current fact, with the concession sentences kept only where the gap
  remains — e.g. differential decay still unbuilt).
- [ ] **Step 3: Panel E amendments** — read `runs/EXAMINATION_IV_BRIEFS/panel_E_concordances.md`
  and apply its paste-ready corrections verbatim: Conway's Life on infinite ℤ² (all
  three doc sites — grep `bounded plane`), the requisite-variety direction fix, the
  free-energy "≈" restoration in BOOTSTRAP.
- [ ] **Step 4: Close the examination record** in `docs/ADVERSARIAL_EXAMINATION.md`:
  after the docket list, add a dated disposition block — each item ①–⑫ marked landed
  with its commit; the A3 concession sentence (panel D item 6) explicitly superseded
  ("A3 is now guarded on the expanded closure and the split-unit raise; the Chapter-16
  routes forward the maps"); V2a.2's block updated: ①–④ discharged, composition tests
  (a)+(b) pinned in `test_live_runner.py`, (c) `M_ACTS` vocabulary remains for V2a.2
  itself.
- [ ] **Step 5: CLAUDE.md touch-ups** (minimal): `live_runner` bullet — carry is
  structural `to_dict` JSON (F2¹³ trigger unreachable, fallback deleted);
  `oracle_notes` bullet — salted seal + verified reveals + People/ filter + P2¹³
  instrument; `agon_metalearning` bullet — the storm reading.
- [ ] **Step 6: CURRENT_PLAN.md** — re-head the NEXT SESSION block: docket ①–⑫ executed
  (one line per cluster with commits); remaining author-side items: RUN 12 disposal,
  RUN 13 launch (riders now in place), V2a.2 unblocked pending its own build.
- [ ] **Step 7: Full suite + quality gate**

```bash
uv run pytest tests/ -q
uv run python tools/core_protection_system.py --report
```
Expected: **0 failed**; core locked + CLEAN. Record the verbatim tally in the commit.

- [ ] **Step 8: Commit** — `git commit -m "Examination IV docket ①–⑫ complete: docs amended, record closed, full suite green"`

---

## Self-review notes

- **Spec coverage:** ① T1 · ② T2 · ③ T3 · core close T4 · ④+⑥ T5 · ⑤ T6 · ⑦ T7 ·
  ⑧ T8 · ⑨ T9 · ⑩ T10 · ⑪ T11 · ⑫ T12–13 · docs/V2a.2-gate/verification T14.
  V2a.2 composition tests (a) carry + (b) decay land in T5; (c) `M_ACTS` is V2a.2's own.
- **Order constraint:** T1–T4 are the single core window (marker present only then).
  T5 depends on nothing in T1–T4 but runs after so the suite stays interpretable.
  T10 depends on T8 (ledger arms ride the nonce-bearing row shape).
- **Embedded ruling calls made (flag at review):** ④ = structural carry (not the
  concession); fallback → skip-and-count (house count-or-refuse), not silent deletion;
  ⑦ = repair (storm) + D7.3 doctrine retreat; ⑫ K3 = re-derive with `yield_per_law`
  kept; K1 = linear declared weights, operational anchors carried as an open
  obligation.
- **Line numbers are 2026-07-19 working-tree references** — verify each region by
  reading before editing; the briefs (`runs/EXAMINATION_IV_BRIEFS/`) are the
  authoritative counterexample record.
