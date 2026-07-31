# The re-measurement pass — retiring `net_score` as a gate statistic, and the window at 8

**Design of record, 2026-07-31.** Executes rulings 1 and 2 of the 2026-07-31 set
(`tasks/todo.md`), redrafted after the author's ruling on act-timing recorded as
[THE_KYTOS.md](../../THE_KYTOS.md) §1.3.

## 1 · What this pass does

Two ruled changes, taken together because the C suite narrates measured figures
throughout at fourteen minutes a run, so this is one re-measurement rather than two.

- **Retire `net_score` as a gate statistic.** The score rose 988 by destroying every
  true law the field carried, then a further 327 by restoring 28 of them. A
  statistic that rises in both directions of the thing under study cannot gate it.
- **`corroboration_window` 5 → 8**, with the rider ruling 2 attached: the window is
  part of the terminal unit's *rate* parameter, so it must be uniform across a
  community, and nothing currently enforces that.

## 2 · The doctrine that reshaped it

The first draft of this design proposed a new module, `src/c_score.py`, carrying a
`CostLedger` of thirteen hand-maintained act counters and a `ScoreVector` record. The
author refused it, and the refusal is the more important half of this document.

Under [THE_KYTOS.md](../../THE_KYTOS.md) §1.3 an act's effect resides in three
places — the **report** of the act inside the membrane, the **resources** outside it,
and the **shared reports** among kytē in the commens — and the act's own decision is
none of them. A private instrument built alongside the act, by an observer, to see
the act from in front of it, is the same error the doctrine names, committed one
level up in Python. The elaboration of the modelling *was itself the symptom*.

So the cost component is **read where it already resides**, and almost all of it
already exists.

## 3 · Cost, read rather than instrumented

| Residence | Where it already is | New code |
|---|---|---|
| Shared reports (commens) | `MarkBoard` — every mark carries `author`, `kind`, `round_idx`, append-only and attributed. Every channel act a unit performs is already reported there. | none — `Counter((m.author, m.kind) for m in board.marks)` |
| Report (inside the membrane) | `MembraneLedger` — bets, hits, misses, abstentions, `restaked`, `late_arrivals` | none |
| The denominator | rounds this unit actually attended — the one number that exists nowhere | **one integer**, `Unit.attended`, incremented in `Unit.step` |

`Unit.attended` is incremented **after** the step completes, per §1.3's write-after
rule, and no code path may read it within the round it counts.

**Where the reader lives: test-side, not `src/`.** The cost reading is one helper in
`tests/test_c_channels.py` beside the existing `_aggregate_ask` tally — it composes
the board `Counter`, the ledger figures and `Unit.attended` into the per-kind
acts-per-attended-round reading. It is an *observer's* reading of already-recorded
residences, so putting it in `src/` would give a unit a faculty it does not have. The
one `src/` change in this phase is the `Unit.attended` integer.

**Internal acts that leave no report stay uncounted, deliberately.** Under §1.3 an
act whose effect reaches no report has no channel by which to influence anything;
counting it privately would invent one and would install exactly the observer this
design just deleted. This is a named limit, not an oversight: it means the cost
reading sees channel work and attendance, and does not see materialization or
anticipation work.

**Sufficiency for ruling 2.** Terminal-unit invariance asks that capacity and rate be
invariant across units. *Rate* is the dataclass parameters, made uniform by §6's
guard. *Capacity* is attendance (now readable) and acts emitted (already on the
board). Two units with identical aperture and identical rate must read equal
attendance and comparable authored marks — which is what the twin control checks and
what makes VII.8's enlarge-vs-reorder gap measurable at all.

## 4 · The retirement rule

The five measured inversions were all **cross-arm** comparisons. The rule follows
their shape rather than banning arithmetic:

> **No gate may be decided by comparing hits − misses between arms.** A cross-arm
> gate is decided on the **law components** — true laws held, converses held — and
> must carry a **participation clause**: the winning arm did not win by ceasing to
> forecast (bets placed, compared). Net is *reported* beside it, never the verdict.
>
> **Within one arm**, "a held law pays" is stated on `hits` and `misses` directly,
> never on the derived scalar, and never as the only clause.
>
> **Cost is asserted only where invariance is claimed** (the twin control);
> everywhere else it is reported.

**Pinning is reporting.** An assertion of an exact measured value (`== (-1421, -106)`)
records a figure with teeth and stays. Only assertions that *decide* a gate by
comparing net across arms move. This is the same standing that
`test_c_membrane.py`'s five arithmetic pins already have.

`MembraneLedger.net_score` survives as a property, with its docstring demoted to
**observability, never a gate** — the status `restaked` and `late_arrivals` already
carry — naming the five inversions as the reason. GATE 1's whole argument requires
the number to stay readable; deleting it would make the series' own recorded
inversions unreproducible. `resolving_membrane.PredictionLedger.net_score` is a
different class and does not move.

## 5 · The gate-by-gate map

**Per-unit `.net_score` assertions, 13 outside `test_c_membrane.py`:**

