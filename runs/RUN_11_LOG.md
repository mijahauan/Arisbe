# Run 11 log — the calibrated precip arm (F1¹⁰'s own prediction) — BUILT 2026-07-10

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— the principle at Part II §11.4, the ledger row at Part III §12; the successor to run 10's F1¹⁰. Run 10 found that the precip arm could not recover because its only
knob, the PoP **gate**, is a *selectivity* knob (raising it makes the arm bet less, never right — it
ratcheted to the 90 % cap and stayed refuted, net −5, acc 0.14 over just **9** bets). F1¹⁰ predicted
the fix: give precip a **calibration** knob that can bet the *majority* outcome. Run 11 builds that
knob (a two-direction cutpoint bet + a dry companion law) and asks: with N no longer starved, does the
calibrated precip arm **recover to a positive net** the way the temperature band did? A yes confirms
F1¹⁰ (knob-type, not domain, gates recovery); a no falsifies it (rain is unpredictable at this
horizon/scoring, and F1¹⁰ was over-read from a small sample). The seeded theory remains the object
under fire; findings are about the game and NWS forecasts as represented — never the world.
*Progression, not progress.*

**The calibration knob (built + verified offline).** The gate arm bets only "rain will happen"
(`forecast_precip → precip`). The calibrated arm adds a **dry companion law**
`~[ (forecast_dry *s *t) ~[ (dry s t) ] ]` and bets a *direction* around a learned cutpoint `pop_cut`:
at/above → **wet** (`(precip …)`), below → **dry** (`(dry …)` = "no precip observed"). Betting dry in
a dry world **hits** (a correct negative forecast scores a hit) — the recovery the gate cannot reach.
`weather_recalibration.recalibrate` moves the cut toward the observed 0.5-crossing (wet losses raise
it, dry losses lower it) and re-seeds either precip law if the world relinquishes it. Precip claims
are raised for *every* forecast hour, so the arm is no longer N-starved. Gate mode is unchanged and
default (`--precip-mode gate` reproduces run 10).

**Driver (to launch):** `caffeinate -i uv run python tools/run_live_weather.py --runs-dir runs/run11
--stations KMIA KTPA KMSY KIAH KJAX --precip-mode calibrated --pop-cut 50 --bin-mode centered
--regenerate --max-seconds 50400` (Gulf/SE July-convection stations · horizon 6 h · temp band 5 °F
centered · **precip calibrated, cut 50 → moves to the observed crossing** · min_interval 600 s ·
ttl 48 polls · supervisor + crash/resume armed · re-generalize on).

**New machinery under test:** `weather_source` calibrated precip mode (`LAW_PRECIP_DRY`, two-direction
`_raise_precip`, dry-bet resolution shape, `pop_cut` persisted) + `weather_recalibration` calibrated
cutpoint controller (wet-loss → cut-up, dry-loss → cut-down; reseeds a fallen wet **or** dry law) +
driver `--precip-mode` / `--pop-cut` + per-arm digest recognising `(dry …)` as precip. Tests:
`test_weather_source.py::test_F1_10_calibrated_dry_arm_recovers_where_the_gate_wet_arm_loses` (the
headline causal, offline through the real loop) + the source/controller unit set. **The temperature
arm is unchanged** — the binned arm remains the in-run reference at its fixed point beside the
calibrated precip arm.

## Session header

| field | value |
|---|---|
| date / operator | 2026-07-11 20:31 → 2026-07-12 ~10:31 (14 h; author-launched) — **completed on `max_seconds`** |
| stations · claim kinds | KIAH KJAX KMIA KMSY KTPA · temp bands (5→20 °F centered), **precip calibrated (cut 50→70, wet/dry)** |
| horizon · ttl | 6 h · 48 polls |
| stops | `max_seconds` 50400 (self-stopped) |
| code version (git SHA) | 89084c4 (run-11 build) |

**Totals:** 17 segments · **316 rounds** · ledger (resolutions only) **81 h / 9 m / 30 a ·
net +72 · accuracy 0.90** · claims raised 196 / resolved 120 / dropped 0 · fetch_errors 18
(KIAH 4 · KJAX 4 · KMIA 4 · KMSY 3 · KTPA 3, absorbed + counted, **0 crashes / 0 resumes**) ·
**10 re-generalizations** (8 temp; 2 precip cut-ups) · **all three laws standing at the end**
(temp band · wet · dry) · poise **● × 17 — every segment poised, zero stumbles**.
**Per-arm:** temp raised 98 / resolved 60 · 22 h / 8 m / 30 a · **net +14** (band pinned at the
20 °F cap, law refelled + reseeded ~1×/segment — the familiar positive-net limit cycle);
precip raised 98 / resolved 60 · **59 h / 1 m / 0 a · net +58 · accuracy 0.983** (~12 % of
raises wet, ~88 % dry; the single miss was the lone resolved *wet* bet; dry bets went 59/59).

## Priors P1¹¹–P4¹¹ — observed vs expected

