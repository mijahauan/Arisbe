# Closing the AlternativeSet Arc: Tasks 5–6, the Temperament Knob, the Follow-On Batch

**Status:** Pre-registered design spec (assistant-drafted under the author's
"close the arc" directive, 2026-07-26; design calls flagged §0 for author veto)
**Date:** 2026-07-26
**Extends:** `2026-07-26-alternative-index-over-ink-design.md` (governing;
nothing here amends it). The inquiry-principle doc remains governing and
unamended.

**Frozen inputs:** the index-over-ink spec + its shipped build (`main` @
`52c31d0`); the author's self-damping ruling of 2026-07-26 (**reserve as a
studiable temperament knob**, commit to neither arm); the follow-on batch as
enumerated in CURRENT_PLAN; the retired Task 5/6 pseudocode of
`2026-07-25-item-4-phase-2-tasks-4-6-revised.md` as *intent* only (its
engineering shape died in Examination V).

---

## §0 Design calls taken in this spec (flagged for the author)

| # | Call | Ruling here |
|---|------|-------------|
| D-1 | What is a Task-5/6 record? | **The interrogative pair, re-emerged.** Every record of every kind holds the same `{atom, denial}` alternatives — exhaustive and exclusive by construction, so the §7(e) witness declaration is discharged *identically* for `hypothetical` and `modal`. The kinds differ in **emergence ink** (which survey surfaced them), never in shape. This is the strongest reading of "replicate the proven wire": trace, settle, law, consumer all run verbatim. |
| D-2 | Which thin spots become records? | Only **zero-grounded** ones: relations in the vocabulary with no grounded instance, and ungrounded law bodies. A 1-instance thin relation's `(r *x)` already *holds* (the instance witnesses the existential) — a record would be born settled, a vacuous question. 1-instance relations and lonely individuals stay the docket's beat (it already harvests them); the survey **names them in params** (honest full brief) without minting records. |
| D-3 | Which branch points become records? | Ground atoms **contested across futures**: present in ≥1 reachable leaf's `m_view`, absent in ≥1, and *not currently held* at the survey state (else born settled). Budget-capped, refusals counted. |
| D-4 | Where does materiality come from for the new kinds? | The **same dry-run trace** (`trace_unknown` on the current M). A thin-spot or branch-point question's consequences are exactly as traceable as a peel unknown's; nothing modal-specific is invented. |
| D-5 | The escape-vs-refuse divergence | **REVISED at plan time (parser evidence):** the EGIF parser retains backslashes (verified live: `\"` in source stays `\"` in the parsed label — no unescaping), so a raw-quote label can never round-trip to itself; internal escaping would mint records whose labels diverge from their emergence ink (an AS1 mismatch by construction). The **refuse arm is the doctrine** (count-or-refuse; refuse-never-mangle): resolve the divergence by documentation — `atom_and_denial_egif`'s docstring states the parser-form convention (labels in the parser's escaped form round-trip; raw embedded quotes are refused and counted, the designed membrane path) — plus a batch-level test pinning that a refused unknown is *counted* in `TraceBatch.unrepresentable`. No code change; the original AC2 wording ("round-trips escaped") is discharged by the escaped-form case. |
| D-6 | New-kind construction invariant | `hypothetical`/`modal` records **require `emerged_from`** at construction — their whole legitimacy is the survey ink. (`interrogative` keeps `Optional` for the honest-untraced path.) |

---

## §1 The temperament knob (the author's ruling, operationalized)

`wants_from_alternatives` splits its single hardcoded `×0.5` into two named
factors:

```python
def wants_from_alternatives(register, *, round_idx=0, cost=1.0,
                            s_register=None, source_record=None,
                            chain=None,
                            self_damping=0.5, cross_damping=0.5) -> List[Want]
```