| File / function | Kind | Disposition |
|---|---|---|
| `test_c_unit.py::test_held_law_beats_a_wrong_law_over_a_run` (72) | cross-arm | law clause + participation clause; net reported |
| `test_c_unit.py::test_every_miss_is_a_distinct_atom_no_bet_is_charged_twice` (448) | within-arm, incidental | → `hits > misses` |
| `test_c_unit.py::test_inducing_unit_learns_the_planted_law_and_its_score_rises` (531, 532) | cross-arm | full re-expression; **name changes** — the score rising is no longer the claim |
| `test_c_stage_gates.py::test_stage_1_gate_a_unit_learns_a_planted_law_and_its_score_rises` (141, 142) | cross-arm | full re-expression; **name changes** |
| `test_c_stage_gates.py::test_a_true_law_held_alone_makes_money_at_every_seed` (179) | within-arm | → `hits > misses`, per seed, per arm |
| `test_c_stage_gates.py::test_the_converse_law_arm_now_bets_and_loses` (237, 241, 242) | 2 within-arm, 1 cross-arm | 237/241 → `misses > hits` / `bets == 0`; 242 re-expressed |
| `test_c_field.py::test_a_wrong_law_has_a_nonzero_hit_ceiling` (268) | within-arm | → `misses > hits` |
| `test_c_channels.py::test_asking_and_answering_beats_being_mute_at_equal_run_length` (590) | cross-arm | **the important one** — this is one of the five inversions; gains both clauses |
| `test_c_channels.py::test_with_full_attention_the_ask_channel_is_inert_rather_than_harmful` (646) | within-arm | → `hits > misses` |

**Aggregate `["net"]` assertions, 15 across 7 functions — 13 are equality pins and
stay.** The two that decide:

- `test_gate_one_...` (3046) — labelled *THE GATE'S OWN CLAUSE, AND IT PASSES*.
  Demoted from verdict to report; the gate's verdict moves to the law and
  participation clauses it *already* asserts. This test is the model the others
  follow, because its docstring already argues that net cannot carry it.
- `test_gate_one_...` (3068), `four_mute < four_chal < four_live` — **kept**, and
  reframed. Its content is precisely *net rose in both directions*, so it asserts the
  inversion rather than deciding by it.

## 6 · The window, and the uniformity guard

`corroboration_window: int = 5` → `8` (`src/c_unit.py:226`), one line, and the
docstring's measured trade table stays as the evidence for the ruling.

The guard, at both community builders — `test_c_channels.py::_play_challenge` (1619)
and `::_play_ask_and_challenge` (2132), the only two places a multi-unit community is
constructed with per-unit rate overrides. Every
unit's `(corroboration_window, corroborating_witnesses, replication_window)` must
agree, or raise — the refusal style `apertures_for`'s `min_witnesses` already uses.
Under ruling 2 these *are* the rate parameter, so a community of mixed rates is not a
community of terminal units and any West-shaped reading off it is void.

A sweep that varies the window still can: it varies it for **all** units at once,
which is what a sweep should have been doing.
`test_the_silence_window_at_three_five_and_eight` sets the window explicitly for the
whole community, so its figures must not move — a free check on the guard and on the
default change both.

## 7 · Narration policy

Every touched docstring gains a **RE-MEASURED AT WINDOW 8** paragraph and **keeps its
window-5 reading beside it**, labelled with the window it was taken under. The two
readings together are the measured basis of the ruling (3 → 8 saves 49 true laws
while sparing 3 false ones); deleting the old figure would destroy the comparison the
ruling was made on. Assertions all move to the new figures; nothing stale is left
asserted.

## 8 · Phases, and the verification that separates them

A figure that moves must have exactly one cause.

| Phase | Change | Required effect on every measured figure |
|---|---|---|
| 1 | `Unit.attended`; the cost reader; the uniformity guard | **none** |
| 2 | Gates re-expressed on the rule of §4; `net_score` docstring demoted | **none** |
| 3 | `corroboration_window` 5 → 8 | the single re-measurement |

Phases 1 and 2 moving no figure is not merely a confound control. It is §1.3's
**non-interference rule under test**: an instrument that changes the act it measures
has got out in front of it. A moved figure in phase 1 or 2 is a finding, not a
nuisance, and stops the pass.

**Done means:** full C suite green (199 at close, plus whatever the guard adds); core
suite green (152); no assertion anywhere decides a gate by a cross-arm net
comparison; every narrated figure that moved carries both readings; `git grep` finds
no `net_score` comparison between arms outside the two reframed GATE 1 clauses.

## 9 · Explicitly out of scope

- **Making a report influence further thought.** §1.3's other half. Nothing reads
  `MembraneLedger` today; making a unit's own report downstream-effective *and only
  downstream* is a real change to what a kytos is, and its natural home is the
  scarcity test, where a null would mean something. Building it inside a
  re-measurement pass would confound both.
- **Weighting witnesses rather than counting them** (`src/c_unit.py:1759-1766`).
  Blocked on the credential, which is ruled and unbuilt. Deliberately not worked
  around: weighting by the challenger's private `peers` standing would make
  corroboration turn on one unit's private opinion, defeating the socially available
  objectified reality §9d grounds it in, and inventing a weight would install the
  solution.
- **The enlarge/reorder prose amendment** to the stage-4 design §11.2(b) (VII.8).
  Rides with the credential build.
- **The PDF book format**, which fails on a pre-existing YAML-alias parse error
  present on `HEAD` before this work (HTML renders 48/48 clean). Flagged, not fixed.

## 10 · Open, and the author's

Grades for the five West rows the corrections touched; the chapter title of
`FROM_THERMODYNAMICS_TO_SEMIOSIS.md`.
