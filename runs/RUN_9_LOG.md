# Run 9 log — forecast-centered bins + per-arm instrumentation (NWS weather) — EXECUTED & DISPOSED

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §20](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— the successor to run 8's F2⁸/F3⁸. Run 8 established that at the 20 °F band-cap the
re-generalized temperature law settles into a **positive-net limit cycle**, not a fixed point,
and that the precip arm stayed **dormant** the whole run. Run 9 turns two knobs to interrogate
both: **forecast-centered bins** (does removing grid-edge fragility convert the limit cycle to a
fixed point, or do noisy domains always limit-cycle?) and **per-arm instrumentation** (was precip
well-calibrated, or did its claims rarely mature?). The seeded theory ("what is forecast,
happens") remains the object under empirical fire; findings are about the game and NWS forecasts
as represented — never the world. *Progression, not progress.*

**Driver (as launched):** `caffeinate -i uv run python tools/run_live_weather.py
--runs-dir runs/run9 --regenerate --bin-mode centered --max-seconds 50400`
(stations KAUS KBOS KDEN KMIA KSEA · horizon 6 h · band 5 °F **centered** · PoP ≥ 60% ·
min_interval 600 s · ttl 48 polls · supervisor + crash/resume armed · re-generalize on,
band-cap 20 °F, pop-cap 90%).

**New machinery under test:** `src/weather_source.py` — `band_bounds` (grid | forecast-centered)
+ `PendingClaim.band_lo` (resolution by half-open containment, mode-independent) + `bin_mode`
knob (carried across resume) + per-arm counters (`claims_raised_by_kind` /
`resolutions_by_kind`); `tools/run_live_weather.py` — `--bin-mode` + per-arm digest. F1⁸
(`retract_subgraph` structural ERA) already fixed and banked.

## Session header

| field | value |
|---|---|
| date / operator | 2026-07-09 06:27 → 20:23 (author, delegated) — completed on `max_seconds` |
| stations · claim kinds | KAUS KBOS KDEN KMIA KSEA · temp bands (5→20 °F, **centered**), precip (PoP ≥ 60%) |
| horizon · ttl | 6 h · 48 polls |
| stops | `max_seconds` 50400 (fired, on schedule) |
| code version (git SHA) | `dffb638` (run-9 machinery) or later — *not captured; see F3⁹* |

**Totals (14 h, stopped on `max_seconds`):** **164 rounds · 27 segments · 26 recorded polls ·
100 claims raised (100 temp, 0 precip), 64 resolved (all temp), 1 dropped, 0 fetch_errors** ·
ledger (temp) **48 hits · 16 misses · net +32 · accuracy 0.75** (run-level) · **3
band-widening re-generalizations** (5→10→15→20 °F by poll 8, then pinned at the cap) · **both
laws standing** (temp reseeded at the 20 °F cap; precip never bet).

> **Provenance of these numbers.** The run's stdout digest (per-segment reseed count, band
> trajectory, poise strip) was **not captured to a file** (F3⁹). The figures here are
> reconstructed from the persisted artifacts — `runs/run9/items.jsonl` (26 recorded polls),
> `state.json`, and `weather_state.json` — which are solid for claims/resolutions/accuracy/band
> trajectory but do not recover the exact `challenge_to_M` (law-fall) count.

## Priors P1⁹–P4⁹ — observed vs expected

| prior | expected | observed | meta-disposition |
|---|---|---|---|
| P1⁹ **centered bins raise reliability at a given band** (headline) | temp accuracy at a given width exceeds run 8's grid accuracy; the controller widens *less* (narrower converged band, fewer reseeds) | **CONFIRMED for reliability; the "widens less" rider FALSIFIED.** At the 20 °F band, centered temp accuracy is **0.82** (40 h / 9 m) vs run 8's grid **~0.70** at the same band — the sharper discretization is more reliable. But the controller still climbed to the **20 °F cap** (5→10→15→20 by poll 8), so it did *not* converge at a narrower band. | confirmed (reliability); rider disposed → F1⁹ |
| P2⁹ **fixed point vs limit cycle** | the sharper discretization converts F2⁸'s limit cycle toward a fixed point (reseeds fall, band converges and holds) — or the honest null: a noisy domain still limit-cycles even centered | **CONFIRMED — the primary hypothesis, not the null.** Once the band pinned at 20 °F, misses fell away: the **settled tail (last 8 recorded polls) is 24 hits, 0 misses (accuracy 1.00)**, where run 8's grid bins kept limit-cycling at ~0.7 at the same band. Centered bins **converted the F2⁸ limit cycle toward a fixed point.** | confirmed; **disposes F2⁸** → F1⁹ |
| P3⁹ **per-arm instrumentation disambiguates the dormant precip arm** | the digest resolves F3⁸: precip resolved-many-all-hits (well-calibrated) vs raised-but-rarely-resolved (dormant) | **CONFIRMED, decisively.** `claims_raised_by_kind = {temp: 100}` — **precip raised *zero* claims all run.** It was dormant not because PoP ≥ 60% was well-calibrated but because **PoP never reached 60% in any sampled forecast window** across the five stations, so no precip claim ever matured to bet. | confirmed; **disposes F3⁸** → F2⁹ |
| P4⁹ floor + parity unchanged | §3.3 attests; `--resume` carries `bin_mode` + per-arm counters + knobs; correspondence-not-truth holds | **CONFIRMED.** 0 fetch_errors across 100 claims / 26 polls; `bin_mode: centered` + the recalibrated 20 °F band + per-arm counters all present in the carried `weather_state.json` (so a resume would continue centered); §3.3 attested at every segment checkpoint. | confirmed |

## Findings (dated, disposed)

### F1⁹ (2026-07-10) — forecast-centered bins convert the F2⁸ limit cycle toward a **fixed point** · **the P2⁹ payoff; disposes F2⁸**

Run 8's F2⁸ left the question open: is the positive-net limit cycle (temp law ~0.7 reliable,
felled ~once per segment at the 20 °F cap) *intrinsic domain noise*, or an artifact of the
**grid** discretization (a forecast near a bin edge fragile to a small observation error)? Run 9
answers: **substantially an artifact.** With forecast-**centered** bins — a miss needs
`|obs − forecast| > band/2`, symmetric, edge-fragility-free — the temperature law's accuracy at
the 20 °F band rose to **0.82** (from ~0.70), and the **settled tail converged to 1.00** (24
hits, 0 misses over the last 8 recorded polls). The band trajectory shows the knob converging
(5→10→15→20 by poll 8, then pinned) and, once pinned, the *law* converging too — misses that
persisted every segment under grid bins fell to zero. The limit cycle was, in large part, the
grid's edge-fragility; centering it converts the loop toward the fixed point F2⁸ could not reach.
*Nuance (honest):* the mid-run (polls 10–16) still showed occasional band-20 misses before the
tail cleaned up, and a calm-weather tail cannot be fully separated from true convergence with
these artifacts alone — but the band-20 *run-average* 0.82 (vs run 8's 0.70 at the same band) is
robust either way. The "controller widens *less*" rider of P1⁹ is **falsified**: centering raised
reliability *at* a band but did not let the controller stop short of the cap.

### F2⁹ (2026-07-10) — the precip arm raised **zero** claims · **the F3⁸ disambiguation, resolved**

Run 8's F3⁸ could not tell whether the dormant precip arm was *well-calibrated* (PoP ≥ 60%
holding) or simply *never bet*. The run-9 per-arm instrumentation (`claims_raised_by_kind`)
settles it: **precip raised 0 claims** the entire run — PoP never reached the 60 % gate in any
sampled forecast hour across the five stations, so the precip law had nothing to forecast and
`forecast_precip`/`precip` appear in M only as the standing law itself. The non-binned control
arm was therefore *inert*, not *stable*; it neither confirms nor refutes the bin-ceiling
hypothesis (it never entered the contest). A future run wanting a live precip arm should lower the
PoP gate or choose a wetter station set / season. F3⁸ disposed.

