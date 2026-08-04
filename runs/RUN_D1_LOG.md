# D-1 — the priced world, read against its pre-registered priors (run log)

> **Spec:** [the D-series design](../docs/superpowers/specs/2026-08-02-d-series-building-the-stake-design.md)
> — priors `P-D1`…`P-D7` in its §7, **committed before anything was built**; the cheat
> register in §8, including item 6's escalation rule; the four arms in §6.
> **Build:** `src/d_world.py` + driver `tools/run_d1.py`, tests `tests/test_d_world.py`
> (59 passing). `src/c_unit.py` and `src/c_marks.py` are untouched by the series;
> `src/c_field.py` gained only the additive `wide_spec` beside an unmoved `default_spec`,
> so no C-series figure moves.
> **Run:** four arms × eight seeds (1, 2, 3, 4, 5, 7, 42, 99) × 60 rounds at each of three
> field widths — **32 communities per width, 96 in all**, plus 24 calibration runs.
> Deterministic: `play` twice on one seed agrees (`test_two_runs_of_one_arm_agree`), and the
> sweep is byte-identical fanned out across workers or run sequentially
> (`analyze.py --jobs`, verified by `cmp`).
> Sweep of record `runs/d1/analyze_d{8,12,16}.txt` → `runs/d1/analysis_d{8,12,16}.json`,
> read by `runs/d1/summarize.py`; the per-channel counts are `runs/d1/channel_probe_d8.txt`.
>
> **EVERY FIGURE BELOW IS FROM THE RE-RUN OF 2026-08-04**, after the round order was restored
> (fix round 5). The earlier sweep measured a world with **a dead answer channel** and its
> artefacts have been deleted rather than left beside these — see *the defects the build found
> by running*, items 5 and 6. Nothing from before the fix is quoted anywhere in this log.

## The result, in one paragraph

**The stake bites and the population does not settle.** Mortality is a consequence of the
subtraction with nothing installed to produce it — no `die()`, no TTL, no lifespan anywhere
in `src/` — and it arrives on schedule: the first death lands in **round 5 or 6 of all eight
seeds** in arm A1, at every field width, and 49–515 units die per 60-round run in a world
where the control (`A0`, the meter read and not subtracted) buries nobody. That is `P-D1`,
and it is the series' point. But the **escalation rule fired at every field width tried** —
8, 12 and 16 domains, seat ceilings 28, 66 and 120 — because in the full-channel priced arm
the population runs to the seat cap in **8/8 seeds at all three widths**. **`P-D7` is refuted
by its own stated failure condition**: *"fails if size runs to the ceiling (the cap is
deciding, not the economy)."* It does — and the ablated arms, which do sit below the cap at
120 seats, turn out not to be settled either but to **oscillate**, which is a third outcome
the prior never named. Widening the field to 120 seats separated the arms without freeing A1:
**A1 holds 120.00 of 120 while the ablated arms cycle down to 96.00 (`A2a`) and 88.12
(`A2b`)** — the channel is worth roughly **36% more standing population**, which is the first
thing in this project's history that *ablating the putative sign* has actually moved. `P-D3`
reads **refuted as literally stated and confirmed in substance**: the ablation does not
shorten a *unit's* life (it lengthens it, by 27–66%), but it plainly costs the *community*
its number. `P-D2` holds on lineage and fails to demonstrate its selection clause, because
the unpriced control reproduces the same ordering with zero mortality. `P-D4` is **not
reached, and for a reason worth more than the prior**: the priced, breeding population
finally gives typification a real choice to make — 26.6% of 25 663 preference occasions have
two or more candidates, against the C-series' *none* — and `whom_to_ask` still has no
consumer, because a question is a broadcast.

## The measured world

Every number in this table is **measured, not chosen** (spec §4). `E1 = 1` is the numéraire
and the only free number. Both prices are re-measured at each field width, because a price
measured in one world and applied in another would be a choice wearing a measurement's
clothes (`test_calibration_is_re_measured_at_each_field_width`).

