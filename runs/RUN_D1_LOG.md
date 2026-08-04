# D-1 — the priced world, read against its pre-registered priors (run log)

> **Spec:** [the D-series design](../docs/superpowers/specs/2026-08-02-d-series-building-the-stake-design.md)
> — priors `P-D1`…`P-D7` in its §7, **committed before anything was built**; the cheat
> register in §8, including item 6's escalation rule; the four arms in §6.
> **Build:** `src/d_world.py` + driver `tools/run_d1.py`, tests `tests/test_d_world.py`
> (56 passing). `src/c_unit.py` and `src/c_marks.py` are untouched by the series;
> `src/c_field.py` gained only the additive `wide_spec` beside an unmoved `default_spec`,
> so no C-series figure moves.
> **Run:** `tools/run_d1.py --rounds 60 --domains {8,12,16}`, 2026-08-04, four arms × eight
> seeds (1, 2, 3, 4, 5, 7, 42, 99) at each of three field widths — **32 communities per
> width, 96 in all**, plus 24 calibration runs. Deterministic: `play` twice on one seed
> agrees (`test_two_runs_of_one_arm_agree`).
> Raw console output `runs/d1/sweep_d{8,12,16}.txt`; the by-hand analysis pass for `P-D2`
> and `P-D4` is `runs/d1/analyze.py` → `runs/d1/analysis_d{8,12,16}.json`.

## The result, in one paragraph

**The stake bites and the population does not settle.** Mortality is a consequence of the
subtraction with nothing installed to produce it — no `die()`, no TTL, no lifespan anywhere
in `src/` — and it arrives on schedule: at eight domains the first death lands in **round 6
of all eight seeds** in arm A1, and 49–60 units die per 60-round run in a world where the
control (`A0`, the meter read and not subtracted) buries nobody. That is `P-D1`, and it is
the series' point. But the **escalation rule fired at every field width tried** — 8, 12 and
16 domains, seat ceilings 28, 66 and 120 — because in the full-channel priced arm the
population runs to the seat cap in essentially every seed and stays there. **`P-D7` is
refuted by its own stated failure condition**: *"fails if size runs to the ceiling (the cap
is deciding, not the economy)."* It does — and the ablated arms, which do sit below the cap
at 120 seats, turn out not to be settled either but to **oscillate** between the ceiling and
roughly half of it, which is a third outcome the prior never named. Widening the field to
120 seats separated the arms without freeing A1: **A1 holds 119.75 of 120 while the ablated
arms cycle down to 89.1 (`A2a`) and 81.4 (`A2b`)** — the channel is worth roughly **47% more
standing population**, which is the first thing in this project's history that *ablating the
putative sign* has actually moved. `P-D3` reads **refuted as literally stated and confirmed in substance**: the
ablation does not shorten a *unit's* life (it lengthens it), but it plainly costs the
*community* its number. `P-D2` holds on lineage and fails to demonstrate its selection
clause, because the unpriced control reproduces the same ordering with zero mortality.
`P-D4` is **not reached, and for a reason worth more than the prior**: the priced,
breeding population finally gives typification a real choice to make — 21.1% of 8 627
preference occasions have two or more candidates, against the C-series' *none* — and
`whom_to_ask` still has no consumer, because a question is a broadcast.

## The measured world

Every number in this table is **measured, not chosen** (spec §4). `E1 = 1` is the numéraire
and the only free number. Both prices are re-measured at each field width, because a price
measured in one world and applied in another would be a choice wearing a measurement's
clothes (`test_calibration_is_re_measured_at_each_field_width`).