- A standing `distinction:{relation}` in the S-register damps severity by
  **`self_damping`** when the record's **own trace admitted it** (resolved by
  dereferencing `record.traced_by` → the trace step's `s_admitted` params —
  the consumer re-reads licensed ink; the record holds nothing), else by
  **`cross_damping`** (the don't-pay-twice case).
- `chain=None` (or an unresolvable `traced_by`) cannot distinguish → applies
  `cross_damping` on bare membership — **today's behavior**.
- **Defaults `0.5 / 0.5` are byte-identical to the shipped wiring** whether or
  not a chain is passed. `self_damping=1.0` = settle-first temperament;
  `0.5` = explore-leaning. The dial is a pre-registerable experiment
  (sweep `self_damping`, measure settlement latency vs discovery yield);
  this spec builds the knob, not the study.

## §2 The two surveys (new module `src/alternative_survey.py`)

Both are **PEEL-twins**: identity transforms via `pc.apply_derived`, earned
at record time (the scan actually runs), params carrying the whole result,
recomputable forever, `m_view`-neutral (the existing gate tripwire
auto-contains them). Both park their surfaced questions under the params key
**`unknown_atoms`** in `peel_step`'s exact shape (`[[rel, ["*"|label, …]], …]`)
so AS1 keeps one code path.

**Thin spots** — `SURVEY_THIN_SPOTS` / act `"thin_spots_surveyed"`:
`survey_thin_spots(egi)` (pure) reads M through `m_view` exactly as
`attention_brief` does — vocabulary, grounded relations, standing scrolls —
and surfaces per D-2: zero-grounded vocabulary relations as `(r, (None,))`
(arity 1: the existential question "is r grounded at all?") and ungrounded law
bodies as `(body, (None,))`, dedup'd, sorted. Params also carry
`thin_but_grounded` and `lonely_individuals` (named, recordless — the
docket's beat, reachable by projected key). `thin_spot_step(pc, *, budget=8)`
records it; over-budget surfacings land in `refused` (counted in params).

**Branch points** — `SURVEY_BRANCHES` / act `"branches_surveyed"`:
`survey_branches(chain, upto=None)` (pure) enumerates fork states by the
`Counter(step.from_state_id) > 1` idiom over the steps before `upto`, collects
each reachable leaf's sheet ground atoms (`m_view`), and surfaces per D-3 the
contested-across-futures atoms not held at the survey state. Params carry the
fork state ids and per-atom witness/counterexample leaf ids (the ◇-not-□
evidence, `modal_query`'s reading recorded as ink). `branch_survey_step(pc,
*, budget=8)` records it against `pc.to_chain()`'s steps **preceding the new
step** (so recompute is well-defined: re-survey the prefix).

**Records from surveys:** `records_from_survey_step(step, *, kind,
round_idx)` builds `AlternativeRecord`s (atom/denial via
`atom_and_denial_egif`, `emerged_from=step.step_id`) — the survey twin of
`record_from_trace_step`. Thin-spot surveys mint `kind="hypothetical"`,
branch surveys `kind="modal"`.

## §3 Law and register extensions (`alternative_index.py`)

- `KINDS_BUILT = ("interrogative", "hypothetical", "modal")`; D-6's
  construction invariant; the witness declaration documented on the class
  (one pair, three emergences).
- **AS1 tightened** (follow-on item): `_EMERGENCE_ACTS = ("peel",
  "thin_spots_surveyed", "branches_surveyed")`. An `emerged_from` step whose
  act is *not* one of these is now a **violation** (the silent pass dies);
  membership of `[relation, star_labels]` in the step's `unknown_atoms` is
  checked uniformly for all three.
- **AS3 tightened** (follow-on item): *introduced-by-step* — the selection
  must hold at `to_state_id` **and not at `from_state_id`** (atom or denial
  arm respectively). `settle_from_chain` aligns: the earliest acknowledged
  step that *introduces* a settling answer is cited (an already-standing
  answer no longer picks up a bystander step's citation).
- `rebuild_from_chain` reads the two survey acts (kind by act) beside `peel`,
  so registers fold from chains that used any producer.
- Docstring caveat (follow-on item): receptions are **snapshot-only** —
  membrane arrivals were never chain steps; `rebuild_from_chain` cannot
  recover them; LRU displacement + rebuild loses them. Stated, not silently
  implied otherwise.

## §4 Cleanups (`alternative_trace.py`)

1. `diverging` drops the provably-redundant `rels_t ^ rels_f` term
   (`rels_t ^ rels_f ⊆ {r for r,_ in extra_t ^ extra_f}`; equivalence
   pinned by test so AS2/gate recompute is undisturbed).
2. K3 honesty check **hoists the reports** from the trace's own
   `materialize_egi` calls instead of materializing a third time; numbers
   pinned identical to `materialization_ratio`'s on fixtures.
3. `BoundedRegister(0)` admits **nothing** (refuse-and-count: `displaced`
   increments, term returned as displaced); capacities ≥1 byte-identical.
4. D-5 as revised: the parser-form convention documented on
   `atom_and_denial_egif`; the refused-is-counted path pinned at the
   `trace_batch` level. No escaping code change.

## §5 Gate and corpus (`test_corpus_polarity_discipline.py` + a builder)

- **Two new recompute obligations** (the PEEL/TRACE pattern): a recorded
  `thin_spots_surveyed` step re-surveys `chain.states[from_state_id]` and
  must reproduce its `unknown_atoms`/`thin_but_grounded`/`lonely_individuals`;
  a recorded `branches_surveyed` step re-surveys the step prefix and must
  reproduce its `unknown_atoms` + fork ids. One falsifier each (doctored
  params flagged).
- **`_ACK_ACTS` drift tripwire** (follow-on item): the gate asserts
  `set(alternative_index._ACK_ACTS) ⊆ set(M_ACTS)`.
- **The trace-bearing corpus exemplar** (follow-on item):
  `tools/build_alternative_traces_exemplar.py` → UoD **`swan_alternatives`**
  (category `domain_model`): the loop fixture's swan M walked through
  peel → thin-spot survey → trace_batch → a branch (two `branch=`-labelled
  lines off one state, the `build_modal_branching` idiom) → branch survey →
  an `admit_step` resolution; saved via `save_uod_with_chain` **and**
  `save_alternative_register(..., chain=chain)`. De-vacuates the trace- and
  survey-recompute obligations (they run non-skipped on ≥1 corpus UoD) and
  discharges AC7's letter on real saved ink.

## §6 Pre-registered acceptance criteria (AC11–AC20)

- **AC11 (knob):** defaults byte-identical on the shipped AC4/AC5 fixtures
  (chain passed or not); `self_damping=1.0` + chain → a material
  self-admitted record reads 8.0 while a second record on the same relation
  (cross case) still damps by `cross_damping`.
- **AC12 (thin-spot survey):** on a fixture M with a zero-grounded relation,
  an ungrounded law, a 1-instance relation, and a lonely individual: exactly
  the zero-grounded + law-body questions are surfaced; the others are named
  recordless; the step recomputes.
- **AC13 (branch survey):** on a forked chain, exactly the
  contested-across-futures, not-currently-held atoms are surfaced with
  witness/counterexample leaves; the step recomputes.
- **AC14 (kinds law):** new-kind construction without `emerged_from` refused;
  AS1 flags a non-emergence `emerged_from` (falsifier bites) and passes all
  three lawful emergences.
- **AC15 (AS3 tightened):** a record citing a bystander step (answer already
  standing at its `from_state`) is refused; `settle_from_chain` on the loop
  fixture cites the introducing step and AC6 still holds.
- **AC16 (the two new wires):** end-to-end on fixtures — survey → records →
  trace → economy asks material-first → resolution via `admit_step` →
  `settle_from_chain` resolves citing that step → `attest_alternative_record`
  passes; for both `hypothetical` and `modal`.
- **AC17 (exemplar):** `swan_alternatives` saved; the gate's trace-recompute
  and both survey-recompute obligations execute **non-skipped** on it; the
  register sidecar attests at the boundary.
- **AC18 (tripwire):** the `_ACK_ACTS ⊆ M_ACTS` assertion stands in the gate.
- **AC19 (cleanups):** diverging-equivalence pinned; K3 numbers identical
  with no third materialization; `BoundedRegister(0)` admits nothing,
  counted; a raw embedded-quote unknown is refused **and counted** in
  `TraceBatch.unrepresentable` (D-5 as revised — the parser-form convention
  documented).
- **AC20 (suite):** full suite green; AC1–AC10 untouched except the one
  amended escape test (named in the plan, D-5).

All deterministic and offline. **The arc closes when AC11–AC20 are green.**

## §7 Out of scope

The self-damping *study* (the knob ships, the sweep is a future
pre-registered run); the source-keyed track-record registry; ascent policy;
the commens-rung threads; non-depth pathology families; any docket code
change (the wire remains the projected key).
