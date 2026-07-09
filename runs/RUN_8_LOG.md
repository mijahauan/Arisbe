# Run 8 log — predict → refute → **re-generalize** (NWS weather) — EXECUTED & DISPOSED

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §19](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— the successor to run 7's F2⁷ (after the world falsified both seeded laws the game fell
*silent*). Run 8 closes the loop: after refutation, **re-generalize** — an adaptive controller
turns the discretization (the falsifiability knob) and re-seeds the fallen law, so the arc is
predict→refute→**re-generalize**, not predict→refute→silence. Launch delegated to the author
(this session); priors P1⁸–P5⁸ affirmed as drafted. The seeded theory ("what is forecast,
happens") is the object under empirical fire; findings are about the game and NWS forecasts as
represented — never the world. *Progression, not progress.*

**Driver (as launched):** `caffeinate -i uv run python tools/run_live_weather.py
--runs-dir runs/run8 --regenerate --max-seconds 50400` (stations KAUS KBOS KDEN KMIA KSEA ·
horizon 6 h · band 5 °F · PoP ≥ 60% · min_interval 600 s · ttl 48 polls · supervisor +
crash/resume armed · re-generalize on, band-cap 20 °F, pop-cap 90%).

**New machinery under test:** `src/weather_recalibration.py` (`recalibrate` — the adaptive
controller-to-target) · the generic `reseed_laws` seam in `live_runner` · `PendingClaim.width`
(in-flight claims resolve at raise-time width) · `weather_source._fetch_retry` (F1⁷
retry/backoff + per-station error counts).

## Session header

| field | value |
|---|---|
| date / operator | 2026-07-07 22:19 → 2026-07-08 12:19 (author, delegated) |
| stations · claim kinds | KAUS KBOS KDEN KMIA KSEA · temp bands (5→20 °F), precip (PoP ≥ 60%) |
| horizon · ttl | 6 h · 48 polls |
| stops | `max_seconds` 50400 (fired, on schedule) |
| code version (git SHA) | `24b3877` (run-8 machinery) |

**Totals (14 h, stopped on `max_seconds`):** **165 rounds · 32 recorded polls · 100 claims
raised, 65 resolved, 0 dropped, 0 fetch_errors** · ledger **30 hits · 13 misses · 22
abstentions · net +17 · accuracy 0.70** · **13 re-generalizations** (temp only) · **both laws
standing at end** (temp reseeded at the 20 °F cap; precip never fell) · **4 crashes survived**
(all absorbed by the crash/resume supervisor — see F1⁸) · poise ● ●.

## Priors P1⁸–P5⁸ — observed vs expected

| prior | expected | observed | meta-disposition |
|---|---|---|---|
| P1⁸ **re-generalization keeps the game alive** (headline) | after a `challenge_to_M`, the fallen kind's law returns within a segment and **bets again** — prediction, not abstention | **CONFIRMED, in full.** 13 re-generalizations: each temp `challenge_to_M` was followed by a reseed and the law bet again the next segment. Run 7's silent second act (F2⁷) is closed — the loop is predict→refute→re-generalize. | the crossing succeeded; F2⁷ disposed |
| P2⁸ the calibration payoff is **live-only** | a re-generalized kind's **live** hit-rate recovers toward `target` as the band widens — the effect the replay structurally cannot show | **CONFIRMED — the headline live vindication.** Temp live accuracy climbed off the 0.00 floor as the band widened 5→10→15→20 °F, then held a windowed **0.67–0.88** with run-level **0.70, net +17**. The offline replay (§19) could only reach net −19 on band-frozen claims; live re-discretization of *fresh* observations produced the recovery. Exactly the causality the replay could not exhibit. | confirmed; the live-only hypothesis holds |
| P3⁸ convergence within the caps | the controller settles (stops stepping) once a kind meets target or hits its cap; no unbounded oscillation | **REFINED (F2⁸).** The *knob* converged — the band stepped to its 20 °F cap and held there, no unbounded oscillation (net stayed positive and grew to +17). But the *law* did **not** settle to a fixed point: at ~0.7 reliability it kept being felled ~once per segment and reseeded — a **positive-net limit cycle**, a *dynamic* steady state. Convergence is of the knob, not the law. | confirmed for the knob; **refined** for the law → F2⁸ |
| P4⁸ F1⁷ resilience | a flaky endpoint recovers within the retry budget (invisible); a dark station is bounded, counted, named | **CONFIRMED.** **0 fetch_errors** across 100 claims / 32 polls; per-station: none. The retry/backoff recovered every transient endpoint failure invisibly. (Contrast run 7's 10 fetch_errors.) | confirmed; F1⁷ closed |
| P5⁸ floor unchanged | §3.3 attests; `--resume` carries the recalibrated knobs; correspondence-not-truth holds | **CONFIRMED, and stress-tested.** The recalibrated band (20 °F) and pending claims were carried intact across **4 crash/resumes**; the run finished on `max_seconds` on schedule (the resumes did *not* extend the wall-budget); correspondence-not-truth holds (a resolved forecast is low-warrant). | confirmed; resume hardened by F1⁸ |

## Findings (dated, disposed)

### F1⁸ (2026-07-08) — `retract_subgraph` crashes on a law-cut with a cross-area line of identity · **FIXED 2026-07-08**

The `challenge_to_M` law-relinquishment (`model_revision.retract_subgraph`) erased a sheet-level
law-cut by a Dau **ERA**, probing *every* sheet cut. Over the long re-generalizing run the
reseeded temp law took on a shape whose interior shares a line of identity across an area
boundary; ERA's for-erasure closure rejects such a cut (*"Selected subgraph contains elements
not in target area"*), so the probe **raised** rather than skipping — 4 crashes. Each was
absorbed by the crash/resume supervisor (F1⁸ is the reason it fired), so the science is intact,
but it is a real robustness gap that recurs in every long re-generalizing run.

*Resolved:* `retract_subgraph` now removes the cut **structurally** (`_without_cut_subtree`,
mirroring the 2026-07-03 `retract_atom` fix) — never invoking the ERA closure validator, keeping
a vertex still incident to a *surviving* edge (so a law's relinquishment never severs a sheet
atom's line). Regression tests: `tests/test_model_revision.py` (6). Core suite + all
`challenge_to_M` users green.

### F2⁸ (2026-07-08) — the re-generalized law settles into a **positive-net limit cycle**, not a fixed point · **the P3⁸ refinement**

For an inherently noisy, discretized domain the honest steady state of predict→refute→re-generalize
is **dynamic**, not static. At the 20 °F cap the temp law is ~0.7 reliable — genuinely
predictive (net +17, climbing) — but ~0.7 reliability *guarantees* an occasional counterexample,
so each segment the world fells it once and the controller reseeds the calibrated law. It never
becomes permanently standing because a discretized weather law *cannot* be made perfectly
reliable. This is arguably a *better* outcome than a frozen fixed point: the loop keeps earning
its calibration against a live world rather than freezing a guess. *Disposition:* not a defect —
the faithful result; it sets **run 9** (forecast-**centered** bins, to test whether a sharper
discretization converts the limit cycle to a fixed point, or whether noisy domains always
limit-cycle).

### F3⁸ (2026-07-08) — the precip arm stayed **dormant** · **run-9 instrumentation queued**

The non-binned precip law (`~[ (forecast_precip *s *t) ~[ (precip s t) ] ]`) **stood the entire
run** — never refuted, never re-generalized; all 13 re-generalizations were temp. The
binned/non-binned contrast is stark: temp (binned) limit-cycled with 13 reseeds; precip (binary)
simply held. Two readings remain open — PoP ≥ 60% was well-calibrated from the start, *or* precip
claims rarely matured/were bet. *Disposition:* run 9 must surface **per-arm bet counts** to
disambiguate; the non-binned arm is the clean control for F2⁸'s bin-ceiling hypothesis (no bin
ceiling → it should either hold or re-generalize *cleanly* by raising the gate, unlike temp).

### F4⁸ (2026-07-08) — the crash/resume supervisor absorbed a **non-fetch** crash · **resume design validated beyond its purpose**

The crash/resume machinery was built (F1⁷) for flaky NWS fetches. Here it absorbed **4 genuine
logic crashes** (F1⁸): each resume restored pending claims + the recalibrated knobs + the decay
clock from `weather_state.json`, and the run finished on schedule. A design built for one failure
mode caught a different one — the resume floor is stronger than its original brief. (With F1⁸
fixed, this path should now be quiet; the resilience remains banked.)

---

*Cross-run disposition:* **F2⁷** (RUN_7_LOG — "the discretization is the falsifiability knob")
is **disposed** by this run: turning the knob (widen the band) after refutation re-generalizes a
betting law, closing the predict→refute→silence gap. The remaining open thread is F2⁸/F3⁸ →
**run 9** (forecast-centered bins + per-arm instrumentation).

**Artifacts:** `runs/run8/items.jsonl` (32 polls, offline replay) · `runs/run8/checkpoints` ·
`runs/run8/state.json` + `weather_state.json` (carried state). See
[runs/OPERATIONS.md](OPERATIONS.md) for the digest glossary.