| prior | expected | observed | meta-disposition |
|---|---|---|---|
| P1¹¹ **precip no longer N-starved** | resolutions lift from run-10's ~9 into the dozens-plus | precip resolved **60** (6.7× run 10), 0 abstentions | **CONFIRMED.** Betting a direction every forecast hour removes the starvation entirely — the arm now matches temp's resolution volume exactly. |
| P2¹¹ **the calibrated arm recovers to a positive net** (headline) | the cut rises, most bets become dry, dry bets hit → net crosses negative→positive; null: net stays ≤ 0 → F1¹⁰ over-read | **net +58, accuracy 0.983** — not merely positive but the run's best arm, out-earning the binned temp arm (+14) 4× | **CONFIRMED — decisively.** Run 10's gate arm: net −5, acc 0.14. Same domain, same stations, same scoring; one variable changed (the knob's *type*). F1¹⁰ stands: **knob-type, not domain, gates recovery.** |
| P3¹¹ **the cutpoint is a calibration knob (both directions)** | the cut settles near the observed 0.5-crossing (not pinned at a cap); both wet and dry bets appear | both directions bet (12 wet raises · 87 dry); the cut moved **only on evidence** (two cut-ups, 50→60→70, each on `acc_wet=0.00`) and **settled at 70 — not the 90 cap**; the fallen wet law reseeded once and stood thereafter | **CONFIRMED, with a refinement.** The knob calibrated rather than ratcheting (contrast run 10's gate → cap). Honest caveat: only **1 wet bet resolved** — the wet side is under-sampled; the payoff is overwhelmingly the majority-outcome (dry) side, exactly as F1¹⁰ predicted. |
| P4¹¹ floor + parity | console captured; knobs+mode carried; §3.3 attests; gate mode reproduces run 10 | console.txt captured the full cut trajectory + reseeds (nothing inferred); 17/17 checkpoints §3.3-attested; 18 fetch errors absorbed per-station, 0 crashes (no resume needed); gate-mode parity pinned by the offline test suite | **CONFIRMED.** |

## Findings (dated, disposed 2026-07-12)

**F1¹¹ (headline) — F1¹⁰ CONFIRMED: the knob-type law holds.** With N no longer starved
(60 resolutions vs 9), the calibrated precip arm recovered to **net +58 / accuracy 0.983**
where run 10's selectivity-gated arm ended **net −5 / accuracy 0.14** — same stations, same
horizon, same scoring, one variable changed. *Whether a refuted theory can re-generalize into a
better one depends on whether its recalibration knob **calibrates** (moves it toward being
right) or merely **selects** (moves it toward betting less).* This is now a twice-evidenced
principle of the game (AEG Part II §11.4), no longer directional.

**F2¹¹ — betting the majority outcome of a rare event is the easiest calibrated win, and the
ledger rewards it honestly.** The recovered net came almost entirely from **dry** bets (59/59
hits): a correct negative forecast scores a hit, so in a domain where the event is rare at the
betting threshold, the calibrated arm converges on mostly-dry and prospers. Honest scope: July
Gulf-coast climatology at a 6 h horizon is *favorable* to the dry side — the win demonstrates
the mechanism, not forecasting skill; a wetter regime (or a lower starting cut) would exercise
the wet side, which here resolved exactly once.

**F3¹¹ — the cutpoint behaved as a genuine calibration knob.** It moved **only on evidence**
(two cut-ups, each triggered by wet losses), **settled at 70 rather than ratcheting to the 90
cap**, and the once-fallen wet law was reseeded and stood to the end. Contrast the run-10 gate,
which ratcheted monotonically to its cap and stayed refuted — the operational signature that
distinguishes a calibration knob from a selectivity knob in the digest stream.

**F4¹¹ — the temp arm reproduced its known dynamics beside the new arm.** Band 5→20 °F (cap)
with ~1 refell+reseed per segment and net +14 — the positive-net limit cycle of F2⁸/F2¹⁰ on
convective stations, unchanged by the precip arm's presence (clean arm isolation). All 17
segments read poised (engagement + settlement + absorption); 18 NWS fetch errors were absorbed
with zero crashes — the F1⁷ resilience machinery is now routine.

**Net for the arc:** the weather trilogy (runs 7–11) closes its question. Predict → refute →
re-generalize **works live**, and its success condition is now stated and twice-tested: give
the theory a knob that calibrates. **Next: run 12 = sports outcomes** — a *discrete* resolving
membrane with no natural width knob, the sharpest test of whether the knob-type law is a law of
the game or a fact about weather.

---

**Artifacts:** `runs/run11/console.txt` (the digest stream — per-arm bets + the cut trajectory) ·
`runs/run11/items.jsonl` (offline replay) · `runs/run11/checkpoints` (17 segments, §3.3-attested) ·
`runs/run11/state.json` + `weather_state.json` (carried state incl. `pop_cut`). See
[runs/OPERATIONS.md](OPERATIONS.md) for the digest glossary.