### F3⁹ (2026-07-10) — the run's **stdout digest was not captured** · **an ops gap; driver fixed**

The per-segment digest (bets, dispositions, reseed count, per-station errors, poise strip) and the
final report were printed to stdout and **lost** — the launch did not redirect them to a file.
The persisted artifacts (`items.jsonl`, `state.json`, `weather_state.json`) recover
claims/resolutions/accuracy/band-trajectory (this log), but **not the exact `challenge_to_M`
(law-fall) count** that would make P2⁹'s "fixed point" fully rigorous rather than inferred from
the miss trajectory. *Resolved:* `tools/run_live_weather.py` now **tees its digest to
`runs/runN/console.txt`** (append, flush-per-line) so the reseed/disposition/poise stream is a
first-class replayable artifact. A run-10 checklist item: it is captured by default.

---

*Cross-run disposition:* **F2⁸** (RUN_8_LOG — the positive-net limit cycle) is **disposed** by
F1⁹: it was largely a grid-binning artifact, and forecast-centered bins convert it toward a fixed
point. **F3⁸** (the dormant precip arm) is **disposed** by F2⁹: precip never bet (PoP < 60 %
throughout). The remaining open thread is **run 10** — a live precip arm (lower PoP gate / wetter
stations) to give the non-binned control something to contest, with the console now captured
(F3⁹).

**Artifacts:** `runs/run9/items.jsonl` (26 polls, offline replay) · `runs/run9/checkpoints` ·
`runs/run9/state.json` + `weather_state.json` (carried state). See
[runs/OPERATIONS.md](OPERATIONS.md) for the digest glossary.
