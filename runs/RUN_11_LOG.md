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
| date / operator | 2026-07-10 (built; live launch delegated to the author) |
| stations · claim kinds | KMIA KTPA KMSY KIAH KJAX · temp bands (5 °F centered), **precip calibrated (cut 50→crossing, wet/dry)** |
| horizon · ttl | 6 h · 48 polls |
| stops | `max_seconds` 50400 |
| code version (git SHA) | _(pending launch)_ |

**Totals:** _(pending)_

## Priors P1¹¹–P4¹¹ — observed vs expected

| prior | expected | observed | meta-disposition |
|---|---|---|---|
| P1¹¹ **precip no longer N-starved** | betting a direction every hour lifts precip resolutions from run-10's ~9 into the dozens-plus | _(pending)_ | _(pending)_ |
| P2¹¹ **the calibrated arm recovers to a positive net** (headline) | the cut rises toward the cap, most bets become dry, dry bets hit → precip net crosses negative→positive (recovery); null: net stays ≤ 0 → rain genuinely unpredictable, F1¹⁰ over-read | _(pending)_ | _(pending)_ |
| P3¹¹ **the cutpoint is a calibration knob (both directions)** | the cut settles near the observed 0.5-crossing (not pinned at a cap); both `(precip …)` and `(dry …)` bets appear | _(pending)_ | _(pending)_ |
| P4¹¹ floor + parity | console.txt captured (cut trajectory + reseeds legible); knobs + mode carried across resume; §3.3 attests; `--precip-mode gate` reproduces run 10 | _(pending)_ | _(pending)_ |

## Findings (dated, disposed)

_(pending execution)_

---

**Artifacts (on execution):** `runs/run11/console.txt` (the digest stream — per-arm bets + cut
trajectory) · `runs/run11/items.jsonl` (offline replay) · `runs/run11/checkpoints` ·
`runs/run11/state.json` + `weather_state.json` (carried state incl. `pop_cut`). See
[runs/OPERATIONS.md](OPERATIONS.md) for the digest glossary.