| field | seats = C(k,2) | `N₀` (three witnesses / domain) | measured τ | measured `E0` | birth threshold 2·`E0` |
|---|---|---|---|---|---|
| **8 domains** (the spec's reference configuration) | **28** | **18** | **0.000397** | **0.061717** | 0.123434 |
| 12 domains | 66 | 30 | 0.000247 | 0.038311 | 0.076621 |
| 16 domains | 120 | 42 | 0.000178 | 0.027571 | 0.055141 |

`τ` is the flat price per unit of demand at which the baseline (arm-0) community breaks even
over its own run — total charge equals total income — summed across all eight seeds so no
single seed sets it. `E0` is the median over units of a unit's own cumulative charge through
`t*`, the **median round of a unit's first hit**. A founder is endowed at exactly `E0` and
must double it before it may breed. **Restoring the answer channel moved both prices** (at 8
domains `E0` fell 0.0768 → 0.0617, a fifth, because a community that can answer holds and
earns differently), which is why nothing measured before the fix may be quoted beside these.

## The arms

| | |
|---|---|
| **A0** | charge computed and reported, **not subtracted** — the control, and the calibration source |
| **A1** | charge subtracted |
| **A2a** | subtracted, mark channel occluded entirely (cost *and* benefit removed) |
| **A2b** | subtracted, acts still minted and charged, and **most of what peers say never reaches** — the honest ablation |

`A2a` is reported beside `A2b` to keep the *mute-and-cheaper* confound visible: a unit with
the channel off mints nothing and could outlive its peers by being silent rather than by
being right.

**`A2b` is not total occlusion, and the earlier description of it as "peers receive nothing"
overstated the arm.** A2b writes to the shared `mint_board` and reads a permanently empty
`void_board`, so what is genuinely cut off is **uptake**: measured over one 60-round run,
`adopt` is never called at all, `answer` mints 0 and `dispose_challenges` resolves 0
(`runs/d1/channel_probe_d8.txt`). But **`Unit.challenge` scans the shared board** for laws
published by other units, so an A2b unit does see its peers' law marks and mints **148
challenge marks** a run in response to them. Peers therefore reach an A2b unit as *stimulus
for what it mints and pays* while reaching it not at all as *content it could adopt*. The
ablation is of the adoptive channel; the charge, and part of what triggers it, still travel.

### 8 domains — 28 seats, `N₀` = 18

| arm | seed | survivors | born | died | acts minted | total charge | peak pop. | first death |
|---|---|---|---|---|---|---|---|---|
| A0 | 1 | 18 | 0 | 0 | 3981 | 50.290 | 18 | — |
| A0 | 2 | 18 | 0 | 0 | 4073 | 52.569 | 18 | — |
| A0 | 3 | 18 | 0 | 0 | 3947 | 52.693 | 18 | — |
| A0 | 4 | 18 | 0 | 0 | 3845 | 49.318 | 18 | — |
| A0 | 5 | 18 | 0 | 0 | 4131 | 52.701 | 18 | — |
| A0 | 7 | 18 | 0 | 0 | 4105 | 51.939 | 18 | — |
| A0 | 42 | 18 | 0 | 0 | 4052 | 53.174 | 18 | — |
| A0 | 99 | 18 | 0 | 0 | 3884 | 51.316 | 18 | — |
| A1 | 1 | 28 | 73 | 63 | 8775 | 43.850 | 28 | 6 |
| A1 | 2 | 28 | 59 | 49 | 8722 | 46.362 | 28 | 6 |
| A1 | 3 | 28 | 73 | 63 | 8752 | 46.064 | 28 | 6 |
| A1 | 4 | 28 | 60 | 50 | 8114 | 47.817 | 28 | 6 |
| A1 | 5 | 28 | 60 | 50 | 8672 | 47.122 | 28 | 5 |
| A1 | 7 | 28 | 65 | 55 | 8592 | 45.625 | 28 | 5 |
| A1 | 42 | 28 | 67 | 57 | 8728 | 46.763 | 28 | 5 |
| A1 | 99 | 28 | 61 | 51 | 8354 | 46.193 | 28 | 5 |
| A2a | 1 | 28 | 43 | 33 | 0 | 47.833 | 28 | 18 |
| A2a | 2 | 28 | 45 | 35 | 0 | 48.779 | 28 | 15 |
| A2a | 3 | 28 | 45 | 35 | 0 | 47.852 | 28 | 16 |
| A2a | 4 | 28 | 45 | 35 | 0 | 46.965 | 28 | 7 |
| A2a | 5 | 28 | 42 | 32 | 0 | 50.267 | 28 | 29 |
| A2a | 7 | 28 | 42 | 32 | 0 | 48.523 | 28 | 13 |
| A2a | 42 | 28 | 47 | 37 | 0 | 47.559 | 28 | 7 |
| A2a | 99 | 28 | 44 | 34 | 0 | 48.649 | 28 | 7 |
| A2b | 1 | 28 | 44 | 34 | 8086 | 50.182 | 28 | 15 |
| A2b | 2 | 28 | 48 | 38 | 8422 | 49.540 | 28 | 14 |
| A2b | 3 | 28 | 50 | 40 | 8462 | 49.015 | 28 | 15 |
| A2b | 4 | 28 | 47 | 37 | 8039 | 50.243 | 28 | 6 |
| A2b | 5 | 28 | 45 | 35 | 8265 | 51.948 | 28 | 29 |
| A2b | 7 | 28 | 45 | 35 | 8266 | 50.610 | 28 | 12 |
| A2b | 42 | 28 | 50 | 40 | 8571 | 48.766 | 28 | 6 |
| A2b | 99 | 28 | 48 | 38 | 8038 | 49.046 | 28 | 6 |

**Every priced arm at every seed ends at exactly 28 — 100% of the ceiling.** Nothing about
the population can be read here; the cap decided it.

### 12 domains — 66 seats, `N₀` = 30

| arm | seed | survivors | born | died | acts minted | total charge | peak pop. | first death |
|---|---|---|---|---|---|---|---|---|
| A0 | 1 | 30 | 0 | 0 | 6671 | 52.774 | 30 | — |
| A0 | 2 | 30 | 0 | 0 | 6693 | 54.878 | 30 | — |
| A0 | 3 | 30 | 0 | 0 | 6577 | 54.465 | 30 | — |
| A0 | 4 | 30 | 0 | 0 | 6469 | 51.548 | 30 | — |
| A0 | 5 | 30 | 0 | 0 | 6879 | 54.277 | 30 | — |
| A0 | 7 | 30 | 0 | 0 | 6716 | 53.541 | 30 | — |
| A0 | 42 | 30 | 0 | 0 | 6689 | 54.973 | 30 | — |
| A0 | 99 | 30 | 0 | 0 | 6559 | 53.544 | 30 | — |
| A1 | 1 | 66 | 233 | 197 | 21635 | 50.359 | 66 | 6 |
| A1 | 2 | 66 | 235 | 199 | 21871 | 49.169 | 66 | 5 |
| A1 | 3 | 66 | 242 | 206 | 21589 | 50.784 | 66 | 6 |
| A1 | 4 | 66 | 269 | 233 | 21711 | 46.503 | 66 | 5 |
| A1 | 5 | 66 | 240 | 204 | 21703 | 49.381 | 66 | 5 |
| A1 | 7 | 66 | 259 | 223 | 21884 | 49.016 | 66 | 5 |
| A1 | 42 | 66 | 247 | 211 | 22187 | 49.504 | 66 | 5 |
| A1 | 99 | 66 | 242 | 206 | 21455 | 48.087 | 66 | 5 |
| A2a | 1 | 66 | 154 | 118 | 0 | 56.085 | 66 | 7 |
| A2a | 2 | 66 | 168 | 132 | 0 | 54.899 | 66 | 7 |
| A2a | 3 | 66 | 159 | 123 | 0 | 55.806 | 66 | 13 |
| A2a | 4 | 66 | 164 | 128 | 0 | 56.228 | 66 | 7 |
| A2a | 5 | 66 | 148 | 112 | 0 | 56.522 | 66 | 20 |
| A2a | 7 | 66 | 163 | 127 | 0 | 56.004 | 66 | 7 |
| A2a | 42 | 66 | 167 | 131 | 0 | 55.111 | 66 | 7 |
| A2a | 99 | 66 | 160 | 124 | 0 | 55.260 | 66 | 7 |
| A2b | 1 | 66 | 165 | 129 | 20416 | 58.982 | 66 | 6 |
| A2b | 2 | 66 | 185 | 149 | 20828 | 57.680 | 66 | 6 |
| A2b | 3 | 66 | 172 | 136 | 20196 | 58.560 | 66 | 13 |
| A2b | 4 | 66 | 180 | 144 | 20463 | 57.850 | 66 | 6 |
| A2b | 5 | 66 | 154 | 118 | 18869 | 58.383 | 66 | 20 |
| A2b | 7 | 66 | 173 | 137 | 20553 | 58.062 | 66 | 6 |
| A2b | 42 | 66 | 179 | 143 | 20865 | 57.697 | 66 | 6 |
| A2b | 99 | 66 | 175 | 139 | 20277 | 57.934 | 66 | 6 |

**Every arm ends at 66/66 in every seed.** The ablated arms dip below the cap during the run
(A2a trough 63.4, A2b 62.2) and are back on it by round 60 — the first faint sign of the
ablation, and no more.

### 16 domains — 120 seats, `N₀` = 42

| arm | seed | survivors | born | died | acts minted | total charge | peak pop. | first death |
|---|---|---|---|---|---|---|---|---|
| A0 | 1 | 42 | 0 | 0 | 9385 | 53.487 | 42 | — |
| A0 | 2 | 42 | 0 | 0 | 9330 | 55.045 | 42 | — |
| A0 | 3 | 42 | 0 | 0 | 9191 | 54.498 | 42 | — |
| A0 | 4 | 42 | 0 | 0 | 9092 | 52.109 | 42 | — |
| A0 | 5 | 42 | 0 | 0 | 9672 | 55.268 | 42 | — |
| A0 | 7 | 42 | 0 | 0 | 9433 | 54.076 | 42 | — |
| A0 | 42 | 42 | 0 | 0 | 9394 | 55.350 | 42 | — |
| A0 | 99 | 42 | 0 | 0 | 9234 | 54.168 | 42 | — |
| A1 | 1 | 120 | 552 | 474 | 40027 | 52.695 | 120 | 6 |
| A1 | 2 | 120 | 593 | 515 | 40568 | 51.754 | 120 | 5 |
| A1 | 3 | 120 | 548 | 470 | 39764 | 51.299 | 120 | 5 |
| A1 | 4 | 120 | 581 | 503 | 40398 | 51.253 | 120 | 5 |
| A1 | 5 | 120 | 531 | 453 | 39369 | 54.453 | 120 | 5 |
| A1 | 7 | 120 | 563 | 485 | 39767 | 52.996 | 120 | 5 |
| A1 | 42 | 120 | 578 | 500 | 40815 | 53.724 | 120 | 5 |
| A1 | 99 | 120 | 555 | 477 | 39639 | 53.057 | 120 | 5 |
| A2a | 1 | 90 | 288 | 240 | 0 | 59.534 | 120 | 7 |
| A2a | 2 | 101 | 328 | 269 | 0 | 60.032 | 120 | 7 |
| A2a | 3 | 98 | 293 | 237 | 0 | 59.701 | 120 | 14 |
| A2a | 4 | 102 | 316 | 256 | 0 | 59.959 | 120 | 7 |
| A2a | 5 | 92 | 258 | 208 | 0 | 59.853 | 120 | 14 |
| A2a | 7 | 100 | 296 | 238 | 0 | 59.925 | 120 | 7 |
| A2a | 42 | 91 | 295 | 246 | 0 | 60.106 | 120 | 7 |
| A2a | 99 | 94 | 299 | 247 | 0 | 59.899 | 120 | 7 |
| A2b | 1 | 88 | 273 | 227 | 30685 | 60.168 | 120 | 6 |
| A2b | 2 | 87 | 307 | 262 | 32540 | 60.321 | 120 | 6 |
| A2b | 3 | 92 | 275 | 225 | 30724 | 59.888 | 120 | 13 |
| A2b | 4 | 88 | 292 | 246 | 31354 | 60.471 | 120 | 6 |
| A2b | 5 | 88 | 259 | 213 | 29673 | 60.547 | 120 | 12 |
| A2b | 7 | 90 | 281 | 233 | 30597 | 59.709 | 120 | 6 |
| A2b | 42 | 77 | 266 | 231 | 31357 | 60.404 | 120 | 6 |
| A2b | 99 | 95 | 290 | 237 | 30753 | 59.595 | 120 | 6 |

**The arms separate.** A1 mean 120.00 of 120; A2a 96.00; A2b 88.12. A1's peak touches the cap
in every seed, and so does every ablated seed's peak — they reach it and fall back.

### The arms in summary

| field | arm | survivors (mean) | % of ceiling | `N_eq / N₀` | born | died | acts | charge | mean unit life | trough (r20–59) |
|---|---|---|---|---|---|---|---|---|---|---|
| 8 | A0 | 18.00 | 64.3 | 1.000 | 0 | 0 | 4 002 | 51.75 | 60.00 | 18.0 |
| 8 | A1 | 28.00 | **100.0** | 1.556 | 64.8 | 54.8 | 8 589 | 46.22 | 19.86 | 28.0 |
| 8 | A2a | 28.00 | **100.0** | 1.556 | 44.1 | 34.1 | 0 | 48.30 | 26.39 | 28.0 |
| 8 | A2b | 28.00 | **100.0** | 1.556 | 47.1 | 37.1 | 8 269 | 49.92 | 25.21 | 28.0 |
| 12 | A0 | 30.00 | 45.5 | 1.000 | 0 | 0 | 6 657 | 53.75 | 60.00 | 30.0 |
| 12 | A1 | 66.00 | **100.0** | 2.200 | 245.9 | 209.9 | 21 754 | 49.10 | 13.53 | 66.0 |
| 12 | A2a | 66.00 | **100.0** | 2.200 | 160.4 | 124.4 | 0 | 55.74 | 19.63 | 63.4 |
| 12 | A2b | 66.00 | **100.0** | 2.200 | 172.9 | 136.9 | 20 308 | 58.14 | 18.34 | 62.2 |
| 16 | A0 | 42.00 | 35.0 | 1.000 | 0 | 0 | 9 341 | 54.25 | 60.00 | 42.0 |
| 16 | A1 | 120.00 | **100.0** | **2.857** | 562.6 | 484.6 | 40 043 | 52.65 | 10.81 | 107.8 |
| 16 | A2a | 96.00 | **80.0** | 2.286 | 296.6 | 242.6 | 0 | 59.88 | 17.96 | 83.0 |
| 16 | A2b | 88.12 | 73.4 | **2.098** | 280.4 | 234.2 | 30 960 | 60.14 | 17.37 | 71.6 |

## The escalation check (spec §8 item 6)

> *"The escalation rule is stated in advance: if a measured equilibrium reaches 80% of the
> ceiling in any arm, the field grows and every figure is re-measured — a result taken at a
> binding ceiling is not reported as an equilibrium."*

**It fired at every field width tried, and it is still firing.**

| field | ceiling | 80% bar | highest population observed | settled level, A1 | A1 seeds ending at the cap | verdict |
|---|---|---|---|---|---|---|
| 8 domains | 28 | 22.4 | **28** (every priced arm, every seed) | 28.00 = 100% | 8/8 | **fires** |
| 12 domains | 66 | 52.8 | **66** (every priced arm, every seed) | 66.00 = 100% | 8/8 | **fires** |
| 16 domains | 120 | 96.0 | **120** (every priced arm, every seed) | 120.00 = 100% | 8/8 | **fires** |

It fires on the ablated arms too at 16 domains: A2a settles at **96.00, which is exactly the
80.0% bar**, and even A2b's 73.4% peaks at 120 in every seed.

The diagnosis survives widening: break-even is calibrated on the run's **total** demand, but
demand grows as models grow, so the early rounds collect a small fraction of an income that
arrives in full every round. The community banks the surplus, crosses `2·E0` and breeds into
whatever cap is available. Widening the field raises the cap and lowers `τ` (0.000397 →
0.000247 → 0.000178 across the three widths, since the same income now clears against more
demand) — so the world is *re-priced cheaper* exactly as fast as it is given more room, and
the full-channel arm reaches the new cap too.

**The finding, stated plainly: the calibrated world has no equilibrium below its seat cap at
any field size tried (8, 12, 16 domains), and `P-D7` fails.** No price was tuned to
manufacture one; the calibration is measured and stays measured.

**What widening did buy** is the arm separation the 8-domain field could not show at all.
At 28 seats every arm reads 28 and the ablation is invisible. At 120 the ablated arms sit
20–27% below the full-channel arm. So the escalation rule earned its keep even though it
never cleared: it converted an unreadable measurement into a readable one.

## The priors

### `P-D1` · mortality is a consequence — **HELD**

> *At subtracted charge, at least one reserve reaches zero within 60 rounds in a majority of
> the eight seeds, with no `die()`, TTL or lifespan anywhere in `src/`. Fails if nobody ever
> dies, or if everybody dies in round one.*

**Held in 8 of 8 seeds, in all three priced arms, at all three field widths.** In arm A1 the
**first death lands in round 5 or 6 in every one of the eight seeds at every width**, and the
arm buries 49–63 units per run at 8 domains, 197–233 at 12, and 453–515 at 16. Nobody dies in
round 0 or round 1, and **no community went extinct in any of the 96 runs** — so neither
failure condition is met. The control `A0`, which computes the identical charge and does not
subtract it, records **zero deaths at every seed and every width**, which is what makes the
reading causal rather than incidental.

Nothing produces the death but running out. `tests/test_d_world.py::test_no_die_no_ttl_no_lifespan_in_the_d_world`
walks `d_world.py`'s AST for identifiers that install mortality and finds none; that guard was
**broken until fix round 5** and is now verified by injection (see defect 7 below).
`test_the_unit_never_gains_a_reserve` pins that `Unit` stores no balance it could die of.

### `P-D2` · laws have lineages, and survival tracks mediation — **HELD on lineage; the selection clause NOT REACHED**

> *Planted true laws should show longer lineages and more holders than converses and
> unplanted regularities. Fails if lineage length is uncorrelated with a law's truth.*

Lineage measured as **holder-rounds** (summed over every round and every living unit holding
the content) and **spread** (distinct units that ever held it), means over the eight seeds:

| field | arm | planted: holder-rounds / spread / laws found | converse | other (unplanted) |
|---|---|---|---|---|
| 8 | A0 (control, no deaths) | 217.5 / 4.51 / 7.62 | 0.0 / 0.00 / 0.00 | 7.1 / 0.12 / 0.25 |
| 8 | A1 | 260.6 / 15.11 / 8.00 | 0.0 / 0.00 / 0.00 | 0.8 / 0.17 / 0.38 |
| 8 | A2a | 304.9 / 12.23 / 8.00 | 0.0 / 0.00 / 0.00 | 2.1 / 0.12 / 0.25 |
| 8 | A2b | 307.5 / 12.78 / 8.00 | 0.0 / 0.00 / 0.00 | 2.0 / 0.12 / 0.25 |
| 16 | A0 (control, no deaths) | 255.0 / 5.28 / 15.12 | 0.0 / 0.00 / 0.00 | 11.2 / 1.06 / 1.00 |
| 16 | A1 | 397.9 / 54.27 / 16.00 | 0.1 / 0.12 / 0.12 | 3.7 / 0.90 / 2.25 |
| 16 | A2a | 531.3 / 31.34 / 16.00 | 1.2 / 0.12 / 0.12 | 17.0 / 1.29 / 1.62 |
| 16 | A2b | 489.5 / 29.64 / 16.00 | 0.0 / 0.00 / 0.00 | 13.3 / 0.91 / 1.38 |

At 12 domains the same shape: planted 333.9 holder-rounds (A1) against 5.2 unplanted, all
twelve planted laws found in every priced run, 1.00 unplanted and 0.00 converses per run.

**The first clause holds and holds hugely** — a planted law accumulates ~261 holder-rounds at
8 domains where a non-planted one accumulates ~1, and every one of the field's planted laws
is found in every priced run at every width. Lineage length is emphatically *not*
uncorrelated with truth.

**The second clause is not reached, and the control is what says so.** `A0` — where nothing
is ever subtracted and **not one unit dies** — shows the same ordering (217.5 planted vs 7.1
unplanted at 8 domains; 255.0 vs 11.2 at 16). An ordering that is already there when
mortality is switched off cannot be evidence that *survival* tracks mediation. What the
figures show is that **induction is accurate**, not that the world selects: the comparison
class is nearly empty (a mean of **0.38 unplanted laws and 0.00 converses per run** at 8
domains, rising only to 2.25 and 0.12 at 16), so the contrast rests on almost no
counter-population. `dispose_challenges` — which fires 642 times in one A1 run —
retracts a false law long before a holder could starve of it, which is the honest mechanism
behind the number.

The one place the priced world visibly changes a lineage is **spread**: at 16 domains a
planted law reaches **54.27** distinct units in A1 against **5.28** in A0 — but that is
**birth**, not death, doing the work. A priced world has 563 newborns per run to socialize
and the control has none. Selection would show as *false* laws dying with their holders, and
there are almost no false laws to die.

### `P-D3` · the ablation bites, measured in survival time — **REFUTED as stated; confirmed in substance on population**

> *A2b's communities die sooner than A1's — occlude the marks, prediction worsens, hitless
> rounds multiply, the stock burns faster. Fails if occluding the sign changes lifespan none.*

**The stated reading is refuted, with the sign inverted, at all three widths.**

| field | mean unit lifespan, A1 | A2a | A2b | first death, A1 | first death, A2b |
|---|---|---|---|---|---|
| 8 domains | **19.86** | 26.39 | **25.21** (+26.9%) | rounds 5–6, all 8 seeds | rounds 6–29 |
| 12 domains | **13.53** | 19.63 | **18.34** (+35.6%) | rounds 5–6, all 8 seeds | rounds 6–20 |
| 16 domains | **10.81** | 17.96 | **17.37** (+60.7%) | rounds 5–6, all 8 seeds | rounds 6–13 |

The ablated community's units live **27–61% LONGER**, not shorter, at all three widths, in
the same direction, and the gap *widens* as the field grows. And **no community died in any
arm at any width**, so the prior's actual predicate — *communities die sooner* — has **no
observations at all**. On its own terms the prior fails, and the reason it fails is
instructive: A1's shorter lifespans are a **turnover** effect, not a mortality effect. At 16
domains A1 puts **595.1 units through the world** per run against A2b's 318.0, and a newborn
inherits nothing, so the full-channel community carries a much larger population of young
poor units that pulls the mean down. Note also that the *first-death* gap, which at 8 domains
runs to 23 rounds, narrows to **one round in six of eight seeds** by 16 domains — the ablated
arm's late first death is itself a small-field artefact and should not be leaned on.

**The substance is confirmed on the number the cap finally let us read.** At 16 domains:

| arm | survivors at round 60 | vs A1 | trough, rounds 20–59 | vs A1 | acts minted | total charge |
|---|---|---|---|---|---|---|
| A1 (full channel) | **120.00** | — | **107.8** | — | 40 043 | 52.65 |
| A2a (channel off entirely) | 96.00 | **−20.0%** | 83.0 | **−23.0%** | 0 | 59.88 |
| A2b (mints and pays, uptake occluded) | **88.12** | **−26.6%** | **71.6** | **−33.6%** | 30 960 | 60.14 |

Occluding uptake costs the community **a fifth to a third of its standing population**, and
`A2b` — the honest ablation, cost held and adoption removed — is the *worst* of the three on
both readings. The **trough** column is given beside the horizon snapshot because the ablated
arms oscillate (see `P-D7`), and the trough is the more robust comparison: it does not depend
on where in the cycle round 60 happened to fall. Both orderings agree.

**The mute-and-cheaper confound does not explain it:** A2a mints zero marks and still ends
20.0% short, and A2b — which pays for every act — ends **below** A2a rather than above it, on
both the horizon and the trough. So the channel's benefit is not an artefact of A2a's
silence, and the cost of speaking does not by itself account for A2b's shortfall.

**This is the first time in this project's history that *ablate the putative sign* has moved
a number.** It required exactly what the design said it required: something had to be able to
run out.

### `P-D4` · typification becomes consequential — **NOT REACHED, and the reason outranks the prior**

> *Units whose asks go to higher-standing peers survive longer. The C-series measured this
> inert at four units — all 939 uptake decisions had exactly one peer standing behind them —
> so it needs a population where a choice exists. Fails if the preference stays inert once
> priced.*

**The prior's precondition is now met — a choice genuinely exists — and its consequence
cannot be tested, because the preference has no consumer in this world.**

Three findings, in the order they were found.

1. **The driver never closed the typify channel.** `Unit.settle_credit` is `credit`'s only
   caller, and the D-1 round order omitted it. So `Unit.peers` was **empty — zero records,
   not zero positive ones — at every unit, every seed, every arm and every width.** There was
   no inert instrument; there was no instrument. Fixed, and pinned by
   `tests/test_d_world.py::test_settling_credit_populates_peers_and_moves_no_dynamics`.

2. **Once closed, the choice the C-series lacked is there.** Sampling every living unit every
   round, arm A1 records tens of thousands of occasions on which some peer had earned a
   positive standing about a relation — and on a quarter of them there were **two or more
   candidates to prefer between:**

   | positive-standing candidates | 1 | 2 | 3 | 4 | 5 | 6 | ≥2 |
   |---|---|---|---|---|---|---|---|
   | occasions, A1 @ 8 domains | 7 127 | 1 301 | 92 | — | — | — | 1 393 / 8 520 = **16.3%** |
   | occasions, A1 @ 12 domains | 13 006 | 3 057 | 898 | 163 | 45 | 15 | 4 178 / 17 184 = **24.3%** |
   | occasions, A1 @ 16 domains | 18 844 | 4 969 | 1 515 | 272 | 63 | — | 6 819 / 25 663 = **26.6%** |

   The choice also *deepens* with the field: six candidates appear at 12 domains where eight
   never produced more than three.

   The C-series measured this degenerate — *"all 939 uptake decisions had exactly one peer
   standing behind them"* — and the prior asked for a population in which a choice exists.
   **It exists.** (`A0`'s static 18-unit community manages 45 occasions and 7 with a choice in
   the same eight runs; `A2a` and `A2b` accumulate **none at all**, since nothing is ever
   adopted through an occluded channel, so `settle_credit` has nothing to reach a verdict on.)

3. **And it changes nothing, because nothing reads it.** With the credit step in place
   **every survivor, birth, death, act and charge figure is identical**, byte for byte, to
   the run without it. `Unit.ask` publishes its question to the **whole board** (`c_unit.py`:
   *"what a question cannot do is choose whom to ask"*), and the driver's uptake step takes
   `board.answer_to(q)` — the first matching fact, whoever wrote it. `whom_to_ask` is
   computed by nobody and read by nobody.

Spec ruling 4 argued that pricing acts minted "gives `whom_to_ask` a reason to matter,
because a unit that asks the wrong peer now pays for nothing." **The measurement says
otherwise:** a unit cannot ask a wrong peer, because it cannot ask a peer at all. The price
reaches the *act of asking* and never reaches the *choice of whom*, and no price can bridge
that gap while the question is a broadcast. Making typification consequential needs a
**targeted ask** — a change to `c_unit.py`, which this series is forbidden to make and which
therefore belongs to its own sitting.

**A correlation appears at the reference configuration and INVERTS as the field grows, so it
is not evidence of anything.** Mean positive-standing records held, A1, survivors versus
units that died:

| field | survivors | died | reads as |
|---|---|---|---|
| 8 domains | **1.65** | 0.87 | survivors hold nearly twice as many |
| 12 domains | 1.62 | 1.27 | near-flat |
| 16 domains | 1.19 | **1.33** | **the dead hold more** |

Had only the reference configuration been run, that 1.65-vs-0.87 would have looked like
`P-D4` half-confirmed. It is exposure time: a unit that lives longer accumulates more records
*by living longer*, and as the field widens and mean lifespan falls from 19.86 to 10.81 the
relationship reverses. **Recorded prominently because it is exactly the kind of number a run
log that reported only its reference configuration would have reported as a result.**
The full distribution is in `runs/d1/analysis_d{8,12,16}.json` (`choice_histogram`,
`standing_survivors_mean`, `standing_dead_mean`).

### `P-D5` · an exponent is measurable, and β ≈ 1 is predicted — **NOT REACHED (nothing fitted, by design)**

> *"Still not a scaling measurement in D-1 — the realised topology is recorded for a later
> series, and nothing is fitted."*

Recorded and not fitted, as the prior itself instructs. What the run does show is **why the
question is harder than the rewrite hoped**: the total charge is nearly flat across every
arm and every field width (43.9 to 60.5 over communities ranging from 18 to 120 units),
because `τ` is *re-measured* at each configuration to make the baseline break even against a
fixed source `E1 = 1`. The calibration re-pins Σcost to the source at every width, so a
cross-width regression would fit the calibration and not the world.

Worse for any naive reading, **cumulative charge is not monotone in activity, in population
or in acts.** At 16 domains A2a mints **zero** acts, carries **96** units and pays **59.88**;
A1 mints **40 043** acts, carries **120** units and pays **52.65**. The arm with a quarter
more units and forty thousand more acts pays **less**.

Two things produce that, and neither is a scaling law. (i) **Demand is dominated by held
content, not by acts**, and held content is largest where units live longest — so the arm
that mints most is the cheapest *per unit-round*:

| demand per unit-round | 8 domains | 12 domains | 16 domains |
|---|---|---|---|
| A1 (full channel) | **72.6** | **54.2** | **46.1** |
| A2a (channel off) | 75.1 | 60.9 | 56.4 |
| A2b (mints, uptake occluded) | 77.7 | 64.0 | **61.3** |

A1's mean lifespan at 16 domains is **10.81** rounds against A2a's 17.96, so its population
is perpetually young and holds little. (ii) Separately, a community charged more per round
starves sooner and therefore accrues fewer unit-rounds to be charged over — A2b logs 5 516
unit-rounds at 16 domains against A1's 6 428. **No cost comparison between arms is asserted
anywhere in this log**, and any exponent fitted to these totals would be reading turnover and
survivorship rather than a metabolism.

### `P-D6` · sensitization is absent, and structurally so — **HELD as a finding-in-advance, not a run outcome**

> *No measure of urgency varies with reserve level, because none can (ruling 5), and the same
> gap blocks the schedule from finding an optimum (ruling 9). Recorded as a result of this
> sitting rather than of a run. The negative check is weak.*

Recorded as the prior asks: **this is a result of the design sitting, not of the run**, and
the check is weak by construction — nothing sensitization-like could have appeared. Two
standing tests give the weak check what teeth it has: `test_the_unit_never_gains_a_reserve`
(no `Unit` **field** holds a balance, so no unit behaviour can vary with a stored one — note
this checks *storage*, not *reading*, and the earlier claim that it proved a unit "cannot
read what it does not have" overstated it) and `test_the_world_holds_no_chooser` (no name in
`d_world.py` is spelled like a chooser; widened in fix round 5 to substring matching and
`ast.arg` after `act_selector(..., choose=None)`, `unit_selector` and `de_select` were all
shown to pass the previous version). Neither proves absence; both catch the cheapest way of
writing the refused thing, and **both were shown to be defeatable and were repaired in this
round rather than trusted.**

Nothing in 96 communities behaved as though a unit noticed its reserve, which is what one
would expect of a world in which the reserve is unreadable.

### `P-D7` · population finds a level, and the level is earned — **REFUTED**

> *Community size settles rather than running to the seat cap or to extinction in every seed,
> and `N_eq / N₀` is higher in A1 than in A2b. **Fails if size runs to the ceiling (the cap
> is deciding, not the economy)** or if the ratio is flat across arms.*

**Refuted by its own first failure condition, at every field size tried.** In arm A1 the
population runs to the seat cap in **8/8 seeds at 8 domains, 8/8 at 12, and 8/8 at 16**, and
the peak touches the cap in **every priced arm at every width**. The cap is deciding, not the
economy. This is not a knife-edge that a larger field would clear: widening from 28 to 66 to
120 seats moved the ceiling by 4.3× and A1 filled all three, because the calibration lowers
`τ` in proportion as the field grows.

**And the ablated arms do not settle either — they oscillate.** The 16-domain field is wide
enough to show that the number under the cap is not an equilibrium but a **boom–bust cycle**.
Population range over rounds 20–59, means across the eight seeds:

| arm @ 16 domains | trough | peak | swing | one seed's trajectory (rounds 10/20/30/40/50/55/59) |
|---|---|---|---|---|
| A1 | 107.8 | 120.0 | 12.2 | 112 · 120 · 120 · 120 · 120 · 120 · 120 |
| A2a | 83.0 | 120.0 | 37.0 | 120 · 118 · 87 · 112 · 116 · 96 · 90 |
| A2b | 71.6 | 113.7 | **42.1** | 120 · 102 · 68 · 109 · 100 · 87 · 88 |

The ablated communities breed to the cap, starve back to two-thirds of it or less, and breed
again; the swing is **42 units wide in A2b**, a third of the whole seat range. A1 climbs to
the cap and locks there (trough 107.8, and 120 for the last ten rounds in every seed). **So
no arm at any width produced a settled level:** one is pinned by the cap and the others cycle.
The mean survivor counts reported above are a snapshot at round 60 of a system still moving —
A2a's last-ten-round mean is 97.19 against 96.00 at the horizon, A2b's 88.38 against 88.12 —
and they should be read as *where the cycle happened to be*, not as an equilibrium.

**The second clause is the one that survives, and it must be reported as unconfirmed rather
than as held**, because A1's numerator is the cap's number and not the economy's:

| field | `N_eq/N₀`, A1 | `N_eq/N₀`, A2b | ratio A1 : A2b |
|---|---|---|---|
| 8 | 1.556 | 1.556 | 1.000 (both capped — flat, and uninformative) |
| 12 | 2.200 | 2.200 | 1.000 (both capped — flat, and uninformative) |
| 16 | 2.857 | 2.098 | **1.362** |

At 16 domains the ratio is **not** flat across arms and it runs in the predicted direction —
the community that predicts better holds 36% more of its number. But `P-D7` asked for a
*settled* level and got a *saturated* one, so the correct verdict is **refuted**, with the
ratio recorded as a live signal for a configuration in which A1 is not pinned.

**A stronger statement than the prior asked for.** `P-D7` offered two failure modes — running
to the cap, or extinction. The run produced a third the prior did not name: **a sustained
boom–bust cycle that reaches neither**. That is the honest characterisation of the priced
world at 120 seats, and it is more interesting than either alternative.

**What would clear it** (recorded, not done): the escalation rule as written grows the field,
and growing the field also lowers the measured `τ`. The two effects cancel. A version of the
check that could clear would have to break that coupling — hold `τ` at the 8-domain value
while widening, or calibrate against the *asymptotic* demand rather than the run's total.
Both are re-designs and neither may be done here, because the calibration is measured and
tuning it to produce an equilibrium is precisely the move §8's cheat register forbids.

## The defects the build found by running

Each was found by **running the world** or **attacking its own guards**, not by reading the
design, and each would have produced a plausible-looking table. The first four were found in
earlier fix rounds; the last three are fix round 5's, and two of them invalidated the entire
first sweep.

1. **The calibration guaranteed extinction, because `E0` covered the time to the first
   LAW when only a HIT earns.** With `t*` read off first law-induction, `N₀·E0 = E1·(t*+1)`
   *regardless of `N₀`*: the community holds exactly the learning period's buffer and no
   margin, by construction. Rounds 0–3 carry zero hitters, so the community arrives at `t*`
   broke and every priced arm went extinct within 30 rounds. Re-reading `t*` off the first
   **hit** was the whole difference between extinction and a living community. *Holding a law
   earns nothing; a hit earns.*

2. **The doubt lifecycle was inert: challenges were minted and charged, and never disposed.**
   `dispose_challenges` is the only route by which an induced law is ever suspended or
   retracted. Omitted from the round, every unit bet on every law it induced — true or false
   — for the rest of the run, while paying for the challenge marks that should have settled
   them. A table drawn from that world would have shown laws with beautiful lineages and
   would have been measuring a world where nothing could ever be given up. Restored, it fires
   **642 times in one A1 run** and is genuinely load-bearing.

3. **The tariff had no aggregate bite under `τ = E1/demand`, so two arms came out
   byte-identical.** With `τ` inversely proportional to realised demand the total collected
   is *exactly* `E1` every round whatever the community does. Measured: A2b and A2a both
   collected 1.0000 and produced **identical** survivors, births and deaths at every seed,
   though A2b minted thousands of acts A2a never touched. Speaking more lowered `τ` and cost
   the community nothing; the price was purely *positional*. `τ` became a **calibrated
   constant** — measured, never chosen, exactly as ruling 7 requires; only the
   demand-normalised form was retired.

4. **The typify channel was never closed** — `settle_credit` was absent from the round order,
   so `Unit.peers` was empty everywhere and `P-D4` had no instrument at all rather than an
   inert one. Recorded under `P-D4` above. Closing it changes no figure, which is how the
   no-consumer finding surfaced.

5. **THE ANSWER CHANNEL WAS DEAD, AND THE DOCSTRING'S FALSE CLAIM IS WHY.** The driver's
   round order was `publish → ask → challenge → answer`, while its own docstring asserted the
   order "is the C-series' own". It was not: the C-series plays **`adopt · attend · ask ·
   ANSWER · publish · challenge · corroborate · dispose · settle_credit`**. `publish` blankets
   the board with everything a unit holds and records each `(kind, content)` in
   `Unit._published`; `answer` refuses any content already there (*"a unit never says one
   thing twice whether asked or not"*). Played after `publish`, **`answer` can never mint**.
   Measured directly at 8 domains, seed 1, on this log's own calibration:

   | | calls | marks minted |
   |---|---|---|
   | `answer`, old order | 1 568 | **0** |
   | `answer`, restored order | 1 606 | **179** |

   Zero, in every arm, every seed and every field width — a whole channel of the C-series'
   division of labour silently absent from a run that reported on it. The order is restored
   and **every figure in this log is from the re-run**; the pre-fix sweep files were deleted
   rather than left beside these. *A docstring that asserts a property instead of checking it
   is how a defect this size survives four fix rounds.*

6. **`corroborate` mints exactly zero, even under the restored order, and the driver said
   otherwise.** The old docstring asserted "CORROBORATE AND DISPOSE ARE NOT OPTIONAL". Only
   one of the two is load-bearing. A corroborating reply is either the disputed head — which
   `publish` has already put in `_published`, so it is refused — or the unit's own
   counterexample through the same **once-per-law-ever** mint `challenge` uses, which the
   challenger already spent. Measured: **0 marks in every arm of every run.** The gating is
   `c_unit.py`'s and this series may not touch it, so the call is kept for order-fidelity and
   is now documented as doing nothing here rather than asserted to be essential.

7. **The mortality guard did not guard, which is the one failure `P-D1` could not survive.**
   `test_no_die_no_ttl_no_lifespan_in_the_d_world` matched banned names **exactly, without
   stripping a leading underscore** — unlike its sibling chooser guard, which had already been
   widened. Verified by injection into `d_world.py`: `def _die(...)`, `def _ttl_expired(...)`
   and `def reap_by_age(...)` **all passed clean**. A fully installed TTL sailed through the
   test on which this prior's entire credibility rests. Matching is now per identifier
   segment (a flat substring test fires on `_settle_population` — *se-**ttl**-e*), all three
   injections now fail, and the chooser guard was widened the same way: `act_selector(...,
   choose=None)`, `unit_selector` and `de_select` all passed the old version and now fail.
   `rank_acts` still passes and is left in the docstring as the honest illustration of what a
   naming trap cannot do.

## Limitations — what this run does not license

- **`A2b` is an ablation of UPTAKE, not of the whole channel.** An A2b unit still reads its
  peers' law marks off the shared board — `Unit.challenge` scans it — and mints 148 challenge
  marks a run in response. What is cut is adoption, answering and disposal (`adopt` never
  called, `answer` and `dispose_challenges` both 0). Any statement of the form "peers reach it
  not at all" is false; the correct one is "nothing peers say can enter its record".
- **`A2a` and `A2b` differ modestly, and the separation needs a long horizon.** At 16
  domains they end 96.00 and 88.12 against a ceiling of 120 — a 7.9-unit gap between them
  against a 24-unit gap to A1. Sixty rounds is enough to say the *channel* matters and not
  enough to say confidently how much of that is the sign and how much the cost of minting.
  A2b's being *below* A2a rather than above it rules out the mute-and-cheaper confound in
  sign, not in magnitude.
- **The cumulative-charge column is not a measure of activity and must not be read as one.**
  It is not monotone in acts, in population or in anything else. At 16 domains the arm that
  minted nothing paid the most (A2a, 59.88) and the arm that minted 40 043 acts paid the
  least (A1, 52.65), because demand is dominated by held content and A1's high-turnover
  population is perpetually young; and separately, a community charged more per round starves
  sooner and accrues fewer unit-rounds to be charged over. **No cost comparison between arms
  is asserted anywhere in this log.**
- **Every population figure is taken at or near a binding ceiling, of a system that is still
  moving.** A1 is pinned by the cap at all three widths; A2a and A2b oscillate with a swing of
  37–42 units. The arm *ordering* at 16 domains is informative and agrees on both the horizon
  snapshot and the trough; the arm *levels* are not equilibria and are not reported as any.
- **A correlation that looked like half of `P-D4` at the reference configuration inverts by
  16 domains** (survivors' positive-standing records 1.65 vs the dead's 0.87 at 8 domains;
  1.19 vs 1.33 at 16). Nothing in this run separates standing from exposure time. Any future
  reading of that pair must control for lifespan before claiming anything.
- **`P-D2`'s comparison class is almost empty.** A mean of 0.38 unplanted laws and 0.00
  converses per run at 8 domains is not a population; the huge lineage contrast rests on the
  near-absence of false laws, which is a fact about the induction routine and
  `dispose_challenges` before it is a fact about the world.
- **`P-D3`'s first-death gap is a small-field artefact.** At 8 domains the ablated arm's first
  death comes up to 23 rounds after A1's; by 16 domains it is one round in six of eight seeds.
  Only the *population* reading of `P-D3` survives widening.
- **`P-D5` and `P-D6` are not run outcomes.** `P-D5` explicitly fits nothing; `P-D6` is a
  finding of the design sitting whose negative check is weak by its own admission — and two of
  the three tests backing it were shown to be defeatable in this round.
- **Field widths beyond 16 were not tried.** At 20 domains the ceiling is 190 and `N₀` 56,
  and the run cost grows faster than the population; the escalation's failure to clear at
  8, 12 and 16 with `τ` falling monotonically (0.000397 → 0.000247 → 0.000178) is what
  licenses the finding, not an exhaustive search.
- **D-series figures do not compare with C-series ones** (spec §6): different field, PAIRS
  scheme, no stagger. No reading here should be set beside a C-series number.

## Disposition

`P-D1` **held** · `P-D2` **held on lineage, selection clause not reached** · `P-D3`
**refuted as stated, confirmed in substance on population** · `P-D4` **not reached — no
consumer** · `P-D5` **not reached, by design** · `P-D6` **held as a finding-in-advance** ·
`P-D7` **refuted**.

Three of seven did not come out as pre-registered, and two of those three are the more
useful readings: `P-D3`'s inversion located the difference between *turnover* and
*mortality*, and `P-D4`'s null located a **missing edge in the architecture** — the ask is a
broadcast, so no price can ever reach the preference. Whether `whom_to_ask` should acquire a
consumer is a `c_unit.py` question and belongs to its own sitting, alongside D-0's
`peers`-versus-`SourceStanding` fork (spec §5.2), which is where the meaning of `P-D4` was
already known to be at stake.

**Two things this run would have got wrong had it stopped at the reference configuration.**
At 8 domains every arm reads 28 survivors, so `P-D3` would have been recorded as *refuted,
full stop* — the ablation invisible — instead of refuted-as-stated and confirmed on
population. And at 8 domains A1's survivors hold nearly twice the positive-standing records
of its dead, which would have read as `P-D4` half-confirmed; by 16 domains the relationship
has **inverted**. The escalation rule never cleared, and it still earned its place in the
cheat register: **widening the field is what made two of these readings honest.**

**And one thing this run would have got wrong entirely had the channels not been counted.**
Four fix rounds passed with `answer` minting nothing and `corroborate` minting nothing, in
every arm at every width, while the driver's docstring asserted the round order was the
C-series' own and that both channels were load-bearing. Survivors, births, deaths, acts and
charges all read plausibly throughout. **A figure that looks reasonable is not evidence that
the thing producing it ran.** The instrument that caught it —
`runs/d1/channel_probe.py`, which counts *marks minted* against *calls made* — costs one
short run and should be pointed at any channel before its absence is read as a result.