| field | seats = C(k,2) | `N₀` (three witnesses / domain) | measured τ | measured `E0` | birth threshold 2·`E0` |
|---|---|---|---|---|---|
| **8 domains** (the spec's reference configuration) | **28** | **18** | **0.000382** | **0.076771** | 0.153542 |
| 12 domains | 66 | 30 | 0.000241 | 0.048108 | 0.096216 |
| 16 domains | 120 | 42 | 0.000174 | 0.034708 | 0.069416 |

`τ` is the flat price per unit of demand at which the baseline (arm-0) community breaks even
over its own run — total charge equals total income — summed across all eight seeds so no
single seed sets it. `E0` is the median over units of a unit's own cumulative charge through
`t*`, the **median round of a unit's first hit**. A founder is endowed at exactly `E0` and
must double it before it may breed.

## The arms

| | |
|---|---|
| **A0** | charge computed and reported, **not subtracted** — the control, and the calibration source |
| **A1** | charge subtracted |
| **A2a** | subtracted, mark channel occluded entirely (cost *and* benefit removed) |
| **A2b** | subtracted, acts still minted and charged but peers receive nothing — **the honest ablation** |

`A2a` is reported beside `A2b` to keep the *mute-and-cheaper* confound visible: a unit with
the channel off mints nothing and could outlive its peers by being silent rather than by
being right.

### 8 domains — 28 seats, `N₀` = 18

| arm | seed | survivors | born | died | acts minted | total charge | peak pop. |
|---|---|---|---|---|---|---|---|
| A0 | 1 | 18 | 0 | 0 | 3877 | 48.226 | 18 |
| A0 | 2 | 18 | 0 | 0 | 4073 | 50.589 | 18 |
| A0 | 3 | 18 | 0 | 0 | 3944 | 50.702 | 18 |
| A0 | 4 | 18 | 0 | 0 | 3845 | 47.461 | 18 |
| A0 | 5 | 18 | 0 | 0 | 4061 | 50.607 | 18 |
| A0 | 7 | 18 | 0 | 0 | 4059 | 49.860 | 18 |
| A0 | 42 | 18 | 0 | 0 | 4052 | 51.171 | 18 |
| A0 | 99 | 18 | 0 | 0 | 3884 | 49.384 | 18 |
| A1 | 1 | 28 | 63 | 53 | 8430 | 42.478 | 28 |
| A1 | 2 | 28 | 66 | 56 | 8822 | 41.898 | 28 |
| A1 | 3 | 28 | 68 | 58 | 8644 | 44.073 | 28 |
| A1 | 4 | 28 | 62 | 52 | 8493 | 41.669 | 28 |
| A1 | 5 | 28 | 60 | 50 | 8544 | 43.836 | 28 |
| A1 | 7 | 28 | 59 | 49 | 8380 | 44.284 | 28 |
| A1 | 42 | 28 | 65 | 55 | 8895 | 41.763 | 28 |
| A1 | 99 | 28 | 70 | 60 | 8166 | 41.401 | 28 |
| A2a | 1 | 28 | 39 | 29 | 0 | 46.672 | 28 |
| A2a | 2 | 28 | 44 | 34 | 0 | 46.893 | 28 |
| A2a | 3 | 28 | 43 | 33 | 0 | 46.880 | 28 |
| A2a | 4 | 28 | 43 | 33 | 0 | 45.756 | 28 |
| A2a | 5 | 28 | 42 | 32 | 0 | 49.175 | 28 |
| A2a | 7 | 28 | 39 | 29 | 0 | 47.598 | 28 |
| A2a | 42 | 28 | 45 | 35 | 0 | 45.464 | 28 |
| A2a | 99 | 28 | 45 | 35 | 0 | 47.903 | 28 |
| A2b | 1 | 28 | 44 | 34 | 7943 | 49.343 | 28 |
| A2b | 2 | 28 | 45 | 35 | 8321 | 48.988 | 28 |
| A2b | 3 | 28 | 46 | 36 | 8345 | 48.045 | 28 |
| A2b | 4 | 28 | 48 | 38 | 8021 | 47.730 | 28 |
| A2b | 5 | 28 | 42 | 32 | 8193 | 51.070 | 28 |
| A2b | 7 | 28 | 44 | 34 | 8147 | 49.321 | 28 |
| A2b | 42 | 28 | 50 | 40 | 8413 | 47.859 | 28 |
| A2b | 99 | 28 | 46 | 36 | 7978 | 48.788 | 28 |

**Every priced arm at every seed ends at exactly 28 — 100% of the ceiling.** Nothing about
the population can be read here; the cap decided it.

### 12 domains — 66 seats, `N₀` = 30

| arm | seed | survivors | born | died | acts minted | total charge | peak pop. |
|---|---|---|---|---|---|---|---|
| A0 | 1 | 30 | 0 | 0 | 6501 | 51.189 | 30 |
| A0 | 2 | 30 | 0 | 0 | 6693 | 53.406 | 30 |
| A0 | 3 | 30 | 0 | 0 | 6574 | 53.001 | 30 |
| A0 | 4 | 30 | 0 | 0 | 6469 | 50.166 | 30 |
| A0 | 5 | 30 | 0 | 0 | 6770 | 52.713 | 30 |
| A0 | 7 | 30 | 0 | 0 | 6654 | 52.003 | 30 |
| A0 | 42 | 30 | 0 | 0 | 6689 | 53.500 | 30 |
| A0 | 99 | 30 | 0 | 0 | 6482 | 52.022 | 30 |
| A1 | 1 | 66 | 228 | 192 | 21034 | 47.453 | 66 |
| A1 | 2 | 66 | 228 | 192 | 21028 | 49.713 | 66 |
| A1 | 3 | 66 | 210 | 174 | 20958 | 49.552 | 66 |
| A1 | 4 | 66 | 212 | 176 | 20554 | 49.006 | 66 |
| A1 | 5 | 66 | 226 | 190 | 21257 | 48.243 | 66 |
| A1 | 7 | 66 | 224 | 188 | 20783 | 48.631 | 66 |
| A1 | 42 | 66 | 231 | 195 | 21477 | 47.414 | 66 |
| A1 | 99 | 66 | 229 | 193 | 20945 | 46.104 | 66 |
| A2a | 1 | 66 | 143 | 107 | 0 | 56.691 | 66 |
| A2a | 2 | 66 | 161 | 125 | 0 | 55.152 | 66 |
| A2a | 3 | 66 | 155 | 119 | 0 | 55.316 | 66 |
| A2a | 4 | 66 | 158 | 122 | 0 | 56.165 | 66 |
| A2a | 5 | 66 | 141 | 105 | 0 | 55.917 | 66 |
| A2a | 7 | 66 | 153 | 117 | 0 | 56.508 | 66 |
| A2a | 42 | 66 | 159 | 123 | 0 | 56.137 | 66 |
| A2a | 99 | 66 | 149 | 113 | 0 | 55.705 | 66 |
| A2b | 1 | 66 | 156 | 120 | 19856 | 57.660 | 66 |
| A2b | 2 | 66 | 170 | 134 | 20321 | 57.012 | 66 |
| A2b | 3 | 66 | 163 | 127 | 19964 | 58.148 | 66 |
| A2b | 4 | 66 | 166 | 130 | 20043 | 57.746 | 66 |
| A2b | 5 | 65 | 141 | 106 | 18374 | 57.707 | 66 |
| A2b | 7 | 66 | 165 | 129 | 20182 | 58.308 | 66 |
| A2b | 42 | 64 | 171 | 137 | 20607 | 57.409 | 66 |
| A2b | 99 | 64 | 157 | 123 | 19706 | 58.156 | 66 |

**A1 and A2a end at 66/66 in every seed; A2b at 65.4 on average** — the first faint sign of
the ablation, three seeds short of the cap and no more.

### 16 domains — 120 seats, `N₀` = 42

| arm | seed | survivors | born | died | acts minted | total charge | peak pop. |
|---|---|---|---|---|---|---|---|
| A0 | 1 | 42 | 0 | 0 | 9160 | 52.017 | 42 |
| A0 | 2 | 42 | 0 | 0 | 9330 | 53.704 | 42 |
| A0 | 3 | 42 | 0 | 0 | 9188 | 53.167 | 42 |
| A0 | 4 | 42 | 0 | 0 | 9092 | 50.840 | 42 |
| A0 | 5 | 42 | 0 | 0 | 9521 | 53.815 | 42 |
| A0 | 7 | 42 | 0 | 0 | 9372 | 52.669 | 42 |
| A0 | 42 | 42 | 0 | 0 | 9393 | 54.002 | 42 |
| A0 | 99 | 42 | 0 | 0 | 9157 | 52.786 | 42 |
| A1 | 1 | 120 | 483 | 405 | 36652 | 50.758 | 120 |
| A1 | 2 | 120 | 414 | 336 | 34323 | 51.627 | 120 |
| A1 | 3 | 120 | 491 | 413 | 37614 | 51.981 | 120 |
| A1 | 4 | 120 | 478 | 400 | 37179 | 52.315 | 120 |
| A1 | 5 | 120 | 507 | 429 | 38352 | 51.611 | 120 |
| A1 | 7 | 120 | 419 | 341 | 34315 | 51.697 | 120 |
| A1 | 42 | 120 | 439 | 361 | 36567 | 53.082 | 120 |
| A1 | 99 | 118 | 480 | 404 | 36767 | 52.511 | 120 |
| A2a | 1 | 94 | 256 | 204 | 0 | 59.192 | 120 |
| A2a | 2 | 85 | 276 | 233 | 0 | 58.707 | 120 |
| A2a | 3 | 87 | 247 | 202 | 0 | 59.508 | 120 |
| A2a | 4 | 90 | 272 | 224 | 0 | 58.744 | 120 |
| A2a | 5 | 92 | 231 | 181 | 0 | 58.834 | 120 |
| A2a | 7 | 89 | 257 | 210 | 0 | 58.851 | 120 |
| A2a | 42 | 83 | 265 | 224 | 0 | 59.561 | 120 |
| A2a | 99 | 93 | 269 | 218 | 0 | 58.633 | 120 |
| A2b | 1 | 86 | 221 | 177 | 28574 | 59.628 | 120 |
| A2b | 2 | 72 | 250 | 220 | 30003 | 59.351 | 120 |
| A2b | 3 | 81 | 236 | 197 | 28899 | 58.864 | 120 |
| A2b | 4 | 77 | 251 | 216 | 29833 | 59.200 | 120 |
| A2b | 5 | 76 | 211 | 177 | 28306 | 59.850 | 120 |
| A2b | 7 | 91 | 257 | 208 | 29569 | 58.833 | 120 |
| A2b | 42 | 84 | 260 | 218 | 30396 | 58.719 | 120 |
| A2b | 99 | 84 | 251 | 209 | 29349 | 58.656 | 120 |

**The arms separate.** A1 mean 119.75 of 120; A2a 89.13; A2b 81.38. A1's peak still touches
the cap in every seed.

### The arms in summary

| field | arm | survivors (mean) | % of ceiling | `N_eq / N₀` | born | died | acts | charge |
|---|---|---|---|---|---|---|---|---|
| 8 | A0 | 18.00 | 64.3 | 1.000 | 0 | 0 | 3 974 | 49.75 |
| 8 | A1 | 28.00 | **100.0** | 1.556 | 64.1 | 54.1 | 8 547 | 42.68 |
| 8 | A2a | 28.00 | **100.0** | 1.556 | 42.5 | 32.5 | 0 | 47.04 |
| 8 | A2b | 28.00 | **100.0** | 1.556 | 45.6 | 35.6 | 8 170 | 48.89 |
| 12 | A0 | 30.00 | 45.5 | 1.000 | 0 | 0 | 6 604 | 52.25 |
| 12 | A1 | 66.00 | **100.0** | 2.200 | 223.5 | 187.5 | 21 004 | 48.26 |
| 12 | A2a | 66.00 | **100.0** | 2.200 | 152.4 | 116.4 | 0 | 55.95 |
| 12 | A2b | 65.38 | **99.1** | 2.179 | 161.1 | 125.8 | 19 882 | 57.77 |
| 16 | A0 | 42.00 | 35.0 | 1.000 | 0 | 0 | 9 277 | 52.88 |
| 16 | A1 | 119.75 | **99.8** | **2.851** | 463.9 | 386.1 | 36 471 | 51.95 |
| 16 | A2a | 89.13 | 74.3 | 2.122 | 259.1 | 212.0 | 0 | 59.00 |
| 16 | A2b | 81.38 | 67.8 | **1.937** | 242.1 | 202.8 | 29 366 | 59.14 |

## The escalation check (spec §8 item 6)

> *"The escalation rule is stated in advance: if a measured equilibrium reaches 80% of the
> ceiling in any arm, the field grows and every figure is re-measured — a result taken at a
> binding ceiling is not reported as an equilibrium."*

**It fired at every field width tried, and it is still firing.**

| field | ceiling | 80% bar | highest population observed | settled level, A1 | verdict |
|---|---|---|---|---|---|
| 8 domains | 28 | 22.4 | **28** (every priced arm, every seed) | 28.00 = 100% | **fires** |
| 12 domains | 66 | 52.8 | **66** (every priced arm) | 66.00 = 100% | **fires** |
| 16 domains | 120 | 96.0 | **120** (every priced arm) | 119.75 = 99.8% | **fires** |

The task's diagnosis of the 8-domain case is confirmed and it survives widening: break-even
is calibrated on the run's **total** demand, but demand grows as models grow, so the early
rounds collect a small fraction of an income that arrives in full every round. The community
banks the surplus, crosses `2·E0` and breeds into whatever cap is available. Widening the
field raises the cap and lowers `τ` (0.000382 → 0.000174 across the three widths, since the
same income now clears against three times the demand) — so the world is *re-priced cheaper*
exactly as fast as it is given more room, and the full-channel arm reaches the new cap too.

**The finding, stated plainly: the calibrated world has no equilibrium below its seat cap at
any field size tried (8, 12, 16 domains), and `P-D7` fails.** No price was tuned to
manufacture one; the calibration is measured and stays measured.

**What widening did buy** is the arm separation the 8-domain field could not show at all.
At 28 seats every arm reads 28 and the ablation is invisible. At 120 the ablated arms sit
25–32% below the full-channel arm. So the escalation rule earned its keep even though it
never cleared: it converted an unreadable measurement into a readable one.

## The priors

### `P-D1` · mortality is a consequence — **HELD**

> *At subtracted charge, at least one reserve reaches zero within 60 rounds in a majority of
> the eight seeds, with no `die()`, TTL or lifespan anywhere in `src/`. Fails if nobody ever
> dies, or if everybody dies in round one.*

**Held in 8 of 8 seeds, in all three priced arms, at all three field widths.** At the
reference configuration arm A1 buries **49–60 units per run** (mean 54.1) and the **first
death lands in round 6 in every one of the eight seeds**. Nobody dies in round 0 or round 1,
and no community went extinct — so neither failure condition is met. The control `A0`, which
computes the identical charge and does not subtract it, records **zero deaths at every seed
and every width**, which is what makes the reading causal rather than incidental.

Nothing produces the death but running out. `tests/test_d_world.py::test_no_die_no_ttl_no_lifespan_in_the_d_world`
scans `src/` for the words and finds none; `test_the_unit_never_gains_a_reserve` pins that
`Unit` cannot perceive the balance it dies of.

### `P-D2` · laws have lineages, and survival tracks mediation — **HELD on lineage; the selection clause NOT REACHED**

> *Planted true laws should show longer lineages and more holders than converses and
> unplanted regularities. Fails if lineage length is uncorrelated with a law's truth.*

Lineage measured as **holder-rounds** (summed over every round and every living unit holding
the content) and **spread** (distinct units that ever held it), at 8 domains, means over the
eight seeds:

| arm | planted: holder-rounds / spread / laws found | converse | other (unplanted) |
|---|---|---|---|
| A0 (control, no deaths) | 204.2 / 4.51 / 7.62 | 0.0 / 0.0 / 0 | 7.12 / 0.12 / 0.25 |
| A1 | 245.1 / 14.98 / 8.00 | 0.0 / 0.0 / 0 | 1.00 / 0.12 / 0.25 |
| A2a | 305.5 / 12.11 / 8.00 | 0.0 / 0.0 / 0 | 2.75 / 0.12 / 0.25 |
| A2b | 306.4 / 12.30 / 8.00 | 0.75 / 0.12 / 0.12 | 5.12 / 0.25 / 0.38 |

The wider fields reproduce it: at 12 domains planted 334.4 holder-rounds (A1) against 1.77
unplanted, all twelve planted laws found in every priced run, 0.88 unplanted and 0.12
converses per run; at 16 domains planted 390.4 against 3.57, all sixteen found, 1.5 unplanted
and 0.25 converses.

**The first clause holds and holds hugely** — a planted law accumulates ~245 holder-rounds
where a non-planted one accumulates ~1, and every one of the field's planted laws is found in
every priced run at every width. Lineage length is emphatically *not* uncorrelated with
truth.

**The second clause is not reached, and the control is what says so.** `A0` — where nothing
is ever subtracted and **not one unit dies** — shows the same ordering (204 planted vs 7.1
unplanted). An ordering that is already there when mortality is switched off cannot be
evidence that *survival* tracks mediation. What the figures show is that **induction is
accurate**, not that the world selects: the comparison class is nearly empty (a mean of
**0.25 unplanted laws and 0.12 converses per run**), so the contrast rests on almost no
counter-population. `dispose_challenges` retracts a false law long before a holder could
starve of it, which is the honest mechanism behind the number.

The one place the priced world visibly changes a lineage is **spread**: at 16 domains a
planted law reaches **45.09** distinct units in A1 against **5.28** in A0 — but that is
**birth**, not death, doing the work. A priced world has 456 newborns per run to socialize
and the control has none. Selection would show as *false* laws dying with their holders, and
there are almost no false laws to die.

### `P-D3` · the ablation bites, measured in survival time — **REFUTED as stated; confirmed in substance on population**

> *A2b's communities die sooner than A1's — occlude the marks, prediction worsens, hitless
> rounds multiply, the stock burns faster. Fails if occluding the sign changes lifespan none.*

**The stated reading is refuted, with the sign inverted, at all three widths.**

| field | mean unit lifespan, A1 | A2a | A2b | first death, A1 | first death, A2b |
|---|---|---|---|---|---|
| 8 domains | **19.50** | 26.95 | **25.64** (+31%) | round 6, all 8 seeds | rounds 7–29 |
| 12 domains | **14.35** | 20.55 | **19.30** (+35%) | round 6, all 8 seeds | rounds 7–20 |
| 16 domains | **12.04** | 19.38 | **19.01** (+58%) | round 6, all 8 seeds | rounds 7–15 |

The ablated community's units live **31–58% LONGER**, not shorter, and its first death comes
1–23 rounds later — at all three widths, in the same direction, and the gap *widens* as the
field grows. And **no community died in any arm at any width**, so the prior's actual
predicate — *communities die sooner* — has **no observations at all**. On its own terms the
prior fails, and the reason it fails is instructive: A1's shorter lifespans are a
**turnover** effect, not a mortality effect. At 16 domains A1 puts **498.1 units through the
world** per run against A2b's 280.1, and a newborn inherits nothing, so the full-channel
community carries a much larger population of young poor units that pulls the mean down.

**The substance is confirmed on the number the cap finally let us read.** At 16 domains:

| arm | survivors at round 60 | vs A1 | trough, rounds 20–59 | vs A1 | acts minted | total charge |
|---|---|---|---|---|---|---|
| A1 (full channel) | **119.75** | — | **91.6** | — | 36 471 | 51.95 |
| A2a (channel off entirely) | 89.13 | **−25.6%** | 76.1 | **−16.9%** | 0 | 59.00 |
| A2b (mints and pays, reaches nobody) | **81.38** | **−32.0%** | **66.6** | **−27.3%** | 29 366 | 59.14 |

Occluding the sign costs the community **a sixth to a third of its standing population**, and
`A2b` — the honest ablation, cost held and sign removed — is the *worst* of the three on
both readings. The **trough** column is given beside the horizon snapshot because the ablated
arms oscillate (see `P-D7`), and the trough is the more robust comparison: it does not depend
on where in the cycle round 60 happened to fall. Both orderings agree.

**The mute-and-cheaper confound does not explain it:** A2a mints zero marks and still ends
25.6% short, and A2b — which pays for every act — ends **below** A2a rather than above it, on
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
   caller, and the D-1 round order omitted it while its own docstring claimed to be "the
   C-series' own" (whose driver does call it, `tests/test_c_channels.py` step (i)). So
   `Unit.peers` was **empty — zero records, not zero positive ones — at every unit, every
   seed, every arm and every width.** There was no inert instrument; there was no instrument.
   Fixed, and pinned by
   `tests/test_d_world.py::test_settling_credit_populates_peers_and_moves_no_dynamics`.

2. **Once closed, the choice the C-series lacked is there.** At 8 domains over eight seeds,
   sampling every living unit every round, arm A1 records **8 627 occasions on which some
   peer had earned a positive standing about a relation** — and on **1 819 of them (21.1%)
   there were two or more candidates to prefer between:**

   | positive-standing candidates | 1 | 2 | 3 | 4 | 5 | ≥2 |
   |---|---|---|---|---|---|---|
   | occasions, A1 @ 8 domains | 6 808 | 1 523 | 276 | 20 | — | 1 819 / 8 627 = **21.1%** |
   | occasions, A1 @ 12 domains | 13 290 | 3 766 | 989 | 227 | 28 | 5 010 / 18 300 = **27.4%** |
   | occasions, A1 @ 16 domains | 19 964 | 5 858 | 1 175 | 149 | 13 | 7 195 / 27 159 = **26.5%** |

   The choice also deepens with the field: five candidates appear at 12 and 16 domains where
   eight never produced more than four.

   The C-series measured this degenerate — *"all 939 uptake decisions had exactly one peer
   standing behind them"* — and the prior asked for a population in which a choice exists.
   **It exists.** At the end of the run A1's 224 surviving units hold **434 (peer, relation)
   records, 428 of them positive**, and hold a preference about **266** relations. (`A0`'s
   static 18-unit community manages 4 records and one preference in the same eight runs;
   `A2a` and `A2b` accumulate none at all, since nothing is ever adopted through an occluded
   channel, so `settle_credit` has nothing to reach a verdict on.)

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
| 8 domains | **1.93** | 0.97 | survivors hold twice as many |
| 12 domains | 1.58 | 1.43 | near-flat |
| 16 domains | 1.07 | **1.44** | **the dead hold more** |

Had only the reference configuration been run, that 1.93-vs-0.97 would have looked like
`P-D4` half-confirmed. It is exposure time: a unit that lives longer accumulates more records
*by living longer*, and as the field widens and mean lifespan falls from 19.50 to 12.04 the
relationship reverses. **Recorded prominently because it is exactly the kind of number a run
log that reported only its reference configuration would have reported as a result.**
The full distribution is in `runs/d1/analysis_d8.json` (`choice_histogram`,
`standing_survivors_mean`, `standing_dead_mean`) and `runs/d1/peers_probe.txt`.

### `P-D5` · an exponent is measurable, and β ≈ 1 is predicted — **NOT REACHED (nothing fitted, by design)**

> *"Still not a scaling measurement in D-1 — the realised topology is recorded for a later
> series, and nothing is fitted."*

Recorded and not fitted, as the prior itself instructs. What the run does show is **why the
question is harder than the rewrite hoped**: the total charge is nearly flat across every
arm and every field width (42.7 to 59.1 over communities ranging from 18 to 120 units),
because `τ` is *re-measured* at each configuration to make the baseline break even against a
fixed source `E1 = 1`. The calibration re-pins Σcost to the source at every width, so a
cross-width regression would fit the calibration and not the world.

Worse for any naive reading, **cumulative charge is not monotone in activity, in population
or in acts.** At 16 domains A2a mints **zero** acts, carries **89** units and pays **59.00**;
A1 mints **36 471** acts, carries **120** units and pays **51.95**. The arm with a third
more units and thirty-six thousand more acts pays **less**.

Two things produce that, and neither is a scaling law. (i) **Demand is dominated by held
content, not by acts**, and held content is largest where units live longest — so the arm
that mints most is the cheapest *per unit-round*:

| demand per unit-round | 8 domains | 12 domains | 16 domains |
|---|---|---|---|
| A1 (full channel) | **70.2** | **55.5** | **49.4** |
| A2a (channel off) | 75.6 | 62.5 | 58.5 |
| A2b (mints, reaches nobody) | 78.7 | 65.2 | **63.7** |

A1's mean lifespan at 16 domains is **12.04** rounds against A2a's 19.38, so its population
is perpetually young and holds little. (ii) Separately, a community charged more per round
starves sooner and therefore accrues fewer unit-rounds to be charged over — A2b logs 5 354
unit-rounds at 16 domains against A1's 6 064. **No cost comparison between arms is asserted
anywhere in this log**, and any exponent fitted to these totals would be reading turnover and
survivorship rather than a metabolism.

### `P-D6` · sensitization is absent, and structurally so — **HELD as a finding-in-advance, not a run outcome**

> *No measure of urgency varies with reserve level, because none can (ruling 5), and the same
> gap blocks the schedule from finding an optimum (ruling 9). Recorded as a result of this
> sitting rather than of a run. The negative check is weak.*

Recorded as the prior asks: **this is a result of the design sitting, not of the run**, and
the check is weak by construction — nothing sensitization-like could have appeared. Two
standing tests give the weak check what teeth it has:
`test_the_unit_never_gains_a_reserve` (no `Unit` attribute holds a balance, so no unit
behaviour can vary with one) and `test_the_world_holds_no_chooser` (no name in `d_world.py`
is spelled like a chooser, widened after review to catch a lambda bound to such a name).
Neither proves absence; both catch the cheapest way of writing the refused thing.

Nothing in 96 communities behaved as though a unit noticed its reserve, which is what one
would expect of a world in which the reserve is unreadable.

### `P-D7` · population finds a level, and the level is earned — **REFUTED**

> *Community size settles rather than running to the seat cap or to extinction in every seed,
> and `N_eq / N₀` is higher in A1 than in A2b. **Fails if size runs to the ceiling (the cap
> is deciding, not the economy)** or if the ratio is flat across arms.*

**Refuted by its own first failure condition, at every field size tried.** In arm A1 the
population runs to the seat cap in **8/8 seeds at 8 domains, 8/8 at 12, and 7/8 at 16**
(the eighth ends at 118 of 120), and the peak touches the cap in **every priced arm at every
width**. The cap is deciding, not the economy. This is not a knife-edge that a larger field
would clear: widening from 28 to 66 to 120 seats moved the ceiling by 4.3× and A1 filled all
three, because the calibration lowers `τ` in proportion as the field grows.

**And the ablated arms do not settle either — they oscillate.** The 16-domain field is wide
enough to show that the number under the cap is not an equilibrium but a **boom–bust cycle**.
Population range over rounds 20–59, means across the eight seeds:

| arm @ 16 domains | trough | peak | swing | one seed's trajectory (rounds 10/20/30/40/50/55/59) |
|---|---|---|---|---|
| A1 | 91.6 | 120.0 | 28.4 | 82 · 120 · 103 · 120 · 120 · 120 · 120 |
| A2a | 76.1 | 120.0 | 43.9 | 120 · 117 · 87 · 104 · 120 · 105 · 94 |
| A2b | 66.6 | 112.0 | **45.4** | 118 · 102 · 64 · 79 · 119 · 105 · 86 |

The ablated communities breed to the cap, starve back to roughly half of it, and breed again;
the swing is **45 units wide in A2b**, a third of the whole seat range. A1 climbs to the cap
and locks there (trough 91.6, and 120 for the last twenty rounds in most seeds). **So no arm
at any width produced a settled level:** one is pinned by the cap and the others cycle. The
mean survivor counts reported above are a snapshot at round 60 of a system still moving —
A2a's last-ten-round mean is 99.22 against 89.13 at the horizon, A2b's 91.38 against 81.38 —
and they should be read as *where the cycle happened to be*, not as an equilibrium.

**The second clause is the one that survives, and it must be reported as unconfirmed rather
than as held**, because A1's numerator is the cap's number and not the economy's:

| field | `N_eq/N₀`, A1 | `N_eq/N₀`, A2b | ratio A1 : A2b |
|---|---|---|---|
| 8 | 1.556 | 1.556 | 1.000 (both capped — flat, and uninformative) |
| 12 | 2.200 | 2.179 | 1.010 |
| 16 | 2.851 | 1.937 | **1.472** |

At 16 domains the ratio is **not** flat across arms and it runs in the predicted direction —
the community that predicts better holds 47% more of its number. But `P-D7` asked for a
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

## The three defects the build found by running

Each was found by **running the world**, not by reading the design, and each would have
produced a plausible-looking table.

1. **The calibration guaranteed extinction, because `E0` covered the time to the first
   LAW when only a HIT earns.** With `t*` read off first law-induction, `N₀·E0 = E1·(t*+1)`
   *regardless of `N₀`*: the community holds exactly the learning period's buffer and no
   margin, by construction. Rounds 0–3 carry zero hitters, so the community arrives at `t*`
   broke and every priced arm went extinct within 30 rounds. Re-reading `t*` off the first
   **hit** moves the median 3.0 → 4.0 and `E0` 0.2215 → 0.2765, and that 25% was the whole
   difference between extinction and a living community. *Holding a law earns nothing; a hit
   earns.*

2. **The doubt lifecycle was inert: challenges were minted and charged, and never disposed.**
   `dispose_challenges` is the only route by which an induced law is ever suspended or
   retracted. Omitted from the round, every unit bet on every law it induced — true or false
   — for the rest of the run, while paying for the challenge marks that should have settled
   them. A table drawn from that world would have shown laws with beautiful lineages and
   would have been measuring a world where nothing could ever be given up.

3. **The tariff had no aggregate bite under `τ = E1/demand`, so two arms came out
   byte-identical.** With `τ` inversely proportional to realised demand the total collected
   is *exactly* `E1` every round whatever the community does. Measured: A2b at demand 408 and
   A2a at demand 294 both collected 1.0000 and produced **identical** survivors, births and
   deaths at every seed, though A2b minted ~2 600 acts A2a never touched. Speaking more
   lowered `τ` and cost the community nothing; the price was purely *positional*. `τ` became
   a **calibrated constant** — measured, never chosen, exactly as ruling 7 requires; only the
   demand-normalised form was retired.

**And a fourth, found in this task by reading a measurement that came back zero** — recorded
under `P-D4` above: the typify channel was never closed (`settle_credit` was absent from the
round order), so `Unit.peers` was empty everywhere; and closing it changes no figure at all,
because `whom_to_ask` has no consumer. The prior had no instrument, and then it turned out
there was nothing for the instrument to be attached to.

## Limitations — what this run does not license

- **`A2a` and `A2b` differ only modestly, and the separation needs a long horizon.** At 16
  domains they end 89.13 and 81.38 against a ceiling of 120 — a 7.75-unit gap between them
  against a 30-unit gap to A1. Sixty rounds is enough to say the *channel* matters and not
  enough to say confidently how much of that is the sign and how much the cost of minting.
  A2b's being *below* A2a rather than above it rules out the mute-and-cheaper confound in
  sign, not in magnitude.
- **The cumulative-charge column is not a measure of activity and must not be read as one.**
  It is not monotone in acts, in population or in anything else. At 16 domains the arm that
  minted nothing paid the most (A2a, 59.00) and the arm that minted 36 471 acts paid the
  least (A1, 51.95), because demand is dominated by held content and A1's high-turnover
  population is perpetually young; and separately, a community charged more per round starves
  sooner and accrues fewer unit-rounds to be charged over. **No cost comparison between arms
  is asserted anywhere in this log.**
- **Every population figure is taken at or near a binding ceiling, of a system that is still
  moving.** A1 is pinned by the cap; A2a and A2b oscillate with a swing of 44–45 units. The
  arm *ordering* at 16 domains is informative and agrees on both the horizon snapshot and the
  trough; the arm *levels* are not equilibria and are not reported as any.
- **A correlation that looked like half of `P-D4` at the reference configuration inverts by
  16 domains** (survivors' positive-standing records 1.93 vs the dead's 0.97 at 8 domains;
  1.07 vs 1.44 at 16). Nothing in this run separates standing from exposure time. Any future
  reading of that pair must control for lifespan before claiming anything.
- **`P-D2`'s comparison class is almost empty.** A mean of 0.25 unplanted laws and 0.12
  converses per run is not a population; the huge lineage contrast rests on the near-absence
  of false laws, which is a fact about the induction routine and `dispose_challenges` before
  it is a fact about the world.
- **`P-D5` and `P-D6` are not run outcomes.** `P-D5` explicitly fits nothing; `P-D6` is a
  finding of the design sitting whose negative check is weak by its own admission.
- **Field widths beyond 16 were not tried.** At 20 domains the ceiling is 190 and `N₀` 56,
  and the run cost grows faster than the population; the escalation's failure to clear at
  8, 12 and 16 with `τ` falling monotonically (0.000382 → 0.000241 → 0.000174) is what
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
population. And at 8 domains A1's survivors hold twice the positive-standing records of its
dead, which would have read as `P-D4` half-confirmed; by 16 domains the relationship has
**inverted**. The escalation rule never cleared, and it still earned its place in the cheat
register: **widening the field is what made two of these readings honest.**
